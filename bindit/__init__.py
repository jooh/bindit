# -*- coding: utf-8 -*-
import logging
import itertools
import pathlib
import shlex
import re

"""Core package for bindit."""

__author__ = """Johan Carlin"""
__email__ = "johan.carlin@gmail.com"
__version__ = "0.2.0"

logging.basicConfig(
    format="%(asctime)s %(filename)s %(funcName)s %(message)s",
    datefmt="%Y/%m/%d %H:%M",
    level="INFO",
)
LOGGER = logging.getLogger("bindit")
DRY_RUN = False
ABS_ONLY = False
IGNORE_PATH = [
    pathlib.Path(p)
    for p in [
        "/bin",
        "/sbin",
        "/usr/bin",
        "/usr/sbin",
        "/usr/local/bin",
        "/usr/local/sbin",
        "/opt",
    ]
]
ARG_SPLIT_PATTERN = "|".join("=:,")


def arg_pairs(args):
    """Return overlapping pairs of the input args ([1,2,3] yields [1,2],[2,3])."""
    # extra None to handle second pass iteration, and to handle badly formed commands
    a, b = itertools.tee(list(args) + [None])
    # advance one generator a step to offset
    next(b, None)
    # and zip to a single generator
    return zip(a, b)


def remove_redundant_binds(binds):
    """Remove entries in the dict binds that are sub-directories of another key.
    Operates in-place.
    """
    sources = set(binds.keys())
    for candidate in sources:
        remaining = sources ^ set([candidate])
        # if a parent of candidate is already bound, we can safely remove it
        if any([test in candidate.parents for test in remaining]):
            del binds[candidate]
    return


def bind_dict_to_arg(mapper, new_binds):
    """Return a generator that converts new_binds to valid container-runner bind
    arguments.

    Args:
        mapper (callable): Function that returns a key, val argument pair when called
            with mapper(source, dest). For example, see docker.volume_bind_args
        new_binds (dict): binds specified in source:destination format

    Returns:
        generator: returns a [key, val] argument pair for each key in new_binds

    """
    # concatenated list of tuples - surprisingly ugly for python but efficient
    return itertools.chain.from_iterable(
        (mapper(source, dest) for source, dest in new_binds.items())
    )


def parse_container_args(
    args_iter, bind_parser=None, valid_args=None, valid_letters=None
):
    """Parse arguments to container runner (e.g., docker run). Typically used as the
    first pass of a CLI application (e.g., bindit.docker.docker).

    Args:
        args_iter (iterator): arg_pairs iterator of arguments
        bind_parser (dict): keys as bind mount flags and values as handles to functions
            that parse such flags into a {source: dest} dict. See e.g.
            bindit.docker.BIND_PARSER
        valid_args (dict) : keys as valid container runner arguments and values as the
            expected type of the argument (or non for boolean flags). See e.g.
            bindit.docker.ARGS
        valid_letters (set): single-letter boolean flags. Used to detect arbitrary
            combinations of letters (e.g., docker run -it)

    Returns:
        tuple: (list: detected args to the container runner (DOES NOT include any new
            binds at this stage), dict: defines user-provided bind mounts
            (manual_binds[source] = dest), str: detected container image)

    """
    container_args = []
    manual_binds = {}
    gotkv = False
    for key, val in args_iter:
        if key in bind_parser:
            # here's a user-defined volume bind. Let's make sure we don't mess with it
            # if it appears in the container image arguments
            user_bind = bind_parser[key](val)
            manual_binds.update(user_bind)
            LOGGER.debug(f"added user-defined bind to manual_binds: {user_bind}")
        if key in valid_args:
            if valid_args[key]:
                # this is a key-value pair - se we expect the next argument to be value
                gotkv = True
                container_args += [key, val]
                LOGGER.debug(f"new key-val arg: {key}={val}")
            else:
                # just a boolean flag - so we don't expect a value argument next
                gotkv = False
                container_args += [key]
                LOGGER.debug(f"new flag: {key}")
        elif gotkv:
            # this is the value side of a k-v pair - so we expect a key or flag next
            gotkv = False
            continue
        elif valid_letters and not (set(key) - valid_letters):
            # multi-letter boolean flag ('docker run -it' and such)
            gotkv = False
            container_args += [key]
            LOGGER.debug(f"multi-letter flag: {key}")
        else:
            # something that's not a key or a value. So it's the container name by
            # process of elimination
            container_name = key
            LOGGER.debug(f"identified container as: {key}")
            break
    return container_args, manual_binds, container_name


def arg_to_file_paths(arg):
    """Generator that returns valid file paths in the input arg, splitting according to
    shell characters (with shlex.split) and on ARG_SPLIT_PATTERN. Paths are valid if
    they exist, are absolute (if ABS_ONLY), and do not have any IGNORE_PATH as
    parents.

    """
    for candidate in shlex.split(arg):
        for this_split in re.split(ARG_SPLIT_PATTERN, candidate):
            if not this_split:
                # skip empty str since these get mapped as valid '.' paths
                continue
            this_path = pathlib.Path(this_split)
            abs_ok = this_path.is_absolute() or not ABS_ONLY
            # check that this_path is not in an ignored path or its sub-directories
            resolved_path = this_path.resolve()
            ignore_ok = all(
                [
                    not this_ignore == resolved_path
                    and this_ignore not in resolved_path.parents
                    for this_ignore in IGNORE_PATH
                ]
            )
            # any non-existent path is fine as long as it's absolute
            # but relative paths must exist to control false positives
            exist_ok = this_path.is_absolute() or resolved_path.exists()
            if exist_ok:
                LOGGER.debug(f"detected path {this_path}")
                LOGGER.debug(f"absolute path pass={abs_ok}")
                LOGGER.debug(f"ignore path pass={ignore_ok}")
            if exist_ok and abs_ok and ignore_ok:
                yield this_path


def parse_image_args(args_iter, manual_binds):
    """Parse arguments to the container image, rebasing binds as necessary to make paths
    available inside the container. Typically used as the second pass of a CLI
    application (following parse_container_args, see e.g., bindit.docker.docker).

    Args:
        args_iter (iterator): arg_pairs iterator of arguments (generally the same you
            would use in parse_container_args to make sure you're in the right place)
        manual_binds (dict): defines user-provided bind mounts
            (manual_binds[source] = dest)

    Returns:
        tuple: (list: args to the image (DOES include rebasing of any args that are
            deemed file paths according to new_binds), dict: defines new bind mounts
            (new_binds[source] = dest))

    """
    image_args = []
    new_binds = {}
    # So we continue working on the same iterator...  but now we don't care about
    # key/value - we just want the keys (and because we added a final None, the final _
    # is always irrelevant)
    for in_arg, _ in args_iter:
        if in_arg is None:
            # special case - container with no image_args
            continue
        # handle potentially multiple paths in this in_arg
        for this_path in arg_to_file_paths(in_arg):
            # we have a path that needs to be remapped
            full_path = this_path.resolve()
            this_dir = full_path.parent
            # can only bind directories
            if full_path.is_dir():
                this_dir = full_path
            # detect manual binds that have a shared base
            try:
                # pick the first manually-specified bind that matches
                manual_parent = next(
                    this_manual_bind
                    for this_manual_bind in manual_binds.keys()
                    if this_manual_bind == this_dir
                    or this_manual_bind in this_dir.parents
                )
                # use the manual_bind to map (inserting any additional sub-directories
                # as necessary)
                new_base = manual_binds[manual_parent] / this_dir.relative_to(
                    manual_parent
                )
                LOGGER.debug(f"rebasing on manual bind: {new_base}")
            except StopIteration:
                LOGGER.debug(f"none of these manual binds match: {manual_binds.keys()}")
                # no manual binds match, so the remaining possibility is that it's a new
                # bind
                if this_dir not in new_binds:
                    new_binds[this_dir] = pathlib.PosixPath(
                        "/bindit"
                    ) / this_dir.relative_to(this_dir.anchor)
                    LOGGER.debug(f"creating new bind: {new_binds[this_dir]}")
                # NB indent - the bind might already exist
                new_base = new_binds[this_dir]
            except:
                # something else went wrong with that tricky generator expression
                raise
            # and we now need to remap the original in_arg accordingly
            new_path = new_base / full_path.name
            if full_path.is_dir():
                # avoid repeating the directory name twice (the one edge case where the
                # old os.path.split made more sense than pathlib)
                new_path = new_base
            LOGGER.debug(f"rebasing in_arg path: {this_path}:{new_path}")
            in_arg = in_arg.replace(str(this_path), str(new_path))
        # NB indent - in all cases in_arg needs to be added to image_args
        image_args.append(in_arg)
    # avoid binding the same path twice (ie, parent and sub-directory)
    remove_redundant_binds(new_binds)
    return image_args, new_binds

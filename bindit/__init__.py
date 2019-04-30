# -*- coding: utf-8 -*-
import logging
import itertools
import pathlib

"""Core package for bindit."""

__author__ = """Johan Carlin"""
__email__ = "johan.carlin@gmail.com"
__version__ = "0.1.0"

logging.basicConfig(
    format="%(asctime)s %(filename)s %(funcName)s %(message)s",
    datefmt="%Y/%m/%d %H:%M",
    level="INFO",
)
LOGGER = logging.getLogger("bindit")
DRY_RUN = False
ABS_ONLY = False


def arg_pairs(args):
    """Return overlapping pairs of the input args ([1,2,3] yields
    [1,2],[2,3])."""
    a, b = itertools.tee(args)
    # advance one generator a step to offset
    next(b, None)
    # and zip to a single generator
    return zip(a, b)


def remove_redundant_binds(binds):
    """remove entries in the dict bind that are sub-directories of another key. Operates
    in-place."""
    sources = set(binds.keys())
    for candidate in sources:
        remaining = sources ^ set([candidate])
        # if a parent of candidate is already bound, we can safely remove it
        if any([test in candidate.parents for test in remaining]):
            del binds[candidate]
    return


def parse_container_args(args, bind_parser=None, valid_args=None, valid_letters=None):
    """parse arguments to container runner (e.g., docker run). For example usage, see bindit.docker.

    Inputs
    bind_parser : dict with keys as bind mount flags and values as handles to functions
        that parse such flags into a {source: dest} dict. See e.g.
        bindit.docker.BIND_PARSER
    valid_args : dict with keys as valid container runner arguments and values as the
        expected type of the argument (or non for boolean flags). See e.g.
        bindit.docker.ARGS
    valid_letters : set of single-letter boolean flags. Used to detect arbitrary
        combinations of letters (e.g., docker run -it)

    Returns
    container_args : list of detected args to the container runner (DOES NOT include any
        new binds at this stage)
    container_name : str
    image_args : list of args to the image (DOES include rebasing of any args that are
        deemed file paths according to new_binds)
    new_binds: dict defining new bind mounts (new_binds[source] = dest)."""
    # FIRST PASS - container runner arguments, including user-specified binds
    container_args = []
    manual_binds = {}
    gotkv = False
    # extra None to handle second pass iteration, and to handle badly formed commands
    # (e.g., missing container_name)
    args_iter = arg_pairs(args + [None])
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
            # we got something that's not a key or a value. So it's the container name
            # by process of elimination
            container_name = key
            LOGGER.debug(f"identified container as: {key}")
            break

    # SECOND PASS - args to the container image, including paths that need to be
    # remapped from source to destination
    image_args = []
    new_binds = {}
    # So we get back on the iterator...  but now we don't care about key/value - we just
    # want the keys (and because we added a final None, the final _ is always
    # irrelevant)
    for arg, _ in args_iter:
        if arg is None:
            # special case - container with no image_args
            continue
        this_path = pathlib.Path(arg)
        if this_path.exists() and (this_path.is_absolute() or not ABS_ONLY):
            this_path = this_path.resolve()
            # we have a path that needs to be remapped
            # can only bind directories
            if this_path.is_dir():
                this_dir = this_path
            else:
                this_dir = this_path.parent
            if this_dir in manual_binds:
                # use the manual_bind to map
                new_base = manual_binds[this_dir]
                LOGGER.debug(f"rebasing on manual bind: {new_base}")
            elif this_dir not in new_binds:
                # ok, if we've made it here we have a new bind on our hands
                new_base = pathlib.PosixPath("/bindit") / this_dir.relative_to(
                    this_dir.anchor
                )
                new_binds[this_dir] = new_base
                LOGGER.debug(f"rebasing on new bind: {new_base}")
            # and we now need to remap the original arg accordingly
            new_arg = new_base / this_path.name
            LOGGER.debug(f"rebasing arg path: {arg}:{new_arg}")
            arg = new_arg
        image_args.append(arg)

    # THIRD PASS - avoid binding the same path twice (ie, parent and sub-directory)
    remove_redundant_binds(new_binds)
    return container_args, container_name, image_args, new_binds

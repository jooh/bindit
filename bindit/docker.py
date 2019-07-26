# -*- coding: utf-8 -*-
import sys
import pathlib
import click
import bindit
import bindit.shell

"""docker-specific interface for bindit."""


def infer_docker_cli():
    """infer valid docker run arguments by parsing the output from docker run --help.
    Returns a dict of key-value pairs and a set of single-letter flags (a quirk of the
    docker API is that multiple letters can be combined under a single hyphen, e.g.
    -it, but only if these are short-hand versions of boolean flags, so e.g. -v can't be
    used in this way). Provides inputs for bindit.parse_container_args."""
    try:
        ret = bindit.shell.run("docker", "run", "--help")
    except FileNotFoundError:
        bindit.LOGGER.warning(
            "WARNING: docker not on path, functionality will be limited."
        )
        return {}, set()
    except:
        raise
    rows = ret.stdout.split("\n")
    valid_args = {}
    # these can be arbitrarily combined (e.g. -it) so need to be parsed separately
    letters = ["-"]
    for thisrow in rows:
        # this works because there is only one arg per row
        try:
            # -1 to skip the whitespace
            indstart = thisrow.index(" --") + 1
            # we got one
            indend = thisrow[indstart:].index(" ") + indstart
            newflag = thisrow[indstart:indend]
            # empty if it's a boolean flag, type if it's a key-value pair
            value = thisrow[indend + 1:].split("  ")[0]
            bindit.LOGGER.debug(f"new flag {newflag} {value}")
            valid_args[newflag] = value
            # there might also be a short-hand version, which is always single-hyphen,
            # single character
            if thisrow[2] == "-":
                bindit.LOGGER.debug(f"\twith short-hand letter version {thisrow[2:4]}")
                valid_args[thisrow[2:4]] = value
                letters.append(thisrow[3])
        except ValueError:
            # bad index means no hit
            pass
        except BaseException:
            raise
    return valid_args, set(letters)


def volume_bind_args(source, dest):
    """return tuple specifying a source:dest volume bind mount in docker format."""
    # docker run struggle to follow symlinks on mac successfully, see
    # https://github.com/docker/for-mac/issues/1298
    # (and tempfile generates symlinked /var paths...)
    source = pathlib.Path(source).resolve()
    return "-v", f"{source}:{dest}"


def mount_bind_args(source, dest):
    """return tuple specifying a bind mount in docker format."""
    source = pathlib.Path(source).resolve()
    return "--mount", f"source={source},destination={dest},type=bind"


def parse_bind_mount(bind_arg):
    """unpack bind-mount bind_arg (e.g., src=/foo,dst=/bar) to dict where the key is a
    resolve pathlib.Path and the value is an unresolved (in-container)
    pathlib.PosixPath."""
    mount_dict = dict([kv.split("=") for kv in bind_arg.split(",")])
    source_key = next(k for k in mount_dict if k in ["source", "src"])
    dest_key = next(k for k in mount_dict if k in ["destination", "dst", "target"])
    return {
        pathlib.Path(mount_dict[source_key]).resolve(): pathlib.PosixPath(
            mount_dict[dest_key]
        )
    }


def parse_bind_volume(bind_arg):
    """unpack volume bind bind_arg (e.g., /foo:/bar) to dict where the key is a
    resolve pathlib.Path and the value is an unresolved (in-container)
    pathlib.PosixPath."""
    # can be up to three, but we only want the first two
    bind_arg = bind_arg.split(":")
    src, dst = bind_arg[:2]
    assert len(bind_arg) < 4, "unexpected number of bind_arg"
    return {pathlib.Path(src).resolve(): pathlib.PosixPath(dst)}


BIND_PARSER = {
    "-v": parse_bind_volume,
    "--volume": parse_bind_volume,
    "--mount": parse_bind_mount,
}

ARGS, LETTERS = infer_docker_cli()


@click.command(context_settings=dict(ignore_unknown_options=True))
@click.argument("run_args", nargs=-1, required=True, type=click.UNPROCESSED)
def run(run_args):
    """click.command that casts run_args to lists and handles parsing of the arguments,
    adding volume binds as necessary and running the container (if not DRY_RUN)."""
    args_iter = bindit.arg_pairs(run_args)
    # handle arguments to the container runner
    container_args, manual_binds, container_name = bindit.parse_container_args(
        args_iter, bind_parser=BIND_PARSER, valid_args=ARGS, valid_letters=LETTERS
    )
    # handle arguments to the image, including any rebasing of paths
    image_args, new_binds = bindit.parse_image_args(args_iter, manual_binds)

    # construct new binds in docker format
    bind_args = list(bindit.bind_dict_to_arg(volume_bind_args, new_binds))

    # generate the final command by inserting the new binds
    final_command = (
        ["docker", "run"] + container_args + bind_args + [container_name] + image_args
    )

    # write out to stdout with appropriate escapes
    sys.stdout.write(bindit.shell.join_and_quote(final_command) + "\n")
    if bindit.DRY_RUN:
        return 0

    # run the beast
    ret = bindit.shell.run(*final_command, interactive=True)
    return ret.returncode


@click.group()
def docker():
    pass


docker.add_command(run)

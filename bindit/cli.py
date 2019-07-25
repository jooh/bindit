# -*- coding: utf-8 -*-
import sys
import pathlib
import click
import bindit
import bindit.docker

"""Main command line interface for bindit."""


@click.command(context_settings=dict(ignore_unknown_options=True))
@click.argument("singularity_args", nargs=-1, type=click.UNPROCESSED)
def singularity(singularity_args):
    print(singularity_args)
    pass


@click.option(
    "-l", "--loglevel", default="INFO", help="Logging level", show_default=True
)
@click.option(
    "-d",
    "--dryrun",
    is_flag=True,
    help="Return formatted shell command without invoking container runner",
)
@click.option("-a", "--absonly", is_flag=True, help="Only rebase absolute paths.")
@click.option(
    "-i",
    "--ignorepath",
    multiple=True,
    type=click.Path(exists=True),
    help="path(s) on the host to ignore when detecting new bind mounts. Typical \
        linux binary locations (/usr/bin etc) are included on this list by default.",
)
@click.group()
def main(loglevel, dryrun, absonly, ignorepath):
    """bindit is a wrapper for container runners that makes it easy to handle file input
    and output for containerized command-line applications. It works by detecting file
    paths in the container image arguments, and rebasing these as necessary onto new
    bind mounts.
    """

    bindit.LOGGER.setLevel(loglevel)
    bindit.DRY_RUN = dryrun
    bindit.ABS_ONLY = absonly
    bindit.IGNORE_PATH += [pathlib.Path(p) for p in ignorepath]
    return


main.add_command(bindit.docker.docker)
main.add_command(singularity)

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover

if getattr(sys, "frozen", False):
    # detect pyinstaller frozen app
    main(*sys.argv[1:])

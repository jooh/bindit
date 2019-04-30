# -*- coding: utf-8 -*-
import sys
import click
import bindit
import bindit.docker

"""Top-level command line interface for bindit."""


@click.command(context_settings=dict(ignore_unknown_options=True))
@click.argument("singularity_args", nargs=-1, type=click.UNPROCESSED)
def singularity(singularity_args):
    print(singularity_args)
    pass


@click.option("-l", "--loglevel", default="INFO", help="Logging level")
@click.option(
    "-d",
    "--dryrun",
    is_flag=True,
    help="Return formatted shell command without invoking container runner",
)
@click.option("-a", "--absonly", is_flag=True, help="Only rebase absolute paths.")
@click.group()
def main(loglevel, dryrun, absonly):
    """bindit is a wrapper for container runners that makes it easy to handle file input
    and output for containerised command-line applications. It works by detecting file
    paths in the container image arguments, and rebasing these as necessary onto new
    bind mounts."""
    bindit.LOGGER.setLevel(loglevel)
    bindit.DRY_RUN = dryrun
    bindit.ABS_ONLY = absonly
    return


main.add_command(bindit.docker.docker)
main.add_command(singularity)

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover

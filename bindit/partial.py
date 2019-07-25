import sys
import click
import bindit.shell

"""Auxiliary command line interface for creating containerized apps with bindit. This
tool draws its name from its inspiration, functools.partial in the standard library."""


@click.command(context_settings=dict(ignore_unknown_options=True))
@click.option(
    "--output_file",
    default=None,
    show_default=True,
    help="Output to file instead of standard out",
)
@click.option(
    "--shebang",
    default="#!/bin/bash",
    show_default=True,
    help="Shell interpreter directive",
)
@click.option(
    "--vararg_pattern",
    default='"$@"',
    show_default=True,
    help='vararg pattern (try "$argv" for csh/tcsh)',
)
@click.argument("script_arg", nargs=-1, required=True, type=click.UNPROCESSED)
def main(output_file, shebang, vararg_pattern, script_arg):
    """bindit_partial constructs a shell script wrapper for bindit (or your container
    runner directly) that can be used as a command line interface for the container. It
    works a bit like functools.partial in the standard library - you can offload some
    default parameters (e.g. for volume binds mounts) to the script in order to obtain a
    cleaner API for the container.

    For main documentation, see bindit.
    """

    script_arg = list(script_arg)
    # detect dryrun mode, and remove that arg. Re-insert it later. (ie, you can generate
    # a dryrun app if that's your thing)
    dry_index = None
    try:
        dry_index = script_arg.index("-d")
        script_arg = (*script_arg[:dry_index], *script_arg[dry_index + 1:])
    except ValueError:
        pass
    except:
        raise
    try:
        dry_index = script_arg.index("--dryrun")
        script_arg = (*script_arg[:dry_index], *script_arg[dry_index + 1:])
    except ValueError:
        pass
    except:
        raise
    # script_arg[0] does not have to be "bindit" - you could use this to create the
    # binds when building the app, and then run e.g. docker directly (might be
    # attractive e.g. on HPC if you don't want bindit on the path everywhere). But in
    # this case you of course lose the ability to bind new input paths on the fly when
    # you run the app.
    start_ind = 0
    line = ""
    if script_arg[0] == "bindit":
        start_ind = 1
        line = "bindit "
    ret = bindit.shell.run(
        "bindit", "--dryrun", *script_arg[start_ind:], interactive=False
    )
    if dry_index:
        line += "--dryrun "
    # last line (in case you are using verbose bindit args)
    line += ret.stdout.split("\n")[-2]
    all_lines = [shebang + "\n", line + " " + vararg_pattern + "\n"]
    if output_file:
        with open(output_file, "w") as file_handle:
            file_handle.writelines(all_lines)
    else:
        sys.stdout.writelines(all_lines)
    return


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover

if getattr(sys, "frozen", False):
    # detect pyinstaller frozen app
    main(*sys.argv[1:])

"""bindit_partial CLI tests."""

import pathlib
import bindit.partial
import bindit.docker
import bindit.shell
import test_docker


def partialtester(lines, shebang, vararg_pattern, *arg):
    assert lines[0] == shebang
    assert lines[1][-len(vararg_pattern) :] == vararg_pattern
    for this_arg in arg:
        assert this_arg in lines[1]
    return


def test_stdout_bash(shebang="#!/bin/bash", vararg_pattern='"$@"'):
    """test output to stdout, including pre-specified bind mounts."""
    with test_docker.tempfile.TemporaryDirectory(
        prefix=test_docker.TEMPFILE_PREFIX
    ) as sourcedir:
        sourcedir_resolved = pathlib.Path(sourcedir).resolve()
        manual_dest = pathlib.PosixPath("/manualbind")
        manual_bind = bindit.docker.volume_bind_args(sourcedir_resolved, manual_dest)
        remaining_arg = (test_docker.IMAGE, "bash", "-x")
        args = (
            "bindit_partial",
            "--shebang",
            shebang,
            "--vararg_pattern",
            vararg_pattern,
            "bindit",
            "docker",
            "run",
            *manual_bind,
            *remaining_arg,
        )
        result = bindit.shell.run(*args, interactive=False)
        lines = result.stdout.split("\n")
        partialtester(
            lines,
            shebang,
            vararg_pattern,
            " ".join(manual_bind),
            " ".join(remaining_arg),
        )
        assert lines[1].split(" ")[0] == "bindit"
    return


def test_file_bash(shebang="#!/bin/bash", vararg_pattern='"$@"'):
    """test output to file."""
    with test_docker.tempfile.TemporaryDirectory(
        prefix=test_docker.TEMPFILE_PREFIX
    ) as sourcedir:
        sourcedir_resolved = pathlib.Path(sourcedir).resolve()
        output_file = sourcedir_resolved / pathlib.Path("output")
        assert not output_file.exists()
        manual_dest = pathlib.PosixPath("/manualbind")
        manual_bind = bindit.docker.volume_bind_args(sourcedir_resolved, manual_dest)
        remaining_arg = (test_docker.IMAGE, "bash", "-x")
        args = (
            "bindit_partial",
            "--shebang",
            shebang,
            "--vararg_pattern",
            vararg_pattern,
            "--output_file",
            output_file,
            "bindit",
            "docker",
            "run",
            *manual_bind,
            *remaining_arg,
        )
        result = bindit.shell.run(*args, interactive=False)
        assert output_file.exists()
        with open(output_file, "r") as file:
            lines = file.read().splitlines()
        partialtester(
            lines,
            shebang,
            vararg_pattern,
            " ".join(manual_bind),
            " ".join(remaining_arg),
        )
        assert lines[1].split(" ")[0] == "bindit"
    return


def test_stdout_csh():
    """test shell override from default bash to c shell."""
    test_stdout_bash(shebang="#!/bin/csh", vararg_pattern='"$argv"')
    return


def test_file_csh():
    """test shell override from default bash to c shell."""
    test_file_bash(shebang="#!/bin/csh", vararg_pattern='"$argv"')
    return


def test_docker_direct():
    """test partial wrap without bindit in the wrapper command.
    (also leaves off the explicit args to bindit_partial to check that default behaviour
    works.)"""
    with test_docker.tempfile.TemporaryDirectory(
        prefix=test_docker.TEMPFILE_PREFIX
    ) as sourcedir:
        sourcedir_resolved = pathlib.Path(sourcedir).resolve()
        manual_dest = pathlib.PosixPath("/manualbind")
        manual_bind = bindit.docker.volume_bind_args(sourcedir_resolved, manual_dest)
        remaining_arg = (test_docker.IMAGE, "bash", "-x")
        args = ("bindit_partial", "docker", "run", *manual_bind, *remaining_arg)
        result = bindit.shell.run(*args, interactive=False)
        lines = result.stdout.split("\n")
        partialtester(
            lines, "#!/bin/bash", '"$@"', " ".join(manual_bind), " ".join(remaining_arg)
        )
        assert lines[1].split(" ")[0] == "docker"
    return

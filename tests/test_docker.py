#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Docker tests for `bindit` package."""

import json
import pathlib
import tempfile
import bindit.shell
import bindit.docker
from click.testing import CliRunner
import subprocess

IMAGE = "alpine:latest"
IMAGE_SHELL_PREFIX = ["/bin/sh", "-c"]
TEMPFILE_PREFIX = f"bindit_{__name__}_"
SOURCE_ABSTRACT = pathlib.Path("$(pwd)/target").resolve()
DEST_ABSTRACT = pathlib.PosixPath("/app")


class DockerRun(object):
    """bindit docker API for detached container runs. The main use is as a
    test context manager."""

    def __init__(
        self,
        *image_arg,
        runner_arg=[],
        name="bindit-test",
        image=IMAGE,
        shell_prefix=IMAGE_SHELL_PREFIX,
    ):
        # so we need to take the args, add a cat to ensure the container stays up
        if image_arg:
            self.image_arg = bindit.shell.join_and_quote(list(image_arg) + ["&", "cat"])
        else:
            self.image_arg = "cat"
        self.shell_prefix = shell_prefix
        self.image = image
        self.name = name
        # input validation
        assert not "--name" in runner_arg, "set name by kwarg"
        assert (
            not "--detach" in runner_arg and not "-d" in runner_arg
        ), "detach arg is redundant"
        self.runner_arg = runner_arg
        if self.is_running():
            print(f"cleaning up orphan container image: {self.name}")
            self.cleanup()

    def __enter__(self):
        # np, image_arg run as a single quoted str to support more complex expressions than
        # standard docker run img cmd syntax allows.
        self.ret = bindit.shell.run(
            "bindit",
            "--loglevel",
            "DEBUG",
            "docker",
            "run",
            "--detach",
            "-it",
            "--name",
            self.name,
            *self.runner_arg,
            self.image,
            *self.shell_prefix,
            self.image_arg,
        )
        return self

    def cleanup(self):
        """remove running container"""
        ret = bindit.shell.run("docker", "container", "rm", "-f", self.name)

    def inspect(self):
        """return parsed JSON from docker inspect."""
        ret = bindit.shell.run("docker", "inspect", self.name)
        return json.loads(ret.stdout)

    def get_mounts(self):
        """return current mounts in a dict where source is key and destination is
        value."""
        result = self.inspect()
        assert len(result) == 1, "only one running instance supported"
        return dict(
            [
                (
                    pathlib.Path(thismount["Source"]).resolve(),
                    pathlib.PosixPath(thismount["Destination"]),
                )
                for thismount in result[0]["Mounts"]
            ]
        )

    def exec(self, *arg):
        """docker exec *arg on running container"""
        ret = bindit.shell.run("docker", "exec", self.name, *arg)
        return ret

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.cleanup()
        assert exc_value == None

    def is_running(self):
        """return true if the container is currently running."""
        ret = bindit.shell.run(
            "docker", "container", "ls", "-q", "--all", "-f", f"name={self.name}"
        )
        if ret.stdout:
            return True
        return False

    def has_file(self, destpath):
        """return true if destpath is present."""
        ret = self.exec("ls", "-1", destpath.parent)
        files = ret.stdout.split("\n")
        return destpath.name in files


def test_cli_inference():
    """check that we have FLAGS, LETTERS, and the correct keys in BIND_PARSER."""
    assert bindit.docker.ARGS
    assert bindit.docker.LETTERS
    for bind in bindit.docker.BIND_PARSER:
        assert bind in bindit.docker.ARGS


def test_parse_bind_mount():
    """test that parse_bind_mount meets docker API requirements."""
    for sourcekey in ["source", "src"]:
        for destkey in ["destination", "dst", "target"]:
            val = f"type=bind,{sourcekey}={SOURCE_ABSTRACT},{destkey}={DEST_ABSTRACT}"
            mapping = bindit.docker.parse_bind_mount(val)
            assert list(mapping.keys())[0] == SOURCE_ABSTRACT
            assert list(mapping.values())[0] == DEST_ABSTRACT


def test_parse_bind_volume():
    """test that parse_bind_volume meets docker API requirements."""
    # two-field version
    mapping = bindit.docker.parse_bind_volume(f"{SOURCE_ABSTRACT}:{DEST_ABSTRACT}")
    assert list(mapping.keys())[0] == SOURCE_ABSTRACT
    assert list(mapping.values())[0] == DEST_ABSTRACT
    # three-field
    mapping = bindit.docker.parse_bind_volume(
        f"{SOURCE_ABSTRACT}:{DEST_ABSTRACT}:ro,consistent"
    )
    assert list(mapping.keys())[0] == SOURCE_ABSTRACT
    assert list(mapping.values())[0] == DEST_ABSTRACT


def test_no_nothing():
    """test that bindit stays out of the way when there's nothing to do."""
    with DockerRun() as container:
        assert container.is_running()
        assert not container.get_mounts()


def test_ignore():
    """test that bindit does not attempt to bind default binary directory."""
    with DockerRun("ls", "/usr/bin") as container:
        assert container.is_running()
        assert not container.get_mounts()


def test_bind():
    """test standard bindit mapping - bind referenced dir, no other manual binds."""
    with tempfile.TemporaryDirectory(prefix=TEMPFILE_PREFIX) as sourcedir:
        sourcedir_resolved = pathlib.Path(sourcedir).resolve()
        sourcefile = pathlib.Path(
            tempfile.mkstemp(dir=sourcedir, prefix=TEMPFILE_PREFIX)[1]
        )
        with DockerRun("ls", sourcefile) as container:
            assert container.is_running()
            # check that sourcedir has been mounted
            mounts = container.get_mounts()
            assert sourcedir_resolved in mounts
            # check that the destination has the correct root directory
            assert pathlib.Path("/bindit") in mounts[sourcedir_resolved].parents


def manual_bind_runner(binder):
    with tempfile.TemporaryDirectory(prefix=TEMPFILE_PREFIX) as sourcedir:
        sourcefile = pathlib.Path(
            tempfile.mkstemp(dir=sourcedir, prefix=TEMPFILE_PREFIX)[1]
        )
        sourcedir_resolved = pathlib.Path(sourcedir).resolve()
        manualdest = pathlib.PosixPath("/manualbind")
        # expected location
        destfile = manualdest / sourcefile.name
        with DockerRun(
            "ls",
            sourcefile,
            runner_arg=list(binder(sourcedir, manualdest)),
        ) as container:
            assert container.is_running()
            mounts = container.get_mounts()
            # verify that the source is there
            assert sourcedir_resolved in mounts
            # and that the destination is the manual destination and not some /bindit
            # stuff
            assert mounts[sourcedir_resolved] == manualdest
            # and that we have no other mounts
            assert list(mounts.keys()) == [sourcedir_resolved]

def test_manual_bind_mount():
    """test handling of a user-defined bind (specified in mount syntax)."""
    manual_bind_runner(bindit.docker.mount_bind_args)


def test_manual_bind_volume():
    """test handling of a user-defined bind (specified in volume syntax)."""
    manual_bind_runner(bindit.docker.volume_bind_args)


def test_no_image_args():
    """test handling of a user-defined bind when no image args are present."""
    with tempfile.TemporaryDirectory(prefix=TEMPFILE_PREFIX) as sourcedir:
        sourcefile = pathlib.Path(
            tempfile.mkstemp(dir=sourcedir, prefix=TEMPFILE_PREFIX)[1]
        )
        sourcedir_resolved = pathlib.Path(sourcedir).resolve()
        destdir = pathlib.PosixPath("/manualbind")
        destfile = destdir / sourcefile.name
        with DockerRun(
            runner_arg=list(bindit.docker.volume_bind_args(sourcedir, destdir))
        ) as container:
            assert container.is_running()
            mounts = container.get_mounts()
            # verify that the source is there
            assert sourcedir_resolved in mounts
            # and that the destination is the manual destination and not some /bindit
            # stuff
            assert mounts[sourcedir_resolved] == destdir
            # and that we have no other mounts
            assert list(mounts.keys()) == [sourcedir_resolved]
            assert container.has_file(destfile)


def test_bind_folder():
    """test bindit mapping of folder - bind referenced dir, without any superfluous
    nesting."""
    with tempfile.TemporaryDirectory(prefix=TEMPFILE_PREFIX) as sourcedir:
        sourcedir_resolved = pathlib.Path(sourcedir).resolve()
        destdir_expected = pathlib.PosixPath(
            "/bindit"
        ) / sourcedir_resolved.relative_to(sourcedir_resolved.anchor)
        with DockerRun("ls", sourcedir) as container:
            assert container.is_running()
            # check that sourcedir has been mounted
            mounts = container.get_mounts()
            assert sourcedir_resolved in mounts
            assert pathlib.PosixPath(mounts[sourcedir_resolved]) == destdir_expected

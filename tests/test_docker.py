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

IMAGE = "nginx:latest"
TEMPFILE_PREFIX = f"bindit_{__name__}_"
SOURCE_ABSTRACT = pathlib.Path("$(pwd)/target").resolve()
DEST_ABSTRACT = pathlib.PosixPath("/app")


class DockerRun(object):
    """bindit docker API for detached container runs. Main use is as a
    test context manager."""

    def __init__(self, *runarg, name="bindit-test"):
        self.runarg = runarg
        self.name = name
        assert not "--name" in runarg, "set name by kwarg"
        assert (
            not "--detach" in runarg and not "-d" in runarg
        ), "detach arg is redundant"
        if self.is_running():
            print(f"cleaning up orphan container image: {self.name}")
            self.cleanup()

    def __enter__(self):
        ret = bindit.shell.run(
            "bindit",
            "--loglevel",
            "DEBUG",
            "docker",
            "run",
            "--detach",
            "--name",
            self.name,
            *self.runarg,
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
        destpath = pathlib.Path(destpath)
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


def test_bind():
    """test standard bindit mapping - bind referenced dir, no other manual binds."""
    with tempfile.TemporaryDirectory(prefix=TEMPFILE_PREFIX) as sourcedir:
        sourcedir_resolved = pathlib.Path(sourcedir).resolve()
        sourcefile = pathlib.Path(
            tempfile.mkstemp(dir=sourcedir, prefix=TEMPFILE_PREFIX)[1]
        )
        with DockerRun(IMAGE, "ls", sourcefile) as container:
            assert container.is_running()
            # check that sourcedir has been mounted
            mounts = container.get_mounts()
            assert sourcedir_resolved in mounts
            # check that the destination has the correct root directory
            assert pathlib.Path("/bindit") in mounts[sourcedir_resolved].parents


def test_manual_bind_mount():
    """test handling of a user-defined bind (specified in mount syntax)."""
    with tempfile.TemporaryDirectory(prefix=TEMPFILE_PREFIX) as sourcedir:
        sourcefile = pathlib.Path(
            tempfile.mkstemp(dir=sourcedir, prefix=TEMPFILE_PREFIX)[1]
        )
        sourcedir_resolved = pathlib.Path(sourcedir).resolve()
        manualdest = pathlib.PosixPath("/manualbind")
        # expected location
        destfile = manualdest / sourcefile.name
        with DockerRun(
            *bindit.docker.mount_bind_args(sourcedir, manualdest),
            IMAGE,
            "ls",
            sourcefile,
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


def test_manual_bind_volume():
    """test handling of a user-defined bind (specified in volume syntax)."""
    with tempfile.TemporaryDirectory(prefix=TEMPFILE_PREFIX) as sourcedir:
        sourcefile = pathlib.Path(
            tempfile.mkstemp(dir=sourcedir, prefix=TEMPFILE_PREFIX)[1]
        )
        sourcedir_resolved = pathlib.Path(sourcedir).resolve()
        manualdest = pathlib.PosixPath("/manualbind")
        # expected location
        destfile = manualdest / sourcefile.name
        with DockerRun(
            *bindit.docker.volume_bind_args(sourcedir, manualdest),
            IMAGE,
            "ls",
            sourcefile,
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


def test_no_image_args():
    """test handling of a user-defined bind when no image args are present."""
    with tempfile.TemporaryDirectory(prefix=TEMPFILE_PREFIX) as sourcedir:
        sourcefile = pathlib.Path(
            tempfile.mkstemp(dir=sourcedir, prefix=TEMPFILE_PREFIX)[1]
        )
        sourcedir_resolved = pathlib.Path(sourcedir).resolve()
        manualdest = pathlib.PosixPath("/manualbind")
        # expected location
        destfile = manualdest / sourcefile.name
        with DockerRun(
            *bindit.docker.volume_bind_args(sourcedir, manualdest), IMAGE
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


def test_no_nothing():
    """test that bindit stays out of the way when there's nothing to do."""
    with DockerRun(IMAGE) as container:
        assert container.is_running()
        assert not container.get_mounts()

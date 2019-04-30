#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Yes, the tests must also have tests."""
import pathlib
import tempfile
import bindit.docker
import test_docker

TEMPFILE_PREFIX = f"bindit_{__name__}_"


def test_docker_daemon():
    """test that docker daemon is operational."""
    ret = bindit.shell.run("docker", "container", "ls")


def test_DockerRun():
    """test standard bind mapping with DockerRun. If this test fails with exit code 125
    (mounts denied), you may need to add the system-specific temp directory to the
    docker mounts (e.g., /var/folders/ on OS X)."""
    # we follow the tutorial at https://docs.docker.com/storage/bind-mounts/
    with tempfile.TemporaryDirectory(prefix=TEMPFILE_PREFIX) as sourcedir:
        sourcefile = pathlib.Path(
            tempfile.mkstemp(dir=sourcedir, prefix=TEMPFILE_PREFIX)[1]
        )
        destdir = pathlib.PosixPath("/bindit/test/")
        destfile = destdir / sourcefile.name
        # so now we map sourcedir:destdir and check that the destfile exists inside
        # container.
        with test_docker.DockerRun(
            *bindit.docker.volume_bind_args(sourcedir, destdir), test_docker.IMAGE
        ) as container:
            mounts = container.get_mounts()
            # check that mount points are as specified
            assert (
                pathlib.Path(list(mounts.keys())[0])
                == pathlib.Path(sourcedir).resolve()
            )
            assert pathlib.Path(list(mounts.values())[0]) == destdir
            assert container.has_file(pathlib.Path(destdir, destfile.name))

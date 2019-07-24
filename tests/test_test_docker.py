#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Yes, the tests must also have tests."""
import time
import pathlib
import tempfile
import bindit.docker
from test_docker import DockerRun

TEMPFILE_PREFIX = f"bindit_{__name__}_"


def test_docker_daemon():
    """test that docker daemon is operational."""
    ret = bindit.shell.run("docker", "container", "ls")

def test_DockerRun_nothing():
    """test DockerRun default behaviour."""
    with tempfile.TemporaryDirectory(prefix=TEMPFILE_PREFIX) as sourcedir:
        sourcefile = pathlib.Path(
            tempfile.mkstemp(dir=sourcedir, prefix=TEMPFILE_PREFIX)[1]
        )
        destdir = pathlib.PosixPath("/bindit/test/")
        destfile = destdir / sourcefile.name
        with DockerRun() as container:
            # give the container process a bit of time to close
            # (sometimes you can get a docker exec in on a badly formed container before
            # the process returns and the container winds down)
            time.sleep(2)
            assert container.is_running()

def test_DockerRun_bind():
    """test standard bind mapping with DockerRun. If this test fails with exit code 125
    (mounts denied), you may need to add the system-specific temp directory to the
    docker mounts (e.g., /var/folders/ on OS X)."""
    with tempfile.TemporaryDirectory(prefix=TEMPFILE_PREFIX) as sourcedir:
        sourcefile = pathlib.Path(
            tempfile.mkstemp(dir=sourcedir, prefix=TEMPFILE_PREFIX)[1]
        )
        destdir = pathlib.PosixPath("/bindit/test/")
        destfile = destdir / sourcefile.name
        # so now we map sourcedir:destdir and check that the destfile exists inside
        # container.
        with DockerRun(
            runner_arg = list(bindit.docker.volume_bind_args(sourcedir, destdir))
        ) as container:
            mounts = container.get_mounts()
            # check that mount points are as specified
            assert (
                pathlib.Path(list(mounts.keys())[0])
                == pathlib.Path(sourcedir).resolve()
            )
            assert pathlib.Path(list(mounts.values())[0]) == destdir
            assert container.has_file(destfile)

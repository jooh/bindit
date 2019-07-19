#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""tests for main `bindit` package."""
import pathlib
import tempfile
import bindit

TEMPFILE_PREFIX = f"bindit_{__name__}_"

def test_remove_redundant_binds_no_redundancy():
    binds = {pathlib.Path(x): None for x in ["/a/", "/b/", "/c/"]}
    old_binds = binds.copy()
    bindit.remove_redundant_binds(binds)
    assert binds == old_binds


def test_remove_redundant_binds_redundancy():
    binds = {pathlib.Path(x): None for x in ["/a/1", "/a/", "/c/"]}
    bindit.remove_redundant_binds(binds)
    assert pathlib.Path("/a/") in binds
    assert pathlib.Path("/c/") in binds
    assert not pathlib.Path("/a/1") in binds


def test_arg_to_file_paths_nothing():
    t = [v for v in bindit.arg_to_file_paths("no 'filepaths here', no:none")]
    assert not t

def test_arg_to_file_paths_valid():
    with tempfile.TemporaryDirectory(prefix=TEMPFILE_PREFIX) as sourcedir:
        with tempfile.TemporaryDirectory(prefix=TEMPFILE_PREFIX) as sourcedir2:
            t = [v for v in bindit.arg_to_file_paths(f"'here a' path={sourcedir}:/invalid/path,{sourcedir2}")]
            assert len(t) == 2
            assert t[0] == pathlib.Path(sourcedir)

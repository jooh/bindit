#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""tests for main `bindit` package."""
import pathlib
import bindit


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

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""General CLI tests for `bindit` package."""

from click.testing import CliRunner
import bindit.cli


def test_install():
    """Test that the bindit CLI is on path and runs."""
    runner = CliRunner()
    result = runner.invoke(bindit.cli.main)
    assert result.exit_code == 0
    assert "bindit is a wrapper for container runners" in result.output
    help_result = runner.invoke(bindit.cli.main, ["--help"])
    assert help_result.exit_code == 0
    assert "--help               Show this message and exit." in help_result.output

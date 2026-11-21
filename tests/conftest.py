"""Shared fixtures."""

import os
import stat
import sys
from pathlib import Path

import pytest


@pytest.fixture
def aws(tmp_path, monkeypatch):
    """A stand-in `aws` first on PATH; returns the directory it stores objects in."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    store = tmp_path / "store"
    store.mkdir()
    executable = bin_dir / "aws"
    executable.write_text(
        f'#!/bin/sh\nexec {sys.executable} {Path(__file__).parent / "fake_aws.py"} "$@"\n'
    )
    executable.chmod(executable.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_AWS_STORE", str(store))
    monkeypatch.delenv("FAKE_AWS_FAIL", raising=False)
    return store

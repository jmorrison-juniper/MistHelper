"""Tests for narrowed container detection exception handlers."""

from __future__ import annotations  # Use postponed annotations for modern typing.

import sys  # Patch module cache entries for the lazy pwd import.
from types import SimpleNamespace  # Build a minimal fake pwd module.

import pytest  # Use monkeypatch and exception assertions.

from src.maps import _container_detection as detection  # Import the module under test.


def test_runtime_user_returns_false_when_uid_lookup_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """A missing Unix user record returns False and does not raise."""

    def _raise_key_error(_uid: int) -> str:  # Provide a fake getpwuid with the expected failure.
        raise KeyError("missing uid")  # Simulate pwd lookup failure for the active uid.

    fake_pwd = SimpleNamespace(getpwuid=_raise_key_error)  # Build the minimal lazy-import target.
    monkeypatch.setitem(sys.modules, "pwd", fake_pwd)  # Force the lazy import to use the fake module.
    monkeypatch.setattr(detection.os, "getuid", lambda: 1000, raising=False)  # Provide a stable uid source.
    assert detection._check_runtime_user() is False  # The narrowed handler keeps the soft-fail behavior.


def test_runtime_user_propagates_unexpected_pwd_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unexpected user lookup fault reaches the caller."""

    def _raise_runtime_error(_uid: int) -> str:  # Provide a fake getpwuid with an unexpected fault.
        raise RuntimeError("pwd broke")  # Prove the handler no longer hides all faults.

    fake_pwd = SimpleNamespace(getpwuid=_raise_runtime_error)  # Build the minimal lazy-import target.
    monkeypatch.setitem(sys.modules, "pwd", fake_pwd)  # Force the lazy import to use the fake module.
    monkeypatch.setattr(detection.os, "getuid", lambda: 1000, raising=False)  # Provide a stable uid source.
    with pytest.raises(RuntimeError, match="pwd broke"):  # The narrowed handler lets runtime faults surface.
        detection._check_runtime_user()  # Run the user heuristic.


def test_app_path_returns_false_when_file_global_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """A missing ``__file__`` global returns False and does not raise."""

    monkeypatch.delattr(detection, "__file__", raising=True)  # Simulate an importer that omits the file path.
    assert detection._check_app_path() is False  # The narrowed handler keeps the soft-fail behavior.

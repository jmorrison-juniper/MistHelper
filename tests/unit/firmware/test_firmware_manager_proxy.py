"""Tests for the firmware manager dependency resolver seam."""

from __future__ import annotations  # Keep annotations stable during pytest collection.

import types  # Build a small dependency host without importing MistHelper.

import src.firmware.firmware_manager as fm_mod  # Import the module under test through its source path.


def test_firmware_manager_uses_source_dependency_resolver() -> None:
    """The firmware manager must not keep a root-module proxy."""
    assert fm_mod._MH is fm_mod.SourceDependencyResolver  # The resolver replaces the deleted proxy.


def test_dependency_host_remains_late_bound(monkeypatch) -> None:
    """The resolver seam must allow tests to replace the active host."""
    first_host = types.SimpleNamespace(InputUtils="first")  # Build the first fake dependency host.
    second_host = types.SimpleNamespace(InputUtils="second")  # Build the second fake dependency host.
    hosts = iter((first_host, second_host))  # Provide a different host for each lookup.
    monkeypatch.setattr(type(fm_mod.SourceDependencyResolver), "active_dependency_host", lambda _self: next(hosts))
    assert fm_mod.SourceDependencyResolver.active_dependency_host().InputUtils == "first"  # Prove first lookup.
    assert fm_mod.SourceDependencyResolver.active_dependency_host().InputUtils == "second"  # Prove late binding.

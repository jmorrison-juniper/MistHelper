"""Unit tests for src.refactors.run_interactive_test.

Wave 13 P2 coverage lift — RunInteractiveTestManager is a thin
orchestrator that late-binds MistHelper and passes org_id closures
through to _build_interactive_test_runner. Cover the resolver, ctor,
getter/setter closures, and run() to close the 43% gap in one file.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on older type checkers

import sys  # WHY: patch.dict(sys.modules) to inject a fake MistHelper module
from unittest.mock import MagicMock, patch  # WHY: MagicMock stubs + patch for sys.modules swap

from src.refactors.run_interactive_test import (
    RunInteractiveTestManager,  # WHY: subject under test
    _resolve_runtime_dependencies,  # WHY: cover the module-level helper directly
)


def _install_fake_misthelper(**attrs: object) -> MagicMock:
    """Return a MagicMock stand-in for MistHelper with the requested attrs pre-set."""
    fake = MagicMock()  # WHY: MagicMock permits arbitrary attribute access without ceremony
    for key, value in attrs.items():  # WHY: seed the required attributes
        setattr(fake, key, value)  # WHY: attach each stub as a module attribute
    return fake  # WHY: caller patches sys.modules["MistHelper"] with this handle


def test_resolve_runtime_dependencies_returns_misthelper_module() -> None:
    """_resolve_runtime_dependencies imports MistHelper and packages it in a SimpleNamespace."""
    fake = _install_fake_misthelper()  # WHY: no attributes needed — we only assert identity
    with patch.dict(sys.modules, {"MistHelper": fake}):  # WHY: force importlib to return our fake
        deps = _resolve_runtime_dependencies()  # WHY: call the resolver under isolation
    assert deps.misthelper_module is fake  # WHY: resolver must expose the imported module handle


def test_manager_init_captures_misthelper_handle() -> None:
    """RunInteractiveTestManager ctor records the current MistHelper module in ._deps."""
    fake = _install_fake_misthelper()
    with patch.dict(sys.modules, {"MistHelper": fake}):
        manager = RunInteractiveTestManager()
    assert manager._deps.misthelper_module is fake  # WHY: init snapshotted our stub module


def test_get_and_set_org_id_round_trip() -> None:
    """The manager's org_id closures read/write against the live MistHelper module."""
    fake = _install_fake_misthelper(org_id="cached-org")  # WHY: seed a pre-existing org_id value
    with patch.dict(sys.modules, {"MistHelper": fake}):
        manager = RunInteractiveTestManager()
    assert manager._get_org_id() == "cached-org"  # WHY: getter honours the current module attribute
    manager._set_org_id("fresh-org")  # WHY: setter must persist a new value
    assert fake.org_id == "fresh-org"  # WHY: setter mutated the shared module handle


def test_get_org_id_returns_none_when_missing() -> None:
    """Getter falls back to None when MistHelper has no org_id attribute yet."""
    fake = MagicMock(spec=[])  # WHY: spec=[] blocks arbitrary attribute access so getattr default fires
    with patch.dict(sys.modules, {"MistHelper": fake}):
        manager = RunInteractiveTestManager()
    assert manager._get_org_id() is None  # WHY: default from getattr(..., None) path


def test_run_delegates_to_interactive_test_runner() -> None:
    """run() builds a runner via _build_interactive_test_runner and coerces execute() to bool."""
    runner = MagicMock()  # WHY: runner exposes execute()
    runner.execute.return_value = True  # WHY: happy path returns truthy verdict
    builder = MagicMock(return_value=runner)  # WHY: _build_interactive_test_runner returns our runner
    fake = _install_fake_misthelper()
    fake._build_interactive_test_runner = builder  # WHY: attach builder on the fake MistHelper
    with patch.dict(sys.modules, {"MistHelper": fake}):
        manager = RunInteractiveTestManager()
        result = manager.run()  # WHY: exercise the orchestration entrypoint
    assert result is True  # WHY: execute() -> True must survive bool() coercion
    builder.assert_called_once()  # WHY: runner was built exactly once
    args = builder.call_args.args  # WHY: builder receives the two org_id closures positionally
    assert callable(args[0]) and callable(args[1])  # WHY: closures must be callable
    runner.execute.assert_called_once_with()  # WHY: runner dispatched


def test_run_returns_false_when_runner_reports_failure() -> None:
    """run() returns False when the runner's execute() returns a falsy verdict."""
    runner = MagicMock()
    runner.execute.return_value = 0  # WHY: falsy verdict must be coerced to False
    builder = MagicMock(return_value=runner)
    fake = _install_fake_misthelper()
    fake._build_interactive_test_runner = builder
    with patch.dict(sys.modules, {"MistHelper": fake}):
        manager = RunInteractiveTestManager()
        assert manager.run() is False  # WHY: bool(0) -> False propagates as the return value

"""Table-driven tests for the menu 291 RRM dry-run precedence policy."""

from __future__ import annotations  # WHY: keep annotations lightweight during tests.

import argparse  # WHY: the policy reads the parsed root CLI namespace.
from types import SimpleNamespace  # WHY: tests need only the root args attribute.
from typing import Any  # WHY: pytest monkeypatch is dynamically typed.

import pytest  # WHY: precedence cases use parametrize.

from src.foundation.runtime.config.source_dependency_resolver import SourceDependencyResolver
from src.mist.resources.site.rrm_reset.dry_run_policy import RrmDryRunPolicy


@pytest.mark.parametrize(
    ("argument", "cli_mode", "environment", "expected", "reason"),
    [
        (True, False, "false", True, "explicit dry-run argument wins"),
        (False, True, "true", False, "explicit live argument wins"),
        (None, True, "false", True, "CLI dry-run wins"),
        (None, False, "true", False, "CLI live-run wins"),
        (None, None, "true", True, "truthy environment forces dry-run"),
        (None, None, "1", True, "numeric truthy environment forces dry-run"),
        (None, None, "yes", True, "yes environment forces dry-run"),
        (None, None, "dry-run", True, "named environment mode forces dry-run"),
        (None, None, "false", True, "false environment cannot authorize live mode"),
        (None, None, "0", True, "zero environment cannot authorize live mode"),
        (None, None, "banana", True, "invalid environment cannot authorize live mode"),
        (None, None, "", True, "empty environment cannot authorize live mode"),
        (None, None, None, True, "absence forces dry-run mode"),
    ],
)
def test_resolve_obeys_precedence(
    monkeypatch: Any,
    argument: bool | None,
    cli_mode: bool | None,
    environment: str | None,
    expected: bool,
    reason: str,
) -> None:
    """The resolver must obey every adopted precedence conflict and safe default."""
    root = SimpleNamespace(args=argparse.Namespace(dry_run=cli_mode))  # WHY: model the root CLI state.
    monkeypatch.setattr(SourceDependencyResolver, "_root_module", root)  # WHY: bind the resolver seam.
    if environment is None:  # WHY: absence differs from an empty environment value.
        monkeypatch.delenv("RRM_DRY_RUN", raising=False)  # WHY: prove the true absence case.
    else:
        monkeypatch.setenv("RRM_DRY_RUN", environment)  # WHY: provide the table environment signal.
    assert RrmDryRunPolicy.resolve(argument) is expected, reason  # WHY: one assertion names each policy rule.


def test_resolve_without_bound_root_forces_dry_run(monkeypatch: Any) -> None:
    """A library call without root CLI state must use the safe environment fallback."""
    monkeypatch.setattr(SourceDependencyResolver, "_root_module", None)  # WHY: model an unbound host module.
    monkeypatch.delenv("RRM_DRY_RUN", raising=False)  # WHY: no lower policy source states a mode.
    assert RrmDryRunPolicy.resolve(None) is True, "unbound root state and absence must force dry-run mode"

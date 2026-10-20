"""Regression tests for package-specification guards in GlobalImportManager."""

from __future__ import annotations  # WHY: follow the repository's postponed-annotation convention.

from unittest.mock import MagicMock  # WHY: isolate import-manager collaborators from package installation.

import MistHelper  # WHY: exercise the production GlobalImportManager implementation.


def _new_manager() -> MistHelper.GlobalImportManager:
    """Build an uninitialized manager for narrow dependency-guard tests."""
    return MistHelper.GlobalImportManager.__new__(
        MistHelper.GlobalImportManager
    )  # WHY: avoid environment-driven startup work unrelated to these guards.


def test_install_guard_refuses_missing_spec_after_permissive_gate() -> None:
    """A defensive package-spec guard prevents accidental unconstrained installation."""
    manager = _new_manager()  # WHY: use only the collaborators reached by the guard.
    manager._auto_install_allowed = MagicMock(
        return_value=True
    )  # WHY: simulate an overridden gate admitting invalid input.
    manager._attempt_install = MagicMock()  # WHY: prove no installer is invoked without a package specification.

    result = manager._install_and_retry(
        "example_module", None, required=True, skip_deps=False
    )  # WHY: exercise the former assert-only defensive path.

    assert result is None  # WHY: invalid package input must fail safely.
    manager._attempt_install.assert_not_called()  # WHY: no installer may receive a missing specification.


def test_upgrade_guard_refuses_missing_spec_after_permissive_gate() -> None:
    """A defensive package-spec guard prevents accidental unconstrained upgrades."""
    manager = _new_manager()  # WHY: use only the collaborators reached by the guard.
    module = object()  # WHY: supply a concrete import result for cache verification.
    manager.imports = {}  # WHY: preserve the normal successful-import cache behavior.
    manager._should_upgrade_package = MagicMock(return_value=True)  # WHY: simulate an overridden upgrade gate.
    manager._check_and_upgrade_package = (
        MagicMock()
    )  # WHY: prove no upgrade is invoked without a package specification.

    manager._record_successful_import(
        module, "example_module", None, skip_deps=False, skip_upgrade=False
    )  # WHY: exercise the former assert-only defensive path.

    assert manager.imports["example_module"] is module  # WHY: successful imports still remain cached.
    manager._check_and_upgrade_package.assert_not_called()  # WHY: no upgrade may receive a missing specification.

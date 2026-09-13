"""Isolated-venv guard unit tests (feature 1020, User Story 2).

Verifies that ``DependencyCheckOrchestrator`` refuses to auto-install/upgrade
packages into a non-isolated (system) Python interpreter by default, while
preserving existing behavior inside a genuine virtual environment and honoring
an explicit operator override. All interpreter state is dependency-injected as a
fake ``sys`` namespace — no real package installs, no subprocess, no network.
See ``specs/1020-safe-test-clean-run/contracts/preflight_failure_contract.md``.
"""

from __future__ import annotations

import types
from unittest.mock import MagicMock

from src.bootstrap.dependency_check import DependencyCheckOrchestrator
from src.bootstrap.package_installer import PackageInstaller

_UNSET = object()  # WHY: sentinel so a fake sys with NO real_prefix attribute differs from real_prefix=None.


def _fake_sys(prefix, base_prefix, real_prefix=_UNSET):
    """Build a fake ``sys`` namespace with controlled prefix/base_prefix/real_prefix."""
    fake = types.SimpleNamespace(prefix=prefix, base_prefix=base_prefix)  # WHY: plain object, no auto-attrs.
    if real_prefix is not _UNSET:  # WHY: only legacy-virtualenv cases set real_prefix at all.
        fake.real_prefix = real_prefix
    return fake


def _build_orchestrator(*, sys_module, env=None, requirements=None):
    """Assemble an orchestrator with a fake interpreter, env, and a spy installer."""
    env = env or {}
    os_module = MagicMock()  # WHY: env lookups routed through injected os for deterministic control.
    os_module.getenv.side_effect = lambda key, default="": env.get(key, default)  # WHY: table-driven env.
    logging_module = MagicMock()  # WHY: capture warning/debug calls without emitting real logs.
    installer = MagicMock(spec=PackageInstaller)  # WHY: spy install calls; never touches real packages.
    installer.find_uv_executable.return_value = (None, None)  # WHY: force pip fallback path deterministically.
    installer.install_uv_with_pip.return_value = False  # WHY: no UV bootstrap in tests.
    installer.install_with_uv.return_value = False  # WHY: UV route disabled.
    installer.install_with_pip.return_value = True  # WHY: pretend pip install succeeds when it runs.
    if requirements is None:  # WHY: default to one missing package so install would fire if permitted.
        requirements = [("pkg-one", "pkg-one>=1.0")]
    orchestrator = DependencyCheckOrchestrator(
        os_module=os_module,
        logging_module=logging_module,
        sys_module=sys_module,
        package_import_map={},
        parse_requirements_file_fn=lambda: requirements,
        get_installed_version_fn=lambda _name: "",  # WHY: empty -> package treated as missing (needs install).
        version_satisfies_fn=lambda _installed, _spec: False,
        get_latest_pypi_version_fn=lambda _name: "",
        parse_version_fn=lambda _value: (0,),
        installer=installer,
    )
    return orchestrator, installer, logging_module


class TestIsolatedVenvPredicate:
    """Unit tests for the _is_running_in_isolated_venv() predicate."""

    def test_system_python_is_not_isolated(self):
        """prefix == base_prefix and no real_prefix -> not isolated (system Python)."""
        orchestrator, _installer, _log = _build_orchestrator(sys_module=_fake_sys("/usr", "/usr"))
        assert orchestrator._is_running_in_isolated_venv() is False

    def test_modern_venv_is_isolated(self):
        """prefix != base_prefix -> isolated (PEP 405 venv)."""
        orchestrator, _installer, _log = _build_orchestrator(sys_module=_fake_sys("/proj/.venv", "/usr"))
        assert orchestrator._is_running_in_isolated_venv() is True

    def test_legacy_virtualenv_real_prefix_is_isolated(self):
        """prefix == base_prefix but real_prefix set -> isolated (legacy virtualenv)."""
        orchestrator, _installer, _log = _build_orchestrator(sys_module=_fake_sys("/usr", "/usr", real_prefix="/orig"))
        assert orchestrator._is_running_in_isolated_venv() is True


class TestVenvGuardRunBehavior:
    """Integration of the predicate into run()'s install/upgrade short-circuit."""

    def test_non_isolated_blocks_install_without_override(self):
        """Non-isolated interpreter + no override -> zero install/upgrade calls."""
        orchestrator, installer, _log = _build_orchestrator(sys_module=_fake_sys("/usr", "/usr"))
        orchestrator.run()
        installer.install_with_pip.assert_not_called()
        installer.install_with_uv.assert_not_called()

    def test_isolated_venv_preserves_install_behavior(self):
        """Genuine isolated venv -> missing packages are still installed (no regression, FR-011)."""
        orchestrator, installer, _log = _build_orchestrator(sys_module=_fake_sys("/proj/.venv", "/usr"))
        orchestrator.run()
        installer.install_with_pip.assert_called()

    def test_isolated_venv_preserves_upgrade_behavior(self):
        """Genuine isolated venv -> outdated packages are still upgraded (no regression, FR-011)."""
        orchestrator, installer, _log = _build_orchestrator(
            sys_module=_fake_sys("/proj/.venv", "/usr"),
            requirements=[("pkg-two", "pkg-two>=2.0")],
        )
        # Make pkg-two importable + installed-but-outdated so it routes to the upgrade path.
        orchestrator._is_importable = lambda _name: True  # type: ignore[assignment]
        orchestrator.get_installed_version_fn = lambda _name: "1.0"  # type: ignore[assignment]
        orchestrator.run()
        installer.install_with_pip.assert_called()  # WHY: pip fallback upgrade fired for the outdated pkg.

    def test_override_allows_system_python_install_with_loud_warning(self):
        """Non-isolated + MISTHELPER_ALLOW_SYSTEM_PYTHON_INSTALL=true -> install proceeds with a loud warning."""
        orchestrator, installer, logging_module = _build_orchestrator(
            sys_module=_fake_sys("/usr", "/usr"),
            env={"MISTHELPER_ALLOW_SYSTEM_PYTHON_INSTALL": "true"},
        )
        orchestrator.run()
        installer.install_with_pip.assert_called()
        warnings = " ".join(str(call.args) for call in logging_module.warning.call_args_list)
        assert "MISTHELPER_ALLOW_SYSTEM_PYTHON_INSTALL" in warnings, "override path must log a loud warning"

    def test_no_venv_message_when_virtual_env_unset(self):
        """Blocked with VIRTUAL_ENV unset -> diagnostic says no venv was created/activated."""
        orchestrator, _installer, logging_module = _build_orchestrator(sys_module=_fake_sys("/usr", "/usr"))
        orchestrator.run()
        messages = " ".join(str(call.args) for call in logging_module.warning.call_args_list).lower()
        assert "no virtual environment" in messages or "no .venv" in messages

    def test_broken_venv_message_when_virtual_env_set(self):
        """Blocked with VIRTUAL_ENV set but not isolated -> diagnostic says the launcher looks broken."""
        orchestrator, _installer, logging_module = _build_orchestrator(
            sys_module=_fake_sys("/usr", "/usr"),
            env={"VIRTUAL_ENV": "/proj/.venv"},
        )
        orchestrator.run()
        messages = " ".join(str(call.args) for call in logging_module.warning.call_args_list).lower()
        assert "launcher" in messages or "broken" in messages or "repair" in messages

    def test_disable_auto_install_and_non_isolated_block_without_duplicate_messages(self):
        """DISABLE_AUTO_INSTALL=true short-circuits first: block with only the disabled debug log, no venv warning."""
        orchestrator, installer, logging_module = _build_orchestrator(
            sys_module=_fake_sys("/usr", "/usr"),
            env={"DISABLE_AUTO_INSTALL": "true"},
        )
        orchestrator.run()
        installer.install_with_pip.assert_not_called()
        logging_module.warning.assert_not_called()  # WHY: no conflicting/duplicate venv-guard message.

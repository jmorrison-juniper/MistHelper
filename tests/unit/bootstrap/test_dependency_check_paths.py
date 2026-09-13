"""Wave 6 P2 coverage for ``src.bootstrap.dependency_check.DependencyCheckOrchestrator``.

The existing ``tests/unit/test_dependency_check.py`` covers only the
``DISABLE_AUTO_INSTALL`` short-circuit and the basic pip-install path. This
file adds targeted coverage for:

- Empty requirements -> warning log + early return.
- All-up-to-date -> debug log + early return.
- Version-spec violation triggers upgrade path.
- ``auto_upgrade=True`` + newer PyPI version triggers upgrade path.
- Package-import-map opt-out (empty import name).
- UV first-pass found -> install_with_uv used.
- UV missing then pip-bootstrap succeeds -> UV re-verified.
- UV missing, pip-bootstrap succeeds but re-check still fails -> pip-only.
- ``_newer_available`` returns False when latest lookup empty.
- ``_log_install_result`` and ``_log_upgrade_result`` failure paths.

All collaborators are ``MagicMock`` doubles; no filesystem or subprocess.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.10+.

from typing import Any  # WHY: Any typing mirrors SUT signature.
from unittest.mock import MagicMock  # WHY: Mandatory spec-based mocks per project policy.

import pytest  # WHY: monkeypatch fixture avoids direct method assignment on the instance.

from src.bootstrap.dependency_check import DependencyCheckOrchestrator, _InstallContext
from src.bootstrap.package_installer import PackageInstaller  # WHY: spec anchor for installer.


def _build(
    *,
    monkeypatch: pytest.MonkeyPatch,
    requirements: list[tuple[str, str]],
    installed_versions: dict[str, str] | None = None,
    latest_versions: dict[str, str] | None = None,
    version_satisfies: dict[tuple[str, str], bool] | None = None,
    auto_upgrade: bool = False,
    disabled: bool = False,
    package_import_map: dict[str, str] | None = None,
    uv_cmd_first: tuple[Any, Any] = (None, None),
    uv_cmd_second: tuple[Any, Any] = (None, None),
    install_uv_ok: bool = False,
    install_with_uv_ok: bool = False,
    install_with_pip_ok: bool = True,
    importable: set[str] | None = None,
    patch_is_importable: bool = True,
) -> tuple[DependencyCheckOrchestrator, MagicMock, MagicMock]:
    """Compose an orchestrator with fully-injected doubles suitable for branch tests.

    Returns (orchestrator, installer_mock, logging_mock) so test bodies can
    assert against installer + logging calls directly. The ``_is_importable``
    method is patched at the class level via ``monkeypatch`` (auto-restored
    at test teardown) unless ``patch_is_importable=False`` is passed.
    """
    # WHY: single builder keeps the test file compact yet flexible.
    installed_versions = installed_versions or {}  # Default no installed versions known.
    latest_versions = latest_versions or {}  # Default no PyPI info.
    version_satisfies = version_satisfies or {}  # Default no satisfaction knowledge.
    package_import_map = package_import_map or {}  # Default no name remap.
    resolved_importable = importable if importable is not None else set()  # Default all imports fail.

    os_module = MagicMock(name="os_module")  # Env access double.

    # Configure getenv to reflect disabled / auto_upgrade flags.
    def _getenv(key: str, default: str = "") -> str:
        if key == "DISABLE_AUTO_INSTALL":  # WHY: gate the top-level short-circuit branch.
            return "true" if disabled else "false"
        if key == "AUTO_UPGRADE_TO_LATEST":  # WHY: gate the auto_upgrade branch inside _check_installed.
            return "true" if auto_upgrade else "false"
        if key == "AUTO_UPGRADE_DEPENDENCIES":  # WHY: alternative env-var name for the same knob.
            return "true" if auto_upgrade else "false"
        return default  # WHY: fall through to caller default.

    os_module.getenv.side_effect = _getenv  # Wire env resolution.

    logging_module = MagicMock(name="logging_module")  # Structured log capture.
    sys_module = MagicMock(name="sys_module")  # Interpreter introspection stub.

    installer = MagicMock(spec=PackageInstaller)  # Mandatory spec-based mock.
    installer.find_uv_executable.side_effect = [uv_cmd_first, uv_cmd_second]  # Two-pass UV probe.
    installer.install_uv_with_pip.return_value = install_uv_ok  # Bootstrap outcome.
    installer.install_with_uv.return_value = install_with_uv_ok  # UV install outcome.
    installer.install_with_pip.return_value = install_with_pip_ok  # pip fallback outcome.

    orchestrator = DependencyCheckOrchestrator(
        os_module=os_module,  # Env access double.
        logging_module=logging_module,  # Structured log capture.
        sys_module=sys_module,  # Interpreter introspection stub.
        package_import_map=package_import_map,  # Optional import remap.
        parse_requirements_file_fn=lambda: requirements,  # Deterministic requirements list.
        get_installed_version_fn=lambda name: installed_versions.get(name, ""),  # Dict-backed lookup.
        version_satisfies_fn=lambda installed, spec: version_satisfies.get(
            (installed, spec), True
        ),  # Dict-backed satisfaction with default True.
        get_latest_pypi_version_fn=lambda name: latest_versions.get(name, ""),  # PyPI info.
        parse_version_fn=lambda v: tuple(int(p) for p in v.split(".") if p.isdigit()) or (0,),  # Cheap tuple parse.
        installer=installer,  # Spec-anchored installer double.
    )

    if patch_is_importable:  # WHY: TestIsImportable exercises the REAL implementation.
        # Patch _is_importable at the class level via monkeypatch (auto-undo at teardown).
        monkeypatch.setattr(  # WHY: monkeypatch is the sanctioned way to swap methods without ignores.
            DependencyCheckOrchestrator,
            "_is_importable",
            lambda self, name: name in resolved_importable,  # Closure over resolved set.
        )
    return orchestrator, installer, logging_module  # Return the wired triple for test bodies.


class TestEarlyReturns:
    """Cover the disabled / empty-reqs / all-ok early-return branches."""

    def test_disabled_short_circuits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """DISABLE_AUTO_INSTALL=true logs debug + returns without calling parse."""
        # WHY: covers _is_auto_install_disabled True branch (line 63-64).
        orchestrator, installer, logging_module = _build(monkeypatch=monkeypatch, requirements=[], disabled=True)
        orchestrator.run()  # Trigger.
        installer.find_uv_executable.assert_not_called()  # UV probe never reached.
        logging_module.debug.assert_called()  # Debug log emitted.

    def test_empty_requirements_warns_and_returns(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Empty requirements triggers warning + early return."""
        # WHY: covers the `if not all_packages` branch (line 66-68).
        orchestrator, installer, logging_module = _build(monkeypatch=monkeypatch, requirements=[])
        orchestrator.run()  # Trigger.
        installer.install_with_pip.assert_not_called()  # No install work.
        logging_module.warning.assert_called()  # Warning log emitted.

    def test_all_up_to_date_debug_logs_and_returns(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When nothing is missing/outdated, run() logs debug + returns."""
        # WHY: covers the `if not missing and not outdated` branch (line 70-72).
        orchestrator, installer, logging_module = _build(
            monkeypatch=monkeypatch,
            requirements=[("pkg-a", "pkg-a>=1.0")],
            installed_versions={"pkg-a": "1.5"},
            version_satisfies={("1.5", "pkg-a>=1.0"): True},
            importable={"pkg-a"},  # Present -> not missing.
        )
        orchestrator.run()  # Trigger.
        installer.find_uv_executable.assert_not_called()  # UV probe skipped.
        installer.install_with_pip.assert_not_called()  # No install.
        # Debug log should be emitted for the all-ok message.
        assert any(
            "up-to-date" in (str(call.args[0]) if call.args else "") for call in logging_module.debug.call_args_list
        )  # WHY: assert the specific info message surfaces.


class TestPackageImportMap:
    """Cover ``_classify_one``'s import-name resolution + opt-out branch."""

    def test_empty_import_name_opts_out(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A mapped import name of '' skips the package entirely."""
        # WHY: covers the `if not import_name` opt-out branch (line 110-111).
        orchestrator, installer, _ = _build(
            monkeypatch=monkeypatch,
            requirements=[("some-pkg", "some-pkg>=1.0")],
            package_import_map={"some-pkg": ""},  # Explicit opt-out.
        )
        orchestrator.run()  # Trigger.
        installer.install_with_pip.assert_not_called()  # Package skipped -> no install path.


class TestUpgradePath:
    """Cover the outdated bucket + upgrade loop."""

    def test_spec_violation_triggers_pip_upgrade(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When version_satisfies returns False, the package is queued for upgrade."""
        # WHY: covers _check_installed constraint-violation branch (line 136-138) + upgrade loop.
        orchestrator, installer, logging_module = _build(
            monkeypatch=monkeypatch,
            requirements=[("pkg-b", "pkg-b>=2.0")],
            installed_versions={"pkg-b": "1.0"},
            version_satisfies={("1.0", "pkg-b>=2.0"): False},  # Violation.
            importable={"pkg-b"},
            install_with_pip_ok=True,
        )
        orchestrator.run()  # Trigger.
        installer.install_with_pip.assert_called_with("pkg-b>=2.0", upgrade=True)  # Upgrade call.
        # Success upgrade log emitted.
        assert any(
            "Successfully upgraded" in str(call.args[0]) for call in logging_module.info.call_args_list if call.args
        )  # WHY: verifies the success-log branch fired.

    def test_auto_upgrade_newer_pypi_triggers_upgrade(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """auto_upgrade True + newer PyPI queues the package for upgrade."""
        # WHY: covers _check_installed auto_upgrade True path + _newer_available True path.
        orchestrator, installer, _ = _build(
            monkeypatch=monkeypatch,
            requirements=[("pkg-c", "pkg-c>=1.0")],
            installed_versions={"pkg-c": "1.0"},
            latest_versions={"pkg-c": "2.0"},  # Newer available.
            version_satisfies={("1.0", "pkg-c>=1.0"): True},  # Spec satisfied.
            auto_upgrade=True,  # Enable latest check.
            importable={"pkg-c"},
        )
        orchestrator.run()  # Trigger.
        installer.install_with_pip.assert_called_with("pkg-c>=1.0", upgrade=True)  # Upgrade attempted.

    def test_auto_upgrade_no_latest_info_no_upgrade(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """_newer_available returns False when latest lookup empty -> no upgrade."""
        # WHY: covers _newer_available `if not latest` branch (line 145-146).
        orchestrator, installer, _ = _build(
            monkeypatch=monkeypatch,
            requirements=[("pkg-d", "pkg-d>=1.0")],
            installed_versions={"pkg-d": "1.0"},
            latest_versions={},  # Empty -> no signal.
            version_satisfies={("1.0", "pkg-d>=1.0"): True},
            auto_upgrade=True,
            importable={"pkg-d"},
        )
        orchestrator.run()  # Trigger.
        installer.install_with_pip.assert_not_called()  # No upgrade queued.

    def test_upgrade_failure_logs_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """pip upgrade failure emits error via _log_upgrade_result."""
        # WHY: covers _log_upgrade_result False branch (line 251).
        orchestrator, installer, logging_module = _build(
            monkeypatch=monkeypatch,
            requirements=[("pkg-e", "pkg-e>=2.0")],
            installed_versions={"pkg-e": "1.0"},
            version_satisfies={("1.0", "pkg-e>=2.0"): False},
            importable={"pkg-e"},
            install_with_pip_ok=False,  # Force failure.
        )
        orchestrator.run()  # Trigger.
        logging_module.error.assert_called()  # Error log emitted.


class TestInstallResultLogging:
    """Cover both branches of ``_log_install_result``."""

    def test_install_failure_logs_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """pip install failure emits error via _log_install_result."""
        # WHY: covers _log_install_result False branch (line 203).
        orchestrator, installer, logging_module = _build(
            monkeypatch=monkeypatch,
            requirements=[("pkg-f", "pkg-f>=1.0")],
            install_with_pip_ok=False,  # Force failure.
        )
        orchestrator.run()  # Trigger.
        logging_module.error.assert_called()  # Error log emitted.


class TestUvBootstrap:
    """Cover the three ``_prepare_installer`` outcomes."""

    def test_uv_found_first_pass(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """UV found on the first probe -> use_uv=True, no bootstrap attempted."""
        # WHY: covers _prepare_installer if uv_cmd True branch (line 152-154) + _try_uv_install path.
        orchestrator, installer, _ = _build(
            monkeypatch=monkeypatch,
            requirements=[("pkg-g", "pkg-g>=1.0")],
            uv_cmd_first=(["uv"], "0.1"),  # First probe returns valid UV.
            install_with_uv_ok=True,  # UV install succeeds.
        )
        orchestrator.run()  # Trigger.
        installer.install_with_uv.assert_called_with(["uv"], "pkg-g>=1.0", upgrade=False)  # UV used.
        installer.install_uv_with_pip.assert_not_called()  # Bootstrap skipped.

    def test_uv_missing_bootstrap_succeeds_reverify_ok(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """UV missing, pip bootstrap succeeds, re-verify finds UV -> use_uv=True."""
        # WHY: covers _bootstrap_uv_via_pip success path (line 163-167).
        orchestrator, installer, _logging_module = _build(
            monkeypatch=monkeypatch,
            requirements=[("pkg-h", "pkg-h>=1.0")],
            uv_cmd_first=(None, None),  # First probe fails.
            uv_cmd_second=(["uv"], "0.2"),  # Re-verify succeeds.
            install_uv_ok=True,  # Bootstrap succeeds.
            install_with_uv_ok=True,  # UV install succeeds.
        )
        orchestrator.run()  # Trigger.
        installer.install_uv_with_pip.assert_called_once()  # Bootstrap invoked.
        installer.install_with_uv.assert_called()  # UV path used post-bootstrap.

    def test_uv_missing_bootstrap_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """UV missing + bootstrap fails -> use_uv=False, pip fallback used."""
        # WHY: covers _bootstrap_uv_via_pip if not install_uv_with_pip branch (line 161-162).
        orchestrator, installer, _ = _build(
            monkeypatch=monkeypatch,
            requirements=[("pkg-i", "pkg-i>=1.0")],
            install_uv_ok=False,  # Bootstrap fails.
        )
        orchestrator.run()  # Trigger.
        installer.install_uv_with_pip.assert_called_once()  # Bootstrap attempted.
        installer.install_with_uv.assert_not_called()  # UV never used.
        installer.install_with_pip.assert_called()  # pip fallback used.

    def test_uv_missing_bootstrap_succeeds_reverify_still_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Bootstrap succeeds but re-verify still returns no UV -> pip-only."""
        # WHY: covers _bootstrap_uv_via_pip if not uv_cmd branch (line 164-165).
        orchestrator, installer, _ = _build(
            monkeypatch=monkeypatch,
            requirements=[("pkg-j", "pkg-j>=1.0")],
            uv_cmd_first=(None, None),
            uv_cmd_second=(None, None),  # Re-verify still fails.
            install_uv_ok=True,  # Bootstrap "succeeds" but binary not present.
        )
        orchestrator.run()  # Trigger.
        installer.install_with_uv.assert_not_called()  # UV path never engaged.
        installer.install_with_pip.assert_called()  # pip fallback used.


class TestTryUvGuards:
    """Directly exercise the defensive guards in ``_try_uv_install`` / ``_try_uv_upgrade``."""

    def test_try_uv_install_returns_false_when_uv_cmd_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """use_uv=True but uv_cmd=None -> defensive guard returns False."""
        # WHY: covers the `if not context.uv_cmd` defensive branch (line 193-194).
        orchestrator, installer, _ = _build(monkeypatch=monkeypatch, requirements=[])
        ctx = _InstallContext(use_uv=True, uv_cmd=None)  # Contradictory but explicitly guarded.
        assert orchestrator._try_uv_install("pkg", ctx) is False  # Falls back.
        installer.install_with_uv.assert_not_called()  # UV never invoked.

    def test_try_uv_upgrade_returns_false_when_uv_cmd_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """use_uv=True but uv_cmd=None on upgrade path -> defensive guard returns False."""
        # WHY: covers the `if not context.uv_cmd` defensive branch (line 241-242).
        orchestrator, installer, _ = _build(monkeypatch=monkeypatch, requirements=[])
        ctx = _InstallContext(use_uv=True, uv_cmd=None)  # Contradictory but explicitly guarded.
        assert orchestrator._try_uv_upgrade("pkg", "pkg>=1", "0.9", ctx) is False  # Falls back.
        installer.install_with_uv.assert_not_called()  # UV never invoked.


class TestIsImportable:
    """Exercise the real ``_is_importable`` implementation (skip the fixture patch)."""

    def test_missing_module_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A definitely-missing module name returns False without raising."""
        # WHY: covers _is_importable ImportError branch (line 121-122).
        orchestrator, _installer, _log = _build(monkeypatch=monkeypatch, requirements=[], patch_is_importable=False)
        assert (
            orchestrator._is_importable("definitely_not_a_real_module_xyz_1018_wave6") is False
        )  # ImportError caught.

    def test_present_module_returns_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A stdlib module returns True."""
        # WHY: covers _is_importable success branch (line 123).
        orchestrator, _installer, _log = _build(monkeypatch=monkeypatch, requirements=[], patch_is_importable=False)
        assert orchestrator._is_importable("json") is True  # stdlib always importable.

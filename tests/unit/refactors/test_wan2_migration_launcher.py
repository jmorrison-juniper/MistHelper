"""Wave 4 P2 coverage for src/refactors/wan2_migration_launcher.py (initiative #1018).

Covers `WAN2MigrationLauncher` construction plus every helper method and every
branch of `launch()` (happy path, exception path via _handle_fatal_error).
MistHelper module attributes are monkeypatched with MagicMock doubles, and
`configure_wan2_migration_dependencies` / `WAN2MigrationManager` /
`WAN2MigrationDependencies` inside `src.gateway.wan2_migration_manager` are
monkeypatched so no real gateway module executes. No source edits, no live I/O.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.10+.

import logging  # WHY: verify structured logs emitted at launch/wire/build stages.
from typing import Any  # WHY: dict-of-mocks return-type annotation.
from unittest.mock import MagicMock  # WHY: FR-008 mandates MagicMock(spec=...) doubles.

import pytest  # WHY: monkeypatch/capsys/caplog fixtures.

from src.refactors.wan2_migration_launcher import (  # WHY: SUT + helper direct imports.
    WAN2MigrationLauncher,
    _resolve_runtime_dependencies,
)


@pytest.fixture
def wired_deps(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Wire all MistHelper attributes + wan2_migration_manager module entry points."""
    mistapi_mock = MagicMock(name="mistapi_module")  # WHY: attribute access on MistHelper.
    config_utils_mock = MagicMock(name="ConfigUtils")  # WHY: class handle.
    cache_utils_mock = MagicMock(name="CacheUtils")  # WHY: class handle.
    org_site_exporter_mock = MagicMock(name="OrgSiteExporter")  # WHY: class handle.
    gateway_export_utils_mock = MagicMock(name="GatewayExportUtils")  # WHY: class handle.
    file_path_utils_mock = MagicMock(name="FilePathUtils")  # WHY: class handle.
    input_utils_mock = MagicMock(name="InputUtils")  # WHY: class handle.
    data_exporter_mock = MagicMock(name="DataExporter")  # WHY: class handle.
    apisession_sentinel = MagicMock(name="apisession_sentinel")  # WHY: current session handle.

    for attr_name, mock_obj in (  # WHY: publish attributes on MistHelper so proxy lookup finds them.
        ("apisession", apisession_sentinel),
        ("mistapi", mistapi_mock),
        ("ConfigUtils", config_utils_mock),
        ("CacheUtils", cache_utils_mock),
        ("OrgSiteExporter", org_site_exporter_mock),
        ("GatewayExportUtils", gateway_export_utils_mock),
        ("FilePathUtils", file_path_utils_mock),
        ("InputUtils", input_utils_mock),
        ("DataExporter", data_exporter_mock),
    ):
        monkeypatch.setattr(
            f"MistHelper.{attr_name}", mock_obj, raising=False
        )  # WHY: proxy lookup is call-time; publish attributes.

    configure_mock = MagicMock(name="configure_wan2_migration_dependencies")  # WHY: intercept wire call.
    monkeypatch.setattr(
        "src.gateway.wan2_migration_manager.configure_wan2_migration_dependencies",
        configure_mock,
    )  # WHY: patch actual module attribute so lazy `from ... import` sees the mock.

    # WHY: WAN2MigrationDependencies is a frozen dataclass; wrap with a MagicMock that echoes kwargs.
    deps_class_mock = MagicMock(name="WAN2MigrationDependencies_class")  # WHY: constructor class handle.
    monkeypatch.setattr(
        "src.gateway.wan2_migration_manager.WAN2MigrationDependencies", deps_class_mock
    )  # WHY: swap dataclass with MagicMock so we can inspect kwargs it was called with.

    manager_instance = MagicMock(name="WAN2MigrationManager_instance")  # WHY: instance returned by class call.
    manager_class_mock = MagicMock(
        name="WAN2MigrationManager_class", return_value=manager_instance
    )  # WHY: class handle.
    monkeypatch.setattr(
        "src.gateway.wan2_migration_manager.WAN2MigrationManager", manager_class_mock
    )  # WHY: swap class in target module so _build_manager instantiates our mock.

    return {  # WHY: expose everything needed for post-condition assertions.
        "apisession": apisession_sentinel,
        "mistapi": mistapi_mock,
        "ConfigUtils": config_utils_mock,
        "CacheUtils": cache_utils_mock,
        "OrgSiteExporter": org_site_exporter_mock,
        "GatewayExportUtils": gateway_export_utils_mock,
        "FilePathUtils": file_path_utils_mock,
        "InputUtils": input_utils_mock,
        "DataExporter": data_exporter_mock,
        "configure": configure_mock,
        "deps_class": deps_class_mock,
        "manager_class": manager_class_mock,
        "manager_instance": manager_instance,
    }


class TestResolveRuntimeDependencies:
    """`_resolve_runtime_dependencies` bundles the MistHelper module handle."""

    def test_returns_bundle_with_misthelper_module(self) -> None:
        """The returned SimpleNamespace exposes the live MistHelper module."""
        deps = _resolve_runtime_dependencies()  # WHY: exercise helper directly.
        assert deps.misthelper_module is not None  # WHY: module resolved.
        assert deps.misthelper_module.__name__ == "MistHelper"  # WHY: identity by module name.


class TestWAN2MigrationLauncherInit:
    """Constructor stores late-bound dependencies."""

    def test_init_resolves_runtime_dependencies(self) -> None:
        """__init__ populates `_deps.misthelper_module` via the resolver."""
        launcher = WAN2MigrationLauncher()  # WHY: exercise construction.
        assert launcher._deps.misthelper_module.__name__ == "MistHelper"  # WHY: name check.

    def test_misthelper_returns_module_handle(self) -> None:
        """`_misthelper()` returns the same module handle stored during init."""
        launcher = WAN2MigrationLauncher()  # WHY: build instance.
        assert launcher._misthelper() is launcher._deps.misthelper_module  # WHY: identity passthrough.


class TestLaunchHappyPath:
    """`launch()` orchestrates wire → build → execute in order."""

    def test_launch_wires_builds_and_executes(
        self, wired_deps: dict[str, Any], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Happy-path launch calls configure, WAN2MigrationManager(), manager.set_site_variable()."""
        launcher = WAN2MigrationLauncher()  # WHY: build launcher after wiring in place.
        with caplog.at_level(logging.INFO):  # WHY: capture launch banner + wire/build info logs.
            launcher.launch()  # WHY: exercise full pipeline.

        assert wired_deps["configure"].call_count == 1  # WHY: wire step invoked exactly once.
        assert wired_deps["deps_class"].call_count == 1  # WHY: WAN2MigrationDependencies constructed once.
        deps_kwargs = wired_deps["deps_class"].call_args.kwargs  # WHY: inspect dataclass constructor kwargs.
        assert deps_kwargs["apisession"] is wired_deps["apisession"]  # WHY: apisession threaded through.
        assert deps_kwargs["config_utils"] is wired_deps["ConfigUtils"]  # WHY: config utils threaded through.
        assert deps_kwargs["cache_utils"] is wired_deps["CacheUtils"]  # WHY: cache utils threaded through.
        assert deps_kwargs["org_site_exporter"] is wired_deps["OrgSiteExporter"]  # WHY: exporter threaded.
        assert deps_kwargs["gateway_export_utils"] is wired_deps["GatewayExportUtils"]  # WHY: gateway utils.
        assert deps_kwargs["file_path_utils"] is wired_deps["FilePathUtils"]  # WHY: file path utils.
        assert deps_kwargs["input_utils"] is wired_deps["InputUtils"]  # WHY: input utils.
        assert deps_kwargs["data_exporter"] is wired_deps["DataExporter"]  # WHY: data exporter.
        assert deps_kwargs["mistapi"] is wired_deps["mistapi"]  # WHY: mistapi threaded through.
        assert isinstance(deps_kwargs["site_exclude_prefix"], str)  # WHY: MIST_SITE_EXCLUDE_PREFIX is str.

        assert wired_deps["manager_class"].call_count == 1  # WHY: manager instantiated exactly once.
        assert wired_deps["manager_instance"].set_site_variable.call_count == 1  # WHY: flow method invoked.
        assert "Menu #149: Starting WAN2 Migration" in caplog.text  # WHY: launch banner logged.

    def test_launch_missing_apisession_uses_none(
        self, wired_deps: dict[str, Any], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When apisession is absent on MistHelper, the deps dataclass receives None (getattr default)."""
        monkeypatch.delattr("MistHelper.apisession", raising=False)  # WHY: force getattr fallback branch.
        launcher = WAN2MigrationLauncher()  # WHY: build launcher post-delete.
        launcher.launch()  # WHY: exercise wire with missing apisession.
        assert wired_deps["deps_class"].call_args.kwargs["apisession"] is None  # WHY: fallback returns None.


class TestLaunchFatalError:
    """`launch()` funnels any exception through `_handle_fatal_error`."""

    def test_launch_wire_failure_logs_and_prints(
        self,
        wired_deps: dict[str, Any],
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """When configure_wan2_migration_dependencies raises, error is logged + printed, no crash."""
        wired_deps["configure"].side_effect = RuntimeError("wire boom")  # WHY: raise during wire step.
        launcher = WAN2MigrationLauncher()  # WHY: build launcher.
        with caplog.at_level(logging.ERROR):  # WHY: fatal path logs at ERROR.
            launcher.launch()  # WHY: exercise exception branch; must not re-raise.
        captured = capsys.readouterr()  # WHY: read printed error.
        assert "ERROR: wire boom" in captured.out  # WHY: user-visible error printed.
        assert "Error running WAN2 Migration" in caplog.text  # WHY: structured error log emitted.
        assert wired_deps["manager_class"].call_count == 0  # WHY: manager never built when wire fails.

    def test_launch_execute_failure_logs_and_prints(
        self,
        wired_deps: dict[str, Any],
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """When manager.set_site_variable() raises, the error surfaces via _handle_fatal_error."""
        wired_deps["manager_instance"].set_site_variable.side_effect = RuntimeError(
            "flow boom"
        )  # WHY: raise on execute.
        launcher = WAN2MigrationLauncher()  # WHY: build launcher.
        with caplog.at_level(logging.ERROR):  # WHY: capture the ERROR log.
            launcher.launch()  # WHY: exercise post-build exception branch.
        captured = capsys.readouterr()  # WHY: capture printed banner.
        assert "ERROR: flow boom" in captured.out  # WHY: user-visible error present.
        assert "Error running WAN2 Migration" in caplog.text  # WHY: structured error log emitted.


class TestHandleFatalError:
    """`_handle_fatal_error` prints and logs directly (unit level)."""

    def test_prints_and_logs(self, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture) -> None:
        """Direct call prints and logs without invoking sys.exit."""
        launcher = WAN2MigrationLauncher()  # WHY: build instance to reach the method.
        error = ValueError("boom-direct")  # WHY: sentinel error we can grep for.
        with caplog.at_level(logging.ERROR):  # WHY: assert on the ERROR log entry.
            launcher._handle_fatal_error(error)  # WHY: direct-call exercises the branch.
        captured = capsys.readouterr()  # WHY: capture print output.
        assert "ERROR: boom-direct" in captured.out  # WHY: printed banner content.
        assert "Error running WAN2 Migration" in caplog.text  # WHY: log entry present.

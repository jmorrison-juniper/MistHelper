"""Wave 4 P2 coverage for src/refactors/service_ping_launcher.py (initiative #1018).

Covers `ServicePingLauncher` construction plus every helper method and every
branch of `launch()` (happy path, exception path via _handle_fatal_error).
MistHelper module attributes are monkeypatched with MagicMock doubles, and
`configure_service_ping_manager_dependencies` / `ServicePingManager` inside
`src.websocket.service_ping_manager` are monkeypatched so no real WebSocket
transport or MistHelper import chain executes. No source edits, no live I/O.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.10+.

import logging  # WHY: verify structured logs emitted at launch/wire/build stages.
from typing import Any  # WHY: dict-of-mocks return-type annotation.
from unittest.mock import MagicMock  # WHY: FR-008 mandates MagicMock(spec=...) doubles.

import pytest  # WHY: monkeypatch/caplog fixtures.

from src.refactors.service_ping_launcher import (  # WHY: SUT + helper direct imports.
    ServicePingLauncher,
    _resolve_runtime_dependencies,
)


@pytest.fixture
def wired_deps(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Wire all MistHelper attributes + service_ping_manager module entry points."""
    mistapi_mock = MagicMock(name="mistapi_module")  # WHY: MistHelper.mistapi is used as attribute access.
    prompt_utils_mock = MagicMock(name="PromptUtils")  # WHY: class handle, not instance.
    input_utils_mock = MagicMock(name="InputUtils")  # WHY: class handle.
    websocket_manager_class = MagicMock(name="WebSocketManager")  # WHY: constructor class handle.
    api_tenant_fetch_utils_mock = MagicMock(name="APITenantFetchUtils")  # WHY: class handle.
    config_utils_mock = MagicMock(name="ConfigUtils")  # WHY: class handle.
    api_fetch_utils_mock = MagicMock(name="APIFetchUtils")  # WHY: class handle.
    apisession_sentinel = MagicMock(name="apisession_sentinel")  # WHY: current session handle.

    for attr_name, mock_obj in (  # WHY: publish attributes on MistHelper so proxy lookup finds them.
        ("apisession", apisession_sentinel),
        ("mistapi", mistapi_mock),
        ("PromptUtils", prompt_utils_mock),
        ("InputUtils", input_utils_mock),
        ("WebSocketManager", websocket_manager_class),
        ("APITenantFetchUtils", api_tenant_fetch_utils_mock),
        ("ConfigUtils", config_utils_mock),
        ("APIFetchUtils", api_fetch_utils_mock),
    ):
        monkeypatch.setattr(
            f"MistHelper.{attr_name}", mock_obj, raising=False
        )  # WHY: proxy lookup is call-time; publish attributes.

    configure_mock = MagicMock(name="configure_service_ping_manager_dependencies")  # WHY: intercept wire call.
    monkeypatch.setattr(
        "src.websocket.service_ping_manager.configure_service_ping_manager_dependencies",
        configure_mock,
    )  # WHY: patch the actual module attribute so lazy `from ... import` sees the mock.

    manager_instance = MagicMock(name="ServicePingManager_instance")  # WHY: instance returned by class call.
    manager_class_mock = MagicMock(name="ServicePingManager_class", return_value=manager_instance)  # WHY: class handle.
    monkeypatch.setattr(
        "src.websocket.service_ping_manager.ServicePingManager", manager_class_mock
    )  # WHY: swap class in target module so build_manager instantiates our mock.

    return {  # WHY: expose everything needed for post-condition assertions.
        "apisession": apisession_sentinel,
        "mistapi": mistapi_mock,
        "PromptUtils": prompt_utils_mock,
        "InputUtils": input_utils_mock,
        "WebSocketManager": websocket_manager_class,
        "APITenantFetchUtils": api_tenant_fetch_utils_mock,
        "ConfigUtils": config_utils_mock,
        "APIFetchUtils": api_fetch_utils_mock,
        "configure": configure_mock,
        "manager_class": manager_class_mock,
        "manager_instance": manager_instance,
    }


class TestResolveRuntimeDependencies:
    """`_resolve_runtime_dependencies` bundles MistHelper module handle."""

    def test_returns_bundle_with_misthelper_module(self) -> None:
        """The returned SimpleNamespace exposes the live MistHelper module."""
        deps = _resolve_runtime_dependencies()  # WHY: exercise helper directly.
        assert deps.misthelper_module is not None  # WHY: module resolved.
        assert deps.misthelper_module.__name__ == "MistHelper"  # WHY: identity check on module name.


class TestServicePingLauncherInit:
    """Constructor stores late-bound dependencies."""

    def test_init_resolves_runtime_dependencies(self) -> None:
        """__init__ populates `_deps.misthelper_module` via the resolver."""
        launcher = ServicePingLauncher()  # WHY: exercise construction.
        assert launcher._deps.misthelper_module.__name__ == "MistHelper"  # WHY: name-check.

    def test_misthelper_returns_module_handle(self) -> None:
        """`_misthelper()` returns the same module handle stored during init."""
        launcher = ServicePingLauncher()  # WHY: build instance.
        assert launcher._misthelper() is launcher._deps.misthelper_module  # WHY: identity passthrough.


class TestLaunchHappyPath:
    """`launch()` orchestrates wire → build → execute in order."""

    def test_launch_wires_builds_and_executes(
        self, wired_deps: dict[str, Any], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Happy-path launch calls configure, ServicePingManager(), and manager.execute() exactly once each."""
        launcher = ServicePingLauncher()  # WHY: build launcher after wiring is in place.
        with caplog.at_level(logging.INFO):  # WHY: capture launch banner + wire/build info logs.
            launcher.launch()  # WHY: exercise full pipeline.

        assert wired_deps["configure"].call_count == 1  # WHY: wire step invoked exactly once.
        call_kwargs = wired_deps["configure"].call_args.kwargs  # WHY: verify dependency wiring by kwarg name.
        assert call_kwargs["apisession_dependency"] is wired_deps["apisession"]  # WHY: apisession threaded through.
        assert call_kwargs["mistapi_dependency"] is wired_deps["mistapi"]  # WHY: mistapi threaded through.
        assert call_kwargs["prompt_utils"] is wired_deps["PromptUtils"]  # WHY: prompt utils threaded through.
        assert call_kwargs["input_utils"] is wired_deps["InputUtils"]  # WHY: input utils threaded through.
        assert call_kwargs["websocket_manager_class"] is wired_deps["WebSocketManager"]  # WHY: WS class threaded.
        assert callable(
            call_kwargs["is_debug_mode"]
        )  # WHY: is_debug_mode should be the IsDebugMode.check bound method.
        assert call_kwargs["api_tenant_fetch_utils"] is wired_deps["APITenantFetchUtils"]  # WHY: tenant utils.
        assert call_kwargs["config_utils"] is wired_deps["ConfigUtils"]  # WHY: config utils.
        assert call_kwargs["api_fetch_utils"] is wired_deps["APIFetchUtils"]  # WHY: fetch utils.

        assert wired_deps["manager_class"].call_count == 1  # WHY: manager instantiated exactly once.
        assert wired_deps["manager_instance"].execute.call_count == 1  # WHY: execute() invoked once.
        assert "Menu #120: Starting WebSocket Service Ping" in caplog.text  # WHY: launch banner logged.

    def test_launch_missing_apisession_uses_none(
        self, wired_deps: dict[str, Any], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When apisession is absent on MistHelper, the wire call receives None (getattr default)."""
        monkeypatch.delattr("MistHelper.apisession", raising=False)  # WHY: force getattr fallback branch.
        launcher = ServicePingLauncher()  # WHY: build launcher post-delete.
        launcher.launch()  # WHY: exercise wire with missing apisession.
        assert wired_deps["configure"].call_args.kwargs["apisession_dependency"] is None  # WHY: fallback returns None.


class TestLaunchFatalError:
    """`launch()` funnels any exception through `_handle_fatal_error`."""

    def test_launch_wire_failure_logs_and_prints(
        self,
        wired_deps: dict[str, Any],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """When configure_service_ping_manager_dependencies raises, error is logged, no crash."""
        wired_deps["configure"].side_effect = RuntimeError("wire boom")  # WHY: raise during wire step.
        launcher = ServicePingLauncher()  # WHY: build launcher.
        with caplog.at_level(logging.WARNING):  # WHY: fatal path logs at WARNING + ERROR.
            launcher.launch()  # WHY: exercise exception branch; must not re-raise.
        assert "ERROR: wire boom" in caplog.text  # WHY: user-visible warning banner emitted.
        assert "Error running Service Ping" in caplog.text  # WHY: structured error log emitted.
        assert wired_deps["manager_class"].call_count == 0  # WHY: manager never built when wire fails.
        assert wired_deps["manager_instance"].execute.call_count == 0  # WHY: execute never reached.

    def test_launch_execute_failure_logs_and_prints(
        self,
        wired_deps: dict[str, Any],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """When manager.execute() raises, the error surfaces via _handle_fatal_error."""
        wired_deps["manager_instance"].execute.side_effect = RuntimeError("execute boom")  # WHY: raise on execute.
        launcher = ServicePingLauncher()  # WHY: build launcher.
        with caplog.at_level(logging.WARNING):  # WHY: capture both WARNING banner and ERROR log.
            launcher.launch()  # WHY: exercise post-build exception branch.
        assert "ERROR: execute boom" in caplog.text  # WHY: user-visible warning banner emitted.
        assert "Error running Service Ping" in caplog.text  # WHY: structured error log emitted.


class TestHandleFatalError:
    """`_handle_fatal_error` logs at WARNING + ERROR directly (unit level)."""

    def test_prints_and_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        """Direct call logs banner + error without invoking sys.exit."""
        launcher = ServicePingLauncher()  # WHY: build instance to reach the method.
        error = ValueError("boom-direct")  # WHY: sentinel error we can grep for.
        with caplog.at_level(logging.WARNING):  # WHY: assert on both WARNING banner and ERROR log entry.
            launcher._handle_fatal_error(error)  # WHY: direct-call exercises the branch.
        assert "ERROR: boom-direct" in caplog.text  # WHY: warning banner content.
        assert "Error running Service Ping" in caplog.text  # WHY: log entry present.

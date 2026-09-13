"""Regression tests for GatewayTestExporter runtime dependency wiring."""

from __future__ import annotations  # WHY: match the repository's postponed-annotation convention.

from types import SimpleNamespace  # WHY: provide focused MistHelper runtime doubles.
from unittest.mock import MagicMock  # WHY: observe dependency wiring and delegated service calls.

from src.export import (
    gateway_test_exporter as exporter_module,  # WHY: patch the exact lazy import lookup used at runtime.
)
from src.export.gateway_test_exporter import (
    GatewayTestExporter,  # WHY: exercise the public gateway-test export entry points.
)
from src.refactors.serial_cc.test_results_by_site import (
    GatewayTestResultsService,  # WHY: isolate the delegated site-results service.
)


def test_synthetic_tests_wires_gateway_dependencies_before_inventory_lookup(monkeypatch) -> None:
    """Synthetic export must configure GatewayExportUtils before it asks for inventory."""
    call_order: list[str] = []  # WHY: prove setup happens before the first gateway inventory access.

    def configure_gateway_module() -> None:
        call_order.append("configure")  # WHY: record gateway DI completion.

    def get_devices_with_sites(org_id: str, fast: bool = False) -> list[tuple[str, str, str, str]]:
        call_order.append("inventory")  # WHY: record the first dependency-sensitive export operation.
        assert org_id == "org-1"  # WHY: preserve the resolved organization context.
        assert fast is False  # WHY: exercise the default systematic-test path.
        return []  # WHY: stop before synthetic-test API calls; wiring is the behavior under test.

    runtime = SimpleNamespace(  # WHY: provide only collaborators reached before the early no-device return.
        _configure_gateway_module=configure_gateway_module,
        PROGRESS_EMITTER=None,
        ConfigUtils=SimpleNamespace(get_cached_or_prompted_org_id=MagicMock(return_value="org-1")),
        GatewayExportUtils=SimpleNamespace(_get_devices_with_sites=get_devices_with_sites),
    )
    monkeypatch.setattr(  # WHY: avoid importing the real application runtime during this isolated unit test.
        exporter_module.importlib,
        "import_module",
        MagicMock(return_value=runtime),
    )

    GatewayTestExporter.synthetic_tests()  # WHY: execute the formerly failing menu-33 export entry point.

    assert call_order == ["configure", "inventory"]  # WHY: DI must precede all gateway inventory use.


def test_site_results_wires_gateway_dependencies_before_delegating(monkeypatch) -> None:
    """Site-result export must wire GatewayExportUtils before its extracted service runs."""
    call_order: list[str] = []  # WHY: prove setup ordering across the extracted service boundary.

    def configure_gateway_module() -> None:
        call_order.append("configure")  # WHY: record dependency setup.

    def execute_service(fast: bool = False) -> None:
        call_order.append("service")  # WHY: record the delegated service entry.
        assert fast is True  # WHY: preserve the caller's fast-mode argument.

    runtime = SimpleNamespace(_configure_gateway_module=configure_gateway_module)  # WHY: only setup is read here.
    monkeypatch.setattr(  # WHY: replace lazy MistHelper import with the minimal runtime double.
        exporter_module.importlib,
        "import_module",
        MagicMock(return_value=runtime),
    )
    monkeypatch.setattr(  # WHY: prevent live API work while observing delegation order.
        GatewayTestResultsService,
        "execute",
        staticmethod(execute_service),
    )

    GatewayTestExporter.test_results_by_site(fast=True)  # WHY: execute the second direct gateway-test entry point.

    assert call_order == ["configure", "service"]  # WHY: service must never run with unwired gateway dependencies.

"""Unit tests for extracted MSP orchestration module."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.inventory.org_device_inventory_msp import OrgDeviceInventoryMSPOrchestrator
from src.inventory.org_device_inventory_msp import configure_org_device_inventory_msp_dependencies


def _configure_msp(*, privileges: list[dict] | None = None, safe_input_return: str = "1") -> MagicMock:
    """Configure MSP module dependencies and return exporter mock."""
    exporter = MagicMock()
    configure_org_device_inventory_msp_dependencies(
        apisession_dependency=object(),
        input_utils=SimpleNamespace(safe_input=MagicMock(return_value=safe_input_return)),
        data_exporter=SimpleNamespace(write_with_format_selection=exporter),
        msp_privileges_value=privileges or [],
    )
    return exporter


def test_resolve_active_msp_returns_none_without_privileges() -> None:
    """MSP resolver should return None when MSP privileges are not available."""
    _configure_msp(privileges=[])
    assert OrgDeviceInventoryMSPOrchestrator._resolve_active_msp() is None


def test_resolve_active_msp_autoselects_single_privilege() -> None:
    """MSP resolver should auto-select when exactly one MSP privilege exists."""
    _configure_msp(privileges=[{"msp_id": "m1", "msp_name": "One MSP", "role": "admin"}])
    selected = OrgDeviceInventoryMSPOrchestrator._resolve_active_msp()
    assert selected is not None
    assert selected["msp_id"] == "m1"


def test_dispatch_routes_to_selected_mode(monkeypatch) -> None:
    """Dispatcher should call the correct callback for mode selections."""
    _configure_msp(privileges=[{"msp_id": "m1", "msp_name": "One MSP", "role": "admin"}], safe_input_return="3")
    single_mock = MagicMock()
    select_mock = MagicMock()
    batch_mock = MagicMock()

    OrgDeviceInventoryMSPOrchestrator.dispatch(
        single_org_fn=single_mock,
        select_org_fn=select_mock,
        batch_fn=batch_mock,
    )

    batch_mock.assert_called_once()
    single_mock.assert_not_called()
    select_mock.assert_not_called()


def test_execute_msp_builds_combined_reports_for_multiple_orgs(monkeypatch) -> None:
    """MSP batch should build combined reports when at least two orgs are processed."""
    _configure_msp(privileges=[{"msp_id": "m1", "msp_name": "MSP Name", "role": "admin"}])
    monkeypatch.setattr(
        OrgDeviceInventoryMSPOrchestrator,
        "_resolve_active_msp",
        staticmethod(lambda: {"msp_id": "m1", "msp_name": "MSP Name", "role": "admin"}),
    )
    monkeypatch.setattr(
        OrgDeviceInventoryMSPOrchestrator,
        "_fetch_org_list",
        staticmethod(lambda active_msp: [{"id": "org-1", "name": "Org One"}, {"id": "org-2", "name": "Org Two"}]),
    )
    combined_mock = MagicMock()
    monkeypatch.setattr(OrgDeviceInventoryMSPOrchestrator, "_build_combined_reports", staticmethod(combined_mock))

    def _run_for_org(org_id: str) -> tuple[list[dict], list[dict], list[dict], str]:
        return ([{"device_type": "ap", "model": "A", "count": 1}], [{"device_type": "ap", "version": "1", "count": 1}], [{"device_type": "ap", "model": "A", "version": "1", "count": 1}], org_id)

    OrgDeviceInventoryMSPOrchestrator.execute_msp(_run_for_org)

    combined_mock.assert_called_once()

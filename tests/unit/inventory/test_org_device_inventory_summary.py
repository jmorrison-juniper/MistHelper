"""Unit tests for extracted OrgDeviceInventorySummary core module."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.inventory.org_device_inventory_summary import OrgDeviceInventorySummaryCore
from src.inventory.org_device_inventory_summary import configure_org_device_inventory_summary_dependencies


def _configure_dependencies() -> MagicMock:
    """Configure module dependencies and return exporter mock for assertions."""
    exporter = MagicMock()
    mistapi_dependency = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    devices=SimpleNamespace(
                        countOrgDevices=MagicMock(return_value=SimpleNamespace(data={"results": []})),
                        searchOrgDevices=MagicMock(return_value=SimpleNamespace(data={"results": [], "next": None})),
                    ),
                    inventory=SimpleNamespace(
                        getOrgInventory=MagicMock(return_value=SimpleNamespace(data=[])),
                    ),
                    orgs=SimpleNamespace(
                        getOrg=MagicMock(return_value=SimpleNamespace(data={"name": "Test Org"})),
                    ),
                )
            )
        ),
        get_all=MagicMock(return_value=[]),
    )
    configure_org_device_inventory_summary_dependencies(
        apisession_dependency=SimpleNamespace(mist_get=MagicMock(return_value=SimpleNamespace(data={"results": [], "next": None}))),
        mistapi_dependency=mistapi_dependency,
        data_exporter=SimpleNamespace(write_with_format_selection=exporter),
        org_id_value="org-1",
    )
    return exporter


def test_aggregate_switch_counts_uses_num_members() -> None:
    """Switch aggregation should sum num_members for VC-accurate physical counts."""
    _configure_dependencies()
    rows = OrgDeviceInventorySummaryCore._aggregate_switch_counts(
        [
            {"model": "EX2300", "num_members": 3},
            {"model": "EX2300", "num_members": 2},
            {"model": "EX4400", "num_members": 1},
        ],
        "model",
    )
    assert rows[0]["model"] == "EX2300"
    assert rows[0]["count"] == 5
    assert rows[1]["model"] == "EX4400"
    assert rows[1]["count"] == 1


def test_aggregate_gateway_counts_counts_physical_records() -> None:
    """Gateway aggregation should count each inventory record as one physical device."""
    _configure_dependencies()
    rows = OrgDeviceInventorySummaryCore._aggregate_gateway_counts(
        [
            {"version": "22.1R1"},
            {"version": "22.1R1"},
            {"version": "23.2R1"},
        ],
        "version",
    )
    assert rows[0]["version"] == "22.1R1"
    assert rows[0]["count"] == 2
    assert rows[1]["version"] == "23.2R1"
    assert rows[1]["count"] == 1


def test_run_for_org_calls_all_export_steps(monkeypatch) -> None:
    """run_for_org should execute model, version, and pivot export flows."""
    _configure_dependencies()
    monkeypatch.setattr(
        OrgDeviceInventorySummaryCore,
        "_resolve_safe_org_name",
        staticmethod(lambda target_org_id: "MyOrg"),
    )
    monkeypatch.setattr(
        OrgDeviceInventorySummaryCore,
        "_fetch_all_counts",
        staticmethod(lambda target_org_id, distinct: [{"device_type": "ap", distinct: "v", "count": 1}]),
    )
    monkeypatch.setattr(
        OrgDeviceInventorySummaryCore,
        "_fetch_versions_per_model",
        staticmethod(lambda target_org_id, model_rows: [{"device_type": "ap", "model": "A", "version": "1", "count": 1}]),
    )
    display_mock = MagicMock()
    pivot_mock = MagicMock()
    monkeypatch.setattr(OrgDeviceInventorySummaryCore, "_display_and_export", staticmethod(display_mock))
    monkeypatch.setattr(OrgDeviceInventorySummaryCore, "_display_pivot_and_export", staticmethod(pivot_mock))

    model_rows, version_rows, ver_per_model, safe_org = OrgDeviceInventorySummaryCore.run_for_org("org-1")

    assert safe_org == "MyOrg"
    assert len(model_rows) == 1
    assert len(version_rows) == 1
    assert len(ver_per_model) == 1
    assert display_mock.call_count == 2
    pivot_mock.assert_called_once()

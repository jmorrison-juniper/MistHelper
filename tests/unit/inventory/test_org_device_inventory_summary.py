"""Unit tests for extracted OrgDeviceInventorySummary core module."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.inventory.org_device_inventory_summary import (
    OrgDeviceInventorySummaryCore,
    configure_org_device_inventory_summary_dependencies,
)


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
        apisession_dependency=SimpleNamespace(
            mist_get=MagicMock(return_value=SimpleNamespace(data={"results": [], "next": None}))
        ),
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


def test_fetch_unassigned_inventory_filters_assigned_devices() -> None:
    """Only inventory records without a site_id should be treated as unassigned."""
    _configure_dependencies()
    from src.inventory import org_device_inventory_summary as _mod

    # get_all returns a mix of assigned (site_id present) and unassigned (site_id missing/empty) records.
    _mod.mistapi.get_all = MagicMock(
        return_value=[
            {"type": "ap", "model": "AP43", "site_id": "site-1"},
            {"type": "ap", "model": "AP43"},
            {"type": "switch", "model": "EX2300", "site_id": ""},
        ]
    )
    unassigned = OrgDeviceInventorySummaryCore._fetch_unassigned_inventory("org-1")
    assert len(unassigned) == 2
    assert all(not record.get("site_id") for record in unassigned)


def test_aggregate_unassigned_counts_version_uses_unassigned_bucket() -> None:
    """Version aggregation should collapse unassigned stock into an 'unassigned' bucket."""
    _configure_dependencies()
    rows = OrgDeviceInventorySummaryCore._aggregate_unassigned_counts(
        [
            {"type": "ap", "model": "AP43", "version": "0.1"},
            {"type": "ap", "model": "AP43"},
            {"type": "switch", "model": "EX2300"},
        ],
        "version",
    )
    by_type = {(row["device_type"], row["version"]): row["count"] for row in rows}
    assert by_type[("ap", "unassigned")] == 2
    assert by_type[("switch", "unassigned")] == 1


def test_aggregate_unassigned_counts_model_keeps_real_model() -> None:
    """Model aggregation should keep the real model so totals merge with assigned counts."""
    _configure_dependencies()
    rows = OrgDeviceInventorySummaryCore._aggregate_unassigned_counts(
        [
            {"type": "ap", "model": "AP43"},
            {"type": "ap", "model": "AP43"},
        ],
        "model",
    )
    assert rows == [{"device_type": "ap", "model": "AP43", "count": 2}]


def test_merge_counts_sums_overlapping_keys() -> None:
    """Merging should sum counts for matching (device_type, value) keys without duplicates."""
    _configure_dependencies()
    base = [{"device_type": "ap", "model": "AP43", "count": 10}]
    extra = [
        {"device_type": "ap", "model": "AP43", "count": 3},
        {"device_type": "switch", "model": "EX2300", "count": 1},
    ]
    merged = OrgDeviceInventorySummaryCore._merge_counts(base, extra, "model")
    by_key = {(row["device_type"], row["model"]): row["count"] for row in merged}
    assert by_key[("ap", "AP43")] == 13
    assert by_key[("switch", "EX2300")] == 1
    assert len(merged) == 2


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
        staticmethod(
            lambda target_org_id, distinct, unassigned_records=None: [{"device_type": "ap", distinct: "v", "count": 1}]
        ),
    )
    from src.inventory.inventory_summary import pivot_renderer as _pivot_mod
    from src.inventory.inventory_summary import version_per_model_fetcher as _vpm_mod

    monkeypatch.setattr(
        _vpm_mod.VersionPerModelFetcher,
        "fetch",
        staticmethod(
            lambda target_org_id, model_rows, unassigned_records=None: [
                {"device_type": "ap", "model": "A", "version": "1", "count": 1}
            ]
        ),
    )
    display_mock = MagicMock()
    pivot_mock = MagicMock()
    monkeypatch.setattr(OrgDeviceInventorySummaryCore, "_display_and_export", staticmethod(display_mock))
    monkeypatch.setattr(_pivot_mod.PivotRenderer, "render", staticmethod(pivot_mock))

    model_rows, version_rows, ver_per_model, safe_org = OrgDeviceInventorySummaryCore.run_for_org("org-1")

    assert safe_org == "MyOrg"
    assert len(model_rows) == 1
    assert len(version_rows) == 1
    assert len(ver_per_model) == 1
    assert display_mock.call_count == 2
    pivot_mock.assert_called_once()

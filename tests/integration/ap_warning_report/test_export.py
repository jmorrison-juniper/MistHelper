"""Exercise source pagination, joins, and the real CSV export boundary."""

import csv
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock, patch

import pytest

from src.operations.exporting.ap_warning_report.operation import REPORT_COLUMNS, ApWarningReport
from src.operations.exporting.export.data_exporter import DataExporter

ORG_ID = "00000000-0000-0000-0000-000000000001"


def response(rows: list[dict[str, Any]], following: str | None = None, status: int = 200) -> SimpleNamespace:
    """Model the public SDK page attributes used by report reads."""
    return SimpleNamespace(status_code=status, data=rows, next=following)


def test_paginated_sources_reach_real_csv_writer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Later-page APs retain site names and definitions in the persisted report."""
    monkeypatch.chdir(tmp_path)
    runtime = SimpleNamespace(
        ConfigUtils=SimpleNamespace(get_cached_or_prompted_org_id=lambda: ORG_ID),
        apisession=Mock(),
        DataExporter=DataExporter,
    )
    pages = {
        "sites-next": response([{"id": "site-two", "name": "Second site"}]),
        "inventory-next": response([{"mac": "000000000002", "type": "ap", "site_id": "site-two", "connected": False}]),
    }
    with (
        patch("src.operations.exporting.ap_warning_report.operation.SourceDependencyResolver", runtime),
        patch(
            "src.operations.exporting.export.data_exporter.SourceDependencyResolver",
            SimpleNamespace(OUTPUT_FORMAT="csv"),
        ),
        patch.object(DataExporter, "_route_to_polyglot", return_value=SimpleNamespace(written=True)),
        patch(
            "mistapi.api.v1.const.ap_led_status.listApLedDefinition",
            return_value=response(
                [{"code": "03", "key": "DHCP", "name": "DHCP error", "description": "No DHCP response"}]
            ),
        ),
        patch(
            "mistapi.api.v1.orgs.sites.listOrgSites",
            return_value=response([{"id": "site-one", "name": "First site"}], "sites-next"),
        ),
        patch(
            "mistapi.api.v1.orgs.inventory.getOrgInventory",
            return_value=response(
                [{"mac": "000000000001", "type": "ap", "site_id": "site-one", "connected": True}],
                "inventory-next",
            ),
        ),
        patch(
            "mistapi.api.v1.sites.stats.listSiteDevicesStats",
            side_effect=[
                response(
                    [
                        {
                            "mac": "000000000001",
                            "status": "connected",
                            "last_trouble": {"code": "03", "timestamp": time.time()},
                        }
                    ]
                ),
                response(
                    [
                        {
                            "mac": "000000000002",
                            "status": "disconnected",
                            "last_trouble": {"code": "99", "timestamp": time.time()},
                        }
                    ]
                ),
            ],
        ),
        patch("mistapi.get_next", side_effect=lambda mist_session, response: pages[response.next]),
    ):
        assert ApWarningReport.run() == 2
    output = tmp_path / "data" / f"ApWarningReport_{ORG_ID}.csv"
    with output.open(encoding="utf-8", newline="") as exported:
        reader = csv.DictReader(exported)
        rows = list(reader)
        assert reader.fieldnames == REPORT_COLUMNS
    assert [row["code"] for row in rows] == ["03", "99"]
    assert rows[1]["site_name"] == "Second site"
    assert rows[1]["connection_status"] == "disconnected"
    assert rows[1]["definition_status"] == "unknown"


@pytest.mark.parametrize("endpoint", ["definitions", "sites", "inventory", "site_statistics"])
@pytest.mark.parametrize("status", [403, 503])
def test_failed_required_source_writes_nothing(endpoint: str, status: int) -> None:
    """Every required endpoint must succeed before the output writer can run."""
    runtime = SimpleNamespace(
        ConfigUtils=SimpleNamespace(get_cached_or_prompted_org_id=lambda: ORG_ID),
        apisession=Mock(),
        DataExporter=SimpleNamespace(write_with_format_selection=Mock()),
    )
    replies = {name: response([]) for name in ("definitions", "sites", "inventory", "site_statistics")}
    replies[endpoint] = response([], status=status)
    if endpoint != "sites":
        replies["sites"] = response([{"id": "site-one", "name": "First site"}])
    with (
        patch("src.operations.exporting.ap_warning_report.operation.SourceDependencyResolver", runtime),
        patch("mistapi.api.v1.const.ap_led_status.listApLedDefinition", return_value=replies["definitions"]),
        patch("mistapi.api.v1.orgs.sites.listOrgSites", return_value=replies["sites"]),
        patch("mistapi.api.v1.orgs.inventory.getOrgInventory", return_value=replies["inventory"]),
        patch(
            "mistapi.api.v1.sites.stats.listSiteDevicesStats",
            return_value=replies["site_statistics"],
        ),
        pytest.raises(RuntimeError, match="failed"),
    ):
        ApWarningReport.run()
    runtime.DataExporter.write_with_format_selection.assert_not_called()


@pytest.mark.parametrize("later_status", [403, 503])
def test_failed_inventory_later_page_prevents_partial_export(later_status: int) -> None:
    """A later-page error must block persistence even when the first AP has a code."""
    runtime = SimpleNamespace(
        ConfigUtils=SimpleNamespace(get_cached_or_prompted_org_id=lambda: ORG_ID),
        apisession=Mock(),
        DataExporter=SimpleNamespace(write_with_format_selection=Mock()),
    )
    initial = response([{"mac": "000000000001", "last_trouble": {"code": "03"}}], "inventory-next")
    with (
        patch("src.operations.exporting.ap_warning_report.operation.SourceDependencyResolver", runtime),
        patch(
            "mistapi.api.v1.const.ap_led_status.listApLedDefinition",
            return_value=response(
                [{"code": "03", "key": "DHCP", "name": "DHCP error", "description": "No DHCP response"}]
            ),
        ),
        patch("mistapi.api.v1.orgs.sites.listOrgSites", return_value=response([])),
        patch("mistapi.api.v1.orgs.inventory.getOrgInventory", return_value=initial),
        patch("mistapi.get_next", return_value=response([], status=later_status)),
        pytest.raises(RuntimeError, match="failed"),
    ):
        ApWarningReport.run()
    runtime.DataExporter.write_with_format_selection.assert_not_called()

"""Unit tests for site inventory health analyzer extraction."""

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from requests.exceptions import ConnectionError, HTTPError, Timeout

from src.mist.intelligence.analytics.site_inventory_health_analyzer import (
    SiteInventoryHealthAnalyzer,
    SiteInventoryHealthAnalyzerDeps,
)

_MODULE_LOGGER = "src.mist.intelligence.analytics.site_inventory_health_analyzer"  # Use the canonical source path.


def _build_mistapi_stub() -> SimpleNamespace:
    """Build a minimal mistapi stub object for analyzer tests."""
    get_org_inventory = MagicMock()
    inventory = SimpleNamespace(getOrgInventory=get_org_inventory)
    orgs = SimpleNamespace(inventory=inventory)
    v1 = SimpleNamespace(orgs=orgs)
    api = SimpleNamespace(v1=v1)
    get_all = MagicMock(return_value=[])
    return SimpleNamespace(api=api, get_all=get_all)


def _build_deps() -> SiteInventoryHealthAnalyzerDeps:
    """Build default dependency object with overridable mocks."""
    return SiteInventoryHealthAnalyzerDeps(
        apisession=MagicMock(),
        mistapi=_build_mistapi_stub(),
        get_org_id_fn=MagicMock(return_value="org-123"),
        all_sites_fn=MagicMock(return_value=[]),
        save_data_fn=MagicMock(),
    )


def test_analyze_exits_when_org_missing(caplog: pytest.LogCaptureFixture) -> None:
    """Analyzer should stop early when org selection is unavailable."""
    deps = _build_deps()
    deps.get_org_id_fn.return_value = None

    with caplog.at_level(logging.WARNING, logger=_MODULE_LOGGER):
        SiteInventoryHealthAnalyzer.analyze(deps)

    assert "No organization selected" in caplog.text


def test_group_devices_by_site_sets_status_from_connected_field() -> None:
    """Grouping should map connected bool to connected/disconnected labels."""
    grouped = SiteInventoryHealthAnalyzer._group_devices_by_site(
        [
            {"site_id": "s1", "type": "ap", "connected": True, "name": "AP-1"},
            {"site_id": "s1", "type": "switch", "connected": False, "name": "SW-1"},
            {"site_id": "s1", "type": "gateway", "name": "GW-1"},
        ]
    )

    assert grouped["s1"]["aps"][0]["status"] == "connected"
    assert grouped["s1"]["switches"][0]["status"] == "disconnected"
    assert grouped["s1"]["gateways"][0]["status"] == "unknown"


def test_find_sites_missing_infrastructure() -> None:
    """Sites with APs but no switch/gateway should be included in missing report."""
    inventory = {
        "site-a": {
            "aps": [{"name": "AP-1"}],
            "switches": [],
            "gateways": [{"name": "GW-1"}],
        },
    }

    result = SiteInventoryHealthAnalyzer._find_sites_missing_infrastructure(inventory, {"site-a": "Site A"})

    assert len(result) == 1
    assert result[0]["site_name"] == "Site A"
    assert "switch" in result[0]["missing_types"]


def test_analyze_happy_path_exports_reports() -> None:
    """Analyze should export both reports when data indicates actionable findings."""
    deps = _build_deps()
    deps.all_sites_fn.return_value = [{"id": "site-1", "name": "Site One"}]

    org_inventory_response = SimpleNamespace(status_code=200, data=[])
    deps.mistapi.api.v1.orgs.inventory.getOrgInventory.return_value = org_inventory_response
    deps.mistapi.get_all.return_value = [
        {
            "site_id": "site-1",
            "type": "ap",
            "name": "AP-1",
            "connected": True,
            "id": "ap-1",
            "mac": "aa:bb",
            "model": "AP32",
            "serial": "SER-AP",
        },
        {
            "site_id": "site-1",
            "type": "switch",
            "name": "SW-1",
            "connected": False,
            "id": "sw-1",
            "mac": "cc:dd",
            "model": "EX4400",
            "serial": "SER-SW",
        },
    ]

    SiteInventoryHealthAnalyzer.analyze(deps)

    assert deps.save_data_fn.call_count >= 1


@pytest.mark.parametrize("stage", ["sites", "inventory", "pagination"])
@pytest.mark.parametrize("failure_type", [ConnectionError, Timeout, HTTPError])
def test_inventory_transport_failure_logs_and_prevents_export(
    stage: str, failure_type: type[Exception], caplog: pytest.LogCaptureFixture
) -> None:
    """A failed request prevents an empty report from representing a healthy inventory."""
    deps = _build_deps()
    deps.all_sites_fn.return_value = [{"id": "site-1", "name": "Site One"}]
    deps.mistapi.get_all.return_value = [{"site_id": "site-1", "type": "ap"}]
    targets = {
        "sites": deps.all_sites_fn,
        "inventory": deps.mistapi.api.v1.orgs.inventory.getOrgInventory,
        "pagination": deps.mistapi.get_all,
    }
    failure = failure_type("inventory unavailable")
    targets[stage].side_effect = failure
    SiteInventoryHealthAnalyzer.analyze(deps)
    deps.save_data_fn.assert_not_called()
    assert "Failed to fetch required data" in caplog.text
    record = next(record for record in caplog.records if record.exc_info)
    assert record.name == _MODULE_LOGGER
    assert record.exc_info[1] is failure
    assert "inventory unavailable" in record.getMessage()


@pytest.mark.parametrize("stage", ["sites", "inventory", "pagination"])
@pytest.mark.parametrize("failure_type", [NameError, TypeError, AttributeError, RuntimeError])
def test_inventory_programming_error_propagates(stage: str, failure_type: type[Exception]) -> None:
    """A defective fetch or pagination call must reach the analyzer caller."""
    deps = _build_deps()
    deps.all_sites_fn.return_value = [{"id": "site-1", "name": "Site One"}]
    targets = {
        "sites": deps.all_sites_fn,
        "inventory": deps.mistapi.api.v1.orgs.inventory.getOrgInventory,
        "pagination": deps.mistapi.get_all,
    }
    targets[stage].side_effect = failure_type("inventory defect")
    with pytest.raises(failure_type, match="inventory defect"):
        SiteInventoryHealthAnalyzer.analyze(deps)
    deps.save_data_fn.assert_not_called()

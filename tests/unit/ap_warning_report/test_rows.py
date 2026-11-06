"""Verify inventory-led warning selection and site enrichment."""

from copy import deepcopy
from typing import Any

import pytest

from src.operations.exporting.ap_warning_report.rows import WarningRows

ORG_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def sources() -> dict[str, list[dict[str, Any]]]:
    """Supply connected, disconnected, healthy, and unobserved APs."""
    return {
        "definitions": [{"code": "03", "key": "DHCP", "name": "DHCP error", "description": "No DHCP response"}],
        "sites": [{"id": "site-one", "name": "First site"}],
        "inventory": [
            {"id": f"ap-{number}", "mac": f"00000000000{number}", "type": "ap", "connected": number == 1}
            for number in range(1, 5)
        ],
        "stats": [
            {
                "mac": "00:00:00:00:00:01",
                "status": "connected",
                "site_id": "site-one",
                "last_trouble": {"code": "03", "timestamp": 0},
            },
            {"mac": "000000000002", "status": "disconnected", "last_trouble": {"code": "99"}},
            {"mac": "000000000003", "last_trouble": {"code": "00"}},
        ],
    }


def test_warning_filter_includes_both_connection_states(sources: dict[str, Any]) -> None:
    """Only nonzero trouble evidence qualifies, independent of connection."""
    original = deepcopy(sources)
    report = WarningRows(ORG_ID, sources)
    rows = report.build("2026-11-05T00:00:00+00:00")
    assert [row["mac"] for row in rows] == ["000000000001", "000000000002"]
    assert [row["connection_status"] for row in rows] == ["connected", "disconnected"]
    assert rows[0]["site_name"] == "First site"
    assert rows[0]["trouble_timestamp"] == "1970-01-01T00:00:00+00:00"
    assert rows[0]["trouble_source"] == "statistics"
    assert rows[1]["definition_status"] == "unknown"
    assert rows[1]["trouble_timestamp"] == ""
    assert report.summary == {"inventory_aps": 4, "missing_trouble": 1, "matched": 2}
    assert sources == original


def test_inventory_evidence_survives_absent_statistics(sources: dict[str, Any]) -> None:
    """Unassigned inventory APs remain eligible when they carry trouble evidence."""
    sources["stats"] = []
    sources["inventory"] = [{"mac": "000000000001", "type": "ap", "connected": False, "last_trouble": {"code": 3}}]
    row = WarningRows(ORG_ID, sources).build("2026-11-05T00:00:00+00:00")[0]
    assert row["trouble_source"] == "inventory"
    assert row["connection_status"] == "disconnected"
    assert row["site_lookup_status"] == "unassigned"
    assert row["site_name"] == ""
    assert row["device_id"] == ""


@pytest.mark.parametrize("observation", [None, {}, {"code": "00"}])
def test_explicit_stats_observation_overrides_stale_inventory(sources: dict[str, Any], observation: object) -> None:
    """A cleared statistics observation must not resurrect inventory trouble."""
    sources["inventory"] = [{"mac": "000000000001", "type": "ap", "last_trouble": {"code": "03"}}]
    sources["stats"] = [{"mac": "000000000001", "last_trouble": observation}]
    assert WarningRows(ORG_ID, sources).build("2026-11-05T00:00:00+00:00") == []


def test_missing_site_and_non_ap_exclusion(sources: dict[str, Any]) -> None:
    """A missing site preserves its identifier without fabricating a name."""
    sources["stats"][0]["site_id"] = "deleted-site"
    sources["inventory"][1]["type"] = "switch"
    rows = WarningRows(ORG_ID, sources).build("2026-11-05T00:00:00+00:00")
    assert len(rows) == 1
    assert rows[0]["site_id"] == "deleted-site"
    assert rows[0]["site_lookup_status"] == "missing"
    assert rows[0]["site_name"] == ""


@pytest.mark.parametrize("collection", ["inventory", "stats", "sites"])
def test_duplicate_identity_rejects_ambiguous_join(sources: dict[str, Any], collection: str) -> None:
    """An ambiguous join must fail instead of silently choosing a row."""
    sources[collection].append(deepcopy(sources[collection][0]))
    with pytest.raises(ValueError, match="Duplicate"):
        WarningRows(ORG_ID, sources).build("2026-11-05T00:00:00+00:00")


@pytest.mark.parametrize("mac", [None, "", "bad", "00:00:00:00:00:gg"])
def test_missing_or_invalid_mac_rejects_incomplete_identity(sources: dict[str, Any], mac: object) -> None:
    """Every scanned AP requires the natural identity used for the join."""
    sources["inventory"][0]["mac"] = mac
    with pytest.raises(ValueError, match="MAC"):
        WarningRows(ORG_ID, sources).build("2026-11-05T00:00:00+00:00")


def test_missing_connection_remains_unknown(sources: dict[str, Any]) -> None:
    """Missing connection data must not be reported as disconnected."""
    sources["inventory"][0].pop("connected")
    sources["stats"][0].pop("status")
    row = WarningRows(ORG_ID, sources).build("2026-11-05T00:00:00+00:00")[0]
    assert row["connection_status"] == "unknown"


@pytest.mark.parametrize("observation", ["03", ["03"], 3])
def test_malformed_observation_fails(sources: dict[str, Any], observation: object) -> None:
    """An invalid trouble object must not silently disappear."""
    sources["stats"][0]["last_trouble"] = observation
    with pytest.raises(ValueError, match="last_trouble"):
        WarningRows(ORG_ID, sources).build("2026-11-05T00:00:00+00:00")


def test_invalid_site_identity_fails(sources: dict[str, Any]) -> None:
    """A malformed site lookup must not become an apparent missing site."""
    sources["sites"][0]["id"] = None
    with pytest.raises(ValueError, match="identity"):
        WarningRows(ORG_ID, sources).build("2026-11-05T00:00:00+00:00")


def test_invalid_ap_assignment_fails(sources: dict[str, Any]) -> None:
    """A malformed assignment must not produce an invented site identity."""
    sources["stats"][0]["site_id"] = 3
    with pytest.raises(ValueError, match="site identifier"):
        WarningRows(ORG_ID, sources).build("2026-11-05T00:00:00+00:00")

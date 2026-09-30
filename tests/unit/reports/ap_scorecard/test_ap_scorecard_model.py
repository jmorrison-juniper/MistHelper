"""Tests for AP scorecard model functions."""

from __future__ import annotations

from src.reports.ap_scorecard.model import (
    AP_SCORECARD_COLUMNS,
    SITE_SCORECARD_COLUMNS,
    build_ap_rows,
    build_organization_summary,
    build_site_rows,
    classify_switch_redundancy,
    normalize_switch_redundancy,
    tile_color_band,
)


def test_ap_scorecard_creates_one_detail_row_per_ap(ap_stats_payload: list[dict[str, object]]) -> None:
    """Detail rows match the AP payload length."""
    rows = build_ap_rows(ap_stats_payload)
    assert len(rows) == len(ap_stats_payload)


def test_ap_scorecard_detail_rows_have_required_columns(ap_stats_payload: list[dict[str, object]]) -> None:
    """Detail row dictionaries expose every contract column."""
    row = build_ap_rows(ap_stats_payload)[0]
    assert set(AP_SCORECARD_COLUMNS) == set(row.__dataclass_fields__)


def test_ap_scorecard_detail_rows_include_org_id(ap_stats_payload: list[dict[str, object]]) -> None:
    """Detail row dictionaries include the organization identifier."""
    row = build_ap_rows(ap_stats_payload, org_id="org-1")[0]
    assert row.org_id == "org-1"


def test_ap_scorecard_vlan_failure_lists_vlan_ids(ap_stats_payload: list[dict[str, object]]) -> None:
    """Inactive wired VLANs fail the VLAN tile and list the VLAN IDs."""
    row = build_ap_rows(ap_stats_payload)[2]
    assert row.inactive_wired_vlans == "20,30"


def test_ap_scorecard_missing_lldp_stat_leaves_power_columns_empty(
    ap_stats_payload: list[dict[str, object]],
) -> None:
    """Missing LLDP data leaves empty power values and does not fail."""
    row = build_ap_rows(ap_stats_payload)[1]
    assert row.lldp_power_allocated == ""
    assert row.lldp_power_needed == ""


def test_ap_scorecard_color_band_thresholds() -> None:
    """Color bands match the Mist Access Points page boundaries."""
    assert tile_color_band(98.5) == "green"
    assert tile_color_band(90.0) == "orange"
    assert tile_color_band(80.0) == "red"


def test_ap_scorecard_site_summary_has_one_row_per_site(ap_stats_payload: list[dict[str, object]]) -> None:
    """Site summary rows include one row for each site with APs."""
    rows = build_site_rows(build_ap_rows(ap_stats_payload))
    assert [row.site_id for row in rows] == ["site-a", "site-b"]


def test_ap_scorecard_redundancy_classification_values() -> None:
    """Redundancy values one, two, and three map to all required classes."""
    assert classify_switch_redundancy(normalize_switch_redundancy(1)) == "none"
    assert classify_switch_redundancy(normalize_switch_redundancy(2)) == "good"
    assert classify_switch_redundancy(normalize_switch_redundancy(3)) == "excellent"


def test_ap_scorecard_redundancy_rejects_none_zero_and_negative_values() -> None:
    """Invalid redundancy inputs stay unknown and never count as healthy."""
    assert normalize_switch_redundancy(None) is None
    assert normalize_switch_redundancy(0) is None
    assert normalize_switch_redundancy(-1) is None
    assert classify_switch_redundancy(normalize_switch_redundancy(None)) == "unknown"
    assert classify_switch_redundancy(normalize_switch_redundancy(0)) == "unknown"
    assert classify_switch_redundancy(normalize_switch_redundancy(-1)) == "unknown"


def test_ap_scorecard_model_handles_none_input() -> None:
    """A missing redundancy value stays unknown."""
    normalized = normalize_switch_redundancy(None)
    assert normalized is None
    assert classify_switch_redundancy(None) == "unknown"


def test_ap_scorecard_model_handles_zero_value() -> None:
    """A zero redundancy value stays unknown."""
    normalized = normalize_switch_redundancy(0)
    assert normalized is None
    assert classify_switch_redundancy(0) == "unknown"


def test_ap_scorecard_model_handles_negative_value() -> None:
    """A negative redundancy value stays unknown."""
    normalized = normalize_switch_redundancy(-1)
    assert normalized is None
    assert classify_switch_redundancy(-1) == "unknown"


def test_ap_scorecard_site_redundancy_counts(ap_stats_payload: list[dict[str, object]]) -> None:
    """Site rows report no, good, and excellent redundancy counts."""
    rows = {row.site_id: row for row in build_site_rows(build_ap_rows(ap_stats_payload))}
    assert rows["site-a"].switch_redundancy_good_count == 1
    assert rows["site-a"].switch_redundancy_excellent_count == 1
    assert rows["site-b"].switch_redundancy_none_count == 1


def test_ap_scorecard_site_summary_has_required_tile_columns(ap_stats_payload: list[dict[str, object]]) -> None:
    """Site row dictionaries expose every contract column."""
    row = build_site_rows(build_ap_rows(ap_stats_payload, org_id="org-1"))[0]
    assert set(SITE_SCORECARD_COLUMNS) == set(row.__dataclass_fields__)
    assert row.org_id == "org-1"


def test_ap_scorecard_organization_summary_percentages(ap_stats_payload: list[dict[str, object]]) -> None:
    """Organization summary reports all five required tile percentages."""
    summary = build_organization_summary(build_ap_rows(ap_stats_payload))
    assert summary.ap_count == 3
    assert summary.connection_status_percent == 66.67
    assert summary.vlans_percent == 66.67
    assert summary.version_compliance_percent == 66.67
    assert summary.switch_redundancy_percent == 66.67
    assert summary.potential_anomalies_percent == 66.67


def test_ap_scorecard_site_name_falls_back_to_site_id() -> None:
    """Rows without a site name use the site identifier."""
    rows = build_ap_rows([{"site_id": "site-only", "mac": "aabb", "model": "AP43", "version": "1.0.0"}])
    assert rows[0].site == "site-only"


def test_ap_scorecard_power_needed_requires_exact_field() -> None:
    """LLDP power needed stays empty when the exact source field is absent."""
    rows = build_ap_rows(
        [
            {
                "site_id": "site-a",
                "mac": "aabb",
                "model": "AP43",
                "version": "1.0.0",
                "lldp_stat": {"power_allocated": 15000, "power_requested": 25500},
            }
        ]
    )
    assert rows[0].lldp_power_needed == ""

"""Tests for the pure switch scorecard model."""

from __future__ import annotations  # WHY: keep annotations consistent with the source package.

from src.mist.intelligence.reports.switch_scorecard.model import (  # WHY: test the pure model without network calls.
    DEFAULT_AFFINITY_LIMIT,
    SwitchScorecardBuilder,
    SwitchScorecardSettings,
)


def _switch(**overrides):  # Build compact switch fixtures for scorecard tests.
    row = {  # WHY: defaults describe one healthy switch.
        "site_id": "site-1",
        "site_name": "Main",
        "name": "sw-1",
        "hostname": "sw-1-host",
        "mac": "aa",
        "model": "EX4400",
        "version": "22.4R3",
        "config_status": "success",
        "ap_redundancy": {"num_aps": 6, "num_aps_with_switch_redundancy": 4},
        "module_stat": [
            {
                "poe": {"max_power": 740, "power_draw": 300},
                "bios_version": "1.0",
                "fpga_version": "2.0",
                "pending_version": "22.4R4",
                "backup_version": "22.4R2",
                "fans": [{"name": "fan0", "status": "ok"}],
                "psus": [{"name": "psu0", "status": "failed"}],
                "temperatures": [{"name": "temp0", "status": "normal"}],
            }
        ],
        "uptime": 172800,
        "last_trouble": "",
    }
    row.update(overrides)  # WHY: each test changes only the relevant fields.
    return row  # WHY: callers receive an independent fixture row.


def test_default_affinity_threshold_and_environment_override():  # Verify FR-008.
    default_settings = SwitchScorecardSettings.from_environment({})  # WHY: unset env must use Mist default.
    custom_settings = SwitchScorecardSettings.from_environment({"SWITCH_AP_AFFINITY_LIMIT": "9"})
    fallback_settings = SwitchScorecardSettings.from_environment({"SWITCH_AP_AFFINITY_LIMIT": "bad"})

    assert default_settings.affinity_limit == DEFAULT_AFFINITY_LIMIT  # WHY: default threshold is specified.
    assert custom_settings.affinity_limit == 9  # WHY: valid env input must override the default.
    assert fallback_settings.affinity_limit == DEFAULT_AFFINITY_LIMIT  # WHY: invalid input falls back safely.
    assert "invalid" in fallback_settings.fallback_note  # WHY: operators need a visible fallback reason.


def test_detail_rows_include_predominant_version_and_module_fields():  # Verify FR-001, FR-002, FR-009, FR-010.
    switches = [_switch(mac="aa"), _switch(mac="bb"), _switch(mac="cc", version="21.4R3")]
    output = SwitchScorecardBuilder.build(switches, SwitchScorecardSettings.from_environment({}))
    first = output.detail_rows[0]  # WHY: all healthy defaults should produce populated module evidence.
    minority = output.detail_rows[2]  # WHY: this row carries the non-predominant version.

    assert first["predominant_model_version"] == "22.4R3"  # WHY: two of three switches use this version.
    assert first["version_compliant"] is True  # WHY: the predominant version is compliant.
    assert minority["version_compliant"] is False  # WHY: the minority version is non-compliant.
    assert first["poe_budget_watts"] == 740  # WHY: module PoE budget must appear in the detail row.
    assert first["poe_draw_watts"] == 300  # WHY: module PoE draw must appear in the detail row.
    assert first["pending_versions"] == "22.4R4"  # WHY: pending module version must appear in the row.
    assert first["bios_versions"] == "1.0"  # WHY: BIOS evidence must appear in the row.
    assert first["fpga_versions"] == "2.0"  # WHY: FPGA evidence must appear in the row.
    assert first["backup_versions"] == "22.4R2"  # WHY: backup partition version must appear in the row.
    assert first["psu_errors"] == "psu0:failed"  # WHY: failed PSU state must appear in the row.
    assert first["uptime_days"] == 2.0  # WHY: uptime must be converted from seconds to days.


def test_missing_module_stat_produces_empty_module_columns():  # Verify FR-011.
    output = SwitchScorecardBuilder.build([_switch(module_stat=None)], SwitchScorecardSettings.from_environment({}))
    row = output.detail_rows[0]  # WHY: one switch should still create one detail row.

    assert row["poe_budget_watts"] == ""  # WHY: missing module evidence should remain blank.
    assert row["poe_draw_watts"] == ""  # WHY: missing module evidence should remain blank.
    assert row["pending_versions"] == ""  # WHY: missing module evidence should remain blank.
    assert row["fan_errors"] == ""  # WHY: missing component lists should not create false errors.


def test_site_rows_include_tile_percentages_and_counts():  # Verify FR-003, FR-004, FR-005, FR-012.
    switches = [
        _switch(site_id="site-1", site_name="Main", mac="aa"),
        _switch(site_id="site-1", site_name="Main", mac="bb", ap_redundancy={"num_aps": 13}),
        _switch(site_id="site-2", site_name="Branch", mac="cc", config_status="failed", uptime=0),
    ]
    output = SwitchScorecardBuilder.build(switches, SwitchScorecardSettings.from_environment({}))
    main = next(row for row in output.site_rows if row["site_id"] == "site-1")
    branch = next(row for row in output.site_rows if row["site_id"] == "site-2")

    assert main["switch_count"] == 2  # WHY: both Main switches contribute to the Main site row.
    assert main["switch_ap_affinity_percent"] == 50.0  # WHY: one of two Main switches exceeds the AP limit.
    assert main["switch_ap_affinity_count"] == 1  # WHY: count must sit beside the percentage.
    assert branch["config_success_percent"] == 0.0  # WHY: failed config status should lower the tile.
    assert branch["switch_uptime_count"] == 0  # WHY: zero uptime should not count as up.
    assert output.org_summary["switch_count"] == 3  # WHY: the organization summary covers all switches.


def test_live_switch_shape_uses_site_lookup_and_config_unknown_count():  # Verify issue 3692 live payload shape.
    switches = [  # WHY: live listOrgDevicesStats rows carry site_id and no config_status.
        _switch(site_id="site-live", site_name=None, mac="aa", config_status=None),
        _switch(site_id="site-live", site_name=None, mac="bb", config_status=None),
    ]
    output = SwitchScorecardBuilder.build(  # WHY: pass the same listOrgSites lookup used by the operation.
        switches,
        SwitchScorecardSettings.from_environment({}),
        {"site-live": "Morrison House Site"},
    )
    detail = output.detail_rows[0]  # WHY: one row proves the lookup filled the detail site name.
    site = output.site_rows[0]  # WHY: one site row proves unknown config handling.

    assert detail["site_name"] == "Morrison House Site"  # WHY: live stats have no site_name field.
    assert site["site_name"] == "Morrison House Site"  # WHY: site summaries must show the site name.
    assert site["config_success_count"] == 0  # WHY: unknown rows are not counted as successes.
    assert site["config_unknown_count"] == 2  # WHY: unknown rows are visible to the operator.
    assert site["config_success_percent"] == 0.0  # WHY: no known config rows leaves no success score.

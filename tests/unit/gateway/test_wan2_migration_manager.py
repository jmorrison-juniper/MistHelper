"""Unit tests for extracted WAN2 migration manager logic."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.gateway.wan2_migration_manager import WAN2MigrationManager
from src.gateway.wan2_migration_manager import configure_wan2_migration_dependencies


def _configure_dependencies(*, site_exclude_prefix: str = "") -> None:
    """Configure minimal dependency graph for WAN2 manager unit tests."""
    configure_wan2_migration_dependencies(
        apisession_dependency=object(),
        config_utils=SimpleNamespace(
            get_cached_or_prompted_org_id=MagicMock(return_value="org-1"),
            check_stop_signal=MagicMock(return_value=False),
        ),
        cache_utils=SimpleNamespace(check_and_generate_csv=MagicMock()),
        org_site_exporter=SimpleNamespace(sites=MagicMock()),
        gateway_export_utils=SimpleNamespace(device_configs=MagicMock(), templates=MagicMock()),
        file_path_utils=SimpleNamespace(get_csv_path=MagicMock(return_value="test.csv")),
        input_utils=SimpleNamespace(safe_input=MagicMock(return_value="yes")),
        data_exporter=SimpleNamespace(save_data_to_output=MagicMock()),
        mistapi_dependency=SimpleNamespace(),
        site_exclude_prefix=site_exclude_prefix,
    )


def test_filter_excluded_sites_respects_configured_prefix() -> None:
    """Site filtering removes only prefixed site names when prefix is configured."""
    _configure_dependencies(site_exclude_prefix="LAB-")
    manager = WAN2MigrationManager()

    sites = [
        {"name": "LAB-Store-1", "id": "1"},
        {"name": "Prod-Store-2", "id": "2"},
    ]

    filtered = manager._filter_excluded_sites(sites)

    assert len(filtered) == 1
    assert filtered[0]["id"] == "2"


def test_confirm_site_variable_operation_returns_false_on_negative_input() -> None:
    """Confirmation prompt returns False when user declines the operation."""
    _configure_dependencies()
    manager = WAN2MigrationManager()
    manager_input = manager.__class__.__dict__["_confirm_site_variable_operation"]

    from src.gateway import wan2_migration_manager as module

    module.InputUtils.safe_input = MagicMock(return_value="no")

    assert manager_input(manager, 5) is False


def test_classify_override_severity_matches_expected_conflicts() -> None:
    """Severity classifier maps IP-type mismatches to expected severity levels."""
    _configure_dependencies()
    manager = WAN2MigrationManager()

    assert manager._classify_override_severity("dhcp", "static") == "CRITICAL"
    assert manager._classify_override_severity("static", "dhcp") == "WARNING"
    assert manager._classify_override_severity("dhcp", "dhcp") == "INFO"
    assert manager._classify_override_severity("unknown", "") == "UNKNOWN"


def test_build_report_data_sets_requires_manual_review_by_severity() -> None:
    """Report builder sets manual review level based on override severity counters."""
    _configure_dependencies()
    manager = WAN2MigrationManager()

    report_rows = manager._build_report_data(
        [
            {
                "site_name": "site-a",
                "site_id": "site-a",
                "variable_set": True,
                "status": "SUCCESS",
                "has_overrides": True,
                "total_override_count": 1,
                "critical_override_count": 1,
                "warning_override_count": 0,
                "info_override_count": 0,
                "override_devices": ["gw-1"],
                "override_details": "gw-1@ge-0/0/1(CRITICAL:DHCP->STATIC)",
                "error": "",
            },
            {
                "site_name": "site-b",
                "site_id": "site-b",
                "variable_set": True,
                "status": "SUCCESS",
                "has_overrides": False,
                "total_override_count": 0,
                "critical_override_count": 0,
                "warning_override_count": 0,
                "info_override_count": 0,
                "override_devices": [],
                "override_details": "",
                "error": "",
            },
        ]
    )

    assert report_rows[0]["requires_manual_review"] == "CRITICAL"
    assert report_rows[1]["requires_manual_review"] == "No"

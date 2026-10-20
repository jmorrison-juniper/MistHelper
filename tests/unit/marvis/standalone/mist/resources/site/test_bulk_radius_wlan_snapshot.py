"""Unit tests for the Menu 122 RADIUS WLAN scan-snapshot export.

Covers BulkRadiusWLANConfigManager._build_snapshot_row (per-WLAN flattening
with value-presence flags) and _export_scan_snapshot (combines compliant +
non-compliant WLANs and writes via DataExporter). The presence flags are the
key feature: they reveal whether a value is real (key present in the API
record) or merely the default the compliance check assumes when absent.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import MistHelper  # Preloaded as the actual script by tests/conftest.py


def _make_manager() -> Any:
    """Build a manager with deterministic target settings (timeout=3, retries=2, fast=True)."""
    manager = MistHelper.BulkRadiusWLANConfigManager()  # __init__ only loads env config (no network)
    manager.org_id = "org-123"  # Stable org id for assertions
    manager.target_timeout = 3  # Force the target values regardless of the host .env
    manager.target_retries = 2  # Force the target retries
    manager.target_fast_dot1x = True  # Force the target fast-timer flag
    return manager  # Ready-to-use manager


def test_snapshot_row_marks_present_values() -> None:
    """A WLAN with all keys present reports present=True and passes the real values through."""
    manager = _make_manager()  # Deterministic manager
    wlan = {  # Fully-specified compliant WLAN record
        "id": "wlan-1",
        "ssid": "Corp",
        "auth": {"type": "eap"},
        "auth_servers": [{"host": "a"}, {"host": "b"}],
        "radsec": {"enabled": False},
        "auth_servers_timeout": 3,
        "auth_servers_retries": 2,
        "fast_dot1x_timers": True,
        "enabled": True,
        "_compliance_status": "COMPLIANT",
        "_inheritance_level": "template",
        "_inheritance_source": "Template ID: abcd1234...",
    }
    row = manager._build_snapshot_row(wlan, "2026-06-25 12:00:00")  # Flatten to a snapshot row
    assert row["wlan_id"] == "wlan-1"  # Identity carried through
    assert row["auth_type"] == "eap"  # Nested auth.type extracted
    assert row["num_auth_servers"] == 2  # Auth-server count derived
    assert row["auth_servers_timeout"] == 3 and row["auth_servers_timeout_present"] is True  # Real value flagged
    assert row["auth_servers_retries"] == 2 and row["auth_servers_retries_present"] is True  # Real value flagged
    assert row["fast_dot1x_timers"] is True and row["fast_dot1x_timers_present"] is True  # Real value flagged
    assert row["compliance_status"] == "COMPLIANT"  # Status carried from the filter step
    assert row["target_timeout"] == 3  # Target snapshotted for comparison


def test_snapshot_row_flags_defaulted_values() -> None:
    """A WLAN missing the timer keys reports present=False with the check's own defaults (5/2/False)."""
    manager = _make_manager()  # Deterministic manager
    wlan = {"id": "wlan-2", "ssid": "Guest", "auth_servers": [{"host": "x"}]}  # No timer keys at all
    row = manager._build_snapshot_row(wlan, "2026-06-25 12:00:00")  # Flatten to a snapshot row
    assert row["auth_servers_timeout"] == 5 and row["auth_servers_timeout_present"] is False  # Defaulted, flagged
    assert row["auth_servers_retries"] == 2 and row["auth_servers_retries_present"] is False  # Defaulted, flagged
    assert row["fast_dot1x_timers"] is False and row["fast_dot1x_timers_present"] is False  # Defaulted, flagged
    assert row["auth_type"] == ""  # Missing auth sub-config -> empty type
    assert row["radsec_enabled"] is False  # Missing radsec -> disabled


def test_snapshot_row_tolerates_non_dict_subconfigs() -> None:
    """Non-dict auth/radsec sub-configs do not raise and degrade to safe empty/False values."""
    manager = _make_manager()  # Deterministic manager
    wlan = {"id": "wlan-3", "ssid": "Odd", "auth": "not-a-dict", "radsec": "nope", "auth_servers": None}  # Malformed
    row = manager._build_snapshot_row(wlan, "2026-06-25 12:00:00")  # Must not raise
    assert row["auth_type"] == ""  # Non-dict auth -> empty type
    assert row["radsec_enabled"] is False  # Non-dict radsec -> disabled
    assert row["num_auth_servers"] == 0  # None auth_servers -> zero count


def test_export_scan_snapshot_combines_and_writes() -> None:
    """_export_scan_snapshot writes one row per RADIUS WLAN (compliant + non-compliant) with stable fields."""
    manager = _make_manager()  # Deterministic manager
    manager.radius_wlans = [{"id": "n-1", "ssid": "NeedsUpdate", "_compliance_status": "NEEDS_UPDATE"}]  # 1 needing
    manager.compliant_wlans = [{"id": "c-1", "ssid": "OK", "_compliance_status": "COMPLIANT"}]  # 1 compliant
    with patch.object(MistHelper.DataExporter, "write_with_format_selection", return_value=True) as mock_write:
        manager._export_scan_snapshot()  # Trigger the export
    mock_write.assert_called_once()  # Exactly one write
    rows = mock_write.call_args.args[0]  # First positional arg is the row list
    filename = mock_write.call_args.args[1]  # Second positional arg is the filename
    assert len(rows) == 2  # Both compliant and non-compliant WLANs included
    assert filename.startswith("RadiusWLANScanSnapshot_") and filename.endswith(".csv")  # Timestamped CSV name
    assert mock_write.call_args.kwargs["fieldnames"] == manager._SNAPSHOT_FIELDS  # Stable column order passed
    statuses = {r["compliance_status"] for r in rows}  # Collect the statuses present
    assert statuses == {"NEEDS_UPDATE", "COMPLIANT"}  # Both buckets represented


def test_export_scan_snapshot_skips_when_empty() -> None:
    """With no RADIUS WLANs discovered, the export is skipped entirely (no write attempted)."""
    manager = _make_manager()  # Deterministic manager
    manager.radius_wlans = []  # Nothing needing update
    manager.compliant_wlans = []  # Nothing compliant either
    with patch.object(MistHelper.DataExporter, "write_with_format_selection", return_value=True) as mock_write:
        manager._export_scan_snapshot()  # Should no-op
    mock_write.assert_not_called()  # No snapshot written when there is no data

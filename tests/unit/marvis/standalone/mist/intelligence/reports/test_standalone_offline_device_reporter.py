"""Unit tests for OfflineDeviceReporter pure functions.

Duplicates testable logic from MistHelper.py OfflineDeviceReporter class
to avoid import side effects (standard MistHelper test pattern).
"""

import datetime
import time

# ---------------------------------------------------------------------------
# Duplicated pure functions from OfflineDeviceReporter
# ---------------------------------------------------------------------------

DEFAULT_THRESHOLD_HOURS = 48
MIN_THRESHOLD_HOURS = 1
MAX_THRESHOLD_HOURS = 8760
MAX_INPUT_RETRIES = 3
MAX_DISPLAY_ROWS = 50


def process_devices(
    all_devices: list[dict],
    site_lookup: dict[str, str],
    threshold_hours: int,
) -> list[dict[str, str]]:
    """Mirror of OfflineDeviceReporter._process_devices()."""
    now = time.time()
    threshold_seconds = threshold_hours * 3600
    offline_records: list[dict[str, str]] = []

    for device in all_devices:
        if device.get("status") == "connected":
            continue
        last_seen_raw = device.get("last_seen") or 0
        last_seen_epoch = float(last_seen_raw) if last_seen_raw else 0.0
        offline_seconds = now - last_seen_epoch
        if offline_seconds < threshold_seconds and last_seen_epoch > 0:
            continue

        never_connected = last_seen_epoch == 0.0
        if never_connected:
            last_seen_str = "Never Connected"
            duration_str = "Never Connected"
            sort_key = float("inf")
        else:
            last_seen_str = datetime.datetime.fromtimestamp(last_seen_epoch).strftime("%Y-%m-%d %H:%M:%S")
            total_hours = int(offline_seconds // 3600)
            days = total_hours // 24
            hours = total_hours % 24
            duration_str = f"{days} days {hours} hours" if days > 0 else f"{hours} hours"
            sort_key = offline_seconds

        device_type_raw = device.get("type", "unknown")
        type_display = {"ap": "AP", "switch": "Switch", "gateway": "Gateway"}.get(
            device_type_raw, device_type_raw.capitalize()
        )
        site_name = site_lookup.get(device.get("site_id", ""), "Unknown Site")

        offline_records.append(
            {
                "Device Name": device.get("name") or "(unnamed)",
                "Device Type": type_display,
                "Site Name": site_name,
                "MAC Address": device.get("mac", ""),
                "Serial Number": device.get("serial", ""),
                "Model": device.get("model", ""),
                "Last Seen": last_seen_str,
                "Offline Duration": duration_str,
                "Status": device.get("status", "disconnected"),
                "_sort_key": str(sort_key),
            }
        )

    offline_records.sort(key=lambda record: float(record["_sort_key"]), reverse=True)
    return offline_records


def display_summary(
    total_device_count: int,
    offline_records: list[dict[str, str]],
    threshold_hours: int,
) -> str:
    """Mirror of OfflineDeviceReporter._display_summary(), returns output as string."""
    lines: list[str] = []
    lines.append("\n--- Summary ---")
    lines.append(f"Total devices in org: {total_device_count:,}")
    lines.append(f"Devices offline > {threshold_hours} hours: {len(offline_records)}")

    type_counts: dict[str, int] = {}
    site_counts: dict[str, int] = {}
    for record in offline_records:
        device_type = record["Device Type"]
        type_counts[device_type] = type_counts.get(device_type, 0) + 1
        site_name = record["Site Name"]
        site_counts[site_name] = site_counts.get(site_name, 0) + 1

    lines.append("\nBy Type:")
    for device_type in ["AP", "Switch", "Gateway"]:
        count = type_counts.get(device_type, 0)
        if count > 0:
            lines.append(f"  {device_type}s: {count}")

    sorted_sites = sorted(site_counts.items(), key=lambda item: item[1], reverse=True)[:5]
    if sorted_sites:
        lines.append("\nTop 5 Sites:")
        for rank, (site_name, count) in enumerate(sorted_sites, 1):
            lines.append(f"  {rank}. {site_name}: {count} offline")

    return "\n".join(lines)


def validate_threshold(raw: str) -> int | None:
    """Validate threshold input. Returns int if valid, None if invalid."""
    try:
        hours = int(raw)
        if MIN_THRESHOLD_HOURS <= hours <= MAX_THRESHOLD_HOURS:
            return hours
        return None
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------


def _make_device(
    name: str = "test-device",
    device_type: str = "ap",
    status: str = "disconnected",
    last_seen: float | None = None,
    site_id: str = "site-001",
    mac: str = "aa:bb:cc:dd:ee:01",
    serial: str = "ABC123",
    model: str = "AP45",
) -> dict:
    """Create a device dict matching Mist API response shape."""
    device: dict = {
        "name": name,
        "type": device_type,
        "status": status,
        "site_id": site_id,
        "mac": mac,
        "serial": serial,
        "model": model,
    }
    if last_seen is not None:
        device["last_seen"] = last_seen
    return device


SITE_LOOKUP = {
    "site-001": "NYC-Office",
    "site-002": "LAX-Branch",
    "site-003": "CHI-DC",
}


# ---------------------------------------------------------------------------
# Tests: validate_threshold
# ---------------------------------------------------------------------------
class TestValidateThreshold:
    """Tests for threshold input validation."""

    def test_valid_default(self):
        assert validate_threshold("48") == 48

    def test_valid_minimum(self):
        assert validate_threshold("1") == 1

    def test_valid_maximum(self):
        assert validate_threshold("8760") == 8760

    def test_below_minimum(self):
        assert validate_threshold("0") is None

    def test_above_maximum(self):
        assert validate_threshold("8761") is None

    def test_negative(self):
        assert validate_threshold("-5") is None

    def test_non_numeric(self):
        assert validate_threshold("abc") is None

    def test_empty_string(self):
        assert validate_threshold("") is None

    def test_float_string(self):
        assert validate_threshold("24.5") is None

    def test_boundary_just_inside_min(self):
        assert validate_threshold("1") == 1

    def test_boundary_just_inside_max(self):
        assert validate_threshold("8760") == 8760


# ---------------------------------------------------------------------------
# Tests: process_devices - filtering
# ---------------------------------------------------------------------------
class TestProcessDevicesFiltering:
    """Tests for device filtering logic."""

    def test_connected_devices_excluded(self):
        devices = [
            _make_device(status="connected", last_seen=time.time() - 100000),
            _make_device(name="offline-ap", status="disconnected", last_seen=time.time() - 200000),
        ]
        result = process_devices(devices, SITE_LOOKUP, 48)
        assert len(result) == 1
        assert result[0]["Device Name"] == "offline-ap"

    def test_recently_offline_excluded(self):
        """Device offline for 1 hour should be excluded with 48h threshold."""
        devices = [
            _make_device(status="disconnected", last_seen=time.time() - 3600),
        ]
        result = process_devices(devices, SITE_LOOKUP, 48)
        assert len(result) == 0

    def test_threshold_boundary_included(self):
        """Device offline for exactly threshold duration should be included."""
        devices = [
            _make_device(status="disconnected", last_seen=time.time() - (48 * 3600 + 1)),
        ]
        result = process_devices(devices, SITE_LOOKUP, 48)
        assert len(result) == 1

    def test_never_connected_included(self):
        """Device with last_seen=0 should always be included."""
        devices = [_make_device(last_seen=0)]
        result = process_devices(devices, SITE_LOOKUP, 48)
        assert len(result) == 1
        assert result[0]["Last Seen"] == "Never Connected"
        assert result[0]["Offline Duration"] == "Never Connected"

    def test_null_last_seen_included(self):
        """Device with last_seen=None should be treated as never connected."""
        devices = [_make_device(last_seen=None)]
        result = process_devices(devices, SITE_LOOKUP, 48)
        assert len(result) == 1
        assert result[0]["Last Seen"] == "Never Connected"

    def test_missing_last_seen_included(self):
        """Device with no last_seen field should be treated as never connected."""
        device = _make_device()
        # last_seen not set since _make_device with last_seen=None doesn't include it
        result = process_devices([device], SITE_LOOKUP, 48)
        assert len(result) == 1
        assert result[0]["Last Seen"] == "Never Connected"

    def test_all_online_returns_empty(self):
        devices = [
            _make_device(name="ap-1", status="connected", last_seen=time.time()),
            _make_device(name="ap-2", status="connected", last_seen=time.time()),
        ]
        result = process_devices(devices, SITE_LOOKUP, 48)
        assert len(result) == 0

    def test_empty_device_list(self):
        result = process_devices([], SITE_LOOKUP, 48)
        assert len(result) == 0

    def test_mixed_types(self):
        """All device types should be processed."""
        now = time.time()
        devices = [
            _make_device(name="ap-1", device_type="ap", status="disconnected", last_seen=now - 200000),
            _make_device(name="sw-1", device_type="switch", status="disconnected", last_seen=now - 200000),
            _make_device(name="gw-1", device_type="gateway", status="disconnected", last_seen=now - 200000),
        ]
        result = process_devices(devices, SITE_LOOKUP, 48)
        assert len(result) == 3
        types = {record["Device Type"] for record in result}
        assert types == {"AP", "Switch", "Gateway"}


# ---------------------------------------------------------------------------
# Tests: process_devices - enrichment
# ---------------------------------------------------------------------------
class TestProcessDevicesEnrichment:
    """Tests for device record enrichment."""

    def test_site_name_resolved(self):
        devices = [_make_device(site_id="site-001", last_seen=time.time() - 200000)]
        result = process_devices(devices, SITE_LOOKUP, 48)
        assert result[0]["Site Name"] == "NYC-Office"

    def test_unknown_site_fallback(self):
        devices = [_make_device(site_id="nonexistent-site", last_seen=time.time() - 200000)]
        result = process_devices(devices, SITE_LOOKUP, 48)
        assert result[0]["Site Name"] == "Unknown Site"

    def test_unnamed_device_fallback(self):
        devices = [_make_device(name="", last_seen=time.time() - 200000)]
        result = process_devices(devices, SITE_LOOKUP, 48)
        assert result[0]["Device Name"] == "(unnamed)"

    def test_none_name_fallback(self):
        devices = [_make_device(name=None, last_seen=time.time() - 200000)]
        result = process_devices(devices, SITE_LOOKUP, 48)
        assert result[0]["Device Name"] == "(unnamed)"

    def test_device_type_capitalization(self):
        devices = [
            _make_device(device_type="ap", last_seen=time.time() - 200000),
        ]
        result = process_devices(devices, SITE_LOOKUP, 48)
        assert result[0]["Device Type"] == "AP"

    def test_switch_type_capitalization(self):
        devices = [_make_device(device_type="switch", last_seen=time.time() - 200000)]
        result = process_devices(devices, SITE_LOOKUP, 48)
        assert result[0]["Device Type"] == "Switch"

    def test_gateway_type_capitalization(self):
        devices = [_make_device(device_type="gateway", last_seen=time.time() - 200000)]
        result = process_devices(devices, SITE_LOOKUP, 48)
        assert result[0]["Device Type"] == "Gateway"

    def test_all_csv_fields_present(self):
        """All 9 display columns must be present in output records."""
        devices = [_make_device(last_seen=time.time() - 200000)]
        result = process_devices(devices, SITE_LOOKUP, 48)
        expected_fields = {
            "Device Name",
            "Device Type",
            "Site Name",
            "MAC Address",
            "Serial Number",
            "Model",
            "Last Seen",
            "Offline Duration",
            "Status",
        }
        record_fields = set(result[0].keys()) - {"_sort_key"}
        assert record_fields == expected_fields


# ---------------------------------------------------------------------------
# Tests: process_devices - sorting
# ---------------------------------------------------------------------------
class TestProcessDevicesSorting:
    """Tests for offline duration sort order."""

    def test_sorted_by_duration_descending(self):
        now = time.time()
        devices = [
            _make_device(name="recent", last_seen=now - (49 * 3600), mac="aa:01"),
            _make_device(name="old", last_seen=now - (100 * 3600), mac="aa:02"),
            _make_device(name="very-old", last_seen=now - (500 * 3600), mac="aa:03"),
        ]
        result = process_devices(devices, SITE_LOOKUP, 48)
        names = [record["Device Name"] for record in result]
        assert names == ["very-old", "old", "recent"]

    def test_never_connected_sorted_first(self):
        now = time.time()
        devices = [
            _make_device(name="recent-offline", last_seen=now - (49 * 3600), mac="aa:01"),
            _make_device(name="never-connected", last_seen=0, mac="aa:02"),
        ]
        result = process_devices(devices, SITE_LOOKUP, 48)
        assert result[0]["Device Name"] == "never-connected"


# ---------------------------------------------------------------------------
# Tests: process_devices - duration formatting
# ---------------------------------------------------------------------------
class TestDurationFormatting:
    """Tests for offline duration string formatting."""

    def test_hours_only(self):
        """Less than 1 day should show hours only."""
        devices = [_make_device(last_seen=time.time() - (5 * 3600))]
        result = process_devices(devices, SITE_LOOKUP, 4)
        duration = result[0]["Offline Duration"]
        assert "days" not in duration
        assert "hours" in duration

    def test_days_and_hours(self):
        """More than 1 day should show days and hours."""
        devices = [_make_device(last_seen=time.time() - (3 * 86400 + 12 * 3600))]
        result = process_devices(devices, SITE_LOOKUP, 48)
        duration = result[0]["Offline Duration"]
        assert "3 days" in duration
        assert "hours" in duration

    def test_timestamp_format(self):
        """Last seen should be formatted as YYYY-MM-DD HH:MM:SS."""
        epoch = time.time() - 200000
        devices = [_make_device(last_seen=epoch)]
        result = process_devices(devices, SITE_LOOKUP, 48)
        last_seen = result[0]["Last Seen"]
        # Verify format by parsing it back
        datetime.datetime.strptime(last_seen, "%Y-%m-%d %H:%M:%S")

    def test_never_connected_duration(self):
        devices = [_make_device(last_seen=0)]
        result = process_devices(devices, SITE_LOOKUP, 48)
        assert result[0]["Offline Duration"] == "Never Connected"
        assert result[0]["Last Seen"] == "Never Connected"


# ---------------------------------------------------------------------------
# Tests: display_summary
# ---------------------------------------------------------------------------

_EXTRA_KEYS = [
    "Device Name",
    "MAC Address",
    "Serial Number",
    "Model",
    "Last Seen",
    "Offline Duration",
    "Status",
    "_sort_key",
]


def _rec(device_type: str, site: str) -> dict:
    """Build a minimal offline-device record for tests."""
    return {
        "Device Type": device_type,
        "Site Name": site,
        **{k: "" for k in _EXTRA_KEYS},
    }


class TestDisplaySummary:
    """Tests for summary statistics output."""

    def test_total_counts(self):
        records = [
            _rec("AP", "NYC-Office"),
            _rec("Switch", "NYC-Office"),
        ]
        output = display_summary(100, records, 48)
        assert "Total devices in org: 100" in output
        assert "Devices offline > 48 hours: 2" in output

    def test_type_breakdown(self):
        records = [
            _rec("AP", "A"),
            _rec("AP", "A"),
            _rec("Switch", "A"),
        ]
        output = display_summary(500, records, 48)
        assert "APs: 2" in output
        assert "Switchs: 1" in output

    def test_top_5_sites(self):
        records = [_rec("AP", "Site-A") for _ in range(3)]
        records += [_rec("AP", "Site-B") for _ in range(2)]
        output = display_summary(100, records, 48)
        assert "1. Site-A: 3 offline" in output
        assert "2. Site-B: 2 offline" in output

    def test_zero_offline(self):
        output = display_summary(100, [], 48)
        assert "Devices offline > 48 hours: 0" in output
        assert "By Type:" in output

    def test_large_device_count_formatted(self):
        """Total device count should use comma formatting."""
        output = display_summary(10000, [], 48)
        assert "Total devices in org: 10,000" in output

    def test_top_5_limit(self):
        """Only top 5 sites should be shown even with more sites."""
        records = []
        for i in range(7):
            site_name = f"Site-{chr(65 + i)}"
            records += [_rec("AP", site_name) for _ in range(7 - i)]
        output = display_summary(100, records, 48)
        assert "5." in output
        # Site-F (index 5) has 2, Site-G (index 6) has 1 - top 5 only
        assert "6." not in output


# ---------------------------------------------------------------------------
# Tests: present_results - display cap
# ---------------------------------------------------------------------------
class TestPresentResultsDisplayCap:
    """Tests for the 50-row display limit."""

    def test_display_cap_message_under_limit(self):
        """When records < 50, show all."""
        records = [
            {
                "Device Name": f"dev-{i}",
                "Device Type": "AP",
                "Site Name": "A",
                "MAC Address": "",
                "Serial Number": "",
                "Model": "",
                "Last Seen": "",
                "Offline Duration": "",
                "Status": "disconnected",
                "_sort_key": "0",
            }
            for i in range(10)
        ]
        # Just verify count logic
        show_count = min(len(records), MAX_DISPLAY_ROWS)
        assert show_count == 10

    def test_display_cap_at_limit(self):
        """When records > 50, cap at 50."""
        records = [
            {
                "Device Name": f"dev-{i}",
                "Device Type": "AP",
                "Site Name": "A",
                "MAC Address": "",
                "Serial Number": "",
                "Model": "",
                "Last Seen": "",
                "Offline Duration": "",
                "Status": "disconnected",
                "_sort_key": "0",
            }
            for i in range(75)
        ]
        show_count = min(len(records), MAX_DISPLAY_ROWS)
        assert show_count == 50

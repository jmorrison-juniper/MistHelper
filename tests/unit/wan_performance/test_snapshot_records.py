"""Normalize controlled API snapshots without claiming full-hour observations."""

import pytest

from src.interfaces.portals.wan_performance.collection.snapshot_records import SnapshotRecords


def snapshot():
    """Supply independent records matching documented API identity fields."""
    return {
        "org_id": "org-one",
        "collected_at_utc": "2024-01-01T12:34:00+00:00",
        "provenance": "live",
        "ports": [
            {"org_id": "org-one", "site_id": "site-one", "mac": "aabbccddeeff", "port_id": "ge-0/0/0", "rx_bps": 40}
        ],
        "peers": [
            {
                "org_id": "org-one",
                "site_id": "site-one",
                "mac": "aabbccddeeff",
                "port_id": "ge-0/0/0",
                "peer_mac": "11:22:33:44:55:66",
                "peer_port_id": "ge-0/0/1",
                "peer_site_id": "site-two",
                "type": "ipsec",
                "loss": 0,
            }
        ],
    }


def test_snapshot_hours_have_no_invented_coverage():
    """Use an observation-hour key without claiming a full-hour measurement."""
    records = SnapshotRecords.build(snapshot())
    assert len(records) == 2
    assert records[0].hour_start_utc.isoformat() == "2024-01-01T12:00:00+00:00"
    assert records[0].collected_at_utc.minute == 34
    assert records[0].metrics["rx_bps"].unit == "bit/s"
    assert records[0].metrics["rx_bps"].sample_count == 1
    assert records[0].metrics["rx_bps"].coverage_fraction is None
    assert records[1].metrics["loss"].value == 0


def test_remote_peer_ports_have_distinct_path_keys():
    """Separate paths with the same local port and peer MAC."""
    first = snapshot()
    second = snapshot()
    second["peers"][0]["peer_port_id"] = "ge-0/0/2"
    assert SnapshotRecords.build(first)[1].natural_key != SnapshotRecords.build(second)[1].natural_key


def test_cross_org_row_is_rejected():
    """Validate tenant context before history or cache writes."""
    data = snapshot()
    data["ports"][0]["org_id"] = "another-org"
    with pytest.raises(ValueError, match="organization"):
        SnapshotRecords.build(data)


def test_byte_counters_do_not_become_rates():
    """Keep cumulative reboot counters out of utilization calculations."""
    data = snapshot()
    data["ports"][0].pop("rx_bps")
    data["ports"][0]["rx_bytes"] = 100000000
    record = SnapshotRecords.build(data)[0]
    assert record.metrics["rx_bps"].value is None
    assert "utilization" not in record.metrics


def test_compact_peer_mac_preserves_the_source_identifier():
    """Accept a compact hexadecimal MAC without changing its identity value."""
    data = snapshot()
    data["peers"][0]["peer_mac"] = "112233445566"
    assert SnapshotRecords.build(data)[1].identity.peer_mac == "112233445566"

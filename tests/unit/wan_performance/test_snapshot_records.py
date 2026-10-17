"""Normalize controlled API snapshots without claiming full-hour observations."""

import json

import pytest

from src.interfaces.portals.wan_performance.collection.snapshot_records import SnapshotRecords
from src.interfaces.portals.wan_performance.integration.record_codec import RecordCodec


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


def test_peer_history_codec_preserves_remote_port_identity():
    """Keep each peer path's remote port in durable history serialization."""
    record = SnapshotRecords.build(snapshot())[1]

    restored = RecordCodec.decode(RecordCodec.encode(record))

    assert restored == record
    assert restored.identity.peer_port_id == "ge-0/0/1"


def test_peer_history_codec_rejects_empty_body():
    """Reject an empty byte body after decoding its transport representation."""
    empty_body = b""
    with pytest.raises(json.JSONDecodeError):
        RecordCodec.decode(empty_body.decode("utf-8"))


def test_peer_history_codec_rejects_malformed_json():
    """Reject malformed stored JSON before it reaches history consumers."""
    with pytest.raises(json.JSONDecodeError):
        RecordCodec.decode("{")


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


@pytest.mark.parametrize(
    ("speed", "receive", "transmit", "expected"),
    [(1000, 0, 800000000, (0, 80)), (100, 70000000, 90000000, (70, 90))],
)
def test_port_utilization_uses_documented_mbps_speed(speed, receive, transmit, expected):
    """Convert gateway Mbps capacity into directional point-in-time percentages."""
    data = snapshot()
    data["ports"][0].update(speed=speed, rx_bps=receive, tx_bps=transmit)
    record = SnapshotRecords.build(data)[0]
    for name, value in zip(("rx_utilization_percent", "tx_utilization_percent"), expected, strict=True):
        assert record.metrics[name].value == value
        assert record.metrics[name].unit == "%"
        assert record.metrics[name].sample_count == 1
        assert record.metrics[name].coverage_fraction is None


@pytest.mark.parametrize("speed", [None, 0, -1, True, "1000", 1.5, float("inf")])
def test_unverified_capacity_keeps_utilization_unknown(speed):
    """Do not manufacture capacity from absent or invalid link-speed fields."""
    data = snapshot()
    data["ports"][0].update(speed=speed, tx_bps=0)
    record = SnapshotRecords.build(data)[0]
    assert record.metrics["rx_utilization_percent"].value is None
    assert record.metrics["tx_utilization_percent"].value is None
    assert record.metrics["rx_utilization_percent"].missing_reason == (
        "Utilization requires a valid rate and positive integer link speed in Mbps."
    )


@pytest.mark.parametrize("receive", [None, -1, True, "bad rate", float("nan"), float("inf")])
def test_invalid_port_rate_remains_unknown_without_discarding_other_direction(receive, caplog):
    """Keep valid observations while explicitly reporting an invalid optional port rate."""
    data = snapshot()
    data["ports"][0].update(speed=100, rx_bps=receive, tx_bps=50000000)
    record = SnapshotRecords.build(data)[0]
    assert record.metrics["rx_bps"].value is None
    assert record.metrics["rx_utilization_percent"].value is None
    assert record.metrics["tx_utilization_percent"].value == 50
    if receive is not None:
        assert "Invalid port snapshot rate" in caplog.text


def test_current_peer_state_keeps_boolean_and_epoch_semantics():
    """Render current state and reported uptime without calculating availability minutes."""
    from src.interfaces.portals.wan_performance.collection.snapshot_records import SnapshotStates

    data = snapshot()
    data["ports"][0]["up"] = False
    data["peers"][0].update(up=True, is_active=False, uptime=0, last_seen=1704112440)
    records = SnapshotRecords.build(data)
    states = SnapshotStates.build(data, records)
    assert records[0].is_up_observation is False
    assert records[1].is_up_observation is True
    assert states[records[0].natural_key] == {"Current link state": "Down"}
    assert states[records[1].natural_key] == {
        "Current link state": "Up",
        "Redundant path": "Standby",
        "Gateway-reported uptime (s)": "0",
        "Last observed (UTC)": "2024-01-01T12:34:00+00:00",
    }
    assert "availability" not in records[1].metrics


@pytest.mark.parametrize(
    "values",
    [
        {"up": None, "is_active": None, "uptime": None, "last_seen": None},
        {"up": 1, "is_active": "true", "uptime": -1, "last_seen": "bad timestamp"},
        {"up": "false", "is_active": 0, "uptime": True, "last_seen": float("inf")},
    ],
)
def test_unknown_or_invalid_peer_state_does_not_become_healthy(values):
    """Keep absent and invalid metadata unknown rather than interpreting truthy values."""
    from src.interfaces.portals.wan_performance.collection.snapshot_records import SnapshotStates

    data = snapshot()
    data["peers"][0].update(values)
    records = SnapshotRecords.build(data)
    states = SnapshotStates.build(data, records)[records[1].natural_key]
    assert states == {
        "Current link state": "Unknown",
        "Redundant path": "Unknown",
        "Gateway-reported uptime (s)": "Unknown",
        "Last observed (UTC)": "Unknown",
    }
    assert records[1].is_up_observation is None

"""Check verified VPN peer fields without assigning undocumented units."""

import pytest

from src.interfaces.wan_performance.collection.snapshot_records import PeerSnapshotMetrics


def test_peer_schema_scalars_use_only_documented_units() -> None:
    """Map loss, latency, and jitter units while retaining MOS as a raw scalar."""
    row = {"latency": 0, "mos": 4.2, "loss": 0.25, "jitter": 2.5, "last_seen": 1470417522}
    metrics = PeerSnapshotMetrics.parse(row)

    assert set(metrics) == {"loss", "latency", "jitter", "mos"}
    assert metrics["loss"].unit == "%"
    assert metrics["loss"].value == 0.25
    assert metrics["latency"].unit == "ms"
    assert metrics["latency"].value == 0
    assert metrics["jitter"].unit == "ms"
    assert metrics["jitter"].value == 2.5
    assert metrics["mos"].unit == "unknown"
    assert metrics["mos"].missing_reason == "The VPN peer stats schema does not define this field's unit."
    assert PeerSnapshotMetrics.raw_fields(row) == {
        "loss": 0.25,
        "latency": 0,
        "jitter": 2.5,
        "mos": 4.2,
        "last_seen": 1470417522,
    }


def test_missing_peer_scalars_remain_explicit() -> None:
    """Keep absent schema fields distinct from measured zero."""
    row = {"latency": None, "mos": None}
    metrics = PeerSnapshotMetrics.parse(row)

    assert set(metrics) == {"latency", "jitter", "loss", "mos"}
    assert all(metric.value is None for metric in metrics.values())
    assert metrics["latency"].missing_reason == "The API snapshot has no value."
    assert metrics["mos"].missing_reason == "The API snapshot has no value."
    assert all(metric.coverage_fraction is None for metric in metrics.values())
    assert PeerSnapshotMetrics.raw_fields(row) == {
        "loss": None,
        "latency": None,
        "jitter": None,
        "mos": None,
        "last_seen": None,
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [("latency", True), ("mos", "4"), ("last_seen", float("nan")), ("latency", float("inf"))],
)
def test_invalid_raw_peer_values_fail(field: str, value: object) -> None:
    """Reject malformed raw source values before storage."""
    with pytest.raises(ValueError, match=field):
        PeerSnapshotMetrics.raw_fields({field: value})


def test_peer_samples_keep_schema_fields_and_ignore_unrelated_values() -> None:
    """Keep documented quality scalars and ignore unrelated status and counter fields."""
    row = {"loss": 0.1, "jitter": 1.5, "rx_bytes": 1000000, "up": True}
    metrics = PeerSnapshotMetrics.parse(row)

    assert set(metrics) == {"latency", "jitter", "loss", "mos"}
    assert metrics["loss"].value == 0.1
    assert metrics["jitter"].value == 1.5
    assert PeerSnapshotMetrics.raw_fields(row) == {
        "loss": 0.1,
        "latency": None,
        "jitter": 1.5,
        "mos": None,
        "last_seen": None,
    }


def test_metrics_are_immutable() -> None:
    """Prevent one consumer from changing another consumer's metric view."""
    metrics = PeerSnapshotMetrics.parse({"loss": 1})
    with pytest.raises(TypeError):
        metrics["loss"] = metrics["loss"]  # type: ignore[index]

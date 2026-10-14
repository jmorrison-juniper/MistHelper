"""Check documented VPN metrics without treating snapshots as hourly history."""

import pytest

from src.interfaces.portals.wan_performance.collection.peer_metrics import PeerSnapshotMetrics


def test_documented_units_and_zero_values() -> None:
    """Retain measured zero and the units in the bundled VPN schema."""
    metrics = PeerSnapshotMetrics.parse({"latency": 0, "jitter": 2.5, "loss": 0, "mos": 5})
    assert metrics["latency"].to_dict() == {
        "value": 0,
        "unit": "ms",
        "sample_count": None,
        "coverage_fraction": None,
        "missing_reason": None,
    }
    assert metrics["jitter"].value == 2.5
    assert metrics["loss"].unit == "%"
    assert metrics["mos"].value == 5


def test_missing_fields_do_not_become_healthy_values() -> None:
    """Make absent values explicit without inventing duration or coverage."""
    metrics = PeerSnapshotMetrics.parse({"latency": None})
    assert set(metrics) == {"latency", "jitter", "loss", "mos"}
    assert all(metric.value is None for metric in metrics.values())
    assert all(metric.missing_reason == "The API snapshot has no value." for metric in metrics.values())
    assert all(metric.coverage_fraction is None for metric in metrics.values())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("latency", -1),
        ("jitter", -1),
        ("loss", -1),
        ("loss", 101),
        ("mos", -1),
        ("mos", 5.1),
        ("latency", True),
        ("loss", "4"),
        ("jitter", float("nan")),
        ("latency", float("inf")),
    ],
)
def test_invalid_external_values_fail(field: str, value: object) -> None:
    """Reject malformed values instead of making success-shaped defaults."""
    with pytest.raises(ValueError, match=field):
        PeerSnapshotMetrics.parse({field: value})


def test_unrelated_counters_and_status_are_not_metrics() -> None:
    """Do not infer utilization, availability, or a historical interval."""
    metrics = PeerSnapshotMetrics.parse({"rx_bytes": 1000000, "up": True, "last_seen": 1470417522})
    assert set(metrics) == {"latency", "jitter", "loss", "mos"}
    assert all(metric.value is None for metric in metrics.values())


def test_metrics_are_immutable() -> None:
    """Prevent one consumer from changing another consumer's snapshot."""
    metrics = PeerSnapshotMetrics.parse({"loss": 1})
    with pytest.raises(TypeError):
        metrics["loss"] = metrics["loss"]  # type: ignore[index]

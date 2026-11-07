"""Verify documented VPN peer metric normalization."""

import pytest

from src.interfaces.wan_performance.collection.snapshot_records import PeerSnapshotMetrics


class TestPeerSnapshotMetrics:
    """Keep peer metric rules separate from history behavior."""

    def test_zero_and_units_are_preserved(self) -> None:
        """Keep zero as a measurement and retain documented units."""
        metrics = PeerSnapshotMetrics.parse({"latency": 0, "loss": 0, "mos": 5})  # Include measured zero values.
        assert metrics["latency"].value == 0  # Do not replace zero with missing.
        assert metrics["latency"].unit == "ms"  # Preserve latency units.
        assert metrics["loss"].unit == "%"  # Preserve loss units.
        assert metrics["mos"].value == 5  # Preserve the upper MOS boundary.

    def test_missing_values_remain_unknown(self) -> None:
        """Explain absent metrics without creating healthy values."""
        metrics = PeerSnapshotMetrics.parse({})  # Model a source row with no metric fields.
        assert set(metrics) == {"latency", "jitter", "loss", "mos"}  # Keep the full schema.
        assert all(metric.value is None for metric in metrics.values())  # Keep all absent values unknown.
        assert all(metric.missing_reason for metric in metrics.values())  # Explain every absence.

    @pytest.mark.parametrize(
        ("field", "value"), [("loss", 101), ("mos", 5.1), ("latency", -1), ("jitter", True), ("loss", "4")]
    )  # Cover invalid source values.
    def test_invalid_peer_metrics_are_rejected(self, field: str, value: object) -> None:
        """Reject invalid peer values instead of returning success-shaped data."""
        with pytest.raises(ValueError, match=field):  # Require a field-specific error.
            PeerSnapshotMetrics.parse({field: value})  # Validate the external value.

    def test_metric_mapping_is_immutable(self) -> None:
        """Prevent one consumer from changing another consumer's values."""
        metrics = PeerSnapshotMetrics.parse({"loss": 1})  # Build one validated metric map.
        with pytest.raises(TypeError):  # Require read-only results.
            metrics["loss"] = metrics["loss"]  # type: ignore[index]  # Reject mutation.

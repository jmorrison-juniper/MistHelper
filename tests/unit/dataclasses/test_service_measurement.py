"""Verify offline service measurements without credentials or source assets."""

import json
import logging
from dataclasses import FrozenInstanceError, asdict

import pytest

from src.foundation.models.data.service_measurement import ServiceMeasurement


class TestServiceMeasurement:
    """Exercise arithmetic, validation, and normalized record integration."""

    @pytest.mark.parametrize(
        ("total", "degraded", "expected"),
        [
            (100, 0, 100.0),
            (100, 100, 0.0),
            (4, 1, 75.0),
            (3, 1, 200 / 3),
            (10**400, 10**399, 90.0),
            (None, None, None),
            (0, 0, None),
        ],
    )
    def test_percentage(self, total: int | None, degraded: int | None, expected: float | None) -> None:
        """Keep missing measurements separate from exact measured values."""
        measurement = ServiceMeasurement(total, degraded)
        if expected is None:
            assert measurement.percentage is None
        else:
            assert measurement.percentage == pytest.approx(expected)

    @pytest.mark.parametrize(
        ("total", "degraded"),
        [
            (-1, 0),
            (1, -1),
            (1, 2),
            (None, 0),
            (1, None),
            (True, 0),
            (1, False),
            (1.5, 1),
            (1, 0.5),
            (float("inf"), 0),
            (1, float("nan")),
            ("1", 0),
            (1, "0"),
        ],
    )
    def test_invalid_counts(self, total: object, degraded: object) -> None:
        """Reject malformed normalized records without coercing their values."""
        with pytest.raises(ValueError, match="Sample counts"):
            ServiceMeasurement(**{"total": total, "degraded": degraded})

    @pytest.mark.parametrize("field", ["total", "degraded"])
    def test_immutable_counts(self, field: str) -> None:
        """Prevent mutation after the measurement passes validation."""
        measurement = ServiceMeasurement(10, 2)
        with pytest.raises(FrozenInstanceError):
            setattr(measurement, field, 11)
        assert measurement.percentage == 80.0

    @pytest.mark.parametrize(("total", "degraded"), [(10, 2), (None, None), (0, 0)])
    def test_normalized_record_round_trip(self, total: int | None, degraded: int | None) -> None:
        """Preserve unavailable and measured states through JSON records."""
        original = ServiceMeasurement(total, degraded)
        record = json.loads(json.dumps(asdict(original)))
        restored = ServiceMeasurement(**record)
        assert asdict(restored) == {"total": total, "degraded": degraded}
        assert restored.percentage == original.percentage

    def test_validation_log_redaction(self, caplog: pytest.LogCaptureFixture) -> None:
        """Report invalid input without including its caller-supplied content."""
        supplied_value = "private caller content"
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError, match="Sample counts"):
            ServiceMeasurement(**{"total": supplied_value, "degraded": 0})
        assert supplied_value not in caplog.text
        assert "Validating service sample counts" in caplog.text
        assert "Sample counts must both be integers or both be absent" in caplog.text

"""Integration tests for drift detection (baseline -> drift -> alert) (T111)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from src.shared.config.constants import AlertSeverity, AlertType
from src.shared.services.diff import DIFF_CHANGE_TYPES, DiffService


class TestDriftDetectionIntegration:
    """Verify drift pipeline from baseline comparison to alert generation."""

    @pytest.fixture()
    def baseline_config(self) -> dict:
        return {
            "radio": {"band_24": {"power": 8, "channel": 1}},
            "ip_config": {"dns": ["8.8.8.8"]},
        }

    @pytest.fixture()
    def drifted_config(self) -> dict:
        return {
            "radio": {"band_24": {"power": 14, "channel": 1}},
            "ip_config": {"dns": ["8.8.8.8", "1.1.1.1"]},
        }

    def test_baseline_vs_drifted_produces_changes(
        self,
        baseline_config: dict,
        drifted_config: dict,
    ) -> None:
        svc = DiffService()
        result = svc.compute_diff(baseline_config, drifted_config)
        assert len(result.changes) > 0

    def test_no_drift_on_matching_config(
        self,
        baseline_config: dict,
    ) -> None:
        svc = DiffService()
        result = svc.compute_diff(baseline_config, baseline_config.copy())
        assert len(result.changes) == 0

    def test_alert_severity_enum_values(self) -> None:
        assert AlertSeverity.CRITICAL.value == "critical"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.INFO.value == "info"

    def test_alert_type_has_drift(self) -> None:
        assert AlertType.DRIFT.value == "drift"

    def test_drift_change_paths_are_descriptive(
        self,
        baseline_config: dict,
        drifted_config: dict,
    ) -> None:
        svc = DiffService()
        result = svc.compute_diff(baseline_config, drifted_config)
        for change in result.changes:
            assert len(change.path) > 0
            # This test asserted ("changed", "added", "removed"). DiffService never
            # emitted those three labels, so the test always failed. The narrower
            # set also loses the split between a value change and a type change.
            # The assertion now reads the exported vocabulary, so a new label must
            # join DIFF_CHANGE_TYPES before it can reach a drift alert.
            assert change.change_type in DIFF_CHANGE_TYPES

    def test_drift_summary_counts(
        self,
        baseline_config: dict,
        drifted_config: dict,
    ) -> None:
        svc = DiffService()
        result = svc.compute_diff(baseline_config, drifted_config)
        total = result.summary.fields_changed + result.summary.fields_added + result.summary.fields_removed
        assert total == len(result.changes)

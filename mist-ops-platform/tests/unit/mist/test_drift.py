"""Tests verifying drift scanner calls compute_diff on DiffService (T024).

Confirms the method name is compute_diff (not compute).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from src.worker.checks.drift import DriftScanner


class TestDriftCallsComputeDiff:
    """DriftScanner must call self._diff.compute_diff()."""

    def test_compute_diffs_calls_compute_diff(self) -> None:
        scanner = DriftScanner.__new__(DriftScanner)
        scanner._diff = MagicMock()
        scanner._diff.compute_diff.return_value = SimpleNamespace(
            changes=[{"path": "radio_config.band_24", "op": "replace"}],
        )

        baseline = MagicMock()
        baseline.config_payload = {"radio_config": {"band_24": {}}}

        revision = MagicMock()
        revision.config_blob = {"radio_config": {"band_24": {"power": 10}}}

        diffs = scanner._compute_diffs(baseline, revision)

        scanner._diff.compute_diff.assert_called_once_with(
            baseline.config_payload,
            revision.config_blob,
        )
        assert len(diffs) == 1

    def test_no_changes_returns_empty(self) -> None:
        scanner = DriftScanner.__new__(DriftScanner)
        scanner._diff = MagicMock()
        scanner._diff.compute_diff.return_value = SimpleNamespace(
            changes=[],
        )

        baseline = MagicMock()
        baseline.config_payload = {}
        revision = MagicMock()
        revision.config_blob = {}

        diffs = scanner._compute_diffs(baseline, revision)
        assert diffs == []

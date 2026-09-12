"""Unit tests for DiffService (T106)."""

from __future__ import annotations

import pytest

from src.shared.services.diff import DiffChange, DiffResult, DiffService, DiffSummary


class TestDiffChange:
    """Verify DiffChange data class."""

    def test_to_dict(self) -> None:
        change = DiffChange(
            path="root.radio.power",
            old_value=8,
            new_value=10,
            change_type="changed",
        )
        result = change.to_dict()
        assert result == {
            "path": "root.radio.power",
            "old_value": 8,
            "new_value": 10,
            "change_type": "changed",
        }

    def test_slots_prevent_arbitrary_attrs(self) -> None:
        change = DiffChange("p", None, None, "added")
        with pytest.raises(AttributeError):
            change.extra = "nope"  # type: ignore[attr-defined]


class TestDiffSummary:
    """Verify DiffSummary counters."""

    def test_initial_zeros(self) -> None:
        summary = DiffSummary()
        assert summary.fields_changed == 0
        assert summary.fields_added == 0
        assert summary.fields_removed == 0

    def test_to_dict(self) -> None:
        summary = DiffSummary()
        summary.fields_changed = 3
        assert summary.to_dict()["fields_changed"] == 3


class TestDiffService:
    """Verify DiffService.compute_diff() edge cases."""

    def setup_method(self) -> None:
        self.svc = DiffService()

    def test_identical_configs_yield_empty(self) -> None:
        config = {"radio": {"power": 10, "channel": 6}}
        result = self.svc.compute_diff(config, config.copy())
        assert len(result.changes) == 0
        assert result.summary.fields_changed == 0

    def test_single_field_change(self) -> None:
        old = {"radio": {"power": 8}}
        new = {"radio": {"power": 12}}
        result = self.svc.compute_diff(old, new)
        assert result.summary.fields_changed >= 1
        paths = [c.path for c in result.changes]
        assert any("power" in p for p in paths)

    def test_field_added(self) -> None:
        old = {"radio": {"power": 8}}
        new = {"radio": {"power": 8, "channel": 11}}
        result = self.svc.compute_diff(old, new)
        assert result.summary.fields_added >= 1

    def test_field_removed(self) -> None:
        old = {"radio": {"power": 8, "channel": 11}}
        new = {"radio": {"power": 8}}
        result = self.svc.compute_diff(old, new)
        assert result.summary.fields_removed >= 1

    def test_nested_change(self) -> None:
        old = {"a": {"b": {"c": 1}}}
        new = {"a": {"b": {"c": 2}}}
        result = self.svc.compute_diff(old, new)
        assert len(result.changes) == 1

    def test_empty_configs(self) -> None:
        result = self.svc.compute_diff({}, {})
        assert len(result.changes) == 0

    def test_complex_nested_structure(self) -> None:
        old = {
            "networks": {
                "vlan10": {"subnet": "10.0.10.0/24", "vlan_id": 10},
                "vlan20": {"subnet": "10.0.20.0/24", "vlan_id": 20},
            },
        }
        new = {
            "networks": {
                "vlan10": {"subnet": "10.0.10.0/24", "vlan_id": 10},
                "vlan20": {"subnet": "10.0.20.0/23", "vlan_id": 20},
            },
        }
        result = self.svc.compute_diff(old, new)
        assert result.summary.fields_changed >= 1

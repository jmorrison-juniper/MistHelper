"""Prove that the failure-field guard can reject each relevant defect."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.unit.upgrade_portal.strategy_failure_limit.markup import FailureFieldGuard


class TestFailureFieldGuard:
    """Exercise the guard decision independently from the template implementation."""

    @staticmethod
    def reference(strategy: str, percentage: int = 17) -> str:
        """Return one contract-shaped field for direct decision tests."""
        inactive = strategy == "big_bang"
        return (
            f'<div data-org-requires-strategy="canary rrm serial"{" hidden" if inactive else ""}>'
            '<label for="max-failure-percentage">Maximum failure percentage</label>'
            '<input type="number" min="0" max="100" id="max-failure-percentage" '
            'name="max_failure_percentage" data-testid="org-upgrade-max-failures" '
            f'value="{percentage}" required{" disabled" if inactive else ""}></div>'
        )

    @pytest.mark.parametrize("strategy", ["canary", "big_bang", "rrm", "serial"])
    @pytest.mark.parametrize("percentage", [0, 17, 100])
    def test_supported_initial_decisions(self, strategy: str, percentage: int) -> None:
        """The direct guard accepts all four specified initial states."""
        guard = FailureFieldGuard(self.reference(strategy, percentage))
        guard.require(strategy, percentage)
        assert guard.checked == 1

    @pytest.mark.parametrize(
        ("removed", "message"),
        [
            (' data-org-requires-strategy="canary rrm serial"', "strategy rule"),
            (" disabled", "enabled state"),
        ],
    )
    def test_negative_controls_fail(self, removed: str, message: str) -> None:
        """An absent rule or a hidden enabled input must fail after one measured field."""
        changed = self.reference("big_bang").replace(removed, "")
        guard = FailureFieldGuard(changed)
        with pytest.raises(AssertionError, match=message):
            guard.require("big_bang", 17)
        assert guard.checked == 1

    def test_an_empty_page_fails_with_zero_checked_fields(self) -> None:
        """No matching field must fail rather than produce empty success evidence."""
        guard = FailureFieldGuard("")
        with pytest.raises(AssertionError, match="exactly one failure field"):
            guard.require("big_bang", 17)
        assert guard.checked == 0

    def test_an_unreadable_input_fails(self, tmp_path: Path) -> None:
        """A missing input cannot enter the guard as an empty successful page."""
        path = tmp_path / "missing-template.html"
        with pytest.raises(FileNotFoundError, match="missing-template.html"):
            FailureFieldGuard.from_file(path)
        assert path.exists() is False

"""Wave 9 P2 coverage tests for src.audit._renderer_time.

Both epoch-formatter helpers have simple guard-then-strftime bodies, so
these tests hit both branches (sentinel 0 vs valid epoch) directly.
"""

from __future__ import annotations  # WHY: postponed eval for consistency with production modules

import pytest  # WHY: parametrized branch coverage of the two formatter functions

from src.audit._renderer_time import epoch_to_readable, epoch_to_short


class TestEpochToReadable:
    """Cover both branches of epoch_to_readable."""

    def test_zero_returns_na_sentinel(self) -> None:
        # WHY: falsy epoch triggers the 'no timestamp' shortcut path
        assert epoch_to_readable(0) == "N/A"

    def test_known_epoch_returns_canonical_utc_string(self) -> None:
        # WHY: 1_700_000_000 == 2023-11-14 22:13 UTC — canonical fixture used by existing tests
        result = epoch_to_readable(1_700_000_000)
        assert result == "2023-11-14 22:13 UTC"

    @pytest.mark.parametrize("epoch", [1, 946_684_800, 2_000_000_000])
    def test_various_positive_epochs_include_utc_marker(self, epoch: int) -> None:
        # WHY: exercise strftime branch with multiple epochs; assert stable UTC suffix
        assert epoch_to_readable(epoch).endswith(" UTC")


class TestEpochToShort:
    """Cover both branches of epoch_to_short."""

    def test_zero_returns_question_mark(self) -> None:
        # WHY: falsy epoch triggers the compact 'no timestamp' shortcut
        assert epoch_to_short(0) == "?"

    def test_known_epoch_returns_month_day_time(self) -> None:
        # WHY: 1_700_000_000 == 2023-11-14 22:13 UTC — verify compact format shape
        result = epoch_to_short(1_700_000_000)
        assert result == "11/14 22:13"

    @pytest.mark.parametrize("epoch", [1, 1_600_000_000, 1_800_000_000])
    def test_various_positive_epochs_contain_slash_and_colon(self, epoch: int) -> None:
        # WHY: strftime "%m/%d %H:%M" always contains the two literal separators
        rendered = epoch_to_short(epoch)
        assert "/" in rendered
        assert ":" in rendered

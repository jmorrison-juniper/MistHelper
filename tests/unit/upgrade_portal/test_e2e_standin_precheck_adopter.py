"""Prove that the E2E stand-in adopter obeys the rules of the shipped reader.

Why:
    Issue #3360. The browser tests replace the pre-check adopter with
    `PortalRecordStore.newest_precheck`. The shipped reader
    `latest_standalone_precheck` adopts only a verified pre-check that names no
    run, and it reads the newest start time first. These tests hold the
    stand-in to the same rules, so a browser journey can prove the standalone
    filter of Delta H3 (FR-103).

    Issue #3353. The pair reader must return the tier of that same capture.
    Its tier conversion must match production without changing the selection.
"""

from __future__ import annotations  # Keep annotations independent from import order.

from typing import Any  # A capture record holds values of different types.

import pytest  # Parametrize the rules that a capture can fail.

from src.upgrade_portal.capture.store import CAPTURE_STATE_FIELD, CaptureState
from tests.support.upgrade_portal_e2e.records import PortalRecordStore

OWNER = "e2e-unit-precheck-owner"  # The test owner that the store binds to each record.
SITE_ID = "site-precheck-one"  # The site that each read names.
OTHER_SITE_ID = "site-precheck-two"  # A site that no read names.
OLDER_STAMP = "2026-09-01T10:00:00+00:00"  # The start time of the older capture.
NEWER_STAMP = "2026-09-01T11:00:00+00:00"  # The start time of the newer capture.
OWNING_RUN = "run-precheck-0001"  # The run that owns a capture in the run filter tests.


def capture(capture_id: str, started_at: str = OLDER_STAMP, **fields: Any) -> dict[str, Any]:
    """Build one verified standalone pre-check of the site, with optional changes.

    Args:
        capture_id: The business key of the capture.
        started_at: The start time in ISO 8601 with a UTC offset.
        **fields: The fields that replace a default value.

    Returns:
        One capture record that the stand-in store accepts.
    """
    record: dict[str, Any] = {  # The shape of a standalone pre-check that the stand-in runner stores.
        "capture_id": capture_id,  # The key that the adopter returns.
        "site_id": SITE_ID,  # The site that the read names.
        "role": "pre",  # The pre-check half of the upgrade.
        "run_id": "",  # A standalone capture names no run.
        "capture_status": "complete",  # Content completeness does not decide pre-check eligibility.
        CAPTURE_STATE_FIELD: CaptureState.VERIFIED.value,  # The shipped reader requires verified lifecycle.
        "started_at": started_at,  # The sort key of the shipped query.
    }
    record.update(fields)  # Apply the change that one test needs.
    return record  # The caller writes the record into the store.


def store_with(*records: dict[str, Any]) -> PortalRecordStore:
    """Return a stand-in store that holds the records in the given order.

    Args:
        *records: The capture records, in the store order.

    Returns:
        The store, ready for one read.
    """
    store = PortalRecordStore(OWNER)  # A new store for each test, so no record crosses tests.
    for record in records:  # The store order follows the argument order.
        store.write_capture(record)  # Store one capture record.
    return store  # The test reads the adopted capture.


def test_a_capture_that_a_run_owns_is_not_adopted() -> None:
    """The shipped reader adopts no capture that a run owns, so the stand-in adopts none."""
    store = store_with(capture("cap-owned", run_id=OWNING_RUN))  # The only pre-check belongs to a run.
    assert store.newest_precheck(SITE_ID) == "", "The stand-in adopted a capture that a run owns."


def test_a_standalone_capture_is_adopted() -> None:
    """A verified standalone pre-check of the site is the adopted capture."""
    store = store_with(capture("cap-standalone"))  # The only pre-check names no run.
    assert store.newest_precheck(SITE_ID) == "cap-standalone", "The stand-in did not adopt the standalone capture."


def test_a_newer_capture_that_a_run_owns_loses_to_a_standalone_capture() -> None:
    """The run filter applies before the order, as in the shipped query."""
    store = store_with(  # The capture that a run owns is newer, and the store holds it last.
        capture("cap-standalone", OLDER_STAMP),
        capture("cap-owned", NEWER_STAMP, run_id=OWNING_RUN),
    )
    assert store.newest_precheck(SITE_ID) == "cap-standalone", "A capture that a run owns won the read."


def test_the_newest_start_time_wins_over_the_store_order() -> None:
    """The shipped query sorts by the start time, newest first."""
    store = store_with(capture("cap-newer", NEWER_STAMP), capture("cap-older", OLDER_STAMP))  # Older one last.
    assert store.newest_precheck(SITE_ID) == "cap-newer", "The store order decided the read, not the start time."


def test_a_capture_with_no_run_field_is_not_adopted() -> None:
    """The shipped query compares the run with an empty text, and a missing field does not match."""
    record = capture("cap-no-run")  # A standalone pre-check shape.
    del record["run_id"]  # Remove the field, so the shipped query reads null.
    store = store_with(record)  # The only pre-check holds no run field.
    assert store.newest_precheck(SITE_ID) == "", "The stand-in adopted a capture with no run field."


def test_a_capture_with_no_start_time_loses() -> None:
    """The shipped sort puts a missing start time below every text, so that capture loses."""
    record = capture("cap-no-start")  # A standalone pre-check shape.
    del record["started_at"]  # Remove the sort key.
    store = store_with(capture("cap-dated", OLDER_STAMP), record)  # The store holds the undated capture last.
    assert store.newest_precheck(SITE_ID) == "cap-dated", "A capture with no start time won the read."


@pytest.mark.parametrize(
    "change",
    [
        {"role": "post"},  # A post-check is never a baseline.
        {CAPTURE_STATE_FIELD: CaptureState.FAILED.value},  # An unverified lifecycle cannot supply the baseline.
        {"site_id": OTHER_SITE_ID},  # A capture of another site.
    ],
    ids=["post-check", "not-verified", "other-site"],
)
def test_a_capture_that_fails_another_rule_is_not_adopted(change: dict[str, str]) -> None:
    """The role rule, the verified rule, and the site rule stay as before."""
    store = store_with(capture("cap-refused", **change))  # The only capture fails one rule.
    assert store.newest_precheck(SITE_ID) == "", f"The stand-in adopted a capture with {change}."


def test_the_store_order_decides_a_tie() -> None:
    """Two equal start times keep the old answer: the capture that the store holds last."""
    store = store_with(capture("cap-first", NEWER_STAMP), capture("cap-last", NEWER_STAMP))  # Equal start times.
    assert store.newest_precheck(SITE_ID) == "cap-last", "A tie did not keep the capture that the store holds last."


class TestPrecheckTierReader:
    """Prove the selected capture identifier and its production tier contract."""

    @pytest.mark.parametrize(
        ("raw_tier", "expected_tier"),
        [(2, 2), (3, 3), ("2", 2), ("3", 3), (" 3 ", 3), (3.9, 3)],
        ids=["standard", "extended", "standard-text", "extended-text", "padded-text", "production-integer-conversion"],
    )
    def test_returns_the_stored_tier(self, raw_tier: Any, expected_tier: int) -> None:
        """The reader returns the selected identifier and the converted stored tier."""
        store = store_with(capture("cap-tier", tier=raw_tier))
        assert store.newest_precheck_tier(SITE_ID) == ("cap-tier", expected_tier)

    @pytest.mark.parametrize(
        "fields",
        [
            {},
            {"tier": None},
            {"tier": ""},
            {"tier": "three"},
            {"tier": "3.5"},
            {"tier": True},
            {"tier": False},
            {"tier": 0},
            {"tier": 1},
            {"tier": 4},
            {"tier": -1},
            {"tier": []},
            {"tier": {}},
        ],
        ids=[
            "missing",
            "null",
            "empty-text",
            "invalid-text",
            "fraction-text",
            "true",
            "false",
            "zero",
            "unknown-low",
            "unknown-high",
            "negative",
            "list",
            "mapping",
        ],
    )
    def test_uses_the_production_default_for_an_unusable_tier(self, fields: dict[str, Any]) -> None:
        """A missing or unusable tier preserves the selected identifier and uses tier 2."""
        store = store_with(capture("cap-default", **fields))
        assert store.newest_precheck_tier(SITE_ID) == ("cap-default", 2)

    def test_returns_the_tier_of_the_selected_newest_standalone_capture(self) -> None:
        """The pair reader preserves the existing origin filter and start-time order."""
        store = store_with(
            capture("cap-newer", NEWER_STAMP, tier=3),
            capture("cap-older", OLDER_STAMP, tier=2),
            capture("cap-owned", "2026-09-01T12:00:00+00:00", tier=2, run_id=OWNING_RUN),
        )
        assert store.newest_precheck(SITE_ID) == "cap-newer"
        assert store.newest_precheck_tier(SITE_ID) == ("cap-newer", 3)

    def test_returns_the_tier_of_the_existing_tie_winner(self) -> None:
        """Equal start times keep the last stored capture and its own tier."""
        store = store_with(
            capture("cap-first", NEWER_STAMP, tier=2),
            capture("cap-last", NEWER_STAMP, tier=3),
        )
        assert store.newest_precheck(SITE_ID) == "cap-last"
        assert store.newest_precheck_tier(SITE_ID) == ("cap-last", 3)

    @pytest.mark.parametrize(
        "records",
        [
            (),
            (
                capture("cap-other-site", tier=3, site_id=OTHER_SITE_ID),
                capture("cap-post", tier=3, role="post"),
                capture("cap-failed", tier=3, state=CaptureState.FAILED.value),
                capture("cap-owned", tier=3, run_id=OWNING_RUN),
            ),
        ],
        ids=["empty-store", "no-eligible-capture"],
    )
    def test_returns_no_identifier_and_the_default_without_a_capture(self, records: tuple[dict[str, Any], ...]) -> None:
        """If no capture matches, the reader returns an empty identifier and tier 2."""
        store = store_with(*records)
        assert store.newest_precheck_tier(SITE_ID) == ("", 2)

"""Prove that the E2E stand-in adopter obeys the rules of the shipped reader.

Why:
    Issue #3360. The browser tests replace the pre-check adopter with
    `PortalRecordStore.newest_precheck`. The shipped reader
    `latest_standalone_precheck` adopts only a verified pre-check that names no
    run, and it reads the newest start time first. These tests hold the
    stand-in to the same rules, so a browser journey can prove the standalone
    filter of Delta H3 (FR-103).
"""

from __future__ import annotations  # Keep annotations independent from import order.

from typing import Any  # A capture record holds values of different types.

import pytest  # Parametrize the rules that a capture can fail.

from tests.support.upgrade_portal_e2e import PortalRecordStore  # The stand-in store under test.

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
        "capture_status": "verified",  # The field that the stand-in reads for a verified capture.
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
        {"capture_status": "failed"},  # A failed capture is not verified in either field.
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

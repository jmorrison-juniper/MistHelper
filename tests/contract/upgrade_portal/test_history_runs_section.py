"""Contract tests for the runs section of the history page.

Why:
    Issue #2199 records the gap. The history page listed stored captures alone.
    It held no upgrade run, so an operator who wanted to reach a run that is
    scheduled, running, or failed had no page to read.

    The moment matters as much as the row. The store writes the offset of the
    machine that started the run, so two runs of one afternoon can read as two
    different hours. Every moment of this page therefore reads as UTC.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from src.upgrade_portal.app.routes import review

# One stored run of each state that the issue names. The record shape copies a
# real document of the ArangoDB collection, offset and all.
STORED_RUNS: tuple[dict[str, Any], ...] = (
    {
        "run_id": "run-scheduled",
        "site_name": "Morrison House Site",
        "site_id": "site-1",
        "state": "scheduled",
        "targets": [{"mac": "a"}, {"mac": "b"}],
        "created_at": "2026-09-02T08:49:45.214567-07:00",
        "updated_at": "2026-09-02T08:49:45.214567-07:00",
        "pre_capture_id": "cap-1",
        "post_capture_id": None,
    },
    {
        "run_id": "run-running",
        "site_name": "Morrison House Site",
        "site_id": "site-1",
        "state": "running",
        "targets": [{"mac": "a"}],
        "created_at": "2026-09-02T09:00:00+00:00",
        "updated_at": "2026-09-02T09:05:00+00:00",
        "pre_capture_id": "cap-2",
        "post_capture_id": None,
    },
    {
        "run_id": "run-failed",
        "site_name": "Morrison House Site",
        "site_id": "site-1",
        "state": "failed",
        "targets": [{"mac": "a"}, {"mac": "b"}, {"mac": "c"}],
        "created_at": "2026-09-01T10:00:00+00:00",
        "updated_at": "2026-09-01T10:30:00+00:00",
        "pre_capture_id": "cap-3",
        "post_capture_id": "cap-4",
    },
    {
        "run_id": "run-succeeded",
        "site_name": "Morrison House Site",
        "site_id": "site-1",
        "state": "succeeded",
        "targets": [{"mac": "a"}],
        "created_at": "2026-08-31T22:00:00+00:00",
        "updated_at": "2026-08-31T22:40:00+00:00",
        "pre_capture_id": "cap-5",
        "post_capture_id": "cap-6",
    },
)

# A record written before the state field existed. The page must name it and
# never hide the row, because that run still happened.
RUN_WITH_NO_STATE: dict[str, Any] = {
    "run_id": "run-old",
    "site_id": "site-1",
    "created_at": "2026-08-01T12:00:00+00:00",
}

# Any epoch second of the last few years reads as ten digits. No column of this
# page may show one.
EPOCH_PATTERN = re.compile(r"\b1[78]\d{8}\b")


@pytest.mark.parametrize("record", STORED_RUNS, ids=lambda record: str(record["state"]))
def test_a_run_row_names_its_state(record: dict[str, Any]) -> None:
    """The section names a scheduled, a running, a failed, and a succeeded run.

    Args:
        record: The stored run under test.
    """
    assert review.run_history_row(record)["state"] == record["state"]


def test_a_run_with_no_state_reads_as_unknown() -> None:
    """A run stored before the state field must appear, and never vanish.

    Why:
        A hidden row tells the operator that the run never happened. An unknown
        state tells the truth, which is that the record names none.
    """
    assert review.run_history_row(RUN_WITH_NO_STATE)["state"] == review.UNKNOWN_RUN_STATE


def test_a_run_row_counts_its_devices() -> None:
    """The row states how many devices the run acts on."""
    assert review.run_history_row(STORED_RUNS[2])["device_count"] == 3


def test_a_run_row_carries_both_capture_keys() -> None:
    """Each row links to the capture from before and the capture from after."""
    row = review.run_history_row(STORED_RUNS[2])
    assert row["pre_capture_id"] == "cap-3"
    assert row["post_capture_id"] == "cap-4"


def test_a_started_moment_reads_as_utc() -> None:
    """A stored offset must reach the page as UTC, never as the local hour.

    Why:
        The store wrote `2026-09-02T08:49:45-07:00`, which is 15:49 UTC. A page
        that showed the stored hour would place this run before a run that
        really came first.
    """
    assert review.run_history_row(STORED_RUNS[0])["started_text"] == "2026-09-02 15:49 UTC"


def test_a_live_run_names_no_end_moment() -> None:
    """A run that still runs has not ended, so the column stays empty."""
    assert review.run_history_row(STORED_RUNS[1])["ended_text"] == ""


def test_a_finished_run_names_its_end_moment() -> None:
    """A run that ended names when it ended."""
    assert review.run_history_row(STORED_RUNS[2])["ended_text"] == "2026-09-01 10:30 UTC"


@pytest.mark.parametrize("record", STORED_RUNS, ids=lambda record: str(record["state"]))
def test_no_column_shows_an_epoch_second(record: dict[str, Any]) -> None:
    """Every moment reads as a human date, so no cell holds an epoch second.

    Args:
        record: The stored run under test.
    """
    row = review.run_history_row(record)
    assert not EPOCH_PATTERN.search(row["started_text"])
    assert not EPOCH_PATTERN.search(row["ended_text"])

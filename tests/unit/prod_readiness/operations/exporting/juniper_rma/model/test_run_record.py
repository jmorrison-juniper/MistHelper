"""Tests for the run record: the status transitions, the counters, and the reason text (data-model.md)."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable.

from src.operations.exporting.juniper_rma.model.run_record import RunRecord  # WHY: the run record under test.


def test_a_new_record_is_running_and_each_record_has_its_own_identifier() -> None:
    """A new record starts in the running state, and two records never share an identifier."""
    first = RunRecord("juniper_rma_correlation")  # WHY: the first run.
    second = RunRecord("juniper_rma_correlation")  # WHY: a second run for the uniqueness check.
    assert first.status == "running"  # WHY: the run starts in the running state.
    assert first.run_id != second.run_id  # WHY: each run has its own identifier.


def test_each_known_status_adds_one_and_an_unknown_status_changes_nothing() -> None:
    """The matched, unmatched, ambiguous, and failed counters each move by one per outcome."""
    record = RunRecord("juniper_rma_correlation")  # WHY: a fresh record.
    for outcome in ("matched", "matched", "unmatched", "ambiguous", "failed", "bogus"):  # WHY: one unknown.
        record.record_outcome(outcome)  # WHY: count each outcome.
    counts = (  # WHY: the four counters in one tuple.
        record.matched_count,
        record.unmatched_count,
        record.ambiguous_count,
        record.failed_count,
    )
    assert counts == (2, 1, 1, 1)  # WHY: the unknown value added nothing.


def test_requests_accumulate_across_calls() -> None:
    """The request count adds each call, and the default step is one call."""
    record = RunRecord("juniper_rma_correlation")  # WHY: a fresh record.
    record.add_requests()  # WHY: the default step of one call.
    record.add_requests(4)  # WHY: four more calls.
    assert record.request_count == 5  # WHY: five calls in total.


def test_finish_without_notes_is_complete_and_sets_the_end_time() -> None:
    """A run with no notes finishes complete and records its end time."""
    record = RunRecord("juniper_rma_correlation")  # WHY: a run with no problems.
    record.finish()  # WHY: finish with the default status rule.
    assert record.status == "complete"  # WHY: no notes means the run was whole.
    assert record.ended_at >= record.started_at  # WHY: the end time is not before the start.


def test_finish_with_a_note_is_incomplete() -> None:
    """A note of a problem makes the default final status incomplete."""
    record = RunRecord("juniper_rma_correlation")  # WHY: a run with one problem.
    record.note_problem("A detail call failed")  # WHY: record the reason.
    record.finish()  # WHY: finish with the default status rule.
    assert record.status == "incomplete"  # WHY: the note means the run was not whole.


def test_an_explicit_status_wins_over_the_notes() -> None:
    """A failed run keeps the failed status even when it has notes."""
    record = RunRecord("juniper_rma_correlation")  # WHY: a run that failed.
    record.note_problem("The request list failed")  # WHY: a reason exists.
    record.finish(status="failed")  # WHY: the caller names the status.
    assert record.status == "failed"  # WHY: the explicit status is kept.


def test_long_reasons_are_cut_to_two_hundred_characters() -> None:
    """A reason longer than 200 characters keeps only its first 200 characters."""
    record = RunRecord("juniper_rma_correlation")  # WHY: a run with a long reason.
    record.note_problem("x" * 500)  # WHY: a reason well above the limit.
    assert len(record.problems[0]) == 200  # WHY: the stored reason is bounded.


def test_as_row_joins_the_reasons_and_carries_the_counts() -> None:
    """The export row joins the reasons with a semicolon and carries the count and the status."""
    record = RunRecord("juniper_rma_correlation")  # WHY: a run with two reasons.
    record.record_outcome("matched")  # WHY: one matched ticket.
    record.note_problem("first reason")  # WHY: the first reason.
    record.note_problem("second reason")  # WHY: the second reason.
    record.finish()  # WHY: the final status.
    row = record.as_row()  # WHY: the export row under test.
    assert row["reason"] == "first reason; second reason"  # WHY: the reasons are joined in order.
    assert (row["matchedCount"], row["status"]) == (1, "incomplete")  # WHY: the count and the status.

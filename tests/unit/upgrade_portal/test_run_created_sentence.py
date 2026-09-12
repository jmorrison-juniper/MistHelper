"""Proof that the run sentence follows the run and not the state word (issue #2105).

Why:
    The run page printed two answers at once. The state block read `The run is
    ready. The pre-check capture has not started.` while the capture block read
    the identifier of a saved pre-check capture. The operator could not tell
    which half of one page was true.

    A run stays in the `created` state after the pre-check capture finishes,
    because only a start of the upgrade moves the state. `RunStatusView` mapped
    the state word to one fixed sentence, so the sentence described the word and
    never the run.

    The repair reads the run. A `created` run with a saved pre-check capture now
    names the next step, and a `created` run with no capture keeps the old
    sentence.

No network:
    Every test below calls a pure class method with a plain dictionary. No test
    reaches a cloud, a Redis server, or a database.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

from typing import Any  # A stored run record is a free-form mapping.

import pytest  # The test framework of the project.

from src.upgrade_portal.runtime.runs import RunState, RunStatusView  # The unit under test.

# WHY: The capture of the issue report. Any non-empty text proves the same rule.
PRE_CAPTURE_ID = "cap-0eb57df4b3e445e6b179efc6953a271d-01"

# WHY: The sentence for a run that has not read the site yet.
READY_SENTENCE = "The run is ready. The pre-check capture has not started."

# WHY: The sentence for a run that holds a saved pre-check capture. It names the
# next step, because the operator chooses the upgrade options after the capture.
SAVED_SENTENCE = "The pre-check capture is saved. Choose the upgrade options next."


def run_record(**fields: Any) -> dict[str, Any]:
    """Build one run record with the fields that the sentence reads.

    Why:
        `RunStatusView.message` reads the state and the capture identifiers. A
        whole record would add fields that no test here reads, and a reader
        would then have to guess which field drives the answer.

    Args:
        **fields: The fields to write over the defaults.

    Returns:
        The run record.
    """
    record: dict[str, Any] = {  # The three fields that the sentence reads.
        "run_id": "run-0eb57df4b3e445e6b179efc6953a271d",  # Names the run in each log line.
        "state": RunState.CREATED.value,  # The state that held the defect.
        "pre_capture_id": None,  # Empty until the pre-check capture saves.
    }
    record.update(fields)  # The test writes over any default it cares about.
    return record


def sentence(record: dict[str, Any]) -> str:
    """Return the sentence that the run page shows for one record.

    Args:
        record: The stored run record.

    Returns:
        The sentence, built the way the status endpoint builds it.
    """
    view = RunStatusView()  # The view holds no state, so one instance serves every test.
    return view.message(record, view.phases(record))  # The same call that `build` makes.


class TestTheCreatedSentence:
    """The `created` state answers with the sentence that fits the run."""

    def test_a_run_with_no_pre_check_capture_reads_as_ready(self) -> None:
        """A fresh run keeps the sentence that invites the first capture."""
        assert sentence(run_record()) == READY_SENTENCE

    def test_a_run_with_a_saved_pre_check_capture_names_the_next_step(self) -> None:
        """This is the defect of issue #2105.

        Why:
            The page named the capture and denied it in the same view. The
            sentence must now agree with the capture block below it.
        """
        assert sentence(run_record(pre_capture_id=PRE_CAPTURE_ID)) == SAVED_SENTENCE

    def test_an_empty_identifier_reads_as_no_capture(self) -> None:
        """An empty text is not a saved capture.

        Why:
            A store that writes an empty string instead of a null value must
            not make the page claim a capture that no operator can open.
        """
        assert sentence(run_record(pre_capture_id="")) == READY_SENTENCE

    def test_a_blank_identifier_reads_as_no_capture(self) -> None:
        """A text of spaces is not a saved capture either."""
        assert sentence(run_record(pre_capture_id="   ")) == READY_SENTENCE

    def test_the_status_body_carries_the_new_sentence(self) -> None:
        """The whole status body carries the sentence, and not the method alone.

        Why:
            The browser reads the `message` key of the body. A repair inside the
            method that never reached the body would leave the page unchanged.
        """
        body = RunStatusView().build(run_record(pre_capture_id=PRE_CAPTURE_ID))
        assert body["message"] == SAVED_SENTENCE  # The page reads this key.
        assert body["pre_capture_id"] == PRE_CAPTURE_ID  # The capture block reads this key.

    def test_a_driver_sentence_still_wins(self) -> None:
        """A sentence from the driver still replaces the sentence of the view.

        Why:
            The driver knows more than the record. The repair must not take the
            voice of the driver away.
        """
        body = RunStatusView().build(run_record(pre_capture_id=PRE_CAPTURE_ID), "The portal reads the site.")
        assert body["message"] == "The portal reads the site."  # The driver still speaks first.


class TestEveryOtherStateKeepsItsSentence:
    """A saved pre-check capture changes the `created` state and no other."""

    @pytest.mark.parametrize(
        "state",
        [state for state in RunState if state is not RunState.CREATED],  # Every state but the one under repair.
    )
    def test_the_sentence_matches_the_state_table(self, state: RunState) -> None:
        """Each other state answers with the sentence of the state table.

        Why:
            The repair reads one field of the record. A repair that reached a
            second state would change a sentence that no issue reported.

        Args:
            state: The run state under test.
        """
        record = run_record(state=state.value, pre_capture_id=PRE_CAPTURE_ID)  # A capture is saved.
        assert sentence(record) == RunStatusView.STATE_MESSAGES[state.value]  # The table still wins.

    def test_an_unknown_state_still_reads_as_in_progress(self) -> None:
        """A state outside the model keeps the neutral sentence.

        Why:
            A stored record from a later release can carry a state that this
            release does not know. The page must still print plain words.
        """
        record = run_record(state="a state of a later release", pre_capture_id=PRE_CAPTURE_ID)
        assert sentence(record) == "The run is in progress."  # The neutral answer of the view.

"""Unit tests for the one Cancellation text of a multi-site child job.

Why:
    Issue #3225. The page printed the cancel status word and the message with
    no separator. The poll then printed a second format with other labels, so
    the text changed after the first poll. The server now builds one text, and
    the page and the poll print it.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.upgrade_portal.upgrade.org_cancel_text import OrgCancelText

STOPPED = "The cloud stopped 1 device(s), and no device was writing firmware."  # The sentence of a site cancel.


@pytest.mark.parametrize("cancellation", [None, {}, "requested", ["requested"]])
def test_a_child_job_with_no_cancel_result_gives_no_text(cancellation: Any) -> None:
    """The cell stays empty, so the page never implies a cancel request."""
    assert OrgCancelText.text(cancellation) == ""  # No result, and no invented words.


def test_the_text_labels_the_status_and_keeps_the_exact_message() -> None:
    """The status word gets a label, and the message keeps the exact cloud words."""
    text = OrgCancelText.text({"status": "requested", "message": STOPPED})  # A result with no list.
    assert text == f"Status: requested. {STOPPED}"  # One space between the two parts.


def test_the_three_lists_use_the_headings_of_the_outcome_panel() -> None:
    """Each list uses the words of its panel heading, in the panel order."""
    cancellation = {  # A result that holds each list.
        "status": "requested",
        "message": STOPPED,
        "cancelled": ["001122334455", "001122334466"],
        "already_writing": ["001122334477"],
        "no_cancel_available": ["001122334488"],
    }
    assert OrgCancelText.text(cancellation) == (
        f"Status: requested. {STOPPED} Cancelled: 001122334455, 001122334466. "
        "Writing firmware: 001122334477. No cancel available: 001122334488."
    )


def test_an_empty_part_leaves_no_empty_label() -> None:
    """An empty status, an empty message, or an empty list adds no words."""
    cancellation = {"status": "", "message": "", "cancelled": [], "already_writing": ["001122334477"]}
    assert OrgCancelText.text(cancellation) == "Writing firmware: 001122334477."  # Only the filled part.


def test_a_list_value_that_is_not_a_list_adds_no_words() -> None:
    """A damaged list adds nothing, so the text never shows a wrong device."""
    cancellation = {"status": "unknown", "cancelled": "001122334455", "no_cancel_available": None}
    assert OrgCancelText.text(cancellation) == "Status: unknown."  # The damaged lists add no words.

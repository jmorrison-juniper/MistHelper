"""The lifecycle word that a stored capture sends to the capture page (issue #3378).

Why:
    The capture page asks the status endpoint every 3 seconds, and it stops when
    `state` holds a finished word. A restart or a trim empties the progress
    memory, so the endpoint then reads the stored capture through
    `stored_progress`.

    That function used to copy the content word `capture_status` into `state`.
    The shipped store writes `complete`, `partial`, or `failed` there. The page
    does not stop on `complete` or `partial`, so one open tab read the whole
    capture document from the store every 3 seconds and never stopped.

    The live path sends `verified` when the read-back matched and `failed` in
    every other case. These tests pin the same rule on the stored path.

No network:
    Every test calls a pure function with a plain dictionary, or reads one file
    of the source tree. No test reaches a cloud, a Redis server, or a database.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import re  # The page constant is read out of the script text.
from pathlib import Path  # The script path is built without a hard-coded separator.
from typing import Any  # A stored capture document is a free-form mapping.

import pytest  # The test framework.

from src.upgrade_portal.app.routes import capture  # The module under test.

CAPTURE_ID = "cap-3378aaaabbbbccccddddeeeeffff0000-01"  # A capture key in the shipped form.
VERIFIED_WORD = "verified"  # The live path sends this word after a matching read-back.
FAILED_WORD = "failed"  # The live path sends this word in every other case.
CONTENT_WORDS = ("complete", "partial", "failed")  # `resolve_status` writes one of these into `capture_status`.
LOST_SECTION = "clients_guest"  # A section that a partial capture did not read.
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]  # The test sits three folders below the root.
SCRIPT_PATH = REPOSITORY_ROOT.joinpath("src", "upgrade_portal", "app", "assets", "static", "js", "portal.js")
FINISHED_PATTERN = re.compile(r"var FINISHED_STATES = \[([^\]]*)\];")  # The one list that ends both capture polls.


def stored_document(content_word: str | None, **changes: Any) -> dict[str, Any]:
    """Build one stored capture document in the shipped shape.

    Args:
        content_word: The `capture_status` value, or None for a document that holds no such field.
        **changes: Fields that replace the defaults.

    Returns:
        The document.
    """
    document: dict[str, Any] = {  # The fields that `stored_progress` reads, with shipped values.
        "capture_id": CAPTURE_ID,  # The key that the page polls.
        "tier": 2,  # Tier 2 skips the extra sections.
        "state": VERIFIED_WORD,  # The store writes this lifecycle word after a matching read-back.
        "counts": {"devices_total": 3},  # A small site.
        "partial_reasons": [],  # A complete capture lost nothing.
    }
    if content_word is not None:  # An older document may hold no content word at all.
        document["capture_status"] = content_word  # The content word of the shipped store.
    document.update(changes)  # The caller changes the fields that its case needs.
    return document  # One document for one case.


def page_finished_words() -> list[str]:
    """Read the words that end the capture poll out of the page script.

    Returns:
        The words of `FINISHED_STATES`, in script order.
    """
    text = SCRIPT_PATH.read_text(encoding="utf-8")  # The script that the portal serves.
    found = FINISHED_PATTERN.search(text)  # The list that both capture readers use.
    assert found is not None, f"{SCRIPT_PATH} holds no FINISHED_STATES list."  # A rename must fail here.
    return re.findall(r'"([^"]+)"', found.group(1))  # The quoted words inside the list.


class TestAStoredCaptureThatReadsBack:
    """A stored capture that the portal read back unchanged sends `verified`."""

    def test_a_complete_capture_sends_verified(self) -> None:
        """The shipped store writes `complete` for a capture that lost nothing."""
        progress = capture.stored_progress(stored_document("complete"), True)  # The read-back holds.
        assert progress["state"] == VERIFIED_WORD  # The page stops the poll on this word.
        assert progress["verified"] is True  # The badge reads Verified.

    def test_a_partial_capture_sends_verified_and_keeps_the_lost_sections(self) -> None:
        """A partial capture still stored and read back, so it ends as `verified`."""
        reasons = [{"section": LOST_SECTION, "reason": "cloud_call_failed", "http_status": 0}]  # One lost section.
        document = stored_document("partial", partial_reasons=reasons)  # The shipped partial shape.
        progress = capture.stored_progress(document, True)  # The read-back holds.
        assert progress["state"] == VERIFIED_WORD  # The live path sends the same word for a partial capture.
        assert progress["partial_reasons"] == reasons  # The partial warning of the page reads this list.
        assert progress["sections"][LOST_SECTION] == capture.SECTION_FAILED  # The section row shows the loss.


class TestAStoredCaptureThatCannotJoinAComparison:
    """A stored capture that this release cannot compare sends `failed`."""

    @pytest.mark.parametrize(
        "document",
        [
            stored_document("complete", state="writing"),  # A worker stopped during the write.
            stored_document("complete", schema_version=99),  # A later release wrote the document.
            stored_document("failed", state="write_failed"),  # The write itself failed.
        ],
        ids=["lifecycle-not-verified", "schema-too-new", "write-failed"],
    )
    def test_the_capture_sends_failed(self, document: dict[str, Any]) -> None:
        """The start button returns, so the operator can take a new capture."""
        progress = capture.stored_progress(document, False)  # The store refused the comparison.
        assert progress["state"] == FAILED_WORD  # The page stops the poll and offers a new capture.
        assert progress["verified"] is False  # The badge reads Not verified.


@pytest.mark.parametrize("comparable", [True, False], ids=["reads-back", "refused"])
@pytest.mark.parametrize("content_word", [*CONTENT_WORDS, None], ids=[*CONTENT_WORDS, "absent"])
def test_every_stored_capture_sends_a_word_that_ends_the_poll(content_word: str | None, comparable: bool) -> None:
    """FR-001 and FR-002: the lifecycle word ends the poll and agrees with the flag."""
    progress = capture.stored_progress(stored_document(content_word), comparable)  # One case of the grid.
    assert progress["state"] in page_finished_words()  # The capture page and the multi-site card both stop.
    assert (progress["state"] == VERIFIED_WORD) is comparable  # The word and the flag never disagree.


def test_the_stored_document_keeps_its_content_word() -> None:
    """FR-003: the history page and the comparison page still read `capture_status`."""
    document = stored_document("partial")  # The content word that the history page shows.
    capture.stored_progress(document, True)  # The status body is built from the document.
    assert document["capture_status"] == "partial"  # The function changed no stored field.


def test_the_page_script_ends_the_poll_on_both_words_of_the_server() -> None:
    """The server words and the page words must stay in step, or the poll runs again."""
    words = page_finished_words()  # The words that end the page poll.
    assert VERIFIED_WORD in words  # A stored capture that reads back.
    assert FAILED_WORD in words  # A stored capture that this release cannot compare.

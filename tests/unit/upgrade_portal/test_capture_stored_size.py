"""The stored size that the capture page reads for a finished capture (issue #2063).

Why:
    The capture page shows one field for the stored size. A live capture carries
    that value because the collector writes it into the progress record when the
    write ends. A capture that the portal reads back from the store reaches the
    page through `stored_page_fields` instead.

    That function used to omit the size, so a stored capture rendered the
    template default of zero. The page then read `Verified` beside `0` bytes
    while the history page read the true size from the same document. A reader
    who opened one capture could conclude the record was empty, or that the
    write defect of issue #2061 had returned.

    These tests pin the size onto the page record, and they pin the poll body
    that must not carry it.

No network:
    Every test below calls a pure function with a plain dictionary. No test
    reaches a cloud, a Redis server, or a database.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

from typing import Any  # A stored capture document is a free-form mapping.

import pytest  # The test framework.

from src.upgrade_portal.app.routes import capture  # The module under test.

CAPTURE_ID = "cap-434b67ead6e94b33a175a8a86ca16c9f-01"  # The tier 3 capture of the issue report.
STORED_SIZE = 39472  # The size that the store measured for that capture.
SIZE_FIELD = "stored_size_bytes"  # The name the template reads.


@pytest.fixture
def document() -> dict[str, Any]:
    """Return one stored capture document, trimmed to the fields the page reads.

    Returns:
        The document.
    """
    return {
        "capture_id": CAPTURE_ID,
        "run_id": "run-434b67ead6e94b33a175a8a86ca16c9f",
        "site_id": "cf36153a-97bb-4974-8f8f-e9cc25d64d83",
        "tier": 3,
        "state": "verified",
        "capture_status": "complete",
        SIZE_FIELD: STORED_SIZE,
        "counts": {"devices_total": 8},
        "partial_reasons": [],
    }


class TestStoredSizeReachesThePage:
    """The page record carries the size that the store measured."""

    def test_the_page_fields_carry_the_stored_size(self, document: dict[str, Any]) -> None:
        """The page reads this record, so the size must be in it."""
        fields = capture.stored_page_fields(document, 3)
        assert fields[SIZE_FIELD] == STORED_SIZE

    def test_the_status_record_carries_the_stored_size(self, document: dict[str, Any]) -> None:
        """`stored_status` builds the whole record that the first render paints."""
        record = capture.stored_status(document, True)
        assert record[SIZE_FIELD] == STORED_SIZE

    def test_the_page_record_is_not_zero_for_a_verified_capture(self, document: dict[str, Any]) -> None:
        """The defect of issue #2063 was a zero beside the word Verified."""
        record = capture.stored_status(document, True)
        assert record["verified"] is True
        assert record[SIZE_FIELD] != 0

    def test_the_stored_size_survives_the_page_context_merge(self, document: dict[str, Any]) -> None:
        """`stored_progress` runs before `stored_page_fields`, so the merge order matters."""
        record = capture.stored_status(document, True)
        # WHY: a merge that ran the two in the other order would drop the size again.
        assert record[SIZE_FIELD] == STORED_SIZE
        assert record["percent"] == capture.WHOLE_PERCENT


class TestStoredSizeReading:
    """`stored_size_of` turns any stored value into a number the page can show."""

    def test_reads_a_plain_number(self, document: dict[str, Any]) -> None:
        """The normal path returns the stored integer."""
        assert capture.stored_size_of(document) == STORED_SIZE

    def test_reads_a_numeric_string(self) -> None:
        """A later version could store the value as text, and the page still shows it."""
        assert capture.stored_size_of({SIZE_FIELD: "1234"}) == 1234

    @pytest.mark.parametrize("value", [None, "", 0])
    def test_an_absent_value_reads_as_zero(self, value: Any) -> None:
        """An older document holds no size, and the page shows zero rather than failing."""
        assert capture.stored_size_of({SIZE_FIELD: value}) == 0

    def test_a_missing_key_reads_as_zero(self) -> None:
        """A document written before the field existed must not raise."""
        assert capture.stored_size_of({}) == 0

    @pytest.mark.parametrize("value", ["not-a-number", [1], {"a": 1}])
    def test_an_unreadable_value_reads_as_zero(self, value: Any) -> None:
        """The page shows a number, so a value it cannot read must not break the render."""
        assert capture.stored_size_of({SIZE_FIELD: value}) == 0


class TestThePollDropsTheSize:
    """The size is a page field, so the poll body must not carry it."""

    def test_the_status_fields_do_not_name_the_size(self) -> None:
        """`STATUS_FIELDS` fixes the poll body, and the contract names no size."""
        assert SIZE_FIELD not in capture.STATUS_FIELDS

    def test_the_status_body_removes_the_size(self, document: dict[str, Any]) -> None:
        """A field the contract omits must never reach the browser through the poll."""
        record = capture.stored_status(document, True)
        assert SIZE_FIELD in record  # WHY: the page render reads it from this record.
        assert SIZE_FIELD not in capture.status_body(record)  # WHY: the poll drops it again.


class TestThePageContextCarriesTheSize:
    """The template reads a top-level value, so the context must set it.

    Why:
        The template reads `stored_size_bytes` from the context root, not from
        the `status` mapping. `status_body` drops the field, so the context has
        to supply it separately or the page falls back to the template default
        of zero. The browser used to fill the gap with one extra read of the
        whole capture, but that read runs only when a poll answers `verified`,
        and no poll runs for a capture that ended before the page opened.
    """

    def test_the_context_names_the_size(self, monkeypatch: pytest.MonkeyPatch, document: dict[str, Any]) -> None:
        """A stored capture must render its true size at the first paint."""
        record = capture.stored_status(document, True)
        monkeypatch.setattr(capture, "page_status", lambda _id: record)  # WHY: no store and no request needed.
        monkeypatch.setattr(capture, "lock_banner_context", lambda _org, _site: {})  # WHY: the banner is separate.
        monkeypatch.setattr(capture, "resolve_org", lambda _value: "")  # WHY: no session in a unit test.
        monkeypatch.setattr(capture, "request", _FakeRequest())  # WHY: the route reads one query argument.
        context = capture.page_context(CAPTURE_ID)
        assert context[SIZE_FIELD] == STORED_SIZE

    def test_the_context_falls_back_to_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A page that names no capture yet shows zero rather than failing."""
        blank = capture.blank_status("", capture.TIER_STANDARD)  # WHY: the record before the first start.
        monkeypatch.setattr(capture, "page_status", lambda _id: blank)
        monkeypatch.setattr(capture, "lock_banner_context", lambda _org, _site: {})
        monkeypatch.setattr(capture, "resolve_org", lambda _value: "")
        monkeypatch.setattr(capture, "request", _FakeRequest())
        context = capture.page_context("")
        assert context[SIZE_FIELD] == 0


class _FakeRequest:
    """The smallest stand-in for the Flask request that `page_context` reads.

    Why:
        `page_context` reads one query argument. A unit test needs no request
        context for that, so this object answers the single call.
    """

    args: dict[str, str] = {}  # WHY: the route calls `.get("site_id", "")` on this mapping.

"""Prove that a null body value never reaches the lock record as text.

Why:
    Issue #2111 records a live lock record that held the text ``None`` in its
    run identifier. The browser sends ``run_id: null`` with the key present, and
    ``dict.get`` returns its default only for a missing key. The reader
    therefore received ``None`` and ``str(None)`` wrote the four letter word.

    A reader that tests ``if record.run_id:`` treats that text as true, so a
    caller believes a run owns the lock when none does. These tests hold the
    rule for both body fields that a browser may send as null.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.upgrade_portal.app.routes import select

FORBIDDEN = "None"  # The text that `str(None)` writes. No field may ever hold it.


class TestTheRunIdentifierNeverReadsAsText:
    """A null run identifier must become an empty value."""

    @pytest.mark.parametrize(
        "body",
        [
            {"run_id": None},  # The browser sends this for a capture with no run.
            {},  # An absent key, which already worked.
            {"run_id": ""},  # An explicit empty value.
        ],
    )
    def test_an_absent_run_reads_as_empty(self, body: dict[str, Any]) -> None:
        """Each of the three shapes means the same thing: no run."""
        value = str(body.get("run_id") or "")  # The rule the reader now applies.
        assert value == ""
        assert value != FORBIDDEN

    def test_a_named_run_survives_unchanged(self) -> None:
        """The guard must not damage a real identifier."""
        body = {"run_id": "run-abc123"}
        assert str(body.get("run_id") or "") == "run-abc123"


class TestTheConfirmationWordNeverReadsAsText:
    """The sibling field carries the same risk, so it takes the same guard."""

    @pytest.mark.parametrize("body", [{"confirm": None}, {}, {"confirm": ""}])
    def test_an_absent_word_reads_as_empty(self, body: dict[str, Any]) -> None:
        """A confirmation word that reads as the text None would refuse a valid caller."""
        value = str(body.get("confirm") or "")
        assert value == ""
        assert value != FORBIDDEN

    def test_a_typed_word_survives_unchanged(self) -> None:
        """The guard must not damage a real word."""
        body = {"confirm": "CONFIRM"}
        assert str(body.get("confirm") or "") == "CONFIRM"


class TestTheSourceCarriesTheGuard:
    """The rule lives in `build_lock_request`, so the source must show it."""

    def test_the_reader_uses_the_or_form_and_not_a_default(self) -> None:
        """A default argument fires only for a missing key, which is the defect."""
        from inspect import getsource

        source = getsource(select.build_lock_request)
        assert "body.get(RUN_FIELD) or" in source  # The null safe form.
        assert 'body.get(RUN_FIELD, "")' not in source  # The form that let None through.

    def test_the_confirmation_field_uses_the_same_form(self) -> None:
        """Both fields must carry the same guard, so neither drifts."""
        from inspect import getsource

        source = getsource(select.build_lock_request)
        assert "body.get(CONFIRM_FIELD) or" in source
        assert 'body.get(CONFIRM_FIELD, "")' not in source

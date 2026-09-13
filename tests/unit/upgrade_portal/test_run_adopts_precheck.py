"""Unit tests for the newest standalone pre-check reader.

Why:
    Issue 2098 asks the run creation to adopt a pre-check that named no run.
    The store reader returns the newest verified capture of a site that holds
    the role ``pre`` and an empty run. The reader skips a capture that already
    names a run, a post capture, and an unverified capture (Delta H3, FR-103,
    Risk 3).

    The fake database below reads the filter from the bind values, so the test
    proves the reader asks for the four rules and returns the newest match. The
    fake sorts by ``started_at`` and hands the newest row first, so the reader
    returns the reading that describes the site as it stands now.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from src.upgrade_portal.capture import store

_SITE = "site-a"  # WHY: The site whose pre-check the run adopts.
_OTHER_SITE = "site-b"  # WHY: A second site the reader must never return.


class _FakeAql:
    """A query seam that applies the pre-check filter from the bind values.

    Why:
        The reader filters by a site, a role, an empty run, and the verified
        state, then sorts newest first. The seam reads those four values from
        the binds, so the test drives the fake with whatever the reader asks.
    """

    def __init__(self, captures: list[dict[str, Any]]) -> None:
        """Bind the seam to the seeded captures.

        Args:
            captures: Every capture the store holds for this test.
        """
        self._captures = captures  # WHY: The scan reads these rows for each query.

    def execute(self, query: str, bind_vars: Mapping[str, Any] | None = None) -> list[Any]:
        """Return the matching captures, newest first.

        Args:
            query: The query text. The seam checks it names the capture collection.
            bind_vars: The site, the role, the empty run, and the verified state.

        Returns:
            The matching rows, newest first, or an empty list.
        """
        binds = dict(bind_vars or {})  # WHY: The seam reads the four rules from the binds.
        if store.CAPTURE_COLLECTION not in query:  # WHY: The reader scans the capture collection alone.
            return []
        matches = [row for row in self._captures if self._keeps(row, binds)]  # The four filters together.
        matches.sort(key=lambda row: str(row.get("started_at", "")), reverse=True)  # Newest first, like the sort.
        return [dict(row) for row in matches]  # A copy stops a caller edit.

    @staticmethod
    def _keeps(row: Mapping[str, Any], binds: Mapping[str, Any]) -> bool:
        """Return True when one capture passes the four filters.

        Args:
            row: One seeded capture.
            binds: The site, the role, the empty run, and the verified state.

        Returns:
            True only when the capture matches every bind value.
        """
        return (
            row.get("site_id") == binds.get("site_id")  # The one site.
            and row.get("role") == binds.get("role")  # The pre-check half.
            and row.get("run_id") == binds.get("empty_run")  # A standalone capture names no run.
            and row.get(store.CAPTURE_STATE_FIELD) == binds.get("verified")  # A proved reading alone.
        )


class _FakeDatabase:
    """A fake handle whose query seam holds the seeded captures.

    Why:
        The reader runs one query through ``database.aql.execute``. The handle
        answers that call from memory, so the test needs no database.
    """

    def __init__(self, captures: list[dict[str, Any]]) -> None:
        """Create a handle over the seeded captures.

        Args:
            captures: Every capture the store holds for this test.
        """
        self.aql = _FakeAql(captures)  # WHY: The reader runs its query through this seam.


def _capture(capture_id: str, site_id: str, role: str, run_id: str, state: str, started_at: str) -> dict[str, Any]:
    """Return one seeded capture document.

    Args:
        capture_id: The business key of the capture.
        site_id: The site the capture reads.
        role: The half of the upgrade, ``pre`` or ``post``.
        run_id: The run the capture names, empty for a standalone capture.
        state: The stored state word.
        started_at: The start time, in ISO-8601 order.

    Returns:
        One capture document with the fields the reader filters by.
    """
    return {
        "capture_id": capture_id,  # The key a caller adopts.
        "site_id": site_id,  # The site the reader narrows by.
        "role": role,  # The pre-check half or the post half.
        "run_id": run_id,  # An empty run marks a standalone capture.
        store.CAPTURE_STATE_FIELD: state,  # The state word the reader checks.
        "started_at": started_at,  # The sort key for newest first.
    }


def _seeded_database() -> _FakeDatabase:
    """Return a fake handle with one newest match and several near misses.

    Returns:
        The handle. Only capture ``cap-new-01`` matches all four rules.
    """
    verified = store.CaptureState.VERIFIED.value  # The one state a comparison trusts.
    captures = [
        _capture("cap-old-01", _SITE, "pre", "", verified, "2026-01-01T00:00:00Z"),  # Older match.
        _capture("cap-new-01", _SITE, "pre", "", verified, "2026-03-01T00:00:00Z"),  # Newest match.
        _capture("cap-run-01", _SITE, "pre", "run-x", verified, "2026-04-01T00:00:00Z"),  # Names a run.
        _capture("cap-post-01", _SITE, "post", "", verified, "2026-04-01T00:00:00Z"),  # Post half.
        _capture("cap-unv-01", _SITE, "pre", "", "assembling", "2026-04-01T00:00:00Z"),  # Unverified.
        _capture("cap-far-01", _OTHER_SITE, "pre", "", verified, "2026-04-01T00:00:00Z"),  # Other site.
    ]
    return _FakeDatabase(captures)  # A handle over the six captures.


def test_latest_standalone_precheck_returns_the_newest_match() -> None:
    """The reader returns the newest verified standalone pre-check of the site."""
    database = _seeded_database()  # One newest match among several near misses.
    result = store.latest_standalone_precheck(_SITE, database)  # The reader runs its query.
    assert result is not None  # The site holds a match.
    assert result["capture_id"] == "cap-new-01"  # The newest match, not the older one.
    assert result["role"] == store.STANDALONE_ROLE  # The pre-check half.
    assert result["run_id"] == ""  # A standalone capture names no run.
    assert result[store.CAPTURE_STATE_FIELD] == store.CaptureState.VERIFIED.value  # A proved reading.


def test_latest_standalone_precheck_skips_every_near_miss() -> None:
    """The reader returns none when only near misses exist."""
    verified = store.CaptureState.VERIFIED.value  # The one trusted state.
    captures = [
        _capture("cap-run-01", _SITE, "pre", "run-x", verified, "2026-04-01T00:00:00Z"),  # Names a run.
        _capture("cap-post-01", _SITE, "post", "", verified, "2026-04-01T00:00:00Z"),  # Post half.
        _capture("cap-unv-01", _SITE, "pre", "", "assembling", "2026-04-01T00:00:00Z"),  # Unverified.
    ]
    result = store.latest_standalone_precheck(_SITE, _FakeDatabase(captures))  # No row passes the four rules.
    assert result is None  # The reader adopts nothing.


def test_latest_standalone_precheck_returns_none_without_a_database(monkeypatch: pytest.MonkeyPatch) -> None:
    """The reader returns none when the store is out of reach."""
    monkeypatch.setattr(store, "connect_database", lambda: None)  # WHY: No store answers this call.
    result = store.latest_standalone_precheck(_SITE)  # The reader opens no query.
    assert result is None  # An unreachable store adopts nothing.

"""Unit tests for the pre-check gate of a multi-site upgrade.

Why:
    Issue #3243. The single-site confirm page stays locked until the site holds
    a verified pre-check capture. The multi-site confirm page had no such gate,
    so an operator could upgrade many sites with no baseline for a comparison.
    These tests prove the view layer that the confirm page, the start route,
    and the progress page share. No test opens a socket.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import pytest

from src.upgrade_portal.capture import store
from src.upgrade_portal.upgrade.org_precheck import OrgPrecheckGate, OrgPrecheckState, SitePrecheck

SITE_ONE = "00000000-0000-0000-0000-0000000000b1"  # The first selected site.
SITE_TWO = "00000000-0000-0000-0000-0000000000b2"  # The second selected site.
SITE_THREE = "00000000-0000-0000-0000-0000000000b3"  # The third selected site.
NAMES = {SITE_ONE: "Site One", SITE_TWO: "Site Two"}  # The third site has no name, so its ID fills in.
PROJECTED_FIELDS = ("capture_id", "site_id", "role", "run_id", store.CAPTURE_STATE_FIELD, "tier", "started_at")


class FixedReader:
    """Answer one fixed capture pair for each site, and record each read."""

    def __init__(self, answers: Mapping[str, tuple[str, int]]) -> None:
        """Keep the answer of each site.

        Args:
            answers: The capture identifier and the tier of each site.
        """
        self.answers = dict(answers)  # A site with no entry holds no pre-check capture.
        self.reads: list[str] = []  # Each entry names one site read, in call order.

    def __call__(self, site_id: str) -> tuple[str, int]:
        """Return the pair of one site, and record the read.

        Args:
            site_id: The site to read.

        Returns:
            The capture identifier and the tier, or an empty identifier.
        """
        self.reads.append(site_id)  # The test proves the read order.
        return self.answers.get(site_id, ("", 2))  # The adopter answers an empty key for a site with none.


class RecordingAql:
    """Record the query text of the store reader, and answer no row."""

    def __init__(self) -> None:
        """Start with no query."""
        self.queries: list[str] = []  # Each entry holds one query text.

    def execute(self, query: str, bind_vars: Mapping[str, Any] | None = None) -> list[Any]:
        """Record one query and answer an empty cursor.

        Args:
            query: The query text.
            bind_vars: The bind values. The test reads the query text alone.

        Returns:
            An empty list, because the site holds no pre-check.
        """
        del bind_vars  # The projection lives in the query text.
        self.queries.append(query)  # The test reads the text after the call.
        return []  # No row, so the reader answers None.


class RecordingDatabase:
    """Hold the recording query seam, as a database handle does."""

    def __init__(self) -> None:
        """Create the seam."""
        self.aql = RecordingAql()  # The store reader runs its query through this seam.


def test_a_site_with_a_capture_is_ready_and_stores_four_fields() -> None:
    """A site with a capture identifier is ready, and its stored entry holds four fields."""
    site = SitePrecheck(SITE_ONE, "Site One", "cap-1-01", 3)  # One site with a tier 3 capture.
    assert site.ready is True  # The identifier is not empty.
    assert site.stored() == {"site_id": SITE_ONE, "site_name": "Site One", "capture_id": "cap-1-01", "tier": 3}


def test_a_site_without_a_capture_is_not_ready() -> None:
    """A site with an empty capture identifier is not ready."""
    assert SitePrecheck(SITE_ONE, "Site One", "", 2).ready is False  # The adopter found no capture.


def test_the_state_is_ready_only_when_each_site_holds_a_capture() -> None:
    """The gate opens only when one or more sites exist and each site holds a capture."""
    one = SitePrecheck(SITE_ONE, "Site One", "cap-1-01", 2)  # A ready site.
    two = SitePrecheck(SITE_TWO, "Site Two", "", 2)  # A site with no capture.
    assert OrgPrecheckState((one,)).ready is True  # One ready site opens the gate.
    assert OrgPrecheckState((one, two)).ready is False  # One missing site keeps the gate closed.
    assert OrgPrecheckState(()).ready is False  # An empty selection never opens the gate.


def test_the_state_names_each_missing_site_in_selection_order() -> None:
    """The refusal message names each site that holds no capture, in the order of the selection."""
    sites = (  # Three sites. The first and the third hold no capture.
        SitePrecheck(SITE_ONE, "Site One", "", 2),
        SitePrecheck(SITE_TWO, "Site Two", "cap-2-01", 2),
        SitePrecheck(SITE_THREE, SITE_THREE, "", 2),
    )
    state = OrgPrecheckState(sites)  # The state of the three sites.
    assert [site.site_id for site in state.missing] == [SITE_ONE, SITE_THREE]  # The selection order.
    assert state.missing_names() == f"Site One, {SITE_THREE}"  # The names, joined with a comma.


def test_the_state_stores_one_entry_for_each_site() -> None:
    """The stored list holds one entry for each site, in the order of the selection."""
    sites = (SitePrecheck(SITE_TWO, "Site Two", "cap-2-01", 2), SitePrecheck(SITE_ONE, "Site One", "cap-1-01", 3))
    stored = OrgPrecheckState(sites).stored()  # The list that the start route writes.
    assert [entry["site_id"] for entry in stored] == [SITE_TWO, SITE_ONE]  # The order of the selection.
    assert stored[1] == {"site_id": SITE_ONE, "site_name": "Site One", "capture_id": "cap-1-01", "tier": 3}


def test_the_gate_reads_each_site_in_order_and_names_each_site() -> None:
    """The gate reads each site once, in order, and a site with no name shows its identifier."""
    reader = FixedReader({SITE_ONE: ("cap-1-01", 3), SITE_THREE: ("cap-3-01", 2)})  # The second site has none.
    state = OrgPrecheckGate(reader).read([SITE_ONE, SITE_TWO, SITE_THREE], NAMES)  # One read for each site.
    assert reader.reads == [SITE_ONE, SITE_TWO, SITE_THREE]  # The order of the selection, one read each.
    assert [site.capture_id for site in state.sites] == ["cap-1-01", "", "cap-3-01"]  # The pairs of the reader.
    assert [site.site_name for site in state.sites] == ["Site One", "Site Two", SITE_THREE]  # The ID fills in.
    assert state.sites[0].tier == 3 and not state.ready  # The tier stays, and the missing site closes the gate.


def test_a_reader_fault_counts_as_a_missing_capture(caplog: pytest.LogCaptureFixture) -> None:
    """A fault of the store read closes the gate for that site and logs a warning."""

    def broken(site_id: str) -> tuple[str, int]:  # A reader that cannot reach the store.
        """Raise the fault of an unreachable store."""
        raise ConnectionError(site_id)  # The store did not answer.

    caplog.set_level(logging.WARNING)  # The fault must reach the log.
    state = OrgPrecheckGate(broken).read([SITE_ONE], NAMES)  # One read that fails.
    assert not state.ready and state.missing_names() == "Site One"  # The gate fails closed.
    assert "ConnectionError" in caplog.text  # The log names the fault type.


def test_a_gate_without_a_reader_counts_each_site_as_missing() -> None:
    """A portal with no pre-check seam keeps the gate closed for each site."""
    state = OrgPrecheckGate(None).read([SITE_ONE, SITE_TWO], NAMES)  # No reader is wired.
    assert [site.ready for site in state.sites] == [False, False]  # No site holds a capture.
    assert state.missing_names() == "Site One, Site Two"  # Each site is named.


def test_the_stored_rows_of_a_record_skip_a_damaged_entry() -> None:
    """The progress page reads the stored list, and a damaged entry never breaks the page."""
    record = {  # One stored list with two valid entries and two damaged entries.
        "pre_captures": [
            {"site_id": SITE_ONE, "site_name": "Site One", "capture_id": "cap-1-01", "tier": 3},
            "not an entry",
            {"site_id": SITE_TWO, "site_name": "Site Two", "capture_id": "", "tier": 2},
            {"site_id": SITE_THREE, "site_name": "", "capture_id": "cap-3-01", "tier": "2"},
        ]
    }
    rows = OrgPrecheckGate.rows_of(record)  # The rows of the progress card.
    assert [row["capture_id"] for row in rows] == ["cap-1-01", "cap-3-01"]  # Each entry that names a capture.
    assert rows[1] == {"site_id": SITE_THREE, "site_name": SITE_THREE, "capture_id": "cap-3-01", "tier": 2}


@pytest.mark.parametrize("record", [{}, {"pre_captures": None}, {"pre_captures": "cap-1-01"}])
def test_a_record_without_a_list_has_no_rows(record: dict[str, Any]) -> None:
    """An operation from an earlier release holds no list, so the card shows the note."""
    assert OrgPrecheckGate.rows_of(record) == []  # No row, so the page shows the text of US4.


def test_the_store_reader_returns_the_fields_that_the_portal_uses() -> None:
    """FR-016: the pre-check query projects seven fields and never returns the whole document."""
    database = RecordingDatabase()  # The seam records the query text.
    assert store.latest_standalone_precheck(SITE_ONE, database) is None  # The seam answers no row.
    query = database.aql.queries[0]  # The one query of the reader.
    assert "RETURN doc\n" not in query  # A whole document holds every device and every client.
    assert "KEEP(doc" in query  # The projection keeps the named fields.
    assert all(f'"{field}"' in query for field in PROJECTED_FIELDS)  # Each field that a caller reads.

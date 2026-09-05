"""Contract tests for the audit log of every site lock action.

Why:
    Issue #2221 records the gap. The portal recorded a takeover and recorded no
    take, no release, and no expiry. A page built on that trail would show one
    takeover and nothing else, and an operator would read it as "one lock action
    ever happened". That is a false account of a site that many operators took
    and released.

    The expiry is the interesting half. No request runs at the moment a hold
    ends, and the lock store drops the key, so nothing remembers who held the
    site. The reader therefore infers the expiry from the trail itself.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.upgrade_portal.compare import lock_audit

ORG_ID = "org-1"
SITE_ID = "site-1"
OTHER_SITE = "site-2"

FIRST_EMAIL = "first.operator@example.invalid"
SECOND_EMAIL = "second.operator@example.invalid"


def line(action: str, actor: str, moment: str, site: str = SITE_ID, previous: str = "") -> dict[str, Any]:
    """Build one trail record.

    Args:
        action: The action name.
        actor: The operator who acted.
        moment: The moment of the action.
        site: The site the action reached.
        previous: The operator who held the site before a takeover.

    Returns:
        The record, in the shape that `runtime/lock.py` writes.
    """
    return {
        "action": action,
        "actor_email": actor,
        "previous_actor_email": previous,
        "occurred_at": moment,
        "org_id": ORG_ID,
        "site_id": site,
    }


def write_trail(folder: Path, records: list[dict[str, Any]]) -> Path:
    """Write one trail file.

    Args:
        folder: The temporary folder.
        records: The records to write, oldest first.

    Returns:
        The path of the trail.
    """
    path = folder / "trail.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")
    return path


# ---------------------------------------------------------------------------
# The expiry, which no writer records
# ---------------------------------------------------------------------------


def test_a_take_after_an_unreleased_hold_reads_as_an_expiry() -> None:
    """A hold that never closed ended with no release.

    Why:
        No request runs at the moment a hold ends. The trail states the fact all
        the same, because the next take found the site free.
    """
    rows = lock_audit.mark_expiries([line("take", FIRST_EMAIL, "t1"), line("take", SECOND_EMAIL, "t2")])
    assert [row["action"] for row in rows] == ["take", "expire", "take"]


def test_a_released_hold_reads_as_no_expiry() -> None:
    """A hold that closed needs no inferred row."""
    records = [line("take", FIRST_EMAIL, "t1"), line("release", FIRST_EMAIL, "t2"), line("take", SECOND_EMAIL, "t3")]
    assert [row["action"] for row in lock_audit.mark_expiries(records)] == ["take", "release", "take"]


def test_an_expiry_names_the_operator_who_went_quiet() -> None:
    """The row names the operator whose hold ended, not the one who took next."""
    rows = lock_audit.mark_expiries([line("take", FIRST_EMAIL, "t1"), line("take", SECOND_EMAIL, "t2")])
    assert rows[1]["actor_email"] == FIRST_EMAIL


def test_two_sites_close_their_holds_on_their_own() -> None:
    """A take of one site says nothing about the hold of another site."""
    records = [
        line("take", FIRST_EMAIL, "t1", SITE_ID),
        line("take", SECOND_EMAIL, "t2", OTHER_SITE),
        line("release", FIRST_EMAIL, "t3", SITE_ID),
    ]
    assert [row["action"] for row in lock_audit.mark_expiries(records)] == ["take", "take", "release"]


def test_a_takeover_needs_no_expiry_row() -> None:
    """A takeover already names the operator it took the site from.

    Why:
        The hold of the earlier operator ended because of the takeover, and not
        by an expiry. An expiry row beside it would count one ending twice, and
        the log would then report a hold that ended in two ways.
    """
    records = [line("take", FIRST_EMAIL, "t1"), line("takeover", SECOND_EMAIL, "t2", SITE_ID, FIRST_EMAIL)]
    assert [row["action"] for row in lock_audit.mark_expiries(records)] == ["take", "takeover"]


# ---------------------------------------------------------------------------
# The row that the page paints
# ---------------------------------------------------------------------------


def test_no_row_holds_an_address() -> None:
    """Warning: the trail names people, and no page of the portal may.

    Why:
        The trail stores the address, because an audit names people. The page
        shows the one-way digest that the portal writes into every log record.
    """
    row = lock_audit.audit_row(line("takeover", SECOND_EMAIL, "t1", SITE_ID, FIRST_EMAIL))
    assert FIRST_EMAIL not in str(row)
    assert SECOND_EMAIL not in str(row)


def test_a_row_names_the_operator_through_a_digest() -> None:
    """The reader still tells two operators apart."""
    first = lock_audit.audit_row(line("take", FIRST_EMAIL, "t1"))
    second = lock_audit.audit_row(line("take", SECOND_EMAIL, "t1"))
    assert first["actor_digest"]
    assert first["actor_digest"] != second["actor_digest"]


def test_a_row_names_the_moment_the_site_and_the_action() -> None:
    """The four values that the issue asks for reach the page."""
    row = lock_audit.audit_row(line("release", FIRST_EMAIL, "2026-09-02T10:00:00+00:00"))
    assert row["occurred_at"] == "2026-09-02T10:00:00+00:00"
    assert row["site_id"] == SITE_ID
    assert row["action"] == "release"
    assert row["actor_digest"]


def test_a_row_written_before_this_change_reads_as_a_takeover() -> None:
    """The takeover was the only action that the trail held.

    Why:
        A row with no action name comes from the earlier writer. Reading it as
        an unknown action would hide a real takeover from the log.
    """
    legacy = {"actor_email": SECOND_EMAIL, "previous_actor_email": FIRST_EMAIL, "site_id": SITE_ID}
    assert lock_audit.audit_row(legacy)["action"] == "takeover"


# ---------------------------------------------------------------------------
# The read
# ---------------------------------------------------------------------------


def test_the_reader_answers_the_newest_action_first(tmp_path: Path) -> None:
    """The page shows the newest action at the top.

    Args:
        tmp_path: The temporary folder of this test.
    """
    path = write_trail(tmp_path, [line("take", FIRST_EMAIL, "t1"), line("release", FIRST_EMAIL, "t2")])
    rows = lock_audit.read_audit_rows(path=path)
    assert [row["action"] for row in rows] == ["release", "take"]


def test_a_damaged_line_costs_that_line_alone(tmp_path: Path) -> None:
    """A process that stopped during a write can leave a partial last line.

    Args:
        tmp_path: The temporary folder of this test.
    """
    path = write_trail(tmp_path, [line("take", FIRST_EMAIL, "t1")])
    with path.open("a", encoding="utf-8") as handle:
        handle.write('{"action": "release", "actor\n')  # A write that stopped partway.
    assert [row["action"] for row in lock_audit.read_audit_rows(path=path)] == ["take"]


def test_an_absent_trail_answers_an_empty_log(tmp_path: Path) -> None:
    """No trail exists until the first action writes one.

    Args:
        tmp_path: The temporary folder of this test.
    """
    assert lock_audit.read_audit_rows(path=tmp_path / "no-such-file.jsonl") == []


def test_the_read_holds_a_row_cap(tmp_path: Path) -> None:
    """The trail appends for ever, so one read answers a page of it.

    Args:
        tmp_path: The temporary folder of this test.
    """
    records = [line("take", FIRST_EMAIL, f"t{index}") for index in range(20)]
    path = write_trail(tmp_path, records)
    assert len(lock_audit.read_audit_rows(limit=5, path=path)) == 5


@pytest.mark.parametrize("action", ["take", "release", "takeover", "expire"])
def test_every_action_name_survives_the_read(tmp_path: Path, action: str) -> None:
    """The four actions that the issue names all reach the page.

    Args:
        tmp_path: The temporary folder of this test.
        action: The action under test.
    """
    path = write_trail(tmp_path, [line(action, FIRST_EMAIL, "t1")])
    assert lock_audit.read_audit_rows(path=path)[0]["action"] == action

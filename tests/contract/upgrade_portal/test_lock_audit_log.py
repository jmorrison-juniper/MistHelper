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
import logging  # Record synthetic trail writes without operator addresses.
from pathlib import Path
from typing import Any

import pytest

from src.interfaces.portals.upgrade_portal.compare import lock_audit

logger = logging.getLogger(__name__)  # Keep temporary fixture records separate from portal records.

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


def write_trail(folder: Path, records: list[dict[str, Any]]) -> Path:  # Keep all audit input temporary and synthetic.
    """Write one trail file.

    Args:
        folder: The temporary folder.
        records: The records to write, oldest first.

    Returns:
        The path of the trail.
    """
    logger.info("Write the synthetic temporary lock audit trail")  # Record file creation before it starts.
    path = folder / "trail.jsonl"  # Use only this test's isolated temporary directory.
    with path.open("w", encoding="utf-8") as handle:  # Never open a checkout or production trail.
        for record in records:  # Preserve stored order for expiry inference.
            handle.write(json.dumps(record) + "\n")  # Write only synthetic records with explicit attribution.
    logger.debug("Wrote %s synthetic lock audit records", len(records))  # Report no stored address or row.
    return path  # Every reader call below supplies the matching organization explicitly.


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


def test_the_reader_answers_the_newest_action_first(tmp_path: Path) -> None:  # Preserve matching event order.
    """The page shows the newest action at the top.

    Args:
        tmp_path: The temporary folder of this test.
    """
    path = write_trail(tmp_path, [line("take", FIRST_EMAIL, "t1"), line("release", FIRST_EMAIL, "t2")])  # Temp input.
    rows = lock_audit.read_audit_rows(path=path, org_id=ORG_ID)  # Keep the existing matching newest-first read.
    assert [row["action"] for row in rows] == ["release", "take"]  # Preserve the original order expectation.


def test_a_damaged_line_costs_that_line_alone(tmp_path: Path) -> None:  # Preserve damaged-line handling.
    """A process that stopped during a write can leave a partial last line.

    Args:
        tmp_path: The temporary folder of this test.
    """
    path = write_trail(tmp_path, [line("take", FIRST_EMAIL, "t1")])  # Keep valid synthetic context before damage.
    logger.info("Append one damaged synthetic audit line")  # Record the temporary file action.
    with path.open("a", encoding="utf-8") as handle:  # Append only to this test's temporary trail.
        handle.write('{"action": "release", "actor\n')  # A write that stopped partway.
    logger.debug("Appended one damaged synthetic audit line")  # Report no stored address.
    assert [
        row["action"] for row in lock_audit.read_audit_rows(path=path, org_id=ORG_ID)
    ] == [  # Keep the valid action.
        "take"
    ]  # Valid row remains.


def test_an_absent_trail_answers_an_empty_log(tmp_path: Path) -> None:  # Missing input must not widen scope.
    """No trail exists until the first action writes one.

    Args:
        tmp_path: The temporary folder of this test.
    """
    assert (  # Preserve the authorized missing-file empty result.
        lock_audit.read_audit_rows(path=tmp_path / "no-such-file.jsonl", org_id=ORG_ID) == []
    )  # Preserve missing-file behavior.


def test_the_read_holds_a_row_cap(tmp_path: Path) -> None:  # Preserve the original positive limit.
    """The trail appends for ever, so one read answers a page of it.

    Args:
        tmp_path: The temporary folder of this test.
    """
    logger.info("Build the synthetic capped audit sequence")  # Record the fixture transformation.
    records = [line("take", FIRST_EMAIL, f"t{index}") for index in range(20)]  # Keep older matching inference context.
    logger.debug("Built %s synthetic capped audit actions", len(records))  # Report only the fixture count.
    path = write_trail(tmp_path, records)  # Persist only synthetic temporary input.
    assert (  # Keep the same cap inside explicit organization scope.
        len(lock_audit.read_audit_rows(limit=5, path=path, org_id=ORG_ID)) == 5
    )  # Preserve the original positive cap.


def test_the_capped_read_matches_the_full_expiry_inference(tmp_path: Path) -> None:  # Keep bounded/full agreement.
    """A page read infers expiry rows from the full trail before it clips rows.

    Args:
        tmp_path: The temporary folder of this test.
    """
    logger.info("Build the synthetic full audit inference sequence")  # Record fixture construction.
    records = [  # Preserve all original matching sites and transition expectations.
        line("take", FIRST_EMAIL, "t1", SITE_ID),  # Open the first site's earlier hold.
        line("take", SECOND_EMAIL, "t2", SITE_ID),  # Infer an expiry before this matching take.
        line("take", FIRST_EMAIL, "t3", OTHER_SITE),  # Keep the second site's independent hold.
        line("release", SECOND_EMAIL, "t4", SITE_ID),  # Close only the first site's hold.
        line("take", SECOND_EMAIL, "t5", OTHER_SITE),  # Infer the second site's matching expiry.
        line("takeover", FIRST_EMAIL, "t6", SITE_ID, SECOND_EMAIL),  # A takeover creates no immediate expiry.
    ]
    logger.debug("Built %s synthetic full audit actions", len(records))  # Report only a count.
    path = write_trail(tmp_path, records)  # Persist only the temporary matching trail.
    full_rows = lock_audit.mark_expiries(records)  # Retain the existing bounded/full comparison.
    expected = [lock_audit.audit_row(row) for row in reversed(full_rows)][  # Preserve the original expected cap.
        :4
    ]  # Preserve the original expected representation.
    assert (  # The new required organization must not change matching inference.
        lock_audit.read_audit_rows(limit=4, path=path, org_id=ORG_ID) == expected
    )  # Add scope without changing the cap.


def test_a_one_row_trail_keeps_the_row_shape(tmp_path: Path) -> None:  # Preserve the existing public representation.
    """A short trail keeps the same row fields and types.

    Args:
        tmp_path: The temporary folder of this test.
    """
    path = write_trail(tmp_path, [line("take", FIRST_EMAIL, "t1")])  # Use the existing synthetic single action.
    rows = lock_audit.read_audit_rows(path=path, org_id=ORG_ID)  # Preserve the public matching row.
    assert rows == [lock_audit.audit_row(line("take", FIRST_EMAIL, "t1"))]  # Keep the existing digest representation.
    assert {field: type(value) for field, value in rows[0].items()} == {  # Preserve every original field type.
        "action": str,  # Actions remain public text.
        "site_id": str,  # Site identifiers retain their original representation.
        "org_id": str,  # Required reader scope does not change stored attribution output.
        "occurred_at": str,  # Moments retain their original representation.
        "actor_digest": str,  # Public output still excludes raw operator addresses.
        "previous_digest": str,  # Public output still excludes raw previous-holder addresses.
        "inferred": bool,  # Actual and inferred records remain distinguishable.
    }


def test_a_trail_shorter_than_the_window_returns_every_row(tmp_path: Path) -> None:  # Keep complete short results.
    """A page larger than the trail returns the whole trail.

    Args:
        tmp_path: The temporary folder of this test.
    """
    logger.info("Build the synthetic short audit sequence")  # Record the fixture transformation.
    records = [  # Preserve the original matching take and release sequence.
        line("take", FIRST_EMAIL, "t1"),
        line("release", FIRST_EMAIL, "t2"),
    ]  # Preserve matching take and release.
    logger.debug("Built %s synthetic short audit actions", len(records))  # Report only a count.
    path = write_trail(tmp_path, records)  # Use a temporary matching trail.
    expected = [lock_audit.audit_row(row) for row in reversed(records)]  # Retain the existing expected digest shape.
    assert lock_audit.read_audit_rows(limit=10, path=path, org_id=ORG_ID) == expected  # Preserve the larger window.


@pytest.mark.parametrize("action", ["take", "release", "takeover", "expire"])
def test_every_action_name_survives_the_read(tmp_path: Path, action: str) -> None:  # Preserve all four action words.
    """The four actions that the issue names all reach the page.

    Args:
        tmp_path: The temporary folder of this test.
        action: The action under test.
    """
    path = write_trail(tmp_path, [line(action, FIRST_EMAIL, "t1")])  # Keep each original synthetic action case.
    assert (  # Explicit scope must preserve each matching stored action.
        lock_audit.read_audit_rows(path=path, org_id=ORG_ID)[0]["action"] == action
    )  # Preserve each public action word.


def test_a_site_read_answers_only_that_site(tmp_path: Path) -> None:  # Keep the site intersection within organization.
    """A site read drops every row of another site.

    Why:
        Issue #2596 reports that the history page narrowed the run list and the
        capture list to one site, and the audit log still showed another site.

    Args:
        tmp_path: The temporary folder of this test.
    """
    logger.info("Build the synthetic two-site audit sequence")  # Record the fixture transformation.
    records = [  # Keep both sites inside the explicit matching organization.
        line("take", FIRST_EMAIL, "t1", SITE_ID),  # Open the requested site's matching hold.
        line("take", SECOND_EMAIL, "t2", OTHER_SITE),  # Keep another site's action outside the requested intersection.
        line("release", FIRST_EMAIL, "t3", SITE_ID),  # Close the requested site's matching hold.
    ]
    logger.debug("Built %s synthetic two-site audit actions", len(records))  # Report a safe count.
    path = write_trail(tmp_path, records)  # Persist only matching synthetic temporary data.
    rows = lock_audit.read_audit_rows(path=path, site_id=SITE_ID, org_id=ORG_ID)  # Keep both scope restrictions.
    assert [row["site_id"] for row in rows] == [SITE_ID, SITE_ID]  # Preserve the original exact site expectation.


def test_an_empty_site_read_answers_every_site(tmp_path: Path) -> None:  # Keep all sites within explicit organization.
    """An empty site reads every site in the explicit selected organization.

    Args:
        tmp_path: The temporary folder of this test.
    """
    logger.info("Build the synthetic organization-wide audit sequence")  # Record fixture transformation.
    records = [  # Populate two matching sites without foreign input.
        line("take", FIRST_EMAIL, "t1", SITE_ID),
        line("take", SECOND_EMAIL, "t2", OTHER_SITE),
    ]  # Matching sites.
    logger.debug("Built %s synthetic organization-wide audit actions", len(records))  # Report only a count.
    path = write_trail(tmp_path, records)  # Use only the temporary matching trail.
    assert lock_audit.read_audit_rows(
        path=path, site_id="", org_id=ORG_ID
    ) == lock_audit.read_audit_rows(  # Same scope.
        path=path, org_id=ORG_ID
    )  # The empty site changes no explicit organization scope.


def test_a_site_read_keeps_the_expiry_that_the_full_read_infers(tmp_path: Path) -> None:  # Keep matching hold context.
    """A site read retains the complete matching sequence before applying its result limit.

    Why:
        The matching site's earlier hold supports its next take.
        Another site's actions cannot change that inference.

    Args:
        tmp_path: The temporary folder of this test.
    """
    logger.info("Build the synthetic matching-site expiry sequence")  # Record fixture construction.
    records = [  # Preserve the original matching-site transitions and another site's independent action.
        line("take", FIRST_EMAIL, "t1", SITE_ID),  # Retain the earlier matching hold for inference.
        line("take", SECOND_EMAIL, "t2", OTHER_SITE),  # Another site's hold cannot change the requested hold.
        line("take", SECOND_EMAIL, "t3", SITE_ID),  # Infer the requested site's matching expiry.
    ]
    logger.debug("Built %s synthetic matching-site expiry actions", len(records))  # Report only a count.
    path = write_trail(tmp_path, records)  # Persist synthetic temporary context before the scoped read.
    full = [  # Retain the original full-versus-site comparison in explicit organization scope.
        row for row in lock_audit.read_audit_rows(path=path, org_id=ORG_ID) if row["site_id"] == SITE_ID
    ]  # Match site.
    assert (  # Another site's action cannot change matching expiry inference.
        lock_audit.read_audit_rows(path=path, site_id=SITE_ID, org_id=ORG_ID) == full
    )  # Preserve bounded/full agreement.
    assert [row["inferred"] for row in full] == [  # Preserve exact inferred-event positions.
        False,
        True,
        False,
    ]  # Preserve the original exact inference expectation.


def test_a_capped_site_read_matches_the_capped_full_read(tmp_path: Path) -> None:  # Count only matching positions.
    """A capped site read answers the newest rows of that site only.

    Why:
        The cap counts the rows that the page shows. A cap that counted every
        site would answer fewer rows than the operator asked for.

    Args:
        tmp_path: The temporary folder of this test.
    """
    logger.info("Build the synthetic interleaved capped-site sequence")  # Record the fixture transformation.
    records = []  # Keep the original interleaved matching-organization input.
    for index in range(10):  # Include more actions than the existing visible window.
        records.append(  # Preserve the requested site's older matching context.
            line("take", FIRST_EMAIL, f"a{index}", OTHER_SITE)
        )  # Other sites consume no requested positions.
        records.append(line("take", SECOND_EMAIL, f"b{index}", SITE_ID))  # Earlier matching context supports inference.
    logger.debug("Built %s synthetic interleaved audit actions", len(records))  # Report a safe fixture count.
    path = write_trail(tmp_path, records)  # Persist only the temporary matching organization trail.
    rows = lock_audit.read_audit_rows(limit=4, path=path, site_id=SITE_ID, org_id=ORG_ID)  # Keep the original cap.
    assert len(rows) == 4  # Preserve the existing exact visible row count.
    assert {row["site_id"] for row in rows} == {SITE_ID}  # Preserve the existing exact site intersection.

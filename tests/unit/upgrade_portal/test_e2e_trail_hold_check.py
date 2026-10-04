"""Prove the run trail hold check of the browser run with no browser and no network.

Why:
    Issue #3508. Two browser tests left a site lock after the test ended, and
    the run still passed. The trail of that run held one take with no release
    for each of the two sites. The class `TrailHoldCheck` of
    `tests/support/upgrade_portal_e2e/records/audit.py` replays the trail after
    the test portal stops, and it fails the run when a hold has no release.
    These direct tests prove each decision of the check with a trail file in a
    temporary folder.
"""

from __future__ import annotations  # Keep annotations independent from import order.

import json  # Write each trail row as one JSON line.
from pathlib import Path  # Name each temporary trail file.
from typing import Any  # A trail row holds values of mixed types.

import pytest  # Check each failure of the check.

from src.interfaces.portals.upgrade_portal.runtime import (
    lock,
)  # The module that writes the trail and names each action.
from tests.support.upgrade_portal_e2e.records.audit import TrailHoldCheck, TrailLine  # The classes under test.

SITE_ID = "66666666-6666-6666-6666-666666666666"  # The site of the test of the lost action answer.
WEST_ID = "99999999-0000-0000-0000-000000343903"  # The site West of the later site checks.
BUSY_SITE_ID = "22222222-2222-2222-2222-222222222222"  # The site that most run-control tests use.
OPERATOR = "e2e.operator@example.invalid"  # The first stand-in operator.
LATER_OPERATOR = "e2e.later.check.operator@example.invalid"  # The operator of the later site checks.
FIRST_MOMENT = "2026-09-27T11:27:33+00:00"  # The moment of the first action of a trail.
LATER_MOMENT = "2026-09-27T11:29:05+00:00"  # The moment of a later action of a trail.


def _row(
    action: str | None, site_id: str = SITE_ID, actor: str = OPERATOR, moment: str = FIRST_MOMENT
) -> dict[str, Any]:
    """Build one trail row in the shape that the lock module writes."""
    row: dict[str, Any] = {"org_id": "org-3508", "site_id": site_id, "actor_email": actor}  # The fields of a row.
    row.update({"previous_actor_email": "", "occurred_at": moment})  # The two other fields of a row.
    if action is not None:  # A row from before issue #2221 holds no action.
        row["action"] = action  # The action that the row records.
    return row  # One record of the trail.


def _trail(tmp_path: Path, rows: list[object]) -> Path:
    """Write the rows as one JSON line each, and return the trail path."""
    trail = tmp_path / lock.AUDIT_FILE_NAME  # The name that the lock module writes.
    trail.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")  # One row on each line.
    return trail  # The check reads this file.


def _bad_trail(tmp_path: Path, line: str) -> Path:
    """Write one valid take and then one bad line, and return the trail path."""
    trail = tmp_path / lock.AUDIT_FILE_NAME  # The name that the lock module writes.
    trail.write_text(json.dumps(_row(lock.ACTION_TAKE)) + "\n" + line + "\n", encoding="utf-8")  # Line 2 is bad.
    return trail  # The check reads this file.


class TestAClosedTrail:
    """A trail where each hold closes passes, and the measure names the counts."""

    def test_a_trail_where_each_hold_ends_with_a_release_passes(self, tmp_path: Path) -> None:
        """Each take has a later release, so the check passes and names 0 leaked holds."""
        rows: list[object] = [_row(lock.ACTION_TAKE), _row(lock.ACTION_RELEASE)]  # One closed hold.
        rows += [_row(lock.ACTION_TAKE, WEST_ID), _row(lock.ACTION_RELEASE, WEST_ID)]  # A second closed hold.
        result = TrailHoldCheck(_trail(tmp_path, rows)).evaluate()  # Replay the trail.
        result.require_no_leak()  # No hold stays open, so no failure.
        assert (result.records, result.sites, result.leaks) == (4, 2, ())  # The counts of the trail.
        assert "read 4 record(s) of 2 site(s)" in result.measure  # The measure names what the check read.
        assert "It found 0 leaked hold(s)." in result.measure  # The measure names the result.
        assert str(result.trail) in result.measure  # The measure names the file that the check read.

    def test_a_takeover_that_a_release_follows_passes(self, tmp_path: Path) -> None:
        """A takeover closes the earlier hold, and the release closes the takeover."""
        rows: list[object] = [_row(lock.ACTION_TAKE), _row(lock.ACTION_TAKEOVER, actor=LATER_OPERATOR)]  # A move.
        rows.append(_row(lock.ACTION_RELEASE, actor=LATER_OPERATOR))  # The new holder frees the site.
        result = TrailHoldCheck(_trail(tmp_path, rows)).evaluate()  # Replay the trail.
        assert result.leaks == ()  # A takeover names the operator it took the site from, so no hold leaked.

    def test_a_release_with_no_open_hold_passes(self, tmp_path: Path) -> None:
        """A release of a site with no open hold closes nothing and leaks nothing."""
        result = TrailHoldCheck(_trail(tmp_path, [_row(lock.ACTION_RELEASE)])).evaluate()  # One release alone.
        assert (result.records, result.leaks) == (1, ())  # The check read the row and found no leak.

    def test_a_blank_line_is_skipped(self, tmp_path: Path) -> None:
        """A blank line holds no record, so the check skips it."""
        trail = tmp_path / lock.AUDIT_FILE_NAME  # The name that the lock module writes.
        take, release = json.dumps(_row(lock.ACTION_TAKE)), json.dumps(_row(lock.ACTION_RELEASE))  # Two rows.
        trail.write_text(f"{take}\n\n   \n{release}\n", encoding="utf-8")  # Two blank lines between the rows.
        result = TrailHoldCheck(trail).evaluate()  # Replay the trail.
        assert (result.records, result.leaks) == (2, ())  # Two records, and the hold closed.

    def test_an_absent_trail_passes_with_zero_records(self, tmp_path: Path) -> None:
        """A run that took no lock wrote no trail, so the check passes with 0 records."""
        result = TrailHoldCheck(tmp_path / lock.AUDIT_FILE_NAME).evaluate()  # No file exists.
        result.require_no_leak()  # No hold, so no failure.
        assert (result.records, result.sites, result.leaks) == (0, 0, ())  # Nothing to read.
        assert "read 0 record(s) of 0 site(s)" in result.measure  # The measure states the empty read.

    def test_an_empty_trail_passes_with_zero_records(self, tmp_path: Path) -> None:
        """A trail of b"" holds no record, so the check passes with 0 records."""
        trail = tmp_path / lock.AUDIT_FILE_NAME  # The name that the lock module writes.
        trail.write_bytes(b"")  # An empty file.
        result = TrailHoldCheck(trail).evaluate()  # Replay the trail.
        assert (result.records, result.sites, result.leaks) == (0, 0, ())  # Nothing to read.


class TestALeakedHold:
    """A hold with no release fails the run, and the message names the site and the operator."""

    def test_a_hold_open_at_the_end_fails_and_names_the_site_and_the_operator(self, tmp_path: Path) -> None:
        """A take with no later release is a leaked hold."""
        rows: list[object] = [_row(lock.ACTION_TAKE), _row(lock.ACTION_RELEASE)]  # One closed hold.
        rows.append(_row(lock.ACTION_TAKE, WEST_ID, LATER_OPERATOR, LATER_MOMENT))  # One open hold.
        result = TrailHoldCheck(_trail(tmp_path, rows)).evaluate()  # Replay the trail.
        assert len(result.leaks) == 1  # One leaked hold.
        with pytest.raises(AssertionError) as caught:  # The run must fail.
            result.require_no_leak()  # The check decides.
        message = str(caught.value)  # The text that pytest reports.
        assert WEST_ID in message and LATER_OPERATOR in message and LATER_MOMENT in message  # The hold.
        assert "It found 1 leaked hold(s)." in message  # The measure leads the message.

    def test_a_take_that_follows_an_open_hold_names_the_expired_hold(self, tmp_path: Path) -> None:
        """A take after an open hold of the same site means that the earlier hold ended with no release."""
        rows: list[object] = [_row(lock.ACTION_TAKE)]  # The first operator takes the site.
        rows.append(_row(lock.ACTION_TAKE, actor=LATER_OPERATOR, moment=LATER_MOMENT))  # A later take.
        rows.append(_row(lock.ACTION_RELEASE, actor=LATER_OPERATOR, moment=LATER_MOMENT))  # The later hold closes.
        result = TrailHoldCheck(_trail(tmp_path, rows)).evaluate()  # Replay the trail.
        assert len(result.leaks) == 1  # The first hold leaked.
        assert SITE_ID in result.leaks[0] and OPERATOR in result.leaks[0]  # The site and the first operator.
        assert LATER_MOMENT in result.leaks[0]  # The moment of the take that found the hold.

    def test_a_takeover_with_no_release_fails(self, tmp_path: Path) -> None:
        """A takeover opens a hold, so a takeover at the end of the trail is a leaked hold."""
        rows: list[object] = [_row(lock.ACTION_TAKE), _row(lock.ACTION_TAKEOVER, actor=LATER_OPERATOR)]  # A move.
        result = TrailHoldCheck(_trail(tmp_path, rows)).evaluate()  # Replay the trail.
        assert len(result.leaks) == 1 and LATER_OPERATOR in result.leaks[0]  # The new holder kept the site.

    def test_a_row_with_no_action_reads_as_a_takeover(self, tmp_path: Path) -> None:
        """A row from before issue #2221 opens a hold, as the audit log of the portal reads it."""
        closed = TrailHoldCheck(_trail(tmp_path, [_row(None), _row(lock.ACTION_RELEASE)])).evaluate()  # Closed.
        assert closed.leaks == ()  # The release closes the old row.
        open_hold = TrailHoldCheck(_trail(tmp_path, [_row(None)])).evaluate()  # The old row alone.
        assert len(open_hold.leaks) == 1 and SITE_ID in open_hold.leaks[0]  # The old row stays open.

    def test_the_trail_of_issue_3497_names_the_two_leaked_sites(self, tmp_path: Path) -> None:
        """The shape of the full run of issue #3497 fails, and the message names both sites."""
        rows: list[object] = []  # The trail in the order of the run.
        for _pair in range(3):  # The busy site closes each hold.
            rows += [_row(lock.ACTION_TAKE, BUSY_SITE_ID), _row(lock.ACTION_RELEASE, BUSY_SITE_ID)]
        rows.append(_row(lock.ACTION_TAKE, WEST_ID, LATER_OPERATOR, LATER_MOMENT))  # The capture start test.
        rows.append(_row(lock.ACTION_TAKE, SITE_ID))  # The test of the lost action answer.
        result = TrailHoldCheck(_trail(tmp_path, rows)).evaluate()  # Replay the trail.
        assert (result.records, result.sites, len(result.leaks)) == (8, 3, 2)  # Two leaked holds.
        with pytest.raises(AssertionError) as caught:  # The run must fail.
            result.require_no_leak()  # The check decides.
        assert WEST_ID in str(caught.value) and SITE_ID in str(caught.value)  # Both sites of the problem.
        assert BUSY_SITE_ID not in str(caught.value)  # A closed site does not show in the message.


class TestABadTrail:
    """A line that the check cannot read fails with its line number."""

    def test_bad_json_fails_and_keeps_the_parser_error(self, tmp_path: Path) -> None:
        """A line that is not JSON fails, and the cause is the JSONDecodeError of the parser."""
        check = TrailHoldCheck(_bad_trail(tmp_path, '{"action": "take", "site_id": '))  # A partial write.
        with pytest.raises(AssertionError, match="Line 2 .* is not JSON") as caught:  # The line number.
            check.evaluate()  # The check reads the trail.
        assert isinstance(caught.value.__cause__, json.JSONDecodeError)  # The report keeps the parser position.

    @pytest.mark.parametrize(
        ("line", "cause"),
        [
            ("[1, 2]", "is not a JSON object"),
            ('"take"', "is not a JSON object"),
            ('{"action": "take"}', "names no site"),
            ('{"action": "take", "site_id": "  "}', "names no site"),
            (json.dumps({"action": "borrow", "site_id": SITE_ID}), "unknown action 'borrow'"),
            (json.dumps({"action": 5, "site_id": SITE_ID}), "unknown action 5"),
        ],
    )
    def test_a_bad_line_fails_and_names_the_line_number(self, tmp_path: Path, line: str, cause: str) -> None:
        """A line of another shape fails, and the message names the line and the fault."""
        check = TrailHoldCheck(_bad_trail(tmp_path, line))  # Line 2 holds the fault.
        with pytest.raises(AssertionError, match="Line 2 ") as caught:  # The line number leads the message.
            check.evaluate()  # The check reads the trail.
        assert cause in str(caught.value)  # The message names the fault.

    def test_a_line_that_is_not_utf8_fails_and_names_the_line_number(self, tmp_path: Path) -> None:
        """A line of bytes that no reader can decode fails with its line number."""
        trail = tmp_path / lock.AUDIT_FILE_NAME  # The name that the lock module writes.
        trail.write_bytes(b"\xff\xfe\n")  # Bytes that are not UTF-8.
        with pytest.raises(AssertionError, match="Line 1 ") as caught:  # The line number leads the message.
            TrailHoldCheck(trail).evaluate()  # The check reads the trail.
        assert isinstance(caught.value.__cause__, UnicodeDecodeError)  # The report keeps the decode error.

    def test_a_trail_that_cannot_open_fails(self, tmp_path: Path) -> None:
        """A trail path that names a folder fails, because a guard must fail when it cannot read its input."""
        folder = tmp_path / lock.AUDIT_FILE_NAME  # The trail name, as a folder.
        folder.mkdir()  # The check cannot read a folder as a file.
        with pytest.raises(OSError):  # The read fault reaches the run.
            TrailHoldCheck(folder).evaluate()  # The check reads the trail.


def test_the_check_reads_the_actions_from_the_lock_module() -> None:
    """The line reader knows the four actions of the lock module, so the tests copy no action name."""
    names = {lock.ACTION_TAKE, lock.ACTION_RELEASE, lock.ACTION_TAKEOVER, lock.ACTION_EXPIRE}  # The writer names.
    assert TrailLine.KNOWN_ACTIONS == frozenset(names)  # One source for each name.


def test_the_line_reader_returns_the_record_and_skips_a_blank_line(tmp_path: Path) -> None:
    """One good line gives its record, and a line of spaces gives no record."""
    trail = tmp_path / lock.AUDIT_FILE_NAME  # The reader names this path in each message.
    good = TrailLine.read(trail, 1, json.dumps(_row(lock.ACTION_TAKE)).encode("utf-8") + b"\n")  # One take.
    assert good is not None and good["action"] == lock.ACTION_TAKE  # The reader keeps the fields.
    assert TrailLine.read(trail, 2, b"   \n") is None  # A blank line holds no record.

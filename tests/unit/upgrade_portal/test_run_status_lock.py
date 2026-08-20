"""Proof that the run status body reports a site lock the run lost.

Why:
    The driver notes a lost site lock on the run record. Another operator can
    take the site, and the lock store can stop answering for longer than the
    retry window. Either way the upgrade keeps running, because firmware in
    flight cannot be recalled, but the run no longer holds the site.

    The status body dropped that note. `RunStatusView.build` wrote a fixed set
    of keys and copied nothing else, so the note reached the record and stopped
    there. An operator whose site was taken read a run that looked healthy and
    learned about the takeover from nothing at all.

    Two rules keep the fix safe, and the tests pin both:

    1. A healthy run adds no key. `contracts/http-api.md` section 5 fixes the
       keys of the body, and a contract test reads exactly those keys. The lock
       report is an exception report, so it appears only when something failed.
    2. The view copies three named keys and no other. A later writer could add
       a lock token to the record entry. A body that copied the whole entry
       would then send that token to the browser.
"""

from __future__ import annotations

from typing import Any

from src.upgrade_portal.runtime.runs import RunStatusView
from src.upgrade_portal.upgrade import driver

# WHY: `contracts/http-api.md` section 5 shows these nine keys. The lock report
# is the tenth key and must never displace one of them.
CONTRACT_FIELDS = {
    "run_id",
    "state",
    "phase_order",
    "phases",
    "targets",
    "stop_request",
    "pre_capture_id",
    "post_capture_id",
    "message",
}

# WHY: One sentence the driver really writes. The test reads the constant, so a
# reworded sentence cannot make the test pass against the wrong field.
LOST_REASON = driver.LOCK_LOST_REASON

# WHY: A time in the form `clock.now_text` returns. The value is a time only, so
# it carries no token and no address.
LOST_AT = "2026-08-19T14:05:00+00:00"


def record_with_lock(entry: object) -> dict[str, Any]:
    """Build a run record that carries one lock entry.

    Why:
        Every lock test needs the same record with one value changed. One
        builder keeps the field name in a single place, so a rename breaks one
        line instead of six.

    Args:
        entry: The value to store under the lock field.

    Returns:
        A run record with a run identifier, a state, and the lock entry.
    """
    return {"run_id": "run-1", "state": "upgrade_running", driver.LOCK_FIELD: entry}


def lost_entry(**changes: object) -> dict[str, Any]:
    """Build the lock entry the driver writes when a run loses the site.

    Args:
        **changes: Keys to add to the entry, or values to replace.

    Returns:
        A lock entry with the three keys the driver writes.
    """
    entry: dict[str, Any] = {"state": driver.LOCK_STATE_LOST, "message": LOST_REASON, "at": LOST_AT}
    entry.update(changes)
    return entry


def test_the_view_names_the_field_the_driver_writes() -> None:
    """The view reads the same field name and sub-keys the driver writes.

    Why:
        The driver writes the note and the view reads it. The two live in
        different modules, and the driver imports the view. A field name that
        drifted would silence the banner for ever, and a test that built its
        own entry would never catch it.
    """
    assert RunStatusView.LOCK_KEY == driver.LOCK_FIELD  # One name for the field, in both modules.
    assert set(RunStatusView.LOCK_FIELDS) == set(lost_entry())  # The view copies every key the driver writes.


def test_a_healthy_run_adds_no_lock_key() -> None:
    """A run that still holds its site lock answers the nine contract keys.

    Why:
        `contracts/http-api.md` section 5 fixes the keys of the body, and a
        contract test asserts that exact set. A key that appeared on every run
        would tell a reader that the portal promises a field the contract never
        fixed, and would break that test.
    """
    body = RunStatusView().build({"run_id": "run-1", "state": "upgrade_running"})
    assert set(body) == CONTRACT_FIELDS  # Exactly the nine keys, and no tenth.
    assert driver.LOCK_FIELD not in body  # The healthy run reports no fault.


def test_a_lost_lock_reaches_the_status_body() -> None:
    """A run that lost the site lock reports the state, the sentence, and the time.

    Why:
        This is the defect. The operator needs all three values: the state word
        drives the banner, the sentence says which of the two failures happened,
        and the time says when the site changed hands.
    """
    body = RunStatusView().build(record_with_lock(lost_entry()))
    report = body[driver.LOCK_FIELD]
    assert report["state"] == driver.LOCK_STATE_LOST  # `portal.js` paints the banner on this word.
    assert report["message"] == LOST_REASON  # The banner repeats the sentence of the server.
    assert report["at"] == LOST_AT  # The operator reads when the run lost the site.


def test_the_lock_report_keeps_the_nine_contract_keys() -> None:
    """The lock report adds one key and replaces none of the nine."""
    body = RunStatusView().build(record_with_lock(lost_entry()))
    assert CONTRACT_FIELDS < set(body)  # Every contract key survives the added report.
    assert set(body) - CONTRACT_FIELDS == {driver.LOCK_FIELD}  # The report adds one key only.


def test_the_report_copies_no_other_value() -> None:
    """A lock token on the record entry never reaches the status body.

    Why:
        The record is a plain mapping and a later writer can add a key to the
        lock entry. A view that copied the whole entry would send a lock token
        to the browser, where any script on the page could read it. The view
        therefore names the three keys it copies.
    """
    entry = lost_entry(lock_token="secret-token-value", operator="someone@example.com")
    report = RunStatusView().build(record_with_lock(entry))[driver.LOCK_FIELD]
    assert set(report) == set(RunStatusView.LOCK_FIELDS)  # Three keys reach the body.
    assert "secret-token-value" not in str(report)  # The token stays on the server.
    assert "someone@example.com" not in str(report)  # The address stays on the server.


def test_a_half_written_entry_still_reports_the_state() -> None:
    """An entry that misses a key still answers that key, with a null value.

    Why:
        The driver writes all three keys together, but a record read from an
        older file may miss one. The page reads the same shape on every poll,
        so a missing key must arrive as null and never as a missing key.
    """
    report = RunStatusView().build(record_with_lock({"state": driver.LOCK_STATE_LOST}))[driver.LOCK_FIELD]
    assert report["state"] == driver.LOCK_STATE_LOST  # The state word survives.
    assert report["message"] is None  # The absent sentence reads as null.
    assert report["at"] is None  # The absent time reads as null.


def test_a_lock_value_that_is_not_a_mapping_adds_no_key() -> None:
    """A lock value of the wrong shape adds no key to the body.

    Why:
        The status endpoint must answer, whatever the record holds. A record
        that carries a string under this field would raise inside the view and
        would take the whole progress page down with it.
    """
    for value in ("lost", ["lost"], 7, None):
        body = RunStatusView().build(record_with_lock(value))
        assert set(body) == CONTRACT_FIELDS  # The wrong shape reports nothing at all.

"""The stored lock record holds an empty run value, never the text None.

Why:
    `spec.md` FR-112 forbids the text ``None`` in a stored lock record when the
    lock names no run. A caller that wraps a missing run with ``str`` writes the
    word ``None`` into the record, and the site list would then show that word to
    the next operator. Issue #2108 records that defect. These tests pin the
    empty run value on every path that builds a record, so a later change cannot
    let the word ``None`` return.

No network:
    Every test builds a record in memory and reads a field back. These tests
    reach no Redis server and no cloud.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import json  # The store keeps a record as JSON text, so one test reads a stored null back.
from typing import Any  # A decoded record maps a key to a free-form value.

from src.upgrade_portal.runtime import identity, lock  # The identity pair and the record under test.

# --------------------------------------------------------------------------
# The fixed values. Each one repeats a rule of the specification.
# --------------------------------------------------------------------------

PROBE_EMAIL = "probe.operator@example.invalid"  # A reserved domain, so no real address appears.
ORG_ID = "00000000-0000-0000-0000-0000000000e5"  # The organization half of the Redis key.
SITE_ID = "00000000-0000-0000-0000-0000000000f6"  # The site half of the same key.

NONE_TEXT = "None"  # The exact word that ``str(None)`` writes and that FR-112 forbids.
EMPTY_RUN = ""  # The one value FR-112 allows when the lock names no run.
REAL_RUN = "run-00000000000000000000000000000000"  # A well-shaped run key must pass through unchanged.

TOKEN_TEXT = "test-token-value"  # A token stands in for the random value the module would mint.
TIME_TEXT = "2026-08-27T00:00:00+00:00"  # One ISO 8601 time for both time fields of a record.


def _probe_owner() -> identity.SessionOwner:
    """Return one identity pair for every test below.

    Returns:
        The operator and browser pair that a record needs.
    """
    return identity.build_owner(PROBE_EMAIL, identity.issue_browser_id())  # The real builder, no cloud.


def test_a_record_maps_the_none_text_to_an_empty_run() -> None:
    """A record built with the word None holds an empty run instead.

    Why:
        FR-112 forbids the word ``None`` in a stored record. The record maps the
        word to an empty string on construction, so no later reader sees it.
    """
    record = lock.LockRecord(
        owner=_probe_owner(),  # The pair the site list shows to the next operator.
        lock_token=TOKEN_TEXT,  # A token proves which acquisition holds the lock.
        run_id=NONE_TEXT,  # A caller wrote the forbidden word here, so the record must clean it.
        acquired_at=TIME_TEXT,  # When the operator first took the site.
        refreshed_at=TIME_TEXT,  # When the last heartbeat arrived.
    )
    assert record.run_id == EMPTY_RUN  # The record maps the forbidden word to the allowed value.
    assert record.to_record()["run_id"] == EMPTY_RUN  # The stored shape carries the same empty value.


def test_a_record_keeps_a_real_run_key_unchanged() -> None:
    """A record built with a real run key keeps that key.

    Why:
        The cleaning rule must map the word ``None`` alone. A real run key must
        reach the store unchanged, or a later start would lose its pre-check.
    """
    record = lock.LockRecord(
        owner=_probe_owner(),  # The identity pair of the holder.
        lock_token=TOKEN_TEXT,  # The token of this acquisition.
        run_id=REAL_RUN,  # A real run key must survive the cleaning rule.
        acquired_at=TIME_TEXT,  # The first hold time.
        refreshed_at=TIME_TEXT,  # The last beat time.
    )
    assert record.run_id == REAL_RUN  # A real run key passes through with no change.


def test_a_request_maps_the_none_text_to_an_empty_run() -> None:
    """A request built with the word None holds an empty run instead.

    Why:
        The route builds a request from the body, and a body with a JSON null
        reaches the request as the word ``None``. The request cleans it, so the
        record the acquisition writes never carries the forbidden word.
    """
    request = lock.LockRequest(
        org_id=ORG_ID,  # The organization half of the key.
        site_id=SITE_ID,  # The site half of the same key.
        owner=_probe_owner(),  # The pair that would hold the lock.
        run_id=NONE_TEXT,  # A body with a JSON null reaches the request as this word.
    )
    assert request.run_id == EMPTY_RUN  # The request maps the forbidden word to the allowed value.


def test_a_stored_null_reads_back_as_an_empty_run() -> None:
    """A record read from a stored JSON null holds an empty run.

    Why:
        An older release, or a value damaged by hand, may hold a JSON null in
        the run field. The reader must map that null to an empty run, so the
        site list never shows the word ``None`` from an old value.
    """
    owner = _probe_owner()  # The pair the stored value names.
    mapping: dict[str, Any] = {
        "actor_email": owner.actor_email,  # The address half of the owner.
        "browser_id": owner.browser_id,  # The browser half of the owner.
        "lock_token": TOKEN_TEXT,  # The token of the stored acquisition.
        "run_id": None,  # A stored JSON null must read back as an empty run.
        "acquired_at": TIME_TEXT,  # The first hold time.
        "refreshed_at": TIME_TEXT,  # The last beat time.
    }
    record = lock.LockRecord.from_json(json.dumps(mapping))  # The real reader, on a stored null.
    assert record is not None  # A well-shaped owner reads back as a record, never None.
    assert record.run_id == EMPTY_RUN  # The reader maps the stored null to the allowed value.

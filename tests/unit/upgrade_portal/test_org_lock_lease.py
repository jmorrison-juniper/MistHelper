"""Unit tests for the multi-site site lock lease (issue #3333)."""

from __future__ import annotations

import threading
from typing import Any

import pytest

from src.upgrade_portal.runtime import lock
from src.upgrade_portal.upgrade.org_cascade.locks import OrgOperationLockLease
from tests.support.org_cascade import VersionedStore

OPERATION_ID = "00000000-0000-0000-0000-000000003333"  # One fake multi-site operation.
ORG_ID = "00000000-0000-0000-0000-00000000a333"  # One fake organization.
SITE_IDS = ("00000000-0000-0000-0000-00000000b333", "00000000-0000-0000-0000-00000000c333")  # Two sites.


def stored_lock(site_id: str) -> dict[str, str]:
    """Return one valid stored lock that belongs to the test operation."""
    return {  # The decoder validates the same six fields as Redis.
        "actor_email": "operator@example.com",  # A valid address builds the stored owner.
        "browser_id": f"00000000-0000-0000-0000-{site_id[-12:]}",  # A valid UUID separates the browser.
        "lock_token": f"token-{site_id}",  # A unique token proves the selected site.
        "run_id": OPERATION_ID,  # The lock belongs to this multi-site operation.
        "acquired_at": "2026-09-30T00:00:00+00:00",  # The original acquisition time stays fixed.
        "refreshed_at": "2026-09-30T00:00:00+00:00",  # The renewal call moves this value in Redis.
    }


def operation() -> dict[str, Any]:
    """Return one operation that holds both test site locks."""
    return {  # The lease reads only these durable operation fields.
        "operation_id": OPERATION_ID,  # The run store key and each lock binding.
        "org_id": ORG_ID,  # The organization part of each Redis key.
        "record_version": 1,  # The compare-and-set writer requires an integer version.
        "site_locks": {site_id: stored_lock(site_id) for site_id in SITE_IDS},  # Both selected sites.
    }


def test_one_renewal_round_refreshes_every_stored_site(monkeypatch: pytest.MonkeyPatch) -> None:
    """The lease renews every selected site during one 60-second round."""
    calls: list[tuple[str, str, object]] = []  # The key, the run binding, and the bound client.

    def refresh(key: str, record: lock.LockRecord, client: object = None) -> int:
        calls.append((key, record.run_id, client))  # Record the safe fields of this renewal.
        return lock.LOCK_TTL_SECONDS  # The store accepted the compare-and-extend.

    monkeypatch.setattr(lock, "refresh_site_lock", refresh)  # The test reaches no Redis service.
    client = object()  # One object proves that every renewal uses the bound client.
    lease = OrgOperationLockLease(VersionedStore(operation()), OPERATION_ID, client)  # The shipped lease.
    assert lease.renew() == len(SITE_IDS)  # One round must renew both selected sites.
    assert calls == [  # The operation organization and each selected site build the two keys.
        (lock.build_key(ORG_ID, site_id), OPERATION_ID, client) for site_id in SITE_IDS
    ]


def test_the_background_lease_renews_after_the_contract_interval(monkeypatch: pytest.MonkeyPatch) -> None:
    """The watch starts renewal without a browser status poll."""
    renewed = threading.Event()  # The test waits for the first background renewal round.

    def refresh(_key: str, _record: lock.LockRecord, _client: object = None) -> int:
        renewed.set()  # The background thread reached the lock store seam.
        return lock.LOCK_TTL_SECONDS  # The store accepted the compare-and-extend.

    monkeypatch.setattr(lock, "refresh_site_lock", refresh)  # The test reaches no Redis service.
    monkeypatch.setattr(lock, "HEARTBEAT_SECONDS", 0.01)  # Keep the production interval but shorten this test.
    lease = OrgOperationLockLease(VersionedStore(operation()), OPERATION_ID, object())  # The shipped lease.
    lease.start()  # The phase watch starts this call after submission.
    try:  # The cleanup must stop the daemon thread even when the assertion fails.
        assert renewed.wait(1) is True  # A closed browser does not stop the background renewal.
    finally:
        lease.stop()  # Leave no renewal thread after the test.


def test_release_deletes_every_lock_and_clears_the_durable_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    """The lease releases every site only after its caller ends the watch scope."""
    released: list[str] = []  # The test records each site key that the lease gives back.

    def release(key: str, _record: lock.LockRecord, _client: object = None) -> lock.ReleaseOutcome:
        released.append(key)  # Record the key without exposing a token.
        return lock.ReleaseOutcome.RELEASED  # The store accepted the compare-and-delete.

    monkeypatch.setattr(lock, "release_site_lock", release)  # The test reaches no Redis service.
    store = VersionedStore(operation())  # The store holds both durable lock copies.
    lease = OrgOperationLockLease(store, OPERATION_ID, object())  # The shipped lease owns the close.
    lease.release()  # The watch calls this only after the post-check stage ends.
    assert released == [lock.build_key(ORG_ID, site_id) for site_id in SITE_IDS]  # Both sites returned.
    assert (store.read_run(OPERATION_ID) or {})["site_locks"] == {}  # A restart sees no held lock.

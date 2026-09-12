"""Verify the HTTP contract for bulk cancel and single-run reconciliation."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.upgrade_portal.app.routes.select import LOCK_RECORDS_KEY
from src.upgrade_portal.persistence.actions import RUN_COLLECTION, ActionRepository
from src.upgrade_portal.runtime import identity, lock
from tests.integration.upgrade_portal.run_controls import FakeDatabase
from tests.support.lock_store_double import FakeLockStore

ORG_ID = "00000000-0000-0000-0000-0000000000aa"
SITE_ID = "00000000-0000-0000-0000-0000000000bb"
RUN_ID = "phase-seven-run"
REQUEST_KEY = "phase-seven-request-key"


class DatabaseRunStore:
    """Read the same controlled run collection that action transactions change."""

    def __init__(self, database: FakeDatabase) -> None:
        """Bind one controlled database."""
        self.database = database

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one controlled run record."""
        return self.database.collection(RUN_COLLECTION).get(run_id)

    def runs_for_site(self, site_id: str) -> list[dict[str, Any]]:
        """Return all controlled runs for one site."""
        return self.database.collection(RUN_COLLECTION).find({"site_id": site_id}, limit=1000)


class EvidenceStore:
    """Return one fixed complete read-only evidence list."""

    def read(self, name: str, **parameters: Any) -> list[dict[str, Any]]:
        """Return complete proof for one known target."""
        assert name == "reconciliation"
        assert parameters["run_id"] == RUN_ID
        return [
            {
                "target_id": "target-one",
                "stored_stop_result": "cancel_accepted",
                "task_id": "task-one",
                "task_state": "final",
                "write_state": "not_writing",
                "driver_state": "stopped",
                "sources": ["stored", "cloud_task", "device", "driver"],
                "observed_at": "2026-09-11T14:00:00+00:00",
                "is_complete": True,
                "has_conflict": False,
            }
        ]


@pytest.fixture
def run_control_client(portal_app: Flask) -> Iterator[tuple[FlaskClient, FakeDatabase]]:
    """Return one signed client with process-owned lock and ArangoDB stand-ins."""
    database = FakeDatabase()
    database.create_collection(RUN_COLLECTION)
    repository = ActionRepository(database)
    repository.bootstrap()
    run = database.seed_run(RUN_ID, "awaiting_confirmation")
    run.update(
        {
            "org_id": ORG_ID,
            "site_id": SITE_ID,
            "updated_at": "2026-09-09T10:00:00+00:00",
            "targets": [{"device_id": "target-one"}],
        }
    )
    database.collections[RUN_COLLECTION]["documents"][RUN_ID] = run
    owner = identity.build_owner("phase-seven@example.invalid", identity.issue_browser_id())
    identity.SESSION_REGISTRY.register(
        identity.OperatorSession(owner, object(), identity.CredentialMode.ENVIRONMENT_TOKEN)
    )
    lock_record = lock.LockRecord(
        owner,
        "phase-seven-lock-token",
        RUN_ID,
        "2026-09-11T13:00:00+00:00",
        "2026-09-11T13:00:00+00:00",
    )
    lock_store = FakeLockStore()
    lock_store.set(lock.build_key(ORG_ID, SITE_ID), lock_record.to_json())
    portal_app.config.update(
        WTF_CSRF_ENABLED=False,
        RUN_STORE=DatabaseRunStore(database),
        RUN_ACTION_STORE=repository,
        LOCK_STORE_CLIENT=lock_store,
        AUTHORIZATION_READER=lambda _scope: True,
        CLOUD_EVIDENCE=EvidenceStore(),
    )
    portal_app.config.pop("RUN_CONTROL_PREVIEW_SERVICE", None)
    try:
        with portal_app.test_client() as client:
            client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)
            with client.session_transaction() as browser_session:
                browser_session[identity.SESSION_OWNER_KEY] = owner.key
                browser_session["selected_org_id"] = ORG_ID
                browser_session[LOCK_RECORDS_KEY] = {SITE_ID: lock_record.to_json()}
            yield client, database
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)


def test_bulk_cancel_uses_preview_and_returns_the_durable_result(
    run_control_client: tuple[FlaskClient, FakeDatabase],
) -> None:
    """Bulk cancel returns one verified atomic success result."""
    client, database = run_control_client
    preview = client.post(
        "/api/runs/bulk-actions/preview",
        json={
            "action": "cancel",
            "organization_id": ORG_ID,
            "history_scope": "all-sites",
            "run_ids": [RUN_ID],
        },
    ).get_json()

    response = client.post(
        "/api/runs/bulk-actions",
        headers={"Idempotency-Key": REQUEST_KEY},
        json={
            "action": "cancel",
            "run_ids": [RUN_ID],
            "confirmation": "CANCEL 1 RUNS",
            "preview_token": preview["preview_token"],
        },
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["counts"] == {"succeeded": 1, "refused": 0, "failed": 0, "unknown": 0}
    assert body["items"][0]["reason"] == "precloud_run_cancelled"
    assert database.collection(RUN_COLLECTION).get(RUN_ID)["state"] == "cancelled"
    stored = client.get(f"/api/run-actions/{body['action_id']}")
    assert stored.status_code == 200
    assert stored.get_json() == body


def test_reconciliation_needs_no_preview_and_stores_complete_evidence(
    run_control_client: tuple[FlaskClient, FakeDatabase],
) -> None:
    """Single-run reconciliation moves stopping only to proven stopped."""
    client, database = run_control_client
    run = database.collection(RUN_COLLECTION).get(RUN_ID)
    run["state"] = "stopping"
    run["_rev"] = "2"
    database.collections[RUN_COLLECTION]["documents"][RUN_ID] = run

    response = client.post(
        f"/api/runs/{RUN_ID}/reconcile",
        headers={"Idempotency-Key": REQUEST_KEY},
        json={"confirmation": f"RECONCILE {RUN_ID}"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["items"][0]["final_state"] == "stopped"
    assert body["items"][0]["evidence_summary"]["active_task_count"] == 0
    assert body["evidence_summary_digest"] == body["items"][0]["evidence_summary"]["decision_basis_digest"]
    assert database.collection(RUN_COLLECTION).get(RUN_ID)["state"] == "stopped"


def test_bulk_retry_returns_the_new_run_and_fresh_precheck_contract(
    run_control_client: tuple[FlaskClient, FakeDatabase],
) -> None:
    """Bulk retry returns one durable result with fresh pre-check navigation."""
    client, database = run_control_client
    run = database.collection(RUN_COLLECTION).get(RUN_ID)
    run.update(
        {
            "state": "failed",
            "updated_at": "2026-09-11T13:00:00+00:00",
            "options": {"strategy": "big_bang", "reboot": True},
            "targets": [{"device_id": "target-one"}],
        }
    )
    database.collections[RUN_COLLECTION]["documents"][RUN_ID] = run
    preview = client.post(
        "/api/runs/bulk-actions/preview",
        json={
            "action": "retry",
            "organization_id": ORG_ID,
            "history_scope": "all-sites",
            "run_ids": [RUN_ID],
        },
    ).get_json()

    response = client.post(
        "/api/runs/bulk-actions",
        headers={"Idempotency-Key": "phase-eight-request-key"},
        json={
            "action": "retry",
            "run_ids": [RUN_ID],
            "confirmation": "RETRY 1 RUNS",
            "preview_token": preview["preview_token"],
        },
    )

    assert response.status_code == 200
    body = response.get_json()
    item = body["items"][0]
    assert item["reason"] == "retry_created"
    assert item["result_run_id"].startswith("run-")
    assert item["precheck_url"] == (f"/captures/new?site_id={SITE_ID}&run_id={item['result_run_id']}&role=pre")
    created = database.collection(RUN_COLLECTION).get(item["result_run_id"])
    assert created is not None
    assert created["retry_of_run_id"] == RUN_ID
    assert created["pre_capture_id"] is None


def test_bulk_retry_live_run_refusal_names_the_current_run(
    run_control_client: tuple[FlaskClient, FakeDatabase],
) -> None:
    """A bulk retry refusal names the current live run and creates no retry."""
    client, database = run_control_client
    source = database.collection(RUN_COLLECTION).get(RUN_ID)
    source.update({"state": "cancelled", "updated_at": "2026-09-11T13:00:00+00:00", "options": {}})
    database.collections[RUN_COLLECTION]["documents"][RUN_ID] = source
    live = database.seed_run("phase-eight-live-run", "upgrade_running")
    live.update({"site_id": SITE_ID, "org_id": ORG_ID})
    database.collections[RUN_COLLECTION]["documents"]["phase-eight-live-run"] = live
    preview = client.post(
        "/api/runs/bulk-actions/preview",
        json={
            "action": "retry",
            "organization_id": ORG_ID,
            "history_scope": "all-sites",
            "run_ids": [RUN_ID],
        },
    ).get_json()

    response = client.post(
        "/api/runs/bulk-actions",
        headers={"Idempotency-Key": "phase-eight-live-key"},
        json={
            "action": "retry",
            "run_ids": [RUN_ID],
            "confirmation": "RETRY 1 RUNS",
            "preview_token": preview["preview_token"],
        },
    )

    assert response.status_code == 200
    item = response.get_json()["items"][0]
    assert item["classification"] == "refused"
    assert item["reason"] == "upgrade_already_running"
    assert item["live_run_id"] == "phase-eight-live-run"


def test_bulk_retry_returns_a_durable_source_time_refusal(
    run_control_client: tuple[FlaskClient, FakeDatabase],
) -> None:
    """A retry source with an invalid update time returns the stable reason."""
    client, database = run_control_client
    source = database.collection(RUN_COLLECTION).get(RUN_ID)
    source.update({"state": "failed", "updated_at": "not-a-time", "options": {}})
    database.collections[RUN_COLLECTION]["documents"][RUN_ID] = source
    preview = client.post(
        "/api/runs/bulk-actions/preview",
        json={
            "action": "retry",
            "organization_id": ORG_ID,
            "history_scope": "all-sites",
            "run_ids": [RUN_ID],
        },
    ).get_json()

    response = client.post(
        "/api/runs/bulk-actions",
        headers={"Idempotency-Key": "phase-eight-time-key"},
        json={
            "action": "retry",
            "run_ids": [RUN_ID],
            "confirmation": "RETRY 1 RUNS",
            "preview_token": preview["preview_token"],
        },
    )

    assert response.status_code == 200
    item = response.get_json()["items"][0]
    assert item["classification"] == "refused"
    assert item["reason"] == "retry_source_time_unknown"
    assert database.collection(RUN_COLLECTION).find({"retry_of_run_id": RUN_ID}, limit=10) == []

"""Verify atomic reconciliation against the controlled ArangoDB transaction."""

from datetime import UTC, datetime

from src.upgrade_portal.api.run_controls.services import SiteMutationGuard, StoppingRunReconciler
from src.upgrade_portal.persistence.actions import (
    ACTION_COLLECTION,
    RUN_COLLECTION,
    ActionRepository,
    DurableActorScope,
)
from tests.integration.upgrade_portal.run_controls import FakeDatabase

NOW = datetime(2026, 9, 11, 14, 0, tzinfo=UTC)


def test_complete_stopping_evidence_commits_run_outcome_and_digest_together() -> None:
    """One transaction stores stopped, the final outcome, and the evidence digest."""
    database = FakeDatabase()
    database.create_collection(RUN_COLLECTION)
    repository = ActionRepository(database)
    repository.bootstrap()
    run = database.seed_run("run-one", "stopping")
    run.update(
        {
            "org_id": "org-one",
            "site_id": "site-one",
            "updated_at": "2026-09-09T10:00:00+00:00",
            "targets": [{"device_id": "target-one"}],
        }
    )
    database.collections[RUN_COLLECTION]["documents"]["run-one"] = run
    guard = SiteMutationGuard(
        lambda _org, _site: True,
        lambda _org, _site: {"lock_token": "token-one"},
        {"site-one": "token-one"},
    )
    evidence = [
        {
            "target_id": "target-one",
            "stored_stop_result": "cancel_accepted",
            "task_id": "task-one",
            "task_state": "final",
            "write_state": "not_writing",
            "driver_state": "stopped",
            "sources": ["stored", "cloud_task", "device", "driver"],
            "observed_at": NOW.isoformat(),
            "is_complete": True,
            "has_conflict": False,
        }
    ]
    service = StoppingRunReconciler(
        repository,
        lambda run_id: database.collection(RUN_COLLECTION).get(run_id),
        guard,
        lambda _run, _now: evidence,
        clock=lambda: NOW,
    )

    result = service.reconcile(
        actor=DurableActorScope.build("email", "operator@example.invalid"),
        idempotency_key="reconcile-request-key-0001",
        confirmation="RECONCILE run-one",
        run_id="run-one",
        organization_id="org-one",
        site_id="site-one",
    )

    stored_run = database.collection(RUN_COLLECTION).get("run-one")
    stored_action = database.collection(ACTION_COLLECTION).get(result._key)
    assert stored_run["state"] == "stopped"
    assert stored_action["items"][0]["classification"] == "succeeded"
    assert (
        stored_action["evidence_summary_digest"]
        == stored_action["items"][0]["evidence_summary"]["decision_basis_digest"]
    )

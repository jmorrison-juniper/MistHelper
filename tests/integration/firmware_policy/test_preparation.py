"""Bind preparation proofs to durable, current, private, single-use operations."""

from pathlib import Path
from typing import Any

import pytest

from src.operations.execution.firmware_policy.sdk import PolicyError
from tests.integration.firmware_policy.test_workflow import prepared
from tests.unit.firmware_policy.fakes import ORG_ID, SITE_ID
from tests.unit.firmware_policy.recovery.fakes import RestoreSession


@pytest.mark.parametrize("kind", ["policy", "restore"])
@pytest.mark.parametrize("change", ["backup", "snapshot", "body", "public", "source"])
def test_prepared_proof_rechecks_private_recovery_and_current_plan(tmp_path: Path, kind: str, change: str) -> None:
    """Confirmation cannot use damaged recovery, a changed plan, or a stale snapshot."""
    if kind == "policy":
        session, workflow, plan = prepared(tmp_path)
        proof = workflow.back_up(plan)
        assert session.writes == []
        if change == "snapshot":
            session.settings[f"/api/v1/sites/{SITE_ID}/setting"]["timezone"] = "changed"
        elif change == "body":
            plan[0].body["auto_upgrade"]["enabled"] = True
        elif change == "source":
            plan[0].original["timezone"] = "changed"

        def apply() -> Any:
            """Apply the prepared policy through its bound recovery proof."""
            return workflow.apply(plan, proof=proof)

    else:
        session = RestoreSession(tmp_path)
        workflow = session.workflow()
        plan = session.prepare()
        proof = workflow.back_up(plan)
        assert session.writes == []
        if change == "snapshot":
            session.settings[f"/api/v1/orgs/{ORG_ID}/setting"]["allow_mist"] = True
        elif change == "body":
            plan.targets[0].body["allow_mist"] = False
        elif change == "source":
            session.path.write_text("{}")

        def apply() -> Any:
            """Apply restoration through its exact confirmation and recovery proof."""
            return workflow.apply(plan, "RESTORE", proof=proof)

    if change == "backup":
        proof.path.write_text("{}")
    elif change == "public":
        proof.path.chmod(0o644)
    with pytest.raises(PolicyError):
        apply()
    assert session.writes == []


@pytest.mark.parametrize("kind", ["policy", "restore"])
def test_preparation_proof_is_consumed_once_without_a_second_backup(tmp_path: Path, kind: str) -> None:
    """A completed operation cannot repeat its writes through the same recovery proof."""
    if kind == "policy":
        session, workflow, plan = prepared(tmp_path)
        proof = workflow.back_up(plan)
        result = workflow.apply(plan, proof=proof)
        assert result.failures == []

        def apply() -> Any:
            """Attempt to consume the same policy proof a second time."""
            return workflow.apply(plan, proof=proof)

        expected_backups = 1
    else:
        session = RestoreSession(tmp_path)
        workflow = session.workflow()
        plan = session.prepare()
        proof = workflow.back_up(plan)
        result = workflow.apply(plan, "RESTORE", proof=proof)
        assert result.failed == []

        def apply() -> Any:
            """Attempt to consume the same restore proof a second time."""
            return workflow.apply(plan, "RESTORE", proof=proof)

        expected_backups = 2
    writes = list(session.writes)
    with pytest.raises(PolicyError, match="consumed"):
        apply()
    assert session.writes == writes
    assert len(list(proof.path.parent.glob("*.json"))) == expected_backups


def test_restore_source_change_after_org_write_stops_sites(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A metadata-preserving source rewrite still fails the per-target change-time check."""
    session = RestoreSession(tmp_path)
    workflow = session.workflow()
    plan = session.prepare()
    proof = workflow.back_up(plan)
    put = session.mist_put

    def changed_source(uri: str, body: dict[str, Any]) -> Any:
        """Corrupt the original source only after one acknowledged organization write."""
        response = put(uri, body)
        session.path.write_bytes(session.path.read_bytes().replace(b"true", b"null", 1))
        return response

    monkeypatch.setattr(session, "mist_put", changed_source)
    result = workflow.apply(plan, "RESTORE", proof=proof)
    assert result.completed == [f"org:{ORG_ID}"]
    assert result.failed == [f"site:{SITE_ID}"]
    assert len(session.writes) == 1


@pytest.mark.parametrize("kind", ["policy", "restore"])
def test_initial_and_recovery_snapshot_callbacks_include_known_completed_and_total(tmp_path: Path, kind: str) -> None:
    """Settings requests must retain known counts instead of resetting progress to zero."""
    events: list[dict[str, Any]] = []
    if kind == "policy":
        session, workflow, previous = prepared(tmp_path)
        workflow.progress = events.append
        workflow.__post_init__()
        plan = [workflow.prepare({"id": ORG_ID, "name": "Fixture Organization"}, [])]
        workflow.back_up(plan)
        expected_initial = [0, 1]
        expected_total = 2
    else:
        session = RestoreSession(tmp_path)
        workflow = session.workflow()
        workflow.progress = events.append
        workflow.__post_init__()
        plan = workflow.prepare(session.path.stem, [f"org:{ORG_ID}", f"site:{SITE_ID}"], session.cloud)
        workflow.back_up(plan)
        expected_initial = [1]
        expected_total = 2
    reads = [event for event in events if event["phase"] == "Read site settings"]
    assert [event["completed"] for event in reads[: len(expected_initial)]] == expected_initial
    assert all(event["total"] == expected_total for event in reads[: len(expected_initial)])
    assert reads[-1]["completed"] >= 1
    assert reads[-1]["total"] == (3 if kind == "policy" else 2)
    assert any(event["phase"] == "backup_verified" and event["completed"] == event["total"] for event in events)
    assert session.writes == []


@pytest.mark.parametrize("kind", ["policy", "restore"])
def test_lost_recovery_after_org_write_stops_remaining_sites(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """A long operation cannot continue after its verified recovery file disappears."""
    if kind == "policy":
        session, workflow, plan = prepared(tmp_path)
    else:
        session = RestoreSession(tmp_path)
        workflow = session.workflow()
        plan = session.prepare()
    proof = workflow.back_up(plan)
    put = session.mist_put

    def lost_recovery(uri: str, body: dict[str, Any]) -> Any:
        """Remove recovery only after the first acknowledged settings write."""
        response = put(uri, body)
        proof.path.unlink()
        return response

    monkeypatch.setattr(session, "mist_put", lost_recovery)
    if kind == "policy":
        result = workflow.apply(plan, proof=proof)
        assert len(result.failures) == 1
        assert result.sites == []
    else:
        result = workflow.apply(plan, "RESTORE", proof=proof)
        assert result.failed == [f"site:{SITE_ID}"]
    assert len(session.writes) == 1


@pytest.mark.parametrize(
    "settings",
    [
        {"auto_upgrade": {"unknown": "private-fixture"}},
        {"ssr": {"auto_upgrade": {"version": "<redacted>"}}},
        {"auto_upgrade": {"enabled": "invalid"}},
    ],
)
def test_unrestorable_recovery_settings_prevent_readiness_and_every_write(
    tmp_path: Path, settings: dict[str, Any]
) -> None:
    """Backup verification cannot declare readiness when restoration rejects its writable state."""
    session, workflow, previous = prepared(tmp_path)
    events: list[dict[str, Any]] = []
    session.settings[f"/api/v1/sites/{SITE_ID}/setting"] = settings
    workflow.progress = events.append
    workflow.__post_init__()
    plan = [workflow.prepare({"id": ORG_ID, "name": "Fixture Organization"}, [])]
    with pytest.raises(PolicyError) as failure:
        workflow.back_up(plan)
    assert str(failure.value) == (
        "The backup firmware policies cannot be restored under the supported schema. "
        "Confirmation is blocked. Obtain the vendor contract for these settings."
    )
    assert session.writes == []
    assert not any(event["phase"] == "backup_verified" for event in events)
    assert not (tmp_path / ".firmware-policy-backups").exists()


def test_org_metadata_ids_distinct_from_owner_do_not_fail_current_ownership(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Organization ownership uses org_id, not unrelated id or site_id metadata."""
    session = RestoreSession(tmp_path)
    original = session.settings[f"/api/v1/orgs/{ORG_ID}/setting"]
    original.update({"id": SITE_ID, "site_id": SITE_ID})
    workflow = session.workflow()
    bundle = workflow.files.read(session.path.stem)
    record = next(record for record in bundle.records if record["scope"] == "org")
    projected: list[str] = []

    def body(scope: str, saved: dict[str, Any], current: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        """Isolate ownership from separately enforced writable schema acceptance."""
        projected.append(scope)
        assert current == original
        return {}, []

    monkeypatch.setattr(workflow.schema, "body", body)
    target, excluded = workflow._target(bundle, record, {ORG_ID: {SITE_ID}})
    assert target.organization == ORG_ID
    assert projected == ["org"]
    assert excluded == []
    assert session.writes == []


@pytest.mark.parametrize("field", ["org_id", "site_id"])
def test_site_wrong_owner_or_scope_identifier_fails_before_projection(tmp_path: Path, field: str) -> None:
    """A scope-correct organization check cannot relax site identity verification."""
    session = RestoreSession(tmp_path)
    session.settings[f"/api/v1/sites/{SITE_ID}/setting"][field] = SITE_ID if field == "org_id" else ORG_ID
    workflow = session.workflow()
    bundle = workflow.files.read(session.path.stem)
    record = next(record for record in bundle.records if record["scope"] == "site")
    with pytest.raises(PolicyError, match="The current settings ownership does not match the selected backup"):
        workflow._target(bundle, record, {ORG_ID: {SITE_ID}})
    assert session.writes == []


def test_org_wrong_owner_still_fails_before_projection(tmp_path: Path) -> None:
    """Distinct metadata never permits an organization response with a different owner."""
    session = RestoreSession(tmp_path)
    session.settings[f"/api/v1/orgs/{ORG_ID}/setting"]["org_id"] = SITE_ID
    workflow = session.workflow()
    bundle = workflow.files.read(session.path.stem)
    record = next(record for record in bundle.records if record["scope"] == "org")
    with pytest.raises(PolicyError, match="The current settings ownership does not match the selected backup"):
        workflow._target(bundle, record, {ORG_ID: {SITE_ID}})
    assert session.writes == []


def test_policy_preparation_accepts_nonpolicy_unknown_null_and_redacted_values(tmp_path: Path) -> None:
    """Recovery usability concerns saved policies, not unrelated response schema drift."""
    session, workflow, previous = prepared(tmp_path)
    uri = f"/api/v1/sites/{SITE_ID}/setting"
    session.settings[uri].update(
        {
            "unknown": "x" * 121856,
            "uwb_config": {"port": None},
            "mist_nac": {"idps": [{"id": ORG_ID}]},
        }
    )
    session.settings[uri]["ssr"]["conductor_token"] = "<redacted>"
    plans = [workflow.prepare({"id": ORG_ID, "name": "Fixture Organization"}, [])]
    proof = workflow.back_up(plans)
    workflow.backup.verify(proof.path, workflow.records(plans))
    assert session.writes == []
    assert proof.path.stat().st_size > 120000


def test_policy_new_org_ap_without_proven_absence_recovery_blocks_readiness(tmp_path: Path) -> None:
    """A new organization policy cannot receive confirmation when its absence cannot be restored."""
    from src.operations.execution.firmware_policy.changes import FirmwarePolicy

    session, workflow, previous = prepared(tmp_path)
    session.settings[f"/api/v1/orgs/{ORG_ID}/setting"].pop("auto_upgrade")
    plans = [workflow.prepare({"id": ORG_ID}, [FirmwarePolicy("ap", False, {"AP41": "historical"})])]
    with pytest.raises(PolicyError, match="Confirmation is blocked"):
        workflow.back_up(plans)
    assert session.writes == []
    assert not (tmp_path / ".firmware-policy-backups").exists()

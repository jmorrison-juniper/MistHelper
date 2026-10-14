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
    assert "source backup changed" in result.error


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

"""Prove legacy ownership limits, saved-state identity, and post-backup freshness."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.operations.execution.firmware_policy.recovery.backup import PolicyBackup
from src.operations.execution.firmware_policy.sdk import PolicyError
from tests.unit.firmware_policy.fakes import ORG_ID, SITE_ID
from tests.unit.firmware_policy.recovery.fakes import RestoreSession


@pytest.mark.parametrize("case", ["wrong-cloud", "wrong-owner", "foreign-site", "ambiguous-owner"])
def test_scope_and_cloud_mismatch_fail_before_writes(tmp_path: Path, monkeypatch: Any, case: str) -> None:
    """Do not infer site ownership or cloud authenticity from a valid checksum."""
    session = RestoreSession(tmp_path)
    workflow = session.workflow()
    if case == "wrong-cloud":
        cloud = "api.eu.mist.com"
    else:
        cloud = session.cloud
    if case == "wrong-owner":
        session.settings[f"/api/v1/sites/{SITE_ID}/setting"]["org_id"] = SITE_ID
    if case == "foreign-site":
        monkeypatch.setattr(workflow.api, "sites", lambda organization: [])
    if case == "ambiguous-owner":
        session.saved[1]["settings"].pop("org_id")
        session.saved.append({"scope": "org", "id": "00000000-0000-0000-0000-000000000099", "settings": {}})
        session.path = session.backup.save(session.saved)
    with pytest.raises(PolicyError):
        workflow.prepare(session.path.stem, [f"org:{ORG_ID}", f"site:{SITE_ID}"], cloud)
    assert session.writes == []


def test_settings_changed_during_recovery_backup_stops_all_writes(tmp_path: Path, monkeypatch: Any) -> None:
    """Freshness must be checked after durable backup verification as well as before it."""
    session = RestoreSession(tmp_path)
    plan = session.prepare()
    save = PolicyBackup.save

    def changed(self: PolicyBackup, records: list[dict[str, Any]]) -> Path:
        """Change current state only after the recovery bundle is durable."""
        path = save(self, records)
        session.settings[f"/api/v1/orgs/{ORG_ID}/setting"]["allow_mist"] = True
        return path

    monkeypatch.setattr(PolicyBackup, "save", changed)
    with pytest.raises(PolicyError, match="changed after preview"):
        session.workflow().apply(plan, "RESTORE")
    assert session.writes == []


@pytest.mark.parametrize("failure", ["read", "identity", "site-stale", "membership", "cancel"])
def test_mid_run_failures_stop_with_exact_partial_results(tmp_path: Path, monkeypatch: Any, failure: str) -> None:
    """Readback and between-target failures must not permit a later site write."""
    session = RestoreSession(tmp_path)
    workflow = session.workflow()
    plan = session.prepare()
    put = session.mist_put

    def changed(uri: str, body: dict[str, Any]) -> Any:
        """Change one dependency immediately after the organization settings write."""
        response = put(uri, body)
        if failure == "read":
            session.fail_read = uri
        elif failure == "identity":
            session.settings[uri]["org_id"] = SITE_ID
        elif failure == "site-stale":
            session.settings[f"/api/v1/sites/{SITE_ID}/setting"]["dns_servers"] = ["9.9.9.9"]
        elif failure == "membership":
            monkeypatch.setattr(workflow.api, "sites", lambda organization: [])
        else:
            workflow.stopped = lambda: True
        return response

    monkeypatch.setattr(session, "mist_put", changed)
    result = workflow.apply(plan, "RESTORE")
    assert len(session.writes) == 1
    if failure in ("read", "identity"):
        assert result.completed == []
        assert result.failed == [f"org:{ORG_ID}"]
        assert result.remaining == [f"site:{SITE_ID}"]
    else:
        assert result.completed == [f"org:{ORG_ID}"]
        assert result.failed == [f"site:{SITE_ID}"]
        assert result.remaining == []


def test_nested_parent_replacement_restores_missing_child_without_changing_input(tmp_path: Path) -> None:
    """A complete parent body must restore saved siblings rather than current siblings."""
    session = RestoreSession(tmp_path)
    session.settings[f"/api/v1/orgs/{ORG_ID}/setting"]["ssr"]["disable_stats"] = True
    original = session.path.read_bytes()
    result = session.workflow().apply(session.prepare(), "RESTORE")
    assert len(result.completed) == 2
    assert session.settings[f"/api/v1/orgs/{ORG_ID}/setting"]["ssr"] == {"conductor_token": "private-fixture"}
    assert session.path.read_bytes() == original


@pytest.mark.parametrize("content", [b"", b"bad json"])
def test_saved_scope_selection_cannot_bypass_invalid_json(tmp_path: Path, content: bytes) -> None:
    """Even known scope identifiers cannot restore from an unreadable source bundle."""
    session = RestoreSession(tmp_path)
    session.path.write_bytes(content)
    with pytest.raises(PolicyError, match="could not be read or parsed"):
        session.prepare()
    assert session.writes == []
    assert session.reads == []

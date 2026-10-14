"""Prove complete recovery coverage, ordered restoration, and precise partial results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.operations.execution.firmware_policy.cli import PolicyMenuInputs, PolicyPrompt
from src.operations.execution.firmware_policy.recovery.backup import BackupAccess, PolicyBackup
from src.operations.execution.firmware_policy.recovery.cli import RestoreMenu
from src.operations.execution.firmware_policy.sdk import PolicyError
from tests.unit.firmware_policy.fakes import ORG_ID, SITE_ID
from tests.unit.firmware_policy.recovery.fakes import RestoreSession


def test_complete_restore_preserves_original_and_verifies_all_recovery_records(
    tmp_path: Path, monkeypatch: Any
) -> None:
    """Every current target must have a verified complete recovery record before writes."""
    session = RestoreSession(tmp_path)
    original = session.path.read_bytes()
    plan = session.prepare()
    preview = plan.preview()
    assert [target["changed_fields"] for target in preview["targets"]] == [1, 2]
    assert preview["excluded"] == {f"org:{ORG_ID}": ["org_id"], f"site:{SITE_ID}": ["org_id", "site_id"]}
    verified: list[list[dict[str, Any]]] = []
    verify = PolicyBackup.verify
    put = session.mist_put

    def checked_verify(self: PolicyBackup, path: Path, records: list[dict[str, Any]]) -> None:
        """Record actual durable comparisons without weakening their behavior."""
        verify(self, path, records)
        verified.append(records)

    def checked_put(uri: str, body: dict[str, Any]) -> Any:
        """Fail if any write precedes complete verified recovery coverage."""
        assert len(verified) >= 2
        assert {record["id"] for record in verified[-1]} == {ORG_ID, SITE_ID}
        assert all(
            record["settings"] == target.original for record, target in zip(verified[-1], plan.targets, strict=True)
        )
        return put(uri, body)

    monkeypatch.setattr(PolicyBackup, "verify", checked_verify)
    monkeypatch.setattr(session, "mist_put", checked_put)
    result = session.workflow().apply(plan, "RESTORE")
    assert result.completed == [f"org:{ORG_ID}", f"site:{SITE_ID}"]
    assert result.failed == result.remaining == []
    assert result.backups_verified == 2
    assert session.writes == [
        (
            f"/api/v1/orgs/{ORG_ID}/setting",
            {"allow_mist": True, "auto_upgrade": {"enabled": True}, "ssr": {"conductor_token": "private-fixture"}},
        ),
        (f"/api/v1/sites/{SITE_ID}/setting", {"dns_servers": ["8.8.8.8"], "-auto_upgrade": ""}),
    ]
    assert session.path.read_bytes() == original


@pytest.mark.parametrize("confirmation", ["", "restore", "RESTORE ", " RESTORE", "YES"])
def test_exact_confirmation_precedes_backups_and_writes(tmp_path: Path, confirmation: str) -> None:
    """Do not accept trimmed or lower-case substitutes for the required word."""
    session = RestoreSession(tmp_path)
    plan = session.prepare()
    with pytest.raises(PolicyError, match="RESTORE exactly"):
        session.workflow().apply(plan, confirmation)
    assert session.writes == []
    assert len(list(session.backup.root.iterdir())) == 1


@pytest.mark.parametrize("change", ["settings", "source", "cloud", "membership", "cancel"])
def test_stale_or_cancelled_plan_stops_before_recovery_and_writes(
    tmp_path: Path, monkeypatch: Any, change: str
) -> None:
    """Every preview dependency must remain current before the recovery gate."""
    session = RestoreSession(tmp_path)
    plan = session.prepare()
    workflow = session.workflow()
    if change == "settings":
        session.settings[f"/api/v1/orgs/{ORG_ID}/setting"]["allow_mist"] = True
    elif change == "source":
        document = json.loads(session.path.read_text())
        document["records"][0]["settings"]["allow_mist"] = False
        document["sha256"] = PolicyBackup.digest(document["records"])
        session.path.write_text(json.dumps(document))
    elif change == "cloud":
        session.cloud = "api.eu.mist.com"
    elif change == "membership":
        monkeypatch.setattr(workflow.api, "sites", lambda organization: [])
    else:
        workflow.stopped = lambda: True
    with pytest.raises(PolicyError):
        workflow.apply(plan, "RESTORE")
    assert session.writes == []
    assert len(list(session.backup.root.iterdir())) == 1


@pytest.mark.parametrize("stage", ["save", "verify"])
def test_failed_recovery_gate_sends_no_write(tmp_path: Path, monkeypatch: Any, stage: str) -> None:
    """A failed durable recovery step cannot become a partially protected restore."""
    session = RestoreSession(tmp_path)
    plan = session.prepare()

    def failed(*args: Any) -> Any:
        """Simulate an unavailable recovery store without bypassing the workflow."""
        raise PolicyError("The recovery backup failed.")

    monkeypatch.setattr(PolicyBackup, stage, failed)
    with pytest.raises(PolicyError, match="recovery backup failed"):
        session.workflow().apply(plan, "RESTORE")
    assert session.writes == []


def test_private_recovery_access_precedes_backup_contents_and_cloud_writes(tmp_path: Path, monkeypatch: Any) -> None:
    """An unproven recovery-file ACL must stop before settings enter that file."""
    session = RestoreSession(tmp_path)
    plan = session.prepare()
    verify = BackupAccess.verify

    def access(path: Path, directory: bool = False, status: Any = None) -> None:
        """Reject only a new recovery file while retaining the original source checks."""
        if not directory and path != session.path:
            raise PolicyError("Recovery file access could not be verified.")
        verify(path, directory=directory, status=status)

    monkeypatch.setattr(BackupAccess, "verify", access)
    with pytest.raises(PolicyError, match="Recovery file access"):
        session.workflow().apply(plan, "RESTORE")
    assert session.writes == []
    recovery = [path for path in session.backup.root.iterdir() if path != session.path]
    assert len(recovery) == 1
    assert recovery[0].read_bytes() == b""


def test_recovery_bundle_must_pass_the_same_restore_loader_before_writes(tmp_path: Path) -> None:
    """A durable recovery file outside supported restore bounds cannot permit a change."""
    session = RestoreSession(tmp_path)
    session.settings[f"/api/v1/orgs/{ORG_ID}/setting"]["ssr"]["conductor_token"] = "x" * (8 * 1024 * 1024)
    original = session.path.read_bytes()
    with pytest.raises(PolicyError, match="could not be verified"):
        session.workflow().apply(session.prepare(), "RESTORE")
    assert session.writes == []
    assert session.path.read_bytes() == original


@pytest.mark.parametrize("status", [400, 403, 500, 503])
@pytest.mark.parametrize("scope", ["org", "site"])
def test_failed_write_stops_with_precise_partial_result(tmp_path: Path, status: int, scope: str) -> None:
    """An attempted failed target differs from verified and unattempted targets."""
    session = RestoreSession(tmp_path)
    session.status = status
    session.fail_write = (
        f"/api/v1/{'orgs' if scope == 'org' else 'sites'}/{ORG_ID if scope == 'org' else SITE_ID}/setting"
    )
    result = session.workflow().apply(session.prepare(), "RESTORE")
    assert result.failed == [f"{scope}:{ORG_ID if scope == 'org' else SITE_ID}"]
    assert result.completed == ([f"org:{ORG_ID}"] if scope == "site" else [])
    assert result.remaining == ([f"site:{SITE_ID}"] if scope == "org" else [])
    assert len(session.writes) == (2 if scope == "site" else 1)
    assert f"HTTP {status}" in result.error
    assert "private-fixture" not in str(result)


def test_failed_saved_state_stops_later_scopes(tmp_path: Path) -> None:
    """A successful status without persistence must not count as completed."""
    session = RestoreSession(tmp_path)
    session.ignore_write = True
    result = session.workflow().apply(session.prepare(), "RESTORE")
    assert result.completed == []
    assert result.failed == [f"org:{ORG_ID}"]
    assert result.remaining == [f"site:{SITE_ID}"]
    assert len(session.writes) == 1


@pytest.mark.parametrize(
    "selection", [[f"site:{SITE_ID}"], [f"org:{ORG_ID}", f"site:{SITE_ID}", f"site:{SITE_ID}"], ["site:unknown"]]
)
def test_invalid_selection_dependencies_fail(tmp_path: Path, selection: list[str]) -> None:
    """A site cannot restore without its organization or through an invented record."""
    session = RestoreSession(tmp_path)
    with pytest.raises(PolicyError):
        session.workflow().prepare(session.path.stem, selection, session.cloud)
    assert session.writes == []


@pytest.mark.parametrize("dry_run", [False, True])
def test_cli_complete_and_dry_run(tmp_path: Path, monkeypatch: Any, capsys: Any, dry_run: bool) -> None:
    """The real menu shares complete restoration guards and keeps values private."""
    session = RestoreSession(tmp_path)
    choices = iter(["1", "A", session.cloud])
    prompt = PolicyPrompt(reader=lambda prompt: next(choices))
    monkeypatch.setattr(
        "src.operations.execution.firmware_policy.recovery.cli.InputUtils.safe_input", lambda *args, **kwargs: "RESTORE"
    )
    menu = RestoreMenu(
        session.workflow().api, PolicyMenuInputs(lambda: ORG_ID, dry_run=dry_run, data_directory=tmp_path), prompt
    )
    menu.run()
    assert len(session.writes) == (0 if dry_run else 2)
    assert "private-fixture" not in capsys.readouterr().out
    assert len(list(session.backup.root.iterdir())) == (1 if dry_run else 2)


@pytest.mark.parametrize("content", [b"", b"bad json"])
def test_complete_workflow_rejects_unreadable_source_before_sdk(tmp_path: Path, content: bytes) -> None:
    """No known selection can bypass the complete source parsing gate."""
    session = RestoreSession(tmp_path)
    session.path.write_bytes(content)
    with pytest.raises(PolicyError, match="could not be read or parsed"):
        session.prepare()
    assert session.writes == []
    assert session.reads == []

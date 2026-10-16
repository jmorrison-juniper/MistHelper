"""Prove phase-aware waits, guarded pagination, and owned inspection dispatch."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from src.operations.execution.firmware_policy.sdk import PolicyApi, PolicyError
from tests.unit.firmware_policy.fakes import ORG_ID, SettingsSession
from tests.unit.firmware_policy_jobs.test_manager import ManualExecutor
from web_portal.routes.firmware_policy.jobs.manager import JobManager


def test_admission_callbacks_retain_capture_and_freshness_phases(tmp_path: Path) -> None:
    """A settings read or allowance wait cannot make the second pass look like capture."""
    executor = ManualExecutor()
    manager = JobManager(tmp_path, executor)
    try:
        identifier = manager.start("owner", "policy", lambda progress: (None, {}))
        manager._progress(identifier, {"phase": "preparing", "completed": 1, "total": 4001})
        manager._progress(identifier, {"phase": "Read site settings", "completed": 1, "total": 4001})
        assert manager.status(identifier, "owner")["progress"]["workflow_phase"] == "preparing"
        manager._progress(identifier, {"phase": "verifying_snapshots", "completed": 4, "total": 4001})
        manager._progress(identifier, {"phase": "waiting", "wait_seconds": 7201, "private": "private-fixture"})
        result = manager.status(identifier, "owner")["progress"]
        assert result["workflow_phase"] == "verifying_snapshots"
        assert result["completed"] == 4 and result["total"] == 4001
        assert result["wait_seconds"] == 7201
        assert "private" not in result
        manager._progress(identifier, {"phase": "backing_up", "completed": 0, "total": 4001})
        assert manager.status(identifier, "owner")["progress"]["workflow_phase"] == "backing_up"
    finally:
        manager.close()


def test_supported_lists_use_1000_and_admit_every_sdk_page(tmp_path: Path, monkeypatch: Any) -> None:
    """Complete pagination retains admission and does not invent bulk settings payloads."""
    session = SettingsSession(tmp_path)
    api = PolicyApi(session)
    first = SimpleNamespace(status_code=200, data=[{"id": ORG_ID}], next="next-page")
    second = SimpleNamespace(status_code=200, data=[{"id": "second"}], next=None)
    calls: list[Any] = []

    def paged(call: Any, action: str, identifier: str) -> Any:
        """Count actual SDK dispatches while choosing the next fixture response."""
        calls.append((action, identifier))
        return first if len(calls) == 1 else call()

    monkeypatch.setattr(api.guard, "request", paged)
    monkeypatch.setattr("mistapi.get_next", lambda actual, response: second)
    assert len(api.sites(ORG_ID)) == 2
    assert len(calls) == 2
    normal = PolicyApi(session)
    normal.sites(ORG_ID)
    normal.inventory(ORG_ID)
    queries = [query for uri, query in session.reads if uri.endswith(("/sites", "/inventory"))]
    assert queries == [{"limit": "1000"}, {"type": "all", "limit": "1000"}]


@pytest.mark.parametrize("status", [403, 503])
def test_paged_api_http_4xx_and_5xx_fail_without_partial_success(tmp_path: Path, status: int) -> None:
    """Maximum page size must not turn a failed list response into an empty result."""
    session = SettingsSession(tmp_path)
    session.fail_read = f"/api/v1/orgs/{ORG_ID}/sites"
    session.status = status
    with pytest.raises(PolicyError, match=f"HTTP {status}") as failure:
        PolicyApi(session).sites(ORG_ID)
    assert "private-fixture" not in str(failure.value)
    assert session.writes == []


@pytest.mark.parametrize("owner", ["", "foreign"])
def test_foreign_comparison_does_not_resolve_private_context(tmp_path: Path, owner: str) -> None:
    """Refuse another browser before looking at or consuming its plan."""
    executor = ManualExecutor()
    manager = JobManager(tmp_path, executor)
    try:
        identifier = manager.start("owner", "policy", lambda progress: (object(), {"preview": {}}))
        executor.run()
        token = manager.status(identifier, "owner")["token"]
        with pytest.raises(PolicyError, match="unavailable"):
            manager.comparison(identifier, owner, {"scope": "org", "id": ORG_ID})
        assert manager.status(identifier, "owner")["token"] == token
    finally:
        manager.close()


def test_other_live_worker_relays_inspection_without_consuming_token(tmp_path: Path, monkeypatch: Any) -> None:
    """Route inspection to the process that retains the verified private plan."""
    owner = JobManager(tmp_path, ManualExecutor())
    other = JobManager(tmp_path, ManualExecutor())
    try:
        identifier = owner.start("browser", "policy", lambda progress: (object(), {"preview": {}}))
        owner.executor.run()
        token = owner.status(identifier, "browser")["token"]
        monkeypatch.setattr(
            "web_portal.routes.firmware_policy.restore.inspection.PreparedInspection.read",
            lambda context, scope, selected: {"scope": scope, "id": selected, "fields": []},
        )
        result = other.comparison(identifier, "browser", {"scope": "org", "id": ORG_ID})
        assert result == {"scope": "org", "id": ORG_ID, "fields": []}
        assert owner.status(identifier, "browser")["token"] == token
    finally:
        other.close()
        owner.close()

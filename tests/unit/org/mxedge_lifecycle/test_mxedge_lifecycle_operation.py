"""Unit tests for the Mist Edge lifecycle operation orchestration."""

from __future__ import annotations  # WHY: match package type syntax.

import csv  # WHY: read the evidence file that the operation writes.
from pathlib import Path  # WHY: tests write under the repository data directory.
from typing import Any  # WHY: fake clients and monkeypatch use dynamic values.

import pytest  # WHY: monkeypatch fixture drives prompts and time.

import src.org.mxedge_lifecycle.operation as operation_module  # WHY: patch module time safely.
from src.org.mxedge_lifecycle.models import STATUS_DRY_RUN, MxEdgeLifecycleModels
from src.org.mxedge_lifecycle.operation import MxEdgeLifecycleOperation  # WHY: system under test.


class FakeClient:
    """Fake lifecycle client that records calls without network."""

    def __init__(self) -> None:
        """Initialize call records and upgrade statuses."""
        self.calls: list[str] = []  # WHY: tests assert whether a request was sent.
        self.statuses: list[dict[str, Any]] = []  # WHY: polling tests control returned statuses.

    def claim(self, body: dict[str, Any]) -> dict[str, Any]:
        """Record a claim call."""
        self.calls.append("claim")  # WHY: prove the request was sent.
        return {"status": "claimed"}  # WHY: accepted response.

    def assign(self, body: dict[str, Any]) -> dict[str, Any]:
        """Record an assign call."""
        self.calls.append("assign")  # WHY: prove the request was sent.
        return {"status": "assigned"}  # WHY: accepted response.

    def unassign(self, body: dict[str, Any]) -> dict[str, Any]:
        """Record an unassign call."""
        self.calls.append("unassign")  # WHY: prove the request was sent.
        return {"status": "unassigned"}  # WHY: accepted response.

    def bounce(self, mxedge_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Record a bounce call."""
        self.calls.append("bounce")  # WHY: prove the request was sent.
        return {"status": "bounced"}  # WHY: accepted response.

    def upgrade(self, body: dict[str, Any]) -> dict[str, Any]:
        """Record an upgrade call."""
        self.calls.append("upgrade")  # WHY: prove the request was sent.
        return {"id": "upgrade-1"}  # WHY: poll uses this identifier.

    def list_upgrades(self) -> list[dict[str, Any]]:
        """Return no fallback upgrades."""
        self.calls.append("list_upgrades")  # WHY: record fallback use.
        return []  # WHY: direct upgrade ID is used in tests.

    def get_upgrade(self, upgrade_id: str) -> dict[str, Any]:
        """Return the next queued upgrade status."""
        self.calls.append(f"get:{upgrade_id}")  # WHY: prove polling read happened.
        return self.statuses.pop(0) if self.statuses else {"status": "completed"}  # WHY: default terminal.


def _csv_path(name: str) -> Path:
    """Return a project-local CSV path and remove a stale file."""
    path = Path("data") / name  # WHY: project-local data path obeys file policy.
    if path.exists():  # WHY: each test needs isolated evidence rows.
        path.unlink()  # WHY: remove stale test output.
    return path  # WHY: caller passes this path to the operation.


def _read_rows(path: Path) -> list[dict[str, str]]:
    """Read CSV rows from a lifecycle test file."""
    with path.open(newline="", encoding="utf-8") as handle:  # WHY: read the file written by the operation.
        return list(csv.DictReader(handle))  # WHY: assertions use column names.


def test_mxedge_lifecycle_wrong_confirmation_sends_no_request() -> None:
    """A wrong confirmation word must block a destructive request."""
    client = FakeClient()  # WHY: record whether claim is sent.
    path = _csv_path("unit_mxedge_lifecycle_wrong.csv")  # WHY: isolate evidence file.
    operation = MxEdgeLifecycleOperation(client, "org-1", path)  # WHY: inject fake client and CSV path.
    request = MxEdgeLifecycleModels.assign(["mx-1"], "site-1")  # WHY: representative destructive request.
    operation._ask = lambda prompt, context: "NO"  # type: ignore[method-assign]  # WHY: simulate wrong word.
    operation._execute(request, lambda: client.assign(request.body))  # WHY: run the confirmation gate.
    assert client.calls == []  # WHY: no request may be sent.
    assert _read_rows(path)[0]["status"] == "cancelled"  # WHY: CSV records the refusal.


def test_mxedge_lifecycle_dry_run_sends_no_request() -> None:
    """Dry-run must write evidence and send no request."""
    client = FakeClient()  # WHY: record whether claim is sent.
    path = _csv_path("unit_mxedge_lifecycle_dry_run.csv")  # WHY: isolate evidence file.
    operation = MxEdgeLifecycleOperation(client, "org-1", path)  # WHY: inject fake client and CSV path.
    request = MxEdgeLifecycleModels.bounce("mx-1", ["0"], dry_run=True)  # WHY: dry-run request.
    operation._ask = lambda prompt, context: "BOUNCE"  # type: ignore[method-assign]  # WHY: correct word.
    operation._execute(request, lambda: client.bounce("mx-1", request.body))  # WHY: run the dry-run gate.
    rows = _read_rows(path)  # WHY: inspect evidence.
    assert client.calls == []  # WHY: dry-run sends no API request.
    assert rows[0]["status"] == STATUS_DRY_RUN  # WHY: row names dry-run.


def test_mxedge_lifecycle_claim_code_not_written_to_csv() -> None:
    """Claim evidence must not store the claim code."""
    secret = "135-546-673"  # WHY: value must be absent from CSV evidence.
    client = FakeClient()  # WHY: record whether claim is sent.
    path = _csv_path("unit_mxedge_lifecycle_claim.csv")  # WHY: isolate evidence file.
    operation = MxEdgeLifecycleOperation(client, "org-1", path)  # WHY: inject fake client and CSV path.
    request = MxEdgeLifecycleModels.claim(secret)  # WHY: build claim request.
    operation._ask = lambda prompt, context: "CLAIM"  # type: ignore[method-assign]  # WHY: correct word.
    operation._execute(request, lambda: client.claim(request.body))  # WHY: send the claim through operation.
    assert secret not in path.read_text(encoding="utf-8")  # WHY: CSV must redact the claim code.
    assert client.calls == ["claim"]  # WHY: live request still sends through fake client.


def test_mxedge_lifecycle_polling_stops_on_terminal_status(monkeypatch: pytest.MonkeyPatch) -> None:
    """Upgrade polling must stop when Mist returns a terminal status."""
    client = FakeClient()  # WHY: fake status API.
    client.statuses = [{"status": "running"}, {"status": "completed"}]  # WHY: second read is terminal.
    path = _csv_path("unit_mxedge_lifecycle_poll.csv")  # WHY: isolate evidence file.
    operation = MxEdgeLifecycleOperation(client, "org-1", path)  # WHY: inject fake client.
    monkeypatch.setattr(operation_module.time, "sleep", lambda seconds: None)  # WHY: avoid real wait.
    result = operation.poll_upgrade("upgrade-1", timeout_seconds=30)  # WHY: run polling loop.
    assert result.terminal is True  # WHY: completed is terminal.
    assert result.poll_count == 2  # WHY: one running read and one completed read.
    assert client.calls == ["get:upgrade-1", "get:upgrade-1"]  # WHY: no extra read after terminal.


def test_mxedge_lifecycle_polling_stops_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Upgrade polling must stop when the timeout expires."""
    client = FakeClient()  # WHY: fake status API.
    client.statuses = [{"status": "running"}, {"status": "running"}]  # WHY: never terminal.
    times = iter([0, 1, 2, 99])  # WHY: force timeout after two reads.
    path = _csv_path("unit_mxedge_lifecycle_timeout.csv")  # WHY: isolate evidence file.
    operation = MxEdgeLifecycleOperation(client, "org-1", path)  # WHY: inject fake client.
    monkeypatch.setattr(operation_module.time, "monotonic", lambda: next(times))  # WHY: deterministic clock.
    monkeypatch.setattr(operation_module.time, "sleep", lambda seconds: None)  # WHY: avoid real wait.
    result = operation.poll_upgrade("upgrade-1", timeout_seconds=2)  # WHY: run timeout path.
    assert result.timed_out is True  # WHY: timeout must be reported.
    assert result.terminal is False  # WHY: no terminal status occurred.
    assert result.poll_count == 2  # WHY: loop stops after the timeout check.

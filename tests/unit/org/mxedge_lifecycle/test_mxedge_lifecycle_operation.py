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
        self.bodies: list[dict[str, Any]] = []  # WHY: prompt-driven tests assert exact request bodies.
        self.statuses: list[dict[str, Any]] = []  # WHY: polling tests control returned statuses.

    def claim(self, body: dict[str, Any]) -> dict[str, Any]:
        """Record a claim call."""
        self.calls.append("claim")  # WHY: prove the request was sent.
        self.bodies.append(body)  # WHY: prove the operation built the expected body.
        return {"status": "claimed"}  # WHY: accepted response.

    def assign(self, body: dict[str, Any]) -> dict[str, Any]:
        """Record an assign call."""
        self.calls.append("assign")  # WHY: prove the request was sent.
        self.bodies.append(body)  # WHY: prove the operation built the expected body.
        return {"status": "assigned"}  # WHY: accepted response.

    def unassign(self, body: dict[str, Any]) -> dict[str, Any]:
        """Record an unassign call."""
        self.calls.append("unassign")  # WHY: prove the request was sent.
        self.bodies.append(body)  # WHY: prove the operation built the expected body.
        return {"status": "unassigned"}  # WHY: accepted response.

    def bounce(self, mxedge_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Record a bounce call."""
        self.calls.append("bounce")  # WHY: prove the request was sent.
        self.bodies.append({"mxedge_id": mxedge_id, **body})  # WHY: prove path ID and body shape.
        return {"status": "bounced"}  # WHY: accepted response.

    def upgrade(self, body: dict[str, Any]) -> dict[str, Any]:
        """Record an upgrade call."""
        self.calls.append("upgrade")  # WHY: prove the request was sent.
        self.bodies.append(body)  # WHY: prove the operation built the expected body.
        return {"id": "upgrade-1"}  # WHY: poll uses this identifier.

    def list_upgrades(self) -> list[dict[str, Any]]:
        """Return no fallback upgrades."""
        self.calls.append("list_upgrades")  # WHY: record fallback use.
        return []  # WHY: direct upgrade ID is used in tests.

    def get_upgrade(self, upgrade_id: str) -> dict[str, Any]:
        """Return the next queued upgrade status."""
        self.calls.append(f"get:{upgrade_id}")  # WHY: prove polling read happened.
        return self.statuses.pop(0) if self.statuses else {"status": "completed"}  # WHY: default terminal.


def _csv_path(tmp_path: Path, name: str) -> Path:
    """Return a per-test CSV path under `tmp_path`."""
    return tmp_path / name  # WHY: tmp_path keeps output away from the repository data directory.


def _read_rows(path: Path) -> list[dict[str, str]]:
    """Read CSV rows from a lifecycle test file."""
    with path.open(newline="", encoding="utf-8") as handle:  # WHY: read the file written by the operation.
        return list(csv.DictReader(handle))  # WHY: assertions use column names.


def test_mxedge_lifecycle_wrong_confirmation_sends_no_request(tmp_path: Path) -> None:
    """A wrong confirmation word must block a destructive request."""
    client = FakeClient()  # WHY: record whether claim is sent.
    path = _csv_path(tmp_path, "wrong.csv")  # WHY: isolate evidence file.
    operation = MxEdgeLifecycleOperation(client, "org-1", path)  # WHY: inject fake client and CSV path.
    request = MxEdgeLifecycleModels.assign(["mx-1"], "site-1")  # WHY: representative destructive request.
    operation._ask = lambda prompt, context: "NO"  # type: ignore[method-assign]  # WHY: simulate wrong word.
    operation._execute(request, lambda: client.assign(request.body))  # WHY: run the confirmation gate.
    assert client.calls == []  # WHY: no request may be sent.
    assert _read_rows(path)[0]["status"] == "cancelled"  # WHY: CSV records the refusal.


def test_mxedge_lifecycle_dry_run_sends_no_request(tmp_path: Path) -> None:
    """Dry-run must write evidence and send no request."""
    client = FakeClient()  # WHY: record whether claim is sent.
    path = _csv_path(tmp_path, "dry_run.csv")  # WHY: isolate evidence file.
    operation = MxEdgeLifecycleOperation(client, "org-1", path)  # WHY: inject fake client and CSV path.
    request = MxEdgeLifecycleModels.bounce("mx-1", ["0"], dry_run=True)  # WHY: dry-run request.
    operation._ask = lambda prompt, context: "BOUNCE"  # type: ignore[method-assign]  # WHY: correct word.
    operation._execute(request, lambda: client.bounce("mx-1", request.body))  # WHY: run the dry-run gate.
    rows = _read_rows(path)  # WHY: inspect evidence.
    assert client.calls == []  # WHY: dry-run sends no API request.
    assert rows[0]["status"] == STATUS_DRY_RUN  # WHY: row names dry-run.


def test_mxedge_lifecycle_claim_code_not_written_to_csv(tmp_path: Path) -> None:
    """Claim evidence must not store the claim code."""
    secret = "135-546-673"  # WHY: value must be absent from CSV evidence.
    client = FakeClient()  # WHY: record whether claim is sent.
    path = _csv_path(tmp_path, "claim.csv")  # WHY: isolate evidence file.
    operation = MxEdgeLifecycleOperation(client, "org-1", path)  # WHY: inject fake client and CSV path.
    request = MxEdgeLifecycleModels.claim(secret)  # WHY: build claim request.
    operation._ask = lambda prompt, context: "CLAIM"  # type: ignore[method-assign]  # WHY: correct word.
    operation._execute(request, lambda: client.claim(request.body))  # WHY: send the claim through operation.
    assert secret not in path.read_text(encoding="utf-8")  # WHY: CSV must redact the claim code.
    assert client.calls == ["claim"]  # WHY: live request still sends through fake client.


def test_mxedge_lifecycle_polling_stops_on_terminal_status(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Upgrade polling must stop when Mist returns a terminal status."""
    client = FakeClient()  # WHY: fake status API.
    client.statuses = [{"status": "running"}, {"status": "completed"}]  # WHY: second read is terminal.
    path = _csv_path(tmp_path, "poll.csv")  # WHY: isolate evidence file.
    operation = MxEdgeLifecycleOperation(client, "org-1", path)  # WHY: inject fake client.
    monkeypatch.setattr(operation_module.time, "sleep", lambda seconds: None)  # WHY: avoid real wait.
    result = operation.poll_upgrade("upgrade-1", timeout_seconds=30)  # WHY: run polling loop.
    assert result.terminal is True  # WHY: completed is terminal.
    assert result.poll_count == 2  # WHY: one running read and one completed read.
    assert client.calls == ["get:upgrade-1", "get:upgrade-1"]  # WHY: no extra read after terminal.


def test_mxedge_lifecycle_polling_stops_on_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Upgrade polling must stop when the timeout expires."""
    client = FakeClient()  # WHY: fake status API.
    client.statuses = [{"status": "running"}, {"status": "running"}]  # WHY: never terminal.
    times = iter([0, 1, 2, 99])  # WHY: force timeout after two reads.
    path = _csv_path(tmp_path, "timeout.csv")  # WHY: isolate evidence file.
    operation = MxEdgeLifecycleOperation(client, "org-1", path)  # WHY: inject fake client.
    monkeypatch.setattr(operation_module.time, "monotonic", lambda: next(times))  # WHY: deterministic clock.
    monkeypatch.setattr(operation_module.time, "sleep", lambda seconds: None)  # WHY: avoid real wait.
    result = operation.poll_upgrade("upgrade-1", timeout_seconds=2)  # WHY: run timeout path.
    assert result.timed_out is True  # WHY: timeout must be reported.
    assert result.terminal is False  # WHY: no terminal status occurred.
    assert result.poll_count == 2  # WHY: loop stops after the timeout check.


def _run_prompted_menu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, answers: list[str], client: FakeClient
) -> tuple[MxEdgeLifecycleOperation, Path]:
    """Run one menu step with scripted operator answers."""
    csv_path = tmp_path / "mxedge_lifecycle.csv"  # WHY: tmp_path keeps test evidence isolated.
    answer_iter = iter(answers)  # WHY: each prompt consumes one planned answer.
    monkeypatch.setattr(  # WHY: drive prompts like the menu 270 operation tests.
        operation_module.InputUtils,
        "safe_input",
        lambda prompt, context: next(answer_iter),
    )
    operation = MxEdgeLifecycleOperation(client, "org-1", csv_path)  # WHY: inject fake client and output path.
    operation.run_menu()  # WHY: drive the real sub-menu path.
    return operation, csv_path  # WHY: callers inspect the CSV and operation state.


def test_mxedge_lifecycle_prompted_claim_sends_after_confirmation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The claim menu path must send only after `CLAIM`."""
    client = FakeClient()  # WHY: record the request without network.
    _, path = _run_prompted_menu(monkeypatch, tmp_path, ["1", "135-546-673", "n", "CLAIM"], client)
    rows = _read_rows(path)  # WHY: verify one evidence row.
    assert client.calls == ["claim"]  # WHY: correct confirmation sends one request.
    assert client.bodies == [{"code": "135-546-673"}]  # WHY: OpenAPI body reaches client.
    assert rows[0]["target"] == "REDACTED"  # WHY: claim code is redacted in CSV.
    assert "135-546-673" not in path.read_text(encoding="utf-8")  # WHY: secret is absent from evidence.


def test_mxedge_lifecycle_prompted_assign_sends_after_confirmation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The assign menu path must build the site assignment body."""
    client = FakeClient()  # WHY: record the request without network.
    _, path = _run_prompted_menu(monkeypatch, tmp_path, ["2", "mx-1,mx-2", "site-1", "n", "ASSIGN"], client)
    assert client.calls == ["assign"]  # WHY: correct confirmation sends one request.
    assert client.bodies == [{"mxedge_ids": ["mx-1", "mx-2"], "site_id": "site-1"}]
    assert _read_rows(path)[0]["status"] == "sent"  # WHY: CSV receives one sent row.


def test_mxedge_lifecycle_empty_assign_ids_prints_one_sentence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Empty assign targets print one sentence and send no request."""
    client = FakeClient()  # WHY: record whether any request is sent.
    _, path = _run_prompted_menu(monkeypatch, tmp_path, ["2", ""], client)  # WHY: reproduce empty live answer.
    output = capsys.readouterr().out  # WHY: inspect the operator-facing validation message.
    assert client.calls == []  # WHY: empty IDs must stop before any API request.
    assert not path.exists()  # WHY: no request object means no lifecycle evidence row.
    assert "No Mist request was sent because mxedge_ids must contain at least one value." in output  # WHY.
    assert "Traceback" not in output  # WHY: validation must not expose a Python traceback.


def test_mxedge_lifecycle_prompted_unassign_sends_after_confirmation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The unassign menu path must build the unassign body."""
    client = FakeClient()  # WHY: record the request without network.
    _, path = _run_prompted_menu(monkeypatch, tmp_path, ["3", "mx-1", "n", "UNASSIGN"], client)
    assert client.calls == ["unassign"]  # WHY: correct confirmation sends one request.
    assert client.bodies == [{"mxedge_ids": ["mx-1"]}]  # WHY: OpenAPI body reaches client.
    assert len(_read_rows(path)) == 1  # WHY: CSV receives one row for the request.


def test_mxedge_lifecycle_prompted_bounce_sends_after_confirmation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The bounce menu path must build the data-port body."""
    client = FakeClient()  # WHY: record the request without network.
    _, path = _run_prompted_menu(monkeypatch, tmp_path, ["4", "mx-1", "0,2", "n", "BOUNCE"], client)
    assert client.calls == ["bounce"]  # WHY: correct confirmation sends one request.
    assert client.bodies == [{"mxedge_id": "mx-1", "ports": ["0", "2"]}]  # WHY: path and body are correct.
    assert _read_rows(path)[0]["detail"] == "bounced"  # WHY: CSV records the response status.


def test_mxedge_lifecycle_prompted_upgrade_polls_and_writes_one_row(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The upgrade menu path must poll status after the upgrade request."""
    client = FakeClient()  # WHY: record the request without network.
    client.statuses = [{"status": "running"}, {"status": "completed"}]  # WHY: terminal on the second poll.
    monkeypatch.setattr(operation_module.time, "sleep", lambda seconds: None)  # WHY: avoid real wait.
    _, path = _run_prompted_menu(monkeypatch, tmp_path, ["5", "mx-1", "default", "n", "UPGRADE"], client)
    rows = _read_rows(path)  # WHY: inspect upgrade evidence.
    assert client.calls == ["upgrade", "get:upgrade-1", "get:upgrade-1"]  # WHY: submit then poll twice.
    assert client.bodies == [{"mxedge_ids": ["mx-1"], "strategy": "serial", "versions": {"tunterm": "default"}}]
    assert rows[0]["detail"] == "upgrade_id=upgrade-1 status=completed polls=2"  # WHY: final poll is recorded.


def test_mxedge_lifecycle_prompted_wrong_word_sends_nothing_and_logs_cancel(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A wrong confirmation word must send nothing and log the cancel."""
    client = FakeClient()  # WHY: record whether any request is sent.
    with caplog.at_level("INFO"):
        _, path = _run_prompted_menu(monkeypatch, tmp_path, ["2", "mx-1", "site-1", "n", "WRONG"], client)
    assert client.calls == []  # WHY: wrong confirmation gates the request.
    assert _read_rows(path)[0]["status"] == "cancelled"  # WHY: CSV records the cancellation.
    assert "cancelled by confirmation" in caplog.text  # WHY: operator log names the cancel.


def test_mxedge_lifecycle_prompted_dry_run_prints_request_and_sends_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Dry-run must print a safe request and send nothing."""
    client = FakeClient()  # WHY: record whether any request is sent.
    _, path = _run_prompted_menu(monkeypatch, tmp_path, ["4", "mx-1", "0", "y", "BOUNCE"], client)
    output = capsys.readouterr().out  # WHY: dry-run prints the request preview.
    assert client.calls == []  # WHY: dry-run sends no request.
    assert "Dry run request: bounce" in output  # WHY: operator sees the preview.
    assert "'ports': ['0']" in output  # WHY: preview includes the body shape.
    assert _read_rows(path)[0]["status"] == "dry_run"  # WHY: CSV records dry-run.


def test_mxedge_lifecycle_prompted_upgrade_timeout_writes_timeout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Upgrade polling must stop at the timeout when no terminal status arrives."""
    client = FakeClient()  # WHY: fake status API.
    client.statuses = [{"status": "running"}, {"status": "running"}]  # WHY: never terminal.
    times = iter([0, 1, 2, 1801])  # WHY: default 1800 second timeout expires after two reads.
    monkeypatch.setattr(operation_module.time, "monotonic", lambda: next(times))  # WHY: deterministic timeout.
    monkeypatch.setattr(operation_module.time, "sleep", lambda seconds: None)  # WHY: avoid real wait.
    _, path = _run_prompted_menu(monkeypatch, tmp_path, ["5", "mx-1", "default", "n", "UPGRADE"], client)
    rows = _read_rows(path)  # WHY: inspect timeout evidence.
    assert client.calls == ["upgrade", "get:upgrade-1", "get:upgrade-1"]  # WHY: polling stopped at timeout.
    assert rows[0]["status"] == "timeout"  # WHY: timeout row is explicit.
    assert rows[0]["detail"] == "upgrade_id=upgrade-1 status=running polls=2"  # WHY: final state is recorded.


def test_mxedge_lifecycle_prompted_quit_and_invalid_choice_do_not_write(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Quit and invalid menu choices must not create a lifecycle row."""
    client = FakeClient()  # WHY: prove no request is sent.
    with caplog.at_level("INFO"):
        _, quit_path = _run_prompted_menu(monkeypatch, tmp_path, ["q"], client)
    assert client.calls == []  # WHY: quit sends nothing.
    assert not quit_path.exists()  # WHY: quit writes no evidence row.
    client = FakeClient()  # WHY: isolate invalid-choice behavior.
    with caplog.at_level("ERROR"):
        _, invalid_path = _run_prompted_menu(monkeypatch, tmp_path, ["9"], client)
    assert client.calls == []  # WHY: invalid choice sends nothing.
    assert not invalid_path.exists()  # WHY: invalid choice writes no evidence row.
    assert "Invalid Mist Edge lifecycle menu choice" in caplog.text  # WHY: operator sees the refusal.


def test_mxedge_lifecycle_execute_records_client_error(tmp_path: Path) -> None:
    """A client exception must create an error row."""
    client = FakeClient()  # WHY: fake client is enough for operation construction.
    path = _csv_path(tmp_path, "client_error.csv")  # WHY: tmp_path keeps output isolated.
    operation = MxEdgeLifecycleOperation(client, "org-1", path)  # WHY: inject output path.
    request = MxEdgeLifecycleModels.assign(["mx-1"], "site-1")  # WHY: representative live request.
    operation._ask = lambda prompt, context: "ASSIGN"  # type: ignore[method-assign]  # WHY: pass confirmation.
    operation._execute(request, lambda: (_ for _ in ()).throw(RuntimeError("api failed")))  # WHY: force error.
    rows = _read_rows(path)  # WHY: inspect error evidence.
    assert rows[0]["status"] == "error"  # WHY: exception becomes an error row.
    assert rows[0]["detail"] == "api failed"  # WHY: detail names the safe error.


def test_mxedge_lifecycle_upgrade_uses_list_fallback_and_handles_missing_id(tmp_path: Path) -> None:
    """Upgrade ID fallback must select a matching row or fail clearly."""
    client = FakeClient()  # WHY: fake list response is controlled here.
    operation = MxEdgeLifecycleOperation(client, "org-1", _csv_path(tmp_path, "fallback.csv"))
    client.list_upgrades = lambda: [{"upgrade_id": "upgrade-2", "mxedge_ids": ["mx-2"]}]  # type: ignore[method-assign]
    assert operation._upgrade_id({}, ["mx-2"]) == "upgrade-2"  # WHY: matching fallback row is used.
    client.list_upgrades = lambda: [{"mxedge_ids": ["mx-3"]}]  # type: ignore[method-assign]
    with pytest.raises(ValueError, match="No Mist Edge upgrade ID"):
        operation._upgrade_id({}, ["mx-2"])  # WHY: no matching ID cannot be polled.


def test_mxedge_lifecycle_claim_dry_run_prints_redacted_body(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Claim dry-run must print a redacted body."""
    client = FakeClient()  # WHY: dry-run should not send any request.
    _, path = _run_prompted_menu(monkeypatch, tmp_path, ["1", "135-546-673", "y", "CLAIM"], client)
    output = capsys.readouterr().out  # WHY: inspect the dry-run preview.
    assert client.calls == []  # WHY: dry-run sends nothing.
    assert "REDACTED" in output  # WHY: body preview is redacted.
    assert "135-546-673" not in output  # WHY: claim code stays secret.
    assert _read_rows(path)[0]["status"] == "dry_run"  # WHY: CSV records dry-run.

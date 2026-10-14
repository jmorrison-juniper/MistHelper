"""Prove bounded execution, private persistence, and fail-closed token ownership."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

import pytest

from src.operations.execution.firmware_policy.sdk import PolicyError
from web_portal.routes.firmware_policy.jobs.manager import JobManager
from web_portal.routes.firmware_policy.jobs.storage import JobFiles
from web_portal.services.data_browser import DataBrowserService


class ManualExecutor:
    """Hold worker calls until the test explicitly advances execution."""

    def __init__(self) -> None:
        """Retain deterministic queued work without creating background threads."""
        self.calls: list[tuple[Any, tuple[Any, ...]]] = []  # Tests control each state transition.

    def submit(self, call: Any, *arguments: Any) -> None:
        """Record a worker instead of racing the test thread."""
        self.calls.append((call, arguments))  # No private workflow runs before the test chooses.

    def run(self) -> None:
        """Execute exactly one admitted worker."""
        call, arguments = self.calls.pop(0)  # Preserve FIFO admission order.
        call(*arguments)  # Exercise the real manager exception and persistence boundary.


def preparation(progress: Any) -> tuple[Any, dict[str, Any]]:
    """Prepare a private proof while emitting a wait beyond the former lifetime."""
    progress({"phase": "waiting", "wait_seconds": 1201, "settings": "private-job-fixture"})
    rows = [
        {"scope": "site", "id": "site", "name": "Alpha", "organization": "Org", "backup": "verified", "status": "ready"}
    ]
    return ("private-job-fixture", object()), {"rows": rows, "preview": {"writes": 0}, "backups_verified": 1}


def test_queued_wait_ready_and_private_persistence(tmp_path: Path) -> None:
    """Keep a long preparation pollable without persisting tokens or settings."""
    executor = ManualExecutor()  # Prevent a real wait in this admission test.
    manager = JobManager(tmp_path, executor)
    identifier = manager.start("owner", "policy", preparation)
    assert manager.status(identifier, "owner")["state"] == "queued"
    executor.run()
    status = manager.status(identifier, "owner")
    assert status["state"] == "ready"
    assert status["progress"] == {"phase": "waiting", "wait_seconds": 1201}
    assert isinstance(status["token"], str) and len(status["token"]) >= 32
    saved = manager.files.directory / f"{identifier}.json"
    assert "private-job-fixture" not in saved.read_text()
    assert status["token"] not in saved.read_text()
    assert "owner" not in manager.status(identifier, "owner")
    if os.name != "nt":
        assert saved.stat().st_mode & 0o777 == 0o600
        assert manager.files.directory.stat().st_mode & 0o777 == 0o700


def test_foreign_poll_and_token_replay_are_rejected(tmp_path: Path) -> None:
    """Consume a token before dispatch and reject foreign access without removing it."""
    executor = ManualExecutor()
    manager = JobManager(tmp_path, executor)
    identifier = manager.start("owner", "policy", preparation)
    executor.run()
    token = manager.status(identifier, "owner")["token"]
    for owner in ("foreign", ""):
        with pytest.raises(PolicyError, match="unavailable"):
            manager.status(identifier, owner)
        with pytest.raises(PolicyError, match="unavailable"):
            manager.apply(owner, token, lambda _: preparation, "policy")
    assert manager.status(identifier, "owner")["token"] == token
    assert (
        manager.apply("owner", token, lambda _: lambda progress: (None, {"result": {"sites": ["site"]}}), "policy")
        == identifier
    )
    assert manager.status(identifier, "owner")["state"] == "applying"
    assert "token" not in manager.status(identifier, "owner")
    with pytest.raises(PolicyError, match="unavailable"):
        manager.apply("owner", token, lambda _: preparation, "policy")
    executor.run()
    assert manager.status(identifier, "owner")["state"] == "complete"
    assert manager.status(identifier, "owner")["rows"][0]["status"] == "complete"


def test_tokens_cannot_cross_workflows_and_cancel_invalidates_restore(tmp_path: Path) -> None:
    """A policy confirmation must never authorize restoration through another endpoint."""
    executor = ManualExecutor()
    manager = JobManager(tmp_path, executor)
    identifier = manager.start("owner", "restore", preparation)
    executor.run()
    token = manager.status(identifier, "owner")["token"]
    with pytest.raises(PolicyError, match="different workflow"):
        manager.apply("owner", token, lambda _: preparation, "policy")
    manager.cancel("owner", token)
    assert manager.status(identifier, "owner")["state"] == "interrupted"
    with pytest.raises(PolicyError, match="unavailable"):
        manager.apply("owner", token, lambda _: preparation, "restore")


def test_restart_interrupts_queued_ready_and_applying_without_replay(tmp_path: Path) -> None:
    """Lose executable plans on restart while retaining explicit private durable status."""
    executor = ManualExecutor()
    manager = JobManager(tmp_path, executor)
    ready = manager.start("owner", "policy", preparation)
    executor.run()
    applying = manager.start("owner", "policy", preparation)
    executor.run()
    token = manager.status(applying, "owner")["token"]
    manager.apply("owner", token, lambda _: preparation, "policy")
    queued = manager.start("owner", "policy", preparation)
    replacement_executor = ManualExecutor()
    replacement = JobManager(tmp_path, replacement_executor)
    for identifier in (ready, applying, queued):
        status = replacement.status(identifier, "owner")
        assert status["state"] == "interrupted"
        assert "token" not in status
        assert "restarted" in status["error"]
    assert replacement_executor.calls == []


@pytest.mark.parametrize("error", [PolicyError("private-job-fixture"), RuntimeError("private-job-fixture")])
def test_failed_backup_and_unexpected_errors_expose_no_secret(tmp_path: Path, caplog: Any, error: Exception) -> None:
    """No failed preparation can produce a confirmation token or private exception text."""

    def failed(progress: Any) -> tuple[Any, dict[str, Any]]:
        """Simulate a failed durable backup before any application."""
        raise error  # The boundary must sanitize checked and unexpected failures.

    executor = ManualExecutor()
    manager = JobManager(tmp_path, executor)
    identifier = manager.start("owner", "policy", failed)
    executor.run()
    status = manager.status(identifier, "owner")
    assert status["state"] == "failed"
    assert "token" not in status
    assert "private-job-fixture" not in json.dumps(status)
    assert "private-job-fixture" not in caplog.text


def test_executor_capacity_is_bounded_and_terminal_outcome_survives_restart(tmp_path: Path) -> None:
    """Refuse an unbounded queue while preserving durable completed results."""
    executor = ManualExecutor()
    manager = JobManager(tmp_path, executor)
    identifiers = [manager.start("owner", "policy", preparation) for _ in range(16)]
    with pytest.raises(PolicyError, match="job limit"):
        manager.start("owner", "policy", preparation)
    executor.run()
    token = manager.status(identifiers[0], "owner")["token"]
    manager.apply("owner", token, lambda _: lambda progress: (None, {"result": {"sites": ["site"]}}), "policy")
    while executor.calls:
        executor.run()
    recovered = JobManager(tmp_path, ManualExecutor())
    assert recovered.status(identifiers[0], "owner")["state"] == "complete"
    assert recovered.status(identifiers[0], "owner")["result"] == {"sites": ["site"]}


def test_parallel_confirmation_consumes_only_once(tmp_path: Path) -> None:
    """Two request threads cannot both authorize the same prepared settings write."""
    executor = ManualExecutor()
    manager = JobManager(tmp_path, executor)
    identifier = manager.start("owner", "policy", preparation)
    executor.run()
    token = manager.status(identifier, "owner")["token"]
    barrier = threading.Barrier(2)
    accepted: list[str] = []
    rejected: list[str] = []

    def confirm() -> None:
        """Race two exact confirmations at the shared token boundary."""
        barrier.wait()  # Both requests reach consumption at the same point.
        try:
            accepted.append(manager.apply("owner", token, lambda _: preparation, "policy"))
        except PolicyError:
            rejected.append("refused")  # Only the second consumption can fail here.

    threads = [threading.Thread(target=confirm) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert accepted == [identifier]
    assert rejected == ["refused"]
    assert len(executor.calls) == 1


def test_real_worker_keeps_long_wait_pollable_without_request_context(tmp_path: Path) -> None:
    """Keep background admission visible while another request polls its owned state."""
    entered = threading.Event()
    release = threading.Event()
    manager = JobManager(tmp_path)

    def blocked(progress: Any) -> tuple[Any, dict[str, Any]]:
        """Use an explicit gate instead of a wall-clock delay."""
        progress({"phase": "waiting", "wait_seconds": 1201})  # A valid long wait must not invalidate preparation.
        entered.set()  # Poll only after the worker has persisted its current admission wait.
        if not release.wait(timeout=5):
            raise PolicyError("The test worker did not receive its release.")
        return preparation(progress)  # The verified proof remains process-owned.

    try:
        identifier = manager.start("owner", "policy", blocked)
        assert entered.wait(timeout=5), "The bounded executor did not start the worker."
        status = manager.status(identifier, "owner")
        assert status["state"] == "preparing"
        assert status["progress"]["wait_seconds"] == 1201
        assert "token" not in status
    finally:
        release.set()  # Stop only this test-owned worker.
        manager.executor.shutdown(wait=True)  # No helper thread remains after the test.
    assert manager.status(identifier, "owner")["state"] == "ready"


def test_status_files_cannot_bypass_owner_checks_through_data_downloads(tmp_path: Path) -> None:
    """Keep both main status and small progress files beneath the existing private download guard."""
    executor = ManualExecutor()
    manager = JobManager(tmp_path, executor)
    identifier = manager.start("owner", "policy", preparation)
    executor.run()
    browser = DataBrowserService(str(tmp_path))
    path = manager.files.directory / f"{identifier}.json"
    assert path.exists()
    assert browser.resolve_safe_path(str(path.relative_to(tmp_path))) is None
    progress = manager.files.directory / f"{identifier}.progress"
    assert progress.exists()
    assert browser.resolve_safe_path(str(progress.relative_to(tmp_path))) is None


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode and link checks use native filesystem semantics.")
def test_private_storage_rejects_shared_files_and_links(tmp_path: Path) -> None:
    """Do not widen access or accept status files through alternate filesystem links."""
    files = JobFiles(tmp_path)
    record = {"job_id": "one", "owner": "digest", "state": "complete"}
    files.save(record)
    path = files.directory / "one.json"
    path.chmod(0o644)
    with pytest.raises(PolicyError, match="another account"):
        files.read_all()
    path.chmod(0o600)
    link = files.directory / "two.json"
    link.symlink_to(path)
    with pytest.raises(PolicyError, match="regular file"):
        files.read_all()

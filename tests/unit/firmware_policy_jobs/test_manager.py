"""Prove bounded execution, private persistence, and fail-closed token ownership."""

from __future__ import annotations

import json
import multiprocessing
import os
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from src.operations.execution.firmware_policy.sdk import PolicyError
from web_portal.routes.firmware_policy.jobs.manager import JobManager
from web_portal.routes.firmware_policy.jobs.ownership import WorkerOwner
from web_portal.routes.firmware_policy.jobs.ownership.targets import TargetWrites
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


@pytest.fixture(autouse=True)
def private_worker_cleanup(monkeypatch: Any) -> Any:
    """Stop every test-owned local route without changing production worker lifetime."""
    owners: list[WorkerOwner] = []
    original = WorkerOwner.__init__

    def track(self: WorkerOwner, *arguments: Any, **keywords: Any) -> None:
        """Record routes created by this test for exact cleanup."""
        original(self, *arguments, **keywords)
        owners.append(self)

    monkeypatch.setattr(WorkerOwner, "__init__", track)
    yield
    for owner in owners:
        owner.close()  # Remove only this test's loopback service and release its native lease.


class ProcessWorkflow:
    """Provide a counted fixture apply operation in another native worker process."""

    def __init__(self, path: Path) -> None:
        """Retain no production credentials or external transport."""
        self.path = path
        self.api = SimpleNamespace(progress=None)
        self.api.session = SimpleNamespace(get_cloud=lambda: "api.mist.com")
        self.backup = SimpleNamespace(root=path.parent / ".firmware-policy-backups")
        self.progress: Any = None

    def apply(self, plans: Any, proof: Any) -> Any:
        """Record each application so cross-worker replay becomes a measurable failure."""
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write("write\n")  # This test-owned file represents one confirmed settings request.
        return SimpleNamespace(organizations=["org"], sites=[], unchanged=[], failures=[], remaining=[])


def process_owner(path: Path, pipe: Any, kind: str = "policy") -> None:
    """Own a verified private plan until the parent requests process shutdown."""
    manager = JobManager(path)

    def prepare(progress: Any) -> tuple[Any, dict[str, Any]]:
        """Bind fixture settings to a proof retained only by the child process."""
        return (ProcessWorkflow(path / "writes.txt"), [], object()), {"rows": [], "preview": {}}

    try:
        identifier = manager.start("owner", kind, prepare)
        manager.executor.shutdown(wait=True)  # Finish preparation before advertising the fixture job.
        from concurrent.futures import ThreadPoolExecutor

        manager.executor = ThreadPoolExecutor(max_workers=1)  # Apply remains available to authenticated relays.
        pipe.send(identifier)
        pipe.recv()  # Keep the real worker lease alive while another process polls and applies.
    finally:
        manager.close()  # Native ownership disappears only after all confirmed work completes.
        pipe.close()


def test_native_workers_route_poll_and_apply_without_false_interruption(tmp_path: Path) -> None:
    """A second process must reach the owning private plan rather than interrupting or replaying it."""
    context = multiprocessing.get_context("spawn")
    manager = JobManager(tmp_path, ManualExecutor())  # An existing worker must discover jobs admitted later.
    parent_pipe, child_pipe = context.Pipe()
    process = context.Process(target=process_owner, args=(tmp_path, child_pipe))
    process.start()
    try:
        assert parent_pipe.poll(10), "The owning process did not finish fixture preparation."
        identifier = parent_pipe.recv()
        ready = manager.status(identifier, "owner")
        assert ready["state"] == "ready"
        assert "worker" not in ready
        token = ready["token"]
        from web_portal.routes.firmware_policy.jobs.workflows import JobWorkflows

        assert manager.apply("owner", token, JobWorkflows.apply, "policy") == identifier
        with pytest.raises(PolicyError):
            manager.apply("owner", token, JobWorkflows.apply, "policy")
        manager.files.read(identifier)  # Verify the shared durable status remains readable after relayed apply.
        complete = manager.status(identifier, "owner")
        assert complete["state"] in {"applying", "complete"}
        parent_pipe.send("stop")  # Ask only the test-owned process to stop gracefully.
        process.join(timeout=10)
        assert process.exitcode == 0
        assert manager.status(identifier, "owner")["state"] == "complete"
        assert (tmp_path / "writes.txt").read_text() == "write\n"
    finally:
        if process.is_alive():
            process.terminate()  # Stop only this exact fixture process after a failed assertion.
            process.join(timeout=10)
        parent_pipe.close()


def test_native_workers_route_cancellation_to_the_plan_owner(tmp_path: Path) -> None:
    """Invalidate a restoration token on its live owner without dispatching any write."""
    context = multiprocessing.get_context("spawn")
    parent_pipe, child_pipe = context.Pipe()
    process = context.Process(target=process_owner, args=(tmp_path, child_pipe, "restore"))
    process.start()
    try:
        assert parent_pipe.poll(10), "The fixture restoration owner did not become ready."
        identifier = parent_pipe.recv()
        manager = JobManager(tmp_path, ManualExecutor())
        ready = manager.status(identifier, "owner")
        manager.cancel("owner", ready["token"])
        assert manager.status(identifier, "owner")["state"] == "interrupted"
        with pytest.raises(PolicyError):
            manager.cancel("owner", ready["token"])
        parent_pipe.send("stop")
        process.join(timeout=10)
        assert process.exitcode == 0
        assert not (tmp_path / "writes.txt").exists()
    finally:
        if process.is_alive():
            process.terminate()  # Stop only the fixture process after an assertion failure.
            process.join(timeout=10)
        parent_pipe.close()


def test_native_workers_cancel_and_owner_death_never_replay(tmp_path: Path) -> None:
    """Relay cancellation to a live owner and explicitly interrupt a lost ready plan."""
    context = multiprocessing.get_context("spawn")
    parent_pipe, child_pipe = context.Pipe()
    process = context.Process(target=process_owner, args=(tmp_path, child_pipe, "restore"))
    process.start()
    try:
        assert parent_pipe.poll(10), "The fixture owner did not become ready."
        identifier = parent_pipe.recv()
        manager = JobManager(tmp_path, ManualExecutor())
        token = manager.status(identifier, "owner")["token"]
        with pytest.raises(PolicyError):
            manager.status(identifier, "foreign")
        with pytest.raises(PolicyError):
            manager.cancel("foreign", token)
        assert manager.status(identifier, "owner")["state"] == "ready"
        process.terminate()  # Simulate a lost Gunicorn worker, not a voluntary cancellation.
        process.join(timeout=10)
        assert manager.status(identifier, "owner")["state"] == "interrupted"
        assert "token" not in manager.status(identifier, "owner")
        with pytest.raises(PolicyError):
            manager.cancel("owner", token)
        assert not (tmp_path / "writes.txt").exists()
    finally:
        if process.is_alive():
            process.terminate()  # Stop only the fixture process if an assertion fails.
            process.join(timeout=10)
        parent_pipe.close()


def process_writer_lock(path: Path, pipe: Any) -> None:
    """Retain organization ownership in an independent native worker process."""
    with TargetWrites.hold(path, "api.mist.com", {"org"}):
        pipe.send("held")
        pipe.recv()  # Keep the writer active until the test releases its exact process.
    pipe.close()


def test_shared_writer_lock_refuses_overlap_and_releases_after_process_exit(tmp_path: Path) -> None:
    """Prevent policy and restoration writers from overlapping across workers or browser owners."""
    context = multiprocessing.get_context("spawn")
    parent_pipe, child_pipe = context.Pipe()
    process = context.Process(target=process_writer_lock, args=(tmp_path, child_pipe))
    process.start()
    try:
        assert parent_pipe.poll(10), "The competing writer did not acquire organization ownership."
        assert parent_pipe.recv() == "held"
        with pytest.raises(PolicyError, match="another active settings writer"):
            with TargetWrites.hold(tmp_path, "api.mist.com", {"org"}):
                pytest.fail("A conflicting writer entered the settings mutation boundary.")
        with TargetWrites.hold(tmp_path, "api.mist.com", {"different"}):
            assert process.is_alive()  # Unrelated organizations retain independent writer capacity.
        with TargetWrites.hold(tmp_path, "api.eu.mist.com", {"org"}):
            assert process.is_alive()  # The cloud identity separates otherwise equal identifiers.
        parent_pipe.send("stop")
        process.join(timeout=10)
        assert process.exitcode == 0
        with TargetWrites.hold(tmp_path, "api.mist.com", {"org"}):
            assert not process.is_alive()  # Native ownership releases after the previous writer finishes.
    finally:
        if process.is_alive():
            process.terminate()  # Stop only this exact test-owned writer.
            process.join(timeout=10)
        parent_pipe.close()


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
    manager.close()  # Simulate process loss and release the native ownership lease.
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


def test_action_factory_failure_records_safe_context_and_releases_capacity(tmp_path: Path, caplog: Any) -> None:
    """Report failed apply construction without leaking private exception values or consuming the token."""
    executor = ManualExecutor()
    manager = JobManager(tmp_path, executor)
    identifier = manager.start("owner", "policy", preparation)
    executor.run()
    token = manager.status(identifier, "owner")["token"]

    def rejected(context: Any) -> Any:
        """Reject construction before the manager consumes the single-use proof."""
        raise RuntimeError("private-job-fixture")  # The diagnostic boundary must record type and job identity only.

    with pytest.raises(PolicyError, match="could not start"):
        manager.apply("owner", token, rejected, "policy")
    assert identifier in caplog.text
    assert "RuntimeError" in caplog.text
    assert "private-job-fixture" not in caplog.text
    assert manager.status(identifier, "owner")["token"] == token
    assert executor.calls == []


def test_executor_dispatch_failure_records_safe_context_without_replay(
    tmp_path: Path, caplog: Any, monkeypatch: Any
) -> None:
    """Record executor admission failure without leaking an exception or admitting uncertain work."""
    executor = ManualExecutor()
    manager = JobManager(tmp_path, executor)

    def rejected(*arguments: Any, **keywords: Any) -> None:
        """Simulate an executor that refuses worker dispatch."""
        raise RuntimeError("private-job-fixture")  # Only the exception type may enter diagnostic output.

    monkeypatch.setattr(executor, "submit", rejected)  # Restore fixture admission after this failure test.
    with pytest.raises(PolicyError, match="could not start"):
        manager.start("owner", "policy", preparation)
    assert "RuntimeError" in caplog.text
    assert "dispatch stopped" in caplog.text
    assert "private-job-fixture" not in caplog.text
    assert executor.calls == []
    assert all(entry.record["state"] == "failed" for entry in manager.entries.values())


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
    manager.close()  # A closed worker retains terminal outcomes but loses executable ready plans.
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


def test_status_storage_empty_body_fails_without_worker_submission(tmp_path: Path) -> None:
    """Reject an empty persisted status rather than treating an interrupted operation as absent."""
    executor = ManualExecutor()
    manager = JobManager(tmp_path, executor)
    identifier = manager.start("owner", "policy", preparation)
    executor.run()
    path = manager.files.directory / f"{identifier}.json"
    with path.open("wb") as stream:
        stream.write(b"")  # Simulate an empty durable input without changing its private access.
    replacement_executor = ManualExecutor()
    with pytest.raises(json.JSONDecodeError, match="Expecting value"):
        JobManager(tmp_path, replacement_executor)
    assert path.read_text(encoding="utf-8") == ""
    assert replacement_executor.calls == []  # Failed recovery cannot dispatch any cloud action.
    assert executor.calls == []  # No application was submitted before storage corruption.


def test_status_storage_malformed_json_fails_without_worker_submission(tmp_path: Path) -> None:
    """Reject invalid persisted JSON without repairing the record or replaying private settings."""
    executor = ManualExecutor()
    manager = JobManager(tmp_path, executor)
    identifier = manager.start("owner", "policy", preparation)
    executor.run()
    path = manager.files.directory / f"{identifier}.json"
    with path.open("w", encoding="utf-8") as stream:
        stream.write('{"state": "ready",')  # Simulate an incomplete durable JSON document.
    replacement_executor = ManualExecutor()
    with pytest.raises(json.JSONDecodeError):
        JobManager(tmp_path, replacement_executor)
    assert path.read_text(encoding="utf-8") == '{"state": "ready",'
    assert replacement_executor.calls == []  # Malformed status cannot authorize a worker.
    assert executor.calls == []  # The private proof remained unconsumed before corruption.


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

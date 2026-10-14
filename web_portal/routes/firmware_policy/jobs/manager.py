"""Run bounded jobs without retaining Flask request contexts or replaying writes."""

from __future__ import annotations

import logging
import secrets
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.operations.execution.firmware_policy.sdk import PolicyError

from .state import JobEntry, JobErrors, JobState
from .storage import JobFiles

logger = logging.getLogger(__name__)
Progress = Callable[[dict[str, Any]], None]
Work = Callable[[Progress], tuple[Any, dict[str, Any]]]


class JobManager:
    """Keep active plans until explicit consumption while bounding admitted work."""

    def __init__(self, data_dir: Path, executor: Any = None) -> None:
        """Recover status only and explicitly interrupt every lost private plan."""
        self.files = JobFiles(data_dir)  # Verify private storage before accepting work.
        self.lock = threading.RLock()  # Serialize token consumption with status changes.
        self.slots = threading.BoundedSemaphore(16)  # Bound running and queued requests.
        self.executor = executor or ThreadPoolExecutor(max_workers=2, thread_name_prefix="firmware-jobs")
        self.entries: dict[str, JobEntry] = {}  # Complete settings exist only in live contexts.
        for record in self.files.read_all():
            if record["state"] in {"queued", "preparing", "ready", "applying"}:
                record.update(
                    state="interrupted",
                    error="The worker restarted. Prepare a new operation.",
                    updated_at=datetime.now(UTC).isoformat(),
                )  # A lost private plan cannot authorize an automatic write replay.
                self.files.save(record)  # Never recover a token or automatically repeat a write.
            self.entries[record["job_id"]] = JobEntry(record)  # Terminal outcomes remain pollable.

    def start(self, owner: str, kind: str, work: Work) -> str:
        """Admit preparation only when both the executor and plan limits permit it."""
        with self.lock:
            active = sum(
                entry.record["state"] in {"queued", "preparing", "ready", "applying"} for entry in self.entries.values()
            )
            if active >= 50 or not self.slots.acquire(blocking=False):
                raise PolicyError("The job limit was reached. Wait for an operation to finish.")
            identifier = str(uuid4())  # Jobs cannot be guessed from a sequence.
            record: dict[str, Any] = dict(
                job_id=identifier,
                owner=JobState.owner(owner),
                kind=kind,
                state="queued",
                progress={},
                rows=[],
                preview=None,
                result=None,
                updated_at=datetime.now(UTC).isoformat(),
            )
            self.entries[identifier] = JobEntry(record)  # Keep full plans out of the durable record.
            self._submit(identifier, work, False)  # Submission has no request-context dependency.
            return identifier  # Both synchronous test workers and real workers share this contract.

    def status(self, identifier: str, owner: str) -> dict[str, Any]:
        """Return identical missing status for unknown jobs and foreign browsers."""
        with self.lock:
            entry = self._owned(identifier, owner)  # Verify ownership before exposing progress.
            return JobState.public(entry)  # Tokens appear only for verified ready operations.

    def apply(self, owner: str, token: str, factory: Callable[[Any], Work], kind: str) -> str:
        """Consume the proof token atomically before any apply worker can execute."""
        with self.lock:
            entry = self._token(owner, token)  # A foreign browser cannot invalidate a valid token.
            if entry.record["kind"] != kind:
                raise PolicyError("The token belongs to a different workflow.")
            if not self.slots.acquire(blocking=False):
                raise PolicyError("The job queue is full. Wait before confirmation.")
            try:
                work = factory(entry.context)  # Build the action while the verified context exists.
            except Exception:
                self.slots.release()  # A rejected action cannot leak an executor admission slot.
                raise PolicyError("The operation could not start. Prepare a new operation.") from None
            entry.token = None  # A replay fails before the executor can issue a write.
            entry.record["state"] = "applying"  # Durable interruption now represents uncertain application.
            self._submit(entry.record["job_id"], work, True)  # Use one identifier throughout the operation.
            return str(entry.record["job_id"])  # The browser polls the same owned record.

    def cancel(self, owner: str, token: str) -> None:
        """Invalidate a ready restoration without any cloud operation."""
        with self.lock:
            entry = self._token(owner, token)  # Require a matching owner and ready token.
            if entry.record["kind"] != "restore":
                raise PolicyError("Select a ready restoration token.")
            entry.token, entry.context = None, None  # Destroy the private executable plan.
            entry.record.update(
                state="interrupted",
                error="The operator cancelled the prepared operation.",
                updated_at=datetime.now(UTC).isoformat(),
            )  # Cancellation has its own durable UTC timestamp.
            self.files.save(entry.record)  # Cancellation survives restart.

    def _owned(self, identifier: str, owner: str) -> JobEntry:
        """Refuse empty ownership and another browser without disclosing existence."""
        entry = self.entries.get(identifier)  # An unknown identifier has no observable private state.
        if not owner or entry is None or entry.record["owner"] != JobState.owner(owner):
            raise PolicyError("The job is unavailable for this browser.")
        return entry  # The caller holds the shared lock.

    def _token(self, owner: str, token: str) -> JobEntry:
        """Check random single-use references without timing-sensitive equality."""
        for entry in self.entries.values():
            if entry.token and secrets.compare_digest(entry.token, token):
                owned = self._owned(entry.record["job_id"], owner)  # Do not consume foreign references.
                if owned.record["state"] == "ready":
                    return owned  # Complete backup verification precedes this state.
        raise PolicyError("The preparation token is unavailable. Prepare a new operation.")

    def _submit(self, identifier: str, work: Work, applying: bool) -> None:
        """Persist admission before dispatch and fail closed if dispatch fails."""
        try:
            self.files.save(self.entries[identifier].record)  # Make accepted work visible before dispatch.
            self.executor.submit(self._run, identifier, work, applying)  # A bounded semaphore limits the queue.
        except Exception:
            self.slots.release()  # Failed dispatch must not leak an admission slot.
            self.entries[identifier].token = None  # Never reissue an uncertain apply token.
            self.entries[identifier].record.update(
                state="failed", error="The job could not start. Prepare a new operation."
            )
            raise PolicyError("The job could not start. Prepare a new operation.") from None

    def _progress(self, identifier: str, event: dict[str, Any]) -> None:
        """Persist only the explicit progress contract under the job lock."""
        with self.lock:
            progress = JobState.progress(event)  # Strip unsupported private values.
            if progress.get("phase") == "waiting":
                previous = self.entries[identifier].record["progress"]  # Admission callbacks can omit current counts.
                for key in ("completed", "total"):
                    if key not in progress and key in previous:
                        progress[key] = previous[key]  # Preserve observed counts without inventing a total.
            self.entries[identifier].record["progress"] = progress  # Unknown totals remain absent.
            self.entries[identifier].record["updated_at"] = datetime.now(
                UTC
            ).isoformat()  # Record the actual callback time.
            self.files.progress(
                self.entries[identifier].record
            )  # Small durable updates avoid repeated large row serialization.

    def _run(self, identifier: str, work: Work, applying: bool) -> None:
        """Keep checked and unexpected failures outside public and private exception logs."""
        try:
            self._update(
                identifier, {"state": "applying" if applying else "preparing"}
            )  # Record the actual worker stage.
            context, values = work(lambda event: self._progress(identifier, event))  # No Flask proxy enters the worker.
            with self.lock:
                entry = self.entries[identifier]  # Serialize final status with polling and confirmation.
                entry.context = None if applying else context  # Release full settings after apply.
                entry.token = (
                    None if applying else secrets.token_urlsafe(32)
                )  # Publish only after every backup verifies.
                entry.record.update(values, state=values.get("state", "complete" if applying else "ready"))
                entry.record["updated_at"] = datetime.now(
                    UTC
                ).isoformat()  # Record actual completion, not admission time.
                if not applying:
                    entry.record.update(values.get("preview", {}))  # Retain original sanitized API metadata.
                else:
                    self._outcome_rows(entry)  # Compact target status follows verified completion.
                self.files.save(entry.record)  # Persist the final sanitized outcome before releasing admission.
        except Exception as error:
            logger.error(
                "Firmware job %s stopped with %s", identifier, type(error).__name__
            )  # Never log exception content.
            self._update(
                identifier, {"state": "failed", "error": JobErrors.message(error)}
            )  # Checked reasons retain HTTP status.
            with self.lock:
                self.entries[identifier].context, self.entries[identifier].token = (
                    None,
                    None,
                )  # No failed backup authorizes writes.
        finally:
            self.slots.release()  # Both checked failures and unexpected worker failures release capacity.

    def _update(self, identifier: str, values: dict[str, Any]) -> None:
        """Write one sanitized transition without exposing partial in-memory changes."""
        with self.lock:
            self.entries[identifier].record.update(values, updated_at=datetime.now(UTC).isoformat())
            self.files.save(self.entries[identifier].record)  # A restarted process reads an explicit state.

    @staticmethod
    def _outcome_rows(entry: JobEntry) -> None:
        """Map checked result identifiers to rows without exposing exception strings."""
        result = entry.record["result"]  # Workflow actions already removed private failure details.
        completed = set(result.get("completed", []) + result.get("organizations", []) + result.get("sites", []))
        unchanged = set(result.get("unchanged", []))  # An inherited policy can require no settings write.
        failed = set(result.get("failed", []))  # Restore failures contain only scoped identifiers.
        rows = []  # Replace the list atomically so polling sees one coherent outcome.
        for original in entry.record["rows"]:
            row = dict(original)  # Never mutate a response already being serialized.
            keys = {row["id"], f"{row['scope']}:{row['id']}"}  # Support both domain result identifier formats.
            row["status"] = (
                "complete"
                if keys & completed
                else "unchanged" if keys & unchanged else "failed" if keys & failed else "remaining"
            )
            rows.append(row)  # No settings or diagnostic data enters the compact status table.
        entry.record["rows"] = rows  # Retain name ordering from preparation.

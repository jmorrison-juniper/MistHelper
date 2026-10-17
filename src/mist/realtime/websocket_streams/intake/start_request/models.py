"""Immutable models for checked WebSocket start requests."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import threading  # Progress updates cross runner and web request threads.
from collections.abc import (
    Callable,  # Device lookup and progress share structural types.
    Mapping,  # Checked targets and parameters remain read-only interfaces.
)
from dataclasses import dataclass, field  # Request records use frozen slot dataclasses.
from datetime import UTC, datetime  # Target outcomes use UTC ISO 8601 values.
from typing import Protocol, cast

from src.mist.realtime.websocket_streams.catalog.model import (
    ChannelDefinition,
    UtilityDefinition,
)  # Requests retain catalog entries.
from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Artifact failures use the stable output contract.


@dataclass(frozen=True, slots=True)
class StartRequest:
    """Hold one request after every intake check passes."""

    kind: str  # The runner type is channel, utility, or shell.
    definition: ChannelDefinition | UtilityDefinition  # The selected catalog entry drives execution.
    targets: Mapping[str, tuple[str, ...]]  # Every target contains checked UUID values.
    parameters: Mapping[str, object]  # Every parameter contains a checked JSON-safe value.
    title: str  # The bounded session title uses safe labels.
    confirmation: str | None = None  # Change and shell requests retain the checked device name.
    device_name: str | None = None  # Audit records use the Mist device name.
    batch_plan: BatchExecutionPlan | None = None  # One parent request may own a frozen batch plan.
    source_by_path: Mapping[str, str] | None = None  # Batch channels map private paths to target keys.

    @property
    def key(self) -> str:
        """Return the selected catalog key."""
        return self.definition.key  # The immutable definition owns the key.

    def target(self, name: str) -> str:
        """Return the first checked target value."""
        values = self.targets.get(name, ())  # An absent target has no values.
        return values[0] if values else ""  # Existing runners treat empty text as absent.


@dataclass(frozen=True, slots=True)
class DeviceFacts:
    """Hold the device facts required by utility intake checks."""

    name: str  # Typed confirmation must match this Mist device name.
    family: str | None  # Utility selection must match this device family.
    mac: str | None = None  # Client discovery needs the validated device MAC.


class DeviceDirectory(Protocol):
    """Describe one device for start request validation."""

    def describe_device(self, site_id: str, device_id: str) -> DeviceFacts | None:
        """Return the selected device facts or None."""


@dataclass(frozen=True, slots=True)
class BatchTargetRequest:
    """Hold one frozen target identity and its checked operation request."""

    target_key: str  # The canonical natural key remains stable for all progress updates.
    identity: Mapping[str, object]  # The public identity excludes labels and command text.
    request: StartRequest  # Each utility or shell target has a fully checked request.


@dataclass(slots=True)
class BatchExecutionPlan:
    """Hold one preview-bound plan and its mutable target outcomes."""

    targets: tuple[BatchTargetRequest, ...]  # The server fixes target order at preview time.
    concurrency: int  # The effective bounded target concurrency.
    commands: tuple[str, ...] = ()  # Shell command order stays exact and private.
    output: Mapping[str, object] | None = None  # The server validates the selected artifact layout.
    artifact_id: str | None = None  # One server-generated directory owns this batch output.
    artifact_writer: Callable[[str, Mapping[str, object], str, object, str | None], None] | None = field(
        default=None, repr=False, compare=False
    )  # Persist redacted results without exposing storage paths to the browser.
    artifact_finisher: Callable[[list[dict[str, object]]], None] | None = field(
        default=None, repr=False, compare=False
    )  # Finalize the manifest after every target stops.
    progress: BatchExecutionPlan._Progress = field(init=False, repr=False)  # One owner groups bounded target state.

    def __post_init__(self) -> None:
        """Create one progress owner for the immutable target plan."""
        self.progress = self._Progress(
            self.targets,
            self.concurrency,
            self.artifact_id,
            self.artifact_writer,
            self.artifact_finisher,
        )  # Keep mutable lifecycle state out of the immutable request data.

    class _Progress:
        """Group target transitions, cancellation, summaries, and artifact state."""

        def __init__(
            self,
            targets: tuple[BatchTargetRequest, ...],
            concurrency: int,
            artifact_id: str | None,
            writer: Callable[[str, Mapping[str, object], str, object, str | None], None] | None,
            finisher: Callable[[list[dict[str, object]]], None] | None,
        ) -> None:
            """Build the four independent progress owners."""
            self.transitions = self._Transitions(targets)  # Keep target state changes atomic.
            self.cancellation = self._Cancellation(self.transitions)  # Share the target lock for queued stops.
            self.artifacts = self._Artifacts(artifact_id, writer, finisher, self.transitions)  # Own saved output state.
            self.summary = self._Summary(self.transitions, self.artifacts, concurrency)  # Read one consistent snapshot.

        class _Transitions:
            """Own target state and result-count changes."""

            def __init__(self, targets: tuple[BatchTargetRequest, ...]) -> None:
                """Create a stable outcome row for each frozen target."""
                self.lock = threading.RLock()  # Serialize runner and polling thread updates.
                self.rows = [
                    {
                        "target_key": target.target_key,
                        "target": dict(target.identity),
                        "state": "queued",
                        "started_at": None,
                        "ended_at": None,
                        "reason_code": None,
                        "result_count": 0,
                        "command_index": None,
                        "completion": None,
                    }
                    for target in targets
                ]  # Preserve exact preview order and every field required by polling.

            def transition(
                self, target_key: str, state: str, reason_code: str | None = None, completion: str | None = None
            ) -> bool:
                """Apply one legal state change and preserve the first terminal result."""
                if state not in {"running", "completed", "stopped", "failed"}:
                    return False  # Refuse unrecognized internal states.
                with self.lock:  # Keep concurrent target callbacks atomic.
                    target = next(
                        (item for item in self.rows if item["target_key"] == target_key), None
                    )  # Find only the checked natural-key row.
                    if target is None or target["state"] not in {"queued", "running"}:
                        return False  # Do not rewrite a missing or terminal target.
                    if state == "running" and target["state"] != "queued":
                        return False  # A running target can start only once.
                    target["state"] = state  # Record one accepted lifecycle state.
                    target["reason_code"] = reason_code  # Keep only stable reason codes.
                    target["completion"] = completion  # Separate result proof from lifecycle state.
                    target["started_at" if state == "running" else "ended_at"] = self._timestamp()  # Mark transition.
                    return True  # Tell the caller whether it owns this final update.

            def record_result(self, target_key: str, command_index: int | None = None) -> None:
                """Count one accepted output and retain a supplied command index."""
                with self.lock:  # Serialize counts with terminal transitions.
                    target = next(
                        (item for item in self.rows if item["target_key"] == target_key), None
                    )  # Resolve the frozen target only.
                    if target is not None:
                        target["result_count"] = cast(int, target["result_count"]) + 1  # Count accepted output.
                        if command_index is not None:
                            target["command_index"] = command_index  # Preserve an explicit shell command index.

            def set_command_index(self, target_key: str, command_index: int) -> None:
                """Record the zero-based finite shell command index."""
                with self.lock:  # Update the index with other target state.
                    target = next(
                        (item for item in self.rows if item["target_key"] == target_key), None
                    )  # Resolve the frozen target only.
                    if target is not None and target["state"] == "running":
                        target["command_index"] = command_index  # Do not update a queued or terminal target.

            @staticmethod
            def _timestamp() -> str:
                """Return one UTC timestamp in ISO 8601 form."""
                return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        class _Cancellation:
            """Own cancellation state and queued-target transitions."""

            def __init__(self, transitions: BatchExecutionPlan._Progress._Transitions) -> None:
                """Use the outcome lock for a consistent cancellation snapshot."""
                self._transitions = transitions  # Queued stops share the target transition lock.
                self._requested = False  # No operator has stopped the parent.

            def is_cancelled(self) -> bool:
                """Return whether the operator closed further target dispatch."""
                with self._transitions.lock:  # Read cancellation with the queued target snapshot.
                    return self._requested  # Keep this state monotonic.

            def cancel_queued(self) -> None:
                """Stop every queued target before the scheduler dispatches again."""
                with self._transitions.lock:  # Make cancellation and queued stops one boundary.
                    self._requested = True  # Prevent later target admission.
                    for target in self._transitions.rows:
                        if target["state"] == "queued":
                            target["state"] = "stopped"  # Stop targets not yet dispatched.
                            target["ended_at"] = self._transitions._timestamp()  # Timestamp the stop result.
                            target["reason_code"] = "cancelled"  # Keep the stable reason code.
                            target["completion"] = "cancelled"  # Keep completion evidence separate.

        class _Artifacts:
            """Own artifact callbacks and their public status."""

            def __init__(
                self,
                artifact_id: str | None,
                writer: Callable[[str, Mapping[str, object], str, object, str | None], None] | None,
                finisher: Callable[[list[dict[str, object]]], None] | None,
                transitions: BatchExecutionPlan._Progress._Transitions,
            ) -> None:
                """Store the server-owned artifact callbacks."""
                self._artifact_id = artifact_id  # The identifier exists only for a prepared batch.
                self._writer = writer  # The callback saves redacted records under its private tree.
                self._finisher = finisher  # The callback closes the manifest after all targets stop.
                self._transitions = transitions  # The final manifest copies a locked progress snapshot.
                self.status = "writing"  # The public summary reports output readiness.

            def write_result(
                self,
                target_key: str,
                identity: Mapping[str, object],
                kind: str,
                content: object,
                summary: str | None,
            ) -> bool:
                """Persist one result or mark required output as failed."""
                if self._writer is None or self._artifact_id is None:
                    return True  # Tests without artifact storage retain prior runner behavior.
                try:
                    self._writer(target_key, identity, kind, content, summary)  # Persist only the redacted record.
                except StreamRequestError:
                    with self._transitions.lock:  # Preserve artifact state with target progress changes.
                        self.status = "failed"  # A required output failure cannot look successful.
                    return False  # Stop this target before publishing an unsaved result.
                return True  # The artifact service accepted the complete record.

            def finish(self) -> bool:
                """Write final outcomes and report manifest failures."""
                if self._finisher is None:
                    with self._transitions.lock:  # Read artifact state consistently with concurrent writers.
                        return self.status == "ready"  # No writer means no saved manifest.
                if not self._write_manifest():
                    return False  # Keep a failed manifest visible to the parent.
                return self._mark_ready()  # Report success only after all writes complete.

            def _write_manifest(self) -> bool:
                """Write a consistent target snapshot to the artifact manifest."""
                finisher = self._finisher
                if finisher is None:
                    return False  # A missing callback cannot create a saved manifest.
                try:
                    with self._transitions.lock:  # Snapshot outcomes after all target callbacks finish.
                        outcomes = [
                            cast(dict[str, object], dict(item)) for item in self._transitions.rows
                        ]  # Keep manifest records independent of mutable state.
                    finisher(outcomes)  # Write the final target manifest.
                except StreamRequestError:
                    with self._transitions.lock:  # Preserve artifact state with target progress changes.
                        self.status = "failed"  # A failed manifest keeps the parent visibly incomplete.
                    return False  # Do not report a complete artifact set.

                return True  # The manifest callback accepted the final target snapshot.

            def _mark_ready(self) -> bool:
                """Mark artifacts ready unless an earlier result write failed."""
                with self._transitions.lock:  # Retain any earlier required-write failure.
                    if self.status == "failed":
                        return False  # A successful manifest cannot hide a failed result write.
                    self.status = "ready"  # Mark output ready only after every required write succeeds.
                    return True  # The full artifact set is ready.

        class _Summary:
            """Read bounded target pages and aggregate counts."""

            def __init__(
                self,
                transitions: BatchExecutionPlan._Progress._Transitions,
                artifacts: BatchExecutionPlan._Progress._Artifacts,
                concurrency: int,
            ) -> None:
                """Store the state owners used for one public snapshot."""
                self._transitions = transitions  # Count target states under their shared lock.
                self._artifacts = artifacts  # Report the current artifact write state.
                self._concurrency = concurrency  # Keep the accepted target worker limit.

            def summary(self) -> dict[str, object]:
                """Return current target counts and aggregate batch state."""
                with self._transitions.lock:  # Keep counts aligned with one target snapshot.
                    counts = {
                        state: sum(item["state"] == state for item in self._transitions.rows)
                        for state in ("queued", "running", "completed", "stopped", "failed")
                    }  # Count every admitted target exactly once.
                    return {
                        "status": self._status(counts),  # Report the aggregate target state.
                        "target_count": len(self._transitions.rows),  # Retain the admitted target count.
                        "concurrency": self._concurrency,  # Report the enforced worker limit.
                        "counts": counts,  # Return each stable target state count.
                        "artifact_status": self._artifacts.status,  # Keep output state separate from target state.
                    }  # Preserve the public batch summary contract.

            def target_page(self, after: int, limit: int) -> dict[str, object]:
                """Return one stable target page and its current outcome counts."""
                with self._transitions.lock:  # Keep one page and its counts consistent.
                    items = self._transitions.rows[after : after + limit]
                    next_after = after + len(items)
                    summary = self.summary()
                    return {
                        "targets": [dict(item) for item in items],  # Return copies, not mutable internal rows.
                        "next_after": next_after,  # Keep the cursor stable for the frozen target order.
                        "complete": next_after >= len(self._transitions.rows),  # Mark the final page explicitly.
                        "counts": summary["counts"],  # Include current aggregate progress.
                    }  # Keep the target page response bounded.

            @staticmethod
            def _status(counts: Mapping[str, int]) -> str:
                """Return the aggregate status from current target counts."""
                if counts["queued"] or counts["running"]:
                    return "stopping" if counts["stopped"] and counts["queued"] == 0 else "running"
                if counts["completed"] == sum(counts.values()):
                    return "completed"
                if counts["failed"] == sum(counts.values()):
                    return "failed"
                return "stopped" if counts["stopped"] else "partial"  # Keep mixed terminal outcomes visible.

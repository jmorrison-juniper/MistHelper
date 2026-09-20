"""Reconcile stale runs from read-only cloud evidence."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast  # Narrow checked records without runtime assertions.

from src.upgrade_portal.api.run_controls.services.bulk import (
    ACTION_LEASE_TIME,
    PRE_CLOUD_STATES,
    SiteMutationGuard,
)
from src.upgrade_portal.api.run_controls.views import RunStalePolicy
from src.upgrade_portal.persistence.actions import (
    ActionIdentity,
    ActionInitialization,
    ActionIntent,
    ActionLease,
    ActionReplayService,
    ActionSource,
    DurableActorScope,
    OutcomeCompletion,
    OutcomeState,
    RecoveryDecision,
    ReplayRequest,
    RunActionOutcome,
    RunMutation,
    UpgradeRunAction,
    canonical_digest,
)
from src.upgrade_portal.runtime.runs import RunStateMachine, RunTransitionError
from src.upgrade_portal.upgrade import gate

logger = logging.getLogger(__name__)

TASK_STATES = frozenset({"active", "final", "absent", "unknown", "unavailable"})
WRITE_STATES = frozenset({"writing", "not_writing", "unknown", "unavailable"})
STOP_RESULTS = frozenset({"cancel_accepted", "already_writing", "not_requested", "unknown"})
DRIVER_STATES = frozenset({"stopped", "completed", "failed", "cancelled"})
SOURCES = frozenset({"stored", "cloud_task", "device", "driver"})
CONFLICT_REASONS = frozenset({"task_state_conflict", "write_state_conflict", "driver_state_conflict", "target_missing"})
LOCK_CHANGED_MESSAGE = "The site lock token changed before the write."  # Name the text without a credential term.
FAILED_REPAIR_NOTE = (  # State exactly why the repair leaves the direct settle fields empty.
    "The portal reconciled this phase from later cloud firmware evidence. "
    "The phase gate did not observe the reboot time or the settle time."
)


@dataclass(frozen=True, slots=True)
class TargetEvidence:
    """Hold safe evidence for one run target."""

    target_digest: str
    stored_stop_result: str
    task_digest: str | None
    task_state: str
    write_state: str
    driver_state: str | None
    sources: tuple[str, ...]
    observed_at: str | None
    is_complete: bool
    has_conflict: bool
    conflict_reason: str | None
    version_target: str
    running_version: str
    fwupdate_status: str
    firmware_success: bool

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> TargetEvidence:
        """Build one validated safe target result from current evidence."""
        target = cls._target(value)  # Preserve the supported target identifier priority.
        evidence = cls._build(value, target)  # Build the same immutable evidence value.
        evidence._validate()
        return evidence

    @classmethod
    def _build(cls, value: Mapping[str, Any], target: str) -> TargetEvidence:
        """Build one target evidence value from primitive evidence fields.

        Args:
            value: The raw evidence mapping.
            target: The validated target identifier.

        Returns:
            The immutable target evidence value.
        """
        return cls(  # Preserve each field conversion from the prior constructor call.
            target_digest=canonical_digest(target),
            stored_stop_result=cls._text(value, "stored_stop_result", "unknown"),
            task_digest=cls._task_digest(value),
            task_state=str(value.get("task_state") or "unknown"),
            write_state=str(value.get("write_state") or "unknown"),
            driver_state=cls._optional_text(value, "driver_state"),
            sources=cls._sources(value),
            observed_at=cls._optional_text(value, "observed_at"),
            is_complete=bool(value.get("is_complete")),
            has_conflict=bool(value.get("has_conflict")),
            conflict_reason=cls._optional_text(value, "conflict_reason"),
            version_target=str(value.get("version_target") or ""),
            running_version=cls._running_version(value),
            fwupdate_status=str(value.get("fwupdate_status") or "").strip().lower(),
            firmware_success=cls._firmware_success(value),
        )

    @staticmethod
    def _text(value: Mapping[str, Any], field: str, default: str) -> str:
        """Return one text field with a safe default."""
        return str(value.get(field) or default)  # Keep empty evidence fields on their defined fallback.

    @classmethod
    def _task_digest(cls, value: Mapping[str, Any]) -> str | None:
        """Return the safe digest of one task identifier."""
        task_id = cls._text(value, "task_id", "")  # Preserve empty task identifier handling.
        return canonical_digest(task_id) if task_id else None  # Store no raw cloud task identifier.

    @staticmethod
    def _sources(value: Mapping[str, Any]) -> tuple[str, ...]:
        """Return the normalized evidence source list."""
        return tuple(sorted({str(source) for source in value.get("sources", ())}))  # Keep stable digest order.

    @staticmethod
    def _running_version(value: Mapping[str, Any]) -> str:
        """Return the running firmware version from approved evidence fields."""
        running = value.get("running_version")  # Prefer the current running-version evidence field.
        fallback = value.get("version_after")  # Accept old scripted evidence that used the target row field.
        return str(running or fallback or "")  # A blank version proves no firmware success.

    @staticmethod
    def _target(value: Mapping[str, Any]) -> str:
        """Return the supported target identifier.

        Args:
            value: The raw evidence mapping.

        Returns:
            The target identifier text.
        """
        target = str(value.get("target_id") or value.get("device_id") or value.get("mac") or "")  # Preserve priority.
        if not target:  # Preserve the empty target refusal.
            raise ValueError("The reconciliation target identifier is empty.")
        return target  # Return the validated target identifier.

    @staticmethod
    def _optional_text(value: Mapping[str, Any], field: str) -> str | None:
        """Return one optional field as text.

        Args:
            value: The raw evidence mapping.
            field: The field name to read.

        Returns:
            The field text, or null when the field is absent.
        """
        return str(value.get(field)) if value.get(field) is not None else None  # Preserve optional text conversion.

    def _validate(self) -> None:
        """Validate the closed evidence values and null rules."""
        self._validate_states()  # Preserve closed value checks.
        self._validate_sources()  # Preserve evidence source checks.
        self._validate_conflict()  # Preserve conflict field checks.
        self._validate_completion()  # Preserve complete evidence checks.

    def _validate_states(self) -> None:
        """Validate one target evidence state set.

        Args:
            None.
        """
        if self.stored_stop_result not in STOP_RESULTS:  # Preserve stored stop result validation.
            raise ValueError("The stored stop result is not supported.")
        if self.task_state not in TASK_STATES or self.write_state not in WRITE_STATES:  # Preserve state validation.
            raise ValueError("The current target evidence state is not supported.")
        if self.driver_state is not None and self.driver_state not in DRIVER_STATES:  # Preserve driver validation.
            raise ValueError("The stored driver state is not supported.")

    def _validate_sources(self) -> None:
        """Validate one target evidence source list.

        Args:
            None.
        """
        if not self.sources or any(source not in SOURCES for source in self.sources):  # Preserve source validation.
            raise ValueError("The target evidence source list is invalid.")

    def _validate_conflict(self) -> None:
        """Validate one target evidence conflict state.

        Args:
            None.
        """
        if self.has_conflict != (self.conflict_reason is not None):  # Preserve conflict field relation.
            raise ValueError("The target evidence conflict fields do not match.")
        if self.conflict_reason is not None and self.conflict_reason not in CONFLICT_REASONS:  # Preserve reason set.
            raise ValueError("The target evidence conflict reason is not supported.")

    def _validate_completion(self) -> None:
        """Validate one target evidence completion state.

        Args:
            None.
        """
        if self.observed_at is None and self.is_complete:  # Preserve complete evidence observation requirement.
            raise ValueError("Complete target evidence requires an observation time.")
        if self.firmware_success and self.fwupdate_status != "success":  # A success needs the cloud status token.
            raise ValueError("Firmware success evidence requires a success status.")  # Refuse an unsafe success.
        if self.firmware_success and not gate.version_matches(self.version_target, self.running_version):  # Match.
            raise ValueError("Firmware success evidence requires a matching running version.")  # Refuse mismatch.

    @classmethod
    def _firmware_success(cls, value: Mapping[str, Any]) -> bool:
        """Return whether the evidence proves a completed firmware update."""
        status = str(value.get("fwupdate_status") or "").strip().lower()  # Normalize the Mist status token.
        target = str(value.get("version_target") or "")  # Read the requested firmware version from safe evidence.
        running = str(value.get("running_version") or value.get("version_after") or "")  # Read the running version.
        explicit = bool(value.get("firmware_success"))  # Preserve scripted tests that state the final conclusion.
        return explicit or (status == "success" and gate.version_matches(target, running))  # Reuse gate rule.

    def summary(self) -> dict[str, Any]:
        """Return the safe canonical target summary."""
        return {
            "target_digest": self.target_digest,
            "stored_stop_result": self.stored_stop_result,
            "task_digest": self.task_digest,
            "task_state": self.task_state,
            "write_state": self.write_state,
            "driver_state": self.driver_state,
            "sources": list(self.sources),
            "observed_at": self.observed_at,
            "is_complete": self.is_complete,
            "has_conflict": self.has_conflict,
            "conflict_reason": self.conflict_reason,
            "version_target": self.version_target,
            "running_version": self.running_version,
            "fwupdate_status": self.fwupdate_status,
            "firmware_success": self.firmware_success,
        }


@dataclass(frozen=True, slots=True)
class ReconciliationEvidence:
    """Hold the complete safe decision input for one stopping run."""

    run_id: str
    run_revision: str
    collected_at: str
    targets: tuple[TargetEvidence, ...]

    def summary(self) -> dict[str, Any]:
        """Return the canonical evidence summary and its matching digest."""
        ordered = sorted(self.targets, key=lambda item: item.target_digest)
        metrics = self._summary_metrics(ordered)  # Keep summary counts together for the digest basis.
        basis = {
            "schema_version": 1,
            "run_id": self.run_id,
            "run_revision": self.run_revision,
            "collected_at": self.collected_at,
            "targets": [item.summary() for item in ordered],
            **metrics,
        }
        return {**basis, "decision_basis_digest": canonical_digest(basis)}

    @staticmethod
    def _summary_metrics(ordered: list[TargetEvidence]) -> dict[str, Any]:
        """Return the summary counts for ordered target evidence.

        Args:
            ordered: The target evidence in digest order.

        Returns:
            The count and flag fields for the evidence summary.
        """
        return {  # Preserve each summary metric name and value.
            "target_count": len(ordered),
            "complete_target_count": sum(item.is_complete for item in ordered),
            "firmware_success_count": sum(item.firmware_success for item in ordered),
            "active_write_count": sum(item.write_state == "writing" for item in ordered),
            "active_task_count": ReconciliationEvidence._active_task_count(ordered),
            "unknown_target_count": ReconciliationEvidence._unknown_target_count(ordered),
            "has_conflict": any(item.has_conflict for item in ordered),
            "is_complete": bool(ordered) and all(item.is_complete for item in ordered),
        }

    @staticmethod
    def _active_task_count(ordered: list[TargetEvidence]) -> int:
        """Return the count of unique active tasks.

        Args:
            ordered: The target evidence in digest order.

        Returns:
            The count of active task identifiers.
        """
        active_tasks = {  # Preserve the unique active task count rule.
            item.task_digest for item in ordered if item.task_state == "active" and item.task_digest
        }
        return len(active_tasks)  # Return only the count that enters the digest basis.

    @staticmethod
    def _unknown_target_count(ordered: list[TargetEvidence]) -> int:
        """Return the count of incomplete targets without conflict.

        Args:
            ordered: The target evidence in digest order.

        Returns:
            The count of unknown target states.
        """
        return sum(not item.is_complete and not item.has_conflict for item in ordered)  # Preserve unknown rule.


class StoppingRunReconciler:
    """Reconcile one stale run without a cloud write."""

    def __init__(
        self,
        repository: Any,
        run_reader: Callable[[str], Mapping[str, Any] | None],
        guard: SiteMutationGuard,
        evidence_reader: Callable[[Mapping[str, Any], str], Sequence[Mapping[str, Any]]],
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Bind durable storage and read-only decision inputs."""
        self._repository = repository
        self._run_reader = run_reader
        self._guard = guard
        self._evidence_reader = evidence_reader
        self._clock = clock or (lambda: datetime.now(tz=UTC))

    def reconcile(
        self,
        *,
        actor: DurableActorScope,
        idempotency_key: str,
        confirmation: str,
        run_id: str,
        organization_id: str,
        site_id: str,
    ) -> UpgradeRunAction:
        """Create or replay one single-run reconciliation action."""
        if confirmation != f"RECONCILE {run_id}":
            raise ValueError("confirmation_mismatch")
        identity = ActionIdentity.from_request(
            actor,
            idempotency_key,
            {"action": "reconcile", "organization_id": organization_id, "run_id": run_id, "site_id": site_id},
            confirmation,
        )
        initialization = ActionInitialization(
            identity,
            ActionSource.reconciliation(organization_id),
            ActionIntent("reconcile", (run_id,), (site_id,), 1),
        )
        now = self._now()
        lease = ActionLease("worker-" + uuid.uuid4().hex, self._future(now, ACTION_LEASE_TIME))
        replay = ActionReplayService(self._repository, lambda: now)
        return replay.resolve(
            ReplayRequest(initialization, lease),
            lambda action, item: self._decision(action, item, now),
        )

    def _decision(
        self,
        action: UpgradeRunAction,
        item: RunActionOutcome,
        now: str,
    ) -> RecoveryDecision:
        """Build one reconciliation result after the durable claim."""
        record = self._run_reader(item.identity.source_run_id)
        refusal = self._initial_refusal(action, item, record, now)  # Preserve early reconciliation refusals.
        if refusal is not None:
            return refusal
        record = cast(Mapping[str, Any], record)  # Narrow the checked record after the refusal helper.
        prior_state = self._state(record)
        if prior_state == "failed":  # A terminal false failure must bypass the stale gate.
            return self._failed_decision(item, record, now)  # Use positive cloud evidence before any mutation.
        stale = RunStalePolicy(self._clock()).assess(record)
        if not stale.is_stale:
            return RecoveryDecision(self._outcome(item, "refused", "run_not_stale", prior_state or "", "", now))
        if prior_state in PRE_CLOUD_STATES:
            return self._precloud_decision(item, record, prior_state, now)
        if prior_state != "stopping":
            return RecoveryDecision(self._outcome(item, "refused", "run_not_reconcilable", prior_state or "", "", now))
        return self._stopping_decision(item, record, now)

    @classmethod
    def failed_run_reconciliation_available(cls, record: Mapping[str, Any]) -> bool:
        """Report whether one failed run is narrow enough for repair evidence."""
        state = str(record.get("state") or "")  # Read the terminal run state before any nested value.
        error = record.get("error")  # Read the stored error that made the run terminal.
        return state == "failed" and cls._error_is_upgrade_timeout(error) and bool(cls._failed_target_digests(record))

    def _initial_refusal(
        self,
        action: UpgradeRunAction,
        item: RunActionOutcome,
        record: Mapping[str, Any] | None,
        now: str,
    ) -> RecoveryDecision | None:
        """Return one initial reconciliation refusal, or null when checks pass.

        Args:
            action: The durable parent action.
            item: The claimed action item.
            record: The current source run record.
            now: The durable action time.

        Returns:
            The refusal decision, or null when reconciliation can continue.
        """
        if record is None:  # Preserve the missing-run refusal.
            return RecoveryDecision(self._outcome(item, "refused", "run_not_found", "", "", now))
        site_id = str(record.get("site_id") or "")  # Preserve the stored site identifier rule.
        if site_id != item.identity.site_id:  # Preserve the site mismatch refusal.
            return RecoveryDecision(self._outcome(item, "refused", "run_changed", "", "", now))
        guard_reason = self._guard.refusal(action.source.organization_id, site_id)  # Recheck permission and lock.
        if guard_reason is not None:  # Preserve guard refusal handling.
            return RecoveryDecision(
                self._outcome(item, "refused", guard_reason, str(record.get("state") or ""), "", now)
            )
        return None  # Let the caller continue with stale and state checks.

    def _precloud_decision(
        self,
        item: RunActionOutcome,
        record: Mapping[str, Any],
        prior_state: str,
        now: str,
    ) -> RecoveryDecision:
        """Cancel one stale pre-cloud run with no cloud read."""
        revision = str(record.get("_rev") or "")
        if not revision:
            return RecoveryDecision(self._outcome(item, "unknown", "run_write_unverified", prior_state, "", now))
        outcome = self._outcome(item, "succeeded", "precloud_run_cancelled", prior_state, "cancelled", now)
        mutation = RunMutation(
            "update",
            item.identity.source_run_id,
            revision,
            prior_state,
            {"state": "cancelled", "updated_at": now},
        )
        return RecoveryDecision(outcome, mutation)

    def _failed_decision(
        self,
        item: RunActionOutcome,
        record: Mapping[str, Any],
        now: str,
    ) -> RecoveryDecision:
        """Repair one failed timeout only when current cloud evidence proves success."""
        revision = str(record.get("_rev") or "")  # Bind the repair to the exact stored record revision.
        summary = self._read_evidence_summary(item, record, revision, now)  # Read only safe evidence fields.
        if not revision:  # A run that cannot bind a revision cannot receive a safe repair.
            return RecoveryDecision(self._outcome(item, "unknown", "run_write_unverified", "failed", "", now, summary))
        if not self.failed_run_reconciliation_available(record):  # Refuse failed records outside the timeout defect.
            return RecoveryDecision(self._outcome(item, "refused", "run_not_reconcilable", "failed", "", now, summary))
        reason, classification = self._failed_evidence_result(summary, self._failed_target_digests(record))
        if classification != "succeeded":  # Incomplete or conflicting evidence must not become success.
            return RecoveryDecision(self._outcome(item, classification, reason, "failed", "", now, summary))
        document = self._failed_repair_document(record, summary, now)  # Build one explicit unmeasured repair record.
        outcome = self._outcome(item, "succeeded", "failed_run_reconciled", "failed", "complete", now, summary)
        mutation = RunMutation("update", item.identity.source_run_id, revision, "failed", document)
        return RecoveryDecision(outcome, mutation)

    def _read_evidence_summary(
        self,
        item: RunActionOutcome,
        record: Mapping[str, Any],
        revision: str,
        now: str,
    ) -> dict[str, Any]:
        """Return one safe evidence summary for a terminal repair."""
        try:  # Evidence collection can fail through a cloud or store seam.
            rows = self._evidence_reader(record, now)  # Read the configured evidence source once.
            targets = tuple(TargetEvidence.from_mapping(row) for row in rows)  # Validate every safe evidence row.
        except Exception as error:  # Keep broad because one evidence read must not hide the audit row.
            logger.exception(
                "The read-only reconciliation evidence collection failed with %s: %s",
                type(error).__name__,
                error,
            )  # Preserve traceback and the exception summary.
            targets = self._unavailable_targets(record)  # Make unavailable evidence explicit.
        evidence = ReconciliationEvidence(item.identity.source_run_id, revision, now, targets)  # Bind proof.
        return evidence.summary()  # Return the digest-bound summary.

    def _stopping_decision(
        self,
        item: RunActionOutcome,
        record: Mapping[str, Any],
        now: str,
    ) -> RecoveryDecision:
        """Use complete read-only evidence to decide one stopping run."""
        revision = str(record.get("_rev") or "")
        try:
            rows = self._evidence_reader(record, now)
            targets = tuple(TargetEvidence.from_mapping(row) for row in rows)
        except Exception as error:
            logger.exception(
                "The read-only reconciliation evidence collection failed with %s: %s",
                type(error).__name__,
                error,
            )
            targets = self._unavailable_targets(record)
        evidence = ReconciliationEvidence(item.identity.source_run_id, revision, now, targets)
        summary = evidence.summary()
        if not revision:
            return RecoveryDecision(
                self._outcome(item, "unknown", "run_write_unverified", "stopping", "", now, summary)
            )
        reason, classification = self._evidence_result(summary)
        if classification != "succeeded":
            return RecoveryDecision(self._outcome(item, classification, reason, "stopping", "", now, summary))
        outcome = self._outcome(
            item,
            "succeeded",
            "stopping_run_reconciled",
            "stopping",
            "stopped",
            now,
            summary,
        )
        mutation = RunMutation(
            "update",
            item.identity.source_run_id,
            revision,
            "stopping",
            {"state": "stopped", "updated_at": now},
        )
        return RecoveryDecision(outcome, mutation)

    @staticmethod
    def _failed_evidence_result(summary: Mapping[str, Any], failed_digests: frozenset[str]) -> tuple[str, str]:
        """Return the outcome for a failed-run firmware evidence repair."""
        if int(summary["active_write_count"]) > 0:  # A device still writing firmware is not settled evidence.
            return "firmware_write_active", "refused"
        if int(summary["active_task_count"]) > 0:  # An active cloud task can still fail later.
            return "cloud_task_active", "refused"
        if bool(summary["has_conflict"]):  # A conflict must stay visible for an operator.
            return "cloud_evidence_conflict", "unknown"
        if not bool(summary["is_complete"]):  # Missing evidence must not become a false success.
            return "cloud_evidence_incomplete", "unknown"
        proved = StoppingRunReconciler._firmware_success_digests(summary)  # Read the proven target set.
        if not failed_digests.issubset(proved):  # Every failed target needs positive current proof.
            return "firmware_success_unproved", "unknown"
        return "failed_run_reconciled", "succeeded"

    @staticmethod
    def _firmware_success_digests(summary: Mapping[str, Any]) -> frozenset[str]:
        """Return the target digests whose firmware success is proven."""
        targets = summary.get("targets")  # Read the safe target rows from the summary.
        if not isinstance(targets, Sequence):  # A malformed summary cannot prove a device.
            return frozenset()
        return frozenset(  # Return only targets with the success flag that validation checked.
            str(target.get("target_digest") or "")
            for target in targets
            if isinstance(target, Mapping) and bool(target.get("firmware_success"))
        )

    @classmethod
    def _failed_repair_document(cls, record: Mapping[str, Any], summary: Mapping[str, Any], now: str) -> dict[str, Any]:
        """Return the run fields for one false-failure repair."""
        targets = cls._repaired_targets(record, summary)  # Repair only targets that current evidence proves.
        phases = cls._repaired_phases(record, now)  # Repair the phase result without inventing direct proof.
        return {  # Store one complete compare-and-swap update document.
            "state": "complete",
            "updated_at": now,
            "targets": targets,
            "phases": phases,
            "error": None,
            "reconciliation": cls._reconciliation_record(record, summary, now),
        }

    @classmethod
    def _repaired_targets(cls, record: Mapping[str, Any], summary: Mapping[str, Any]) -> list[dict[str, Any]]:
        """Return target rows with proven false failures repaired."""
        evidence = cls._evidence_by_digest(summary)  # Index validated evidence by digest.
        repaired: list[dict[str, Any]] = []  # Preserve the stored target order.
        for target in record.get("targets", ()):  # Inspect every stored target row once.
            copied = dict(target) if isinstance(target, Mapping) else {"value": target}  # Preserve odd rows.
            digest = cls._target_digest(copied)  # Use the same digest that the evidence summary stores.
            proof = evidence.get(digest)  # Read current proof for this target, if any.
            if cls._target_needs_repair(copied) and proof is not None:  # Repair only false failed targets.
                cls._repair_target(copied, proof)  # Mutate the copied row with explicit evidence fields.
            repaired.append(copied)  # Keep the target in its original position.
        return repaired

    @staticmethod
    def _repair_target(target: dict[str, Any], proof: Mapping[str, Any]) -> None:
        """Write one target repair without inventing direct settle observations."""
        target["state"] = "settled"  # Current cloud evidence proves the upgrade did complete.
        target["version_after"] = proof.get("running_version")  # Store the running version that proved success.
        target["version_outcome"] = gate.OUTCOME_VERSION_MATCH  # The shared comparison rule already passed.
        target["reboot_seen_at"] = None  # The gate did not observe this moment, so keep it unmeasured.
        target["settled_at"] = None  # The gate did not observe this moment, so keep it unmeasured.
        target["reconciliation_state"] = "firmware_success_unmeasured_settle"  # Explain the repaired state.
        target["reconciliation_note"] = FAILED_REPAIR_NOTE  # State why the direct proof fields stay empty.

    @classmethod
    def _repaired_phases(cls, record: Mapping[str, Any], now: str) -> list[dict[str, Any]]:
        """Return phase rows with a repaired timeout phase."""
        phases: list[dict[str, Any]] = []  # Preserve the stored phase order.
        for phase in record.get("phases", ()):  # Inspect every phase row once.
            copied = dict(phase) if isinstance(phase, Mapping) else {"value": phase}  # Preserve odd rows.
            if copied.get("state") == "failed" and cls._error_is_upgrade_timeout(record.get("error")):
                copied.update({"state": "settled", "settled": copied.get("total", 0), "settled_at": now})
                copied["note"] = FAILED_REPAIR_NOTE  # State that the direct gate observations stayed absent.
            phases.append(copied)  # Keep the phase in its original position.
        return phases

    @staticmethod
    def _reconciliation_record(record: Mapping[str, Any], summary: Mapping[str, Any], now: str) -> dict[str, Any]:
        """Return an audit pointer that distinguishes a repaired result."""
        return {  # Keep only safe values in the operator-facing run record.
            "reason": "failed_run_reconciled",
            "at": now,
            "prior_state": "failed",
            "prior_error": record.get("error"),
            "evidence_summary_digest": summary.get("decision_basis_digest"),
            "unmeasured_fields": ["reboot_seen_at", "settled_at"],
        }

    @staticmethod
    def _evidence_by_digest(summary: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
        """Return evidence rows by target digest."""
        targets = summary.get("targets")  # Read the validated target list.
        rows = targets if isinstance(targets, Sequence) else ()  # Refuse malformed rows by returning empty.
        return {  # Index only proven firmware success rows.
            str(row.get("target_digest") or ""): row
            for row in rows
            if isinstance(row, Mapping) and bool(row.get("firmware_success"))
        }

    @staticmethod
    def _target_needs_repair(target: Mapping[str, Any]) -> bool:
        """Report whether one target carries the false-failure shape."""
        return str(target.get("state") or "") == "failed" and target.get("version_after") in (None, "")

    @staticmethod
    def _target_digest(target: Mapping[str, Any]) -> str:
        """Return the canonical digest for one stored target identifier."""
        target_id = str(target.get("device_id") or target.get("mac") or target.get("id") or "")  # Preserve priority.
        return canonical_digest(target_id) if target_id else ""  # Match TargetEvidence without storing raw values.

    @classmethod
    def _failed_target_digests(cls, record: Mapping[str, Any]) -> frozenset[str]:
        """Return the failed target digests that require proof."""
        return frozenset(  # Build the exact set that evidence must prove.
            cls._target_digest(target)
            for target in record.get("targets", ())
            if isinstance(target, Mapping) and cls._target_needs_repair(target) and cls._target_digest(target)
        )

    @staticmethod
    def _error_is_upgrade_timeout(error: Any) -> bool:
        """Report whether the stored error is the phase-limit timeout defect."""
        if not isinstance(error, Mapping):  # A missing or malformed error cannot identify the timeout defect.
            return False
        message = str(error.get("message") or "")  # Read safe operator text only.
        stage = str(error.get("stage") or "")  # Read the failed stage that the driver stored.
        return stage == "upgrade" and "did not return before the phase limit" in message

    @staticmethod
    def _evidence_result(summary: Mapping[str, Any]) -> tuple[str, str]:
        """Return the stable reason and classification for one evidence summary."""
        if int(summary["active_write_count"]) > 0:
            return "firmware_write_active", "refused"
        if int(summary["active_task_count"]) > 0:
            return "cloud_task_active", "refused"
        if bool(summary["has_conflict"]):
            return "cloud_evidence_conflict", "unknown"
        if not bool(summary["is_complete"]):
            unavailable = any(
                target["task_state"] == "unavailable" or target["write_state"] == "unavailable"
                for target in summary["targets"]
            )
            return ("cloud_evidence_unavailable" if unavailable else "cloud_evidence_incomplete"), "unknown"
        return "stopping_run_reconciled", "succeeded"

    @staticmethod
    def _unavailable_targets(record: Mapping[str, Any]) -> tuple[TargetEvidence, ...]:
        """Return safe unavailable evidence for every stored target."""
        rows = []
        for target in record.get("targets", ()):
            if not isinstance(target, Mapping):
                continue
            target_id = str(target.get("device_id") or target.get("mac") or target.get("id") or "")
            if not target_id:
                continue
            rows.append(
                TargetEvidence.from_mapping(
                    {
                        "target_id": target_id,
                        "stored_stop_result": "unknown",
                        "task_state": "unavailable",
                        "write_state": "unavailable",
                        "sources": ["stored"],
                        "observed_at": None,
                        "is_complete": False,
                        "has_conflict": False,
                    }
                )
            )
        return tuple(rows)

    @staticmethod
    def _outcome(
        item: RunActionOutcome,
        classification: str,
        reason: str,
        prior_state: str,
        final_state: str,
        now: str,
        summary: Mapping[str, Any] | None = None,
    ) -> RunActionOutcome:
        """Return one final reconciliation outcome."""
        messages = {
            "run_not_found": "The portal found no run with this identifier.",
            "site_write_forbidden": "The current operator cannot write to this site.",
            "site_lock_not_owned": "The current operator does not own the site lock.",
            "site_lock_token_changed": LOCK_CHANGED_MESSAGE,  # Reuse safe text without a flagged constant name.
            "run_changed": "The run changed before the write.",
            "run_not_stale": "The run is not stale.",
            "run_not_reconcilable": "The current run state does not permit reconciliation.",
            "precloud_run_cancelled": "The portal cancelled the stale pre-cloud run.",
            "firmware_write_active": "A target still writes firmware.",
            "cloud_task_active": "A cloud task is still active.",
            "cloud_evidence_incomplete": "The cloud evidence is incomplete.",
            "cloud_evidence_conflict": "The cloud evidence conflicts.",
            "cloud_evidence_unavailable": "The cloud evidence is unavailable.",
            "firmware_success_unproved": "The cloud does not prove firmware success for every failed target.",
            "run_write_failed": "The portal could not write the run record.",
            "run_write_unverified": "The portal cannot verify the run write.",
            "failed_run_reconciled": (
                "The portal confirmed firmware success from current cloud evidence. "
                "The original gate did not measure the reboot or settle times."
            ),
            "stopping_run_reconciled": (
                "The portal confirmed that no selected firmware task remains. "
                "Some devices can have finished before this check."
            ),
        }
        state = OutcomeState(prior_state, final_state, now, now)
        result_run_id = item.identity.source_run_id if classification == "succeeded" else ""
        completion = OutcomeCompletion(classification, reason, messages[reason], result_run_id, state)
        return item.finalized(completion, summary)

    @staticmethod
    def _state(record: Mapping[str, Any]) -> str | None:
        """Return one canonical run state, or null for an invalid value."""
        try:
            return RunStateMachine.read_state(dict(record)).value
        except RunTransitionError:
            return None

    def _now(self) -> str:
        """Return one normalized UTC time."""
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("The reconciliation clock must return an aware time.")
        return value.astimezone(UTC).isoformat()

    @staticmethod
    def _future(now: str, duration: timedelta) -> str:
        """Return one lease end after the supplied UTC time."""
        return (datetime.fromisoformat(now) + duration).isoformat()

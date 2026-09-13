"""Process durable bulk run actions with current site guards."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from typing import Any, cast  # Narrow checked records without runtime assertions.

from src.upgrade_portal.api.run_controls.services.retry import (
    RETRYABLE_STATES,
    RetryCopyPolicy,
    RetryPolicyError,
)
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
    RetryRunMutation,
    RunActionOutcome,
    RunMutation,
    UpgradeRunAction,
    canonical_digest,
)
from src.upgrade_portal.runtime.runs import RunStateMachine, RunTransitionError

logger = logging.getLogger(__name__)

PRE_CLOUD_STATES = frozenset({"created", "pre_capture_running", "pre_capture_done", "awaiting_confirmation"})
ACTION_LEASE_TIME = timedelta(minutes=5)
LOCK_CHANGED_MESSAGE = "The site lock token changed before the write."  # Name the text without a credential term.
RetryRunBuilder = Callable[  # Keep the retry builder signature in one local term.
    [Mapping[str, Any], list[dict[str, Any]], Mapping[str, Any]],
    Mapping[str, Any],
]


class BulkActionError(ValueError):
    """Report one stable bulk action refusal code."""

    def __init__(self, code: str) -> None:
        """Store one safe machine code."""
        super().__init__(code)
        self.code = code


class SiteMutationGuard:
    """Recheck current permission and the exact site lock token."""

    def __init__(
        self,
        permission_reader: Callable[[str, str], bool],
        lock_reader: Callable[[str, str], Any],
        expected_tokens: Mapping[str, str],
    ) -> None:
        """Bind current guard readers and the signed-session token snapshot."""
        self._permission_reader = permission_reader
        self._lock_reader = lock_reader
        self._expected_tokens = dict(expected_tokens)

    def refusal(self, organization_id: str, site_id: str) -> str | None:
        """Return one guard refusal, or null when the write can start."""
        logger.info("Recheck one run action site guard")
        if not self._permission_reader(organization_id, site_id):
            return "site_write_forbidden"
        expected = self._expected_tokens.get(site_id, "")
        if not expected:
            return "site_lock_not_owned"
        current = self._lock_reader(organization_id, site_id)
        current_token = self._token(current)
        if not current_token:
            return "site_lock_not_owned"
        if current_token != expected:
            return "site_lock_token_changed"
        logger.debug("The run action site guard passed")
        return None

    @staticmethod
    def _token(record: Any) -> str:
        """Return the lock token from one supported lock record."""
        if isinstance(record, Mapping):
            return str(record.get("lock_token") or "")
        return str(getattr(record, "lock_token", "") or "")


class BulkRunActionService:
    """Process cancel and retry actions through the durable action journal."""

    def __init__(
        self,
        repository: Any,
        run_reader: Callable[[str], Mapping[str, Any] | None],
        guard: SiteMutationGuard,
        site_run_reader: Callable[[str], list[Mapping[str, Any]]] | None = None,
        retry_run_builder: (
            Callable[
                [Mapping[str, Any], list[dict[str, Any]], Mapping[str, Any]],
                Mapping[str, Any],
            ]
            | None
        ) = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Bind the durable repository, current run reader, and guard."""
        self._repository = repository
        self._run_reader = run_reader
        self._guard = guard
        self._site_run_reader = site_run_reader
        self._retry_run_builder = retry_run_builder
        self._clock = clock or (lambda: datetime.now(tz=UTC))

    def cancel(
        self,
        *,
        actor: DurableActorScope,
        idempotency_key: str,
        confirmation: str,
        preview: Mapping[str, Any],
    ) -> UpgradeRunAction:
        """Create or replay one atomic bulk cancel action."""
        run_ids = self._run_ids(preview)
        expected = f"CANCEL {len(run_ids)} RUNS"
        if confirmation != expected:
            raise BulkActionError("confirmation_mismatch")
        organization_id = str(preview.get("organization_id") or "")
        history_scope = str(preview.get("history_scope") or "")
        preview_id = str(preview.get("preview_id") or "")
        site_count = int(preview.get("site_count") or 0)
        site_ids = tuple(self._site_id(self._run_reader(run_id)) for run_id in run_ids)
        identity = ActionIdentity.from_request(
            actor,
            idempotency_key,
            {
                "action": "cancel",
                "organization_id": organization_id,
                "history_scope": history_scope,
                "run_ids": list(run_ids),
                "preview_id": preview_id,
                "preview_digest": canonical_digest(preview),
            },
            confirmation,
        )
        initialization = ActionInitialization(
            identity,
            ActionSource.bulk(
                preview_id,
                canonical_digest(preview),
                organization_id,
                history_scope,
            ),
            ActionIntent("cancel", run_ids, site_ids, site_count),
        )
        now = self._now()
        lease = ActionLease("worker-" + uuid.uuid4().hex, self._future(now, ACTION_LEASE_TIME))
        replay = ActionReplayService(self._repository, lambda: now)
        request = ReplayRequest(initialization, lease)
        return replay.resolve(request, lambda action, item: self._cancel_item(action, item, now))

    def retry(
        self,
        *,
        actor: DurableActorScope,
        idempotency_key: str,
        confirmation: str,
        preview: Mapping[str, Any],
    ) -> UpgradeRunAction:
        """Create or replay one atomic bulk retry action."""
        retry_run_builder = self._retry_run_builder  # Freeze the optional builder before the replay closure.
        if self._site_run_reader is None or retry_run_builder is None:  # Refuse retry when one reader is unavailable.
            raise BulkActionError("retry_unavailable")
        run_ids = self._run_ids(preview)
        expected = f"RETRY {len(run_ids)} RUNS"
        if confirmation != expected:
            raise BulkActionError("confirmation_mismatch")
        records = tuple(self._run_reader(run_id) for run_id in run_ids)  # Preserve one read per requested run.
        winners = self._retry_winners(records)  # Select the same newest retry source for each site.
        initialization = self._retry_initialization(actor, idempotency_key, confirmation, preview, records)
        now = self._now()
        lease = ActionLease("worker-" + uuid.uuid4().hex, self._future(now, ACTION_LEASE_TIME))
        replay = ActionReplayService(self._repository, lambda: now)
        request = ReplayRequest(initialization, lease)
        return replay.resolve(
            request,
            lambda action, item: self._retry_item(action, item, winners, retry_run_builder),  # Keep the callable typed.
        )

    def _cancel_item(
        self,
        action: UpgradeRunAction,
        item: RunActionOutcome,
        now: str,
    ) -> RecoveryDecision:
        """Build one current cancel decision after the durable claim."""
        record = self._run_reader(item.identity.source_run_id)
        if record is None:
            return RecoveryDecision(self._outcome(item, "refused", "run_not_found", "", "", now))
        site_id = self._site_id(record)
        if site_id != item.identity.site_id:
            return RecoveryDecision(self._outcome(item, "refused", "run_changed", "", "", now))
        guard_reason = self._guard.refusal(action.source.organization_id, site_id)
        if guard_reason is not None:
            outcome = self._outcome(item, "refused", guard_reason, str(record.get("state") or ""), "", now)
            return RecoveryDecision(outcome, site_block=(site_id, guard_reason))
        prior_state = self._state(record)
        if prior_state is None:
            return RecoveryDecision(self._outcome(item, "refused", "run_state_unknown", "", "", now))
        if prior_state in RunStateMachine.TERMINAL:
            return RecoveryDecision(self._outcome(item, "refused", "run_already_final", prior_state, "", now))
        if prior_state not in PRE_CLOUD_STATES:
            return RecoveryDecision(self._outcome(item, "refused", "run_not_precloud", prior_state, "", now))
        revision = str(record.get("_rev") or "")
        if not revision:
            return RecoveryDecision(self._outcome(item, "unknown", "run_write_unverified", prior_state, "", now))
        changed_at = self._now()
        outcome = self._outcome(
            item,
            "succeeded",
            "precloud_run_cancelled",
            prior_state,
            "cancelled",
            changed_at,
        )
        mutation = RunMutation(
            "update",
            item.identity.source_run_id,
            revision,
            prior_state,
            {"state": "cancelled", "updated_at": changed_at},
        )
        return RecoveryDecision(outcome, mutation)

    def _retry_item(
        self,
        action: UpgradeRunAction,
        item: RunActionOutcome,
        winners: Mapping[str, str],
        retry_run_builder: RetryRunBuilder,
    ) -> RecoveryDecision:
        """Build one current retry decision after the durable claim."""
        checked_at = self._now()
        record = self._run_reader(item.identity.source_run_id)
        refusal = self._retry_item_refusal(action, item, record, checked_at)  # Preserve all early refusal checks.
        if refusal is not None:
            return refusal
        record = cast(Mapping[str, Any], record)  # Narrow the checked record after the refusal helper.
        site_id = self._site_id(record)  # Reuse the checked site identifier for later checks.
        prior_state = self._state(record)  # Reuse the checked source state for later outcomes.
        policy = RetryCopyPolicy(self._clock())
        try:
            policy.source_time(record)
            copied_options = policy.copy_options(record)
            copied_targets = policy.copy_targets(record)
        except RetryPolicyError as error:
            return RecoveryDecision(self._retry_outcome(item, "refused", error.code, prior_state, checked_at))
        if winners.get(site_id) != item.identity.source_run_id:
            return RecoveryDecision(
                self._retry_outcome(item, "refused", "site_duplicate_retry_source", prior_state, checked_at)
            )
        live_run_id = self._live_run_id(site_id, item.identity.source_run_id)
        if live_run_id:
            return RecoveryDecision(
                self._retry_outcome(
                    item,
                    "refused",
                    "upgrade_already_running",
                    prior_state,
                    checked_at,
                    live_run_id=live_run_id,
                )
            )
        revision = str(record.get("_rev") or "")
        if not revision:
            return RecoveryDecision(
                self._retry_outcome(item, "unknown", "retry_create_unverified", prior_state, checked_at)
            )
        created = self._build_retry_run(retry_run_builder, record, copied_targets, copied_options)  # Build safely.
        result_run_id = str(created.get("run_id") or "")  # Summarize the builder result without target data.
        if not result_run_id:
            return RecoveryDecision(self._retry_outcome(item, "failed", "retry_create_failed", prior_state, checked_at))
        self._prepare_retry_document(  # Apply the durable retry fields after the builder returns an identifier.
            created, action, item, copied_targets, copied_options
        )
        outcome = self._retry_outcome(
            item,
            "succeeded",
            "retry_created",
            prior_state,
            checked_at,
            result_run_id=result_run_id,
            final_state="created",
        )
        mutation = RetryRunMutation(
            result_run_id,
            item.identity.source_run_id,
            revision,
            prior_state,
            site_id,
            created,
        )
        return RecoveryDecision(outcome, mutation)

    def _retry_initialization(
        self,
        actor: DurableActorScope,
        idempotency_key: str,
        confirmation: str,
        preview: Mapping[str, Any],
        records: tuple[Mapping[str, Any] | None, ...],
    ) -> ActionInitialization:
        """Build one retry action initialization.

        Args:
            actor: The durable actor for the request.
            idempotency_key: The client request key.
            confirmation: The typed confirmation text.
            preview: The verified preview payload.
            records: The current source run records.

        Returns:
            The durable action initialization.
        """
        organization_id = str(preview.get("organization_id") or "")  # Preserve the signed organization value.
        history_scope = str(preview.get("history_scope") or "")  # Preserve the signed history scope value.
        preview_id = str(preview.get("preview_id") or "")  # Preserve the signed preview identifier.
        site_ids = tuple(self._site_id(record) for record in records)  # Preserve prior site identifier extraction.
        identity = ActionIdentity.from_request(  # Build the same durable identity payload.
            actor,
            idempotency_key,
            self._retry_request_document(preview, organization_id, history_scope, preview_id),
            confirmation,
        )
        return ActionInitialization(  # Keep the durable retry source and intent unchanged.
            identity,
            ActionSource.bulk(preview_id, canonical_digest(preview), organization_id, history_scope),
            ActionIntent("retry", self._run_ids(preview), site_ids, int(preview.get("site_count") or 0)),
        )

    @staticmethod
    def _retry_request_document(
        preview: Mapping[str, Any],
        organization_id: str,
        history_scope: str,
        preview_id: str,
    ) -> dict[str, Any]:
        """Return the request document for one retry action.

        Args:
            preview: The verified preview payload.
            organization_id: The organization from the preview.
            history_scope: The history scope from the preview.
            preview_id: The preview identifier from the preview.

        Returns:
            The canonical retry request document.
        """
        return {  # Preserve the exact durable identity fields.
            "action": "retry",
            "organization_id": organization_id,
            "history_scope": history_scope,
            "run_ids": list(BulkRunActionService._run_ids(preview)),
            "preview_id": preview_id,
            "preview_digest": canonical_digest(preview),
        }

    def _retry_winners(self, records: tuple[Mapping[str, Any] | None, ...]) -> dict[str, str]:
        """Return the newest retry source for each site.

        Args:
            records: The current source run records.

        Returns:
            A map from site identifier to winning run identifier.
        """
        policy = RetryCopyPolicy(self._clock())  # Use one clock value for the winner policy.
        return policy.newest_by_site(tuple(record for record in records if record is not None))  # Skip absent rows.

    def _retry_item_refusal(
        self,
        action: UpgradeRunAction,
        item: RunActionOutcome,
        record: Mapping[str, Any] | None,
        checked_at: str,
    ) -> RecoveryDecision | None:
        """Return one early retry refusal, or null when checks pass.

        Args:
            action: The durable parent action.
            item: The claimed action item.
            record: The current source run record.
            checked_at: The final check time.

        Returns:
            The refusal decision, or null when retry can continue.
        """
        if record is None:  # Preserve the missing-run refusal.
            return RecoveryDecision(self._retry_outcome(item, "refused", "run_not_found", "", checked_at))
        site_id = self._site_id(record)  # Preserve the current site identifier check.
        prior_state = self._state(record)  # Preserve the current source state read.
        if site_id != item.identity.site_id:  # Preserve the site mismatch refusal.
            return RecoveryDecision(self._retry_outcome(item, "refused", "run_changed", "", checked_at))
        guard_reason = self._guard.refusal(action.source.organization_id, site_id)  # Recheck permission and lock.
        if guard_reason is not None:  # Preserve guard refusal handling.
            outcome = self._retry_outcome(item, "refused", guard_reason, str(record.get("state") or ""), checked_at)
            return RecoveryDecision(outcome, site_block=(site_id, guard_reason))
        if prior_state not in RETRYABLE_STATES:  # Preserve retryable-state refusal.
            return RecoveryDecision(
                self._retry_outcome(item, "refused", "run_not_retryable", prior_state or "", checked_at)
            )
        return None  # Let the caller continue with retry copy checks.

    @staticmethod
    def _build_retry_run(
        retry_run_builder: RetryRunBuilder,
        record: Mapping[str, Any],
        copied_targets: list[dict[str, Any]],
        copied_options: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Build one retry run document from copied safe data.

        Args:
            retry_run_builder: The approved retry run builder.
            record: The checked source run record.
            copied_targets: The copied target list.
            copied_options: The copied option map.

        Returns:
            The new retry run document.
        """
        logger.info("Build one retry run from the approved source")  # Record the action before the builder runs.
        created = dict(retry_run_builder(record, copied_targets, copied_options))  # Use the checked builder from retry.
        result_run_id = str(created.get("run_id") or "")  # Summarize the builder result without target data.
        logger.debug("Built one retry run from the approved source with identifier %s", result_run_id)  # Confirm build.
        return created  # Return the mutable run document for final durable fields.

    @staticmethod
    def _prepare_retry_document(
        created: dict[str, Any],
        action: UpgradeRunAction,
        item: RunActionOutcome,
        copied_targets: list[dict[str, Any]],
        copied_options: Mapping[str, Any],
    ) -> None:
        """Apply durable retry fields to one created run document.

        Args:
            created: The mutable retry run document.
            action: The durable parent action.
            item: The claimed action item.
            copied_targets: The copied target list.
            copied_options: The copied option map.
        """
        created["state"] = "created"  # Preserve the durable retry starting state.
        created["site_id"] = item.identity.site_id  # Preserve the checked source site.
        created["org_id"] = action.source.organization_id  # Preserve the action source organization.
        created["targets"] = copied_targets  # Preserve the approved copied targets.
        created["options"] = copied_options  # Preserve the approved copied options.
        created["retry_of_run_id"] = item.identity.source_run_id  # Preserve the source run link.
        created.pop("_key", None)  # Remove storage identity from the builder output.
        created.pop("_id", None)  # Remove storage identity from the builder output.
        created.pop("_rev", None)  # Remove storage revision from the builder output.

    def _live_run_id(self, site_id: str, source_run_id: str) -> str:
        """Return one current nonfinal run for the site."""
        if self._site_run_reader is None:
            return ""
        rows = sorted(self._site_run_reader(site_id), key=lambda row: str(row.get("run_id") or ""))
        for row in rows:
            run_id = str(row.get("run_id") or "")
            if not run_id or run_id == source_run_id:
                continue
            state = self._state(row)
            if state is None or state not in RunStateMachine.TERMINAL:
                return run_id
        return ""

    @staticmethod
    def _retry_outcome(
        item: RunActionOutcome,
        classification: str,
        reason: str,
        prior_state: str,
        now: str,
        *,
        result_run_id: str = "",
        final_state: str = "",
        live_run_id: str = "",
    ) -> RunActionOutcome:
        """Return one final retry outcome."""
        messages = {
            "retry_created": "The portal created a retry run.",
            "run_not_found": "The portal found no run with this identifier.",
            "run_not_retryable": "The source run is not failed, stopped, or cancelled.",
            "retry_source_time_unknown": "The source run has no valid update time.",
            "retry_options_unsupported": "The source run has an unsupported option.",
            "retry_options_invalid": "The source run has an invalid option value.",
            "site_duplicate_retry_source": "A newer selected source won for this site.",
            "site_write_forbidden": "The current operator cannot write to this site.",
            "site_lock_not_owned": "The current operator does not own the site lock.",
            "site_lock_token_changed": LOCK_CHANGED_MESSAGE,  # Reuse safe text without a flagged constant name.
            "upgrade_already_running": "The site already has a live upgrade run.",
            "run_changed": "The source run changed before the write.",
            "retry_create_failed": "The portal could not create the retry run.",
            "retry_create_unverified": "The portal cannot verify the retry run.",
        }
        state = OutcomeState(prior_state, final_state, now, now)
        completion = OutcomeCompletion(
            classification,
            reason,
            messages[reason],
            result_run_id,
            state,
            live_run_id,
        )
        return item.finalized(completion)

    @staticmethod
    def _outcome(
        item: RunActionOutcome,
        classification: str,
        reason: str,
        prior_state: str,
        final_state: str,
        now: str,
    ) -> RunActionOutcome:
        """Return one final cancel outcome."""
        messages = {
            "precloud_run_cancelled": "The portal cancelled the pre-cloud run.",
            "run_not_found": "The portal found no run with this identifier.",
            "run_not_precloud": "The run already reached cloud work.",
            "run_already_final": "The run already has a final state.",
            "run_state_unknown": "The portal cannot identify the current run state.",
            "site_write_forbidden": "The current operator cannot write to this site.",
            "site_lock_not_owned": "The current operator does not own the site lock.",
            "site_lock_token_changed": LOCK_CHANGED_MESSAGE,  # Reuse safe text without a flagged constant name.
            "run_changed": "The run changed before the write.",
            "run_write_unverified": "The portal cannot verify the run write.",
        }
        state = OutcomeState(prior_state, final_state, now, now)
        result_run_id = item.identity.source_run_id if classification == "succeeded" else ""
        completion = OutcomeCompletion(classification, reason, messages[reason], result_run_id, state)
        return item.finalized(completion)

    @staticmethod
    def _run_ids(preview: Mapping[str, Any]) -> tuple[str, ...]:
        """Return the validated ordered run identifiers from one preview."""
        raw = preview.get("run_ids")
        if not isinstance(raw, list) or any(not isinstance(value, str) or not value for value in raw):
            raise BulkActionError("preview_mismatch")
        run_ids = tuple(raw)
        if not 1 <= len(run_ids) <= 50:
            raise BulkActionError("batch_size_invalid")
        if len(set(run_ids)) != len(run_ids):
            raise BulkActionError("duplicate_run_id")
        return run_ids

    @staticmethod
    def _site_id(record: Mapping[str, Any] | None) -> str:
        """Return one run site identifier, or empty text."""
        return str(record.get("site_id") or "") if record is not None else ""

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
            raise ValueError("The action clock must return an aware time.")
        return value.astimezone(UTC).isoformat()

    @staticmethod
    def _future(now: str, duration: timedelta) -> str:
        """Return one lease end after the supplied UTC time."""
        return (datetime.fromisoformat(now) + duration).isoformat()

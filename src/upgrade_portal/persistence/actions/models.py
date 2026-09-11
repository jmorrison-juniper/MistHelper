"""Define immutable records for durable upgrade run actions.

Why:
    The action journal must keep one stable request and one ordered result for
    each run. These records validate that durable shape before a store write.
"""

from __future__ import annotations  # Keep each annotation independent from import order.

import hashlib  # Create stable digests without storing request secrets.
import json  # Create canonical text for each stable digest.
import logging  # Record model construction without raw actor values.
import re  # Validate each stored digest before a database write.
import uuid  # Create opaque public action identifiers.
from collections.abc import Mapping, Sequence  # Accept read-only request and evidence values.
from dataclasses import dataclass, replace  # Build immutable records and safe changed copies.
from datetime import UTC, datetime  # Validate each durable lease and completion time.
from types import MappingProxyType  # Stop a caller from changing nested evidence.
from typing import Any, Self  # Describe JSON values and immutable copy methods.

logger = logging.getLogger(__name__)  # Keep action model logs in one named module.

_DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")  # Accept one SHA-256 hexadecimal digest.
_VISIBLE_ASCII_PATTERN = re.compile(r"^[\x21-\x7e]{16,128}$")  # Match the request key contract.
_SOURCE_KINDS = frozenset({"bulk_preview", "single_reconciliation"})  # Keep source values closed.
_ACTION_NAMES = frozenset({"cancel", "retry", "reconcile"})  # Keep action values closed.
_PROCESSING_STATES = frozenset({"pending", "claimed", "final"})  # Keep item states closed.
_CLASSIFICATIONS = frozenset({"succeeded", "refused", "failed", "unknown"})  # Keep result classes closed.
_SAFE_SUMMARY_FIELDS = frozenset(  # Allow only the approved reconciliation summary fields.
    {
        "schema_version",  # Identify the safe summary schema.
        "run_id",  # Link the summary to its source run.
        "run_revision",  # Bind the decision to the evidence read.
        "collected_at",  # State when the service collected the evidence.
        "targets",  # Hold only safe target evidence rows.
        "target_count",  # State the expected number of target rows.
        "complete_target_count",  # Count target rows with complete proof.
        "active_write_count",  # Count targets that still write firmware.
        "active_task_count",  # Count distinct active task digests.
        "unknown_target_count",  # Count incomplete targets without a conflict.
        "has_conflict",  # State whether evidence sources disagree.
        "is_complete",  # State whether every target has current proof.
        "decision_basis_digest",  # Bind the stored summary to its canonical fields.
    }
)  # Close the approved summary field set.
_SAFE_TARGET_FIELDS = frozenset(  # Allow only the approved safe target evidence fields.
    {
        "target_digest",  # Replace the raw target identifier.
        "stored_stop_result",  # Record the prior stored stop result.
        "task_digest",  # Replace the raw cloud task identifier.
        "task_state",  # Record the current task state.
        "write_state",  # Record the current firmware write state.
        "driver_state",  # Record any stored final driver state.
        "sources",  # Name the safe evidence sources.
        "observed_at",  # State when the current read completed.
        "is_complete",  # State whether this target has sufficient proof.
        "has_conflict",  # State whether sources disagree for this target.
        "conflict_reason",  # Name the stable conflict reason.
    }
)  # Close the approved target field set.


def _canonical_json(value: object) -> str:  # Give every digest one stable JSON representation.
    """Return canonical JSON text for a digest."""
    serializable = _thaw_json(value)  # Convert immutable mappings and tuples to plain JSON values.
    return json.dumps(serializable, sort_keys=True, separators=(",", ":"), ensure_ascii=True)  # Keep bytes stable.


def canonical_digest(value: object) -> str:  # Build a safe public digest from a JSON-compatible value.
    """Return one SHA-256 digest for a JSON-compatible value."""
    payload = _canonical_json(value).encode("utf-8")  # Use one encoding for every stored digest.
    return hashlib.sha256(payload).hexdigest()  # Store only the one-way digest.


def _require_digest(value: str, field_name: str) -> None:  # Validate one stored digest without logging its value.
    """Reject a value that is not one SHA-256 hexadecimal digest."""
    if _DIGEST_PATTERN.fullmatch(value) is None:  # A malformed digest cannot bind durable data.
        raise ValueError(f"The {field_name} value is not a SHA-256 digest.")  # Name only the safe field.


def _parse_time(value: str, field_name: str) -> datetime:  # Normalize one durable time for lease comparisons.
    """Return one aware UTC-compatible time."""
    try:  # A stored value can be malformed or can omit its time zone.
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))  # Accept the contract UTC suffix.
    except (TypeError, ValueError) as error:  # Keep the unsafe source value out of the message.
        raise ValueError(f"The {field_name} value is not a valid time.") from error  # Give one safe refusal.
    if parsed.tzinfo is None:  # A naive time cannot support a safe lease comparison.
        raise ValueError(f"The {field_name} value has no time zone.")  # Require an explicit zone.
    return parsed.astimezone(UTC)  # Compare every lease in one time zone.


def _is_json_sequence(value: Any) -> bool:  # Separate JSON array detection from recursive copying.
    """Report whether one value is a nontext JSON sequence."""
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))  # Exclude text values.


def _freeze_json(value: Any) -> Any:  # Copy one evidence value into immutable containers.
    """Return an immutable copy of one JSON-compatible value."""
    if isinstance(value, Mapping):  # A mapping needs an immutable recursive copy.
        copied = {str(key): _freeze_json(item) for key, item in value.items()}  # Copy each safe field.
        return MappingProxyType(copied)  # Stop a caller from changing the stored summary.
    if _is_json_sequence(value):  # Freeze JSON arrays but keep text scalar values unchanged.
        return tuple(_freeze_json(item) for item in value)  # Preserve order without a mutable list.
    return value  # Scalars are already immutable JSON values.


def _thaw_json(value: Any) -> Any:  # Copy one immutable value into JSON containers.
    """Return a mutable JSON-compatible copy for serialization."""
    if isinstance(value, Mapping):  # Convert each immutable mapping to a plain JSON object.
        return {str(key): _thaw_json(item) for key, item in value.items()}  # Copy every nested field.
    if isinstance(value, tuple):  # Convert each immutable sequence to a JSON array.
        return [_thaw_json(item) for item in value]  # Preserve the stored order.
    return value  # Return a scalar without modification.


def _require_summary_fields(summary: Mapping[str, Any]) -> None:  # Enforce the approved summary field set.
    """Reject an unsafe or incomplete evidence summary field set."""
    if set(summary) != _SAFE_SUMMARY_FIELDS:  # Extra fields can expose unsafe evidence.
        raise ValueError("The evidence summary has an unsafe or missing field.")  # Refuse the whole summary.


def _evidence_targets(summary: Mapping[str, Any]) -> Sequence[Any]:  # Validate and return safe target rows.
    """Return the validated target list from one evidence summary."""
    targets = summary.get("targets")  # Read the target list before count checks.
    if not _is_json_sequence(targets):  # Require one JSON target list.
        raise ValueError("The evidence summary targets value is not a list.")  # Keep the field shape stable.
    for target in targets:  # Inspect every target for an unsafe raw field.
        if not isinstance(target, Mapping) or set(target) != _SAFE_TARGET_FIELDS:  # Require the exact safe shape.
            raise ValueError("The evidence summary has an unsafe target field.")  # Reject raw target data.
    return targets  # Give count validation the approved target sequence.


def _require_target_count(
    summary: Mapping[str, Any], targets: Sequence[Any]
) -> None:  # Bind the declared target count.
    """Require the target count to match the stored target list."""
    if summary.get("target_count") != len(targets):  # The count must describe the stored list.
        raise ValueError("The evidence summary target count does not match.")  # Refuse incomplete evidence.


def evidence_summary_digest(summary: Mapping[str, Any]) -> str:  # Validate safe proof and return its digest.
    """Validate one safe evidence summary and return its decision digest."""
    _require_summary_fields(summary)  # Refuse an unsafe or incomplete top-level shape.
    targets = _evidence_targets(summary)  # Refuse an unsafe target list or target field.
    _require_target_count(summary, targets)  # Bind the declared count to the stored list.
    digest = str(summary.get("decision_basis_digest", ""))  # Read the claimed canonical digest.
    _require_digest(digest, "decision_basis_digest")  # Refuse a malformed evidence digest.
    basis = {  # Build the canonical decision input without its own digest.
        key: _thaw_json(value)  # Convert each immutable value for canonical JSON.
        for key, value in summary.items()  # Preserve every approved summary field.
        if key != "decision_basis_digest"  # Exclude the digest from its own input.
    }
    if canonical_digest(basis) != digest:  # A changed summary cannot keep the prior decision digest.
        raise ValueError("The evidence summary digest does not match.")  # Refuse unbound evidence.
    return digest  # Let the action store the same verified digest.


@dataclass(frozen=True, slots=True)
class DurableActorScope:  # Own one stable digest for an existing durable identity.
    """Hold a normalized durable actor and its safe scope digest."""

    identity_kind: str  # Name the existing identity kind.
    normalized_actor: str  # Keep the normalized value inside trusted process memory.
    actor_scope: str  # Store and expose only this stable digest.

    def __post_init__(self) -> None:  # Validate direct construction of a durable actor scope.
        """Require normalized identity values and their matching digest."""
        if self.identity_kind != self.identity_kind.strip().casefold():  # Require one stable kind spelling.
            raise ValueError("The durable identity kind is not normalized.")  # Refuse an unstable scope.
        if self.normalized_actor != self.normalized_actor.strip().casefold():  # Require one actor spelling.
            raise ValueError("The durable actor identity is not normalized.")  # Expose no actor value.
        expected = canonical_digest(  # Rebuild the stable scope from its two durable inputs.
            {"identity_kind": self.identity_kind, "normalized_actor": self.normalized_actor}
        )
        if not self.identity_kind or not self.normalized_actor or self.actor_scope != expected:
            raise ValueError("The durable actor scope does not match its identity.")  # Refuse an invalid binding.

    @classmethod
    def build(cls, identity_kind: str, actor_identity: str) -> Self:  # Create one normalized durable actor scope.
        """Build a stable scope that excludes browser and session identifiers."""
        logger.info("Build one durable actor scope")  # Record the safe identity transformation.
        kind = identity_kind.strip().casefold()  # Give the identity kind one stable spelling.
        actor = actor_identity.strip().casefold()  # Give the durable actor one stable spelling.
        if not kind or not actor:  # An empty identity would merge unrelated requests.
            raise ValueError("The durable actor identity is incomplete.")  # Expose no raw identity value.
        scope = canonical_digest({"identity_kind": kind, "normalized_actor": actor})  # Bind both durable fields.
        logger.debug("Built one durable actor scope")  # Confirm the transformation without actor data.
        return cls(kind, actor, scope)  # Keep the normalized value out of later serialization.


@dataclass(frozen=True, slots=True)
class ActionIdentity:  # Own the safe request-binding digests for one action.
    """Hold the safe digests that bind one idempotent action request."""

    actor_scope: str  # Bind the action to one durable actor.
    idempotency_key_digest: str  # Replace the raw request key.
    request_digest: str  # Bind all source-specific request fields.
    confirmation_digest: str  # Replace the exact typed confirmation.

    def __post_init__(self) -> None:  # Reject unsafe digest fields before persistence.
        """Validate every digest before the record reaches a store."""
        _require_digest(self.actor_scope, "actor_scope")  # Require the durable actor digest.
        _require_digest(self.idempotency_key_digest, "idempotency_key_digest")  # Require a safe request key.
        _require_digest(self.request_digest, "request_digest")  # Require a stable request binding.
        _require_digest(self.confirmation_digest, "confirmation_digest")  # Require a safe phrase digest.

    @classmethod
    def from_request(
        cls,
        actor: DurableActorScope,
        idempotency_key: str,
        request_fields: Mapping[str, Any],
        confirmation: str,
    ) -> Self:  # Convert raw request values into safe durable digests.
        """Build the safe identity values from one validated request."""
        logger.info("Build one action request digest set")  # Record the digest action before calculation.
        if _VISIBLE_ASCII_PATTERN.fullmatch(idempotency_key) is None:  # Enforce the HTTP request key contract.
            raise ValueError("The idempotency key must use 16 through 128 visible ASCII characters.")
        identity = cls(  # Store no raw request key, phrase, or actor identity.
            actor_scope=actor.actor_scope,  # Use the stable durable actor scope.
            idempotency_key_digest=canonical_digest(idempotency_key),  # Protect the raw request key.
            request_digest=canonical_digest(_thaw_json(request_fields)),  # Bind the source-specific fields.
            confirmation_digest=canonical_digest(confirmation),  # Protect the exact typed phrase.
        )
        logger.debug("Built one action request digest set")  # Confirm completion without raw input.
        return identity  # Give persistence only safe digest values.


@dataclass(frozen=True, slots=True)
class ActionSource:  # Own source-specific preview and organization values.
    """Hold the source-specific action fields."""

    source_kind: str  # Select bulk preview or single reconciliation rules.
    preview_id: str | None  # Name the bulk preview, or stay null for reconciliation.
    preview_digest: str | None  # Bind the bulk preview, or stay null for reconciliation.
    organization_id: str  # Keep the current organization scope.
    history_scope: str | None  # Keep the bulk history scope, or stay null for reconciliation.

    def __post_init__(self) -> None:  # Enforce the null and required rules for this source.
        """Enforce the null and required rules for each source."""
        self._validate_scope()  # Require one supported source and one organization.
        self._validate_preview_fields()  # Enforce the source-specific null rules.

    def _validate_scope(self) -> None:  # Validate the common action source fields.
        """Require one supported source and one organization."""
        if self.source_kind not in _SOURCE_KINDS:  # An unknown source has no safe field policy.
            raise ValueError("The action source kind is not supported.")  # Refuse unknown source behavior.
        if not self.organization_id.strip():  # Both action sources require one visible organization.
            raise ValueError("The action organization is empty.")  # Stop an unscoped action.

    def _validate_preview_fields(self) -> None:  # Apply the selected source-specific field rules.
        """Validate preview values for the selected source kind."""
        preview_fields = (self.preview_id, self.preview_digest, self.history_scope)  # Group the source fields.
        if self.source_kind == "bulk_preview" and not all(preview_fields):  # Bulk work needs all preview values.
            raise ValueError("A bulk action requires every preview field.")  # Fail before persistence.
        if self.source_kind == "single_reconciliation" and any(value is not None for value in preview_fields):
            raise ValueError("A reconciliation action requires null preview fields.")  # Keep sources separate.
        if self.preview_digest is not None:  # A present preview digest must have the safe stored shape.
            _require_digest(self.preview_digest, "preview_digest")  # Reject raw preview content.

    @classmethod
    def bulk(
        cls, preview_id: str, preview_digest: str, organization_id: str, history_scope: str
    ) -> Self:  # Build one validated authoritative preview source.
        """Build one source that came from an authoritative bulk preview."""
        logger.info("Build one bulk action source")  # Record source construction before validation.
        source = cls("bulk_preview", preview_id, preview_digest, organization_id, history_scope)  # Require fields.
        logger.debug("Built one bulk action source")  # Confirm construction without source values.
        return source  # Give action initialization one validated bulk source.

    @classmethod
    def reconciliation(cls, organization_id: str) -> Self:  # Build one validated reconciliation source.
        """Build one source for a single reconciliation without a preview."""
        logger.info("Build one reconciliation action source")  # Record source construction before validation.
        source = cls("single_reconciliation", None, None, organization_id, None)  # Keep preview fields null.
        logger.debug("Built one reconciliation action source")  # Confirm construction without scope values.
        return source  # Give action initialization one validated single-run source.


@dataclass(frozen=True, slots=True)
class ActionIntent:  # Own the ordered requested runs and authoritative site count.
    """Hold the ordered requested runs and their action."""

    action: str  # Name cancel, retry, or reconcile.
    run_ids: tuple[str, ...]  # Preserve the exact request order.
    site_ids: tuple[str, ...]  # Keep one known or empty site for each run.
    site_count: int  # Keep the authoritative site count.

    def __post_init__(self) -> None:  # Freeze and validate ordered action intent values.
        """Validate the action and the ordered identifier list."""
        object.__setattr__(self, "run_ids", tuple(self.run_ids))  # Freeze the ordered request identifiers.
        object.__setattr__(self, "site_ids", tuple(self.site_ids))  # Freeze the positional site identifiers.
        self._validate_action()  # Require one supported action name.
        self._validate_run_ids()  # Require 1 through 50 ordered distinct identifiers.
        self._validate_site_ids()  # Require aligned sites and an exact known count.

    def _validate_action(self) -> None:  # Validate one closed action name.
        """Require one supported action name."""
        if self.action not in _ACTION_NAMES:  # An unknown action has no mutation contract.
            raise ValueError("The action name is not supported.")  # Refuse unknown behavior.

    def _validate_run_ids(self) -> None:  # Validate batch bounds and identifier uniqueness.
        """Require 1 through 50 ordered distinct nonempty run identifiers."""
        if not 1 <= len(self.run_ids) <= 50:  # The HTTP contract limits one action to 50 runs.
            raise ValueError("An action must contain 1 through 50 run identifiers.")  # Keep batch size safe.
        if len(set(self.run_ids)) != len(self.run_ids):  # Silent deduplication would change confirmation counts.
            raise ValueError("The action contains a duplicate run identifier.")  # Reject the complete request.
        if any(not run_id for run_id in self.run_ids):  # An empty identifier cannot own an outcome.
            raise ValueError("The action contains an empty run identifier.")  # Require one stable key per item.

    def _validate_site_ids(self) -> None:  # Validate positional sites and the authoritative site count.
        """Require one site entry per run and an exact known site count."""
        if len(self.site_ids) != len(self.run_ids):  # Each placeholder needs its matching site value.
            raise ValueError("The action site list does not match the run list.")  # Preserve positional binding.
        if not 1 <= self.site_count <= len(self.run_ids):  # A site count cannot exceed its run count.
            raise ValueError("The action site count does not match the run list.")  # Refuse an invalid count.
        known_sites = {site_id for site_id in self.site_ids if site_id}  # Count only known placeholder sites.
        if known_sites and self.site_count != len(known_sites):  # Known sites must match the authoritative count.
            raise ValueError("The action site count does not match its known sites.")  # Refuse an inexact count.


@dataclass(frozen=True, slots=True)
class OutcomeIdentity:  # Own stable identity fields for one ordered item.
    """Hold the stable identity fields of one action outcome."""

    source_run_id: str  # Name the requested run.
    site_id: str  # Name the known site, or use empty text before processing.
    action: str  # Repeat the parent action.

    def __post_init__(self) -> None:  # Validate one stable item identity.
        """Require one source run and one supported parent action."""
        if not self.source_run_id:  # An empty run cannot own one durable outcome.
            raise ValueError("The outcome source run identifier is empty.")  # Refuse an unsafe item.
        if self.action not in _ACTION_NAMES:  # An unknown action cannot share parent semantics.
            raise ValueError("The outcome action is not supported.")  # Refuse a mismatched item.

    def document(self) -> dict[str, Any]:  # Serialize the stable item identity fields.
        """Return the identity fields for storage."""
        return {  # Keep the stored item shape flat.
            "source_run_id": self.source_run_id,  # Preserve the request identifier.
            "site_id": self.site_id,  # Preserve the known site scope.
            "action": self.action,  # Preserve the parent action name.
        }


@dataclass(frozen=True, slots=True)
class OutcomeClaim:  # Own one item processing state and worker lease.
    """Hold the processing claim of one action item."""

    processing_state: str  # Name pending, claimed, or final.
    claim_owner: str | None  # Name the opaque worker that owns possible work.
    claim_expires_at: str | None  # State when that item claim expires.

    def __post_init__(self) -> None:  # Enforce the item state and claim field relation.
        """Validate the item processing state and claim fields."""
        if self.processing_state not in _PROCESSING_STATES:  # An unknown state breaks recovery.
            raise ValueError("The item processing state is not supported.")  # Refuse an unsafe lifecycle.
        if self.processing_state == "pending" and (self.claim_owner or self.claim_expires_at):
            raise ValueError("A pending item cannot hold a claim.")  # Keep untouched items unowned.
        if self.processing_state != "pending" and (not self.claim_owner or not self.claim_expires_at):
            raise ValueError("A claimed or final item requires its claim fields.")  # Keep mutation ownership.
        if self.claim_expires_at is not None:  # A present claim time must support a safe comparison.
            _parse_time(self.claim_expires_at, "claim_expires_at")  # Refuse malformed or naive times.

    def document(self) -> dict[str, Any]:  # Serialize one item claim.
        """Return the claim fields for storage."""
        return {  # Keep the stored item shape flat.
            "processing_state": self.processing_state,  # Preserve recovery state.
            "claim_owner": self.claim_owner,  # Preserve the opaque worker owner.
            "claim_expires_at": self.claim_expires_at,  # Preserve the claim lease end.
        }


@dataclass(frozen=True, slots=True)
class OutcomeState:  # Own the final eligibility, result, and observation values.
    """Hold the prior, final, and observation times of one outcome."""

    prior_state: str  # State the run value at its final eligibility read.
    final_state: str  # State the verified result, or empty text.
    checked_at: str  # State the final check time, or empty text.
    completed_at: str  # State the outcome time, or empty text.

    def document(self) -> dict[str, str]:  # Serialize final run state fields.
        """Return the state fields for storage."""
        return {  # Keep the stored item shape flat.
            "prior_state": self.prior_state,  # Preserve the final eligibility state.
            "final_state": self.final_state,  # Preserve only a verified final state.
            "checked_at": self.checked_at,  # Preserve the final check time.
            "completed_at": self.completed_at,  # Preserve the durable outcome time.
        }


@dataclass(frozen=True, slots=True)
class OutcomeCompletion:  # Own one final classification, reason, message, and state.
    """Hold the final result fields that replace one placeholder."""

    classification: str  # Name succeeded, refused, failed, or unknown.
    reason: str  # Give one stable machine reason.
    message: str  # Give safe operator text.
    result_run_id: str  # Name the changed or created run, or use empty text.
    state: OutcomeState  # Keep the run states and times together.

    def __post_init__(self) -> None:  # Enforce one supported and explained final result.
        """Validate one final result."""
        if self.classification not in _CLASSIFICATIONS:  # An unknown class cannot enter response counts.
            raise ValueError("The outcome classification is not supported.")  # Refuse an unstable result.
        if not self.reason or not self.message:  # A final result must explain itself.
            raise ValueError("A final outcome requires a reason and a message.")  # Keep operator results useful.
        self._validate_result_claims()  # Keep success and unknown state claims exact.

    def _validate_result_claims(self) -> None:  # Validate result identifiers and final state claims.
        """Require success proof and prevent unverified final state claims."""
        if self.classification == "succeeded" and (not self.result_run_id or not self.state.final_state):
            raise ValueError("A succeeded outcome requires a verified result run and state.")  # Require proof.
        if self.classification != "succeeded" and self.result_run_id:
            raise ValueError("A nonsuccess outcome cannot name a result run.")  # Avoid a false mutation claim.
        if self.classification == "unknown" and self.state.final_state:
            raise ValueError("An unknown outcome cannot claim a final state.")  # Preserve uncertainty.

    def document(self) -> dict[str, Any]:  # Serialize one final result.
        """Return the final result fields for storage."""
        result = {  # Keep the stored item shape flat.
            "classification": self.classification,  # Preserve the stable result class.
            "reason": self.reason,  # Preserve the stable machine reason.
            "message": self.message,  # Preserve safe operator text.
            "result_run_id": self.result_run_id,  # Preserve the verified result identifier.
        }
        result.update(self.state.document())  # Add the four final state fields.
        return result  # Give the repository one complete result map.


@dataclass(frozen=True, slots=True)
class RunActionOutcome:  # Own one immutable item across pending, claimed, and final states.
    """Hold one immutable ordered action item as a documented value record."""

    identity: OutcomeIdentity  # Keep stable item identity together.
    claim: OutcomeClaim  # Keep processing ownership together.
    completion: OutcomeCompletion  # Keep result classification and state together.
    evidence_summary: Mapping[str, Any] | None  # Hold only canonical safe reconciliation proof.

    @property
    def source_run_id(self) -> str:  # Expose the nested source run identifier.
        """Return the requested run identifier."""
        return self.identity.source_run_id  # Read the value from the cohesive identity record.

    @property
    def site_id(self) -> str:  # Expose the nested site identifier.
        """Return the known site identifier."""
        return self.identity.site_id  # Read the value from the cohesive identity record.

    @property
    def action(self) -> str:  # Expose the nested parent action name.
        """Return the parent action name."""
        return self.identity.action  # Read the value from the cohesive identity record.

    @property
    def processing_state(self) -> str:  # Expose the nested item processing state.
        """Return the item processing state."""
        return self.claim.processing_state  # Read the value from the cohesive claim record.

    @property
    def claim_owner(self) -> str | None:  # Expose the nested opaque claim owner.
        """Return the opaque item claim owner."""
        return self.claim.claim_owner  # Read the value from the cohesive claim record.

    @property
    def claim_expires_at(self) -> str | None:  # Expose the nested item claim expiry.
        """Return the item claim expiry."""
        return self.claim.claim_expires_at  # Read the value from the cohesive claim record.

    @property
    def classification(self) -> str:  # Expose the nested stable result class.
        """Return the stable result classification."""
        return self.completion.classification  # Read the value from the cohesive completion record.

    @property
    def reason(self) -> str:  # Expose the nested stable result reason.
        """Return the stable result reason."""
        return self.completion.reason  # Read the value from the cohesive completion record.

    @property
    def message(self) -> str:  # Expose the nested safe operator message.
        """Return the safe operator message."""
        return self.completion.message  # Read the value from the cohesive completion record.

    @property
    def result_run_id(self) -> str:  # Expose the nested result run identifier.
        """Return the changed or created run identifier."""
        return self.completion.result_run_id  # Read the value from the cohesive completion record.

    @property
    def prior_state(self) -> str:  # Expose the nested final eligibility state.
        """Return the final eligibility state."""
        return self.completion.state.prior_state  # Read the value from the cohesive state record.

    @property
    def final_state(self) -> str:  # Expose the nested verified final state.
        """Return the verified final state."""
        return self.completion.state.final_state  # Read the value from the cohesive state record.

    @property
    def checked_at(self) -> str:  # Expose the nested final check time.
        """Return the final check time."""
        return self.completion.state.checked_at  # Read the value from the cohesive state record.

    @property
    def completed_at(self) -> str:  # Expose the nested durable outcome time.
        """Return the durable outcome time."""
        return self.completion.state.completed_at  # Read the value from the cohesive state record.

    def __post_init__(self) -> None:  # Freeze proof and enforce placeholder and evidence rules.
        """Validate placeholder and evidence rules."""
        if self.evidence_summary is not None:  # A direct constructor can receive a mutable mapping.
            object.__setattr__(self, "evidence_summary", _freeze_json(self.evidence_summary))  # Freeze all proof.
        self._validate_placeholder()  # Enforce one unknown not-processed value before finalization.
        self._validate_evidence()  # Enforce safe reconciliation evidence and stopped proof.

    def _validate_placeholder(self) -> None:  # Validate action and nonfinal placeholder values.
        """Validate the action and nonfinal placeholder values."""
        if self.claim.processing_state != "final" and self.completion.reason != "not_processed":
            raise ValueError("A nonfinal outcome must use the not_processed placeholder.")  # Keep one placeholder.
        if self.claim.processing_state != "final" and self.completion.classification != "unknown":
            raise ValueError("A nonfinal outcome must use the unknown classification.")  # Keep one placeholder.
        if self.claim.processing_state == "final":  # A final item needs both durable observation times.
            self._validate_final_times()  # Refuse a final item that still looks like a placeholder.

    def _validate_final_times(self) -> None:  # Validate final outcome observation and completion times.
        """Require aware check and completion times for a final item."""
        if not self.completion.state.checked_at or not self.completion.state.completed_at:
            raise ValueError("A final outcome requires check and completion times.")  # Keep audit times exact.
        _parse_time(self.completion.state.checked_at, "checked_at")  # Require one aware final check time.
        _parse_time(self.completion.state.completed_at, "completed_at")  # Require one aware outcome time.

    def _validate_evidence(self) -> None:  # Validate safe proof and the stopped evidence requirement.
        """Validate optional reconciliation evidence."""
        if self.evidence_summary is not None:  # A present summary must contain safe canonical fields.
            evidence_summary_digest(self.evidence_summary)  # Reject unsafe or unbound evidence.
        if self.evidence_summary is not None and self.identity.action != "reconcile":
            raise ValueError("Only a reconciliation outcome can hold evidence.")  # Keep bulk output free of proof.
        if self.completion.state.final_state == "stopped" and self.evidence_summary is None:
            raise ValueError("A stopped reconciliation outcome requires evidence.")  # Require proof for stopped.

    @classmethod
    def pending(cls, run_id: str, site_id: str, action: str) -> Self:  # Build one durable placeholder.
        """Build one ordered durable unknown placeholder."""
        state = OutcomeState("", "", "", "")  # A placeholder makes no state claim.
        completion = OutcomeCompletion("unknown", "not_processed", "The portal did not process this run.", "", state)
        return cls(OutcomeIdentity(run_id, site_id, action), OutcomeClaim("pending", None, None), completion, None)

    def claimed(self, owner: str, expires_at: str) -> Self:  # Claim one pending item before possible work.
        """Return this pending item with one durable processing claim."""
        if self.claim.processing_state != "pending":  # Recovery must never repeat claimed or final work.
            raise ValueError("Only a pending item can receive a claim.")  # Refuse a repeated mutation.
        return replace(self, claim=OutcomeClaim("claimed", owner, expires_at))  # Preserve the placeholder result.

    def finalized(
        self, completion: OutcomeCompletion, evidence_summary: Mapping[str, Any] | None = None
    ) -> Self:  # Close one claimed item with its durable result.
        """Return this claimed item with one final durable outcome."""
        if self.claim.processing_state != "claimed":  # A final write must own the possible mutation.
            raise ValueError("Only a claimed item can become final.")  # Keep compare-and-swap ownership.
        evidence = _freeze_json(evidence_summary) if evidence_summary is not None else None  # Freeze safe proof.
        return replace(
            self, claim=replace(self.claim, processing_state="final"), completion=completion, evidence_summary=evidence
        )

    def interrupted(self, completed_at: str) -> Self:  # Close one abandoned claim without repeating work.
        """Return one abandoned claimed item as a final unknown result."""
        state = OutcomeState("", "", completed_at, completed_at)  # Record when recovery closed the item.
        result = OutcomeCompletion(
            "unknown", "processing_interrupted", "Processing stopped before verification.", "", state
        )
        return self.finalized(result)  # Never repeat a possibly committed mutation.

    def document(self) -> dict[str, Any]:  # Serialize one complete flat action item.
        """Return the flat storage document for this outcome."""
        result = self.identity.document()  # Start with stable item identity.
        result.update(self.claim.document())  # Add processing ownership fields.
        result.update(self.completion.document())  # Add placeholder or final result fields.
        result["evidence_summary"] = _thaw_json(self.evidence_summary)  # Add only safe reconciliation proof.
        return result  # Preserve the exact flat data-model shape.

    def response(self) -> dict[str, Any]:  # Serialize one safe public action item.
        """Return the safe API response fields for this outcome."""
        document = self.document()  # Start from the validated flat item.
        document.pop("claim_owner")  # Keep worker identity out of the public result.
        document.pop("claim_expires_at")  # Keep the internal item lease out of the result.
        document.pop("checked_at")  # Keep the response aligned with the current HTTP contract.
        document.pop("completed_at")  # Keep the response aligned with the current HTTP contract.
        return document  # Expose no actor, request key, or raw evidence identifier.

    @classmethod
    def from_document(cls, document: Mapping[str, Any]) -> Self:  # Restore one validated stored item.
        """Build one validated outcome from a stored flat document."""
        identity = OutcomeIdentity(
            str(document["source_run_id"]), str(document.get("site_id", "")), str(document["action"])
        )
        claim = OutcomeClaim(  # Restore the durable processing state.
            str(document["processing_state"]),  # Restore pending, claimed, or final.
            document.get("claim_owner"),  # Restore the opaque worker owner.
            document.get("claim_expires_at"),  # Restore the item lease end.
        )
        completion = cls._completion_from_document(document)  # Restore all final result fields.
        summary = document.get("evidence_summary")  # Read optional safe reconciliation proof.
        evidence = _freeze_json(summary) if isinstance(summary, Mapping) else None  # Freeze a stored summary.
        return cls(identity, claim, completion, evidence)  # Validate the complete restored item.

    @staticmethod
    def _completion_from_document(
        document: Mapping[str, Any],
    ) -> OutcomeCompletion:  # Restore one cohesive completion value.
        """Return validated completion fields from one stored item."""
        state = OutcomeState(  # Restore the four final state fields.
            str(document.get("prior_state", "")),  # Restore the final eligibility state.
            str(document.get("final_state", "")),  # Restore the verified result state.
            str(document.get("checked_at", "")),  # Restore the final check time.
            str(document.get("completed_at", "")),  # Restore the outcome time.
        )
        completion = OutcomeCompletion(  # Restore placeholder or final result fields.
            str(document["classification"]),  # Restore the stable result class.
            str(document["reason"]),  # Restore the stable machine reason.
            str(document.get("message", "")),  # Restore safe operator text.
            str(document.get("result_run_id", "")),  # Restore the verified result identifier.
            state,  # Keep state fields grouped in memory.
        )
        return completion  # Give the outcome constructor one cohesive final result.


@dataclass(frozen=True, slots=True)
class ActionKey:  # Own the ArangoDB key, public identifier, and schema version.
    """Hold the database key and the public action identifier."""

    document_key: str  # Use the composite domain digest as the ArangoDB key.
    action_id: str  # Give the API one opaque public identifier.
    schema_version: int  # Start the durable action schema at one.

    def __post_init__(self) -> None:  # Validate direct construction of durable action keys.
        """Require one SHA-256 document key and schema version one."""
        _require_digest(self.document_key, "_key")  # Keep the composite key in its safe stored form.
        if not self.action_id.startswith("action-"):  # Public identifiers use one opaque stable prefix.
            raise ValueError("The public action identifier has an invalid format.")  # Refuse a raw identifier.
        if self.schema_version != 1 or isinstance(self.schema_version, bool):  # Accept the integer one only.
            raise ValueError("The action schema version must be the integer 1.")  # Keep the reader compatible.


@dataclass(frozen=True, slots=True)
class ActionBinding:  # Keep action keys and safe request identity in one value.
    """Hold the action keys and safe request identity together."""

    key: ActionKey  # Keep database and public identifiers together.
    identity: ActionIdentity  # Keep durable actor and request digests together.


@dataclass(frozen=True, slots=True)
class ActionLease:  # Own one opaque worker and its durable lease end.
    """Hold one opaque action processing lease."""

    owner: str  # Name one worker without actor or credential data.
    expires_at: str  # State when another worker can take ownership.

    def __post_init__(self) -> None:  # Validate one opaque worker lease.
        """Validate the opaque owner and its expiry."""
        if not self.owner.strip():  # An empty owner cannot protect a mutation.
            raise ValueError("The action lease owner is empty.")  # Refuse an unsafe lease.
        _parse_time(self.expires_at, "processing_expires_at")  # Require one aware lease end.

    def is_current(self, now: str) -> bool:  # Compare one lease with a controlled current time.
        """Report whether this lease still protects the action."""
        return _parse_time(self.expires_at, "processing_expires_at") > _parse_time(now, "current_time")


@dataclass(frozen=True, slots=True)
class ActionLifecycle:  # Own action status, lease, times, and safe evidence digest.
    """Hold the action status, lease, times, and evidence digest."""

    status: str  # Name processing or complete.
    lease: ActionLease  # Keep the current action owner and expiry together.
    created_at: str  # State when the action record started.
    completed_at: str | None  # State when every item became final.
    evidence_summary_digest: str | None  # Bind final reconciliation evidence.

    def __post_init__(self) -> None:  # Validate action status, times, and safe evidence.
        """Validate action status, times, and evidence digest."""
        if self.status not in {"processing", "complete"}:  # An unknown status breaks replay.
            raise ValueError("The action status is not supported.")  # Refuse an unsafe lifecycle.
        _parse_time(self.created_at, "created_at")  # Require one aware creation time.
        if self.status == "complete" and self.completed_at is None:  # Completion needs its audit time.
            raise ValueError("A complete action requires a completion time.")  # Keep completion durable.
        if self.status == "processing" and self.completed_at is not None:  # Processing cannot claim completion.
            raise ValueError("A processing action cannot have a completion time.")  # Keep lifecycle exact.
        if self.completed_at is not None:  # A present completion time must be safe to compare.
            _parse_time(self.completed_at, "completed_at")  # Refuse malformed or naive times.
        if self.evidence_summary_digest is not None:  # A present evidence digest must be safe.
            _require_digest(self.evidence_summary_digest, "evidence_summary_digest")  # Reject raw proof.


@dataclass(frozen=True, slots=True)
class ActionLedger:  # Own ordered action items and durable site stop decisions.
    """Hold ordered outcomes and durable site blocks."""

    items: tuple[RunActionOutcome, ...]  # Keep one item for every requested run.
    site_blocks: tuple[tuple[str, str], ...]  # Keep each durable site stop reason.

    def __post_init__(self) -> None:  # Freeze ordered outcomes and site block pairs.
        """Freeze the ordered items and site block entries."""
        object.__setattr__(self, "items", tuple(self.items))  # Stop a caller from changing outcome order.
        blocks = tuple((str(site_id), str(reason)) for site_id, reason in self.site_blocks)  # Copy each pair.
        if len({site_id for site_id, _ in blocks}) != len(blocks):  # One site can hold only one stop reason.
            raise ValueError("The action contains a duplicate site block.")  # Preserve the first guard failure.
        if any(not site_id or not reason for site_id, reason in blocks):  # Every block needs a safe explanation.
            raise ValueError("An action site block is incomplete.")  # Refuse an unusable safety record.
        object.__setattr__(self, "site_blocks", blocks)  # Stop a caller from changing durable site blocks.

    def block_map(self) -> dict[str, str]:  # Copy the immutable site block pairs for serialization.
        """Return a fresh site block map."""
        return dict(self.site_blocks)  # Stop a caller from editing the immutable ledger.


@dataclass(frozen=True, slots=True)
class ActionInitialization:  # Own the complete validated action creation request.
    """Hold the validated source, identity, and intent for initialization."""

    identity: ActionIdentity  # Bind the durable actor and request digests.
    source: ActionSource  # Apply bulk or reconciliation null rules.
    intent: ActionIntent  # Preserve the ordered requested runs and sites.

    def __post_init__(self) -> None:  # Validate the relation between source and action.
        """Validate the relation between the action and its source."""
        is_reconcile = self.intent.action == "reconcile"  # Read the action source relation once.
        if is_reconcile != (self.source.source_kind == "single_reconciliation"):
            raise ValueError("The action source does not match the action name.")  # Keep sources unambiguous.
        if is_reconcile and (len(self.intent.run_ids) != 1 or self.intent.site_count != 1):
            raise ValueError("A reconciliation action requires one run and one site.")  # Enforce single-run work.


@dataclass(frozen=True, slots=True)
class UpgradeRunAction:  # Own one immutable durable action as a documented value record.
    """Hold one immutable durable action as a documented value record."""

    binding: ActionBinding  # Keep keys and safe request identity together.
    source: ActionSource  # Keep source-specific fields together.
    intent: ActionIntent  # Keep ordered request values together.
    lifecycle: ActionLifecycle  # Keep status, lease, times, and evidence together.
    ledger: ActionLedger  # Keep ordered outcomes and site blocks together.

    @property
    def key(self) -> ActionKey:  # Expose nested action key values.
        """Return the database and public action identifiers."""
        return self.binding.key  # Keep the stored value inside the cohesive binding.

    @property
    def _key(self) -> str:  # Expose the exact ArangoDB data-model field.
        """Return the ArangoDB document key."""
        return self.key.document_key  # Expose the exact data-model field without another stored attribute.

    @property
    def identity(self) -> ActionIdentity:  # Expose nested safe request identity values.
        """Return the safe durable request identity."""
        return self.binding.identity  # Keep the stored value inside the cohesive binding.

    @property
    def action_id(self) -> str:  # Expose the opaque public action identifier.
        """Return the opaque public action identifier."""
        return self.key.action_id  # Read the value from the cohesive key record.

    @property
    def schema_version(self) -> int:  # Expose the durable action schema version.
        """Return the durable action schema version."""
        return self.key.schema_version  # Read the value from the cohesive key record.

    @property
    def actor_scope(self) -> str:  # Expose the safe durable actor digest.
        """Return the durable actor scope digest."""
        return self.identity.actor_scope  # Read the value from the cohesive request identity.

    @property
    def idempotency_key_digest(self) -> str:  # Expose the safe request key digest.
        """Return the safe request key digest."""
        return self.identity.idempotency_key_digest  # Read the value from the cohesive request identity.

    @property
    def request_digest(self) -> str:  # Expose the source-specific request digest.
        """Return the source-specific request digest."""
        return self.identity.request_digest  # Read the value from the cohesive request identity.

    @property
    def confirmation_digest(self) -> str:  # Expose the exact typed confirmation digest.
        """Return the exact confirmation digest."""
        return self.identity.confirmation_digest  # Read the value from the cohesive request identity.

    @property
    def source_kind(self) -> str:  # Expose the source-specific action kind.
        """Return the action source kind."""
        return self.source.source_kind  # Read the value from the cohesive source record.

    @property
    def preview_id(self) -> str | None:  # Expose the bulk preview identifier or null.
        """Return the bulk preview identifier, or null."""
        return self.source.preview_id  # Read the value from the cohesive source record.

    @property
    def preview_digest(self) -> str | None:  # Expose the bulk preview digest or null.
        """Return the bulk preview digest, or null."""
        return self.source.preview_digest  # Read the value from the cohesive source record.

    @property
    def organization_id(self) -> str:  # Expose the current organization scope.
        """Return the current organization scope."""
        return self.source.organization_id  # Read the value from the cohesive source record.

    @property
    def history_scope(self) -> str | None:  # Expose the bulk history scope or null.
        """Return the bulk history scope, or null."""
        return self.source.history_scope  # Read the value from the cohesive source record.

    @property
    def action(self) -> str:  # Expose cancel, retry, or reconcile.
        """Return cancel, retry, or reconcile."""
        return self.intent.action  # Read the value from the cohesive intent record.

    @property
    def status(self) -> str:  # Expose processing or complete.
        """Return processing or complete."""
        return self.lifecycle.status  # Read the value from the cohesive lifecycle record.

    @property
    def run_count(self) -> int:  # Expose the exact requested run count.
        """Return the exact requested run count."""
        return len(self.intent.run_ids)  # Derive the count from the immutable ordered identifiers.

    @property
    def site_count(self) -> int:  # Expose the authoritative site count.
        """Return the authoritative site count."""
        return self.intent.site_count  # Read the value from the cohesive intent record.

    @property
    def items(self) -> tuple[RunActionOutcome, ...]:  # Expose ordered immutable action outcomes.
        """Return the ordered immutable outcomes."""
        return self.ledger.items  # Read the value from the cohesive ledger record.

    @property
    def site_blocks(self) -> Mapping[str, str]:  # Expose immutable durable site stop decisions.
        """Return an immutable durable site block map."""
        return MappingProxyType(self.ledger.block_map())  # Stop a caller from changing stored safety state.

    @property
    def created_at(self) -> str:  # Expose the action creation time.
        """Return the action creation time."""
        return self.lifecycle.created_at  # Read the value from the cohesive lifecycle record.

    @property
    def processing_expires_at(self) -> str:  # Expose the action processing lease end.
        """Return the action processing lease expiry."""
        return self.lifecycle.lease.expires_at  # Read the value from the cohesive lifecycle record.

    @property
    def processing_owner(self) -> str:  # Expose the opaque action processing owner.
        """Return the opaque action processing owner."""
        return self.lifecycle.lease.owner  # Read the value from the cohesive lifecycle record.

    @property
    def completed_at(self) -> str | None:  # Expose the action completion time or null.
        """Return the action completion time, or null."""
        return self.lifecycle.completed_at  # Read the value from the cohesive lifecycle record.

    @property
    def evidence_summary_digest(self) -> str | None:  # Expose the safe reconciliation digest or null.
        """Return the safe reconciliation evidence digest, or null."""
        return self.lifecycle.evidence_summary_digest  # Read the value from the cohesive lifecycle record.

    @staticmethod
    def document_key(actor_scope: str, idempotency_key_digest: str) -> str:
        """Return the ArangoDB key for the composite durable domain key."""
        return canonical_digest([actor_scope, idempotency_key_digest])  # Preserve the approved field order.

    def __post_init__(self) -> None:  # Validate composite identity, ordered items, and final state.
        """Validate the complete action relation."""
        self._validate_binding()  # Require the registered composite domain key and source relation.
        self._validate_items()  # Require exact ordered items with the parent action.
        self._validate_completion()  # Require all final items before complete status.
        self._validate_evidence_digest()  # Bind safe reconciliation proof to the parent action.

    def _validate_binding(self) -> None:  # Validate the composite key and source relation.
        """Validate the composite key and source-specific action relation."""
        expected_key = self.document_key(self.identity.actor_scope, self.identity.idempotency_key_digest)
        if self.key.document_key != expected_key:  # The ArangoDB key must match the composite domain key.
            raise ValueError("The action document key does not match its domain key.")  # Refuse split identity.
        is_reconcile = self.intent.action == "reconcile"  # Read the source and action relation once.
        if is_reconcile != (self.source.source_kind == "single_reconciliation"):
            raise ValueError("The action source does not match the action name.")  # Reject corrupt stored data.
        if is_reconcile and (len(self.intent.run_ids) != 1 or self.intent.site_count != 1):
            raise ValueError("A reconciliation action requires one run and one site.")  # Reject corrupt storage.

    def _validate_items(self) -> None:  # Validate ordered item identity and parent action values.
        """Require one correctly ordered item for every requested run."""
        run_ids = tuple(item.identity.source_run_id for item in self.ledger.items)  # Read durable item order.
        if run_ids != self.intent.run_ids:  # A missing or moved placeholder breaks exact outcomes.
            raise ValueError("The action items do not match the requested run order.")  # Preserve exact order.
        if any(item.identity.action != self.intent.action for item in self.ledger.items):
            raise ValueError("An action item does not match its parent action.")  # Refuse mixed operations.

    def _validate_completion(self) -> None:  # Validate processing-to-complete item state.
        """Require every item to be final when the action is complete."""
        if self.lifecycle.status == "complete" and any(
            item.claim.processing_state != "final" for item in self.ledger.items
        ):
            raise ValueError("A complete action requires every item to be final.")  # Prevent partial completion.

    def _validate_evidence_digest(self) -> None:  # Validate parent and item evidence digest agreement.
        """Validate the action digest against each stored evidence summary."""
        digests = tuple(  # Read each verified decision digest from the ordered outcomes.
            evidence_summary_digest(item.evidence_summary)  # Recheck the safe summary before serialization.
            for item in self.ledger.items  # Inspect every requested outcome.
            if item.evidence_summary is not None  # Ignore pre-cloud and pre-evidence outcomes.
        )
        stored = self.lifecycle.evidence_summary_digest  # Read the parent digest once.
        if digests:  # A present summary requires one matching parent digest.
            self._require_matching_evidence(digests, stored)  # Refuse missing or different parent proof.
            return  # No orphan digest check applies when an outcome holds proof.
        if stored is not None:  # A parent digest without a summary proves nothing.
            raise ValueError("The action evidence digest has no outcome summary.")  # Refuse orphan evidence.

    @staticmethod
    def _require_matching_evidence(digests: tuple[str, ...], stored: str | None) -> None:
        """Require all item evidence digests to match the parent digest."""
        if stored is None or any(digest != stored for digest in digests):  # Bind every stored summary.
            raise ValueError("The action evidence digest does not match its outcome.")  # Refuse partial proof.

    @classmethod
    def initialize(cls, request: ActionInitialization, lease: ActionLease, created_at: str) -> Self:
        """Build one processing action with ordered durable placeholders."""
        logger.info("Build one durable action record")  # Record the model action before construction.
        document_key = canonical_digest([request.identity.actor_scope, request.identity.idempotency_key_digest])
        action_id = "action-" + uuid.uuid4().hex  # Create one opaque public identifier.
        items = tuple(  # Build one durable placeholder for each ordered request identifier.
            RunActionOutcome.pending(run_id, site_id, request.intent.action)  # Keep position and site together.
            for run_id, site_id in zip(request.intent.run_ids, request.intent.site_ids, strict=True)
        )
        lifecycle = ActionLifecycle("processing", lease, created_at, None, None)  # Start one active action lease.
        action = cls(  # Assemble the five cohesive action records.
            ActionBinding(ActionKey(document_key, action_id, 1), request.identity),  # Bind keys to safe identity.
            request.source,  # Preserve source-specific null rules.
            request.intent,  # Preserve exact ordered request values.
            lifecycle,  # Preserve processing state and lease.
            ActionLedger(items, ()),  # Start with no durable site block.
        )
        logger.debug("Built one durable action with %s item(s)", len(items))  # Report a safe count.
        return action  # Give persistence one fully validated record.

    def with_item(self, item: RunActionOutcome) -> Self:
        """Return the action with exactly one item replaced in place."""
        positions = [
            index
            for index, current in enumerate(self.ledger.items)
            if current.identity.source_run_id == item.identity.source_run_id
        ]
        if len(positions) != 1:  # One requested run must own exactly one durable item.
            raise ValueError("The action does not contain exactly one matching item.")  # Refuse a wrong update.
        items = list(self.ledger.items)  # Build a changed copy and keep the stored order.
        items[positions[0]] = item  # Replace only the matching outcome.
        ledger = replace(self.ledger, items=tuple(items))  # Freeze the changed ordered item list.
        lifecycle = self.lifecycle  # Preserve the parent evidence digest for an item without evidence.
        if item.evidence_summary is not None:  # Bind a reconciliation summary in this same immutable change.
            digest = evidence_summary_digest(item.evidence_summary)  # Verify the canonical safe proof.
            lifecycle = replace(lifecycle, evidence_summary_digest=digest)  # Store the matching parent digest.
        return replace(self, ledger=ledger, lifecycle=lifecycle)  # Keep the record immutable and valid.

    def with_lease(self, lease: ActionLease) -> Self:
        """Return the processing action with a new action lease."""
        if self.lifecycle.status != "processing":  # A complete action cannot return to processing.
            raise ValueError("A complete action cannot receive a processing lease.")  # Preserve finality.
        return replace(self, lifecycle=replace(self.lifecycle, lease=lease))  # Keep every other field stable.

    def with_site_block(self, site_id: str, reason: str) -> Self:
        """Return the action with one durable site stop reason."""
        blocks = self.ledger.block_map()  # Build a changed copy of the immutable site map.
        existing = blocks.get(site_id)  # Preserve the first guard failure for the audit.
        if existing is not None and existing != reason:  # A second reason must not rewrite history.
            raise ValueError("The action already has a different site block.")  # Keep the first stop reason.
        blocks[site_id] = reason  # Store the durable site stop decision.
        ordered = tuple(sorted(blocks.items()))  # Keep serialization stable across workers.
        return replace(self, ledger=replace(self.ledger, site_blocks=ordered))  # Keep all outcomes unchanged.

    def completed(self, completed_at: str) -> Self:
        """Return this action as complete when every item is final."""
        if any(item.claim.processing_state != "final" for item in self.ledger.items):
            raise ValueError("The action cannot complete before every item is final.")  # Refuse partial success.
        lifecycle = replace(self.lifecycle, status="complete", completed_at=completed_at)  # Store completion.
        return replace(self, lifecycle=lifecycle)  # Preserve every request and outcome field.

    def with_evidence_digest(self, digest: str | None) -> Self:
        """Return this action with the matching safe evidence digest."""
        lifecycle = replace(self.lifecycle, evidence_summary_digest=digest)  # Store proof with the outcome write.
        return replace(self, lifecycle=lifecycle)  # Preserve all other durable action values.

    def item(self, run_id: str) -> RunActionOutcome:
        """Return the one durable item for a requested run."""
        matches = tuple(item for item in self.ledger.items if item.identity.source_run_id == run_id)  # Find one.
        if len(matches) != 1:  # A request identifier must never own zero or two outcomes.
            raise ValueError("The action does not contain exactly one requested run.")  # Refuse unsafe work.
        return matches[0]  # Give the caller the immutable item.

    def document(self) -> dict[str, Any]:
        """Return the complete flat ArangoDB document."""
        document = self._binding_document()  # Start with the composite key and safe request digests.
        document.update(self._request_document())  # Add source-specific fields and authoritative counts.
        document.update(self._state_document())  # Add lifecycle, outcomes, and durable site blocks.
        return document  # Match the approved UpgradeRunAction data model exactly.

    def _binding_document(self) -> dict[str, Any]:
        """Return action keys and safe request binding fields."""
        return {  # Keep the binding fields flat for ArangoDB indexes.
            "_key": self.key.document_key,  # Use the composite domain digest.
            "action_id": self.key.action_id,  # Store the opaque public identifier.
            "schema_version": self.key.schema_version,  # Store schema version one.
            "actor_scope": self.identity.actor_scope,  # Store only the safe actor digest.
            "idempotency_key_digest": self.identity.idempotency_key_digest,  # Store no raw request key.
            "request_digest": self.identity.request_digest,  # Bind source-specific request content.
            "confirmation_digest": self.identity.confirmation_digest,  # Store no typed phrase.
        }

    def _request_document(self) -> dict[str, Any]:
        """Return source-specific request fields and exact counts."""
        return {  # Keep source and intent fields flat for stable storage.
            "source_kind": self.source.source_kind,  # Store bulk or reconciliation.
            "preview_id": self.source.preview_id,  # Store the bulk preview identifier, or null.
            "preview_digest": self.source.preview_digest,  # Store the bulk preview digest, or null.
            "organization_id": self.source.organization_id,  # Store the current organization scope.
            "history_scope": self.source.history_scope,  # Store the bulk history scope, or null.
            "action": self.intent.action,  # Store cancel, retry, or reconcile.
            "run_count": len(self.intent.run_ids),  # Store the exact requested count.
            "site_count": self.intent.site_count,  # Store the authoritative site count.
        }

    def _state_document(self) -> dict[str, Any]:
        """Return lifecycle, ordered outcome, and site block fields."""
        return {  # Keep state fields flat for one document replacement.
            "status": self.lifecycle.status,  # Store processing or complete.
            "items": [item.document() for item in self.ledger.items],  # Preserve ordered durable outcomes.
            "site_blocks": self.ledger.block_map(),  # Preserve durable site stop decisions.
            "created_at": self.lifecycle.created_at,  # Store the action creation time.
            "processing_expires_at": self.lifecycle.lease.expires_at,  # Store the action lease end.
            "processing_owner": self.lifecycle.lease.owner,  # Store only the opaque worker owner.
            "completed_at": self.lifecycle.completed_at,  # Store the completion time, or null.
            "evidence_summary_digest": self.lifecycle.evidence_summary_digest,  # Bind safe reconciliation proof.
        }

    def response(self) -> dict[str, Any]:
        """Return the stable safe action response."""
        counts = {name: 0 for name in ("succeeded", "refused", "failed", "unknown")}  # Start fixed class counts.
        for item in self.ledger.items:  # Count each requested run exactly once.
            counts[item.completion.classification] += 1  # Use the validated closed classification set.
        return {  # Expose no actor scope, request digest, worker owner, or internal key.
            "action_id": self.key.action_id,  # Return the opaque public identifier.
            "action": self.intent.action,  # Return the requested action name.
            "status": self.lifecycle.status,  # Return processing or complete.
            "run_count": len(self.intent.run_ids),  # Return the exact requested count.
            "site_count": self.intent.site_count,  # Return the authoritative site count.
            "evidence_summary_digest": self.lifecycle.evidence_summary_digest,  # Return only the safe digest.
            "counts": counts,  # Return one total for each stable classification.
            "items": [item.response() for item in self.ledger.items],  # Preserve request order.
        }

    @classmethod
    def from_document(cls, document: Mapping[str, Any]) -> Self:
        """Build one validated immutable action from an ArangoDB document."""
        binding = cls._binding_from_document(document)  # Restore keys and safe request identity.
        source = cls._source_from_document(document)  # Restore source-specific values and null rules.
        item_documents = document.get("items", ())  # Read the ordered stored outcome list.
        items = tuple(RunActionOutcome.from_document(item) for item in item_documents)  # Validate every outcome.
        intent = cls._intent_from_document(document, items)  # Restore ordered request values.
        lifecycle = cls._lifecycle_from_document(document)  # Restore status, lease, times, and evidence.
        blocks = document.get("site_blocks", {})  # Read durable site stop decisions.
        ledger = ActionLedger(items, tuple(sorted(dict(blocks).items())))  # Freeze the stable block map.
        action = cls(binding, source, intent, lifecycle, ledger)  # Validate all cross-field rules.
        if int(document["run_count"]) != len(items):  # The stored count must match its ordered item list.
            raise ValueError("The action run count does not match its item list.")  # Refuse a corrupt record.
        return action  # Give callers one immutable verified model.

    @staticmethod
    def _binding_from_document(document: Mapping[str, Any]) -> ActionBinding:
        """Return action keys and safe request identity from storage."""
        identity = ActionIdentity(  # Restore only safe request binding values.
            str(document["actor_scope"]),  # Restore the durable actor digest.
            str(document["idempotency_key_digest"]),  # Restore the request key digest.
            str(document["request_digest"]),  # Restore the request content digest.
            str(document["confirmation_digest"]),  # Restore the typed phrase digest.
        )
        key = ActionKey(str(document["_key"]), str(document["action_id"]), int(document["schema_version"]))
        return ActionBinding(key, identity)  # Keep keys and safe request digests together.

    @staticmethod
    def _source_from_document(document: Mapping[str, Any]) -> ActionSource:
        """Return validated source-specific fields from storage."""
        return ActionSource(  # Restore source-specific fields and enforce null rules.
            str(document["source_kind"]),  # Restore bulk or reconciliation.
            document.get("preview_id"),  # Restore the preview identifier, or null.
            document.get("preview_digest"),  # Restore the preview digest, or null.
            str(document["organization_id"]),  # Restore the organization scope.
            document.get("history_scope"),  # Restore the history scope, or null.
        )

    @staticmethod
    def _intent_from_document(document: Mapping[str, Any], items: tuple[RunActionOutcome, ...]) -> ActionIntent:
        """Return ordered action intent from stored outcomes."""
        return ActionIntent(  # Rebuild the ordered action intent from durable items.
            str(document["action"]),  # Restore the action name.
            tuple(item.identity.source_run_id for item in items),  # Preserve stored outcome order.
            tuple(item.identity.site_id for item in items),  # Preserve the matching site order.
            int(document["site_count"]),  # Restore the authoritative site count.
        )

    @staticmethod
    def _lifecycle_from_document(document: Mapping[str, Any]) -> ActionLifecycle:
        """Return validated action lifecycle fields from storage."""
        lease = ActionLease(str(document["processing_owner"]), str(document["processing_expires_at"]))  # Restore lease.
        return ActionLifecycle(  # Restore status, times, and safe evidence digest.
            str(document["status"]),  # Restore processing or complete.
            lease,  # Keep owner and expiry together.
            str(document["created_at"]),  # Restore the creation time.
            document.get("completed_at"),  # Restore the completion time, or null.
            document.get("evidence_summary_digest"),  # Restore the safe evidence digest, or null.
        )

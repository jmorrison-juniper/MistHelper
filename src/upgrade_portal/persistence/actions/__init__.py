"""Publish the durable upgrade run action persistence API."""

from .models import (  # Export immutable action and outcome records.
    ActionBinding,
    ActionIdentity,
    ActionInitialization,
    ActionIntent,
    ActionLease,
    ActionLifecycle,
    ActionSource,
    DurableActorScope,
    OutcomeClaim,
    OutcomeCompletion,
    OutcomeIdentity,
    OutcomeState,
    RunActionOutcome,
    UpgradeRunAction,
    canonical_digest,
    evidence_summary_digest,
)
from .replay import ActionReplayService, RecoveryDecision, ReplayRequest  # Export replay and recovery behavior.
from .repository import (  # Export the ArangoDB-only action repository and stable errors.
    ACTION_COLLECTION,
    RUN_COLLECTION,
    ActionRepository,
    ActionRequestConflict,
    ActionStateConflict,
    ActionStoreError,
    ActionStoreUnavailable,
)
from .transactions import (  # Export the explicit transaction seam and mutation values.
    ArangoTransactionAdapter,
    AtomicWriteResult,
    RunMutation,
    TransactionScope,
)

__all__ = [  # Keep the planned persistence package surface explicit.
    "ACTION_COLLECTION",  # Publish the approved action collection name.
    "RUN_COLLECTION",  # Publish the authoritative run collection name.
    "ActionBinding",  # Publish cohesive action key and identity values.
    "ActionIdentity",  # Publish safe request binding values.
    "ActionInitialization",  # Publish the validated initialization request.
    "ActionIntent",  # Publish ordered requested run values.
    "ActionLease",  # Publish opaque action and item lease values.
    "ActionLifecycle",  # Publish action status and time values.
    "ActionReplayService",  # Publish idempotent replay and recovery.
    "ActionRepository",  # Publish the ArangoDB-only durable repository.
    "ActionRequestConflict",  # Publish the different-request conflict.
    "ActionSource",  # Publish source-specific preview rules.
    "ActionStateConflict",  # Publish compare-and-swap conflicts.
    "ActionStoreError",  # Publish the common action store error.
    "ActionStoreUnavailable",  # Publish the fail-closed unavailable error.
    "ArangoTransactionAdapter",  # Publish the production transaction adapter.
    "AtomicWriteResult",  # Publish verified atomic write values.
    "DurableActorScope",  # Publish stable durable actor scope construction.
    "OutcomeClaim",  # Publish item processing state values.
    "OutcomeCompletion",  # Publish final result values.
    "OutcomeIdentity",  # Publish stable item identity values.
    "OutcomeState",  # Publish final run state values.
    "RecoveryDecision",  # Publish one recovery processor result.
    "ReplayRequest",  # Publish one replay request value.
    "RunActionOutcome",  # Publish one immutable ordered action item.
    "RunMutation",  # Publish one atomic run write request.
    "TransactionScope",  # Publish transaction collection scope.
    "UpgradeRunAction",  # Publish one immutable durable action record.
    "canonical_digest",  # Publish stable digest construction for request fields.
    "evidence_summary_digest",  # Publish safe evidence digest validation.
]

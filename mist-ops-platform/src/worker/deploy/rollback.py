"""Rollback logic — saga pattern with compensating transactions (T049, R-08).

Implements pre-snapshot capture, sequential push with failure detection,
and compensating rollback to restore previous configs on failure.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from src.shared.mist.endpoints import MistEndpointService
from src.worker.deploy.executor import ConfigPushExecutor, PushResult

logger = logging.getLogger(__name__)


@dataclass
class RollbackState:
    """Track state for saga-pattern rollback."""

    snapshots: dict[str, dict[str, Any]] = field(default_factory=dict)
    pushed: list[dict[str, str]] = field(default_factory=list)
    rollback_results: list[PushResult] = field(default_factory=list)
    status: str = "pending"
    error: str = ""


class RollbackService:
    """Saga-pattern rollback for multi-device config changes (R-08).

    Workflow:
    1. Pre-flight: Snapshot current configs of all targets
    2. Execute: Push new config sequentially
    3. On failure: Compensate by restoring pre-change snapshots
    """

    def __init__(
        self,
        db: Session,
        mist: MistEndpointService,
    ) -> None:
        self._db = db
        self._executor = ConfigPushExecutor(db, mist)
        self._mist = mist

    def execute_with_rollback(
        self,
        entity_type: str,
        targets: list[dict[str, str]],
        new_config: dict[str, Any],
    ) -> RollbackState:
        """Push config with automatic rollback on failure.

        Returns RollbackState with final status and per-device results.
        """
        state = RollbackState()
        self._capture_snapshots(entity_type, targets, state)

        if state.status == "snapshot_failed":
            return state

        self._push_with_saga(entity_type, targets, new_config, state)
        return state

    # -- phase 1: pre-flight snapshot ------------------------------------

    def _capture_snapshots(
        self,
        entity_type: str,
        targets: list[dict[str, str]],
        state: RollbackState,
    ) -> None:
        """Read current configs from Mist for rollback capability."""
        for entity_ids in targets:
            key = _entity_key(entity_ids)
            current = self._read_current_config(entity_type, entity_ids)
            if current is None:
                state.status = "snapshot_failed"
                state.error = f"Cannot read current config for {key}"
                logger.error("Pre-flight snapshot failed: %s", key)
                return
            state.snapshots[key] = current

    def _read_current_config(
        self,
        entity_type: str,
        entity_ids: dict[str, str],
    ) -> dict[str, Any] | None:
        """Fetch the live config from Mist API."""
        from src.shared.mist.types import ENTITY_ENDPOINT_MAP

        endpoint = ENTITY_ENDPOINT_MAP.get(entity_type)
        if endpoint is None:
            return None

        result = self._mist.read_entity(
            api_module=endpoint.api_module,
            read_method=endpoint.read_method,
            ids=entity_ids,
        )
        if result.success and isinstance(result.data, dict):
            return result.data
        return None

    # -- phase 2: push with saga ----------------------------------------

    def _push_with_saga(
        self,
        entity_type: str,
        targets: list[dict[str, str]],
        new_config: dict[str, Any],
        state: RollbackState,
    ) -> None:
        """Push sequentially; rollback on first failure."""
        for entity_ids in targets:
            result = self._executor.push_revision(
                entity_type, entity_ids, new_config,
            )
            if result.success:
                state.pushed.append(entity_ids)
            else:
                state.error = result.error
                self._compensate(entity_type, state)
                return

        state.status = "completed"

    # -- phase 3: compensating transactions ------------------------------

    def _compensate(
        self,
        entity_type: str,
        state: RollbackState,
    ) -> None:
        """Restore pre-change configs for all previously pushed devices."""
        logger.warning(
            "Rolling back %d devices due to push failure",
            len(state.pushed),
        )
        all_restored = True
        for entity_ids in reversed(state.pushed):
            key = _entity_key(entity_ids)
            snapshot = state.snapshots.get(key)
            if snapshot is None:
                logger.error("No snapshot for rollback: %s", key)
                all_restored = False
                continue

            result = self._executor.push_revision(
                entity_type, entity_ids, snapshot,
            )
            state.rollback_results.append(result)
            if not result.success:
                logger.error("Rollback push failed for %s", key)
                all_restored = False

        state.status = "rolled_back" if all_restored else "partial_rollback"


def _entity_key(ids: dict[str, str]) -> str:
    """Create a stable string key from entity IDs dict."""
    return "|".join(f"{k}={v}" for k, v in sorted(ids.items()))

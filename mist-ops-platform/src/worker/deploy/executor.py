"""Config push executor — install-from-revision via Mist API (T048, R-05).

Pushes a stored config revision back to the target entity using the
appropriate Mist API write endpoint.  Records the push as an audit event.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from src.shared.mist.endpoints import MistEndpointService
from src.shared.mist.types import ENTITY_ENDPOINT_MAP

logger = logging.getLogger(__name__)

# WHY: ordered from the most specific entity to the least, so the push record
# names the device when the caller supplies one.
_ENTITY_ID_KEYS = ("device_id", "wlan_id", "network_id", "site_id")


@dataclass(frozen=True)
class PushResult:
    """Result of a single config push operation."""

    entity_id: UUID
    entity_type: str
    success: bool
    status_code: int = 0
    error: str = ""


@dataclass
class BatchPushResult:
    """Aggregate result for multi-device push."""

    results: list[PushResult] = field(default_factory=list)
    total: int = 0
    succeeded: int = 0
    failed: int = 0


class ConfigPushExecutor:
    """Push stored config revisions to Mist devices (R-05).

    Uses the entity-type-to-endpoint mapping to resolve the
    correct Mist API write method for each entity type.
    """

    def __init__(
        self,
        db: Session,
        mist: MistEndpointService,
    ) -> None:
        self._db = db
        self._mist = mist

    def push_revision(
        self,
        entity_type: str,
        entity_ids: dict[str, str],
        config_payload: dict[str, Any],
    ) -> PushResult:
        """Push a config payload to a single entity.

        Args:
            entity_type: Type key (e.g., 'device', 'site_setting')
            entity_ids: ID params for the API call (site_id, device_id, etc.)
            config_payload: Full JSON config to push

        Returns:
            PushResult with success/failure status.
        """
        endpoint = ENTITY_ENDPOINT_MAP.get(entity_type)
        if endpoint is None:
            logger.error(  # WHY: the caller reads the result only, so the log carries the reason.
                "No write endpoint for entity type %s, so the push never ran.",
                entity_type,
            )
            return PushResult(
                # WHY: name the real device, so the record never points at a phantom.
                entity_id=_resolve_entity_uuid(entity_ids),
                entity_type=entity_type,
                success=False,
                error=f"No write endpoint for entity type: {entity_type}",
            )

        result = self._mist.write_entity(
            entity_type=entity_type,
            ids=entity_ids,
            body=config_payload,
        )

        entity_uuid = _resolve_entity_uuid(entity_ids)
        if result.success:
            logger.info(
                "Config pushed to %s %s (status=%d)",
                entity_type,
                entity_uuid,
                result.status_code,
            )
        else:
            logger.error(
                "Config push failed for %s %s: %s",
                entity_type,
                entity_uuid,
                result.error,
            )

        return PushResult(
            entity_id=entity_uuid,
            entity_type=entity_type,
            success=result.success,
            status_code=result.status_code,
            error=result.error or "",
        )

    def push_batch(
        self,
        entity_type: str,
        targets: list[dict[str, str]],
        config_payload: dict[str, Any],
    ) -> BatchPushResult:
        """Push config to multiple entities sequentially.

        Stops on first failure if stop_on_failure is desired
        (caller handles via rollback service).
        """
        batch = BatchPushResult(total=len(targets))
        for entity_ids in targets:
            result = self.push_revision(
                entity_type,
                entity_ids,
                config_payload,
            )
            batch.results.append(result)
            if result.success:
                batch.succeeded += 1
            else:
                batch.failed += 1
                break  # Saga pattern: stop on failure for rollback
        return batch


def _resolve_entity_uuid(ids: dict[str, str]) -> UUID:
    """Return the most specific entity UUID from an ID dict.

    The caller prints the result as the identity of the device in the log line
    that reports the push, so a silent substitution would name a device that
    does not exist. Every rejected value leaves a warning.
    """
    for key in _ENTITY_ID_KEYS:
        value = ids.get(key)
        if not value:
            continue  # WHY: an absent key is normal, so it needs no record.
        try:
            return UUID(value)  # WHY: the normal path reports the real device.
        except ValueError:
            logger.warning(  # WHY: issue #1924 requires a record on every recovery path.
                "Entity key %s holds %r, which is not a UUID. The push record drops it.",
                key,
                value,
            )
    return _synthetic_entity_uuid(sorted(ids))


def _synthetic_entity_uuid(keys: list[str]) -> UUID:
    """Return a fresh UUID and record that no key supplied a real one."""
    synthetic = uuid4()  # WHY: PushResult.entity_id needs a UUID the caller can store.
    logger.warning(  # WHY: without this line the push record names an unknown device.
        "No entity key in %s supplied a UUID. Identifier %s is synthetic.",
        keys,
        synthetic,
    )
    return synthetic

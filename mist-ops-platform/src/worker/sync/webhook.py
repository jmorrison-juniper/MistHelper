"""Mist webhook receiver processing logic (T043, R-02).

Mist webhooks push events in real time.  This module parses
incoming payloads and dispatches Celery tasks to capture the
changed configuration or status immediately.

Supported webhook topics:
    - ``audit`` — config changes with actor attribution
    - ``device-events`` — firmware/state changes
    - ``alarms`` — threshold violations
    - ``device-updowns`` — online/offline transitions
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any

logger = logging.getLogger(__name__)


class WebhookProcessor:
    """Parse and dispatch Mist webhook payloads."""

    SUPPORTED_TOPICS = frozenset(
        {
            "audit",
            "device-events",
            "alarms",
            "device-updowns",
        }
    )

    def __init__(self, webhook_secret: str) -> None:
        self._secret = webhook_secret

    # -- public entry point ----------------------------------------------

    def process(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Route a validated webhook payload to the right handler.

        Returns a summary dict with topic, event count, and task ids.
        """
        topic = payload.get("topic", "unknown")
        events = payload.get("events", [])

        if topic not in self.SUPPORTED_TOPICS:
            logger.warning("Ignoring unsupported webhook topic: %s", topic)
            return {"topic": topic, "status": "ignored"}

        handler = self._topic_handlers().get(topic)
        if handler is None:
            return {"topic": topic, "status": "no_handler"}

        task_ids = handler(events)
        return {"topic": topic, "events": len(events), "tasks": task_ids}

    # -- HMAC validation -------------------------------------------------

    def validate_signature(self, body: bytes, signature: str) -> bool:
        """Verify Mist webhook HMAC-SHA256 signature.

        Mist sends the signature in the ``X-Mist-Signature-v2`` header
        as a hex-encoded HMAC-SHA256 digest of the raw request body.
        """
        expected = hmac.new(
            self._secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    # -- topic handlers --------------------------------------------------

    def _topic_handlers(self) -> dict[str, Any]:
        """Map topic names to handler methods."""
        return {
            "audit": self._handle_audit,
            "device-events": self._handle_device_events,
            "alarms": self._handle_alarms,
            "device-updowns": self._handle_device_updowns,
        }

    def _handle_audit(self, events: list[dict]) -> list[str]:
        """Enqueue config sync for each changed entity."""
        from src.worker.tasks.sync_tasks import sync_org_inventory

        task_ids: list[str] = []
        org_ids = _extract_org_ids(events)
        for org_id in org_ids:
            result = sync_org_inventory.delay(org_id)
            task_ids.append(result.id)
        return task_ids

    def _handle_device_events(self, events: list[dict]) -> list[str]:
        """Enqueue status sync for affected orgs."""
        from src.worker.tasks.sync_tasks import sync_org_inventory

        task_ids: list[str] = []
        org_ids = _extract_org_ids(events)
        for org_id in org_ids:
            result = sync_org_inventory.delay(org_id)
            task_ids.append(result.id)
        return task_ids

    def _handle_alarms(self, events: list[dict]) -> list[str]:
        """Log alarms and trigger status refresh."""
        from src.worker.tasks.sync_tasks import sync_org_inventory

        task_ids: list[str] = []
        org_ids = _extract_org_ids(events)
        for org_id in org_ids:
            logger.info("Alarm received for org %s", org_id)
            result = sync_org_inventory.delay(org_id)
            task_ids.append(result.id)
        return task_ids

    def _handle_device_updowns(self, events: list[dict]) -> list[str]:
        """Trigger immediate status snapshot on up/down transitions."""
        from src.worker.tasks.sync_tasks import sync_org_inventory

        task_ids: list[str] = []
        org_ids = _extract_org_ids(events)
        for org_id in org_ids:
            result = sync_org_inventory.delay(org_id)
            task_ids.append(result.id)
        return task_ids


def _extract_org_ids(events: list[dict]) -> set[str]:
    """Deduplicate org IDs from a list of webhook events."""
    org_ids: set[str] = set()
    for event in events:
        org_id = event.get("org_id")
        if org_id:
            org_ids.add(str(org_id))
    return org_ids

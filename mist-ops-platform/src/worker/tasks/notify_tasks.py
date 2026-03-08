"""Notification dispatch Celery tasks (T028).

``send_notification`` is enqueued by services that need to alert
operators. It loads the channel from the database and delegates to
``NotificationService``.
"""

from __future__ import annotations

import logging

from src.worker.celeryconfig import app

logger = logging.getLogger(__name__)


@app.task(name="src.worker.tasks.notify_tasks.send_notification", bind=True, max_retries=3)
def send_notification(
    self,
    channel_id: str,
    alert_type: str,
    payload: dict,
) -> dict:
    """Dispatch a single notification to a channel."""
    from src.shared.services.notification import NotificationService

    # In full implementation: load channel from DB by channel_id
    # For scaffold: log and delegate to service
    logger.info(
        "Dispatching %s to channel %s",
        alert_type,
        channel_id,
    )
    service = NotificationService()
    # Placeholder — real impl loads channel_type + endpoint from DB
    success = service.dispatch(
        channel_type="webhook",
        endpoint="",
        alert_type=alert_type,
        payload=payload,
    )
    return {"channel_id": channel_id, "success": success}

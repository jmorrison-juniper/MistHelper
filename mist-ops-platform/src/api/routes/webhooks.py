"""Webhook routes — Mist event ingestion endpoint (T044).

POST /webhooks/mist  — receives Mist webhook payloads with
HMAC-SHA256 signature verification and dispatches to the
``WebhookProcessor`` for event routing.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, status

from src.shared.config.settings import get_settings
from src.worker.sync.webhook import WebhookProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post(
    "/mist",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Receive Mist webhook events",
)
async def receive_mist_webhook(request: Request) -> dict:
    """Validate HMAC signature and dispatch webhook events.

    Mist sends:
      - ``X-Mist-Signature-v2`` header (HMAC-SHA256 hex digest)
      - JSON body with ``topic`` and ``events`` fields

    Returns 202 Accepted with dispatch summary.
    """
    settings = get_settings()
    secret = settings.mist_webhook_secret

    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook secret not configured",
        )

    raw_body = await request.body()
    signature = request.headers.get("X-Mist-Signature-v2", "")

    processor = WebhookProcessor(secret)

    if not processor.validate_signature(raw_body, signature):
        logger.warning("Webhook signature validation failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    payload = await request.json()
    result = processor.process(payload)
    return {"status": "accepted", **result}

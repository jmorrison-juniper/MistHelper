"""Webhook receiver endpoint for Mist Cloud audit and stats events.

Verifies HMAC-SHA256 signatures, dispatches audit payloads to ArangoDB
config snapshots, and stats payloads to Redis TimeSeries ingestion.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any

from flask import Blueprint, current_app, jsonify, request

webhook_bp = Blueprint("webhooks", __name__)


def _verify_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 signature from X-Mist-Signature header."""
    if not secret:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _get_router() -> Any | None:
    """Retrieve DatabaseRouter from app config if available."""
    return current_app.config.get("DB_ROUTER")


@webhook_bp.route("/api/webhook", methods=["POST"])
def receive_webhook() -> tuple:
    """Receive and dispatch Mist webhook payloads."""
    secret = current_app.config.get("WEBHOOK_SECRET", "")
    signature = request.headers.get("X-Mist-Signature", "")
    body = request.get_data()

    if secret and not _verify_signature(body, signature, secret):
        logging.warning("Webhook signature verification failed")
        return jsonify({"error": "invalid signature"}), 403

    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "invalid JSON"}), 400

    topic = payload.get("topic", "")
    router = _get_router()

    if topic == "audits":
        _handle_audit(router, payload)
    elif topic in _STATS_TOPICS:
        _handle_stats(router, payload)
    else:
        logging.debug("Unhandled webhook topic: %s", topic)

    return jsonify({"status": "ok"}), 200


_STATS_TOPICS = {
    "client-sessions",
    "device-updowns",
    "device-events",
    "client-latency",
}


def _handle_audit(router: Any | None, payload: dict) -> None:
    """Dispatch audit events to config snapshot handler."""
    if router is None:
        return
    events = payload.get("events", [payload])
    for event in events:
        try:
            router.handle_webhook_audit(event)
        except Exception as error:
            logging.warning("Audit snapshot failed: %s", error)


def _handle_stats(router: Any | None, payload: dict) -> None:
    """Dispatch stats events to Redis TimeSeries ingestion."""
    if router is None:
        return
    topic = payload.get("topic", "")
    events = payload.get("events", [])
    try:
        redis_writer = getattr(router, "_redis_writer", None)
        if redis_writer is not None and hasattr(redis_writer, "ingest_webhook"):
            redis_writer.ingest_webhook(events, topic)
    except Exception as error:
        logging.warning("Stats ingestion failed for %s: %s", topic, error)

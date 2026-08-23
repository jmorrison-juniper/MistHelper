"""Webhook receiver endpoint for Mist Cloud audit and stats events.

The route verifies an HMAC-SHA256 signature on every request before it
dispatches a payload. Audit payloads reach the ArangoDB config snapshot
handler. Stats payloads reach the Redis TimeSeries ingestion handler.

The route fails closed. If the shared secret is absent, the route
rejects every request with code 503, and no payload reaches the
dispatch path. An unset secret never means "accept every caller".
See issue #1907.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any

from flask import Blueprint, current_app, jsonify, request

webhook_bp = Blueprint("webhooks", __name__)

# WHY: one name for the config key stops a typo from disabling the check.
# The nosec below marks a bandit false positive. The string is a Flask
# config key name, not a credential. See B105.
WEBHOOK_SECRET_CONFIG_KEY = "WEBHOOK_SECRET"  # nosec B105

# WHY: one name for the on/off key keeps the factory and the tests in step.
WEBHOOK_ENABLED_CONFIG_KEY = "WEBHOOK_ENABLED"

# WHY: Mist Cloud sends the HMAC-SHA256 hex digest in this header.
SIGNATURE_HEADER = "X-Mist-Signature"

# WHY: these topics carry metrics, so they reach the time-series handler.
_STATS_TOPICS = {
    "client-sessions",
    "device-updowns",
    "device-events",
    "client-latency",
}


def _verify_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify the HMAC-SHA256 signature from the X-Mist-Signature header."""
    if not secret:
        return False  # WHY: an empty secret authenticates nobody, so refuse it.
    if not signature:
        return False  # WHY: an absent header can never match a computed digest.
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()  # WHY: recompute from the raw body.
    return hmac.compare_digest(expected, signature)  # WHY: constant time stops a byte-by-byte digest leak.


def _get_router() -> Any | None:
    """Retrieve DatabaseRouter from app config if available."""
    return current_app.config.get("DB_ROUTER")


def _get_configured_secret() -> str:
    """Return the configured shared secret, or an empty string."""
    raw = current_app.config.get(WEBHOOK_SECRET_CONFIG_KEY, "")  # WHY: an absent key must read as unconfigured.
    return str(raw or "").strip()  # WHY: a whitespace-only value is not a usable secret.


def _reject_unverified_request() -> tuple | None:
    """Return a rejection response when the request is not authentic.

    The function returns None only when the signature matches the raw
    request body. Every other outcome is a rejection.
    """
    secret = _get_configured_secret()
    if not secret:
        logging.error(
            "Webhook rejected: %s is not configured, so the portal cannot identify the sender",
            WEBHOOK_SECRET_CONFIG_KEY,
        )  # WHY: an operator needs a clear cause for every 503 reply.
        return jsonify({"error": "webhook receiver is not configured"}), 503
    body = request.get_data()  # WHY: the digest covers the raw bytes, not the parsed JSON.
    logging.info("Verifying the webhook signature for a body of %d bytes", len(body))
    if not _verify_signature(body, request.headers.get(SIGNATURE_HEADER, ""), secret):
        logging.warning("Webhook rejected: the signature does not match the body")
        return jsonify({"error": "invalid signature"}), 403
    logging.debug("Webhook signature verified for a body of %d bytes", len(body))
    return None


@webhook_bp.route("/api/webhook", methods=["POST"])
def receive_webhook() -> tuple:
    """Receive and dispatch Mist webhook payloads."""
    rejection = _reject_unverified_request()  # WHY: verify first, so no forged body reaches a handler.
    if rejection is not None:
        return rejection
    payload = request.get_json(silent=True)  # WHY: parse only after the body proves authentic.
    if not payload:
        logging.warning("Webhook rejected: the signed body is not valid JSON")
        return jsonify({"error": "invalid JSON"}), 400
    _dispatch_payload(payload)
    return jsonify({"status": "ok"}), 200


def _dispatch_payload(payload: dict) -> None:
    """Send one verified payload to the handler that matches its topic."""
    topic = payload.get("topic", "")
    router = _get_router()
    logging.info("Dispatching a verified webhook payload for topic '%s'", topic)
    if topic == "audits":
        _handle_audit(router, payload)
    elif topic in _STATS_TOPICS:
        _handle_stats(router, payload)
    else:
        logging.debug("Unhandled webhook topic: %s", topic)
    logging.debug("Dispatch complete for topic '%s'", topic)


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

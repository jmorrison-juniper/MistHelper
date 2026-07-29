"""Notification dispatch service with channel adapters (T027, R-12).

``NotificationService`` routes alerts to the correct adapter
(email via SMTP or webhook via httpx) based on channel type.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class EmailAdapter:
    """Send notifications via SMTP (stdlib)."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 587,
        username: str = "",
        password: str = "",  # nosec B107 - The empty string is a "not provided" sentinel.
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password

    def send(
        self,
        destination: str,
        subject: str,
        body: str,
    ) -> bool:
        """Deliver an email notification; return True on success."""
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["To"] = destination
        msg["From"] = self._username or "noreply@mistops.local"
        msg.set_content(body)
        try:
            with smtplib.SMTP(self._host, self._port) as server:
                if self._username:
                    server.starttls()
                    server.login(self._username, self._password)
                server.send_message(msg)
            return True
        except Exception:
            logger.exception("Email send failed to %s", destination)
            return False


class WebhookAdapter:
    """Send notifications via HTTP POST (httpx)."""

    def send(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> bool:
        """POST payload to *url*; return True on 2xx response."""
        try:
            response = httpx.post(
                url,
                json=payload,
                headers=headers or {},
                timeout=10.0,
            )
            return response.is_success
        except Exception:
            logger.exception("Webhook POST failed to %s", url)
            return False


class NotificationService:
    """Route alerts to subscribed channels via adapters."""

    def __init__(self) -> None:
        self._email = EmailAdapter()
        self._webhook = WebhookAdapter()

    def dispatch(
        self,
        channel_type: str,
        endpoint: str,
        alert_type: str,
        payload: dict[str, Any],
    ) -> bool:
        """Send notification to the appropriate adapter."""
        if channel_type == "email":
            subject = f"[MistOps] {alert_type}"
            body = str(payload)
            return self._email.send(endpoint, subject, body)

        if channel_type == "webhook":
            envelope = {"alert_type": alert_type, **payload}
            return self._webhook.send(endpoint, envelope)

        logger.warning("Unknown channel type: %s", channel_type)
        return False

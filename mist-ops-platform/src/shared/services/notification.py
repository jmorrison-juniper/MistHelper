"""Notification dispatch service with channel adapters (T027, R-12).

``NotificationService`` routes alerts to the correct adapter
(email via SMTP or webhook via httpx) based on channel type.
"""

from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# The stdlib default for smtplib.SMTP is unbounded, so a silent mail host
# holds a Celery worker thread forever. Ten seconds matches the timeout that
# the webhook adapter below already uses.
DEFAULT_SMTP_TIMEOUT_SECONDS = 10.0

# An operator tunes a slow relay through this environment variable, so a
# change needs no new image and no code edit.
SMTP_TIMEOUT_ENV_VAR = "SMTP_TIMEOUT_SECONDS"


def _read_smtp_timeout() -> float:
    """Return the SMTP timeout in seconds from the environment."""
    raw = os.getenv(SMTP_TIMEOUT_ENV_VAR, "").strip()  # WHY: an unset variable reads as "".
    if not raw:
        return DEFAULT_SMTP_TIMEOUT_SECONDS  # WHY: no override keeps the documented default.
    try:
        seconds = float(raw)  # WHY: the environment holds text, and the socket needs a number.
    except ValueError:
        logger.warning(
            "Invalid %s value '%s'. Using %.1f seconds.",
            SMTP_TIMEOUT_ENV_VAR,
            raw,
            DEFAULT_SMTP_TIMEOUT_SECONDS,
        )
        return DEFAULT_SMTP_TIMEOUT_SECONDS
    if seconds <= 0:
        # WHY: zero or less makes the socket non-blocking, which breaks every send.
        logger.warning(
            "The %s value must be above zero. Using %.1f seconds.",
            SMTP_TIMEOUT_ENV_VAR,
            DEFAULT_SMTP_TIMEOUT_SECONDS,
        )
        return DEFAULT_SMTP_TIMEOUT_SECONDS
    return seconds


class EmailAdapter:
    """Send notifications via SMTP (stdlib)."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 587,
        username: str = "",
        password: str = "",  # nosec B107 - The empty string is a "not provided" sentinel.
        *,
        timeout: float | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        # WHY: a caller can set the limit, and the environment supplies the rest.
        self._timeout = timeout if timeout is not None else _read_smtp_timeout()

    def send(
        self,
        destination: str,
        subject: str,
        body: str,
    ) -> bool:
        """Deliver an email notification; return True on success."""
        msg = self._build_message(destination, subject, body)
        logger.info(
            "Sending an email alert to %s through %s:%s",
            destination,
            self._host,
            self._port,
        )
        try:
            # WHY: the timeout bounds the connect, so a silent host cannot hold the worker.
            with smtplib.SMTP(self._host, self._port, timeout=self._timeout) as server:
                self._start_session(server)  # WHY: TLS and login run only with a username.
                server.send_message(msg)
        except TimeoutError:
            # WHY: the operator needs the host, the port, and the limit to tune the relay.
            logger.error(
                "Email to %s timed out on %s:%s after %s seconds",
                destination,
                self._host,
                self._port,
                self._timeout,
            )
            return False
        except Exception:
            logger.exception("Email send failed to %s", destination)
            return False
        logger.debug("Email alert delivered to %s", destination)
        return True

    def _build_message(
        self,
        destination: str,
        subject: str,
        body: str,
    ) -> EmailMessage:
        """Assemble the message the SMTP session sends."""
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["To"] = destination
        msg["From"] = self._username or "noreply@mistops.local"
        msg.set_content(body)
        return msg

    def _start_session(self, server: Any) -> None:
        """Upgrade to TLS and authenticate when a username exists."""
        if not self._username:
            return  # WHY: an open relay in a lab needs no login.
        server.starttls()  # WHY: the password must not cross the network in clear text.
        server.login(self._username, self._password)


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

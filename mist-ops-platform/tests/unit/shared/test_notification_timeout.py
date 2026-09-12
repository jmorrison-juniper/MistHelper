"""Tests that the SMTP adapter bounds its connect time (issue #1909).

``smtplib.SMTP`` waits without a limit when the caller passes no
``timeout`` argument. A mail host that drops packets then holds a Celery
worker thread forever. These tests prove that the adapter passes an
explicit timeout and reports a timeout as a clean failure.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

from src.shared.services import notification

if TYPE_CHECKING:
    # WHY: this module reads pytest names in annotations only.
    import pytest

_TEST_HOST = "mail.example.net"
_TEST_PORT = 2525
_CUSTOM_TIMEOUT_SECONDS = 2.5
_ENVIRONMENT_TIMEOUT_SECONDS = 4.0
_DESTINATION = "noc@example.net"


def _make_adapter(**kwargs: Any) -> notification.EmailAdapter:
    """Build an adapter that points at the test mail host."""
    # WHY: a fixed host and port let the log assertions match exact text.
    return notification.EmailAdapter(
        host=_TEST_HOST,
        port=_TEST_PORT,
        **kwargs,
    )


def _install_fake_smtp(
    monkeypatch: pytest.MonkeyPatch,
    error: Exception | None = None,
) -> dict[str, Any]:
    """Replace smtplib.SMTP and return the captured constructor arguments."""
    captured: dict[str, Any] = {}

    class _FakeSMTP:
        """Record the constructor arguments and simulate one session."""

        def __init__(self, host: str, port: int, **kwargs: Any) -> None:
            captured["host"] = host  # WHY: the test asserts the target host.
            captured["port"] = port  # WHY: the test asserts the target port.
            captured.update(kwargs)  # WHY: the timeout arrives as a keyword.
            if error is not None:
                # WHY: a silent mail host raises during the connect call.
                raise error

        def __enter__(self) -> _FakeSMTP:
            return self

        def __exit__(self, *_exc_info: Any) -> bool:
            return False

        def starttls(self) -> None:
            """Accept the TLS upgrade without a network call."""

        def login(self, *_args: Any) -> None:
            """Accept the credentials without a network call."""

        def send_message(self, _message: Any) -> None:
            """Accept the message without a network call."""

    # WHY: the adapter reads smtplib.SMTP at call time, so patch the attribute.
    monkeypatch.setattr(notification.smtplib, "SMTP", _FakeSMTP)
    return captured


class TestEmailAdapterTimeout:
    """The SMTP connect must carry an explicit and tunable timeout."""

    def test_connect_passes_a_timeout(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured = _install_fake_smtp(monkeypatch)

        assert _make_adapter().send(_DESTINATION, "subject", "body") is True

        assert "timeout" in captured
        assert captured["timeout"] == notification.DEFAULT_SMTP_TIMEOUT_SECONDS
        assert captured["timeout"] > 0

    def test_constructor_timeout_wins(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured = _install_fake_smtp(monkeypatch)

        adapter = _make_adapter(timeout=_CUSTOM_TIMEOUT_SECONDS)
        adapter.send(_DESTINATION, "subject", "body")

        assert captured["timeout"] == _CUSTOM_TIMEOUT_SECONDS

    def test_environment_variable_tunes_the_default(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured = _install_fake_smtp(monkeypatch)
        monkeypatch.setenv(
            notification.SMTP_TIMEOUT_ENV_VAR,
            str(_ENVIRONMENT_TIMEOUT_SECONDS),
        )

        _make_adapter().send(_DESTINATION, "subject", "body")

        assert captured["timeout"] == _ENVIRONMENT_TIMEOUT_SECONDS

    def test_invalid_environment_value_keeps_the_default(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured = _install_fake_smtp(monkeypatch)
        # WHY: an operator can type a word or a negative number by mistake.
        monkeypatch.setenv(notification.SMTP_TIMEOUT_ENV_VAR, "soon")

        _make_adapter().send(_DESTINATION, "subject", "body")

        assert captured["timeout"] == notification.DEFAULT_SMTP_TIMEOUT_SECONDS


class TestEmailAdapterTimeoutFailure:
    """A stalled mail host must produce a clean failure and a clear log."""

    def test_timeout_returns_false(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _install_fake_smtp(monkeypatch, error=TimeoutError("timed out"))

        result = _make_adapter().send(_DESTINATION, "subject", "body")

        assert result is False

    def test_timeout_logs_host_port_and_limit(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        _install_fake_smtp(monkeypatch, error=TimeoutError("timed out"))
        caplog.set_level(logging.ERROR, logger=notification.logger.name)

        _make_adapter(timeout=_CUSTOM_TIMEOUT_SECONDS).send(
            _DESTINATION,
            "subject",
            "body",
        )

        errors = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert errors, "the timeout must report at ERROR level"
        message = errors[0].getMessage()
        assert _TEST_HOST in message
        assert str(_TEST_PORT) in message
        assert str(_CUSTOM_TIMEOUT_SECONDS) in message


class TestWebhookAdapterTimeout:
    """The webhook POST must keep its explicit timeout."""

    def test_post_passes_a_timeout(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        post = MagicMock(name="httpx_post")
        post.return_value = MagicMock(is_success=True)
        monkeypatch.setattr(notification.httpx, "post", post)

        assert notification.WebhookAdapter().send("https://hook", {}) is True

        assert post.call_args.kwargs["timeout"] > 0

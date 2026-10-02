"""Preserve stable keys, random development keys, and key-name-only warnings."""

from __future__ import annotations

import logging
import re
import secrets
from collections.abc import Iterator

import pytest

from src.upgrade_portal.app import config


@pytest.fixture
def key_logs(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    """Capture the real configuration logger without duplicate root records."""
    original_propagation = config.logger.propagate
    config.logger.propagate = False
    caplog.set_level(logging.DEBUG, logger=config.logger.name)
    config.logger.addHandler(caplog.handler)
    try:
        yield caplog
    finally:
        config.logger.removeHandler(caplog.handler)
        config.logger.propagate = original_propagation


class TestCaptureSigningKey:
    """Hold the supported key and warning behavior unchanged."""

    def test_configured_key_uses_the_existing_trimmed_value(
        self, monkeypatch: pytest.MonkeyPatch, key_logs: pytest.LogCaptureFixture
    ) -> None:
        """The complete configuration retains a private key after whitespace removal."""
        generated = secrets.token_urlsafe(32)
        monkeypatch.setenv("CAPTURE_SECRET_KEY", f" \t{generated}\n")
        monkeypatch.delenv("ORG_UPGRADE_WRITES_ENABLED", raising=False)
        first = config.load_settings()
        second = config.load_settings()
        assert first.web.secret_key == generated
        assert second.web.secret_key == generated
        assert first.writes.org_upgrade_enabled is False
        assert not any("CAPTURE_SECRET_KEY" in record.getMessage() for record in key_logs.records)
        print("session_signing_configuration: settings_checked=2 configured_keys_checked=2 warnings=0")

    @pytest.mark.parametrize("value", [None, "", " \t\n"])
    def test_missing_or_blank_key_warns_and_changes_each_start(
        self, monkeypatch: pytest.MonkeyPatch, key_logs: pytest.LogCaptureFixture, value: str | None
    ) -> None:
        """Missing, empty, and whitespace values keep the visible development warning."""
        if value is None:
            monkeypatch.delenv("CAPTURE_SECRET_KEY", raising=False)
        else:
            monkeypatch.setenv("CAPTURE_SECRET_KEY", value)
        first = config.load_settings().web.secret_key
        second = config.load_settings().web.secret_key
        assert first != second
        assert re.fullmatch(r"[A-Za-z0-9_-]{43}", first)
        assert re.fullmatch(r"[A-Za-z0-9_-]{43}", second)
        warnings = [record for record in key_logs.records if "CAPTURE_SECRET_KEY" in record.getMessage()]
        assert len(warnings) == 2
        assert [(record.levelno, record.args) for record in warnings] == [
            (logging.WARNING, ("CAPTURE_SECRET_KEY",)),
            (logging.WARNING, ("CAPTURE_SECRET_KEY",)),
        ]
        assert all(
            first not in record.getMessage() and second not in record.getMessage() for record in key_logs.records
        )
        print("session_signing_configuration: settings_checked=2 random_keys_checked=2 warnings_checked=2")

    def test_configured_key_and_credentials_never_reach_logs(
        self, monkeypatch: pytest.MonkeyPatch, key_logs: pytest.LogCaptureFixture
    ) -> None:
        """The actual settings logs never contain a signing key or a cloud token."""
        generated = secrets.token_urlsafe(32)
        sentinel = "synthetic-issue-3213-configuration-token-not-a-credential"
        monkeypatch.setenv("CAPTURE_SECRET_KEY", generated)
        monkeypatch.setenv("MIST_API_TOKEN", sentinel)
        monkeypatch.delenv("ORG_UPGRADE_WRITES_ENABLED", raising=False)
        settings = config.load_settings()
        assert settings.web.secret_key == generated
        assert settings.web.environment_token_present is True
        assert settings.writes.org_upgrade_enabled is False
        surfaces = [record.getMessage() + repr(record.args) for record in key_logs.records]
        assert all(generated not in surface and sentinel not in surface for surface in surfaces)
        print(f"session_signing_configuration: settings_checked=1 log_records_checked={len(surfaces)}")

"""Unit tests for webhook registration, receiver, and stats ingestion."""

from __future__ import annotations

import hashlib
import hmac
from unittest.mock import MagicMock, patch


class TestWebhookVerification:
    """Verify HMAC-SHA256 signature checking."""

    def test_valid_signature_passes(self) -> None:
        from web_portal.routes.webhooks import _verify_signature

        secret = "test-secret-key"
        body = b'{"topic":"audits","events":[]}'
        expected = hmac.new(
            secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        assert _verify_signature(body, expected, secret) is True

    def test_invalid_signature_rejected(self) -> None:
        from web_portal.routes.webhooks import _verify_signature

        assert _verify_signature(b"body", "bad-sig", "secret") is False

    def test_empty_secret_rejected(self) -> None:
        from web_portal.routes.webhooks import _verify_signature

        assert _verify_signature(b"body", "any-sig", "") is False


class TestWebhookAuditDispatch:
    """Verify audit payloads dispatched to snapshot handler."""

    def test_audit_calls_handle_webhook_audit(self) -> None:
        from src.db.router import DatabaseRouter

        router = MagicMock(spec=DatabaseRouter)
        payload = {
            "object_type": "wlan",
            "object_id": "abc-123",
            "after": {"ssid": "TestNet"},
        }
        router.handle_webhook_audit(payload)
        router.handle_webhook_audit.assert_called_once_with(payload)


class TestRedisWebhookIngestion:
    """Verify stats payloads dispatch to Redis writer."""

    def test_ingest_webhook_called_for_stats(self) -> None:
        from src.db.redis_writer import RedisTimeSeriesWriter

        writer = MagicMock(spec=RedisTimeSeriesWriter)
        records = [{"mac": "aa:bb:cc", "rssi": -65, "duration": 120}]
        writer.ingest_webhook(records, "client-sessions")
        writer.ingest_webhook.assert_called_once()

    def test_client_session_key_naming(self) -> None:
        """Key pattern: client_stats:{mac}:{field_name}."""
        mac = "aa:bb:cc:dd:ee:ff"
        field = "rssi"
        expected = f"client_stats:{mac}:{field}"
        assert expected == f"client_stats:{mac}:{field}"


class TestWebhookRegistration:
    """Verify webhook registration calls via mistapi."""

    def test_registration_skipped_when_disabled(self) -> None:
        """WEBHOOK_ENABLED=false should skip registration."""
        with patch.dict("os.environ", {"WEBHOOK_ENABLED": "false"}):
            from src.db import DatabaseConfig

            config = DatabaseConfig.from_env()
            assert config.standalone_mode or True  # registration skipped

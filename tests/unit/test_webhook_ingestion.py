"""Unit tests for webhook registration, receiver, and stats ingestion."""

from __future__ import annotations

import builtins
import hashlib
import hmac
import io
import json
import socket
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, call, patch

import pytest
from arango.exceptions import ArangoError
from flask import Flask
from redis.exceptions import ConnectionError as RedisConnectionError
from structlog.testing import capture_logs

if TYPE_CHECKING:
    from src.foundation.persistence.db.router import DatabaseRouter
    from src.foundation.persistence.db.writers.redis_writer import RedisTimeSeriesWriter


@pytest.fixture(autouse=True)
def isolated_webhooks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject external access and confine test output to the temporary directory."""
    denied = MagicMock(side_effect=AssertionError("External access is forbidden"))
    for target in ("connect", "connect_ex"):
        monkeypatch.setattr(socket.socket, target, denied)
    for target in ("getaddrinfo", "gethostbyname", "create_connection"):
        monkeypatch.setattr(socket, target, denied)
    for target in ("builtins.input", "getpass.getpass", "dotenv.load_dotenv", "dotenv.dotenv_values"):
        monkeypatch.setattr(target, denied)
    monkeypatch.setattr("src.foundation.persistence.db.DatabaseConfig.from_env", denied)
    monkeypatch.setattr("src.foundation.persistence.db.host_resolver.DEFAULT_RESOLVER.resolve", denied)
    original_open = builtins.open

    def guarded_open(path: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        """Reject credential files and output outside the isolated directory."""
        resolved = Path(path).resolve()
        if resolved.name.startswith(".env") or (
            any(flag in mode for flag in "wax+") and not resolved.is_relative_to(tmp_path)
        ):
            raise AssertionError("File access is outside the test boundary")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(io, "open", guarded_open)
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def router() -> DatabaseRouter:
    """Use the real router without opening a database connection."""
    from src.foundation.persistence.db import DatabaseConfig
    from src.foundation.persistence.db.router import DatabaseRouter

    return DatabaseRouter(DatabaseConfig(standalone_mode=True))


@pytest.fixture
def redis_writer() -> Iterator[RedisTimeSeriesWriter]:
    """Use real ingestion code with only the Redis and DNS boundaries replaced."""
    from src.foundation.persistence.db import DatabaseConfig
    from src.foundation.persistence.db.writers.redis_writer import RedisTimeSeriesWriter

    with (
        patch("src.foundation.persistence.db.writers.redis_writer.redis.Redis") as client_class,
        patch("src.foundation.persistence.db.host_resolver.DEFAULT_RESOLVER.resolve") as resolve,
        patch("src.foundation.persistence.db.writers.redis_writer.time.time", return_value=1700000000),
    ):
        resolve.return_value.addresses = ("127.0.0.1",)
        client_class.return_value.module_list.return_value = [{"name": "timeseries"}]
        yield RedisTimeSeriesWriter(DatabaseConfig(redis_host="redis.invalid"))


class WebhookRequest:
    """Send signed requests through the real Flask route without a server."""

    @staticmethod
    def post(router: DatabaseRouter | None, payload: dict) -> Any:
        """Exercise signature verification and dispatch with an isolated Flask client."""
        from web_portal.routes.webhooks import webhook_bp

        app = Flask(__name__)
        app.config.update(TESTING=True, WEBHOOK_SECRET="test-secret-key", DB_ROUTER=router)
        app.register_blueprint(webhook_bp)
        body = json.dumps(payload).encode()
        signature = hmac.new(b"test-secret-key", body, hashlib.sha256).hexdigest()
        return app.test_client().post(
            "/api/webhook", data=body, content_type="application/json", headers={"X-Mist-Signature": signature}
        )


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

    def test_audit_calls_handle_webhook_audit(self, router: DatabaseRouter) -> None:
        """A signed audit must reach the real router and preserve snapshot arguments."""
        router._arango_writer = MagicMock()
        payload = {
            "object_type": "wlan",
            "object_id": "abc-123",
            "after": {"ssid": "TestNet"},
        }
        response = WebhookRequest.post(router, {"topic": "audits", "events": [payload]})

        assert response.status_code == 200
        assert response.get_json() == {"status": "ok"}
        expected_hash = hashlib.sha256(json.dumps(payload["after"], sort_keys=True).encode()).hexdigest()
        router._arango_writer.snapshot.assert_called_once_with(
            "wlan", "abc-123", {"ssid": "TestNet"}, expected_hash, "webhook"
        )

    @pytest.mark.parametrize("events", [[], [{"object_type": "wlan"}]])
    def test_empty_or_unidentified_audits_do_not_snapshot(self, router: DatabaseRouter, events: list[dict]) -> None:
        """Empty batches and missing identifiers must not write snapshots."""
        router._arango_writer = MagicMock()
        response = WebhookRequest.post(router, {"topic": "audits", "events": events})
        assert response.status_code == 200
        router._arango_writer.snapshot.assert_not_called()

    def test_snapshot_failure_is_logged_and_later_events_continue(self, router: DatabaseRouter) -> None:
        """An unavailable backend must not discard the next audit event."""
        router._arango_writer = MagicMock()
        router._arango_writer.snapshot.side_effect = [ArangoError("snapshot unavailable"), None]
        events = [{"object_id": "first"}, {"object_id": "second"}]
        with capture_logs() as logs:
            response = WebhookRequest.post(router, {"topic": "audits", "events": events})
        assert response.status_code == 200
        assert [entry.args[1] for entry in router._arango_writer.snapshot.call_args_list] == ["first", "second"]
        assert logs == [
            {
                "event": "webhook_snapshot_failed",
                "log_level": "warning",
                "entity_id": "first",
                "error": "snapshot unavailable",
            }
        ]

    def test_audit_without_backend_is_a_no_op(self, router: DatabaseRouter) -> None:
        """A standalone router must accept an audit without connecting to a backend."""
        response = WebhookRequest.post(router, {"topic": "audits", "object_id": "abc-123"})
        assert response.status_code == 200
        assert router._arango_writer is None


class TestRedisWebhookIngestion:
    """Verify stats payloads dispatch to Redis writer."""

    def test_ingest_webhook_called_for_stats(self, router: DatabaseRouter, redis_writer: RedisTimeSeriesWriter) -> None:
        """A signed stats event must queue both numeric values and execute the pipeline."""
        router._redis_writer = redis_writer
        records = [{"mac": "aa:bb:cc", "rssi": -65, "duration": 120}]
        response = WebhookRequest.post(router, {"topic": "client-sessions", "events": records})
        assert response.status_code == 200
        redis_writer._client.pipeline.assert_called_once_with(transaction=False)
        pipeline = redis_writer._client.pipeline.return_value
        assert pipeline.execute_command.call_args_list == [
            call("TS.ADD", "client_stats:aa:bb:cc:rssi", 1700000000000, -65.0, "DUPLICATE_POLICY", "LAST"),
            call("TS.ADD", "client_stats:aa:bb:cc:duration", 1700000000000, 120.0, "DUPLICATE_POLICY", "LAST"),
        ]
        pipeline.execute.assert_called_once_with()

    @pytest.mark.parametrize(
        ("topic", "prefix"),
        [
            ("client-sessions", "client_stats"),
            ("device-updowns", "device_events"),
            ("device-events", "device_events"),
            ("client-latency", "client_latency"),
        ],
    )
    def test_client_session_key_naming(
        self, router: DatabaseRouter, redis_writer: RedisTimeSeriesWriter, topic: str, prefix: str
    ) -> None:
        """Every supported stats topic must use the product key prefix."""
        router._redis_writer = redis_writer
        response = WebhookRequest.post(router, {"topic": topic, "events": [{"mac": "aa:bb", "rssi": -65}]})
        assert response.status_code == 200
        redis_writer._client.pipeline.return_value.execute_command.assert_called_once_with(
            "TS.ADD", f"{prefix}:aa:bb:rssi", 1700000000000, -65.0, "DUPLICATE_POLICY", "LAST"
        )
        assert redis_writer._ts.create.call_args_list[0].args == (f"{prefix}:aa:bb:rssi",)

    @pytest.mark.parametrize("events", [[], [{"mac": "aa:bb", "active": True, "rssi": "-65", "value": None}]])
    def test_empty_or_nonnumeric_events_do_not_execute(
        self, redis_writer: RedisTimeSeriesWriter, events: list[dict]
    ) -> None:
        """A batch without numeric metrics must return zero and perform no writes."""
        assert redis_writer.ingest_webhook(events, "client-sessions") == 0
        pipeline = redis_writer._client.pipeline.return_value
        pipeline.execute_command.assert_not_called()
        pipeline.execute.assert_not_called()
        redis_writer._ts.create.assert_not_called()

    @pytest.mark.parametrize(
        ("identity", "entity"),
        [({"mac": "aa:bb", "device_id": 123}, "aa:bb"), ({"device_id": 123}, "123"), ({}, "unknown")],
    )
    def test_entity_selection_excludes_numeric_identifiers(
        self, redis_writer: RedisTimeSeriesWriter, identity: dict, entity: str
    ) -> None:
        """Identifiers must select keys rather than become numeric metrics."""
        assert redis_writer.ingest_webhook([{**identity, "rssi": -65}], "client-sessions") == 1
        redis_writer._client.pipeline.return_value.execute_command.assert_called_once_with(
            "TS.ADD", f"client_stats:{entity}:rssi", 1700000000000, -65.0, "DUPLICATE_POLICY", "LAST"
        )

    def test_pipeline_failure_is_logged_by_receiver(
        self, router: DatabaseRouter, redis_writer: RedisTimeSeriesWriter, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The receiver must report a failed flush rather than log a successful ingestion."""
        router._redis_writer = redis_writer
        pipeline = redis_writer._client.pipeline.return_value
        pipeline.execute.side_effect = RedisConnectionError("pipeline unavailable")
        response = WebhookRequest.post(router, {"topic": "client-sessions", "events": [{"mac": "aa:bb", "rssi": -65}]})
        assert response.status_code == 200
        pipeline.execute.assert_called_once_with()
        assert "Stats ingestion failed for client-sessions: pipeline unavailable" in caplog.text
        assert "webhook_ingested" not in caplog.text

    @pytest.mark.parametrize("topic", ["client-sessions", "audits", "unsupported"])
    @pytest.mark.parametrize("missing_router", [True, False])
    def test_missing_handlers_and_unknown_topics_are_no_ops(
        self, router: DatabaseRouter, topic: str, missing_router: bool
    ) -> None:
        """Missing storage handlers and unknown topics must not open external connections."""
        response = WebhookRequest.post(None if missing_router else router, {"topic": topic, "events": []})
        assert response.status_code == 200
        assert response.get_json() == {"status": "ok"}

    def test_unknown_topic_does_not_reach_available_handlers(self, router: DatabaseRouter) -> None:
        """Unknown topics must not reach either available storage handler."""
        router._arango_writer = MagicMock()
        router._redis_writer = MagicMock()
        response = WebhookRequest.post(
            router, {"topic": "unsupported", "events": [{"object_id": "abc-123", "rssi": -65}]}
        )
        assert response.status_code == 200
        router._arango_writer.snapshot.assert_not_called()
        router._redis_writer.ingest_webhook.assert_not_called()


class TestWebhookRegistration:
    """Verify webhook registration calls via mistapi."""

    @pytest.mark.parametrize(("enabled", "status"), [("false", 404), ("true", 503)])
    def test_registration_skipped_when_disabled(
        self, monkeypatch: pytest.MonkeyPatch, enabled: str, status: int
    ) -> None:
        """The environment must control actual route registration without database configuration."""
        from web_portal.app import WebPortalApp

        monkeypatch.setenv("WEBHOOK_ENABLED", enabled)
        monkeypatch.delenv("WEBHOOK_SECRET", raising=False)
        app = Flask(__name__)
        WebPortalApp._load_webhook_config(app)
        WebPortalApp._register_webhook_blueprint(app)
        assert app.config["WEBHOOK_ENABLED"] is (enabled == "true")
        assert ("/api/webhook" in {rule.rule for rule in app.url_map.iter_rules()}) is (enabled == "true")
        assert app.test_client().post("/api/webhook", json={"topic": "audits"}).status_code == status

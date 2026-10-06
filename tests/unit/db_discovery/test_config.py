"""Prove central configuration discovery with no production DNS or store."""

from __future__ import annotations

import os
import socket
import time
from concurrent.futures import Future, ThreadPoolExecutor
from unittest.mock import patch

import pytest
from arango.exceptions import ArangoServerError
from arango.request import Request
from arango.response import Response

from src.foundation.persistence.db import DatabaseConfig
from src.foundation.persistence.db.coordination.router import DatabaseRouter
from src.foundation.persistence.db.support import host_resolver
from src.foundation.persistence.db.support.host_resolver import ResolutionResult
from tests.unit.db_discovery.fakes import ResolverHarness

DISCOVERY_ENV = {
    "ARANGO_HOST": "http://missing-arango.invalid:9529",
    "REDIS_HOST": "missing-redis.invalid",
}
REQUIRED_ENV = {
    "ARANGO_USERNAME": "controlled-user",
    "ARANGO_ROOT_PASSWORD": "controlled" + "-arango-value",
    "REDIS_PASSWORD": "controlled" + "-redis-value",
}


class TestConfigurationDeadline:
    """Measure the real configuration caller before and after the repair."""

    def test_repeated_failed_config_uses_one_lookup_per_hostname(self, discovery: ResolverHarness) -> None:
        """Issue #3318: two configuration reads must share the negative cache."""
        resolver = discovery.lookup
        with patch.dict(os.environ, DISCOVERY_ENV, clear=True):
            first = DatabaseConfig.from_env()
            second = DatabaseConfig.from_env()
        assert first.standalone_mode is True
        assert second.standalone_mode is True
        assert resolver.calls == [
            ("missing-arango.invalid", None, socket.AF_UNSPEC, socket.SOCK_STREAM),
            ("missing-redis.invalid", None, socket.AF_UNSPEC, socket.SOCK_STREAM),
        ]

    def test_blocked_config_lookup_has_a_real_caller_deadline(self, discovery: ResolverHarness) -> None:
        """Issue #3318: a blocked operating system lookup must not hold the caller."""
        resolver = discovery.lookup
        resolver.blocked_hosts = {"missing-arango.invalid", "missing-redis.invalid"}
        completed = False
        with patch.dict(os.environ, DISCOVERY_ENV, clear=True), ThreadPoolExecutor(max_workers=1) as caller:
            started = time.monotonic()
            pending = caller.submit(DatabaseConfig.from_env)
            try:
                completed = pending.result(timeout=2.6).standalone_mode
            except TimeoutError:
                completed = False
            finally:
                elapsed = time.monotonic() - started
                resolver.release.set()
            assert pending.result(timeout=2).standalone_mode is True
        assert completed is True, f"The configuration caller remained blocked after {elapsed:.3f} seconds."
        assert elapsed < 2.6, f"The two-name caller exceeded its DNS budget: {elapsed:.3f} seconds."


class TestPartialBackendBoundary:
    """Expose DNS work after the configuration permits one backend."""

    def test_capture_store_skips_driver_when_only_redis_resolves(self, discovery: ResolverHarness) -> None:
        """A failed ArangoDB name must not repeat through the portal driver."""
        from src.interfaces.portals.upgrade_portal.capture import store

        resolver = discovery.lookup
        resolver.answers["missing-redis.invalid"] = resolver.addresses()
        with (
            patch.dict(os.environ, DISCOVERY_ENV | REQUIRED_ENV, clear=True),
            patch.object(store, "ArangoClient") as client,
        ):
            client.return_value.db.return_value = "controlled-handle"
            config = DatabaseConfig.from_env()
            result = store._open_database(config)
        assert config.standalone_mode is False
        assert result is None
        assert client.call_count == 0
        assert len(resolver.calls) == 2

    def test_redis_preflight_reuses_the_failed_configuration_lookup(self, discovery: ResolverHarness) -> None:
        """A resolved ArangoDB name must not leave repeated Redis DNS."""
        from src.foundation.persistence.db.backends.redis_writer import RedisTimeSeriesWriter

        resolver = discovery.lookup
        resolver.answers["missing-arango.invalid"] = resolver.addresses()
        with patch.dict(os.environ, DISCOVERY_ENV | REQUIRED_ENV, clear=True):
            config = DatabaseConfig.from_env()
            for _attempt in range(2):
                with pytest.raises(ConnectionError, match="not resolvable"):
                    RedisTimeSeriesWriter._preflight_dns(config.redis_host)
        assert config.standalone_mode is False
        assert [call[0] for call in resolver.calls].count("missing-redis.invalid") == 1

    @staticmethod
    def _partial_config(discovery: ResolverHarness) -> DatabaseConfig:
        """Retain a working Redis name while ArangoDB discovery fails."""
        discovery.lookup.answers["missing-redis.invalid"] = discovery.lookup.addresses()
        with patch.dict(os.environ, DISCOVERY_ENV | REQUIRED_ENV, clear=True):
            return DatabaseConfig.from_env()

    def test_arango_preflight_reuses_failed_dns_in_partial_backend_mode(
        self, discovery: ResolverHarness, record_property
    ) -> None:
        """Refuse the unresolved backend before its driver while keeping Redis available."""
        from src.foundation.persistence.db.backends import arango_writer
        from src.foundation.persistence.db.coordination import router as router_module

        config = self._partial_config(discovery)
        discovery.lookup.blocked_hosts.add("missing-arango.invalid")
        with (
            patch.object(arango_writer, "ArangoClient") as client,
            patch.object(router_module, "RedisTimeSeriesWriter"),
            patch.object(router_module, "RedisJSONWriter"),
        ):
            started = time.monotonic()
            router = DatabaseRouter(config)
            elapsed = time.monotonic() - started
        record_property("partial_backend_cached_refusal_seconds", elapsed)
        assert elapsed < 0.3
        assert client.call_count == 0
        assert router._arango_available is False
        assert router._redis_available is True
        assert router._redis_json_available is True
        assert [call[0] for call in discovery.lookup.calls].count("missing-arango.invalid") == 1


class TestConfigurationPolicy:
    """Preserve operator mode, credentials, names, and finite recovery."""

    @pytest.mark.parametrize("value", ["true", "TRUE", "True"])
    def test_explicit_standalone_skips_all_lookups(self, discovery: ResolverHarness, value: str) -> None:
        with patch.dict(os.environ, {"MISTHELPER_STANDALONE": value}, clear=True):
            config = DatabaseConfig.from_env()
        assert config.standalone_mode is True
        assert config.arango_username == ""
        assert config.arango_password == ""
        assert config.redis_password == ""
        assert discovery.lookup.calls == []

    @pytest.mark.parametrize("missing_field", sorted(REQUIRED_ENV))
    def test_partial_backend_still_requires_every_credential(
        self, discovery: ResolverHarness, missing_field: str
    ) -> None:
        discovery.lookup.answers["missing-redis.invalid"] = discovery.lookup.addresses()
        environment = DISCOVERY_ENV | REQUIRED_ENV
        del environment[missing_field]
        with patch.dict(os.environ, environment, clear=True), pytest.raises(ValueError, match=missing_field):
            DatabaseConfig.from_env()
        assert [call[0] for call in discovery.lookup.calls] == ["missing-arango.invalid", "missing-redis.invalid"]

    @pytest.mark.parametrize("resolved_hostname", ["missing-arango.invalid", "missing-redis.invalid"])
    def test_one_resolved_backend_keeps_partial_mode_and_names(
        self, discovery: ResolverHarness, resolved_hostname: str
    ) -> None:
        discovery.lookup.answers[resolved_hostname] = discovery.lookup.addresses()
        with patch.dict(os.environ, DISCOVERY_ENV | REQUIRED_ENV, clear=True):
            config = DatabaseConfig.from_env()
        assert config.standalone_mode is False
        assert config.arango_host == "http://missing-arango.invalid:9529"
        assert config.redis_host == "missing-redis.invalid"
        assert config.arango_username == "controlled-user"
        assert config.webhook_enabled is True
        assert len(discovery.lookup.calls) == 2

    def test_changed_external_hostname_is_checked_without_waiting_for_expiry(self, discovery: ResolverHarness) -> None:
        with patch.dict(os.environ, DISCOVERY_ENV | REQUIRED_ENV, clear=True):
            first = DatabaseConfig.from_env()
            os.environ["ARANGO_HOST"] = "https://external-db.invalid:9443"
            discovery.lookup.answers["external-db.invalid"] = discovery.lookup.addresses()
            second = DatabaseConfig.from_env()
        assert first.standalone_mode is True
        assert second.standalone_mode is False
        assert second.arango_host == "https://external-db.invalid:9443"
        assert [call[0] for call in discovery.lookup.calls] == [
            "missing-arango.invalid",
            "missing-redis.invalid",
            "external-db.invalid",
        ]

    def test_expired_negative_configuration_detects_a_later_backend(self, discovery: ResolverHarness) -> None:
        with patch.dict(os.environ, DISCOVERY_ENV | REQUIRED_ENV, clear=True):
            first = DatabaseConfig.from_env()
            discovery.lookup.answers["missing-arango.invalid"] = discovery.lookup.addresses()
            assert DatabaseConfig.from_env().standalone_mode is True
            discovery.clock.advance(30)
            recovered = DatabaseConfig.from_env()
        assert first.standalone_mode is True
        assert recovered.standalone_mode is False
        assert recovered.arango_host == first.arango_host
        assert len(discovery.lookup.calls) == 4


class TestCaptureStoreRecovery:
    """Retry absent handles while preserving configured client URLs and errors."""

    def test_later_store_is_visible_after_expiry_and_keeps_tls_url(self, discovery: ResolverHarness) -> None:
        from src.interfaces.portals.upgrade_portal.capture import store

        secret = "controlled" + "-url-value"
        environment = DISCOVERY_ENV | REQUIRED_ENV | {"ARANGO_HOST": f"https://uri-user:{secret}@store.invalid:9443"}
        discovery.lookup.answers["missing-redis.invalid"] = discovery.lookup.addresses()
        handle = object()
        with patch.dict(os.environ, environment, clear=True), patch.object(store, "ArangoClient") as client:
            client.return_value.db.return_value = handle
            assert store.connect_database() is None
            assert store.connect_database() is None
            assert client.call_count == 0
            discovery.lookup.answers["store.invalid"] = discovery.lookup.addresses()
            discovery.clock.advance(30)
            assert store.connect_database() is handle
            assert store.connect_database() is handle
            client.assert_called_once_with(hosts=environment["ARANGO_HOST"], request_timeout=10.0)
            client.return_value.db.assert_called_once_with(
                "misthelper",
                username=REQUIRED_ENV["ARANGO_USERNAME"],
                password=REQUIRED_ENV["ARANGO_ROOT_PASSWORD"],
                verify=True,
            )
        assert [call[0] for call in discovery.lookup.calls].count("store.invalid") == 2
        assert store._DATABASE_HANDLE is handle

    @staticmethod
    def _driver_error(status_code: int) -> ArangoServerError:
        """Build the installed SDK error shape without an HTTP connection."""
        response = Response(
            method="get",
            url="https://missing-arango.invalid/_api/version",
            headers={},
            status_code=status_code,
            status_text="Controlled error",
            raw_body='{"error": true, "errorNum": 1200, "errorMessage": "Controlled driver error."}',
        )
        return ArangoServerError(response, Request(method="get", endpoint="/_api/version"))

    @pytest.mark.parametrize("status_code", [404, 503], ids=["http_4xx", "http_5xx"])
    def test_http_4xx_and_http_5xx_keep_driver_fallback_semantics(
        self, discovery: ResolverHarness, status_code: int
    ) -> None:
        from src.interfaces.portals.upgrade_portal.capture import store

        discovery.lookup.answers["missing-arango.invalid"] = discovery.lookup.addresses()
        with (
            patch.dict(os.environ, DISCOVERY_ENV | REQUIRED_ENV, clear=True),
            patch.object(store, "ArangoClient") as client,
        ):
            client.return_value.db.side_effect = self._driver_error(status_code)
            assert store._open_database(DatabaseConfig.from_env()) is None
            assert client.return_value.db.call_count == 1
        assert len(discovery.lookup.calls) == 2

    def test_malformed_json_driver_error_remains_visible(self, discovery: ResolverHarness) -> None:
        from src.interfaces.portals.upgrade_portal.capture import store

        discovery.lookup.answers["missing-arango.invalid"] = discovery.lookup.addresses()
        with (
            patch.dict(os.environ, DISCOVERY_ENV | REQUIRED_ENV, clear=True),
            patch.object(store, "ArangoClient") as client,
        ):
            client.return_value.db.side_effect = ValueError("Controlled malformed JSON.")
            with pytest.raises(ValueError, match="Controlled malformed JSON"):
                store._open_database(DatabaseConfig.from_env())
            assert client.return_value.db.call_count == 1
        assert len(discovery.lookup.calls) == 2

    def test_configuration_credentials_and_uri_credentials_do_not_enter_logs(
        self, discovery: ResolverHarness, caplog
    ) -> None:
        import logging

        from src.interfaces.portals.upgrade_portal.capture import store

        secret = "controlled" + "-uri-value"
        environment = DISCOVERY_ENV | REQUIRED_ENV | {"ARANGO_HOST": f"https://uri-user:{secret}@store.invalid:9443"}
        discovery.lookup.answers["missing-redis.invalid"] = discovery.lookup.addresses()
        with patch.dict(os.environ, environment, clear=True), caplog.at_level(logging.DEBUG):
            assert store._open_database(DatabaseConfig.from_env()) is None
        assert "store.invalid" in caplog.text
        assert secret not in caplog.text
        assert "uri-user" not in caplog.text
        assert REQUIRED_ENV["ARANGO_ROOT_PASSWORD"] not in caplog.text
        assert REQUIRED_ENV["REDIS_PASSWORD"] not in caplog.text


class TestPreflightCacheEdges:
    """Check timeout races and both released preflight entry points."""

    def test_completed_future_during_timeout_keeps_its_success(self, discovery: ResolverHarness) -> None:
        resolver = discovery.create()
        resolved = ResolutionResult(tuple(discovery.lookup.addresses()))
        future: Future[ResolutionResult] = Future()
        future.set_result(resolved)
        with patch.object(future, "result", side_effect=[TimeoutError("Controlled completion race."), resolved]):
            result = resolver._wait(("db.invalid", socket.AF_UNSPEC, socket.SOCK_STREAM, 0, 0), future)
        assert result is resolved
        assert resolver.resource_counts()["cached"] == 0
        assert discovery.lookup.calls == []

    def test_explicit_standalone_store_creates_no_dns_or_client(self, discovery: ResolverHarness) -> None:
        from src.interfaces.portals.upgrade_portal.capture import store

        with patch.object(store, "ArangoClient") as client:
            assert store._open_database(DatabaseConfig(standalone_mode=True)) is None
        assert client.call_count == 0
        assert discovery.lookup.calls == []

    def test_redis_json_and_timeseries_share_one_preflight_result(self, discovery: ResolverHarness) -> None:
        from src.foundation.persistence.db.backends import redis_writer

        discovery.lookup.answers["missing-redis.invalid"] = discovery.lookup.addresses()
        with (
            patch.dict(os.environ, DISCOVERY_ENV | REQUIRED_ENV, clear=True),
            patch.object(redis_writer.redis, "Redis") as client,
        ):
            client.return_value.module_list.return_value = [{"name": b"ReJSON"}]
            config = DatabaseConfig.from_env()
            writer = redis_writer.RedisJSONWriter(config)
            redis_writer.RedisTimeSeriesWriter._preflight_dns(config.redis_host)
        assert writer._client is client.return_value
        assert client.call_args.kwargs["host"] == "missing-redis.invalid"
        assert [call[0] for call in discovery.lookup.calls].count("missing-redis.invalid") == 1

    def test_redis_preflight_has_a_real_deadline_and_preserves_error_cause(
        self, discovery: ResolverHarness, record_property
    ) -> None:
        from src.foundation.persistence.db.backends.redis_writer import RedisTimeSeriesWriter

        discovery.lookup.blocked_hosts.add("blocked-redis.invalid")
        started = time.monotonic()
        with pytest.raises(ConnectionError, match="not resolvable") as failure:
            RedisTimeSeriesWriter._preflight_dns("blocked-redis.invalid")
        elapsed = time.monotonic() - started
        record_property("redis_preflight_elapsed_seconds", elapsed)
        assert 0.9 <= elapsed < 1.3, elapsed
        assert isinstance(failure.value.__cause__, TimeoutError)
        assert len(discovery.lookup.calls) == 1
        discovery.drain(host_resolver.DEFAULT_RESOLVER)

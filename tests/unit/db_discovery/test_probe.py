"""Keep central TCP readiness separate from cached DNS discovery."""

from __future__ import annotations

import errno
import os
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
import structlog
from arango.exceptions import ArangoError

from src import db
from src.db import DatabaseConfig, arango_writer
from src.db.arango_writer import ArangoDBWriter
from src.db.host_resolver import ResolverLimits
from src.db.redis_writer import RedisTimeSeriesWriter
from src.refactors.endpoint_primary_key_strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES
from tests.unit.arango_indexes.fakes import ArangoIndexWriterHarness
from tests.unit.db_discovery.fakes import ControlledPreflightCall, ControlledSockets, ResolverHarness


class TestNumericAddresses:
    """Use actual resolved families and numeric targets without a second DNS call."""

    def test_ipv4_uses_the_resolved_numeric_address(self, discovery: ResolverHarness, monkeypatch) -> None:
        discovery.lookup.answers["db.invalid"] = discovery.lookup.addresses()
        sockets = ControlledSockets()
        monkeypatch.setattr(db.socket, "socket", sockets)
        with patch(
            "src.db.socket.create_connection", side_effect=AssertionError("Raw hostname connection is forbidden.")
        ):
            assert db._can_connect("db.invalid", 8529) is True
        assert sockets.calls == [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)]
        assert sockets.targets == [("192.0.2.10", 8529)]
        assert len(discovery.lookup.calls) == 1
        assert 0 < sockets.connections[0].settimeout.call_args.args[0] <= 0.5
        sockets.connections[0].__exit__.assert_called_once_with(None, None, None)

    def test_ipv6_retains_flow_and_scope(self, discovery: ResolverHarness, monkeypatch) -> None:
        discovery.lookup.answers["db.invalid"] = [
            (socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("2001:db8::10", 0, 3, 7))
        ]
        sockets = ControlledSockets()
        monkeypatch.setattr(db.socket, "socket", sockets)
        assert db._can_connect("db.invalid", 9379) is True
        assert sockets.calls == [(socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_TCP)]
        assert sockets.targets == [("2001:db8::10", 9379, 3, 7)]
        assert len(discovery.lookup.calls) == 1

    def test_warm_configuration_addresses_are_reused_by_tcp(self, discovery: ResolverHarness, monkeypatch) -> None:
        discovery.lookup.answers.update(
            {"db.invalid": discovery.lookup.addresses(), "redis.invalid": discovery.lookup.addresses()}
        )
        sockets = ControlledSockets()
        monkeypatch.setattr(db.socket, "socket", sockets)
        assert db._hosts_unreachable("http://db.invalid:9529", "redis.invalid") is False
        assert db._can_connect("db.invalid", 8529) is True
        assert len(discovery.lookup.calls) == 2
        assert sockets.targets == [("192.0.2.10", 8529)]

    def test_second_address_can_answer_after_the_first_refuses(self, discovery: ResolverHarness, monkeypatch) -> None:
        discovery.lookup.answers["db.invalid"] = discovery.lookup.addresses() + discovery.lookup.addresses("192.0.2.11")
        sockets = ControlledSockets([ConnectionRefusedError("Controlled refusal."), None])
        monkeypatch.setattr(db.socket, "socket", sockets)
        assert db._can_connect("db.invalid", 8529) is True
        assert sockets.targets == [("192.0.2.10", 8529), ("192.0.2.11", 8529)]
        assert len(discovery.lookup.calls) == 1
        assert all(connection.__exit__.call_count == 1 for connection in sockets.connections)

    def test_failed_dns_creates_no_tcp_socket(self, discovery: ResolverHarness, monkeypatch) -> None:
        sockets = ControlledSockets()
        monkeypatch.setattr(db.socket, "socket", sockets)
        assert db._can_connect("db.invalid", 8529) is False
        assert sockets.calls == []
        assert sockets.targets == []
        assert len(discovery.lookup.calls) == 1


class TestTcpBudgets:
    """Use one TCP budget instead of one new budget per resolved address."""

    def test_blocked_dns_remains_bounded_before_tcp_starts(
        self, discovery: ResolverHarness, monkeypatch, record_property
    ) -> None:
        discovery.lookup.blocked_hosts.add("db.invalid")
        sockets = ControlledSockets()
        monkeypatch.setattr(db.socket, "socket", sockets)
        started = time.monotonic()
        assert db._can_connect("db.invalid", 8529) is False
        elapsed = time.monotonic() - started
        record_property("probe_dns_elapsed_seconds", elapsed)
        assert 0.9 <= elapsed < 1.3, elapsed
        assert sockets.calls == []
        discovery.drain(db.host_resolver.DEFAULT_RESOLVER)

    def test_first_socket_timeout_exhausts_the_aggregate_budget(self, discovery: ResolverHarness, monkeypatch) -> None:
        discovery.lookup.answers["db.invalid"] = discovery.lookup.addresses() + discovery.lookup.addresses("192.0.2.11")
        sockets = ControlledSockets([TimeoutError("Controlled TCP timeout.")], delay=0.1)
        monkeypatch.setattr(db.socket, "socket", sockets)
        monkeypatch.setattr(db, "PROBE_TIMEOUT_SECONDS", 0.03)
        started = time.monotonic()
        assert db._can_connect("db.invalid", 8529) is False
        assert 0.02 <= time.monotonic() - started < 0.2
        assert sockets.targets == [("192.0.2.10", 8529)]
        assert len(discovery.lookup.calls) == 1
        assert sockets.connections[0].__exit__.call_count == 1

    def test_each_later_address_receives_only_the_remaining_budget(
        self, discovery: ResolverHarness, monkeypatch
    ) -> None:
        discovery.lookup.answers["db.invalid"] = discovery.lookup.addresses() + discovery.lookup.addresses("192.0.2.11")
        sockets = ControlledSockets([ConnectionRefusedError("Controlled refusal."), None], delay=0.01)
        monkeypatch.setattr(db.socket, "socket", sockets)
        assert db._can_connect("db.invalid", 8529) is True
        budgets = [connection.settimeout.call_args.args[0] for connection in sockets.connections]
        assert 0 < budgets[1] < budgets[0] <= 0.5
        assert len(sockets.targets) == 2

    def test_dns_success_does_not_cache_tcp_readiness(self, discovery: ResolverHarness, monkeypatch) -> None:
        discovery.lookup.answers["db.invalid"] = discovery.lookup.addresses()
        sockets = ControlledSockets([ConnectionRefusedError("Controlled unavailable service."), None])
        monkeypatch.setattr(db.socket, "socket", sockets)
        assert db._can_connect("db.invalid", 8529) is False
        assert db._can_connect("db.invalid", 8529) is True
        assert len(discovery.lookup.calls) == 1
        assert sockets.targets == [("192.0.2.10", 8529), ("192.0.2.10", 8529)]

    @pytest.mark.parametrize(
        "error", [OSError("Controlled socket failure."), OverflowError("Controlled invalid port.")]
    )
    def test_socket_creation_error_returns_an_unavailable_probe(
        self, discovery: ResolverHarness, error: Exception
    ) -> None:
        discovery.lookup.answers["db.invalid"] = discovery.lookup.addresses()
        with patch("src.db.socket.socket", side_effect=error):
            assert db._can_connect("db.invalid", 8529) is False
        assert len(discovery.lookup.calls) == 1


class TestConfiguredBackendProbes:
    """Preserve configured names, ports, and partial service readiness."""

    def test_remote_names_and_ports_are_preserved_outside_compose(
        self, discovery: ResolverHarness, monkeypatch
    ) -> None:
        environment = {
            "ARANGO_HOST": "https://db.remote.invalid:9999",
            "REDIS_HOST": "redis.remote.invalid",
            "REDIS_PORT": "6380",
        }
        discovery.lookup.answers.update(
            {"db.remote.invalid": discovery.lookup.addresses(), "redis.remote.invalid": discovery.lookup.addresses()}
        )
        sockets = ControlledSockets([ConnectionRefusedError("Controlled ArangoDB refusal."), None])
        monkeypatch.setattr(db.socket, "socket", sockets)
        with patch.dict(os.environ, environment, clear=True):
            assert db.polyglot_hosts_unreachable() is False
        assert sockets.targets == [("192.0.2.10", 9999), ("192.0.2.10", 6380)]
        assert [call[0] for call in discovery.lookup.calls] == ["db.remote.invalid", "redis.remote.invalid"]

    def test_unreadable_redis_port_and_absent_arango_port_keep_defaults(
        self, discovery: ResolverHarness, monkeypatch
    ) -> None:
        environment = {
            "ARANGO_HOST": "https://db.remote.invalid",
            "REDIS_HOST": "redis.remote.invalid",
            "REDIS_PORT": "unreadable",
        }
        discovery.lookup.answers.update(
            {"db.remote.invalid": discovery.lookup.addresses(), "redis.remote.invalid": discovery.lookup.addresses()}
        )
        sockets = ControlledSockets()
        monkeypatch.setattr(db.socket, "socket", sockets)
        with patch.dict(os.environ, environment, clear=True):
            assert db.polyglot_hosts_unreachable() is False
        assert sockets.targets == [("192.0.2.10", 9529), ("192.0.2.10", 9379)]

    def test_resolved_but_refused_services_remain_unavailable(self, discovery: ResolverHarness, monkeypatch) -> None:
        discovery.lookup.answers.update(
            {"misthelper-arangodb": discovery.lookup.addresses(), "misthelper-redis": discovery.lookup.addresses()}
        )
        sockets = ControlledSockets(
            [
                ConnectionRefusedError("Controlled ArangoDB refusal."),
                ConnectionRefusedError("Controlled Redis refusal."),
            ]
        )
        monkeypatch.setattr(db.socket, "socket", sockets)
        with patch.dict(os.environ, {}, clear=True):
            assert db.polyglot_hosts_unreachable() is True
        assert len(discovery.lookup.calls) == 2
        assert len(sockets.targets) == 2

    def test_repeated_tcp_probe_reuses_both_dns_queries(self, discovery: ResolverHarness, monkeypatch) -> None:
        discovery.lookup.answers.update(
            {"misthelper-arangodb": discovery.lookup.addresses(), "misthelper-redis": discovery.lookup.addresses()}
        )
        sockets = ControlledSockets()
        monkeypatch.setattr(db.socket, "socket", sockets)
        with patch.dict(os.environ, {}, clear=True):
            assert db.polyglot_hosts_unreachable() is False
            assert db.polyglot_hosts_unreachable() is False
        assert len(discovery.lookup.calls) == 2
        assert len(sockets.targets) == 4

    def test_two_failed_names_have_cached_dns_and_no_tcp_work(self, discovery: ResolverHarness, monkeypatch) -> None:
        sockets = ControlledSockets()
        monkeypatch.setattr(db.socket, "socket", sockets)
        with patch.dict(os.environ, {}, clear=True):
            assert db.polyglot_hosts_unreachable() is True
            assert db.polyglot_hosts_unreachable() is True
        assert len(discovery.lookup.calls) == 2
        assert sockets.targets == []


class TestArangoDnsPreflight:
    """Prove the inherited preflight deadline and both cache expiry paths."""

    def test_native_blocked_preflight_obeys_the_real_one_second_deadline(
        self, discovery: ResolverHarness, record_property
    ) -> None:
        discovery.lookup.blocked_hosts.add("blocked-arango.invalid")
        probe = ControlledPreflightCall(discovery.lookup)
        failure, elapsed, completed = probe.measure(lambda: ArangoDBWriter._preflight_dns("blocked-arango.invalid"))
        record_property("arango_preflight_elapsed_seconds", elapsed)
        record_property("arango_preflight_completed_inside_budget", completed)
        assert completed is True, f"The inherited preflight remained blocked after {elapsed:.3f} seconds."
        assert 0.9 <= elapsed < 1.3, elapsed
        assert isinstance(failure, ConnectionError)
        assert isinstance(failure.__cause__, TimeoutError)
        assert len(discovery.lookup.calls) == 1

    def test_failed_configuration_and_preflight_share_one_negative_lookup(self, discovery: ResolverHarness) -> None:
        assert db._hosts_unreachable("https://missing-arango.invalid:9443", "missing-redis.invalid") is True
        for _attempt in range(3):
            with pytest.raises(ConnectionError, match="not resolvable") as failure:
                ArangoDBWriter._preflight_dns("missing-arango.invalid")
            assert isinstance(failure.value.__cause__, socket.gaierror)
        assert [call[0] for call in discovery.lookup.calls] == ["missing-arango.invalid", "missing-redis.invalid"]

    def test_positive_preflight_cache_expires_at_thirty_seconds(self, discovery: ResolverHarness) -> None:
        discovery.lookup.answers["arango.invalid"] = discovery.lookup.addresses()
        ArangoDBWriter._preflight_dns("arango.invalid")
        discovery.clock.advance(29.999)
        ArangoDBWriter._preflight_dns("arango.invalid")
        assert len(discovery.lookup.calls) == 1
        discovery.clock.advance(0.001)
        discovery.lookup.answers["arango.invalid"] = discovery.lookup.addresses("192.0.2.11")
        ArangoDBWriter._preflight_dns("arango.invalid")
        assert len(discovery.lookup.calls) == 2
        assert db.host_resolver.DEFAULT_RESOLVER.resolve("arango.invalid").addresses == tuple(
            discovery.lookup.addresses("192.0.2.11")
        )

    def test_negative_preflight_cache_expiry_detects_recovery(self, discovery: ResolverHarness) -> None:
        with pytest.raises(ConnectionError, match="not resolvable"):
            ArangoDBWriter._preflight_dns("arango.invalid")
        discovery.lookup.answers["arango.invalid"] = discovery.lookup.addresses()
        discovery.clock.advance(29.999)
        with pytest.raises(ConnectionError, match="not resolvable"):
            ArangoDBWriter._preflight_dns("arango.invalid")
        assert len(discovery.lookup.calls) == 1
        discovery.clock.advance(0.001)
        ArangoDBWriter._preflight_dns("arango.invalid")
        assert len(discovery.lookup.calls) == 2
        assert db.host_resolver.DEFAULT_RESOLVER.resolve("arango.invalid").error is None

    def test_successful_preflight_and_numeric_tcp_share_the_same_addresses(
        self, discovery: ResolverHarness, monkeypatch
    ) -> None:
        discovery.lookup.answers["arango.invalid"] = discovery.lookup.addresses()
        sockets = ControlledSockets()
        monkeypatch.setattr(db.socket, "socket", sockets)
        ArangoDBWriter._preflight_dns("arango.invalid")
        assert db._can_connect("arango.invalid", 9529) is True
        assert len(discovery.lookup.calls) == 1
        assert sockets.targets == [("192.0.2.10", 9529)]


class TestArangoPreflightResources:
    """Prove native guard refusals, finite shared work, and protected driver behavior."""

    def test_parallel_preflights_share_one_lookup_and_release_all_helpers(self, discovery: ResolverHarness) -> None:
        discovery.lookup.answers["arango.invalid"] = discovery.lookup.addresses()
        discovery.lookup.blocked_hosts.add("arango.invalid")
        resolver = db.host_resolver.DEFAULT_RESOLVER
        with ThreadPoolExecutor(max_workers=12) as callers:
            futures = [callers.submit(ArangoDBWriter._preflight_dns, "arango.invalid") for _request in range(12)]
            assert discovery.lookup.wait_for_calls(1) is True
            discovery.lookup.release.set()
            assert [future.result(timeout=2) for future in futures] == [None] * 12
        assert len(discovery.lookup.calls) == 1
        assert resolver.resource_counts()["pending"] == 0
        assert resolver.resource_counts()["workers"] <= 2
        resolver.close(timeout=1)
        assert resolver.resource_counts() == {"workers": 0, "pending": 0, "queued": 0, "cached": 1}

    def test_saturated_preflights_refuse_extra_work_then_recover(self, discovery: ResolverHarness) -> None:
        discovery.lookup.blocked_hosts.update({"first.invalid", "second.invalid"})
        resolver = discovery.create(ResolverLimits(timeout_seconds=0.03), shared=True)
        for hostname in ("first.invalid", "second.invalid"):
            with pytest.raises(ConnectionError, match="not resolvable") as failure:
                ArangoDBWriter._preflight_dns(hostname)
            assert isinstance(failure.value.__cause__, TimeoutError)
        with (
            structlog.testing.capture_logs() as records,
            pytest.raises(ConnectionError, match="not resolvable") as failure,
        ):
            ArangoDBWriter._preflight_dns("later.invalid")
        assert isinstance(failure.value.__cause__, OSError)
        assert failure.value.__cause__.errno == errno.EBUSY
        assert resolver.resource_counts() == {"workers": 2, "pending": 2, "queued": 0, "cached": 2}
        assert any(
            record["event"] == "arango_dns_preflight_unavailable" and record["checked_hosts"] == 1 for record in records
        )
        discovery.drain(resolver)
        discovery.lookup.answers["later.invalid"] = discovery.lookup.addresses()
        ArangoDBWriter._preflight_dns("later.invalid")
        assert [call[0] for call in discovery.lookup.calls] == ["first.invalid", "second.invalid", "later.invalid"]

    def test_dns_guard_refusal_reports_one_checked_host_and_prevents_client_creation(
        self, discovery: ResolverHarness
    ) -> None:
        config = DatabaseConfig(arango_host="https://missing.invalid:9443")
        with structlog.testing.capture_logs() as records, patch.object(arango_writer, "ArangoClient") as client:
            with pytest.raises(ConnectionError, match="not resolvable") as failure:
                ArangoDBWriter(config)
        assert isinstance(failure.value.__cause__, socket.gaierror)
        assert client.call_count == 0
        assert len(discovery.lookup.calls) == 1
        assert any(
            record["event"] == "arango_dns_preflight_unavailable" and record["checked_hosts"] == 1 for record in records
        )
        assert not any(record["event"] == "arango_dns_preflight_finished" for record in records)

    def test_original_tls_url_credentials_and_declared_indexes_remain_unchanged(
        self, discovery: ResolverHarness, remote_arango_config: DatabaseConfig
    ) -> None:
        config = remote_arango_config
        discovery.lookup.answers["external-arango.invalid"] = discovery.lookup.addresses()
        harness = ArangoIndexWriterHarness(config)
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES["listOrgMarvisActions"]
        with patch.object(arango_writer, "ArangoClient", autospec=True, return_value=harness.client) as client:
            writer = ArangoDBWriter(config)
            try:
                result = writer.write([{"uuid": "action-1"}], "listOrgMarvisActions", strategy)
            finally:
                writer.close()
        client.assert_called_once_with(hosts=config.arango_host)
        assert harness.client.db.call_args_list[0].kwargs == {
            "username": config.arango_username,
            "password": config.arango_password,
        }
        collection = harness.database.collections["listOrgMarvisActions"]
        assert [entry.args[0] for entry in collection.handle.add_index.call_args_list] == [
            {"type": "persistent", "fields": [name]} for name in strategy["indexes"]
        ]
        assert len(strategy["indexes"]) == 5
        assert (result.success, result.records_written, result.records_failed) == (True, 1, 0)
        assert [call[0] for call in discovery.lookup.calls] == ["external-arango.invalid"]

    def test_resolved_preflight_does_not_change_driver_error_semantics(self, discovery: ResolverHarness) -> None:
        discovery.lookup.answers["arango.invalid"] = discovery.lookup.addresses()
        config = DatabaseConfig(arango_host="https://arango.invalid:9443")
        error = ArangoError("Controlled driver failure.")
        with patch.object(arango_writer, "ArangoClient") as client:
            client.return_value.db.side_effect = error
            with pytest.raises(ArangoError, match="Controlled driver failure") as failure:
                ArangoDBWriter(config)
        assert failure.value is error
        assert client.call_count == 1
        assert len(discovery.lookup.calls) == 1


class TestRedisConstructorPreflight:
    """Preserve the actual constructor's DNS cause and single-query contract."""

    def test_constructor_preserves_dns_cause_identity_and_one_lookup(self, discovery: ResolverHarness) -> None:
        error = socket.gaierror("Name or service not known")
        discovery.lookup.answers["localhost"] = error
        config = DatabaseConfig(redis_host="localhost", redis_port=6379)
        with patch("src.db.redis_writer.redis.Redis") as client:
            with pytest.raises(ConnectionError, match="not resolvable") as failure:
                RedisTimeSeriesWriter(config)
        assert failure.value.__cause__ is error
        assert len(discovery.lookup.calls) == 1
        assert discovery.lookup.calls == [("localhost", None, socket.AF_UNSPEC, socket.SOCK_STREAM)]
        assert client.call_count == 0

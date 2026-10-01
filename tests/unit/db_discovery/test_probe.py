"""Keep central TCP readiness separate from cached DNS discovery."""

from __future__ import annotations

import os
import socket
import time
from unittest.mock import patch

import pytest

from src import db
from tests.unit.db_discovery.fakes import ControlledSockets, ResolverHarness


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

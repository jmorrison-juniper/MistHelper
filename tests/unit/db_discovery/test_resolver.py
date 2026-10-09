"""Prove actual deadlines, expiring results, and finite DNS resources."""

from __future__ import annotations

import errno
import math
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from unittest.mock import patch

import pytest
import structlog

from src.foundation.persistence.db.host_resolver import ResolutionResult, ResolverLimits
from tests.unit.db_discovery.fakes import ResolverHarness


class TestLimitsAndErrors:
    """Reject invalid limits and surface lookup or worker failures."""

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("timeout_seconds", 0),
            ("timeout_seconds", -1),
            ("timeout_seconds", math.inf),
            ("timeout_seconds", math.nan),
            ("cache_ttl_seconds", 0),
            ("cache_ttl_seconds", math.inf),
            ("max_workers", 0),
            ("max_cache_entries", 0),
        ],
    )
    def test_invalid_limits_fail_with_a_checked_field(self, field, value) -> None:
        with structlog.testing.capture_logs() as records, pytest.raises(ValueError, match=field):
            ResolverLimits(**{field: value})
        assert records[-1]["event"] == "database_dns_invalid_limit"
        assert records[-1]["checked_limits"] == 1
        assert records[-1]["field"] == field

    @pytest.mark.parametrize(
        "error",
        [socket.gaierror(socket.EAI_AGAIN, "Controlled temporary failure."), TimeoutError("Controlled timeout.")],
    )
    def test_os_failure_has_an_explicit_cached_error(self, discovery: ResolverHarness, error: OSError) -> None:
        discovery.lookup.answers["db.invalid"] = error
        resolver = discovery.create()
        with structlog.testing.capture_logs() as records:
            first = resolver.resolve("db.invalid")
            second = resolver.resolve("db.invalid")
        assert first.addresses == ()
        assert first.error is error
        assert second is first
        assert len(discovery.lookup.calls) == 1
        assert any(record["event"] == "database_dns_failed" for record in records)
        assert not any(record["event"] == "database_dns_timeout" for record in records)

    @pytest.mark.parametrize(
        "error",
        [
            ValueError("Invalid controlled query."),
            UnicodeError("Invalid text."),
            RuntimeError("Resolver capability failed."),
        ],
    )
    def test_lookup_errors_propagate_without_success_results(
        self, discovery: ResolverHarness, error: Exception
    ) -> None:
        discovery.lookup.answers["db.invalid"] = error
        resolver = discovery.create()
        with pytest.raises(type(error), match=str(error)):
            resolver.resolve("db.invalid")
        assert resolver.resource_counts()["pending"] == 0
        assert resolver.resource_counts()["cached"] == 0
        discovery.lookup.answers["db.invalid"] = discovery.lookup.addresses()
        assert resolver.resolve("db.invalid").addresses == tuple(discovery.lookup.addresses())

    def test_worker_start_failure_leaves_no_pending_job(self, discovery: ResolverHarness) -> None:
        resolver = discovery.create()
        with patch(
            "src.foundation.persistence.db.host_resolver.Thread.start",
            side_effect=RuntimeError("Controlled worker capability."),
        ):
            with pytest.raises(RuntimeError, match="Controlled worker capability"):
                resolver.resolve("db.invalid")
        assert resolver.resource_counts() == {"workers": 0, "pending": 0, "queued": 0, "cached": 0}
        discovery.lookup.answers["db.invalid"] = discovery.lookup.addresses()
        assert resolver.resolve("db.invalid").error is None

    def test_empty_and_non_ip_answers_fail_with_checked_counts(self, discovery: ResolverHarness) -> None:
        discovery.lookup.answers["empty.invalid"] = []
        resolver = discovery.create()
        with structlog.testing.capture_logs() as records:
            empty = ResolutionResult.from_records([])
            non_ip_family = socket.AF_UNSPEC  # Not an IP family on any OS; AF_UNIX does not exist on Windows.
            non_ip = ResolutionResult.from_records([(non_ip_family, socket.SOCK_STREAM, 0, "", (1, b"controlled"))])
            worker_empty = resolver.resolve("empty.invalid")
        assert empty.addresses == ()
        assert isinstance(empty.error, socket.gaierror)
        assert non_ip.addresses == ()
        assert isinstance(non_ip.error, socket.gaierror)
        assert worker_empty.addresses == ()
        assert isinstance(worker_empty.error, socket.gaierror)
        assert any(
            record["event"] == "database_dns_unsupported_address" and record["checked_addresses"] == 1
            for record in records
        )
        assert [
            record["checked_addresses"]
            for record in records
            if record["event"] == "database_dns_addresses_check_finished"
        ] == [0, 1, 0]
        assert any(
            record["event"] == "database_dns_empty_result" and record["checked_queries"] == 1 for record in records
        )


class TestLookupCache:
    """Refresh each actual lookup identity after a finite monotonic period."""

    def test_positive_cache_expires_at_thirty_seconds(self, discovery: ResolverHarness) -> None:
        discovery.lookup.answers["db.invalid"] = discovery.lookup.addresses()
        resolver = discovery.create()
        first = resolver.resolve("db.invalid")
        discovery.clock.advance(29.999)
        assert resolver.resolve("db.invalid") is first
        assert len(discovery.lookup.calls) == 1
        discovery.clock.advance(0.001)
        discovery.lookup.answers["db.invalid"] = discovery.lookup.addresses("192.0.2.11")
        assert resolver.resolve("db.invalid").addresses == tuple(discovery.lookup.addresses("192.0.2.11"))
        assert len(discovery.lookup.calls) == 2

    def test_negative_cache_expiry_allows_later_database(self, discovery: ResolverHarness) -> None:
        resolver = discovery.create()
        first = resolver.resolve("db.invalid")
        discovery.lookup.answers["db.invalid"] = discovery.lookup.addresses()
        discovery.clock.advance(29.999)
        assert resolver.resolve("db.invalid") is first
        assert len(discovery.lookup.calls) == 1
        discovery.clock.advance(0.001)
        recovered = resolver.resolve("db.invalid")
        assert recovered.addresses == tuple(discovery.lookup.addresses())
        assert recovered.error is None
        assert len(discovery.lookup.calls) == 2

    def test_name_family_and_socket_options_have_distinct_cache_keys(self, discovery: ResolverHarness) -> None:
        discovery.lookup.answers.update(
            {"db.invalid": discovery.lookup.addresses(), "other.invalid": discovery.lookup.addresses()}
        )
        resolver = discovery.create()
        for hostname, family, socket_type in [
            ("db.invalid", socket.AF_UNSPEC, socket.SOCK_STREAM),
            ("db.invalid", socket.AF_INET, socket.SOCK_STREAM),
            ("db.invalid", socket.AF_UNSPEC, 0),
            ("other.invalid", socket.AF_UNSPEC, socket.SOCK_STREAM),
        ]:
            assert resolver.resolve(hostname, family, socket_type).error is None
            assert resolver.resolve(hostname, family, socket_type).error is None
        assert discovery.lookup.calls == [
            ("db.invalid", None, socket.AF_UNSPEC, socket.SOCK_STREAM),
            ("db.invalid", None, socket.AF_INET, socket.SOCK_STREAM),
            ("db.invalid", None, socket.AF_UNSPEC, 0),
            ("other.invalid", None, socket.AF_UNSPEC, socket.SOCK_STREAM),
        ]

    def test_cache_stays_finite_and_rechecks_evicted_name(self, discovery: ResolverHarness) -> None:
        resolver = discovery.create()
        for index in range(129):
            hostname = f"db-{index}.invalid"
            discovery.lookup.answers[hostname] = discovery.lookup.addresses()
            assert resolver.resolve(hostname).error is None
        assert resolver.resource_counts()["cached"] == 128
        assert len(discovery.lookup.calls) == 129
        assert resolver.resolve("db-0.invalid").error is None
        assert len(discovery.lookup.calls) == 130
        assert resolver.resource_counts()["cached"] == 128

    def test_wall_clock_changes_do_not_change_cache_time(self, discovery: ResolverHarness, monkeypatch) -> None:
        resolver = discovery.create()
        first = resolver.resolve("db.invalid")
        monkeypatch.setattr(time, "time", lambda: -1_000_000.0)
        assert resolver.resolve("db.invalid") is first
        discovery.clock.advance(30)
        assert resolver.resolve("db.invalid").addresses == ()
        assert len(discovery.lookup.calls) == 2


class TestCallerDeadline:
    """Measure real waits separately from the controlled cache clock."""

    def test_default_blocked_lookup_returns_in_about_one_second(
        self, discovery: ResolverHarness, record_property
    ) -> None:
        discovery.lookup.blocked_hosts.add("db.invalid")
        resolver = discovery.create()
        started = time.monotonic()
        result = resolver.resolve("db.invalid")
        elapsed = time.monotonic() - started
        record_property("caller_elapsed_seconds", elapsed)
        assert 0.9 <= elapsed < 1.3, elapsed
        assert result.addresses == ()
        assert isinstance(result.error, TimeoutError)
        assert discovery.lookup.calls == [("db.invalid", None, socket.AF_UNSPEC, socket.SOCK_STREAM)]
        assert resolver.resource_counts() == {"workers": 1, "pending": 1, "queued": 0, "cached": 1}
        discovery.drain(resolver)

    def test_timeout_cache_prevents_repeated_waits_and_workers(self, discovery: ResolverHarness) -> None:
        discovery.lookup.blocked_hosts.add("db.invalid")
        resolver = discovery.create(ResolverLimits(timeout_seconds=0.03))
        first = resolver.resolve("db.invalid")
        started = time.monotonic()
        results = [resolver.resolve("db.invalid") for _request in range(20)]
        assert time.monotonic() - started < 0.1
        assert all(result is first for result in results)
        assert len(discovery.lookup.calls) == 1
        assert resolver.resource_counts()["pending"] == 1
        discovery.drain(resolver)

    def test_expiry_does_not_duplicate_still_blocked_work(self, discovery: ResolverHarness) -> None:
        discovery.lookup.blocked_hosts.add("db.invalid")
        resolver = discovery.create(ResolverLimits(timeout_seconds=0.03))
        assert isinstance(resolver.resolve("db.invalid").error, TimeoutError)
        discovery.clock.advance(30)
        assert isinstance(resolver.resolve("db.invalid").error, TimeoutError)
        assert len(discovery.lookup.calls) == 1
        assert resolver.resource_counts()["workers"] == 1
        assert resolver.resource_counts()["pending"] == 1
        discovery.drain(resolver)
        discovery.lookup.answers["db.invalid"] = discovery.lookup.addresses()
        discovery.clock.advance(30)
        assert resolver.resolve("db.invalid").error is None
        assert len(discovery.lookup.calls) == 2

    def test_late_completion_does_not_extend_negative_expiry(self, discovery: ResolverHarness) -> None:
        discovery.lookup.answers["db.invalid"] = discovery.lookup.addresses()
        discovery.lookup.blocked_hosts.add("db.invalid")
        resolver = discovery.create(ResolverLimits(timeout_seconds=0.03))
        first = resolver.resolve("db.invalid")
        discovery.clock.advance(10)
        discovery.drain(resolver)
        assert resolver.resolve("db.invalid") is first
        discovery.clock.advance(20)
        assert resolver.resolve("db.invalid").error is None
        assert len(discovery.lookup.calls) == 2

    def test_socket_timeout_is_not_the_caller_deadline(self, discovery: ResolverHarness) -> None:
        discovery.lookup.answers["db.invalid"] = TimeoutError("Controlled immediate resolver timeout.")
        resolver = discovery.create()
        started = time.monotonic()
        with structlog.testing.capture_logs() as records:
            result = resolver.resolve("db.invalid")
        assert time.monotonic() - started < 0.3
        assert isinstance(result.error, socket.timeout)
        assert any(record["event"] == "database_dns_failed" for record in records)
        assert not any(record["event"] == "database_dns_timeout" for record in records)


class TestConcurrentResources:
    """Prove single-flight, finite outstanding work, and recovered capacity."""

    def test_parallel_same_hostname_shares_one_query(self, discovery: ResolverHarness) -> None:
        discovery.lookup.answers["db.invalid"] = discovery.lookup.addresses()
        discovery.lookup.blocked_hosts.add("db.invalid")
        resolver = discovery.create()
        barrier = Barrier(12)
        with ThreadPoolExecutor(max_workers=12) as callers:
            futures = [callers.submit(lambda: (barrier.wait(), resolver.resolve("db.invalid"))[1]) for _ in range(12)]
            assert discovery.lookup.wait_for_calls(1) is True
            discovery.lookup.release.set()
            results = [future.result(timeout=2) for future in futures]
        assert len(discovery.lookup.calls) == 1
        assert all(result.addresses == tuple(discovery.lookup.addresses()) for result in results)
        assert resolver.resource_counts()["workers"] <= 2
        assert resolver.resource_counts()["pending"] == 0

    def test_blocked_distinct_names_cannot_create_extra_work(self, discovery: ResolverHarness) -> None:
        names = [f"blocked-{index}.invalid" for index in range(12)]
        discovery.lookup.blocked_hosts.update(names)
        resolver = discovery.create(ResolverLimits(timeout_seconds=0.04))
        with ThreadPoolExecutor(max_workers=12) as callers:
            results = list(callers.map(resolver.resolve, names))
        counts = resolver.resource_counts()
        assert len(discovery.lookup.calls) == 2
        assert counts == {"workers": 2, "pending": 2, "queued": 0, "cached": 2}
        assert sum(isinstance(result.error, TimeoutError) for result in results) == 2
        assert sum(isinstance(result.error, OSError) and result.error.errno == errno.EBUSY for result in results) == 10
        discovery.drain(resolver)
        discovery.lookup.answers["recovered.invalid"] = discovery.lookup.addresses()
        assert resolver.resolve("recovered.invalid").error is None
        assert len(discovery.lookup.calls) == 3
        assert resolver.resource_counts()["pending"] == 0

    def test_many_timeout_periods_keep_the_same_finite_workers(self, discovery: ResolverHarness) -> None:
        discovery.lookup.blocked_hosts.update({"first.invalid", "second.invalid"})
        resolver = discovery.create(ResolverLimits(timeout_seconds=0.005))
        assert isinstance(resolver.resolve("first.invalid").error, TimeoutError)
        assert isinstance(resolver.resolve("second.invalid").error, TimeoutError)
        for period in range(10):
            discovery.clock.advance(30)
            assert isinstance(resolver.resolve("first.invalid").error, TimeoutError)
            assert resolver.resolve(f"capacity-{period}.invalid").error.errno == errno.EBUSY
            assert resolver.resource_counts()["workers"] == 2
            assert resolver.resource_counts()["pending"] == 2
            assert resolver.resource_counts()["queued"] == 0
        assert len(discovery.lookup.calls) == 2
        assert resolver.resource_counts()["cached"] <= 128
        discovery.drain(resolver)

    def test_cache_eviction_does_not_duplicate_an_active_lookup(self, discovery: ResolverHarness) -> None:
        discovery.lookup.blocked_hosts.add("blocked.invalid")
        discovery.lookup.answers["other.invalid"] = discovery.lookup.addresses()
        resolver = discovery.create(ResolverLimits(timeout_seconds=0.03, max_cache_entries=1))
        assert isinstance(resolver.resolve("blocked.invalid").error, TimeoutError)
        assert resolver.resolve("other.invalid").error is None
        assert isinstance(resolver.resolve("blocked.invalid").error, TimeoutError)
        assert [call[0] for call in discovery.lookup.calls].count("blocked.invalid") == 1
        assert resolver.resource_counts()["cached"] == 1
        discovery.drain(resolver)

    def test_failed_capacity_is_not_a_permanent_negative_cache(self, discovery: ResolverHarness) -> None:
        discovery.lookup.blocked_hosts.update({"first.invalid", "second.invalid"})
        resolver = discovery.create(ResolverLimits(timeout_seconds=0.01))
        resolver.resolve("first.invalid")
        resolver.resolve("second.invalid")
        refused = resolver.resolve("later.invalid")
        assert refused.addresses == ()
        assert refused.error.errno == errno.EBUSY
        assert resolver.resource_counts()["cached"] == 2
        discovery.drain(resolver)
        discovery.lookup.answers["later.invalid"] = discovery.lookup.addresses()
        assert resolver.resolve("later.invalid").error is None
        assert [call[0] for call in discovery.lookup.calls].count("later.invalid") == 1


class TestWorkerShutdown:
    """Keep blocked helpers from holding the process or leaking after release."""

    def test_close_has_one_finite_budget_for_all_blocked_workers(self, discovery: ResolverHarness) -> None:
        discovery.lookup.blocked_hosts.update({"first.invalid", "second.invalid"})
        resolver = discovery.create(ResolverLimits(timeout_seconds=0.01))
        resolver.resolve("first.invalid")
        resolver.resolve("second.invalid")
        started = time.monotonic()
        with structlog.testing.capture_logs() as records:
            resolver.close(timeout=0.03)
        assert time.monotonic() - started < 0.2
        assert resolver.resource_counts()["workers"] == 2
        assert any(
            record["event"] == "database_dns_shutdown_deadline" and record["remaining_workers"] == 2
            for record in records
        )
        discovery.lookup.release.set()
        resolver.close(timeout=1)
        assert resolver.resource_counts() == {"workers": 0, "pending": 0, "queued": 0, "cached": 2}

    def test_closed_resolver_rejects_new_queries(self, discovery: ResolverHarness) -> None:
        resolver = discovery.create()
        resolver.close()
        with pytest.raises(RuntimeError, match="resolver is closed"):
            resolver.resolve("db.invalid")
        assert resolver.resource_counts() == {"workers": 0, "pending": 0, "queued": 0, "cached": 0}

    @pytest.mark.parametrize("timeout", [-1, math.inf, math.nan])
    def test_invalid_shutdown_budget_raises(self, discovery: ResolverHarness, timeout: float) -> None:
        resolver = discovery.create()
        with pytest.raises(ValueError, match="finite and nonnegative"):
            resolver.close(timeout)
        assert resolver.resource_counts()["workers"] == 0

    def test_daemon_lookup_cannot_hold_process_shutdown(self) -> None:
        script = (
            "from threading import Event\n"
            "from src.foundation.persistence.db.host_resolver import BoundedHostResolver, ResolverLimits\n"
            "blocked = Event()\n"
            "def lookup(hostname, port, family, socket_type):\n"
            "    blocked.wait()\n"
            "    return []\n"
            "resolver = BoundedHostResolver(ResolverLimits(timeout_seconds=0.02), lookup)\n"
            "result = resolver.resolve('controlled.invalid')\n"
            "print('checked_dns_shutdown=1 timeout=' + str(isinstance(result.error, TimeoutError)))\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=Path(__file__).resolve().parents[3],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "checked_dns_shutdown=1 timeout=True" in result.stdout

    def test_unresolved_and_unicode_names_keep_controlled_identity(self, discovery: ResolverHarness) -> None:
        hostname = "db-\u00e9.invalid"
        discovery.lookup.answers[hostname] = discovery.lookup.addresses()
        resolver = discovery.create()
        assert resolver.resolve(hostname).addresses == tuple(discovery.lookup.addresses())
        assert discovery.lookup.calls == [(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)]

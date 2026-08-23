"""Tests for the bounded operation run registry in the web portal.

Issue #1860 reported unbounded growth. The run registry kept every run, and
each run kept one entry for every log record. These tests hold the caps in
place, so the portal worker cannot grow until an out-of-memory kill.
"""

import json
import logging
import time

import pytest

from web_portal.services.operation import (
    DEFAULT_RUN_HISTORY_MAX,
    DEFAULT_RUN_LOG_MAX_ENTRIES,
    DEFAULT_RUN_RETENTION_SECONDS,
    OperationExecutor,
    _RunLogHandler,
)

# The three environment variables the operator uses to size the caps.
CAP_VARIABLES = (
    "PORTAL_RUN_LOG_MAX_ENTRIES",
    "PORTAL_RUN_HISTORY_MAX",
    "PORTAL_RUN_RETENTION_SECONDS",
)


def _menu_actions() -> dict:
    """Return three harmless menu entries for the executor under test."""
    return {
        "11": (lambda: None, "Export the organization inventory"),
        "12": (lambda: None, "Export the organization devices"),
        "13": (lambda: None, "Export the organization sites"),
    }


def _make_record(message: str) -> logging.LogRecord:
    """Return one user-facing log record for the run log handler."""
    return logging.LogRecord(
        name="misthelper",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
    )


@pytest.fixture
def executor_factory(monkeypatch):
    """Return a factory that builds an executor with small caps."""
    created = []

    def _build(log_cap: int, history_cap: int, retention: int) -> OperationExecutor:
        monkeypatch.setenv("PORTAL_RUN_LOG_MAX_ENTRIES", str(log_cap))
        monkeypatch.setenv("PORTAL_RUN_HISTORY_MAX", str(history_cap))
        monkeypatch.setenv("PORTAL_RUN_RETENTION_SECONDS", str(retention))
        executor = OperationExecutor(_menu_actions(), None, None, None)
        created.append(executor)
        return executor

    yield _build
    for executor in created:
        executor._pool.shutdown(wait=False)


def _emit_records(run: dict, count: int) -> None:
    """Send the given count of log records into the run record."""
    handler = _RunLogHandler(run, None)
    for index in range(count):
        handler.handle(_make_record(f"Fetched batch {index}"))


def test_registry_stays_at_the_cap_when_runs_exceed_it(executor_factory):
    """The registry keeps only the most recent finished runs."""
    executor = executor_factory(log_cap=5, history_cap=3, retention=3600)
    run_ids = []
    for _ in range(10):
        run = executor._create_run("11")
        run["status"] = "completed"
        run["completed_at"] = time.time()
        run_ids.append(run["run_id"])
        assert len(executor._runs) <= 4
    executor._prune_runs()
    assert len(executor._runs) == 3
    assert set(executor._runs) == set(run_ids[-3:])


def test_run_log_list_stops_at_the_cap(executor_factory):
    """A run log holds at most the capped number of entries."""
    executor = executor_factory(log_cap=5, history_cap=3, retention=3600)
    run = executor._create_run("11")
    _emit_records(run, 12)
    assert len(run["log_messages"]) == 5
    assert run["dropped_log_count"] == 7


def test_prune_never_evicts_a_pending_or_running_run(executor_factory):
    """A pending run and a running run survive every prune."""
    executor = executor_factory(log_cap=5, history_cap=1, retention=1)
    pending = executor._create_run("11")
    running = executor._create_run("12")
    running["status"] = "running"
    for index in range(5):
        finished = executor._create_run("13")
        finished["status"] = "completed"
        finished["completed_at"] = 1000.0 + index
    executor._prune_runs()
    assert pending["run_id"] in executor._runs
    assert running["run_id"] in executor._runs
    assert len(executor._runs) == 2


def test_retention_removes_a_finished_run(executor_factory):
    """A finished run older than the retention period leaves the registry."""
    executor = executor_factory(log_cap=5, history_cap=10, retention=60)
    stale = executor._create_run("11")
    stale["status"] = "completed"
    stale["completed_at"] = time.time() - 600
    fresh = executor._create_run("12")
    fresh["status"] = "completed"
    fresh["completed_at"] = time.time()
    executor._prune_runs()
    assert stale["run_id"] not in executor._runs
    assert fresh["run_id"] in executor._runs


def test_run_response_reports_the_dropped_log_count(executor_factory):
    """The run response tells the operator how many entries the cap dropped."""
    executor = executor_factory(log_cap=2, history_cap=3, retention=3600)
    run = executor._create_run("11")
    _emit_records(run, 5)
    response = executor.get_run_status(run["run_id"])
    assert response["dropped_log_count"] == 3
    assert len(response["log_messages"]) == 2
    assert response["log_messages"][0]["message"] == "Fetched batch 3"


def test_run_response_holds_plain_lists_for_json(executor_factory):
    """The response holds plain lists, so Flask can encode it as JSON."""
    executor = executor_factory(log_cap=3, history_cap=3, retention=3600)
    run = executor._create_run("11")
    _emit_records(run, 4)
    response = executor.get_run_status(run["run_id"])
    assert isinstance(response["log_messages"], list)
    assert json.loads(json.dumps(response))["dropped_log_count"] == 1


def test_caps_use_the_documented_defaults_when_unset(monkeypatch):
    """An unset environment leaves the documented default caps in place."""
    for name in CAP_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    executor = OperationExecutor(_menu_actions(), None, None, None)
    assert executor._log_max_entries == DEFAULT_RUN_LOG_MAX_ENTRIES
    assert executor._history_max == DEFAULT_RUN_HISTORY_MAX
    assert executor._retention_seconds == DEFAULT_RUN_RETENTION_SECONDS
    executor._pool.shutdown(wait=False)


@pytest.mark.parametrize("bad_value", ["abc", "0", "-5", ""])
def test_caps_reject_an_unusable_environment_value(monkeypatch, bad_value):
    """An unusable environment value falls back to the default cap."""
    monkeypatch.setenv("PORTAL_RUN_LOG_MAX_ENTRIES", bad_value)
    executor = OperationExecutor(_menu_actions(), None, None, None)
    assert executor._log_max_entries == DEFAULT_RUN_LOG_MAX_ENTRIES
    executor._pool.shutdown(wait=False)

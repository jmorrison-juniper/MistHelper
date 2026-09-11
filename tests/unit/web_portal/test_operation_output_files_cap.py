"""Tests for the bounded output file list in a web portal run record.

Issue #1870: pull request #1867 bounded the two log lists, and it left
``run["output_files"]`` without a cap. One run against a large organization
appends one distinct name for each site, so the list still grew without a
bound. These tests hold the new cap in place.
"""

import json
import logging

import pytest

from web_portal.services.operation import (
    DEFAULT_RUN_OUTPUT_FILES_MAX,
    OperationExecutor,
    _RunLogHandler,
)


def _menu_actions() -> dict:
    """Return one harmless menu entry for the executor under test."""
    return {"11": (lambda: None, "Export the organization inventory")}


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


def _emit_output_files(run: dict, count: int) -> None:
    """Report the given count of distinct output files into the run record."""
    handler = _RunLogHandler(run, None)
    for index in range(count):
        handler.handle(_make_record(f"wrote 10 rows to data/site_{index}.csv"))


@pytest.fixture
def executor_factory(monkeypatch):
    """Return a factory that builds an executor with a small output file cap."""
    created = []

    def _build(output_files_cap: int) -> OperationExecutor:
        monkeypatch.setenv("PORTAL_RUN_OUTPUT_FILES_MAX", str(output_files_cap))
        executor = OperationExecutor(_menu_actions(), None, None, None)
        created.append(executor)
        return executor

    yield _build
    for executor in created:
        executor._pool.shutdown(wait=False)


def test_output_files_stop_at_the_cap(executor_factory):
    """The output file list holds at most the capped number of names."""
    executor = executor_factory(output_files_cap=4)
    run = executor._create_run("11")
    _emit_output_files(run, 20)
    assert len(run["output_files"]) == 4


def test_output_files_keep_the_newest_names(executor_factory):
    """The cap discards the oldest name, so the newest output stays visible."""
    executor = executor_factory(output_files_cap=3)
    run = executor._create_run("11")
    _emit_output_files(run, 10)
    assert list(run["output_files"]) == ["site_7.csv", "site_8.csv", "site_9.csv"]


def test_output_files_still_reject_a_duplicate_name(executor_factory):
    """One file that the operation writes twice adds one entry."""
    executor = executor_factory(output_files_cap=5)
    run = executor._create_run("11")
    handler = _RunLogHandler(run, None)
    for _ in range(4):
        handler.handle(_make_record("wrote 10 rows to data/site_0.csv"))
    assert list(run["output_files"]) == ["site_0.csv"]
    assert run["dropped_output_file_count"] == 0


def test_run_response_reports_the_dropped_output_file_count(executor_factory):
    """The response tells the operator how many names the cap dropped."""
    executor = executor_factory(output_files_cap=2)
    run = executor._create_run("11")
    _emit_output_files(run, 7)
    response = executor.get_run_status(run["run_id"])
    assert response["dropped_output_file_count"] == 5
    assert len(response["output_files"]) == 2


def test_run_response_holds_a_plain_output_file_list(executor_factory):
    """The response holds a plain list, so Flask can encode it as JSON."""
    executor = executor_factory(output_files_cap=3)
    run = executor._create_run("11")
    _emit_output_files(run, 5)
    response = executor.get_run_status(run["run_id"])
    assert isinstance(response["output_files"], list)
    assert json.loads(json.dumps(response))["dropped_output_file_count"] == 2


def test_complete_event_holds_a_plain_output_file_list(executor_factory):
    """The completion event holds a plain list, so the SSE stream can encode it."""
    executor = executor_factory(output_files_cap=3)
    run = executor._create_run("11")
    _emit_output_files(run, 5)
    published = []
    executor._event_bus = type("Bus", (), {"publish": lambda _self, name, data: published.append((name, data))})()
    executor._publish_complete(run)
    assert isinstance(published[0][1]["output_files"], list)
    assert json.dumps(published[0][1])


def test_output_files_cap_uses_the_documented_default_when_unset(monkeypatch):
    """An unset environment leaves the documented default cap in place."""
    monkeypatch.delenv("PORTAL_RUN_OUTPUT_FILES_MAX", raising=False)
    executor = OperationExecutor(_menu_actions(), None, None, None)
    assert executor._output_files_max == DEFAULT_RUN_OUTPUT_FILES_MAX
    executor._pool.shutdown(wait=False)


@pytest.mark.parametrize("bad_value", ["abc", "0", "-5", ""])
def test_output_files_cap_warns_about_an_unusable_value(monkeypatch, caplog, bad_value):
    """An unusable environment value falls back to the default and warns."""
    monkeypatch.setenv("PORTAL_RUN_OUTPUT_FILES_MAX", bad_value)
    with caplog.at_level(logging.WARNING):
        executor = OperationExecutor(_menu_actions(), None, None, None)
    assert executor._output_files_max == DEFAULT_RUN_OUTPUT_FILES_MAX
    assert "PORTAL_RUN_OUTPUT_FILES_MAX" in caplog.text
    executor._pool.shutdown(wait=False)

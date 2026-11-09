"""Verify that portal input values stay out of interceptor diagnostics."""

import builtins
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.foundation.models.operation_outcome import OperationOutcome
from web_portal.services.input_hook import InputInterceptor, web_input_context
from web_portal.services.operation import OperationExecutor


def test_queued_answers_keep_order_without_logging_values(caplog):
    """Keep ordered values and a useful diagnostic without exposing the answers."""
    answers = ["example-person@example.invalid", "synthetic-code-4821", "", 17]
    with caplog.at_level(logging.DEBUG, logger="web_portal.services.input_hook"):
        with web_input_context(answers):
            received = [InputInterceptor._patched_input("Synthetic prompt") for _ in answers]
            with pytest.raises(EOFError, match="Web input queue exhausted"):
                InputInterceptor._patched_input()

    assert received == ["example-person@example.invalid", "synthetic-code-4821", "", "17"]
    assert [record.getMessage() for record in caplog.records] == ["InputInterceptor: consumed queued answer"] * len(
        answers
    )
    assert all(not record.args for record in caplog.records)


def test_queue_is_cleared_after_operation_failure(monkeypatch):
    """Restore console input when an operation exits with an exception."""
    cli_input = Mock(return_value="cli-answer")
    monkeypatch.setattr(InputInterceptor, "_original_input", cli_input)
    with pytest.raises(RuntimeError, match="synthetic failure"):
        with web_input_context(["unused"]):
            raise RuntimeError("synthetic failure")
    assert InputInterceptor._patched_input("CLI prompt: ") == "cli-answer"
    cli_input.assert_called_once_with("CLI prompt: ")


def test_cli_fallback_and_empty_queue_are_distinct(monkeypatch):
    """Preserve the CLI prompt and reject an empty web queue without a CLI read."""
    cli_input = Mock(return_value="cli-answer")
    monkeypatch.setattr(InputInterceptor, "_original_input", cli_input)
    InputInterceptor.clear_queue()
    assert InputInterceptor._patched_input("CLI prompt: ") == "cli-answer"
    cli_input.assert_called_once_with("CLI prompt: ")

    with web_input_context([]):
        with pytest.raises(EOFError, match="Web input queue exhausted"):
            InputInterceptor._patched_input("Web prompt: ")
    cli_input.assert_called_once_with("CLI prompt: ")


def test_concurrent_queues_preserve_independent_values():
    """Keep two overlapping operations on their own positional queues."""
    barrier = threading.Barrier(2)

    def consume(answers):
        with web_input_context(answers):
            first = InputInterceptor._patched_input()
            barrier.wait(timeout=10)
            second = InputInterceptor._patched_input()
            with pytest.raises(EOFError, match="Web input queue exhausted"):
                InputInterceptor._patched_input()
        return [first, second]

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(consume, ["alpha-one", "alpha-two"])
        second = pool.submit(consume, ["beta-one", "beta-two"])
        assert first.result(timeout=10) == ["alpha-one", "alpha-two"]
        assert second.result(timeout=10) == ["beta-one", "beta-two"]


def test_portal_execution_does_not_capture_or_publish_queued_values(monkeypatch, tmp_path, caplog):
    """Exercise the real run capture and event publication with synthetic input."""
    answers = ["example-person@example.invalid", "synthetic-code-4821"]
    received = []
    event_bus = Mock()
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setattr(builtins, "input", InputInterceptor._patched_input)

    def handler():
        received.extend([input("Email: "), input("Code: ")])
        return OperationOutcome("completed", "Synthetic operation completed.")

    executor = OperationExecutor(
        {"11": SimpleNamespace(handler=handler, title="Synthetic operation")}, None, None, event_bus
    )
    run = executor._create_run("11")
    try:
        with caplog.at_level(logging.DEBUG, logger="web_portal.services.input_hook"):
            future = executor._pool.submit(executor._execute_operation, run, {"input_answers": answers})
            future.result(timeout=10)
        assert run["status"] == "completed"
        assert received == answers
        captured = [entry["message"] for key in ("log_messages", "debug_messages") for entry in run[key]]
        published = [call.args[1] for call in event_bus.publish.call_args_list]
        assert captured.count("InputInterceptor: consumed queued answer") == 2
        assert sum(event.get("message") == "InputInterceptor: consumed queued answer" for event in published) == 2
        for answer in answers:
            assert answer not in repr(captured)
            assert answer not in repr(published)
            assert answer not in caplog.text
    finally:
        executor.shutdown(10)

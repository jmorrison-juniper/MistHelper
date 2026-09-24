"""Unit tests for the refusal record of the insight metric exports (issue #3267)."""

from __future__ import annotations  # WHY: Keep the annotations cheap to evaluate.

import dataclasses  # WHY: Prove that a refusal record cannot change after the operation stores it.
import logging  # WHY: Read the warning lines and the operator lines of the refusal record.
from types import SimpleNamespace  # WHY: Build a response object with a real status value.
from typing import Any  # WHY: Type the loose bodies that the Mist API can return.
from unittest.mock import MagicMock  # WHY: Stand in for a response that holds no integer status.

import pytest  # WHY: Use the caplog fixture and the parametrize marker.

from src.export.site_insights.metric_refusals import MetricRefusal, MetricRefusalLog  # WHY: The code under test.


def answer(status_code: Any, data: Any = None) -> SimpleNamespace:
    """Return a response object in the shape of a mistapi APIResponse."""
    return SimpleNamespace(status_code=status_code, data=data)  # WHY: Only the status and the body matter.


def operator_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Return the operator lines, which start with an exclamation mark."""
    return [record.getMessage() for record in caplog.records if record.getMessage().startswith("!")]


@pytest.mark.parametrize("status_code", [200, 204, 399])  # WHY: Each status below 400 is not a refusal.
def test_record_ignores_an_answer_below_400(status_code: int) -> None:
    """A status below 400 is not a refusal, so the log stays empty."""
    refusals = MetricRefusalLog("device insight")  # WHY: A new log for one run.
    assert refusals.record("tx_bps", answer(status_code, {"results": []})) is False  # WHY: Not refused.
    assert refusals.refusals == []  # WHY: Nothing was stored.


@pytest.mark.parametrize("status_code", [None, "400", MagicMock(name="status")])  # WHY: No integer status.
def test_record_ignores_an_answer_without_an_integer_status(status_code: Any) -> None:
    """A response without an integer status keeps the old path of the caller."""
    refusals = MetricRefusalLog("device insight")  # WHY: A new log for one run.
    assert refusals.record("tx_bps", answer(status_code, {"detail": "text"})) is False  # WHY: Not refused.
    assert refusals.refusals == []  # WHY: Nothing was stored.


def test_record_ignores_an_object_without_a_status() -> None:
    """A plain body without a status attribute is not a refusal."""
    refusals = MetricRefusalLog("device insight")  # WHY: A new log for one run.
    assert refusals.record("tx_bps", {"detail": "text"}) is False  # WHY: A dict holds no status attribute.


@pytest.mark.parametrize("status_code", [400, 404, 429, 500])  # WHY: Each status of 400 or more is a refusal.
def test_record_stores_each_refusal(status_code: int) -> None:
    """A status of 400 or more becomes one refusal with the metric, the status, and the reason."""
    refusals = MetricRefusalLog("device insight")  # WHY: A new log for one run.
    body = {"detail": "port_id is required"}  # WHY: The body of a recorded refusal.
    assert refusals.record("port-metrics", answer(status_code, body)) is True  # WHY: Refused.
    assert refusals.refusals == [MetricRefusal("port-metrics", status_code, "port_id is required")]  # WHY: Stored.


def test_record_logs_a_warning(caplog: pytest.LogCaptureFixture) -> None:
    """Each refusal writes one warning with the metric, the status, and the reason."""
    refusals = MetricRefusalLog("device insight")  # WHY: A new log for one run.
    with caplog.at_level(logging.WARNING):  # WHY: Capture the warning line.
        refusals.record("port-metrics", answer(400, {"detail": "port_id is required"}))  # WHY: One refusal.
    warnings = [record.getMessage() for record in caplog.records if record.levelno == logging.WARNING]  # WHY: Read.
    assert warnings == [  # WHY: One warning line names the scope, the metric, the status, and the reason.
        "The Mist API refused device insight metric port-metrics with HTTP 400: port_id is required"
    ]


@pytest.mark.parametrize(  # WHY: Mist error bodies use one of three keys for the reason.
    ("body", "expected"),
    [
        ({"detail": "first"}, "first"),
        ({"error": "second"}, "second"),
        ({"message": "third"}, "third"),
        ({"detail": "", "error": "second"}, "second"),
        ("a plain text body", "a plain text body"),
    ],
)
def test_reason_reads_the_first_known_key(body: Any, expected: str) -> None:
    """The reason comes from the first key that holds text, or from a plain text body."""
    assert MetricRefusalLog.reason(body) == expected  # WHY: The operator reads the text of the Mist API.


@pytest.mark.parametrize(  # WHY: The live site insight answers hold the reason in the key details (issue #3266).
    ("body", "expected"),
    [
        ({"details": "unknown"}, "unknown"),
        ({"detail": "first", "details": "second"}, "first"),
        ({"details": "", "error": "third"}, "third"),
    ],
)
def test_reason_reads_the_details_key_after_the_detail_key(body: Any, expected: str) -> None:
    """FR-008 of #3266: the key details holds a reason, and the key detail stays first."""
    assert MetricRefusalLog.reason(body) == expected  # WHY: The operator reads the reason that the body holds.


@pytest.mark.parametrize("body", [{}, [], None, "", {"other": 1}, "   "])  # WHY: Bodies that hold no reason.
def test_reason_names_no_reason_for_an_empty_body(body: Any) -> None:
    """A body without a reason gives a fixed text, so the operator line is never empty."""
    assert MetricRefusalLog.reason(body) == MetricRefusalLog.NO_REASON  # WHY: A fixed, known text.


def test_reason_is_ascii_on_one_line_and_short() -> None:
    """FR-004: the reason holds ASCII characters only, on one line, with 200 characters or fewer."""
    body = {"detail": "caf\u00e9 is\r\nrefused " + "x" * 500}  # WHY: Text that is not ASCII, a line break, length.
    reason = MetricRefusalLog.reason(body)  # WHY: Build the reason.
    assert reason.isascii()  # WHY: The log must stay ASCII.
    assert "\n" not in reason and "\r" not in reason  # WHY: A line break could forge a second log line.
    assert len(reason) <= MetricRefusalLog.REASON_LIMIT  # WHY: Keep the operator line short.
    assert reason.startswith("caf? is refused x")  # WHY: The text keeps its meaning.


def test_report_writes_nothing_without_refusals(caplog: pytest.LogCaptureFixture) -> None:
    """A run without a refusal adds no operator line."""
    refusals = MetricRefusalLog("device insight")  # WHY: A new log for one run.
    with caplog.at_level(logging.INFO):  # WHY: Capture every line.
        refusals.report("Branch-SSR")  # WHY: Report an empty log.
    assert caplog.records == []  # WHY: Nothing to tell the operator.


def test_report_writes_a_heading_and_one_line_for_each_refusal(caplog: pytest.LogCaptureFixture) -> None:
    """FR-003: the operator reads one heading and one line for each refused metric."""
    refusals = MetricRefusalLog("device insight")  # WHY: A new log for one run.
    refusals.record("port-metrics", answer(400, {"detail": "port_id is required"}))  # WHY: First refusal.
    refusals.record("top-flow-by-src", answer(400, {"detail": "only for switch devices"}))  # WHY: Second refusal.
    caplog.clear()  # WHY: Read only the report lines.
    with caplog.at_level(logging.INFO):  # WHY: Capture the report lines.
        refusals.report("Branch-SSR")  # WHY: Report the two refusals.
    assert operator_lines(caplog) == [  # WHY: One heading, then one line for each refusal in order.
        "! The Mist API refused 2 device insight metrics for Branch-SSR:",
        "!   port-metrics: HTTP 400, port_id is required",
        "!   top-flow-by-src: HTTP 400, only for switch devices",
    ]


def test_clear_empties_the_log() -> None:
    """FR-005: a cleared log holds no refusal of an earlier run."""
    refusals = MetricRefusalLog("device insight")  # WHY: A new log for one run.
    refusals.record("port-metrics", answer(400, {"detail": "port_id is required"}))  # WHY: One refusal.
    refusals.clear()  # WHY: Start the next run.
    assert refusals.refusals == []  # WHY: The earlier refusal is gone.


def test_a_refusal_is_immutable() -> None:
    """A stored refusal cannot change after the log stores it."""
    refusal = MetricRefusal("port-metrics", 400, "port_id is required")  # WHY: One refusal record.
    with pytest.raises(dataclasses.FrozenInstanceError):  # WHY: The record is frozen.
        refusal.reason = "changed"  # WHY: Try to change a frozen field.

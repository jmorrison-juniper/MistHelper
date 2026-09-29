"""Tests for the on-demand synthetic test trigger."""

from __future__ import annotations  # WHY: keep annotations lazy for pytest collection.

import logging  # WHY: caplog validates that secrets do not reach log text.
from dataclasses import dataclass, field  # WHY: fakes need small state containers.
from typing import Any  # WHY: fake responses carry heterogeneous JSON values.

from src.troubleshooting.synthetic_test_trigger.models import (
    EXPORT_ENDPOINT_NAME,
    EXPORT_FILENAME,
    ExportRowBuilder,
    RequestBodyBuilder,
    SyntheticTestRequest,
    SyntheticTestResult,
)
from src.troubleshooting.synthetic_test_trigger.operation import SyntheticTestRuntime, SyntheticTestTriggerRunner


@dataclass
class FakeResponse:
    """Small response double with the same data attribute that mistapi returns."""

    data: dict[str, Any]  # WHY: production code reads the SDK response data attribute.


@dataclass
class FakeClient:
    """Capture trigger and poll calls from the runner."""

    poll_response: object  # WHY: each test controls what one poll returns.
    triggers: list[SyntheticTestRequest] = field(default_factory=list)  # WHY: assertions inspect trigger calls.
    polls: list[SyntheticTestRequest] = field(default_factory=list)  # WHY: assertions inspect poll calls.

    def trigger(self, request: SyntheticTestRequest) -> object:
        """Capture one trigger call."""
        self.triggers.append(request)  # WHY: tests must prove confirmation controls API calls.
        return FakeResponse({"status": "success"})  # WHY: runner ignores trigger response in this feature.

    def poll_once(self, request: SyntheticTestRequest) -> object:
        """Capture one poll call."""
        self.polls.append(request)  # WHY: tests must prove polling happened.
        return self.poll_response  # WHY: caller normalizes the injected response.


@dataclass
class ExportCapture:
    """Capture export calls without writing files."""

    calls: list[tuple[list[dict[str, object]], str, str, list[str]]] = field(default_factory=list)

    def write(self, rows: list[dict[str, object]], filename: str, api_name: str, fieldnames: list[str]) -> bool:
        """Capture one export request."""
        self.calls.append((rows, filename, api_name, fieldnames))  # WHY: tests inspect file name and row safety.
        return True  # WHY: runner should see a successful export.


class PromptAnswers:
    """Return a deterministic answer for each prompt."""

    def __init__(self, answers: list[str]) -> None:
        """Store prompted answers in order."""
        self._answers = answers  # WHY: tests model an operator dialogue.

    def read(self, prompt: str, context: str) -> str:
        """Return the next answer."""
        assert prompt  # WHY: every runtime prompt must show text to the operator.
        assert context  # WHY: every runtime prompt must name an EOF-safe context.
        return self._answers.pop(0)  # WHY: ordered answers prove the prompt flow.


def build_runtime(
    client: Any,
    prompts: PromptAnswers,
    capture: ExportCapture,
    device_id: str = "device-1",
) -> SyntheticTestRuntime:
    """Build a runner runtime with all side effects captured."""
    return SyntheticTestRuntime(  # WHY: tests inject all side effects through the runtime seam.
        client=client,
        site_selector=lambda: "site-1",
        device_selector=lambda site_id, device_type: device_id,
        input_reader=prompts.read,
        exporter=capture.write,
        sleep_fn=lambda seconds: None,
        monotonic_fn=_monotonic_counter(),
    )


def _monotonic_counter() -> Any:
    """Return a clock function that advances by one second per call."""
    ticks = {"value": -1.0}  # WHY: first call returns zero for a fresh deadline.

    def read_time() -> float:
        """Return the next monotonic value."""
        ticks["value"] += 1.0  # WHY: each call advances time without real waiting.
        return ticks["value"]  # WHY: runner timeout logic reads this value.

    return read_time  # WHY: runtime expects a zero-argument clock callable.


def test_site_request_body_shape() -> None:
    """Site requests include only the optional OpenAPI email field."""
    body = RequestBodyBuilder.site("noc@example.com")  # WHY: site schema accepts optional email.
    assert body == {"email": "noc@example.com"}  # WHY: no other field belongs in the site body.


def test_device_request_body_shape() -> None:
    """Device requests keep schema fields and coerce numeric values."""
    body = RequestBodyBuilder.device("lan_connectivity", {"host": "8.8.8.8", "ping_count": "10"})
    assert body == {"type": "lan_connectivity", "host": "8.8.8.8", "ping_count": 10}


def test_radius_body_shape_and_secret_summary() -> None:
    """RADIUS requests include the password only in the API body."""
    body = RequestBodyBuilder.radius("user1", "secret-value", "dot1x")  # WHY: RADIUS schema requires these fields.
    request = SyntheticTestRequest("radius", "site-1", body, {"scope": "radius"}, device_id="switch-1")
    row = ExportRowBuilder.build(request, request_result("success"))  # WHY: export must not contain the password.
    assert body == {"user": "user1", "password": "secret-value", "profile": "dot1x"}
    assert "secret-value" not in str(row)  # WHY: acceptance criteria forbid secret export.
    assert request.public_body()["password"] == "********"  # WHY: logs use masked bodies.


def test_confirmation_cancel_prevents_trigger() -> None:
    """Any confirmation other than lowercase y cancels the API trigger."""
    client = FakeClient(FakeResponse({"status": "success"}))  # WHY: poll should never be reached.
    capture = ExportCapture()  # WHY: export should never be reached.
    prompts = PromptAnswers(["1", "", "N"])  # WHY: site scope, blank email, then cancel.
    runner = SyntheticTestTriggerRunner(build_runtime(client, prompts, capture), timeout_seconds=1)
    result = runner.run()  # WHY: execute the full prompt flow.
    assert result is None  # WHY: cancellation returns no result.
    assert client.triggers == []  # WHY: no API trigger is sent after cancel.
    assert capture.calls == []  # WHY: no file is written after cancel.


def test_timeout_writes_clear_export_row() -> None:
    """A missing poll result writes a timeout row."""
    client = FakeClient(FakeResponse({"results": []}))  # WHY: empty search response forces timeout.
    capture = ExportCapture()  # WHY: capture CSV rows.
    prompts = PromptAnswers(["1", "", "y"])  # WHY: site scope, blank email, send trigger.
    runner = SyntheticTestTriggerRunner(build_runtime(client, prompts, capture), timeout_seconds=0)
    result = runner.run()  # WHY: execute trigger and bounded polling.
    assert result is not None and result.timed_out  # WHY: timeout is the expected final state.
    assert capture.calls[0][1] == EXPORT_FILENAME  # WHY: acceptance criteria name this file.
    assert capture.calls[0][2] == EXPORT_ENDPOINT_NAME  # WHY: exporter uses the registered API key.
    assert "within 0 seconds" in str(capture.calls[0][0][0]["reason"])  # WHY: timeout message is clear.


def test_completed_site_result_exports_row() -> None:
    """A completed site result writes one safe CSV row."""
    response = FakeResponse({"results": [{"status": "success", "type": "dhcp", "failed": False}]})
    client = FakeClient(response)  # WHY: one poll returns a completed result.
    capture = ExportCapture()  # WHY: capture CSV rows.
    prompts = PromptAnswers(["1", "", "y"])  # WHY: site scope, blank email, send trigger.
    runner = SyntheticTestTriggerRunner(build_runtime(client, prompts, capture), timeout_seconds=5)
    result = runner.run()  # WHY: execute the full site happy path.
    assert result is not None and result.status == "success"  # WHY: the site result completed.
    assert capture.calls[0][0][0]["test_type"] == "dhcp"  # WHY: result values are included in the row.
    assert capture.calls[0][3] == ExportRowBuilder.FIELDNAMES  # WHY: export columns are stable.


def test_radius_secret_never_reaches_logs_or_export(caplog: Any) -> None:
    """The RADIUS password stays out of logs and export rows."""
    caplog.set_level(logging.DEBUG)  # WHY: capture all feature logs for the secret scan.
    client = FakeClient(FakeResponse({"status": "success", "type": "radius"}))  # WHY: completed poll result.
    capture = ExportCapture()  # WHY: capture CSV rows.
    prompts = PromptAnswers(["3", "user1", "shared-secret", "", "y"])  # WHY: RADIUS prompts and confirm.
    runner = SyntheticTestTriggerRunner(build_runtime(client, prompts, capture, "switch-1"), timeout_seconds=5)
    result = runner.run()  # WHY: execute the RADIUS workflow.
    assert result is not None and result.status == "success"  # WHY: workflow completed.
    assert "shared-secret" not in caplog.text  # WHY: logs must not reveal the password.
    assert "shared-secret" not in str(capture.calls)  # WHY: export rows must not reveal the password.


def request_result(status: str) -> SyntheticTestResult:
    """Return a result object for export row tests."""
    return SyntheticTestResult(status=status, raw={"status": status})  # WHY: tests need a minimal result.

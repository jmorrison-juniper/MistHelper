"""Tests for the on-demand synthetic test trigger."""

from __future__ import annotations  # WHY: keep annotations lazy for pytest collection.

import csv  # WHY: one operation test proves the exported CSV content on disk.
import logging  # WHY: caplog validates that secrets do not reach log text.
from dataclasses import dataclass, field  # WHY: fakes need small state containers.
from pathlib import Path  # WHY: tmp_path uses Path objects for isolated export files.
from typing import Any  # WHY: fake responses carry heterogeneous JSON values.

import pytest  # WHY: monkeypatch and tmp_path typing keep operation seams isolated.

from src.troubleshooting.synthetic_test_trigger import client as synthetic_client_module
from src.troubleshooting.synthetic_test_trigger.client import SyntheticTestClient
from src.troubleshooting.synthetic_test_trigger.models import (
    EXPORT_ENDPOINT_NAME,
    EXPORT_FILENAME,
    ExportRowBuilder,
    RequestBodyBuilder,
    SyntheticTestRequest,
    SyntheticTestResult,
)
from src.troubleshooting.synthetic_test_trigger.operation import (
    RuntimePromptReader,
    SyntheticTestRuntime,
    SyntheticTestTrigger,
    SyntheticTestTriggerRunner,
)


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


def test_device_result_writes_csv_into_tmp_path(tmp_path: Path) -> None:
    """The device workflow can write the export row to an isolated CSV file."""
    response = FakeResponse({"status": "success", "type": "ping", "latency": 12})  # WHY: device poll result.
    client = FakeClient(response)  # WHY: fake client avoids all network calls.
    prompts = PromptAnswers(["2", "ping", "host=8.8.8.8,ping_count=3", "y"])  # WHY: drive the device prompts.
    csv_calls: list[Path] = []  # WHY: assertions need the exact file path that was written.

    def write_csv(
        rows: list[dict[str, object]],
        filename: str,
        api_name: str,
        fieldnames: list[str],
    ) -> bool:
        """Write rows to tmp_path through the exporter seam."""
        assert filename == EXPORT_FILENAME  # WHY: the operation must request the required CSV name.
        assert api_name == EXPORT_ENDPOINT_NAME  # WHY: the operation must use the registered export key.
        output_file = tmp_path / filename  # WHY: tmp_path keeps the test out of repository data folders.
        with output_file.open("w", newline="", encoding="utf-8") as handle:  # WHY: CSV needs newline control.
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")  # WHY: exporter filters.
            writer.writeheader()  # WHY: operators need column names in the CSV file.
            writer.writerows(rows)  # WHY: write the operation export row for verification.
        csv_calls.append(output_file)  # WHY: test proves that exactly one CSV file was written.
        return True  # WHY: the operation treats the export as successful.

    runtime = SyntheticTestRuntime(  # WHY: tests inject each side effect through the runtime seam.
        client=client,
        site_selector=lambda: "site-1",
        device_selector=lambda site_id, device_type: "device-1",
        input_reader=prompts.read,
        exporter=write_csv,
        sleep_fn=lambda seconds: None,
        monotonic_fn=_monotonic_counter(),
    )
    runner = SyntheticTestTriggerRunner(runtime, timeout_seconds=5)  # WHY: execute the operation workflow.
    result = runner.run()  # WHY: drive trigger, poll, report, and export.
    with csv_calls[0].open(newline="", encoding="utf-8") as handle:  # WHY: read back the created CSV.
        row = next(csv.DictReader(handle))  # WHY: one completed result writes one row.
    assert result is not None and result.status == "success"  # WHY: the device result completed.
    assert row["device_id"] == "device-1"  # WHY: device scope must include the selected device.
    assert row["latency"] == "12"  # WHY: result values must reach the CSV export.


def test_invalid_scope_and_missing_device_stop_before_trigger(caplog: Any) -> None:
    """Invalid selections stop before the client receives a trigger request."""
    caplog.set_level(logging.ERROR)  # WHY: the operation logs clear stop reasons.
    client = FakeClient(FakeResponse({"status": "success"}))  # WHY: fake client captures any mistaken trigger.
    capture = ExportCapture()  # WHY: export should not run for invalid prompt paths.
    invalid_prompts = PromptAnswers(["9"])  # WHY: unknown scope must stop the workflow.
    invalid_runner = SyntheticTestTriggerRunner(build_runtime(client, invalid_prompts, capture), timeout_seconds=1)
    missing_device_prompts = PromptAnswers(["2"])  # WHY: device scope with no selected device must stop.
    missing_runtime = build_runtime(client, missing_device_prompts, capture, device_id="")  # WHY: no device.
    missing_runner = SyntheticTestTriggerRunner(missing_runtime, timeout_seconds=1)  # WHY: run the second path.
    assert invalid_runner.run() is None  # WHY: unknown scope cannot send a trigger.
    assert missing_runner.run() is None  # WHY: missing device cannot send a trigger.
    assert client.triggers == []  # WHY: neither invalid path may call the Mist API.
    assert "Unknown synthetic test scope answer" in caplog.text  # WHY: log explains the invalid scope.
    assert "No device selected" in caplog.text  # WHY: log explains the missing device.


def test_no_site_and_failed_export_paths(caplog: Any) -> None:
    """Missing site and failed export paths produce operator-visible logs."""
    caplog.set_level(logging.DEBUG)  # WHY: capture error logs and export result details.
    client = FakeClient(FakeResponse({"results": [{"status": "success"}]}))  # WHY: successful poll reaches export.
    no_site_runtime = build_runtime(client, PromptAnswers([]), ExportCapture())  # WHY: reuse standard fakes.
    no_site_runtime = SyntheticTestRuntime(  # WHY: replace only the site selector with a missing selection.
        client=no_site_runtime.client,
        site_selector=lambda: None,
        device_selector=no_site_runtime.device_selector,
        input_reader=no_site_runtime.input_reader,
        exporter=no_site_runtime.exporter,
        sleep_fn=no_site_runtime.sleep_fn,
        monotonic_fn=no_site_runtime.monotonic_fn,
    )
    failed_runtime = SyntheticTestRuntime(  # WHY: replace exporter to cover the failed write branch.
        client=client,
        site_selector=lambda: "site-1",
        device_selector=lambda site_id, device_type: "device-1",
        input_reader=PromptAnswers(["1", "", "y"]).read,
        exporter=lambda rows, filename, api_name, fieldnames: False,
        sleep_fn=lambda seconds: None,
        monotonic_fn=_monotonic_counter(),
    )
    no_site_result = SyntheticTestTriggerRunner(no_site_runtime).run()  # WHY: no site stops before prompts.
    failed_result = SyntheticTestTriggerRunner(failed_runtime, timeout_seconds=5).run()  # WHY: export is last.
    assert no_site_result is None  # WHY: no site must stop without a result.
    assert failed_result and failed_result.status == "success"  # WHY: failed export does not change result status.
    assert "No site selected" in caplog.text  # WHY: missing site has a clear log message.
    assert "could not write" in caplog.text  # WHY: failed export has a clear log message.


def test_runtime_prompt_reader_and_menu_handler_are_bound(monkeypatch: pytest.MonkeyPatch) -> None:
    """The public menu handler builds a runtime and delegates to the runner."""
    prompts: list[tuple[str, str]] = []  # WHY: capture PromptReader calls without real console input.
    runs: list[bool] = []  # WHY: prove the public handler invokes the runner once.

    def fake_input(prompt: str, context: str) -> str:
        """Return one sanitized input value."""
        prompts.append((prompt, context))  # WHY: the reader must pass through both prompt and context.
        return "  y  "  # WHY: RuntimePromptReader strips surrounding spaces.

    class FakeRunner:
        """Small runner double for the public menu handler."""

        def __init__(self, runtime: SyntheticTestRuntime) -> None:
            """Accept the runtime built by the menu handler."""
            assert isinstance(runtime, SyntheticTestRuntime)  # WHY: handler must bind runtime dependencies first.

        def run(self) -> None:
            """Capture the menu delegation."""
            runs.append(True)  # WHY: the public handler should delegate exactly once.

    runtime = build_runtime(FakeClient(FakeResponse({"status": "success"})), PromptAnswers([]), ExportCapture())
    monkeypatch.setattr("src.troubleshooting.synthetic_test_trigger.operation.InputUtils.safe_input", fake_input)
    monkeypatch.setattr(SyntheticTestRuntime, "from_runtime", classmethod(lambda cls: runtime))
    monkeypatch.setattr("src.troubleshooting.synthetic_test_trigger.operation.SyntheticTestTriggerRunner", FakeRunner)
    assert RuntimePromptReader.read("Continue? ", "context_name") == "y"  # WHY: input reader strips whitespace.
    SyntheticTestTrigger.run()  # WHY: public menu handler must remain callable.
    assert prompts == [("Continue? ", "context_name")]  # WHY: reader passed prompt context to InputUtils.
    assert runs == [True]  # WHY: handler delegated to the runner once.


def test_client_dispatches_each_sdk_function_with_explicit_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    """The client sends each scope through its SDK function without generic forwarding."""
    calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []  # WHY: inspect SDK call shapes.

    def capture_site_trigger(*args: object, **kwargs: object) -> FakeResponse:
        """Capture a site trigger SDK call."""
        calls.append(("site_trigger", args, kwargs))  # WHY: prove the client passed explicit positional args.
        return FakeResponse({"status": "started"})  # WHY: client returns the SDK response.

    def capture_device_trigger(*args: object, **kwargs: object) -> FakeResponse:
        """Capture a device trigger SDK call."""
        calls.append(("device_trigger", args, kwargs))  # WHY: prove the device endpoint was selected.
        return FakeResponse({"status": "started"})  # WHY: client returns the SDK response.

    def capture_radius_trigger(*args: object, **kwargs: object) -> FakeResponse:
        """Capture a RADIUS trigger SDK call."""
        calls.append(("radius_trigger", args, kwargs))  # WHY: prove the RADIUS endpoint was selected.
        return FakeResponse({"status": "started"})  # WHY: client returns the SDK response.

    def capture_site_poll(*args: object, **kwargs: object) -> FakeResponse:
        """Capture a site poll SDK call."""
        calls.append(("site_poll", args, kwargs))  # WHY: prove query fields are named kwargs.
        return FakeResponse({"results": []})  # WHY: client returns the SDK response.

    def capture_device_poll(*args: object, **kwargs: object) -> FakeResponse:
        """Capture a device poll SDK call."""
        calls.append(("device_poll", args, kwargs))  # WHY: prove non-site poll endpoint was selected.
        return FakeResponse({"status": "success"})  # WHY: client returns the SDK response.

    monkeypatch.setattr(synthetic_client_module.site_synthetic_test, "triggerSiteSyntheticTest", capture_site_trigger)
    monkeypatch.setattr(synthetic_client_module.site_devices, "triggerSiteDeviceSyntheticTest", capture_device_trigger)
    monkeypatch.setattr(
        synthetic_client_module.site_devices,
        "startSiteSwitchRadiusSyntheticTest",
        capture_radius_trigger,
    )
    monkeypatch.setattr(synthetic_client_module.site_synthetic_test, "searchSiteSyntheticTest", capture_site_poll)
    monkeypatch.setattr(synthetic_client_module.site_devices, "getSiteDeviceSyntheticTest", capture_device_poll)
    api_client = SyntheticTestClient("session")  # WHY: SDK functions receive the shared session object.
    site_request = SyntheticTestRequest("site", "site-1", {}, {"scope": "site"}, poll_query={"by": "user"})
    device_request = SyntheticTestRequest("device", "site-1", {"type": "ping"}, {}, device_id="device-1")
    radius_request = SyntheticTestRequest("radius", "site-1", {"user": "u"}, {}, device_id="switch-1")
    assert api_client.trigger(site_request).data["status"] == "started"  # WHY: site trigger returns SDK data.
    assert api_client.trigger(device_request).data["status"] == "started"  # WHY: device trigger returns SDK data.
    assert api_client.trigger(radius_request).data["status"] == "started"  # WHY: RADIUS trigger returns SDK data.
    assert api_client.poll_once(site_request).data == {"results": []}  # WHY: site poll returns search data.
    assert api_client.poll_once(device_request).data["status"] == "success"  # WHY: device poll returns result data.
    assert calls[3][2]["by"] == "user" and calls[3][2]["limit"] == 1  # WHY: poll query used named kwargs.
    assert [call[0] for call in calls] == [  # WHY: all five operation IDs are routed.
        "site_trigger",
        "device_trigger",
        "radius_trigger",
        "site_poll",
        "device_poll",
    ]


def request_result(status: str) -> SyntheticTestResult:
    """Return a result object for export row tests."""
    return SyntheticTestResult(status=status, raw={"status": status})  # WHY: tests need a minimal result.

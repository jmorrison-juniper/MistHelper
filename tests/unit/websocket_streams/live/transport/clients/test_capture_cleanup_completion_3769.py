"""Prove cleanup resolves before the utility reports one terminal result."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import replace
from types import SimpleNamespace

import pytest

from src.websocket_streams.live.runners.utility.runner.capture import CaptureStopper
from src.websocket_streams.live.runners.utility.runner.execution import UtilityExecution
from src.websocket_streams.live.runners.utility.runner.utility_runner import RunContext, RunnerState
from src.websocket_streams.live.runners.utility.triggers.models import UtilityTiming
from src.websocket_streams.live.sessions.record.state import SessionState
from src.websocket_streams.live.transport.endpoint import MistStreamEndpoint, TransportProfile
from src.websocket_streams.live.transport.stream_client import StreamClient
from tests.unit.websocket_streams.live.runners.utility.test_ws_utility_runner import (
    ORG_ID,
    SITE_ID,
    FakeSink,
    ShortTriggerTable,
    _fast_table,
    _packet_record,
    _request,
    _slow_table,
)
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.api import FakeApiResponse, FakeApiSession
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.devices import StreamDevice
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.server import FakeMistCloud


class ControlledApi(FakeApiSession):
    """Hold trigger and DELETE responses at observable boundaries."""

    class CloseControl:
        """Close the real transport before a controlled delay or failure."""

        def __init__(self, *, fail: bool = False) -> None:
            self.original = StreamClient.close
            self.fail = fail
            self.entered, self.release = threading.Event(), threading.Event()

        def callback(self) -> Callable[[StreamClient], None]:
            def controlled_close(client: StreamClient) -> None:
                self.original(client)
                self.entered.set()
                if self.fail:
                    raise RuntimeError("The controlled client close failed.")
                if not self.release.wait(3.0):
                    raise TimeoutError("The test did not release stream close.")

            return controlled_close

    def __init__(self, cloud: FakeMistCloud) -> None:
        super().__init__(cloud)
        self.trigger_entered = threading.Event()
        self.trigger_release = threading.Event()
        self.delete_entered = threading.Event()
        self.delete_release = threading.Event()
        self.before_post_return = self.hold_trigger
        self.add_override("/pcaps/capture", data={"id": "cap-owned"})
        self.add_override("/pcaps?limit=1", data=[{"id": "cap-owned"}])
        self.lookup_status = self.delete_status = 200
        self.lookup_error: Exception | None = None
        self.delete_error: Exception | None = None
        self.output_device: StreamDevice | None = None

    def hold_trigger(self, uri: str, body: object | None) -> None:
        self.trigger_entered.set()
        if not self.trigger_release.wait(3.0):
            raise TimeoutError("The test did not release the trigger.")
        if self.output_device is not None:
            self.output_device.publish_capture(f"/sites/{SITE_ID}/pcaps", "cap-owned", _packet_record())

    def mist_get(self, uri: str) -> FakeApiResponse:
        response = super().mist_get(uri)
        if self.lookup_error is not None:
            raise self.lookup_error
        response.status_code = self.lookup_status
        return response

    def mist_delete(self, uri: str) -> FakeApiResponse:
        self.delete_entered.set()
        if not self.delete_release.wait(3.0):
            raise TimeoutError("The test did not release capture cleanup.")
        response = super().mist_delete(uri)
        if self.delete_error is not None:
            raise self.delete_error
        response.status_code = self.delete_status
        return response


class CaptureScenario:
    """Run the real utility lifecycle against a controlled loopback cloud."""

    def __init__(self, key: str = "ex.remotePcap") -> None:
        self.cloud = FakeMistCloud()
        self.key = key
        self.sink = FakeSink()
        self.state = RunnerState()
        self.thread: threading.Thread | None = None

    def __enter__(self) -> CaptureScenario:
        self.cloud.__enter__()
        self.device = StreamDevice()
        self.cloud.register("/api-ws/v1/stream", self.device)
        self.api = ControlledApi(self.cloud)
        profile = TransportProfile(
            stream_url=f"{self.cloud.base_ws_url}/api-ws/v1/stream",
            allow_loopback=True,
            read_timeout_seconds=0.2,
            subscribe_timeout_seconds=1.0,
        )
        self.context = RunContext(
            self.api,
            MistStreamEndpoint(self.api, profile),
            _request(self.key, "packets"),
            self.sink,
            _slow_table(),
            self.state,
        )
        self.path = (
            f"/api/v1/orgs/{ORG_ID}/pcaps" if self.key.startswith("mxedge.org") else f"/api/v1/sites/{SITE_ID}/pcaps"
        )
        return self

    def __exit__(self, kind: object, error: object, trace: object) -> None:
        self.state.stopping.set()
        self.api.trigger_release.set()
        self.api.delete_release.set()
        if self.thread is not None:
            self.thread.join(3.0)
            assert self.thread.is_alive() is False
        self.cloud.__exit__(kind, error, trace)

    def start(self, execution: UtilityExecution, *, stop_during_trigger: bool = True) -> None:
        self.thread = threading.Thread(target=execution.run)
        self.thread.start()
        assert self.api.trigger_entered.wait(3.0) is True
        if stop_during_trigger:
            self.state.stopping.set()
        self.api.trigger_release.set()

    def finish(self) -> tuple[SessionState, str]:
        self.api.delete_release.set()
        result = self.sink.wait_finished()
        if self.thread is not None:
            self.thread.join(3.0)
            assert self.thread.is_alive() is False
        assert self.sink.finished == [result]
        return result


class TestCompletionOrdering:
    """Use event barriers rather than elapsed time to prove ordering."""

    @pytest.mark.parametrize("key", ["ex.remotePcap", "mxedge.orgRemotePcap"])
    def test_run_waits_for_capture_cleanup_before_final_result(self, key: str) -> None:
        with CaptureScenario(key) as scenario:
            scenario.start(UtilityExecution(scenario.context))
            assert scenario.api.delete_entered.wait(3.0) is True
            assert scenario.sink.finished == []
            assert [(call.method, call.uri) for call in scenario.api.calls] == [
                ("POST", f"{scenario.path}/capture"),
                ("GET", f"{scenario.path}?limit=1"),
            ]
            assert scenario.finish() == (SessionState.STOPPED, "The operator stopped the session.")
            assert [(call.method, call.uri) for call in scenario.api.calls][-1] == ("DELETE", scenario.path)

    @pytest.mark.parametrize(
        ("stop", "expected"),
        [
            (False, (SessionState.FINISHED, "The utility finished.")),
            (True, (SessionState.STOPPED, "The operator stopped the session.")),
        ],
    )
    def test_close_barrier_delays_terminal_and_preserves_normal_reason(
        self,
        monkeypatch: pytest.MonkeyPatch,
        stop: bool,
        expected: tuple[SessionState, str],
    ) -> None:
        control = ControlledApi.CloseControl()
        monkeypatch.setattr(StreamClient, "close", control.callback())
        with CaptureScenario() as scenario:
            scenario.context = replace(scenario.context, triggers=_fast_table())
            scenario.api.output_device = scenario.device
            try:
                scenario.start(UtilityExecution(scenario.context), stop_during_trigger=False)
                assert control.entered.wait(3.0) is True
                assert scenario.sink.finished == []
                if stop:
                    scenario.state.stopping.set()
                control.release.set()
                assert scenario.finish() == expected
                assert scenario.api.delete_entered.is_set() is stop
            finally:
                control.release.set()

    @pytest.mark.parametrize("stop", [False, True])
    def test_runtime_failure_retains_existing_stop_mapping(self, stop: bool) -> None:
        with CaptureScenario() as scenario:
            scenario.api.overrides.clear()
            scenario.api.add_override("/pcaps/capture", status_code=503, data={})
            scenario.start(UtilityExecution(scenario.context), stop_during_trigger=stop)
            expected = (
                (SessionState.STOPPED, "The operator stopped the session.")
                if stop
                else (
                    SessionState.FAILED,
                    "The utility failed with status 503.",
                )
            )
            assert scenario.finish() == expected
            assert [call.method for call in scenario.api.calls] == ["POST"]

    def test_cooperative_cancellation_during_delete_waits_for_cleanup(self) -> None:
        with CaptureScenario() as scenario:
            scenario.start(UtilityExecution(scenario.context))
            assert scenario.api.delete_entered.wait(3.0) is True
            scenario.state.stopping.set()
            assert scenario.sink.finished == []
            assert scenario.finish() == (SessionState.STOPPED, "The operator stopped the session.")
            assert [(call.method, call.uri) for call in scenario.api.calls][-1] == ("DELETE", scenario.path)

    @pytest.mark.parametrize(
        ("output", "timing", "expected"),
        [
            (
                False,
                UtilityTiming(0.5, 0.05, 1.0),
                (
                    SessionState.TIMED_OUT,
                    "The device sent no output before the time limit. "
                    "Check that the device is connected, then try again.",
                ),
            ),
            (
                True,
                UtilityTiming(0.5, 5.0, 0.1),
                (
                    SessionState.FINISHED,
                    "The utility reached its time limit of 0.1 seconds.",
                ),
            ),
        ],
    )
    def test_normal_completion_preserves_limits_without_cloud_stop(
        self,
        output: bool,
        timing: UtilityTiming,
        expected: tuple[SessionState, str],
    ) -> None:
        with CaptureScenario() as scenario:
            scenario.context = RunContext(
                scenario.api,
                scenario.context.endpoint,
                scenario.context.request,
                scenario.sink,
                ShortTriggerTable(timing),
                scenario.state,
            )
            if output:
                scenario.api.output_device = scenario.device
            scenario.start(UtilityExecution(scenario.context), stop_during_trigger=False)
            assert scenario.finish() == expected
            assert [call.method for call in scenario.api.calls] == ["POST"]


class TestCleanupFailures:
    """Require explicit failure for each independent cleanup operation."""

    @pytest.mark.parametrize("operation", ["GET", "DELETE"])
    @pytest.mark.parametrize("status", [400, 403, 500, 503])
    def test_http_4xx_5xx_cleanup_failure_is_not_stopped(self, operation: str, status: int) -> None:
        with CaptureScenario() as scenario:
            if operation == "GET":
                scenario.api.lookup_status = status
            else:
                scenario.api.delete_status = status
            scenario.start(UtilityExecution(scenario.context))
            assert scenario.finish() == (
                SessionState.FAILED,
                "The utility cleanup failed. Read the portal log for the cause.",
            )
            assert [call.method for call in scenario.api.calls] == (
                ["POST", "GET"] if operation == "GET" else ["POST", "GET", "DELETE"]
            )

    @pytest.mark.parametrize("operation", ["GET", "DELETE"])
    @pytest.mark.parametrize("error", [TimeoutError("private token"), ConnectionError("private token")])
    def test_timeout_connection_error_is_visible_and_redacted(
        self,
        operation: str,
        error: Exception,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        with CaptureScenario() as scenario:
            if operation == "GET":
                scenario.api.lookup_error = error
            else:
                scenario.api.delete_error = error
            scenario.start(UtilityExecution(scenario.context))
            assert scenario.finish() == (
                SessionState.FAILED,
                "The utility cleanup failed. Read the portal log for the cause.",
            )
            assert "utility_cleanup_failed" in caplog.text
            assert "utility_cleanup_trace" in caplog.text
            assert "private token" not in caplog.text

    @pytest.mark.parametrize("stop", [False, True])
    def test_client_close_failure_does_not_prevent_matching_cloud_stop(
        self,
        monkeypatch: pytest.MonkeyPatch,
        stop: bool,
    ) -> None:
        control = ControlledApi.CloseControl(fail=True)
        monkeypatch.setattr(StreamClient, "close", control.callback())
        with CaptureScenario() as scenario:
            scenario.context = replace(scenario.context, triggers=_fast_table())
            scenario.start(UtilityExecution(scenario.context), stop_during_trigger=stop)
            assert scenario.finish() == (
                SessionState.FAILED,
                "The utility cleanup failed. Read the portal log for the cause.",
            )
            assert scenario.api.delete_entered.is_set() is stop
            assert [call.method for call in scenario.api.calls] == (["POST", "GET", "DELETE"] if stop else ["POST"])

    def test_two_cleanup_failures_are_both_logged_and_finish_once(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        control = ControlledApi.CloseControl(fail=True)
        monkeypatch.setattr(StreamClient, "close", control.callback())
        with CaptureScenario() as scenario:
            scenario.api.delete_status = 503
            scenario.start(UtilityExecution(scenario.context))
            assert scenario.finish()[0] == SessionState.FAILED
            assert [call.method for call in scenario.api.calls] == ["POST", "GET", "DELETE"]
            assert caplog.text.count('"event":"utility_cleanup_failed"') == 2

    @pytest.mark.parametrize("status", [None, "200", True])
    @pytest.mark.parametrize("operation", ["GET", "DELETE"])
    def test_unavailable_or_malformed_status_reports_failed_terminal(
        self,
        monkeypatch: pytest.MonkeyPatch,
        status: object,
        operation: str,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        with CaptureScenario() as scenario:
            method = "mist_get" if operation == "GET" else "mist_delete"
            original = getattr(scenario.api, method)

            def malformed_response(uri: str) -> object:
                answer = original(uri)
                return SimpleNamespace(data=answer.data, **({"status_code": status} if status is not None else {}))

            monkeypatch.setattr(scenario.api, method, malformed_response)
            scenario.start(UtilityExecution(scenario.context))
            assert scenario.finish() == (
                SessionState.FAILED,
                "The utility cleanup failed. Read the portal log for the cause.",
            )
            assert [call.method for call in scenario.api.calls] == (
                ["POST", "GET"] if operation == "GET" else ["POST", "GET", "DELETE"]
            )
            assert '"count":1,"event":"capture_response_failed"' in caplog.text


class TestCaptureIdentityAndStatus:
    """Keep lookup selection and original site or organization scope."""

    @pytest.mark.parametrize("key", ["ex.remotePcap", "mxedge.orgRemotePcap"])
    @pytest.mark.parametrize("data", [[], [{"id": "different"}], {"results": []}, {"results": [{"id": "different"}]}])
    def test_empty_or_different_capture_does_not_delete(self, key: str, data: object) -> None:
        with CaptureScenario(key) as scenario:
            scenario.api.overrides.clear()
            scenario.api.add_override("/pcaps/capture", data={"id": "cap-owned"})
            scenario.api.add_override("/pcaps?limit=1", data=data)
            scenario.start(UtilityExecution(scenario.context))
            assert scenario.finish() == (SessionState.STOPPED, "The operator stopped the session.")
            assert [(call.method, call.uri) for call in scenario.api.calls] == [
                ("POST", f"{scenario.path}/capture"),
                ("GET", f"{scenario.path}?limit=1"),
            ]

    @pytest.mark.parametrize("answer", [{}, {"id": None}, {"id": 1}])
    def test_missing_trigger_identity_does_not_guess_capture(self, answer: dict[str, object]) -> None:
        with CaptureScenario() as scenario:
            scenario.api.overrides.clear()
            scenario.api.add_override("/pcaps/capture", data=answer)
            scenario.start(UtilityExecution(scenario.context))
            assert scenario.finish() == (SessionState.STOPPED, "The operator stopped the session.")
            assert [call.method for call in scenario.api.calls] == ["POST"]

    @pytest.mark.parametrize("status", [None, "", "200", True, {}, 200.0])
    @pytest.mark.parametrize("operation", ["GET", "DELETE"])
    def test_malformed_or_missing_status_never_reports_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
        status: object,
        operation: str,
    ) -> None:
        api = FakeApiSession()
        api.add_override("/pcaps?limit=1", data=[{"id": "cap-owned"}])
        response = SimpleNamespace(data=[{"id": "cap-owned"}])
        if status is not None:
            response.status_code = status
        method = "mist_get" if operation == "GET" else "mist_delete"
        monkeypatch.setattr(api, method, lambda uri: response)
        with pytest.raises(RuntimeError, match="API did not confirm status 200"):
            CaptureStopper(api).stop_site(SITE_ID, "cap-owned")
        assert [call.method for call in api.calls] == ([] if operation == "GET" else ["GET"])

    def test_mapping_match_and_existing_malformed_json_empty_body_behavior(self) -> None:
        api = FakeApiSession()
        api.add_override("?limit=1", data={"results": [{"id": "cap-owned"}]})
        assert CaptureStopper(api).stop_org(ORG_ID, "cap-owned") is True
        assert [(call.method, call.uri) for call in api.calls] == [
            ("GET", f"/api/v1/orgs/{ORG_ID}/pcaps?limit=1"),
            ("DELETE", f"/api/v1/orgs/{ORG_ID}/pcaps"),
        ]
        for data in ("bad json", None):
            api.calls.clear()
            api.overrides.clear()
            api.add_override("?limit=1", data=data)
            assert CaptureStopper(api).stop_site(SITE_ID, "cap-owned") is False
            assert [call.method for call in api.calls] == ["GET"]
        api.calls.clear()
        api.overrides.clear()
        api.add_override("?limit=1", data="")
        assert CaptureStopper(api).stop_site(SITE_ID, "cap-owned") is False
        assert [call.method for call in api.calls] == ["GET"]

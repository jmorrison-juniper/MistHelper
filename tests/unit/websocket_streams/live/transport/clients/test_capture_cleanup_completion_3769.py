"""Prove terminal notification follows capture cleanup without scheduling retries."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager

import pytest

from src.mist.realtime.websocket_streams.live.runners.utility.runner.monitoring import UtilityStreamMonitor
from src.mist.realtime.websocket_streams.live.runners.utility.runner.utility_runner import UtilityRunner
from src.mist.realtime.websocket_streams.live.sessions.record.state import SessionState
from tests.unit.websocket_streams.live.runners.utility import test_ws_utility_runner as utility_tests
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.api import FakeApiResponse, FakeApiSession
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.devices import StreamDevice
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.server import FakeMistCloud


class CleanupBarrierApi(FakeApiSession):
    """Hold the cleanup request before the controlled cloud records it."""

    def __init__(self, cloud: FakeMistCloud) -> None:
        """Create a bounded cleanup barrier."""
        super().__init__(cloud)
        self.entered = threading.Event()
        self.release = threading.Event()

    def prepare(self, matching: bool, failure: str | None) -> None:
        """Select the owned capture and optional cleanup exception."""
        self.add_override("/pcaps/capture", data={"id": "cap-owned"})
        self.add_override(
            "/pcaps?limit=1",
            data=[{"id": "cap-owned" if matching else "cap-foreign"}],
            exception=RuntimeError("private cleanup detail") if failure == "GET" else None,
        )
        if failure == "DELETE":
            self.add_override("/pcaps", exception=RuntimeError("private cleanup detail"))

    def mist_get(self, uri: str) -> FakeApiResponse:
        """Block the identity check until the test permits cleanup."""
        self.entered.set()
        if not self.release.wait(3.0):
            raise RuntimeError("The cleanup barrier did not release.")
        return super().mist_get(uri)


class CleanupSink(utility_tests.FakeSink):
    """Signal that the trigger answer is available before a stop request."""

    def __init__(self) -> None:
        """Create the trigger publication event."""
        super().__init__()
        self.live = threading.Event()

    def mark_live(self, note: str = "") -> None:
        """Publish readiness after the runner stores its trigger answer."""
        super().mark_live(note)
        self.live.set()


class TestCaptureCleanupCompletion:
    """Check cleanup ordering, identity safety, and explicit failures."""

    @staticmethod
    @contextmanager
    def running(
        key: str, matching: bool = True, failure: str | None = None
    ) -> Iterator[tuple[CleanupBarrierApi, CleanupSink, UtilityRunner]]:
        """Run the real stream and always release and join its worker."""
        with FakeMistCloud() as cloud:
            cloud.register("/api-ws/v1/stream", StreamDevice())
            api, sink = CleanupBarrierApi(cloud), CleanupSink()
            api.prepare(matching, failure)
            runner, _ = utility_tests._build_runner(
                cloud, api, utility_tests._request(key, "packets"), utility_tests._slow_table(), sink
            )
            worker = threading.Thread(target=runner._execution.run)
            worker.start()
            try:
                assert sink.live.wait(3.0), "The capture trigger did not complete."
                runner.stop()
                assert api.entered.wait(3.0), "The worker did not enter capture cleanup."
                yield api, sink, runner
            finally:
                api.release.set()
                worker.join(3.0)
                assert not worker.is_alive(), "The capture worker did not exit."

    @pytest.mark.parametrize(
        ("key", "scope", "target"),
        [
            ("ex.remotePcap", "sites", utility_tests.SITE_ID),
            ("mxedge.orgRemotePcap", "orgs", utility_tests.ORG_ID),
        ],
    )
    def test_terminal_waits_for_matching_cleanup(self, key: str, scope: str, target: str) -> None:
        """Fail deterministically if terminal state precedes matching DELETE."""
        with self.running(key) as (api, sink, _runner):
            assert sink.finished == [], "Terminal state was published while cleanup remained blocked."
            assert not any(call.method == "DELETE" for call in api.calls)
            api.release.set()
            assert sink.wait_finished() == (SessionState.STOPPED, "The operator stopped the session.")
            assert [(call.method, call.uri) for call in api.calls][-2:] == [
                ("GET", f"/api/v1/{scope}/{target}/pcaps?limit=1"),
                ("DELETE", f"/api/v1/{scope}/{target}/pcaps"),
            ]
        assert len(sink.finished) == 1

    @pytest.mark.parametrize("key", ["ex.remotePcap", "mxedge.orgRemotePcap"])
    def test_foreign_capture_is_not_deleted(self, key: str) -> None:
        """Complete the identity check without deleting a different capture."""
        with self.running(key, matching=False) as (api, sink, _runner):
            assert sink.finished == []
            api.release.set()
            assert sink.wait_finished()[0] == SessionState.STOPPED
        assert not any(call.method == "DELETE" for call in api.calls)
        assert len(sink.finished) == 1

    @pytest.mark.parametrize("key", ["ex.remotePcap", "mxedge.orgRemotePcap"])
    @pytest.mark.parametrize("failure", ["GET", "DELETE"])
    def test_cleanup_exception_reports_failure(self, key: str, failure: str, caplog: pytest.LogCaptureFixture) -> None:
        """Do not report stopped when capture identity checking or deletion raises."""
        with self.running(key, failure=failure) as (api, sink, _runner):
            assert sink.finished == []
            api.release.set()
            state, reason = sink.wait_finished()
        assert state == SessionState.FAILED
        assert reason == "The utility cleanup failed. Read the portal log for the cause."
        assert "private cleanup detail" not in reason
        assert "utility_cleanup_failed" in caplog.text
        assert "private cleanup detail" not in caplog.text
        assert len(sink.finished) == 1

    def test_execution_error_waits_for_cleanup(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Preserve stop precedence for an execution error after cleanup."""

        def interrupted(monitor: UtilityStreamMonitor, *_arguments: object) -> None:
            """Model a transport error after the operator requests stop."""
            assert monitor.context.state.stopping.wait(3.0)
            raise RuntimeError("The stream closed during stop.")

        monkeypatch.setattr(UtilityStreamMonitor, "read", interrupted)
        with self.running("ex.remotePcap") as (api, sink, _runner):
            assert sink.finished == []
            api.release.set()
            assert sink.wait_finished()[0] == SessionState.STOPPED
        assert len(sink.finished) == 1

"""Order and record correlation through the actual capture service."""

from __future__ import annotations

import json

import pytest
from mistapi.websockets.__ws_client import _MistWebsocket

from src.websocket_streams.live.captures.model import CaptureDependencies
from src.websocket_streams.live.captures.runner import PacketCaptureRunner
from src.websocket_streams.live.sessions.manager import RunnerFactory
from src.websocket_streams.live.sessions.record import SessionState
from tests.unit.websocket_streams.live.captures.support.local_stream import LocalPacketStream
from tests.unit.websocket_streams.live.captures.support.portal import CaptureHarness, PacketEvents
from tests.unit.websocket_streams.live.captures.support.sdk import Identities


class TestCaptureOrder:
    """Require the exact confirmation before the single SDK POST."""

    def test_subscription_confirmation_precedes_capture_post(self, capture_harness: CaptureHarness) -> None:
        """Keep the capture unstarted until its own confirmation arrives."""
        harness = capture_harness
        harness.api.script.stop.auto_ack = False
        session = harness.start()
        harness.wait(lambda: bool(harness.api.script.stop.sockets))
        client = harness.api.script.stop.sockets[0]
        assert [action[0] for action in harness.api.script.actions].count("POST") == 0
        client.emit({"event": "channel_subscribed", "channel": f"/sites/{Identities.OTHER}/pcaps"})
        assert [action[0] for action in harness.api.script.actions].count("POST") == 0
        client.emit({"event": "channel_subscribed", "channel": f"/sites/{Identities.SITE}/pcaps"})
        harness.wait(lambda: session.state is SessionState.LIVE)
        names = [action[0] for action in harness.api.script.actions]
        assert names.index("ack") < names.index("POST")
        assert names.count("POST") == 1

    def test_first_records_arrive_before_the_post_response(self, capture_harness: CaptureHarness) -> None:
        """Retain immediate JSON-string records after the response establishes identity."""
        harness = capture_harness

        def before_answer() -> None:
            """Deliver the first record while the SDK POST still runs."""
            event = PacketEvents.packet(0)
            event["data"] = json.dumps(event["data"])
            harness.api.script.stop.sockets[0].emit(event)

        harness.api.script.start.before_answer = before_answer
        session = harness.start()
        harness.wait(lambda: session.state is SessionState.LIVE)
        records = [json.loads(record.content_json) for record in session.snapshot_records() if record.kind == "packet"]
        assert [record["timestamp"] for record in records] == [0]
        assert "pcap_raw" not in records[0]
        assert [action[0] for action in harness.api.script.actions].count("POST") == 1

    def test_duplicate_confirmation_does_not_start_again(self, capture_harness: CaptureHarness) -> None:
        """Keep one start across repeated SDK confirmations."""
        harness = capture_harness
        session = harness.start()
        harness.wait(lambda: session.state is SessionState.LIVE)
        client = harness.api.script.stop.sockets[0]
        for _confirmation in range(3):
            client.emit({"event": "channel_subscribed", "channel": f"/sites/{Identities.SITE}/pcaps"})
        assert [action[0] for action in harness.api.script.actions].count("POST") == 1
        assert session.state is SessionState.LIVE

    def test_reconnect_keeps_identity_and_deadline(self, capture_harness: CaptureHarness) -> None:
        """Accept a fresh confirmation without restarting or extending the capture."""
        harness = capture_harness
        session = harness.start()
        harness.wait(lambda: session.state is SessionState.LIVE)
        runner = session.runner
        assert isinstance(runner, PacketCaptureRunner)
        deadline = runner.context.progress.deadline
        harness.clock.advance(61)
        client = harness.api.script.stop.sockets[0]
        client._on_error_cb(ConnectionError("untrusted remote error"))
        client.connect()
        client.emit(PacketEvents.packet(61))
        assert runner.context.progress.deadline == deadline == 120
        assert runner.context.progress.packets == 1
        assert [action[0] for action in harness.api.script.actions].count("POST") == 1

    def test_other_site_and_capture_records_never_reach_the_card(self, capture_harness: CaptureHarness) -> None:
        """Reject both correlation dimensions before session delivery."""
        harness = capture_harness
        session = harness.start()
        harness.wait(lambda: session.state is SessionState.LIVE)
        client = harness.api.script.stop.sockets[0]
        client.emit(PacketEvents.packet(1, capture_id=Identities.OTHER))
        client.emit(PacketEvents.packet(2, channel=f"/sites/{Identities.OTHER}/pcaps"))
        client.emit(PacketEvents.packet(3))
        records = [json.loads(record.content_json) for record in session.snapshot_records() if record.kind == "packet"]
        assert [record["timestamp"] for record in records] == [3]
        assert session.runner.context.progress.packets == 1


class TestPendingRecords:
    """Keep early and malformed events within the record contract."""

    def test_pending_buffer_has_message_and_byte_caps(self, capture_harness: CaptureHarness) -> None:
        """Bound records while the accepted identifier is still unavailable."""
        harness = capture_harness
        harness.api.script.start.release.clear()
        session = harness.start()
        assert harness.api.script.start.entered.wait(1.0)
        client = harness.api.script.stop.sockets[0]
        for timestamp in range(200):
            client.emit(PacketEvents.packet(timestamp))
        pending = session.runner._monitor.records.pending
        assert pending.last_seq == 200 and pending.dropped >= 100
        assert pending.bytes_used <= 256 * 1024
        harness.api.script.start.release.set()
        harness.wait(lambda: session.state is SessionState.LIVE)
        records = [json.loads(record.content_json) for record in session.snapshot_records() if record.kind == "packet"]
        assert len(records) == 100 and records[0]["timestamp"] == 100
        assert any("early records" in record.content_json for record in session.snapshot_records())

    @pytest.mark.parametrize("data", ["not JSON", "[]", {"capture_id": Identities.CAPTURE}, {"pcap_dict": {}}])
    def test_invalid_event_reports_failure_and_cleanup(self, capture_harness: CaptureHarness, data: object) -> None:
        """Do not turn malformed packet events into successful capture output."""
        harness = capture_harness
        session = harness.start()
        harness.wait(lambda: session.state is SessionState.LIVE)
        client = harness.api.script.stop.sockets[0]
        client.emit({"event": "data", "channel": f"/sites/{Identities.SITE}/pcaps", "data": data})
        harness.wait(lambda: not session.live)
        assert session.state is SessionState.FAILED
        assert client.disconnect_count == 1 and not client.ready()
        assert [action[0] for action in harness.api.script.actions].count("DELETE") == 1

    def test_matching_end_record_finishes_without_cloud_stop(self, capture_harness: CaptureHarness) -> None:
        """Recognize the documented terminal event after one packet."""
        harness = capture_harness
        session = harness.start()
        harness.wait(lambda: session.state is SessionState.LIVE)
        client = harness.api.script.stop.sockets[0]
        client.emit(PacketEvents.packet(1))
        client.emit(PacketEvents.end())
        harness.wait(lambda: not session.live)
        assert session.state is SessionState.FINISHED
        assert [action[0] for action in harness.api.script.actions].count("DELETE") == 0
        assert not client.ready()

    @pytest.mark.parametrize("cycle", range(10))
    def test_real_sdk_cleanup_releases_every_owned_thread(
        self, capture_harness: CaptureHarness, monkeypatch: pytest.MonkeyPatch, cycle: int
    ) -> None:
        """Repeat the real SDK shutdown race through controlled local sockets."""
        harness = capture_harness
        stream = LocalPacketStream(harness.api)
        monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
        monkeypatch.setattr(_MistWebsocket, "_build_ws_url", lambda _client: stream.url)
        harness.manager._runner_factory = RunnerFactory(
            harness.api, CaptureDependencies(harness.clock, harness.clock.wait)
        )
        try:
            session = harness.start()
            harness.wait(lambda: session.state is SessionState.LIVE)
            stream.packet(cycle)
            harness.wait(lambda: session.runner.context.progress.packets == 1)
            harness.manager.stop(session.session_id)
            session.runner.worker.join(timeout=12.0)
            client = session.runner._monitor.connection.client
            assert session.state is SessionState.STOPPED and not session.runner.worker.is_alive()
            assert not client._thread.is_alive() and not client._callback_thread.is_alive()
            assert client.ready() is False and stream.state.clients == set()
            assert [action[0] for action in harness.api.script.actions].count("DELETE") == 1
        finally:
            stream.close()

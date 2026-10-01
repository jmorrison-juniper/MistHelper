"""Duration, payload, and resource limits through real capture services."""

from __future__ import annotations

import json

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.websocket_streams.catalog.utilities import UtilityCatalog
from src.websocket_streams.intake.fields import FieldValueChecker, StreamRequestError
from src.websocket_streams.live.captures.control import CaptureBodies
from src.websocket_streams.live.captures.runner import PacketCaptureRunner
from src.websocket_streams.live.sessions.record import SessionState
from src.websocket_streams.live.sessions.settings import StreamSettings
from tests.unit.websocket_streams.live.captures.support.portal import CaptureHarness, PacketEvents
from tests.unit.websocket_streams.live.captures.support.sdk import Identities


class TestCaptureDuration:
    """Prove the exact duration range rather than the old utility timer."""

    @pytest.mark.parametrize("duration", [60, 120, 3600])
    def test_packets_continue_for_the_requested_duration(self, capture_harness: CaptureHarness, duration: int) -> None:
        """Accept records before, after, and near the selected deadline."""
        harness = capture_harness
        session = harness.start(duration)
        harness.wait(lambda: session.state is SessionState.LIVE)
        client = harness.api.script.stop.sockets[0]
        times = sorted({59, duration - 1} | ({61} if duration > 60 else set()))
        for timestamp in times:
            harness.clock.advance(timestamp)
            client.emit(PacketEvents.packet(timestamp))
            harness.manager.read(session.session_id, 0, 500)
            harness.manager.reap_once()
            assert session.state is SessionState.LIVE
        assert isinstance(session.runner, PacketCaptureRunner)
        assert session.runner.context.progress.deadline == duration
        records = [json.loads(record.content_json) for record in session.snapshot_records() if record.kind == "packet"]
        assert [record["timestamp"] for record in records] == times
        harness.clock.advance(duration)
        harness.wait(lambda: not session.live)
        session.runner.worker.join(timeout=2.0)
        assert session.state is SessionState.FINISHED and not session.runner.worker.is_alive()
        assert client.disconnect_count == 1 and not client.ready()

    @pytest.mark.parametrize(
        "duration",
        [
            59,
            3601,
            86400,
            -60,
            True,
            60.0,
            "60.5",
            None,
            "",
            "٦٠",
            "６０",
            "9" * 5000,
            pytest.param(10**5000, id="oversized-int"),
        ],
    )
    def test_invalid_duration_is_refused_before_sdk_work(
        self, capture_harness: CaptureHarness, duration: object
    ) -> None:
        """Reject unsafe duration shapes before device lookup, connection, or POST."""
        harness = capture_harness
        with pytest.raises(StreamRequestError) as caught:
            harness.services.start_session(harness.body(duration))
        assert caught.value.code == "bad_request" and caught.value.extra["field"] == "duration"
        assert harness.api.script.actions == []
        assert harness.manager.live_count() == 0

    def test_omitted_duration_keeps_the_explicit_sixty_second_default(self, capture_harness: CaptureHarness) -> None:
        """Keep the existing request default without accepting invalid explicit values."""
        body = capture_harness.body()
        body["parameters"].pop("duration")
        request = capture_harness.services._checker().check(body)
        plan = CaptureBodies.build(request)
        assert request.parameters["duration"] == plan.duration == 60
        assert plan.body["duration"] == 60

    @given(duration=st.integers(min_value=60, max_value=3600))
    def test_every_supported_integer_remains_unchanged(self, duration: int) -> None:
        """Apply the actual field checker to generated valid durations."""
        definition = UtilityCatalog().get("ap.remotePcapWired")
        assert definition is not None
        field = next(field for field in definition.fields if field.name == "duration")
        assert FieldValueChecker().check(field, str(duration)) == duration
        assert field.minimum == 60 and field.maximum == 3600

    def test_all_capture_fields_advertise_the_same_range(self) -> None:
        """Keep each SDK packet utility and the public limit consistent."""
        captures = [entry for entry in UtilityCatalog().entries() if entry.output == "packets"]
        fields = [next(field for field in entry.fields if field.name == "duration") for entry in captures]
        assert len(captures) == len(fields) == 7
        assert {(field.minimum, field.maximum, field.default, field.required) for field in fields} == {
            (60, 3600, 60, True)
        }
        assert StreamSettings().limits_payload()["capture_seconds"] == 3600


class TestCapturePayloads:
    """Keep every SDK family and packet ceiling in the real request path."""

    @pytest.mark.parametrize(
        ("family", "key", "kind", "target"),
        [
            ("ap", "ap.remotePcapWired", "wired", "ap_mac"),
            ("ap", "ap.remotePcapWireless", "radiotap", "ap_mac"),
            ("ex", "ex.remotePcap", "switch", "switches"),
            ("srx", "srx.remotePcap", "gateway", "gateways"),
            ("ssr", "ssr.remotePcap", "gateway", "gateways"),
            ("mxedge", "mxedge.siteRemotePcap", "mxedge", "mxedges"),
            ("mxedge", "mxedge.orgRemotePcap", "mxedge", "mxedges"),
        ],
    )
    def test_payload_and_scope_use_the_exact_sdk(self, family: str, key: str, kind: str, target: str) -> None:
        """Call the installed capture function with the selected duration and device."""
        harness = CaptureHarness(family)
        try:
            session = harness.start(3600, key)
            harness.wait(lambda: session.state is SessionState.LIVE)
            posts = [action for action in harness.api.script.actions if action[0] == "POST"]
            assert len(posts) == 1 and posts[0][2]["type"] == kind
            assert posts[0][2]["duration"] == 3600 and posts[0][2]["format"] == "stream"
            assert target in posts[0][2] and "port_ids" not in posts[0][2] and "interfaces" not in posts[0][2]
            group = "orgs" if key == "mxedge.orgRemotePcap" else "sites"
            identifier = Identities.ORG if group == "orgs" else Identities.SITE
            assert posts[0][1] == f"/api/v1/{group}/{identifier}/pcaps/capture"
            assert harness.api.script.stop.sockets[0]._channels == [f"/{group}/{identifier}/pcaps"]
            if family == "ssr":
                assert posts[0][2]["raw"] is False
        finally:
            harness.close()


class TestCaptureScopeAndContext:
    """Preserve regional routing, caller context, and neighboring streams."""

    @pytest.mark.parametrize(
        "host",
        [
            "api.mist.com",
            "api.gc1.mist.com",
            "api.ac2.mist.com",
            "api.gc2.mist.com",
            "api.gc4.mist.com",
            "api.eu.mist.com",
            "api.gc3.mist.com",
            "api.ac6.mist.com",
            "api.gc6.mist.com",
            "api.ac5.mist.com",
            "api.gc5.mist.com",
            "api.gc7.mist.com",
        ],
    )
    def test_every_region_retains_sdk_host_and_authentication(self, capture_harness: CaptureHarness, host: str) -> None:
        """Use the real SDK URL and header helpers without a remote connection."""
        from mistapi.websockets.__ws_client import _MistWebsocket

        api = capture_harness.api
        api._cloud_uri = host
        client = _MistWebsocket(api, channels=[f"/sites/{Identities.SITE}/pcaps"])
        assert client._build_ws_url() == f"wss://{host.replace('api.', 'api-ws.', 1)}/api-ws/v1/stream"
        assert client._get_headers()["Authorization"] == "Token " + api._apitoken[api._apitoken_index]
        assert client._build_sslopt() == {}
        assert client._get_cookie() is None

    def test_scope_guard_refuses_duplicate_without_consuming_a_slot(self, capture_harness: CaptureHarness) -> None:
        """Keep duplicate capture admission separate from the total session limit."""
        harness = capture_harness
        session = harness.start()
        harness.wait(lambda: session.state is SessionState.LIVE)
        with pytest.raises(StreamRequestError) as caught:
            harness.start()
        assert caught.value.code == "session_live"
        assert harness.manager.live_count() == 1
        assert [action[0] for action in harness.api.script.actions].count("POST") == 1

    def test_regular_utility_keeps_the_existing_runner(self, capture_harness: CaptureHarness) -> None:
        """Do not extend the SDK utility timer for unrelated commands."""
        request = capture_harness.services._checker().check(
            {
                "kind": "utility",
                "key": "ap.ping",
                "targets": {"site_id": Identities.SITE, "device_id": Identities.DEVICE},
                "parameters": {"host": "192.0.2.1"},
            }
        )
        session = capture_harness.manager._new_session(request)
        assert session.runner.__class__.__name__ == "UtilityRunner"
        assert "duration" not in request.parameters
        assert [action[0] for action in capture_harness.api.script.actions].count("POST") == 0


class TestCaptureResourceLimits:
    """Preserve packet, session, and buffer bounds at the new boundary."""

    @pytest.mark.parametrize("length", [64, 1536, 1537, 2048])
    def test_packet_length_preserves_the_1536_ceiling(self, capture_harness: CaptureHarness, length: int) -> None:
        """Keep the current packet length repair at the new API boundary."""
        body = capture_harness.body()
        body["parameters"]["max_pkt_len"] = length
        if length <= 1536:
            request = capture_harness.services._checker().check(body)
            assert CaptureBodies.build(request).body["max_pkt_len"] == length
        else:
            with pytest.raises(StreamRequestError) as caught:
                capture_harness.services.start_session(body)
            assert caught.value.extra["field"] == "max_pkt_len"
            assert capture_harness.manager.live_count() == 0

    def test_another_ap_mac_is_refused_before_connection(self, capture_harness: CaptureHarness) -> None:
        """Do not silently target another AP through an optional field."""
        body = capture_harness.body(key="ap.remotePcapWireless")
        body["parameters"]["ap_mac"] = "001122334455"
        with pytest.raises(StreamRequestError) as caught:
            capture_harness.services.start_session(body)
        assert caught.value.extra["field"] == "ap_mac"
        assert [action[0] for action in capture_harness.api.script.actions].count("POST") == 0
        assert capture_harness.api.script.stop.sockets == []

    def test_session_buffer_and_rate_window_stay_bounded(self, capture_harness: CaptureHarness) -> None:
        """Use the actual existing caps under a packet burst."""
        harness = capture_harness
        session = harness.start(3600)
        harness.wait(lambda: session.state is SessionState.LIVE)
        client = harness.api.script.stop.sockets[0]
        for timestamp in range(600):
            client.emit(PacketEvents.packet(timestamp))
        assert len(session.snapshot_records()) == 500
        assert session.counters.dropped == 101
        assert session.buffer.bytes_used <= 8 * 1024 * 1024
        assert client._callback_queue.maxsize == client._queue.maxsize == 64

    def test_same_scope_and_total_session_limits_fail_before_start(self) -> None:
        """Keep capture scope admission atomic with the existing live limit."""
        harness = CaptureHarness(settings=StreamSettings(max_sessions=1))
        try:
            first = harness.start()
            harness.wait(lambda: first.state is SessionState.LIVE)
            with pytest.raises(StreamRequestError) as caught:
                harness.start()
            assert caught.value.code == "limit_reached"
            assert [action[0] for action in harness.api.script.actions].count("POST") == 1
            assert harness.manager.live_count() == 1
        finally:
            harness.close()

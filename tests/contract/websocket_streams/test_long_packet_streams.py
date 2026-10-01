"""Actual WebSockets routes with duration, permission, CSRF, and cloud stop checks."""

from __future__ import annotations

import json
import re

import pytest

from src.websocket_streams.live.sessions.record import SessionState
from tests.unit.websocket_streams.live.captures.support.portal import CaptureHarness, PacketEvents, PortalFixture
from tests.unit.websocket_streams.live.captures.support.sdk import Identities


class TestPacketRoutes:
    """Keep real controller and request guards in the feature proof."""

    @staticmethod
    def token(client) -> str:
        """Read the real CSRF token from the actual page."""
        page = client.get("/websockets")
        assert page.status_code == 200
        match = re.search(r'<meta name="csrf-token" content="([^"]+)">', page.get_data(as_text=True))
        assert match is not None
        return match.group(1)

    @pytest.mark.parametrize("duration", [60, 120, 3600])
    def test_controller_streams_records_past_sixty_seconds_and_stops_cloud(self, duration: int) -> None:
        """Exercise start, actual buffer reads, and stop through protected routes."""
        harness = CaptureHarness()
        try:
            client = PortalFixture.app(harness).test_client()
            headers = {"X-CSRFToken": self.token(client)}
            started = client.post("/api/websockets/sessions", json=harness.body(duration), headers=headers)
            assert started.status_code == 201
            session_id = started.json["session_id"]
            session = harness.manager._get(session_id)
            harness.wait(lambda: session.state is SessionState.LIVE)
            timestamp = 61 if duration > 60 else 59
            harness.clock.advance(timestamp)
            harness.api.script.stop.sockets[0].emit(PacketEvents.packet(timestamp))
            answer = client.get(f"/api/websockets/sessions/{session_id}/messages")
            assert answer.status_code == 200 and answer.json["session"]["state"] == "live"
            assert any(
                record["content"].get("timestamp") == timestamp
                for record in answer.json["messages"]
                if record["kind"] == "packet"
            )
            assert client.post(f"/api/websockets/sessions/{session_id}/stop", headers=headers).status_code == 202
            harness.wait(lambda: session.state is SessionState.STOPPED)
            assert [action[0] for action in harness.api.script.actions].count("DELETE") == 1
        finally:
            harness.close()

    @pytest.mark.parametrize("duration", [59, 3601, "٦٠", "9" * 5000, True, None])
    def test_invalid_durations_return_http_400_without_sdk_work(self, duration: object) -> None:
        """Run invalid values through the actual JSON controller."""
        harness = CaptureHarness()
        try:
            client = PortalFixture.app(harness).test_client()
            response = client.post(
                "/api/websockets/sessions", json=harness.body(duration), headers={"X-CSRFToken": self.token(client)}
            )
            assert response.status_code == 400
            assert response.json["code"] == "bad_request" and response.json["field"] == "duration"
            assert harness.api.script.actions == [] and harness.manager.live_count() == 0
        finally:
            harness.close()

    def test_csrf_raw_paths_and_caller_org_id_remain_refused(self) -> None:
        """Do not disable existing request protections for the new runner."""
        harness = CaptureHarness()
        try:
            client = PortalFixture.app(harness).test_client()
            assert client.post("/api/websockets/sessions", json=harness.body()).status_code == 400
            headers = {"X-CSRFToken": self.token(client)}
            body = harness.body()
            body["targets"]["org_id"] = Identities.OTHER
            response = client.post("/api/websockets/sessions", json=body, headers=headers)
            assert response.status_code == 400 and response.json["field"] == "org_id"
            body = harness.body() | {"path": "wss://127.0.0.1/other"}
            response = client.post("/api/websockets/sessions", json=body, headers=headers)
            assert response.status_code == 400 and response.json["field"] == "path"
            assert harness.api.script.actions == [] and harness.api.script.stop.sockets == []
        finally:
            harness.close()

    def test_download_redacts_credentials_and_omits_private_stream_context(self) -> None:
        """Keep secrets and raw stream identity out of actual route answers."""
        harness = CaptureHarness()
        try:
            client = PortalFixture.app(harness).test_client()
            headers = {"X-CSRFToken": self.token(client)}
            response = client.post("/api/websockets/sessions", json=harness.body(), headers=headers)
            session = harness.manager._get(response.json["session_id"])
            harness.wait(lambda: session.state is SessionState.LIVE)
            event = PacketEvents.packet(1)
            event["data"]["pcap_dict"]["api_token"] = harness.api._apitoken[0]
            harness.api.script.stop.sockets[0].emit(event)
            download = client.get(f"/api/websockets/sessions/{session.session_id}/download")
            text = download.get_data(as_text=True)
            packets = [json.loads(line) for line in text.splitlines() if json.loads(line)["kind"] == "packet"]
            assert packets[0]["content"]["api_token"] == "[REDACTED]"
            assert harness.api._apitoken[0] not in text
            assert "pcap_raw" not in text and "/pcaps" not in text and "wss://" not in text
        finally:
            harness.close()

"""Cloud stop identity, failure states, and required capture cleanup."""

from __future__ import annotations

import pytest
from requests import Request, Response, Session
from requests.exceptions import Timeout

from src.websocket_streams.intake.fields import StreamRequestError
from src.websocket_streams.live.captures.control import CaptureResponses
from src.websocket_streams.live.captures.runner import PacketCaptureRunner
from src.websocket_streams.live.captures.transport import CaptureHttpSession
from src.websocket_streams.live.sessions.record import SessionState
from tests.unit.websocket_streams.live.captures.support.portal import CaptureHarness, PacketEvents
from tests.unit.websocket_streams.live.captures.support.sdk import Identities
from websocket import WebSocketException


class TestCaptureStop:
    """Require a cloud stop rather than only a stream disconnect."""

    def test_early_stop_checks_active_identity_and_stops_once(self, capture_harness: CaptureHarness) -> None:
        """Use exact SDK status and DELETE functions for the accepted capture."""
        harness = capture_harness
        session = harness.start(3600)
        harness.wait(lambda: session.state is SessionState.LIVE)
        harness.clock.advance(61)
        harness.manager.stop(session.session_id)
        harness.manager.stop(session.session_id)
        harness.wait(lambda: not session.live)
        operations = [(action[0], action[1]) for action in harness.api.script.actions]
        uri = f"/api/v1/sites/{Identities.SITE}/pcaps/capture"
        assert operations[-2:] == [("GET", uri), ("DELETE", uri)]
        assert operations.count(("DELETE", uri)) == 1
        assert session.state is SessionState.STOPPED and "Mist accepted" in session.reason
        assert harness.api.script.stop.sockets[0].disconnect_count == 1
        session.runner.worker.join(timeout=2.0)
        assert not session.runner.worker.is_alive()

    def test_org_stop_preserves_organization_identity(self) -> None:
        """Stop the selected organization capture through its exact SDK functions."""
        harness = CaptureHarness("mxedge")
        try:
            session = harness.start(120, "mxedge.orgRemotePcap")
            harness.wait(lambda: session.state is SessionState.LIVE)
            harness.manager.stop(session.session_id)
            harness.wait(lambda: not session.live)
            uri = f"/api/v1/orgs/{Identities.ORG}/pcaps/capture"
            operations = [(action[0], action[1]) for action in harness.api.script.actions]
            assert operations[-2:] == [("GET", uri), ("DELETE", uri)]
            assert session.state is SessionState.STOPPED
            assert all("/sites/" not in action[1] for action in harness.api.script.actions)
        finally:
            harness.close()

    def test_another_active_capture_refuses_cloud_stop(self, capture_harness: CaptureHarness) -> None:
        """Do not use a stored capture list or stop another capture."""
        harness = capture_harness
        session = harness.start()
        harness.wait(lambda: session.state is SessionState.LIVE)
        harness.api.script.status.data = {"id": Identities.OTHER}
        harness.manager.stop(session.session_id)
        harness.wait(lambda: not session.live)
        assert session.state is SessionState.FAILED and "identifier changed" in session.reason
        assert [action[0] for action in harness.api.script.actions].count("DELETE") == 0
        assert not harness.api.script.stop.sockets[0].ready()

    @pytest.mark.parametrize("status", [400, 401, 403, 404, 429, 500, 503])
    def test_failed_cloud_stop_is_not_success(self, capture_harness: CaptureHarness, status: int) -> None:
        """Make both HTTP 4xx and HTTP 5xx stop responses fail explicitly."""
        harness = capture_harness
        session = harness.start()
        harness.wait(lambda: session.state is SessionState.LIVE)
        harness.api.script.stop.status = status
        harness.manager.stop(session.session_id)
        harness.wait(lambda: not session.live)
        assert session.state is SessionState.FAILED and f"HTTP {status}" in session.reason
        assert [action[0] for action in harness.api.script.actions].count("DELETE") == 1
        assert not harness.api.script.stop.sockets[0].ready()

    def test_stop_before_confirmation_never_starts_capture(self, capture_harness: CaptureHarness) -> None:
        """Stop before admission even if a late confirmation arrives."""
        harness = capture_harness
        harness.api.script.stop.auto_ack = False
        session = harness.start()
        harness.wait(lambda: bool(harness.api.script.stop.sockets))
        harness.manager.stop(session.session_id)
        harness.api.script.stop.sockets[0].emit(
            {"event": "channel_subscribed", "channel": f"/sites/{Identities.SITE}/pcaps"}
        )
        harness.wait(lambda: not session.live)
        assert session.state is SessionState.STOPPED
        assert [action[0] for action in harness.api.script.actions].count("POST") == 0
        assert [action[0] for action in harness.api.script.actions].count("DELETE") == 0


class TestCaptureFailures:
    """Prove refusal, disconnect, permission, and timeout outcomes."""

    @pytest.mark.parametrize("status", [400, 401, 403, 404, 429, 500, 503])
    def test_start_http_4xx_and_http_5xx_refuse_and_close(self, capture_harness: CaptureHarness, status: int) -> None:
        """Close the confirmed stream when the real SDK start is refused."""
        harness = capture_harness
        harness.api.script.start.status = status
        session = harness.start()
        harness.wait(lambda: not session.live)
        assert session.state is SessionState.FAILED and f"HTTP {status}" in session.reason
        assert [action[0] for action in harness.api.script.actions].count("POST") == 1
        assert [action[0] for action in harness.api.script.actions].count("DELETE") == 0
        assert not harness.api.script.stop.sockets[0].ready()

    def test_subscription_timeout_closes_without_post(self, capture_harness: CaptureHarness) -> None:
        """Measure the ten-second subscription deadline with the controlled clock."""
        harness = capture_harness
        harness.api.script.stop.auto_ack = False
        session = harness.start()
        harness.wait(lambda: bool(harness.clock.waits))
        harness.clock.advance(10)
        harness.wait(lambda: not session.live)
        assert session.state is SessionState.FAILED and "not confirmed" in session.reason
        assert [action[0] for action in harness.api.script.actions].count("POST") == 0
        assert not harness.api.script.stop.sockets[0].ready()

    def test_subscription_refusal_never_starts_capture(self, capture_harness: CaptureHarness) -> None:
        """Treat the documented refusal as a terminal failure."""
        harness = capture_harness
        harness.api.script.stop.auto_ack = False
        session = harness.start()
        harness.wait(lambda: bool(harness.api.script.stop.sockets))
        client = harness.api.script.stop.sockets[0]
        client.emit({"event": "subscribe_failed", "channel": f"/sites/{Identities.SITE}/pcaps"})
        harness.wait(lambda: not session.live)
        assert session.state is SessionState.FAILED and "refused" in session.reason
        assert [action[0] for action in harness.api.script.actions].count("POST") == 0
        assert client.disconnect_count == 1

    def test_unexpected_disconnect_requests_matching_cloud_stop(self, capture_harness: CaptureHarness) -> None:
        """Do not report a clean capture after terminal transport loss."""
        harness = capture_harness
        session = harness.start()
        harness.wait(lambda: session.state is SessionState.LIVE)
        client = harness.api.script.stop.sockets[0]
        client._on_close_cb(1006, "untrusted remote text")
        harness.wait(lambda: not session.live)
        assert session.state is SessionState.FAILED and "connection closed" in session.reason
        assert "untrusted" not in session.reason
        assert [action[0] for action in harness.api.script.actions].count("DELETE") == 1
        assert not client.ready()

    def test_foreign_organization_never_connects_or_starts(self, capture_harness: CaptureHarness) -> None:
        """Use actual target reads before any stream or capture work."""
        harness = capture_harness
        harness.api.script.scope.org_id = Identities.OTHER
        session = harness.start()
        harness.wait(lambda: not session.live)
        assert session.state is SessionState.FAILED and "portal organization" in session.reason
        assert harness.api.script.stop.sockets == []
        assert [action[0] for action in harness.api.script.actions].count("POST") == 0


class TestCaptureCleanup:
    """Keep late responses and lifecycle paths explicit and bounded."""

    def test_stop_during_start_stops_the_late_accepted_capture(self, capture_harness: CaptureHarness) -> None:
        """Wait for accepted identity instead of forgetting an in-flight capture."""
        harness = capture_harness
        harness.api.script.start.release.clear()
        session = harness.start()
        assert harness.api.script.start.entered.wait(1.0)
        harness.manager.stop(session.session_id)
        harness.api.script.start.release.set()
        harness.wait(lambda: not session.live)
        assert session.state is SessionState.STOPPED
        assert [action[0] for action in harness.api.script.actions].count("POST") == 1
        assert [action[0] for action in harness.api.script.actions].count("DELETE") == 1
        assert not harness.api.script.stop.sockets[0].ready()

    @pytest.mark.parametrize(
        "data", [{}, {"id": Identities.CAPTURE, "org_id": Identities.OTHER}, {"error": "local refusal"}]
    )
    def test_invalid_start_response_is_uncertain_not_success(
        self, capture_harness: CaptureHarness, data: object
    ) -> None:
        """Release the stream without choosing an untrusted stop identity."""
        harness = capture_harness
        harness.api.script.start.data = data
        session = harness.start()
        harness.wait(lambda: not session.live)
        assert session.state is SessionState.FAILED
        assert [action[0] for action in harness.api.script.actions].count("DELETE") == 0
        assert not harness.api.script.stop.sockets[0].ready()

    def test_silent_capture_reaches_its_own_timeout(self, capture_harness: CaptureHarness) -> None:
        """Do not apply the utility's thirty-second first-message timeout."""
        harness = capture_harness
        session = harness.start()
        harness.wait(lambda: session.state is SessionState.LIVE)
        harness.clock.advance(61)
        harness.manager.read(session.session_id, 0, 1)
        assert session.state is SessionState.LIVE
        harness.clock.advance(120)
        harness.wait(lambda: not session.live)
        assert session.state is SessionState.TIMED_OUT
        assert [action[0] for action in harness.api.script.actions].count("DELETE") == 0
        assert not harness.api.script.stop.sockets[0].ready()

    def test_idle_stop_and_shell_input_keep_existing_rules(self, capture_harness: CaptureHarness) -> None:
        """Keep idle capture cancellation and non-shell input refusal active."""
        harness = capture_harness
        session = harness.start(3600)
        harness.wait(lambda: session.state is SessionState.LIVE)
        assert isinstance(session.runner, PacketCaptureRunner)
        with pytest.raises(StreamRequestError) as caught:
            session.runner.send_input("show version")
        assert caught.value.code == "not_open"
        harness.clock.advance(121)
        harness.manager.reap_once()
        harness.wait(lambda: not session.live)
        assert session.state is SessionState.STOPPED
        assert [action[0] for action in harness.api.script.actions].count("DELETE") == 1

    def test_natural_end_without_packets_is_explicit(self, capture_harness: CaptureHarness) -> None:
        """Recognize a matching end event without inventing packet output."""
        harness = capture_harness
        session = harness.start()
        harness.wait(lambda: session.state is SessionState.LIVE)
        harness.api.script.stop.sockets[0].emit(PacketEvents.end())
        harness.wait(lambda: not session.live)
        assert session.state is SessionState.TIMED_OUT
        assert [action[0] for action in harness.api.script.actions].count("DELETE") == 0


class TestCaptureTransport:
    """Measure HTTP deadlines and private transport isolation."""

    def test_http_options_and_source_context_remain_private(
        self, capture_harness: CaptureHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Keep source headers, cookies, TLS, proxy, and retry behavior unchanged."""
        harness = capture_harness
        source = harness.api._session
        source.cookies.set("local-cookie", "local-value")
        source.verify = "local-ca.pem"
        source.cert = ("local-cert.pem", "local-key.pem")
        source.proxies = {"https": "http://127.0.0.1:9600"}
        observed = []

        def send(_session, request, **options):
            """Record the actual requests boundary without a network request."""
            observed.append((request, options))
            response = Response()
            response.status_code = 200
            response.request = request
            response._content = b"{}"
            return response

        monkeypatch.setattr(Session, "send", send)
        clone, http = CaptureHttpSession.for_api(harness.api, harness.clock)
        try:
            http.send(Request("GET", "https://api.eu.mist.com/local-fixture").prepare())
            assert observed[0][1]["timeout"] == (5.0, 10.0)
            assert http.headers == source.headers and http.cookies == source.cookies
            assert http.verify == source.verify and http.cert == source.cert and http.proxies == source.proxies
            assert http.headers is not source.headers and http.cookies is not source.cookies
            assert clone._MAX_429_RETRIES == harness.api._MAX_429_RETRIES == 3
            assert http.adapters["https://"] is not source.adapters["https://"]
        finally:
            http.close()

    def test_elapsed_and_cancelled_http_phases_refuse_transmission(self, capture_harness: CaptureHarness) -> None:
        """Fail before a request after its deadline or an earlier stop."""
        harness = capture_harness
        session = harness.start()
        harness.wait(lambda: session.state is SessionState.LIVE)
        http = session.runner._monitor.api.http
        http.prepare(None)
        harness.clock.advance(30)
        request = Request("GET", "https://api.eu.mist.com/local-fixture").prepare()
        with pytest.raises(Timeout):
            http.send(request)
        http.prepare(session.runner.context.events.stopping)
        session.runner.context.events.stopping.set()
        with pytest.raises(Timeout):
            http.send(request)
        assert [action[0] for action in harness.api.script.actions].count("POST") == 1

    @pytest.mark.parametrize("retry_after", ["3600", "9" * 5000, "٦٠", "-1", "invalid"])
    def test_unbounded_rate_waits_fail_without_sleep(self, capture_harness: CaptureHarness, retry_after: str) -> None:
        """Keep rate-limit retries inside the declared HTTP phase."""
        harness = capture_harness
        _, http = CaptureHttpSession.for_api(harness.api, harness.clock)
        response = harness.api.answer(429, {})
        raw = Response()
        raw.headers["Retry-After"] = retry_after
        try:
            with pytest.raises(Timeout):
                http.wait_rate_limit(raw, 0)
            assert harness.clock() == 0 and response.status_code == 429
            assert harness.api.script.actions == []
        finally:
            http.close()

    def test_connection_cleanup_failure_does_not_prevent_cloud_stop(
        self, capture_harness: CaptureHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Preserve the verified cloud action even if SDK cleanup reports failure."""
        harness = capture_harness
        session = harness.start()
        harness.wait(lambda: session.state is SessionState.LIVE)
        connection = session.runner._monitor.connection
        original = connection.close

        def fail_after_close() -> None:
            """Release the actual socket, then report the controlled cleanup fault."""
            original()
            raise WebSocketException("untrusted remote text")

        monkeypatch.setattr(connection, "close", fail_after_close)
        harness.manager.stop(session.session_id)
        harness.wait(lambda: not session.live)
        assert session.state is SessionState.FAILED and "cleanup failed" in session.reason
        assert "untrusted" not in session.reason
        assert [action[0] for action in harness.api.script.actions].count("DELETE") == 1
        assert not harness.api.script.stop.sockets[0].ready()

    def test_stop_before_worker_start_never_creates_a_connection(self, capture_harness: CaptureHarness) -> None:
        """Prove cancellation before the first worker instruction."""
        harness = capture_harness
        request = harness.services._checker().check(harness.body())
        session = harness.manager._new_session(request)
        assert isinstance(session.runner, PacketCaptureRunner)
        session.runner.stop()
        session.runner.start()
        session.runner.worker.join(timeout=2.0)
        assert session.state is SessionState.STOPPED and not session.runner.worker.is_alive()
        assert harness.api.script.stop.sockets == []
        assert [action[0] for action in harness.api.script.actions].count("POST") == 0


class TestCaptureResponseGuards:
    """Prove malformed and success-shaped response failures."""

    @pytest.mark.parametrize("raw", ["<html>local proxy error</html>", "{broken", "[]"])
    def test_invalid_success_body_is_refused(self, raw: str) -> None:
        """Do not accept the SDK's empty object after JSON parsing fails."""
        from types import SimpleNamespace

        response = SimpleNamespace(status_code=200, data={}, raw_data=raw)
        with pytest.raises(StreamRequestError) as caught:
            CaptureResponses.stopped(response)
        assert caught.value.code == "not_ready" and "invalid" in caught.value.message

    @pytest.mark.parametrize(
        "data", [{"error": "local refusal"}, {"failed": ["local device"]}, {"success": False}, {"ok": False}]
    )
    def test_http_200_error_object_is_not_a_confirmed_stop(self, capture_harness: CaptureHarness, data: dict) -> None:
        """Check explicit response failures without exposing their content."""
        harness = capture_harness
        session = harness.start()
        harness.wait(lambda: session.state is SessionState.LIVE)
        harness.api.script.stop.data = data
        harness.manager.stop(session.session_id)
        harness.wait(lambda: not session.live)
        assert session.state is SessionState.FAILED
        assert [action[0] for action in harness.api.script.actions].count("DELETE") == 1
        assert "local refusal" not in session.reason

    @pytest.mark.parametrize("status", [403, 500])
    def test_failed_status_read_never_sends_delete(self, capture_harness: CaptureHarness, status: int) -> None:
        """Prove both HTTP 4xx and HTTP 5xx identity-read refusals."""
        harness = capture_harness
        session = harness.start()
        harness.wait(lambda: session.state is SessionState.LIVE)
        harness.api.script.status.status = status
        harness.manager.stop(session.session_id)
        harness.wait(lambda: not session.live)
        assert session.state is SessionState.FAILED and f"HTTP {status}" in session.reason
        assert [action[0] for action in harness.api.script.actions].count("DELETE") == 0

    def test_cleanup_releases_private_http_session_after_start_exception(
        self, capture_harness: CaptureHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Keep typed transport failures out of a successful card state."""
        harness = capture_harness

        def fail_start() -> None:
            """Raise before a synthetic capture response exists."""
            raise OSError("untrusted remote text")

        harness.api.script.start.before_answer = fail_start
        closed = []
        original = CaptureHttpSession.close

        def close(http) -> None:
            """Observe the actual private HTTP cleanup."""
            closed.append(http)
            original(http)

        monkeypatch.setattr(CaptureHttpSession, "close", close)
        session = harness.start()
        harness.wait(lambda: not session.live)
        assert session.state is SessionState.FAILED and "untrusted" not in session.reason
        assert len(closed) == 1
        assert not harness.api.script.stop.sockets[0].ready()

    def test_packet_logs_exclude_remote_text_and_credentials(
        self, capture_harness: CaptureHarness, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Keep metadata logs ASCII and omit packet and authentication content."""
        import logging

        harness = capture_harness
        caplog.set_level(logging.DEBUG)
        session = harness.start()
        harness.wait(lambda: session.state is SessionState.LIVE)
        client = harness.api.script.stop.sockets[0]
        client._on_error_cb(ConnectionError(harness.api._apitoken[0]))
        client.emit(PacketEvents.packet(1))
        harness.manager.stop(session.session_id)
        harness.wait(lambda: not session.live)
        own = "\n".join(
            record.getMessage()
            for record in caplog.records
            if record.name.startswith("src.websocket_streams.live.captures")
        )
        assert harness.api._apitoken[0] not in own
        assert "192.0.2.1" not in own and "pcap_raw" not in own
        assert own.isascii() and "error_type=ConnectionError" in own
        assert not harness.api.script.stop.sockets[0].ready()

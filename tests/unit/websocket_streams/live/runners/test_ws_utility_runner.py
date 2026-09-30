"""Tests for the WebSockets utility runner."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

from enum import Enum  # Enum conversion tests need a small enum.

import pytest  # The tests check input refusal.

from src.websocket_streams.catalog.model import (
    FieldKind,
    FieldSpec,
    Safety,
    UtilityDefinition,
)  # Tests build local definitions.
from src.websocket_streams.intake.fields import StreamRequestError  # Input refusal uses this error.
from src.websocket_streams.intake.start_request import StartRequest  # Tests build checked requests by hand.
from src.websocket_streams.live.runners import utility as utility_module  # The tests patch capture functions.
from src.websocket_streams.live.runners.utility import CaptureStopper, UtilityRunner  # The tests cover utility helpers.
from src.websocket_streams.live.sessions.record import SessionState  # Fake sinks record final state.


class FakeSink:
    """A fake session sink."""

    def __init__(self) -> None:
        """Build an empty sink."""
        self.messages: list[tuple[str, object, str | None]] = []  # Keep output messages.
        self.finished: list[tuple[SessionState, str]] = []  # Keep end states.

    def mark_live(self, note: str = "") -> None:
        """Ignore live transitions."""
        return None  # Utility runner does not call this method directly.

    def add_message(self, kind: str, content: object, *, source: str | None = None, summary: str | None = None) -> None:
        """Record one message."""
        self.messages.append((kind, content, summary))  # Tests verify message kind and summary.

    def finish(self, state: SessionState, reason: str) -> None:
        """Record a final state."""
        self.finished.append((state, reason))  # Tests verify end state mapping.

    def mark_input_ready(self) -> None:
        """Ignore shell readiness."""
        return None  # Utility runner never opens shell input.


class FakeResponse:
    """A fake SDK UtilResponse."""

    def __init__(self, status: int = 200, error: str | None = None) -> None:
        """Build one fake response.

        Args:
            status: The trigger status code.
            error: The WebSocket error text.
        """
        self.done = True  # The fake starts complete.
        self.ws_error = error  # The runner reads this field.
        self.trigger_api_response = type("Trigger", (), {"status_code": status})()  # The runner reads this status.
        self.disconnects = 0  # Stop tests count disconnect calls.

    def disconnect(self) -> None:
        """Record one disconnect call."""
        self.disconnects += 1  # The stop loop calls this method.


class TestUtilityRunner:
    """Verify utility runner behavior."""

    def test_messages_and_finish_states(self) -> None:
        """Map SDK output and states to the sink."""
        sink = FakeSink()  # Record runner output.
        runner = UtilityRunner(
            object(), self._request("lines"), sink, clock=lambda: 0.0, sleeper=lambda _delay: None
        )  # Build a utility runner.
        runner._on_message("line one")  # Simulate line output.
        assert sink.messages == [("text", "line one", None)]  # Line output becomes text.
        runner._response = FakeResponse(status=500)  # Simulate a trigger failure.
        runner._finish_from_response(0.0)  # Map the response to an end state.
        assert sink.finished[-1][0] == SessionState.FAILED  # Non-200 status fails.
        runner._response = FakeResponse()  # Simulate a clean response.
        runner._finish_from_response(0.0)  # Map the response to an end state.
        assert sink.finished[-1][0] == SessionState.FINISHED  # Output plus no error finishes.

    def test_timeout_stop_input_and_capture_arguments(self) -> None:
        """Cover timeout, stop, input refusal, and capture interface build."""
        sink = FakeSink()  # Record runner output.
        runner = UtilityRunner(
            object(), self._request("packets"), sink, clock=lambda: 60.0, sleeper=lambda _delay: None
        )  # Build a packet runner.
        runner._response = FakeResponse()  # Simulate a response with no output.
        runner._finish_from_response(0.0)  # Map no output to timeout.
        assert sink.finished[-1][0] == SessionState.TIMED_OUT  # No output times out.
        runner._response.done = False  # Keep the response open for stop.
        runner._disconnect_until_done()  # Ask the fake response to disconnect.
        assert runner._response.disconnects == 20  # The stop loop is bounded.
        with pytest.raises(StreamRequestError):  # Utility runners are not shells.
            runner.send_input("show version")  # Try shell input.
        capture = runner._capture_arguments()  # Build capture device interfaces.
        assert capture["device_interfaces"]["dev-a"] == {"ge-0/0/1": None}  # The SDK form matches the docstring.

    def test_packet_and_screen_messages(self) -> None:
        """Shape packet and screen output kinds."""
        packet_sink = FakeSink()  # Record packet output.
        packet_runner = UtilityRunner(
            object(), self._request("packets"), packet_sink, sleeper=lambda _delay: None
        )  # Build a packet runner.
        packet_runner._on_message({"src_ip": "1.1.1.1"})  # Simulate one packet.
        assert packet_sink.messages[0][0] == "packet"  # Packet output uses packet kind.
        screen_sink = FakeSink()  # Record screen output.
        screen_runner = UtilityRunner(
            object(), self._request("screen"), screen_sink, sleeper=lambda _delay: None
        )  # Build a screen runner.
        screen_runner._on_message("top")  # Simulate one screen.
        assert screen_sink.messages[0] == ("screen", "top", None)  # Screen output replaces the view.

    def test_sdk_arguments_org_target_enum_and_start_stop(self) -> None:
        """Cover SDK argument building, enum conversion, start, and stop."""
        runner = UtilityRunner(
            object(), self._org_request(), FakeSink(), sleeper=lambda _delay: None
        )  # Build an org runner.
        runner._run = lambda: None  # Keep the start thread away from the real SDK.
        runner.start()  # Start the background thread.
        runner.stop()  # Start the stop thread.
        args = runner._sdk_arguments(lambda **_kwargs: None)  # Build SDK arguments with a fake function.
        assert args["org_id"] == "org-a"  # Organization utilities pass org_id.
        assert args["duration"] == 60  # Capture utilities force 60 seconds.
        assert "device_interfaces" in args  # Mist Edge captures use device_interfaces.
        assert runner._enum_type(SampleEnum) is SampleEnum  # Direct enum annotations are found.
        assert (
            runner._enum_value(self._enum_function, "node", "node0") is SampleEnum.NODE0
        )  # Enum text becomes an enum.

    def test_capture_stopper_matches_before_stop(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Stop only matching site and organization captures."""
        calls: list[str] = []  # Record stop calls.
        response = type("Response", (), {"data": [{"id": "cap-a"}]})()  # Build a matching SDK response.
        monkeypatch.setattr(
            utility_module.site_pcaps, "listSitePacketCaptures", lambda *_args, **_kwargs: response
        )  # Fake the site read.
        monkeypatch.setattr(
            utility_module.site_pcaps, "stopSitePacketCapture", lambda *_args, **_kwargs: calls.append("site")
        )  # Fake the site stop.
        monkeypatch.setattr(
            utility_module.org_pcaps, "listOrgPacketCaptures", lambda *_args, **_kwargs: response
        )  # Fake the org read.
        monkeypatch.setattr(
            utility_module.org_pcaps, "stopOrgPacketCapture", lambda *_args, **_kwargs: calls.append("org")
        )  # Fake the org stop.
        stopper = CaptureStopper(object())  # Build the stopper.
        assert stopper.stop_site("site-a", "cap-a") is True  # Matching site capture stops.
        assert stopper.stop_org("org-a", "cap-a") is True  # Matching org capture stops.
        assert stopper.stop_site("site-a", "other") is False  # Nonmatching capture does not stop.
        assert calls == ["site", "org"]  # Only matching captures caused stop calls.

    def test_runner_stops_matching_capture_after_disconnect(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Call the capture stopper when a stopped runner has a capture id."""
        calls: list[str] = []  # Record stop calls.
        response = type("Response", (), {"data": [{"id": "cap-a"}]})()  # Build a matching capture list.
        monkeypatch.setattr(
            utility_module.site_pcaps, "listSitePacketCaptures", lambda *_args, **_kwargs: response
        )  # Fake the site read.
        monkeypatch.setattr(
            utility_module.site_pcaps, "stopSitePacketCapture", lambda *_args, **_kwargs: calls.append("site")
        )  # Fake the site stop.
        runner = UtilityRunner(
            object(), self._request("packets"), FakeSink(), sleeper=lambda _delay: None
        )  # Build a capture runner.
        runner._response = FakeResponse()  # Build a fake SDK response.
        runner._response.trigger_api_response.data = {"id": "cap-a"}  # Add the capture id from the trigger.
        runner._stop_capture_if_needed()  # Stop only the matching active capture.
        assert calls == ["site"]  # The runner sent one site stop.

    def _request(self, output: str) -> StartRequest:
        """Build a checked utility request.

        Args:
            output: The utility output kind.

        Returns:
            A utility start request.
        """
        target = FieldSpec("device_id", "Device", FieldKind.UUID, picker="devices")  # Build a device target.
        definition = UtilityDefinition(
            "ex.remotePcap", "ex", "remotePcap", "Capture", "Capture packets.", (), Safety.CAPTURE, output, (target,)
        )  # Build a capture utility.
        return StartRequest(
            "utility",
            definition,
            {"site_id": ("site-a",), "device_id": ("dev-a",)},
            {"port_ids": ["ge-0/0/1"]},
            "Capture",
        )  # Return a checked request.

    def _org_request(self) -> StartRequest:
        """Build a checked organization capture request.

        Returns:
            A utility start request.
        """
        target = FieldSpec("mxedge_id", "Mist Edge", FieldKind.UUID, picker="mxedges")  # Build a Mist Edge target.
        definition = UtilityDefinition(
            "mxedge.orgRemotePcap",
            "mxedge",
            "orgRemotePcap",
            "Capture",
            "Capture packets.",
            (),
            Safety.CAPTURE,
            "packets",
            (target,),
            "organization",
        )  # Build an organization capture utility.
        return StartRequest(
            "utility",
            definition,
            {"org_id": ("org-a",), "mxedge_id": ("mx-a",)},
            {"interfaces": ["port0"]},
            "Capture",
        )  # Return a checked request.

    def _enum_function(self, node: SampleEnum) -> None:
        """Provide an enum annotation for conversion tests.

        Args:
            node: The enum value.
        """
        return None  # The function is never called.


class SampleEnum(Enum):
    """A small enum for conversion tests."""

    NODE0 = "node0"  # The runner converts this value from text.

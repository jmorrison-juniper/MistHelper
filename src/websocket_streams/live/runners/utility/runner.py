"""Run Mist device utilities through the owned stream client.

Why:
    Issue #3671 replaces the broken Mist SDK WebSocket order. The runner now
    subscribes before it sends the REST trigger, so fast device output is not
    lost.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # The runner logs safe state changes and counts.
import threading  # Utility monitoring must not block a web request.
import time  # The runner uses monotonic time for limits.
from collections.abc import Mapping  # REST answers and packet records are mappings.
from dataclasses import dataclass, field  # Runtime state stays in one object.
from typing import Protocol, runtime_checkable  # The public constructor still accepts object.

from src.websocket_streams.catalog.model import UtilityDefinition  # Utility runners need utility-only fields.
from src.websocket_streams.intake.fields import StreamRequestError  # Non-shell input raises this contract error.
from src.websocket_streams.intake.start_request import StartRequest  # The request is already checked.
from src.websocket_streams.live.runners.text import PacketSummary  # Packet output needs one summary line.
from src.websocket_streams.live.runners.utility.filters import (
    UtilityMessageFilter,
)  # Filters session or capture events.
from src.websocket_streams.live.runners.utility.triggers import (
    UtilityRequest,
    UtilityTiming,
    UtilityTriggerTable,
)  # Trigger table owns SDK parity data.
from src.websocket_streams.live.sessions.record import (
    SessionSink,
    SessionState,
)  # The runner writes through this protocol.
from src.websocket_streams.live.transport.endpoint import MistStreamEndpoint  # The stream client needs endpoint values.
from src.websocket_streams.live.transport.frames import ConnectionClosed, FrameDecoder, SubscribeError  # Stream errors.
from src.websocket_streams.live.transport.stream_client import StreamClient  # Owned WebSocket stream client.

logger = logging.getLogger(__name__)  # Keep utility runner records under this module.


@runtime_checkable
class _ApiSessionProtocol(Protocol):
    """The REST methods that a utility trigger needs."""

    def mist_post(self, uri: str, body: object | None = None) -> object:
        """Send a POST request.

        Args:
            uri: The API path.
            body: The JSON-safe body.

        Returns:
            The API response object.
        """
        ...  # Protocol method has no implementation.

    def mist_get(self, uri: str) -> object:
        """Send a GET request.

        Args:
            uri: The API path.

        Returns:
            The API response object.
        """
        ...  # Protocol method has no implementation.

    def mist_delete(self, uri: str) -> object:
        """Send a DELETE request.

        Args:
            uri: The API path.

        Returns:
            The API response object.
        """
        ...  # Protocol method has no implementation.


@dataclass(slots=True)
class _RunnerState:
    """Mutable runtime state for one utility run."""

    stopping: threading.Event = field(default_factory=threading.Event)  # stop() and the run loop share this event.
    live_marked: bool = False  # The session goes live one time.
    output_count: int = 0  # End-state logic distinguishes timeout from finished.
    client: StreamClient | None = None  # stop() closes the live stream client.
    trigger: UtilityRequest | None = None  # Capture stop reads trigger metadata.
    answer: Mapping[str, object] | None = None  # Capture stop reads the trigger answer.
    lock: threading.Lock = field(default_factory=threading.Lock)  # Protect client and answer references.


class UtilityRunner:
    """Run one utility trigger and stream its output."""

    def __init__(
        self,
        apisession: object,
        endpoint: MistStreamEndpoint,
        request: StartRequest,
        sink: SessionSink,
        triggers: UtilityTriggerTable | None = None,
    ) -> None:
        """Build one utility runner.

        Args:
            apisession: The Mist API session.
            endpoint: The stream endpoint configuration.
            request: The checked utility request.
            sink: The session sink that receives output.
            triggers: Optional trigger table for tests.
        """
        self._apisession = self._api_session(apisession)  # REST triggers run through this API session.
        self._endpoint = endpoint  # StreamClient reads auth and timeouts here.
        self._request = request  # The checked request names the utility.
        self._sink = sink  # The runner reports output through this sink.
        self._triggers = triggers or UtilityTriggerTable()  # Tests can inject short timings.
        self._state = _RunnerState()  # Keep mutable runtime state in one object.

    def start(self) -> None:
        """Start the utility and return at once."""
        logger.info("Starting WebSockets utility runner for key %s", self._request.key)  # Log before thread start.
        thread = threading.Thread(
            target=self._run, name=f"ws-util-{self._request.key}", daemon=True
        )  # A daemon thread cannot block shutdown.
        thread.start()  # The web request returns after the thread starts.
        logger.debug("Started WebSockets utility runner thread for key %s", self._request.key)  # Log safe metadata.

    def stop(self) -> None:
        """Ask the utility to stop and return at once."""
        logger.info("Stopping WebSockets utility runner for key %s", self._request.key)  # Log before close.
        self._state.stopping.set()  # The run loop maps completion to stopped.
        with self._state.lock:  # Copy the client reference safely.
            client = self._state.client  # The runner can still be opening.
        if client is not None:  # stop() before open is harmless.
            client.close()  # Close wakes any blocked stream read.
        logger.debug("Stop requested for WebSockets utility runner key %s", self._request.key)  # Log after close.

    def _run(self) -> None:
        """Open the stream, send the trigger, and read filtered output."""
        started = time.monotonic()  # Timing limits use the same monotonic source.
        try:  # The runner must report thread failures as session failures.
            trigger = self._prepare_trigger()  # Build the SDK-parity REST trigger.
            client = self._open_stream(trigger)  # Subscribe before the REST trigger.
            if self._state.stopping.is_set():  # A stop between subscribe and trigger must prevent side effects.
                self._finish_stopped()  # Finish without sending the REST trigger.
                return  # The utility never starts after an operator stop.
            filterer = UtilityMessageFilter(trigger.listen.channel)  # Match only this trigger output.
            answer = self._send_trigger(trigger)  # Send REST trigger after subscription.
            self._bind_filter(filterer, answer)  # Bind with the session or capture identifier.
            self._read_until_done(client, trigger.listen.timing, filterer, started)  # Apply the stream limits.
            self._finish(started)  # Map the collected output to a final state.
        except SubscribeError as exc:
            self._fail(f"The stream subscription failed: {exc.detail}.")  # Do not leak the channel path.
        except ConnectionClosed as exc:
            if self._state.stopping.is_set() and not exc.dropped:  # A local close during open is an operator stop.
                self._finish_stopped()  # Map the interrupted open to stopped.
            else:
                self._fail(str(exc) or "The utility failed.")  # Return a safe failure reason.
        except (StreamRequestError, RuntimeError, OSError) as exc:
            self._fail(str(exc) or "The utility failed.")  # Return a safe failure reason.
        except Exception:
            logger.exception("WebSockets utility runner crashed for key %s", self._request.key)  # Log traceback.
            self._sink.finish(
                SessionState.FAILED, "The utility failed. Read the portal log for the cause."
            )  # Keep page reason safe.
        finally:
            self._close_client()  # Ensure stop() has no stale client reference.

    @staticmethod
    def _api_session(apisession: object) -> _ApiSessionProtocol:
        """Return an API session with the REST methods that utilities use.

        Args:
            apisession: The untyped API session from the manager.

        Returns:
            The API session narrowed to the REST trigger protocol.
        """
        if not isinstance(apisession, _ApiSessionProtocol):  # The runner needs three REST methods.
            raise RuntimeError("The API session cannot send utility trigger requests.")  # Fail before stream opens.
        return apisession  # The caller can now use typed REST methods.

    def _prepare_trigger(self) -> UtilityRequest:
        """Build the trigger table request.

        Returns:
            The SDK-parity utility request.
        """
        logger.info("Building WebSockets utility trigger for key %s", self._request.key)  # Log before lookup.
        trigger = self._triggers.request_for(self._request)  # The table owns method, path, body, and listen data.
        if trigger.listen.channel == "url":  # Screen commands belong to ScreenRunner.
            raise StreamRequestError("bad_request", "This utility must run through the screen runner.")  # Refuse here.
        with self._state.lock:  # Publish trigger metadata for stop().
            self._state.trigger = trigger  # Capture stop uses trigger scope.
        logger.debug("Built WebSockets utility trigger for key %s", self._request.key)  # Log after lookup.
        return trigger  # The runner can open the stream.

    def _open_stream(self, trigger: UtilityRequest) -> StreamClient:
        """Open and subscribe the stream client.

        Args:
            trigger: The utility trigger request.

        Returns:
            The open stream client.
        """
        logger.info("Opening utility stream before trigger for key %s", trigger.key)  # Log before network open.
        client = StreamClient(self._endpoint, [trigger.listen.channel_path])  # Subscribe to one utility channel.
        with self._state.lock:  # Publish the client so stop() can close it.
            self._state.client = client  # stop() can now wake open or read.
        client.open()  # Return only after channel_subscribed.
        logger.debug("Opened utility stream before trigger for key %s", trigger.key)  # Log after subscribe.
        return client  # The caller can send the REST trigger.

    def _send_trigger(self, trigger: UtilityRequest) -> Mapping[str, object]:
        """Send the utility REST trigger.

        Args:
            trigger: The REST trigger request.

        Returns:
            The trigger answer data.
        """
        logger.info("Sending WebSockets utility trigger for key %s", trigger.key)  # Log before REST call.
        response = self._send_rest(trigger)  # Dispatch to the API session method.
        status = int(getattr(response, "status_code", 0))  # The fake and SDK responses expose this field.
        data = getattr(response, "data", {})  # The trigger answer holds session or capture id.
        if status != 200 or not isinstance(data, Mapping):  # A refused trigger cannot safely filter output.
            raise RuntimeError(f"The utility failed with status {status}.")  # Keep the reason safe.
        with self._state.lock:  # Publish the trigger answer for capture stop.
            self._state.answer = data  # Stop reads the capture id from this mapping.
        self._mark_live_once()  # A successful trigger means the utility is running.
        logger.debug("Sent WebSockets utility trigger for key %s with status %s", trigger.key, status)  # Safe metadata.
        return data  # The filter binds to this answer.

    def _send_rest(self, trigger: UtilityRequest) -> object:
        """Dispatch one REST request to the fake or SDK API session.

        Args:
            trigger: The REST trigger request.

        Returns:
            The API response object.
        """
        if trigger.method == "POST":  # Utility triggers are POST today.
            return self._apisession.mist_post(trigger.path, trigger.body)  # Send the SDK-parity body.
        if trigger.method == "GET":  # Keep the interface future-safe.
            return self._apisession.mist_get(trigger.path)  # GET has no body.
        return self._apisession.mist_delete(trigger.path)  # DELETE has no body.

    def _bind_filter(self, filterer: UtilityMessageFilter, answer: Mapping[str, object]) -> None:
        """Bind the filter and emit held matches.

        Args:
            filterer: The utility message filter.
            answer: The REST trigger answer.
        """
        logger.info("Binding WebSockets utility output filter for key %s", self._request.key)  # Log before bind.
        held = filterer.bind(answer)  # Held output can arrive before the trigger answer.
        for payload in held:  # Emit any held matching payload.
            self._emit(payload)  # Keep message kinds and summaries stable.
        logger.debug("Bound WebSockets utility output filter with %s held outputs", len(held))  # Log count only.

    def _read_until_done(
        self, client: StreamClient, timing: UtilityTiming, filterer: UtilityMessageFilter, started: float
    ) -> None:
        """Read stream events until a limit or stop occurs.

        Args:
            client: The open stream client.
            timing: The utility timing limits.
            filterer: The bound utility filter.
            started: The monotonic start time.
        """
        last_output = started  # Quiet time starts at trigger start until output arrives.
        first_deadline = started + timing.first_output_seconds  # Bound the first output wait.
        total_deadline = started + timing.total_seconds  # Bound the whole utility.
        while not self._done(first_deadline, total_deadline, last_output, timing):  # Stop on any limit.
            event = self._next_event(client)  # Short reads let stop() finish quickly.
            if event is None:  # A quiet interval is not a failure.
                continue  # Recheck limits before the next read.
            last_output = self._handle_event(event, filterer, last_output)  # Filter and emit matching output.

    def _next_event(self, client: StreamClient) -> Mapping[str, object] | None:
        """Read one event or treat a local stop close as no event.

        Args:
            client: The open stream client.

        Returns:
            A decoded event, or None after a stop close.
        """
        try:  # stop() closes the client from another thread.
            return client.next_event(0.05)  # Keep the read slice short for stop and fast quiet completion.
        except ConnectionClosed:  # A local close is the normal stop path.
            if self._state.stopping.is_set():  # stop() already chose the final state.
                return None  # Let the loop see the stop event.
            raise  # A remote close before stop remains a failure.

    def _done(self, first_deadline: float, total_deadline: float, last_output: float, timing: UtilityTiming) -> bool:
        """Return whether a run limit has ended the stream.

        Args:
            first_deadline: The first output deadline.
            total_deadline: The total run deadline.
            last_output: The time of the last output.
            timing: The utility timing limits.

        Returns:
            True when the run should stop.
        """
        now = time.monotonic()  # Read the clock once for consistent checks.
        if self._state.stopping.is_set():  # Operator stop ends the loop.
            return True  # The caller will map the final state.
        if now >= total_deadline:  # The total limit ended the loop.
            return True  # The caller will map the final state.
        if self._state.output_count == 0 and now >= first_deadline:  # No first output arrived in time.
            return True  # The final state becomes timed out.
        return self._state.output_count > 0 and now - last_output >= timing.quiet_seconds  # Quiet after output ends.

    def _handle_event(self, event: Mapping[str, object], filterer: UtilityMessageFilter, last_output: float) -> float:
        """Filter one stream event and emit matching output.

        Args:
            event: The decoded stream event.
            filterer: The bound utility filter.
            last_output: The prior output time.

        Returns:
            The updated last output time.
        """
        payload = FrameDecoder.data_payload(event)  # Decode nested JSON data before filtering.
        matches = filterer.offer(payload)  # Drop output for other sessions or captures.
        for match in matches:  # Most events hold one match.
            self._emit(match)  # Store the output in the session sink.
        return time.monotonic() if matches else last_output  # Only matching output resets quiet time.

    def _emit(self, payload: object) -> None:
        """Emit one filtered payload to the session sink.

        Args:
            payload: The filtered command text or capture payload.
        """
        self._state.output_count += 1  # Count output for the end-state decision.
        definition = self._utility_definition()  # Utility-only fields need narrowing.
        self._mark_live_once()  # Output also proves the device runs the utility.
        if definition.output == "packets":  # Packet captures use packet records.
            packet = self._packet_payload(payload)  # Keep the old packet content shape.
            self._sink.add_message("packet", packet, summary=PacketSummary.summarize(packet))  # Store packet summary.
        else:  # Line utilities append output.
            self._sink.add_message("text", str(payload))  # Store one line of text.

    def _packet_payload(self, payload: object) -> object:
        """Return the packet dictionary from a capture payload.

        Args:
            payload: The filtered capture payload.

        Returns:
            The packet dictionary, or the original payload.
        """
        if isinstance(payload, Mapping) and "pcap_dict" in payload:  # Filter returns the full capture payload.
            return payload["pcap_dict"]  # The existing page expects packet content only.
        return payload  # Malformed payloads stay visible for diagnostics.

    def _finish(self, started: float) -> None:
        """Map the run result to a session end state.

        Args:
            started: The monotonic start time.
        """
        if self._state.stopping.is_set():  # Operator or reaper stopped the utility.
            self._sink.finish(SessionState.STOPPED, "The operator stopped the session.")  # Stop wins.
        elif self._state.output_count == 0:  # The stream finished without output.
            self._sink.finish(
                SessionState.TIMED_OUT,
                "The device sent no output before the time limit. Check that the device is connected, then try again.",
            )  # Tell the operator what to check.
        else:  # Output arrived and no failure was recorded.
            self._sink.finish(SessionState.FINISHED, self._finish_reason(started))  # Report successful completion.

    def _finish_stopped(self) -> None:
        """Finish the utility after an operator stop."""
        logger.info("Finishing stopped WebSockets utility runner for key %s", self._request.key)  # Log before finish.
        self._sink.finish(SessionState.STOPPED, "The operator stopped the session.")  # Stop wins over start.
        logger.debug("Finished stopped WebSockets utility runner for key %s", self._request.key)  # Log after finish.

    def _finish_reason(self, started: float) -> str:
        """Return the plain completion reason.

        Args:
            started: The monotonic start time.

        Returns:
            The completion reason.
        """
        elapsed = time.monotonic() - started  # Compare actual run time to the trigger total.
        if self._state.trigger is not None and elapsed >= self._state.trigger.listen.timing.total_seconds:  # Total.
            return "The SDK 60 second limit ended the session."  # Keep the existing reason text.
        return "The utility finished."  # Normal completion needs no extra detail.

    def _fail(self, reason: str) -> None:
        """Finish the session as failed.

        Args:
            reason: The safe failure reason.
        """
        logger.warning(
            "WebSockets utility runner failed for key %s: %s", self._request.key, reason
        )  # Expected failure.
        self._sink.finish(SessionState.FAILED, reason)  # The page shows the plain reason.

    def _close_client(self) -> None:
        """Close and clear the stream client."""
        with self._state.lock:  # Copy and clear the shared client reference.
            client = self._state.client  # The client can be None after early failure.
            self._state.client = None  # Future stop calls become harmless.
        if client is not None:  # A failed open can leave no client.
            client.close()  # Ensure the socket is closed.
        self._stop_capture_if_needed()  # A stopped capture can need a REST stop.

    def _mark_live_once(self) -> None:
        """Mark the session live one time."""
        if self._state.live_marked:  # A later call changes nothing.
            return  # The session is already live.
        self._state.live_marked = True  # Set the flag before calling the sink.
        self._sink.mark_live()  # The record changes the state only from connecting.

    def _utility_definition(self) -> UtilityDefinition:
        """Return the checked utility definition.

        Returns:
            The utility definition.

        Raises:
            StreamRequestError: The request does not hold a utility definition.
        """
        definition = self._request.definition  # Store the union before narrowing.
        if not isinstance(definition, UtilityDefinition):  # Utility runners require utility definitions.
            raise StreamRequestError("bad_request", "The utility definition is not valid.")  # Fail safely.
        return definition  # The caller can read utility-only fields.

    def _stop_capture_if_needed(self) -> None:
        """Stop a matching packet capture after a stop request."""
        trigger = self._state.trigger  # Store the trigger for local checks.
        if not self._state.stopping.is_set() or trigger is None:  # Only operator stops need capture cleanup.
            return  # Natural capture end does not send a stop request.
        answer = self._state.answer or {}  # A refused trigger has no capture id.
        capture_id = answer.get("id") if trigger.listen.channel != "cmd" else None  # Captures answer with id.
        if not isinstance(capture_id, str):  # No capture id means no safe stop call.
            return  # The runner must not stop another capture.
        stopper = CaptureStopper(self._apisession)  # Reuse the already-checked API session.
        if trigger.listen.channel == "org_pcaps":  # Organization captures use org stop.
            stopper.stop_org(self._request.target("org_id"), capture_id)  # Stop only a matching organization capture.
        else:  # Site captures use site stop.
            stopper.stop_site(self._request.target("site_id"), capture_id)  # Stop only a matching site capture.


class CaptureStopper:
    """Stop a packet capture only when it matches this session."""

    def __init__(self, apisession: _ApiSessionProtocol) -> None:
        """Build one capture stopper.

        Args:
            apisession: The Mist API session.
        """
        self._apisession = apisession  # REST stop calls use the checked API session.

    def stop_site(self, site_id: str, capture_id: str) -> bool:
        """Stop a site capture when the active capture identifier matches.

        Args:
            site_id: The site identifier.
            capture_id: The capture identifier of this session.

        Returns:
            True when a stop request was sent.
        """
        logger.info("Checking site packet capture before stop")  # Log before the API read.
        response = self._apisession.mist_get(f"/api/v1/sites/{site_id}/pcaps?limit=1")  # Read active capture state.
        match = self._has_capture(response, capture_id)  # Compare the active capture identifier.
        logger.debug("Checked site packet capture match=%s", match)  # Log safe metadata only.
        if not match:  # A stop call ends all captures at the site.
            return False  # Do not stop a capture of another session.
        self._apisession.mist_delete(f"/api/v1/sites/{site_id}/pcaps")  # Stop the matching capture.
        return True  # The caller can report that it sent a stop.

    def stop_org(self, org_id: str, capture_id: str) -> bool:
        """Stop an organization capture when the identifier matches.

        Args:
            org_id: The organization identifier.
            capture_id: The capture identifier of this session.

        Returns:
            True when a stop request was sent.
        """
        logger.info("Checking organization packet capture before stop")  # Log before the API read.
        response = self._apisession.mist_get(f"/api/v1/orgs/{org_id}/pcaps?limit=1")  # Read active capture state.
        match = self._has_capture(response, capture_id)  # Compare the active capture identifier.
        logger.debug("Checked organization packet capture match=%s", match)  # Log safe metadata only.
        if not match:  # A stop call can affect another operator.
            return False  # Do not stop a capture of another session.
        self._apisession.mist_delete(f"/api/v1/orgs/{org_id}/pcaps")  # Stop the matching capture.
        return True  # The caller can report that it sent a stop.

    def _has_capture(self, response: object, capture_id: str) -> bool:
        """Return whether an API response names the capture identifier.

        Args:
            response: The untyped API response.
            capture_id: The expected capture identifier.

        Returns:
            True when the response holds the identifier.
        """
        data = getattr(response, "data", None)  # The API response stores records here.
        if isinstance(data, list):  # List responses hold capture rows directly.
            rows = data  # Use the direct response rows.
        elif isinstance(data, Mapping):  # Paginated responses hold rows under results.
            rows = data.get("results", [])  # Use the paginated response rows.
        else:  # Any other shape cannot name an active capture.
            rows = []  # Keep the comparison safe.
        return any(isinstance(row, Mapping) and row.get("id") == capture_id for row in rows)  # Match this capture.

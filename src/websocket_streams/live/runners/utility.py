"""Run Mist device utilities that stream output.

Why:
    Issue #3551. Device utilities trigger a REST request and then receive
    output on a WebSocket. The web request must return at once, while a
    background thread maps the SDK result to the session state.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import importlib  # The runner loads the SDK family module by name.
import logging  # The runner logs starts, stops, and end states.
import threading  # Utility monitoring must not block a web request.
import time  # The default clock and sleeper come from the standard library.
from collections.abc import Callable, Mapping  # Tests inject fake functions.
from typing import Any  # The SDK is untyped at the call boundary.

from mistapi.api.v1.orgs import pcaps as org_pcaps  # The stopper reads and stops organization captures.
from mistapi.api.v1.sites import pcaps as site_pcaps  # The stopper reads and stops site captures.

from src.websocket_streams.catalog.model import UtilityDefinition  # Utility runners need utility-only fields.
from src.websocket_streams.catalog.sdk_annotation import SdkAnnotation  # The SDK signature names each enum.
from src.websocket_streams.intake.fields import StreamRequestError  # Non-shell input raises this contract error.
from src.websocket_streams.intake.start_request import StartRequest  # The request is already checked.
from src.websocket_streams.live.runners.text import PacketSummary  # Packet output needs one summary line.
from src.websocket_streams.live.sessions.record import (
    SessionSink,
    SessionState,
)  # The runner writes through this protocol.

logger = logging.getLogger(__name__)  # Keep utility runner records under this module.


class UtilityRunner:
    """Run one SDK utility function in the background."""

    def __init__(
        self,
        apisession: object,
        request: StartRequest,
        sink: SessionSink,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        """Build one utility runner.

        Args:
            apisession: The Mist API session.
            request: The checked utility request.
            sink: The session sink that receives output.
            clock: The monotonic clock.
            sleeper: The sleep function used by the monitor loop.
        """
        self._apisession = apisession  # The SDK uses this object for authentication.
        self._request = request  # The checked request names the SDK function.
        self._sink = sink  # The runner reports output through this sink.
        self._clock = clock  # Tests inject a fake clock.
        self._sleeper = sleeper  # Tests inject a no-op sleeper.
        self._response: Any | None = None  # The SDK UtilResponse is untyped.
        self._stopping = threading.Event()  # Stop requests map the final state.
        self._output_count = 0  # End-state logic distinguishes timeout from finished.
        self._live_marked = False  # The session goes live one time, on an accepted trigger or on the first output.

    def start(self) -> None:
        """Start the SDK utility and return at once."""
        logger.info("Starting WebSockets utility runner for key %s", self._request.key)  # Log before the thread starts.
        thread = threading.Thread(
            target=self._run, name=f"ws-util-{self._request.key}", daemon=True
        )  # A daemon thread cannot block shutdown.
        thread.start()  # The web request returns after the thread starts.
        logger.debug(
            "Started WebSockets utility runner thread for key %s", self._request.key
        )  # Log safe metadata only.

    def stop(self) -> None:
        """Ask the SDK utility to stop and return at once."""
        logger.info(
            "Stopping WebSockets utility runner for key %s", self._request.key
        )  # Log before the stop thread starts.
        self._stopping.set()  # The monitor maps completion to stopped.
        thread = threading.Thread(
            target=self._disconnect_until_done, name=f"ws-util-stop-{self._request.key}", daemon=True
        )  # Repeat disconnect off the request thread.
        thread.start()  # The web request returns at once.
        logger.debug(
            "Stop requested for WebSockets utility runner key %s", self._request.key
        )  # Log safe metadata only.

    def send_input(self, text: str) -> None:
        """Reject shell input for a utility runner.

        Args:
            text: The ignored text.

        Raises:
            StreamRequestError: Always, because utility streams are not shells.
        """
        raise StreamRequestError(
            "not_open", "This session does not accept shell input."
        )  # Only shell runners accept input.

    def _run(self) -> None:
        """Call the SDK function and monitor its UtilResponse."""
        started = self._clock()  # Duration notes use the same clock as tests.
        try:  # SDK calls can fail before a response exists.
            logger.info("Calling SDK utility for key %s", self._request.key)  # Log before the SDK call.
            self._response = self._call_sdk()  # The SDK returns a UtilResponse at once.
            logger.debug("SDK utility call returned for key %s", self._request.key)  # Log after the SDK call.
            self._wait_for_done()  # Monitor completion in this background thread.
            self._finish_from_response(started)  # Map SDK state to session state.
        except Exception as exc:  # Broad catch protects the portal worker.
            logger.exception(
                "WebSockets utility runner failed for key %s", self._request.key
            )  # Log traceback without secrets.
            self._sink.finish(SessionState.FAILED, str(exc) or "The utility failed.")  # Report a plain failure.

    def _call_sdk(self) -> Any:
        """Call the SDK utility function.

        Returns:
            The SDK UtilResponse object.
        """
        definition = self._utility_definition()  # The checked definition names the SDK function.
        module = importlib.import_module(f"mistapi.device_utils.{definition.family}")  # Load the SDK family module.
        function = getattr(module, definition.function_name)  # Get the checked facade function.
        kwargs = self._sdk_arguments(function)  # Build checked SDK arguments.
        return function(**kwargs)  # The SDK starts its own WebSocket work.

    def _sdk_arguments(self, function: Callable[..., Any]) -> dict[str, object]:
        """Build SDK keyword arguments from the checked request.

        Args:
            function: The SDK facade function.

        Returns:
            Keyword arguments for the SDK function.
        """
        params = {
            key: self._enum_value(function, key, value) for key, value in self._request.parameters.items()
        }  # Convert enum parameters.
        params.update(self._target_arguments())  # Add targets after parameters.
        params["apisession"] = self._apisession  # The SDK needs the Mist session.
        params["on_message"] = self._on_message  # The SDK calls this for stream output.
        if self._request.key.endswith("remotePcap") or "Pcap" in self._request.key:  # Captures must last 60 seconds.
            params["duration"] = 60  # The SDK and Mist overlap at this value only.
            params.update(self._capture_arguments())  # Add device_interfaces for cabled captures.
        return params  # The SDK function receives only checked values.

    def _target_arguments(self) -> dict[str, object]:
        """Return target arguments for the SDK function.

        Returns:
            A dictionary of SDK target arguments.
        """
        definition = self._utility_definition()  # Utility-only fields need narrowing.
        if (
            self._request.target("org_id") and definition.scope == "organization"
        ):  # Organization Mist Edge capture uses org_id.
            return {"org_id": self._request.target("org_id")}  # The portal setting supplied this value.
        targets: dict[str, object] = {"site_id": self._request.target("site_id")}  # Most utilities are site scoped.
        device_id = self._request.target("device_id") or self._request.target("mxedge_id")  # Mist Edge uses mxedge_id.
        if device_id and definition.family != "mxedge":  # Non-Mist Edge SDK calls use device_id.
            targets["device_id"] = device_id  # Add the checked device identifier.
        return targets  # The SDK accepts these target names.

    def _capture_arguments(self) -> dict[str, object]:
        """Return capture-only arguments.

        Returns:
            A dictionary with ``device_interfaces`` when the SDK needs it.
        """
        device_id = self._request.target("device_id") or self._request.target(
            "mxedge_id"
        )  # Captures name a device or a Mist Edge.
        ports = self._request.parameters.get("port_ids") or self._request.parameters.get(
            "interfaces"
        )  # The field depends on family.
        if not device_id or not isinstance(ports, list):  # AP captures do not use device_interfaces.
            return {}  # The SDK function accepts no device_interfaces here.
        interfaces = {str(port): None for port in ports}  # The SDK form maps each interface to an optional filter.
        return {"device_interfaces": {device_id: interfaces}}  # The SDK docstring requires this nested form.

    def _enum_value(self, function: Callable[..., Any], key: str, value: object) -> object:
        """Convert one parameter to an SDK enum when needed.

        Args:
            function: The SDK function.
            key: The parameter name.
            value: The checked JSON-safe value.

        Returns:
            The original value, or an SDK enum member.
        """
        hints = SdkAnnotation.hints(function)  # Read real SDK annotations for enum parameters.
        annotation = hints.get(key)  # Missing hints mean no conversion is needed.
        enum_type = SdkAnnotation.enum_type(annotation)  # Optional enum annotations need unwrapping.
        if enum_type is not None and isinstance(value, str):  # JSON-safe requests hold enum values as text.
            return enum_type(value)  # The SDK functions expect enum members.
        return value  # Non-enum values pass through unchanged.

    def _on_message(self, message: object) -> None:
        """Handle one SDK utility message.

        Args:
            message: The raw SDK message.
        """
        self._output_count += 1  # Count output for the end-state decision.
        self._mark_live_once()  # Output proves that the device runs the utility.
        definition = self._utility_definition()  # Utility-only fields need narrowing.
        if definition.output == "packets":  # Packet captures use packet records.
            self._sink.add_message(
                "packet", message, summary=PacketSummary.summarize(message)
            )  # Store packet content and summary.
        elif definition.output == "screen":  # Screen utilities replace the view.
            self._sink.add_message("screen", str(message))  # Store the newest screen text.
        else:  # Line utilities append output.
            self._sink.add_message("text", str(message))  # Store one line of text.

    def _wait_for_done(self) -> None:
        """Wait until the SDK reports completion, and mark the session live when the trigger succeeds."""
        while self._response is not None and not bool(
            getattr(self._response, "done", True)
        ):  # Poll the untyped SDK response.
            self._mark_live_when_accepted()  # The SDK sets the trigger result on its own thread.
            self._sleeper(0.05)  # Sleep briefly on the background thread.

    def _utility_definition(self) -> UtilityDefinition:
        """Return the checked utility definition.

        Returns:
            The utility definition.
        """
        definition = self._request.definition  # Store the union before narrowing.
        if not isinstance(definition, UtilityDefinition):  # Utility runners require utility definitions.
            raise StreamRequestError(
                "bad_request", "The utility definition is not valid."
            )  # Fail safely if callers break the contract.
        return definition  # The caller can read utility-only fields.

    def _finish_from_response(self, started: float) -> None:
        """Map the SDK response to the session end state.

        Args:
            started: The monotonic start time.
        """
        status = self._trigger_status()  # The REST trigger result decides a refused start.
        error = getattr(self._response, "ws_error", None)  # The SDK stores WebSocket errors here.
        if self._stopping.is_set():  # Operator or reaper stopped the utility.
            self._sink.finish(
                SessionState.STOPPED, "The operator stopped the session."
            )  # Stop beats other clean outcomes.
        elif status != 200 or error:  # The trigger or WebSocket failed.
            self._sink.finish(
                SessionState.FAILED, f"The utility failed with status {status}."
            )  # Keep the reason plain.
        elif self._output_count == 0:  # The SDK finished without output.
            self._sink.finish(
                SessionState.TIMED_OUT,
                "The device sent no output before the time limit. Check that the device is connected, then try again.",
            )  # Tell the operator what to check.
        else:  # Output arrived and no failure was recorded.
            self._sink.finish(SessionState.FINISHED, self._finish_reason(started))  # Report successful completion.

    def _trigger_status(self) -> object:
        """Return the HTTP status of the SDK trigger request.

        Returns:
            The status code, or 200 when the SDK recorded no trigger response.
        """
        trigger = getattr(self._response, "trigger_api_response", None)  # The SDK stores the REST result here.
        return getattr(trigger, "status_code", 200) if trigger is not None else 200  # No trigger means no failure.

    def _mark_live_when_accepted(self) -> None:
        """Mark the session live after the Mist API accepts the trigger request."""
        trigger = getattr(self._response, "trigger_api_response", None)  # The SDK sets this value on its own thread.
        if trigger is not None and getattr(trigger, "status_code", None) == 200:  # The device now runs the utility.
            self._mark_live_once()  # The page shows Live while the device sends output.

    def _mark_live_once(self) -> None:
        """Mark the session live one time, because the record logs each state change."""
        if self._live_marked:  # A later call changes nothing.
            return  # The session is already live.
        self._live_marked = True  # Set the flag first, so that the other thread does not repeat the call.
        self._sink.mark_live()  # The record changes the state only from connecting.

    def _finish_reason(self, started: float) -> str:
        """Return the plain completion reason.

        Args:
            started: The monotonic start time.

        Returns:
            The completion reason.
        """
        elapsed = self._clock() - started  # The SDK maximum duration is 60 seconds.
        if elapsed >= 59.0:  # The SDK can close at the 60-second limit.
            return "The SDK 60 second limit ended the session."  # Tell the operator why it ended.
        return "The utility finished."  # Normal completion needs no extra detail.

    def _disconnect_until_done(self) -> None:
        """Repeat disconnect until the SDK response reports done."""
        for _attempt in range(20):  # Bound the stop thread.
            response = self._response  # Copy the untyped response reference.
            if response is None or bool(getattr(response, "done", True)):  # Nothing remains to disconnect.
                break  # A capture can still need a REST stop.
            disconnect = getattr(response, "disconnect", None)  # The SDK response exposes this method.
            if callable(disconnect):  # A fake can omit the method.
                disconnect()  # SDK disconnect is safe to repeat.
            self._sleeper(0.05)  # Give the SDK time to mark done.
        self._stop_capture_if_needed()  # A packet capture may need a REST stop after disconnect.

    def _stop_capture_if_needed(self) -> None:
        """Stop a matching packet capture after a stop request."""
        if "Pcap" not in self._request.key:  # Only packet captures need a capture stop.
            return  # Other utilities only need disconnect.
        response = self._response  # Copy the untyped response reference.
        trigger = (
            getattr(response, "trigger_api_response", None) if response is not None else None
        )  # Read trigger data.
        data = getattr(trigger, "data", None) if trigger is not None else None  # The SDK stores capture id here.
        capture_id = data.get("id") if isinstance(data, Mapping) else None  # Capture ids are dictionary values.
        if not isinstance(capture_id, str):  # No capture id means no safe stop call.
            return  # The runner must not stop another capture.
        stopper = CaptureStopper(self._apisession)  # Build a scoped capture stopper.
        definition = self._utility_definition()  # Utility-only fields need narrowing.
        if definition.scope == "organization":  # Organization captures use org stop.
            stopper.stop_org(self._request.target("org_id"), capture_id)  # Stop only a matching organization capture.
        else:  # Site captures use site stop.
            stopper.stop_site(self._request.target("site_id"), capture_id)  # Stop only a matching site capture.


class CaptureStopper:
    """Stop a packet capture only when it matches this session."""

    def __init__(self, apisession: object) -> None:
        """Build one capture stopper.

        Args:
            apisession: The Mist API session.
        """
        self._apisession = apisession  # The SDK stop functions need this session.

    def stop_site(self, site_id: str, capture_id: str) -> bool:
        """Stop a site capture when the active capture identifier matches.

        Args:
            site_id: The site identifier.
            capture_id: The capture identifier of this session.

        Returns:
            True when a stop request was sent.
        """
        logger.info("Checking site packet capture before stop")  # Log before the API read.
        response = site_pcaps.listSitePacketCaptures(
            self._apisession, site_id=site_id, limit=1
        )  # Read active capture state.
        match = self._has_capture(response, capture_id)  # Compare the active capture identifier.
        logger.debug("Checked site packet capture match=%s", match)  # Log safe metadata only.
        if not match:  # A stop call ends all captures at the site.
            return False  # Do not stop a capture of another session.
        site_pcaps.stopSitePacketCapture(self._apisession, site_id=site_id)  # Stop the matching capture.
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
        response = org_pcaps.listOrgPacketCaptures(
            self._apisession, org_id=org_id, limit=1
        )  # Read active capture state.
        match = self._has_capture(response, capture_id)  # Compare the active capture identifier.
        logger.debug("Checked organization packet capture match=%s", match)  # Log safe metadata only.
        if not match:  # A stop call can affect another operator.
            return False  # Do not stop a capture of another session.
        org_pcaps.stopOrgPacketCapture(self._apisession, org_id=org_id)  # Stop the matching capture.
        return True  # The caller can report that it sent a stop.

    def _has_capture(self, response: object, capture_id: str) -> bool:
        """Return whether an API response names the capture identifier.

        Args:
            response: The untyped SDK response.
            capture_id: The expected capture identifier.

        Returns:
            True when the response holds the identifier.
        """
        data = getattr(response, "data", None)  # The SDK response stores records here.
        rows = (
            data if isinstance(data, list) else data.get("results", []) if isinstance(data, Mapping) else []
        )  # Accept both response shapes.
        return any(
            isinstance(row, Mapping) and row.get("id") == capture_id for row in rows
        )  # Match only the capture of this session.

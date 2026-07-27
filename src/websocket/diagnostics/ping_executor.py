"""PingDeviceExecutor: orchestrate ping-over-WebSocket diagnostic workflow."""

from __future__ import annotations  # WHY: forward refs for WebSocketManager and typing.

import logging  # WHY: standard logging for action observability.
from dataclasses import dataclass  # WHY: frozen slotted bundles for wide signatures.
from typing import Any  # WHY: generic typing for the ping-result payload.

from src.websocket.context import WebSocketCmdDeps  # WHY: injected dependency bundle.
from src.websocket.diagnostics.common import (  # WHY: shared executor helpers.
    detect_debug_mode,
    extract_command_session,
    post_device_command,
    prepare_command_credentials,
    print_extra_result_fields,
)
from src.websocket.manager import (  # WHY: WebSocket lifecycle + error utilities.
    WebSocketManager,
    cleanup_ws_connection,
    dump_ws_debug_state,
    log_ws_error,
    select_ws_site,
)

_DEFAULT_PING_TARGET = "8.8.8.8"  # WHY: legacy default destination preserved verbatim.
_DEFAULT_PING_COUNT = 4  # WHY: legacy default packet count preserved verbatim.
_MIN_PING_COUNT = 1  # WHY: inclusive lower bound enforced on user input.
_MAX_PING_COUNT = 100  # WHY: inclusive upper bound enforced on user input.
_WS_RESULT_TIMEOUT = 30  # WHY: seconds to wait for ping output via WebSocket.
_SESSION_PREVIEW_LEN = 8  # WHY: length of session-id preview echoed to operator.
_EXCLUDED_RESULT_KEYS = frozenset({"raw", "Output", "session"})  # WHY: fields printed elsewhere.

_INPUT_CONTEXT = "websocket_ping"  # WHY: safe-input context tag for ping prompts.
_PROMPT_TARGET = "Enter the target hostname or IP address to ping (default: 8.8.8.8): "  # WHY: legacy.
_PROMPT_COUNT = "Enter number of ping packets (default: 4): "  # WHY: legacy prompt text.
_MSG_NO_DEVICE = "! No device selected. Operation cancelled."  # WHY: legacy phrasing preserved.
_MSG_INVALID_COUNT = "! Invalid ping count. Using default: 4"  # WHY: legacy phrasing preserved.
_MSG_RANGE_COUNT = "! Ping count must be between 1 and 100. Using default: 4"  # WHY: legacy phrasing.
_MSG_TIMEOUT = "! Timeout waiting for ping results"  # WHY: legacy timeout phrasing.
_MSG_EMPTY_RESULT = "No output data received"  # WHY: legacy empty-result phrasing.
_HEADER_SEPARATOR = "=" * 60  # WHY: legacy header/footer separator preserved.
_SECTION_UNDERLINE = "-" * 40  # WHY: legacy section underline preserved.


@dataclass(frozen=True, slots=True)
class _PingRequest:  # WHY: frozen bundle keeps _issue_ping_and_render parameter count low.
    """Immutable bundle of inputs required to POST a ping command."""

    deps: WebSocketCmdDeps  # WHY: injected dependency bundle.
    site_id: str  # WHY: Mist site scope for the REST endpoint.
    device_id: str  # WHY: Mist device scope for the REST endpoint.
    target_host: str  # WHY: validated ping target hostname or IP.
    ping_count: int  # WHY: clamped packet count from prompt.
    debug_mode: bool  # WHY: toggles verbose operator output.


@dataclass(frozen=True, slots=True)
class _PostContext:  # WHY: frozen bundle keeps _post_ping_command parameter count low.
    """Immutable bundle wiring the WebSocket manager to a ping request."""

    request: _PingRequest  # WHY: original ping-request inputs.
    websocket_manager: WebSocketManager  # WHY: connected WS to reuse for POST/demux.


class PingDeviceExecutor:  # WHY: orchestrates ping-over-WebSocket diagnostic workflow.
    """Run an interactive ping command on a Mist device via the WebSocket stream."""

    def execute(self, deps: WebSocketCmdDeps) -> None:  # WHY: top-level workflow entry.
        """Top-level entry: prompt user, run ping, render results."""
        logging.info("Starting WebSocket ping operation...")  # WHY: action log at workflow start.
        debug_mode = detect_debug_mode()  # WHY: honor --debug / -d flag once per run.
        self._emit_debug_banner(debug_mode)  # WHY: mirror legacy debug banner + trace lines.
        websocket_manager: WebSocketManager | None = None  # WHY: tracked for finally cleanup.
        try:  # WHY: mirror legacy try/except/finally so cleanup always runs.
            websocket_manager = self._run_workflow(deps, debug_mode)  # WHY: drive workflow.
        except Exception as ping_error:  # noqa: BLE001  # WHY: match legacy resilience broad catch.
            log_ws_error(f"WebSocket ping operation failed: {ping_error}", debug_mode)  # WHY: log.
            logging.debug("EXIT: ping_device_websocket - error")  # WHY: trace marker preserved.
        finally:  # WHY: always release WS resources on any exit path.
            cleanup_ws_connection(websocket_manager, debug_mode)  # WHY: disconnect if connected.
            logging.debug("EXIT: ping_device_websocket")  # WHY: trace marker preserved.

    @staticmethod
    def _emit_debug_banner(debug_mode: bool) -> None:
        """Emit the legacy debug banner + duplicate log + trace marker."""
        if debug_mode:  # WHY: legacy raises root logger level + prints banner.
            logging.getLogger().setLevel(logging.DEBUG)  # WHY: surface DEBUG records.
            print("[DEBUG] DEBUG MODE ENABLED")  # WHY: user-facing banner kept verbatim.
        logging.info("Starting WebSocket ping operation...")  # WHY: legacy duplicate log preserved.
        logging.debug("ENTER: ping_device_websocket")  # WHY: trace marker kept verbatim.

    def _run_workflow(self, deps: WebSocketCmdDeps, debug_mode: bool) -> WebSocketManager | None:
        """Prompt user, dispatch ping, render output. Return WS manager for cleanup."""
        site_id = select_ws_site(deps, debug_mode)  # WHY: interactive site picker.
        if site_id is None:  # WHY: user cancelled site selection.
            return None  # WHY: skip rest of workflow.
        device_id = self._select_device(deps, site_id, debug_mode)  # WHY: interactive device pick.
        if device_id is None:  # WHY: user cancelled or no devices available.
            return None  # WHY: skip rest of workflow.
        target_host = self._prompt_target_host(deps, debug_mode)  # WHY: validated ping target.
        if target_host is None:  # WHY: validation failed. Message already printed.
            return None  # WHY: skip rest of workflow.
        ping_count = self._prompt_ping_count(deps, debug_mode)  # WHY: clamped packet count.
        request = _PingRequest(  # WHY: bundle all inputs into a frozen record.
            deps=deps,
            site_id=site_id,
            device_id=device_id,
            target_host=target_host,
            ping_count=ping_count,
            debug_mode=debug_mode,
        )
        return self._issue_ping_and_render(request)  # WHY: connect, POST, await, render.

    @staticmethod
    def _select_device(deps: WebSocketCmdDeps, site_id: str, debug_mode: bool) -> str | None:
        """Run the device picker and echo the selection under debug mode."""
        device_id = deps.select_device_fn(site_id, device_type="all")  # WHY: device picker.
        if not device_id:  # WHY: user cancelled or no devices available.
            print(_MSG_NO_DEVICE)  # WHY: legacy phrasing preserved.
            return None  # WHY: caller aborts workflow.
        if debug_mode:  # WHY: legacy debug echo of chosen device id.
            print(f"[DEBUG] Selected device_id = {device_id}")  # WHY: legacy phrasing.
        return device_id  # WHY: caller uses the id for downstream calls.

    def _prompt_target_host(self, deps: WebSocketCmdDeps, debug_mode: bool) -> str | None:
        """Ask user for ping target. Return validated host string or None on rejection."""
        target_input = deps.safe_input_fn(  # WHY: EOF-safe input wrapper.
            _PROMPT_TARGET, context=_INPUT_CONTEXT
        ).strip()  # WHY: drop incidental whitespace from prompt response.
        target_host = target_input or _DEFAULT_PING_TARGET  # WHY: apply legacy default.
        logging.debug("Validating ping target host=%s", target_host)  # WHY: log before check.
        if not deps.validate_target_fn(target_host):  # WHY: reject unsafe / malformed hosts.
            print(f"! Invalid ping target: {target_host}")  # WHY: legacy phrasing preserved.
            logging.warning("Rejected invalid ping target host=%s", target_host)  # WHY: log.
            return None  # WHY: caller aborts workflow.
        if debug_mode:  # WHY: legacy debug echo of the chosen host.
            print(f"[DEBUG] Target host = {target_host}")  # WHY: legacy phrasing preserved.
        logging.debug("Ping target accepted host=%s", target_host)  # WHY: log after success.
        return target_host  # WHY: validated host returned to caller.

    def _prompt_ping_count(self, deps: WebSocketCmdDeps, debug_mode: bool) -> int:
        """Ask user for ping packet count. Return clamped int with legacy defaults."""
        raw_count = deps.safe_input_fn(  # WHY: EOF-safe input wrapper.
            _PROMPT_COUNT, context=_INPUT_CONTEXT
        ).strip()  # WHY: drop incidental whitespace from prompt response.
        parsed = self._parse_ping_count(raw_count)  # WHY: parse + range-check user input.
        return self._announce_count(parsed, debug_mode)  # WHY: chainable echo of result.

    @staticmethod
    def _parse_ping_count(raw_count: str) -> int:
        """Parse and range-check ping count input. Fall back to legacy default."""
        if not raw_count:  # WHY: empty input means accept default count.
            return _DEFAULT_PING_COUNT  # WHY: legacy fallback preserved.
        try:  # WHY: parse user input as integer. Revert to default on failure.
            parsed_count = int(raw_count)  # WHY: raises ValueError on non-numeric input.
        except ValueError:  # WHY: match legacy behavior of warning + default.
            print(_MSG_INVALID_COUNT)  # WHY: legacy phrasing preserved.
            logging.warning("Rejected non-numeric ping count input=%r", raw_count)  # WHY: log.
            return _DEFAULT_PING_COUNT  # WHY: legacy fallback preserved.
        if parsed_count < _MIN_PING_COUNT or parsed_count > _MAX_PING_COUNT:  # WHY: guard.
            print(_MSG_RANGE_COUNT)  # WHY: legacy phrasing preserved.
            logging.warning("Rejected out-of-range ping count=%d", parsed_count)  # WHY: log.
            return _DEFAULT_PING_COUNT  # WHY: legacy fallback preserved.
        return parsed_count  # WHY: accepted value path.

    @staticmethod
    def _announce_count(ping_count: int, debug_mode: bool) -> int:
        """Echo selected ping count under debug mode then return it for chaining."""
        if debug_mode:  # WHY: mirror legacy debug echo of the chosen count.
            print(f"[DEBUG] Ping count = {ping_count}")  # WHY: legacy phrasing preserved.
        return ping_count  # WHY: chainable return keeps callers concise.

    def _issue_ping_and_render(self, request: _PingRequest) -> WebSocketManager | None:
        """Connect WS, POST ping, await results, render output. Returns WS for cleanup."""
        websocket_manager = self._connect_ws(request)  # WHY: build WS + subscribe.
        if not websocket_manager.connect_and_subscribe(  # WHY: subscribe to WS stream.
            request.site_id, request.device_id, request.debug_mode
        ):
            logging.warning("WebSocket connect+subscribe failed for ping")  # WHY: log on fail.
            return websocket_manager  # WHY: hand to finally for cleanup.
        logging.debug("WebSocket connect+subscribe succeeded for ping")  # WHY: log on success.
        context = _PostContext(request=request, websocket_manager=websocket_manager)  # WHY: bundle.
        session_id = self._post_ping_command(context)  # WHY: POST + demux session id.
        if session_id is None:  # WHY: POST failed. Helper already disconnected.
            return websocket_manager  # WHY: hand to finally for cleanup.
        self._await_and_render(  # WHY: wait for WS result then render.
            websocket_manager, session_id, request.target_host, request.debug_mode
        )
        return websocket_manager  # WHY: hand to finally for cleanup.

    @staticmethod
    def _connect_ws(request: _PingRequest) -> WebSocketManager:
        """Emit legacy banner lines and build a fresh WebSocketManager for the run."""
        print(  # WHY: legacy banner announcing target + device.
            f"\n-> Executing ping to {request.target_host} on device {request.device_id}..."
        )
        print(f"-> Ping count: {request.ping_count}")  # WHY: legacy banner preserved.
        print("-> Establishing WebSocket connection...")  # WHY: legacy banner preserved.
        websocket_manager = WebSocketManager(request.deps.apisession)  # WHY: per-run manager.
        logging.info(  # WHY: action log before connect+subscribe.
            "Connecting WebSocket for ping site=%s device=%s",
            request.site_id,
            request.device_id,
        )
        return websocket_manager  # WHY: caller subscribes then proceeds.

    def _post_ping_command(self, context: _PostContext) -> str | None:
        """POST the ping command and return the session id (or None on failure)."""
        request = context.request  # WHY: alias for repeated field access.
        self._announce_post(request)  # WHY: legacy status + debug lines.
        credentials = prepare_command_credentials(  # WHY: pull + validate Mist host/token.
            request.deps.apisession, context.websocket_manager, request.debug_mode
        )
        if credentials is None:  # WHY: credential lookup failed. Helper disconnected.
            return None  # WHY: caller aborts the workflow.
        mist_host, mist_apitoken = credentials  # WHY: unpack into local variables.
        ping_url, headers = self._build_ping_request(  # WHY: assemble URL + headers.
            mist_host, mist_apitoken, request.site_id, request.device_id
        )
        payload = {"host": request.target_host, "count": request.ping_count}  # WHY: REST body.
        ping_response = post_device_command(  # WHY: POST and capture full response.
            ping_url, headers, payload, request.debug_mode, "ping"
        )
        if ping_response is None:  # WHY: defensive. Helper currently never returns None.
            return None  # WHY: treat as POST failure.
        return extract_command_session(  # WHY: demux session id for WS wait.
            ping_response, context.websocket_manager, "ping"
        )

    @staticmethod
    def _announce_post(request: _PingRequest) -> None:
        """Emit the legacy status line + optional debug payload echo before POST."""
        print("-> Issuing ping command...")  # WHY: legacy status line preserved.
        logging.debug(  # WHY: action log before HTTP POST.
            "Ping payload prepared host=%s count=%d", request.target_host, request.ping_count
        )
        if request.debug_mode:  # WHY: legacy debug echo of the payload.
            payload = {"host": request.target_host, "count": request.ping_count}  # WHY: display.
            print(f"[DEBUG] Ping payload = {payload}")  # WHY: legacy phrasing preserved.

    @staticmethod
    def _build_ping_request(
        mist_host: str, mist_apitoken: str, site_id: str, device_id: str
    ) -> tuple[str, dict[str, str]]:
        """Return the (url, headers) pair for the device-scoped ping REST call."""
        ping_url = (  # WHY: device-scoped ping endpoint URL.
            f"https://{mist_host}/api/v1/sites/{site_id}/devices/{device_id}/ping"
        )
        headers = {  # WHY: REST headers required by the Mist API.
            "Authorization": f"Token {mist_apitoken}",
            "Content-Type": "application/json",
        }
        return ping_url, headers  # WHY: caller passes tuple to post_device_command.

    def _await_and_render(
        self,
        websocket_manager: WebSocketManager,
        session_id: str,
        target_host: str,
        debug_mode: bool,
    ) -> None:
        """Wait for the ping result on the WS, then render it or report timeout."""
        self._announce_wait(session_id, debug_mode)  # WHY: legacy banner + debug lines.
        logging.info(  # WHY: action log before blocking wait.
            "Awaiting ping result session=%s", session_id[:_SESSION_PREVIEW_LEN]
        )
        ping_result = websocket_manager.wait_for_command_result(  # WHY: block on WS result.
            session_id, timeout_seconds=_WS_RESULT_TIMEOUT
        )
        logging.debug("Ping wait completed; has_result=%s", ping_result is not None)  # WHY: after-log for wait outcome.
        if debug_mode:  # WHY: legacy debug echo of wait outcome + shape.
            self._echo_wait_outcome(ping_result)  # WHY: emit legacy debug lines.
        if ping_result:  # WHY: success path renders captured payload.
            self._render_ping_result(ping_result, target_host)  # WHY: legacy render block.
            return  # WHY: done rendering.
        print(_MSG_TIMEOUT)  # WHY: legacy phrasing preserved.
        logging.warning("WebSocket ping operation timed out")  # WHY: after log on timeout.
        dump_ws_debug_state(websocket_manager, debug_mode)  # WHY: surface WS state for triage.

    @staticmethod
    def _announce_wait(session_id: str, debug_mode: bool) -> None:
        """Print the legacy banner + optional debug lines announcing the wait."""
        preview = session_id[:_SESSION_PREVIEW_LEN]  # WHY: short id for operator display.
        print(f"-> Ping command issued (session: {preview}...)")  # WHY: legacy status line.
        print("-> Waiting for ping results...")  # WHY: legacy status line preserved.
        if debug_mode:  # WHY: mirror legacy debug prints of session + waiting state.
            print(f"[DEBUG] Full session ID = {session_id}")  # WHY: legacy debug line.
            print("[DEBUG] Starting to wait for WebSocket results...")  # WHY: legacy line.

    @staticmethod
    def _echo_wait_outcome(ping_result: dict[str, Any] | None) -> None:
        """Print the legacy debug summary of the wait outcome shape."""
        print(f"[DEBUG] wait_for_command_result returned: {ping_result is not None}")  # WHY: line.
        if ping_result:  # WHY: show available top-level keys only when payload present.
            print(f"[DEBUG] Result keys: {list(ping_result.keys())}")  # WHY: legacy line.

    def _render_ping_result(self, ping_result: dict[str, Any], target_host: str) -> None:
        """Print the well-known + extra fields of a ping result payload."""
        self._print_result_banner()  # WHY: legacy header block preserved.
        raw_output = ping_result.get("raw", "")  # WHY: primary output field in schema.
        other_output = ping_result.get("Output", "")  # WHY: secondary output field.
        self._render_output_sections(raw_output, other_output)  # WHY: pick raw/other branches.
        print_extra_result_fields(ping_result, set(_EXCLUDED_RESULT_KEYS))  # WHY: extras.
        if not raw_output and not other_output:  # WHY: surface empty-result diagnostic.
            self._render_empty_result(ping_result)  # WHY: emit legacy phrasing block.
        print(_HEADER_SEPARATOR)  # WHY: legacy visual closer preserved.
        logging.info(  # WHY: final action log on successful render.
            "WebSocket ping completed successfully for %s", target_host
        )

    @staticmethod
    def _print_result_banner() -> None:
        """Emit the legacy header block above ping success output."""
        print("\n" + _HEADER_SEPARATOR)  # WHY: legacy visual separator preserved.
        print("PING RESULTS:")  # WHY: legacy header preserved verbatim.
        print(_HEADER_SEPARATOR)  # WHY: legacy visual separator preserved.

    @staticmethod
    def _render_output_sections(raw_output: str, other_output: str) -> None:
        """Render the raw / other output sections for a successful ping result."""
        if raw_output:  # WHY: render raw output block when present.
            print("RAW OUTPUT:")  # WHY: section header preserved.
            print(_SECTION_UNDERLINE)  # WHY: section underline preserved.
            print(raw_output)  # WHY: show captured raw text.
        if other_output and other_output != raw_output:  # WHY: avoid duplicate echo.
            print("\nOTHER OUTPUT:")  # WHY: section header preserved.
            print(_SECTION_UNDERLINE)  # WHY: section underline preserved.
            print(other_output)  # WHY: show captured secondary text.

    @staticmethod
    def _render_empty_result(ping_result: dict[str, Any]) -> None:
        """Print the legacy empty-result diagnostic lines."""
        print(_MSG_EMPTY_RESULT)  # WHY: legacy phrasing preserved.
        print(f"Available result keys: {list(ping_result.keys())}")  # WHY: aid for triage.

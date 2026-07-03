"""WebSocket + confirmation helper cluster for :mod:`src.device.utility_commands`.

Owns the 6 helpers that drive device-command WebSocket flows and the
typed-keyword destructive-op confirmation prompt. Splitting these off
:class:`~src.device.utility_commands.DeviceUtilityCommands` shrinks the
parent, keeps the WebSocket lifecycle (connect / subscribe / execute /
disconnect) in one focused module, and lets the same wrapper +
``__getattr__`` proxy pattern used by the Phase-1 selection cluster
handle attribute lookup transparently.

The parent binds an instance as ``self._websocket`` and its
``__getattr__`` proxies unknown attribute lookups here so shared state
(dependency callables, mistapi module) stays transparent. Peer-method
calls inside this cluster route through ``self._uc._method(...)`` so
``patch.object(duc, "_method", ...)`` in tests wins over the cluster's
own binding.

Two 6-parameter helpers (``_stream_ws_output``, ``_display_and_export_result``)
that historically carried ``# noqa: PLR0913`` in the parent module are now
bundled into frozen ``StreamWsSpec`` / ``ExportResultSpec`` dataclasses so the
underlying methods take a single specification object and the compliance
STRUCT-PARAMS rule (limit 5) is satisfied without any noqa.
"""

# pylint: disable=logging-fstring-interpolation

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import logging  # WHY: exception-level logging when WebSocket calls fail
import time  # WHY: 1s sleep after subscription to let the channel settle
from dataclasses import dataclass  # WHY: frozen bundle structs replace multi-arg method signatures
from datetime import UTC, datetime  # WHY: ISO timestamp on exported command results
from typing import Any, cast  # WHY: cast narrows Any from __getattr__ proxy

from src.device._utility_commands_cluster import _ClusterBase  # WHY: shared proxy base


@dataclass(frozen=True)  # WHY: frozen so callers cannot mutate mid-flow
class StreamWsSpec:  # WHY: bundle for _stream_ws_output single-arg signature
    """Bundle of parameters passed to :meth:`_UtilityCommandsWebsocket._stream_ws_output`.

    Groups the 6 originally-positional args (site_id, device_id, sdk_method,
    body, websocket_manager, timeout_seconds) into a single specification so
    the underlying helper method has a single-argument signature satisfying
    STRUCT-PARAMS (limit 5).
    """

    site_id: str  # WHY: mistapi site scope for SDK call
    device_id: str  # WHY: mistapi device scope for SDK call
    sdk_method: Any  # WHY: bound mistapi method (traceroute/monitor_traffic/etc.)
    body: dict[str, Any] | None  # WHY: optional JSON body; some SDK methods take none
    websocket_manager: Any  # WHY: already-connected WebSocketManager instance
    timeout_seconds: int  # WHY: overall wait budget for streaming result


@dataclass(frozen=True)  # WHY: frozen so callers cannot mutate mid-flow
class ExportResultSpec:  # WHY: bundle for _display_and_export_result single-arg signature
    """Bundle of parameters passed to :meth:`_UtilityCommandsWebsocket._display_and_export_result`.

    Groups the 6 originally-positional args (result, command_name, site_id,
    device_id, api_function_name, filename) into a single spec so the helper
    method has a single-argument signature satisfying STRUCT-PARAMS.
    """

    result: dict[str, Any] | None  # WHY: WebSocket command payload; None on timeout
    command_name: str  # WHY: label rendered in banner header
    site_id: str  # WHY: audit metadata on exported row
    device_id: str  # WHY: audit metadata on exported row
    api_function_name: str  # WHY: mistapi function label for exporter
    filename: str  # WHY: output CSV filename


class _UtilityCommandsWebsocket(_ClusterBase):  # WHY: cluster wrapper mirroring _UtilityCommandsSelection
    """Wrapper class holding the WebSocket + confirm helpers."""

    # ------------------------------------------------------------------
    # WebSocket command lifecycle (request/response)
    # ------------------------------------------------------------------

    def _run_websocket_command(
        self,
        site_id: str,
        device_id: str,
        sdk_method: Any,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:  # WHY: request/response variant returns final payload
        """Execute WebSocket command: POST -> subscribe -> await."""
        websocket_manager = self._ws_factory(self._apisession)  # WHY: __getattr__ proxy to parent state
        if not self._prepare_ws_channel(websocket_manager, site_id, device_id):  # WHY: connect+subscribe
            return None  # WHY: channel setup already emitted diagnostics
        return self._safe_execute_ws(  # WHY: extracted helper keeps this method <=25 lines
            site_id,
            device_id,
            sdk_method,
            body,
            websocket_manager,
        )

    def _safe_execute_ws(  # noqa: PLR0913
        self,
        site_id: str,
        device_id: str,
        sdk_method: Any,
        body: dict[str, Any] | None,
        websocket_manager: Any,
    ) -> dict[str, Any] | None:
        """Run ``_execute_ws_command`` with log-and-continue error handling."""
        try:
            # WHY: route through parent so patch.object(duc, "_execute_ws_command", ...) intercepts
            return cast(  # WHY: parent proxy returns Any; narrow to concrete type
                "dict[str, Any] | None",
                self._call(
                    "_execute_ws_command",
                    site_id,
                    device_id,
                    sdk_method,
                    body,
                    websocket_manager,
                ),
            )
        except Exception as error:  # WHY: log-and-continue on any WS/SDK failure
            logging.exception("WebSocket command failed: %s", error)  # WHY: audit failure with stack
            print(f"! Command failed: {error}")  # WHY: surface error to operator
            return None  # WHY: caller treats None as no-result
        finally:
            websocket_manager.disconnect()  # WHY: always clean up socket

    def _execute_ws_command(  # noqa: PLR0913
        self,
        site_id: str,
        device_id: str,
        sdk_method: Any,
        body: dict[str, Any] | None,
        websocket_manager: Any,
    ) -> dict[str, Any] | None:  # WHY: single-shot request returning result payload
        """Run SDK method and wait for WebSocket result."""
        response = self._invoke_sdk(sdk_method, site_id, device_id, body)  # WHY: unified SDK invocation
        session_id = self._extract_session_id(response)  # WHY: parse session or fail fast
        if session_id is None:  # WHY: missing session -> nothing to await
            return None  # WHY: helper already emitted diagnostics
        print(f"-> Command issued (session: {session_id[:8]}...)")  # WHY: operator feedback
        print("-> Waiting for results...")  # WHY: hint on latency budget
        result: dict[str, Any] | None = websocket_manager.wait_for_command_result(
            session_id, timeout_seconds=120  # WHY: 2-minute cap matches mistapi default
        )
        return result  # WHY: caller renders/exports this payload

    # ------------------------------------------------------------------
    # WebSocket command lifecycle (streaming variant)
    # ------------------------------------------------------------------

    def _run_streaming_command(  # noqa: PLR0913
        self,
        site_id: str,
        device_id: str,
        sdk_method: Any,
        body: dict[str, Any] | None = None,
        timeout_seconds: int = 120,
    ) -> None:  # WHY: streaming variant prints inline; no return payload
        """Execute streaming WebSocket command with output display."""
        websocket_manager = self._ws_factory(self._apisession)  # WHY: __getattr__ proxy to parent state
        if not self._prepare_ws_channel(websocket_manager, site_id, device_id):  # WHY: connect+subscribe
            return  # WHY: helper already emitted diagnostics
        spec = StreamWsSpec(  # WHY: bundle 6 params so the streaming helper is single-arg
            site_id=site_id,
            device_id=device_id,
            sdk_method=sdk_method,
            body=body,
            websocket_manager=websocket_manager,
            timeout_seconds=timeout_seconds,
        )
        self._safe_stream(spec, websocket_manager)  # WHY: extracted try/except keeps <=25 lines

    def _safe_stream(self, spec: StreamWsSpec, websocket_manager: Any) -> None:
        """Run ``_stream_ws_output`` with Ctrl+C and log-and-continue handling."""
        try:
            # WHY: route through parent so patch.object(duc, "_stream_ws_output", ...) intercepts
            self._call("_stream_ws_output", spec)
        except KeyboardInterrupt:  # WHY: operator Ctrl+C is a normal stop signal
            print("\n-> Streaming stopped by user.")  # WHY: acknowledge intentional halt
        except Exception as error:  # WHY: log-and-continue on any WS/SDK failure
            logging.exception("Streaming command failed: %s", error)  # WHY: audit failure with stack
            print(f"! Streaming failed: {error}")  # WHY: surface error to operator
        finally:
            websocket_manager.disconnect()  # WHY: always clean up

    def _stream_ws_output(self, spec: StreamWsSpec) -> None:  # WHY: single-arg spec keeps STRUCT clean
        """Stream WebSocket output to console using a :class:`StreamWsSpec`."""
        response = self._invoke_sdk(spec.sdk_method, spec.site_id, spec.device_id, spec.body)  # WHY: SDK call
        session_id = self._extract_session_id(response, absent_msg="! No session ID returned.")  # WHY: parse
        if session_id is None:  # WHY: no session -> nothing to stream
            return  # WHY: helper already emitted diagnostics
        print(f"-> Streaming started (session: {session_id[:8]}...)")  # WHY: operator feedback
        print("-> Press Ctrl+C to stop.\n")  # WHY: hint on how to end streaming
        result = spec.websocket_manager.wait_for_command_result(
            session_id,
            timeout_seconds=spec.timeout_seconds,
            activity_timeout_seconds=30,  # WHY: idle-cutoff for streaming variant
        )
        self._print_stream_raw(result)  # WHY: single-branch renderer keeps C low here

    # ------------------------------------------------------------------
    # Result rendering + dual-output export
    # ------------------------------------------------------------------

    def _display_and_export_result(self, spec: ExportResultSpec) -> None:  # WHY: single-arg spec keeps STRUCT clean
        """Display WebSocket result and write to dual output using :class:`ExportResultSpec`."""
        if not spec.result:  # WHY: timeout / disconnect / API error
            print("! No results received (timeout or error).")  # WHY: signal empty result
            return
        raw_output, other_output = self._print_result_block(spec.command_name, spec.result)  # WHY: banner
        export_data = self._build_export_row(spec, raw_output, other_output)  # WHY: canonical payload
        self._write_export_fn([export_data], spec.filename, spec.api_function_name)  # WHY: __getattr__ proxy

    # ------------------------------------------------------------------
    # Destructive-op confirmation
    # ------------------------------------------------------------------

    def _confirm_destructive(self, prompt: str, keyword: str, context: str) -> bool:
        """Require typed keyword confirmation for destructive ops."""
        confirmation = self._safe_input_fn(prompt, context=context)  # WHY: __getattr__ proxy
        if confirmation != keyword:  # WHY: exact-match gate; even leading/trailing space fails
            print("! Operation cancelled - confirmation not matched.")  # WHY: signal cancel
            return False
        return True

    # ------------------------------------------------------------------
    # Private sub-helpers (keep the public helpers under C<=5)
    # ------------------------------------------------------------------

    def _prepare_ws_channel(self, websocket_manager: Any, site_id: str, device_id: str) -> bool:
        """Connect the WS manager and subscribe to the per-device command channel."""
        if not websocket_manager.connect():  # WHY: bail if WS handshake fails
            print("! Failed to establish WebSocket connection.")  # WHY: expose handshake failure
            return False
        channel = f"/sites/{site_id}/devices/{device_id}/cmd"  # WHY: per-device command channel
        if not websocket_manager.subscribe_to_channel(channel):  # WHY: subscribe before firing SDK call
            print("! Failed to subscribe to device command channel.")  # WHY: expose subscribe failure
            websocket_manager.disconnect()  # WHY: release socket on subscribe failure
            return False
        time.sleep(1)  # WHY: let subscription settle before command
        return True

    def _invoke_sdk(
        self,
        sdk_method: Any,
        site_id: str,
        device_id: str,
        body: dict[str, Any] | None,
    ) -> Any:
        """Invoke the mistapi SDK method with or without a body."""
        if body is not None:  # WHY: some SDK methods take a body, others do not
            return sdk_method(self._apisession, site_id, device_id, body)  # WHY: __getattr__ proxy
        return sdk_method(self._apisession, site_id, device_id)  # WHY: __getattr__ proxy

    @staticmethod
    def _extract_session_id(
        response: Any,
        absent_msg: str = "! No session ID returned from command.",
    ) -> str | None:
        """Extract the WebSocket session id from an SDK response or return None."""
        if not hasattr(response, "data"):  # WHY: mistapi returns response object with .data
            print("! No response data from API.")  # WHY: signal empty payload
            return None
        response_data = response.data if isinstance(response.data, dict) else {}  # WHY: guard shape
        session_id = response_data.get("session")  # WHY: session_id is the WS correlation key
        if not session_id:  # WHY: no session -> nothing to wait for
            print(absent_msg)  # WHY: differentiate command vs streaming context
            return None
        return cast("str", session_id)  # WHY: narrow Any from dict.get

    @staticmethod
    def _print_stream_raw(result: dict[str, Any] | None) -> None:
        """Print the raw streaming output if present."""
        if not result:  # WHY: nothing to print on timeout / disconnect
            return
        raw = result.get("raw", "")  # WHY: streaming variant only reads 'raw'
        if raw:  # WHY: skip blank lines from empty payloads
            print(raw)

    @staticmethod
    def _print_result_block(command_name: str, result: dict[str, Any]) -> tuple[str, str]:
        """Print the display block for a command result and return (raw, other)."""
        print("\n" + "=" * 60)  # WHY: banner separates command output block
        print(f"{command_name.upper()} RESULTS:")  # WHY: identify command in operator log
        print("=" * 60)
        raw_output = str(result.get("raw", ""))  # WHY: preferred output key
        if raw_output:  # WHY: skip if absent
            print(raw_output)
        other_output = str(result.get("Output", ""))  # WHY: some SDK paths emit under 'Output'
        if other_output and other_output != raw_output:  # WHY: avoid double-printing same content
            print(other_output)
        return raw_output, other_output

    @staticmethod
    def _build_export_row(
        spec: ExportResultSpec,
        raw_output: str,
        other_output: str,
    ) -> dict[str, Any]:
        """Build the export row consumed by :attr:`_write_export_fn`."""
        return {
            "device_id": spec.device_id,
            "site_id": spec.site_id,
            "command": spec.command_name,
            "timestamp": datetime.now(UTC).isoformat(),  # WHY: audit trail on export
            "raw_output": raw_output or other_output or str(spec.result),  # WHY: fallback preserves payload
        }

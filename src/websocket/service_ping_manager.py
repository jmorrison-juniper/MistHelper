"""Service ping manager extracted from MistHelper.py."""

from __future__ import annotations  # WHY: PEP 563 postponed annotations for forward refs.

import logging  # WHY: emit info/debug logs across service ping workflow phases.
import sys  # WHY: read argv to record debug context on entry.
from typing import Any  # WHY: injected utility modules are opaque to the type checker.

from src.websocket.service_ping_discovery import (  # WHY: reuse discovery mixin and DI helpers.
    ServicePingDiscoveryDependencies,  # WHY: dataclass expected by discovery configure hook.
    ServicePingDiscoveryMixin,  # WHY: provides shared tenant/service discovery methods.
    configure_service_ping_discovery_dependencies,  # WHY: forwards deps to discovery module.
)

apisession: Any = None  # WHY: lazily-bound authenticated Mist session assigned via injection.
mistapi: Any = None  # WHY: lazily-bound mistapi module reference for API calls.
PromptUtils: Any = None  # WHY: lazily-bound prompt helper for site/device selection.
InputUtils: Any = None  # WHY: lazily-bound input helper for confirmation prompts.
WebSocketManager: Any = None  # WHY: lazily-bound websocket transport class.
is_debug_mode_fn: Any = None  # WHY: lazily-bound debug mode probe used at manager init.
APITenantFetchUtils: Any = None  # WHY: lazily-bound tenant discovery class forwarded to mixin.
ConfigUtils: Any = None  # WHY: lazily-bound cached org lookup helper.
APIFetchUtils: Any = None  # WHY: lazily-bound service discovery helper class.

_GATEWAY_TIMEOUT_TOTAL = 45  # WHY: extended websocket wait window for slower SSR gateway responses.
_GATEWAY_TIMEOUT_ACTIVITY = 5  # WHY: activity idle timeout tuned to SSR gateway pacing.
_DEFAULT_TIMEOUT_TOTAL = 30  # WHY: default websocket wait window for non-gateway devices.
_DEFAULT_TIMEOUT_ACTIVITY = 3  # WHY: default activity idle timeout for non-gateway devices.
_SUBSCRIPTION_TIMEOUT = 15  # WHY: seconds to wait for websocket subscription confirmation.
_SESSION_SHORT_LEN = 8  # WHY: character count for the truncated session preview shown to users.
_DEVICE_TYPE_LABELS = {"ap": "Access Point", "switch": "Switch"}  # WHY: friendly names for warnings.
_TROUBLESHOOTING_TIPS = {  # WHY: per-device-type hint tables consulted after a timeout.
    "gateway": (  # WHY: gateway-specific guidance for service ping timeouts.
        "Verify service name is valid for this SSR",
        "Check if host is reachable through the specified service",
        "Confirm SSR routing configuration for the service",
        "Try with a different service name",
    ),
    "switch": (  # WHY: switch-specific fallback guidance.
        "Switches typically do not support service ping",
        "Try using regular ping (Menu 87) for basic connectivity",
        "Service ping is an SSR-specific feature",
    ),
    "ap": (  # WHY: access-point-specific fallback guidance.
        "Access Points do not support service ping",
        "Try using regular ping (Menu 87) for basic connectivity",
        "Service ping is an SSR-specific feature",
    ),
}
_DEFAULT_TIPS = (  # WHY: fallback guidance when the device type is unknown.
    "Service ping is designed for SSR gateways",
    "Try using regular ping (Menu 87) for basic connectivity",
)


def configure_service_ping_manager_dependencies(**deps: Any) -> None:  # WHY: variadic collapse.
    """Configure runtime dependencies for the extracted service ping manager."""
    global apisession, mistapi, PromptUtils, InputUtils, WebSocketManager  # WHY: publish bindings.
    global is_debug_mode_fn, APITenantFetchUtils, ConfigUtils, APIFetchUtils  # WHY: continued globals.
    apisession = deps["apisession_dependency"]  # WHY: publish injected apisession handle.
    mistapi = deps["mistapi_dependency"]  # WHY: publish injected mistapi module.
    PromptUtils = deps["prompt_utils"]  # WHY: publish prompt helper for menu flow.
    InputUtils = deps["input_utils"]  # WHY: publish input helper for user confirmation.
    WebSocketManager = deps["websocket_manager_class"]  # WHY: publish websocket transport class.
    is_debug_mode_fn = deps["is_debug_mode"]  # WHY: publish debug probe closure.
    APITenantFetchUtils = deps["api_tenant_fetch_utils"]  # WHY: publish tenant utility class.
    ConfigUtils = deps["config_utils"]  # WHY: publish config utility helper.
    APIFetchUtils = deps["api_fetch_utils"]  # WHY: publish api fetch utility class.
    configure_service_ping_discovery_dependencies(  # WHY: forward matching deps to discovery module.
        ServicePingDiscoveryDependencies(
            apisession=deps["apisession_dependency"],  # WHY: mirror injected session into discovery.
            mistapi=deps["mistapi_dependency"],  # WHY: mirror mistapi module into discovery.
            api_tenant_fetch_utils=deps["api_tenant_fetch_utils"],  # WHY: reuse tenant utility.
            config_utils=deps["config_utils"],  # WHY: reuse config utility.
            api_fetch_utils=deps["api_fetch_utils"],  # WHY: reuse api fetch utility.
            input_utils=deps["input_utils"],  # WHY: reuse input helper for discovery prompts.
        )
    )


def _short_session_preview(session_id: str) -> str:  # WHY: extract shortening logic for reuse.
    """Return a short preview of the session id for user-facing output."""
    if len(session_id) > _SESSION_SHORT_LEN:  # WHY: only truncate when longer than preview budget.
        return session_id[:_SESSION_SHORT_LEN] + "..."  # WHY: preserve prefix and mark truncation.
    return session_id  # WHY: short ids are safe to show in full.


class ServicePingManager(ServicePingDiscoveryMixin):  # WHY: define ServicePingManager class.
    """Manager class for SSR Service Ping operations via WebSocket."""

    DEFAULT_HOST = "8.8.8.8"  # WHY: safe default public IP used when no host is entered.
    DEFAULT_COUNT = 4  # WHY: default ping count matches Junos SSR service-ping default.
    DEFAULT_SIZE = 56  # WHY: default payload size matches Junos SSR service-ping default.
    MIN_SIZE = 56  # WHY: minimum payload size accepted by SSR service-ping.
    MAX_SIZE = 65535  # WHY: maximum payload size accepted by SSR service-ping.
    DEFAULT_TENANT = "testing-tools"  # WHY: canonical tenant name used by SSR test tooling.
    DEFAULT_SERVICE = "web-session"  # WHY: canonical service name for web-session tests.

    def __init__(self) -> None:  # WHY: constructor initialises manager state and discovery caches.
        """Initialize manager state and discovery caches."""
        self.debug_mode = bool(is_debug_mode_fn()) if is_debug_mode_fn else False  # WHY: latch debug.
        self.site_id: str | None = None  # WHY: selected site id populated during workflow start.
        self.device_id: str | None = None  # WHY: selected device id populated during workflow start.
        self.device_info: dict[str, Any] | None = None  # WHY: cached device metadata for gating.
        self.websocket_manager: Any | None = None  # WHY: websocket transport instance created later.
        self.org_tenants: list[str] = []  # WHY: cache of org-scope tenant names for combined list.
        self.site_tenants: list[str] = []  # WHY: cache of site-scope tenant names.
        self.policy_tenants: list[str] = []  # WHY: cache of service-policy tenant names.
        self.template_tenants: list[str] = []  # WHY: cache of gateway-template tenant names.
        self.device_tenants: list[str] = []  # WHY: cache of device-scope tenant names.
        self.org_services: list[dict[str, Any]] = []  # WHY: cache of raw org service records.
        self.org_service_names: list[str] = []  # WHY: cache of org service names for prompts.
        self.device_services: list[str] = []  # WHY: cache of device-scope service names.

    def _debug_print(self, message: str) -> None:  # WHY: helper prints only when debug is enabled.
        """Print debug message when debug mode is enabled."""
        if self.debug_mode:  # WHY: suppress noise when debug mode is off.
            print(f"[DEBUG] {message}")  # WHY: annotate output as debug for operator scanning.

    def _select_site_and_device(self) -> bool:  # WHY: gather site/device selections from user.
        """Prompt for site and gateway device selection."""
        self.site_id = PromptUtils.select_site_id_from_csv()  # WHY: reuse CSV site chooser flow.
        if not self.site_id:  # WHY: guard-return when user aborts site prompt.
            print("! No site selected. Operation cancelled.")  # WHY: notify operator of exit.
            return False  # WHY: signal caller to abort workflow.
        self._debug_print(f"Selected site_id = {self.site_id}")  # WHY: trace picked site for debug.
        self.device_id = PromptUtils.select_device_id_from_inventory(  # WHY: gateway-only inventory.
            self.site_id, device_type="gateway"
        )
        if not self.device_id:  # WHY: guard-return when no gateway device is available.
            print("! No gateway devices found or selected. Service Ping requires an SSR gateway.")
            return False  # WHY: signal caller that gateway selection failed.
        self._debug_print(f"Selected device_id = {self.device_id}")  # WHY: trace picked device.
        return True  # WHY: selections complete, allow workflow to continue.

    def _lookup_device_info(self) -> bool:  # WHY: pure lookup step split out to drop CC of caller.
        """Populate device_info from the Mist API listSiteDevices response."""
        try:  # WHY: mistapi failures must not crash the workflow.
            logging.info(  # WHY: record the lookup for operational tracing.
                "Fetching gateway device details for site %s and device %s",
                self.site_id,
                self.device_id,
            )
            raw_data = mistapi.api.v1.sites.devices.listSiteDevices(  # WHY: query gateway list.
                apisession, self.site_id, type="gateway"
            ).data
            logging.debug("Retrieved %d gateway devices for site %s", len(raw_data or []), self.site_id)
            self.device_info = next(  # WHY: pick the entry matching the chosen device id.
                (device for device in raw_data if device.get("id") == self.device_id),
                None,
            )
            logging.debug("Device lookup complete for %s, found=%s", self.device_id, self.device_info is not None)
        except Exception as error:  # WHY: swallow api errors and drop to unknown-device prompt.
            logging.warning("Could not retrieve device details: %s", error)  # WHY: warn on failure.
            self._debug_print(f"Device details error: {error}")  # WHY: surface exception in debug.
            return False  # WHY: caller must fall through to unknown-device confirmation.
        return True  # WHY: lookup succeeded, caller can inspect device_info.

    def _fetch_device_info(self) -> bool:  # WHY: coordinator combining lookup and validation.
        """Fetch target device information and validate it for service ping."""
        if not self._lookup_device_info():  # WHY: lookup failure escalates to unknown-device prompt.
            return self._confirm_unknown_device()
        if not self.device_info:  # WHY: missing record also uses the unknown-device confirmation.
            return self._confirm_unknown_device()
        return self._validate_device_type()  # WHY: normal path validates against gateway requirement.

    def _validate_device_type(self) -> bool:  # WHY: gating logic for gateway vs other device kinds.
        """Validate the chosen device type and warn when not a gateway."""
        if self.device_info is None:  # WHY: defensive guard when info was cleared during lookup.
            return self._confirm_unknown_device()
        device_type = self.device_info.get("type", "unknown")  # WHY: default keeps output consistent.
        device_model = self.device_info.get("model", "unknown")  # WHY: model name for messaging.
        self._debug_print(f"Device type: {device_type}, model: {device_model}")  # WHY: trace types.
        if device_type == "gateway":  # WHY: gateway is the intended target, so accept directly.
            print(f"!? SSR Gateway detected (Model: {device_model})")  # WHY: confirm detection.
            print("   -> Service Ping allows ping packets to follow service-specific paths")
            return True  # WHY: gateway devices always pass validation.
        device_label = _DEVICE_TYPE_LABELS.get(device_type, "Unknown device type")  # WHY: friendly.
        print(f"!? WARNING: {device_label} detected (Model: {device_model})")  # WHY: warn user.
        print("   -> Service Ping is designed for SSR gateways")  # WHY: reinforce use case.
        return self._confirm_proceed()  # WHY: ask user before continuing on non-gateway.

    def _confirm_unknown_device(self) -> bool:  # WHY: reusable prompt for indeterminate devices.
        """Prompt before continuing when device type cannot be determined."""
        print("!? Cannot determine device type - proceeding with caution")  # WHY: warn operator.
        print("   -> Service Ping is designed for SSR gateways")  # WHY: reinforce use case.
        return self._confirm_proceed()  # WHY: reuse yes/no confirmation.

    def _confirm_proceed(self) -> bool:  # WHY: helper that gates continuation on user confirmation.
        """Prompt user to confirm proceeding on non-optimal device types."""
        choice = (  # WHY: normalise input by stripping whitespace and lowercasing.
            InputUtils.safe_input(
                "   -> Continue anyway? (y/N): ",
                context="service_ping_continue",
            )
            .strip()
            .lower()
        )
        if choice != "y":  # WHY: any answer other than explicit yes cancels the operation.
            print("Operation cancelled.")  # WHY: acknowledge the cancel path for the operator.
            return False  # WHY: signal caller to abort workflow.
        return True  # WHY: user opted to continue on a non-optimal device.

    def _wait_for_subscription(self, command_channel: str) -> None:  # WHY: extracted subscription wait.
        """Wait for the websocket subscription confirmation and surface status to user."""
        print("-> Waiting for subscription confirmation...")  # WHY: signal waiting state to user.
        if not self.websocket_manager.wait_for_subscription_confirmation(  # WHY: block until acked.
            command_channel, timeout_seconds=_SUBSCRIPTION_TIMEOUT
        ):
            print("! Subscription confirmation not received within timeout")  # WHY: warn on skip.
            print("! Proceeding anyway, but results may not be received")  # WHY: describe risk.
            return  # WHY: exit early after warning.
        print("-> Subscription confirmed")  # WHY: acknowledge successful subscription.

    def _setup_websocket(self) -> bool:  # WHY: orchestrate websocket connect + subscribe.
        """Connect and subscribe websocket transport for command results."""
        self.websocket_manager = WebSocketManager(apisession)  # WHY: instantiate transport client.
        if not self.websocket_manager.connect():  # WHY: guard against connect failure.
            print("! Failed to establish WebSocket connection")  # WHY: notify operator of failure.
            return False  # WHY: cannot proceed without transport connection.
        self._debug_print("WebSocket connection established")  # WHY: trace connect for debug.
        command_channel = f"/sites/{self.site_id}/devices/{self.device_id}/cmd"  # WHY: build path.
        if not self.websocket_manager.subscribe_to_channel(command_channel):  # WHY: guard subscribe.
            print("! Failed to subscribe to device command channel")  # WHY: notify on failure.
            return False  # WHY: cannot proceed without subscription.
        self._debug_print(f"Subscribed to channel: {command_channel}")  # WHY: trace subscribe.
        print("-> WebSocket connected and subscribed")  # WHY: confirm handshake to operator.
        self._wait_for_subscription(command_channel)  # WHY: helper handles ack wait and messaging.
        return True  # WHY: transport ready for command dispatch.

    def _handle_ping_response(self, response: Any) -> str | None:  # WHY: extract response parsing.
        """Interpret Mist API response and return session id or None on failure."""
        logging.info("Service ping mistapi response status: %s", response.status_code)  # WHY: log.
        logging.info("Service ping mistapi response data: %s", response.data)  # WHY: log body.
        self._debug_print(f"mistapi Response Status = {response.status_code}")  # WHY: debug status.
        self._debug_print(f"mistapi Response Data = {response.data}")  # WHY: debug body.
        if response.status_code != 200:  # WHY: any non-200 status signals command rejection.
            print(f"Failed to issue Service Ping command. Status {response.status_code}: {response.data}")
            logging.error("Service ping failed - status %s: %s", response.status_code, response.data)
            return None  # WHY: caller aborts result waiting on failure.
        session_id = response.data.get("session", "")  # WHY: session id is stringly-typed in payload.
        if session_id:  # WHY: only print/log when the api actually returned a session identifier.
            short_id = _short_session_preview(session_id)  # WHY: prefer short form for user output.
            print(f"-> Service Ping command issued (session: {short_id})")  # WHY: confirm dispatch.
            self._debug_print(f"Full session ID: {session_id}")  # WHY: retain full id in debug log.
        else:  # WHY: still report success even when session id is missing.
            print("-> Service Ping command issued (no session ID returned)")  # WHY: note absence.
        return session_id or None  # WHY: treat empty string as None for downstream branching.

    def _execute_service_ping(self, payload: dict[str, Any]) -> str | None:  # WHY: dispatch coord.
        """Issue the Mist API service-ping request and return session ID."""
        print("-> Issuing Service Ping command...")  # WHY: signal dispatch to operator.
        self._debug_print(f"Service ping payload being sent: {payload}")  # WHY: debug payload.
        logging.info("Sending service ping via mistapi to device: %s", self.device_id)  # WHY: log.
        logging.info("Service ping payload: %s", payload)  # WHY: log payload for audit.
        try:  # WHY: guard the API round-trip so error path is uniform.
            response = mistapi.api.v1.sites.devices.servicePingFromSsr(  # WHY: dispatch call inline.
                apisession, self.site_id, self.device_id, payload
            )
        except Exception as error:  # WHY: any api failure must be surfaced without crashing menu.
            print(f"Error issuing Service Ping command via mistapi: {error}")  # WHY: user-visible.
            logging.error("Service ping error: %s", error)  # WHY: log error for post-mortem.
            self._debug_print(f"mistapi exception details: {type(error).__name__}: {error}")
            return None  # WHY: caller treats None as dispatch failure.
        return self._handle_ping_response(response)  # WHY: helper interprets the successful response.

    def _select_timeout_profile(self) -> tuple[int, int]:  # WHY: pure lookup for wait profile.
        """Return (total, activity) websocket wait timeouts for the current device type."""
        if self.device_info and self.device_info.get("type") == "gateway":  # WHY: extended profile.
            print("   -> Using extended timeout for SSR gateway (45s total, 5s activity)")
            return _GATEWAY_TIMEOUT_TOTAL, _GATEWAY_TIMEOUT_ACTIVITY  # WHY: slow SSR responses.
        return _DEFAULT_TIMEOUT_TOTAL, _DEFAULT_TIMEOUT_ACTIVITY  # WHY: default pace for non-gateway.

    def _wait_for_results(self, session_id: str) -> dict[str, Any] | None:  # WHY: wait coordinator.
        """Wait for websocket command results with device-type-specific timeout."""
        print("-> Waiting for Service Ping results...")  # WHY: signal waiting state to operator.
        self._debug_print(f"Full session ID = {session_id}")  # WHY: emit full session id in debug.
        self._debug_print("Starting to wait for WebSocket results...")  # WHY: trace wait start.
        if self.websocket_manager is None:  # WHY: guard against calls without an active transport.
            return None  # WHY: nothing to wait on when transport is missing.
        timeout_seconds, activity_timeout = self._select_timeout_profile()  # WHY: pick timeouts.
        result = self.websocket_manager.wait_for_command_result(  # WHY: block until ack or timeout.
            session_id,
            timeout_seconds=timeout_seconds,
            activity_timeout_seconds=activity_timeout,
        )
        self._debug_print(f"wait_for_command_result returned: {result is not None}")  # WHY: trace.
        if result:  # WHY: only log key set when we actually received a payload.
            self._debug_print(f"Result keys: {list(result.keys())}")  # WHY: highlight schema.
        return result  # WHY: return raw result dict for downstream display.

    def _display_results(self, result: dict[str, Any] | None, payload: dict[str, Any]) -> None:
        """Display success or timeout result output."""
        if result:  # WHY: presence of result determines success vs timeout branch.
            self._display_success_results(result, payload)  # WHY: format success output.
            return  # WHY: guard-return keeps this dispatcher trivial.
        self._display_timeout_results(payload)  # WHY: format timeout guidance for operator.

    def _print_ping_output(self, raw_output: str, parsed_output: str) -> None:  # WHY: printing.
        """Print raw and parsed ping output sections when available."""
        if raw_output:  # WHY: only print the raw section when the payload actually contains data.
            print("PING OUTPUT:")  # WHY: label section for operator scanning.
            print("-" * 40)  # WHY: visual separator.
            print(raw_output)  # WHY: dump the raw ping output verbatim.
        if parsed_output and parsed_output != raw_output:  # WHY: skip duplicate parsed content.
            print("\nPARSED OUTPUT:")  # WHY: label parsed section.
            print("-" * 40)  # WHY: visual separator.
            print(parsed_output)  # WHY: dump the parsed representation for reference.

    def _handle_empty_output(self) -> None:  # WHY: helper drops CC from success-results method.
        """Print the empty-output notice and non-gateway troubleshooting when applicable."""
        print("No output data received")  # WHY: operator needs to know payload was empty.
        if self.device_info and self.device_info.get("type") != "gateway":  # WHY: hint block.
            self._display_non_gateway_troubleshooting()  # WHY: guidance for wrong device kind.

    def _display_success_results(self, result: dict[str, Any], payload: dict[str, Any]) -> None:
        """Display successful service ping results."""
        print("\n" + "=" * 60)  # WHY: leading separator introduces the results section.
        print("SERVICE PING RESULTS:")  # WHY: banner labels this block for the operator.
        print("=" * 60)  # WHY: matching trailing bar frames the banner.
        if self.device_info is not None:  # WHY: only print device context when we have metadata.
            self._display_device_context(payload)  # WHY: helper prints identity and routing note.
        raw_output = result.get("raw", "")  # WHY: raw text is the primary output when present.
        parsed_output = result.get("Output", "")  # WHY: parsed variant may replace raw when equal.
        self._print_ping_output(raw_output, parsed_output)  # WHY: helper handles both sections.
        if not raw_output and not parsed_output:  # WHY: highlight missing output edge case.
            self._handle_empty_output()  # WHY: helper prints notice and any hint block needed.
        print("=" * 60)  # WHY: final separator closes the results section.
        self._log_success(payload)  # WHY: emit completion log with device and service context.

    def _display_device_context(self, payload: dict[str, Any]) -> None:  # WHY: identity block.
        """Display device identity/context in the results section."""
        if self.device_info is None:  # WHY: guard when info was cleared between validation and print.
            return  # WHY: nothing to display without device metadata.
        device_type = self.device_info.get("type", "unknown")  # WHY: default keeps output consistent.
        device_model = self.device_info.get("model", "unknown")  # WHY: model string for context.
        device_name = self.device_info.get("name", "Unknown Device")  # WHY: preserve label fallback.
        print(f"Device: {device_name} ({str(device_type).upper()}: {device_model})")  # WHY: line 1.
        print(f"Service: {payload['service']} -> Host: {payload['host']}")  # WHY: show routing pair.
        if device_type == "gateway":  # WHY: gateway path emphasises service-specific routing note.
            print("Note: Service-specific routing path used for ping packets")  # WHY: reinforce.
        else:  # WHY: non-gateway path warns about partial support.
            print("Note: Device may not fully support service ping functionality")  # WHY: caution.
        print("-" * 60)  # WHY: visual separator before subsequent output sections.

    def _display_non_gateway_troubleshooting(self) -> None:  # WHY: helper for hint block.
        """Display guidance for non-gateway devices with no result output."""
        print("\nTroubleshooting for non-gateway devices:")  # WHY: label the hint block.
        print("-> Service Ping is designed specifically for SSR gateways")  # WHY: reinforce use.
        print("-> Try using regular ping (Menu 87) instead")  # WHY: suggest fallback command.
        print("-> Verify device supports service ping functionality")  # WHY: request verification.

    def _log_success(self, payload: dict[str, Any]) -> None:  # WHY: emit uniform completion log.
        """Log successful completion summary."""
        if self.device_info:  # WHY: only include name/type when metadata is available.
            device_name = self.device_info.get("name", "Unknown Device")  # WHY: log-friendly name.
            device_type = self.device_info.get("type", "unknown")  # WHY: log-friendly type label.
            logging.info(
                "Service ping completed for %s (%s) - Service: %s, Host: %s",
                device_name,
                device_type,
                payload["service"],
                payload["host"],
            )
            return  # WHY: alternate branch handled below.
        logging.info(  # WHY: fallback log when device metadata is missing.
            "Service ping completed for device %s - Service: %s, Host: %s",
            self.device_id,
            payload["service"],
            payload["host"],
        )

    def _print_timeout_tips(self, device_type: str, tips: tuple[str, ...]) -> None:  # WHY: printer.
        """Print troubleshooting tips with device-type-specific banner text."""
        if device_type == "gateway":  # WHY: gateways get a dedicated header before their tips.
            print("\nTroubleshooting for SSR gateways:")  # WHY: contextual banner.
            remaining = tips  # WHY: keep the full tip list for gateway devices.
        else:  # WHY: non-gateway path uses first tip as a note and prints the rest as arrows.
            print(f"\nNote: {tips[0]}")  # WHY: elevate primary note before the arrow list.
            remaining = tips[1:]  # WHY: skip the first tip since it was printed above.
        for tip in remaining:  # WHY: emit each remaining tip as a bullet-style hint.
            print(f"-> {tip}")  # WHY: arrow prefix matches the existing UX style.

    def _display_timeout_results(self, payload: dict[str, Any]) -> None:  # WHY: timeout hint flow.
        """Display timeout guidance when websocket results are not received."""
        del payload  # WHY: payload unused after refactor; kept in signature for back-compat.
        print("\nNo Service Ping results received within timeout period.")  # WHY: primary message.
        if not self.device_info:  # WHY: bail out with a minimal log when we lack device metadata.
            logging.warning("Service ping timeout - no results received for device %s", self.device_id)
            return  # WHY: skip formatted guidance when we cannot identify device type.
        device_type = self.device_info.get("type", "unknown")  # WHY: drives tip table lookup.
        device_name = self.device_info.get("name", "Unknown Device")  # WHY: identify device.
        print(f"Device: {device_name} ({device_type})")  # WHY: identify device before tips.
        tips = _TROUBLESHOOTING_TIPS.get(device_type, _DEFAULT_TIPS)  # WHY: table fetch with fallback.
        self._print_timeout_tips(device_type, tips)  # WHY: helper prints correctly framed hints.
        logging.warning("Service ping timeout - no results received for device %s", self.device_id)

    def _cleanup(self) -> None:  # WHY: teardown helper called from execute's finally block.
        """Disconnect websocket transport and swallow cleanup exceptions."""
        try:  # WHY: cleanup must never raise into the menu loop.
            if self.websocket_manager is not None:  # WHY: only disconnect when transport exists.
                self.websocket_manager.disconnect()  # WHY: release the websocket connection.
                print("-> WebSocket connection closed")  # WHY: confirm teardown to operator.
        except Exception as error:  # WHY: log-and-swallow any disconnect exception.
            logging.warning("WebSocket cleanup error: %s", error)  # WHY: warn on cleanup failure.

    def _preflight(self) -> bool:  # WHY: execute uses this to prep site/device before running.
        """Perform site/device selection and device validation, returning readiness."""
        if not self._select_site_and_device():  # WHY: abort early when selection fails.
            return False
        if not self._fetch_device_info():  # WHY: abort early when device does not validate.
            return False
        return True  # WHY: workflow ready to proceed to discovery and prompts.

    def _prepare_payload(self) -> dict[str, Any]:  # WHY: execute uses this to build ping payload.
        """Discover tenants/services and prompt the user for the full payload."""
        self._fetch_all_tenants()  # WHY: populate tenant caches from mixin.
        self._fetch_all_services()  # WHY: populate service caches from mixin.
        all_tenants = self._build_combined_tenants()  # WHY: unified tenant list for prompt.
        all_services = self._build_combined_services()  # WHY: unified service list for prompt.
        print("\n" + "=" * 50)  # WHY: separator introduces configuration block.
        print("SERVICE PING CONFIGURATION")  # WHY: banner labels prompt block.
        print("=" * 50)  # WHY: trailing bar frames the banner.
        tenant = self._prompt_for_tenant(all_tenants)  # WHY: ask user for tenant choice.
        service = self._prompt_for_service(all_services)  # WHY: ask user for service choice.
        params = self._prompt_for_ping_parameters()  # WHY: collect host/count/size and node.
        payload = self._build_payload(service, tenant, params)  # WHY: assemble final API payload.
        self._display_configuration(payload)  # WHY: confirm the constructed payload to operator.
        return payload  # WHY: return payload for the actual dispatch phase.

    def _run_ping_flow(self, payload: dict[str, Any]) -> None:  # WHY: dispatch + wait + display.
        """Run the websocket setup, ping dispatch, wait, and result display phases."""
        print(f"\n-> Executing Service Ping on device {self.device_id}...")  # WHY: signal start.
        if not self._setup_websocket():  # WHY: abort if transport is unavailable.
            return
        session_id = self._execute_service_ping(payload)  # WHY: dispatch and capture session id.
        if not session_id:  # WHY: cannot wait when session id is missing.
            print("! No session ID received - cannot wait for results")  # WHY: explain abort.
            return
        result = self._wait_for_results(session_id)  # WHY: block until result or timeout.
        self._display_results(result, payload)  # WHY: format outcome for operator.

    def _run_workflow(self) -> None:  # WHY: consolidated workflow body for the execute try block.
        """Run the full service ping workflow inside a single guarded call."""
        if not self._preflight():  # WHY: abort when selection or validation fails.
            return
        payload = self._prepare_payload()  # WHY: build ping payload from discovery and prompts.
        self._run_ping_flow(payload)  # WHY: dispatch payload, wait, and display results.

    def execute(self) -> None:  # WHY: menu 120 entry point orchestrating the workflow.
        """Run the complete service ping workflow for menu operation 120."""
        logging.debug("ENTER: ServicePingManager.execute")  # WHY: trace lifecycle boundary.
        if self.debug_mode:  # WHY: only emit debug banner when the flag is set.
            print("[DEBUG] Starting Service Ping via WebSocket operation...")  # WHY: user-visible.
            print(f"[DEBUG] Command line args: {sys.argv}")  # WHY: record invocation context.
        try:  # WHY: wrap workflow so cleanup always runs even on failure.
            self._run_workflow()  # WHY: single call keeps this method within block/CC limits.
        except KeyboardInterrupt:  # WHY: operator abort is a normal termination path.
            print("\nOperation cancelled by user")  # WHY: acknowledge cancellation.
            logging.info("Service ping operation cancelled by user")  # WHY: log the cancel path.
        except Exception as error:  # WHY: log and surface any unexpected workflow failure.
            print(f"Error during Service Ping operation: {error}")  # WHY: user-visible error.
            logging.error("Service ping error: %s", error)  # WHY: log for post-mortem.
        finally:  # WHY: always run cleanup regardless of success or failure.
            self._cleanup()  # WHY: teardown transport and swallow disconnect errors.
            logging.debug("EXIT: ServicePingManager.execute")  # WHY: trace lifecycle boundary.

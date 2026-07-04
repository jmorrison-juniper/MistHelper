"""Service ping manager extracted from MistHelper.py."""

from __future__ import annotations

import logging
import sys
from typing import Any

from src.websocket.service_ping_discovery import (
    ServicePingDiscoveryDependencies,
    ServicePingDiscoveryMixin,
    configure_service_ping_discovery_dependencies,
)

apisession: Any = None
mistapi: Any = None
PromptUtils: Any = None
InputUtils: Any = None
WebSocketManager: Any = None
is_debug_mode_fn: Any = None
APITenantFetchUtils: Any = None
ConfigUtils: Any = None
APIFetchUtils: Any = None


def configure_service_ping_manager_dependencies(
    *,
    apisession_dependency: Any,
    mistapi_dependency: Any,
    prompt_utils: Any,
    input_utils: Any,
    websocket_manager_class: Any,
    is_debug_mode: Any,
    api_tenant_fetch_utils: Any,
    config_utils: Any,
    api_fetch_utils: Any,
) -> None:
    """Configure runtime dependencies for the extracted service ping manager."""
    global apisession
    global mistapi
    global PromptUtils
    global InputUtils
    global WebSocketManager
    global is_debug_mode_fn
    global APITenantFetchUtils
    global ConfigUtils
    global APIFetchUtils

    apisession = apisession_dependency
    mistapi = mistapi_dependency
    PromptUtils = prompt_utils
    InputUtils = input_utils
    WebSocketManager = websocket_manager_class
    is_debug_mode_fn = is_debug_mode
    APITenantFetchUtils = api_tenant_fetch_utils
    ConfigUtils = config_utils
    APIFetchUtils = api_fetch_utils

    configure_service_ping_discovery_dependencies(
        ServicePingDiscoveryDependencies(
            apisession=apisession_dependency,
            mistapi=mistapi_dependency,
            api_tenant_fetch_utils=api_tenant_fetch_utils,
            config_utils=config_utils,
            api_fetch_utils=api_fetch_utils,
            input_utils=input_utils,
        )
    )


class ServicePingManager(ServicePingDiscoveryMixin):
    """Manager class for SSR Service Ping operations via WebSocket."""

    DEFAULT_HOST = "8.8.8.8"
    DEFAULT_COUNT = 4
    DEFAULT_SIZE = 56
    MIN_SIZE = 56
    MAX_SIZE = 65535
    DEFAULT_TENANT = "testing-tools"
    DEFAULT_SERVICE = "web-session"

    def __init__(self) -> None:
        """Initialize manager state and discovery caches."""
        self.debug_mode = bool(is_debug_mode_fn()) if is_debug_mode_fn else False
        self.site_id: str | None = None
        self.device_id: str | None = None
        self.device_info: dict[str, Any] | None = None
        self.websocket_manager: Any | None = None

        self.org_tenants: list[str] = []
        self.site_tenants: list[str] = []
        self.policy_tenants: list[str] = []
        self.template_tenants: list[str] = []
        self.device_tenants: list[str] = []

        self.org_services: list[dict[str, Any]] = []
        self.org_service_names: list[str] = []
        self.device_services: list[str] = []

    def _debug_print(self, message: str) -> None:
        """Print debug message when debug mode is enabled."""
        if self.debug_mode:
            print(f"[DEBUG] {message}")

    def _select_site_and_device(self) -> bool:
        """Prompt for site and gateway device selection."""
        self.site_id = PromptUtils.select_site_id_from_csv()
        if not self.site_id:
            print("! No site selected. Operation cancelled.")
            return False

        self._debug_print(f"Selected site_id = {self.site_id}")

        self.device_id = PromptUtils.select_device_id_from_inventory(self.site_id, device_type="gateway")
        if not self.device_id:
            print("! No gateway devices found or selected. Service Ping requires an SSR gateway.")
            return False

        self._debug_print(f"Selected device_id = {self.device_id}")
        return True

    def _fetch_device_info(self) -> bool:
        """Fetch target device information and validate it for service ping."""
        try:
            logging.info("Fetching gateway device details for site %s and device %s", self.site_id, self.device_id)
            raw_data = mistapi.api.v1.sites.devices.listSiteDevices(apisession, self.site_id, type="gateway").data
            logging.debug("Retrieved %d gateway devices for site %s", len(raw_data or []), self.site_id)
            self.device_info = next((device for device in raw_data if device.get("id") == self.device_id), None)
            logging.debug("Device lookup complete for %s, found=%s", self.device_id, self.device_info is not None)
        except Exception as error:
            logging.warning("Could not retrieve device details: %s", error)
            self._debug_print(f"Device details error: {error}")
            return self._confirm_unknown_device()

        if not self.device_info:
            return self._confirm_unknown_device()

        return self._validate_device_type()

    def _validate_device_type(self) -> bool:
        """Validate the chosen device type and warn when not a gateway."""
        if self.device_info is None:
            return self._confirm_unknown_device()

        device_type = self.device_info.get("type", "unknown")
        device_model = self.device_info.get("model", "unknown")

        self._debug_print(f"Device type: {device_type}, model: {device_model}")

        if device_type == "gateway":
            print(f"!? SSR Gateway detected (Model: {device_model})")
            print("   -> Service Ping allows ping packets to follow service-specific paths")
            return True

        type_messages = {"ap": "Access Point", "switch": "Switch"}
        device_label = type_messages.get(device_type, "Unknown device type")
        print(f"!? WARNING: {device_label} detected (Model: {device_model})")
        print("   -> Service Ping is designed for SSR gateways")
        return self._confirm_proceed()

    def _confirm_unknown_device(self) -> bool:
        """Prompt before continuing when device type cannot be determined."""
        print("!? Cannot determine device type - proceeding with caution")
        print("   -> Service Ping is designed for SSR gateways")
        return self._confirm_proceed()

    def _confirm_proceed(self) -> bool:
        """Prompt user to confirm proceeding on non-optimal device types."""
        choice = (
            InputUtils.safe_input(
                "   -> Continue anyway? (y/N): ",
                context="service_ping_continue",
            )
            .strip()
            .lower()
        )
        if choice != "y":
            print("Operation cancelled.")
            return False
        return True

    def _setup_websocket(self) -> bool:
        """Connect and subscribe websocket transport for command results."""
        self.websocket_manager = WebSocketManager(apisession)

        if not self.websocket_manager.connect():
            print("! Failed to establish WebSocket connection")
            return False

        self._debug_print("WebSocket connection established")

        command_channel = f"/sites/{self.site_id}/devices/{self.device_id}/cmd"
        if not self.websocket_manager.subscribe_to_channel(command_channel):
            print("! Failed to subscribe to device command channel")
            return False

        self._debug_print(f"Subscribed to channel: {command_channel}")
        print("-> WebSocket connected and subscribed")

        print("-> Waiting for subscription confirmation...")
        if not self.websocket_manager.wait_for_subscription_confirmation(command_channel, timeout_seconds=15):
            print("! Subscription confirmation not received within timeout")
            print("! Proceeding anyway, but results may not be received")
        else:
            print("-> Subscription confirmed")

        return True

    def _execute_service_ping(self, payload: dict[str, Any]) -> str | None:
        """Issue the Mist API service-ping request and return session ID."""
        print("-> Issuing Service Ping command...")
        self._debug_print(f"Service ping payload being sent: {payload}")
        logging.info("Sending service ping via mistapi to device: %s", self.device_id)
        logging.info("Service ping payload: %s", payload)

        try:
            response = mistapi.api.v1.sites.devices.servicePingFromSsr(
                apisession,
                self.site_id,
                self.device_id,
                payload,
            )
            logging.info("Service ping mistapi response status: %s", response.status_code)
            logging.info("Service ping mistapi response data: %s", response.data)

            self._debug_print(f"mistapi Response Status = {response.status_code}")
            self._debug_print(f"mistapi Response Data = {response.data}")

            if response.status_code != 200:
                print(f"Failed to issue Service Ping command. Status {response.status_code}: {response.data}")
                logging.error("Service ping failed - status %s: %s", response.status_code, response.data)
                return None

            session_id = response.data.get("session", "")
            if session_id:
                short_id = session_id[:8] + "..." if len(session_id) > 8 else session_id
                print(f"-> Service Ping command issued (session: {short_id})")
                self._debug_print(f"Full session ID: {session_id}")
            else:
                print("-> Service Ping command issued (no session ID returned)")

            return session_id or None
        except Exception as error:
            print(f"Error issuing Service Ping command via mistapi: {error}")
            logging.error("Service ping error: %s", error)
            self._debug_print(f"mistapi exception details: {type(error).__name__}: {error}")
            return None

    def _wait_for_results(self, session_id: str) -> dict[str, Any] | None:
        """Wait for websocket command results with device-type-specific timeout."""
        print("-> Waiting for Service Ping results...")
        self._debug_print(f"Full session ID = {session_id}")
        self._debug_print("Starting to wait for WebSocket results...")

        if self.websocket_manager is None:
            return None

        if self.device_info and self.device_info.get("type") == "gateway":
            timeout_seconds = 45
            activity_timeout = 5
            print("   -> Using extended timeout for SSR gateway (45s total, 5s activity)")
        else:
            timeout_seconds = 30
            activity_timeout = 3

        result = self.websocket_manager.wait_for_command_result(
            session_id,
            timeout_seconds=timeout_seconds,
            activity_timeout_seconds=activity_timeout,
        )

        self._debug_print(f"wait_for_command_result returned: {result is not None}")
        if result:
            self._debug_print(f"Result keys: {list(result.keys())}")
        return result

    def _display_results(self, result: dict[str, Any] | None, payload: dict[str, Any]) -> None:
        """Display success or timeout result output."""
        if result:
            self._display_success_results(result, payload)
        else:
            self._display_timeout_results(payload)

    def _display_success_results(self, result: dict[str, Any], payload: dict[str, Any]) -> None:
        """Display successful service ping results."""
        print("\n" + "=" * 60)
        print("SERVICE PING RESULTS:")
        print("=" * 60)

        if self.device_info is not None:
            self._display_device_context(payload)

        raw_output = result.get("raw", "")
        if raw_output:
            print("PING OUTPUT:")
            print("-" * 40)
            print(raw_output)

        parsed_output = result.get("Output", "")
        if parsed_output and parsed_output != raw_output:
            print("\nPARSED OUTPUT:")
            print("-" * 40)
            print(parsed_output)

        if not raw_output and not parsed_output:
            print("No output data received")
            if self.device_info and self.device_info.get("type") != "gateway":
                self._display_non_gateway_troubleshooting()

        print("=" * 60)
        self._log_success(payload)

    def _display_device_context(self, payload: dict[str, Any]) -> None:
        """Display device identity/context in the results section."""
        if self.device_info is None:
            return
        device_type = self.device_info.get("type", "unknown")
        device_model = self.device_info.get("model", "unknown")
        device_name = self.device_info.get("name", "Unknown Device")

        print(f"Device: {device_name} ({str(device_type).upper()}: {device_model})")
        print(f"Service: {payload['service']} -> Host: {payload['host']}")

        if device_type == "gateway":
            print("Note: Service-specific routing path used for ping packets")
        else:
            print("Note: Device may not fully support service ping functionality")

        print("-" * 60)

    def _display_non_gateway_troubleshooting(self) -> None:
        """Display guidance for non-gateway devices with no result output."""
        print("\nTroubleshooting for non-gateway devices:")
        print("-> Service Ping is designed specifically for SSR gateways")
        print("-> Try using regular ping (Menu 87) instead")
        print("-> Verify device supports service ping functionality")

    def _log_success(self, payload: dict[str, Any]) -> None:
        """Log successful completion summary."""
        if self.device_info:
            device_name = self.device_info.get("name", "Unknown Device")
            device_type = self.device_info.get("type", "unknown")
            logging.info(
                "Service ping completed for %s (%s) - Service: %s, Host: %s",
                device_name,
                device_type,
                payload["service"],
                payload["host"],
            )
        else:
            logging.info(
                "Service ping completed for device %s - Service: %s, Host: %s",
                self.device_id,
                payload["service"],
                payload["host"],
            )

    def _display_timeout_results(self, payload: dict[str, Any]) -> None:
        """Display timeout guidance when websocket results are not received."""
        print("\nNo Service Ping results received within timeout period.")

        if not self.device_info:
            logging.warning("Service ping timeout - no results received for device %s", self.device_id)
            return

        device_type = self.device_info.get("type", "unknown")
        device_name = self.device_info.get("name", "Unknown Device")
        print(f"Device: {device_name} ({device_type})")

        troubleshooting = {
            "gateway": [
                "Verify service name is valid for this SSR",
                "Check if host is reachable through the specified service",
                "Confirm SSR routing configuration for the service",
                "Try with a different service name",
            ],
            "switch": [
                "Switches typically do not support service ping",
                "Try using regular ping (Menu 87) for basic connectivity",
                "Service ping is an SSR-specific feature",
            ],
            "ap": [
                "Access Points do not support service ping",
                "Try using regular ping (Menu 87) for basic connectivity",
                "Service ping is an SSR-specific feature",
            ],
        }

        tips = troubleshooting.get(
            device_type,
            [
                "Service ping is designed for SSR gateways",
                "Try using regular ping (Menu 87) for basic connectivity",
            ],
        )

        if device_type == "gateway":
            print("\nTroubleshooting for SSR gateways:")
        else:
            print(f"\nNote: {tips[0]}")
            tips = tips[1:]

        for tip in tips:
            print(f"-> {tip}")

        logging.warning("Service ping timeout - no results received for device %s", self.device_id)

    def _cleanup(self) -> None:
        """Disconnect websocket transport and swallow cleanup exceptions."""
        try:
            if self.websocket_manager is not None:
                self.websocket_manager.disconnect()
                print("-> WebSocket connection closed")
        except Exception as error:
            logging.warning("WebSocket cleanup error: %s", error)

    def execute(self) -> None:
        """Run the complete service ping workflow for menu operation 120."""
        logging.debug("ENTER: ServicePingManager.execute")

        if self.debug_mode:
            print("[DEBUG] Starting Service Ping via WebSocket operation...")
            print(f"[DEBUG] Command line args: {sys.argv}")

        try:
            if not self._select_site_and_device():
                return
            if not self._fetch_device_info():
                return

            self._fetch_all_tenants()
            self._fetch_all_services()

            all_tenants = self._build_combined_tenants()
            all_services = self._build_combined_services()

            print("\n" + "=" * 50)
            print("SERVICE PING CONFIGURATION")
            print("=" * 50)

            tenant = self._prompt_for_tenant(all_tenants)
            service = self._prompt_for_service(all_services)
            params = self._prompt_for_ping_parameters()

            payload = self._build_payload(service, tenant, params)
            self._display_configuration(payload)

            print(f"\n-> Executing Service Ping on device {self.device_id}...")
            if not self._setup_websocket():
                return

            session_id = self._execute_service_ping(payload)
            if not session_id:
                print("! No session ID received - cannot wait for results")
                return

            result = self._wait_for_results(session_id)
            self._display_results(result, payload)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            logging.info("Service ping operation cancelled by user")
        except Exception as error:
            print(f"Error during Service Ping operation: {error}")
            logging.error("Service ping error: %s", error)
        finally:
            self._cleanup()
            logging.debug("EXIT: ServicePingManager.execute")

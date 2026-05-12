"""WebSocket device commands: MAC table retrieval via Mist API WebSocket stream."""

from __future__ import annotations

import logging
import sys
from typing import Any

import requests

from src.websocket.context import WebSocketCmdDeps
from src.websocket.manager import (
    WebSocketManager,
    check_mist_credentials,
    cleanup_ws_connection,
    dump_ws_debug_state,
    get_mist_credentials,
    log_ws_error,
    select_ws_site,
)


class WebSocketCommands:
    """WebSocket Commands Class for Mist API device operations.

    This class organizes all WebSocket-based device command functions following
    the agents guide requirement that "All features, or helpers need to live
    under the appropriately titled/named 'Class's for code clarity and organization."

    All methods are static since they don't require instance state and can be
    called directly from menu actions.

    SECURITY: All methods use authenticated WebSocket connections with session-based
    command demultiplexing for concurrent command safety.
    """

    @staticmethod
    def show_mac_table(deps: WebSocketCmdDeps) -> None:  # noqa: C901, PLR0912, PLR0915  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        """Execute show MAC table command on a switch device via WebSocket.

        MAC tables are a Layer 2 switching feature and are only meaningful on switches.
        Routers/gateways operate at Layer 3 and typically don't maintain MAC tables.

        Follows the documented Mist API pattern:
        1. Connect to WebSocket
        2. Subscribe to device command channel
        3. Issue POST show_mac_table command
        4. Await results via WebSocket stream

        SECURITY: Uses authenticated WebSocket connection with session-based
        command demultiplexing for concurrent command safety.
        """
        logging.info("Menu #5: Starting WebSocket show MAC table operation")
        # Check for debug mode from command line arguments
        debug_mode = "--debug" in sys.argv or "-d" in sys.argv

        if debug_mode:
            logging.getLogger().setLevel(logging.DEBUG)
            print("[DEBUG] DEBUG MODE ENABLED")

        logging.debug("ENTER: show_mac_table_websocket")

        try:
            # Interactive site selection
            site_id = select_ws_site(deps, debug_mode)
            if site_id is None:
                return

            # Get device selection - MAC table is a Layer 2 switching feature
            print("-> MAC table is available on switches (Layer 2 devices)")
            print("-> Routers/gateways operate at Layer 3 and typically don't maintain MAC tables")
            print("-> APs forward wireless traffic but don't maintain traditional MAC tables")
            device_id = deps.select_device_fn(site_id, device_type="switch")
            if not device_id:
                print("! No switch device selected. MAC table command requires Layer 2 switching devices.")
                print("! Only switches maintain MAC address learning tables for Ethernet forwarding.")
                return

            if debug_mode:
                print(f"[DEBUG] Selected device_id = {device_id}")

            print(f"\n-> Executing show MAC table on device {device_id}...")
            print("-> Establishing WebSocket connection...")

            # Initialize WebSocket manager and connect+subscribe in one step
            websocket_manager = WebSocketManager(deps.apisession)
            if not websocket_manager.connect_and_subscribe(site_id, device_id, debug_mode):
                return

            # Issue show MAC table command via REST API
            mac_table_payload: dict[str, Any] = {}  # show_mac_table typically doesn't require additional parameters

            print("-> Issuing show MAC table command...")
            logging.debug(f"MAC table payload: {mac_table_payload}")

            if debug_mode:
                print(f"[DEBUG] MAC table payload = {mac_table_payload}")

            # Get authentication details for direct HTTP request
            mist_host, mist_apitoken = get_mist_credentials(deps.apisession)
            if not check_mist_credentials(websocket_manager, mist_host, mist_apitoken, debug_mode):
                return

            # Make direct POST request to trigger show MAC table
            mac_table_url = f"https://{mist_host}/api/v1/sites/{site_id}/devices/{device_id}/show_mac_table"
            headers = {"Authorization": f"Token {mist_apitoken}", "Content-Type": "application/json"}

            if debug_mode:
                print(f"[DEBUG] POST URL = {mac_table_url}")
                print("[DEBUG] Headers = {'Authorization': 'Token [REDACTED]', 'Content-Type': 'application/json'}")

            mac_table_response = requests.post(mac_table_url, headers=headers, json=mac_table_payload, timeout=30)

            if debug_mode:
                print(f"[DEBUG] HTTP Response Status = {mac_table_response.status_code}")
                print(f"[DEBUG] HTTP Response Body = {mac_table_response.text}")

            if mac_table_response.status_code != 200:
                print(f"! Failed to issue show MAC table command: {mac_table_response.status_code}")
                print(f"! Response: {mac_table_response.text}")
                websocket_manager.disconnect()
                return

            # Extract session ID from response
            response_data = mac_table_response.json()
            session_id = response_data.get("session")
            if not session_id:
                print("! No session ID returned from show MAC table command")
                websocket_manager.disconnect()
                return

            print(f"-> Show MAC table command issued (session: {session_id[:8]}...)")
            print("-> Waiting for MAC table results...")

            if debug_mode:
                print(f"[DEBUG] Full session ID = {session_id}")
                print("[DEBUG] Starting to wait for WebSocket results...")

            # Wait for MAC table results via WebSocket (longer timeout for potentially large tables)
            mac_table_result = websocket_manager.wait_for_command_result(session_id, timeout_seconds=60)

            if debug_mode:
                print(f"[DEBUG] wait_for_command_result returned: {mac_table_result is not None}")
                if mac_table_result:
                    print(f"[DEBUG] Result keys: {list(mac_table_result.keys())}")

            if mac_table_result:
                print("\n" + "=" * 60)
                print("MAC TABLE RESULTS:")
                print("=" * 60)

                # Display raw output (this is where MAC table results come according to documentation)
                raw_output = mac_table_result.get("raw", "")
                if raw_output:
                    print("RAW OUTPUT:")
                    print("-" * 40)
                    print(raw_output)

                # Display any other output fields that might be present
                output_fields = mac_table_result.get("Output", "")
                if output_fields and output_fields != raw_output:
                    print("\nOTHER OUTPUT:")
                    print("-" * 40)
                    print(output_fields)

                # Show all available fields for debugging
                available_fields = [key for key in mac_table_result.keys() if key not in ["raw", "Output", "session"]]
                if available_fields:
                    print(f"\nOTHER AVAILABLE FIELDS: {available_fields}")
                    for field in available_fields:
                        field_value = mac_table_result.get(field)
                        if field_value:
                            print(f"{field}: {field_value}")

                if not raw_output and not output_fields:
                    print("No output data received")
                    print(f"Available result keys: {list(mac_table_result.keys())}")

                print("=" * 60)

                # Log the successful operation
                logging.info("WebSocket show MAC table completed successfully")

            else:
                print("! Timeout waiting for MAC table results")
                print("! This may indicate:")
                print("  - The device doesn't support MAC table commands (common for routers/Layer 3 devices)")
                print("  - The device is busy or not responding")
                print("  - Network connectivity issues")
                print("! Note: MAC tables are primarily a Layer 2 (switch) feature")
                logging.warning("WebSocket show MAC table operation timed out")
                dump_ws_debug_state(websocket_manager, debug_mode)

        except Exception as mac_table_error:
            error_message = f"WebSocket show MAC table operation failed: {mac_table_error}"
            log_ws_error(error_message, debug_mode)
            logging.debug("EXIT: show_mac_table_websocket - error")

        finally:
            # Always cleanup WebSocket connection
            cleanup_ws_connection(locals().get("websocket_manager"), debug_mode)
            logging.debug("EXIT: show_mac_table_websocket")

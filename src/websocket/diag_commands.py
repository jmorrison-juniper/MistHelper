"""WebSocket network diagnostic commands: ping and ARP via Mist API WebSocket stream."""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import traceback

import requests

from src.websocket.context import WebSocketCmdDeps
from src.websocket.manager import WebSocketManager


class WebSocketNetworkDiagCommands:
    """
    WebSocket Network Diagnostic Commands

    Handles ping, ARP, and service ping operations via WebSocket.
    Extracted from WebSocketCommands.
    """

    @staticmethod
    def ping_device(deps: WebSocketCmdDeps) -> None:  # noqa: C901, PLR0912, PLR0915
        """
        Execute ping command on a network device via WebSocket.

        Follows the documented Mist API pattern:
        1. Connect to WebSocket
        2. Subscribe to device command channel
        3. Issue POST ping command
        4. Await results via WebSocket stream

        SECURITY: Uses authenticated WebSocket connection with session-based
        command demultiplexing for concurrent command safety.
        """
        logging.info("Starting WebSocket ping operation...")

        # Check for debug mode from command line args
        debug_mode = "--debug" in sys.argv or "-d" in sys.argv

        if debug_mode:
            logging.getLogger().setLevel(logging.DEBUG)
            print("[DEBUG] DEBUG MODE ENABLED")

        logging.info("Starting WebSocket ping operation...")
        logging.debug("ENTER: ping_device_websocket")

        try:
            # Interactive site and device selection
            site_id = deps.select_site_fn()
            if not site_id:
                print("! No site selected. Operation cancelled.")
                return

            if debug_mode:
                print(f"[DEBUG] Selected site_id = {site_id}")

            # Get device selection
            device_id = deps.select_device_fn(site_id, device_type="all")
            if not device_id:
                print("! No device selected. Operation cancelled.")
                return

            if debug_mode:
                print(f"[DEBUG] Selected device_id = {device_id}")

            # Get ping target from user (default to 8.8.8.8)
            target_input = deps.safe_input_fn(
                "Enter the target hostname or IP address to ping (default: 8.8.8.8): ",
                context="websocket_ping",
            ).strip()
            target_host = target_input if target_input else "8.8.8.8"

            # Validate target host
            if not deps.validate_target_fn(target_host):
                print(f"! Invalid ping target: {target_host}")
                return

            if debug_mode:
                print(f"[DEBUG] Target host = {target_host}")

            # Get ping count (optional)
            ping_count_input = deps.safe_input_fn(
                "Enter number of ping packets (default: 4): ",
                context="websocket_ping",
            ).strip()
            ping_count = 4
            if ping_count_input:
                try:
                    ping_count = int(ping_count_input)
                    if ping_count < 1 or ping_count > 100:
                        print("! Ping count must be between 1 and 100. Using default: 4")
                        ping_count = 4
                except ValueError:
                    print("! Invalid ping count. Using default: 4")
                    ping_count = 4

            if debug_mode:
                print(f"[DEBUG] Ping count = {ping_count}")

            print(f"\n-> Executing ping to {target_host} on device {device_id}...")
            print(f"-> Ping count: {ping_count}")
            print("-> Establishing WebSocket connection...")

            # Initialize WebSocket manager
            websocket_manager = WebSocketManager(deps.apisession)

            if debug_mode:
                print("[DEBUG] WebSocketManager initialized")

            # Connect to WebSocket
            if not websocket_manager.connect():
                print("! Failed to establish WebSocket connection")
                return

            if debug_mode:
                print("[DEBUG] WebSocket connection established")

            # Subscribe to device command channel
            command_channel = f"/sites/{site_id}/devices/{device_id}/cmd"
            if not websocket_manager.subscribe_to_channel(command_channel):
                print("! Failed to subscribe to device command channel")
                websocket_manager.disconnect()
                return

            if debug_mode:
                print(f"[DEBUG] Subscribed to channel: {command_channel}")

            print("-> WebSocket connected and subscribed")

            # Wait a moment for subscription to be established
            time.sleep(1)

            # Issue ping command via REST API
            ping_payload = {"host": target_host, "count": ping_count}

            print("-> Issuing ping command...")
            logging.debug(f"Ping payload: {ping_payload}")

            if debug_mode:
                print(f"[DEBUG] Ping payload = {ping_payload}")

            # Get authentication details for direct HTTP request
            mist_host = getattr(deps.apisession, "host", None) or os.getenv("MIST_HOST")
            mist_apitoken = getattr(deps.apisession, "apitoken", None) or os.getenv("MIST_APITOKEN")

            if not mist_host or not mist_apitoken:
                print("! Mist host or API token not found in session or environment")
                websocket_manager.disconnect()
                return

            if debug_mode:
                print(f"[DEBUG] mist_host = {mist_host}")
                print(f"[DEBUG] API token length = {len(mist_apitoken) if mist_apitoken else 0}")

            # Make direct POST request to trigger ping
            ping_url = f"https://{mist_host}/api/v1/sites/{site_id}/devices/{device_id}/ping"
            headers = {"Authorization": f"Token {mist_apitoken}", "Content-Type": "application/json"}

            if debug_mode:
                print(f"[DEBUG] POST URL = {ping_url}")
                print("[DEBUG] Headers = {'Authorization': 'Token [REDACTED]', 'Content-Type': 'application/json'}")

            ping_response = requests.post(ping_url, headers=headers, json=ping_payload, timeout=30)

            if debug_mode:
                print(f"[DEBUG] HTTP Response Status = {ping_response.status_code}")
                print(f"[DEBUG] HTTP Response Body = {ping_response.text}")

            if ping_response.status_code != 200:
                print(f"! Failed to issue ping command: {ping_response.status_code}")
                print(f"! Response: {ping_response.text}")
                websocket_manager.disconnect()
                return

            # Extract session ID from response
            response_data = ping_response.json()
            session_id = response_data.get("session")
            if not session_id:
                print("! No session ID returned from ping command")
                websocket_manager.disconnect()
                return

            print(f"-> Ping command issued (session: {session_id[:8]}...)")
            print("-> Waiting for ping results...")

            if debug_mode:
                print(f"[DEBUG] Full session ID = {session_id}")
                print("[DEBUG] Starting to wait for WebSocket results...")

            # Wait for ping results via WebSocket
            ping_result = websocket_manager.wait_for_command_result(session_id, timeout_seconds=30)

            if debug_mode:
                print(f"[DEBUG] wait_for_command_result returned: {ping_result is not None}")
                if ping_result:
                    print(f"[DEBUG] Result keys: {list(ping_result.keys())}")

            if ping_result:
                print("\n" + "=" * 60)
                print("PING RESULTS:")
                print("=" * 60)

                # Display raw output (this is where ping results come according to documentation)
                raw_output = ping_result.get("raw", "")
                if raw_output:
                    print("RAW OUTPUT:")
                    print("-" * 40)
                    print(raw_output)

                # Display any other output fields that might be present
                output_fields = ping_result.get("Output", "")
                if output_fields and output_fields != raw_output:
                    print("\nOTHER OUTPUT:")
                    print("-" * 40)
                    print(output_fields)

                # Show all available fields for debugging
                available_fields = [key for key in ping_result.keys() if key not in ["raw", "Output", "session"]]
                if available_fields:
                    print(f"\nOTHER AVAILABLE FIELDS: {available_fields}")
                    for field in available_fields:
                        field_value = ping_result.get(field)
                        if field_value:
                            print(f"{field}: {field_value}")

                if not raw_output and not output_fields:
                    print("No output data received")
                    print(f"Available result keys: {list(ping_result.keys())}")

                print("=" * 60)

                # Log the successful operation
                logging.info(f"WebSocket ping completed successfully for {target_host}")

            else:
                print("! Timeout waiting for ping results")
                logging.warning("WebSocket ping operation timed out")

                if debug_mode:
                    print("[DEBUG] Checking WebSocket manager state...")
                    print(f"[DEBUG] Connected = {websocket_manager.connected}")
                    print(f"[DEBUG] Subscribed channels = {websocket_manager.subscribed_channels}")
                    with websocket_manager.results_lock:
                        print(f"[DEBUG] Pending results = {list(websocket_manager.command_results.keys())}")

        except Exception as ping_error:
            error_message = f"WebSocket ping operation failed: {ping_error}"
            print(f"! {error_message}")
            logging.error(error_message)

            if debug_mode:
                print("[DEBUG] Exception details:")
                traceback.print_exc()

            logging.debug("EXIT: ping_device_websocket - error")

        finally:
            # Always cleanup WebSocket connection
            try:
                websocket_manager_local = locals().get("websocket_manager")
                if websocket_manager_local is not None:
                    websocket_manager_local.disconnect()
                    print("-> WebSocket connection closed")

                    if debug_mode:
                        print("[DEBUG] WebSocket cleanup completed")
            except Exception as cleanup_error:
                logging.warning(f"WebSocket cleanup error: {cleanup_error}")

            logging.debug("EXIT: ping_device_websocket")

    @staticmethod
    def arp_device(deps: WebSocketCmdDeps) -> None:  # noqa: C901, PLR0912, PLR0915
        """
        Execute ARP command on a network device via WebSocket.

        Follows the documented Mist API pattern for ARP commands:
        1. Subscribe to WebSocket channel
        2. POST ARP command
        3. Receive results via WebSocket stream with session-based demultiplexing

        SECURITY: Uses authenticated WebSocket connection with session-based
        command demultiplexing for concurrent command safety.
        """
        logging.info("Starting WebSocket ARP operation...")
        logging.debug("ENTER: arp_device_websocket")

        debug_mode = "--debug" in sys.argv or "-d" in sys.argv

        if debug_mode:
            print("[DEBUG] Starting ARP via WebSocket operation...")

        try:
            # Interactive site and device selection
            site_id = deps.select_site_fn()
            if not site_id:
                print("! No site selected. Operation cancelled.")
                return

            if debug_mode:
                print(f"[DEBUG] Selected site_id = {site_id}")

            # Get device selection
            device_id = deps.select_device_fn(site_id, device_type="all")
            if not device_id:
                print("! No device selected. Operation cancelled.")
                return

            if debug_mode:
                print(f"[DEBUG] Selected device_id = {device_id}")

            # Get device details to check type and model for compatibility
            device_info = None
            try:
                rawdata = deps.list_devices_fn(deps.apisession, site_id, type="all").data
                device_info = next((device for device in rawdata if device.get("id") == device_id), None)

                if device_info:
                    device_type = device_info.get("type", "unknown")
                    device_model = device_info.get("model", "unknown")
                    device_name = device_info.get("name", f"Device {device_id[:8]}")

                    if debug_mode:
                        print(f"[DEBUG] Device type: {device_type}, model: {device_model}, name: {device_name}")

                    # Warn about device compatibility
                    if device_type == "switch":
                        print(f"!?  WARNING: Switch detected (Model: {device_model})")
                        print("   -> Switches may have limited WebSocket ARP support")
                        print("   -> Consider using SSH-based ARP commands instead")
                        print("   -> This operation may timeout or return limited results")

                        response = (
                            deps.safe_input_fn(
                                "   -> Continue anyway? (y/N): ",
                                context="websocket_arp",
                            )
                            .strip()
                            .lower()
                        )
                        if response not in ["y", "yes"]:
                            print("! Operation cancelled by user")
                            return

                    elif device_type == "gateway":
                        print(f"!? Gateway detected (Model: {device_model})")
                        print("   -> Gateways have good WebSocket ARP support")
                        print("   -> Results may differ from Access Points")

                    elif device_type == "ap":
                        print(f"!? Access Point detected (Model: {device_model})")
                        print("   -> Access Points have full WebSocket ARP support")

                    else:
                        print(f"? Unknown device type: {device_type} (Model: {device_model})")
                        print("   -> Proceeding with standard ARP command")

            except Exception as device_check_error:
                logging.warning(f"Could not verify device compatibility: {device_check_error}")
                if debug_mode:
                    print(f"[DEBUG] Device check failed: {device_check_error}")
                print("   -> Proceeding with standard ARP command")

            print(f"\n-> Executing ARP command on device {device_id}...")
            print("-> Establishing WebSocket connection...")

            if debug_mode:
                print("[DEBUG] WebSocketManager initialized")

            # Initialize WebSocket manager
            websocket_manager = WebSocketManager(deps.apisession)

            # Connect to WebSocket
            if not websocket_manager.connect():
                print("! Failed to establish WebSocket connection")
                return

            if debug_mode:
                print("[DEBUG] WebSocket connection established")

            # Subscribe to device command channel
            command_channel = f"/sites/{site_id}/devices/{device_id}/cmd"
            if not websocket_manager.subscribe_to_channel(command_channel):
                print("! Failed to subscribe to device command channel")
                websocket_manager.disconnect()
                return

            if debug_mode:
                print(f"[DEBUG] Subscribed to channel: {command_channel}")

            print("-> WebSocket connected and subscribed")

            # Wait a moment for subscription to be established
            time.sleep(1)

            print("-> Issuing ARP command...")

            # Get authentication details for direct HTTP request
            mist_host = getattr(deps.apisession, "host", None) or os.getenv("MIST_HOST")
            mist_apitoken = getattr(deps.apisession, "apitoken", None) or os.getenv("MIST_APITOKEN")

            if debug_mode:
                print(f"[DEBUG] mist_host = {mist_host}")
                print(f"[DEBUG] API token length = {len(mist_apitoken) if mist_apitoken else 'None'}")

            if not mist_host or not mist_apitoken:
                print("! Mist host or API token not found in session or environment")
                websocket_manager.disconnect()
                return

            # Make direct POST request to trigger ARP command
            arp_url = f"https://{mist_host}/api/v1/sites/{site_id}/devices/{device_id}/arp"
            headers = {"Authorization": f"Token {mist_apitoken}", "Content-Type": "application/json"}

            if debug_mode:
                print(f"[DEBUG] POST URL = {arp_url}")
                print("[DEBUG] Headers = {'Authorization': 'Token [REDACTED]', 'Content-Type': 'application/json'}")

            # ARP command typically doesn't need a payload body
            arp_response = requests.post(arp_url, headers=headers, json={}, timeout=30)

            if debug_mode:
                print(f"[DEBUG] HTTP Response Status = {arp_response.status_code}")
                print(f"[DEBUG] HTTP Response Body = {arp_response.text}")

            if arp_response.status_code != 200:
                print(f"! Failed to issue ARP command: {arp_response.status_code}")
                print(f"! Response: {arp_response.text}")
                websocket_manager.disconnect()
                return

            # Extract session ID from response
            response_data = arp_response.json()
            session_id = response_data.get("session")
            if not session_id:
                print("! No session ID returned from ARP command")
                websocket_manager.disconnect()
                return

            print(f"-> ARP command issued (session: {session_id[:8]}...)")
            print("-> Waiting for ARP results...")

            if debug_mode:
                print(f"[DEBUG] Full session ID = {session_id}")
                print("[DEBUG] Starting to wait for WebSocket results...")

            # Determine timeout based on device type
            if device_info:
                device_type = device_info.get("type", "unknown")
                if device_type == "switch":
                    # Switches often timeout, give them more time
                    timeout_seconds = 45
                    print("   -> Using extended timeout for switch (45 seconds)")
                elif device_type == "gateway":
                    # Gateways work but may be slower
                    timeout_seconds = 35
                    print("   -> Using extended timeout for gateway (35 seconds)")
                else:
                    # APs and unknown devices use standard timeout
                    timeout_seconds = 30
            else:
                timeout_seconds = 30

            # Wait for ARP results via WebSocket
            arp_result = websocket_manager.wait_for_command_result(session_id, timeout_seconds=timeout_seconds)

            if debug_mode:
                print(f"[DEBUG] wait_for_command_result returned: {arp_result is not None}")
                if arp_result:
                    print(f"[DEBUG] Result keys: {list(arp_result.keys())}")

            if arp_result:
                print("\n" + "=" * 60)
                print("ARP TABLE RESULTS:")
                print("=" * 60)

                # Add device-specific context
                if device_info:
                    device_type = device_info.get("type", "unknown")
                    device_model = device_info.get("model", "unknown")
                    device_name = device_info.get("name", "Unknown Device")

                    print(f"Device: {device_name} ({device_type.upper()}: {device_model})")

                    if device_type == "switch":
                        print("Note: Switch ARP data may show forwarding table or limited ARP information")
                    elif device_type == "gateway":
                        print("Note: Gateway ARP data may include routing information")
                    elif device_type == "ap":
                        print("Note: Access Point ARP data shows client connectivity information")

                    print("-" * 60)

                # Display raw output if available
                raw_output = arp_result.get("raw", "")
                if raw_output:
                    # Parse and display gateway data in table format if it's JSON
                    if device_info and device_info.get("type") == "gateway" and raw_output.strip().startswith("{"):
                        try:
                            # json is already imported globally
                            gateway_data = json.loads(raw_output)

                            if gateway_data.get("status") == "SUCCESS" and "rows" in gateway_data:
                                print("PARSED ARP TABLE:")
                                print("-" * 40)

                                # Get column headers
                                columns = gateway_data.get("columns", [])
                                if columns:
                                    # Create header row
                                    column_headers = [
                                        col.get("display_name", col.get("id", "Unknown")) for col in columns
                                    ]

                                    # Calculate column widths
                                    rows = gateway_data.get("rows", [])
                                    col_widths = []
                                    for idx, header in enumerate(column_headers):
                                        max_width = len(header)
                                        for row in rows:
                                            col_id = columns[idx].get("id", "")
                                            cell_value = str(row.get(col_id, ""))
                                            max_width = max(max_width, len(cell_value))
                                        col_widths.append(min(max_width + 2, 20))  # Cap at 20 chars

                                    # Print header
                                    header_line = " | ".join(
                                        header.ljust(col_widths[idx]) for idx, header in enumerate(column_headers)
                                    )
                                    print(header_line)
                                    print("-" * len(header_line))

                                    # Print data rows
                                    for row in rows:
                                        row_values = []
                                        for idx, col in enumerate(columns):
                                            col_id = col.get("id", "")
                                            cell_value = str(row.get(col_id, ""))
                                            # Truncate if too long
                                            if len(cell_value) > col_widths[idx] - 2:
                                                cell_value = cell_value[: col_widths[idx] - 5] + "..."
                                            row_values.append(cell_value.ljust(col_widths[idx]))
                                        print(" | ".join(row_values))

                                    print(f"\nTotal ARP Entries: {len(rows)}")

                                    # Also show raw for reference if debug mode
                                    if debug_mode:
                                        print("\nRAW JSON OUTPUT (Debug):")
                                        print("-" * 40)
                                        print(raw_output)
                                else:
                                    print("No column information available in gateway response")
                                    print("RAW OUTPUT:")
                                    print("-" * 40)
                                    print(raw_output)
                            else:
                                print("Gateway response format not recognized")
                                print("RAW OUTPUT:")
                                print("-" * 40)
                                print(raw_output)

                        except json.JSONDecodeError as json_error:
                            if debug_mode:
                                print(f"[DEBUG] Failed to parse gateway JSON: {json_error}")
                            print("Failed to parse gateway JSON output")
                            print("RAW OUTPUT:")
                            print("-" * 40)
                            print(raw_output)
                    else:
                        # For APs and other devices, show raw output
                        print("RAW OUTPUT:")
                        print("-" * 40)
                        print(raw_output)

                # Display parsed output if available
                parsed_output = arp_result.get("Output", "")
                if parsed_output and parsed_output != raw_output:
                    print("\nPARSED OUTPUT:")
                    print("-" * 40)
                    print(parsed_output)

                if not raw_output and not parsed_output:
                    print("No output data received")
                    if device_info and device_info.get("type") == "switch":
                        print("\nTroubleshooting for switches:")
                        print("-> Try using SSH-based commands instead")
                        print("-> Some switches require specific ARP command syntax")
                        print("-> WebSocket API may have limited switch support")

                print("=" * 60)

                # Log the successful operation with device context
                device_context = f"device {device_id}"
                if device_info:
                    device_context = f"{device_info.get('type', 'unknown')} {device_info.get('name', device_id[:8])}"
                logging.info(f"WebSocket ARP completed successfully for {device_context}")

            else:
                print("! Timeout waiting for ARP results")

                # Provide device-specific troubleshooting advice
                if device_info:
                    device_type = device_info.get("type", "unknown")
                    device_model = device_info.get("model", "unknown")

                    if device_type == "switch":
                        print(f"\nSwitch troubleshooting ({device_model}):")
                        print("-> Switches often have limited WebSocket ARP support")
                        print("-> Try using SSH-based 'show arp' commands instead")
                        print("-> Some switch models require specific command syntax")
                        print("-> Consider using Menu option for SSH device commands")
                    elif device_type == "gateway":
                        print(f"\nGateway troubleshooting ({device_model}):")
                        print("-> Try increasing timeout or checking network connectivity")
                        print("-> Gateway may require different ARP command format")
                    else:
                        print(f"\nGeneral troubleshooting ({device_type}):")
                        print("-> Check device connectivity and WebSocket support")
                        print("-> Some devices may require SSH-based commands")

                logging.warning("WebSocket ARP operation timed out")

        except Exception as arp_error:
            error_message = f"WebSocket ARP operation failed: {arp_error}"
            print(f"! {error_message}")
            logging.error(error_message)
            logging.debug("EXIT: arp_device_websocket - error")

        finally:
            # Always cleanup WebSocket connection
            try:
                websocket_manager_local = locals().get("websocket_manager")
                if websocket_manager_local is not None:
                    websocket_manager_local.disconnect()
                    print("-> WebSocket connection closed")
            except Exception as cleanup_error:
                logging.warning(f"WebSocket cleanup error: {cleanup_error}")

            logging.debug("EXIT: arp_device_websocket")

"""WebSocket Manager for Mist API real-time communications."""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import threading
import time
import traceback
from typing import Any

try:
    import websocket
except ImportError as _ws_err:
    raise ImportError("websocket-client is required but not installed. Run: pip install websocket-client") from _ws_err


def _is_debug_mode() -> bool:
    """Check if debug mode is enabled via command line arguments."""
    return "--debug" in sys.argv or "-d" in sys.argv


class _PerformanceMonitor:
    """Simple performance monitoring to detect hangs and infinite loops."""

    def __init__(self, name: str, max_iterations: int = 10000, log_interval: float = 5.0) -> None:
        self.name = name
        self.start_time = time.time()
        self.last_log_time = self.start_time
        self.iteration_count = 0
        self.max_iterations = max_iterations
        self.log_interval = log_interval

    def check_iteration(self) -> None:
        """Call this on each loop iteration to detect hangs."""
        self.iteration_count += 1
        current_time = time.time()
        if _is_debug_mode() and (current_time - self.last_log_time) >= self.log_interval:
            elapsed = current_time - self.start_time
            print(f"[PERF] {self.name}: {self.iteration_count} iterations in {elapsed:.1f}s")
            self.last_log_time = current_time
        if self.iteration_count > self.max_iterations:
            error_msg = f"CIRCUIT BREAKER: {self.name} exceeded {self.max_iterations} iterations!"
            print(f"[EMERGENCY] {error_msg}")
            logging.error(error_msg)
            raise RuntimeError(error_msg)

    def finish(self) -> None:
        """Call when loop completes normally."""
        elapsed = time.time() - self.start_time
        if _is_debug_mode():
            print(f"[PERF] {self.name} completed: {self.iteration_count} iterations in {elapsed:.1f}s")


def log_ws_error(error_message: str, debug_mode: bool) -> None:
    """Print and log a WebSocket operation error with optional debug traceback."""
    print(f"! {error_message}")
    logging.error(error_message)
    if debug_mode:
        print("[DEBUG] Exception details:")
        traceback.print_exc()


def cleanup_ws_connection(ws_manager: Any, debug_mode: bool = False) -> None:
    """Disconnect WebSocket manager and log cleanup, swallowing cleanup errors."""
    try:
        if ws_manager is not None:
            ws_manager.disconnect()
            print("-> WebSocket connection closed")
            if debug_mode:
                print("[DEBUG] WebSocket cleanup completed")
    except Exception as cleanup_error:
        logging.warning(f"WebSocket cleanup error: {cleanup_error}")


def get_mist_credentials(apisession: Any) -> tuple[str | None, str | None]:
    """Extract Mist host and API token from session or environment variables."""
    mist_host = getattr(apisession, "host", None) or os.getenv("MIST_HOST")
    mist_apitoken = getattr(apisession, "apitoken", None) or os.getenv("MIST_APITOKEN")
    return mist_host, mist_apitoken


def dump_ws_debug_state(ws_mgr: Any, debug_mode: bool) -> None:
    """Print WebSocket manager debug state when debug mode is active."""
    if debug_mode:
        print("[DEBUG] Checking WebSocket manager state...")
        print(f"[DEBUG] Connected = {ws_mgr.connected}")
        print(f"[DEBUG] Subscribed channels = {ws_mgr.subscribed_channels}")
        with ws_mgr.results_lock:
            print(f"[DEBUG] Pending results = {list(ws_mgr.command_results.keys())}")


def select_ws_site(deps: Any, debug_mode: bool) -> str | None:
    """Prompt for site selection, returning None and printing a message if cancelled."""
    site_id: str | None = deps.select_site_fn() or None
    if not site_id:
        print("! No site selected. Operation cancelled.")
        return None
    if debug_mode:
        print(f"[DEBUG] Selected site_id = {site_id}")
    return site_id


def check_mist_credentials(ws_mgr: Any, mist_host: str | None, mist_apitoken: str | None, debug_mode: bool) -> bool:
    """Validate Mist host and token; disconnect ws_mgr and return False if invalid."""
    if not mist_host or not mist_apitoken:
        print("! Mist host or API token not found in session or environment")
        if ws_mgr is not None:
            ws_mgr.disconnect()
        return False
    if debug_mode:
        print(f"[DEBUG] mist_host = {mist_host}")
        print(f"[DEBUG] API token length = {len(mist_apitoken) if mist_apitoken else 0}")
    return True


class WebSocketManager:
    """WebSocket Manager for Mist API real-time communications.

    This class handles WebSocket connections to the Mist API following the
    documented patterns: subscribe first, issue POST command, await results.

    SECURITY: WebSocket connections use authenticated sessions with proper
    credential handling and session-based command demultiplexing.
    """

    def __init__(self, mist_session: Any, mist_host: str | None = None) -> None:
        """Initialize WebSocket manager with Mist session.

        Args:
            mist_session: Authenticated Mist API session
            mist_host: Mist API host (if None, will get from session)
        """
        self.mist_session = mist_session
        self.mist_host = mist_host or getattr(mist_session, "host", None) or os.getenv("MIST_HOST", "api.mist.com")

        # Convert API host to WebSocket host
        assert self.mist_host is not None, "mist_host must be set"  # nosec B101
        websocket_host = self.mist_host.replace("api.", "api-ws.")
        self.websocket_url = f"wss://{websocket_host}/api-ws/v1/stream"
        self.websocket_connection: websocket.WebSocketApp | None = None
        self.logger = logging.getLogger(__name__)
        self.connected = False
        self.subscribed_channels: set[str] = set()
        self.confirmed_subscriptions: set[str] = set()

        # Results storage for command outputs
        self.command_results: dict[str, Any] = {}
        self.results_lock = threading.Lock()
        self.websocket_thread: threading.Thread | None = None

    def connect(self) -> bool:
        """Establish WebSocket connection with proper authentication.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Prepare authentication headers using session token
            mist_apitoken = getattr(self.mist_session, "apitoken", None) or os.getenv("MIST_APITOKEN")
            if not mist_apitoken:
                self.logger.error("No API token found in session or environment")
                return False

            self.logger.debug(f"WebSocket URL: {self.websocket_url}")
            self.logger.debug(f"Auth token configured (length: {len(mist_apitoken)} chars)")
            auth_header = f"Authorization: Token {mist_apitoken}"
            headers = [auth_header]

            # Create WebSocket connection
            self.websocket_connection = websocket.WebSocketApp(
                self.websocket_url,
                header=headers,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open,
            )

            # Start connection in background thread
            connection = self.websocket_connection
            self.websocket_thread = threading.Thread(target=connection.run_forever, daemon=True)
            self.websocket_thread.start()

            # Wait for connection to establish
            timeout_counter = 0
            while not self.connected and timeout_counter < 10:
                time.sleep(0.5)
                timeout_counter += 1
                if timeout_counter % 2 == 0:
                    self.logger.debug(f"WebSocket handshake waiting... ({timeout_counter * 0.5:.1f}s)")

            if self.connected:
                self.logger.info("WebSocket connection established successfully")
                return True
            else:
                self.logger.error("WebSocket connection timeout")
                return False

        except Exception as connection_error:
            self.logger.error(f"WebSocket connection failed: {connection_error}")
            return False

    def connect_and_subscribe(self, site_id: str, device_id: str, debug_mode: bool) -> bool:
        """Connect to WebSocket and subscribe to the device command channel.

        Handles initialization, connection, subscription, and a brief stabilization
        wait as a single atomic setup step used by all WebSocket command methods.

        Args:
            site_id (str): Mist site UUID.
            device_id (str): Mist device UUID.
            debug_mode (bool): Whether to print debug output.

        Returns:
            bool: True if connected and subscribed, False otherwise.
        """
        if debug_mode:
            print("[DEBUG] WebSocketManager initialized")

        if not self.connect():
            print("! Failed to establish WebSocket connection")
            return False

        if debug_mode:
            print("[DEBUG] WebSocket connection established")

        command_channel = f"/sites/{site_id}/devices/{device_id}/cmd"
        if not self.subscribe_to_channel(command_channel):
            print("! Failed to subscribe to device command channel")
            self.disconnect()
            return False

        if debug_mode:
            print(f"[DEBUG] Subscribed to channel: {command_channel}")

        print("-> WebSocket connected and subscribed")
        time.sleep(1)
        return True

    def subscribe_to_channel(self, channel_path: str) -> bool:
        """Subscribe to a WebSocket channel for receiving command outputs.

        Args:
            channel_path (str): Channel path (e.g., "/sites/{site_id}/devices/{device_id}/cmd")

        Returns:
            bool: True if subscription successful, False otherwise
        """
        if not self.connected:
            self.logger.error("Cannot subscribe: WebSocket not connected")
            return False

        try:
            subscription_message = {"subscribe": channel_path}

            if self.websocket_connection is not None:
                self.websocket_connection.send(json.dumps(subscription_message))
            self.subscribed_channels.add(channel_path)
            self.logger.debug(f"Subscribed to channel: {channel_path}")
            return True

        except Exception as subscription_error:
            self.logger.error(f"Channel subscription failed: {subscription_error}")
            return False

    def wait_for_subscription_confirmation(self, channel_path, timeout_seconds=10):  # type: ignore[no-untyped-def]
        """Wait for WebSocket subscription confirmation for a specific channel.

        Args:
            channel_path (str): Channel path to wait for confirmation
            timeout_seconds (int): Maximum time to wait for confirmation

        Returns:
            bool: True if confirmation received, False if timeout
        """
        start_time = time.time()

        debug_mode = getattr(self, "debug_mode", False) or os.getenv("DEBUG", "").lower() in ["true", "1", "yes"]

        if debug_mode:
            self.logger.debug(f"Waiting for subscription confirmation for: {channel_path}")
            print(f"[DEBUG] Waiting for subscription confirmation for: {channel_path}")

        while time.time() - start_time < timeout_seconds:
            # Check if subscription is confirmed
            if channel_path in self.confirmed_subscriptions:
                if debug_mode:
                    self.logger.debug(f"Subscription confirmed for: {channel_path}")
                    print(f"[DEBUG] Subscription confirmed for: {channel_path}")
                return True

            time.sleep(0.1)  # Small sleep to avoid busy waiting

        # Timeout reached
        if debug_mode:
            self.logger.debug(f"Timeout waiting for subscription confirmation: {channel_path}")
            print(f"[DEBUG] Timeout waiting for subscription confirmation: {channel_path}")
        self.logger.warning(f"Timeout waiting for subscription confirmation: {channel_path}")
        return False

    def wait_for_command_result(  # noqa: C901, PLR0912, PLR0915  # pylint: disable=too-many-locals,too-many-branches,too-many-statements,too-many-nested-blocks
        self,
        session_id: str,
        timeout_seconds: int = 30,
        activity_timeout_seconds: int | None = None,
    ) -> dict[str, Any] | None:
        """Wait for command result with specific session ID.

        For commands like ping that produce multiple output segments,
        this will collect all results until the command completes.

        Args:
            session_id (str): Session ID from command POST response
            timeout_seconds (int): Maximum time to wait for result
            activity_timeout_seconds (int): Seconds to wait after last message before considering complete

        Returns:
            dict: Complete command result data or None if timeout
        """
        debug_mode = _is_debug_mode()
        start_time = time.time()
        last_activity = time.time()
        last_message_count = 0  # Track number of messages to detect new activity

        # Reset MAC table completion cache for new sessions
        if hasattr(self, "_mac_expected_entries"):
            delattr(self, "_mac_expected_entries")

        # Use custom activity timeout if provided, otherwise default to 2 seconds
        activity_timeout = activity_timeout_seconds if activity_timeout_seconds is not None else 2
        check_count = 0
        last_debug_time = start_time
        performance_log_interval = 5.0  # Log performance every 5 seconds

        # Create performance monitor to detect infinite loops
        perf_monitor = _PerformanceMonitor(
            f"wait_for_command_result({session_id[:8]}...)", max_iterations=10000, log_interval=5.0
        )

        if debug_mode:
            self.logger.debug(f"Waiting for session {session_id} (timeout: {timeout_seconds}s)")
            self.logger.debug(f"Current time: {time.time()}")
            self.logger.debug(f"Activity timeout: {activity_timeout}s)")
            print(f"[DEBUG] Waiting for session {session_id} (timeout: {timeout_seconds}s)")
            print(f"[DEBUG] Current time: {time.time()}")
            print(f"[DEBUG] Activity timeout: {activity_timeout}s)")

        while time.time() - start_time < timeout_seconds:
            # Monitor for infinite loops
            perf_monitor.check_iteration()

            current_time = time.time()
            check_count += 1

            # Performance logging every 5 seconds in debug mode
            if debug_mode and (current_time - last_debug_time) >= performance_log_interval:
                elapsed = current_time - start_time
                self.logger.debug(f"Check #{check_count} at {elapsed:.1f}s - Still waiting for session {session_id}")
                self.logger.debug(f"Last activity: {current_time - last_activity:.1f}s ago")
                print(f"[PERF] Check #{check_count} at {elapsed:.1f}s - Still waiting for session {session_id}")
                print(f"[PERF] Last activity: {current_time - last_activity:.1f}s ago")
                with self.results_lock:
                    available_sessions = list(self.command_results.keys())
                    if session_id in self.command_results:
                        msg_count = len(self.command_results[session_id])
                        self.logger.debug(f"Found {msg_count} messages for our session")
                        print(f"[PERF] Found {msg_count} messages for our session")
                    else:
                        self.logger.debug(f"Our session not in results yet. Available: {available_sessions}")
                        print(f"[PERF] Our session not in results yet. Available: {available_sessions}")
                last_debug_time = current_time

            with self.results_lock:
                if session_id in self.command_results:
                    collected_output = self.command_results[session_id]
                    current_message_count = len(collected_output)

                    # Update last_activity only when NEW messages arrive
                    if current_message_count > last_message_count:
                        last_activity = time.time()
                        last_message_count = current_message_count
                        if debug_mode:
                            self.logger.debug(
                                f"New activity detected: {current_message_count} messages (+{current_message_count - (last_message_count - (current_message_count - last_message_count))}) "  # noqa: E501
                            )

                    if collected_output:
                        # Check ALL messages for completion indicators, not just the latest
                        all_raw_content = ""
                        for result in collected_output:
                            all_raw_content += result.get("raw", "")

                        latest_result = collected_output[-1]
                        latest_raw = latest_result.get("raw", "")

                        if debug_mode and check_count % 50 == 1:  # Debug every 50 checks (roughly 5 seconds)
                            self.logger.debug(f"Check #{check_count}, found {len(collected_output)} messages")
                            self.logger.debug(f"Latest raw (first 100 chars): {repr(latest_raw[:100])}")
                            self.logger.debug(f"Total content length: {len(all_raw_content)} chars")
                            print(f"[DEBUG] Check #{check_count}, found {len(collected_output)} messages")
                            print(f"[DEBUG] Latest raw (first 100 chars): {repr(latest_raw[:100])}")
                            print(f"[DEBUG] Total content length: {len(all_raw_content)} chars")
                            # For service ping debugging, show more content
                            if len(all_raw_content) > 0:
                                self.logger.debug(f"Service ping content sample: {repr(all_raw_content[:300])}")
                                print(f"[DEBUG] Service ping content sample: {repr(all_raw_content[:300])}")
                                if "bytes from" in all_raw_content.lower():
                                    self.logger.debug("Service ping: Found 'bytes from' pattern")
                                    print("[DEBUG] Service ping: Found 'bytes from' pattern")
                                if "seq=" in all_raw_content.lower():
                                    self.logger.debug("Service ping: Found 'seq=' pattern")
                                    print("[DEBUG] Service ping: Found 'seq=' pattern")
                                if "time=" in all_raw_content.lower():
                                    self.logger.debug("Service ping: Found 'time=' pattern")
                                    print("[DEBUG] Service ping: Found 'time=' pattern")

                        # Check if ANY of the collected content looks like a final command summary
                        # Ping completion indicators
                        ping_indicators = ["round-trip min/avg/max", "round-trip min/avg/max/stddev", "rtt min/avg/max"]
                        # Service ping completion indicators - SSR service ping specific patterns
                        service_ping_indicators = [
                            "service ping completed",  # Generic service ping completion
                            "service-ping",  # Service ping command reference
                            "packet transmitted",  # "10 packets transmitted"
                            "packets transmitted",  # Alternative format
                            "received",  # "10 received" - common in ping summaries
                            "packet loss",  # Alternative packet loss indicator
                            "transmission failure",  # Service ping specific failure
                            "service path",  # Service path reference
                            "tenant context",  # Tenant context completion
                            "service route",  # Service routing completion
                        ]
                        # ARP completion indicators - specific patterns from actual ARP output
                        arp_indicators = [
                            "total mac entries",  # "Total 31 MAC Entries."
                            "total flows:",  # "Total Flows:151"
                            "mac-flow hi-water",  # "Mac-Flow Hi-Water:2865"
                            "arp table",  # Generic ARP table reference
                            "no arp entries",  # Empty ARP table
                            "arp cache",  # ARP cache reference
                        ]
                        # Gateway-specific completion indicators (SSR gateways often have shorter output)
                        gateway_indicators = [
                            "connected routes",  # Gateway routing table
                            "total entries",  # Gateway route totals
                            "kernel routes",  # SSR kernel routing
                            "bgp routes",  # BGP routing information
                            "static routes",  # Static route information
                            "route table",  # Generic route table reference
                        ]
                        # Switch-specific completion indicators
                        switch_indicators = [
                            "learning table",  # Switch MAC learning
                            "fdb entries",  # Forwarding database
                            "vlan information",  # VLAN details
                            "port statistics",  # Port stats
                            "interface status",  # Interface information
                            "ethernet switching table",  # MAC table header
                            "entries, 40 learned",  # MAC table summary (specific count varies)
                            "entries,",  # Generic MAC table entry count
                            "learned",  # MAC learning completion
                        ]
                        # General completion indicators
                        general_indicators = ["command completed", "operation complete", "finished"]

                        all_indicators = (
                            ping_indicators
                            + service_ping_indicators
                            + arp_indicators
                            + gateway_indicators
                            + switch_indicators
                            + general_indicators
                        )
                        found_indicator = None

                        if (
                            debug_mode and check_count % 100 == 1
                        ):  # Debug indicator checking every 100 checks (roughly 10 seconds)
                            self.logger.debug(f"Checking {len(all_indicators)} completion indicators")
                            self.logger.debug(
                                f"Content sample for indicator check: {repr(all_raw_content.lower()[:150])}"
                            )
                            print(f"[DEBUG] Checking {len(all_indicators)} completion indicators")
                            print(f"[DEBUG] Content sample for indicator check: {repr(all_raw_content.lower()[:150])}")

                        for indicator in all_indicators:
                            # Skip generic indicators for MAC table commands to allow proper completion detection
                            if "ethernet switching table" in all_raw_content.lower() and indicator in [
                                "ethernet switching table",
                                "entries,",
                                "learned",
                            ]:
                                continue  # Let MAC table specific logic handle this
                            if indicator in all_raw_content.lower():
                                found_indicator = indicator
                                if debug_mode:
                                    self.logger.debug(f"FOUND completion indicator: '{indicator}'")
                                    print(f"[DEBUG] FOUND completion indicator: '{indicator}'")
                                break

                        # Alternative completion: look for "packet loss" followed by "round-trip" pattern (ping specific)  # noqa: E501
                        if not found_indicator and "packet loss" in all_raw_content.lower():
                            # Check if we have the complete statistics block
                            lines = all_raw_content.lower().split("\n")
                            for line in lines:
                                if "packet loss" in line and (
                                    "round-trip" in all_raw_content.lower() or "rtt" in all_raw_content.lower()
                                ):
                                    found_indicator = "complete statistics block"
                                    if debug_mode:
                                        self.logger.debug("FOUND ping statistics completion pattern")
                                        self.logger.debug(f"Packet loss line: {repr(line[:100])}")
                                        print("[DEBUG] FOUND ping statistics completion pattern")
                                        print(f"[DEBUG] Packet loss line: {repr(line[:100])}")
                                    break

                        # Service ping specific completion: look for individual ping responses with timing
                        if (
                            not found_indicator and len(collected_output) >= 3
                        ):  # Service ping typically has multiple responses
                            # Look for service ping patterns - individual responses with seq/ttl/time
                            service_ping_pattern_count = 0
                            if "seq=" in all_raw_content.lower() and (
                                "ttl=" in all_raw_content.lower() or "time=" in all_raw_content.lower()
                            ):
                                service_ping_pattern_count += 1
                            if "bytes from" in all_raw_content.lower():
                                service_ping_pattern_count += 1

                            if debug_mode and check_count % 200 == 1:  # Debug service ping patterns
                                self.logger.debug(
                                    f"Service ping pattern analysis: found {service_ping_pattern_count} service ping indicators"  # noqa: E501
                                )
                                print(
                                    f"[DEBUG] Service ping pattern analysis: found {service_ping_pattern_count} service ping indicators"  # noqa: E501
                                )
                                if "seq=" in all_raw_content.lower():
                                    self.logger.debug("Found seq= pattern in service ping output")
                                    print("[DEBUG] Found seq= pattern in service ping output")
                                if "bytes from" in all_raw_content.lower():
                                    self.logger.debug("Found 'bytes from' pattern in service ping output")
                                    print("[DEBUG] Found 'bytes from' pattern in service ping output")

                            # If we see service ping patterns and have been collecting for reasonable time
                            if service_ping_pattern_count >= 2:
                                # For service ping, if we have multiple ping responses and some idle time, consider complete  # noqa: E501
                                if (
                                    time.time() - last_activity > 3
                                ):  # Wait 3 seconds after last response for service ping
                                    found_indicator = "service ping pattern detected"
                                    if debug_mode:
                                        self.logger.debug(
                                            f"FOUND service ping completion: {service_ping_pattern_count} patterns detected"  # noqa: E501
                                        )
                                        self.logger.debug(f"Service ping idle time: {time.time() - last_activity:.1f}s")
                                        print(
                                            f"[DEBUG] FOUND service ping completion: {service_ping_pattern_count} patterns detected"  # noqa: E501
                                        )
                                        print(f"[DEBUG] Service ping idle time: {time.time() - last_activity:.1f}s")

                        # Alternative service ping completion: check for count-based completion
                        if not found_indicator and len(collected_output) >= 5:  # Reasonable number of responses
                            # Count individual ping responses in format: "64 bytes from X.X.X.X: seq=N ttl=N time=N ms"
                            ping_response_count = all_raw_content.lower().count("bytes from")
                            if (
                                ping_response_count >= 5 and time.time() - last_activity > 2
                            ):  # Have responses and idle time
                                found_indicator = f"count-based completion ({ping_response_count} responses)"
                                if debug_mode:
                                    self.logger.debug(
                                        f"FOUND count-based service ping completion: {ping_response_count} responses"
                                    )
                                    self.logger.debug(
                                        f"Idle time since last response: {time.time() - last_activity:.1f}s"
                                    )
                                    print(
                                        f"[DEBUG] FOUND count-based service ping completion: {ping_response_count} responses"  # noqa: E501
                                    )
                                    print(f"[DEBUG] Idle time since last response: {time.time() - last_activity:.1f}s")

                        # MAC table completion: detect when table is complete and device stops sending
                        if not found_indicator and (
                            "ethernet switching table" in all_raw_content.lower()
                            or "thernet switching table" in all_raw_content.lower()
                        ):
                            # Search for "Ethernet switching table : XXX entries" pattern in reassembled buffer
                            # Look for pattern like "Ethernet switching table : 44 entries" (handles chunking)
                            table_pattern = r"ethernet switching table\s*:\s*(\d+)\s+entries"
                            match = re.search(table_pattern, all_raw_content.lower())

                            if match:
                                entry_count = int(match.group(1))

                                # First check: if we're getting the same message content repeatedly (completion signal)
                                if len(collected_output) >= 5:
                                    # Get the last 5 message contents
                                    last_messages = [msg.get("raw", "") for msg in collected_output[-5:]]
                                    # If all 5 are identical (and not empty), the command has finished
                                    if len(set(last_messages)) == 1 and last_messages[0].strip():
                                        found_indicator = f"mac table completion (detected {len(last_messages)} repeated identical messages)"  # noqa: E501
                                        if debug_mode:
                                            self.logger.debug(
                                                f"FOUND MAC table completion: {len(last_messages)} repeated identical messages detected"  # noqa: E501
                                            )
                                            self.logger.debug(f"Repeated message: {repr(last_messages[0][:100])}")
                                            print(
                                                f"[DEBUG] FOUND MAC table completion: {len(last_messages)} repeated identical messages detected"  # noqa: E501
                                            )
                                            print(f"[DEBUG] Repeated message: {repr(last_messages[0][:100])}")
                                    else:
                                        if debug_mode and check_count % 50 == 1:
                                            # Show how many unique messages in the last 5
                                            unique_count = len(set(last_messages))
                                            print(
                                                f"[DEBUG] MAC table: found {entry_count} entries, last 5 messages have {unique_count} unique contents"  # noqa: E501
                                            )

                                # Second check: if device has been idle for 3+ seconds and we have substantial MAC entries  # noqa: E501
                                if not found_indicator and len(collected_output) >= 10 and entry_count >= 10:
                                    idle_time = time.time() - last_activity
                                    if idle_time >= 3.0:  # Device has been quiet for 3 seconds
                                        found_indicator = f"mac table completion (idle timeout: {entry_count} entries, {idle_time:.1f}s idle)"  # noqa: E501
                                        if debug_mode:
                                            self.logger.debug(
                                                f"FOUND MAC table completion via idle timeout: {entry_count} entries, {idle_time:.1f}s idle"  # noqa: E501
                                            )
                                            print(
                                                f"[DEBUG] FOUND MAC table completion via idle timeout: {entry_count} entries, {idle_time:.1f}s idle"  # noqa: E501
                                            )

                                if not found_indicator and debug_mode and check_count % 50 == 1:
                                    idle_time = time.time() - last_activity
                                    print(f"[DEBUG] MAC table: found {entry_count} entries, idle for {idle_time:.1f}s")
                            else:
                                if debug_mode and check_count % 50 == 1:
                                    print(
                                        f"[DEBUG] MAC table: checking for completion pattern in {len(all_raw_content)} chars"  # noqa: E501
                                    )

                        # ARP-specific completion: check for structured ARP output patterns
                        if not found_indicator and len(collected_output) >= 2:
                            # Look for ARP table structure patterns
                            arp_patterns = ["ip address", "hw address", "interface", "incomplete", "permanent"]
                            arp_pattern_count = sum(1 for pattern in arp_patterns if pattern in all_raw_content.lower())

                            if debug_mode and check_count % 200 == 1:  # Debug ARP patterns less frequently
                                print(
                                    f"[DEBUG] ARP pattern analysis: found {arp_pattern_count}/{len(arp_patterns)} patterns"  # noqa: E501
                                )
                                found_patterns = [p for p in arp_patterns if p in all_raw_content.lower()]
                                print(f"[DEBUG] Found ARP patterns: {found_patterns}")

                            # If we see multiple ARP patterns, this might be a complete ARP table
                            if arp_pattern_count >= 2:
                                # Check if we've been collecting for at least 1 second (ARP commands are usually fast)
                                if time.time() - last_activity > 1:
                                    found_indicator = "arp table structure detected"
                                    if debug_mode:
                                        print(
                                            f"[DEBUG] FOUND ARP table completion: {arp_pattern_count} patterns detected"
                                        )

                        if found_indicator:
                            # This appears to be the final ping summary
                            if debug_mode:
                                self.logger.debug(f"Found completion indicator '{found_indicator}' in combined content")
                                self.logger.debug(f"Completing after {check_count} checks")
                                self.logger.debug(f"Total collected messages: {len(collected_output)}")
                                self.logger.debug(f"Total content length: {len(all_raw_content)} characters")
                                self.logger.debug(
                                    f"Raw content sample (first 200 chars): {repr(all_raw_content[:200])}"
                                )
                                self.logger.debug(
                                    f"Raw content sample (last 200 chars): {repr(all_raw_content[-200:])}"
                                )
                                print(f"[DEBUG] Found completion indicator '{found_indicator}' in combined content")
                                print(f"[DEBUG] Completing after {check_count} checks")
                                print(f"[DEBUG] Total collected messages: {len(collected_output)}")
                                print(f"[DEBUG] Total content length: {len(all_raw_content)} characters")
                                print(f"[DEBUG] Raw content sample (first 200 chars): {repr(all_raw_content[:200])}")
                                print(f"[DEBUG] Raw content sample (last 200 chars): {repr(all_raw_content[-200:])}")
                            final_results = self.command_results.pop(session_id)
                            break
                else:
                    if debug_mode and check_count % 50 == 1:  # Debug every 5 seconds
                        self.logger.debug(f"Check #{check_count}, no results yet for session {session_id}")
                        self.logger.debug(f"Available sessions: {list(self.command_results.keys())}")
                        print(f"[DEBUG] Check #{check_count}, no results yet for session {session_id}")
                        print(f"[DEBUG] Available sessions: {list(self.command_results.keys())}")

            # Emergency circuit breaker - if we're doing too many checks, something is wrong
            if check_count > 10000:  # At 0.1s per check, this is ~16 minutes
                if debug_mode:
                    self.logger.error(f"Circuit breaker triggered at {check_count} checks!")
                    self.logger.error("This indicates a possible infinite loop or system hang")
                    print(f"[EMERGENCY] Circuit breaker triggered at {check_count} checks!")
                    print("[EMERGENCY] This indicates a possible infinite loop or system hang")
                self.logger.error(f"Emergency circuit breaker: {check_count} checks exceeded for session {session_id}")
                with self.results_lock:
                    final_results = self.command_results.pop(session_id, [])
                return final_results if final_results else None

            # Check for activity timeout (no new messages)
            collected_count = 0
            with self.results_lock:
                if session_id in self.command_results:
                    collected_count = len(self.command_results[session_id])

            if collected_count > 0 and (time.time() - last_activity > activity_timeout):
                if debug_mode:
                    self.logger.debug(
                        f"Activity timeout reached ({activity_timeout}s), completing with {collected_count} messages"
                    )
                    print(
                        f"[DEBUG] Activity timeout reached ({activity_timeout}s), completing with {collected_count} messages"  # noqa: E501
                    )
                self.logger.info(f"No new data for {activity_timeout}s, assuming command complete")
                with self.results_lock:
                    if session_id in self.command_results:
                        final_results = self.command_results.pop(session_id)
                        break

            # Critical: Ensure we don't create a busy wait loop
            time.sleep(0.1)  # Check every 100ms - DO NOT REMOVE THIS SLEEP
        else:
            # Timeout occurred
            if debug_mode:
                self.logger.debug(f"Timeout occurred after {timeout_seconds}s, {check_count} checks")
                print(f"[DEBUG] Timeout occurred after {timeout_seconds}s, {check_count} checks")
            with self.results_lock:
                final_results = self.command_results.pop(session_id, [])

            if not final_results:
                if debug_mode:
                    print(f"[DEBUG] No results collected for session {session_id}")
                self.logger.warning(f"Timeout waiting for command result: {session_id}")
                perf_monitor.finish()  # Mark performance monitoring as complete
                return None

        # Combine all collected output
        perf_monitor.finish()  # Mark performance monitoring as complete

        if final_results:
            if debug_mode:
                self.logger.debug(f"Combining {len(final_results)} result segments")
                self.logger.debug(f"Total wait time: {time.time() - start_time:.2f} seconds")
                self.logger.debug(f"Total checks performed: {check_count}")
                print(f"[DEBUG] Combining {len(final_results)} result segments")
                print(f"[DEBUG] Total wait time: {time.time() - start_time:.2f} seconds")
                print(f"[DEBUG] Total checks performed: {check_count}")

            combined_raw = ""
            combined_other: dict[str, Any] = {}

            for index, result in enumerate(final_results):
                raw_content = result.get("raw", "")
                if raw_content:
                    combined_raw += raw_content
                    if debug_mode and len(final_results) > 5:  # Only show details for complex results
                        print(f"[DEBUG] Segment {index + 1}: {len(raw_content)} chars")

                # Collect any other fields
                for key, value in result.items():
                    if key not in ["raw", "session"]:
                        if key in combined_other:
                            combined_other[key] = str(combined_other[key]) + str(value)
                        else:
                            combined_other[key] = value

            # Return combined result
            final_result = {"raw": combined_raw, "session": session_id}
            final_result.update(combined_other)

            if debug_mode:
                print(f"[DEBUG] Final combined result length: {len(combined_raw)} characters")
                print(f"[DEBUG] Final result fields: {list(final_result.keys())}")
                print(f"[DEBUG] First 150 chars of final result: {repr(combined_raw[:150])}")
                print(f"[DEBUG] Last 150 chars of final result: {repr(combined_raw[-150:])}")
                if len(combined_raw) == 0:
                    print("[DEBUG] WARNING: Final result is empty - this may indicate an issue")
                print(f"[DEBUG] Session {session_id} result collection complete")
                print("[DEBUG] " + "=" * 60)

            self.logger.info(f"Command completed with {len(final_results)} message segments")
            return final_result

        perf_monitor.finish()  # Mark performance monitoring as complete
        return None

    def _on_open(self, websocket_connection):  # type: ignore[no-untyped-def]
        """Handle connection-opened event from stream."""
        self.connected = True
        self.logger.debug("WebSocket connection opened")

    def _on_message(self, websocket_connection, message):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912, PLR0915  # pylint: disable=too-many-branches,too-many-statements,too-many-nested-blocks
        r"""Handle incoming message from stream.

        Processes incoming messages following the documented Mist API format::

            {
                "event": "data",
                "channel": "/sites/{site_id}/devices/{device_id}/cmd",
                "data": {
                    "session": "session_id",
                    "raw": "64 bytes from 23.211.0.110: seq=8 ttl=58 time=12.323 ms\n"
                }
            }
        """
        debug_mode = _is_debug_mode()

        try:
            if debug_mode:
                print(f"[DEBUG] Raw WebSocket message received: {repr(message)} (type: {type(message)})")
            self.logger.debug(f"Raw WebSocket message received: {repr(message)} (type: {type(message)})")

            # Parse JSON message - handle string messages first
            message_data = None
            if isinstance(message, str):
                try:
                    message_data = json.loads(message)
                    if debug_mode:
                        print(f"[DEBUG] Successfully parsed JSON message: {message_data}")
                    self.logger.debug(f"Successfully parsed JSON message: {message_data}")
                except json.JSONDecodeError as json_error:
                    if debug_mode:
                        print(f"[DEBUG] Failed to parse JSON message: {json_error}")
                        print(f"[DEBUG] Raw message content: {repr(message)}")
                    self.logger.warning(f"Failed to parse JSON message: {json_error}")
                    self.logger.debug(f"Raw message content: {repr(message)}")
                    return
            elif isinstance(message, dict):
                message_data = message
                if debug_mode:
                    print(f"[DEBUG] Received dict message: {message_data}")
                self.logger.debug(f"Received dict message: {message_data}")
            else:
                if debug_mode:
                    print(f"[DEBUG] Unexpected message type: {type(message)}, content: {repr(message)}")
                self.logger.warning(f"Unexpected message type: {type(message)}, content: {repr(message)}")
                return

            # Ensure we have a valid message_data dict before proceeding
            if not isinstance(message_data, dict):
                if debug_mode:
                    print(f"[DEBUG] Message data is not a dict after parsing: {type(message_data)}")
                self.logger.error(f"Message data is not a dict after parsing: {type(message_data)}")
                return

            # Enhanced packet content logging for debug mode
            if debug_mode:
                print("[PACKET] WebSocket packet details:")
                print(f"[PACKET]   Event: {message_data.get('event', 'unknown')}")
                print(f"[PACKET]   Channel: {message_data.get('channel', 'unknown')}")
                if "data" in message_data:
                    data_content = message_data["data"]
                    print(f"[PACKET]   Data type: {type(data_content)}")
                    if isinstance(data_content, dict):
                        print(f"[PACKET]   Data keys: {list(data_content.keys())}")
                        if "session" in data_content:
                            session_id = data_content["session"]
                            print(f"[PACKET]   Session ID: {session_id}")
                        if "raw" in data_content:
                            raw_content = data_content["raw"]
                            print(f"[PACKET]   Raw content length: {len(str(raw_content))} chars")
                            print(f"[PACKET]   Raw content: {repr(raw_content)}")
                    else:
                        print(f"[PACKET]   Data content: {repr(data_content)}")
                else:
                    print("[PACKET]   No data field in message")

            # Handle subscription confirmation
            if message_data.get("event") == "channel_subscribed":
                channel = message_data.get("channel")
                if debug_mode:
                    print(f"[DEBUG] Channel subscription confirmed: {channel}")
                self.logger.info(f"Channel subscription confirmed: {channel}")
                # Track confirmed subscription
                if channel:
                    self.confirmed_subscriptions.add(channel)
                return

            # Handle command data following documented format
            if message_data.get("event") == "data":
                channel = message_data.get("channel", "")
                data_payload = message_data.get("data", {})

                if debug_mode:
                    print(f"[DEBUG] Processing data event from channel: {channel}")
                    print(f"[DEBUG] Data payload type: {type(data_payload)}")
                    print(f"[DEBUG] Data payload content: {repr(data_payload)}")

                # Check if data_payload is actually a nested message structure
                if isinstance(data_payload, str):
                    try:
                        # Sometimes the data field contains a JSON string
                        data_payload = json.loads(data_payload)
                        if debug_mode:
                            print(f"[DEBUG] Parsed nested JSON in data field: {data_payload}")
                        self.logger.debug(f"Parsed nested JSON in data field: {data_payload}")
                    except json.JSONDecodeError:
                        if debug_mode:
                            print(f"[DEBUG] Data field is string but not JSON: {data_payload}")
                        self.logger.warning(f"Data field is string but not JSON: {data_payload}")
                        return

                # Check if we have another nested event structure
                if isinstance(data_payload, dict) and data_payload.get("event") == "data":
                    # This is a nested structure, extract the actual data
                    actual_data = data_payload.get("data", {})
                    if debug_mode:
                        print(f"[DEBUG] Found nested event structure, extracting actual data: {actual_data}")
                    self.logger.debug(f"Found nested event structure, extracting actual data: {actual_data}")
                    data_payload = actual_data

                session_id = data_payload.get("session") if isinstance(data_payload, dict) else None

                if debug_mode:
                    print(f"[DEBUG] Processing data event - channel: {channel}, session: {session_id}")
                    print(f"[DEBUG] Final data payload: {data_payload}")
                    if session_id:
                        print(f"[DEBUG] Session ID extracted: {session_id}")
                    else:
                        print("[DEBUG] No session ID found in data payload")

                self.logger.debug(f"Processing data event - channel: {channel}, session: {session_id}")
                self.logger.debug(f"Final data payload: {data_payload}")

                if session_id:
                    # Store each message for streaming commands like ping
                    with self.results_lock:
                        # Initialize a list for this session if it doesn't exist
                        if session_id not in self.command_results:
                            self.command_results[session_id] = []
                            if debug_mode:
                                print(f"[DEBUG] Initialized new result list for session: {session_id}")
                        # Append this message to the list
                        self.command_results[session_id].append(data_payload)

                        if debug_mode:
                            current_count = len(self.command_results[session_id])
                            print(f"[DEBUG] Stored message #{current_count} for session {session_id}")
                            if "raw" in data_payload:
                                raw_data = data_payload["raw"]
                                print(f"[DEBUG] Raw data in stored message: {repr(raw_data)}")
                            print(f"[DEBUG] Complete stored message: {data_payload}")

                        self.logger.debug(f"Stored command result for session {session_id}: {data_payload}")
                    self.logger.debug(f"Command result segment received for session: {session_id}")
                    self.logger.debug(f"Total segments for session: {len(self.command_results[session_id])}")
                else:
                    self.logger.warning(f"Received data event without session ID. Full message: {message_data}")
                    self.logger.warning(f"Data payload: {data_payload}")
            else:
                self.logger.debug(f"Unhandled message event type: {message_data.get('event')}")

        except Exception as message_error:
            self.logger.error(f"Error processing WebSocket message: {message_error}")
            self.logger.debug("Exception details:", exc_info=True)
            self.logger.debug(f"Problematic message: {repr(message)}")
            self.logger.debug(f"Message type: {type(message)}")

    def _on_error(self, websocket_connection, error):  # type: ignore[no-untyped-def]
        """Handle error events from connection."""
        self.logger.debug(f"WebSocket error type: {type(error).__name__}")
        self.logger.error(f"WebSocket error: {error}")

    def _on_close(self, websocket_connection, close_status_code, close_message):  # type: ignore[no-untyped-def]
        """Handle closed connection event."""
        self.connected = False
        self.logger.debug(f"WebSocket close details: status_code={close_status_code}, message={close_message}")
        self.logger.info(f"WebSocket connection closed (status: {close_status_code})")

    def disconnect(self) -> None:
        """Close WebSocket connection and cleanup resources."""
        if self.websocket_connection:
            self.websocket_connection.close()
        self.connected = False
        self.subscribed_channels.clear()

        with self.results_lock:
            self.command_results.clear()

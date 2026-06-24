"""Scan capture orchestration extracted from MistHelper high-CC offender."""

import importlib
import logging
from types import SimpleNamespace
from typing import Any, cast

# Band-choice to band-code map (accepts menu indices and direct band codes).
_BAND_MAP = {"1": "24", "2": "5", "3": "6", "24": "24", "5": "5", "6": "6"}
# Bandwidth-choice to MHz value map.
_BANDWIDTH_MAP = {"1": "20", "2": "40", "3": "80", "4": "160"}


def _resolve_prompt_helpers() -> tuple[Any, Any, Any, Any, Any]:
    """Resolve helper classes from MistHelper at runtime to avoid circular imports."""
    misthelper_module = importlib.import_module("MistHelper")  # Late import avoids circular src->MistHelper dependency
    return (
        misthelper_module.InputUtils,
        misthelper_module.PromptUtils,
        misthelper_module.PromptNetworkDeviceUtils,
        misthelper_module.DeviceUtils,
        misthelper_module.mistapi,
    )


class SiteScanCaptureService:
    """Owns scan radio capture flow formerly embedded in MistHelper method."""

    @staticmethod
    def _select_ap(
        manager: Any, input_utils: Any, prompt_network_device_utils: Any, device_utils: Any, site_id: str
    ) -> tuple[str | None, str]:
        """Select the target AP; return (ap_mac, mode) where mode is 'single', 'all', or 'abort'."""
        logging.debug("Prompting for AP selection from site inventory")  # Trace the AP prompt
        prompt_utils = prompt_network_device_utils(
            manager.mist_session, input_utils.safe_input, device_utils.expand_port_range_string
        )  # Build the device prompt helper
        ap_mac = prompt_utils.select_ap_mac(site_id)  # Interactive AP picker (may return the ALL_APS sentinel)
        if not ap_mac:  # Nothing selected or selection failed
            logging.warning("No AP selected or AP selection failed - aborting capture")  # Trace the abort
            return None, "abort"  # Signal abort
        if ap_mac == "ALL_APS":  # User chose to capture from every AP
            logging.info("User selected all APs - launching multi-AP captures")  # Trace the all-AP path
            return None, "all"  # Signal the all-AP path (launched by caller)
        normalized_ap_mac = manager.normalize_mac_address(ap_mac)  # Normalize the single AP MAC
        logging.debug("Selected and normalized AP MAC: %s", normalized_ap_mac)  # Trace the normalized MAC
        return normalized_ap_mac, "single"  # Single-AP capture path

    @staticmethod
    def _select_band(input_utils: Any) -> str:
        """Prompt for the radio band; return the resolved band code (defaults to 5 GHz)."""
        logging.debug("Prompting for band selection")  # Trace the band prompt
        print("\nSelect band:")  # Prompt header
        print("  1. 2.4 GHz")  # Option 1
        print("  2. 5 GHz (default)")  # Option 2 (default)
        print("  3. 6 GHz")  # Option 3
        band_choice = input_utils.safe_input(
            "Enter choice [1-3] (default 2): ", default_value="2", context="band"
        )  # Read the band choice
        band = _BAND_MAP.get(band_choice, "5")  # Map to a band code, defaulting to 5 GHz
        logging.debug("Band selected: %s (choice: %s)", band, band_choice)  # Trace the resolved band
        return band  # Resolved band code

    @staticmethod
    def _prompt_channel(input_utils: Any, band: str) -> int | None:
        """Prompt for a band-appropriate channel; return None to abort (message printed)."""
        logging.debug("Prompting for channel")  # Trace the channel prompt
        if band == "24":  # 2.4 GHz valid channels are 1-11
            channel_str = input_utils.safe_input(
                "Enter channel (1-11, default 1): ", default_value="1", context="channel"
            )  # Read the 2.4 GHz channel
        elif band == "5":  # 5 GHz has the standard UNII channel set
            channel_str = input_utils.safe_input(
                "Enter channel (36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 144, default 36): ",  # noqa: E501
                default_value="36",
                context="channel",
            )  # Read the 5 GHz channel
        else:  # 6 GHz channels span 1-233
            channel_str = input_utils.safe_input(
                "Enter channel (1-233, default 1): ", default_value="1", context="channel"
            )  # Read the 6 GHz channel
        try:  # Validate the channel parses as an integer
            channel = int(channel_str)  # Parse the channel
            logging.debug("Channel selected: %s", channel)  # Trace the channel
            return channel  # Validated channel
        except ValueError:  # Non-numeric channel
            print(f"\n! Invalid channel: {channel_str}")  # Inform the user
            logging.error("Invalid channel value: %s", channel_str)  # Trace the failure
            return None  # Abort

    @staticmethod
    def _select_bandwidth(input_utils: Any, band: str) -> str | None:
        """Prompt for a band-appropriate bandwidth; return None to abort (message printed)."""
        logging.debug("Prompting for bandwidth")  # Trace the bandwidth prompt
        print("\nSelect bandwidth:")  # Prompt header
        print("  1. 20 MHz")  # Option 1
        print("  2. 40 MHz")  # Option 2
        if band in ["5", "6"]:  # 80 MHz only valid for 5/6 GHz
            print("  3. 80 MHz")  # Option 3
        if band == "6":  # 160 MHz only valid for 6 GHz
            print("  4. 160 MHz")  # Option 4
        bw_choice = input_utils.safe_input(
            "Enter choice (default 1): ", default_value="1", context="bandwidth"
        )  # Read the bandwidth choice
        bandwidth = _BANDWIDTH_MAP.get(bw_choice, "20")  # Map to MHz, defaulting to 20 MHz
        logging.debug("Bandwidth selected: %s MHz (choice: %s)", bandwidth, bw_choice)  # Trace the resolved bandwidth
        if band == "24" and bandwidth not in ["20", "40"]:  # 2.4 GHz only supports 20/40 MHz
            print(f"\n! Invalid bandwidth {bandwidth} for 2.4 GHz band")  # Inform the user
            logging.error("Invalid bandwidth %s for 2.4 GHz band", bandwidth)  # Trace the failure
            return None  # Abort
        return bandwidth  # Validated bandwidth

    @staticmethod
    def _prompt_duration(input_utils: Any) -> int | None:
        """Prompt for capture duration (60-86400s); return None to abort (message printed)."""
        logging.debug("Prompting for duration")  # Trace the duration prompt
        duration_str = input_utils.safe_input(
            "Enter capture duration in seconds (default 60, min 60, max 86400): ",
            default_value="60",
            context="duration",
        )  # Read the duration
        try:  # Validate the duration parses and is in range
            duration = int(duration_str)  # Parse the duration
            if duration < 60 or duration > 86400:  # Enforce the API's allowed range
                print("\n! Duration must be between 60 and 86400 seconds (API requirement)")  # Inform the user
                logging.error("Duration out of range: %s", duration)  # Trace the range failure
                return None  # Abort
            logging.debug("Duration set: %s seconds", duration)  # Trace the duration
            return duration  # Validated duration
        except ValueError:  # Non-numeric duration
            print(f"\n! Invalid duration: {duration_str}")  # Inform the user
            logging.error("Invalid duration value: %s", duration_str)  # Trace the failure
            return None  # Abort

    @staticmethod
    def _prompt_num_packets(input_utils: Any) -> int | None:
        """Prompt for packet count (0-10000); return None to abort (message printed)."""
        logging.debug("Prompting for packet count")  # Trace the packet-count prompt
        num_packets_str = input_utils.safe_input(
            "Enter number of packets (default 1024, max 10000): ", default_value="1024", context="num_packets"
        )  # Read the packet count
        try:  # Validate the count parses and is in range
            num_packets = int(num_packets_str)  # Parse the count
            if num_packets < 0 or num_packets > 10000:  # Enforce the allowed range
                print("\n! Number of packets must be between 0 and 10000")  # Inform the user
                logging.error("Packet count out of range: %s", num_packets)  # Trace the range failure
                return None  # Abort
            logging.debug("Packet count set: %s", num_packets)  # Trace the count
            return num_packets  # Validated count
        except ValueError:  # Non-numeric count
            print(f"\n! Invalid number of packets: {num_packets_str}")  # Inform the user
            logging.error("Invalid packet count value: %s", num_packets_str)  # Trace the failure
            return None  # Abort

    @staticmethod
    def _prompt_loop_mode(input_utils: Any) -> bool:
        """Prompt whether to enable continuous loop mode."""
        print("\nLoop Mode:")  # Section header
        print("  Automatically start a new capture when the current one completes")  # Explanation line 1
        print("  Downloads happen in background while next capture runs")  # Explanation line 2
        loop_mode = input_utils.safe_input(
            "Enable continuous loop mode? (y/n, default n): ", default_value="n", context="loop_mode"
        )  # Read the loop choice
        return bool(loop_mode.lower() == "y")  # Enabled only on explicit yes

    @staticmethod
    def _build_payload(capture: SimpleNamespace) -> dict[str, Any]:
        """Build the scan capture payload from gathered settings."""
        payload: dict[str, Any] = {
            "type": "scan",
            "ap_mac": capture.ap_mac,
            "band": capture.band,
            "channel": capture.channel,
            "bandwidth": capture.bandwidth,
            "duration": capture.duration,
            "num_packets": capture.num_packets,
            "format": capture.capture_format,
            "max_pkt_len": 1300,
        }  # Scan-capture payload (max packet length fixed at 1300 bytes)
        logging.debug("Payload constructed: %s", payload)  # Trace the constructed payload
        return payload  # Completed payload

    @staticmethod
    def _print_summary(capture: SimpleNamespace) -> None:
        """Print the scan capture configuration summary."""
        print("\n" + "=" * 80)  # Top divider
        print(" CAPTURE CONFIGURATION SUMMARY")  # Section title
        print("=" * 80)  # Divider
        print("  Capture Type: Scan Radio")  # Capture type
        print(f"  AP MAC: {capture.ap_mac}")  # Target AP
        print(f"  Band: {capture.band} GHz")  # Band
        print(f"  Channel: {capture.channel}")  # Channel
        print(f"  Bandwidth: {capture.bandwidth} MHz")  # Bandwidth
        print(f"  Duration: {capture.duration} seconds")  # Duration
        print(f"  Packets: {capture.num_packets}")  # Packet count
        print(
            f"  Loop Mode: {'ENABLED (continuous until Ctrl+C)' if capture.enable_loop else 'Disabled (single capture)'}"  # noqa: E501
        )  # Loop mode
        print("=" * 80)  # Bottom divider

    @staticmethod
    def _check_existing_captures(manager: Any, mistapi: Any, input_utils: Any, site_id: str, ap_mac: str) -> bool:
        """Warn on an existing capture for the AP; return False if the user cancels."""
        print(f"\n> Checking for existing captures on AP {ap_mac}...")  # Inform the user of the pre-check
        try:  # Pre-check failures are non-fatal (warn and proceed)
            response = mistapi.api.v1.sites.pcaps.listSitePacketCaptures(manager.mist_session, site_id)  # List pcaps
            if response.status_code == 200:  # Only inspect successful responses
                existing_captures = response.data or []  # Existing captures (or empty)
                ap_has_capture = any(
                    cap.get("ap_mac", "").replace(":", "").replace("-", "").lower()
                    == ap_mac.replace(":", "").replace("-", "").lower()
                    for cap in existing_captures
                )  # True when this AP already has a capture (MAC-normalized comparison)
                if ap_has_capture:  # Warn and confirm when a conflict exists
                    print("\n! WARNING: This AP already has a capture in progress or recently completed")  # Warn
                    print("  Mist only allows one capture per AP at a time")  # Explain the constraint
                    print("  The new capture may fail with 'Recording already in progress'")  # Explain the risk
                    proceed = input_utils.safe_input(
                        "\nContinue anyway? (y/n, default n): ",
                        default_value="n",
                        context="capture_conflict_confirmation",
                    ).lower()  # Read the override choice
                    if proceed != "y":  # User declined to proceed
                        print("\n* Capture cancelled by user")  # Inform the user
                        logging.info("User cancelled capture due to existing capture on AP")  # Trace the cancel
                        return False  # Signal cancel
        except Exception as error:  # Pre-check API failure - warn and proceed
            logging.warning("Failed to check for existing captures: %s", error)  # Trace the failure
        return True  # Proceed with the capture

    @classmethod
    def execute(cls, manager: Any) -> None:
        """Run scan radio packet capture workflow using manager dependencies."""
        input_utils, prompt_utils, prompt_network_device_utils, device_utils, mistapi = _resolve_prompt_helpers()
        logging.info("Starting site scan capture")  # Trace workflow start

        site_id = prompt_utils.select_site_with_logging()  # Prompt for the target site
        logging.debug("Site selection returned: %s", site_id)  # Trace the selection
        if not site_id:  # No site chosen
            logging.warning("No site_id returned from selection - aborting capture")  # Trace the abort
            return  # Abort the workflow

        logging.debug("Proceeding with scan capture configuration for site: %s", site_id)  # Trace progress
        print("\n" + "-" * 80)  # Top divider
        print(" SCAN RADIO CAPTURE CONFIGURATION")  # Section title
        print("-" * 80)  # Bottom divider

        ap_mac, mode = cls._select_ap(manager, input_utils, prompt_network_device_utils, device_utils, site_id)  # AP
        if mode == "abort":  # AP selection failed (message already traced)
            return  # Abort the workflow
        if mode == "all":  # User chose all APs - launch multi-AP captures
            manager._start_site_scan_capture_all_aps(site_id)  # Run captures across every AP
            return  # All-AP path handled
        ap_mac = cast(str, ap_mac)  # Single-AP path always yields a normalized MAC (narrows type for mypy)

        band = cls._select_band(input_utils)  # Resolve the radio band

        channel = cls._prompt_channel(input_utils, band)  # Resolve a band-appropriate channel
        if channel is None:  # Invalid channel (message already printed)
            return  # Abort the workflow

        bandwidth = cls._select_bandwidth(input_utils, band)  # Resolve a band-appropriate bandwidth
        if bandwidth is None:  # Invalid bandwidth (message already printed)
            return  # Abort the workflow

        duration = cls._prompt_duration(input_utils)  # Resolve the capture duration
        if duration is None:  # Invalid duration (message already printed)
            return  # Abort the workflow

        num_packets = cls._prompt_num_packets(input_utils)  # Resolve the packet count
        if num_packets is None:  # Invalid count (message already printed)
            return  # Abort the workflow

        capture_format = manager._get_capture_format_selection()  # Capture output format

        enable_loop = cls._prompt_loop_mode(input_utils)  # Whether to run continuous loop mode

        capture = SimpleNamespace(
            ap_mac=ap_mac,
            band=band,
            channel=channel,
            bandwidth=bandwidth,
            duration=duration,
            num_packets=num_packets,
            capture_format=capture_format,
            enable_loop=enable_loop,
        )  # Bundle all gathered settings

        payload = cls._build_payload(capture)  # Construct the API payload
        cls._print_summary(capture)  # Show the configuration summary

        logging.debug("Waiting for user confirmation")  # Trace the confirmation wait
        input_utils.safe_input(
            "\nPress Enter to start capture (Ctrl+C to cancel): ", context="confirmation", allow_empty=True
        )  # Final confirmation before starting

        if not cls._check_existing_captures(manager, mistapi, input_utils, site_id, ap_mac):  # Conflict pre-check
            return  # User cancelled due to an existing capture

        logging.info("User confirmed - executing site capture")  # Trace the execution
        if enable_loop:  # Continuous loop mode
            manager._execute_site_capture_loop(site_id, payload)  # Run captures in a loop
        else:  # Single capture
            manager._execute_site_capture(site_id, payload)  # Run a single capture

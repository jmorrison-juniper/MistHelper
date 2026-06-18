"""Wireless client capture orchestration extracted from MistHelper offender #6."""

import importlib
import logging
from types import SimpleNamespace
from typing import Any

# Bounded-integer prompt specifications: each carries prompt text, default, input context,
# the noun used in the invalid message, the inclusive low/high bounds, and the range-error lines.
_DURATION_SPEC = SimpleNamespace(
    prompt="Enter capture duration in seconds (default 60, max 86400): ",
    default="60",
    context="duration",
    invalid_label="duration",
    low=60,
    high=86400,
    range_lines=[
        "\n! Duration must be between 60 and 86400 seconds",
        "  (Mist API requires minimum 60 seconds for all packet captures)",
    ],
)
_PACKETS_SPEC = SimpleNamespace(
    prompt="Enter number of packets (default 1024, max 10000, 0 for unlimited): ",
    default="1024",
    context="num_packets",
    invalid_label="number of packets",
    low=0,
    high=10000,
    range_lines=["\n! Number of packets must be between 0 and 10000"],
)
_MAX_PKT_LEN_SPEC = SimpleNamespace(
    prompt="Enter max packet length in bytes (default 1300, max 2048): ",
    default="1300",
    context="max_pkt_len",
    invalid_label="max packet length",
    low=64,
    high=2048,
    range_lines=["\n! Max packet length must be between 64 and 2048 bytes"],
)


def _resolve_prompt_helpers() -> tuple[Any, Any, Any, Any]:
    """Resolve helper classes from MistHelper module to preserve runtime compatibility."""
    misthelper_module = importlib.import_module("MistHelper")  # Late import avoids circular src->MistHelper dependency
    return (
        misthelper_module.InputUtils,
        misthelper_module.PromptUtils,
        misthelper_module.PromptClientUtils,
        misthelper_module.PromptNetworkDeviceUtils,
    )


class SiteWirelessClientCaptureService:
    """Owns wireless client capture flow formerly embedded in MistHelper method."""

    @staticmethod
    def _print_intro() -> None:
        """Print the wireless client capture configuration banner."""
        print("\n" + "-" * 80)  # Top divider
        print(" WIRELESS CLIENT CAPTURE CONFIGURATION")  # Section title
        print("-" * 80)  # Bottom divider
        print("\nThis capture type monitors ongoing traffic from ALREADY CONNECTED wireless clients.")  # Purpose
        print(
            "Note: To capture new connection attempts (auth/assoc handshakes), use New Association Capture instead."
        )  # Guidance toward the alternate capture type

    @staticmethod
    def _select_client_mac(manager: Any, input_utils: Any, prompt_client_utils: Any, site_id: str) -> str | None:
        """Select and validate the target client MAC; return None to abort (message printed)."""
        print("\nClient selection:")  # Prompt header
        print("  1. Select from connected clients")  # Option 1
        print("  2. Manually enter MAC address")  # Option 2
        client_choice = input_utils.safe_input(
            "Enter choice (default 1): ", default_value="1", context="client_select"
        )  # Read the selection mode
        if client_choice == "1":  # Pick from the connected-clients list
            client_mac = prompt_client_utils.select_client_mac(site_id)  # Interactive client picker
            if not client_mac:  # Nothing selected
                print("\n! No client selected")  # Inform the user
                return None  # Abort
        else:  # Manual MAC entry
            client_mac = input_utils.safe_input("\nEnter client MAC address: ", context="client_mac")  # Read MAC
        if not manager.validate_mac_address(client_mac):  # Reject malformed MACs
            print(f"\n! Invalid MAC address format: {client_mac}")  # Inform the user
            return None  # Abort
        return str(manager.normalize_mac_address(client_mac))  # Return normalized MAC

    @staticmethod
    def _select_ap_filter(
        manager: Any, input_utils: Any, prompt_network_device_utils: Any, site_id: str
    ) -> tuple[str | None, bool]:
        """Optionally select an AP filter; return (ap_mac, ok) where ok=False signals abort."""
        print("\nOptional: Filter by specific AP")  # Prompt header
        print("  1. Select AP from list")  # Option 1
        print("  2. Enter MAC manually")  # Option 2
        print("  3. Skip (capture from any AP)")  # Option 3
        ap_choice = input_utils.safe_input(
            "Enter choice (default 3): ", default_value="3", context="ap_filter"
        )  # Read the AP-filter mode
        ap_mac = None  # Default: no AP filter
        if ap_choice == "1":  # Pick AP from the site inventory
            expand_port_range_fn = getattr(manager, "expand_port_range_string", lambda value: [value])  # Range expander
            prompt_utils = prompt_network_device_utils(
                manager.mist_session, input_utils.safe_input, expand_port_range_fn
            )  # Build the device prompt helper
            ap_mac = prompt_utils.select_ap_mac(site_id)  # Interactive AP picker
            if ap_mac:  # Normalize only when an AP was chosen
                ap_mac = manager.normalize_mac_address(ap_mac)  # Normalize the AP MAC
        elif ap_choice == "2":  # Manual AP MAC entry
            ap_mac = input_utils.safe_input("Enter AP MAC address: ", context="ap_mac")  # Read AP MAC
            if not manager.validate_mac_address(ap_mac):  # Reject malformed AP MACs
                print(f"\n! Invalid AP MAC address format: {ap_mac}")  # Inform the user
                return None, False  # Abort
            ap_mac = manager.normalize_mac_address(ap_mac)  # Normalize the AP MAC
        return ap_mac, True  # Resolved AP filter (or None) and continue

    @staticmethod
    def _prompt_bounded_int(input_utils: Any, spec: SimpleNamespace) -> int | None:
        """Prompt for an integer within spec bounds; return None to abort (message printed)."""
        raw = input_utils.safe_input(spec.prompt, default_value=spec.default, context=spec.context)  # Read raw value
        try:  # Validate that the input parses as an integer
            value = int(raw)  # Parse the integer
        except ValueError:  # Non-numeric input
            print(f"\n! Invalid {spec.invalid_label}: {raw}")  # Inform the user
            return None  # Abort
        if value < spec.low or value > spec.high:  # Enforce the inclusive bounds
            for line in spec.range_lines:  # Print each range-error line
                print(line)  # Inform the user
            return None  # Abort
        return value  # Validated integer

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
        """Build the client capture payload from gathered settings."""
        payload: dict[str, Any] = {
            "type": "client",
            "client_mac": capture.client_mac,
            "duration": capture.duration,
            "num_packets": capture.num_packets,
            "max_pkt_len": capture.max_pkt_len,
            "includes_mcast": capture.includes_mcast,
            "format": capture.capture_format,
        }  # Core client-capture payload
        if capture.ap_mac:  # Add the AP filter only when one was chosen
            payload["ap_mac"] = capture.ap_mac  # Restrict capture to this AP
        if capture.tcpdump_expr:  # Add a packet filter only when provided
            payload["tcpdump_expression"] = capture.tcpdump_expr  # Apply the tcpdump expression
        return payload  # Completed payload

    @staticmethod
    def _print_summary(capture: SimpleNamespace) -> None:
        """Print the capture configuration summary."""
        print("\n" + "=" * 80)  # Top divider
        print(" CAPTURE CONFIGURATION SUMMARY")  # Section title
        print("=" * 80)  # Divider
        print("  Capture Type: Wireless Client")  # Capture type
        print(f"  Client MAC: {capture.client_mac}")  # Target client
        if capture.ap_mac:  # Show AP filter when present
            print(f"  AP MAC Filter: {capture.ap_mac}")  # AP filter value
        if capture.tcpdump_expr:  # Show packet filter when present
            print(f"  Packet Filter: {capture.tcpdump_expr}")  # tcpdump expression
        else:  # Otherwise note that all traffic is captured
            print("  Packet Filter: None (all traffic)")  # No filter
        print(f"  Duration: {capture.duration} seconds")  # Duration
        print(f"  Packets: {capture.num_packets} ({'unlimited' if capture.num_packets == 0 else 'max'})")  # Packets
        print(f"  Max Packet Length: {capture.max_pkt_len} bytes")  # Max packet length
        print(f"  Include Multicast: {'Yes' if capture.includes_mcast else 'No'}")  # Multicast flag
        print(f"  Format: {capture.capture_format}")  # Capture format
        print(
            f"  Loop Mode: {'ENABLED (continuous until Ctrl+C)' if capture.enable_loop else 'Disabled (single capture)'}"  # noqa: E501
        )  # Loop mode
        print("=" * 80)  # Bottom divider

    @classmethod
    def execute(cls, manager: Any) -> None:
        """Run wireless client packet capture workflow using manager dependencies."""
        input_utils, prompt_utils, prompt_client_utils, prompt_network_device_utils = _resolve_prompt_helpers()
        logging.info("Starting site wireless client capture")  # Trace workflow start

        site_id = prompt_utils.select_site_with_logging()  # Prompt for the target site
        if not site_id:  # No site chosen
            return  # Abort the workflow

        cls._print_intro()  # Show the configuration banner

        client_mac = cls._select_client_mac(manager, input_utils, prompt_client_utils, site_id)  # Resolve client MAC
        if not client_mac:  # Selection aborted (message already printed)
            return  # Abort the workflow

        ap_mac, ap_ok = cls._select_ap_filter(manager, input_utils, prompt_network_device_utils, site_id)  # AP filter
        if not ap_ok:  # AP selection aborted (message already printed)
            return  # Abort the workflow

        duration = cls._prompt_bounded_int(input_utils, _DURATION_SPEC)  # Prompt for capture duration
        if duration is None:  # Invalid duration (message already printed)
            return  # Abort the workflow

        num_packets = cls._prompt_bounded_int(input_utils, _PACKETS_SPEC)  # Prompt for packet count
        if num_packets is None:  # Invalid packet count (message already printed)
            return  # Abort the workflow

        max_pkt_len = cls._prompt_bounded_int(input_utils, _MAX_PKT_LEN_SPEC)  # Prompt for max packet length
        if max_pkt_len is None:  # Invalid max packet length (message already printed)
            return  # Abort the workflow

        includes_mcast_input = input_utils.safe_input(
            "Include multicast traffic? (y/n, default n): ", default_value="n", context="includes_mcast"
        )  # Read the multicast choice
        includes_mcast = includes_mcast_input.lower() == "y"  # Enabled only on explicit yes

        tcpdump_expr = manager._get_tcpdump_expression_selection()  # Optional tcpdump packet filter
        capture_format = manager._get_capture_format_selection()  # Capture output format

        enable_loop = cls._prompt_loop_mode(input_utils)  # Whether to run continuous loop mode

        capture = SimpleNamespace(
            client_mac=client_mac,
            ap_mac=ap_mac,
            duration=duration,
            num_packets=num_packets,
            max_pkt_len=max_pkt_len,
            includes_mcast=includes_mcast,
            tcpdump_expr=tcpdump_expr,
            capture_format=capture_format,
            enable_loop=enable_loop,
        )  # Bundle all gathered settings

        payload = cls._build_payload(capture)  # Construct the API payload
        cls._print_summary(capture)  # Show the configuration summary

        input_utils.safe_input(
            "\nPress Enter to start capture (Ctrl+C to cancel): ", context="confirmation", allow_empty=True
        )  # Final confirmation before starting

        if enable_loop:  # Continuous loop mode
            manager._execute_site_capture_loop(site_id, payload)  # Run captures in a loop
        else:  # Single capture
            manager._execute_site_capture(site_id, payload)  # Run a single capture

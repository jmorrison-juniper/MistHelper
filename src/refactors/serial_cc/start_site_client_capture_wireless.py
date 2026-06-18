"""Wireless client capture orchestration extracted from MistHelper offender #6."""

import importlib
import logging


def _resolve_prompt_helpers():
    """Resolve helper classes from MistHelper module to preserve runtime compatibility."""
    misthelper_module = importlib.import_module("MistHelper")
    return (
        misthelper_module.InputUtils,
        misthelper_module.PromptUtils,
        misthelper_module.PromptClientUtils,
        misthelper_module.PromptNetworkDeviceUtils,
    )


class SiteWirelessClientCaptureService:
    """Owns wireless client capture flow formerly embedded in MistHelper method."""

    @staticmethod
    def execute(manager):  # noqa: C901, PLR0912, PLR0915
        """Run wireless client packet capture workflow using manager dependencies."""
        InputUtils, PromptUtils, PromptClientUtils, PromptNetworkDeviceUtils = _resolve_prompt_helpers()
        logging.info("Starting site wireless client capture")

        site_id = PromptUtils.select_site_with_logging()
        if not site_id:
            return

        print("\n" + "-" * 80)
        print(" WIRELESS CLIENT CAPTURE CONFIGURATION")
        print("-" * 80)
        print("\nThis capture type monitors ongoing traffic from ALREADY CONNECTED wireless clients.")
        print("Note: To capture new connection attempts (auth/assoc handshakes), use New Association Capture instead.")

        print("\nClient selection:")
        print("  1. Select from connected clients")
        print("  2. Manually enter MAC address")
        client_choice = InputUtils.safe_input("Enter choice (default 1): ", default_value="1", context="client_select")

        client_mac = None
        if client_choice == "1":
            client_mac = PromptClientUtils.select_client_mac(site_id)
            if not client_mac:
                print("\n! No client selected")
                return
        else:
            client_mac = InputUtils.safe_input("\nEnter client MAC address: ", context="client_mac")

        if not manager.validate_mac_address(client_mac):
            print(f"\n! Invalid MAC address format: {client_mac}")
            return
        client_mac = manager.normalize_mac_address(client_mac)

        print("\nOptional: Filter by specific AP")
        print("  1. Select AP from list")
        print("  2. Enter MAC manually")
        print("  3. Skip (capture from any AP)")
        ap_choice = InputUtils.safe_input("Enter choice (default 3): ", default_value="3", context="ap_filter")

        ap_mac = None
        if ap_choice == "1":
            expand_port_range_fn = getattr(manager, "expand_port_range_string", lambda value: [value])
            prompt_utils = PromptNetworkDeviceUtils(manager.mist_session, InputUtils.safe_input, expand_port_range_fn)
            ap_mac = prompt_utils.select_ap_mac(site_id)
            if ap_mac:
                ap_mac = manager.normalize_mac_address(ap_mac)
        elif ap_choice == "2":
            ap_mac = InputUtils.safe_input("Enter AP MAC address: ", context="ap_mac")
            if not manager.validate_mac_address(ap_mac):
                print(f"\n! Invalid AP MAC address format: {ap_mac}")
                return
            ap_mac = manager.normalize_mac_address(ap_mac)

        duration_str = InputUtils.safe_input(
            "Enter capture duration in seconds (default 60, max 86400): ", default_value="60", context="duration"
        )
        try:
            duration = int(duration_str)
            if duration < 60 or duration > 86400:
                print("\n! Duration must be between 60 and 86400 seconds")
                print("  (Mist API requires minimum 60 seconds for all packet captures)")
                return
        except ValueError:
            print(f"\n! Invalid duration: {duration_str}")
            return

        num_packets_str = InputUtils.safe_input(
            "Enter number of packets (default 1024, max 10000, 0 for unlimited): ",
            default_value="1024",
            context="num_packets",
        )
        try:
            num_packets = int(num_packets_str)
            if num_packets < 0 or num_packets > 10000:
                print("\n! Number of packets must be between 0 and 10000")
                return
        except ValueError:
            print(f"\n! Invalid number of packets: {num_packets_str}")
            return

        max_pkt_len_str = InputUtils.safe_input(
            "Enter max packet length in bytes (default 1300, max 2048): ", default_value="1300", context="max_pkt_len"
        )
        try:
            max_pkt_len = int(max_pkt_len_str)
            if max_pkt_len < 64 or max_pkt_len > 2048:
                print("\n! Max packet length must be between 64 and 2048 bytes")
                return
        except ValueError:
            print(f"\n! Invalid max packet length: {max_pkt_len_str}")
            return

        includes_mcast_input = InputUtils.safe_input(
            "Include multicast traffic? (y/n, default n): ", default_value="n", context="includes_mcast"
        )
        includes_mcast = includes_mcast_input.lower() == "y"

        tcpdump_expr = manager._get_tcpdump_expression_selection()
        capture_format = manager._get_capture_format_selection()

        print("\nLoop Mode:")
        print("  Automatically start a new capture when the current one completes")
        print("  Downloads happen in background while next capture runs")
        loop_mode = InputUtils.safe_input(
            "Enable continuous loop mode? (y/n, default n): ", default_value="n", context="loop_mode"
        )
        enable_loop = loop_mode.lower() == "y"

        payload = {
            "type": "client",
            "client_mac": client_mac,
            "duration": duration,
            "num_packets": num_packets,
            "max_pkt_len": max_pkt_len,
            "includes_mcast": includes_mcast,
            "format": capture_format,
        }

        if ap_mac:
            payload["ap_mac"] = ap_mac
        if tcpdump_expr:
            payload["tcpdump_expression"] = tcpdump_expr

        print("\n" + "=" * 80)
        print(" CAPTURE CONFIGURATION SUMMARY")
        print("=" * 80)
        print("  Capture Type: Wireless Client")
        print(f"  Client MAC: {client_mac}")
        if ap_mac:
            print(f"  AP MAC Filter: {ap_mac}")
        if tcpdump_expr:
            print(f"  Packet Filter: {tcpdump_expr}")
        else:
            print("  Packet Filter: None (all traffic)")
        print(f"  Duration: {duration} seconds")
        print(f"  Packets: {num_packets} ({'unlimited' if num_packets == 0 else 'max'})")
        print(f"  Max Packet Length: {max_pkt_len} bytes")
        print(f"  Include Multicast: {'Yes' if includes_mcast else 'No'}")
        print(f"  Format: {capture_format}")
        print(f"  Loop Mode: {'ENABLED (continuous until Ctrl+C)' if enable_loop else 'Disabled (single capture)'}")
        print("=" * 80)

        InputUtils.safe_input(
            "\nPress Enter to start capture (Ctrl+C to cancel): ", context="confirmation", allow_empty=True
        )

        if enable_loop:
            manager._execute_site_capture_loop(site_id, payload)
        else:
            manager._execute_site_capture(site_id, payload)

"""Scan capture orchestration extracted from MistHelper high-CC offender."""

import importlib
import logging


def _resolve_prompt_helpers():
    """Resolve helper classes from MistHelper at runtime to avoid circular imports."""
    misthelper_module = importlib.import_module("MistHelper")
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
    def execute(manager):  # noqa: C901, PLR0912, PLR0915
        """Run scan radio packet capture workflow using manager dependencies."""
        InputUtils, PromptUtils, PromptNetworkDeviceUtils, DeviceUtils, mistapi = _resolve_prompt_helpers()
        logging.info("Starting site scan capture")

        site_id = PromptUtils.select_site_with_logging()
        logging.debug(f"Site selection returned: {site_id}")
        if not site_id:
            logging.warning("No site_id returned from selection - aborting capture")
            return

        logging.debug(f"Proceeding with scan capture configuration for site: {site_id}")
        print("\n" + "-" * 80)
        print(" SCAN RADIO CAPTURE CONFIGURATION")
        print("-" * 80)

        logging.debug("Prompting for AP selection from site inventory")
        prompt_utils = PromptNetworkDeviceUtils(
            manager.mist_session, InputUtils.safe_input, DeviceUtils.expand_port_range_string
        )
        ap_mac = prompt_utils.select_ap_mac(site_id)
        if not ap_mac:
            logging.warning("No AP selected or AP selection failed - aborting capture")
            return

        if ap_mac == "ALL_APS":
            logging.info("User selected all APs - launching multi-AP captures")
            manager._start_site_scan_capture_all_aps(site_id)
            return

        ap_mac = manager.normalize_mac_address(ap_mac)
        logging.debug(f"Selected and normalized AP MAC: {ap_mac}")

        logging.debug("Prompting for band selection")
        print("\nSelect band:")
        print("  1. 2.4 GHz")
        print("  2. 5 GHz (default)")
        print("  3. 6 GHz")
        band_choice = InputUtils.safe_input("Enter choice [1-3] (default 2): ", default_value="2", context="band")

        band_map = {"1": "24", "2": "5", "3": "6", "24": "24", "5": "5", "6": "6"}
        band = band_map.get(band_choice, "5")
        logging.debug(f"Band selected: {band} (choice: {band_choice})")

        logging.debug("Prompting for channel")
        if band == "24":
            channel_str = InputUtils.safe_input(
                "Enter channel (1-11, default 1): ", default_value="1", context="channel"
            )
        elif band == "5":
            channel_str = InputUtils.safe_input(
                "Enter channel (36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 144, default 36): ",  # noqa: E501
                default_value="36",
                context="channel",
            )
        else:
            channel_str = InputUtils.safe_input(
                "Enter channel (1-233, default 1): ", default_value="1", context="channel"
            )

        try:
            channel = int(channel_str)
            logging.debug(f"Channel selected: {channel}")
        except ValueError:
            print(f"\n! Invalid channel: {channel_str}")
            logging.error(f"Invalid channel value: {channel_str}")
            return

        logging.debug("Prompting for bandwidth")
        print("\nSelect bandwidth:")
        print("  1. 20 MHz")
        print("  2. 40 MHz")
        if band in ["5", "6"]:
            print("  3. 80 MHz")
        if band == "6":
            print("  4. 160 MHz")
        bw_choice = InputUtils.safe_input("Enter choice (default 1): ", default_value="1", context="bandwidth")
        bw_map = {"1": "20", "2": "40", "3": "80", "4": "160"}
        bandwidth = bw_map.get(bw_choice, "20")
        logging.debug(f"Bandwidth selected: {bandwidth} MHz (choice: {bw_choice})")

        if band == "24" and bandwidth not in ["20", "40"]:
            print(f"\n! Invalid bandwidth {bandwidth} for 2.4 GHz band")
            logging.error(f"Invalid bandwidth {bandwidth} for 2.4 GHz band")
            return

        logging.debug("Prompting for duration")
        duration_str = InputUtils.safe_input(
            "Enter capture duration in seconds (default 60, min 60, max 86400): ",
            default_value="60",
            context="duration",
        )
        try:
            duration = int(duration_str)
            if duration < 60 or duration > 86400:
                print("\n! Duration must be between 60 and 86400 seconds (API requirement)")
                logging.error(f"Duration out of range: {duration}")
                return
            logging.debug(f"Duration set: {duration} seconds")
        except ValueError:
            print(f"\n! Invalid duration: {duration_str}")
            logging.error(f"Invalid duration value: {duration_str}")
            return

        logging.debug("Prompting for packet count")
        num_packets_str = InputUtils.safe_input(
            "Enter number of packets (default 1024, max 10000): ", default_value="1024", context="num_packets"
        )
        try:
            num_packets = int(num_packets_str)
            if num_packets < 0 or num_packets > 10000:
                print("\n! Number of packets must be between 0 and 10000")
                logging.error(f"Packet count out of range: {num_packets}")
                return
            logging.debug(f"Packet count set: {num_packets}")
        except ValueError:
            print(f"\n! Invalid number of packets: {num_packets_str}")
            logging.error(f"Invalid packet count value: {num_packets_str}")
            return

        capture_format = manager._get_capture_format_selection()

        print("\nLoop Mode:")
        print("  Automatically start a new capture when the current one completes")
        print("  Downloads happen in background while next capture runs")
        loop_mode = InputUtils.safe_input(
            "Enable continuous loop mode? (y/n, default n): ", default_value="n", context="loop_mode"
        )
        enable_loop = loop_mode.lower() == "y"

        logging.debug("Building capture payload")
        payload = {
            "type": "scan",
            "ap_mac": ap_mac,
            "band": band,
            "channel": channel,
            "bandwidth": bandwidth,
            "duration": duration,
            "num_packets": num_packets,
            "format": capture_format,
            "max_pkt_len": 1300,
        }
        logging.debug(f"Payload constructed: {payload}")

        print("\n" + "=" * 80)
        print(" CAPTURE CONFIGURATION SUMMARY")
        print("=" * 80)
        print("  Capture Type: Scan Radio")
        print(f"  AP MAC: {ap_mac}")
        print(f"  Band: {band} GHz")
        print(f"  Channel: {channel}")
        print(f"  Bandwidth: {bandwidth} MHz")
        print(f"  Duration: {duration} seconds")
        print(f"  Packets: {num_packets}")
        print(f"  Loop Mode: {'ENABLED (continuous until Ctrl+C)' if enable_loop else 'Disabled (single capture)'}")
        print("=" * 80)

        logging.debug("Waiting for user confirmation")
        InputUtils.safe_input(
            "\nPress Enter to start capture (Ctrl+C to cancel): ", context="confirmation", allow_empty=True
        )

        print(f"\n> Checking for existing captures on AP {ap_mac}...")
        try:
            response = mistapi.api.v1.sites.pcaps.listSitePacketCaptures(manager.mist_session, site_id)
            if response.status_code == 200:
                existing_captures = response.data or []
                ap_has_capture = any(
                    cap.get("ap_mac", "").replace(":", "").replace("-", "").lower()
                    == ap_mac.replace(":", "").replace("-", "").lower()
                    for cap in existing_captures
                )
                if ap_has_capture:
                    print("\n! WARNING: This AP already has a capture in progress or recently completed")
                    print("  Mist only allows one capture per AP at a time")
                    print("  The new capture may fail with 'Recording already in progress'")
                    proceed = InputUtils.safe_input(
                        "\nContinue anyway? (y/n, default n): ",
                        default_value="n",
                        context="capture_conflict_confirmation",
                    ).lower()
                    if proceed != "y":
                        print("\n* Capture cancelled by user")
                        logging.info("User cancelled capture due to existing capture on AP")
                        return
        except Exception as error:
            logging.warning(f"Failed to check for existing captures: {error}")

        logging.info("User confirmed - executing site capture")
        if enable_loop:
            manager._execute_site_capture_loop(site_id, payload)
        else:
            manager._execute_site_capture(site_id, payload)

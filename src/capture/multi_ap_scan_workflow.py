"""Workflow extraction for multi-AP scan packet capture orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any


@dataclass
class MultiApScanCaptureWorkflow:
    """Run the multi-AP site scan capture workflow with compatibility-preserving prompts."""

    manager: Any
    mistapi_module: Any
    input_utils: Any
    device_utils: Any

    def _prompt_band(self) -> str:
        """Prompt for scan band and normalize to Mist API values."""
        logging.info(
            "Prompting operator for scan band selection"
        )  # Log before requesting user input for band selection.
        print("\nSelect band:")  # Show legacy header text so operator flow remains unchanged.
        print("  1. 2.4 GHz")  # Show legacy option 1 exactly as before for compatibility.
        print("  2. 5 GHz (default)")  # Show legacy default option exactly as before.
        print("  3. 6 GHz")  # Show legacy option 3 exactly as before for compatibility.
        band_choice = self.input_utils.safe_input(  # Capture operator input using safe input handling for EOF safety.
            "Enter choice [1-3] (default 2): ",
            default_value="2",
            context="band",
        )
        logging.debug(
            "Received band choice input value: %s", band_choice
        )  # Log raw operator choice for troubleshooting.
        band_map = {
            "1": "24",
            "2": "5",
            "3": "6",
            "24": "24",
            "5": "5",
            "6": "6",
        }  # Map menu choices to Mist API band values.
        resolved_band = band_map.get(band_choice, "5")  # Resolve to a safe default to preserve legacy behavior.
        logging.debug(
            "Resolved band selection to API value: %s", resolved_band
        )  # Log normalized band value after mapping.
        return resolved_band  # Return normalized band string used by downstream capture payload logic.

    def _prompt_channel(self, band: str) -> int | None:
        """Prompt for channel using legacy per-band prompt text."""
        logging.info(
            "Prompting operator for channel selection in band %s", band
        )  # Log before channel prompt so input context is explicit.
        if band == "24":
            channel_str = self.input_utils.safe_input(  # Request 2.4GHz channel using legacy bounded prompt text.
                "Enter channel (1-11, default 1): ",
                default_value="1",
                context="channel",
            )
        elif band == "5":
            channel_str = self.input_utils.safe_input(  # Request 5GHz channel using legacy bounded prompt text.
                "Enter channel (36-144, default 36): ",
                default_value="36",
                context="channel",
            )
        else:
            channel_str = self.input_utils.safe_input(  # Request 6GHz channel using legacy bounded prompt text.
                "Enter channel (1-233, default 1): ",
                default_value="1",
                context="channel",
            )
        try:
            channel_value = int(
                channel_str
            )  # Convert operator input into numeric channel value used by payload builder.
            logging.debug("Validated channel value: %s", channel_value)  # Log parsed channel value after conversion.
            return channel_value  # Return channel integer for downstream capture configuration.
        except ValueError:
            print(f"\n! Invalid channel: {channel_str}")  # Preserve legacy operator-facing invalid-channel message.
            logging.error(
                "Invalid channel input provided: %s", channel_str
            )  # Log conversion failure for troubleshooting invalid input.
            return None  # Return sentinel so caller can short-circuit execution safely.

    def _prompt_bandwidth(self, band: str) -> str:
        """Prompt for channel bandwidth preserving legacy options."""
        logging.info(
            "Prompting operator for bandwidth selection in band %s", band
        )  # Log before asking for bandwidth to preserve action traceability.
        print("\nSelect bandwidth:")  # Preserve legacy prompt header for bandwidth selection.
        print("  1. 20 MHz")  # Preserve legacy bandwidth option 1 text.
        print("  2. 40 MHz")  # Preserve legacy bandwidth option 2 text.
        if band in ["5", "6"]:
            print("  3. 80 MHz")  # Display 80MHz only for 5/6GHz bands to preserve legacy constraints.
        if band == "6":
            print("  4. 160 MHz")  # Display 160MHz only for 6GHz band as legacy behavior requires.
        bw_choice = self.input_utils.safe_input(  # Collect bandwidth selection with safe input handling.
            "Enter choice (default 1): ",
            default_value="1",
            context="bandwidth",
        )
        logging.debug(
            "Received bandwidth choice input value: %s", bw_choice
        )  # Log raw bandwidth selection for diagnostics.
        bw_map = {"1": "20", "2": "40", "3": "80", "4": "160"}  # Map UI choices to API width strings.
        resolved_bandwidth = bw_map.get(bw_choice, "20")  # Resolve to legacy default when input is unexpected.
        logging.debug(
            "Resolved bandwidth selection to API value: %s", resolved_bandwidth
        )  # Log normalized bandwidth value after mapping.
        return resolved_bandwidth  # Return normalized width for payload construction.

    def _prompt_duration(self) -> int | None:
        """Prompt for capture duration with legacy validation rules."""
        logging.info(
            "Prompting operator for capture duration"
        )  # Log before duration prompt for operator action traceability.
        duration_str = self.input_utils.safe_input(  # Request duration input while preserving safe EOF behavior.
            "Enter capture duration in seconds (default 60, min 60, max 86400): ",
            default_value="60",
            context="duration",
        )
        try:
            duration = int(duration_str)  # Convert textual input to integer for numeric validation and API payload use.
            if duration < 60 or duration > 86400:
                print(
                    "\n! Duration must be between 60 and 86400 seconds (API requirement)"
                )  # Preserve legacy validation message for operator clarity.
                logging.error(
                    "Duration input out of valid API range: %s", duration
                )  # Log validation failure to support incident troubleshooting.
                return None  # Return sentinel so caller exits early on invalid duration.
            logging.debug(
                "Validated capture duration value: %s", duration
            )  # Log accepted duration used for capture request.
            return duration  # Return validated duration so execution can continue.
        except ValueError:
            print(f"\n! Invalid duration: {duration_str}")  # Preserve legacy invalid-format message for operators.
            logging.error(
                "Invalid duration input provided: %s", duration_str
            )  # Log conversion failure for observability.
            return None  # Return sentinel to trigger safe early return in caller.

    def _prompt_num_packets(self) -> int | None:
        """Prompt for packet count preserving legacy validation."""
        logging.info(
            "Prompting operator for packet count"
        )  # Log before packet-count prompt for traceable interaction flow.
        num_packets_str = self.input_utils.safe_input(  # Request packet-count input while preserving EOF-safe behavior.
            "Enter number of packets (default 1024, max 10000): ",
            default_value="1024",
            context="num_packets",
        )
        try:
            num_packets = int(num_packets_str)  # Convert packet-count input to integer for range validation.
            if num_packets < 0 or num_packets > 10000:
                print(
                    "\n! Number of packets must be between 0 and 10000"
                )  # Preserve legacy range-error message for operator guidance.
                logging.error(
                    "Packet-count input out of valid range: %s", num_packets
                )  # Log rejected packet-count value.
                return None  # Return sentinel so caller safely aborts capture launch.
            logging.debug("Validated packet count value: %s", num_packets)  # Log accepted packet-count used in payload.
            return num_packets  # Return validated packet count for payload assembly.
        except ValueError:
            print(
                f"\n! Invalid number of packets: {num_packets_str}"
            )  # Preserve legacy invalid-format message for operator feedback.
            logging.error(
                "Invalid packet-count input provided: %s", num_packets_str
            )  # Log conversion failure for diagnostics.
            return None  # Return sentinel to maintain safe early-exit behavior.

    def _build_payload(
        self,
        ap_macs: list[str],
        band: str,
        channel: int,
        bandwidth: str,
        duration: int,
        num_packets: int,
        capture_format: str,
    ) -> dict[str, Any]:
        """Build the legacy single-call multi-AP scan payload."""
        logging.info(
            "Building multi-AP capture payload for %d APs", len(ap_macs)
        )  # Log before payload assembly so operators can trace request creation.
        aps_dict: dict[str, dict[str, str]] = (
            {}
        )  # Initialize per-AP configuration map required by Mist scan payload schema.
        for ap_mac in ap_macs:  # Iterate AP inventory to populate each AP capture specification.
            normalized_mac = self.manager.normalize_mac_address(
                ap_mac
            )  # Normalize MAC format to prevent payload mismatches.
            aps_dict[normalized_mac] = {
                "band": band,
                "channel": str(channel),
                "width": str(bandwidth),
            }  # Attach per-AP radio configuration while preserving legacy schema.
        payload = {  # Build full scan payload that mirrors legacy single-call multi-AP contract.
            "type": "scan",
            "band": band,
            "channel": channel,
            "bandwidth": bandwidth,
            "duration": duration,
            "num_packets": num_packets,
            "format": capture_format,
            "max_pkt_len": 1300,
            "aps": aps_dict,
        }
        logging.debug(
            "Multi-AP payload constructed for %d APs", len(ap_macs)
        )  # Log payload completion summary without exposing sensitive data.
        return payload  # Return payload to caller for API invocation.

    def _display_summary(
        self,
        ap_count: int,
        band: str,
        channel: int,
        bandwidth: str,
        duration: int,
        num_packets: int,
        capture_format: str,
    ) -> None:
        """Print legacy multi-AP capture summary text."""
        logging.info("Displaying multi-AP capture configuration summary")  # Log before emitting operator summary block.
        print("\n" + "=" * 80)  # Render legacy visual separator used in CLI output.
        print(" MULTI-AP CAPTURE CONFIGURATION SUMMARY")  # Render legacy summary title for operator clarity.
        print("=" * 80)  # Render legacy visual separator for readability.
        print("  Capture Type: Scan Radio (All APs)")  # Display fixed capture type to confirm workflow mode.
        print(f"  Number of APs: {ap_count}")  # Display AP count so operator can validate selection scope.
        print(f"  Band: {band} GHz")  # Display band so operator can verify RF target.
        print(f"  Channel: {channel}")  # Display channel so operator can verify RF target.
        print(f"  Bandwidth: {bandwidth} MHz")  # Display bandwidth so operator can verify capture width.
        print(f"  Duration: {duration} seconds")  # Display duration so operator can verify runtime expectation.
        print(f"  Packets: {num_packets}")  # Display packet limit so operator can verify capture volume.
        print(f"  Format: {capture_format}")  # Display output format so operator can verify post-capture handling.
        print("=" * 80)  # Render legacy closing separator to delimit summary block.
        logging.debug(
            "Displayed summary for %d APs with format %s", ap_count, capture_format
        )  # Log summary contents at a high level for auditability.

    def _check_existing_captures(self, site_id: str) -> None:
        """Run a non-blocking courtesy lookup for existing site captures."""
        logging.info("Checking for existing site captures before launch")  # Log before courtesy API check.
        try:
            response = self.mistapi_module.api.v1.sites.pcaps.listSitePacketCaptures(
                self.manager.mist_session, site_id
            )  # Query current site capture list to surface potential conflicts.
            logging.debug(
                "Existing-capture lookup returned HTTP status %s", response.status_code
            )  # Log API response status.
            if response.status_code == 200:
                existing_captures = response.data or []  # Normalize empty data to list.
                if existing_captures:
                    logging.debug(
                        "%d capture(s) already in progress or recently completed", len(existing_captures)
                    )  # Log discovered captures for operator diagnostics.
        except Exception as check_error:
            logging.debug(
                "Could not check for existing captures: %s", check_error
            )  # Keep failure non-blocking to preserve legacy semantics.

    def _gather_capture_config(self) -> dict[str, Any] | None:
        """Prompt operator for capture parameters; return config dict or None on abort."""
        band = self._prompt_band()  # Prompt for band first per legacy flow.
        channel = self._prompt_channel(band)  # Prompt for channel constrained by band.
        if channel is None:
            logging.warning("Channel selection invalid; aborting multi-AP capture workflow")  # Log abort reason.
            return None  # Abort on invalid channel input.
        bandwidth = self._prompt_bandwidth(band)  # Prompt for bandwidth after channel.
        duration = self._prompt_duration()  # Prompt for duration with bounds validation.
        if duration is None:
            logging.warning("Duration selection invalid; aborting multi-AP capture workflow")  # Log abort reason.
            return None  # Abort on invalid duration.
        num_packets = self._prompt_num_packets()  # Prompt for packet limit.
        if num_packets is None:
            logging.warning("Packet-count selection invalid; aborting multi-AP capture workflow")  # Log abort.
            return None  # Abort on invalid packet count.
        logging.info("Prompting operator for capture format selection")  # Log before format prompt.
        capture_format = self.manager._get_capture_format_selection()  # Resolve capture format.
        logging.debug("Selected capture format: %s", capture_format)  # Log chosen format.
        return {
            "band": band,
            "channel": channel,
            "bandwidth": bandwidth,
            "duration": duration,
            "num_packets": num_packets,
            "capture_format": capture_format,
        }  # Return aggregated config consumed by launch logic.

    def _post_launch_action(self, capture_format: str, site_id: str, capture_id: str, duration: int) -> None:
        """Dispatch post-launch wait/download or stream-subscribe based on capture format."""
        if capture_format == "pcap":
            print("\n> Waiting for PCAP file to be ready...")  # Preserve legacy wait message.
            print("  This may take a few moments after capture completes.")  # Preserve legacy expectation message.
            logging.info(
                "Delegating to site PCAP wait/download workflow for capture_id=%s", capture_id
            )  # Log before wait/download action.
            self.manager._wait_and_download_pcap(site_id, capture_id, duration)  # Trigger wait/download.
            logging.debug("Site PCAP wait/download workflow finished for capture_id=%s", capture_id)  # Log completion.
        elif capture_format == "stream":
            print(
                "\n> Stream format selected - subscribe to WebSocket for real-time data"
            )  # Preserve legacy stream guidance text.
            logging.info(
                "Delegating to site capture stream subscription for capture_id=%s", capture_id
            )  # Log before stream subscription.
            self.manager._subscribe_to_site_capture_stream(site_id, capture_id)  # Trigger stream subscription.
            logging.debug(
                "Site capture stream subscription flow completed for capture_id=%s", capture_id
            )  # Log stream completion.

    def _handle_launch_success(
        self, result: dict[str, Any], site_id: str, ap_macs: list[str], capture_format: str, duration: int
    ) -> None:
        """Print success output, export metadata, and dispatch post-launch action."""
        capture_id = result.get("id", "unknown")  # Extract capture identifier with safe fallback.
        ap_count = result.get("ap_count", len(ap_macs))  # Extract AP count with fallback to requested size.
        print("\n* Multi-AP capture started successfully!")  # Preserve legacy success banner.
        print(f"  Capture ID: {capture_id}")  # Preserve legacy capture-id output.
        print(f"  AP Count: {ap_count}")  # Preserve AP count output.
        print(f"  Format: {capture_format}")  # Preserve format output.
        print(f"  Duration: {duration} seconds")  # Preserve duration output.
        print(f"  Expires: {result.get('expiry', 'unknown')}")  # Preserve expiry output.
        logging.info(
            "Multi-AP capture started: capture_id=%s, ap_count=%s", capture_id, ap_count
        )  # Log capture start summary.
        logging.info("Exporting capture metadata to output backend")  # Log before metadata export.
        self.manager._export_capture_info_to_csv(result, "site", site_id)  # Persist capture metadata.
        logging.debug("Capture metadata export completed for capture_id=%s", capture_id)  # Log export completion.
        self._post_launch_action(capture_format, site_id, capture_id, duration)  # Dispatch on format.

    def _handle_launch_error(self, response: Any) -> None:
        """Print legacy error guidance for failed startSitePacketCapture responses."""
        error_details = response.data if hasattr(response, "data") else "Unknown error"  # Normalize error details.
        is_conflict = (
            response.status_code == 400
            and isinstance(error_details, dict)
            and "Recording already in progress" in error_details.get("detail", "")
        )  # Identify legacy conflict path.
        if is_conflict:
            print("\n! Capture(s) already in progress on one or more APs")  # Preserve legacy conflict message.
            print("  Mist only allows one capture per AP at a time")  # Preserve legacy limitation message.
            print(
                "  Wait for existing captures to complete or check Mist portal to stop them"
            )  # Preserve legacy remediation guidance.
        else:
            print(f"\n! Failed to start capture: {response.status_code}")  # Preserve generic failure message.
            print(f"  Error details: {error_details}")  # Preserve detailed error output.
        logging.error(
            "Multi-AP capture failed: %s - %s", response.status_code, error_details
        )  # Log API failure outcome.

    def _launch_capture(self, site_id: str, ap_macs: list[str], config: dict[str, Any]) -> None:
        """Build payload, call startSitePacketCapture, and dispatch success/error handlers."""
        print(
            f"\n> Launching multi-AP capture for {len(ap_macs)} APs with single API call..."
        )  # Preserve launch message.
        payload = self._build_payload(
            ap_macs,
            config["band"],
            config["channel"],
            config["bandwidth"],
            config["duration"],
            config["num_packets"],
            config["capture_format"],
        )  # Build full payload used by API call.
        logging.debug("Payload ready for startSitePacketCapture request")  # Log payload readiness.
        try:
            logging.info("Calling startSitePacketCapture for site %s", site_id)  # Log before primary API action.
            response = self.mistapi_module.api.v1.sites.pcaps.startSitePacketCapture(
                self.manager.mist_session, site_id, payload
            )  # Invoke start API.
            logging.debug("startSitePacketCapture returned HTTP status %s", response.status_code)  # Log API status.
            if response.status_code == 200:
                self._handle_launch_success(
                    response.data, site_id, ap_macs, config["capture_format"], config["duration"]
                )  # Dispatch success path.
            else:
                self._handle_launch_error(response)  # Dispatch error path.
        except Exception as error:
            print(f"\n! Error starting multi-AP capture: {error}")  # Preserve legacy exception message.
            logging.exception("Exception launching multi-AP capture: %s", error)  # Log exception with traceback.

    def run(self, site_id: str) -> None:
        """Execute the extracted multi-AP scan capture workflow."""
        logging.info("Starting multi-AP scan capture for site: %s", site_id)  # Log workflow start.
        logging.info("Fetching AP MAC inventory for site %s", site_id)  # Log before inventory lookup.
        ap_macs = self.device_utils.get_all_ap_macs_from_site(site_id)  # Retrieve AP MACs.
        logging.debug("Retrieved %d AP MAC addresses for site %s", len(ap_macs), site_id)  # Log inventory result.
        if not ap_macs:
            print("\n! No APs found at site")  # Preserve legacy no-AP message.
            logging.warning("No AP MACs found for site %s; aborting workflow", site_id)  # Log early-exit reason.
            return  # Exit early because no APs means no valid targets.
        print(f"\n* Found {len(ap_macs)} APs at site")  # Preserve legacy success message with AP count.
        print("  Checking for existing captures...")  # Preserve operator cue before courtesy check.
        self._check_existing_captures(site_id)  # Run non-blocking courtesy check.
        print(f"  Preparing to launch {len(ap_macs)} simultaneous captures...")  # Preserve operator cue before prompts.
        print("\n" + "-" * 80)  # Preserve legacy section separator.
        print(" SCAN RADIO CAPTURE CONFIGURATION (All APs)")  # Preserve legacy configuration header.
        print("-" * 80)  # Preserve legacy section separator.
        config = self._gather_capture_config()  # Prompt for full capture configuration.
        if config is None:
            return  # Abort on invalid operator input.
        self._display_summary(
            len(ap_macs),
            config["band"],
            config["channel"],
            config["bandwidth"],
            config["duration"],
            config["num_packets"],
            config["capture_format"],
        )  # Display configuration summary before final confirmation.
        logging.info(
            "Requesting final operator confirmation before starting capture"
        )  # Log before confirmation prompt.
        self.input_utils.safe_input(  # Pause for explicit operator confirmation.
            f"\nPress Enter to start capture for {len(ap_macs)} APs (Ctrl+C to cancel): ",
            context="confirmation",
            allow_empty=True,
        )
        logging.debug(
            "Operator confirmation received; proceeding with multi-AP capture launch"
        )  # Log confirmation completion.
        self._launch_capture(site_id, ap_macs, config)  # Launch capture and handle response.
        logging.info("Multi-AP scan capture function completed")  # Log workflow completion boundary.

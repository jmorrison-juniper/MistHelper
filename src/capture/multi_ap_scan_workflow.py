"""Workflow extraction for multi-AP scan packet capture orchestration."""

from __future__ import annotations  # WHY: Defer annotation evaluation so forward references stay lightweight.

import logging  # WHY: Emit structured diagnostics consistent with sibling capture workflows.
from dataclasses import dataclass  # WHY: Use frozen dataclasses for immutable value-object semantics.
from typing import Any  # WHY: Preserve legacy DI collaborator typing without leaking concrete classes.

_SEP_WIDE = "=" * 80  # WHY: Reuse legacy summary separator without duplicating literal in every print call.
_SEP_SECTION = "-" * 80  # WHY: Reuse legacy section separator without duplicating literal in every print call.
_BAND_CHOICES = (
    {  # WHY: Central band-choice table replaces branching to shrink prompt handler and stay legacy-compatible.
        "1": "24",
        "2": "5",
        "3": "6",
        "24": "24",
        "5": "5",
        "6": "6",
    }
)
_BAND_DEFAULT = "5"  # WHY: Legacy fallback band value preserved as module constant for reuse.
_BW_CHOICES = {
    "1": "20",
    "2": "40",
    "3": "80",
    "4": "160",
}  # WHY: Legacy bandwidth mapping preserved as module constant.
_BW_DEFAULT = "20"  # WHY: Legacy fallback bandwidth preserved as module constant.
_CHANNEL_SPECS: dict[str, tuple[str, str]] = {  # WHY: Table of band-specific channel prompts eliminates if/elif chain.
    "24": ("Enter channel (1-11, default 1): ", "1"),
    "5": ("Enter channel (36-144, default 36): ", "36"),
    "6": ("Enter channel (1-233, default 1): ", "1"),
}
_MIN_DURATION_SEC = 60  # WHY: Legacy minimum capture duration required by the Mist API contract.
_MAX_DURATION_SEC = 86400  # WHY: Legacy maximum capture duration accepted by the Mist API contract.
_MAX_PACKETS = 10000  # WHY: Legacy maximum packet count accepted by the Mist API contract.
_DEFAULT_MAX_PKT_LEN = 1300  # WHY: Legacy default max packet length embedded in scan payload.


@dataclass(frozen=True, slots=True)  # WHY: Frozen spec keeps parse helper under param limit while grouping messaging.
class BoundedIntSpec:  # WHY: Group bounded-int parse parameters into a single immutable value.
    """Immutable spec describing bounds and legacy operator messages for bounded-int parsing."""

    low: int  # WHY: Inclusive lower bound applied during range check.
    high: int  # WHY: Inclusive upper bound applied during range check.
    range_msg: str  # WHY: Legacy console message when the value is outside the accepted range.
    invalid_msg: str  # WHY: Legacy console message when the value cannot be parsed as int.
    range_log: str  # WHY: Log format string used when the value falls outside the accepted range.
    invalid_log: str  # WHY: Log format string used when integer parsing fails.


@dataclass(frozen=True, slots=True)  # WHY: Frozen slots collapse 6 payload/display arguments into one value object.
class CaptureConfig:  # WHY: Value object aggregating operator-selected capture parameters.
    """Immutable capture configuration collected from operator prompts."""

    band: str  # WHY: Normalized Mist API band string used in payload and summary.
    channel: int  # WHY: Numeric channel value used in payload and summary.
    bandwidth: str  # WHY: Normalized bandwidth string used in payload and summary.
    duration: int  # WHY: Validated capture duration in seconds.
    num_packets: int  # WHY: Validated packet count for capture payload.
    capture_format: str  # WHY: Selected capture format string (pcap/stream) driving post-launch dispatch.


@dataclass  # WHY: Mutable holder for injected collaborators keeps legacy constructor signature intact.
class MultiApScanCaptureWorkflow:
    """Run the multi-AP site scan capture workflow with compatibility-preserving prompts."""

    manager: Any  # WHY: Provides session, MAC normalization, format selection, and export helpers.
    mistapi_module: Any  # WHY: Mist REST client wrapper used to invoke site capture endpoints.
    input_utils: Any  # WHY: Safe-input helper providing EOF-tolerant operator prompts.
    device_utils: Any  # WHY: Site inventory helper providing AP MAC discovery.

    def _prompt_band(self) -> str:  # WHY: Resolve operator band selection to a normalized Mist API string.
        """Prompt for scan band and normalize to Mist API values."""
        logging.info("Prompting operator for scan band selection")  # WHY: Record band-prompt entry for traceability.
        print("\nSelect band:")  # WHY: Preserve legacy header text.
        print("  1. 2.4 GHz")  # WHY: Preserve legacy option 1 text.
        print("  2. 5 GHz (default)")  # WHY: Preserve legacy default option text.
        print("  3. 6 GHz")  # WHY: Preserve legacy option 3 text.
        choice = self.input_utils.safe_input(  # WHY: Capture operator choice with EOF-safe helper.
            "Enter choice [1-3] (default 2): ", default_value="2", context="band"
        )
        resolved = _BAND_CHOICES.get(choice, _BAND_DEFAULT)  # WHY: Normalize via table + legacy default fallback.
        logging.debug("Resolved band selection to API value: %s", resolved)  # WHY: Record normalized band value.
        return resolved  # WHY: Return normalized band string used by downstream payload logic.

    def _prompt_channel(self, band: str) -> int | None:  # WHY: Resolve band-specific operator channel selection.
        """Prompt for channel using legacy per-band prompt text."""
        prompt_text, default_value = _CHANNEL_SPECS.get(band, _CHANNEL_SPECS["6"])  # WHY: Look up prompt text.
        logging.info("Prompting operator for channel selection in band %s", band)  # WHY: Trace channel-prompt entry.
        channel_str = self.input_utils.safe_input(  # WHY: Capture operator channel value with EOF-safe helper.
            prompt_text, default_value=default_value, context="channel"
        )
        return self._parse_channel(channel_str)  # WHY: Delegate integer conversion + error reporting.

    def _parse_channel(self, channel_str: str) -> int | None:  # WHY: Convert channel text with legacy error handling.
        """Convert channel text to int or emit legacy invalid-channel message."""
        try:
            channel_value = int(channel_str)  # WHY: Convert operator input into numeric channel value.
        except ValueError:
            print(f"\n! Invalid channel: {channel_str}")  # WHY: Preserve legacy operator-facing error message.
            logging.error("Invalid channel input provided: %s", channel_str)  # WHY: Log conversion failure.
            return None  # WHY: Sentinel so caller can short-circuit execution safely.
        logging.debug("Validated channel value: %s", channel_value)  # WHY: Log parsed channel for diagnostics.
        return channel_value  # WHY: Return numeric channel for downstream capture configuration.

    def _prompt_bandwidth(self, band: str) -> str:  # WHY: Resolve band-constrained operator bandwidth selection.
        """Prompt for channel bandwidth preserving legacy options."""
        logging.info("Prompting operator for bandwidth selection in band %s", band)  # WHY: Trace bandwidth prompt.
        self._print_bandwidth_menu(band)  # WHY: Emit legacy menu, band-constrained.
        choice = self.input_utils.safe_input(  # WHY: Capture bandwidth selection with EOF-safe helper.
            "Enter choice (default 1): ", default_value="1", context="bandwidth"
        )
        resolved = _BW_CHOICES.get(choice, _BW_DEFAULT)  # WHY: Map choice to legacy width string with default.
        logging.debug("Resolved bandwidth selection to API value: %s", resolved)  # WHY: Log normalized bandwidth.
        return resolved  # WHY: Return normalized width for payload construction.

    def _print_bandwidth_menu(self, band: str) -> None:  # WHY: Emit legacy bandwidth menu based on band constraints.
        """Print legacy bandwidth options constrained by band."""
        print("\nSelect bandwidth:")  # WHY: Preserve legacy header text.
        print("  1. 20 MHz")  # WHY: Preserve legacy option 1 text.
        print("  2. 40 MHz")  # WHY: Preserve legacy option 2 text.
        if band in {"5", "6"}:  # WHY: 80MHz only valid on 5/6GHz per legacy constraints.
            print("  3. 80 MHz")  # WHY: Preserve legacy option 3 text.
        if band == "6":  # WHY: 160MHz only valid on 6GHz per legacy constraints.
            print("  4. 160 MHz")  # WHY: Preserve legacy option 4 text.

    def _prompt_duration(self) -> int | None:  # WHY: Resolve validated operator capture duration.
        """Prompt for capture duration with legacy validation rules."""
        logging.info("Prompting operator for capture duration")  # WHY: Trace duration prompt entry.
        duration_str = self.input_utils.safe_input(  # WHY: Capture duration input with EOF-safe helper.
            "Enter capture duration in seconds (default 60, min 60, max 86400): ",
            default_value="60",
            context="duration",
        )
        spec = BoundedIntSpec(  # WHY: Package duration bounds and legacy messages for shared parse helper.
            low=_MIN_DURATION_SEC,
            high=_MAX_DURATION_SEC,
            range_msg="\n! Duration must be between 60 and 86400 seconds (API requirement)",
            invalid_msg=f"\n! Invalid duration: {duration_str}",
            range_log="Duration input out of valid API range: %s",
            invalid_log="Invalid duration input provided: %s",
        )
        return self._parse_bounded_int(duration_str, spec)  # WHY: Delegate parsing + range validation.

    def _prompt_num_packets(self) -> int | None:  # WHY: Resolve validated operator packet-count selection.
        """Prompt for packet count preserving legacy validation."""
        logging.info("Prompting operator for packet count")  # WHY: Trace packet-count prompt entry.
        packets_str = self.input_utils.safe_input(  # WHY: Capture packet-count input with EOF-safe helper.
            "Enter number of packets (default 1024, max 10000): ",
            default_value="1024",
            context="num_packets",
        )
        spec = BoundedIntSpec(  # WHY: Package packet-count bounds and legacy messages for shared parse helper.
            low=0,
            high=_MAX_PACKETS,
            range_msg="\n! Number of packets must be between 0 and 10000",
            invalid_msg=f"\n! Invalid number of packets: {packets_str}",
            range_log="Packet-count input out of valid range: %s",
            invalid_log="Invalid packet-count input provided: %s",
        )
        return self._parse_bounded_int(packets_str, spec)  # WHY: Delegate parsing + range validation.

    def _parse_bounded_int(self, raw: str, spec: BoundedIntSpec) -> int | None:  # WHY: Shared parse + range check.
        """Convert raw string to bounded int. Emit legacy messages on failure."""
        try:
            value = int(raw)  # WHY: Convert textual input to integer for numeric validation.
        except ValueError:
            print(spec.invalid_msg)  # WHY: Preserve legacy invalid-format message for operators.
            logging.error(spec.invalid_log, raw)  # WHY: Log conversion failure for observability.
            return None  # WHY: Sentinel to trigger safe early return in caller.
        if value < spec.low or value > spec.high:  # WHY: Enforce legacy inclusive range check.
            print(spec.range_msg)  # WHY: Preserve legacy validation message for operator clarity.
            logging.error(spec.range_log, value)  # WHY: Log validation failure for troubleshooting.
            return None  # WHY: Sentinel so caller exits early on invalid value.
        logging.debug("Validated bounded int value: %s", value)  # WHY: Log accepted value for diagnostics.
        return value  # WHY: Return validated integer for downstream use.

    def _build_payload(  # WHY: Convert config + AP inventory into legacy single-call multi-AP scan payload.
        self, ap_macs: list[str], config: CaptureConfig
    ) -> dict[str, Any]:
        """Build the legacy single-call multi-AP scan payload."""
        logging.info("Building multi-AP capture payload for %d APs", len(ap_macs))  # WHY: Trace payload build entry.
        aps_dict = self._build_aps_dict(ap_macs, config)  # WHY: Delegate per-AP dict construction.
        payload: dict[str, Any] = {  # WHY: Mirror legacy scan payload contract exactly.
            "type": "scan",
            "band": config.band,
            "channel": config.channel,
            "bandwidth": config.bandwidth,
            "duration": config.duration,
            "num_packets": config.num_packets,
            "format": config.capture_format,
            "max_pkt_len": _DEFAULT_MAX_PKT_LEN,
            "aps": aps_dict,
        }
        logging.debug("Multi-AP payload constructed for %d APs", len(ap_macs))  # WHY: Log completion without secrets.
        return payload  # WHY: Return payload for API invocation.

    def _build_aps_dict(  # WHY: Isolate per-AP normalization so payload builder stays within length limits.
        self, ap_macs: list[str], config: CaptureConfig
    ) -> dict[str, dict[str, str]]:
        """Build the per-AP radio configuration map required by the Mist scan payload schema."""
        aps_dict: dict[str, dict[str, str]] = {}  # WHY: Initialize per-AP configuration map.
        for ap_mac in ap_macs:  # WHY: Iterate AP inventory to populate each AP capture specification.
            normalized = self.manager.normalize_mac_address(ap_mac)  # WHY: Normalize MAC to prevent mismatches.
            aps_dict[normalized] = {  # WHY: Attach per-AP radio config using legacy schema keys.
                "band": config.band,
                "channel": str(config.channel),
                "width": str(config.bandwidth),
            }
        return aps_dict  # WHY: Return complete per-AP dict for payload assembly.

    def _display_summary(self, ap_count: int, config: CaptureConfig) -> None:  # WHY: Emit operator-facing summary.
        """Print legacy multi-AP capture summary text."""
        logging.info("Displaying multi-AP capture configuration summary")  # WHY: Trace summary emission entry.
        print("\n" + _SEP_WIDE)  # WHY: Render legacy visual separator.
        print(" MULTI-AP CAPTURE CONFIGURATION SUMMARY")  # WHY: Render legacy title text.
        print(_SEP_WIDE)  # WHY: Render legacy separator for readability.
        print("  Capture Type: Scan Radio (All APs)")  # WHY: Confirm capture workflow mode to operator.
        print(f"  Number of APs: {ap_count}")  # WHY: Confirm AP selection scope to operator.
        print(f"  Band: {config.band} GHz")  # WHY: Confirm RF band target to operator.
        print(f"  Channel: {config.channel}")  # WHY: Confirm RF channel target to operator.
        print(f"  Bandwidth: {config.bandwidth} MHz")  # WHY: Confirm capture width to operator.
        print(f"  Duration: {config.duration} seconds")  # WHY: Confirm runtime expectation to operator.
        print(f"  Packets: {config.num_packets}")  # WHY: Confirm capture volume to operator.
        print(f"  Format: {config.capture_format}")  # WHY: Confirm output format to operator.
        print(_SEP_WIDE)  # WHY: Render legacy closing separator.
        logging.debug("Displayed summary for %d APs (%s)", ap_count, config.capture_format)  # WHY: Log summary.

    def _check_existing_captures(self, site_id: str) -> None:  # WHY: Courtesy lookup for existing site captures.
        """Run a non-blocking courtesy lookup for existing site captures."""
        logging.info("Checking for existing site captures before launch")  # WHY: Trace courtesy check entry.
        try:
            response = self.mistapi_module.api.v1.sites.pcaps.listSitePacketCaptures(  # WHY: Query current captures.
                self.manager.mist_session, site_id
            )
        except Exception as check_error:  # WHY: Keep failure non-blocking to preserve legacy semantics.
            logging.debug("Could not check for existing captures: %s", check_error)  # WHY: Log non-blocking failure.
            return  # WHY: Exit courtesy check silently on failure per legacy behavior.
        logging.debug("Existing-capture lookup returned HTTP status %s", response.status_code)  # WHY: Log status.
        if response.status_code == 200:  # WHY: Only inspect payload on success per legacy behavior.
            existing = response.data or []  # WHY: Normalize empty data to list for len().
            if existing:  # WHY: Emit diagnostic only when conflicting captures exist.
                logging.debug("%d capture(s) already in progress or recently completed", len(existing))  # WHY: Log.

    def _gather_capture_config(self) -> CaptureConfig | None:  # WHY: Sequence operator prompts and validate output.
        """Prompt operator for capture parameters. Return CaptureConfig or None on abort."""
        band = self._prompt_band()  # WHY: Prompt for band first per legacy flow.
        channel = self._prompt_channel(band)  # WHY: Prompt for channel constrained by band.
        if channel is None:  # WHY: Abort early when channel input is invalid.
            logging.warning("Channel selection invalid; aborting multi-AP capture workflow")  # WHY: Log abort.
            return None  # WHY: Signal caller to short-circuit.
        bandwidth = self._prompt_bandwidth(band)  # WHY: Prompt for bandwidth after channel.
        duration = self._prompt_duration()  # WHY: Prompt for duration with bounds validation.
        if duration is None:  # WHY: Abort early when duration input is invalid.
            logging.warning("Duration selection invalid; aborting multi-AP capture workflow")  # WHY: Log abort.
            return None  # WHY: Signal caller to short-circuit.
        num_packets = self._prompt_num_packets()  # WHY: Prompt for packet limit with bounds validation.
        if num_packets is None:  # WHY: Abort early when packet count is invalid.
            logging.warning("Packet-count selection invalid; aborting multi-AP capture workflow")  # WHY: Log abort.
            return None  # WHY: Signal caller to short-circuit.
        capture_format = self.manager._get_capture_format_selection()  # WHY: Resolve capture format via manager.
        logging.debug("Selected capture format: %s", capture_format)  # WHY: Log chosen format for diagnostics.
        return CaptureConfig(band, channel, bandwidth, duration, num_packets, capture_format)  # WHY: Aggregate.

    def _post_launch_action(  # WHY: Dispatch wait/download vs stream subscription based on capture format.
        self, capture_format: str, site_id: str, capture_id: str, duration: int
    ) -> None:
        """Dispatch post-launch wait/download or stream-subscribe based on capture format."""
        if capture_format == "pcap":  # WHY: Preserve legacy pcap-format branch.
            print("\n> Waiting for PCAP file to be ready...")  # WHY: Preserve legacy wait message.
            print("  This may take a few moments after capture completes.")  # WHY: Preserve legacy expectation.
            logging.info("Delegating to site PCAP wait/download for capture_id=%s", capture_id)  # WHY: Log.
            self.manager._wait_and_download_pcap(site_id, capture_id, duration)  # WHY: Invoke wait/download.
            logging.debug("Site PCAP wait/download finished for capture_id=%s", capture_id)  # WHY: Log completion.
        elif capture_format == "stream":  # WHY: Preserve legacy stream-format branch.
            print("\n> Stream format selected - subscribe to WebSocket for real-time data")  # WHY: Preserve message.
            logging.info("Delegating to site capture stream subscription for capture_id=%s", capture_id)  # WHY: Log.
            self.manager._subscribe_to_site_capture_stream(site_id, capture_id)  # WHY: Invoke stream subscription.
            logging.debug("Site capture stream subscription completed for capture_id=%s", capture_id)  # WHY: Log.

    def _handle_launch_success(  # WHY: Print success output, export metadata, and dispatch post-launch action.
        self, result: dict[str, Any], site_id: str, ap_macs: list[str], config: CaptureConfig
    ) -> None:
        """Print success output, export metadata, and dispatch post-launch action."""
        capture_id = result.get("id", "unknown")  # WHY: Extract capture identifier with legacy fallback.
        ap_count = result.get("ap_count", len(ap_macs))  # WHY: Extract AP count with fallback to requested size.
        print("\n* Multi-AP capture started successfully!")  # WHY: Preserve legacy success banner.
        print(f"  Capture ID: {capture_id}")  # WHY: Preserve legacy capture-id output.
        print(f"  AP Count: {ap_count}")  # WHY: Preserve legacy AP count output.
        print(f"  Format: {config.capture_format}")  # WHY: Preserve legacy format output.
        print(f"  Duration: {config.duration} seconds")  # WHY: Preserve legacy duration output.
        print(f"  Expires: {result.get('expiry', 'unknown')}")  # WHY: Preserve legacy expiry output.
        logging.info("Multi-AP capture started: capture_id=%s ap_count=%s", capture_id, ap_count)  # WHY: Log.
        self.manager._export_capture_info_to_csv(result, "site", site_id)  # WHY: Persist capture metadata.
        logging.debug("Capture metadata export completed for capture_id=%s", capture_id)  # WHY: Log export end.
        self._post_launch_action(config.capture_format, site_id, capture_id, config.duration)  # WHY: Dispatch.

    def _handle_launch_error(self, response: Any) -> None:  # WHY: Emit legacy operator guidance for API failures.
        """Print legacy error guidance for failed startSitePacketCapture responses."""
        error_details = response.data if hasattr(response, "data") else "Unknown error"  # WHY: Normalize details.
        is_conflict = (  # WHY: Identify legacy conflict path when Mist reports existing capture on any AP.
            response.status_code == 400
            and isinstance(error_details, dict)
            and "Recording already in progress" in error_details.get("detail", "")
        )
        if is_conflict:  # WHY: Preserve legacy conflict-specific messaging.
            print("\n! Capture(s) already in progress on one or more APs")  # WHY: Preserve conflict message.
            print("  Mist only allows one capture per AP at a time")  # WHY: Preserve limitation message.
            print("  Wait for existing captures to complete or check Mist portal to stop them")  # WHY: Guidance.
        else:  # WHY: Fall back to generic failure output for non-conflict errors.
            print(f"\n! Failed to start capture: {response.status_code}")  # WHY: Preserve generic failure output.
            print(f"  Error details: {error_details}")  # WHY: Preserve detailed error output.
        logging.error("Multi-AP capture failed: %s - %s", response.status_code, error_details)  # WHY: Log outcome.

    def _launch_capture(  # WHY: Build payload, invoke start API, dispatch success/error handling.
        self, site_id: str, ap_macs: list[str], config: CaptureConfig
    ) -> None:
        """Build payload, call startSitePacketCapture, and dispatch success/error handlers."""
        print(f"\n> Launching multi-AP capture for {len(ap_macs)} APs with single API call...")  # WHY: Legacy msg.
        payload = self._build_payload(ap_macs, config)  # WHY: Assemble legacy payload for API call.
        logging.debug("Payload ready for startSitePacketCapture request")  # WHY: Log payload readiness.
        try:
            logging.info("Calling startSitePacketCapture for site %s", site_id)  # WHY: Trace API call entry.
            response = self.mistapi_module.api.v1.sites.pcaps.startSitePacketCapture(  # WHY: Invoke start API.
                self.manager.mist_session, site_id, payload
            )
        except Exception as error:  # WHY: Preserve legacy exception handling with operator-facing message.
            print(f"\n! Error starting multi-AP capture: {error}")  # WHY: Preserve legacy exception message.
            logging.exception("Exception launching multi-AP capture: %s", error)  # WHY: Log traceback.
            return  # WHY: Exit early after logging the exception per legacy behavior.
        logging.debug("startSitePacketCapture returned HTTP status %s", response.status_code)  # WHY: Log status.
        if response.status_code == 200:  # WHY: 200 signals successful launch per legacy contract.
            self._handle_launch_success(response.data, site_id, ap_macs, config)  # WHY: Success branch dispatch.
        else:  # WHY: Non-200 dispatches legacy error-handling path.
            self._handle_launch_error(response)  # WHY: Emit legacy error guidance and log outcome.

    def _print_prep_header(self, ap_count: int) -> None:  # WHY: Emit legacy pre-config header block to operator.
        """Emit legacy pre-configuration header lines shown before prompts."""
        print(f"\n* Found {ap_count} APs at site")  # WHY: Preserve legacy AP-count success message.
        print("  Checking for existing captures...")  # WHY: Preserve legacy courtesy-check cue.

    def _print_config_header(self, ap_count: int) -> None:  # WHY: Emit legacy configuration banner to operator.
        """Emit legacy configuration header block shown before prompts."""
        print(f"  Preparing to launch {ap_count} simultaneous captures...")  # WHY: Preserve legacy prep cue.
        print("\n" + _SEP_SECTION)  # WHY: Preserve legacy section separator.
        print(" SCAN RADIO CAPTURE CONFIGURATION (All APs)")  # WHY: Preserve legacy configuration header.
        print(_SEP_SECTION)  # WHY: Preserve legacy section separator.

    def _confirm_and_launch(  # WHY: Prompt for final confirmation and dispatch capture launch.
        self, site_id: str, ap_macs: list[str], config: CaptureConfig
    ) -> None:
        """Pause for operator confirmation then launch capture."""
        logging.info("Requesting final operator confirmation before starting capture")  # WHY: Trace confirm entry.
        self.input_utils.safe_input(  # WHY: Pause for explicit operator confirmation with EOF-safe helper.
            f"\nPress Enter to start capture for {len(ap_macs)} APs (Ctrl+C to cancel): ",
            context="confirmation",
            allow_empty=True,
        )
        logging.debug("Operator confirmation received; proceeding with launch")  # WHY: Log confirmation completion.
        self._launch_capture(site_id, ap_macs, config)  # WHY: Launch capture and dispatch response.

    def run(self, site_id: str) -> None:  # WHY: Entry point orchestrating the extracted multi-AP scan workflow.
        """Execute the extracted multi-AP scan capture workflow."""
        logging.info("Starting multi-AP scan capture for site: %s", site_id)  # WHY: Log workflow start.
        ap_macs = self.device_utils.get_all_ap_macs_from_site(site_id)  # WHY: Retrieve AP MAC inventory.
        logging.debug("Retrieved %d AP MAC addresses for site %s", len(ap_macs), site_id)  # WHY: Log inventory.
        if not ap_macs:  # WHY: Short-circuit when no APs are available for capture.
            print("\n! No APs found at site")  # WHY: Preserve legacy no-AP message.
            logging.warning("No AP MACs found for site %s; aborting workflow", site_id)  # WHY: Log early exit.
            return  # WHY: Exit early because no APs means no valid targets.
        self._print_prep_header(len(ap_macs))  # WHY: Emit legacy pre-config header to operator.
        self._check_existing_captures(site_id)  # WHY: Run non-blocking courtesy check for existing captures.
        self._print_config_header(len(ap_macs))  # WHY: Emit legacy configuration banner to operator.
        config = self._gather_capture_config()  # WHY: Prompt for full capture configuration.
        if config is None:  # WHY: Abort when any operator prompt fails validation.
            return  # WHY: Exit silently on invalid operator input per legacy behavior.
        self._display_summary(len(ap_macs), config)  # WHY: Display configuration summary before confirmation.
        self._confirm_and_launch(site_id, ap_macs, config)  # WHY: Prompt confirmation and launch capture.
        logging.info("Multi-AP scan capture function completed")  # WHY: Log workflow completion boundary.


__all__ = [
    "BoundedIntSpec",
    "CaptureConfig",
    "MultiApScanCaptureWorkflow",
]  # WHY: Explicit public surface for the workflow module.

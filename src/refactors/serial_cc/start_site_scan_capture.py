"""Scan capture orchestration extracted from MistHelper high-CC offender."""

from __future__ import annotations  # WHY: PEP 563 postponed annotations for forward Any typing

import importlib  # WHY: Late-bound MistHelper import avoids circular src->MistHelper
import logging  # WHY: Structured trace for workflow start/site abort events
from dataclasses import dataclass  # WHY: Frozen slotted state bundles keep execute() CC low
from types import SimpleNamespace  # WHY: SimpleNamespace preserves bounded-int spec shape used in tests
from typing import Any, cast  # WHY: Manager/prompt helpers are dynamic MistHelper attrs; cast narrows AP MAC

# Module-level constants - dividers, banner text, prompts, and event log strings extracted so
# every method has fixed CC and no repeated string literals appear inline.
_MIST_MODULE = "MistHelper"  # WHY: Single source for the late-import target
logger = logging.getLogger(__name__)  # WHY: module-scoped logger for #886 print-to-logger migration.
_LOG_START = "Starting site scan capture"  # WHY: Event log message (single-source)
_LOG_SITE_ABORT = "No site_id returned from selection - aborting capture"  # WHY: Abort trace on missing site
_LOG_PROGRESS = "Proceeding with scan capture configuration for site: %s"  # WHY: Progress trace template
_LOG_CONFIRM_WAIT = "Waiting for user confirmation"  # WHY: Trace before final Enter prompt
_LOG_EXECUTING = "User confirmed - executing site capture"  # WHY: Trace once payload dispatch begins
_DIVIDER_DASH = "-" * 80  # WHY: Banner top/bottom rule
_DIVIDER_EQUAL = "=" * 80  # WHY: Summary top/bottom rule
_INTRO_TITLE = " SCAN RADIO CAPTURE CONFIGURATION"  # WHY: Banner section title
_SUMMARY_TITLE = " CAPTURE CONFIGURATION SUMMARY"  # WHY: Summary section title
_BAND_HEADER = "\nSelect band:"  # WHY: Band prompt header
_BAND_OPT_24 = "  1. 2.4 GHz"  # WHY: Band option 1 (2.4 GHz)
_BAND_OPT_5 = "  2. 5 GHz (default)"  # WHY: Band option 2 (5 GHz default)
_BAND_OPT_6 = "  3. 6 GHz"  # WHY: Band option 3 (6 GHz)
_PROMPT_BAND = "Enter choice [1-3] (default 2): "  # WHY: Band-choice prompt text
_BW_HEADER = "\nSelect bandwidth:"  # WHY: Bandwidth prompt header
_BW_OPT_20 = "  1. 20 MHz"  # WHY: Bandwidth option 1 (20 MHz)
_BW_OPT_40 = "  2. 40 MHz"  # WHY: Bandwidth option 2 (40 MHz)
_BW_OPT_80 = "  3. 80 MHz"  # WHY: Bandwidth option 3 (80 MHz - 5/6 GHz only)
_BW_OPT_160 = "  4. 160 MHz"  # WHY: Bandwidth option 4 (160 MHz - 6 GHz only)
_PROMPT_BW = "Enter choice (default 1): "  # WHY: Bandwidth-choice prompt text
_LOOP_HEADER = "\nLoop Mode:"  # WHY: Loop-mode prompt header
_LOOP_LINE1 = "  Automatically start a new capture when the current one completes"  # WHY: Loop explanation line 1
_LOOP_LINE2 = "  Downloads happen in background while next capture runs"  # WHY: Loop explanation line 2
_PROMPT_LOOP = "Enable continuous loop mode? (y/n, default n): "  # WHY: Loop-mode prompt text
_PROMPT_CONFIRM = "\nPress Enter to start capture (Ctrl+C to cancel): "  # WHY: Final confirmation prompt text
_PROMPT_OVERRIDE = "\nContinue anyway? (y/n, default n): "  # WHY: Existing-capture override prompt text
_YES = "y"  # WHY: Canonical yes literal
_ALL_APS_SENTINEL = "ALL_APS"  # WHY: Picker sentinel signalling capture across every AP
_MODE_ABORT = "abort"  # WHY: AP-selection mode signalling workflow abort
_MODE_ALL = "all"  # WHY: AP-selection mode signalling all-AP capture path
_MODE_SINGLE = "single"  # WHY: AP-selection mode signalling single-AP capture path
_MAX_PKT_LEN = 1300  # WHY: Scan capture max packet length (bytes, API-fixed)
_INVALID_BW_24_MSG = "\n! Invalid bandwidth {value} for 2.4 GHz band"  # WHY: 2.4 GHz bandwidth failure template
_LOG_INVALID_BW_24 = "Invalid bandwidth %s for 2.4 GHz band"  # WHY: 2.4 GHz bandwidth failure log template
_PRE_CHECK_MSG = "\n> Checking for existing captures on AP {ap_mac}..."  # WHY: User-facing pre-check message
_WARN_LINES = (  # WHY: Existing-capture warning lines (tuple keeps _print_conflict_warning CC low)
    "\n! WARNING: This AP already has a capture in progress or recently completed",
    "  Mist only allows one capture per AP at a time",
    "  The new capture may fail with 'Recording already in progress'",
)
_CANCEL_MSG = "\n* Capture cancelled by user"  # WHY: User cancellation confirmation message
_LOG_USER_CANCEL = "User cancelled capture due to existing capture on AP"  # WHY: User-cancel trace
_LOG_PRECHECK_FAIL = "Failed to check for existing captures: %s"  # WHY: API pre-check failure trace template
# Band-choice to band-code map (accepts menu indices and direct band codes).
_BAND_MAP = {"1": "24", "2": "5", "3": "6", "24": "24", "5": "5", "6": "6"}  # WHY: Choice/code -> band-code
# Bandwidth-choice to MHz value map.
_BANDWIDTH_MAP = {"1": "20", "2": "40", "3": "80", "4": "160"}  # WHY: Choice -> MHz string
# Display map replaces inline ternary so _print_summary stays under CC threshold.
_LOOP_LABEL_MAP = {  # WHY: Loop-mode rendering (extracted from inline ternary)
    True: "ENABLED (continuous until Ctrl+C)",
    False: "Disabled (single capture)",
}
# Channel-prompt specs per band: prompt text + default value. Table-driven so _prompt_channel
# has fixed CC and no per-band branch cascade.
_CHANNEL_PROMPTS: dict[str, tuple[str, str]] = {
    "24": ("Enter channel (1-11, default 1): ", "1"),
    "5": (
        "Enter channel (36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 144, default 36): ",  # noqa: E501
        "36",
    ),
    "6": ("Enter channel (1-233, default 1): ", "1"),
}
# Extra bandwidth menu rows shown per band (5 GHz adds 80 MHz; 6 GHz adds 80 and 160 MHz).
_BANDWIDTH_EXTRA_ROWS: dict[str, tuple[str, ...]] = {
    "5": (_BW_OPT_80,),
    "6": (_BW_OPT_80, _BW_OPT_160),
}
# 2.4 GHz only permits 20 and 40 MHz - any other resolved value must abort.
_BW_ALLOWED_24 = frozenset({"20", "40"})  # WHY: Allowed bandwidth set for the 2.4 GHz band


# Bounded-integer prompt specifications: each carries prompt text, default, input context,
# the noun used in the invalid message, the inclusive low/high bounds, and the range-error lines.
_DURATION_SPEC = SimpleNamespace(
    prompt="Enter capture duration in seconds (default 60, min 60, max 86400): ",
    default="60",
    context="duration",
    invalid_label="duration",
    low=60,
    high=86400,
    range_lines=["\n! Duration must be between 60 and 86400 seconds (API requirement)"],
)
_PACKETS_SPEC = SimpleNamespace(
    prompt="Enter number of packets (default 1024, max 10000): ",
    default="1024",
    context="num_packets",
    invalid_label="number of packets",
    low=0,
    high=10000,
    range_lines=["\n! Number of packets must be between 0 and 10000"],
)
# Ordered tuple drives sequential bounded-int prompts inside _gather_settings (table-driven).
_BOUNDED_INT_SPECS = (_DURATION_SPEC, _PACKETS_SPEC)  # WHY: Table-drives prompt sequence


def _resolve_prompt_helpers() -> tuple[Any, Any, Any, Any, Any]:
    """Resolve helper classes from MistHelper at runtime to avoid circular imports."""
    misthelper_module = importlib.import_module(_MIST_MODULE)  # WHY: Late import avoids circular src->MistHelper
    return (
        misthelper_module.InputUtils,
        misthelper_module.PromptUtils,
        misthelper_module.PromptNetworkDeviceUtils,
        misthelper_module.DeviceUtils,
        misthelper_module.mistapi,
    )


@dataclass(frozen=True, slots=True)
class _Helpers:
    """Frozen bundle of resolved MistHelper helpers so execute() carries one arg, not five."""

    input_utils: Any  # WHY: safe_input entry point
    prompt_utils: Any  # WHY: select_site_with_logging entry point
    prompt_network_device_utils: Any  # WHY: interactive AP MAC picker factory
    device_utils: Any  # WHY: expand_port_range_string for the picker helper
    mistapi: Any  # WHY: mistapi module for the pre-check listSitePacketCaptures call


@dataclass(frozen=True, slots=True)
class _Settings:
    """Frozen bundle of all user-gathered scan capture settings; hands off to payload/summary/dispatch."""

    ap_mac: str  # WHY: Target AP MAC (normalized) for single-AP path
    band: str  # WHY: Radio band code ("24", "5", "6")
    channel: int  # WHY: Radio channel (band-appropriate)
    bandwidth: str  # WHY: Channel bandwidth in MHz (string form for API)
    duration: int  # WHY: Capture duration in seconds
    num_packets: int  # WHY: Packet cap (0-10000)
    capture_format: str  # WHY: Capture output format (pcap/pcapng/...)
    enable_loop: bool  # WHY: Continuous loop-mode flag


class SiteScanCaptureService:
    """Owns scan radio capture flow formerly embedded in MistHelper method."""

    @staticmethod
    def _print_intro() -> None:
        """Print the scan radio capture configuration banner."""
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("\n%s", _DIVIDER_DASH)  # WHY: Top divider
        logger.info("%s", _INTRO_TITLE)  # WHY: Section title
        logger.info("%s", _DIVIDER_DASH)  # WHY: Bottom divider

    @staticmethod
    def _select_ap(manager: Any, helpers: _Helpers, site_id: str) -> tuple[str | None, str]:
        """Select the target AP; return (ap_mac, mode) where mode is 'single', 'all', or 'abort'."""
        logger.debug("Prompting for AP selection from site inventory")  # WHY: Trace the AP prompt
        prompt_utils = helpers.prompt_network_device_utils(
            manager.mist_session, helpers.input_utils.safe_input, helpers.device_utils.expand_port_range_string
        )  # WHY: Build the device prompt helper
        ap_mac = prompt_utils.select_ap_mac(site_id)  # WHY: Interactive AP picker (may return the ALL_APS sentinel)
        if not ap_mac:  # WHY: Nothing selected or selection failed
            logger.warning("No AP selected or AP selection failed - aborting capture")  # WHY: Trace the abort
            return None, _MODE_ABORT  # WHY: Signal abort
        if ap_mac == _ALL_APS_SENTINEL:  # WHY: User chose to capture from every AP
            logger.info("User selected all APs - launching multi-AP captures")  # WHY: Trace the all-AP path
            return None, _MODE_ALL  # WHY: Signal the all-AP path (launched by caller)
        normalized_ap_mac = manager.normalize_mac_address(ap_mac)  # WHY: Normalize the single AP MAC
        logger.debug("Selected and normalized AP MAC: %s", normalized_ap_mac)  # WHY: Trace the normalized MAC
        return normalized_ap_mac, _MODE_SINGLE  # WHY: Single-AP capture path

    @staticmethod
    def _select_band(input_utils: Any) -> str:
        """Prompt for the radio band; return the resolved band code (defaults to 5 GHz)."""
        logger.debug("Prompting for band selection")  # WHY: Trace the band prompt
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("%s", _BAND_HEADER)  # WHY: Prompt header
        logger.info("%s", _BAND_OPT_24)  # WHY: 2.4 GHz option
        logger.info("%s", _BAND_OPT_5)  # WHY: 5 GHz option (default)
        logger.info("%s", _BAND_OPT_6)  # WHY: 6 GHz option
        band_choice = input_utils.safe_input(
            _PROMPT_BAND, default_value="2", context="band"
        )  # WHY: Read the band choice
        band = _BAND_MAP.get(band_choice, "5")  # WHY: Map to a band code, defaulting to 5 GHz
        logger.debug("Band selected: %s (choice: %s)", band, band_choice)  # WHY: Trace the resolved band
        return band  # WHY: Resolved band code

    @staticmethod
    def _prompt_channel(input_utils: Any, band: str) -> int | None:
        """Prompt for a band-appropriate channel; return None to abort (message printed)."""
        logger.debug("Prompting for channel")  # WHY: Trace the channel prompt
        prompt_text, default_value = _CHANNEL_PROMPTS[band]  # WHY: Table-driven per-band prompt
        channel_str = input_utils.safe_input(
            prompt_text, default_value=default_value, context="channel"
        )  # WHY: Read the raw channel input
        try:  # WHY: Validate the channel parses as an integer
            channel = int(channel_str)  # WHY: Parse the channel
        except ValueError:  # WHY: Non-numeric channel
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("\n! Invalid channel: %s", channel_str)  # WHY: Inform the user
            logger.error("Invalid channel value: %s", channel_str)  # WHY: Trace the failure
            return None  # WHY: Abort
        logger.debug("Channel selected: %s", channel)  # WHY: Trace the channel
        return channel  # WHY: Validated channel

    @staticmethod
    def _print_bandwidth_menu(band: str) -> None:
        """Emit the bandwidth menu rows (base + per-band extras) with fixed CC."""
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("%s", _BW_HEADER)  # WHY: Prompt header
        logger.info("%s", _BW_OPT_20)  # WHY: 20 MHz option
        logger.info("%s", _BW_OPT_40)  # WHY: 40 MHz option
        for row in _BANDWIDTH_EXTRA_ROWS.get(band, ()):  # WHY: Table-driven extra rows per band
            logger.info("%s", row)  # WHY: 80 MHz for 5/6 GHz, 160 MHz for 6 GHz

    @classmethod
    def _select_bandwidth(cls, input_utils: Any, band: str) -> str | None:
        """Prompt for a band-appropriate bandwidth; return None to abort (message printed)."""
        logger.debug("Prompting for bandwidth")  # WHY: Trace the bandwidth prompt
        cls._print_bandwidth_menu(band)  # WHY: Emit the menu rows via a helper (keeps CC low)
        bw_choice = input_utils.safe_input(
            _PROMPT_BW, default_value="1", context="bandwidth"
        )  # WHY: Read the bandwidth choice
        bandwidth = _BANDWIDTH_MAP.get(bw_choice, "20")  # WHY: Map to MHz, defaulting to 20 MHz
        logger.debug("Bandwidth selected: %s MHz (choice: %s)", bandwidth, bw_choice)  # WHY: Trace the value
        if band == "24" and bandwidth not in _BW_ALLOWED_24:  # WHY: 2.4 GHz only supports 20/40 MHz
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("%s", _INVALID_BW_24_MSG.format(value=bandwidth))  # WHY: Inform the user
            logger.error(_LOG_INVALID_BW_24, bandwidth)  # WHY: Trace the failure
            return None  # WHY: Abort
        return bandwidth  # WHY: Validated bandwidth

    @staticmethod
    def _prompt_bounded_int(input_utils: Any, spec: SimpleNamespace) -> int | None:
        """Prompt for an integer within spec bounds; return None to abort (message printed)."""
        raw = input_utils.safe_input(spec.prompt, default_value=spec.default, context=spec.context)  # WHY: Read raw
        try:  # WHY: Validate that the input parses as an integer
            value = int(raw)  # WHY: Parse the integer
        except ValueError:  # WHY: Non-numeric input
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("\n! Invalid %s: %s", spec.invalid_label, raw)  # WHY: Inform the user
            logger.error("Invalid %s value: %s", spec.invalid_label, raw)  # WHY: Trace the failure
            return None  # WHY: Abort
        if value < spec.low or value > spec.high:  # WHY: Enforce the inclusive bounds
            for line in spec.range_lines:  # WHY: Print each range-error line
                # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
                logger.warning("%s", line)  # WHY: Inform the user
            logger.error("%s out of range: %s", spec.invalid_label, value)  # WHY: Trace the range failure
            return None  # WHY: Abort
        logger.debug("%s set: %s", spec.invalid_label, value)  # WHY: Trace the accepted value
        return value  # WHY: Validated integer

    @classmethod
    def _collect_bounded_ints(cls, input_utils: Any) -> tuple[int, ...] | None:
        """Run the bounded-int prompts (duration, packets); None aborts."""
        values: list[int] = []  # WHY: Accumulator for validated integers
        for spec in _BOUNDED_INT_SPECS:  # WHY: Table-driven sequential prompting
            value = cls._prompt_bounded_int(input_utils, spec)  # WHY: Prompt one bounded int
            if value is None:  # WHY: Invalid input (message already printed)
                return None  # WHY: Abort the sequence
            values.append(value)  # WHY: Accept the validated integer
        return tuple(values)  # WHY: Immutable ordered pair

    @staticmethod
    def _prompt_loop_mode(input_utils: Any) -> bool:
        """Prompt whether to enable continuous loop mode."""
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("%s", _LOOP_HEADER)  # WHY: Section header
        logger.info("%s", _LOOP_LINE1)  # WHY: Explanation line 1
        logger.info("%s", _LOOP_LINE2)  # WHY: Explanation line 2
        loop_mode = input_utils.safe_input(
            _PROMPT_LOOP, default_value="n", context="loop_mode"
        )  # WHY: Read the loop choice
        return bool(loop_mode.lower() == _YES)  # WHY: Enabled only on explicit yes

    @staticmethod
    def _build_payload(settings: _Settings) -> dict[str, Any]:
        """Build the scan capture payload from gathered settings."""
        payload: dict[str, Any] = {
            "type": "scan",
            "ap_mac": settings.ap_mac,
            "band": settings.band,
            "channel": settings.channel,
            "bandwidth": settings.bandwidth,
            "duration": settings.duration,
            "num_packets": settings.num_packets,
            "format": settings.capture_format,
            "max_pkt_len": _MAX_PKT_LEN,
        }  # WHY: Scan-capture payload (max packet length fixed at 1300 bytes)
        logger.debug("Payload constructed: %s", payload)  # WHY: Trace the constructed payload
        return payload  # WHY: Completed payload

    @staticmethod
    def _summary_rows(settings: _Settings) -> list[tuple[str, str]]:
        """Return ordered (label, value) rows for the summary table; keeps _print_summary CC low."""
        return [
            ("Capture Type", "Scan Radio"),
            ("AP MAC", settings.ap_mac),
            ("Band", f"{settings.band} GHz"),
            ("Channel", str(settings.channel)),
            ("Bandwidth", f"{settings.bandwidth} MHz"),
            ("Duration", f"{settings.duration} seconds"),
            ("Packets", str(settings.num_packets)),
            ("Loop Mode", _LOOP_LABEL_MAP[settings.enable_loop]),
        ]  # WHY: Table-driven rows replace inline branches in the printer

    @classmethod
    def _print_summary(cls, settings: _Settings) -> None:
        """Print the scan capture configuration summary using table-driven rendering."""
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("\n%s", _DIVIDER_EQUAL)  # WHY: Top divider
        logger.info("%s", _SUMMARY_TITLE)  # WHY: Section title
        logger.info("%s", _DIVIDER_EQUAL)  # WHY: Divider
        for label, value in cls._summary_rows(settings):  # WHY: Uniform label-value rendering
            logger.info("  %s: %s", label, value)  # WHY: One row per iteration (no branching)
        logger.info("%s", _DIVIDER_EQUAL)  # WHY: Bottom divider

    @staticmethod
    def _canonical_mac(value: str) -> str:
        """Normalize a MAC by stripping separators and lower-casing (for comparison only)."""
        return value.replace(":", "").replace("-", "").lower()  # WHY: MAC comparison ignores separators/case

    @classmethod
    def _list_existing_captures(cls, helpers: _Helpers, manager: Any, site_id: str) -> list[dict[str, Any]] | None:
        """Fetch the site's existing captures; None means the pre-check failed (warn and proceed)."""
        try:  # WHY: Pre-check API failures are non-fatal - warn and proceed
            response = helpers.mistapi.api.v1.sites.pcaps.listSitePacketCaptures(
                manager.mist_session, site_id
            )  # WHY: List pcaps at the target site
        except Exception as error:  # WHY: Pre-check API failure - warn and proceed
            logger.warning(_LOG_PRECHECK_FAIL, error)  # WHY: Trace the failure
            return None  # WHY: Signal proceed-without-check
        if response.status_code != 200:  # WHY: Only inspect successful responses
            return []  # WHY: Non-200 -> treat as no known captures
        return response.data or []  # WHY: Existing captures (or empty on 200 with no data)

    @classmethod
    def _has_conflict(cls, existing_captures: list[dict[str, Any]], ap_mac: str) -> bool:
        """Return True when the AP already has an existing capture (MAC-normalized comparison)."""
        ap_canonical = cls._canonical_mac(ap_mac)  # WHY: Normalize target MAC once
        return any(
            cls._canonical_mac(cap.get("ap_mac", "")) == ap_canonical for cap in existing_captures
        )  # WHY: True when any existing capture matches this AP after normalization

    @staticmethod
    def _print_conflict_warning() -> None:
        """Emit the multi-line existing-capture warning banner."""
        for line in _WARN_LINES:  # WHY: Table-driven emission keeps CC fixed
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("%s", line)  # WHY: One warning line per iteration

    @classmethod
    def _confirm_conflict_override(cls, input_utils: Any) -> bool:
        """Prompt whether to continue past an existing capture; False cancels."""
        cls._print_conflict_warning()  # WHY: Show the warning banner
        proceed = input_utils.safe_input(
            _PROMPT_OVERRIDE, default_value="n", context="capture_conflict_confirmation"
        ).lower()  # WHY: Read the override choice
        if proceed != _YES:  # WHY: User declined to proceed
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("%s", _CANCEL_MSG)  # WHY: Inform the user
            logger.info(_LOG_USER_CANCEL)  # WHY: Trace the cancel
            return False  # WHY: Signal cancel
        return True  # WHY: User confirmed override

    @classmethod
    def _check_existing_captures(cls, manager: Any, helpers: _Helpers, site_id: str, ap_mac: str) -> bool:
        """Warn on an existing capture for the AP; return False if the user cancels."""
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("%s", _PRE_CHECK_MSG.format(ap_mac=ap_mac))  # WHY: Inform the user of the pre-check
        existing_captures = cls._list_existing_captures(helpers, manager, site_id)  # WHY: Fetch existing captures
        if existing_captures is None:  # WHY: Pre-check API failure (already logged) - proceed
            return True  # WHY: Non-fatal, continue with capture
        if not cls._has_conflict(existing_captures, ap_mac):  # WHY: No conflict detected
            return True  # WHY: Nothing to warn about, continue
        return cls._confirm_conflict_override(helpers.input_utils)  # WHY: Warn and read override

    @classmethod
    def _gather_prompted_values(cls, manager: Any, helpers: _Helpers, ap_mac: str) -> _Settings | None:
        """Run band/channel/bandwidth/bounded-ints/format/loop prompts; None aborts."""
        band = cls._select_band(helpers.input_utils)  # WHY: Resolve the radio band
        channel = cls._prompt_channel(helpers.input_utils, band)  # WHY: Resolve a band-appropriate channel
        if channel is None:  # WHY: Invalid channel (message already printed)
            return None  # WHY: Abort
        bandwidth = cls._select_bandwidth(helpers.input_utils, band)  # WHY: Resolve a band-appropriate bandwidth
        if bandwidth is None:  # WHY: Invalid bandwidth (message already printed)
            return None  # WHY: Abort
        ints = cls._collect_bounded_ints(helpers.input_utils)  # WHY: Duration + packet count
        if ints is None:  # WHY: One of the bounded-int prompts failed
            return None  # WHY: Abort
        return _Settings(
            ap_mac=ap_mac,
            band=band,
            channel=channel,
            bandwidth=bandwidth,
            duration=ints[0],
            num_packets=ints[1],
            capture_format=manager._get_capture_format_selection(),  # WHY: Capture output format
            enable_loop=cls._prompt_loop_mode(helpers.input_utils),  # WHY: Continuous loop mode
        )

    @classmethod
    def _select_ap_or_dispatch(cls, manager: Any, helpers: _Helpers, site_id: str) -> str | None:
        """Select the AP and handle abort/all-APs modes; return normalized MAC or None to stop."""
        ap_mac, mode = cls._select_ap(manager, helpers, site_id)  # WHY: Interactive AP selection
        if mode == _MODE_ABORT:  # WHY: AP selection failed (message already traced)
            return None  # WHY: Abort the workflow
        if mode == _MODE_ALL:  # WHY: User chose all APs - launch multi-AP captures
            manager._start_site_scan_capture_all_aps(site_id)  # WHY: Run captures across every AP
            return None  # WHY: All-AP path handled by manager - stop here
        return cast(str, ap_mac)  # WHY: Single-AP path always yields a normalized MAC (narrows type for mypy)

    @staticmethod
    def _dispatch(manager: Any, site_id: str, payload: dict[str, Any], enable_loop: bool) -> None:
        """Dispatch to loop or single capture based on the resolved loop-mode flag."""
        if enable_loop:  # WHY: Continuous loop mode
            manager._execute_site_capture_loop(site_id, payload)  # WHY: Run captures in a loop
            return  # WHY: Loop path complete
        manager._execute_site_capture(site_id, payload)  # WHY: Run a single capture

    @classmethod
    def _finalize_and_run(cls, manager: Any, helpers: _Helpers, site_id: str, settings: _Settings) -> None:
        """Build payload, show summary, wait for confirmation, pre-check conflict, then dispatch."""
        payload = cls._build_payload(settings)  # WHY: Construct the API payload
        cls._print_summary(settings)  # WHY: Show the configuration summary
        logger.debug(_LOG_CONFIRM_WAIT)  # WHY: Trace the confirmation wait
        helpers.input_utils.safe_input(
            _PROMPT_CONFIRM, context="confirmation", allow_empty=True
        )  # WHY: Final confirmation before starting
        if not cls._check_existing_captures(manager, helpers, site_id, settings.ap_mac):  # WHY: Conflict pre-check
            return  # WHY: User cancelled due to an existing capture
        logger.info(_LOG_EXECUTING)  # WHY: Trace the execution
        cls._dispatch(manager, site_id, payload, settings.enable_loop)  # WHY: Loop vs single capture dispatch

    @classmethod
    def execute(cls, manager: Any) -> None:
        """Run scan radio packet capture workflow using manager dependencies."""
        helpers = _Helpers(*_resolve_prompt_helpers())  # WHY: Frozen helper bundle (one arg instead of five)
        logger.info(_LOG_START)  # WHY: Trace workflow start
        site_id = helpers.prompt_utils.select_site_with_logging()  # WHY: Prompt for the target site
        logger.debug("Site selection returned: %s", site_id)  # WHY: Trace the selection
        if not site_id:  # WHY: No site chosen
            logger.warning(_LOG_SITE_ABORT)  # WHY: Trace the abort
            return  # WHY: Abort the workflow
        logger.debug(_LOG_PROGRESS, site_id)  # WHY: Trace progress
        cls._print_intro()  # WHY: Show the configuration banner
        ap_mac = cls._select_ap_or_dispatch(manager, helpers, site_id)  # WHY: Select AP or dispatch all-AP path
        if ap_mac is None:  # WHY: Abort mode or all-APs path already handled
            return  # WHY: Nothing more for single-AP execute to do
        settings = cls._gather_prompted_values(manager, helpers, ap_mac)  # WHY: Collect remaining inputs
        if settings is None:  # WHY: Any prompt aborted (message already printed)
            return  # WHY: Abort the workflow
        cls._finalize_and_run(manager, helpers, site_id, settings)  # WHY: Payload -> summary -> confirm -> dispatch

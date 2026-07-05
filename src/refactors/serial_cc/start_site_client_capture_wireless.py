"""Wireless client capture orchestration extracted from MistHelper offender #6."""

from __future__ import annotations  # WHY: PEP 563 postponed annotations for forward Any typing

import importlib  # WHY: Late-bound MistHelper import avoids circular src->MistHelper
import logging  # WHY: Structured trace for workflow start/site abort events
from dataclasses import dataclass  # WHY: Frozen slotted state bundles keep execute() CC low
from types import SimpleNamespace  # WHY: SimpleNamespace preserves bounded-int spec shape used in tests
from typing import Any  # WHY: Manager/prompt helpers are dynamic MistHelper attrs

# Module-level constants - dividers, banner text, prompts, and event log strings extracted so
# every method has fixed CC and no repeated string literals appear inline.
_MIST_MODULE = "MistHelper"  # WHY: Single source for the late-import target
_LOG_START = "Starting site wireless client capture"  # WHY: Event log message (single-source)
_DIVIDER_DASH = "-" * 80  # WHY: Banner top/bottom rule
_DIVIDER_EQUAL = "=" * 80  # WHY: Summary top/bottom rule
_INTRO_TITLE = " WIRELESS CLIENT CAPTURE CONFIGURATION"  # WHY: Banner section title
_INTRO_PURPOSE = "\nThis capture type monitors ongoing traffic from ALREADY CONNECTED wireless clients."
_INTRO_GUIDANCE = "Note: To capture new connection attempts (auth/assoc handshakes), use New Association Capture instead."  # noqa: E501
_SUMMARY_TITLE = " CAPTURE CONFIGURATION SUMMARY"  # WHY: Summary section title
_CLIENT_HEADER = "\nClient selection:"  # WHY: Client-selection prompt header
_CLIENT_OPT_LIST = "  1. Select from connected clients"  # WHY: Client-selection option 1
_CLIENT_OPT_MANUAL = "  2. Manually enter MAC address"  # WHY: Client-selection option 2
_AP_HEADER = "\nOptional: Filter by specific AP"  # WHY: AP-filter prompt header
_AP_OPT_LIST = "  1. Select AP from list"  # WHY: AP-filter option 1
_AP_OPT_MANUAL = "  2. Enter MAC manually"  # WHY: AP-filter option 2
_AP_OPT_SKIP = "  3. Skip (capture from any AP)"  # WHY: AP-filter option 3
_LOOP_HEADER = "\nLoop Mode:"  # WHY: Loop-mode prompt header
_LOOP_LINE1 = "  Automatically start a new capture when the current one completes"  # WHY: Loop explanation line 1
_LOOP_LINE2 = "  Downloads happen in background while next capture runs"  # WHY: Loop explanation line 2
_PROMPT_CLIENT_CHOICE = "Enter choice (default 1): "  # WHY: Client-mode prompt text
_PROMPT_AP_CHOICE = "Enter choice (default 3): "  # WHY: AP-filter prompt text
_PROMPT_LOOP = "Enable continuous loop mode? (y/n, default n): "  # WHY: Loop-mode prompt text
_PROMPT_MCAST = "Include multicast traffic? (y/n, default n): "  # WHY: Multicast prompt text
_PROMPT_CONFIRM = "\nPress Enter to start capture (Ctrl+C to cancel): "  # WHY: Final confirmation prompt text
_PROMPT_CLIENT_MAC = "\nEnter client MAC address: "  # WHY: Manual client MAC prompt text
_PROMPT_AP_MAC = "Enter AP MAC address: "  # WHY: Manual AP MAC prompt text
_YES = "y"  # WHY: Canonical yes literal
_NO_CLIENT_MSG = "\n! No client selected"  # WHY: Client-selection abort message
_INVALID_CLIENT_MAC_MSG = "\n! Invalid MAC address format: {value}"  # WHY: Client-MAC failure template
_INVALID_AP_MAC_MSG = "\n! Invalid AP MAC address format: {value}"  # WHY: AP-MAC failure template
_CLIENT_MODE_LIST = "1"  # WHY: Menu choice mapping to list-based client selection
_AP_MODE_LIST = "1"  # WHY: Menu choice mapping to list-based AP selection
_AP_MODE_MANUAL = "2"  # WHY: Menu choice mapping to manual AP MAC entry
# Display maps replace inline ternaries so _print_summary stays under CC threshold.
_YES_NO_MAP = {True: "Yes", False: "No"}  # WHY: Multicast flag rendering
_LOOP_LABEL_MAP = {  # WHY: Loop-mode rendering (extracted from inline ternary)
    True: "ENABLED (continuous until Ctrl+C)",
    False: "Disabled (single capture)",
}
_PACKETS_HINT_MAP = {True: "unlimited", False: "max"}  # WHY: Packet-count hint rendering
_FILTER_NONE_LABEL = "None (all traffic)"  # WHY: Displayed when no tcpdump expression given

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
# Ordered tuple drives sequential bounded-int prompts inside _gather_settings (table-driven).
_BOUNDED_INT_SPECS = (_DURATION_SPEC, _PACKETS_SPEC, _MAX_PKT_LEN_SPEC)  # WHY: Table-drives prompt sequence


def _resolve_prompt_helpers() -> tuple[Any, Any, Any, Any]:
    """Resolve helper classes from MistHelper module to preserve runtime compatibility."""
    misthelper_module = importlib.import_module(_MIST_MODULE)  # WHY: Late import avoids circular src->MistHelper
    return (
        misthelper_module.InputUtils,
        misthelper_module.PromptUtils,
        misthelper_module.PromptClientUtils,
        misthelper_module.PromptNetworkDeviceUtils,
    )


@dataclass(frozen=True, slots=True)
class _Helpers:
    """Frozen bundle of resolved MistHelper helpers so execute() carries one arg, not four."""

    input_utils: Any  # WHY: safe_input entry point
    prompt_utils: Any  # WHY: select_site_with_logging entry point
    prompt_client_utils: Any  # WHY: interactive client MAC picker factory
    prompt_network_device_utils: Any  # WHY: interactive AP MAC picker factory


@dataclass(frozen=True, slots=True)
class _Settings:
    """Frozen bundle of all user-gathered capture settings; hands off to payload/summary/dispatch."""

    client_mac: str  # WHY: Target wireless client MAC (normalized)
    ap_mac: str | None  # WHY: Optional AP MAC filter (None disables filter)
    duration: int  # WHY: Capture duration in seconds
    num_packets: int  # WHY: Packet cap (0 for unlimited)
    max_pkt_len: int  # WHY: Max packet length in bytes
    includes_mcast: bool  # WHY: Include multicast traffic flag
    tcpdump_expr: str  # WHY: Optional tcpdump expression (empty means unset)
    capture_format: str  # WHY: Capture output format (pcap/pcapng/...)
    enable_loop: bool  # WHY: Continuous loop-mode flag


class SiteWirelessClientCaptureService:
    """Owns wireless client capture flow formerly embedded in MistHelper method."""

    @staticmethod
    def _print_intro() -> None:
        """Print the wireless client capture configuration banner."""
        print("\n" + _DIVIDER_DASH)  # WHY: Top divider
        print(_INTRO_TITLE)  # WHY: Section title
        print(_DIVIDER_DASH)  # WHY: Bottom divider
        print(_INTRO_PURPOSE)  # WHY: Purpose line
        print(_INTRO_GUIDANCE)  # WHY: Guidance toward the alternate capture type

    @staticmethod
    def _read_client_mac(helpers: _Helpers, site_id: str, choice: str) -> str | None:
        """Read a raw (pre-validation) client MAC via list picker or manual entry."""
        if choice == _CLIENT_MODE_LIST:  # WHY: Pick from the connected-clients list
            client_mac = helpers.prompt_client_utils.select_client_mac(site_id)  # WHY: Interactive picker
            if not client_mac:  # WHY: Nothing selected
                print(_NO_CLIENT_MSG)  # WHY: Inform the user
                return None  # WHY: Abort
            return str(client_mac)  # WHY: Return picker result
        return str(helpers.input_utils.safe_input(_PROMPT_CLIENT_MAC, context="client_mac"))  # WHY: Manual entry

    @classmethod
    def _select_client_mac(cls, manager: Any, helpers: _Helpers, site_id: str) -> str | None:
        """Select and validate the target client MAC; return None to abort (message printed)."""
        print(_CLIENT_HEADER)  # WHY: Prompt header
        print(_CLIENT_OPT_LIST)  # WHY: Option 1 (list picker)
        print(_CLIENT_OPT_MANUAL)  # WHY: Option 2 (manual entry)
        choice = helpers.input_utils.safe_input(
            _PROMPT_CLIENT_CHOICE, default_value=_CLIENT_MODE_LIST, context="client_select"
        )  # WHY: Read the selection mode
        client_mac = cls._read_client_mac(helpers, site_id, choice)  # WHY: Resolve mac via chosen mode
        if client_mac is None:  # WHY: Selection aborted (message printed)
            return None  # WHY: Propagate abort
        if not manager.validate_mac_address(client_mac):  # WHY: Reject malformed MACs
            print(_INVALID_CLIENT_MAC_MSG.format(value=client_mac))  # WHY: Inform the user
            return None  # WHY: Abort
        return str(manager.normalize_mac_address(client_mac))  # WHY: Return normalized MAC

    @staticmethod
    def _select_ap_from_list(manager: Any, helpers: _Helpers, site_id: str) -> str | None:
        """Interactive AP picker path; returns normalized AP MAC or None when nothing chosen."""
        expand_port_range_fn = getattr(manager, "expand_port_range_string", lambda value: [value])  # WHY: Range fn
        prompt_utils = helpers.prompt_network_device_utils(
            manager.mist_session, helpers.input_utils.safe_input, expand_port_range_fn
        )  # WHY: Build the device prompt helper
        ap_mac = prompt_utils.select_ap_mac(site_id)  # WHY: Interactive AP picker
        if not ap_mac:  # WHY: Nothing selected
            return None  # WHY: No AP filter applied
        return str(manager.normalize_mac_address(ap_mac))  # WHY: Return normalized MAC

    @staticmethod
    def _select_ap_manual(manager: Any, helpers: _Helpers) -> tuple[str | None, bool]:
        """Manual AP MAC entry path; returns (mac, ok) where ok=False signals abort."""
        ap_mac = helpers.input_utils.safe_input(_PROMPT_AP_MAC, context="ap_mac")  # WHY: Read AP MAC
        if not manager.validate_mac_address(ap_mac):  # WHY: Reject malformed AP MACs
            print(_INVALID_AP_MAC_MSG.format(value=ap_mac))  # WHY: Inform the user
            return None, False  # WHY: Abort
        return str(manager.normalize_mac_address(ap_mac)), True  # WHY: Normalized MAC + continue

    @classmethod
    def _select_ap_filter(cls, manager: Any, helpers: _Helpers, site_id: str) -> tuple[str | None, bool]:
        """Optionally select an AP filter; return (ap_mac, ok) where ok=False signals abort."""
        print(_AP_HEADER)  # WHY: Prompt header
        print(_AP_OPT_LIST)  # WHY: Option 1 (list)
        print(_AP_OPT_MANUAL)  # WHY: Option 2 (manual)
        print(_AP_OPT_SKIP)  # WHY: Option 3 (skip)
        ap_choice = helpers.input_utils.safe_input(
            _PROMPT_AP_CHOICE, default_value="3", context="ap_filter"
        )  # WHY: Read the AP-filter mode
        if ap_choice == _AP_MODE_LIST:  # WHY: Interactive picker path
            return cls._select_ap_from_list(manager, helpers, site_id), True  # WHY: List path result
        if ap_choice == _AP_MODE_MANUAL:  # WHY: Manual entry path
            return cls._select_ap_manual(manager, helpers)  # WHY: Manual path result
        return None, True  # WHY: Skip - no AP filter, continue

    @staticmethod
    def _prompt_bounded_int(input_utils: Any, spec: SimpleNamespace) -> int | None:
        """Prompt for an integer within spec bounds; return None to abort (message printed)."""
        raw = input_utils.safe_input(spec.prompt, default_value=spec.default, context=spec.context)  # WHY: Read raw
        try:  # WHY: Validate that the input parses as an integer
            value = int(raw)  # WHY: Parse the integer
        except ValueError:  # WHY: Non-numeric input
            print(f"\n! Invalid {spec.invalid_label}: {raw}")  # WHY: Inform the user
            return None  # WHY: Abort
        if value < spec.low or value > spec.high:  # WHY: Enforce the inclusive bounds
            for line in spec.range_lines:  # WHY: Print each range-error line
                print(line)  # WHY: Inform the user
            return None  # WHY: Abort
        return value  # WHY: Validated integer

    @staticmethod
    def _prompt_loop_mode(input_utils: Any) -> bool:
        """Prompt whether to enable continuous loop mode."""
        print(_LOOP_HEADER)  # WHY: Section header
        print(_LOOP_LINE1)  # WHY: Explanation line 1
        print(_LOOP_LINE2)  # WHY: Explanation line 2
        loop_mode = input_utils.safe_input(
            _PROMPT_LOOP, default_value="n", context="loop_mode"
        )  # WHY: Read the loop choice
        return bool(loop_mode.lower() == _YES)  # WHY: Enabled only on explicit yes

    @classmethod
    def _collect_bounded_ints(cls, input_utils: Any) -> tuple[int, ...] | None:
        """Run the three bounded-int prompts (duration, packets, max_pkt_len); None aborts."""
        values: list[int] = []  # WHY: Accumulator for validated integers
        for spec in _BOUNDED_INT_SPECS:  # WHY: Table-driven sequential prompting
            value = cls._prompt_bounded_int(input_utils, spec)  # WHY: Prompt one bounded int
            if value is None:  # WHY: Invalid input (message already printed)
                return None  # WHY: Abort the sequence
            values.append(value)  # WHY: Accept the validated integer
        return tuple(values)  # WHY: Immutable ordered triple

    @classmethod
    def _gather_settings(cls, manager: Any, helpers: _Helpers, site_id: str) -> _Settings | None:
        """Collect all user-provided settings for the capture; return None to abort workflow."""
        client_mac = cls._select_client_mac(manager, helpers, site_id)  # WHY: Resolve client MAC
        if not client_mac:  # WHY: Client selection aborted
            return None  # WHY: Abort workflow
        ap_mac, ap_ok = cls._select_ap_filter(manager, helpers, site_id)  # WHY: Resolve optional AP filter
        if not ap_ok:  # WHY: AP selection aborted
            return None  # WHY: Abort workflow
        ints = cls._collect_bounded_ints(helpers.input_utils)  # WHY: Duration/packets/max_pkt_len
        if ints is None:  # WHY: One of the bounded-int prompts failed
            return None  # WHY: Abort workflow
        return cls._finalize_settings(manager, helpers, client_mac, ap_mac, ints)  # WHY: Assemble the settings

    @classmethod
    def _read_trailing_toggles(cls, manager: Any, helpers: _Helpers) -> tuple[bool, str, str, bool]:
        """Read (includes_mcast, tcpdump_expr, capture_format, enable_loop); trims _finalize_settings."""
        mcast_raw = helpers.input_utils.safe_input(
            _PROMPT_MCAST, default_value="n", context="includes_mcast"
        )  # WHY: Read the multicast choice
        tcpdump_expr = manager._get_tcpdump_expression_selection()  # WHY: Optional tcpdump packet filter
        capture_format = manager._get_capture_format_selection()  # WHY: Capture output format
        enable_loop = cls._prompt_loop_mode(helpers.input_utils)  # WHY: Whether to run continuous loop mode
        return mcast_raw.lower() == _YES, tcpdump_expr, capture_format, enable_loop  # WHY: 4-tuple result

    @classmethod
    def _finalize_settings(
        cls,
        manager: Any,
        helpers: _Helpers,
        client_mac: str,
        ap_mac: str | None,
        ints: tuple[int, ...],
    ) -> _Settings:
        """Read the remaining scalar toggles/format inputs and materialize the _Settings bundle."""
        includes_mcast, tcpdump_expr, capture_format, enable_loop = cls._read_trailing_toggles(manager, helpers)
        return _Settings(
            client_mac=client_mac,
            ap_mac=ap_mac,
            duration=ints[0],
            num_packets=ints[1],
            max_pkt_len=ints[2],
            includes_mcast=includes_mcast,
            tcpdump_expr=tcpdump_expr,
            capture_format=capture_format,
            enable_loop=enable_loop,
        )

    @staticmethod
    def _build_payload(settings: _Settings) -> dict[str, Any]:
        """Build the client capture payload from gathered settings."""
        payload: dict[str, Any] = {
            "type": "client",
            "client_mac": settings.client_mac,
            "duration": settings.duration,
            "num_packets": settings.num_packets,
            "max_pkt_len": settings.max_pkt_len,
            "includes_mcast": settings.includes_mcast,
            "format": settings.capture_format,
        }  # WHY: Core client-capture payload
        if settings.ap_mac:  # WHY: Add the AP filter only when one was chosen
            payload["ap_mac"] = settings.ap_mac  # WHY: Restrict capture to this AP
        if settings.tcpdump_expr:  # WHY: Add a packet filter only when provided
            payload["tcpdump_expression"] = settings.tcpdump_expr  # WHY: Apply the tcpdump expression
        return payload  # WHY: Completed payload

    @staticmethod
    def _ap_filter_rows(ap_mac: str | None) -> list[tuple[str, str]]:
        """Return a single AP-filter row when a MAC is set, else no rows (avoids ternary/or branch)."""
        if ap_mac:  # WHY: Only emit the row when an AP filter was selected
            return [("AP MAC Filter", ap_mac)]  # WHY: Single-row list keeps caller branch-free
        return []  # WHY: Skip AP row entirely when no filter set

    @classmethod
    def _summary_rows(cls, settings: _Settings) -> list[tuple[str, str]]:
        """Return ordered (label, value) rows for the summary table; keeps _print_summary CC low."""
        filter_display = settings.tcpdump_expr if settings.tcpdump_expr else _FILTER_NONE_LABEL  # WHY: None label
        packets_hint = _PACKETS_HINT_MAP[settings.num_packets == 0]  # WHY: Table-driven hint (no ternary branch)
        rows: list[tuple[str, str]] = [
            ("Capture Type", "Wireless Client"),
            ("Client MAC", settings.client_mac),
        ]  # WHY: Base rows always emitted
        rows.extend(cls._ap_filter_rows(settings.ap_mac))  # WHY: Optional AP filter row (no inline ternary)
        rows.extend(
            [
                ("Packet Filter", filter_display),
                ("Duration", f"{settings.duration} seconds"),
                ("Packets", f"{settings.num_packets} ({packets_hint})"),
                ("Max Packet Length", f"{settings.max_pkt_len} bytes"),
                ("Include Multicast", _YES_NO_MAP[settings.includes_mcast]),
                ("Format", settings.capture_format),
                ("Loop Mode", _LOOP_LABEL_MAP[settings.enable_loop]),
            ]
        )  # WHY: Trailing rows appended en bloc
        return rows  # WHY: Ordered summary rows

    @classmethod
    def _print_summary(cls, settings: _Settings) -> None:
        """Print the capture configuration summary using table-driven rendering."""
        print("\n" + _DIVIDER_EQUAL)  # WHY: Top divider
        print(_SUMMARY_TITLE)  # WHY: Section title
        print(_DIVIDER_EQUAL)  # WHY: Divider
        for label, value in cls._summary_rows(settings):  # WHY: Uniform label-value rendering
            print(f"  {label}: {value}")  # WHY: One row per iteration (no branching)
        print(_DIVIDER_EQUAL)  # WHY: Bottom divider

    @staticmethod
    def _dispatch(manager: Any, site_id: str, payload: dict[str, Any], enable_loop: bool) -> None:
        """Dispatch to loop or single capture based on the resolved loop-mode flag."""
        if enable_loop:  # WHY: Continuous loop mode
            manager._execute_site_capture_loop(site_id, payload)  # WHY: Run captures in a loop
            return  # WHY: Loop path complete
        manager._execute_site_capture(site_id, payload)  # WHY: Run a single capture

    @classmethod
    def execute(cls, manager: Any) -> None:
        """Run wireless client packet capture workflow using manager dependencies."""
        helpers = _Helpers(*_resolve_prompt_helpers())  # WHY: Frozen helper bundle
        logging.info(_LOG_START)  # WHY: Trace workflow start
        site_id = helpers.prompt_utils.select_site_with_logging()  # WHY: Prompt for the target site
        if not site_id:  # WHY: No site chosen (message already printed by helper)
            return  # WHY: Abort the workflow
        cls._print_intro()  # WHY: Show the configuration banner
        settings = cls._gather_settings(manager, helpers, site_id)  # WHY: Collect all inputs
        if settings is None:  # WHY: Any prompt aborted (message already printed)
            return  # WHY: Abort the workflow
        payload = cls._build_payload(settings)  # WHY: Construct the API payload
        cls._print_summary(settings)  # WHY: Show the configuration summary
        helpers.input_utils.safe_input(
            _PROMPT_CONFIRM, context="confirmation", allow_empty=True
        )  # WHY: Final confirmation before starting
        cls._dispatch(manager, site_id, payload, settings.enable_loop)  # WHY: Loop vs single capture dispatch

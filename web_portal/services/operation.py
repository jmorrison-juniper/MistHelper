"""Operation execution service for the MistHelper web portal.

Dispatches menu operations in background threads, tracks run state,
captures log output, and publishes SSE events via PortalEventBus.
"""

import logging
import os
import re
import threading
import time
import uuid
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import wait as wait_for_futures
from typing import Any

from src.utils.operation_registry import OperationRegistry
from web_portal.services.output_scan import OutputFileScanner

logger = logging.getLogger(__name__)  # Use a module logger so records include this module name.

# The page groups the operations under a readable heading. A number outside
# every range below lands under "Other", which stays correct but less helpful.
# Issue #3082 widened the portal to every safe operation, so the ranges now
# cover the whole registry instead of stopping at menu 89.
CATEGORY_RANGES = [
    (1, 4, "Core Organization"),
    (5, 8, "WebSocket Device Commands"),
    (9, 10, "Packet Captures"),
    (11, 19, "Organization Exports"),
    (20, 28, "Location Exports"),
    (29, 34, "Site Data Exports"),
    (35, 39, "Template Exports"),
    (40, 41, "Statistics & Analytics"),
    (42, 48, "Security & Configuration"),
    (49, 62, "Site Config & Monitoring"),
    (63, 65, "Work In Progress"),
    (66, 89, "Insights & Diagnostics"),
    (90, 96, "Device Troubleshooting"),
    (188, 208, "Org Administration"),
    (209, 234, "Site Operations"),
    (235, 247, "Counts & Summaries"),
    (248, 268, "Endpoint Explorer"),
    (269, 269, "Network Security Scans"),
]

# Menu numbers whose range gives the wrong category name. Issue #3153.
#
# A menu number records when an operation joined the menu. It does not record
# what the operation does. The ranges above therefore misfiled eight rows, and
# three category names described no operation they held. An operator who opened
# "Packet Captures" found two device inventory exports and no packet capture.
#
# Each entry below states the label the operator reads, so a reviewer can judge
# the destination without opening the menu.
CATEGORY_OVERRIDES = {
    5: "Organization Exports",  # Export E911 report for the organization.
    6: "Insights & Diagnostics",  # Site Config Analysis across every site.
    7: "Insights & Diagnostics",  # Site Inventory Health Analysis across every site.
    8: "Organization Exports",  # Export the full inventory of devices in the organization.
    9: "Organization Exports",  # Export a list of all devices in the organization.
    10: "Organization Exports",  # Export all devices with site and address information.
    40: "Template Exports",  # Export AP template information for the organization.
    41: "Template Exports",  # Export switch template information for the organization.
}

# The safety categories that the portal may run. `OperationRegistry` in
# src/utils/operation_registry.py is the single source of truth for the safety
# category of every operation, and this set is the only gate the portal applies.
#
# Issue #3082: a second bound, DESTRUCTIVE_THRESHOLD, once compared the menu
# number against 90. A menu number states when an operation was added, and it
# states nothing about what the operation does. That bound hid 79 operations
# that the registry calls safe, and it forced an explicit allowlist for menu
# 269. A new safe operation above the bound never appeared, and no test reported
# the absence. The registry verdict now decides alone.
PORTAL_RUNNABLE_CATEGORIES = frozenset({"safe", "interactive_safe"})

# --- Run registry memory caps ----------------------------------------------
# The portal runs as one long-lived Gunicorn worker. Issue #1860 showed that an
# unbounded run registry drives that worker into an out-of-memory kill, and the
# kill can interrupt a write to the data directory. Every cap below is a
# default. An operator raises or lowers a cap with the matching environment
# variable, which deploy/.env.example documents.

# Maximum log entries one run keeps in each of its two log stores.
DEFAULT_RUN_LOG_MAX_ENTRIES = 2000

# Maximum finished runs the registry keeps. An active run never counts here.
DEFAULT_RUN_HISTORY_MAX = 50

# Seconds the registry keeps a finished run. One hour matches the event bus.
DEFAULT_RUN_RETENTION_SECONDS = 3600

# Maximum output file names one run keeps. A per-site export writes one name
# for each site, so a large organization can report thousands of names.
DEFAULT_RUN_OUTPUT_FILES_MAX = 500

# The two states that mark work the portal must never evict.
ACTIVE_RUN_STATUSES = ("pending", "running")

# Seconds shutdown() waits for in-flight runs before it drops the pool.
# Issue #1861: without a bound, a stuck run could hang a restart forever.
DEFAULT_OPERATION_SHUTDOWN_GRACE_SECONDS = 30

# A completed run with no file must still state the empty-result reason.
NO_OUTPUT_REASON_MARKERS = (
    "no ",  # Most empty-result lines start with "No ... data found".
    "not found",  # Some selection helpers use this wording for an empty lookup.
    "returned no data",  # Some get-by-id handlers use this explicit API result line.
    "skipping",  # Some optional workflows report an intentional skip.
    "0 ",  # Some summary lines state that zero records were exported.
)

# A missing required answer is not a successful run, even when the handler returned.
MISSING_INPUT_MARKERS = (
    "no site selected",  # Site-scoped handlers log this when the portal supplied no site answer.
    "no client input provided",  # Client insight handlers log this when no client answer arrived.
    "no device selected",  # Device insight handlers log this when no device answer arrived.
    "no identifier supplied",  # Get-by-id handlers log this when a required ID is blank.
    "no beacon selected",  # Beacon detail handlers log this when the beacon ID is blank.
    "no value provided",  # Shared identifier prompts log this when a required value is blank.
    "not available in web portal",  # The executor logs this when raw interactive input is required.
)

# A handler that catches its own API error still did not produce a successful result.
HANDLED_ERROR_MARKERS = (
    "error fetching",  # Exporters use this wording when an SDK call failed and was caught.
    "failed to",  # Other helpers use this wording for a caught operational failure.
    "could not",  # Prompt and lookup helpers use this wording for an unrecoverable failure.
)


def _read_positive_int_env(name: str, default: int) -> int:
    """Read a positive whole number cap from the environment."""
    raw = os.environ.get(name)  # An unset variable keeps the documented default.
    if raw is None:
        return default  # Return early, because the operator set no override.
    try:
        value = int(raw)  # The operator supplies the cap as a decimal string.
    except ValueError:
        # Report the bad value, because a silent fallback hides an operator mistake.
        logging.warning("Ignoring %s: the value %r is not a whole number", name, raw)
        return default  # Keep the default, because an unusable value must not remove the cap.
    if value < 1:
        # Report the bad value, because a cap below one would discard every record.
        logger.warning("Ignoring %s: the value %d is below the minimum of 1", name, value)
        return default  # Keep the default, because the cap must hold at least one item.
    return value  # Accept the override, because the value is usable.


# --- Parameter Definitions -------------------------------------------------
# Each entry maps a menu number to its category and ordered parameter list.
# param_type: site, device, client, choice, text, number
# depends_on: name of parameter this depends on (for cascading dropdowns)
# device_filter: ap, switch, gateway, all (only for param_type=device)

PARAMETER_REGISTRY = {}


def _site_param(required: bool = True) -> dict:
    """Build a site-type parameter definition."""
    return {
        "name": "site_id",
        "label": "Site",
        "param_type": "site",
        "required": required,
    }


def _device_param(device_filter: str = "all") -> dict:
    """Build a device-type parameter definition."""
    return {
        "name": "device_id",
        "label": "Device",
        "param_type": "device",
        "required": True,
        "depends_on": "site_id",
        "device_filter": device_filter,
    }


def _text_param(name: str, label: str, **kwargs) -> dict:
    """Build a text-type parameter definition."""
    param = {"name": name, "label": label, "param_type": "text", "required": False}
    param.update(kwargs)
    return param


def _number_param(name: str, label: str, **kwargs) -> dict:
    """Build a number-type parameter definition."""
    param = {"name": name, "label": label, "param_type": "number", "required": False}
    param.update(kwargs)
    return param


def _required_text_param(name: str, label: str, **kwargs) -> dict:
    """Build a required text parameter definition."""
    param = _text_param(name, label, **kwargs)  # Reuse the optional text builder so all text metadata stays uniform.
    param["required"] = True  # Make the Run button wait for the identifier that the API path requires.
    return param  # Return a complete parameter definition for the portal form.


def _choice_param(name: str, label: str, options: list, **kwargs) -> dict:
    """Build a choice-type parameter definition."""
    param = {
        "name": name,
        "label": label,
        "param_type": "choice",
        "required": True,
        "options": options,
    }
    param.update(kwargs)
    return param


def _indexed_options(operation_names: list) -> list:
    """Number a list of operation names the way the chooser prompt numbers them.

    Why:
        ``CountExporter._choose`` and ``SimpleEndpointExporter._choose`` print a
        numbered table and then read one digit. The recorded answer must be that
        digit, so the control stores the position and shows the operation name.

    Args:
        operation_names: The operation names, in the order the chooser prints them.

    Returns:
        One option for each name, whose value is the 1-based position.
    """
    # The chooser numbers its rows from one, so the value must match that origin.
    return [{"value": str(position), "label": name} for position, name in enumerate(operation_names, start=1)]


def _site_scoped_chooser_options() -> tuple:
    """Return the count and simple-endpoint choices that menus 236 and 261 offer.

    Why:
        Both menus print a table built from a tuple in the exporter module. A
        second copy of those names here would drift the moment either tuple
        changed, and the operator would then pick the wrong operation. Reading
        the tuples keeps one source of truth.

    Returns:
        The count options and the simple-endpoint options, in chooser order.
    """
    # These modules already load when the menu table builds, so the import is
    # resolved by this point and costs nothing extra.
    from src.export.count_exporter import _SITE_OPS as site_count_ops
    from src.export.simple_endpoint_exporter import _SITE_OPS as site_endpoint_ops

    count_options = _indexed_options([entry.operation for entry in site_count_ops])  # Menu 236 offers these.
    endpoint_options = _indexed_options([entry.operation for entry in site_endpoint_ops])  # Menu 261 offers these.
    return count_options, endpoint_options


def _build_registry() -> dict:
    """Build the full PARAMETER_REGISTRY mapping."""
    registry = {}

    # --- Simple site-only operations (1 prompt: site) ---
    site_only_menus = [
        "29",
        "30",
        "31",
        "32",
        "34",
        "49",
        "50",
        "51",
        "52",
        "53",
        "66",  # Menu 66 prompts for a site before it can list site beacons.
        "68",
        "70",
        "71",
        "84",
        "210",  # Menu 210 prompts for a site before it can read assets of interest.
        "213",  # Menu 213 prompts for a site before it can read the application list.
        "224",  # Menu 224 prompts for a site before it can search rogue events.
        # Issues #3179, #3151, and #3152. Each row below reaches exactly one
        # site prompt in its call graph, offered no control, and failed every
        # run of the full sweep with "No site selected". The operation printed
        # all 143 sites to the log, read a closed input stream, and gave up.
        "60",  # SiteDeviceExporter.devices
        "61",  # SiteDeviceExporter.device_stats
        "65",  # SiteClientExporter.clients
        "77",  # SiteAnomalyExporter.anomaly_events
        "92",  # PromptUtils.select_site_with_logging
        "93",  # InteractiveDisplayUtils.site_inventory
        "198",  # SiteWanUsageExporter.wan_usages
        "200",  # SiteGuestAuthorizationExporter.guest_authorization
        "201",  # SiteMistEdgeEventsExporter.mist_edge_events
        "202",  # SiteNacClientEventsExporter.nac_client_events
        "214",  # SiteSystemEventsExporter.system_events
        "215",  # SiteSearchExporter.alarms
        "216",  # SiteSearchExporter.assets
        "217",  # SiteSearchExporter.bgp_stats
        "218",  # SiteSearchExporter.calls
        "219",  # SiteSearchExporter.skyatp_events
        "220",  # SiteSearchExporter.wireless_client_events
        "221",  # SiteSearchExporter.wan_clients
        "222",  # SiteSearchExporter.device_events
        "223",  # SiteSearchExporter.devices
        "225",  # SiteSearchExporter.ospf_stats
        "226",  # SiteSearchExporter.device_last_configs
        "227",  # SiteSearchExporter.device_config_history
        "228",  # SiteSearchExporter.discovered_switches
        "244",  # SiteSearchExporter.service_path_events
        "257",  # SiteSearchExporter.nac_clients
        "258",  # SiteOtherDeviceEventsExporter.other_device_events
        # These rows reach a site prompt first and a plain input() call after
        # it. The sweep proved that a plain call survives a closed stream by
        # taking its default, so the site control alone unblocks the run.
        "63",  # SiteDeviceExporter.device_virtual_chassis
        "78",  # SiteAnomalyExporter.device_anomaly_events
        "199",  # SiteWebhookDeliveriesExporter.deliveries
    ]
    for menu in site_only_menus:
        registry[menu] = {
            "category": "interactive",
            "parameters": [_site_param()],
        }

    # Each row below reaches a site prompt and then one or more identifier
    # prompts that reject an empty answer. A site control alone let the run
    # start and then abort at the identifier prompt, so the portal reported a
    # complete run that wrote nothing. Issues #3181 and #3184 recorded that
    # silent abort. Every prompt now owns a control, in prompt order.
    registry["211"] = {  # Menu 211 reads one asset filter by its identifier.
        "category": "interactive",  # The portal must collect both values before Run.
        "parameters": [
            _site_param(),  # Answer the site prompt the handler reads first.
            _required_text_param(  # Answer the asset filter prompt that rejects an empty value.
                "assetfilter_id", "Asset Filter ID", placeholder="Mist asset filter UUID"
            ),
        ],
    }
    registry["212"] = {  # Menu 212 reads one asset by its identifier.
        "category": "interactive",  # The portal must collect both values before Run.
        "parameters": [
            _site_param(),  # Answer the site prompt the handler reads first.
            _required_text_param(  # Answer the asset prompt that rejects an empty value.
                "asset_id", "Asset ID", placeholder="Mist asset UUID"
            ),
        ],
    }
    registry["246"] = {  # Menu 246 troubleshoots one call for one client meeting.
        "category": "interactive",  # The portal must collect all three values before Run.
        "parameters": [
            _site_param(),  # Answer the site prompt the handler reads first.
            _required_text_param(  # Answer the client MAC prompt that rejects an empty value.
                "client_mac", "Client MAC", placeholder="98:3a:78:ea:4a:44"
            ),
            _required_text_param(  # Answer the meeting prompt that rejects an empty value.
                "meeting_id", "Meeting ID", placeholder="Meeting UUID"
            ),
        ],
    }

    # Menus 229, 236, and 261 each reach a plain prompt BEFORE the site prompt.
    # A site control alone would send the site name to that first prompt and
    # leave the site prompt reading a closed stream, so the run would still
    # fail. Each row therefore declares its first answer first, then the site.
    # Issue #3196 recorded this ordering requirement.
    count_options, endpoint_options = _site_scoped_chooser_options()  # Read both chooser tables once.

    registry["229"] = {  # Menu 229 searches zone sessions for one site.
        "category": "interactive",  # The portal must collect both answers before Run.
        "parameters": [
            _choice_param(  # Answer the zone type prompt the handler reads first.
                "zone_type",
                "Zone Type",
                [
                    {"value": "zones", "label": "zones"},  # The SDK path accepts this value.
                    {"value": "rssizones", "label": "rssizones"},  # The SDK path accepts this value.
                ],
                default="zones",  # The prompt uses the same default for an empty answer.
            ),
            _site_param(),  # Answer the site prompt the handler reads second.
        ],
    }
    registry["236"] = {  # Menu 236 runs one site-scoped count operation.
        "category": "interactive",  # The portal must collect both answers before Run.
        "parameters": [
            _choice_param("count_operation", "Count Operation", count_options),  # The chooser reads this digit first.
            _site_param(),  # Answer the site prompt the handler reads second.
        ],
    }
    registry["261"] = {  # Menu 261 runs one site-scoped simple read endpoint.
        "category": "interactive",  # The portal must collect both answers before Run.
        "parameters": [
            _choice_param("endpoint_operation", "Endpoint", endpoint_options),  # The chooser reads this digit first.
            _site_param(),  # Answer the site prompt the handler reads second.
        ],
    }

    # --- Site + device (all types) ---
    site_device_all_menus = ["72", "74", "80", "81", "85"]
    for menu in site_device_all_menus:
        registry[menu] = {
            "category": "interactive",
            "parameters": [_site_param(), _device_param("all")],
        }

    # --- Site + switch ---
    for menu in ["5", "33"]:
        registry[menu] = {
            "category": "interactive",
            "parameters": [_site_param(), _device_param("switch")],
        }

    # --- Site + gateway ---
    registry["73"] = {
        "category": "interactive",
        "parameters": [_site_param(), _device_param("gateway")],
    }

    registry["75"] = {  # Menu 75 asks for a site and then one client.
        "category": "interactive",  # The portal must render input controls before Run.
        "parameters": [
            _site_param(),  # Answer the site prompt that the handler reads first.
            {
                "name": "client_mac",  # Match the client selector name used by the browser form.
                "label": "Client",  # Show the operator the required client choice.
                "param_type": "client",  # Load clients after the site choice is known.
                "required": True,  # A client insight export cannot run without a client.
                "depends_on": "site_id",  # Keep the client selector scoped to the selected site.
            },
        ],
    }

    registry["76"] = {  # Menu 76 asks for a site and then one device.
        "category": "interactive",  # The portal must render input controls before Run.
        "parameters": [_site_param(), _device_param("all")],  # Answer the site and device prompts.
    }

    # --- Forwarding table (menu 6): gateway + text fields ---
    registry["6"] = {
        "category": "interactive",
        "parameters": [
            _site_param(),
            _device_param("gateway"),
            _text_param("prefix", "IP Prefix", placeholder="0.0.0.0/0", default="0.0.0.0/0"),
            _text_param("service_name", "Service Name", placeholder="press Enter to skip"),
            _text_param("vrf", "VRF Name", placeholder="press Enter to skip"),
            _text_param("node", "Node", placeholder="node0/node1 for HA"),
        ],
    }

    # --- Routing table (menu 7): switch + text fields ---
    registry["7"] = {
        "category": "interactive",
        "parameters": [
            _site_param(),
            _device_param("switch"),
            _text_param("prefix", "Route Prefix", placeholder="press Enter to show all"),
            _text_param("protocol", "Protocol Filter", placeholder="press Enter for any"),
            _text_param("vrf", "VRF Name", placeholder="press Enter to skip"),
            _text_param("neighbor", "BGP Neighbor IP", placeholder="press Enter to skip"),
        ],
    }

    # --- SSR routes (menu 8): gateway + many params ---
    registry["8"] = {
        "category": "interactive",
        "parameters": [
            _site_param(),
            _device_param("gateway"),
            _text_param("protocol", "Protocol", placeholder="press Enter for API default"),
            _text_param("prefix", "Route Prefix", placeholder="e.g. 192.168.1.0/24"),
            _text_param("vrf", "VRF Name", placeholder="press Enter for default VRF"),
            _text_param("neighbor", "BGP Neighbor IP", placeholder="press Enter to skip"),
        ],
    }

    # --- Ping device (menu 87) ---
    registry["87"] = {
        "category": "interactive",
        "parameters": [
            _site_param(),
            _device_param("all"),
            _text_param("target_host", "Target Host/IP", default="8.8.8.8", placeholder="8.8.8.8"),
            _number_param("ping_count", "Ping Count", default="4", min_value=1, max_value=100),
        ],
    }

    # --- ARP device (menu 88) ---
    registry["88"] = {
        "category": "interactive",
        "parameters": [_site_param(), _device_param("all")],
    }

    # --- Client operations ---
    # Menus 69 and 86 once carried a client control as well. Neither handler
    # asks for a client. SiteConfigExporter.wlans exports the WLAN list of a
    # site, and current_channel_planning reads the RRM plan of a site. Each
    # reaches one site prompt and stops. The extra control forced the operator
    # to answer a question the operation never asks, and the client list was
    # empty for most sites, so the Run control never became usable. Issue #3191
    # recorded that blocked state.
    registry["69"] = {  # Menu 69 exports the WLAN list of one site.
        "category": "interactive",  # The portal must render the site control before Run.
        "parameters": [_site_param()],  # Answer the single site prompt the handler reaches.
    }
    registry["86"] = {  # Menu 86 exports the RRM channel and power plan of one site.
        "category": "interactive",  # The portal must render the site control before Run.
        "parameters": [_site_param()],  # Answer the single site prompt the handler reaches.
    }

    registry["209"] = {  # Menu 209 asks for raw identifiers, not a site name.
        "category": "interactive",  # The portal must block Run until both identifiers exist.
        "parameters": [
            _required_text_param("site_id", "Site ID", placeholder="Mist site UUID"),  # API path site identifier.
            _required_text_param(  # Build the required beacon identifier control.
                "beacon_id", "Beacon ID", placeholder="Mist beacon UUID"  # API path beacon identifier.
            ),
        ],
    }

    # --- Service ping (menu 89): gateway + many params ---
    registry["89"] = {
        "category": "interactive",
        "parameters": [
            _site_param(),
            _device_param("gateway"),
            _text_param("tenant", "Tenant", placeholder="select index or skip"),
            _text_param("service", "Service", placeholder="select index or enter custom"),
            _text_param("host", "Target Host/IP", default="8.8.8.8", placeholder="8.8.8.8"),
            _number_param("count", "Ping Count", default="4", min_value=1, max_value=100),
        ],
    }

    # --- Packet captures (complex interactive) ---
    registry["9"] = {
        "category": "interactive",
        "parameters": [
            _choice_param(
                "capture_type",
                "Capture Type",
                [
                    {"value": "1", "label": "Wireless Client"},
                    {"value": "2", "label": "Wired Client"},
                    {"value": "3", "label": "Gateway"},
                    {"value": "4", "label": "Switch"},
                    {"value": "5", "label": "New Association"},
                    {"value": "6", "label": "Scan Radio"},
                ],
            ),
            _site_param(),
            _text_param("client_mac", "Client MAC", placeholder="e.g. aa:bb:cc:dd:ee:ff"),
            _number_param("duration", "Duration (seconds)", default="60", min_value=10, max_value=300),
            _number_param("num_packets", "Packet Count", default="100", min_value=1, max_value=10000),
            _number_param("max_pkt_len", "Max Packet Length", default="128", min_value=64, max_value=1500),
        ],
    }

    registry["10"] = {
        "category": "interactive",
        "parameters": [
            _text_param("mxedge_index", "MxEdge Index", placeholder="select MxEdge index"),
            _text_param("port_index", "Port Index", placeholder="select port index"),
            _text_param("tcpdump_filter", "Tcpdump Filter", placeholder="press Enter for none"),
            _number_param("duration", "Duration (seconds)", default="30", min_value=1, max_value=86400),
            _number_param("num_packets", "Packet Count", default="1024", min_value=0, max_value=10000),
            _number_param("max_pkt_len", "Max Packet Length", default="128", min_value=1, max_value=2048),
        ],
    }

    # --- CLI-only operations ---
    registry["62"] = {
        "category": "cli_only",
        "parameters": [],
        "cli_only_message": (
            "Interactive troubleshooting requires multi-step keyboard input. " "Use SSH access on port 2200."
        ),
    }
    registry["79"] = {
        "category": "cli_only",
        "parameters": [],
        "cli_only_message": (
            "Interactive CLI shell requires persistent keyboard input. " "Use SSH access on port 2200."
        ),
    }
    # Menu 241 starts a metrics server that serves until an operator stops it.
    # A browser run held a worker thread until the request timed out, then
    # reported "Operation requires interactive input". That message named the
    # wrong cause, and the run wasted a thread the portal needs for real work.
    # Issue #3182 recorded the misleading failure.
    registry["241"] = {  # Menu 241 serves Mist Cloud health on port 8057.
        "category": "cli_only",  # The portal hides Run and explains the reason instead.
        "parameters": [],  # A server takes no operator answer, so it needs no control.
        "cli_only_message": (  # Name the port and the start path the operator should use.
            "This operation starts a long-running metrics server on port 8057 and serves "
            "until you stop it. A browser run cannot host it. Start it with the "
            "--metrics-gateway flag, or use SSH access on port 2200."
        ),
    }

    return registry


PARAMETER_REGISTRY = _build_registry()


class OperationExecutor:
    """Execute MistHelper menu operations in background threads.

    Tracks OperationRun state, captures stdout/log output,
    and publishes real-time SSE events via the event bus.
    """

    def __init__(
        self,
        menu_actions: dict,
        apisession: Any | None,
        org_id: str | None,
        event_bus: Any | None,
    ):
        """Initialize with shared MistHelper dependencies."""
        self._menu_actions = menu_actions
        self._apisession = apisession
        self._org_id = org_id
        self._event_bus = event_bus
        self._runs = {}
        self._lock = threading.Lock()
        self._sequence = 0  # A rising number orders the runs when the clock repeats a value.
        self._shutdown_done = False  # Guards shutdown(), so a repeat call is a safe no-op.
        self._configure_limits()  # Read the caps once, so every run shares one setting.
        cpu_count = os.cpu_count() or 2
        max_workers = max(1, cpu_count - 1)
        logger.info("Operation pool: %d workers (CPUs detected: %d)", max_workers, cpu_count)
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="op")

    def _configure_limits(self) -> None:
        """Read the run registry memory caps from the environment."""
        logger.info("Reading the web portal run registry memory caps")  # Log before the read.
        # Each cap reads one variable and falls back to the documented default.
        self._log_max_entries = _read_positive_int_env("PORTAL_RUN_LOG_MAX_ENTRIES", DEFAULT_RUN_LOG_MAX_ENTRIES)
        self._history_max = _read_positive_int_env("PORTAL_RUN_HISTORY_MAX", DEFAULT_RUN_HISTORY_MAX)
        self._retention_seconds = _read_positive_int_env("PORTAL_RUN_RETENTION_SECONDS", DEFAULT_RUN_RETENTION_SECONDS)
        self._output_files_max = _read_positive_int_env("PORTAL_RUN_OUTPUT_FILES_MAX", DEFAULT_RUN_OUTPUT_FILES_MAX)
        # Read the shutdown grace period, so shutdown() honors an operator override.
        self._shutdown_grace_seconds = _read_positive_int_env(
            "PORTAL_OPERATION_SHUTDOWN_GRACE_SECONDS", DEFAULT_OPERATION_SHUTDOWN_GRACE_SECONDS
        )
        # Record the result, so an operator can confirm the caps the portal applied.
        logger.debug(
            "Run caps: %d log entries, %d finished runs, %d seconds of retention, %d output files, "
            "%d second shutdown grace period",
            self._log_max_entries,
            self._history_max,
            self._retention_seconds,
            self._output_files_max,
            self._shutdown_grace_seconds,
        )

    def start_operation(self, menu_number: str, parameters: dict) -> dict:
        """Validate and start an operation in a background thread."""
        error = self._validate_operation(menu_number)
        if error:
            return error
        conflict = self._check_conflict(menu_number)
        if conflict:
            return conflict
        run = self._create_run(menu_number)
        # Keep the future, so shutdown() can wait for this run before it closes the pool.
        run["_future"] = self._pool.submit(self._execute_operation, run, parameters)
        return self._run_to_dict(run)

    def get_run_status(self, run_id: str) -> dict | None:
        """Return current status of a specific operation run."""
        with self._lock:
            run = self._runs.get(run_id)
        if run is None:
            return None
        return self._run_to_dict(run)

    def get_active_runs(self) -> list:
        """Return list of currently running operations."""
        with self._lock:
            return [self._run_to_summary(run) for run in self._runs.values() if run["status"] in ACTIVE_RUN_STATUSES]

    def stop_operation(self, run_id: str) -> dict:
        """Request graceful stop of a running operation.

        Creates the ``stop_loop.txt`` sentinel file that loop-style
        operations (Menu 75/76) check between iterations.  Also marks
        the run as ``failed`` so that ``_check_conflict`` no longer
        blocks a fresh start of the same menu number.

        Returns:
            Dict with status message or error.
        """
        with self._lock:
            run = self._runs.get(run_id)
        if run is None:
            return {"error": "Run not found"}
        if run["status"] not in ACTIVE_RUN_STATUSES:
            return {"error": "Operation is not running"}
        run["_stop_requested"] = True
        self._update_status(run, "failed", 100)
        run["error_message"] = "Stopped by user"
        try:
            stop_path = os.path.join(os.getcwd(), "stop_loop.txt")
            with open(stop_path, "w", encoding="utf-8") as fh:
                fh.write("stop requested by web portal\n")
            logger.info("Stop signal sent for run %s (stop_loop.txt created)", run_id)
        except OSError as exc:
            logging.warning("Could not create stop_loop.txt: %s", exc)
        return {"status": "stop_requested", "run_id": run_id}

    def shutdown(self, grace_seconds: float | None = None) -> None:
        """Wait for in-flight runs, then shut down the worker pool.

        A second call is a no-op. A duplicate shutdown signal, or a
        duplicate call from a test, must not raise or repeat the work.
        """
        with self._lock:
            if self._shutdown_done:  # A prior call already drained the pool, so skip the repeat work.
                logger.debug("Operation pool already shut down, skipping repeat call")
                return
            self._shutdown_done = True  # Mark shutdown first, so a second call returns above.
            # Collect only the futures still in flight, so a finished run is not awaited again.
            pending: list[Future] = [
                run["_future"]
                for run in self._runs.values()
                if run.get("_future") is not None and not run["_future"].done()
            ]
        # Fall back to the configured default, so a caller need not pass a value.
        wait_seconds = self._shutdown_grace_seconds if grace_seconds is None else grace_seconds
        logger.info(
            "Stopping the operation pool: %d run(s) in flight, %s second grace period", len(pending), wait_seconds
        )
        # Bound the wait, so one stuck run cannot hang the whole shutdown path.
        done, not_done = wait_for_futures(pending, timeout=wait_seconds)
        if not_done:
            # Warn, because an operator must know a run did not finish before the pool closed.
            logger.warning("Operation pool shutdown: %d run(s) still in flight after the grace period", len(not_done))
        self._pool.shutdown(wait=False)  # Release the worker threads now, the wait above already bounded the delay.
        logger.info("Operation pool stopped: %d of %d run(s) finished cleanly", len(done), len(pending))

    def build_category_list(self, menu_actions: dict) -> list:
        """Build categorized operation list for the UI."""
        categories = {}
        for key, value in menu_actions.items():
            if not self._is_portal_runnable(key):  # One rule for the page and the run gate.
                continue
            num = self._parse_menu_number(key)  # Safe here, because the gate proved the key parses.
            category = self._get_category(num)
            desc = value.title  # Use the named menu row instead of legacy tuple positions.
            reg_entry = PARAMETER_REGISTRY.get(key)
            op_category = reg_entry["category"] if reg_entry else "non_interactive"
            if category not in categories:
                categories[category] = []
            categories[category].append(
                {
                    "menu_number": key,
                    "description": desc,
                    "category": op_category,
                }
            )
        for operations in categories.values():
            # Sort by the numeric value, not the text. Text order puts "10"
            # before "9", and the page showed an operator a shuffled list.
            operations.sort(key=lambda op: self._parse_menu_number(op["menu_number"]))
        return [{"name": name, "operations": ops} for name, ops in sorted(categories.items(), key=lambda x: x[0])]

    def get_operation_parameters(self, menu_number: str) -> dict | None:
        """Return parameter requirements for an operation."""
        if menu_number not in self._menu_actions:
            return None
        value = self._menu_actions[menu_number]
        desc = value.title  # Use the named menu row instead of legacy tuple positions.
        entry = PARAMETER_REGISTRY.get(menu_number)
        if entry is not None:
            result = {
                "menu_number": menu_number,
                "description": desc,
                "category": entry.get("category", "interactive"),
                "parameters": entry.get("parameters", []),
            }
            if "cli_only_message" in entry:
                result["cli_only_message"] = entry["cli_only_message"]
            return result
        return {
            "menu_number": menu_number,
            "description": desc,
            "category": "non_interactive",
            "parameters": [],
        }

    def _validate_operation(self, menu_number: str) -> dict | None:
        """Check that the operation exists and that the portal may run it."""
        if menu_number not in self._menu_actions:
            return {"error": f"Operation {menu_number} not found"}
        if not self._is_portal_runnable(menu_number):  # One rule for the page and the run gate.
            return {"error": self._refusal_message(menu_number)}
        value = self._menu_actions[menu_number]
        func = value.handler  # Use the named menu row instead of legacy tuple positions.
        if func is None:
            return {"error": "API not authenticated. Connect via SSH to run operations."}
        return None

    def _is_portal_runnable(self, menu_number: str) -> bool:
        """Report whether the portal may run one operation.

        The check reads `OperationRegistry`, which the project documents as the
        single source of truth for the safety category. The check fails closed.
        An unregistered key, an unparseable key, and any category outside
        `PORTAL_RUNNABLE_CATEGORIES` all return False.
        """
        logger.info("Portal checks whether it may run operation %s", menu_number)
        category = OperationRegistry.skip_category(menu_number)  # Authoritative safety verdict.
        num = self._parse_menu_number(menu_number)  # None when int() cannot read the key.
        allowed = (
            category in PORTAL_RUNNABLE_CATEGORIES  # The registry must call the operation safe.
            and num is not None  # A key the page cannot place must never run.
        )
        logger.debug("Portal verdict for operation %s: category=%s allowed=%s", menu_number, category, allowed)
        return allowed

    @staticmethod
    def _refusal_message(menu_number: str) -> str:
        """Build the message that tells the operator why the portal refused."""
        category = OperationRegistry.skip_category(menu_number)  # Name the reason for the refusal.
        return (
            f"Menu number {menu_number} is not a safe operation, so the portal cannot run it. "
            f"The safety category is '{category}'. Connect over SSH to run this operation."
        )

    def _check_conflict(self, menu_number: str) -> dict | None:
        """Check if the same operation is already running."""
        with self._lock:
            for run in self._runs.values():
                if run["menu_number"] == menu_number and run["status"] in ACTIVE_RUN_STATUSES:
                    return {
                        "error": f"Operation {menu_number} is already running",
                        "run_id": run["run_id"],
                    }
        return None

    def _create_run(self, menu_number: str) -> dict:
        """Create a new OperationRun record and bound the registry."""
        run = self._build_run_record(menu_number)  # Build the record apart, so this method stays short.
        with self._lock:
            self._sequence += 1  # Give the run an order that does not depend on the clock resolution.
            run["sequence"] = self._sequence  # Store the order, because two runs can share one timestamp.
            self._runs[run["run_id"]] = run  # Publish the run, so the status endpoints can find it.
        self._prune_runs()  # Prune after the insert, so the registry cannot grow past the cap.
        return run

    def _build_run_record(self, menu_number: str) -> dict:
        """Return one run record that holds bounded log stores."""
        value = self._menu_actions[menu_number]
        desc = value.title  # Use the named menu row instead of legacy tuple positions.
        return {
            "run_id": str(uuid.uuid4()),
            "menu_number": menu_number,
            "description": desc,
            "status": "pending",
            "started_at": time.time(),
            "completed_at": None,
            "progress_pct": 0,
            # A bounded deque drops the oldest entry, so one long run cannot fill the worker memory.
            "log_messages": deque(maxlen=self._log_max_entries),
            "debug_messages": deque(maxlen=self._log_max_entries),
            # The counter covers both stores, so the operator sees the total loss.
            "dropped_log_count": 0,
            "error_message": None,
            # A bounded deque keeps the newest name, so a per-site export cannot grow the record.
            "output_files": deque(maxlen=self._output_files_max),
            # The counter reports the output file names the cap discarded.
            "dropped_output_file_count": 0,
            "completion_message": None,
        }

    def _prune_runs(self) -> None:
        """Remove the finished runs that pass the cap or the retention period."""
        with self._lock:
            # Select the finished runs only, because an active run must survive every prune.
            finished = [(rid, run) for rid, run in self._runs.items() if run["status"] not in ACTIVE_RUN_STATUSES]
            stale = self._select_stale_runs(finished)  # Decide inside the lock, so the registry cannot change.
            for run_id in stale:
                del self._runs[run_id]  # Drop the record, so the worker gets the memory back.
            remaining = len(self._runs)  # Read the size inside the lock, because another thread can add a run.
        if stale:
            # Log the removal, so an operator can explain a run record that left the portal.
            logger.info("Removed %d finished operation runs, %d runs remain", len(stale), remaining)

    def _select_stale_runs(self, finished: list) -> list:
        """Return the identifiers of the finished runs the portal may drop.

        The caller holds the registry lock. Only finished runs reach this
        method, so the portal never evicts a pending or a running operation.
        """
        cutoff = time.time() - self._retention_seconds  # A run that ended before this time is past retention.
        ordered = sorted(finished, key=self._sort_key, reverse=True)  # Put the newest finished run first.
        stale = [run_id for run_id, _ in ordered[self._history_max :]]  # Every run past the cap leaves.
        kept = ordered[: self._history_max]  # The cap keeps the most recent finished runs.
        stale.extend(run_id for run_id, run in kept if self._finished_at(run) < cutoff)  # Retention drops old work.
        return stale

    def _sort_key(self, item: tuple) -> tuple:
        """Return the key that orders the finished runs from oldest to newest."""
        run = item[1]  # A registry item pairs the identifier with the record.
        return (self._finished_at(run), run.get("sequence", 0))  # The sequence breaks a clock tie.

    @staticmethod
    def _finished_at(run: dict) -> float:
        """Return the time the run finished, or the start time as the fallback."""
        return run["completed_at"] or run["started_at"]

    def _execute_operation(self, run: dict, parameters: dict) -> None:
        """Execute the operation function in a background thread."""
        from web_portal.services.input_hook import web_input_context

        self._update_status(run, "running", 0)
        input_answers = parameters.get("input_answers", [])
        try:
            func = self._menu_actions[run["menu_number"]].handler  # Use the named menu row for execution.
            if input_answers:
                with web_input_context(input_answers):
                    self._capture_and_run(run, func)
            else:
                self._capture_and_run(run, func)
            if not run.get("_stop_requested"):
                self._finish_successful_operation(run)  # Assess result evidence before the portal reports success.
        except (EOFError, SystemExit):
            if not run.get("_stop_requested"):
                self._handle_failure(run, "Operation requires interactive input (not available in web portal)")
        except Exception as exc:
            if not run.get("_stop_requested"):
                self._handle_failure(run, str(exc))

    def _capture_and_run(self, run: dict, func) -> None:
        """Run function with log capture via a logging handler.

        Captures logging output from the operation function and publishes
        it via SSE. Print output goes to container stdout (not captured)
        since MistHelper logs all meaningful progress via logging.info().

        A scanner watches the data directory around the call, because the log
        prose names only some of the files an operation writes (issue #3089).
        """
        handler = _RunLogHandler(run, self._event_bus)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        scanner = OutputFileScanner()  # Read the data directory the portal writes into.
        scanner.snapshot()  # Record the pre-run state, so a new file is visible later.
        try:
            func()
        finally:
            root_logger.removeHandler(handler)
            self._record_scanned_files(run, scanner)  # Report a file even when no log line named it.

    def _finish_successful_operation(self, run: dict) -> None:
        """Mark a returned handler as complete only when the result is honest."""
        logger.info("Assessing operation %s result evidence", run["menu_number"])  # Log before the evidence check.
        missing_input = self._missing_input_reason(run)  # Read the log for a required answer that never arrived.
        if missing_input:  # A required missing answer means the operation did not really run.
            logger.debug("Operation %s missed required input: %s", run["menu_number"], missing_input)  # Result trace.
            self._handle_failure(run, f"Operation could not run because required input was missing: {missing_input}")
            return
        handled_error = self._handled_error_reason(run)  # Read the log for an error that the handler caught.
        if handled_error:  # A caught handler error must not report as successful completion.
            logger.debug(  # Result trace.
                "Operation %s returned after a handled error: %s", run["menu_number"], handled_error
            )
            self._handle_failure(run, handled_error)  # Surface the concrete handler error to the status record.
            return
        completion_message = self._completion_message(run)  # Build the message shown on the completed run.
        if completion_message is None:  # No file and no no-data reason would be silent success.
            logger.debug("Operation %s produced no output evidence", run["menu_number"])  # Result trace.
            self._handle_failure(run, "Operation finished without an output file or a no-data message.")
            return
        run["completion_message"] = completion_message  # Store the message for REST replay and SSE completion.
        logger.debug("Operation %s completion message: %s", run["menu_number"], completion_message)  # Result trace.
        self._update_status(run, "completed", 100)  # Mark completion only after the evidence check passes.
        self._publish_complete(run)  # Publish the complete event with the honest result message.

    def _completion_message(self, run: dict) -> str | None:
        """Return a completion message that names a file or an empty-result reason."""
        if run["output_files"]:  # Output files are concrete evidence that the operation produced a result.
            return "Operation completed"  # Keep the established success message when a result exists.
        reason = self._no_output_reason(run)  # Read the main log for the empty-result explanation.
        if reason:  # A readable no-data line is an honest completed result.
            return f"Operation completed with no output file: {reason}"
        return None  # No file and no explanation must not become a silent success.

    def _missing_input_reason(self, run: dict) -> str | None:
        """Return the first log line that says a required input was missing."""
        for message in self._run_log_messages(run):  # Scan the user-facing log in the order the operator saw.
            lowered = message.lower()  # Normalize case so marker checks stay simple.
            if any(marker in lowered for marker in MISSING_INPUT_MARKERS):  # Detect a required missing answer.
                return message  # Return the exact log line, so the operator sees the concrete missing input.
        return None  # No missing-input message appeared.

    def _handled_error_reason(self, run: dict) -> str | None:
        """Return the first log line that says the handler caught an error."""
        for message in self._run_log_messages(run):  # Scan the user-facing log in the order the operator saw.
            lowered = message.lower()  # Normalize case so marker checks stay simple.
            if any(marker in lowered for marker in HANDLED_ERROR_MARKERS):  # Detect a caught handler failure.
                return message  # Return the exact error line, so the operator sees the concrete cause.
        return None  # No handled-error message appeared.

    def _no_output_reason(self, run: dict) -> str | None:
        """Return the first log line that explains a completed run with no file."""
        for message in reversed(self._run_log_messages(run)):  # Prefer the latest summary line.
            lowered = message.lower()  # Normalize case so marker checks stay simple.
            if any(marker in lowered for marker in NO_OUTPUT_REASON_MARKERS):  # Detect an empty-result explanation.
                return message  # Return the exact line from the handler.
        return None  # No empty-result message appeared.

    @staticmethod
    def _run_log_messages(run: dict) -> list[str]:
        """Return the user-facing log messages from a run record."""
        messages: list[str] = []  # Keep a plain list so callers can scan more than once.
        for entry in run.get("log_messages", []):  # The run stores dict entries from _RunLogHandler.
            if isinstance(entry, dict):  # Normal path for records captured by the handler.
                messages.append(str(entry.get("message", "")))  # Use only the text for marker checks.
            else:  # Defensive path for older tests or legacy run records.
                messages.append(str(entry))  # Preserve the message text in a uniform list.
        return messages  # Return the normalized log messages.

    def _record_scanned_files(self, run: dict, scanner: OutputFileScanner) -> None:
        """Merge the scanned file names into the run record without a duplicate."""
        logger.info("Run %s collects the files it wrote", run["run_id"])  # Log before the comparison.
        try:
            found = scanner.changed_files()  # Ask the directory, not the log prose.
        except OSError as error:  # A scan failure must not fail an operation that already finished.
            logging.warning("Run %s could not scan %s: %s", run["run_id"], scanner.root, error)
            return
        known = set(run["output_files"])  # The log scrape may already hold a name.
        added = [name for name in found if name not in known]
        for name in added:
            run["output_files"].append(name)  # The bounded deque drops the oldest name when it is full.
        logger.debug("Run %s added %d scanned files to %d known names", run["run_id"], len(added), len(known))

    def _update_status(self, run: dict, status: str, progress: int) -> None:
        """Update run status and publish SSE event."""
        with self._lock:
            run["status"] = status
            run["progress_pct"] = progress
            if status in ("completed", "failed"):
                run["completed_at"] = time.time()
        if self._event_bus:
            self._event_bus.publish(
                "status",
                {
                    "run_id": run["run_id"],
                    "status": status,
                    "progress_pct": progress,
                    "menu_number": run["menu_number"],
                    "description": run["description"],
                },
            )
        if status not in ACTIVE_RUN_STATUSES:
            self._prune_runs()  # Free an old finished run as soon as this run finishes.

    def _publish_complete(self, run: dict) -> None:
        """Publish completion SSE event."""
        if not self._event_bus:
            return
        duration = (run["completed_at"] or time.time()) - run["started_at"]
        self._event_bus.publish(
            "complete",
            {
                "run_id": run["run_id"],
                "status": "completed",
                "message": run.get("completion_message") or "Operation completed",
                "completion_message": run.get("completion_message") or "Operation completed",
                # Copy the bounded deque into a list, so the SSE stream can encode the event.
                "output_files": list(run["output_files"]),
                "duration_seconds": round(duration, 1),
            },
        )

    def _handle_failure(self, run: dict, message: str) -> None:
        """Update run to failed state and publish error event."""
        with self._lock:
            run["status"] = "failed"
            run["error_message"] = message
            run["completed_at"] = time.time()
        if self._event_bus:
            duration = run["completed_at"] - run["started_at"]
            self._event_bus.publish(
                "error_event",
                {
                    "run_id": run["run_id"],
                    "status": "failed",
                    "message": message,
                    "error_message": message,
                    "duration_seconds": round(duration, 1),
                },
            )
        self._prune_runs()  # A failed run is finished, so free an old record now.

    def _run_to_dict(self, run: dict) -> dict:
        """Convert run record to API response format."""
        return {
            "run_id": run["run_id"],
            "menu_number": run["menu_number"],
            "description": run["description"],
            "status": run["status"],
            "started_at": run["started_at"],
            "completed_at": run["completed_at"],
            "progress_pct": run["progress_pct"],
            "error_message": run["error_message"],
            "completion_message": run.get("completion_message"),
            "output_files": list(run.get("output_files", [])),
            # The read boundary copies each bounded deque into a list, so JSON encoding still works.
            "log_messages": list(run.get("log_messages", [])),
            "debug_messages": list(run.get("debug_messages", [])),
            # Report the loss, so the operator knows the cap truncated the run log.
            "dropped_log_count": run.get("dropped_log_count", 0),
            # Report the same loss for the output file names the cap discarded.
            "dropped_output_file_count": run.get("dropped_output_file_count", 0),
        }

    def _run_to_summary(self, run: dict) -> dict:
        """Convert run to abbreviated summary for active list."""
        return {
            "run_id": run["run_id"],
            "menu_number": run["menu_number"],
            "description": run["description"],
            "status": run["status"],
            "progress_pct": run["progress_pct"],
            # Show the loss in the active list, so a long run reports the truncation early.
            "dropped_log_count": run.get("dropped_log_count", 0),
            # Show the same loss for the output file names the cap discarded.
            "dropped_output_file_count": run.get("dropped_output_file_count", 0),
        }

    def _parse_menu_number(self, key: str) -> int | None:
        """Parse string menu key to integer, return None if non-numeric."""
        try:
            return int(key)
        except (ValueError, TypeError):
            return None

    def _get_category(self, num: int) -> str:
        """Map a menu number to its category name."""
        override = CATEGORY_OVERRIDES.get(num)
        if override is not None:
            return override  # The range gives the wrong name for this row. Issue #3153.
        for low, high, name in CATEGORY_RANGES:
            if low <= num <= high:
                return name
        return "Other"


class _RunLogHandler(logging.Handler):
    """Logging handler that captures log lines to an OperationRun.

    Routes log output into two tiers based on source and content:
    - Main log: user-facing progress messages (fetched N records, wrote file)
    - Debug log: library internals, rate limiter, API plumbing

    Also auto-detects output file paths from log messages so the
    Output Files section populates without changes to legacy menu code.
    """

    # Logger name prefixes whose output always goes to debug panel
    _DEBUG_LOGGERS = frozenset(
        (
            "urllib3",
            "requests",
            "werkzeug",
            "flask",
            "mistapi",
        )
    )

    # Message prefixes that indicate internal plumbing (even at INFO)
    _INTERNAL_PREFIXES = (
        "apiresponse:",
        "apirequest:",
        "apitoken:",
        "Rate limiting:",
        "Hour boundary crossed",
        "Adaptive delay",
        "PID controller",
        "request headers:",
        "_gen_query:",
        "_check_next",
        "_url:",
        "Processing ",
        "Connection-aware threading:",
        "CPU-aware threading:",
        "Connection pool protection:",
        "API Optimization:",
        "Fast mode:",
        "Retry ",
        "FAST RETRY",
    )

    # Regex to extract output filenames from log messages.
    # Issue #3089: the phrase list and the extension list were both too short,
    # so a Markdown report announced as "Mermaid report: data/X.md" never
    # matched. The second branch now accepts any data-directory path, whatever
    # sentence carries it.
    _OUTPUT_FILE_RE = re.compile(
        r"(?:(?:wrote \d+ rows to|written to|wrote results to|saved to|report:|exported to)"
        r"\s+(?:data[/\\])?|data[/\\])"
        r"(\S+\.(?:csv|db|json|sqlite|md|html|htm|txt|xlsx|xls|pcap|yaml|yml|xml|png|pdf))",
        re.IGNORECASE,
    )

    def __init__(self, run: dict, event_bus):
        """Initialize with the run record and event bus."""
        super().__init__()
        self._run = run
        self._event_bus = event_bus

    def emit(self, record: logging.LogRecord) -> None:
        """Capture a log record and route to appropriate SSE channel."""
        message = self.format(record)
        level = record.levelname.lower()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created))
        is_main = self._is_user_facing(record, message)
        event_type = "log" if is_main else "debug_log"
        storage = "log_messages" if is_main else "debug_messages"
        self._store_message(storage, message, level)  # The bounded store counts an entry the cap drops.
        if is_main:
            self._check_output_file(message)
        if self._event_bus:
            self._event_bus.publish(
                event_type,
                {
                    "run_id": self._run["run_id"],
                    "message": message,
                    "level": level,
                    "timestamp": timestamp,
                },
            )

    def _store_message(self, storage: str, message: str, level: str) -> None:
        """Append one entry to a bounded run log and count a discarded entry.

        This method writes no log record. The handler sits on the root logger,
        so a log call here would capture its own output. The logging framework
        holds the handler lock during a call, so the counter needs no lock.
        """
        target = self._run[storage]  # The store is the bounded deque the run record created.
        maxlen = getattr(target, "maxlen", None)  # A plain list reports no cap, so the count stays at zero.
        if maxlen is not None and len(target) >= maxlen:
            # Count the entry the deque is about to discard, so the response can report the loss.
            self._run["dropped_log_count"] = self._run.get("dropped_log_count", 0) + 1
        target.append({"message": message, "level": level})  # The deque drops the oldest entry when it is full.

    def _is_user_facing(self, record: logging.LogRecord, message: str) -> bool:
        """Decide if a message belongs in the main execution log."""
        if record.levelno >= logging.WARNING:
            return True
        if record.levelno < logging.INFO:
            return False
        logger_root = record.name.split(".")[0]
        if logger_root in self._DEBUG_LOGGERS:
            return False
        if any(message.startswith(prefix) for prefix in self._INTERNAL_PREFIXES):
            return False
        if self._looks_like_http_log(message):
            return False
        return True

    @staticmethod
    def _looks_like_http_log(message: str) -> bool:
        """Detect urllib3-style HTTP request log lines."""
        return message.startswith("http") and "HTTP/" in message

    def _check_output_file(self, message: str) -> None:
        """Extract output filenames from log messages."""
        match = self._OUTPUT_FILE_RE.search(message)
        if match:
            filename = match.group(1)  # The first group holds the file name without the data prefix.
            if filename not in self._run["output_files"]:
                self._store_output_file(filename)  # The bounded store counts a name the cap drops.

    def _store_output_file(self, filename: str) -> None:
        """Append one output file name and count a discarded name.

        This method writes no log record, for the reason `_store_message`
        states. The logging framework holds the handler lock during a call,
        so the counter needs no lock.
        """
        target = self._run["output_files"]  # The store is the bounded deque the run record created.
        maxlen = getattr(target, "maxlen", None)  # A plain list reports no cap, so the count stays at zero.
        if maxlen is not None and len(target) >= maxlen:
            # Count the name the deque is about to discard, so the response can report the loss.
            self._run["dropped_output_file_count"] = self._run.get("dropped_output_file_count", 0) + 1
        target.append(filename)  # The deque drops the oldest name, so the newest output stays visible.

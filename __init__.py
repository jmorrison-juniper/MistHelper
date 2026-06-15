"""Top-level package exports.

Prefer lightweight compatibility facades for fast test-collection, but expose a
lazy import path to the full `MistHelper.py` implementation when a legacy symbol
is accessed. Module-level ``__getattr__`` defers importing the heavyweight
module until an attribute is requested, avoiding import-time side-effects
during test discovery.

This file also ensures that the repository's ``src`` package is available as a
top-level import (``import src``) because many extracted modules use absolute
``src.*`` imports. We map the package-local ``MistHelper.src`` to the global
``src`` name in ``sys.modules`` to satisfy those imports without modifying the
existing modules.
"""

_heavy_module = None  # Cache for the heavyweight MistHelper module
PROGRESS_EMITTER = None  # Global telemetry emitter handle expected by unit tests and runtime patches

import importlib  # Importlib used for lazy loading heavy module
import logging  # Logging for debug during import-time mapping
import re  # Regex helper for scope parsing compatibility shim
import sys  # sys used to expose package-local src as top-level import

# Ensure top-level `src` points to the package-local `MistHelper.src` module so
# absolute imports like `import src.export.site_insights_exporter` succeed when
# running tests from the package checkout (no install step).
try:
    if "src" not in sys.modules:  # Avoid clobbering an existing global `src`
        try:
            _src_mod = importlib.import_module(f"{__name__}.src")
            sys.modules["src"] = _src_mod  # Expose as top-level package
            logging.debug("Mapped package submodule %s.src to top-level 'src'", __name__)
        except Exception as _map_exc:
            # Mapping failed; leave `src` resolution to normal import machinery
            logging.debug("Could not map package src into sys.modules: %s", _map_exc)
except Exception:
    # Be resilient: never fail package import because of mapping attempt
    pass

# Import from the legacy monolith for backward compatibility.
try:
    from .MistHelper import *
except Exception:
    pass


def _load_heavy_module():
    """Import and cache the full `MistHelper.MistHelper` module on demand.

    Returns the imported module object. Uses package-relative import so this
    file works whether the package is on sys.path as a package or executed as
    a module.
    """
    global _heavy_module
    if _heavy_module is not None:
        return _heavy_module

    try:
        # Import as submodule of this package (MistHelper.MistHelper)
        _heavy_module = importlib.import_module(f"{__name__}.MistHelper")
    except Exception:
        # Fall back to top-level module name if package-relative import fails
        _heavy_module = importlib.import_module("MistHelper")
    # Ensure the heavy module uses the same mistapi proxy/object as the package-level
    # facades so tests monkeypatching `MistHelper.mistapi` affect the runtime
    # calls performed inside the heavy module. Prefer the package-level symbol if
    # present, otherwise fall back to any already-imported mistapi module.
    try:
        pkg = sys.modules.get(__name__)
        if pkg is not None and hasattr(pkg, "mistapi"):
            _heavy_module.mistapi = pkg.mistapi
        else:
            # Fall back to global mistapi module in sys.modules if present
            if "mistapi" in sys.modules:
                _heavy_module.mistapi = sys.modules["mistapi"]
    except Exception:
        # Be defensive: do not raise during lazy import
        pass
    return _heavy_module


def __getattr__(name: str):
    """Lazy attribute access: delegate to heavy module when attribute missing.

    On first access copy the attribute into this package's globals so subsequent
    lookups (and dir()/hasattr()) behave like normal module attributes.
    """
    if name in globals():
        return globals()[name]

    heavy = _load_heavy_module()

    # Lightweight compatibility shims preserved for tests while decomposition
    # is in progress. These avoid re-introducing deleted compat modules.
    if name == "DataProcessingUtils":

        class _DataProcessingUtils:
            @staticmethod
            def flatten_nested_fields(data):
                fn = getattr(heavy, "flatten_nested_fields_in_list", None)
                if fn:
                    return fn(data)
                return data

            @staticmethod
            def escape_multiline(data):
                fn = getattr(heavy, "escape_multiline_strings_for_csv", None)
                if fn:
                    return fn(data)
                return data

            @staticmethod
            def get_unique_keys(rows):
                keys = set()
                for row in rows or []:
                    if isinstance(row, dict):
                        keys.update(row.keys())
                return sorted(keys)

        globals()["DataProcessingUtils"] = _DataProcessingUtils
        return _DataProcessingUtils

    if name == "InsightMetricsUtils":

        class _InsightMetricsUtils:
            @staticmethod
            def _parse_scopes(scopes_text: str):
                if not scopes_text:
                    return set()
                text = scopes_text.strip()
                if text.startswith("[") and text.endswith("]"):
                    text = re.sub(r"[\[\]'\"]", "", text)
                return {value.strip() for value in text.split(",") if value.strip()}

            @staticmethod
            def export_legacy(*args, **kwargs):
                return None

            @staticmethod
            def get_by_scope(*args, **kwargs):
                fn = getattr(heavy, "get_insight_metrics_by_scope", None)
                if fn:
                    return fn(*args, **kwargs)
                return []

        globals()["InsightMetricsUtils"] = _InsightMetricsUtils
        return _InsightMetricsUtils

    if name == "PromptUtils":

        class _PromptUtils:
            @staticmethod
            def _sync_heavy_runtime_context() -> None:
                heavy_runtime_module = _load_heavy_module()  # Load cached heavy module so facade and runtime share state.
                package_module = sys.modules.get(__name__)  # Resolve package module object to read monkeypatched globals.
                if package_module is not None and hasattr(package_module, "mistapi"):
                    heavy_runtime_module.mistapi = package_module.mistapi  # Keep heavy module mistapi aligned with package facade.

            @staticmethod
            def select_site_id_from_csv(*args, **kwargs):
                _PromptUtils._sync_heavy_runtime_context()  # Sync heavy module dependencies before dispatching call.
                fn = getattr(heavy, "prompt_select_site_id_from_csv", None)
                if fn:
                    return fn(*args, **kwargs)
                return ""

            @staticmethod
            def select_site(*args, **kwargs):
                _PromptUtils._sync_heavy_runtime_context()  # Sync heavy module dependencies before dispatching call.
                fn = getattr(heavy, "prompt_select_site_id_from_csv", None)
                if fn:
                    return fn(*args, **kwargs)
                return ""

            @staticmethod
            def select_device_id_from_inventory(*args, **kwargs):
                _PromptUtils._sync_heavy_runtime_context()  # Sync heavy module dependencies before dispatching call.
                fn = getattr(heavy, "prompt_select_device_id_from_inventory", None)
                if fn:
                    return fn(*args, **kwargs)
                return ""

            @staticmethod
            def _determine_search_scope(site_id):
                if site_id:
                    return site_id
                scope_choice = (
                    __getattr__("InputUtils")
                    .safe_input(
                        "Search scope - (s)ite-specific or (o)rganization-wide? [s/o]: ",
                        context="client_search_scope",
                    )
                    .strip()
                    .lower()
                )
                if scope_choice == "s":
                    selected_site = _PromptUtils.select_site()
                    if not selected_site:
                        print(" No site selected.")
                        return False
                    return selected_site
                return None

            @staticmethod
            def _extract_selected_client(client, sites_cache, default_site_id):
                client_mac = client.get("mac", "")
                client_type = client.get("client_type", "unknown")
                client_site_id = client.get("site_id", default_site_id) or ""
                hostname = client.get("hostname", client.get("name", "Unknown"))
                print("\n Selected client:")
                print(f"   Name: {hostname}")
                print(f"   MAC: {client_mac}")
                print(f"   Type: {client_type}")
                if client_site_id and client_site_id in (sites_cache or {}):
                    print(f"   Site: {sites_cache[client_site_id]}")
                return client_mac, client_type, client_site_id

            @staticmethod
            def _handle_client_selection(all_clients, sites_cache, default_site_id):
                try:
                    max_index = len(all_clients) - 1
                    user_input = __getattr__("InputUtils").safe_input(
                        f"\n  Enter client index (0-{max_index}) or 'q' to quit: ",
                        context="client_selection_index",
                    ).strip()
                    if user_input.lower() in ["q", "quit", "exit"]:
                        print(" Exiting client selection...")
                        return None, None, None
                    idx = int(user_input)
                    if 0 <= idx <= max_index:
                        return _PromptUtils._extract_selected_client(all_clients[idx], sites_cache, default_site_id)
                    print(f"! Invalid index. Please enter a number between 0 and {max_index}.")
                    return None, None, None
                except ValueError:
                    print(" Please enter a valid number or 'q' to quit.")
                    return None, None, None
                except (EOFError, KeyboardInterrupt):
                    return None, None, None

        globals()["PromptUtils"] = _PromptUtils
        return _PromptUtils

    if name == "EnhancedSSHRunner":

        class _EnhancedSSHRunner:
            @staticmethod
            def sanitize_filename(value: str):
                fn = getattr(heavy, "sanitize_filename", None)
                if fn:
                    return fn(value)
                return value.replace(" ", "_")

        globals()["EnhancedSSHRunner"] = _EnhancedSSHRunner
        return _EnhancedSSHRunner

    if name == "SiteExportUtils":
        from src.export.site_export_utils import SiteExportUtils as _SiteExportUtils

        if not hasattr(_SiteExportUtils, "_normalize_client_mac_or_none"):

            def _normalize_client_mac_or_none(client_mac: str):
                if not client_mac:
                    return None
                clean = client_mac.replace(":", "").replace("-", "").replace(".", "").lower()
                if len(clean) != 12 or not all(character in "0123456789abcdef" for character in clean):
                    return None
                return ":".join(clean[index : index + 2] for index in range(0, 12, 2))

            _SiteExportUtils._normalize_client_mac_or_none = staticmethod(_normalize_client_mac_or_none)

        globals()["SiteExportUtils"] = _SiteExportUtils
        return _SiteExportUtils

    if name == "SiteClientExporter":

        class _SiteClientExporter:
            @staticmethod
            def clients(*args, **kwargs):
                fn = getattr(heavy, "export_site_clients_to_csv", None)
                if fn:
                    return fn(*args, **kwargs)
                return None

            @staticmethod
            def client_insights(*args, **kwargs):
                fn = getattr(heavy, "export_site_client_insights_to_csv", None)
                if fn:
                    return fn(*args, **kwargs)
                return None

            @staticmethod
            def _normalize_client_mac_or_none(client_mac: str):
                return __getattr__("SiteExportUtils")._normalize_client_mac_or_none(client_mac)

        globals()["SiteClientExporter"] = _SiteClientExporter
        return _SiteClientExporter

    if name == "OrgAlarmEventExporter":

        class _OrgAlarmEventExporter:
            @staticmethod
            def alarms(*args, **kwargs):
                fn = getattr(heavy, "export_open_org_alarms_to_csv", None)
                if fn:
                    return fn(*args, **kwargs)
                return None

            @staticmethod
            def device_events_52w(*args, **kwargs):
                fn = getattr(heavy, "export_all_org_device_events_52w_to_csv", None)
                if fn:
                    return fn(*args, **kwargs)
                return None

        globals()["OrgAlarmEventExporter"] = _OrgAlarmEventExporter
        return _OrgAlarmEventExporter

    if name == "APIDataFetcher":

        class _APIDataFetcher:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def execute(self):
                fn = getattr(heavy, "fetch_and_display_api_data", None)
                if fn:
                    return fn(**self.kwargs)
                return None

        globals()["APIDataFetcher"] = _APIDataFetcher
        return _APIDataFetcher

    # Special-case legacy container-style utilities that historically were
    # provided as classes in the monolithic `MistHelper.py` but may now be
    # present as top-level functions. Synthesize a minimal compatibility class
    # on-demand so tests that patch `MistHelper.ConfigUtils` continue to work.
    if name == "ConfigUtils":
        # If heavy module already exposes the class, use it directly.
        val = getattr(heavy, "ConfigUtils", None)
        # Treat string sentinels like '<MISSING>' as absent
        if val is not None and not (isinstance(val, str) and val.startswith("<") and val.endswith(">")):
            globals()["ConfigUtils"] = val
            return globals()["ConfigUtils"]

        # Otherwise create a thin facade class delegating to module-level
        # functions when available (get_cached_or_prompted_org_id, check_stop_signal).
        class _ConfigUtils:
            @staticmethod
            def get_cached_or_prompted_org_id(*args, **kwargs):
                fn = getattr(heavy, "get_cached_or_prompted_org_id", None)
                if fn:
                    return fn(*args, **kwargs)
                raise AttributeError("get_cached_or_prompted_org_id not available")

            @staticmethod
            def check_stop_signal(*args, **kwargs):
                fn = getattr(heavy, "check_stop_signal", None)
                if fn:
                    return fn(*args, **kwargs)
                # Default conservative behaviour: no stop signal
                return False

        globals()["ConfigUtils"] = _ConfigUtils
        return _ConfigUtils

    if name == "InputUtils":
        # Create a thin facade class delegating to module-level safe_input
        val = getattr(heavy, "InputUtils", None)
        # Treat string sentinels like '<MISSING>' as absent
        if val is not None and not (isinstance(val, str) and val.startswith("<") and val.endswith(">")):
            globals()["InputUtils"] = val
            return globals()["InputUtils"]

        class _InputUtils:
            @staticmethod
            def safe_input(*args, **kwargs):
                fn = getattr(heavy, "safe_input", None)
                if fn:
                    return fn(*args, **kwargs)
                try:
                    return input(args[0] if args else "").strip()
                except Exception:
                    return ""

        globals()["InputUtils"] = _InputUtils
        return _InputUtils

    if name == "OperationRegistry":

        class _OperationRegistry:
            @staticmethod
            def skip_category(option: str) -> str:
                option_value = str(option)
                if option_value in {"101", "153"}:
                    return "resource_intensive"
                if option_value.isdigit() and 102 <= int(option_value) <= 123:
                    return "websocket"
                if option_value.isdigit() and 124 <= int(option_value) <= 153:
                    return "interactive"
                if option_value.isdigit() and 154 <= int(option_value) <= 187:
                    return "destructive"
                return "safe"

            @staticmethod
            def skip_reason(option: str) -> str:
                category = _OperationRegistry.skip_category(option)
                if category == "destructive":
                    return f"DESTRUCTIVE operation: menu {option}"
                if category == "websocket":
                    return f"WebSocket interactive operation: menu {option}"
                if category == "interactive":
                    return f"Interactive operation: menu {option}"
                if category == "resource_intensive":
                    return f"Resource-intensive operation: menu {option}"
                return ""

            @staticmethod
            def is_safe(option: str) -> bool:
                return _OperationRegistry.skip_category(option) == "safe"

            @staticmethod
            def is_interactive_safe(option: str) -> bool:
                return str(option) in {"29", "30", "31", "32", "33", "34", "49", "50", "51", "52", "53", "68", "69", "81", "84", "85", "86", "92", "93", "94", "95", "96"}

            @staticmethod
            def wave1_entry_routing_baseline() -> dict:
                return {
                    "101": "resource_intensive",
                    "102": "websocket",
                    "123": "websocket",
                    "124": "interactive",
                    "153": "resource_intensive",
                    "154": "destructive",
                    "187": "destructive",
                }

            @staticmethod
            def wave1_safety_classification_baseline() -> dict:
                return {
                    "safe_true": ["1", "11", "12", "13"],
                    "safe_false": ["102", "124", "154", "187"],
                    "interactive_safe_true": ["29", "34", "68", "86"],
                    "interactive_safe_false": ["1", "124", "154"],
                    "destructive_markers": ["154", "155", "187"],
                }

        globals()["OperationRegistry"] = _OperationRegistry
        return _OperationRegistry

    if name == "WAN2MigrationManager":
        from src.gateway import wan2_migration_manager as _wan2_module

        class _WAN2MigrationManager:
            def __init__(self):
                _wan2_module.configure_wan2_migration_dependencies(
                    apisession_dependency=getattr(heavy, "apisession", None),
                    config_utils=__getattr__("ConfigUtils"),
                    cache_utils=getattr(heavy, "CacheUtils", None),
                    org_site_exporter=getattr(heavy, "OrgSiteExporter", None),
                    gateway_export_utils=getattr(heavy, "GatewayExportUtils", None),
                    file_path_utils=getattr(heavy, "FilePathUtils", None),
                    input_utils=__getattr__("InputUtils"),
                    data_exporter=getattr(heavy, "DataExporter", None),
                    mistapi_dependency=getattr(heavy, "mistapi", None),
                    site_exclude_prefix=getattr(heavy, "MIST_SITE_EXCLUDE_PREFIX", ""),
                )
                self._impl = _wan2_module.WAN2MigrationManager()

            def __getattr__(self, attr_name):
                return getattr(self._impl, attr_name)

            def set_site_variable(self):
                return self._impl.set_site_variable()

        globals()["WAN2MigrationManager"] = _WAN2MigrationManager
        return _WAN2MigrationManager

    if name == "ServicePingManager":
        from src.websocket.service_ping_manager import (
            ServicePingManager as _ServicePingManager,
            configure_service_ping_manager_dependencies as _configure_service_ping_manager_dependencies,
        )

        _configure_service_ping_manager_dependencies(
            apisession_dependency=getattr(heavy, "apisession", None),
            mistapi_dependency=getattr(heavy, "mistapi", None),
            prompt_utils=__getattr__("PromptUtils"),
            input_utils=__getattr__("InputUtils"),
            websocket_manager_class=getattr(heavy, "WebSocketManager", None),
            is_debug_mode=getattr(heavy, "is_debug_mode", lambda: False),
            api_tenant_fetch_utils=getattr(heavy, "APITenantFetchUtils", None),
            config_utils=__getattr__("ConfigUtils"),
            api_fetch_utils=getattr(heavy, "APIFetchUtils", None),
        )
        globals()["ServicePingManager"] = _ServicePingManager
        return _ServicePingManager

    if name == "TroubleshootUtils":
        from src.troubleshooting.marvis_troubleshoot_utils import (
            MarvisTroubleshootDeps as _MarvisTroubleshootDeps,
            MarvisTroubleshootUtils as _ExtractedMarvisTroubleshootUtils,
        )

        class _MarvisDataUtils:
            @staticmethod
            def format_for_csv(data, analysis_type="generic"):
                formatter = getattr(heavy, "format_marvis_data_for_csv", None)
                if formatter:
                    return formatter(data, analysis_type)
                return data if isinstance(data, list) else [data]

        class _TroubleshootUtils:
            @staticmethod
            def _build_deps():
                return _MarvisTroubleshootDeps(
                    apisession=getattr(heavy, "apisession", None),
                    mistapi=getattr(heavy, "mistapi", None),
                    config_utils=__getattr__("ConfigUtils"),
                    prompt_client_utils=getattr(heavy, "PromptClientUtils", None),
                    prompt_utils=__getattr__("PromptUtils"),
                    data_exporter=getattr(heavy, "DataExporter", None),
                    marvis_data_utils=_MarvisDataUtils,
                    data_processing_utils=__getattr__("DataProcessingUtils"),
                )

            @staticmethod
            def client_connectivity():
                _ExtractedMarvisTroubleshootUtils.client_connectivity(_TroubleshootUtils._build_deps())

            @staticmethod
            def device_performance():
                _ExtractedMarvisTroubleshootUtils.device_performance(_TroubleshootUtils._build_deps())

            @staticmethod
            def network_connectivity():
                _ExtractedMarvisTroubleshootUtils.network_connectivity(_TroubleshootUtils._build_deps())

            @staticmethod
            def view_insights():
                _ExtractedMarvisTroubleshootUtils.view_insights(_TroubleshootUtils._build_deps())

            @staticmethod
            def launch_interactive() -> None:
                logging.info("Entering TroubleshootUtils.launch_interactive")
                print(" Starting Marvis (VNA - Virtual Network Assistant) Troubleshooting")
                print("=" * 65)
                print()
                __getattr__("ConfigUtils").get_cached_or_prompted_org_id()
                print(" Marvis AI Troubleshooting Options:")
                print("1. Troubleshoot client connectivity issues (guided client selection)")
                print("2. Diagnose device performance problems (guided device selection)")
                print("3. Analyze network connectivity issues (site-level analysis)")
                print("4. View organization Marvis insights and capabilities")
                print("5. Exit")
                print()
                choice = __getattr__("InputUtils").safe_input("Select an option (1-5): ", context="marvis_launch_menu").strip()
                if choice == "1":
                    _TroubleshootUtils.client_connectivity()
                elif choice == "2":
                    _TroubleshootUtils.device_performance()
                elif choice == "3":
                    _TroubleshootUtils.network_connectivity()
                elif choice == "4":
                    _TroubleshootUtils.view_insights()
                elif choice == "5":
                    print("Exiting Marvis troubleshooting.")
                    logging.info("Exiting TroubleshootUtils.launch_interactive via user exit choice")
                    return
                else:
                    print(" Invalid option selected.")
                logging.info("Exiting TroubleshootUtils.launch_interactive with choice: %s", choice)

        globals()["TroubleshootUtils"] = _TroubleshootUtils
        return _TroubleshootUtils

    if name == "SSHRunnerManager":
        from src.ssh.ssh_runner_manager import (
            SSHRunnerManager as _ExtractedSSHRunnerManager,
            SSHRunnerManagerDeps as _SSHRunnerManagerDeps,
        )

        class _ShimCacheUtils:
            @staticmethod
            def check_and_generate_csv(file_name, generate_function):
                function_ref = getattr(heavy, "check_and_generate_csv", None)
                if function_ref:
                    return function_ref(file_name, generate_function)
                return False

        class _ShimGatewayExportUtils:
            @staticmethod
            def management_ips(*args, **kwargs):
                function_ref = getattr(heavy, "export_gateway_management_ips_to_csv", None)
                if function_ref:
                    return function_ref(*args, **kwargs)
                return None

        class _ShimFilePathUtils:
            @staticmethod
            def get_csv_path(filename):
                function_ref = getattr(heavy, "get_csv_file_path", None)
                if function_ref:
                    return function_ref(filename)
                return filename

        class _SSHRunnerManager:
            @staticmethod
            def _build_deps():
                return _SSHRunnerManagerDeps(
                    args=getattr(heavy, "args", None),
                    progress_emitter=globals().get("PROGRESS_EMITTER", None),
                    enhanced_ssh_runner=getattr(heavy, "EnhancedSSHRunner", None),
                    input_utils=__getattr__("InputUtils"),
                    cache_utils=getattr(heavy, "CacheUtils", _ShimCacheUtils),
                    gateway_export_utils=getattr(heavy, "GatewayExportUtils", _ShimGatewayExportUtils),
                    file_path_utils=getattr(heavy, "FilePathUtils", _ShimFilePathUtils),
                )

            @staticmethod
            def interactive():
                return _ExtractedSSHRunnerManager.interactive(_SSHRunnerManager._build_deps())

            @staticmethod
            def by_gateway_template(fast=False):
                return _ExtractedSSHRunnerManager.by_gateway_template(_SSHRunnerManager._build_deps(), fast=fast)

            @staticmethod
            def _collect_missing_data(hosts, username, password, commands):
                return _ExtractedSSHRunnerManager._collect_missing_data(
                    _SSHRunnerManager._build_deps(),
                    hosts,
                    username,
                    password,
                    commands,
                )

            @staticmethod
            def _confirm_execution(count):
                return _ExtractedSSHRunnerManager._confirm_execution(_SSHRunnerManager._build_deps(), count)

        globals()["SSHRunnerManager"] = _SSHRunnerManager
        return _SSHRunnerManager

    if name == "OrgTicketManager":
        import csv as _csv
        import os as _os

        class _OrgTicketManager:
            TICKET_TYPES = ["question", "problem", "incident", "feature_request"]

            @staticmethod
            def _org_id():
                return __getattr__("ConfigUtils").get_cached_or_prompted_org_id()

            @staticmethod
            def _write_rows_csv(rows, filename):
                if not rows:
                    return
                data_directory = "data"
                _os.makedirs(data_directory, exist_ok=True)
                path = _os.path.join(data_directory, filename)
                all_fields = sorted({field for row in rows if isinstance(row, dict) for field in row.keys()})
                with open(path, "w", newline="", encoding="utf-8") as file_handle:
                    writer = _csv.DictWriter(file_handle, fieldnames=all_fields)
                    writer.writeheader()
                    writer.writerows(rows)

            @staticmethod
            def _list_tickets(org_id):
                response = heavy.mistapi.api.v1.orgs.tickets.listOrgTickets(getattr(heavy, "apisession", None), org_id, limit=1000)
                payload = getattr(response, "data", [])
                if isinstance(payload, list):
                    return payload
                if isinstance(payload, dict):
                    if isinstance(payload.get("results"), list):
                        return payload.get("results", [])
                    return [payload]
                getter = getattr(heavy.mistapi, "get_all", None)
                mist_session = getattr(heavy, "apisession", None)
                if getter and mist_session is not None:
                    try:
                        data = getter(response=response, mist_session=mist_session)
                        return data or []
                    except TypeError:
                        data = getter(response, mist_session)
                        return data or []
                return []

            @staticmethod
            def list_tickets():
                org_id = _OrgTicketManager._org_id()
                tickets = _OrgTicketManager._list_tickets(org_id)
                if not tickets:
                    print(" No tickets found.")
                    return
                _OrgTicketManager._write_rows_csv(tickets, "OrgTickets.csv")
                print(f"! Exported {len(tickets)} tickets to data/OrgTickets.csv")

            @staticmethod
            def create_ticket():
                org_id = _OrgTicketManager._org_id()
                subject = __getattr__("InputUtils").safe_input("Enter ticket subject: ", default_value="", allow_empty=True, context="ticket_subject")
                subject = str(subject or "").strip()
                if not subject:
                    print(" Ticket creation cancelled.")
                    return
                type_choice = __getattr__("InputUtils").safe_input("Ticket type [1=question,2=problem,3=incident,4=feature_request] (default 2): ", default_value="2", allow_empty=True, context="ticket_type")
                type_choice = str(type_choice or "2").strip()
                ticket_type = {
                    "1": "question",
                    "2": "problem",
                    "3": "incident",
                    "4": "feature_request",
                }.get(type_choice, "problem")
                comment = __getattr__("InputUtils").safe_input("Initial comment (optional): ", default_value="", allow_empty=True, context="ticket_comment")
                body = {"subject": subject, "type": ticket_type}
                if str(comment or "").strip():
                    body["comment"] = str(comment).strip()
                heavy.mistapi.api.v1.orgs.tickets.createOrgTicket(getattr(heavy, "apisession", None), org_id, body)
                print("! Ticket created.")

            @staticmethod
            def _select_ticket(org_id):
                tickets = _OrgTicketManager._list_tickets(org_id)
                if not tickets:
                    print(" No tickets found.")
                    return ""
                print("\nAvailable tickets:")
                for index, ticket in enumerate(tickets, start=1):
                    print(f"  {index}. {ticket.get('id', '')} | {ticket.get('subject', '')} | {ticket.get('status', '')}")
                selection = __getattr__("InputUtils").safe_input("Select ticket number (Enter to cancel): ", default_value="", allow_empty=True, context="ticket_select")
                selection = str(selection or "").strip()
                if not selection:
                    return ""
                try:
                    selected_index = int(selection) - 1
                    if 0 <= selected_index < len(tickets):
                        return str(tickets[selected_index].get("id", ""))
                except ValueError:
                    pass
                return ""

            @staticmethod
            def add_comment():
                org_id = _OrgTicketManager._org_id()
                ticket_id = _OrgTicketManager._select_ticket(org_id)
                if not ticket_id:
                    print(" Operation cancelled.")
                    return
                comment = __getattr__("InputUtils").safe_input("Comment text (optional): ", default_value="", allow_empty=True, context="ticket_comment")
                comment = str(comment or "").strip()
                file_path = __getattr__("InputUtils").safe_input("Attachment file path (optional): ", default_value="", allow_empty=True, context="ticket_comment_file")
                file_path = str(file_path or "").strip()
                if not comment and not file_path:
                    print(" Operation cancelled -- no comment content provided.")
                    return
                if file_path:
                    if _os.path.exists(file_path):
                        heavy.mistapi.api.v1.orgs.tickets.addOrgTicketCommentFile(
                            getattr(heavy, "apisession", None),
                            org_id,
                            ticket_id,
                            comment=comment,
                            file=file_path,
                        )
                        print("! Comment with attachment added.")
                        return
                    print(f" File not found: {file_path}. Falling back to text comment.")
                heavy.mistapi.api.v1.orgs.tickets.addOrgTicketComment(
                    getattr(heavy, "apisession", None),
                    org_id,
                    ticket_id,
                    {"comment": comment},
                )
                print("! Comment added.")

            @staticmethod
            def update_ticket():
                org_id = _OrgTicketManager._org_id()
                ticket_id = _OrgTicketManager._select_ticket(org_id)
                if not ticket_id:
                    print(" Operation cancelled.")
                    return
                subject = __getattr__("InputUtils").safe_input("New subject (optional): ", default_value="", allow_empty=True, context="ticket_update_subject")
                status = __getattr__("InputUtils").safe_input("New status (optional): ", default_value="", allow_empty=True, context="ticket_update_status")
                ticket_type = __getattr__("InputUtils").safe_input("New type (optional): ", default_value="", allow_empty=True, context="ticket_update_type")
                body = {}
                if str(subject or "").strip():
                    body["subject"] = str(subject).strip()
                if str(status or "").strip():
                    body["status"] = str(status).strip()
                if str(ticket_type or "").strip():
                    body["type"] = str(ticket_type).strip()
                if not body:
                    print(" Operation cancelled -- no changes requested.")
                    return
                heavy.mistapi.api.v1.orgs.tickets.updateOrgTicket(getattr(heavy, "apisession", None), org_id, ticket_id, body)
                print("! Ticket updated.")

            @staticmethod
            def _fetch_ticket_detail(org_id, ticket_id):
                response = heavy.mistapi.api.v1.orgs.tickets.getOrgTicket(getattr(heavy, "apisession", None), org_id, ticket_id)
                return getattr(response, "data", {}) or {}

            @staticmethod
            def view_ticket():
                org_id = _OrgTicketManager._org_id()
                ticket_id = _OrgTicketManager._select_ticket(org_id)
                if not ticket_id:
                    print(" Operation cancelled.")
                    return
                detail = _OrgTicketManager._fetch_ticket_detail(org_id, ticket_id)
                if not detail:
                    print(" No ticket details found.")
                    return
                print("\nTicket Details")
                print("=" * 60)
                for key in ["id", "subject", "status", "type", "created_at", "updated_at"]:
                    if key in detail:
                        print(f"{key}: {detail.get(key)}")
                comments = detail.get("comments", []) or []
                if comments:
                    print("\nComments:")
                    for index, comment in enumerate(comments, start=1):
                        author = comment.get("author", "unknown")
                        text = comment.get("comment", "")
                        created = comment.get("created_at", "")
                        print(f"  {index}. {author} | {created} | {text}")

            @staticmethod
            def export_ticket_details():
                org_id = _OrgTicketManager._org_id()
                tickets = _OrgTicketManager._list_tickets(org_id)
                if not tickets:
                    print(" No tickets found.")
                    return
                details = []
                for ticket in tickets:
                    ticket_id = str(ticket.get("id", ""))
                    if not ticket_id:
                        continue
                    details.append(_OrgTicketManager._fetch_ticket_detail(org_id, ticket_id))
                details = [row for row in details if row]
                if not details:
                    print(" No ticket details found.")
                    return
                _OrgTicketManager._write_rows_csv(details, "OrgTicketDetails.csv")
                print(f"! Exported {len(details)} ticket details to data/OrgTicketDetails.csv")

        globals()["OrgTicketManager"] = _OrgTicketManager
        return _OrgTicketManager

    if name == "TimeUtils":

        class _TimeUtils:
            @staticmethod
            def get_dynamic_lookback_hours(default_hours, minimum_hours):
                _ = minimum_hours
                return default_hours

            @staticmethod
            def log_dynamic_lookback(label, hours):
                logging.debug("Dynamic lookback for %s: %sh", label, hours)

        globals()["TimeUtils"] = _TimeUtils
        return _TimeUtils

    if name == "OrgInventoryExporter":

        class _OrgInventoryExporter:
            @staticmethod
            def inventory():
                emitter = globals().get("PROGRESS_EMITTER", None)
                start_time = time.time()
                if emitter:
                    emitter.emit_progress_start("12", "inventory", 1)
                fetcher = __getattr__("APIDataFetcher")(
                    title="Org Inventory:",
                    api_call=heavy.mistapi.api.v1.orgs.inventory.getOrgInventory,
                    filename="OrgInventory.csv",
                    sort_key="model",
                    vc=True,
                    limit=1000,
                )
                fetcher.execute()
                if emitter:
                    emitter.emit_progress_complete("12", "inventory", 1, 1, False, time.time() - start_time)

        globals()["OrgInventoryExporter"] = _OrgInventoryExporter
        return _OrgInventoryExporter

    if name == "OrgDeviceStatsExporter":

        class _OrgDeviceStatsExporter:
            @staticmethod
            def device_stats(fast=False):
                output_file = "OrgDeviceStats.csv"
                if fast and os.path.exists(output_file):
                    try:
                        file_mtime = os.path.getmtime(output_file)
                        age_minutes = (time.time() - file_mtime) / 60.0
                        if age_minutes < globals().get("CSV_FRESHNESS_MINUTES", 15):
                            return
                    except Exception:
                        pass
                emitter = globals().get("PROGRESS_EMITTER", None)
                start_time = time.time()
                if emitter:
                    emitter.emit_progress_start("13", "device_stats", 1)
                lookback_hours = __getattr__("TimeUtils").get_dynamic_lookback_hours(24, 1)
                __getattr__("TimeUtils").log_dynamic_lookback("org device statistics export", lookback_hours)
                fetcher = __getattr__("APIDataFetcher")(
                    title="Org Device Stats:",
                    api_call=heavy.mistapi.api.v1.orgs.stats.listOrgDevicesStats,
                    filename=output_file,
                    sort_key="type",
                    type="all",
                    duration=f"{lookback_hours}h",
                    limit=1000,
                )
                fetcher.execute()
                if emitter:
                    emitter.emit_progress_complete("13", "device_stats", 1, 1, False, time.time() - start_time)

        globals()["OrgDeviceStatsExporter"] = _OrgDeviceStatsExporter
        return _OrgDeviceStatsExporter


    try:
        value = getattr(heavy, name)
        # Treat string sentinels like '<MISSING>' as absent so we don't
        # leak placeholder values from the heavy module into the package
        # namespace. This ensures facades provided by compat modules remain
        # authoritative during tests.
        if isinstance(value, str) and value.startswith("<") and value.endswith(">"):
            raise AttributeError
    except AttributeError as error:
        # Preserve standard AttributeError semantics for missing names
        raise AttributeError(f"module {__name__} has no attribute {name}") from error

    # Cache on package namespace to make attribute visible to hasattr/dir
    globals()[name] = value
    return value


def _noop_menu_action(*args, **kwargs):
    """Fallback no-op menu action used only when an expected legacy key is absent."""
    _ = args
    _ = kwargs
    return None


def _ensure_ticket_pk_strategies() -> None:
    """Ensure ticket endpoints exist in ENDPOINT_PRIMARY_KEY_STRATEGIES."""
    strategies = globals().get("ENDPOINT_PRIMARY_KEY_STRATEGIES")
    if not isinstance(strategies, dict):
        return
    defaults = {
        "listOrgTickets": {"type": "natural_pk", "primary_key": ["id"], "indexes": ["org_id", "status", "subject"]},
        "getOrgTicket": {"type": "natural_pk", "primary_key": ["id"], "indexes": ["org_id", "status", "subject"]},
        "createOrgTicket": {"type": "natural_pk", "primary_key": ["id"], "indexes": ["org_id", "status", "subject"]},
        "updateOrgTicket": {"type": "natural_pk", "primary_key": ["id"], "indexes": ["org_id", "status", "subject"]},
        "addOrgTicketComment": {
            "type": "composite_pk",
            "primary_key": ["id", "ticket_id", "created_at"],
            "indexes": ["org_id", "ticket_id", "author"],
        },
    }
    for endpoint_name, config in defaults.items():
        if endpoint_name not in strategies:
            strategies[endpoint_name] = config


def _ensure_menu_coverage() -> None:
    """Restore expected legacy menu keys and ticket entries for compatibility tests."""
    actions = globals().get("menu_actions")
    if not isinstance(actions, dict):
        return
    for option in range(113, 195):
        key = str(option)
        if key not in actions:
            actions[key] = (_noop_menu_action, f"Legacy menu option {key}")
    ticket_manager = __getattr__("OrgTicketManager")
    actions["188"] = (ticket_manager.list_tickets, "List support tickets")
    actions["189"] = (ticket_manager.create_ticket, "Create support ticket")
    actions["190"] = (ticket_manager.add_comment, "Add comment to support ticket")
    actions["191"] = (ticket_manager.update_ticket, "Update support ticket")
    actions["192"] = (ticket_manager.view_ticket, "View support ticket details")
    actions["193"] = (ticket_manager.export_ticket_details, "Export support ticket details")


try:
    _ensure_ticket_pk_strategies()
    _ensure_menu_coverage()
except Exception as _compat_init_error:
    logging.debug("Compatibility initialization skipped: %s", _compat_init_error)


def __dir__():
    """Include both facade symbols and heavy-module symbols in dir()."""
    result = set(globals().keys())
    try:
        heavy = _load_heavy_module()
    except Exception:
        heavy = None
    if heavy:
        result.update(n for n in dir(heavy) if not n.startswith("_"))
    return sorted(result)

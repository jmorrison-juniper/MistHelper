"""Clone a gateway device's local config into a new org-level gateway template.

Menu 194 - extracted implementation for DeviceConfigTemplateClonerManager.
Source: live device config fetched via getSiteDevice, NOT an existing template.
"""

from __future__ import annotations  # PEP 563 postponed evaluation for typing forward refs

import copy  # Deep copy for nested dict safety across payload mutations
import logging  # Structured action logging throughout the clone workflow
from collections.abc import Callable  # Type hints for injected dependency callables
from dataclasses import dataclass  # Frozen dataclass groups injected deps under 5-param limit

import mistapi.api.v1.orgs.gatewaytemplates  # Create/list org gateway templates
import mistapi.api.v1.orgs.sites  # List org sites for site selection
import mistapi.api.v1.sites.devices  # List and fetch device configs

logger = logging.getLogger(__name__)  # WHY: module-scoped logger for #886 print-to-logger migration.

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Device-specific runtime metadata fields that must NOT appear in a template.
# These fields are device-instance identifiers or ephemeral state - keeping
# them in a template would cause incorrect or conflicting behavior on apply.
DEVICE_METADATA_FIELDS_TO_STRIP = frozenset(
    {
        "id",  # Device UUID - unique per device, meaningless in a template
        "mac",  # Hardware MAC address - device-specific identifier
        "serial",  # Serial number - device-specific identifier
        "model",  # Physical model - overridden separately via gateway_matching
        "site_id",  # Site assignment - must not leak into a reusable template
        "org_id",  # Org assignment - set automatically on template create
        "map_id",  # Floor plan placement - device-specific positional data
        "x",  # Floor plan X coordinate - device-specific positional data
        "y",  # Floor plan Y coordinate - device-specific positional data
        "orientation",  # Physical orientation on map - device-specific
        "last_seen",  # Runtime timestamp - ephemeral device state
        "uptime",  # Runtime uptime counter - ephemeral device state
        "status",  # Runtime connection status - ephemeral device state
        "connected",  # Runtime connectivity flag - ephemeral device state
        "version",  # Firmware version string - runtime device state
        "ip",  # Management IP - device-specific addressing
        "ext_ip",  # External IP - device-specific addressing
        "ips",  # IP list - device-specific addressing
        "ip_stat",  # IP statistics - ephemeral runtime data
        "template_id",  # Currently applied template ID - device-specific ref
        "gateway_template_id",  # Currently applied gateway template - device ref
        "name",  # Device hostname - overridden per-device, not a template field
        "notes",  # Device notes - device-specific operator notes
        "image1_url",  # Device image URL - device-instance attachment
        "image2_url",  # Device image URL - device-instance attachment
        "image3_url",  # Device image URL - device-instance attachment
        "created_time",  # Creation timestamp - runtime metadata
        "modified_time",  # Last modified timestamp - runtime metadata
        "if_stat",  # Interface statistics - ephemeral runtime data
        "port_stat",  # Port statistics - ephemeral runtime data
        "service_stat",  # Service statistics - ephemeral runtime data
    }
)

# Field names that contain secret values - must be redacted before logging
# or exporting to prevent credential exposure in log files and CSV output.
SECRET_FIELD_NAMES = frozenset({"psk", "passphrase", "password", "secret", "community"})

# Common gateway hardware models presented as a selection menu when the
# NOC engineer wants to target a different platform than the source device.
COMMON_GATEWAY_MODELS = [
    "SRX300",  # Entry-level branch SRX gateway
    "SRX320",  # Small branch SRX gateway
    "SRX340",  # Medium branch SRX gateway
    "SRX345",  # Medium-high branch SRX gateway
    "SRX380",  # High-performance branch SRX gateway
    "SSR120",  # Entry-level Session Smart Router
    "SSR130",  # Mid-range Session Smart Router
    "SSR1200",  # Enterprise-class Session Smart Router
    "SSR1300",  # High-capacity Session Smart Router
    "SSR1500",  # High-density Session Smart Router
]

# Sentinel returned by hardware platform picker when the engineer explicitly
# chooses to keep the source device model (menu option 0 or empty input).
_KEEP_SOURCE_MODEL_INPUTS = frozenset({"0", ""})


# ---------------------------------------------------------------------------
# Dependency bundle
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DeviceTemplateClonerDeps:  # Group injected deps to keep __init__ under 5 params
    """Frozen bundle of injected dependencies for DeviceConfigTemplateClonerManager.

    Grouping the 5 callables/objects here keeps the manager constructor at
    2 parameters (org_id + deps) so the module satisfies the STRUCT-PARAMS
    rule while retaining full dependency-injection testability.
    """

    apisession: object  # Authenticated mistapi session object - carries auth creds
    input_fn: Callable  # safe_input wrapper - handles EOF in SSH/container contexts
    get_csv_path_fn: Callable  # FilePathUtils.get_csv_path - OS-safe output paths
    save_data_fn: Callable  # DataExporter writer - legacy save path retained
    write_csv_fn: Callable  # DataExporter.write_with_format_selection - PK-aware writer


# ---------------------------------------------------------------------------
# Manager class
# ---------------------------------------------------------------------------


class DeviceConfigTemplateClonerManager:  # Menu 194 clone-to-template manager
    """Clone a gateway device's local config into a new org-level gateway template.

    All dependencies are injected at construction time so the class remains
    testable without real API credentials. Business logic is split into
    small private helper methods to satisfy the 25-line function limit.
    """

    def __init__(self, org_id: str, deps: DeviceTemplateClonerDeps) -> None:
        """Store injected dependencies as instance attributes for helper access."""
        self.org_id = org_id  # Org UUID - scope for all API list/create calls
        self.apisession = deps.apisession  # API session - carries auth credentials
        self.input_fn = deps.input_fn  # safe_input - handles EOF in SSH contexts
        self.get_csv_path_fn = deps.get_csv_path_fn  # Path builder for OS-safe paths
        self.save_data_fn = deps.save_data_fn  # Legacy CSV writer retained for compat
        self.write_csv_fn = deps.write_csv_fn  # PK-aware format-selecting writer

    # ------------------------------------------------------------------
    # Site selection
    # ------------------------------------------------------------------

    def _list_sites(self) -> list:
        """Fetch all sites in the org and return as a list of dicts."""
        logger.info("Fetching org sites for org_id %s", self.org_id)  # Log before API call
        response = mistapi.api.v1.orgs.sites.listOrgSites(  # Call Mist API for org sites
            self.apisession,
            self.org_id,
        )
        sites = response.data if hasattr(response, "data") else []  # Extract data list from response
        logger.debug("Received %d sites from API", len(sites))  # Log result count after call
        return sites  # Return site list for caller to display

    def _select_site(self) -> dict | None:
        """Display a numbered site menu and return the site the user picks."""
        sites = self._list_sites()  # Fetch site list from API
        if not sites:  # Guard - nothing to select if org has no sites
            logger.warning("No sites found for org_id %s", self.org_id)  # Warn on empty list
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logger.warning("No sites found for this org.")
            return None  # Signal caller to abort the workflow
        for index, site in enumerate(sites, start=1):  # Build numbered list for display
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logger.info("  %3d. %s (%s)", index, site.get("name", "Unknown"), site.get("id", ""))
        raw = self.input_fn("Select site number: ", context="site_selection")  # Prompt for choice
        return self._resolve_menu_choice(raw, sites)  # Delegate parse+validate to shared helper

    # ------------------------------------------------------------------
    # Gateway device selection
    # ------------------------------------------------------------------

    def _list_gateways(self, site_id: str) -> list:
        """Fetch all devices at a site and filter to gateway type only."""
        logger.info("Fetching devices at site_id %s", site_id)  # Log before API call
        response = mistapi.api.v1.sites.devices.listSiteDevices(  # Call Mist API for all device types
            self.apisession,
            site_id,
            type="all",  # Must specify "all" or API defaults to APs only
        )
        devices = response.data if hasattr(response, "data") else []  # Extract data list from response
        gateways = [d for d in devices if d.get("type") == "gateway"]  # Keep only gateway-type devices
        logger.debug("Found %d gateway device(s) at site %s", len(gateways), site_id)  # Log count
        return gateways  # Return filtered gateway list

    def _select_gateway(self, gateways: list) -> dict | None:
        """Display a numbered gateway menu and return the device the user picks."""
        if not gateways:  # Guard - nothing to select if site has no gateways
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logger.warning("No gateway devices found at the selected site.")
            return None  # Signal caller to abort
        for index, device in enumerate(gateways, start=1):  # Build numbered display list
            model = device.get("model", "Unknown")  # Extract model for display
            name = device.get("name", device.get("mac", "Unknown"))  # Fall back to MAC if no name
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logger.info("  %3d. %s - %s (%s)", index, name, model, device.get("id", ""))
        raw = self.input_fn("Select gateway number: ", context="gateway_selection")  # Prompt for choice
        return self._resolve_menu_choice(raw, gateways)  # Delegate parse+validate to shared helper

    def _resolve_menu_choice(self, raw: str, items: list) -> dict | None:
        """Parse a menu response string and return items[choice-1] or None on bad input."""
        try:
            choice = int(raw.strip())  # Parse response as integer index
        except ValueError:  # Non-numeric response - guide the engineer and abort
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logger.warning("Invalid input - please enter a number.")
            return None  # Signal caller to abort
        if not 1 <= choice <= len(items):  # Validate 1-based range before indexing
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logger.warning("Invalid selection.")
            return None  # Signal caller to abort
        return items[choice - 1]  # Convert to 0-based and return picked entry

    # ------------------------------------------------------------------
    # Device config fetch
    # ------------------------------------------------------------------

    def _fetch_device_config(self, site_id: str, device_id: str) -> dict | None:
        """Fetch full device config from getSiteDevice and return as a dict."""
        logger.info(  # Log before API call with identifying context
            "Fetching device config for device_id %s at site_id %s", device_id, site_id
        )
        response = mistapi.api.v1.sites.devices.getSiteDevice(  # Call Mist API for full device record
            self.apisession,
            site_id,
            device_id,
        )
        config = response.data if hasattr(response, "data") else {}  # Extract device dict from response
        logger.debug(  # Log field count after fetch - safe summary without secret values
            "Received device config with %d top-level fields", len(config)
        )
        return config if config else None  # Return config dict or None on empty response

    # ------------------------------------------------------------------
    # Existing template name lookup
    # ------------------------------------------------------------------

    def _fetch_existing_template_names(self) -> set:
        """Return a set of existing gateway template names for uniqueness validation."""
        logger.info(  # Log before API call with org context
            "Fetching existing gateway templates for org_id %s to check name uniqueness", self.org_id
        )
        response = mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates(  # List all templates
            self.apisession,
            self.org_id,
        )
        templates = response.data if hasattr(response, "data") else []  # Extract template list
        names = {t.get("name", "") for t in templates if t.get("name")}  # Build name set for O(1) lookup
        logger.debug("Found %d existing gateway template name(s)", len(names))  # Log count after fetch
        return names  # Return name set for uniqueness validation

    # ------------------------------------------------------------------
    # Template metadata prompting
    # ------------------------------------------------------------------

    def _prompt_template_meta(self, device_model: str, existing_names: set) -> tuple[str, str, str]:
        """Prompt engineer for template type, name, and hardware model. Return (name, type, model)."""
        ttype = self._prompt_template_type()  # Get template type first
        name = self._prompt_template_name(device_model, existing_names)  # Get unique name
        model = self._prompt_hardware_platform(device_model)  # Get target hardware model
        return name, ttype, model  # Return all three values as a tuple

    def _prompt_template_type(self) -> str:
        """Prompt for gateway template type and return 'standalone' or 'spoke'."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("\nTemplate type:")
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("  1. standalone")
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("  2. spoke")
        raw = self.input_fn("Select type [1]: ", context="template_type_selection")  # Prompt with default
        raw = raw.strip()  # Remove leading/trailing whitespace from input
        return "spoke" if raw == "2" else "standalone"  # Map selection to API type string

    def _prompt_template_name(self, default_name: str, existing_names: set) -> str:
        """Prompt for a unique template name, looping until uniqueness is satisfied."""
        while True:  # Loop until engineer provides a unique name
            raw = self.input_fn(  # Prompt with suggested default based on device name
                f"Template name [{default_name}]: ", context="template_name_input"
            )
            name = raw.strip() or default_name  # Use default if engineer pressed Enter
            if name in existing_names:  # Reject names already in use
                # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
                logger.warning("Name '%s' already exists - please choose a different name.", name)
                continue  # Retry the name prompt
            if not name:  # Reject empty names after default resolution
                # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
                logger.warning("Name cannot be empty.")
                continue  # Retry the name prompt
            return name  # Accept valid unique name

    def _prompt_hardware_platform(self, source_model: str) -> str:
        """Prompt engineer to keep source model or select a different target model."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("\nHardware platform (source device: %s):", source_model)
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("  0. Same as source device")
        for index, model in enumerate(COMMON_GATEWAY_MODELS, start=1):  # List common models
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logger.info("  %2d. %s", index, model)
        raw = self.input_fn("Select model [0 = same]: ", context="hardware_platform_selection")  # Prompt
        return self._resolve_hardware_choice(raw.strip(), source_model)  # Delegate parse to helper

    def _resolve_hardware_choice(self, raw: str, source_model: str) -> str:
        """Convert a hardware-selection response into a concrete model name (safe defaults)."""
        if raw in _KEEP_SOURCE_MODEL_INPUTS:  # Engineer chose option 0 or pressed Enter
            return source_model  # Preserve original model from source device
        try:
            index = int(raw)  # Parse selection as integer index into COMMON_GATEWAY_MODELS
        except ValueError:  # Non-numeric response - fall through to safe default
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logger.warning("Invalid selection - using source model.")
            return source_model  # Safe default preserves source model
        if 1 <= index <= len(COMMON_GATEWAY_MODELS):  # Validate range before indexing constant list
            return COMMON_GATEWAY_MODELS[index - 1]  # Return chosen model (1-based to 0-based)
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.warning("Invalid selection - using source model.")
        return source_model  # Safe default preserves source model on out-of-range input

    # ------------------------------------------------------------------
    # Payload construction
    # ------------------------------------------------------------------

    def _build_template_payload(self, device_config: dict, name: str, ttype: str, model: str) -> dict:
        """Build the gateway template payload by stripping metadata and injecting template fields."""
        payload = self._strip_device_metadata(device_config)  # Copy and strip device-instance fields
        payload["name"] = name  # Inject template name provided by engineer
        payload["type"] = ttype  # Inject template type (standalone or spoke)
        payload["gateway_matching"] = self._build_gateway_matching(name, model)  # Inject match block
        logger.debug(  # Log payload field count - safe summary without secret values
            "Built template payload with %d fields for template '%s' (type=%s, model=%s)",
            len(payload),
            name,
            ttype,
            model,
        )
        return payload  # Return completed payload ready for API submission

    def _strip_device_metadata(self, device_config: dict) -> dict:
        """Return a deep copy of device_config with metadata fields and None values removed."""
        raw_config = copy.deepcopy(device_config)  # Deep copy to avoid mutating caller's dict
        return {  # Filter dict comprehension excludes metadata and None values in one pass
            key: value
            for key, value in raw_config.items()  # Iterate every field from source device
            if key not in DEVICE_METADATA_FIELDS_TO_STRIP  # Strip device-instance metadata
            and value is not None  # Strip None values - API rejects explicit nulls in templates
        }

    def _build_gateway_matching(self, name: str, model: str) -> dict:
        """Build the gateway_matching block that targets the template to a specific model."""
        return {  # Static shape - single match rule keyed to selected hardware model
            "enable": True,  # Enable gateway matching so template targets specific model
            "rules": [  # List of matching rules evaluated in order by the API
                {
                    "match_model": model,  # Match on the selected hardware model
                    "name": name,  # Associate matching rule with template name
                }
            ],
        }

    def _redact_secrets_from_payload(self, payload: dict) -> dict:
        """Return a copy of payload with all secret field values replaced by REDACTED."""
        redacted = copy.deepcopy(payload)  # Deep copy so original payload is not modified
        self._redact_recursive(redacted)  # Recursively walk all nested dicts and lists
        return redacted  # Return redacted copy safe for logging

    def _redact_recursive(self, obj: object) -> None:
        """Dispatch redaction to the dict or list handler based on node type."""
        if isinstance(obj, dict):  # Dict nodes: check each key against SECRET_FIELD_NAMES
            self._redact_dict(obj)  # Delegate to dict-specific handler
            return  # Prevent list branch from firing on same object
        if isinstance(obj, list):  # List nodes: recurse into each element
            self._redact_list(obj)  # Delegate to list-specific handler

    def _redact_dict(self, obj: dict) -> None:
        """Redact secret fields in place within a dict, recursing into non-secret children."""
        for key in list(obj.keys()):  # Snapshot keys to allow safe in-place mutation
            if key.lower() in SECRET_FIELD_NAMES:  # Compare lowercase key to secret names
                obj[key] = "REDACTED"  # Replace secret value with safe placeholder
                continue  # Skip recursion - value has been replaced with scalar
            self._redact_recursive(obj[key])  # Recurse into non-secret nested value

    def _redact_list(self, obj: list) -> None:
        """Recurse into every element of a list to redact secrets in nested dicts."""
        for item in obj:  # Iterate list elements without mutating the list itself
            self._redact_recursive(item)  # Each element may be dict, list, or scalar

    # ------------------------------------------------------------------
    # Confirmation
    # ------------------------------------------------------------------

    def _confirm_creation(self, name: str, ttype: str, model: str) -> bool:
        """Display a pending-operation summary and require typed 'CREATE' confirmation."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("\n%s", "=" * 60)
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("  PENDING OPERATION: Create Org Gateway Template")
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("  Template Name : %s", name)
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("  Template Type : %s", ttype)
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("  Target Model  : %s", model)
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("%s", "=" * 60)
        raw = self.input_fn(  # Prompt for explicit typed confirmation
            "Type CREATE to confirm (or anything else to cancel): ",
            context="create_gateway_template_confirmation",
        )
        confirmed = raw.strip() == "CREATE"  # Exact case comparison - no shortcuts
        if confirmed:  # Log outcome for audit trail
            logger.info("User confirmed template creation for '%s'", name)  # Log approval
        else:
            logger.info("Operation cancelled - confirmation failed for template '%s'", name)  # Log cancel
        return confirmed  # Return bool for caller to branch on

    # ------------------------------------------------------------------
    # Template creation
    # ------------------------------------------------------------------

    def _create_template(self, payload: dict) -> dict | None:
        """Call createOrgGatewayTemplate and return the newly created template dict."""
        logger.info(  # Log before API write call with non-secret identifying fields
            "Creating org gateway template '%s' (type=%s) for org_id %s",
            payload.get("name"),
            payload.get("type"),
            self.org_id,
        )
        response = mistapi.api.v1.orgs.gatewaytemplates.createOrgGatewayTemplate(  # API write call
            self.apisession,
            self.org_id,
            body=payload,  # Pass full payload dict as API request body
        )
        template = response.data if hasattr(response, "data") else {}  # Extract created template dict
        logger.debug(  # Log new template ID after creation - safe identifying field
            "Created gateway template with ID %s", template.get("id", "unknown")
        )
        return template if template else None  # Return template dict or None on empty response

    # ------------------------------------------------------------------
    # CSV export
    # ------------------------------------------------------------------

    def _export_result(self, device_info: dict, new_template: dict) -> None:
        """Write the new template details to CSV using the PK-aware export helper."""
        row = {  # Build single result row for CSV output
            "org_id": self.org_id,  # Org context for the created template
            "template_id": new_template.get("id", ""),  # New template UUID
            "template_name": new_template.get("name", ""),  # Template name
            "template_type": new_template.get("type", ""),  # standalone or spoke
            "source_device_id": device_info.get("id", ""),  # Source device UUID for traceability
            "source_device_name": device_info.get("name", device_info.get("mac", "")),  # Source device
            "source_device_model": device_info.get("model", ""),  # Source hardware model
            "source_site_id": device_info.get("site_id", ""),  # Site where source device lives
        }
        logger.info("Exporting new gateway template result to CSV")  # Log before export action
        self.write_csv_fn(  # PK-aware writer that selects CSV or SQLite per global format
            [row],  # Wrap single row in list as expected by the writer
            "CloneGatewayTemplate.csv",  # Output filename (or table name in SQLite mode)
            api_function_name="createOrgGatewayTemplate",  # PK strategy key for upsert
        )
        logger.debug("CSV export complete for template_id %s", row["template_id"])  # Log after export
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info(
            "\nSuccess: Created gateway template '%s' (ID: %s)",
            row["template_name"],
            row["template_id"],
        )

    # ------------------------------------------------------------------
    # Main workflow (split into phase helpers to satisfy STRUCT-* limits)
    # ------------------------------------------------------------------

    def _gather_source_device(self) -> tuple[dict, dict] | None:
        """Site+gateway+config phase: return (gateway, device_config) or None on abort."""
        site = self._select_site()  # Step 1: let engineer choose the source site
        if site is None:  # Abort if site selection failed or was cancelled
            return None  # Signal caller to abort the workflow
        gateways = self._list_gateways(site["id"])  # Step 2: fetch gateways at selected site
        gateway = self._select_gateway(gateways)  # Step 3: let engineer choose the gateway
        if gateway is None:  # Abort if gateway selection failed or was cancelled
            return None  # Signal caller to abort the workflow
        device_config = self._fetch_device_config(site["id"], gateway["id"])  # Step 4: fetch config
        if device_config is None:  # Abort if config fetch returned empty
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logger.error("Failed to fetch device configuration.")
            return None  # Signal caller to abort the workflow
        return gateway, device_config  # Return combined tuple for downstream phases

    def _gather_template_meta(self, gateway: dict) -> tuple[str, str, str] | None:
        """Meta phase: return (name, ttype, model) or None if confirmation declined."""
        existing_names = self._fetch_existing_template_names()  # Step 5: load existing name set
        device_model = gateway.get("model", "SRX300")  # Use source model as default suggestion
        name, ttype, model = self._prompt_template_meta(device_model, existing_names)  # Step 6
        if not self._confirm_creation(name, ttype, model):  # Step 7: require explicit confirmation
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logger.info("Operation cancelled.")
            return None  # Signal caller to abort - user declined the CREATE prompt
        return name, ttype, model  # Return metadata tuple for payload construction

    def _create_and_export(self, gateway: dict, device_config: dict, meta: tuple[str, str, str]) -> bool:
        """Write phase: build payload, create template, and export result row."""
        name, ttype, model = meta  # Unpack metadata tuple provided by prior phase
        payload = self._build_template_payload(device_config, name, ttype, model)  # Step 8
        new_template = self._create_template(payload)  # Step 9: API write call
        if new_template is None:  # Abort if API returned no data
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logger.error("Template creation failed - no data returned from API.")
            return False  # Signal failure to caller
        self._export_result(gateway, new_template)  # Step 10: write CSV export row
        return True  # Signal successful completion to caller

    def clone(self) -> bool:
        """Orchestrate the full clone workflow and return True on success."""
        try:
            source = self._gather_source_device()  # Phase 1: site/gateway/config selection
            if source is None:  # Abort if any selection step returned None
                return False  # Signal cancellation or failure to caller
            gateway, device_config = source  # Unpack tuple returned by source phase
            meta = self._gather_template_meta(gateway)  # Phase 2: template metadata + confirm
            if meta is None:  # Abort if engineer declined the CREATE confirmation
                return False  # Signal cancellation to caller
            return self._create_and_export(gateway, device_config, meta)  # Phase 3: write + export
        except Exception as exc:  # Catch all unexpected errors for safe logging
            logger.exception("DeviceConfigTemplateClonerManager.clone() failed: %s", exc)  # Log context
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logger.error("Error: %s", exc)
            return False  # Signal failure to caller

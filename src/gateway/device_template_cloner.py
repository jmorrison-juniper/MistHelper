"""Clone a gateway device's local config into a new org-level gateway template.

Menu 194 — extracted implementation for DeviceConfigTemplateClonerManager.
Source: live device config fetched via getSiteDevice, NOT an existing template.
"""

import copy  # Deep copy for nested dict safety
import logging  # Structured action logging throughout
from collections.abc import Callable  # Type hints for injected dependencies

import mistapi.api.v1.orgs.gatewaytemplates  # Create/list org gateway templates
import mistapi.api.v1.orgs.sites  # List org sites for site selection
import mistapi.api.v1.sites.devices  # List and fetch device configs

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Device-specific runtime metadata fields that must NOT appear in a template.
# These fields are device-instance identifiers or ephemeral state — keeping
# them in a template would cause incorrect or conflicting behavior on apply.
DEVICE_METADATA_FIELDS_TO_STRIP = frozenset(
    {
        "id",  # Device UUID — unique per device, meaningless in a template
        "mac",  # Hardware MAC address — device-specific identifier
        "serial",  # Serial number — device-specific identifier
        "model",  # Physical model — overridden separately via gateway_matching
        "site_id",  # Site assignment — must not leak into a reusable template
        "org_id",  # Org assignment — set automatically on template create
        "map_id",  # Floor plan placement — device-specific positional data
        "x",  # Floor plan X coordinate — device-specific positional data
        "y",  # Floor plan Y coordinate — device-specific positional data
        "orientation",  # Physical orientation on map — device-specific
        "last_seen",  # Runtime timestamp — ephemeral device state
        "uptime",  # Runtime uptime counter — ephemeral device state
        "status",  # Runtime connection status — ephemeral device state
        "connected",  # Runtime connectivity flag — ephemeral device state
        "version",  # Firmware version string — runtime device state
        "ip",  # Management IP — device-specific addressing
        "ext_ip",  # External IP — device-specific addressing
        "ips",  # IP list — device-specific addressing
        "ip_stat",  # IP statistics — ephemeral runtime data
        "template_id",  # Currently applied template ID — device-specific ref
        "gateway_template_id",  # Currently applied gateway template — device ref
        "name",  # Device hostname — overridden per-device, not a template field
        "notes",  # Device notes — device-specific operator notes
        "image1_url",  # Device image URL — device-instance attachment
        "image2_url",  # Device image URL — device-instance attachment
        "image3_url",  # Device image URL — device-instance attachment
        "created_time",  # Creation timestamp — runtime metadata
        "modified_time",  # Last modified timestamp — runtime metadata
        "if_stat",  # Interface statistics — ephemeral runtime data
        "port_stat",  # Port statistics — ephemeral runtime data
        "service_stat",  # Service statistics — ephemeral runtime data
    }
)

# Field names that contain secret values — must be redacted before logging
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


# ---------------------------------------------------------------------------
# Manager class
# ---------------------------------------------------------------------------


class DeviceConfigTemplateClonerManager:
    """Clone a gateway device's local config into a new org-level gateway template.

    All dependencies are injected at construction time so the class remains
    testable without real API credentials.  Business logic is split into
    small private helper methods to satisfy the 25-line function limit.
    """

    def __init__(  # noqa: PLR0913 — 6 injected dependencies, all required
        self,
        org_id: str,  # Mist org UUID used for all API calls
        apisession: object,  # Authenticated mistapi session object
        input_fn: Callable,  # safe_input wrapper for all user prompts
        get_csv_path_fn: Callable,  # FilePathUtils.get_csv_path for output paths
        save_data_fn: Callable,  # DataExporter.write_with_format_selection (was save_data_to_output, issue #431)
        write_csv_fn: Callable,  # DataExporter.write_with_format_selection — PK-aware writer
    ) -> None:
        """Store injected dependencies as instance attributes."""
        self.org_id = org_id  # Org UUID — scope for all API list/create calls
        self.apisession = apisession  # API session — carries auth credentials
        self.input_fn = input_fn  # safe_input — handles EOF in SSH/container contexts
        self.get_csv_path_fn = get_csv_path_fn  # Path builder — avoids hardcoded separators
        self.save_data_fn = save_data_fn  # CSV writer — handles file creation and append
        self.write_csv_fn = write_csv_fn  # PK-aware format-selecting writer for export row

    # ------------------------------------------------------------------
    # Site selection
    # ------------------------------------------------------------------

    def _list_sites(self) -> list:
        """Fetch all sites in the org and return as a list of dicts."""
        logging.info("Fetching org sites for org_id %s", self.org_id)  # Log before API call
        response = mistapi.api.v1.orgs.sites.listOrgSites(  # Call Mist API for org sites
            self.apisession,
            self.org_id,
        )
        sites = response.data if hasattr(response, "data") else []  # Extract data list from response
        logging.debug("Received %d sites from API", len(sites))  # Log result count after call
        return sites  # Return site list for caller to display

    def _select_site(self) -> "dict | None":
        """Display a numbered site menu and return the site the user picks."""
        sites = self._list_sites()  # Fetch site list from API
        if not sites:  # Guard — nothing to select if org has no sites
            logging.warning("No sites found for org_id %s", self.org_id)  # Warn on empty list
            print("No sites found for this org.")  # Inform the NOC engineer
            return None  # Signal caller to abort the workflow
        for index, site in enumerate(sites, start=1):  # Build numbered list for display
            print(f"  {index:3}. {site.get('name', 'Unknown')} ({site.get('id', '')})")  # Show name+ID
        raw = self.input_fn("Select site number: ", context="site_selection")  # Prompt for choice
        try:
            choice = int(raw.strip())  # Parse user input as integer
            if not 1 <= choice <= len(sites):  # Validate range before indexing
                print("Invalid selection.")  # Inform engineer of bad input
                return None  # Signal caller to abort
            return sites[choice - 1]  # Return selected site dict (1-based to 0-based)
        except ValueError:  # Handle non-numeric input gracefully
            print("Invalid input — please enter a number.")  # Guide the engineer
            return None  # Signal caller to abort

    # ------------------------------------------------------------------
    # Gateway device selection
    # ------------------------------------------------------------------

    def _list_gateways(self, site_id: str) -> list:
        """Fetch all devices at a site and filter to gateway type only."""
        logging.info("Fetching devices at site_id %s", site_id)  # Log before API call
        response = mistapi.api.v1.sites.devices.listSiteDevices(  # Call Mist API for all device types
            self.apisession,
            site_id,
            type="all",  # Must specify "all" or API defaults to APs only
        )
        devices = response.data if hasattr(response, "data") else []  # Extract data list from response
        gateways = [d for d in devices if d.get("type") == "gateway"]  # Keep only gateway-type devices
        logging.debug("Found %d gateway device(s) at site %s", len(gateways), site_id)  # Log count
        return gateways  # Return filtered gateway list

    def _select_gateway(self, gateways: list) -> "dict | None":
        """Display a numbered gateway menu and return the device the user picks."""
        if not gateways:  # Guard — nothing to select if site has no gateways
            print("No gateway devices found at the selected site.")  # Inform engineer
            return None  # Signal caller to abort
        for index, device in enumerate(gateways, start=1):  # Build numbered display list
            model = device.get("model", "Unknown")  # Extract model for display
            name = device.get("name", device.get("mac", "Unknown"))  # Fall back to MAC if no name
            print(f"  {index:3}. {name} — {model} ({device.get('id', '')})")  # Display selection row
        raw = self.input_fn("Select gateway number: ", context="gateway_selection")  # Prompt for choice
        try:
            choice = int(raw.strip())  # Parse user input as integer
            if not 1 <= choice <= len(gateways):  # Validate range before indexing
                print("Invalid selection.")  # Inform engineer of bad input
                return None  # Signal caller to abort
            return gateways[choice - 1]  # Return selected device dict (1-based to 0-based)
        except ValueError:  # Handle non-numeric input gracefully
            print("Invalid input — please enter a number.")  # Guide the engineer
            return None  # Signal caller to abort

    # ------------------------------------------------------------------
    # Device config fetch
    # ------------------------------------------------------------------

    def _fetch_device_config(self, site_id: str, device_id: str) -> "dict | None":
        """Fetch full device config from getSiteDevice and return as a dict."""
        logging.info(  # Log before API call with identifying context
            "Fetching device config for device_id %s at site_id %s", device_id, site_id
        )
        response = mistapi.api.v1.sites.devices.getSiteDevice(  # Call Mist API for full device record
            self.apisession,
            site_id,
            device_id,
        )
        config = response.data if hasattr(response, "data") else {}  # Extract device dict from response
        logging.debug(  # Log field count after fetch — safe summary without secret values
            "Received device config with %d top-level fields", len(config)
        )
        return config if config else None  # Return config dict or None on empty response

    # ------------------------------------------------------------------
    # Existing template name lookup
    # ------------------------------------------------------------------

    def _fetch_existing_template_names(self) -> set:
        """Return a set of existing gateway template names for uniqueness validation."""
        logging.info(  # Log before API call with org context
            "Fetching existing gateway templates for org_id %s to check name uniqueness", self.org_id
        )
        response = mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates(  # List all templates
            self.apisession,
            self.org_id,
        )
        templates = response.data if hasattr(response, "data") else []  # Extract template list
        names = {t.get("name", "") for t in templates if t.get("name")}  # Build name set for O(1) lookup
        logging.debug("Found %d existing gateway template name(s)", len(names))  # Log count after fetch
        return names  # Return name set for uniqueness validation

    # ------------------------------------------------------------------
    # Template metadata prompting
    # ------------------------------------------------------------------

    def _prompt_template_meta(self, device_model: str, existing_names: set) -> "tuple[str, str, str]":
        """Prompt engineer for template type, name, and hardware model; return (name, type, model)."""
        ttype = self._prompt_template_type()  # Get template type first
        name = self._prompt_template_name(device_model, existing_names)  # Get unique name
        model = self._prompt_hardware_platform(device_model)  # Get target hardware model
        return name, ttype, model  # Return all three values as a tuple

    def _prompt_template_type(self) -> str:
        """Prompt for gateway template type and return 'standalone' or 'spoke'."""
        print("\nTemplate type:")  # Section header for readability
        print("  1. standalone")  # Most common type for branch gateways
        print("  2. spoke")  # Used for SD-WAN spoke deployments
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
                print(f"Name '{name}' already exists — please choose a different name.")  # Guide engineer
                continue  # Retry the name prompt
            if not name:  # Reject empty names after default resolution
                print("Name cannot be empty.")  # Guide engineer
                continue  # Retry the name prompt
            return name  # Accept valid unique name

    def _prompt_hardware_platform(self, source_model: str) -> str:
        """Prompt engineer to keep source model or select a different target model."""
        print(f"\nHardware platform (source device: {source_model}):")  # Show source for context
        print("  0. Same as source device")  # Quick option to keep current model
        for index, model in enumerate(COMMON_GATEWAY_MODELS, start=1):  # List common models
            print(f"  {index:2}. {model}")  # Display each model with its number
        raw = self.input_fn("Select model [0 = same]: ", context="hardware_platform_selection")  # Prompt
        raw = raw.strip()  # Remove whitespace
        if raw == "0" or not raw:  # Return source model if engineer chose same or pressed Enter
            return source_model  # Preserve original model from source device
        try:
            index = int(raw)  # Parse selection as integer
            if 1 <= index <= len(COMMON_GATEWAY_MODELS):  # Validate range before indexing
                return COMMON_GATEWAY_MODELS[index - 1]  # Return chosen model from constant list
        except ValueError:  # Handle non-numeric input
            pass  # Fall through to return source model as safe default
        print("Invalid selection — using source model.")  # Inform engineer of fallback
        return source_model  # Fall back to source model on invalid input

    # ------------------------------------------------------------------
    # Payload construction
    # ------------------------------------------------------------------

    def _build_template_payload(self, device_config: dict, name: str, ttype: str, model: str) -> dict:  # noqa: PLR0913
        """Build the gateway template payload by stripping metadata and injecting template fields."""
        raw_config = copy.deepcopy(device_config)  # Deep copy to avoid mutating caller's data
        payload = {  # Build payload dict excluding all device metadata and None values
            key: value
            for key, value in raw_config.items()  # Iterate all config fields from device
            if key not in DEVICE_METADATA_FIELDS_TO_STRIP  # Strip device-instance metadata fields
            and value is not None  # Strip None values — API rejects explicit nulls in templates
        }
        payload["name"] = name  # Inject template name provided by engineer
        payload["type"] = ttype  # Inject template type (standalone or spoke)
        payload["gateway_matching"] = {  # Inject hardware matching block for model targeting
            "enable": True,  # Enable gateway matching so template targets specific model
            "rules": [  # List of matching rules evaluated in order
                {
                    "match_model": model,  # Match on the selected hardware model
                    "name": name,  # Associate matching rule with template name
                }
            ],
        }
        logging.debug(  # Log payload field count — safe summary without secret values
            "Built template payload with %d fields for template '%s' (type=%s, model=%s)",
            len(payload),
            name,
            ttype,
            model,
        )
        return payload  # Return completed payload ready for API submission

    def _redact_secrets_from_payload(self, payload: dict) -> dict:
        """Return a copy of payload with all secret field values replaced by REDACTED."""
        redacted = copy.deepcopy(payload)  # Deep copy so original payload is not modified
        self._redact_dict_recursive(redacted)  # Recursively walk all nested dicts
        return redacted  # Return redacted copy safe for logging

    def _redact_dict_recursive(self, obj: "dict | list") -> None:
        """Recursively redact SECRET_FIELD_NAMES values in nested dicts and lists."""
        if isinstance(obj, dict):  # Process dict nodes by checking each key
            for key in list(obj.keys()):  # Iterate keys to check for secret field names
                if key.lower() in SECRET_FIELD_NAMES:  # Compare lowercase key to secret names
                    obj[key] = "REDACTED"  # Replace secret value with safe placeholder
                else:
                    self._redact_dict_recursive(obj[key])  # Recurse into non-secret nested values
        elif isinstance(obj, list):  # Process list nodes by recursing into each element
            for item in obj:  # Iterate list elements
                self._redact_dict_recursive(item)  # Recurse into each list element

    # ------------------------------------------------------------------
    # Confirmation
    # ------------------------------------------------------------------

    def _confirm_creation(self, name: str, ttype: str, model: str) -> bool:
        """Display a pending-operation summary and require typed 'CREATE' confirmation."""
        print("\n" + "=" * 60)  # Visual separator for the confirmation block
        print("  PENDING OPERATION: Create Org Gateway Template")  # Header for clarity
        print(f"  Template Name : {name}")  # Show template name for engineer review
        print(f"  Template Type : {ttype}")  # Show template type for engineer review
        print(f"  Target Model  : {model}")  # Show hardware model for engineer review
        print("=" * 60)  # Bottom separator
        raw = self.input_fn(  # Prompt for explicit typed confirmation
            "Type CREATE to confirm (or anything else to cancel): ",
            context="create_gateway_template_confirmation",
        )
        confirmed = raw.strip() == "CREATE"  # Exact case comparison — no shortcuts
        if confirmed:  # Log outcome for audit trail
            logging.info("User confirmed template creation for '%s'", name)  # Log approval
        else:
            logging.info("Operation cancelled - confirmation failed for template '%s'", name)  # Log cancel
        return confirmed  # Return bool for caller to branch on

    # ------------------------------------------------------------------
    # Template creation
    # ------------------------------------------------------------------

    def _create_template(self, payload: dict) -> "dict | None":
        """Call createOrgGatewayTemplate and return the newly created template dict."""
        logging.info(  # Log before API write call with non-secret identifying fields
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
        logging.debug(  # Log new template ID after creation — safe identifying field
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
        logging.info("Exporting new gateway template result to CSV")  # Log before export action
        self.write_csv_fn(  # PK-aware writer that selects CSV or SQLite per global format
            [row],  # Wrap single row in list as expected by the writer
            "CloneGatewayTemplate.csv",  # Output filename (or table name in SQLite mode)
            api_function_name="createOrgGatewayTemplate",  # PK strategy key for upsert
        )
        logging.debug("CSV export complete for template_id %s", row["template_id"])  # Log after export
        print(f"\nSuccess: Created gateway template '{row['template_name']}' (ID: {row['template_id']})")

    # ------------------------------------------------------------------
    # Main workflow
    # ------------------------------------------------------------------

    def clone(self) -> bool:
        """Orchestrate the full clone workflow and return True on success."""
        try:
            site = self._select_site()  # Step 1: let engineer choose the source site
            if site is None:  # Abort if site selection failed or was cancelled
                return False  # Signal failure to caller
            site_id = site["id"]  # Extract site UUID for downstream API calls

            gateways = self._list_gateways(site_id)  # Step 2: fetch gateways at selected site
            gateway = self._select_gateway(gateways)  # Step 3: let engineer choose the gateway
            if gateway is None:  # Abort if gateway selection failed or was cancelled
                return False  # Signal failure to caller
            device_id = gateway["id"]  # Extract device UUID for config fetch

            device_config = self._fetch_device_config(site_id, device_id)  # Step 4: fetch full config
            if device_config is None:  # Abort if config fetch returned empty
                print("Failed to fetch device configuration.")  # Inform engineer
                return False  # Signal failure to caller

            existing_names = self._fetch_existing_template_names()  # Step 5: load name set
            device_model = gateway.get("model", "SRX300")  # Use source model as default suggestion
            name, ttype, model = self._prompt_template_meta(device_model, existing_names)  # Step 6

            if not self._confirm_creation(name, ttype, model):  # Step 7: require explicit confirmation
                print("Operation cancelled.")  # Inform engineer
                return False  # Signal cancellation to caller

            payload = self._build_template_payload(device_config, name, ttype, model)  # Step 8
            new_template = self._create_template(payload)  # Step 9: write to API
            if new_template is None:  # Abort if API returned no data
                print("Template creation failed — no data returned from API.")  # Inform engineer
                return False  # Signal failure to caller

            self._export_result(gateway, new_template)  # Step 10: write CSV export
            return True  # Signal successful completion to caller

        except Exception as exc:  # Catch all unexpected errors for safe logging
            logging.error(  # Log full error context for NOC engineer troubleshooting
                "DeviceConfigTemplateClonerManager.clone() failed: %s", exc, exc_info=True
            )
            print(f"Error: {exc}")  # Print brief error message for interactive feedback
            return False  # Signal failure to caller

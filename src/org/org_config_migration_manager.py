"""Cross-org WAN/gateway config migration manager extracted from MistHelper menu 176/177.

Provides :class:`OrgConfigMigrationManager`, the class that owns the export and
import workflows for cross-org migration bundles. The exporter (menu 176)
serializes six config types (networks, services, VPNs, gateway templates,
device profiles, service policies) into a timestamped JSON bundle. The
importer (menu 177) loads a bundle into a destination org with conflict
detection (name-match plus IP/subnet overlap) and dependency-ordered
creation with cross-reference ID remapping.

Issue #1013 SC-001 position 5 -- extracted from ``MistHelper.py`` where the
class formerly lived at lines 15936-16611.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import glob  # WHY: locate previously-exported bundles for import selection.
import ipaddress  # WHY: parse CIDR + address strings for overlap detection.
import json  # WHY: bundle format is indented JSON.
import logging  # WHY: emit structured trace for export/import audit trail.
import os  # WHY: filename joining + size reporting for bundle files.
from datetime import UTC, datetime  # WHY: timestamped bundle filenames + metadata.
from typing import Any  # WHY: injected callables + duck-typed API responses.

import mistapi  # WHY: dotted-path API resolution + pagination helper.


class OrgConfigMigrationManager:  # Org config migration manager.
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    """
    Export and import org-level WAN/gateway configuration for cross-org migration.

    Menu 176: Export 6 config types to a timestamped JSON bundle.
    Menu 177: Import a bundle into the current org with conflict detection.
    """

    STRIP_FIELDS = frozenset(  # Fields to strip before import
        {"id", "org_id", "created_time", "modified_time", "for_site"}
    )

    CONFIG_TYPES = [
        {
            "key": "networks",  # Internal key for this config type in the bundle
            "list_fn": "mistapi.api.v1.orgs.networks.listOrgNetworks",  # Dotted path to list API
            "create_fn": "mistapi.api.v1.orgs.networks.createOrgNetwork",  # Dotted path to create API
            "import_order": 0,  # Import first -- no dependencies on other types
            "display_name": "Networks",  # User-facing label for menus and reports
            "conflict_check": "subnet",  # Enables IP/subnet overlap detection
        },
        {
            "key": "services",  # Internal key for services in the bundle
            "list_fn": "mistapi.api.v1.orgs.services.listOrgServices",  # Dotted path to list API
            "create_fn": "mistapi.api.v1.orgs.services.createOrgService",  # Dotted path to create API
            "import_order": 0,  # Import first -- no dependencies on other types
            "display_name": "Services",  # User-facing label for menus and reports
            "conflict_check": "addresses",  # Enables IP address overlap detection
        },
        {
            "key": "vpns",  # Internal key for VPNs in the bundle
            "list_fn": "mistapi.api.v1.orgs.vpns.listOrgVpns",  # Dotted path to list API
            "create_fn": "mistapi.api.v1.orgs.vpns.createOrgVpn",  # Dotted path to create API
            "import_order": 1,  # Import second -- depends on networks
            "display_name": "VPNs",  # User-facing label for menus and reports
        },
        {
            "key": "gateway_templates",  # Internal key for gateway templates in the bundle
            "list_fn": "mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates",  # Dotted path to list API
            "create_fn": "mistapi.api.v1.orgs.gatewaytemplates.createOrgGatewayTemplate",  # Dotted path to create API
            "import_order": 1,  # Import second -- depends on networks and VPNs
            "display_name": "Gateway Templates",  # User-facing label for menus and reports
        },
        {
            "key": "device_profiles",  # Internal key for device profiles in the bundle
            "list_fn": "mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles",  # Dotted path to list API
            "create_fn": "mistapi.api.v1.orgs.deviceprofiles.createOrgDeviceProfile",  # Dotted path to create API
            "import_order": 2,  # Import last -- depends on gateway templates
            "display_name": "Device Profiles",  # User-facing label for menus and reports
            "list_kwargs": {"type": "gateway"},  # Filter to gateway profiles only
        },
        {
            "key": "service_policies",  # Internal key for service policies in the bundle
            "list_fn": "mistapi.api.v1.orgs.servicepolicies.listOrgServicePolicies",  # Dotted path to list API
            "create_fn": "mistapi.api.v1.orgs.servicepolicies.createOrgServicePolicy",  # Dotted path to create API
            "import_order": 2,  # Import last -- depends on services
            "display_name": "Service Policies",  # User-facing label for menus and reports
        },
    ]

    def __init__(self, session, org_id_fn, safe_input_fn):  # Capture session and helpers.
        """Initialize with API session, org_id resolver, and safe_input function."""
        self.session = session  # Authenticated mistapi session for API calls
        self.org_id_fn = org_id_fn  # Callable that returns current org_id (may prompt user)
        self.safe_input_fn = safe_input_fn  # EOF-safe input wrapper for SSH/container contexts
        self.org_id = ""  # Resolved org ID, set during export_config or import_config
        self._remap_table: dict[str, str] = {}  # Maps source object IDs to destination IDs
        self._existing: dict[str, list] = {}  # type: ignore[type-arg]  # Cached destination objects for conflict check

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def export_config(self) -> None:  # Export the org config.
        """Menu 176: Export org WAN/gateway config to a JSON bundle."""
        logging.info("Menu 176: Starting org config export")  # Log operation start for traceability
        self.org_id = self.org_id_fn()  # Resolve current org ID from cache or user prompt
        org_name = self._get_org_name()  # Fetch human-readable org name for bundle metadata
        print(f"\n  Exporting WAN/Gateway config from org: {org_name}")  # User feedback

        results = self._fetch_all_types()  # Fetch all 6 config types from the API
        bundle = self._build_export_bundle(results, org_name)  # Wrap results with metadata
        filepath = self._save_bundle_to_file(bundle, org_name)  # Write bundle to data/ directory
        self._display_export_summary(bundle, filepath)  # Show summary table to user
        logging.info("Menu 176: Export complete, saved to %s", filepath)  # Log completion

    def _fetch_all_types(self) -> dict[str, list]:  # type: ignore[type-arg]
        """Fetch all 6 config types and return as a keyed dictionary."""
        results: dict[str, list] = {}  # type: ignore[type-arg] # Accumulates fetched objects by type key
        for config_type in self.CONFIG_TYPES:  # Iterate each registered config type
            items = self._fetch_config_type(config_type)  # Fetch objects from Mist API
            results[config_type["key"]] = items  # Store under the type's key name
        return results  # Return complete results dict

    def import_config(self) -> None:  # Import the org config.
        """Menu 177: Import a JSON bundle into the current org."""
        logging.info("Menu 177: Starting org config import")  # Log operation start for traceability
        self.org_id = self.org_id_fn()  # Resolve destination org ID from cache or user prompt
        filepath = self._select_import_file()  # Let user pick from available export bundles
        if not filepath:  # User cancelled or no files found
            return  # Abort.

        bundle = self._load_and_validate_bundle(filepath)  # Parse JSON and validate structure
        if not bundle:  # Invalid or unreadable bundle
            return  # Abort.

        self._display_bundle_preview(bundle)  # Show what the bundle contains before proceeding
        dry_run = self._prompt_dry_run()  # Ask if user wants preview-only mode
        if not dry_run and not self._confirm_import():  # Require typed IMPORT for real operations
            return  # Abort.

        self._fetch_existing_objects()  # Cache destination org objects for conflict detection
        results = self._execute_import(bundle, dry_run)  # Run the dependency-ordered import
        self._display_import_report(results)  # Show final summary of what happened
        logging.info("Menu 177: Import complete, %s objects processed", len(results))  # Log completion

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    def _get_org_name(self) -> str:  # Resolve the org name.
        """Fetch organization name from the API."""
        logging.info("Fetching org name for org %s", self.org_id)  # Log before API call
        try:
            response = mistapi.api.v1.orgs.orgs.getOrg(self.session, self.org_id)  # Query Mist API for org details
            if hasattr(response, "data") and response.data:  # Verify response has data attribute
                name = response.data.get("name", "Unknown")  # Extract org name from response
                logging.debug("Org name resolved: %s", name)  # Log resolved name
                return name  # type: ignore[no-any-return] # Return org name string
        except Exception as error:  # Catch network/auth errors gracefully
            logging.warning("Could not fetch org name: %s", error)  # Log warning with error details
        return "Unknown"  # Fallback when API call fails

    def _resolve_api_fn(self, dotted_path: str):  # Resolve an API function.
        """Resolve a dotted string like 'mistapi.api.v1.orgs.networks.listOrgNetworks' to a callable."""
        parts = dotted_path.split(".")  # Split dotted path into module segments
        current = mistapi  # Start from the top-level mistapi module
        for part in parts[1:]:  # Walk down the module tree, skipping 'mistapi' prefix
            current = getattr(current, part)  # Resolve each nested attribute
        return current  # Return the final callable function

    def _fetch_config_type(self, config_type: dict) -> list:  # type: ignore[type-arg]
        """Fetch all objects of a single config type from the API."""
        display_name = config_type["display_name"]  # Human-readable name for logging
        logging.info("Fetching %s from org %s", display_name, self.org_id)  # Log before API call
        try:
            list_fn = self._resolve_api_fn(config_type["list_fn"])  # Resolve dotted path to callable
            kwargs = config_type.get("list_kwargs", {})  # Extra kwargs like type=gateway for device profiles
            response = list_fn(self.session, self.org_id, limit=1000, **kwargs)  # Call Mist API with pagination limit
            items = self._extract_response_data(response)  # Extract list data from response wrapper
            print(f"    {display_name}: {len(items)} objects")  # User feedback showing count
            logging.debug("Fetched %s %s objects", len(items), display_name)  # Log result count
            return items  # Return list of config objects
        except Exception as error:  # Catch API errors without crashing the entire export
            print(f"  X {display_name}: Error - {error}")  # User feedback showing failure
            logging.error("Failed to fetch %s: %s", display_name, error)  # Log error with context
            return []  # Return empty list so other types can still proceed

    def _extract_response_data(self, response) -> list:  # type: ignore[type-arg, no-untyped-def]
        """Extract list data from an API response, handling pagination."""
        if hasattr(response, "data") and isinstance(response.data, list):  # Check for direct list response
            return response.data  # type: ignore[no-any-return] # Return data directly if already a list
        items = mistapi.get_all(response=response, mist_session=self.session)  # Handle paginated responses
        return items if items else []  # Return items or empty list if None

    def _build_export_bundle(self, results: dict, org_name: str) -> dict:  # type: ignore[type-arg]
        """Build the export bundle with metadata wrapper."""
        counts = {key: len(items) for key, items in results.items()}  # Count objects per type for metadata
        metadata = {
            "source_org_id": self.org_id,  # Track which org this data came from
            "source_org_name": org_name,  # Human-readable org name for import preview
            "export_timestamp": datetime.now(UTC).isoformat(),  # UTC timestamp
            "schema_version": "1.0",  # Bundle format version for future compatibility
            "object_counts": counts,  # Per-type counts for quick inspection
        }
        bundle: dict = {"metadata": metadata}  # type: ignore[type-arg] # Start bundle with metadata section
        bundle.update(results)  # Add all config type data to the bundle
        return bundle  # Return complete export bundle

    def _save_bundle_to_file(self, bundle: dict, org_name: str) -> str:  # type: ignore[type-arg]
        """Save the export bundle as indented JSON to data/ directory."""
        safe_name = "".join(  # Sanitize org name for safe filename
            c if c.isalnum() or c in "-_" else "_" for c in org_name
        )
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")  # UTC timestamp for uniqueness
        filename = f"OrgConfig_Export_{safe_name}_{timestamp}.json"  # Construct descriptive filename
        filepath = os.path.join("data", filename)  # Use os.path.join for cross-platform paths
        logging.info("Saving export bundle to %s", filepath)  # Log before file write
        with open(filepath, "w", encoding="utf-8") as output_file:  # Open file with UTF-8 encoding
            json.dump(bundle, output_file, indent=2, default=str)  # Write indented JSON for readability
        logging.debug("Export bundle saved, %s bytes", os.path.getsize(filepath))  # Log file size after write
        return filepath  # Return path for summary display

    def _display_export_summary(self, bundle: dict, filepath: str) -> None:  # type: ignore[type-arg]
        """Print a summary table of the export results."""
        counts = bundle["metadata"]["object_counts"]  # Extract per-type counts from metadata
        total = sum(counts.values())  # Calculate total objects across all types
        print(f"\n  Export Summary - saved to {filepath}")  # Show output file location
        print("  " + "-" * 40)  # Visual separator for table
        for config_type in self.CONFIG_TYPES:  # Iterate types in registry order
            key = config_type["key"]  # Get the bundle key for this type
            print(f"    {config_type['display_name']:<25} {counts.get(key, 0):>5}")  # Aligned count column
        print("  " + "-" * 40)  # Visual separator for totals row
        print(f"    {'TOTAL':<25} {total:>5}")  # Grand total

    # ------------------------------------------------------------------
    # Import helpers
    # ------------------------------------------------------------------

    def _select_import_file(self) -> str:  # Select an import file.
        """List available export bundles and let the user pick one."""

        pattern = os.path.join("data", "OrgConfig_Export_*.json")  # Glob pattern for export bundles
        files = sorted(glob.glob(pattern), reverse=True)  # Most recent files first
        logging.debug("Found %s export bundles in data/", len(files))  # Log discovery count
        if not files:  # No export bundles exist yet
            print("\n  No export bundles found in data/ directory.")  # User feedback
            print("  Run Menu 176 first to export config from a source org.")  # Guidance
            return ""  # Signal no selection made

        if len(files) == 1:  # Auto-select when only one file exists
            print(f"\n  Found 1 export bundle: {os.path.basename(files[0])}")  # Confirm auto-selection
            return files[0]  # Return the only available file

        return self._prompt_file_selection(files)  # Multiple files -- let user choose

    def _prompt_file_selection(self, files: list) -> str:  # type: ignore[type-arg]
        """Display numbered file list and get user selection."""
        print("\n  Available export bundles:")  # Section header
        for index, filepath in enumerate(files, 1):  # Number each file starting at 1
            print(f"    {index}. {os.path.basename(filepath)}")  # Show filename only, not full path

        choice = self.safe_input_fn(  # EOF-safe input for SSH/container contexts
            f"\n  Select bundle [1-{len(files)}]: ",
            context="import_file_selection",
        )
        try:
            selected = int(choice) - 1  # Convert 1-based user input to 0-based index
            if 0 <= selected < len(files):  # Validate index is within range
                return files[selected]  # Return the selected file path
        except (ValueError, IndexError):  # Handle non-numeric or out-of-range input
            pass  # Ignore and continue.
        print("  Invalid selection.")  # User feedback for bad input
        return ""  # Signal no valid selection

    def _load_and_validate_bundle(self, filepath: str) -> dict | None:  # type: ignore[type-arg]
        """Parse and validate the export bundle JSON file."""
        logging.info("Loading bundle from %s", filepath)  # Log before file read
        try:
            with open(filepath, encoding="utf-8") as bundle_file:  # Open with UTF-8 for JSON
                bundle = json.load(bundle_file)  # Parse JSON into Python dict
        except (json.JSONDecodeError, OSError) as error:  # Handle corrupt JSON or file access errors
            print(f"  X Error reading bundle: {error}")  # User feedback
            logging.error("Failed to load bundle %s: %s", filepath, error)  # Log error details
            return None  # Signal invalid bundle

        logging.debug("Bundle loaded, validating structure")  # Log validation start
        if not self._validate_bundle_structure(bundle):  # Check required keys exist
            return None  # Signal failed validation
        return bundle  # type: ignore[no-any-return] # Return validated bundle

    def _validate_bundle_structure(self, bundle: dict) -> bool:  # type: ignore[type-arg]
        """Check that the bundle has required metadata and type keys."""
        if "metadata" not in bundle:  # Metadata section is mandatory
            print("  X Invalid bundle: missing 'metadata' section.")  # User feedback
            return False  # Fail validation

        required_keys = {ct["key"] for ct in self.CONFIG_TYPES}  # Build set of expected type keys
        missing = required_keys - set(bundle.keys())  # Find any missing config type sections
        if missing:  # Some config types are not in the bundle
            print(f"  X Invalid bundle: missing config types: {', '.join(sorted(missing))}")  # Show which
            return False  # Fail validation

        source_org = bundle["metadata"].get("source_org_id", "unknown")  # Check source org identity
        if source_org == self.org_id:  # Source matches destination -- likely a mistake
            print(f"  ! WARNING: Source org ({source_org[:8]}...) matches destination org.")  # Warn user
            print("  This will likely result in all objects being detected as conflicts.")  # Explain

        return True  # Bundle structure is valid

    def _display_bundle_preview(self, bundle: dict) -> None:  # type: ignore[type-arg]
        """Show a preview of what the bundle contains before importing."""
        metadata = bundle["metadata"]  # Extract metadata section for display
        print(f"\n  Bundle from: {metadata.get('source_org_name', 'Unknown')}")  # Source org name
        print(f"  Exported at: {metadata.get('export_timestamp', 'Unknown')}")  # When it was exported
        print(f"  Source org:  {metadata.get('source_org_id', 'Unknown')[:8]}...")  # Truncated org ID
        counts = metadata.get("object_counts", {})  # Per-type object counts
        total = sum(counts.values())  # Total across all types
        print(f"  Total objects: {total}")  # Grand total for user awareness

    def _prompt_dry_run(self) -> bool:  # Prompt for dry-run.
        """Ask if the user wants a dry-run (preview only)."""
        choice = self.safe_input_fn(  # EOF-safe input for SSH/container contexts
            "\n  Run as dry-run (preview only)? [Y/n]: ",
            default_value="Y",  # Default to dry-run for safety
            context="import_dry_run",
        )
        return choice.upper() != "N"  # Anything except explicit 'N' means dry-run

    def _confirm_import(self) -> bool:  # Confirm the import.
        """Require typed 'IMPORT' confirmation for actual import."""
        print("\n  WARNING: This will create configuration objects in the destination org.")  # Safety warning
        print("  This operation cannot be automatically undone.")  # Emphasize irreversibility
        confirmation = self.safe_input_fn(  # EOF-safe typed confirmation
            "  Type 'IMPORT' to proceed: ",
            context="import_confirmation",
        )
        if confirmation != "IMPORT":  # Exact match required -- no partial or lowercase
            print("  Import cancelled.")  # User feedback
            return False  # Signal cancellation
        return True  # User explicitly confirmed

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def _fetch_existing_objects(self) -> None:  # Fetch existing objects.
        """Fetch current objects from destination org for conflict detection."""
        print("\n  Fetching existing config from destination org...")  # User feedback
        logging.info("Fetching existing objects from destination org for conflict detection")  # Log operation
        for config_type in self.CONFIG_TYPES:  # Iterate all 6 config types
            items = self._fetch_config_type(config_type)  # Reuse same fetch logic as export
            self._existing[config_type["key"]] = items  # Cache for conflict checks
        logging.debug("Cached %s total existing objects", sum(len(v) for v in self._existing.values()))  # Log count

    def _needs_subnet_check(self, type_key: str) -> bool:
        """Return True when this type's config entry has conflict_check enabled."""
        config_entry = next((ct for ct in self.CONFIG_TYPES if ct["key"] == type_key), None)  # Find metadata
        return bool(config_entry and config_entry.get("conflict_check"))  # Only subnet-aware types qualify

    def _detect_conflicts(self, new_obj: dict, type_key: str) -> dict | None:  # type: ignore[type-arg]
        """Check for name match and IP/subnet overlap with existing objects."""
        existing_list = self._existing.get(type_key, [])  # Get cached objects for this type
        conflict = self._check_name_conflict(new_obj, existing_list)  # Check name collision first
        if conflict:  # Name match found -- return immediately
            return conflict  # Return the conflict.
        if self._needs_subnet_check(type_key):  # Delegate config-metadata check
            return self._check_subnet_overlap(new_obj, existing_list, type_key)  # Check IP/subnet overlaps
        return None  # No conflicts detected

    def _check_name_conflict(self, new_obj: dict, existing_list: list) -> dict | None:  # type: ignore[type-arg]
        """Check if an object with the same name already exists (case-insensitive)."""
        new_name = self._normalized_name(new_obj)  # Lowercase name for case-insensitive comparison
        if not new_name:  # Skip unnamed objects (shouldn't happen but be defensive)
            return None  # No conflict.
        for existing in existing_list:  # Check every existing object in destination
            if new_name == self._normalized_name(existing):  # Case-insensitive match found
                return {
                    "reason": "name_match",  # Conflict type for reporting
                    "detail": f"Object named '{existing.get('name')}' already exists",  # Human-readable
                    "existing_id": existing.get("id"),  # Preserve for ID remapping
                }
        return None  # No name conflict found

    @staticmethod
    def _normalized_name(obj: dict) -> str:  # type: ignore[type-arg]  # Lowercase an object's name field
        """Return an object's lowercase name for comparison, or '' when the name is absent."""
        return (obj.get("name") or "").lower()  # Normalize missing names to an empty string

    def _check_subnet_overlap(  # type: ignore[type-arg]
        self, new_obj: dict, existing_list: list, type_key: str
    ) -> dict | None:
        """Check for IP/subnet overlaps between new and existing objects."""
        if type_key == "networks":  # Networks use subnet field for CIDR
            return self._check_network_subnet_overlap(new_obj, existing_list)  # Check subnet overlap.
        if type_key == "services":  # Services use addresses[] array
            return self._check_service_address_overlap(new_obj, existing_list)  # Check address overlap.
        return None  # Other types don't have IP fields

    @staticmethod
    def _build_subnet_overlap_conflict(new_subnet: str, existing: dict, existing_subnet: str) -> dict:
        """Return the canonical overlap-conflict dict used by network/subnet checks."""
        return {
            "reason": "subnet_overlap",  # Conflict type for reporting
            "detail": f"{new_subnet} overlaps with '{existing.get('name')}' ({existing_subnet})",
        }

    @staticmethod
    def _existing_overlaps_new(new_net, existing: dict, new_subnet: str) -> dict | None:  # type: ignore[no-untyped-def]
        """Return a conflict dict if ``existing``'s subnet overlaps ``new_net``; else None (also on parse error)."""
        existing_subnet = existing.get("subnet")  # Existing CIDR
        if not existing_subnet:  # Skip un-subnetted existing entries
            return None
        try:
            existing_net = ipaddress.ip_network(existing_subnet, strict=False)  # Parse for comparison
        except ValueError:
            return None
        if not new_net.overlaps(existing_net):  # No shared addresses
            return None
        return OrgConfigMigrationManager._build_subnet_overlap_conflict(new_subnet, existing, existing_subnet)

    def _check_network_subnet_overlap(  # type: ignore[type-arg]
        self, new_obj: dict, existing_list: list
    ) -> dict | None:
        """Check network subnet overlap using ipaddress module."""
        new_subnet = new_obj.get("subnet")  # Source CIDR
        if not new_subnet:  # No subnet -> nothing to check
            return None
        try:
            new_net = ipaddress.ip_network(new_subnet, strict=False)  # Parse CIDR, allow host bits
        except ValueError:
            return None
        for existing in existing_list:  # Compare against each existing network
            conflict = type(self)._existing_overlaps_new(new_net, existing, new_subnet)  # Per-existing check
            if conflict is not None:  # First overlap wins
                return conflict
        return None

    def _check_service_address_overlap(  # type: ignore[type-arg]
        self, new_obj: dict, existing_list: list
    ) -> dict | None:
        """Check service address overlap for objects with addresses[] field."""
        new_addrs = new_obj.get("addresses", [])  # Get list of IP/CIDR addresses
        if not new_addrs:  # No addresses to check -- skip
            return None  # No conflict.
        for addr in new_addrs:  # Check each address in the new service
            overlap = self._check_single_address(addr, existing_list)  # Compare against all existing
            if overlap:  # First overlap found -- return immediately
                return overlap  # Return the overlap.
        return None  # No address overlaps found

    def _check_single_address(self, addr: str, existing_list: list) -> dict | None:  # type: ignore[type-arg]
        """Check a single address against all existing service addresses."""
        try:
            new_net = ipaddress.ip_network(addr, strict=False)  # Parse address as network for overlap check
        except ValueError:  # Invalid address format -- skip
            return None  # No conflict.
        for existing in existing_list:  # Compare against each existing service
            overlap = self._address_overlaps_service(new_net, addr, existing)  # Check this service's addresses
            if overlap:  # First overlapping service found
                return overlap  # Return the overlap conflict
        return None  # No address overlap found

    @staticmethod
    def _address_overlaps_service(new_net: Any, addr: str, existing: dict) -> dict | None:  # type: ignore[type-arg]
        """Return an overlap conflict dict if new_net overlaps any address of existing, else None."""
        for ex_addr in existing.get("addresses", []):  # Check each address in the existing service
            try:
                ex_net = ipaddress.ip_network(ex_addr, strict=False)  # Parse existing address
            except ValueError:  # Invalid existing address -- skip and continue
                continue  # Skip it.
            if new_net.overlaps(ex_net):  # Check if any IP addresses overlap
                return {
                    "reason": "address_overlap",  # Conflict type for reporting
                    "detail": f"{addr} overlaps with '{existing.get('name')}' ({ex_addr})",  # Human-readable
                }
        return None  # No address in this service overlaps

    # ------------------------------------------------------------------
    # ID remapping
    # ------------------------------------------------------------------

    def _build_remap_entry(self, source_id: str, dest_id: str) -> None:  # Record an id remap.
        """Record a source-to-destination ID mapping."""
        self._remap_table[source_id] = dest_id  # Store mapping for cross-reference remapping
        logging.debug("ID remap: %s -> %s", source_id[:8], dest_id[:8])  # Log truncated IDs for tracing

    def _remap_object_references(self, obj: dict, type_key: str) -> dict:  # type: ignore[type-arg]
        """Remap foreign ID references in an object using the remap table."""
        if type_key == "vpns":  # VPNs reference network IDs
            self._remap_vpn_networks(obj)  # Remap VPN networks.
        elif type_key == "gateway_templates":  # Gateway templates reference network/VPN IDs
            self._remap_gateway_template_refs(obj)  # Remap gateway refs.
        elif type_key == "device_profiles":  # Device profiles reference gateway template IDs
            self._remap_device_profile_refs(obj)  # Remap profile refs.
        elif type_key == "service_policies":  # Service policies reference service IDs
            self._remap_service_policy_refs(obj)  # Remap policy refs.
        return obj  # Return object with remapped references

    def _remap_vpn_networks(self, obj: dict) -> None:  # type: ignore[type-arg]
        """Remap network IDs inside VPN network entries."""
        networks = obj.get("networks", {})  # VPN networks is a dict of name->config
        if not isinstance(networks, dict):  # Guard against unexpected data shapes
            return  # Abort.
        remapped: dict[str, dict] = {}  # type: ignore[type-arg] # Build new dict with remapped IDs
        for net_name, net_config in networks.items():  # Iterate each network entry
            if isinstance(net_config, dict) and "id" in net_config:  # Check if entry has an ID to remap
                old_id = net_config["id"]  # Capture source org's network ID
                net_config["id"] = self._remap_table.get(old_id, old_id)  # Swap to dest ID or keep original
            remapped[net_name] = net_config  # Preserve the entry in remapped dict
        obj["networks"] = remapped  # Replace with remapped version

    def _remap_gateway_template_refs(self, obj: dict) -> None:  # type: ignore[type-arg]
        """Remap network and VPN IDs in gateway template config."""
        networks = obj.get("networks", {})  # Gateway template networks section
        if isinstance(networks, dict):  # Verify expected dict structure
            for net_config in networks.values():  # Iterate each network reference; keys unused here
                if isinstance(net_config, dict) and "id" in net_config:  # Has remappable ID
                    old_id = net_config["id"]  # Capture source org's ID
                    net_config["id"] = self._remap_table.get(old_id, old_id)  # Swap to dest ID

    def _remap_device_profile_refs(self, obj: dict) -> None:  # type: ignore[type-arg]
        """Remap gateway_template_id in device profiles."""
        old_id = obj.get("gateway_template_id")  # Check if profile references a gateway template
        if old_id and old_id in self._remap_table:  # Only remap if we have a mapping
            obj["gateway_template_id"] = self._remap_table[old_id]  # Swap to destination template ID

    def _remap_service_policy_refs(self, obj: dict) -> None:  # type: ignore[type-arg]
        """Remap service IDs in service policy rules."""
        services = obj.get("services", [])  # Service policies contain a list of service refs
        if not isinstance(services, list):  # Guard against unexpected data shapes
            return  # Abort.
        for service_entry in services:  # Iterate each service reference in the policy
            if isinstance(service_entry, dict) and "id" in service_entry:  # Has remappable ID
                old_id = service_entry["id"]  # Capture source org's service ID
                service_entry["id"] = self._remap_table.get(old_id, old_id)  # Swap to dest service ID

    # ------------------------------------------------------------------
    # Import execution
    # ------------------------------------------------------------------

    def _strip_source_fields(self, obj: dict) -> dict:  # type: ignore[type-arg]
        """Return a copy of obj with source-org-specific fields removed."""
        return {key: value for key, value in obj.items() if key not in self.STRIP_FIELDS}  # Filter out id, org_id, etc.

    def _execute_import(self, bundle: dict, dry_run: bool) -> list:  # type: ignore[type-arg]
        """Import objects in dependency order, skipping conflicts."""
        results: list = []  # type: ignore[type-arg] # Accumulates import results for final report
        sorted_types = sorted(self.CONFIG_TYPES, key=lambda ct: ct["import_order"])  # Dependency order
        action_label = "[DRY RUN] " if dry_run else ""  # Prefix for user output in dry-run mode
        print(f"\n  {action_label}Importing configuration objects...")  # User feedback

        for config_type in sorted_types:  # Process each type in dependency order
            objects = bundle.get(config_type["key"], [])  # Get objects of this type from bundle
            if not objects:  # Skip empty types
                continue  # Skip it.
            self._import_type_batch(config_type, objects, dry_run, results)  # Import the batch
        return results  # Return all results for report

    def _import_type_batch(  # type: ignore[type-arg]
        self,
        config_type: dict,
        objects: list,
        dry_run: bool,
        results: list,
    ) -> None:
        """Import a batch of objects for a single config type."""
        display = config_type["display_name"]  # Human-readable type name for output
        label = "[DRY RUN] " if dry_run else ""  # Prefix for dry-run output
        print(f"\n    {label}{display} ({len(objects)} objects):")  # User feedback with count
        logging.info("Importing %s %s objects (dry_run=%s)", len(objects), display, dry_run)  # Log batch start

        for obj in objects:  # Process each object in the batch
            self._process_import_object(config_type, obj, dry_run, results)  # Delegate per-object logic

    def _clean_and_remap(self, obj: dict, type_key: str) -> dict:  # type: ignore[type-arg]
        """Strip source-org-specific fields from an import object then remap its cross-references."""
        cleaned = self._strip_source_fields(obj)  # Remove source-org-specific fields.
        cleaned = self._remap_object_references(cleaned, type_key)  # Remap cross-references to dest IDs.
        return cleaned  # Return the cleaned + remapped object.

    def _process_import_object(  # type: ignore[type-arg]
        self, config_type: dict, obj: dict, dry_run: bool, results: list
    ) -> None:
        """Process a single object: conflict check, remap, create or skip."""
        obj_name = obj.get("name", "unnamed")  # Extract object name for logging and reporting
        source_id = obj.get("id", "")  # Capture source org ID for remapping
        type_key = config_type["key"]  # Bundle key for this config type
        label = "[DRY RUN] " if dry_run else ""  # Prefix for output
        conflict = self._detect_conflicts(obj, type_key)  # Check for name/subnet conflicts
        if conflict:  # Conflict found -- skip and record
            self._record_conflict(type_key, obj_name, source_id, conflict, results)  # Record the conflict.
            return  # Skip it.
        cleaned = self._clean_and_remap(obj, type_key)  # Strip + remap.
        if dry_run:  # Preview mode -- don't make API calls
            print(f"      {label}Would import: {obj_name}")  # Show what would happen
            results.append({"type": type_key, "name": obj_name, "status": "would_import"})  # Record for report
            return  # Abort.
        self._create_and_record(config_type, cleaned, obj_name, source_id, results)  # Create via API

    def _record_conflict(  # type: ignore[type-arg]
        self,
        type_key: str,
        name: str,
        source_id: str,
        conflict: dict,
        results: list,
    ) -> None:
        """Record a skipped object due to conflict and update remap table."""
        print(f"      SKIP: {name} - {conflict['detail']}")  # User feedback showing skip reason
        results.append({"type": type_key, "name": name, "status": "skipped", "reason": conflict["detail"]})  # Record
        existing_id = conflict.get("existing_id")  # Get destination org's matching object ID
        if existing_id and source_id:  # Both IDs available -- record mapping for cross-references
            self._build_remap_entry(source_id, existing_id)  # Remap to existing id.

    def _create_and_record(  # type: ignore[type-arg]
        self,
        config_type: dict,
        cleaned: dict,
        name: str,
        source_id: str,
        results: list,
    ) -> None:
        """Create a single object via the API and record the result."""
        type_key = config_type["key"]  # Bundle key for logging
        logging.info("Creating %s '%s' in destination org", type_key, name)  # Log before API call
        try:
            create_fn = self._resolve_api_fn(config_type["create_fn"])  # Resolve create endpoint
            response = create_fn(self.session, self.org_id, body=cleaned)  # Call Mist API to create
            new_id = self._extract_created_id(response)  # Extract new object ID from response
            if source_id and new_id:  # Record mapping for downstream cross-references
                self._build_remap_entry(source_id, new_id)  # Remap to new id.
            print(f"      OK: {name}")  # User feedback showing success
            logging.debug("Created %s '%s' with ID %s", type_key, name, new_id[:8] if new_id else "n/a")  # Log result
            results.append({"type": type_key, "name": name, "status": "imported"})  # Record success
        except Exception as error:  # Catch API errors without stopping the entire import
            print(f"      FAIL: {name} - {error}")  # User feedback showing failure
            logging.error("Failed to create %s '%s': %s", type_key, name, error)  # Log error with context
            results.append({"type": type_key, "name": name, "status": "failed", "reason": str(error)})  # Record failure

    def _extract_created_id(self, response) -> str:  # Extract the created id.
        """Extract the new object ID from a create API response."""
        if hasattr(response, "data") and isinstance(response.data, dict):  # Check response has data dict
            return response.data.get("id", "")  # type: ignore[no-any-return] # Return the new ID
        return ""  # Fallback when response format is unexpected

    # ------------------------------------------------------------------
    # Import report
    # ------------------------------------------------------------------

    def _display_import_report(self, results: list) -> None:  # type: ignore[type-arg]
        """Print a summary report of the import operation."""
        buckets = self._partition_import_results(results)  # Group result rows by status into 4 buckets
        print("\n  " + "=" * 55)  # Report header separator
        print("  IMPORT REPORT")  # Report title
        print("  " + "=" * 55)  # Report header separator
        self._print_import_report_sections(buckets)  # Render every non-empty bucket as a section
        self._print_report_totals(
            buckets["imported"], buckets["skipped"], buckets["failed"], buckets["would_import"]
        )  # Render the grand totals row

    def _partition_import_results(self, results: list) -> dict:  # type: ignore[type-arg]
        """Group import results by status into a stable four-bucket dict."""
        logging.debug("Partitioning %s import results into status buckets", len(results))  # Trace start
        buckets: dict = {"imported": [], "skipped": [], "failed": [], "would_import": []}  # Stable section ordering
        for result in results:  # Walk every result row
            bucket = buckets.get(result.get("status"))  # Look up the matching bucket (None for unknown statuses)
            if bucket is not None:  # Drop any result whose status is not one of the four expected values
                bucket.append(result)  # Collect into its bucket
        logging.debug(
            "Partitioned buckets: imported=%s skipped=%s failed=%s would_import=%s",
            len(buckets["imported"]),
            len(buckets["skipped"]),
            len(buckets["failed"]),
            len(buckets["would_import"]),
        )  # Trace bucket sizes for diagnostics
        return buckets  # Return the populated buckets

    def _print_import_report_sections(self, buckets: dict) -> None:  # type: ignore[type-arg]
        """Render every non-empty bucket as a labeled report section in stable display order."""
        section_order = [
            ("would_import", "WOULD IMPORT (dry-run)"),  # Dry-run preview comes first
            ("imported", "IMPORTED"),  # Then successful imports
            ("skipped", "SKIPPED (conflicts)"),  # Then conflict-skips
            ("failed", "FAILED"),  # Then failures last
        ]
        for bucket_key, section_title in section_order:  # Walk sections in display order
            items = buckets[bucket_key]  # Read this bucket's items
            if items:  # Suppress empty sections to keep the report compact
                self._print_report_section(section_title, items)  # Print the populated section

    def _print_report_section(self, title: str, items: list) -> None:  # type: ignore[type-arg]
        """Print a single section of the import report."""
        print(f"\n  {title} ({len(items)}):")  # Section header with count
        for item in items:  # Iterate each result in this section
            reason = item.get("reason", "")  # Get conflict/error reason if present
            suffix = f" -- {reason}" if reason else ""  # Append reason as suffix
            print(f"    {item['type']:<20} {item['name']:<30}{suffix}")  # Aligned columns

    def _print_report_totals(  # type: ignore[type-arg]
        self, imported: list, skipped: list, failed: list, would_import: list
    ) -> None:
        """Print the totals row of the import report."""
        print("\n  " + "-" * 55)  # Separator before totals
        total = len(imported) + len(skipped) + len(failed) + len(would_import)  # Grand total
        print(f"  Total: {total} objects processed")  # Total line
        if would_import:  # Show dry-run count
            print(f"    Would import: {len(would_import)}")  # Show would-import count.
        if imported:  # Show imported count
            print(f"    Imported:     {len(imported)}")  # Show imported count.
        if skipped:  # Show skipped count
            print(f"    Skipped:      {len(skipped)}")  # Show skipped count.
        if failed:  # Show failed count
            print(f"    Failed:       {len(failed)}")  # Show failed count.

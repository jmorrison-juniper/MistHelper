"""BulkRadiusWLANConfigManager -- Menu 122 bulk RADIUS timer configuration.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 15).
Scans org WLANs, filters those using RADIUS/RadSec auth, and offers bulk
update of auth_servers_timeout, auth_servers_retries, and fast_dot1x_timers.
All non-static methods keep instance state (org_id, WLAN buckets, change
records); callers continue to reach the class through the
``MistHelper.BulkRadiusWLANConfigManager`` re-export alias.

FR-008 remediation applied during extraction:
- ``_add_index`` / ``_parse_one_part`` / ``_parse_selection`` now use
  ``list[int]`` instead of bare ``list`` (removes 5x ``# type: ignore[type-arg]``).
- ``_already_configured`` wraps its comparison result in ``bool(...)`` so mypy
  no longer sees ``Any`` leaking through ``dict.get`` (removes ``no-any-return``).
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.9+.

import csv  # WHY: audit-trail CSV writer.
import importlib  # WHY: lazy MistHelper import to reach live helper classes without circular load.
import logging  # WHY: structured lifecycle + audit logging.
import os  # WHY: env-var config + path helpers for the audit CSV.
import time  # WHY: inter-call sleep to respect API rate limits.
from datetime import datetime  # WHY: timestamps for scan snapshot + audit trail rows.
from typing import Any  # WHY: raw WLAN rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for listOrgWlans + updateOrgWlan endpoints.


class BulkRadiusWLANConfigManager:
    """
    Bulk configuration of RADIUS authentication timer settings for org WLANs.

    Scans all WLANs in the organization, identifies those using RADIUS/RadSec
    authentication, and allows bulk update of auth_servers_timeout,
    auth_servers_retries, and fast_dot1x_timers settings.

    Target values are read from .env with sensible defaults:
    - RADIUS_AUTH_TIMEOUT: 3 seconds
    - RADIUS_AUTH_RETRIES: 2
    - RADIUS_FAST_DOT1X: true

    SECURITY: Destructive operation - requires explicit 'APPLY' confirmation.
    Generates CSV audit trail in data/ directory.

    Usage:
        BulkRadiusWLANConfigManager().manage()
        BulkRadiusWLANConfigManager().manage(dry_run=True)
    """

    CANCEL_KEYWORDS = {"q", "quit", "cancel", "back"}

    # Stable column order for the per-scan WLAN snapshot (see _export_scan_snapshot).
    # The *_present flags reveal whether a value is real (key was in the API record)
    # or merely the default the compliance check assumes when the key is absent.
    _SNAPSHOT_FIELDS = [
        "scan_timestamp",
        "org_id",
        "ssid",
        "wlan_id",
        "compliance_status",
        "inheritance_level",
        "inheritance_source",
        "auth_type",
        "num_auth_servers",
        "radsec_enabled",
        "auth_servers_timeout",
        "auth_servers_timeout_present",
        "auth_servers_retries",
        "auth_servers_retries_present",
        "fast_dot1x_timers",
        "fast_dot1x_timers_present",
        "target_timeout",
        "target_retries",
        "target_fast_dot1x",
        "enabled",
    ]

    def __init__(self) -> None:
        """Initialize manager and load configuration from .env."""
        self.org_id: str = ""
        self.all_wlans: list[dict[str, Any]] = []
        self.radius_wlans: list[dict[str, Any]] = []
        self.compliant_wlans: list[dict[str, Any]] = []
        self.selected_wlans: list[dict[str, Any]] = []
        self.change_records: list[dict[str, Any]] = []
        self.dry_run: bool = False
        self._load_env_config()

    def _load_env_config(self) -> None:
        """Load RADIUS configuration from .env with defaults."""
        self.target_timeout = int(os.getenv("RADIUS_AUTH_TIMEOUT", "3"))
        self.target_retries = int(os.getenv("RADIUS_AUTH_RETRIES", "2"))
        self.target_fast_dot1x = os.getenv("RADIUS_FAST_DOT1X", "true").lower() == "true"
        logging.debug(
            "Loaded RADIUS config: timeout=%s, retries=%s, fast_dot1x=%s",
            self.target_timeout,
            self.target_retries,
            self.target_fast_dot1x,
        )

    def _display_config(self) -> None:
        """Display loaded .env configuration values at startup."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of IsDebugMode helper.
        print("\n" + "=" * 70)
        print("  BULK RADIUS WLAN CONFIGURATION (Menu 122)")
        print("=" * 70)
        if self.dry_run:
            print("\n  >> DRY-RUN MODE: No changes will be made <<")
        if mh.IsDebugMode.check():  # Emit banner when the operator opted into verbose debug logs
            print("\n  >> DEBUG MODE: Verbose logging enabled <<")
        print("\n  Target configuration loaded from .env:")
        print(f"    - auth_servers_timeout: {self.target_timeout} seconds")
        print(f"    - auth_servers_retries: {self.target_retries}")
        print(f"    - fast_dot1x_timers:    {self.target_fast_dot1x}")
        print("")

    # _safe_input removed per issue #431 (ARCH-DELEGATE). Callers now use
    # InputUtils.safe_input(prompt, context="bulk_radius_config") directly.

    def _get_org_id(self) -> bool:
        """Get organization ID from cache or prompt."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils helper.
        self.org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()
        if not self.org_id:
            logging.error("Could not determine organization ID")
            print("\n[!] Unable to determine organization ID. Exiting.")
            return False
        return True

    def _scan_org_wlans(self) -> bool:
        """Fetch all WLANs in the organization using listOrgWlans API."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession + IsDebugMode.
        print("[*] Scanning organization for WLANs...")
        logging.info("Fetching org WLANs for org_id: %s", self.org_id)
        try:
            response = mistapi.api.v1.orgs.wlans.listOrgWlans(mh.apisession, self.org_id)
            if response.status_code != 200:
                logging.error("Failed to fetch org WLANs: HTTP %s", response.status_code)
                print(f"\n[!] Failed to fetch WLANs: HTTP {response.status_code}")
                return False
            self.all_wlans = response.data
            if mh.IsDebugMode.check():  # Dump per-WLAN payload only when debug mode is enabled
                logging.debug("API response data (%s WLANs): %s", len(self.all_wlans), self.all_wlans)
            logging.info("Found %s total WLANs in organization", len(self.all_wlans))
            print(f"[+] Found {len(self.all_wlans)} total WLANs in organization")
            return True
        except Exception as e:
            logging.error("Exception fetching org WLANs: %s", e)
            print(f"\n[!] Error fetching WLANs: {e}")
            return False

    def _uses_radius_auth(self, wlan: dict[str, Any]) -> bool:
        """Check if WLAN uses RADIUS or RadSec authentication."""
        has_auth_servers = bool(wlan.get("auth_servers"))
        radsec_config = wlan.get("radsec", {})
        has_radsec = radsec_config.get("enabled", False) if isinstance(radsec_config, dict) else False
        auth_config = wlan.get("auth", {})
        uses_eap = auth_config.get("type", "") in ["eap", "eap192"] if isinstance(auth_config, dict) else False
        return has_auth_servers or has_radsec or uses_eap

    def _already_configured(self, wlan: dict[str, Any]) -> bool:
        """Check if WLAN already has the target settings."""
        current_timeout = wlan.get("auth_servers_timeout", 5)
        current_retries = wlan.get("auth_servers_retries", 2)
        current_fast = wlan.get("fast_dot1x_timers", False)
        # WHY: wrap in bool() so mypy sees a proper bool rather than Any propagated from dict.get.
        return bool(
            current_timeout == self.target_timeout
            and current_retries == self.target_retries
            and current_fast == self.target_fast_dot1x
        )

    def _log_radius_wlan_classification(self, status: str, wlan: dict[str, Any]) -> None:
        """Emit debug log explaining why a WLAN landed in compliant vs needs-update bucket."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of IsDebugMode helper.
        if not mh.IsDebugMode.check():  # Only emit when verbose mode is on
            return
        logging.debug(
            "%s: %s - timeout=%s, retries=%s, fast=%s",
            status,
            wlan.get("ssid"),
            wlan.get("auth_servers_timeout", 5),
            wlan.get("auth_servers_retries", 2),
            wlan.get("fast_dot1x_timers", False),
        )

    def _classify_radius_wlan(self, wlan: dict[str, Any]) -> None:
        """Tag a single RADIUS WLAN as COMPLIANT or NEEDS_UPDATE and push it into the matching bucket."""
        if self._already_configured(wlan):  # Has all three timer fields at target values
            wlan["_compliance_status"] = "COMPLIANT"  # Tag for downstream display
            self.compliant_wlans.append(wlan)  # Add to the compliant bucket
            self._log_radius_wlan_classification("COMPLIANT", wlan)  # Verbose audit trail
        else:  # Needs at least one timer field adjusted
            wlan["_compliance_status"] = "NEEDS_UPDATE"  # Tag for downstream display
            self.radius_wlans.append(wlan)  # Add to the needs-update bucket
            self._log_radius_wlan_classification("NEEDS_UPDATE", wlan)  # Verbose audit trail

    def _filter_radius_wlans(self) -> None:
        """Filter WLANs to RADIUS-enabled, separating compliant from non-compliant."""
        self.radius_wlans = []  # Bucket for WLANs that need timer changes
        self.compliant_wlans = []  # Bucket for WLANs already at target timers
        for wlan in self.all_wlans:  # Walk every WLAN discovered in this run
            if not self._uses_radius_auth(wlan):  # Skip non-RADIUS WLANs entirely
                continue
            self._add_inheritance_metadata(wlan)  # Decorate with template/org inheritance info
            self._classify_radius_wlan(wlan)  # Sort into compliant vs needs-update bucket
        total_radius = len(self.radius_wlans) + len(self.compliant_wlans)  # Combined RADIUS WLAN count
        logging.info(
            "Found %s RADIUS WLANs: %s needing config, %s compliant",
            total_radius,
            len(self.radius_wlans),
            len(self.compliant_wlans),
        )
        print(
            f"[+] Found {total_radius} RADIUS WLANs ({len(self.radius_wlans)} needing configuration, {len(self.compliant_wlans)} already compliant)"  # noqa: E501
        )

    def _add_inheritance_metadata(self, wlan: dict[str, Any]) -> None:
        """Add inheritance level metadata to WLAN for display."""
        template_id = wlan.get("template_id")
        if template_id:
            wlan["_inheritance_level"] = "template"
            wlan["_inheritance_source"] = f"Template ID: {template_id[:8]}..."
        else:
            wlan["_inheritance_level"] = "org"
            wlan["_inheritance_source"] = "Org-Level WLAN"

    def _build_combined_wlan_rows(self) -> list[tuple[dict[str, Any], int | None]]:
        """Pair WLANs with display indices: selectable WLANs get 1-based numbers; compliant ones get None."""
        display_index = 1  # Running 1-based number for selectable WLANs
        combined: list[tuple[dict[str, Any], int | None]] = []  # Output pairs
        for wlan in self.radius_wlans:  # Selectable WLANs that need configuration
            combined.append((wlan, display_index))  # Give each a selectable index
            display_index += 1  # Advance the index
        for wlan in self.compliant_wlans:  # Already-compliant WLANs (not selectable)
            combined.append((wlan, None))  # No index for compliant rows
        combined.sort(key=lambda item: item[0].get("ssid", "").lower())  # Sort by SSID
        return combined  # Ready for rendering

    def _print_wlan_row(self, wlan: dict[str, Any], idx: int | None) -> None:
        """Print one WLAN row in the compliance table, with COMPLIANT tag suffix where applicable."""
        ssid = wlan.get("ssid", "Unknown")  # The WLAN's SSID (fallback if missing)
        is_compliant = wlan.get("_compliance_status") == "COMPLIANT"  # Whether already at target
        suffix = " (COMPLIANT)" if is_compliant else ""  # Tag for clarity
        ssid_display = (ssid[:13] + suffix) if is_compliant else ssid[:24]  # Truncate to column width
        level = wlan.get("_inheritance_level", "unknown")[:11]  # Inheritance level
        timeout = wlan.get("auth_servers_timeout", 5)  # Current timeout value
        retries = wlan.get("auth_servers_retries", 2)  # Current retry value
        fast = "Yes" if wlan.get("fast_dot1x_timers", False) else "No"  # Fast-timer flag
        idx_str = str(idx) if idx is not None else "--"  # Index, or '--' for non-selectable
        print(f"  {idx_str:<4} {ssid_display:<25} {level:<12} {timeout:<8} {retries:<8} {fast:<6}")

    def _display_wlans(self) -> None:
        """Display unified table of all RADIUS WLANs with compliance markers."""
        print("\n" + "-" * 70)  # Top border
        print("  RADIUS-ENABLED WLANs")  # Title
        print("-" * 70)  # Separator
        print(f"  {'#':<4} {'SSID':<25} {'Level':<12} {'Timeout':<8} {'Retries':<8} {'Fast':<6}")  # Headers
        print("-" * 70)  # Separator
        combined = self._build_combined_wlan_rows()  # Sorted (wlan, idx) pairs
        for wlan, idx in combined:  # Render each row
            self._print_wlan_row(wlan, idx)
        print("-" * 70)  # Bottom border
        total = len(self.radius_wlans) + len(self.compliant_wlans)  # Total across both buckets
        print(
            f"  Total: {total} RADIUS WLANs ({len(self.radius_wlans)} selectable, {len(self.compliant_wlans)} compliant)"  # noqa: E501
        )
        print("")  # Blank spacer line

    @staticmethod
    def _is_range_part(part: str) -> bool:
        """Return True when a selection piece is a range like '3-7' (not a leading-minus negative)."""
        return "-" in part and not part.startswith("-")  # A dash that isn't a leading minus marks a range.

    @staticmethod
    def _parse_range_part(part: str) -> tuple[int, int] | None:
        """Parse a 'start-end' range piece into 0-based (start, end), swapping reversed bounds; None if invalid."""
        try:  # Non-numeric range pieces are skipped.
            range_parts = part.split("-")  # Split into start and end.
            if len(range_parts) != 2:  # Only a well-formed two-ended range is valid.
                return None  # Malformed range; skip it.
            start = int(range_parts[0].strip()) - 1  # Convert start to 0-based.
            end = int(range_parts[1].strip()) - 1  # Convert end to 0-based.
            if start > end:  # Tolerate reversed ranges like '7-3'.
                start, end = end, start  # Swap so start <= end.
            return start, end  # The inclusive 0-based bounds.
        except ValueError:  # A non-numeric range piece.
            logging.warning("Invalid range format: %s", part)  # Log and skip it.
            return None  # Skip the malformed range.

    @staticmethod
    def _parse_single_index(part: str) -> int | None:
        """Parse a single index piece into a 0-based index, or None when it is non-numeric."""
        try:  # Non-numeric single pieces are skipped.
            return int(part) - 1  # Convert to 0-based.
        except ValueError:  # A non-numeric single piece.
            logging.warning("Invalid index: %s", part)  # Log and skip it.
            return None  # Skip the malformed index.

    @staticmethod
    def _add_index(idx: int, max_count: int, selected_indices: list[int]) -> None:
        """Append idx to selected_indices when valid and not already chosen; warn when it is out of range."""
        if 0 <= idx < max_count and idx not in selected_indices:  # Valid and not already chosen.
            selected_indices.append(idx)  # Add this index.
        elif idx >= max_count:  # Index beyond the list.
            print(f"    [!] Index {idx + 1} out of range (max: {max_count})")  # Warn the user.

    @staticmethod
    def _parse_one_part(part: str, max_count: int, selected_indices: list[int]) -> None:
        """Interpret one selection piece (range or single index) and add its valid indices to selected_indices."""
        if BulkRadiusWLANConfigManager._is_range_part(part):  # This piece is a range like '3-7'.
            rng = BulkRadiusWLANConfigManager._parse_range_part(part)  # Parse the inclusive bounds.
            if rng is not None:  # The range parsed cleanly.
                for idx in range(rng[0], rng[1] + 1):  # Expand the inclusive range.
                    BulkRadiusWLANConfigManager._add_index(idx, max_count, selected_indices)  # Add each valid index.
        else:  # This piece is a single index.
            idx = BulkRadiusWLANConfigManager._parse_single_index(part)  # Parse the single index.
            if idx is not None:  # The index parsed cleanly.
                BulkRadiusWLANConfigManager._add_index(idx, max_count, selected_indices)  # Add the valid index.

    def _parse_selection(self, user_input: str) -> list[int] | None:
        """Parse user selection input into list of 0-based indices, or None for cancel."""
        cleaned = user_input.strip().lower()  # Normalize the input for keyword comparison.
        if cleaned in self.CANCEL_KEYWORDS:  # The user asked to cancel.
            return None  # Signal cancellation to the caller.
        if cleaned == "all":  # The user selected every WLAN.
            return list(range(len(self.radius_wlans)))  # Return all 0-based indices.
        selected_indices: list[int] = []  # Accumulate the parsed 0-based indices.
        max_count = len(self.radius_wlans)  # Upper bound for valid indices.
        normalized = (
            user_input.lower().replace(" through ", "-").replace("through", "-")
        )  # Treat 'through' like a range dash.
        parts = [part.strip() for part in normalized.split(",")]  # Split comma-separated selections into pieces.
        for part in parts:  # Interpret each selection piece.
            BulkRadiusWLANConfigManager._parse_one_part(part, max_count, selected_indices)  # Add its valid indices.
        selected_indices.sort()  # Present the chosen indices in ascending order.
        return selected_indices  # Hand the parsed indices back to the caller.

    def _display_preview(self) -> None:
        """Display preview of changes that will be applied."""
        print("\n" + "=" * 70)  # Top border of the preview banner
        print("  PREVIEW: CHANGES TO BE APPLIED")  # Banner title
        print("=" * 70)  # Bottom border of the preview banner
        print("\n  Target settings:")  # Sub-header for the target values
        print(f"    auth_servers_timeout: {self.target_timeout} seconds")  # The timeout that will be applied
        print(f"    auth_servers_retries: {self.target_retries}")  # The retry count that will be applied
        print(f"    fast_dot1x_timers:    {self.target_fast_dot1x}")  # The fast-timer flag that will be applied
        print(f"\n  WLANs to be updated ({len(self.selected_wlans)} total):")  # How many WLANs will change
        print("-" * 70)  # Separator before the per-WLAN diff
        for wlan in self.selected_wlans:  # Show a before/after for each selected WLAN
            ssid = wlan.get("ssid", "Unknown")  # The WLAN's SSID
            curr_timeout = wlan.get("auth_servers_timeout", 5)  # Its current timeout
            curr_retries = wlan.get("auth_servers_retries", 2)  # Its current retry count
            curr_fast = wlan.get("fast_dot1x_timers", False)  # Its current fast-timer flag
            print(f"\n  SSID: {ssid}")  # Label this WLAN's diff block
            print(f"    timeout: {curr_timeout} -> {self.target_timeout}")  # Old -> new timeout
            print(f"    retries: {curr_retries} -> {self.target_retries}")  # Old -> new retries
            print(f"    fast_dot1x: {curr_fast} -> {self.target_fast_dot1x}")  # Old -> new fast-timer flag
        print("\n" + "-" * 70)  # Closing separator under the preview

    def _apply_changes(self) -> None:
        """Apply configuration changes to selected WLANs with rate limiting."""
        mode_label = "DRY-RUN: Simulating" if self.dry_run else "Applying"  # Verb depends on dry-run.
        print(f"\n[*] {mode_label} configuration to {len(self.selected_wlans)} WLANs...")  # Announce.
        success_count = 0  # WLANs updated successfully.
        fail_count = 0  # WLANs that failed.
        for idx, wlan in enumerate(self.selected_wlans, 1):  # Process each (1-based for display).
            if self._update_one_wlan(idx, wlan):  # Dispatch the per-WLAN update.
                success_count += 1  # Count success.
            else:
                fail_count += 1  # Count failure.
            time.sleep(0.3)  # Brief pause between writes to respect API rate limits.
        result_label = "DRY-RUN complete" if self.dry_run else "Update complete"  # Final verb.
        print(f"\n[+] {result_label}: {success_count} successful, {fail_count} failed")  # Show totals.
        logging.info("%s: %s success, %s failed", result_label, success_count, fail_count)  # Log totals.

    def _update_one_wlan(self, idx: int, wlan: dict[str, Any]) -> bool:
        """Update (or simulate) a single WLAN. Return True on success/simulated success."""
        wlan_id = wlan.get("id")  # Unique WLAN ID needed for the update call.
        ssid = wlan.get("ssid", "Unknown")  # SSID for user-facing messages.
        if not wlan_id:  # Defensive: the WLAN record lacks an ID.
            logging.error("Missing WLAN ID for %s", ssid)  # Log the missing identifier.
            self._record_change(wlan, "failed", "Missing WLAN ID")  # Audit the failure.
            return False  # Treat as failure.
        payload = self._build_radius_payload()  # Build the timer-only update body.
        print(f"  [{idx}/{len(self.selected_wlans)}] Updating {ssid}...", end=" ")  # Progress line.
        logging.info(  # Log before the update, noting dry-run vs real.
            "%s org WLAN %s (%s) with payload: %s",
            "DRY-RUN: Would update" if self.dry_run else "Updating",
            wlan_id,
            ssid,
            payload,
        )
        if self.dry_run:  # Dry-run path: simulate without an API call.
            return self._simulate_wlan_update(wlan, payload)  # Simulated success.
        return self._call_wlan_update_api(wlan, payload)  # Real API path.

    def _build_radius_payload(self) -> dict[str, Any]:
        """Build the timer-only update body for the configured RADIUS targets."""
        return {  # Build the timer-only update body for this WLAN.
            "auth_servers_timeout": self.target_timeout,  # Target timeout to apply.
            "auth_servers_retries": self.target_retries,  # Target retry count to apply.
            "fast_dot1x_timers": self.target_fast_dot1x,  # Target fast-timer flag to apply.
        }

    def _simulate_wlan_update(self, wlan: dict[str, Any], payload: dict[str, Any]) -> bool:
        """Record a dry-run change and print the simulated outcome. Always returns True."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of IsDebugMode helper.
        ssid = wlan.get("ssid", "Unknown")  # SSID for user-facing messages.
        print("DRY-RUN (would update)")  # Show that no real change was made.
        self._record_change(wlan, "DRY-RUN", "")  # Record the simulated change.
        if mh.IsDebugMode.check():  # Only dump payload when debugging.
            logging.debug("DRY-RUN payload for %s: %s", ssid, payload)  # Log the would-be payload.
        return True  # Count the simulation as a success.

    def _call_wlan_update_api(self, wlan: dict[str, Any], payload: dict[str, Any]) -> bool:
        """Call updateOrgWlan, log + audit the outcome, return True iff HTTP 200."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession + IsDebugMode.
        wlan_id = wlan["id"]  # ID was validated upstream.
        ssid = wlan.get("ssid", "Unknown")  # SSID for user-facing messages.
        try:
            response = mistapi.api.v1.orgs.wlans.updateOrgWlan(
                mh.apisession, self.org_id, wlan_id, payload
            )  # Push the update.
            if response.status_code == 200:  # Update succeeded.
                print("OK")  # Complete the progress line with success.
                self._record_change(wlan, "success", "")  # Audit the successful change.
                if mh.IsDebugMode.check():  # Debug-only response dump.
                    logging.debug("API response for %s: %s", ssid, response.data)  # Log body.
                return True  # Real success.
            print(f"FAILED (HTTP {response.status_code})")  # Complete the progress line with failure.
            self._record_change(wlan, "failed", f"HTTP {response.status_code}")  # Audit failure.
            logging.error("Failed to update %s: HTTP %s", ssid, response.status_code)  # Log HTTP error.
            return False  # API failure.
        except Exception as e:  # Update call raised.
            print(f"ERROR ({e})")  # Complete the progress line with the error.
            self._record_change(wlan, "failed", str(e))  # Audit the exception.
            logging.error("Exception updating %s: %s", ssid, e)  # Log the exception detail.
            return False  # Exception failure.

    def _record_change(self, wlan: dict[str, Any], status: str, error_msg: str) -> None:
        """Record a change for the audit trail."""
        record = {  # Build a flat audit record capturing before/after values
            "timestamp": datetime.now().isoformat(),  # When the change was recorded
            "wlan_id": wlan.get("id", ""),  # The WLAN's ID
            "ssid": wlan.get("ssid", ""),  # The WLAN's SSID
            "site_name": wlan.get("_inheritance_source", "Org-Level"),  # Where the WLAN is defined
            "inheritance_level": wlan.get("_inheritance_level", "unknown"),  # Site/template/org level
            "before_timeout": wlan.get("auth_servers_timeout", 5),  # Timeout before the change
            "after_timeout": self.target_timeout,  # Timeout after the change
            "before_retries": wlan.get("auth_servers_retries", 2),  # Retries before the change
            "after_retries": self.target_retries,  # Retries after the change
            "before_fast_dot1x": wlan.get("fast_dot1x_timers", False),  # Fast-timer flag before the change
            "after_fast_dot1x": self.target_fast_dot1x,  # Fast-timer flag after the change
            "status": status,  # Outcome (success/failed/DRY-RUN)
            "error_message": error_msg,  # Any error detail for failures
        }
        self.change_records.append(record)  # Append to the audit trail for later CSV export

    def _export_scan_snapshot(self) -> None:
        """Persist every pulled RADIUS WLAN's settings to disk so they can be examined after the run."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter helper.
        all_radius = self.radius_wlans + self.compliant_wlans  # Every RADIUS WLAN discovered this scan
        if not all_radius:  # Nothing was pulled -> nothing to snapshot
            logging.debug("No RADIUS WLANs to snapshot; skipping scan export")  # Trace the empty case
            return  # No snapshot to write
        logging.info("Exporting scan snapshot for %s RADIUS WLAN(s)", len(all_radius))  # Before-action log
        scan_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Human-readable scan time stamped on each row
        rows = [self._build_snapshot_row(wlan, scan_timestamp) for wlan in all_radius]  # Flatten each WLAN to a row
        file_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Compact stamp for a unique, non-overwriting filename
        filename = f"RadiusWLANScanSnapshot_{file_stamp}.csv"  # Snapshot filename (DataExporter drops .csv for SQLite)
        ok = mh.DataExporter.write_with_format_selection(  # Multi-backend write: CSV by default, SQLite if configured
            rows,
            filename,
            fieldnames=self._SNAPSHOT_FIELDS,
        )
        if ok:  # The export succeeded
            print(f"[+] Scan snapshot of {len(rows)} RADIUS WLAN(s) saved to data/{filename}")  # Show the location
            logging.info("Scan snapshot written to data/%s (%s rows)", filename, len(rows))  # After-action log
        else:  # The export failed (permissions, disk, or backend error)
            print("[!] Failed to save scan snapshot (see log for details)")  # Inform the operator of the failure
            logging.error("Failed to write RADIUS WLAN scan snapshot to %s", filename)  # Log the failure

    def _build_snapshot_row(self, wlan: dict[str, Any], scan_timestamp: str) -> dict[str, Any]:
        """Flatten one RADIUS WLAN into an examinable snapshot row with value-presence flags."""
        radsec, auth = wlan.get("radsec", {}), wlan.get("auth", {})  # Sub-configs (each may be missing/non-dict)
        return {  # One flat, examinable row per RADIUS WLAN
            "scan_timestamp": scan_timestamp,  # When this scan ran (identical for every row in the run)
            "org_id": self.org_id,  # Organization the WLANs were pulled from
            "ssid": wlan.get("ssid", ""),  # Human-readable network name
            "wlan_id": wlan.get("id", ""),  # Stable WLAN UUID
            "compliance_status": wlan.get("_compliance_status", ""),  # COMPLIANT/NEEDS_UPDATE from the filter step
            "inheritance_level": wlan.get("_inheritance_level", ""),  # template vs org (from _add_inheritance_metadata)
            "inheritance_source": wlan.get("_inheritance_source", ""),  # Where the WLAN is defined
            "auth_type": auth.get("type", "") if isinstance(auth, dict) else "",  # eap/eap192/psk/etc.
            "num_auth_servers": len(wlan.get("auth_servers", []) or []),  # How many RADIUS servers are configured
            "radsec_enabled": radsec.get("enabled", False) if isinstance(radsec, dict) else False,  # RadSec on/off
            "auth_servers_timeout": wlan.get("auth_servers_timeout", 5),  # Actual value (5 = the check's own default)
            "auth_servers_timeout_present": "auth_servers_timeout" in wlan,  # True => real value; False => defaulted
            "auth_servers_retries": wlan.get("auth_servers_retries", 2),  # Actual value (2 = the check's own default)
            "auth_servers_retries_present": "auth_servers_retries" in wlan,  # True => real value; False => defaulted
            "fast_dot1x_timers": wlan.get("fast_dot1x_timers", False),  # Actual value (False = the check's own default)
            "fast_dot1x_timers_present": "fast_dot1x_timers" in wlan,  # True => real value; False => defaulted
            "target_timeout": self.target_timeout,  # Target timeout this run compared against
            "target_retries": self.target_retries,  # Target retries this run compared against
            "target_fast_dot1x": self.target_fast_dot1x,  # Target fast-timer flag this run compared against
            "enabled": wlan.get("enabled", ""),  # Whether the WLAN itself is enabled
        }

    _AUDIT_TRAIL_FIELDNAMES = [
        "timestamp",
        "wlan_id",
        "ssid",
        "site_name",
        "inheritance_level",
        "before_timeout",
        "after_timeout",
        "before_retries",
        "after_retries",
        "before_fast_dot1x",
        "after_fast_dot1x",
        "status",
        "error_message",
    ]

    def _write_audit_csv(self, filepath: str) -> None:
        """Write self.change_records to a CSV at filepath; log success or surface failure to the user."""
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self._AUDIT_TRAIL_FIELDNAMES)
                writer.writeheader()  # Write the column header row
                writer.writerows(self.change_records)  # Write every recorded change
            print(f"\n[+] Audit trail exported to: {filepath}")
            logging.info("Audit trail exported to %s with %s records", filepath, len(self.change_records))
        except Exception as e:  # Writing the CSV failed (permissions, disk, etc.)
            print(f"\n[!] Failed to export audit trail: {e}")
            logging.error("Failed to export audit trail: %s", e)

    def _export_audit_trail(self) -> None:
        """Export change records to CSV in data/ directory."""
        if not self.change_records:  # No changes were recorded this run
            print("[*] No changes to export.")
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Unique filename timestamp
        prefix = "DRYRUN_" if self.dry_run else ""  # Mark dry-run exports distinctly
        filename = f"{prefix}RadiusWLANBulkConfig_{timestamp}.csv"  # Composed audit CSV name
        filepath = os.path.join("data", filename)  # Place under data/ (cross-platform)
        os.makedirs("data", exist_ok=True)  # Ensure target directory exists
        self._write_audit_csv(filepath)  # Open + write + report

    def manage(self, dry_run: bool = False) -> None:
        """Main entry point - orchestrates the bulk RADIUS WLAN configuration."""
        self.dry_run = dry_run  # Remember whether this run only simulates changes.
        logging.info("Starting Bulk RADIUS WLAN Configuration (Menu 122)")  # Announce workflow start.
        if not self._scan_and_prepare():  # Display + org + scan + filter + snapshot + empty guard.
            return  # Abort on any precondition failure.
        if self._handle_all_compliant():  # Every RADIUS WLAN already at target settings.
            return  # No-op completion.
        self._display_wlans()  # Show the selectable WLAN table.
        selected_indices = self._prompt_and_parse_selection()  # Prompt + parse.
        if selected_indices is None:  # Cancelled or invalid selection.
            return  # Abort the workflow.
        self.selected_wlans = [self.radius_wlans[i] for i in selected_indices]  # Resolve indices.
        self._confirm_and_apply()  # Preview + APPLY confirm + apply + audit + completion.

    def _scan_and_prepare(self) -> bool:
        """Display config, fetch + filter WLANs, persist snapshot. Return False on failure."""
        self._display_config()  # Show the target settings the user configured.
        if not self._get_org_id():  # Resolve the org ID; abort if unavailable.
            return False  # Cannot proceed without an org.
        if not self._scan_org_wlans():  # Fetch all org WLANs; abort on failure.
            return False  # Cannot proceed without WLAN data.
        self._filter_radius_wlans()  # Split WLANs into selectable vs already-compliant buckets.
        self._export_scan_snapshot()  # Persist the pulled settings for post-run examination.
        total_radius = len(self.radius_wlans) + len(self.compliant_wlans)  # Total RADIUS WLANs.
        if total_radius == 0:  # No RADIUS WLANs exist in the org.
            print("\n[*] No RADIUS-enabled WLANs found in the organization.")  # Inform the user.
            logging.info("No RADIUS WLANs found in organization")  # Log the empty result.
            return False  # Nothing to do.
        return True  # Ready to proceed to the apply phase.

    def _handle_all_compliant(self) -> bool:
        """Return True (and short-circuit manage) when every RADIUS WLAN already complies."""
        if not self.radius_wlans and self.compliant_wlans:  # Every RADIUS WLAN already meets target.
            self._display_wlans()  # Still show the table for transparency.
            print("[*] All RADIUS WLANs are already at target settings. No changes needed.")  # Inform.
            logging.info("All RADIUS WLANs already compliant - no changes needed")  # Log the no-op.
            return True  # Caller should short-circuit.
        return False  # Need to proceed to selection.

    def _prompt_and_parse_selection(self) -> list[int] | None:
        """Prompt for WLAN selection, parse it, return indices or None on cancel/invalid."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InputUtils helper.
        print("  Enter selection (e.g., 'all', '1', '1,3,5', '1-5') or 'q' to cancel:")  # Syntax.
        # Issue #431: inlined self._safe_input -> canonical InputUtils.safe_input.
        selection = mh.InputUtils.safe_input("  > ", context="wlan_selection")  # Prompt.
        if not selection.strip():  # User entered nothing.
            print("\n[*] No selection made. Exiting.")  # Inform the user.
            return None  # Abort.
        selected_indices = self._parse_selection(selection)  # Parse into 0-based indices.
        if selected_indices is None:  # User explicitly cancelled (e.g., 'q').
            print("\n[*] Operation cancelled by user.")  # Acknowledge.
            logging.info("Menu 122 cancelled by user at selection prompt")  # Log cancellation.
            return None  # Abort.
        if not selected_indices:  # Selection parsed to no valid indices.
            print("\n[!] Invalid selection. Please use valid indices.")  # Reject input.
            return None  # Abort.
        return selected_indices  # Return the resolved indices.

    def _confirm_and_apply(self) -> None:
        """Show preview, require APPLY confirmation, then apply changes + audit + completion."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InputUtils helper.
        self._display_preview()  # Show a before/after preview of the pending changes.
        print("\n  WARNING: This will modify WLAN authentication settings.")  # Warn before the destructive step.
        print("  Type 'APPLY' to proceed, or anything else to cancel.")  # Explain the confirmation.
        # Issue #431: inlined self._safe_input -> canonical InputUtils.safe_input.
        confirm = mh.InputUtils.safe_input("  > ", context="apply_confirm")  # Read confirmation.
        if confirm.strip() != "APPLY":  # Not the exact confirmation word.
            print("\n[*] Operation cancelled by user.")  # Acknowledge cancellation.
            logging.info("Bulk RADIUS config cancelled by user")  # Log cancellation.
            return  # Abort without making changes.
        self._apply_changes()  # Apply (or simulate) the timer changes.
        self._export_audit_trail()  # Write the before/after audit trail to CSV.
        print("\n[+] Bulk RADIUS WLAN configuration completed.")  # Tell the user it finished.
        logging.info("Bulk RADIUS WLAN Configuration completed successfully")  # Log completion.

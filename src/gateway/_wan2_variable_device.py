"""Device-migration cluster for wan2_variable.

Holds the scan-and-migrate flow for device-level port overrides: site
scoping, per-site scan, per-device inspection, and the per-device
migration itself (fast or sequential). Extracted so the parent module
stays under STRUCT-LENGTH while the busiest helper
(``_migrate_single_device_override``) stays under CC/length/block
budgets after its internal split.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref parent type

import logging  # WHY: audit-log every scan/migration outcome
import threading  # WHY: Semaphore signature for worker callable
import traceback  # WHY: capture stack trace on unexpected mistapi failures
from typing import Any  # WHY: mistapi responses/configs are heterogenous dicts

from tqdm import tqdm  # WHY: progress bars over site and device lists

from ._wan2_variable_cluster import _ClusterBase  # WHY: parent-proxy pattern shared with peers


class _Wan2VariableDevice(_ClusterBase):
    """Device scan + per-device migration helpers."""

    def _find_devices_needing_migration(
        self,
        sites: list[dict[str, str]],
        migrated_template_ids: set[str],
    ) -> list[dict[str, Any]]:
        """Find devices with port overrides matching the search pattern."""
        import mistapi  # pylint: disable=import-outside-toplevel  # WHY: lazy import breaks cycle

        print("\n  Step 7: Migrating device-level port overrides" f" ({self._operation_mode.upper()} mode)...")
        self._print_device_migration_header()  # WHY: mode banner
        affected, site_to_template = self._build_affected_site_set(sites, migrated_template_ids)
        logging.info(
            "Device migration scope: %s sites using migrated templates (out of %s total sites)",
            len(affected),
            len(sites),
        )  # WHY: audit scope
        print(f"  >> Optimization: Checking only {len(affected)}" f" affected sites (not all {len(sites)} sites)")
        if not affected:  # WHY: nothing to scan when zero affected sites
            return []  # WHY: skip API calls entirely
        print("  >> Fetching gateway device configurations" f" for {len(affected)} affected sites...")
        return self._scan_site_devices(affected, site_to_template, mistapi)  # WHY: hand off to scanner

    def _print_device_migration_header(self) -> None:
        """Print device migration mode header."""
        search = self._search_pattern  # WHY: alias for readability
        replace = self._replacement_value  # WHY: alias for readability
        if self._operation_mode == "apply":  # WHY: apply-mode copy
            print("  !? CRITICAL: Preserving static IP" " configurations on devices")  # WHY: highlight preservation
            print(f"  !? Renaming device overrides from" f" '{search}' to '{replace}'")  # WHY: describe edit
            return  # WHY: skip revert branch
        print("  !? REVERT: Updating device overrides" " to match template reversion")  # WHY: revert-mode copy
        print(f"  !? Renaming device overrides from" f" '{search}' to '{replace}'")  # WHY: describe edit

    def _build_affected_site_set(
        self,
        sites: list[dict[str, str]],
        migrated_template_ids: set[str],
    ) -> tuple[set[str], dict[str, str]]:
        """Build set of site IDs using migrated templates."""
        site_to_template: dict[str, str] = {}  # WHY: sid -> template mapping for post-scan lookup
        affected: set[str] = set()  # WHY: candidate site IDs to scan
        for site in sites:  # WHY: iterate every kept site
            self._classify_site_row(site, migrated_template_ids, affected, site_to_template)  # WHY: extracted
        return affected, site_to_template  # WHY: caller uses both structures

    def _classify_site_row(
        self,
        site: dict[str, str],
        migrated_template_ids: set[str],
        affected: set[str],
        site_to_template: dict[str, str],
    ) -> None:
        """Classify a single site row, updating affected/site_to_template."""
        name = site.get("name", "").strip()  # WHY: name feeds exclude prefix check
        if self._is_excluded_site_name(name):  # WHY: SECURITY excludes handled via helper
            logging.debug("Skipping excluded site %s from device migration scope", name)  # WHY: trace skip
            return  # WHY: drop excluded site entirely
        sid = site.get("id", "").strip()  # WHY: sid required for API scan
        tid = site.get("gatewaytemplate_id", "").strip()  # WHY: tid required for template correlation
        if not (sid and tid):  # WHY: skip rows lacking either identifier
            return  # WHY: nothing usable
        site_to_template[sid] = tid  # WHY: always retain mapping for post-scan template lookup
        if tid in migrated_template_ids:  # WHY: only scan sites tied to migrated templates
            affected.add(sid)  # WHY: enqueue for scan

    def _is_excluded_site_name(self, name: str) -> bool:
        """Return True when the site's name matches the SECURITY exclude prefix."""
        prefix = self._site_exclude_prefix  # WHY: cache attr for both branches
        return bool(prefix) and name.startswith(prefix)  # WHY: single expression keeps caller CC low

    def _scan_site_devices(
        self,
        affected_site_ids: set[str],
        site_to_template: dict[str, str],
        mistapi_mod: Any,
    ) -> list[dict[str, Any]]:
        """Scan affected sites for devices with port overrides."""
        devices: list[dict[str, Any]] = []  # WHY: accumulator for return
        for sid in tqdm(
            affected_site_ids,
            desc="Checking site devices",
            unit="site",
        ):  # WHY: progress bar over sites
            self._scan_one_site(sid, site_to_template, mistapi_mod, devices)  # WHY: extracted for CC budget
        logging.info(
            "Found %s devices with %s overrides needing migration",
            len(devices),
            self._search_pattern,
        )  # WHY: audit result
        return devices  # WHY: caller feeds to migration orchestrator

    def _scan_one_site(
        self,
        sid: str,
        site_to_template: dict[str, str],
        mistapi_mod: Any,
        devices: list[dict[str, Any]],
    ) -> None:
        """Scan devices at a single site, appending matches to devices."""
        try:  # WHY: mistapi calls raise on transport failure
            resp = mistapi_mod.api.v1.sites.devices.listSiteDevices(self._apisession, sid, type="gateway")
            site_devices = mistapi_mod.get_all(response=resp, mist_session=self._apisession)  # WHY: pagination
            for device in site_devices:  # WHY: iterate every returned gateway
                match = self._check_device_override(device, sid, site_to_template, mistapi_mod)  # WHY: filter
                if match:  # WHY: keep only devices carrying overrides
                    devices.append(match)  # WHY: accumulate into caller's list
        except Exception as exc:  # pylint: disable=broad-exception-caught  # WHY: mistapi failures vary
            logging.error("Error checking devices at site %s: %s", sid, exc)  # WHY: audit failure

    def _check_device_override(
        self,
        device: dict[str, Any],
        site_id: str,
        site_to_template: dict[str, str],
        mistapi_mod: Any,
    ) -> dict[str, Any] | None:
        """Check if a single device has port overrides matching pattern."""
        did = device.get("id", "").strip()  # WHY: device id used for follow-up API call
        name = device.get("name", "").strip()  # WHY: friendly name for logs
        search = self._search_pattern  # WHY: alias for readability
        resp = mistapi_mod.api.v1.sites.devices.getSiteDevice(self._apisession, site_id, did)  # WHY: get override
        config = getattr(resp, "data", {})  # WHY: guard missing .data attr
        port_config = config.get("port_config", {})  # WHY: overrides live here
        if not isinstance(port_config, dict):  # WHY: skip malformed rows
            return None  # WHY: nothing to migrate
        if not any(k == search or k.startswith(f"{search}.") for k in port_config):  # WHY: fast filter
            return None  # WHY: device does not carry an override on the search pattern
        logging.info("Found device '%s' with %s override at site %s", name, search, site_id)  # WHY: audit
        return {
            "site_id": site_id,  # WHY: needed for update API path
            "device_id": did,  # WHY: needed for update API path
            "device_name": name,  # WHY: report label
            "template_id": site_to_template.get(site_id),  # WHY: cross-ref for reports
        }

    def _migrate_single_device_override(
        self,
        device_info: dict[str, Any],
        connection_semaphore: threading.Semaphore,
    ) -> dict[str, Any]:
        """Migrate port override keys on a single device."""
        import mistapi  # pylint: disable=import-outside-toplevel  # WHY: lazy import breaks cycle

        result = self._init_device_result(device_info)  # WHY: extracted for length budget
        name = device_info["device_name"]  # WHY: reused in error branches
        try:  # WHY: mistapi calls raise on transport failure
            with connection_semaphore:  # WHY: honor caller's parallelism budget
                self._perform_device_migration(device_info, result, mistapi)  # WHY: extracted for CC budget
        except Exception as exc:  # pylint: disable=broad-exception-caught  # WHY: mistapi failures vary
            result["status"] = "ERROR"  # WHY: report path
            result["error"] = str(exc)  # WHY: capture failure text
            logging.error("Error migrating device %s: %s", name, exc)  # WHY: audit trail
            logging.error(traceback.format_exc())  # WHY: preserve stack
        return result  # WHY: caller aggregates results

    @staticmethod
    def _init_device_result(device_info: dict[str, Any]) -> dict[str, Any]:
        """Build the initial per-device result dict with default fields."""
        return {
            "device_name": device_info["device_name"],  # WHY: report label
            "device_id": device_info["device_id"],  # WHY: cross-ref for reports
            "site_id": device_info["site_id"],  # WHY: cross-ref for reports
            "template_id": device_info["template_id"],  # WHY: cross-ref for reports
            "status": "",  # WHY: populated by branches below
            "ports_migrated": "",  # WHY: filled on success
            "error": "",  # WHY: filled on failure/skip
        }

    def _perform_device_migration(
        self,
        device_info: dict[str, Any],
        result: dict[str, Any],
        mistapi_mod: Any,
    ) -> None:
        """Fetch, rename, and commit a device's port overrides."""
        name = device_info["device_name"]  # WHY: reused in logs
        port_config = self._fetch_device_port_config(device_info, mistapi_mod, result)  # WHY: extracted
        if port_config is None:  # WHY: helper set status/error on invalid config
            return  # WHY: nothing further to do
        ports_renamed = self._rename_port_keys(
            port_config,
            self._search_pattern,
            self._replacement_value,
            name,
        )  # WHY: shared rename helper
        if not ports_renamed:  # WHY: pattern absent at commit time
            result["status"] = "SKIPPED"  # WHY: report path
            result["error"] = f"No {self._search_pattern} ports found in config"  # WHY: explain
            return  # WHY: no API mutation needed
        result["ports_migrated"] = "; ".join(ports_renamed)  # WHY: summary for report
        self._commit_device_or_dry_run(device_info, port_config, result, mistapi_mod)  # WHY: extracted

    def _fetch_device_port_config(
        self,
        device_info: dict[str, Any],
        mistapi_mod: Any,
        result: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Return the port_config dict or None (setting result on failure)."""
        did = device_info["device_id"]  # WHY: reused across trace + API call
        sid = device_info["site_id"]  # WHY: needed for API path
        name = device_info["device_name"]  # WHY: log label
        logging.debug("Fetching device config for %s (%s)", name, did)  # WHY: trace call site
        resp = mistapi_mod.api.v1.sites.devices.getSiteDevice(self._apisession, sid, did)
        config = getattr(resp, "data", {})  # WHY: guard missing .data attr
        if not isinstance(config, dict):  # WHY: skip malformed device rows
            result["status"] = "SKIPPED"  # WHY: report path
            result["error"] = "Invalid device config structure"  # WHY: explain
            return None  # WHY: caller returns immediately
        port_config = config.get("port_config", {})  # WHY: overrides live here
        if not isinstance(port_config, dict):  # WHY: skip malformed port_config shapes
            result["status"] = "SKIPPED"  # WHY: report path
            result["error"] = "No port_config found"  # WHY: explain
            return None  # WHY: caller returns immediately
        result["_config"] = config  # WHY: retain original config for commit path
        return port_config  # WHY: caller mutates in place

    def _commit_device_or_dry_run(
        self,
        device_info: dict[str, Any],
        port_config: dict[str, Any],
        result: dict[str, Any],
        mistapi_mod: Any,
    ) -> None:
        """Send API update or mark dry-run; populates result status/error."""
        config = result.pop("_config", {})  # WHY: retrieved earlier; drop from public payload
        config["port_config"] = port_config  # WHY: ensure mutation persists in outer config
        name = device_info["device_name"]  # WHY: reused in both branches
        if self._dry_run:  # WHY: dry-run bypasses API mutation
            result["status"] = "DRY-RUN"  # WHY: report path
            logging.info(
                "DRY-RUN: Would migrate port overrides for device %s: %s", name, result["ports_migrated"]
            )  # WHY: audit
            return  # WHY: no API call in dry-run
        logging.debug("Updating device %s via API", name)  # WHY: trace call site
        update_resp = mistapi_mod.api.v1.sites.devices.updateSiteDevice(
            self._apisession, device_info["site_id"], device_info["device_id"], body=config
        )  # WHY: single mistapi update call
        self._record_device_update_status(update_resp, name, result)  # WHY: extracted for length budget

    @staticmethod
    def _record_device_update_status(update_resp: Any, name: str, result: dict[str, Any]) -> None:
        """Populate result status/error from a device update response."""
        if update_resp.status_code == 200:  # WHY: 200 == success per Mist API
            result["status"] = "SUCCESS"  # WHY: report path
            logging.info("Successfully migrated port overrides for device %s", name)  # WHY: audit success
            return  # WHY: no error data to record
        result["status"] = "FAILED"  # WHY: any non-200 is a failure
        result["error"] = f"API returned status" f" {update_resp.status_code}"  # WHY: preserve original text
        logging.error("Failed to update device %s: status %s", name, update_resp.status_code)  # WHY: audit

    @staticmethod
    def _rename_port_keys(
        port_config: dict[str, Any],
        search: str,
        replacement: str,
        device_name: str,
    ) -> list[str]:
        """Rename port_config keys matching the search pattern in-place."""
        renamed: list[str] = []  # WHY: accumulator for return
        for key in list(port_config.keys()):  # WHY: snapshot keys; mutating dict during iteration
            new_key = _match_port_rename(key, search, replacement)  # WHY: module helper for CC budget
            if new_key is None:  # WHY: key does not match
                continue  # WHY: leave untouched
            port_config[new_key] = port_config.pop(key)  # WHY: rename preserves value
            renamed.append(f"{key}->{new_key}")  # WHY: diff line for report
            logging.debug("Device %s: Renamed %s to %s", device_name, key, new_key)  # WHY: trace
        return renamed  # WHY: caller stores on result

    def _run_device_migrations(
        self,
        devices_needing_migration: list[dict[str, Any]],
        fast: bool,
    ) -> list[dict[str, Any]]:
        """Orchestrate device override migrations."""
        if not devices_needing_migration:  # WHY: empty list -> emit no-op message and return
            print("\n  No devices with ge-0/0/1 overrides found" " - no device migrations needed")
            logging.info("No device-level override migrations required")  # WHY: audit no-op
            return []  # WHY: nothing to report
        self._print_device_migration_intro(len(devices_needing_migration))  # WHY: extracted for length
        results = self._dispatch_device_migration(devices_needing_migration, fast)  # WHY: extracted for CC
        self._save_data(results, "GatewayDevice_WAN2_Override_Migration.csv")  # WHY: persist audit report
        self._print_device_migration_summary(results)  # WHY: extracted for length budget
        return results  # WHY: caller feeds to _generate_reports

    @staticmethod
    def _print_device_migration_intro(count: int) -> None:
        """Print the migration-intro block for the found device count."""
        print(f"\n  Found {count} devices with port overrides to migrate")  # WHY: summary
        print("  These devices will have port_config keys renamed" " from 'ge-0/0/1' to '{{wan2_interface}}'")
        print("  This preserves static IP configurations" " after template migration")  # WHY: explain intent

    def _dispatch_device_migration(
        self,
        devices_needing_migration: list[dict[str, Any]],
        fast: bool,
    ) -> list[dict[str, Any]]:
        """Choose fast or sequential migration and return the results list."""
        use_fast = fast and len(devices_needing_migration) > 5 and self._pool_fn is not None  # WHY: gates
        if use_fast:  # WHY: parallel path
            return self._migrate_devices_fast(devices_needing_migration)  # WHY: hand off to fast worker
        return self._migrate_devices_sequential(devices_needing_migration, fast)  # WHY: sequential path

    @staticmethod
    def _print_device_migration_summary(results: list[dict[str, Any]]) -> None:
        """Print the post-migration counters block."""
        success = sum(1 for r in results if r["status"] == "SUCCESS")  # WHY: aggregate for banner
        failed = len(results) - success  # WHY: derive failure count
        print("\n  Device Override Migration Complete!")  # WHY: banner
        print(f"  Devices Processed: {len(results)}")  # WHY: total
        print(f"  Successfully Migrated: {success}")  # WHY: success count
        print(f"  Failed: {failed}")  # WHY: failure count
        print("  Device migration report:" " GatewayDevice_WAN2_Override_Migration.csv")  # WHY: file hint
        logging.info("Device override migration: %s successful, %s failed", success, failed)  # WHY: audit

    def _migrate_devices_fast(self, devices: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Migrate devices using connection pool (fast mode)."""
        assert self._pool_fn is not None  # noqa: S101  # WHY: preserved from original module

        count = len(devices)  # WHY: banner count
        print(f"\n  !? Fast mode enabled: Processing {count}" " devices with connection pooling")
        logging.info("Fast mode: Using connection pool for %s device migrations", count)  # WHY: audit
        results, failed = self._pool_fn(
            work_items=devices,
            worker_function=self._migrate_single_device_override,
            batch_description="devices",
        )  # WHY: hand off to injected pool executor
        if failed:  # WHY: pool reports failed items separately
            logging.warning("Fast mode: %s device migrations failed", len(failed))  # WHY: audit
        return list(results)  # WHY: caller expects a list

    def _migrate_devices_sequential(
        self,
        devices: list[dict[str, Any]],
        fast: bool,
    ) -> list[dict[str, Any]]:
        """Migrate devices sequentially."""
        self._print_sequential_banner(len(devices), fast)  # WHY: extracted for CC/length budget
        logging.info("Sequential mode: Processing %s devices one at a time", len(devices))  # WHY: audit
        dummy_semaphore = threading.Semaphore(1)  # WHY: worker expects semaphore even in seq mode
        results: list[dict[str, Any]] = []  # WHY: accumulator for return
        for device_info in tqdm(
            devices,
            desc="Migrating device overrides",
            unit="device",
        ):  # WHY: progress bar per device
            results.append(self._migrate_single_device_override(device_info, dummy_semaphore))  # WHY: worker
        return results  # WHY: caller aggregates

    @staticmethod
    def _print_sequential_banner(count: int, fast: bool) -> None:
        """Print the sequential-mode intro banner."""
        if fast and count <= 5:  # WHY: fast requested but too few devices
            print(f"\n  Sequential mode: Processing {count}" " devices (fast mode requires >5 devices)")
            return  # WHY: alternate copy branch handled
        print(f"\n  Sequential mode: Processing {count} devices")  # WHY: default banner


def _match_port_rename(key: str, search: str, replacement: str) -> str | None:
    """Return the new key for a port rename, or None when no match."""
    if key == search:  # WHY: exact match on primary key
        return replacement  # WHY: full rename
    if key.startswith(f"{search}."):  # WHY: subinterface variant
        return f"{replacement}{key[len(search) :]}"  # WHY: preserve subinterface suffix
    return None  # WHY: unmatched

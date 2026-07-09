"""APIFetchUtils -- higher-level org/site API fetchers.

Extracted from MistHelper.py during initiative 1014 (Cat E, position 8).
Canonical body lives here; MistHelper.py provides a top-level re-export
alias (``from src.api.api_fetch_utils import APIFetchUtils``) so historical
``MistHelper.APIFetchUtils`` / ``mh.APIFetchUtils`` callers keep working.

Cross-class references (ConfigUtils, APICoreFetchUtils, FilePathUtils,
FastModeSequentialMaxRetries, ConnectionPoolExecutor) and the module-level
``apisession`` are resolved lazily via ``importlib.import_module("MistHelper")``
inside method bodies to keep FR-028 IG-health clean (no top-level MistHelper
import statement).
"""

# pylint: disable=broad-exception-caught

from __future__ import annotations  # WHY: PEP 604 unions in annotations.

import csv  # WHY: parse SiteList.csv for gateway site-name enrichment.
import functools  # WHY: functools.partial for pool worker bindings.
import importlib  # WHY: lazy MistHelper fetch of cross-class refs + apisession.
import logging  # WHY: structured trace + failure reporting.
import threading  # WHY: Semaphore serialization in sequential gateway fetch.
import time  # WHY: exponential backoff sleep between retries.
from typing import Any  # WHY: return-type annotations for dynamic dicts.

import mistapi  # WHY: dotted-path Mist API resolution + pagination helper.
from tqdm import tqdm  # WHY: progress bar for long-running site/device fetches.


class APIFetchUtils:  # Higher-level org/site fetchers.
    """Centralized API fetch utilities.

    Groups all data fetching functions for better code organization.
    All methods are static to avoid unnecessary object instantiation.
    """

    @staticmethod
    def organization_services() -> list[dict[str, Any]]:  # Fetch and flatten org services.
        """Fetch all org-level services via the Mist API; return list of service dicts (empty on error).

        SECURITY: Read-only operation fetching configuration data only.
        """
        try:
            mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils + apisession.
            org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the target org.
            logging.info("Fetching organization services for org_id: %s", org_id)  # Log before the API call.

            # Call the Mist API to get organization services
            response = mistapi.api.v1.orgs.services.listOrgServices(mh.apisession, org_id, limit=1000)  # List services.

            if hasattr(response, "data") and response.data:  # Only proceed with data.
                services_data = response.data  # Unwrap the payload.
                logging.info("Successfully retrieved %s organization services", len(services_data))  # Log the count.
                services_list = APIFetchUtils._normalize_org_services(services_data)  # Normalize to display rows.
                return services_list  # Return normalized services.

            logging.warning("No organization services found or response data is empty")  # Warn on empty response.
            return []  # No services to return.

        except Exception as error:  # Never crash on API failure.
            logging.error("Failed to fetch organization services: %s", error)  # Log the fetch failure.
            return []  # Degrade to empty list.

    @staticmethod
    def _normalize_org_services(services_data: list[Any]) -> list[dict[str, Any]]:  # Flatten raw services to rows
        """Normalize raw org service records into name/type/description rows (keeping the full config)."""
        services_list = []  # Accumulate normalized rows.
        for service in services_data:  # Walk each service.
            if isinstance(service, dict):  # Skip non-dict entries.
                services_list.append(
                    {
                        "name": service.get("name", "unnamed"),  # Default missing names.
                        "type": service.get("type", "custom"),  # Default missing type.
                        "description": service.get("description", ""),  # Default missing description.
                        "full_config": service,  # Keep full config for reference
                    }
                )  # Record the normalized service row
        return services_list  # Return normalized services.

    @staticmethod
    def _fetch_single_site_setting(apisession, site):
        """Fetch one site's settings; tag with id/name; return dict or None on failure."""
        site_id = site.get("id")  # Target site id
        site_name = site.get("name", "Unnamed Site")  # Friendly site label
        try:
            config = mistapi.api.v1.sites.setting.getSiteSetting(apisession, site_id).data  # Fetch site settings
            config["site_id"] = site_id  # Tag with site id
            config["site_name"] = site_name  # Tag with site name
            logging.info("! Fetched config for site: %s (ID: %s)", site_name, site_id)
            return config
        except Exception as error:  # Skip sites that fail
            logging.warning("! Failed to fetch config for %s (ID: %s): %s", site_name, site_id, error)
            return None

    @staticmethod
    def all_site_settings(apisession, org_id, limit=1000):  # Fetch settings for every site.
        """Fetch per-site settings for every site in the org; limit param is unused (kept for back-compat)."""
        del limit  # Kept in signature for back-compat; explicitly discard so linters do not flag it.
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of APICoreFetchUtils + ConfigUtils.
        logging.info("Fetching all site settings...")  # Log before fetching sites
        sites = mh.APICoreFetchUtils.all_sites_with_limit(org_id)  # List all sites first
        all_configs = []  # Collect per-site settings
        for site in tqdm(sites, desc="Sites", unit="site"):  # type: ignore[no-untyped-call]
            if mh.ConfigUtils.check_stop_signal():  # Honor a user stop request
                break  # Stop iterating sites
            config = APIFetchUtils._fetch_single_site_setting(apisession, site)  # One site at a time
            if config is not None:  # Skip failed fetches
                all_configs.append(config)
        logging.info("Fetched settings for %s sites.", len(all_configs))  # Log total fetched
        return all_configs  # Return all site settings

    @staticmethod
    def _gw_load_inventory(apisession, org_id):
        """Fetch the org inventory; return the device list, or None when the fetch fails."""
        logging.info("Fetching org inventory to find gateway devices...")  # Log before the inventory fetch.
        try:  # The inventory fetch is the one hard dependency; isolate its failure.
            response = mistapi.api.v1.orgs.inventory.getOrgInventory(apisession, org_id, limit=1000)  # Fetch inventory.
            return mistapi.get_all(response=response, mist_session=apisession)  # Page through all devices.
        except Exception as error:  # Inventory fetch failed.
            logging.error("! Failed to fetch org inventory: %s", error)  # Log the failure.
            return None  # Signal failure so the caller degrades to an empty result.

    @staticmethod
    def _gw_load_site_names():
        """Load the site id -> name map from SiteList.csv; return an empty map when the file is unavailable."""
        try:  # The site-name CSV is optional enrichment; missing file is non-fatal.
            mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilePathUtils.
            site_list_path = mh.FilePathUtils.get_csv_path("SiteList.csv")  # Locate the site list CSV.
            with open(site_list_path, encoding="utf-8") as file_handle:  # Read site names from CSV.
                reader = csv.DictReader(file_handle)  # Parse CSV rows.
                return {row.get("id"): row.get("name", "Unnamed Site") for row in reader}  # id->name map.
        except Exception as error:  # CSV missing or unreadable.
            logging.warning("! Failed to load SiteList.csv for site names: %s", error)  # Warn names may be unknown.
            return {}  # Degrade to an empty lookup.

    @staticmethod
    def _gw_build_work_items(inventory, site_name_lookup):
        """Build (site_id, device_id, site_name) work items for each gateway device in the inventory."""
        work_items = []  # Accumulate one tuple per gateway needing a config fetch.
        for device in inventory:  # Scan every inventory device.
            if device.get("type") != "gateway":  # Only gateways need configs; skip everything else.
                continue  # Move to the next device.
            site_id = device.get("site_id")  # Owning site id.
            device_id = device.get("id")  # Device id.
            if site_id and device_id:  # Require both ids before queueing a fetch.
                site_name = site_name_lookup.get(site_id, "Unknown")  # Resolve the site name for enrichment.
                work_items.append((site_id, device_id, site_name))  # Queue the fetch.
        return work_items  # Hand the gateway work list back to the caller.

    @staticmethod
    def _gw_fetch_one_config(apisession, work_item, connection_semaphore):
        """Fetch one gateway device's config (site-tagged); return the config dict, or None on empty/failure."""
        work_site_id, work_device_id, work_site_name = work_item  # Unpack the work item.
        with connection_semaphore:  # Limit concurrent connections via the pool semaphore.
            try:  # Isolate per-device failures so one bad device doesn't abort the batch.
                logging.debug("Fetching config for %s (%s)", work_device_id, work_site_name)  # Trace the fetch.
                config_response = mistapi.api.v1.sites.devices.getSiteDevice(  # Call the device API.
                    apisession, work_site_id, work_device_id
                )
                config = getattr(config_response, "data", {})  # Unwrap data safely.
                if config:  # Only keep non-empty configs.
                    config["site_name"] = work_site_name  # Tag with site name for enrichment.
                    config["site_id"] = work_site_id  # Tag with site id for enrichment.
                    logging.debug("! Config fetched for %s", work_device_id)  # Trace success.
                    return config  # Return the enriched config.
                logging.warning("! Empty config for device %s", work_device_id)  # Warn on empty config.
                return None  # Treat empty config as a miss.
            except Exception as inner_error:  # Per-device fetch failed.
                logging.error("! Failed to fetch config for device %s: %s", work_device_id, inner_error)  # Log error.
                return None  # Mark this device failed.

    @staticmethod
    def _gw_retry_one_item(apisession, failed_work_item, connection_semaphore, max_retries):
        """Retry one failed gateway config fetch up to max_retries with backoff; return the config or None."""
        _, failed_device_id, _ = failed_work_item  # Only the device id is needed here (for logging).
        for attempt in range(max_retries + 1):  # Bounded retry loop (initial try plus retries).
            result = APIFetchUtils._gw_fetch_one_config(apisession, failed_work_item, connection_semaphore)  # Try.
            if result is not None:  # Retry succeeded.
                return result  # Hand back the recovered config.
            if attempt < max_retries:  # More attempts remain.
                delay = 0.5 * (1.5**attempt)  # Exponential backoff delay.
                logging.debug(  # Trace the retry/backoff.
                    "Retrying device %s in %.2fs (attempt %s/%s)",
                    failed_device_id,
                    delay,
                    attempt + 2,
                    max_retries + 1,
                )
                time.sleep(delay)  # Back off before retrying.
        logging.warning(  # Warn after exhausting every attempt.
            "! Failed to fetch config for device %s after %s attempts", failed_device_id, max_retries + 1
        )
        return None  # Every attempt failed.

    @staticmethod
    def _gw_retry_configs(apisession, failed_items, connection_semaphore):
        """Retry failed gateway config fetches with bounded exponential backoff; return the recovered configs."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FastModeSequentialMaxRetries.
        max_retries = mh.FastModeSequentialMaxRetries.VALUE  # Configurable retry count from extracted class attribute.
        retry_results = []  # Collect configs recovered on retry.
        for failed_work_item in failed_items:  # Walk every failed item.
            result = APIFetchUtils._gw_retry_one_item(
                apisession, failed_work_item, connection_semaphore, max_retries
            )  # Retry this item with backoff.
            if result is not None:  # The item recovered on retry.
                retry_results.append(result)  # Keep the recovered config.
        return retry_results  # Return the configs recovered during retry.

    @staticmethod
    def _gw_collect_fast(apisession, work_items):
        """Fetch gateway configs concurrently through the connection pool with retry; return the successes."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConnectionPoolExecutor.
        successful_results, _ = mh.ConnectionPoolExecutor.execute(  # Pooled concurrent fetch; discard failures.
            work_items=work_items,
            worker_function=functools.partial(APIFetchUtils._gw_fetch_one_config, apisession),  # Bind apisession.
            batch_description="gateway device configs",
            retry_function=functools.partial(APIFetchUtils._gw_retry_configs, apisession),  # Bind apisession.
        )
        return successful_results  # The pool already retried failures; return the successes.

    @staticmethod
    def _gw_collect_sequential(apisession, work_items):
        """Fetch each gateway config sequentially using a serializing semaphore; return the collected configs."""
        all_device_configs = []  # Accumulate sequential results.
        dummy_semaphore = threading.Semaphore(1)  # Serialize sequential fetches with a single permit.
        for work_item in tqdm(work_items, desc="Fetching Configs", unit="device"):  # type: ignore[no-untyped-call]
            result = APIFetchUtils._gw_fetch_one_config(apisession, work_item, dummy_semaphore)  # Fetch one config.
            if result is not None:  # Keep non-empty results.
                all_device_configs.append(result)  # Collect the config.
        return all_device_configs  # Return the sequentially fetched configs.

    @staticmethod
    def gateway_device_configs(apisession, org_id, fast=False, max_workers=None):
        """Fetch configuration details for all gateway devices in the org inventory.

        When ``fast`` is True the per-device fetches run concurrently through the
        connection pool (with retry); otherwise they run sequentially. Returns a list
        of site-tagged device configuration dicts (empty when the inventory fetch fails).
        ``max_workers`` is accepted for call-site compatibility.
        """
        del max_workers  # Kept in signature for call-site compatibility; explicitly discard so linters do not flag it.
        inventory = APIFetchUtils._gw_load_inventory(apisession, org_id)  # Fetch the org inventory (None on failure).
        if inventory is None:  # The inventory fetch failed outright.
            return []  # Degrade to an empty list.
        logging.info("Found %s total devices in org inventory.", len(inventory))  # Log the device count.
        site_name_lookup = APIFetchUtils._gw_load_site_names()  # Load site id->name enrichment map.
        work_items = APIFetchUtils._gw_build_work_items(inventory, site_name_lookup)  # Build the gateway work list.
        logging.info("Prepared %s gateway device config API calls.", len(work_items))  # Log planned API calls.
        if fast:  # Fast mode uses the connection pool with retry.
            all_device_configs = APIFetchUtils._gw_collect_fast(apisession, work_items)  # Pooled concurrent path.
        else:  # Sequential processing for non-fast mode.
            all_device_configs = APIFetchUtils._gw_collect_sequential(apisession, work_items)  # Serial fetch path.
        all_device_configs = [config for config in all_device_configs if config is not None]  # Drop any failures.
        logging.info("! Completed fetching %s gateway device configs.", len(all_device_configs))  # Log completion.
        return all_device_configs  # Return the gateway configs.

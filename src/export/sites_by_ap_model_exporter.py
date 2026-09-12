"""SitesByAPModelExporter -- sites-by-AP-model CSV export for menu 88.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 28).
Fetches org AP inventory, prompts operator to choose a model, then writes
one row per site listing address parts, AP count, and AP MAC list. All
methods are static -- no state is kept on the class. Callers continue to
reach it through the ``MistHelper.SitesByAPModelExporter`` re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for return types.

import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured trace for export lifecycle events.
import re  # WHY: slugify AP model names into filesystem-safe filenames.
from typing import Any  # WHY: raw device / site dicts from mistapi are duck-typed.


class SitesByAPModelExporter:
    """Sites by AP Model Exporter.

    Exports a CSV listing every site that contains APs of a user-selected model,
    including the site address, AP count, and individual AP MAC addresses.
    Site detail lookups use the mistapi pagination engine, which internally
    parallelises multi-page fetches across all available CPU cores.
    """

    @staticmethod
    def _get_ap_models(org_id: str) -> tuple[list[dict], list[str]]:  # type: ignore[type-arg]
        """Return (ap_inventory, sorted_unique_models) for the organisation."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of APICoreFetchUtils facade.
        inventory = mh.APICoreFetchUtils.all_inventory_with_limit(org_id)  # Fetch org inventory.
        aps = [d for d in inventory if d.get("type") == "ap"]  # Keep only APs.
        models = sorted({d.get("model", "") for d in aps if d.get("model")})  # Distinct sorted models.
        return aps, models  # Return APs and models.

    @staticmethod
    def _print_model_options(models: list[str], aps: list[dict]) -> None:  # type: ignore[type-arg]
        """Print numbered list of AP models with per-model device count."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("\nAvailable AP models:")
        for idx, model in enumerate(models, 1):  # List each model
            count = sum(1 for d in aps if d.get("model") == model)  # APs of this model
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logging.info("  %3d. %s (%s APs)", idx, model, count)

    @staticmethod
    def _resolve_model_choice(choice: str, models: list[str]) -> str | None:
        """Parse the user's 1-based model selection string and return the chosen model or None on bad input."""
        try:
            selected = int(choice.strip()) - 1  # Convert to 0-based index
            return models[selected] if 0 <= selected < len(models) else None  # Bounds check
        except (ValueError, IndexError):
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logging.info("! Invalid selection.")
            return None

    @staticmethod
    def _prompt_model_selection(models: list[str], aps: list[dict]) -> str | None:  # type: ignore[type-arg]
        """Prompt user to select an AP model from the numbered list."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InputUtils facade.
        SitesByAPModelExporter._print_model_options(models, aps)  # Render numbered options
        choice = mh.InputUtils.safe_input(  # Read the choice
            "\nSelect model number (or Enter to cancel): ",
            context="ap_model_selection",
        )
        if not choice.strip():  # Empty input cancels
            return None
        return SitesByAPModelExporter._resolve_model_choice(choice, models)  # Parse + bounds-check

    @staticmethod
    def _split_address(address: str) -> tuple[str, str, str, str, str]:  # Split an address string.
        """Split a full address string into street, city, state, zip, country."""
        try:
            parts = address.split(", ")  # Split on commas.
            street = parts[0]  # Street part.
            city = parts[1]  # City part.
            state_zip = parts[2].split()  # State/zip part.
            state = state_zip[0]  # State token.
            zip_code = state_zip[1]  # Zip token.
            country = parts[3]  # Country part.
            return street, city, state, zip_code, country  # Return the parts.
        except Exception as exception:  # Parse failed.
            logging.debug("Failed to split address '%s': %s", address, exception)  # Trace the failure.
            return address, "", "", "", ""  # Return address as street.

    @staticmethod
    def _build_export_rows(
        aps: list[dict],  # type: ignore[type-arg]
        model: str,
        site_map: dict[str, dict],  # type: ignore[type-arg]
    ) -> list[dict]:  # type: ignore[type-arg]
        """Group APs by site and build one CSV row per matching site."""
        grouped = SitesByAPModelExporter._group_aps_by_site(aps, model)  # APs of this model, grouped by site_id
        ordered = sorted(grouped.items(), key=lambda x: site_map.get(x[0], {}).get("name", ""))  # Sort by site name
        return [
            SitesByAPModelExporter._build_site_row(site_id, devices, model, site_map)  # One row per matching site
            for site_id, devices in ordered
        ]  # CSV rows, one per site

    @staticmethod
    def _build_site_row(
        site_id: str,
        devices: list[dict],  # type: ignore[type-arg]
        model: str,
        site_map: dict[str, dict],  # type: ignore[type-arg]
    ) -> dict:  # type: ignore[type-arg]
        """Build a single CSV row for one site's APs of a given model (count, address parts, MAC list)."""
        site = site_map.get(site_id, {})  # Look up the site.
        street, city, state, zip_code, country = SitesByAPModelExporter._split_address(site.get("address", ""))  # Addr
        return {
            "site_id": site_id,
            "site_name": site.get("name", ""),
            "ap_model": model,
            "ap_count": len(devices),
            "address": street,
            "city": city,
            "state": state,
            "zip": zip_code,
            "country": country,
            "ap_macs": ", ".join(d.get("mac", "") for d in devices),
        }

    @staticmethod
    def _group_aps_by_site(aps: list[dict], model: str) -> dict[str, list[dict]]:  # type: ignore[type-arg]  # Group APs
        """Group APs matching the given model by their site_id (APs without a model match or site_id are skipped)."""
        grouped: dict[str, list[dict]] = {}  # type: ignore[type-arg]  # site_id -> matching AP devices
        for device in aps:  # Walk APs.
            if device.get("model") == model and device.get("site_id"):  # Match model with a site.
                grouped.setdefault(device["site_id"], []).append(device)  # Group by site.
        return grouped  # The site_id -> devices map

    @staticmethod
    def _finalize_ap_model_export(rows: list, model: str) -> None:  # type: ignore[type-arg]
        """Slugify model, build per-model filename, write CSV, and log + print summary."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter facade.
        safe_model = re.sub(r"[^a-zA-Z0-9_-]", "_", model)  # Slugify the model.
        filename = f"SitesByAPModel_{safe_model}.csv"  # Build the CSV name.
        mh.DataExporter.write_with_format_selection(rows, filename, api_function_name="getSitesByAPModel")  # Persist.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("\n[OK] Exported %s sites with %s APs to %s", len(rows), model, filename)
        logging.info("Exported %s sites with AP model %s", len(rows), model)  # Log the export.

    @staticmethod
    def _build_site_map(all_sites: list) -> dict[str, Any]:  # type: ignore[type-arg]
        """Return a ``{site_id: site}`` map from a sites listing, skipping entries without an ``id``."""
        return {site["id"]: site for site in all_sites if site.get("id")}  # Index sites for O(1) lookup by id

    @staticmethod
    def export_sites_by_ap_model() -> None:  # Export sites by AP model.
        """Export CSV of sites containing APs of a selected model with site address info."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils + APICoreFetchUtils facades.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("Export Sites by AP Model:")
        logging.info("Starting export of sites by AP model...")  # Trace start
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("! Fetching AP inventory from organization...")
        aps, models = SitesByAPModelExporter._get_ap_models(org_id)  # Fetch APs and models
        if not models:  # No models in inventory
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logging.info("! No APs found in organization inventory.")
            return
        model = SitesByAPModelExporter._prompt_model_selection(models, aps)  # Prompt operator for a model
        if not model:  # Operator skipped
            return
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("! Fetching site details for sites with %s APs...", model)
        all_sites = mh.APICoreFetchUtils.all_sites_with_limit(org_id)  # List all sites
        site_map = SitesByAPModelExporter._build_site_map(all_sites)  # Index sites by id for row lookup
        rows = SitesByAPModelExporter._build_export_rows(aps, model, site_map)  # Build export rows
        if not rows:  # No rows match the chosen model
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logging.info("! No sites found with %s APs.", model)
            return
        SitesByAPModelExporter._finalize_ap_model_export(rows, model)  # Slug + filename + write + log

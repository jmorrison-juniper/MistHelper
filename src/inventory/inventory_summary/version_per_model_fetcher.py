"""Fetches firmware version distribution per device model with VC/HA awareness."""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref annotations

import logging  # WHY: structured log emission for orchestrator + fetcher tracing

from src.inventory import org_device_inventory_summary as _parent  # Parent module exposes apisession / mistapi globals


class VersionPerModelFetcher:  # WHY: namespace for the decomposed version-per-model expansion helpers
    """Decomposed replacement for the original `_fetch_versions_per_model` helper."""

    @staticmethod
    def _expand_model_rows(  # Walks model_rows and produces per-model expansion via helper
        model_rows: list[dict],  # WHY: the callee stopped needing the org id, so this level drops it too
        switch_records: list[dict],
        gateway_records: list[dict],
    ) -> list[dict]:
        """Expand non-AP model rows into per-version count rows (APs handled in bulk elsewhere)."""
        all_rows: list[dict] = []  # Accumulator for every (device_type, model, version) row
        for model_row in model_rows:  # Iterate the precomputed top-level model counts
            if model_row.get("device_type") == "ap":  # APs are expanded in bulk from inventory
                continue  # Skip here so AP counts are not produced twice
            rows = VersionPerModelFetcher._rows_for_model(
                model_row,  # WHY: model_row now sits first, because the org id left the signature
                switch_records,
                gateway_records,
            )  # Delegate per-row expansion to a small helper
            all_rows.extend(rows)  # Append helper output verbatim. Helper returns [] on skip
        return all_rows  # WHY: caller merges these into the final row set

    @staticmethod
    def _sort_row_key(row: dict) -> tuple:  # WHY: pluck the three sort keys for stable ordering
        """Stable sort key for output rows: (device_type, model, -count)."""
        return (  # WHY: negative count sorts high-count entries first per legacy behavior
            row.get("device_type", ""),
            row.get("model", ""),
            -int(row.get("count", 0)),
        )

    @staticmethod
    def _append_bulk_rows(  # Adds AP + unassigned rows in one place
        target_org_id: str,
        all_rows: list[dict],
        ap_records: list[dict] | None,
        unassigned_records: list[dict] | None,
    ) -> None:
        """Append AP + unassigned-stock rows to ``all_rows`` (in-place)."""
        all_rows.extend(
            VersionPerModelFetcher._ap_rows(target_org_id, ap_records)
        )  # APs from inventory so never-connected + unassigned APs are included
        all_rows.extend(
            VersionPerModelFetcher._unassigned_rows(target_org_id, unassigned_records)
        )  # Unassigned switch stock surfaces under the "unassigned" version column

    @staticmethod
    def fetch(  # Public orchestrator -- composes pre-fetches + expansions + bulk AP/unassigned rows
        target_org_id: str,
        model_rows: list[dict],
        unassigned_records: list[dict] | None = None,
        ap_records: list[dict] | None = None,
    ) -> list[dict]:
        """Return per-model version count rows across AP / switch / gateway types."""
        logging.info(
            "Fetching version distribution per model, org=%s", target_org_id
        )  # Trace orchestrator entry for ops visibility
        # WHY: single switch/gateway fetch shared across all model rows
        switch_records = VersionPerModelFetcher._prefetch_switches(target_org_id, model_rows)  # switches once
        gateway_records = VersionPerModelFetcher._prefetch_gateways(target_org_id, model_rows)  # gateways once
        all_rows = VersionPerModelFetcher._expand_model_rows(
            model_rows, switch_records, gateway_records
        )  # Per-model expansion (non-AP). The org id stops at this orchestrator
        VersionPerModelFetcher._append_bulk_rows(
            target_org_id, all_rows, ap_records, unassigned_records
        )  # Adds AP + unassigned rows in-place
        all_rows.sort(key=VersionPerModelFetcher._sort_row_key)  # type/model/-count order
        logging.debug(
            "Total version-per-model rows after fetch and sort: %d", len(all_rows)
        )  # Record final row count for diagnostics
        return all_rows  # WHY: sorted, fully expanded rows returned to summary orchestrator

    @staticmethod
    def _ap_rows(target_org_id: str, ap_records: list[dict] | None) -> list[dict]:  # WHY: bulk AP rows
        """Build per-model AP rows from full inventory, bucketing version into the three real states."""
        # APs are expanded from getOrgInventory (the portal "Claim APs" source) rather than the count
        # API, so claimed-but-never-connected APs (no firmware version) surface under an "unknown"
        # version bucket and unassigned APs under an "unassigned" bucket instead of vanishing entirely.
        if ap_records is None:  # WHY: fallback fetch preserves standalone usage
            ap_records = _parent.OrgDeviceInventorySummaryCore._fetch_ap_inventory(target_org_id)  # AP fetch
        logging.info("Building AP version-per-model rows from %d records", len(ap_records))  # Log before aggregation
        counts: dict[tuple[str, str], int] = {}  # Running total per (model, version_bucket)
        for record in ap_records:  # Walk every claimed AP exactly once
            model_name = record.get("model") or "unknown"  # Keep real model for the pivot's Model column
            version = _parent.OrgDeviceInventorySummaryCore._ap_inventory_bucket(  # Shared 3-way bucket rule
                record, "version"
            )
            key = (model_name, version)  # Compose grouping key
            counts[key] = counts.get(key, 0) + 1  # One inventory record == one physical AP
        rows = [  # Materialize into standard row shape; device_type is always "ap" here
            {"device_type": "ap", "model": model_name, "version": version, "count": count}
            for (model_name, version), count in counts.items()
        ]
        logging.debug("AP version-per-model produced %d rows", len(rows))  # Record outcome
        return rows  # WHY: caller extends the aggregate row set with these AP entries

    @staticmethod
    def _accumulate_unassigned(  # Folds unassigned-inventory records into (type, model) counts
        records: list[dict],
    ) -> dict[tuple[str, str], int]:
        """Return ``{(device_type, model): count}`` for the given unassigned-inventory records."""
        counts: dict[tuple[str, str], int] = {}  # Running total per (device_type, model)
        for record in records:  # Walk each unassigned inventory record once
            device_type = record.get("type") or "unknown"  # Inventory record carries its own ap/switch type
            model_name = record.get("model") or "unknown"  # Keep real model so it lines up with assigned rows
            key = (device_type, model_name)  # Compose grouping key
            counts[key] = counts.get(key, 0) + 1  # Each unassigned record is one physical device
        return counts  # WHY: caller materializes rows from these aggregate counts

    @staticmethod
    def _unassigned_rows(  # Builds rows for unassigned switch stock
        target_org_id: str, unassigned_records: list[dict] | None
    ) -> list[dict]:
        """Build per-model rows for unassigned switch stock, bucketed under version 'unassigned'."""
        # These switches are claimed but not assigned to a site, so the assigned-only search API
        # never returns them. We surface them under a dedicated "unassigned" version so the pivot
        # renderer emits a clearly labelled column instead of silently undercounting. (Unassigned
        # APs are handled by _ap_rows, which counts all APs straight from inventory.)
        if unassigned_records is None:  # WHY: fallback fetch preserves standalone usage
            unassigned_records = _parent.OrgDeviceInventorySummaryCore._fetch_unassigned_inventory(target_org_id)
        logging.info("Building unassigned version-per-model rows from %d records", len(unassigned_records))  # log
        counts = VersionPerModelFetcher._accumulate_unassigned(unassigned_records)  # Delegate fold
        rows = [  # Materialize into standard rows with the synthetic "unassigned" version bucket
            {
                "device_type": device_type,
                "model": model_name,
                "version": "unassigned",
                "count": count,
            }
            for (device_type, model_name), count in counts.items()
        ]
        logging.debug("Unassigned version-per-model produced %d rows", len(rows))  # Record outcome
        return rows  # WHY: caller extends the aggregate row set with these unassigned entries

    @staticmethod
    def _prefetch_switches(target_org_id: str, model_rows: list[dict]) -> list[dict]:  # WHY: single switch fetch
        """Fetch switch inventory once if any switch models are present."""
        if not any(
            row.get("device_type") == "switch" for row in model_rows
        ):  # Skip API call when no switches need expansion
            return []  # WHY: no switch models -> skip API entirely
        logging.info(
            "Pre-fetching switch inventory for version distribution, org=%s", target_org_id
        )  # Log before potentially slow API
        try:
            records = _parent.OrgDeviceInventorySummaryCore._fetch_switch_physical_inventory(
                target_org_id
            )  # Reuse existing fetcher
        except Exception as error:  # Inventory fetch errors must not abort the whole summary run
            logging.exception("Switch inventory pre-fetch failed: %s", error)  # Capture traceback for postmortem
            records = []  # Degrade gracefully so per-model loop yields empty switch rows
        logging.debug("Switch pre-fetch returned %d records", len(records))  # Record outcome for diagnostics
        return records  # WHY: caller uses these for per-model switch expansion

    @staticmethod
    def _prefetch_gateways(target_org_id: str, model_rows: list[dict]) -> list[dict]:  # WHY: single gateway fetch
        """Fetch gateway inventory once if any gateway models are present."""
        if not any(
            row.get("device_type") == "gateway" for row in model_rows
        ):  # Skip API call when no gateways need expansion
            return []  # WHY: no gateway models -> skip API entirely
        logging.info(
            "Pre-fetching gateway inventory for version distribution, org=%s", target_org_id
        )  # Log before potentially slow API
        try:
            records = _parent.OrgDeviceInventorySummaryCore._fetch_gateway_physical_inventory(
                target_org_id
            )  # Reuse existing fetcher
        except Exception as error:  # Inventory fetch errors must not abort the whole summary run
            logging.exception("Gateway inventory pre-fetch failed: %s", error)  # Capture traceback for postmortem
            records = []  # Degrade gracefully so per-model loop yields empty gateway rows
        logging.debug("Gateway pre-fetch returned %d records", len(records))  # Record outcome for diagnostics
        return records

    @staticmethod
    def _rows_for_model(
        model_row: dict,  # WHY: the body dispatches on prefetched records only, so the org id left the signature
        switch_records: list[dict],
        gateway_records: list[dict],
    ) -> list[dict]:
        """Produce version-count rows for a single (device_type, model) pair."""
        device_type = model_row.get("device_type", "")  # Discriminator selects which expansion branch to take
        model_name = model_row.get("model", "")  # Required to filter inventory or build API query
        if not model_name:  # Defensive: skip blank model rows so we never emit empty model="" output
            return []
        if device_type == "switch":  # Aggregate VC-aware switch counts from prefetched inventory
            return VersionPerModelFetcher._switch_rows(model_name, switch_records)
        if device_type == "gateway":  # Aggregate HA-aware gateway counts from prefetched inventory
            return VersionPerModelFetcher._gateway_rows(model_name, gateway_records)
        return []  # APs are handled in bulk by _ap_rows. Any other type has no per-model expansion here

    @staticmethod
    def _accumulate_switch_versions(  # Folds switch inventory records into version->count map (VC-aware)
        model_name: str, switch_records: list[dict]
    ) -> dict[str, int]:
        """Return ``{version: total_members}`` for switches of a single model (VC-stack aware)."""
        version_counts: dict[str, int] = {}  # Per-version running total for this specific model
        for record in switch_records:  # Iterate the prefetched inventory once per call
            if record.get("model") != model_name:  # Skip records belonging to a different switch model
                continue
            version = record.get("version") or "unknown"  # Treat missing firmware version as "unknown"
            num_members = int(
                record.get("num_members") or 1
            )  # Count each VC member individually. Default to 1 for standalone
            version_counts[version] = (
                version_counts.get(version, 0) + num_members
            )  # Add this record's VC members to the bucket
        return version_counts

    @staticmethod
    def _switch_rows(model_name: str, switch_records: list[dict]) -> list[dict]:
        """Aggregate switch version counts using num_members for VC stack accuracy."""
        version_counts = VersionPerModelFetcher._accumulate_switch_versions(
            model_name, switch_records
        )  # Delegate the inner counting loop
        return [  # Materialize accumulator into export-ready row dicts
            {"device_type": "switch", "model": model_name, "version": version, "count": count}
            for version, count in version_counts.items()
        ]

    @staticmethod
    def _gateway_rows(model_name: str, gateway_records: list[dict]) -> list[dict]:
        """Aggregate gateway version counts. One row per inventory record (HA pairs already split)."""
        version_counts: dict[str, int] = {}  # Per-version running total for this specific model
        for record in gateway_records:  # Iterate the prefetched inventory once per call
            if record.get("model") != model_name:  # Skip records belonging to a different gateway model
                continue
            version = record.get("version") or "unknown"  # Treat missing firmware version as "unknown" bucket
            version_counts[version] = (
                version_counts.get(version, 0) + 1
            )  # Each inventory record is one physical gateway
        return [  # Materialize accumulator into export-ready row dicts
            {"device_type": "gateway", "model": model_name, "version": version, "count": count}
            for version, count in version_counts.items()
        ]

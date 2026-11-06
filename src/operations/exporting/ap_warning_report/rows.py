"""Join inventory identity with reported AP trouble evidence and site names."""

from __future__ import annotations

import logging
import re
from typing import Any

from src.operations.exporting.ap_warning_report.codes import CodeDefinitions, TroubleCode

logger = logging.getLogger(__name__)


class ApIdentity:
    """Validate natural device keys before combining source records."""

    @staticmethod
    def mac(value: object) -> str:
        """Normalize an AP MAC address without manufacturing an identity."""
        if not isinstance(value, str):
            raise ValueError("An AP MAC address is required")
        normalized = value.replace(":", "").replace("-", "").lower()
        if re.fullmatch(r"[0-9a-f]{12}", normalized) is None:
            raise ValueError("An AP MAC address must contain twelve hexadecimal digits")
        return normalized

    @staticmethod
    def index(rows: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
        """Reject ambiguous identities instead of silently choosing a source row."""
        result: dict[str, dict[str, Any]] = {}
        for row in rows:
            key = ApIdentity.mac(row.get(field)) if field == "mac" else row.get(field)
            if not isinstance(key, str) or not key:
                raise ValueError("A source record has no identity")
            if key in result:
                raise ValueError(f"Duplicate AP report source identity for {field}")
            result[key] = row
        return result


class TroubleEvidence:
    """Read site statistics evidence without treating it as proof of an active fault."""

    @staticmethod
    def read(statistics: dict[str, Any]) -> tuple[str, str, bool]:
        """Return the site-reported code, time, and missing-code state."""
        observation = statistics.get("last_trouble")  # WHY: Site statistics are the report's eligible evidence.
        if observation is None:  # WHY: Inventory data cannot replace a missing site observation.
            return "", "", True  # WHY: Keep missing evidence distinct from a healthy AP.
        if not isinstance(observation, dict):  # WHY: Reject malformed evidence instead of hiding it.
            raise ValueError("AP last_trouble must be an object")  # WHY: Invalid payloads must stop the report.
        raw_code = observation.get("code")  # WHY: Normalize the exact code supplied by Mist.
        code = TroubleCode.normalize(raw_code)  # WHY: Exclude zero values and preserve numeric formatting.
        missing = raw_code is None or not str(raw_code).strip()  # WHY: Count absent codes explicitly.
        return (
            code,
            TroubleCode.timestamp(observation.get("timestamp")),
            missing,
        )  # WHY: Retain the observation time for filtering.


class ReportSources:
    """Prepare validated lookup tables once for a report build."""

    def __init__(self, sources: dict[str, list[dict[str, Any]]]) -> None:
        """Validate source identities before selecting any warning rows."""
        logger.info("Indexing AP warning report sources")
        self.definitions = CodeDefinitions(sources["definitions"])
        self.sites = ApIdentity.index(sources["sites"], "id")
        ap_statistics = [row for row in sources["stats"] if row.get("type", "ap") == "ap"]
        self.statistics = ApIdentity.index(ap_statistics, "mac")
        inventory = [row for row in sources["inventory"] if row.get("type", "ap") == "ap"]
        self.inventory = ApIdentity.index(inventory, "mac")
        logger.debug(
            "Indexed AP warning report sources inventory=%d statistics=%d", len(self.inventory), len(self.statistics)
        )


class WarningRows:
    """Build inventory-led rows and keep coverage counts separate from health."""

    def __init__(self, org_id: str, sources: dict[str, list[dict[str, Any]]]) -> None:
        """Retain immutable source references for one report build."""
        self._org_id, self._sources = org_id, sources
        self.summary = {
            "inventory_aps": 0,
            "site_statistics_aps": 0,
            "missing_trouble": 0,
            "excluded_trouble": 0,
            "matched": 0,
        }

    def build(self, reported_at: str) -> list[dict[str, Any]]:
        """Select recent site-reported trouble and enrich each inventory identity."""
        logger.info("Building AP warning report rows")
        sources = ReportSources(self._sources)
        self.summary = {
            "inventory_aps": len(sources.inventory),
            "site_statistics_aps": len(sources.statistics),
            "missing_trouble": 0,
            "excluded_trouble": 0,
            "matched": 0,
        }
        rows: list[dict[str, Any]] = []
        for mac, device in sorted(sources.inventory.items()):
            stats = sources.statistics.get(mac, {})
            code, timestamp, missing = TroubleEvidence.read(stats)
            self.summary["missing_trouble"] += missing
            if not code:
                continue
            if timestamp and not TroubleCode.is_recent(timestamp, reported_at):
                self.summary["excluded_trouble"] += 1
                continue
            row = self._row(device, stats, sources.sites)
            row.update(sources.definitions.describe(code))
            row.update(trouble_timestamp=timestamp, trouble_source="statistics", reported_at=reported_at)
            rows.append(row)
        self.summary["matched"] = len(rows)
        logger.debug("Built AP warning report rows counts=%s", self.summary)
        return rows

    def _row(self, device: dict[str, Any], stats: dict[str, Any], sites: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Retain inventory metadata and available assignment without invented values."""
        row = {field: device.get(field) or "" for field in ("name", "serial", "model")}
        row.update(org_id=self._org_id, device_id=device.get("id") or "", mac=ApIdentity.mac(device["mac"]))
        site_id = stats["site_id"] if "site_id" in stats else device.get("site_id")
        row.update(self._site(site_id, sites))
        row["connection_status"] = self._connection(device, stats)
        return row

    @staticmethod
    def _site(site_id: Any, sites: dict[str, dict[str, Any]]) -> dict[str, str]:
        """Keep missing and unassigned sites distinct from a resolved site name."""
        if site_id is not None and not isinstance(site_id, str):
            raise ValueError("An AP site identifier must be text")
        site = sites.get(site_id or "", {})
        name = site.get("name") or ""
        status = "found" if name else ("missing" if site_id else "unassigned")
        return {"site_id": site_id or "", "site_name": name, "site_lookup_status": status}

    @staticmethod
    def _connection(device: dict[str, Any], stats: dict[str, Any]) -> str:
        """Prefer reported statistics state and preserve unknown connection data."""
        if stats.get("status") in ("connected", "disconnected"):
            return str(stats["status"])
        connected = device.get("connected")
        if isinstance(connected, bool):
            return "connected" if connected else "disconnected"
        return "unknown"

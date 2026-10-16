"""Build formula-safe CSV data and download it from the shared data directory."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from flask import Response, send_file

from src.foundation.models.dataclasses.export_backend_options import ExportBackendOptions
from src.operations.exporting.export.data_exporter import DataExporter
from web_portal.services.data_browser import DataBrowserService

logger = logging.getLogger(__name__)
SOURCE_ATTRIBUTION = (
    "MistOrgLicensingComparison by jmorrison-juniper is licensed under "
    "CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/)."
)


class ComparisonExportRows:
    """Validate comparison rows and neutralize spreadsheet formulas."""

    @staticmethod
    def _safe_cell(value: Any) -> Any:
        """Neutralize formula markers in text cells before CSV export."""
        if not isinstance(value, str):
            return value
        # Spreadsheet formula prefixes must remain inert when an operator opens the CSV.
        if value.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
            return "'" + value
        return value

    @classmethod
    def _json_cell(cls, value: Any) -> Any:
        """Serialize nested values with stable keys and formula-safe text."""
        return cls._safe_cell(json.dumps(value, ensure_ascii=True, sort_keys=True))

    @classmethod
    def _row(cls, result: Any) -> dict[str, Any] | None:
        """Build one CSV row or reject a missing organization name."""
        if not isinstance(result, dict) or not isinstance(result.get("name"), str):
            return None
        return {
            "organization": cls._safe_cell(result["name"]),
            "organization_id": cls._safe_cell(result.get("org_id", "")),
            "source": cls._safe_cell(result.get("source", "")),
            "source_attribution": SOURCE_ATTRIBUTION,
            "request_status": cls._safe_cell(result.get("request_status", "unavailable")),
            "license_summary": cls._json_cell(result.get("license_summary", "")),
            "license_use_by_site": cls._json_cell(result.get("license_use_by_site", "")),
            "inventory": cls._json_cell(result.get("inventory", "")),
            "balances": cls._json_cell(result.get("balances", "")),
        }

    @classmethod
    def build(cls, payload: Any) -> tuple[list[dict[str, Any]], str | None]:
        """Build CSV rows only from a non-empty comparison response."""
        if not isinstance(payload, dict) or not isinstance(payload.get("results"), list) or not payload["results"]:
            return [], "The comparison has no exportable rows."
        logger.info("Preparing %d licensing comparison rows for CSV export.", len(payload["results"]))
        rows: list[dict[str, Any]] = []
        for result in payload["results"]:
            row = cls._row(result)
            if row is None:
                return [], "Each comparison row must include an organization name."
            rows.append(row)
        logger.debug("Prepared %d licensing comparison CSV rows.", len(rows))
        return rows, None


class CsvExportService:
    """Write and resolve a CSV through the existing data services."""

    _fieldnames = [
        "organization",
        "organization_id",
        "source",
        "source_attribution",
        "request_status",
        "license_summary",
        "license_use_by_site",
        "inventory",
        "balances",
    ]

    def __init__(self, data_dir: Path) -> None:
        """Keep all export paths inside the configured data directory."""
        self.data_dir = data_dir.resolve()

    def _persist(self, rows: list[dict[str, Any]], target: Path) -> bool:
        """Use the shared exporter without writing operator rows to a database."""
        return DataExporter.write_with_format_selection(
            rows,
            str(target),
            api_function_name=None,  # type: ignore[arg-type]  # CSV-only output must not mirror session input to a database.
            fieldnames=self._fieldnames,
            backend_options=ExportBackendOptions(format_override="csv"),
        )

    def _resolve(self, filename: str) -> Path | None:
        """Resolve the CSV through the data browser's path guard."""
        resolved = DataBrowserService(str(self.data_dir)).resolve_safe_path(filename)
        return Path(resolved) if resolved is not None else None

    def write(self, rows: list[dict[str, Any]]) -> tuple[Response | None, str | None]:
        """Persist a request-scoped CSV and prepare its safe download response."""
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        filename = f"mist_org_licensing_comparison_{timestamp}_{uuid4().hex[:8]}.csv"
        target = self.data_dir / filename
        logger.info("Writing %d licensing comparison rows to CSV.", len(rows))
        if not self._persist(rows, target):
            logger.error("The licensing comparison CSV write failed.")
            return None, "The CSV export failed. Try again."
        resolved = self._resolve(filename)
        if resolved is None:
            logger.error("The licensing comparison CSV could not be resolved below the data directory.")
            return None, "The CSV export could not be read from the data directory."
        logger.debug("Prepared the licensing comparison CSV download.")
        return send_file(Path(resolved), as_attachment=True, download_name=filename, mimetype="text/csv"), None

"""AnomalyMetricsDiscovery extracted from MistHelper.

Discovers site-scoped anomaly metrics from ConstInsightMetrics.csv for
AI/ML analysis. Originally defined as ``AnomalyMetricsDiscovery`` inside
MistHelper.py. Extracted here per initiative 1011 to shrink the monolith.

Runtime dependency ``FilePathUtils`` still lives inside MistHelper.py and
is resolved lazily via the ``_MH`` module-level proxy so this module keeps
its import graph flat and honours any test monkey-patches applied at
runtime.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import csv  # Reads ConstInsightMetrics.csv into structured dictionaries
import logging  # Structured action logging required by Constitution VII
import os  # Filesystem existence check for the CSV path
from typing import Any  # Loose typing for late-bound MistHelper attributes

from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: resolve source dependencies without importing the root module.
)

logger = logging.getLogger(__name__)  # Keep refactor logs tied to this module.
_MH = SourceDependencyResolver  # Use the source resolver for lazy dependency access.


class AnomalyMetricsDiscovery:
    """Discover and prioritize site-scoped anomaly metrics from ConstInsightMetrics.csv.

    Provides fallback metrics when CSV is unavailable. Used for AI/ML anomaly analysis.
    """

    # Priority keywords for anomaly-related metrics
    PRIORITY_KEYWORDS = [
        "roam",
        "availability",
        "capacity",
        "coverage",
        "client",
        "throughput",
        "latency",
        "band",
        "ap-",
        "switch-",
    ]

    # Fallback metrics when CSV unavailable
    FALLBACK_METRICS = [
        {"metric_name": "client-roam-band5", "description": "5GHz roaming anomalies", "priority": True},
        {"metric_name": "client-roam-band24", "description": "2.4GHz roaming anomalies", "priority": True},
        {"metric_name": "ap-availability", "description": "AP availability anomalies", "priority": True},
    ]

    @classmethod
    def discover(cls) -> list[dict[str, Any]]:
        """Discover potential anomaly metrics from ConstInsightMetrics.csv.

        Returns:
            List of metric dictionaries with metric_name, description, and priority.

        File, encoding, CSV, and runtime failures return the fallback metrics.
        Other exceptions propagate so programming errors remain visible.
        """
        logger.info("Reading ConstInsightMetrics.csv for anomaly metrics")  # Record discovery without a private path.
        try:
            metrics_path = _MH.FilePathUtils.get_csv_path(
                "ConstInsightMetrics.csv"
            )  # Resolve CSV location via MistHelper's FilePathUtils

            if not os.path.exists(metrics_path):  # Skip when the CSV was never exported
                return cls._handle_missing_csv()  # Emit warning and fall back to defaults

            return cls._parse_metrics_csv(metrics_path)  # Parse and return discovered metrics

        except (OSError, UnicodeError, csv.Error, RuntimeError) as exception:  # Preserve supported failure fallbacks.
            logging.error(
                "Error reading ConstInsightMetrics.csv (%s). Using fallback metrics.", type(exception).__name__
            )  # Report the failure type without exception text, file contents, or credentials.
            logger.debug("Returning %s fallback anomaly metrics", len(cls.FALLBACK_METRICS))  # Record fallback size.
            return cls.FALLBACK_METRICS.copy()  # Return a defensive copy of the fallback set

    @classmethod
    def _handle_missing_csv(cls) -> list[dict[str, Any]]:
        """Handle case when ConstInsightMetrics.csv is not found."""
        logger.warning(
            "ConstInsightMetrics.csv not found. Please export organization constants first (menu option 11)."
        )  # Guide operator toward the export menu that produces the CSV
        logger.debug(
            "Returning %s fallback anomaly metrics", len(cls.FALLBACK_METRICS)
        )  # Record missing-file recovery.
        return cls.FALLBACK_METRICS.copy()  # Defensive copy so callers can mutate without side effects

    @classmethod
    def _parse_metrics_csv(cls, csv_path: str) -> list[dict[str, Any]]:
        """Parse metrics CSV and extract site-scoped anomaly metrics."""
        potential_metrics = []  # Accumulator for site-scoped rows only

        with open(csv_path, encoding="utf-8") as csv_file:  # UTF-8 CSV is the Mist export standard
            reader = csv.DictReader(csv_file)  # Yield rows keyed by header names
            for row in reader:  # Walk each metric definition
                metric = cls._process_csv_row(row)  # Filter/transform row into an anomaly candidate
                if metric:  # Non-site or empty-key rows return None and are skipped
                    potential_metrics.append(metric)  # Accept eligible metric

        return cls._sort_by_priority(potential_metrics)  # Priority-first ordering before returning

    @classmethod
    def _process_csv_row(cls, row: dict[str, str | None]) -> dict[str, Any] | None:
        """Process a single CSV row and return metric dict if site-scoped."""
        if any(
            row.get(field, "") is None for field in ("key", "name", "scope")
        ):  # DictReader pads short rows with None.
            raise csv.Error(
                "A metric row has fewer values than its header."
            )  # Keep malformed CSV on the fallback path.
        metric_key = (row.get("key") or "").strip().lower()  # Normalize validated text for keyword matching.
        metric_name = (row.get("name") or "").strip()  # Preserve blank and absent descriptions.
        metric_scope = (row.get("scope") or "").strip().lower()  # Limit anomaly discovery to site metrics.

        if metric_scope != "site" or not metric_key:  # Reject non-site or unnamed rows
            return None  # Signals _parse_metrics_csv to skip this row

        is_priority = any(
            keyword in metric_key for keyword in cls.PRIORITY_KEYWORDS
        )  # Prioritize known anomaly buckets
        description = (
            metric_name if metric_name else f"Anomaly events for {metric_key}"
        )  # Fallback description when name blank

        return {
            "metric_name": metric_key,
            "description": description,
            "priority": is_priority,
        }  # Structured metric record

    @classmethod
    def _sort_by_priority(cls, metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Sort metrics with priority items first, then alphabetically."""
        metrics.sort(
            key=lambda x: (not x.get("priority", False), x["metric_name"])
        )  # False<True keeps priority items first
        logger.info(
            "Found %s potential anomaly metrics from ConstInsightMetrics.csv", len(metrics)
        )  # Log discovery count
        return metrics  # Return sorted list to caller

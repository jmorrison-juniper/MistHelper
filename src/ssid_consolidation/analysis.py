"""Analysis helpers for per-cluster deviation and cross-cluster drift reports."""

from __future__ import annotations

from typing import Any

ClusterReport = dict[str, dict[str, dict[str, int]]]


class AnalysisManager:
    """Build deviation summaries from collected phase 1 SSID rows."""

    DEFAULT_EXCLUDE = {
        "id",
        "org_id",
        "site_id",
        "template_id",
        "created_time",
        "modified_time",
        "edge_cluster_id",
        "edge_cluster_name",
    }

    def per_cluster_deviation(
        self,
        rows: list[dict[str, Any]],
        exclude_fields: list[str] | None = None,
    ) -> ClusterReport:
        """Count parameter values per edge cluster, excluding identity fields."""
        excluded_fields = set(exclude_fields or []) | self.DEFAULT_EXCLUDE
        per_cluster: ClusterReport = {}
        for row in rows:
            cluster = row.get("edge_cluster_id") or "unknown"
            per_cluster.setdefault(cluster, {})
            for key, value in row.items():
                if key in excluded_fields:
                    continue
                param_map = per_cluster[cluster].setdefault(key, {})
                normalized_value = "<NULL>" if value is None else str(value)
                param_map[normalized_value] = param_map.get(normalized_value, 0) + 1
        return per_cluster

    def _majority_value(self, counts: dict[str, int]) -> str | None:
        """Return the most common value for a cluster parameter map."""
        if not counts:
            return None
        return max(counts.items(), key=lambda item: item[1])[0]

    def cross_cluster_drift(self, per_cluster_report: ClusterReport) -> dict[str, dict[str, str | None]]:
        """Return parameters whose majority value differs between clusters."""
        params: set[str] = set()
        for cluster_map in per_cluster_report.values():
            params.update(cluster_map.keys())
        drift: dict[str, dict[str, str | None]] = {}
        for param in params:
            majority_by_cluster = {
                cluster: self._majority_value(cluster_map.get(param, {}))
                for cluster, cluster_map in per_cluster_report.items()
            }
            if len({value for value in majority_by_cluster.values() if value is not None}) > 1:
                drift[param] = majority_by_cluster
        return drift

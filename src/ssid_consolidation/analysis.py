from collections import defaultdict
from typing import List, Dict, Any


class AnalysisManager:
    """Per-cluster deviation analysis and cross-cluster drift detection."""

    DEFAULT_EXCLUDE = {"id", "org_id", "site_id", "template_id", "created_time", "modified_time", "edge_cluster_id", "edge_cluster_name"}

    def per_cluster_deviation(self, rows: List[Dict[str, Any]], exclude_fields=None) -> Dict[str, Dict[str, Dict[str, int]]]:
        exclude = set(exclude_fields or []) | self.DEFAULT_EXCLUDE
        per_cluster: Dict[str, Dict[str, Dict[str, int]]] = {}
        for row in rows:
            cluster = row.get("edge_cluster_id") or "unknown"
            per_cluster.setdefault(cluster, {})
            for k, v in row.items():
                if k in exclude:
                    continue
                param_map = per_cluster[cluster].setdefault(k, {})
                key = "<NULL>" if v is None else str(v)
                param_map[key] = param_map.get(key, 0) + 1
        return per_cluster

    def cross_cluster_drift(self, per_cluster_report: Dict[str, Dict[str, Dict[str, int]]]) -> Dict[str, Dict[str, str]]:
        # For each parameter, compute the majority value per cluster and flag parameters where
        # the majority values differ across clusters.
        params = set()
        for cluster_map in per_cluster_report.values():
            params.update(cluster_map.keys())

        drift: Dict[str, Dict[str, str]] = {}
        for param in params:
            majority_by_cluster: Dict[str, str] = {}
            for cluster, cluster_map in per_cluster_report.items():
                counts = cluster_map.get(param, {})
                if counts:
                    # pick the value with max count
                    maj_val = max(counts.items(), key=lambda kv: kv[1])[0]
                else:
                    maj_val = None
                majority_by_cluster[cluster] = maj_val

            # determine if majority values differ across clusters
            values = set(v for v in majority_by_cluster.values() if v is not None)
            if len(values) > 1:
                drift[param] = majority_by_cluster

        return drift

"""Phase 3 site-groups cluster for the SSID Template Consolidation manager.

Owns the Phase 3 workflow: derive per-cluster + pilot site groups from
the Phase 1 cache, display the plan, ensure groups exist, and assign
matrix sites to their target groups. Split out of the parent module so
the coordinator stays under the compliance length / block budgets while
the pure helpers remain re-exported via
:mod:`ssid_template_consolidation`.

The ``_create_site_group`` and ``_assign_group_sites`` helpers are
intentionally *not* moved here: they resolve ``mistapi`` at call time
and the historical unit tests patch ``mistapi`` through the parent
module's namespace (e.g. ``patch.object(ssid_template_consolidation,
"mistapi", ...)``), which only intercepts calls whose ``__globals__``
binding *is* the parent module. Keeping those two helpers in the parent
preserves those tests without teaching them about internal module
boundaries.
"""

# WHY: cluster methods intentionally reach into the parent manager's private
# helpers (_load_cache, _offer_resume, _save_phase_results, _confirm_or_cancel)
# and defer sibling imports until call-time to break import cycles. The class
# also has only orchestrator methods so pylint's public-method threshold does
# not fit this proxy pattern.
# pylint: disable=protected-access,import-outside-toplevel,too-few-public-methods,cyclic-import

from __future__ import annotations  # WHY: postponed evaluation for forward-ref parent type

from datetime import datetime  # WHY: assignment timestamps
from typing import Any  # WHY: broad typing for opaque cache / row payloads

from ._ssid_template_cluster import _ClusterBase  # WHY: shared parent-proxy wrapper

# ---------------------------------------------------------------------------
# Pure module-level helpers
# ---------------------------------------------------------------------------


def _compute_group_plan(cache: dict[str, Any]) -> dict[str, Any]:
    """Build site group assignment plan from matrix data."""
    matrix = cache.get("matrix", [])  # WHY: per-site rows drive assignment
    mxtunnels = cache.get("data", {}).get("mxtunnels", [])  # WHY: clusters == mxtunnels
    existing_groups = cache.get("data", {}).get("sitegroups", [])  # WHY: reuse existing IDs
    existing_lookup = {group.get("name", ""): group for group in existing_groups}

    cluster_names = sorted({tunnel.get("name", "") for tunnel in mxtunnels if tunnel.get("name")})
    groups = _build_cluster_groups(cluster_names, existing_lookup)
    _add_pilot_group(groups, existing_lookup)

    group_name_map = {g["group_name"]: g for g in groups}
    _assign_matrix_sites(matrix, group_name_map)
    return {"groups": groups}


def _build_cluster_groups(
    cluster_names: list[str],
    existing_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build production group entries for each cluster."""
    groups: list[dict[str, Any]] = []
    for cluster_name in cluster_names:
        group_name = f"misthelper_prod_{cluster_name}"
        existing = existing_lookup.get(group_name)  # WHY: reuse when the group already exists
        groups.append(
            {
                "group_name": group_name,
                "cluster_name": cluster_name,
                "group_id": (existing.get("id", "") if existing else ""),
                "exists": bool(existing),
                "sites": [],
            }
        )
    return groups


def _add_pilot_group(
    groups: list[dict[str, Any]],
    existing_lookup: dict[str, dict[str, Any]],
) -> None:
    """Add the pilot site group entry (in-place)."""
    pilot_existing = existing_lookup.get("misthelper_pilot")  # WHY: pilot is a fixed group name
    groups.append(
        {
            "group_name": "misthelper_pilot",
            "cluster_name": "pilot",
            "group_id": (pilot_existing.get("id", "") if pilot_existing else ""),
            "exists": bool(pilot_existing),
            "sites": [],
        }
    )


def _assign_matrix_sites(
    matrix: list[dict[str, Any]],
    group_name_map: dict[str, dict[str, Any]],
) -> None:
    """Assign matrix sites to their target groups (in-place)."""
    for row in matrix:
        if row.get("psk_detected") or row.get("anomaly"):
            continue  # WHY: PSK/anomaly rows are excluded from consolidation
        target = row.get("target_group", "")
        mapped = "misthelper_pilot" if target == "pilot" else f"misthelper_prod_{target}"
        target_group = group_name_map.get(mapped)
        if target_group:
            target_group["sites"].append(
                {
                    "site_id": row.get("site_id", ""),
                    "site_name": row.get("site_name", ""),
                }
            )


def _display_group_plan(plan: dict[str, Any]) -> None:
    """Print the group assignment plan."""
    print("\n  Site Group Plan:")
    for group in plan.get("groups", []):
        status = "exists" if group["exists"] else "to create"
        site_count = len(group["sites"])
        print(f"    {group['group_name']} ({status}) " f"- {site_count} sites")
        for site in group["sites"][:5]:  # WHY: bound console noise per group
            print(f"      - {site['site_name']}")
        if len(group["sites"]) > 5:
            print(f"      ... and {len(group['sites']) - 5} more")


def _build_assign_results(
    sites: list[dict[str, Any]],
    existing_ids: list[str],
    group: dict[str, Any],
    group_id: str,
) -> list[dict[str, Any]]:
    """Build assignment result records for successful operations."""
    timestamp = datetime.now().isoformat()  # WHY: single timestamp per batch
    results: list[dict[str, Any]] = []
    for site in sites:
        status = "already_assigned" if site["site_id"] in existing_ids else "assigned"
        results.append(
            {
                "site_name": site["site_name"],
                "site_id": site["site_id"],
                "group_name": group["group_name"],
                "group_id": group_id,
                "cluster_name": group.get("cluster_name", ""),
                "status": status,
                "reason": "",
                "timestamp": timestamp,
            }
        )
    return results


def _build_failed_assign_results(
    sites: list[dict[str, Any]],
    group: dict[str, Any],
    group_id: str,
    error: Exception,
) -> list[dict[str, Any]]:
    """Build failed assignment result records."""
    return [
        {
            "site_name": site["site_name"],
            "site_id": site["site_id"],
            "group_name": group["group_name"],
            "group_id": group_id,
            "cluster_name": group.get("cluster_name", ""),
            "status": "failed",
            "reason": str(error),
            "timestamp": datetime.now().isoformat(),
        }
        for site in sites
    ]


def _get_existing_group_site_ids(cache: dict[str, Any], group_id: str) -> list[str]:
    """Get current site_ids from cached sitegroup data."""
    for group in cache.get("data", {}).get("sitegroups", []):  # WHY: linear search over cached groups
        if group.get("id") == group_id:
            ids: list[str] = group.get("site_ids", []) or []
            return ids
    return []


# ---------------------------------------------------------------------------
# Cluster class wrapping parent phase-3 orchestrators
# ---------------------------------------------------------------------------


class _SsidTemplatePhase3Cluster(_ClusterBase):
    """Owns the Phase 3 site-group orchestrator + ensure/assign coordinators."""

    def phase3_site_groups(self) -> None:
        """Phase 3 orchestrator — create groups and assign sites."""
        parent = self._mm  # WHY: proxy alias for readability + W0212 avoidance
        print("\n=== Phase 3: Create / Assign Site Groups ===")
        import logging  # noqa: PLC0415 — kept local so this cluster ships zero import-time deps

        logging.info("Phase 3: Starting site group configuration")

        if not self._load_cache_or_bail():
            return

        resuming, prior_results = parent._offer_resume(3, [])  # noqa: SLF001
        group_plan = _compute_group_plan(parent.cache)
        _display_group_plan(group_plan)

        group_count = len(group_plan["groups"])
        if not parent._confirm_or_cancel(f"Create/assign {group_count} site groups?"):  # noqa: SLF001
            return

        group_plan = self._call("_ensure_groups_exist", group_plan)
        results = self._call("_assign_sites_to_groups", group_plan, prior_results if resuming else [])
        parent._save_phase_results(3, results)  # noqa: SLF001
        parent.write_data_fn(
            data=results,
            filename_or_table="ssid_consolidation_site_groups",
            api_function_name="ssidConsolidationSiteGroups",
        )
        # WHY: phase45 owns the shared summary helper — import directly to avoid
        # routing through the parent module (mypy [attr-defined] on re-export).
        from ._ssid_template_phase45 import (
            _print_phase_summary,  # noqa: PLC0415 — local import keeps import graph shallow
        )

        _print_phase_summary("Phase 3", results)

    def _ensure_groups_exist(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Create missing site groups and record their IDs."""
        parent = self._mm  # WHY: proxy alias
        import logging  # noqa: PLC0415

        # WHY: parent owns the creator so tests can patch mistapi at the parent module.
        from .ssid_template_consolidation import _create_site_group  # noqa: PLC0415 — local import breaks cycle

        for group in plan.get("groups", []):
            if group["exists"]:
                logging.info(
                    "Group '%s' already exists (id=%s)",
                    group["group_name"],
                    group["group_id"],
                )
                continue
            _create_site_group(group, parent.org_id, parent.apisession)
        return plan

    def _assign_sites_to_groups(
        self,
        plan: dict[str, Any],
        resume_from: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Assign sites to their target groups via additive merge."""
        parent = self._mm  # WHY: proxy alias

        # WHY: parent owns the per-group assigner so tests can patch mistapi at parent.
        from .ssid_template_consolidation import _assign_group_sites  # noqa: PLC0415 — local import breaks cycle

        completed_ids: set[tuple[str, str]] = {
            (str(row.get("site_id", "")), str(row.get("group_id", "")))
            for row in resume_from
            if row.get("status") == "assigned"
        }
        results: list[dict[str, Any]] = list(resume_from) if resume_from else []

        for group in plan.get("groups", []):
            if not group.get("group_id"):
                continue  # WHY: skip groups whose creation failed upstream
            group_results = _assign_group_sites(
                group,
                completed_ids,
                parent.cache,
                parent.org_id,
                parent.apisession,
            )
            results.extend(group_results)
        return results

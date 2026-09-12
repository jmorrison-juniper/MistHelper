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
module's namespace (for example ``patch.object(ssid_template_consolidation,
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

import logging  # WHY: workflow telemetry emitted from the phase 3 orchestrator
from dataclasses import dataclass  # WHY: bundle site-assignment identity fields
from datetime import datetime  # WHY: assignment timestamps
from typing import Any  # WHY: broad typing for opaque cache / row payloads

from ._ssid_template_cluster import _ClusterBase  # WHY: shared parent-proxy wrapper

# ---------------------------------------------------------------------------
# Module-level constants (magic value hoisting)
# ---------------------------------------------------------------------------
_PROD_GROUP_PREFIX = "misthelper_prod_"  # WHY: production site-group naming convention
_PILOT_GROUP_NAME = "misthelper_pilot"  # WHY: fixed name for the pilot site-group
_PILOT_TARGET = "pilot"  # WHY: matrix rows targeting pilot cluster route to the pilot group
_PHASE_ID = 3  # WHY: phase index for offer_resume / save_phase_results dispatch
_PHASE_LABEL = "Phase 3"  # WHY: label used by _print_phase_summary for report output
_PHASE3_HEADER = "=== Phase 3: Create / Assign Site Groups ==="  # WHY: user-facing banner
_PHASE3_START_LOG = "Phase 3: Starting site group configuration"  # WHY: startup log line
_GROUP_EXISTS_LOG = "Group '%s' already exists (id=%s)"  # WHY: reuse-existing skip message
_WRITE_FILENAME = "ssid_consolidation_site_groups"  # WHY: parquet/table sink filename
_WRITE_API_NAME = "ssidConsolidationSiteGroups"  # WHY: mist API function tag for archival
_DISPLAY_SITE_LIMIT = 5  # WHY: bound console noise per group when previewing sites
_STATUS_ASSIGNED = "assigned"  # WHY: success status for newly assigned site rows
_STATUS_ALREADY = "already_assigned"  # WHY: idempotent status when site was already in group
_STATUS_FAILED = "failed"  # WHY: status for failed assignment attempts

# ---------------------------------------------------------------------------
# Bundle dataclass — collapses group + group_id + timestamp into one arg
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)  # WHY: immutable slotted bundle keeps builders under budget
class _AssignRowContext:
    """Bundle of identity fields shared by every assignment result row.

    Rather than plumbing ``group``, ``group_id`` and ``timestamp`` through
    each result-builder loop iteration, the caller packs them once into
    this frozen slotted bundle and the helpers read the fields directly.
    """

    group: dict[str, Any]  # WHY: raw group entry (carries group_name + cluster_name)
    group_id: str  # WHY: mist site-group id used on the result row
    timestamp: str  # WHY: single ISO timestamp shared across the row batch


# ---------------------------------------------------------------------------
# Pure module-level helpers — matrix plan builders
# ---------------------------------------------------------------------------


def _compute_group_plan(cache: dict[str, Any]) -> dict[str, Any]:  # WHY: exported for tests + re-export
    """Build site group assignment plan from matrix data."""
    matrix = cache.get("matrix", [])  # WHY: per-site rows drive assignment
    data = cache.get("data", {})  # WHY: nested cache section holds sibling artifacts
    mxtunnels = data.get("mxtunnels", [])  # WHY: clusters == mxtunnels by convention
    existing_groups = data.get("sitegroups", [])  # WHY: reuse existing IDs when present
    existing_lookup = {group.get("name", ""): group for group in existing_groups}  # WHY: name->group index
    cluster_names = _extract_cluster_names(mxtunnels)  # WHY: unique sorted cluster keys
    groups = _build_cluster_groups(cluster_names, existing_lookup)  # WHY: prod-group entries
    _add_pilot_group(groups, existing_lookup)  # WHY: append the fixed pilot entry in-place
    group_name_map = {g["group_name"]: g for g in groups}  # WHY: name->entry lookup for assignment
    _assign_matrix_sites(matrix, group_name_map)  # WHY: mutate group entries with matched sites
    return {"groups": groups}  # WHY: caller expects a plan dict with a groups key


def _extract_cluster_names(mxtunnels: list[dict[str, Any]]) -> list[str]:  # WHY: split for CC budget
    """Return unique sorted cluster names extracted from mxtunnels."""
    return sorted({tunnel.get("name", "") for tunnel in mxtunnels if tunnel.get("name")})  # WHY: dedupe+sort


def _build_cluster_groups(
    cluster_names: list[str],
    existing_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:  # WHY: exported for tests + re-export
    """Build production group entries for each cluster."""
    groups: list[dict[str, Any]] = []  # WHY: accumulator for the returned list
    for cluster_name in cluster_names:  # WHY: one entry per unique cluster
        groups.append(_make_cluster_entry(cluster_name, existing_lookup))  # WHY: delegate row shaping
    return groups  # WHY: hand accumulated entries back to caller


def _make_cluster_entry(
    cluster_name: str,
    existing_lookup: dict[str, dict[str, Any]],
) -> dict[str, Any]:  # WHY: single-entry builder keeps loop CC low
    """Shape one production group entry for the given cluster name."""
    group_name = f"{_PROD_GROUP_PREFIX}{cluster_name}"  # WHY: production naming convention
    existing = existing_lookup.get(group_name)  # WHY: reuse when the group already exists
    return {
        "group_name": group_name,  # WHY: fully qualified misthelper_prod_<cluster>
        "cluster_name": cluster_name,  # WHY: preserved for downstream tagging
        "group_id": existing.get("id", "") if existing else "",  # WHY: empty id when we must create
        "exists": bool(existing),  # WHY: gate for the create-if-missing step
        "sites": [],  # WHY: filled later by _assign_matrix_sites
    }


def _add_pilot_group(
    groups: list[dict[str, Any]],
    existing_lookup: dict[str, dict[str, Any]],
) -> None:  # WHY: exported for tests + re-export
    """Add the pilot site group entry (in-place)."""
    pilot_existing = existing_lookup.get(_PILOT_GROUP_NAME)  # WHY: pilot is a fixed group name
    groups.append(
        {
            "group_name": _PILOT_GROUP_NAME,  # WHY: constant name for the pilot bucket
            "cluster_name": _PILOT_TARGET,  # WHY: matches matrix rows tagged as pilot
            "group_id": pilot_existing.get("id", "") if pilot_existing else "",  # WHY: reuse when present
            "exists": bool(pilot_existing),  # WHY: skip create step when already there
            "sites": [],  # WHY: filled later by _assign_matrix_sites
        }
    )


def _matrix_row_eligible(row: dict[str, Any]) -> bool:  # WHY: guard extraction keeps outer CC down
    """Return True when the matrix row should participate in consolidation."""
    return not (row.get("psk_detected") or row.get("anomaly"))  # WHY: PSK/anomaly rows are excluded


def _resolve_target_group_name(target: str) -> str:  # WHY: pure mapper keeps outer CC down
    """Map a matrix ``target_group`` value onto its canonical group name."""
    return _PILOT_GROUP_NAME if target == _PILOT_TARGET else f"{_PROD_GROUP_PREFIX}{target}"  # WHY: table map


def _site_entry(row: dict[str, Any]) -> dict[str, Any]:  # WHY: shape a compact site row once
    """Return the {site_id, site_name} entry appended to a group's sites list."""
    return {"site_id": row.get("site_id", ""), "site_name": row.get("site_name", "")}  # WHY: compact site row


def _assign_matrix_sites(
    matrix: list[dict[str, Any]],
    group_name_map: dict[str, dict[str, Any]],
) -> None:  # WHY: exported for tests + re-export
    """Assign matrix sites to their target groups (in-place)."""
    for row in matrix:  # WHY: iterate over every planned site row
        if not _matrix_row_eligible(row):  # WHY: skip PSK / anomaly rows via extracted guard
            continue  # WHY: excluded rows do not affect any group
        mapped = _resolve_target_group_name(row.get("target_group", ""))  # WHY: pilot vs prod dispatch
        target_group = group_name_map.get(mapped)  # WHY: None when the group is not on the plan
        if target_group:  # WHY: silently drop rows whose target group is absent
            target_group["sites"].append(_site_entry(row))  # WHY: attach compact site record


# ---------------------------------------------------------------------------
# Pure module-level helpers — display + result builders
# ---------------------------------------------------------------------------


def _display_group_plan(plan: dict[str, Any]) -> None:  # WHY: exported for tests + re-export
    """Print the group assignment plan."""
    logging.warning("Site Group Plan:")  # WHY: section header for the console preview
    for group in plan.get("groups", []):  # WHY: preview one group entry at a time
        _print_group_header(group)  # WHY: header line with exists/create + site count
        _print_group_preview(group)  # WHY: bounded preview of member sites


def _print_group_header(group: dict[str, Any]) -> None:  # WHY: extracted from _display_group_plan
    """Print a single group header row (status + site count)."""
    status = "exists" if group["exists"] else "to create"  # WHY: preview action verb
    site_count = len(group["sites"])  # WHY: total members before truncation
    logging.warning("%s (%s) - %d sites", group["group_name"], status, site_count)  # WHY: single header line


def _print_group_preview(group: dict[str, Any]) -> None:  # WHY: extracted from _display_group_plan
    """Print a bounded preview of a group's assigned sites."""
    sites = group["sites"]  # WHY: alias for readability
    for site in sites[:_DISPLAY_SITE_LIMIT]:  # WHY: bound console noise per group
        logging.warning("- %s", site["site_name"])  # WHY: one visible site name per line
    if len(sites) > _DISPLAY_SITE_LIMIT:  # WHY: only mention overflow when it exists
        logging.warning("... and %d more", len(sites) - _DISPLAY_SITE_LIMIT)  # WHY: overflow marker


def _build_assign_results(
    sites: list[dict[str, Any]],
    existing_ids: list[str],
    group: dict[str, Any],
    group_id: str,
) -> list[dict[str, Any]]:  # WHY: exported for tests + re-export
    """Build assignment result records for successful operations."""
    ctx = _AssignRowContext(group=group, group_id=group_id, timestamp=datetime.now().isoformat())  # WHY: pack once
    return [_success_row(site, existing_ids, ctx) for site in sites]  # WHY: one row per site


def _success_row(
    site: dict[str, Any],
    existing_ids: list[str],
    ctx: _AssignRowContext,
) -> dict[str, Any]:  # WHY: per-site builder called from list comprehension
    """Build one successful-assignment result row."""
    status = _STATUS_ALREADY if site["site_id"] in existing_ids else _STATUS_ASSIGNED  # WHY: idempotent tag
    return _result_row(site, ctx, status=status, reason="")  # WHY: shared shaping keeps schema aligned


def _build_failed_assign_results(
    sites: list[dict[str, Any]],
    group: dict[str, Any],
    group_id: str,
    error: Exception,
) -> list[dict[str, Any]]:  # WHY: exported for tests + re-export
    """Build failed assignment result records."""
    ctx = _AssignRowContext(group=group, group_id=group_id, timestamp=datetime.now().isoformat())  # WHY: pack once
    reason = str(error)  # WHY: cached string form of the raised exception
    return [_result_row(site, ctx, status=_STATUS_FAILED, reason=reason) for site in sites]  # WHY: one row per site


def _result_row(
    site: dict[str, Any],
    ctx: _AssignRowContext,
    *,
    status: str,
    reason: str,
) -> dict[str, Any]:  # WHY: single row shaper shared by success + failure paths
    """Shape one assignment result row from a site + context bundle."""
    return {
        "site_name": site["site_name"],  # WHY: friendly site label for reports
        "site_id": site["site_id"],  # WHY: mist site id for the assignment record
        "group_name": ctx.group["group_name"],  # WHY: parent group's canonical name
        "group_id": ctx.group_id,  # WHY: parent group's mist id (may be blank on failure)
        "cluster_name": ctx.group.get("cluster_name", ""),  # WHY: cluster tag from the group entry
        "status": status,  # WHY: assigned/already_assigned/failed enum
        "reason": reason,  # WHY: populated only on failure rows
        "timestamp": ctx.timestamp,  # WHY: single ISO timestamp shared across the batch
    }


def _get_existing_group_site_ids(cache: dict[str, Any], group_id: str) -> list[str]:  # WHY: exported for tests
    """Get current site_ids from cached sitegroup data."""
    for group in cache.get("data", {}).get("sitegroups", []):  # WHY: linear search over cached groups
        if group.get("id") == group_id:  # WHY: match on the mist-assigned id
            ids: list[str] = group.get("site_ids", []) or []  # WHY: normalize null site_ids to empty list
            return ids  # WHY: found match — stop scanning
    return []  # WHY: no cached entry — caller treats as empty


# ---------------------------------------------------------------------------
# Cluster class wrapping parent phase-3 orchestrators
# ---------------------------------------------------------------------------


class _SsidTemplatePhase3Cluster(_ClusterBase):  # WHY: exported for parent __init__ binding
    """Owns the Phase 3 site-group orchestrator + ensure/assign coordinators."""

    def phase3_site_groups(self) -> None:  # WHY: orchestrator entry point invoked by the parent manager
        """Phase 3 orchestrator — create groups and assign sites."""
        parent = self._mm  # WHY: proxy alias for readability + W0212 avoidance
        _log_phase3_start()  # WHY: emit banner + telemetry once
        if not self._load_cache_or_bail():  # WHY: shared preamble — abort when Phase 1 skipped
            return  # WHY: cache preamble already printed the bail message
        resuming, prior_results = parent._offer_resume(_PHASE_ID)
        group_plan = _compute_group_plan(parent.cache)  # WHY: derive plan from Phase 1 cache
        _display_group_plan(group_plan)  # WHY: user preview before confirming
        prompt = f"Create/assign {len(group_plan['groups'])} site groups?"  # WHY: confirmation prompt copy
        if not parent._confirm_or_cancel(prompt):  # shared preamble helper
            return  # WHY: user declined — phase aborts without persistence
        group_plan = self._call("_ensure_groups_exist", group_plan)  # WHY: create missing groups first
        resume_state = prior_results if resuming else []  # WHY: pass prior rows only when resuming
        results = self._call("_assign_sites_to_groups", group_plan, resume_state)  # WHY: assign matrix sites
        self._persist_phase3_results(results)  # WHY: save + write + summary in one call

    def _persist_phase3_results(self, results: list[dict[str, Any]]) -> None:  # WHY: extracted persistence tail
        """Save phase results, hand them to the writer, and print the summary."""
        parent = self._mm  # WHY: proxy alias for readability + W0212 avoidance
        parent._save_phase_results(_PHASE_ID, results)  # parent owns phase-state save
        parent.write_data_fn(  # WHY: hand rows to the configured writer (parquet/table)
            data=results,
            filename_or_table=_WRITE_FILENAME,  # WHY: consistent sink label across phases
            api_function_name=_WRITE_API_NAME,  # WHY: mist API tag preserved on the archival row
        )
        # WHY: phase45 owns the shared summary helper — import directly to avoid
        # routing through the parent module (mypy [attr-defined] on re-export).
        from ._ssid_template_phase45 import (
            _print_phase_summary,  # local import keeps import graph shallow
        )

        _print_phase_summary(_PHASE_LABEL, results)  # WHY: emit success/failure summary

    def _ensure_groups_exist(self, plan: dict[str, Any]) -> dict[str, Any]:  # WHY: coordinator for create step
        """Create missing site groups and record their IDs."""
        parent = self._mm  # WHY: proxy alias
        # WHY: parent owns the creator so tests can patch mistapi at the parent module.
        from .ssid_template_consolidation import _create_site_group  # local import breaks cycle

        for group in plan.get("groups", []):  # WHY: iterate over every planned group
            _ensure_single_group(group, parent, _create_site_group)  # WHY: delegate per-group branching
        return plan  # WHY: caller expects the mutated plan back

    def _assign_sites_to_groups(
        self,
        plan: dict[str, Any],
        resume_from: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:  # WHY: coordinator for assignment step
        """Assign sites to their target groups via additive merge."""
        parent = self._mm  # WHY: proxy alias
        # WHY: parent owns the per-group assigner so tests can patch mistapi at parent.
        from .ssid_template_consolidation import _assign_group_sites  # local import breaks cycle

        completed_ids = _build_completed_ids(resume_from)  # WHY: dedupe set for idempotent resume
        results: list[dict[str, Any]] = list(resume_from) if resume_from else []  # WHY: seed with prior rows
        for group in plan.get("groups", []):  # WHY: iterate over every planned group
            if not group.get("group_id"):  # WHY: skip groups whose creation failed upstream
                continue  # WHY: no id means no sites can be attached
            group_results = _assign_group_sites(  # WHY: parent helper performs the mistapi assignment
                group, completed_ids, parent.cache, parent.org_id, parent.apisession
            )
            results.extend(group_results)  # WHY: fold per-group rows into the batch
        return results  # WHY: full batch is persisted by the orchestrator


# ---------------------------------------------------------------------------
# Static coordinator helpers (kept module-level so class stays orchestration-only)
# ---------------------------------------------------------------------------


def _log_phase3_start() -> None:  # WHY: extracted from phase3_site_groups
    """Print the banner and emit the startup log line for Phase 3."""
    logging.warning(_PHASE3_HEADER)  # WHY: user-facing banner marks phase entry
    logging.info(_PHASE3_START_LOG)  # WHY: telemetry alongside the banner


def _ensure_single_group(
    group: dict[str, Any],
    parent: Any,
    create_fn: Any,
) -> None:  # WHY: extracted from _ensure_groups_exist loop
    """Create the group when missing. Otherwise log the reuse."""
    if group["exists"]:  # WHY: reuse existing groups without hitting mistapi
        logging.info(_GROUP_EXISTS_LOG, group["group_name"], group["group_id"])  # WHY: audit trail
        return  # WHY: skip create call when already present
    create_fn(group, parent.org_id, parent.apisession)  # WHY: parent owns creator (mistapi patched there)


def _build_completed_ids(resume_from: list[dict[str, Any]]) -> set[tuple[str, str]]:  # WHY: extracted set-comp
    """Build the (site_id, group_id) dedupe set from prior assigned rows."""
    return {
        (str(row.get("site_id", "")), str(row.get("group_id", "")))  # WHY: string coercion for stable keys
        for row in resume_from  # WHY: iterate every previously observed result row
        if row.get("status") == _STATUS_ASSIGNED  # WHY: only completed rows count as done
    }

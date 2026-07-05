"""Phase 2 site-variables cluster for the SSID Template Consolidation manager.

Owns the Phase 2 workflow: derive a MISTHELPER_* variable assignment
plan from the Phase 1 cache, display a summary + conflicts table, and
batch-write the plan through ``updateSiteInfo``. Split out of the parent
module so the coordinator stays under the compliance length / block
budgets while the pure helpers remain re-exported via
:mod:`ssid_template_consolidation`.

The ``_write_single_site_vars`` helper is intentionally *not* moved
here: it resolves ``mistapi`` at call time and the historical unit
tests patch ``mistapi`` through the parent module's namespace (e.g.
``patch.object(ssid_template_consolidation, "mistapi", ...)``), which
only intercepts calls whose ``__globals__`` binding *is* the parent
module. Keeping that single helper in the parent preserves those
tests without teaching them about internal module boundaries.
"""

# WHY: cluster methods intentionally reach into the parent manager's private
# helpers (_load_cache, _offer_resume, _save_phase_results, _confirm_or_cancel)
# and defer sibling imports until call-time to break import cycles. The class
# also has only orchestrator methods so pylint's public-method threshold does
# not fit this proxy pattern.
# pylint: disable=protected-access,import-outside-toplevel,too-few-public-methods,cyclic-import

from __future__ import annotations  # WHY: postponed evaluation for forward-ref parent type

from typing import Any  # WHY: broad typing for opaque cache / row payloads

from ._ssid_template_cluster import _ClusterBase  # WHY: shared parent-proxy wrapper

# WHY: module constants centralize magic values referenced by the pure helpers.
_MISTHELPER_PREFIX = "MISTHELPER_"  # WHY: canonical prefix for generated site var names
_CONFLICT_DISPLAY_LIMIT = 10  # WHY: bound console noise to first N conflicts
_CHECKPOINT_INTERVAL = 10  # WHY: flush partial results every N writes for resume safety
_STATUS_PENDING = "pending"  # WHY: entry awaiting write
_STATUS_SKIPPED = "skipped"  # WHY: entry deliberately not written (PSK/anomaly)
_STATUS_CONFIGURED = "already_configured"  # WHY: proposed matches existing value
_STATUS_CONFLICT = "conflict"  # WHY: existing value differs from proposed
_STATUS_WRITTEN = "written"  # WHY: entry successfully persisted (used for resume dedup)

# ---------------------------------------------------------------------------
# Pure module-level helpers
# ---------------------------------------------------------------------------


def _compute_variable_plan(cache: dict[str, Any]) -> list[dict[str, Any]]:  # WHY: entry point for plan build
    """Build variable assignment plan from Phase 1 deviations."""
    deviations = cache.get("deviations", [])  # WHY: canonical deviation list
    matrix = cache.get("matrix", [])  # WHY: per-site rows to visit
    variable_params = _extract_deviation_params(deviations)  # WHY: derive param space
    if not variable_params:  # WHY: nothing to plan when no deviations were found
        return []  # WHY: empty plan short-circuits downstream summary/write steps
    plan: list[dict[str, Any]] = []  # WHY: accumulator for per-site/per-param entries
    for row in matrix:  # WHY: one iteration per candidate site
        plan.extend(_plan_entries_for_row(row, variable_params, cache))  # WHY: fan out row -> N entries
    return plan  # WHY: caller expects flat list of entries


def _plan_entries_for_row(
    row: dict[str, Any],
    variable_params: list[str],
    cache: dict[str, Any],
) -> list[dict[str, Any]]:  # WHY: extracted to keep _compute_variable_plan CC <= 5
    """Build every plan entry for a single matrix row (skip vs. proposal)."""
    if row.get("psk_detected") or row.get("anomaly"):  # WHY: PSK/anomaly rows always skipped
        return [_build_skip_entry(row, param) for param in variable_params]  # WHY: one skip per param
    site_vars = _get_cached_site_vars(cache, row.get("site_id", ""))  # WHY: current per-site vars
    return [_build_variable_entry(row, param, site_vars) for param in variable_params]  # WHY: proposal per param


def _extract_deviation_params(deviations: list[dict[str, Any]]) -> list[str]:  # WHY: builds param space
    """Extract unique parameter names from deviations."""
    params: set[str] = set()  # WHY: dedupe param names across deviations
    for deviation in deviations:  # WHY: scan every recorded deviation
        if deviation.get("cluster_name") != "cross_cluster":  # WHY: only per-cluster deviations
            params.add(deviation.get("parameter", ""))  # WHY: collect the parameter name
    return sorted(params - {""})  # WHY: drop the sentinel empty parameter


def _build_skip_entry(row: dict[str, Any], param: str) -> dict[str, Any]:  # WHY: PSK/anomaly row builder
    """Build a skipped variable entry for PSK/anomaly sites."""
    reason = (  # WHY: reason string differs by skip cause
        "PSK site" if row.get("psk_detected") else f"Anomaly: {row.get('anomaly_reason', '')}"
    )
    return {  # WHY: shape matches _build_variable_entry for uniform downstream handling
        "site_name": row.get("site_name", ""),  # WHY: display label for summary tables
        "site_id": row.get("site_id", ""),  # WHY: identifier for grouping/writes
        "variable_name": f"{_MISTHELPER_PREFIX}{param.upper()}",  # WHY: canonical var naming
        "proposed_value": "",  # WHY: no value proposed for skipped rows
        "current_value": "",  # WHY: skip entries deliberately omit lookup
        "status": _STATUS_SKIPPED,  # WHY: marks entry as intentionally not written
        "reason": reason,  # WHY: user-visible explanation of the skip
        "timestamp": "",  # WHY: populated at write time only
    }


def _get_cached_site_vars(cache: dict[str, Any], site_id: str) -> dict[str, str]:  # WHY: cache lookup helper
    """Get existing site vars from cached org data."""
    for site in cache.get("data", {}).get("sites", []):  # WHY: linear search over cached sites
        if site.get("id") == site_id:  # WHY: found the matching site
            vars_dict: dict[str, str] = site.get("vars", {}) or {}  # WHY: coerce None -> {} for callers
            return vars_dict  # WHY: return the existing var map for comparison
    return {}  # WHY: site not in cache -> treat as empty vars


def _classify_variable(current: str, proposed: str) -> tuple[str, str]:  # WHY: extracted to shrink parent fn
    """Compute (status, reason) for a proposed variable given the current value."""
    if current and current == proposed:  # WHY: same value already stored means no-op
        return _STATUS_CONFIGURED, "Same value already exists"  # WHY: signal skip-write
    if current and current != proposed:  # WHY: existing but differing value -> conflict
        return _STATUS_CONFLICT, f"Existing value: {current}"  # WHY: conflict details for summary
    return _STATUS_PENDING, ""  # WHY: no existing value -> normal write


def _build_variable_entry(
    row: dict[str, Any],
    param: str,
    site_vars: dict[str, str],
) -> dict[str, Any]:  # WHY: builds a single plan entry (proposal path)
    """Build a single variable assignment entry."""
    var_name = f"{_MISTHELPER_PREFIX}{param.upper()}"  # WHY: canonical MISTHELPER_* name
    proposed = str(row.get(param, row.get("vlan_id", "")))  # WHY: vlan_id is the historical default
    current = str(site_vars.get(var_name, ""))  # WHY: existing value drives status classification
    status, reason = _classify_variable(current, proposed)  # WHY: shared status/reason logic
    return {  # WHY: mirrors _build_skip_entry shape for uniform downstream handling
        "site_name": row.get("site_name", ""),  # WHY: display label for summary tables
        "site_id": row.get("site_id", ""),  # WHY: identifier for grouping/writes
        "variable_name": var_name,  # WHY: fully-qualified var name for API payload
        "proposed_value": proposed,  # WHY: value to write on the site
        "current_value": current,  # WHY: preserved for audit / conflict display
        "status": status,  # WHY: drives write vs. skip vs. conflict paths
        "reason": reason,  # WHY: user-visible explanation of the status
        "timestamp": "",  # WHY: populated at write time only
    }


def _count_statuses(plan: list[dict[str, Any]]) -> dict[str, int]:  # WHY: extracted to keep display CC <=5
    """Return counts of pending/configured/conflict/skipped entries in the plan."""
    counts: dict[str, int] = {  # WHY: pre-seed all keys so summary output is stable
        _STATUS_PENDING: 0,
        _STATUS_CONFIGURED: 0,
        _STATUS_CONFLICT: 0,
        _STATUS_SKIPPED: 0,
    }
    for entry in plan:  # WHY: single pass over plan is cheaper than 4 list comps
        status = entry.get("status", "")  # WHY: default guards malformed entries
        if status in counts:  # WHY: ignore statuses we do not summarize
            counts[status] += 1  # WHY: tally the recognized status
    return counts  # WHY: caller renders the summary table from these counts


def _display_variable_summary(plan: list[dict[str, Any]]) -> None:  # WHY: user-facing summary output
    """Display variable assignment summary table."""
    counts = _count_statuses(plan)  # WHY: single-pass tally keeps this function CC low
    print("\n  Variable Assignment Plan:")  # WHY: header aligns with parent phases
    print(f"    Pending:            {counts[_STATUS_PENDING]}")  # WHY: entries queued for write
    print(f"    Already configured: {counts[_STATUS_CONFIGURED]}")  # WHY: no-op count
    print(f"    Conflicts:          {counts[_STATUS_CONFLICT]}")  # WHY: needs operator attention
    print(f"    Skipped:            {counts[_STATUS_SKIPPED]}")  # WHY: PSK/anomaly rows
    if counts[_STATUS_CONFLICT]:  # WHY: only pay for the details table when needed
        conflicts = [e for e in plan if e["status"] == _STATUS_CONFLICT]  # WHY: filter for detail rows
        _print_conflicts(conflicts)  # WHY: render bounded conflict detail table


def _print_conflicts(conflicts: list[dict[str, Any]]) -> None:  # WHY: bounded conflict output
    """Print conflict details for variable summary."""
    print("\n  Conflicts (existing value differs from proposed):")  # WHY: section header
    for entry in conflicts[:_CONFLICT_DISPLAY_LIMIT]:  # WHY: bound console noise to first N
        site = entry["site_name"]  # WHY: readable local for f-string
        var_name = entry["variable_name"]  # WHY: readable local for f-string
        current = entry["current_value"]  # WHY: readable local for f-string
        proposed = entry["proposed_value"]  # WHY: readable local for f-string
        print(f"    {site}: {var_name} = {current} -> {proposed}")  # WHY: one line per conflict
    if len(conflicts) > _CONFLICT_DISPLAY_LIMIT:  # WHY: signal that output was truncated
        print(f"    ... and {len(conflicts) - _CONFLICT_DISPLAY_LIMIT} more")  # WHY: overflow count


def _group_entries_by_site(entries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group variable entries by site_id for batched writes."""
    groups: dict[str, list[dict[str, Any]]] = {}  # WHY: dict groups entries per API call
    for entry in entries:  # WHY: single pass over entries
        groups.setdefault(entry["site_id"], []).append(entry)  # WHY: append to per-site bucket
    return groups  # WHY: caller iterates one call per site_id


def _select_pending_entries(
    plan: list[dict[str, Any]],
    completed_ids: set[Any],
) -> list[dict[str, Any]]:  # WHY: extracted to keep _write_site_variables CC low
    """Filter plan down to pending entries not already completed by prior run."""
    return [  # WHY: comprehension keeps intent obvious
        entry
        for entry in plan
        if entry["status"] == _STATUS_PENDING and entry["site_id"] not in completed_ids  # WHY: resume skip
    ]


def _resume_completed_ids(resume_from: list[dict[str, Any]]) -> set[Any]:  # WHY: helper isolates set logic
    """Collect site_ids that were successfully written in a prior run."""
    return {row.get("site_id") for row in resume_from if row.get("status") == _STATUS_WRITTEN}


# ---------------------------------------------------------------------------
# Cluster class wrapping parent phase-2 orchestrators
# ---------------------------------------------------------------------------


class _SsidTemplatePhase2Cluster(_ClusterBase):
    """Owns the Phase 2 site-variable orchestrator + write coordinator."""

    def phase2_site_variables(self) -> None:  # WHY: user-facing Phase 2 entry point
        """Phase 2 orchestrator - compute variable plan, write to sites."""
        print("\n=== Phase 2: Write Site Variables ===")  # WHY: banner marks phase boundary
        import logging  # noqa: PLC0415 — kept local so this cluster ships zero import-time deps

        logging.info("Phase 2: Starting site variable configuration")  # WHY: audit trail
        if not self._load_cache_or_bail():  # WHY: cache preamble aborts on missing Phase 1
            return
        plan = _compute_variable_plan(self._mm.cache)  # WHY: derive plan from cached deviations
        if not plan:  # WHY: nothing to configure means we exit cleanly
            print("  No site variables to configure (no deviations detected).")
            return
        _display_variable_summary(plan)  # WHY: show operator the counts + conflicts
        if not self._confirm_phase2_write(plan):  # WHY: confirmation is user-blocking
            return
        self._execute_phase2_plan(plan)  # WHY: delegate write orchestration to helper

    def _confirm_phase2_write(self, plan: list[dict[str, Any]]) -> bool:  # WHY: isolates the prompt path
        """Prompt the operator to proceed with the pending write count."""
        pending = sum(1 for p in plan if p["status"] == _STATUS_PENDING)  # WHY: only pending drives writes
        return bool(self._mm._confirm_or_cancel(f"Write site variables for {pending} sites?"))  # noqa: SLF001

    def _execute_phase2_plan(self, plan: list[dict[str, Any]]) -> None:  # WHY: post-confirm coordinator
        """Run resume + write + persist + summary in one flow."""
        parent = self._mm  # WHY: proxy alias for readability + W0212 avoidance
        resuming, prior_results = parent._offer_resume(2, [])  # noqa: SLF001
        results = self._call("_write_site_variables", plan, prior_results if resuming else [])
        parent._save_phase_results(2, results)  # noqa: SLF001
        parent.write_data_fn(  # WHY: persist to org-scoped sink for later phases
            data=results,
            filename_or_table="ssid_consolidation_site_vars",
            api_function_name="ssidConsolidationSiteVars",
        )
        # WHY: phase45 owns the shared summary helper — import directly to avoid
        # routing through the parent module (mypy [attr-defined] on re-export).
        from ._ssid_template_phase45 import (
            _print_phase_summary,  # noqa: PLC0415 — local import keeps import graph shallow
        )

        _print_phase_summary("Phase 2", results)  # WHY: one-line status footer for operator

    def _write_site_variables(
        self,
        plan: list[dict[str, Any]],
        resume_from: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Write site variables via updateSiteInfo."""
        parent = self._mm  # WHY: proxy alias for readability
        completed_ids = _resume_completed_ids(resume_from)  # WHY: dedupe against previous run
        results: list[dict[str, Any]] = list(resume_from) if resume_from else []  # WHY: seed with priors
        pending_entries = _select_pending_entries(plan, completed_ids)  # WHY: only write what remains
        site_groups = _group_entries_by_site(pending_entries)  # WHY: one API call per site
        # WHY: parent owns the per-site writer so tests can patch mistapi at the parent module.
        from .ssid_template_consolidation import _write_single_site_vars  # noqa: PLC0415 — local import breaks cycle

        for site_id, entries in site_groups.items():  # WHY: iterate the batched writes
            result = _write_single_site_vars(site_id, entries, parent.cache, parent.apisession)
            results.extend(result)  # WHY: accumulate per-site results
            if len(results) % _CHECKPOINT_INTERVAL == 0:  # WHY: bounded checkpoint cadence
                parent._save_phase_results(2, results)  # noqa: SLF001 — intra-package checkpoint
        return results  # WHY: caller feeds this into _save_phase_results + write_data_fn

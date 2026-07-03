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

# ---------------------------------------------------------------------------
# Pure module-level helpers
# ---------------------------------------------------------------------------


def _compute_variable_plan(
    cache: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build variable assignment plan from Phase 1 deviations."""
    deviations = cache.get("deviations", [])  # WHY: canonical deviation list
    matrix = cache.get("matrix", [])  # WHY: per-site rows to visit
    variable_params = _extract_deviation_params(deviations)  # WHY: derive param space
    if not variable_params:
        return []  # WHY: nothing to plan when no deviations were found

    plan: list[dict[str, Any]] = []
    for row in matrix:
        if row.get("psk_detected") or row.get("anomaly"):
            for param in variable_params:
                plan.append(_build_skip_entry(row, param))  # WHY: PSK/anomaly rows skipped
            continue
        site_vars = _get_cached_site_vars(cache, row.get("site_id", ""))  # WHY: current per-site vars
        for param in variable_params:
            entry = _build_variable_entry(row, param, site_vars)
            plan.append(entry)
    return plan


def _extract_deviation_params(
    deviations: list[dict[str, Any]],
) -> list[str]:
    """Extract unique parameter names from deviations."""
    params: set[str] = set()
    for deviation in deviations:
        if deviation.get("cluster_name") != "cross_cluster":  # WHY: only per-cluster deviations
            params.add(deviation.get("parameter", ""))
    return sorted(params - {""})  # WHY: drop the sentinel empty parameter


def _build_skip_entry(row: dict[str, Any], param: str) -> dict[str, Any]:
    """Build a skipped variable entry for PSK/anomaly sites."""
    reason = "PSK site" if row.get("psk_detected") else f"Anomaly: {row.get('anomaly_reason', '')}"
    return {
        "site_name": row.get("site_name", ""),
        "site_id": row.get("site_id", ""),
        "variable_name": f"MISTHELPER_{param.upper()}",
        "proposed_value": "",
        "current_value": "",
        "status": "skipped",
        "reason": reason,
        "timestamp": "",
    }


def _get_cached_site_vars(cache: dict[str, Any], site_id: str) -> dict[str, str]:
    """Get existing site vars from cached org data."""
    for site in cache.get("data", {}).get("sites", []):  # WHY: linear search over cached sites
        if site.get("id") == site_id:
            vars_dict: dict[str, str] = site.get("vars", {}) or {}
            return vars_dict
    return {}


def _build_variable_entry(
    row: dict[str, Any],
    param: str,
    site_vars: dict[str, str],
) -> dict[str, Any]:
    """Build a single variable assignment entry."""
    var_name = f"MISTHELPER_{param.upper()}"
    proposed = str(row.get(param, row.get("vlan_id", "")))  # WHY: vlan_id is the historical default
    current = str(site_vars.get(var_name, ""))

    if current and current == proposed:
        status = "already_configured"
        reason = "Same value already exists"
    elif current and current != proposed:
        status = "conflict"
        reason = f"Existing value: {current}"
    else:
        status = "pending"
        reason = ""

    return {
        "site_name": row.get("site_name", ""),
        "site_id": row.get("site_id", ""),
        "variable_name": var_name,
        "proposed_value": proposed,
        "current_value": current,
        "status": status,
        "reason": reason,
        "timestamp": "",
    }


def _display_variable_summary(
    plan: list[dict[str, Any]],
) -> None:
    """Display variable assignment summary table."""
    pending = [e for e in plan if e["status"] == "pending"]
    skipped = [e for e in plan if e["status"] == "skipped"]
    configured = [e for e in plan if e["status"] == "already_configured"]
    conflicts = [e for e in plan if e["status"] == "conflict"]

    print("\n  Variable Assignment Plan:")
    print(f"    Pending:            {len(pending)}")
    print(f"    Already configured: {len(configured)}")
    print(f"    Conflicts:          {len(conflicts)}")
    print(f"    Skipped:            {len(skipped)}")

    if conflicts:
        _print_conflicts(conflicts)  # WHY: only pay for the details table when needed


def _print_conflicts(conflicts: list[dict[str, Any]]) -> None:
    """Print conflict details for variable summary."""
    print("\n  Conflicts (existing value differs from proposed):")
    for entry in conflicts[:10]:  # WHY: bound console noise to first 10
        site = entry["site_name"]
        var_name = entry["variable_name"]
        current = entry["current_value"]
        proposed = entry["proposed_value"]
        print(f"    {site}: {var_name} = {current} -> {proposed}")
    if len(conflicts) > 10:
        print(f"    ... and {len(conflicts) - 10} more")


def _group_entries_by_site(
    entries: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group variable entries by site_id for batched writes."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        groups.setdefault(entry["site_id"], []).append(entry)
    return groups


# ---------------------------------------------------------------------------
# Cluster class wrapping parent phase-2 orchestrators
# ---------------------------------------------------------------------------


class _SsidTemplatePhase2Cluster(_ClusterBase):
    """Owns the Phase 2 site-variable orchestrator + write coordinator."""

    def phase2_site_variables(self) -> None:
        """Phase 2 orchestrator — compute variable plan, write to sites."""
        parent = self._mm  # WHY: proxy alias for readability + W0212 avoidance
        print("\n=== Phase 2: Write Site Variables ===")
        import logging  # noqa: PLC0415 — kept local so this cluster ships zero import-time deps

        logging.info("Phase 2: Starting site variable configuration")

        if not self._load_cache_or_bail():
            return

        resuming, prior_results = parent._offer_resume(2, [])  # noqa: SLF001
        plan = _compute_variable_plan(parent.cache)
        if not plan:
            print("  No site variables to configure (no deviations detected).")
            return

        _display_variable_summary(plan)
        pending = len([p for p in plan if p["status"] == "pending"])
        if not parent._confirm_or_cancel(f"Write site variables for {pending} sites?"):  # noqa: SLF001
            return

        results = self._call("_write_site_variables", plan, prior_results if resuming else [])
        parent._save_phase_results(2, results)  # noqa: SLF001
        parent.write_data_fn(
            data=results,
            filename_or_table="ssid_consolidation_site_vars",
            api_function_name="ssidConsolidationSiteVars",
        )
        # WHY: phase45 owns the shared summary helper — import directly to avoid
        # routing through the parent module (mypy [attr-defined] on re-export).
        from ._ssid_template_phase45 import (
            _print_phase_summary,  # noqa: PLC0415 — local import keeps import graph shallow
        )

        _print_phase_summary("Phase 2", results)

    def _write_site_variables(
        self,
        plan: list[dict[str, Any]],
        resume_from: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Write site variables via updateSiteInfo."""
        parent = self._mm  # WHY: proxy alias
        completed_ids = {row.get("site_id") for row in resume_from if row.get("status") == "written"}
        results: list[dict[str, Any]] = list(resume_from) if resume_from else []

        pending_entries = [
            entry for entry in plan if entry["status"] == "pending" and entry["site_id"] not in completed_ids
        ]
        site_groups = _group_entries_by_site(pending_entries)

        # WHY: parent owns the per-site writer so tests can patch mistapi at the parent module.
        from .ssid_template_consolidation import _write_single_site_vars  # noqa: PLC0415 — local import breaks cycle

        for site_id, entries in site_groups.items():
            result = _write_single_site_vars(site_id, entries, parent.cache, parent.apisession)
            results.extend(result)
            if len(results) % 10 == 0:
                parent._save_phase_results(2, results)  # noqa: SLF001 — intra-package checkpoint

        return results

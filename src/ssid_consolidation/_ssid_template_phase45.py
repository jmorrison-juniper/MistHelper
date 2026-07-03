"""Phase 4 & 5 templates+disable cluster for the SSID Template Consolidation manager.

Owns the Phase 4 (create consolidated templates) and Phase 5 (disable
old SSIDs) workflows plus the pure helpers that shape their plans.
Split out of the parent module so the coordinator stays under the
compliance length / block budgets while the pure helpers remain
re-exported via :mod:`ssid_template_consolidation`.

Two dataclasses are also defined here:

* :class:`TemplateOpParams` bundles the eight shared parameters
  consumed by every template create/update helper so their signatures
  collapse to two arguments (the params bundle plus at most one extra
  positional). Without the bundle every worker would exceed the
  STRUCT-PARAMS limit of five.
* :class:`TemplateOutcome` bundles the result-side fields for
  :func:`_template_result` so its signature stays within budget.

The four mistapi-touching helpers (``_create_or_update_single_template``,
``_handle_existing_non_misthelper``, ``_append_ssid_to_template``,
``_create_new_template``) and ``_disable_single_ssid`` are intentionally
*not* moved here: they resolve ``mistapi`` at call time and the historical
unit tests patch ``mistapi`` through the parent module's namespace
(e.g. ``patch.object(ssid_template_consolidation, "mistapi", ...)``),
which only intercepts calls whose ``__globals__`` binding *is* the
parent module. Keeping those five helpers in the parent preserves those
tests without teaching them about internal module boundaries.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref parent type

import json  # WHY: deviation ``unique_values`` are stored as JSON strings
import logging  # WHY: workflow telemetry across phases 4 + 5
import os  # WHY: MIST_TEMPLATE_BASENAME env override lookup
from dataclasses import dataclass  # WHY: bundle template-op params + result payload
from datetime import datetime  # WHY: ISO timestamps for template + disable operations
from typing import Any  # WHY: broad typing for opaque cache / row payloads

from ._ssid_template_cluster import _ClusterBase  # WHY: shared parent-proxy wrapper

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
SafeInputFn = Any  # WHY: Callable[[str, ...], str] — kept opaque so tests can inject MagicMock

# ---------------------------------------------------------------------------
# Bundle dataclasses (STRUCT-PARAMS remediation)
# ---------------------------------------------------------------------------


@dataclass
class TemplateOpParams:
    """Bundle of shared arguments for template create/update helpers.

    The historical helper trio (``_create_new_template``,
    ``_append_ssid_to_template``, ``_handle_existing_non_misthelper``)
    each accepted 7-8 positional arguments, violating the 5-parameter
    STRUCT-PARAMS limit. Collapsing the recurring set into this frozen
    bundle brings every caller to at most two arguments (bundle + one
    optional extra like ``existing`` for the append variant).
    """

    template_name: str  # WHY: fully-qualified template name (misthelper_<group>_<basename>)
    wlan_config: dict[str, Any]  # WHY: WLAN config dict to write / append
    group_info: dict[str, str]  # WHY: group_id + cluster_name for the target sitegroup
    timestamp: str  # WHY: single ISO timestamp shared by every result row
    target_ssid: str  # WHY: SSID name used for dedupe when appending to existing template
    org_id: str  # WHY: org scope for mistapi calls
    apisession: Any  # WHY: mistapi.APISession handle
    safe_input_fn: SafeInputFn  # WHY: prompt user when overwrite confirmation is needed


@dataclass
class TemplateOutcome:
    """Result payload for :func:`_template_result`.

    Separates the three "variable" outcome fields (template_id, action,
    error) from the identity fields already carried by
    :class:`TemplateOpParams` (template_name, group_info, timestamp),
    so the result builder stays within STRUCT-PARAMS budget.
    """

    template_id: str  # WHY: id returned by createOrgTemplate / existing template id
    action: str  # WHY: "created" | "updated_append" | "skipped" | "already_exists" | "failed"
    error: str = ""  # WHY: exception message on failure; empty on success


# ---------------------------------------------------------------------------
# Phase 4 pure helpers
# ---------------------------------------------------------------------------


def _resolve_deviations(cache: dict[str, Any], safe_input_fn: SafeInputFn) -> dict[tuple[str, str], Any]:
    """Interactively resolve deviations — no pre-selected default."""
    deviations = cache.get("deviations", [])  # WHY: canonical deviation list from Phase 1
    resolutions: dict[tuple[str, str], Any] = {}  # WHY: (cluster, param) -> chosen value

    for deviation in deviations:
        if deviation.get("cluster_name") == "cross_cluster":
            continue  # WHY: cross-cluster deviations resolved separately (drift record)
        _resolve_single_deviation(deviation, resolutions, safe_input_fn)
    return resolutions


def _resolve_single_deviation(
    deviation: dict[str, Any],
    resolutions: dict[tuple[str, str], Any],
    safe_input_fn: SafeInputFn,
) -> None:
    """Resolve a single deviation interactively."""
    cluster = deviation.get("cluster_name", "")  # WHY: keyed by cluster for per-cluster resolution
    param = deviation.get("parameter", "")  # WHY: parameter name being consolidated
    unique_values: list[dict[str, Any]] = json.loads(deviation.get("unique_values", "[]"))
    _print_deviation_choices(param, cluster, unique_values)
    _record_deviation_choice(cluster, param, unique_values, resolutions, safe_input_fn)


def _print_deviation_choices(
    param: str,
    cluster: str,
    unique_values: list[dict[str, Any]],
) -> None:
    """Print the numbered list of candidate values for a deviation."""
    print(f"\n  Deviation: {param} in cluster '{cluster}'")  # WHY: header per deviation
    for index, entry in enumerate(unique_values, 1):
        sites_preview = ", ".join(entry["sites"][:3])  # WHY: bound preview to 3 site names
        print(f"    {index}. {entry['value']} " f"({entry['count']} sites: {sites_preview})")
        if len(entry["sites"]) > 3:
            remaining = len(entry["sites"]) - 3  # WHY: report tail count without noise
            print(f"       ... and {remaining} more sites")


def _record_deviation_choice(
    cluster: str,
    param: str,
    unique_values: list[dict[str, Any]],
    resolutions: dict[tuple[str, str], Any],
    safe_input_fn: SafeInputFn,
) -> None:
    """Prompt operator and record the chosen canonical value."""
    choice: str = safe_input_fn(
        f"  Select canonical value [1-{len(unique_values)}]: ",
        context="ssid_consolidation_deviation_resolution",
    )
    try:
        selected_index = int(choice) - 1  # WHY: 1-based menu -> 0-based index
        if 0 <= selected_index < len(unique_values):
            selected = unique_values[selected_index]["value"]  # WHY: canonical value chosen
            resolutions[(cluster, param)] = selected
            logging.info(
                "Deviation resolved: %s/%s = %s " "(selected from %d options at %s)",
                cluster,
                param,
                selected,
                len(unique_values),
                datetime.now().isoformat(),
            )
        else:
            print(f"  ! Invalid selection. Skipping {param}.")
    except ValueError:
        print(f"  ! Invalid input. Skipping {param}.")


def _load_group_plan_from_results(
    phase3_results: dict[str, Any],
) -> dict[str, dict[str, str]]:
    """Extract group_name -> group_id mapping from Phase 3 results."""
    group_map: dict[str, dict[str, str]] = {}  # WHY: dedup by group_name for stable ordering
    for result in phase3_results.get("results", []):
        group_name = result.get("group_name", "")
        if group_name and group_name not in group_map:
            group_map[group_name] = {
                "group_id": result.get("group_id", ""),
                "cluster_name": result.get("cluster_name", ""),
            }
    return group_map


def _build_all_template_configs(
    group_plan: dict[str, dict[str, str]],
    resolutions: dict[tuple[str, str], Any],
    cache: dict[str, Any],
    target_ssid: str,
) -> dict[str, dict[str, Any]]:
    """Build WLAN configs for each group's template."""
    configs: dict[str, dict[str, Any]] = {}  # WHY: keyed by group_name for downstream iteration
    for group_name, group_info in group_plan.items():
        cluster = group_info.get("cluster_name", "")  # WHY: cluster drives the deviation set
        config = _build_template_config(cluster, resolutions, cache, target_ssid)
        configs[group_name] = config
    return configs


def _build_template_config(
    cluster_name: str,
    resolutions: dict[tuple[str, str], Any],
    cache: dict[str, Any],
    target_ssid: str,
) -> dict[str, Any]:
    """Build a single WLAN config with variable refs for deviations."""
    deviation_params = _cluster_deviation_params(cache, cluster_name)  # WHY: params needing var refs
    representative = _find_representative(cache, cluster_name)  # WHY: source row for concrete values
    config: dict[str, Any] = {"ssid": target_ssid, "enabled": True}
    if representative:
        _populate_from_representative(config, representative, deviation_params)
    for param in deviation_params:
        if param not in ("vlan_id",):
            config[param] = f"{{{{MISTHELPER_{param.upper()}}}}}"  # WHY: variable placeholder
    return config


def _cluster_deviation_params(cache: dict[str, Any], cluster_name: str) -> set[str]:
    """Return the set of parameter names that deviate within a cluster."""
    deviations = cache.get("deviations", [])  # WHY: iterate over Phase-1 deviation records
    return {
        param  # WHY: bind local so mypy narrows to str after the None filter below
        for dev in deviations
        if dev.get("cluster_name") == cluster_name and dev.get("cluster_name") != "cross_cluster"
        for param in (dev.get("parameter"),)
        if isinstance(param, str)
    }


def _find_representative(cache: dict[str, Any], cluster_name: str) -> dict[str, Any] | None:
    """Find a representative matrix row for the cluster."""
    matrix: list[dict[str, Any]] = cache.get("matrix", [])  # WHY: per-site rows from Phase 1
    primary = _first_clean_row(matrix, cluster_name)  # WHY: prefer same-cluster clean row
    if primary is not None:
        return primary
    return _first_clean_row(matrix, "pilot")  # WHY: fall back to pilot when cluster is empty


def _first_clean_row(matrix: list[dict[str, Any]], target_group: str) -> dict[str, Any] | None:
    """Return the first non-anomaly, non-PSK row for a target group."""
    for row in matrix:
        if row.get("target_group") == target_group and not row.get("anomaly") and not row.get("psk_detected"):
            return row  # WHY: first clean row is sufficient — no need to score
    return None


def _populate_from_representative(
    config: dict[str, Any],
    representative: dict[str, Any],
    deviation_params: set[str],
) -> None:
    """Populate template config from representative row."""
    if "vlan_id" in deviation_params:
        config["vlan_id"] = "{{MISTHELPER_VLAN_ID}}"  # WHY: vlan varies per site -> variable ref
    else:
        config["vlan_id"] = representative.get("vlan_id", "")  # WHY: no deviation -> concrete value
    config["auth"] = {"type": representative.get("auth_type", "")}  # WHY: auth mirrors representative
    mxtunnel_id = representative.get("mxtunnel_id", "")  # WHY: only set when tunneling is in use
    if mxtunnel_id:
        config["mxtunnel_ids"] = [mxtunnel_id]


def _display_template_plan(
    configs: dict[str, dict[str, Any]],
    group_plan: dict[str, dict[str, str]],
) -> None:
    """Print template creation plan."""
    print("\n  Template Plan:")  # WHY: header separates the plan from prior output
    for group_name, config in configs.items():
        group_info = group_plan.get(group_name, {})  # WHY: recover group_id for display
        group_id = group_info.get("group_id", "new")
        print(f"    {group_name} (group_id={group_id})")
        print(f"      SSID: {config.get('ssid', '')}")
        for key, value in config.items():
            if key != "ssid":
                print(f"      {key}: {value}")


# ---------------------------------------------------------------------------
# Phase 5 pure helpers
# ---------------------------------------------------------------------------


def _build_disable_plan(
    cache: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build plan for disabling old SSIDs."""
    matrix = cache.get("matrix", [])  # WHY: per-site rows drive the disable decision
    plan: list[dict[str, Any]] = []
    for row in matrix:
        plan.append(_classify_disable_entry(row))
    return plan


def _classify_disable_entry(
    row: dict[str, Any],
) -> dict[str, Any]:
    """Classify a single site for disable action."""
    base = _build_disable_base(row)  # WHY: build shared identity fields first
    skip = _skip_reason_for_row(row)  # WHY: consolidate the 4 skip predicates
    if skip is not None:
        status, reason = skip
        base["status"] = status
        base["reason"] = reason
        return base
    base["status"] = "to_disable"  # WHY: default action when no skip predicate fired
    base["reason"] = ""
    return base


def _skip_reason_for_row(row: dict[str, Any]) -> tuple[str, str] | None:
    """Return (status, reason) if the row should be skipped, else None."""
    if row.get("psk_detected"):
        return ("skipped", "PSK site")  # WHY: PSK sites never take part in consolidation
    if row.get("anomaly"):
        return ("skipped", f"Anomaly: {row.get('anomaly_reason', '')}")
    if not row.get("ssid_enabled", True):
        return ("already_disabled", "SSID already disabled")  # WHY: idempotent no-op
    if not row.get("ssid_id"):
        return ("skipped", "No SSID ID found")
    return None


def _build_disable_base(row: dict[str, Any]) -> dict[str, Any]:
    """Build base dictionary for a disable plan entry."""
    return {
        "site_name": row.get("site_name", ""),
        "site_id": row.get("site_id", ""),
        "old_template_name": row.get("template_name", ""),
        "old_template_id": row.get("template_id", ""),
        "ssid_name": row.get("ssid_name", ""),
        "ssid_id": row.get("ssid_id", ""),
        "previous_enabled": row.get("ssid_enabled", True),
        "timestamp": "",
    }


def _display_disable_plan(
    plan: list[dict[str, Any]],
) -> None:
    """Print disable plan summary."""
    counts = _partition_disable_plan(plan)  # WHY: single pass over the plan
    print("\n  Disable Plan:")
    print(f"    To disable:       {counts['to_disable']}")
    print(f"    Already disabled: {counts['already_disabled']}")
    print(f"    Skipped:          {counts['skipped']}")


def _partition_disable_plan(plan: list[dict[str, Any]]) -> dict[str, int]:
    """Count disable-plan entries by status."""
    counts = {"to_disable": 0, "already_disabled": 0, "skipped": 0}  # WHY: fixed set of buckets
    for entry in plan:
        status = entry.get("status", "")
        if status in counts:
            counts[status] += 1
    return counts


def _set_ssid_disabled(wlans: list[dict[str, Any]], ssid_id: str) -> bool:
    """Set enabled=False on the matching SSID. Returns True if found."""
    for wlan in wlans:
        if wlan.get("id") == ssid_id:
            wlan["enabled"] = False  # WHY: mutate in place — caller reuses the list
            return True
    return False


# ---------------------------------------------------------------------------
# Shared output helper
# ---------------------------------------------------------------------------


def _print_phase_summary(phase_label: str, results: list[dict[str, Any]]) -> None:
    """Print a summary of phase results by status."""
    status_counts: dict[str, int] = {}  # WHY: aggregate over heterogeneous status field
    for result in results:
        status = result.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    print(f"\n  {phase_label} Summary:")
    for status, count in sorted(status_counts.items()):
        print(f"    {status}: {count}")


# ---------------------------------------------------------------------------
# Cluster class wrapping parent phase-4 + phase-5 orchestrators
# ---------------------------------------------------------------------------


class _SsidTemplatePhase45Cluster(_ClusterBase):
    """Owns the Phase 4 + Phase 5 orchestrators and their coordinators."""

    def phase4_templates(self) -> None:
        """Phase 4 orchestrator — resolve deviations, create templates."""
        parent = self._mm  # WHY: proxy alias for readability + W0212 avoidance
        print("\n=== Phase 4: Create Consolidated Templates ===")
        logging.info("Phase 4: Starting template creation")

        preflight = self._phase4_preflight()  # WHY: split cache + plan build out of orchestrator
        if preflight is None:
            return
        group_plan, configs = preflight

        _display_template_plan(configs, group_plan)
        if not parent._confirm_or_cancel(f"Create/update {len(configs)} templates?"):  # noqa: SLF001
            return

        results = self._call("_create_or_update_templates", configs, group_plan)
        parent._save_phase_results(4, results)  # noqa: SLF001 — intra-package checkpoint
        parent.write_data_fn(
            data=results,
            filename_or_table="ssid_consolidation_templates",
            api_function_name="ssidConsolidationTemplates",
        )
        _print_phase_summary("Phase 4", results)

    def _phase4_preflight(
        self,
    ) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, Any]]] | None:
        """Load cache + phase-3 results, resolve deviations, build template configs."""
        parent = self._mm  # WHY: proxy alias
        cached = parent._load_cache()  # noqa: SLF001 — cluster helper is intra-package
        if not cached:
            print("! Phase 1 cache not found. Run Phase 1 first.")
            return None
        parent.cache = cached

        phase3_results = parent._load_phase_results(3)  # noqa: SLF001
        if not phase3_results:
            print("! Phase 3 results not found. Run Phase 3 first.")
            return None

        resolutions = _resolve_deviations(parent.cache, parent.safe_input_fn)
        group_plan = _load_group_plan_from_results(phase3_results)
        configs = _build_all_template_configs(group_plan, resolutions, parent.cache, parent.target_ssid)
        return group_plan, configs

    def _create_or_update_templates(
        self,
        configs: dict[str, dict[str, Any]],
        group_plan: dict[str, dict[str, str]],
    ) -> list[dict[str, Any]]:
        """Create or update templates for each group."""
        parent = self._mm  # WHY: proxy alias
        basename = os.environ.get("MIST_TEMPLATE_BASENAME", parent.target_ssid)
        existing_templates = {
            tmpl.get("name", ""): tmpl for tmpl in parent.cache.get("data", {}).get("wlan_templates", [])
        }
        # WHY: parent owns the mistapi-touching worker so tests can patch mistapi at parent.
        from .ssid_template_consolidation import (  # noqa: PLC0415 — local import breaks cycle
            _create_or_update_single_template,
        )

        results: list[dict[str, Any]] = []
        for group_name, config in configs.items():
            params = TemplateOpParams(
                template_name=f"misthelper_{group_name}_{basename}",
                wlan_config=config,
                group_info=group_plan.get(group_name, {}),
                timestamp=datetime.now().isoformat(),
                target_ssid=parent.target_ssid,
                org_id=parent.org_id,
                apisession=parent.apisession,
                safe_input_fn=parent.safe_input_fn,
            )
            results.append(_create_or_update_single_template(params, existing_templates))
        return results

    def phase5_disable_old(self) -> None:
        """Phase 5 orchestrator — disable matching SSIDs in old templates."""
        parent = self._mm  # WHY: proxy alias
        print("\n=== Phase 5: Disable Old SSIDs ===")
        logging.info("Phase 5: Starting old SSID disable")

        prep = self._phase5_prepare_plan()  # WHY: split cache + plan build out of orchestrator
        if prep is None:
            return
        resuming, prior_results, plan, to_disable = prep

        if not to_disable:
            print("  No SSIDs to disable.")
            return
        if not parent._confirm_or_cancel(f"Disable {len(to_disable)} SSIDs in old templates?"):  # noqa: SLF001
            return

        results = self._call("_disable_ssids", plan, prior_results if resuming else [])
        parent._save_phase_results(5, results)  # noqa: SLF001
        parent.write_data_fn(
            data=results,
            filename_or_table="ssid_consolidation_disable",
            api_function_name="ssidConsolidationDisable",
        )
        _print_phase_summary("Phase 5", results)

    def _phase5_prepare_plan(
        self,
    ) -> tuple[bool, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]] | None:
        """Load cache, offer resume, and build the disable plan."""
        parent = self._mm  # WHY: proxy alias
        cached = parent._load_cache()  # noqa: SLF001
        if not cached:
            print("! Phase 1 cache not found. Run Phase 1 first.")
            return None
        parent.cache = cached

        resuming, prior_results = parent._offer_resume(5, [])  # noqa: SLF001
        plan = _build_disable_plan(parent.cache)
        to_disable = [entry for entry in plan if entry["status"] == "to_disable"]
        _display_disable_plan(plan)
        return resuming, prior_results, plan, to_disable

    def _disable_ssids(
        self,
        plan: list[dict[str, Any]],
        resume_from: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Disable SSIDs in old templates via GET-modify-PUT."""
        parent = self._mm  # WHY: proxy alias
        completed_ids = self._collect_completed_ids(resume_from)
        results: list[dict[str, Any]] = list(resume_from) if resume_from else []

        # WHY: parent owns the mistapi-touching worker so tests can patch mistapi at parent.
        from .ssid_template_consolidation import _disable_single_ssid  # noqa: PLC0415 — local import breaks cycle

        for entry in plan:
            key = (entry.get("site_id"), entry.get("ssid_id"))
            if entry["status"] != "to_disable":
                if key not in completed_ids:
                    results.append(entry)  # WHY: preserve non-actionable rows in results
                continue
            if key in completed_ids:
                continue  # WHY: resume-safe — skip rows already disabled last run
            results.append(_disable_single_ssid(entry, parent.org_id, parent.apisession))
            if len(results) % 10 == 0:
                parent._save_phase_results(5, results)  # noqa: SLF001 — intra-package checkpoint
        return results

    @staticmethod
    def _collect_completed_ids(
        resume_from: list[dict[str, Any]],
    ) -> set[tuple[str | None, str | None]]:
        """Extract (site_id, ssid_id) pairs already disabled in a prior run."""
        return {(row.get("site_id"), row.get("ssid_id")) for row in resume_from if row.get("status") == "disabled"}

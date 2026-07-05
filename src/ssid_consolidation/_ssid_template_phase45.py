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

# WHY: cluster methods intentionally reach into the parent manager's private
# helpers (_load_cache, _offer_resume, _save_phase_results, _confirm_or_cancel)
# and defer sibling imports until call-time to break import cycles. The class
# also has only orchestrator methods so pylint's public-method threshold does
# not fit this proxy pattern.
# pylint: disable=protected-access,import-outside-toplevel,too-few-public-methods,cyclic-import

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
# Module-level constants (magic value hoisting)
# ---------------------------------------------------------------------------
_CROSS_CLUSTER = "cross_cluster"  # WHY: sentinel cluster name resolved by drift path, not deviations
_PILOT_GROUP = "pilot"  # WHY: fallback target_group when the cluster has no clean row
_VLAN_ID_KEY = "vlan_id"  # WHY: parameter name given special-cased handling in template config
_VLAN_ID_VAR = "{{MISTHELPER_VLAN_ID}}"  # WHY: variable placeholder written when vlan varies per site
_MISTHELPER_PREFIX = "misthelper_"  # WHY: template-name prefix identifying MistHelper-owned rows
_TEMPLATE_BASENAME_ENV = "MIST_TEMPLATE_BASENAME"  # WHY: env override for the shared template suffix
_DEVIATION_CONTEXT = "ssid_consolidation_deviation_resolution"  # WHY: safe_input_fn context tag
_PHASE4_ID = 4  # WHY: phase index for save_phase_results / write_data_fn dispatch
_PHASE4_LABEL = "Phase 4"  # WHY: label used by _print_phase_summary for the templates phase
_PHASE4_HEADER = "\n=== Phase 4: Create Consolidated Templates ==="  # WHY: user-facing banner
_PHASE4_START_LOG = "Phase 4: Starting template creation"  # WHY: startup log line for phase 4
_PHASE4_WRITE_FILENAME = "ssid_consolidation_templates"  # WHY: parquet/table sink label for phase 4
_PHASE4_WRITE_API_NAME = "ssidConsolidationTemplates"  # WHY: mist API function tag for phase 4 write
_PHASE5_ID = 5  # WHY: phase index for save_phase_results / offer_resume dispatch
_PHASE5_LABEL = "Phase 5"  # WHY: label used by _print_phase_summary for the disable phase
_PHASE5_HEADER = "\n=== Phase 5: Disable Old SSIDs ==="  # WHY: user-facing banner
_PHASE5_START_LOG = "Phase 5: Starting old SSID disable"  # WHY: startup log line for phase 5
_PHASE5_WRITE_FILENAME = "ssid_consolidation_disable"  # WHY: parquet/table sink label for phase 5
_PHASE5_WRITE_API_NAME = "ssidConsolidationDisable"  # WHY: mist API function tag for phase 5 write
_STATUS_TO_DISABLE = "to_disable"  # WHY: default action tag for actionable disable-plan rows
_STATUS_ALREADY_DISABLED = "already_disabled"  # WHY: idempotent tag when SSID was already disabled
_STATUS_SKIPPED = "skipped"  # WHY: tag when a row is skipped (PSK / anomaly / missing SSID id)
_STATUS_DISABLED = "disabled"  # WHY: success tag written by _disable_single_ssid after PUT
_REASON_PSK = "PSK site"  # WHY: skip reason string for PSK-detected rows
_REASON_ALREADY = "SSID already disabled"  # WHY: skip reason string for pre-disabled rows
_REASON_NO_ID = "No SSID ID found"  # WHY: skip reason string when no ssid_id is present
_DISABLE_CHECKPOINT_INTERVAL = 10  # WHY: rows-per-checkpoint cadence for phase 5 save
_SITES_PREVIEW_LIMIT = 3  # WHY: bound console noise when printing candidate site names
_DEVIATION_LOG_MSG = (  # WHY: single audit-log format string for deviation resolutions
    "Deviation resolved: %s/%s = %s (selected from %d options at %s)"
)

# ---------------------------------------------------------------------------
# Bundle dataclasses (STRUCT-PARAMS remediation)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)  # WHY: immutable slotted bundle keeps callers under 5-arg budget
class TemplateOpParams:  # pylint: disable=too-many-instance-attributes
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


@dataclass(frozen=True, slots=True)  # WHY: immutable slotted result payload for _template_result
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
# Phase 4 pure helpers — deviation resolution
# ---------------------------------------------------------------------------


def _resolve_deviations(cache: dict[str, Any], safe_input_fn: SafeInputFn) -> dict[tuple[str, str], Any]:
    """Interactively resolve deviations — no pre-selected default."""
    deviations = cache.get("deviations", [])  # WHY: canonical deviation list from Phase 1
    resolutions: dict[tuple[str, str], Any] = {}  # WHY: (cluster, param) -> chosen value
    for deviation in deviations:  # WHY: process every candidate row from Phase 1
        if deviation.get("cluster_name") == _CROSS_CLUSTER:  # WHY: drift path owns cross-cluster rows
            continue  # WHY: cross-cluster deviations resolved separately (drift record)
        _resolve_single_deviation(deviation, resolutions, safe_input_fn)  # WHY: per-row interactive prompt
    return resolutions  # WHY: mapping consumed by _build_template_config


def _resolve_single_deviation(
    deviation: dict[str, Any],
    resolutions: dict[tuple[str, str], Any],
    safe_input_fn: SafeInputFn,
) -> None:
    """Resolve a single deviation interactively."""
    cluster = deviation.get("cluster_name", "")  # WHY: keyed by cluster for per-cluster resolution
    param = deviation.get("parameter", "")  # WHY: parameter name being consolidated
    unique_values: list[dict[str, Any]] = json.loads(deviation.get("unique_values", "[]"))  # WHY: JSON-encoded list
    _print_deviation_choices(param, cluster, unique_values)  # WHY: emit numbered menu for operator
    _record_deviation_choice(cluster, param, unique_values, resolutions, safe_input_fn)  # WHY: capture selection


def _print_deviation_choices(
    param: str,
    cluster: str,
    unique_values: list[dict[str, Any]],
) -> None:
    """Print the numbered list of candidate values for a deviation."""
    print(f"\n  Deviation: {param} in cluster '{cluster}'")  # WHY: header per deviation
    for index, entry in enumerate(unique_values, 1):  # WHY: 1-based menu numbering for operator
        _print_choice_entry(index, entry)  # WHY: delegate row rendering to keep loop body tight


def _print_choice_entry(index: int, entry: dict[str, Any]) -> None:
    """Print one candidate value row plus optional 'and N more sites' tail."""
    sites_preview = ", ".join(entry["sites"][:_SITES_PREVIEW_LIMIT])  # WHY: bounded preview
    print(f"    {index}. {entry['value']} ({entry['count']} sites: {sites_preview})")  # WHY: candidate line
    remaining = len(entry["sites"]) - _SITES_PREVIEW_LIMIT  # WHY: tail count when list exceeds preview
    if remaining > 0:  # WHY: only emit tail hint when overflow rows exist
        print(f"       ... and {remaining} more sites")  # WHY: report tail count without noise


def _record_deviation_choice(
    cluster: str,
    param: str,
    unique_values: list[dict[str, Any]],
    resolutions: dict[tuple[str, str], Any],
    safe_input_fn: SafeInputFn,
) -> None:
    """Prompt operator and record the chosen canonical value."""
    choice: str = safe_input_fn(  # WHY: menu prompt through the injected safe input wrapper
        f"  Select canonical value [1-{len(unique_values)}]: ",
        context=_DEVIATION_CONTEXT,
    )
    selected_index = _parse_choice_index(choice, param)  # WHY: shared parse handles ValueError branch
    if selected_index is None:  # WHY: parser already emitted the skip message
        return  # WHY: nothing to record when the choice was invalid
    _apply_choice(cluster, param, selected_index, unique_values, resolutions)  # WHY: mutate on valid pick


def _parse_choice_index(choice: str, param: str) -> int | None:
    """Convert operator input to a 0-based index; return None + print on invalid input."""
    try:
        return int(choice) - 1  # WHY: 1-based menu -> 0-based index
    except ValueError:  # WHY: non-integer input is a soft failure — skip param, keep loop
        print(f"  ! Invalid input. Skipping {param}.")  # WHY: user-visible skip reason
        return None  # WHY: caller treats None as skip signal


def _apply_choice(
    cluster: str,
    param: str,
    selected_index: int,
    unique_values: list[dict[str, Any]],
    resolutions: dict[tuple[str, str], Any],
) -> None:
    """Validate the index and either record the resolution or emit a skip message."""
    if not 0 <= selected_index < len(unique_values):  # WHY: out-of-range index is a soft failure
        print(f"  ! Invalid selection. Skipping {param}.")  # WHY: user-visible skip reason
        return  # WHY: skip when index falls outside the menu bounds
    selected = unique_values[selected_index]["value"]  # WHY: canonical value chosen
    resolutions[(cluster, param)] = selected  # WHY: cluster+param uniquely keys the resolution
    logging.info(  # WHY: audit-log the operator's canonical selection
        _DEVIATION_LOG_MSG,
        cluster,
        param,
        selected,
        len(unique_values),
        datetime.now().isoformat(),
    )


# ---------------------------------------------------------------------------
# Phase 4 pure helpers — group / template plan builders
# ---------------------------------------------------------------------------


def _load_group_plan_from_results(
    phase3_results: dict[str, Any],
) -> dict[str, dict[str, str]]:
    """Extract group_name -> group_id mapping from Phase 3 results."""
    group_map: dict[str, dict[str, str]] = {}  # WHY: dedup by group_name for stable ordering
    for result in phase3_results.get("results", []):  # WHY: iterate over Phase 3 result rows
        group_name = result.get("group_name", "")  # WHY: primary key for the plan map
        if group_name and group_name not in group_map:  # WHY: keep first occurrence per group_name
            group_map[group_name] = {  # WHY: capture the two fields consumed by phase 4
                "group_id": result.get("group_id", ""),
                "cluster_name": result.get("cluster_name", ""),
            }
    return group_map  # WHY: caller iterates in insertion order (stable)


def _build_all_template_configs(
    group_plan: dict[str, dict[str, str]],
    resolutions: dict[tuple[str, str], Any],
    cache: dict[str, Any],
    target_ssid: str,
) -> dict[str, dict[str, Any]]:
    """Build WLAN configs for each group's template."""
    configs: dict[str, dict[str, Any]] = {}  # WHY: keyed by group_name for downstream iteration
    for group_name, group_info in group_plan.items():  # WHY: one config per planned group
        cluster = group_info.get("cluster_name", "")  # WHY: cluster drives the deviation set
        configs[group_name] = _build_template_config(cluster, resolutions, cache, target_ssid)  # WHY: assemble row
    return configs  # WHY: caller feeds this into _create_or_update_templates


def _build_template_config(
    cluster_name: str,
    resolutions: dict[tuple[str, str], Any],
    cache: dict[str, Any],
    target_ssid: str,
) -> dict[str, Any]:
    """Build a single WLAN config with variable refs for deviations."""
    deviation_params = _cluster_deviation_params(cache, cluster_name)  # WHY: params needing var refs
    representative = _find_representative(cache, cluster_name)  # WHY: source row for concrete values
    config: dict[str, Any] = {"ssid": target_ssid, "enabled": True}  # WHY: base fields shared by all templates
    if representative:  # WHY: only merge concrete values when a representative was found
        _populate_from_representative(config, representative, deviation_params)  # WHY: fill vlan/auth/mxtunnel
    _apply_deviation_placeholders(config, deviation_params)  # WHY: overlay variable refs for deviating params
    return config  # WHY: caller stores this config in the group->config map


def _apply_deviation_placeholders(config: dict[str, Any], deviation_params: set[str]) -> None:
    """Overlay variable placeholders for parameters that deviate (excluding vlan_id)."""
    for param in deviation_params:  # WHY: one placeholder per deviating parameter
        if param == _VLAN_ID_KEY:  # WHY: vlan_id already handled by _populate_from_representative
            continue  # WHY: vlan variable is placed under a different naming convention
        config[param] = f"{{{{MISTHELPER_{param.upper()}}}}}"  # WHY: variable placeholder


def _cluster_deviation_params(cache: dict[str, Any], cluster_name: str) -> set[str]:
    """Return the set of parameter names that deviate within a cluster."""
    deviations = cache.get("deviations", [])  # WHY: iterate over Phase-1 deviation records
    matches = filter(lambda dev: _is_cluster_deviation(dev, cluster_name), deviations)  # WHY: filter first
    return {param for dev in matches if (param := dev.get("parameter")) and isinstance(param, str)}  # WHY: dedupe


def _is_cluster_deviation(deviation: dict[str, Any], cluster_name: str) -> bool:
    """Return True if the deviation row belongs to ``cluster_name`` and is not the drift bucket."""
    name = deviation.get("cluster_name")  # WHY: single lookup shared by both checks
    return name == cluster_name and name != _CROSS_CLUSTER  # WHY: exclude drift-record bucket


def _find_representative(cache: dict[str, Any], cluster_name: str) -> dict[str, Any] | None:
    """Find a representative matrix row for the cluster."""
    matrix: list[dict[str, Any]] = cache.get("matrix", [])  # WHY: per-site rows from Phase 1
    primary = _first_clean_row(matrix, cluster_name)  # WHY: prefer same-cluster clean row
    if primary is not None:  # WHY: same-cluster hit wins over pilot fallback
        return primary  # WHY: clean cluster row supplies concrete values
    return _first_clean_row(matrix, _PILOT_GROUP)  # WHY: fall back to pilot when cluster is empty


def _first_clean_row(matrix: list[dict[str, Any]], target_group: str) -> dict[str, Any] | None:
    """Return the first non-anomaly, non-PSK row for a target group."""
    for row in matrix:  # WHY: linear scan is fine — matrix rarely exceeds 10^3 rows
        if _is_clean_row(row, target_group):  # WHY: predicate keeps CC of this loop at 2
            return row  # WHY: first clean row is sufficient — no need to score
    return None  # WHY: no clean row for target -> caller falls back or gives up


def _is_clean_row(row: dict[str, Any], target_group: str) -> bool:
    """Return True when the row matches the target group and is neither an anomaly nor PSK."""
    if row.get("target_group") != target_group:  # WHY: rows for other groups are skipped
        return False  # WHY: filter mismatched group before checking flags
    return not row.get("anomaly") and not row.get("psk_detected")  # WHY: reject anomaly / PSK rows


def _populate_from_representative(
    config: dict[str, Any],
    representative: dict[str, Any],
    deviation_params: set[str],
) -> None:
    """Populate template config from representative row."""
    if _VLAN_ID_KEY in deviation_params:  # WHY: vlan_id deviates -> emit variable reference
        config[_VLAN_ID_KEY] = _VLAN_ID_VAR  # WHY: vlan varies per site -> variable ref
    else:  # WHY: no vlan deviation -> copy the concrete value from the representative
        config[_VLAN_ID_KEY] = representative.get("vlan_id", "")  # WHY: no deviation -> concrete value
    config["auth"] = {"type": representative.get("auth_type", "")}  # WHY: auth mirrors representative
    mxtunnel_id = representative.get("mxtunnel_id", "")  # WHY: only set when tunneling is in use
    if mxtunnel_id:  # WHY: skip mxtunnel_ids entirely for non-tunneled deployments
        config["mxtunnel_ids"] = [mxtunnel_id]  # WHY: single-element list matches mist schema


def _display_template_plan(
    configs: dict[str, dict[str, Any]],
    group_plan: dict[str, dict[str, str]],
) -> None:
    """Print template creation plan."""
    print("\n  Template Plan:")  # WHY: header separates the plan from prior output
    for group_name, config in configs.items():  # WHY: one block per group in the plan
        group_info = group_plan.get(group_name, {})  # WHY: recover group_id for display
        _print_template_row(group_name, group_info, config)  # WHY: delegate row rendering


def _print_template_row(
    group_name: str,
    group_info: dict[str, str],
    config: dict[str, Any],
) -> None:
    """Print one template plan block (group header + SSID + remaining fields)."""
    group_id = group_info.get("group_id", "new")  # WHY: 'new' sentinel when the group is not yet created
    print(f"    {group_name} (group_id={group_id})")  # WHY: block header
    print(f"      SSID: {config.get('ssid', '')}")  # WHY: SSID always printed first for readability
    for key, value in config.items():  # WHY: iterate remaining config fields
        if key != "ssid":  # WHY: ssid already emitted above
            print(f"      {key}: {value}")  # WHY: two-space indent aligns with header


# ---------------------------------------------------------------------------
# Phase 5 pure helpers
# ---------------------------------------------------------------------------


def _build_disable_plan(
    cache: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build plan for disabling old SSIDs."""
    matrix = cache.get("matrix", [])  # WHY: per-site rows drive the disable decision
    return [_classify_disable_entry(row) for row in matrix]  # WHY: one plan entry per matrix row


def _classify_disable_entry(
    row: dict[str, Any],
) -> dict[str, Any]:
    """Classify a single site for disable action."""
    base = _build_disable_base(row)  # WHY: build shared identity fields first
    skip = _skip_reason_for_row(row)  # WHY: consolidate the 4 skip predicates
    if skip is not None:  # WHY: skip predicate takes precedence over default action
        status, reason = skip  # WHY: unpack (status, reason) tuple returned by predicate
        base["status"] = status  # WHY: skip status assigned by predicate
        base["reason"] = reason  # WHY: skip reason paired with the status
        return base  # WHY: short-circuit before the default action assignment
    base["status"] = _STATUS_TO_DISABLE  # WHY: default action when no skip predicate fired
    base["reason"] = ""  # WHY: empty reason for actionable rows
    return base  # WHY: caller collects entries into the plan list


def _skip_reason_for_row(row: dict[str, Any]) -> tuple[str, str] | None:
    """Return (status, reason) if the row should be skipped, else None."""
    if row.get("psk_detected"):  # WHY: PSK sites never take part in consolidation
        return (_STATUS_SKIPPED, _REASON_PSK)  # WHY: PSK sites never take part in consolidation
    if row.get("anomaly"):  # WHY: anomaly rows are diagnosed separately, not consolidated
        return (_STATUS_SKIPPED, f"Anomaly: {row.get('anomaly_reason', '')}")  # WHY: preserve anomaly reason
    if not row.get("ssid_enabled", True):  # WHY: already-disabled rows are idempotent no-ops
        return (_STATUS_ALREADY_DISABLED, _REASON_ALREADY)  # WHY: idempotent no-op
    if not row.get("ssid_id"):  # WHY: missing SSID id -> nothing to disable
        return (_STATUS_SKIPPED, _REASON_NO_ID)  # WHY: skip when SSID id was never captured
    return None  # WHY: no skip -> caller marks the row actionable


def _build_disable_base(row: dict[str, Any]) -> dict[str, Any]:
    """Build base dictionary for a disable plan entry."""
    return {  # WHY: identity fields shared by both actionable and skipped rows
        "site_name": row.get("site_name", ""),
        "site_id": row.get("site_id", ""),
        "old_template_name": row.get("template_name", ""),
        "old_template_id": row.get("template_id", ""),
        "ssid_name": row.get("ssid_name", ""),
        "ssid_id": row.get("ssid_id", ""),
        "previous_enabled": row.get("ssid_enabled", True),
        "timestamp": "",  # WHY: timestamp filled in only when the row is actioned
    }


def _display_disable_plan(
    plan: list[dict[str, Any]],
) -> None:
    """Print disable plan summary."""
    counts = _partition_disable_plan(plan)  # WHY: single pass over the plan
    print("\n  Disable Plan:")  # WHY: header separates the plan from prior output
    print(f"    To disable:       {counts[_STATUS_TO_DISABLE]}")  # WHY: actionable count first
    print(f"    Already disabled: {counts[_STATUS_ALREADY_DISABLED]}")  # WHY: idempotent-skip count
    print(f"    Skipped:          {counts[_STATUS_SKIPPED]}")  # WHY: other-skip count last


def _partition_disable_plan(plan: list[dict[str, Any]]) -> dict[str, int]:
    """Count disable-plan entries by status."""
    counts = {_STATUS_TO_DISABLE: 0, _STATUS_ALREADY_DISABLED: 0, _STATUS_SKIPPED: 0}  # WHY: fixed buckets
    for entry in plan:  # WHY: single linear pass keeps CC at 3
        status = entry.get("status", "")  # WHY: default to blank for defensive branch
        if status in counts:  # WHY: ignore statuses outside the fixed bucket set
            counts[status] += 1  # WHY: increment matching bucket
    return counts  # WHY: caller reads the three known keys


def _set_ssid_disabled(wlans: list[dict[str, Any]], ssid_id: str) -> bool:
    """Set enabled=False on the matching SSID. Returns True if found."""
    for wlan in wlans:  # WHY: linear scan is fine — templates carry O(10) wlans
        if wlan.get("id") == ssid_id:  # WHY: match on the mist-assigned id
            wlan["enabled"] = False  # WHY: mutate in place — caller reuses the list
            return True  # WHY: exit early after first match
    return False  # WHY: caller reports skip when the WLAN row is absent


# ---------------------------------------------------------------------------
# Shared output helper
# ---------------------------------------------------------------------------


def _print_phase_summary(phase_label: str, results: list[dict[str, Any]]) -> None:
    """Print a summary of phase results by status."""
    status_counts = _tally_status(results)  # WHY: aggregate over heterogeneous status field
    print(f"\n  {phase_label} Summary:")  # WHY: header per phase for the summary block
    for status, count in sorted(status_counts.items()):  # WHY: deterministic status ordering
        print(f"    {status}: {count}")  # WHY: single indent aligns with plan blocks


def _tally_status(results: list[dict[str, Any]]) -> dict[str, int]:
    """Count result rows grouped by their ``status`` field."""
    counts: dict[str, int] = {}  # WHY: dynamic bucket set — sum any status the phase emits
    for result in results:  # WHY: linear pass over the phase result list
        status = result.get("status", "unknown")  # WHY: default bucket when a row omits status
        counts[status] = counts.get(status, 0) + 1  # WHY: increment or initialize
    return counts  # WHY: caller renders the counts as a sorted list


# ---------------------------------------------------------------------------
# Cluster class wrapping parent phase-4 + phase-5 orchestrators
# ---------------------------------------------------------------------------


class _SsidTemplatePhase45Cluster(_ClusterBase):
    """Owns the Phase 4 + Phase 5 orchestrators and their coordinators."""

    def phase4_templates(self) -> None:
        """Phase 4 orchestrator — resolve deviations, create templates."""
        parent = self._mm  # WHY: proxy alias for readability + W0212 avoidance
        print(_PHASE4_HEADER)  # WHY: user-facing banner
        logging.info(_PHASE4_START_LOG)  # WHY: audit-log start of phase 4
        preflight = self._phase4_preflight()  # WHY: split cache + plan build out of orchestrator
        if preflight is None:  # WHY: preflight already printed the bail message
            return  # WHY: abort when Phase 3 results or cache are missing
        group_plan, configs = preflight  # WHY: unpack the two artifacts returned by preflight
        _display_template_plan(configs, group_plan)  # WHY: user preview before confirming
        prompt = f"Create/update {len(configs)} templates?"  # WHY: confirmation prompt copy
        if not parent._confirm_or_cancel(prompt):  # noqa: SLF001 — shared preamble helper
            return  # WHY: user declined -> phase aborts without persistence
        results = self._call("_create_or_update_templates", configs, group_plan)  # WHY: run per-group loop
        self._persist_phase4_results(results)  # WHY: save + write + summary in one call

    def _persist_phase4_results(self, results: list[dict[str, Any]]) -> None:
        """Save phase 4 results, hand them to the writer, and print the summary."""
        parent = self._mm  # WHY: proxy alias for readability + W0212 avoidance
        parent._save_phase_results(_PHASE4_ID, results)  # noqa: SLF001 — parent owns phase-state save
        parent.write_data_fn(  # WHY: hand rows to the configured writer (parquet/table)
            data=results,
            filename_or_table=_PHASE4_WRITE_FILENAME,  # WHY: consistent sink label across phases
            api_function_name=_PHASE4_WRITE_API_NAME,  # WHY: mist API tag preserved on archival row
        )
        _print_phase_summary(_PHASE4_LABEL, results)  # WHY: emit success/failure summary

    def _phase4_preflight(
        self,
    ) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, Any]]] | None:
        """Load cache + phase-3 results, resolve deviations, build template configs."""
        parent = self._mm  # WHY: proxy alias
        if not self._load_cache_or_bail():  # WHY: shared preamble — abort when Phase 1 skipped
            return None  # WHY: cache preamble already printed the bail message
        phase3_results = parent._load_phase_results(3)  # noqa: SLF001
        if not phase3_results:  # WHY: phase 4 depends on Phase 3 groups being materialized
            print("! Phase 3 results not found. Run Phase 3 first.")  # WHY: operator-visible reason
            return None  # WHY: abort until phase 3 has been executed
        resolutions = _resolve_deviations(parent.cache, parent.safe_input_fn)  # WHY: interactive step
        group_plan = _load_group_plan_from_results(phase3_results)  # WHY: shape the group plan map
        configs = _build_all_template_configs(  # WHY: per-group config synthesis
            group_plan,
            resolutions,
            parent.cache,
            parent.target_ssid,
        )
        return group_plan, configs  # WHY: caller consumes both artifacts

    def _create_or_update_templates(
        self,
        configs: dict[str, dict[str, Any]],
        group_plan: dict[str, dict[str, str]],
    ) -> list[dict[str, Any]]:
        """Create or update templates for each group."""
        parent = self._mm  # WHY: proxy alias
        basename = os.environ.get(_TEMPLATE_BASENAME_ENV, parent.target_ssid)  # WHY: env override or default
        existing_templates = _build_existing_template_lookup(parent.cache)  # WHY: name->template index
        # WHY: parent owns the mistapi-touching worker so tests can patch mistapi at parent.
        from .ssid_template_consolidation import (  # noqa: PLC0415 — local import breaks cycle
            _create_or_update_single_template,
        )

        return [  # WHY: one result per group processed
            _create_or_update_single_template(  # WHY: dispatcher handles create/update/skip branches
                self._build_template_op_params(group_name, config, group_plan, basename),
                existing_templates,
            )
            for group_name, config in configs.items()
        ]

    def _build_template_op_params(
        self,
        group_name: str,
        config: dict[str, Any],
        group_plan: dict[str, dict[str, str]],
        basename: str,
    ) -> TemplateOpParams:
        """Assemble the TemplateOpParams bundle for a single group's template op."""
        parent = self._mm  # WHY: proxy alias for readability + W0212 avoidance
        return TemplateOpParams(  # WHY: pack once so callers stay under STRUCT-PARAMS budget
            template_name=f"{_MISTHELPER_PREFIX}{group_name}_{basename}",
            wlan_config=config,
            group_info=group_plan.get(group_name, {}),  # WHY: empty dict when group missing from plan
            timestamp=datetime.now().isoformat(),  # WHY: per-row timestamp for the result record
            target_ssid=parent.target_ssid,
            org_id=parent.org_id,
            apisession=parent.apisession,
            safe_input_fn=parent.safe_input_fn,
        )

    def phase5_disable_old(self) -> None:
        """Phase 5 orchestrator — disable matching SSIDs in old templates."""
        parent = self._mm  # WHY: proxy alias
        print(_PHASE5_HEADER)  # WHY: user-facing banner
        logging.info(_PHASE5_START_LOG)  # WHY: audit-log start of phase 5
        prep = self._phase5_prepare_plan()  # WHY: split cache + plan build out of orchestrator
        if prep is None:  # WHY: preflight already printed the bail message
            return  # WHY: abort when cache is missing
        resuming, prior_results, plan, to_disable = prep  # WHY: unpack the four preflight artifacts
        if not to_disable:  # WHY: nothing to do — empty actionable slice
            print("  No SSIDs to disable.")  # WHY: operator-visible reason for the no-op
            return  # WHY: skip persistence when the plan is empty
        prompt = f"Disable {len(to_disable)} SSIDs in old templates?"  # WHY: confirmation prompt copy
        if not parent._confirm_or_cancel(prompt):  # noqa: SLF001 — shared preamble helper
            return  # WHY: user declined -> phase aborts without persistence
        resume_state = prior_results if resuming else []  # WHY: pass prior rows only when resuming
        results = self._call("_disable_ssids", plan, resume_state)  # WHY: run per-entry disable loop
        self._persist_phase5_results(results)  # WHY: save + write + summary in one call

    def _persist_phase5_results(self, results: list[dict[str, Any]]) -> None:
        """Save phase 5 results, hand them to the writer, and print the summary."""
        parent = self._mm  # WHY: proxy alias for readability + W0212 avoidance
        parent._save_phase_results(_PHASE5_ID, results)  # noqa: SLF001 — parent owns phase-state save
        parent.write_data_fn(  # WHY: hand rows to the configured writer (parquet/table)
            data=results,
            filename_or_table=_PHASE5_WRITE_FILENAME,  # WHY: consistent sink label across phases
            api_function_name=_PHASE5_WRITE_API_NAME,  # WHY: mist API tag preserved on archival row
        )
        _print_phase_summary(_PHASE5_LABEL, results)  # WHY: emit success/failure summary

    def _phase5_prepare_plan(
        self,
    ) -> tuple[bool, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]] | None:
        """Load cache, offer resume, and build the disable plan."""
        parent = self._mm  # WHY: proxy alias
        if not self._load_cache_or_bail():  # WHY: shared preamble — abort when Phase 1 skipped
            return None  # WHY: cache preamble already printed the bail message
        resuming, prior_results = parent._offer_resume(_PHASE5_ID, [])  # noqa: SLF001
        plan = _build_disable_plan(parent.cache)  # WHY: shape the per-site disable plan
        to_disable = [entry for entry in plan if entry["status"] == _STATUS_TO_DISABLE]  # WHY: actionable slice
        _display_disable_plan(plan)  # WHY: user preview before confirming
        return resuming, prior_results, plan, to_disable  # WHY: caller unpacks the four artifacts

    def _disable_ssids(
        self,
        plan: list[dict[str, Any]],
        resume_from: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Disable SSIDs in old templates via GET-modify-PUT."""
        parent = self._mm  # WHY: proxy alias
        completed_ids = self._collect_completed_ids(resume_from)  # WHY: dedupe against prior-run rows
        results: list[dict[str, Any]] = list(resume_from) if resume_from else []  # WHY: seed with prior rows
        # WHY: parent owns the mistapi-touching worker so tests can patch mistapi at parent.
        from .ssid_template_consolidation import _disable_single_ssid  # noqa: PLC0415 — local import breaks cycle

        for entry in plan:  # WHY: one iteration per plan entry
            self._process_disable_entry(entry, completed_ids, results, _disable_single_ssid, parent)  # WHY: split
        return results  # WHY: caller persists this to the phase 5 output file

    def _process_disable_entry(  # pylint: disable=too-many-arguments
        self,
        entry: dict[str, Any],
        completed_ids: set[tuple[str | None, str | None]],
        results: list[dict[str, Any]],
        disable_fn: Any,
        parent: Any,
    ) -> None:
        """Process one plan entry into the results list (mutates in place)."""
        key = (entry.get("site_id"), entry.get("ssid_id"))  # WHY: composite key for resume dedupe
        if entry["status"] != _STATUS_TO_DISABLE:  # WHY: non-actionable row -> preserve or skip
            if key not in completed_ids:  # WHY: avoid duplicating rows already carried from resume
                results.append(entry)  # WHY: preserve non-actionable rows in results
            return  # WHY: nothing else to do for non-actionable rows
        if key in completed_ids:  # WHY: resume-safe -- skip rows already disabled last run
            return  # WHY: resume-safe -- skip rows already disabled last run
        results.append(disable_fn(entry, parent.org_id, parent.apisession))  # WHY: perform mist PUT
        if len(results) % _DISABLE_CHECKPOINT_INTERVAL == 0:  # WHY: incremental checkpoint every N rows
            parent._save_phase_results(_PHASE5_ID, results)  # noqa: SLF001 — intra-package checkpoint

    @staticmethod
    def _collect_completed_ids(
        resume_from: list[dict[str, Any]],
    ) -> set[tuple[str | None, str | None]]:
        """Extract (site_id, ssid_id) pairs already disabled in a prior run."""
        return {  # WHY: set of keys speeds up dedupe inside the main loop
            (row.get("site_id"), row.get("ssid_id")) for row in resume_from if row.get("status") == _STATUS_DISABLED
        }


def _build_existing_template_lookup(cache: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return a name -> template dict lookup from the cached wlan_templates list."""
    templates = cache.get("data", {}).get("wlan_templates", [])  # WHY: nested cache section
    return {tmpl.get("name", ""): tmpl for tmpl in templates}  # WHY: name-keyed index for O(1) dispatch

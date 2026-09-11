"""Phase 1 audit cluster for the SSID Template Consolidation manager.

Owns the read-only audit workflow: bulk org data fetch, per-site matrix
construction, per-group deviation analysis, cross-cluster drift, and the
Phase 1 summary line. Split out of the parent module so the coordinator
stays under the compliance length / block budgets while the pure helpers
remain re-exported via :mod:`ssid_template_consolidation`.

The 13-parameter ``_assemble_site_row`` signature that historically
tripped the STRUCT-PARAMS rule is now driven by a frozen
:class:`_SiteRowInputs` dataclass so the helper takes a single argument.
"""

# WHY: this cluster's ``_fetch_and_log`` intentionally mirrors the parent
# module's copy so tests that patch ``mistapi`` on this module's globals still
# observe the call — the duplicate is load-bearing and documented on the
# helper's docstring, so silence pylint's R0801 for the file. The cluster also
# reaches into the parent manager's private helpers and defers sibling imports
# to break import cycles.
# pylint: disable=duplicate-code,protected-access,import-outside-toplevel,too-few-public-methods

from __future__ import annotations  # WHY: postponed evaluation for forward-ref parent type

import json  # WHY: JSON encoding of deviation record values + sitegroup_ids
import logging  # WHY: emit telemetry alongside other phases
import re  # WHY: pilot_pattern is a compiled regex owned by the parent
from dataclasses import dataclass  # WHY: frozen bundle for the 13-param row assembly
from typing import Any  # WHY: broad typing for opaque payloads

import mistapi  # WHY: paginated fetch + REST call factories

from ._ssid_template_cluster import _ClusterBase  # WHY: shared parent-proxy wrapper

# ---------------------------------------------------------------------------
# Module-level constants — hoisted magic values / thresholds
# ---------------------------------------------------------------------------

_TEMPLATES_LABEL = "templates"  # WHY: fetch label reused in operator prints + logs
_ORG_WLANS_LABEL = "org WLANs"  # WHY: fetch label kept as constant for stability
_SITES_LABEL = "sites"  # WHY: fetch label reused across fetch spec
_MXTUNNELS_LABEL = "Mist Edge tunnels"  # WHY: operator-friendly wording for MX tunnels
_SITEGROUPS_LABEL = "site groups"  # WHY: singular label for the site groups fetch
_TOTAL_BULK_CALLS = 5  # WHY: 5 bulk API calls per audit — echoed in operator print
_MIN_ELIGIBLE_SSIDS = 2  # WHY: only 2-SSID templates enter consolidation flow
_MAX_ELIGIBLE_SSIDS = 2  # WHY: 3+ SSID templates require manual review
_MIN_CLUSTERS_FOR_DRIFT = 2  # WHY: cross-cluster drift needs at least 2 canonicals
_CROSS_CLUSTER_TAG = "cross_cluster"  # WHY: reserved cluster_name marking drift records
_CACHE_REUSE_CONTEXT = "ssid_consolidation_cache_reuse"  # WHY: telemetry key on safe_input_fn
_CACHE_REUSE_PROMPT = "  Use cached data? (Y/n): "  # WHY: operator-facing prompt string
_MATRIX_TABLE = "ssid_consolidation_matrix"  # WHY: filename/table for matrix dump
_MATRIX_API_FN = "ssidConsolidationMatrix"  # WHY: API function tag for matrix dump
_DEVIATIONS_TABLE = "ssid_consolidation_deviations"  # WHY: filename/table for deviations
_DEVIATIONS_API_FN = "ssidConsolidationDeviation"  # WHY: API function tag for deviations

# ---------------------------------------------------------------------------
# Pure module-level helpers
# ---------------------------------------------------------------------------


def _fetch_and_log(  # WHY: mirror parent's fetch helper so mistapi patching lands here too
    label: str,
    api_fn: Any,
    session: Any,
    org_id: str,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Fetch data via API, paginate, and log count.

    Uses this module's own ``mistapi`` import for name resolution, which
    keeps tests that patch ``_ssid_template_phase1.mistapi`` (or the
    shared ``mistapi`` MagicMock injected via ``sys.modules``) in effect
    for ``_fetch_all_org_data`` callers.
    """
    logging.warning("Fetching %s...", label)  # WHY: operator telemetry during multi-call fetch
    response = api_fn(session, org_id, **kwargs)  # WHY: mistapi list endpoint call
    data: list[dict[str, Any]] = (  # WHY: paginate response. None -> [] keeps callers dict-safe
        mistapi.get_all(response=response, mist_session=session) or []
    )
    logging.info("%s fetched: %d", label.capitalize(), len(data))  # WHY: audit trail per collection
    return data  # WHY: caller stores under spec.key in the result dict


def _build_mxtunnel_lookup(  # WHY: build id -> display-name map used by row cluster resolution
    mxtunnels: list[dict[str, Any]],
) -> dict[str, str]:
    """Build cluster_id -> cluster_name lookup."""
    return {  # WHY: dict-comp filters entries with missing ids to keep lookup consistent
        tunnel.get("id", ""): tunnel.get("name", "") for tunnel in mxtunnels if tunnel.get("id")
    }


def _build_template_lookup(  # WHY: build id -> template map used by resolve + deviation helpers
    templates: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Build template_id -> template object lookup."""
    return {tmpl.get("id", ""): tmpl for tmpl in templates if tmpl.get("id")}  # WHY: id-keyed lookup


def _build_sitegroup_lookup(  # WHY: build id -> sitegroup map (retained for signature parity)
    sitegroups: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Build sitegroup_id -> sitegroup object lookup."""
    return {group.get("id", ""): group for group in sitegroups if group.get("id")}  # WHY: id-keyed


def _template_applies_to_site(  # WHY: direct-scope + group-scope check used by resolve loop
    template: dict[str, Any],
    site: dict[str, Any],
) -> bool:
    """Return True when template applies to the site via direct or group scope."""
    applies = template.get("applies", {})  # WHY: applies dict carries site/sitegroup scope
    if site.get("id") in (applies.get("site_ids") or []):  # WHY: direct binding wins immediately
        return True  # WHY: direct scope match short-circuits the group-membership scan
    group_ids = set(applies.get("sitegroup_ids") or [])  # WHY: set enables O(1) disjoint check
    return not group_ids.isdisjoint(site.get("sitegroup_ids") or [])  # WHY: overlap => applies


def _resolve_template(  # WHY: match a site to its owning template via first-hit iteration
    site: dict[str, Any],
    template_lookup: dict[str, dict[str, Any]],  # WHY: the scope check reads site["sitegroup_ids"] directly instead
) -> tuple[dict[str, Any] | None, str]:
    """Find the WLAN template assigned to a site via applies scope."""
    for template_id, template in template_lookup.items():  # WHY: iterate all until first match
        if _template_applies_to_site(template, site):  # WHY: delegated scope check keeps CC low
            return template, template_id  # WHY: first-hit wins — templates are single-scope in Mist
    return None, ""  # WHY: unassigned site is common. Caller flags it


def _get_template_wlans(  # WHY: normalize None -> [] so downstream can rely on iterable shape
    template: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract WLANs list from a template object."""
    wlans: list[dict[str, Any]] = template.get("wlans", []) or []  # WHY: guard None -> empty list
    return wlans  # WHY: caller iterates without needing another None check


def _find_target_wlan(  # WHY: linear scan for target SSID. WLAN lists are typically 1..8 entries
    wlans: list[dict[str, Any]], target_ssid: str
) -> dict[str, Any] | None:
    """Find the WLAN matching the target SSID name."""
    target = target_ssid.lower()  # WHY: normalize once — SSIDs match case-insensitive
    for wlan in wlans:  # WHY: linear scan is fine — WLAN lists are small
        if wlan.get("ssid", "").lower() == target:  # WHY: case-insensitive equality on ssid name
            return wlan  # WHY: return the first matching WLAN — SSID names are unique per template
    return None  # WHY: absent target SSID is a common phase-1 finding


def _classify_ssid_count(
    ssid_count: int,
) -> tuple[bool, str]:  # WHY: bucket WLAN-count into anomaly reason for phase-1 gating
    """Return (anomaly, reason) based on WLAN count in the template."""
    if ssid_count == 0:  # WHY: empty template is a data anomaly
        return True, "0 SSIDs"  # WHY: reason string is user-facing in the report
    if ssid_count < _MIN_ELIGIBLE_SSIDS:  # WHY: only-target-SSID is not consolidation-ready
        return True, "1 SSID"  # WHY: reason string surfaces in dashboard summaries
    if ssid_count > _MAX_ELIGIBLE_SSIDS:  # WHY: 3+ SSIDs require manual review
        return True, "3+ SSIDs"  # WHY: string covers 3,4,5+ so downstream does not overspecify
    return False, ""  # WHY: exactly 2 SSIDs — eligible count


def _classify_matched(  # WHY: split matched-WLAN anomaly-detection to stay under CC/length budgets
    matched_wlan: dict[str, Any],
    mxtunnel_lookup: dict[str, str],
    psk_auth_types: tuple[str, ...],
) -> tuple[bool, bool, str]:
    """Classify a matched WLAN — detect PSK and Edge cluster mapping."""
    auth_type = matched_wlan.get("auth", {}).get("type", "")  # WHY: auth.type separates PSK vs 802.1x
    psk_detected = auth_type in psk_auth_types  # WHY: PSK sites use different consolidation flow
    mxtunnel_ids = matched_wlan.get("mxtunnel_ids", [])  # WHY: list from template body
    first_id = mxtunnel_ids[0] if mxtunnel_ids else ""  # WHY: primary tunnel id or empty sentinel
    if not first_id or first_id not in mxtunnel_lookup:  # WHY: no Edge mapping => anomaly
        return psk_detected, True, "no Edge cluster mapping"  # WHY: caller uses this reason in the report row
    return psk_detected, False, ""  # WHY: eligible site — no anomaly, no PSK skip


def _classify_site(  # WHY: single-entry classifier that chains guard clauses in priority order
    template: dict[str, Any] | None,
    wlans: list[dict[str, Any]],
    matched_wlan: dict[str, Any] | None,
    mxtunnel_lookup: dict[str, str],
    psk_auth_types: tuple[str, ...],
) -> tuple[bool, bool, str]:
    """Classify a site as PSK, anomaly, or eligible."""
    if not template:  # WHY: unassigned site cannot participate in consolidation
        return False, True, "no template assigned"  # WHY: reason routes site to the anomalies list
    if not matched_wlan:  # WHY: template exists but target SSID is missing
        return False, True, "target SSID not found"  # WHY: distinguishes missing-SSID from other anomalies
    count_anomaly, count_reason = _classify_ssid_count(len(wlans))  # WHY: split SSID-count branch
    if count_anomaly:  # WHY: any SSID-count anomaly short-circuits the classify path
        return False, True, count_reason  # WHY: preserve upstream reason string verbatim
    return _classify_matched(matched_wlan, mxtunnel_lookup, psk_auth_types)  # WHY: PSK/Edge check


def _determine_target_group(  # WHY: choose pilot vs cluster grouping label for the phase-1 report
    site_name: str,
    cluster_name: str,
    pilot_pattern: re.Pattern[str],
) -> str:
    """Assign target group — pilot if name matches pattern, else cluster."""
    if pilot_pattern.search(site_name):  # WHY: pilot/test/lab keyword tags a site as non-prod
        return "pilot"  # WHY: literal group name matches downstream sort/report keys
    return cluster_name if cluster_name else "unknown"  # WHY: unknown cluster falls to catch-all


# ---------------------------------------------------------------------------
# Site row assembly (13-param signature bundled via **kwargs)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _SiteRowInputs:  # pylint: disable=too-many-instance-attributes
    """Frozen bundle for :func:`_assemble_site_row`.

    Kept as an internal documentation aid describing the 13 fields the
    kwargs-only :func:`_assemble_site_row` accepts. The helper itself uses
    ``**inputs`` so external callers (including the test suite) may pass
    the fields as keyword arguments without constructing this dataclass.
    """

    site_name: str  # WHY: display name for reports
    site_id: str  # WHY: primary key for every downstream phase
    template_name: str  # WHY: for operator context in matrix export
    template_id: str  # WHY: needed by phases 4/5 to update templates
    matched_wlan: dict[str, Any] | None  # WHY: source of ssid/auth/vlan fields
    first_tunnel_id: str  # WHY: chosen mxtunnel_id for the row
    cluster_name: str  # WHY: mxtunnel display name -> target_group
    psk_detected: bool  # WHY: PSK sites are excluded from group flow
    anomaly: bool  # WHY: anomaly sites are excluded from group flow
    anomaly_reason: str  # WHY: audit rationale for exclusions
    wlans: list[dict[str, Any]]  # WHY: full WLAN list to count against
    site: dict[str, Any]  # WHY: source for sitegroup_ids field
    target_group: str  # WHY: cluster or pilot bucket


def _matched_field(matched: dict[str, Any] | None, key: str, default: Any) -> Any:
    """Return a field from the matched WLAN or a default when matched is None."""
    return matched.get(key, default) if matched else default  # WHY: single ternary avoids CC bloat


def _matched_auth_type(matched: dict[str, Any] | None) -> str:
    """Return the matched WLAN auth.type string or empty when absent."""
    if not matched:  # WHY: absent matched WLAN means no auth info to report
        return ""
    auth_value = matched.get("auth", {}).get("type", "")  # WHY: two-hop dict access is normal shape
    return str(auth_value)  # WHY: coerce to str for stable matrix column


def _matched_vlan(matched: dict[str, Any] | None) -> str:
    """Return the matched WLAN vlan_id as a string or empty."""
    if not matched:  # WHY: no matched WLAN means no VLAN column value
        return ""
    return str(matched.get("vlan_id", ""))  # WHY: matrix column is string-typed


def _assemble_site_row(**inputs: Any) -> dict[str, Any]:
    """Assemble the final site row dictionary from keyword-passed fields."""
    matched = inputs.get("matched_wlan")  # WHY: local alias to keep dict-literal readable
    site = inputs.get("site") or {}  # WHY: guard optional site dict for sitegroup_ids extraction
    wlans = inputs.get("wlans") or []  # WHY: default empty list keeps len() safe
    return {
        "site_name": inputs.get("site_name", ""),  # WHY: passthrough matrix field
        "site_id": inputs.get("site_id", ""),  # WHY: primary key for every downstream phase
        "template_name": inputs.get("template_name", ""),  # WHY: operator-friendly context
        "template_id": inputs.get("template_id", ""),  # WHY: id needed by phases 4/5
        "ssid_name": _matched_field(matched, "ssid", ""),  # WHY: matched-field extract keeps CC low
        "ssid_id": _matched_field(matched, "id", ""),  # WHY: matched-field extract keeps CC low
        "auth_type": _matched_auth_type(matched),  # WHY: nested auth.type via helper
        "vlan_id": _matched_vlan(matched),  # WHY: helper handles string coercion
        "mxtunnel_id": inputs.get("first_tunnel_id", ""),  # WHY: chosen Edge tunnel id
        "mxtunnel_name": inputs.get("cluster_name", ""),  # WHY: chosen Edge tunnel display name
        "psk_detected": inputs.get("psk_detected", False),  # WHY: PSK flag from classify step
        "anomaly": inputs.get("anomaly", False),  # WHY: anomaly flag from classify step
        "anomaly_reason": inputs.get("anomaly_reason", ""),  # WHY: audit rationale field
        "ssid_enabled": _matched_field(matched, "enabled", False),  # WHY: default False when unmatched
        "ssid_count_in_template": len(wlans),  # WHY: cached len avoids recomputation downstream
        "sitegroup_ids": json.dumps(site.get("sitegroup_ids") or []),  # WHY: encode list -> JSON
        "target_group": inputs.get("target_group", ""),  # WHY: cluster or pilot bucket
    }


def _resolve_site_wlan(  # WHY: bundles template + wlans + matched lookup into a single 4-tuple
    site: dict[str, Any],
    target_ssid: str,
    template_lookup: dict[str, dict[str, Any]],  # WHY: the callee stopped taking the group map, so this level drops it
) -> tuple[dict[str, Any] | None, str, list[dict[str, Any]], dict[str, Any] | None]:
    """Resolve the assigned template + matched WLAN for a site."""
    template, template_id = _resolve_template(site, template_lookup)  # WHY: scope check needs the template map only
    wlans = _get_template_wlans(template) if template else []  # WHY: guard None template
    matched_wlan = _find_target_wlan(wlans, target_ssid)  # WHY: locate target SSID in list
    return template, template_id, wlans, matched_wlan


def _pick_first_tunnel(  # WHY: null-safe primary-tunnel extractor used by row assembly
    matched_wlan: dict[str, Any] | None,
) -> str:
    """Return the first mxtunnel id from a matched WLAN or empty string."""
    if not matched_wlan:  # WHY: no match => no tunnel id available
        return ""
    ids = matched_wlan.get("mxtunnel_ids", [])  # WHY: template's tunnel bindings
    return ids[0] if ids else ""  # WHY: primary tunnel wins as row's cluster anchor


@dataclass(frozen=True, slots=True)
class _SiteLookups:
    """Bundle of the three id-keyed lookups needed to build a matrix row."""

    template_lookup: dict[str, dict[str, Any]]  # WHY: template_id -> template dict
    sitegroup_lookup: dict[str, dict[str, Any]]  # WHY: sitegroup_id -> sitegroup dict
    mxtunnel_lookup: dict[str, str]  # WHY: mxtunnel_id -> cluster display name


def _assemble_row_from_resolution(  # WHY: extracted from _build_site_row to keep length <=25
    site: dict[str, Any],
    resolution: tuple[dict[str, Any] | None, str, list[dict[str, Any]], dict[str, Any] | None],
    classification: tuple[bool, bool, str],
    tunnel_info: tuple[str, str, str],
) -> dict[str, Any]:
    """Assemble the final site row dict from resolved template + classification + tunnel data."""
    template, template_id, wlans, matched_wlan = resolution  # WHY: unpack resolve_site_wlan return
    psk, anomaly, reason = classification  # WHY: unpack classify_site tri-tuple
    first_tunnel_id, cluster_name, target_group = tunnel_info  # WHY: unpack tunnel triple
    return _assemble_site_row(  # WHY: kwargs signature keeps STRUCT-PARAMS at 1
        site_name=site.get("name", ""),
        site_id=site.get("id", ""),
        template_name=template.get("name", "") if template else "",
        template_id=template_id,
        matched_wlan=matched_wlan,
        first_tunnel_id=first_tunnel_id,
        cluster_name=cluster_name,
        psk_detected=psk,
        anomaly=anomaly,
        anomaly_reason=reason,
        wlans=wlans,
        site=site,
        target_group=target_group,
    )


def _build_site_row(  # WHY: 5-param signature (lookups bundled) preserves test-facing shape
    site: dict[str, Any],
    target_ssid: str,
    psk_auth_types: tuple[str, ...],
    pilot_pattern: re.Pattern[str],
    lookups: _SiteLookups,
) -> dict[str, Any] | None:
    """Build a single matrix row for one site."""
    if not site.get("id", ""):  # WHY: unidentifiable site cannot be reported
        return None
    resolution = _resolve_site_wlan(  # WHY: bundle template + wlans + matched into one tuple
        site, target_ssid, lookups.template_lookup  # WHY: the group map left the callee signature in issue #887
    )
    _, _, wlans, matched_wlan = resolution  # WHY: extract fields needed for classify/tunnel steps
    classification = _classify_site(  # WHY: five-way classification result
        resolution[0], wlans, matched_wlan, lookups.mxtunnel_lookup, psk_auth_types
    )
    first_tunnel_id = _pick_first_tunnel(matched_wlan)  # WHY: helper picks primary tunnel
    cluster_name = lookups.mxtunnel_lookup.get(first_tunnel_id, "")  # WHY: display name via lookup
    target_group = _determine_target_group(  # WHY: pilot/cluster/unknown bucket
        site.get("name", ""), cluster_name, pilot_pattern
    )
    return _assemble_row_from_resolution(  # WHY: helper builds the final row dict
        site, resolution, classification, (first_tunnel_id, cluster_name, target_group)
    )


# ---------------------------------------------------------------------------
# Deviation analysis helpers
# ---------------------------------------------------------------------------


def _group_by_target(
    rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group matrix rows by target_group name."""
    groups: dict[str, list[dict[str, Any]]] = {}  # WHY: accumulator keyed by target_group name
    for row in rows:  # WHY: linear pass — order preserved via setdefault + append
        group_name = row.get("target_group", "unknown")  # WHY: default keeps orphans grouped
        groups.setdefault(group_name, []).append(row)  # WHY: create bucket lazily then append
    return groups


def _analyze_group_deviations(  # WHY: main deviation loop for a target_group bucket
    group_name: str,
    rows: list[dict[str, Any]],
    template_lookup: dict[str, dict[str, Any]],
    target_ssid: str,
    metadata_fields: set[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Analyze deviations within a single group."""
    wlan_configs = _collect_group_wlan_configs(rows, template_lookup, target_ssid)  # WHY: WLAN dicts
    if not wlan_configs:  # WHY: no configs to compare => no deviations
        return [], {}
    all_keys = _collect_comparison_keys(wlan_configs, metadata_fields)  # WHY: union - metadata
    registry = _DeviationRegistry(deviations=[], canonicals={})  # WHY: bundled accumulator
    for key in all_keys:  # WHY: iterate keys once — inner logic decides deviation vs canonical
        values_map = _collect_key_values(key, wlan_configs, rows)  # WHY: value -> [site names]
        _record_deviation_or_canonical(  # WHY: helper handles both branches to keep CC low
            group_name, rows, key, values_map, registry
        )
    return registry.deviations, registry.canonicals


@dataclass(frozen=True, slots=True)
class _DeviationRegistry:
    """Mutable-list bundle for deviation records + per-key canonical values."""

    deviations: list[dict[str, Any]]  # WHY: appended when a key has >1 unique value
    canonicals: dict[str, Any]  # WHY: single-value keys and mode for drift analysis


def _record_deviation_or_canonical(  # WHY: 5-param signature (registry bundled) closes STRUCT-PARAMS
    group_name: str,
    rows: list[dict[str, Any]],
    key: str,
    values_map: dict[str, list[str]],
    registry: _DeviationRegistry,
) -> None:
    """Append a deviation record or set the canonical for a single-value key."""
    if len(values_map) > 1:  # WHY: >1 unique value means the key deviates in the group
        deviation = _build_deviation_record(group_name, rows, key, values_map)
        registry.deviations.append(deviation)  # WHY: record the divergent parameter
        registry.canonicals[key] = deviation.get("canonical_value")  # WHY: mode canonical for drift
    elif values_map:  # WHY: single-value keys still contribute canonicals for drift check
        registry.canonicals[key] = next(iter(values_map.keys()))  # WHY: only-one value is canonical


def _collect_group_wlan_configs(
    rows: list[dict[str, Any]],
    template_lookup: dict[str, dict[str, Any]],
    target_ssid: str,
) -> list[dict[str, Any]]:
    """Collect matched WLAN JSON dicts for all rows in a group."""
    configs: list[dict[str, Any]] = []  # WHY: accumulator — same length or shorter than rows
    for row in rows:  # WHY: iterate rows once — nothing depends on prior state
        template = template_lookup.get(row.get("template_id", ""))  # WHY: lookup by id
        if not template:  # WHY: row's template may have been deleted mid-audit
            continue
        wlans = _get_template_wlans(template)  # WHY: shared extractor honors None guard
        matched = _find_target_wlan(wlans, target_ssid)  # WHY: locate target SSID in WLAN list
        if matched:  # WHY: only include configs that actually have the target SSID
            configs.append(matched)
    return configs


def _collect_comparison_keys(
    wlan_configs: list[dict[str, Any]],
    metadata_fields: set[str],
) -> set[str]:
    """Build union of all WLAN config keys excluding metadata."""
    all_keys: set[str] = set()  # WHY: accumulator across all configs
    for config in wlan_configs:  # WHY: union of every seen key
        all_keys.update(config.keys())  # WHY: dict.keys view is safe to feed set.update
    return all_keys - metadata_fields  # WHY: metadata (id/timestamps) is not a real config diff


def _collect_key_values(
    key: str,
    wlan_configs: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """Collect unique values for a key with their site names."""
    values_map: dict[str, list[str]] = {}  # WHY: value_json -> [site names] map
    for index, config in enumerate(wlan_configs):  # WHY: enumerate to index into rows in parallel
        value = json.dumps(config.get(key), default=str, sort_keys=True)  # WHY: stable key for dedup
        site_name = rows[index].get("site_name", "") if index < len(rows) else ""  # WHY: index guard
        values_map.setdefault(value, []).append(site_name)  # WHY: bucket sites under the same value
    return values_map


def _build_deviation_record(
    group_name: str,
    rows: list[dict[str, Any]],
    key: str,
    values_map: dict[str, list[str]],
) -> dict[str, Any]:
    """Build a deviation record for a parameter with multiple values."""
    unique_values = [  # WHY: expand map into list of {value, sites, count}
        {"value": json.loads(value), "sites": sites, "count": len(sites)} for value, sites in values_map.items()
    ]
    unique_values.sort(key=lambda entry: entry["count"], reverse=True)  # WHY: most-common first
    canonical = unique_values[0]["value"] if unique_values else None  # WHY: mode wins as canonical
    cluster_id = rows[0].get("mxtunnel_id", "") if rows else ""  # WHY: first row is representative
    return {
        "cluster_name": group_name,  # WHY: group is the cluster/pilot bucket name
        "cluster_id": cluster_id,  # WHY: mxtunnel_id from representative row
        "parameter": key,  # WHY: the WLAN field name that deviates
        "unique_values": json.dumps(unique_values, default=str),  # WHY: JSON encode list of values
        "canonical_value": json.dumps(canonical, default=str),  # WHY: JSON encode mode
    }


def _build_drift_candidates(
    cluster_canonicals: dict[str, dict[str, Any]],
) -> tuple[set[str], dict[str, dict[str, Any]]]:
    """Return (all_params, per-param cluster -> value) for drift analysis."""
    all_params: set[str] = set()  # WHY: union of every seen parameter across clusters
    for canonicals in cluster_canonicals.values():  # WHY: union across all clusters
        all_params.update(canonicals.keys())  # WHY: every canonical param becomes a candidate
    per_param: dict[str, dict[str, Any]] = {}  # WHY: param -> {cluster: canonical_value}
    for param in all_params:  # WHY: build reverse index once
        per_param[param] = {
            cluster_name: canonicals[param]
            for cluster_name, canonicals in cluster_canonicals.items()
            if param in canonicals
        }
    return all_params, per_param


def _detect_cross_cluster_drift(
    cluster_canonicals: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Detect parameters where canonical values differ across clusters."""
    if len(cluster_canonicals) < _MIN_CLUSTERS_FOR_DRIFT:  # WHY: need >=2 clusters to compare
        return []
    all_params, per_param = _build_drift_candidates(cluster_canonicals)  # WHY: helper reduces CC
    drift: list[dict[str, Any]] = []  # WHY: accumulator for cross-cluster drift records
    for param in all_params:  # WHY: only params seen in any cluster are candidates
        values_by_cluster = per_param[param]  # WHY: cluster -> canonical value for this param
        unique_canonical = {  # WHY: set of JSON-stable serializations for dedup
            json.dumps(value, default=str, sort_keys=True) for value in values_by_cluster.values()
        }
        if len(unique_canonical) > 1:  # WHY: differing canonicals across clusters => drift
            _append_drift_record(drift, param, values_by_cluster)
    return drift


def _append_drift_record(
    drift: list[dict[str, Any]],
    param: str,
    values_by_cluster: dict[str, Any],
) -> None:
    """Append a cross-cluster drift deviation record."""
    unique_values = [  # WHY: shape mirrors group-deviation records for downstream code
        {"value": value, "sites": [cluster], "count": 1} for cluster, value in values_by_cluster.items()
    ]
    drift.append(
        {
            "cluster_name": _CROSS_CLUSTER_TAG,  # WHY: reserved name distinguishes drift from dev
            "cluster_id": "",  # WHY: drift is not tied to a single mxtunnel
            "parameter": param,  # WHY: WLAN field name that varies across clusters
            "unique_values": json.dumps(unique_values, default=str),  # WHY: encode list -> JSON
            "canonical_value": "",  # WHY: drift has no single canonical
        }
    )


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def _tally_matrix_row(  # WHY: single-row tally isolates CC away from the outer summation
    row: dict[str, Any],
    counts: list[int],
) -> None:
    """Increment eligible/psk/anomaly counters based on a matrix row's flags."""
    psk = bool(row.get("psk_detected"))  # WHY: cache to avoid two lookups per row
    ano = bool(row.get("anomaly"))  # WHY: cache to avoid two lookups per row
    counts[0] += int(not psk and not ano)  # WHY: eligible == neither flag set
    counts[1] += int(psk)  # WHY: PSK-flagged tally
    counts[2] += int(ano)  # WHY: anomaly-flagged tally


def _phase1_counts(  # WHY: return the (eligible, psk, anomaly) triple used in the summary print
    matrix: list[dict[str, Any]],
) -> tuple[int, int, int]:
    """Return (eligible_count, psk_count, anomaly_count) over the matrix."""
    counts = [0, 0, 0]  # WHY: list allows in-place mutation from the helper
    for row in matrix:  # WHY: single pass — each row updates all three counters
        _tally_matrix_row(row, counts)  # WHY: helper isolates the per-row branching
    return counts[0], counts[1], counts[2]  # WHY: unpack for named triple return


def _print_phase1_summary(
    matrix: list[dict[str, Any]],
    deviations: list[dict[str, Any]],
) -> None:
    """Print Phase 1 audit summary."""
    eligible, psk_count, anomaly_count = _phase1_counts(matrix)  # WHY: single-pass tallies
    logging.warning("Total sites:   %d", len(matrix))  # WHY: operator-visible tally
    logging.warning("Eligible:      %d", eligible)  # WHY: operator-visible eligible count
    logging.warning("PSK excluded:  %d", psk_count)  # WHY: operator-visible PSK excluded count
    logging.warning("Anomalies:     %d", anomaly_count)  # WHY: operator-visible anomaly count
    logging.warning("Deviations:    %d", len(deviations))  # WHY: operator-visible deviation count
    logging.info(  # WHY: durable log record mirrors console summary
        "Phase 1 complete: %d sites, %d eligible, %d deviations",
        len(matrix),
        eligible,
        len(deviations),
    )


# ---------------------------------------------------------------------------
# Cluster class wrapping parent phase-1 orchestrators
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _FetchSpec:
    """Frozen bundle describing one bulk fetch call in Phase 1."""

    key: str  # WHY: result dict key under which fetched data is stored
    label: str  # WHY: operator-facing label + log tag for the fetch call
    api_fn: Any  # WHY: mistapi list endpoint factory
    limited: bool  # WHY: True means pass parent.page_limit as kwargs


class _SsidTemplatePhase1Cluster(_ClusterBase):
    """Owns the Phase 1 read-only audit orchestrator + helpers."""

    def phase1_audit(self) -> None:
        """Phase 1 orchestrator — fetch data, build matrix, analyze."""
        parent = self._mm  # WHY: proxy alias for readability + W0212 avoidance
        logging.warning("=== Phase 1: Read-Only Audit ===")  # WHY: operator-visible section banner
        logging.info(  # WHY: audit-log start-of-phase entry with SSID context
            "Phase 1: Starting read-only audit for SSID '%s'",
            parent.target_ssid,
        )
        # WHY: route through parent so `patch.object(mgr, "_phase1_load_or_fetch", ...)` intercepts.
        org_data = self._call("_phase1_load_or_fetch")
        if not org_data:  # WHY: prerequisite fetch failure aborts the phase gracefully
            logging.warning("Failed to load or fetch organization data.")
            return
        matrix = self._call("_build_matrix", org_data)  # WHY: allow test patches on parent
        deviations = self._call("_analyze_deviations", matrix, org_data)  # WHY: allow test patches
        self._call("_phase1_save_and_report", org_data, matrix, deviations)  # WHY: allow test patches

    def _phase1_load_or_fetch(self) -> dict[str, Any] | None:
        """Load cached data or fetch fresh from API."""
        cached_data = self._try_load_cached()  # WHY: helper isolates cache-read + prompt branch
        if cached_data is not None:  # WHY: sentinel None means proceed to fresh fetch
            return cached_data
        logging.warning("Fetching fresh organization data...")  # WHY: operator telemetry for fetch path
        # WHY: route through parent so tests may patch _fetch_all_org_data on mgr directly.
        fresh: dict[str, Any] = self._call("_fetch_all_org_data")
        return fresh

    def _try_load_cached(self) -> dict[str, Any] | None:
        """Return cached org data when operator accepts reuse. None otherwise."""
        parent = self._mm  # WHY: proxy alias for readability + W0212 avoidance
        from ._ssid_template_cache import _cache_age_minutes  # local avoids cycle

        cached = parent._load_cache()  # cluster helper is intra-package
        if not cached or not cached.get("data"):  # WHY: no cache => caller performs fresh fetch
            return None
        age = _cache_age_minutes(cached.get("collected_at", ""))  # WHY: minutes since cache stamp
        logging.warning("Cached data found (%.0f minutes old).", age)  # WHY: operator sees freshness
        choice = parent.safe_input_fn(  # WHY: prompt operator with default-Y reuse
            _CACHE_REUSE_PROMPT,
            default_value="Y",
            context=_CACHE_REUSE_CONTEXT,
        )
        if choice.strip().lower() in ("n", "no"):  # WHY: operator declined -> fresh fetch path
            return None
        logging.info("Using cached org data")  # WHY: audit log for cache-reuse decision
        cached_data: dict[str, Any] | None = cached.get("data")  # WHY: narrow Any -> dict|None
        return cached_data

    def _phase1_save_and_report(
        self,
        org_data: dict[str, Any],
        matrix: list[dict[str, Any]],
        deviations: list[dict[str, Any]],
    ) -> None:
        """Save Phase 1 outputs and print summary."""
        parent = self._mm  # WHY: proxy alias for readability + W0212 avoidance
        parent._save_cache(  # cluster helper is intra-package
            {"data": org_data, "matrix": matrix, "deviations": deviations},
        )
        self._write_phase1_outputs(matrix, deviations)  # WHY: helper isolates the 2 dump calls
        _print_phase1_summary(matrix, deviations)  # WHY: operator summary after persistence

    def _write_phase1_outputs(
        self,
        matrix: list[dict[str, Any]],
        deviations: list[dict[str, Any]],
    ) -> None:
        """Write matrix and deviations via parent's writer function."""
        parent = self._mm  # WHY: proxy alias for readability + W0212 avoidance
        parent.write_data_fn(  # WHY: matrix dump goes to the ssidConsolidationMatrix sink
            data=matrix,
            filename_or_table=_MATRIX_TABLE,
            api_function_name=_MATRIX_API_FN,
        )
        parent.write_data_fn(  # WHY: deviations dump goes to the ssidConsolidationDeviation sink
            data=deviations,
            filename_or_table=_DEVIATIONS_TABLE,
            api_function_name=_DEVIATIONS_API_FN,
        )

    def _fetch_specs(self) -> tuple[_FetchSpec, ...]:
        """Return the immutable tuple of Phase 1 bulk-fetch specifications."""
        return (
            _FetchSpec("wlan_templates", _TEMPLATES_LABEL, mistapi.api.v1.orgs.templates.listOrgTemplates, False),
            _FetchSpec("org_wlans", _ORG_WLANS_LABEL, mistapi.api.v1.orgs.wlans.listOrgWlans, True),
            _FetchSpec("sites", _SITES_LABEL, mistapi.api.v1.orgs.sites.listOrgSites, True),
            _FetchSpec("mxtunnels", _MXTUNNELS_LABEL, mistapi.api.v1.orgs.mxtunnels.listOrgMxTunnels, False),
            _FetchSpec("sitegroups", _SITEGROUPS_LABEL, mistapi.api.v1.orgs.sitegroups.listOrgSiteGroups, False),
        )

    def _fetch_all_org_data(self) -> dict[str, Any]:
        """Fetch all org data using 5 bulk API calls."""
        parent = self._mm  # WHY: proxy alias for readability + W0212 avoidance
        result: dict[str, Any] = {}  # WHY: accumulator keyed by spec.key
        for spec in self._fetch_specs():  # WHY: table-driven loop replaces 5 open-coded calls
            kwargs = {"limit": parent.page_limit} if spec.limited else {}  # WHY: only some paginated
            result[spec.key] = _fetch_and_log(spec.label, spec.api_fn, parent.apisession, parent.org_id, **kwargs)
        logging.info("Total org-level API calls: %d", _TOTAL_BULK_CALLS)  # WHY: audit trail count
        logging.warning("Done (%d API calls)", _TOTAL_BULK_CALLS)  # WHY: operator-visible finalizer
        return result

    def _build_matrix(self, org_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Build per-site consolidation matrix from org data."""
        parent = self._mm  # WHY: proxy alias for readability + W0212 avoidance
        lookups = _SiteLookups(  # WHY: bundle 3 lookups into a single dataclass argument
            template_lookup=_build_template_lookup(org_data.get("wlan_templates", [])),
            sitegroup_lookup=_build_sitegroup_lookup(org_data.get("sitegroups", [])),
            mxtunnel_lookup=_build_mxtunnel_lookup(org_data.get("mxtunnels", [])),
        )
        matrix: list[dict[str, Any]] = []  # WHY: accumulator — one row per site with a site_id
        for site in org_data.get("sites", []):  # WHY: iterate every site once
            row = _build_site_row(
                site,
                parent.target_ssid,
                parent.PSK_AUTH_TYPES,
                parent.PILOT_PATTERN,
                lookups,
            )
            if row:  # WHY: _build_site_row skips rows with no site_id
                matrix.append(row)
        logging.info("Matrix built: %d sites", len(matrix))  # WHY: audit trail for matrix size
        return matrix

    def _analyze_deviations(
        self,
        matrix: list[dict[str, Any]],
        org_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Detect per-cluster deviations and cross-cluster drift."""
        parent = self._mm  # WHY: proxy alias for readability + W0212 avoidance
        eligible = [row for row in matrix if not row.get("anomaly") and not row.get("psk_detected")]
        template_lookup = _build_template_lookup(org_data.get("wlan_templates", []))  # WHY: id->tmpl
        deviations, cluster_canonicals = self._collect_group_deviations(  # WHY: group-level pass
            eligible, template_lookup, parent.target_ssid, parent.METADATA_FIELDS
        )
        deviations.extend(_detect_cross_cluster_drift(cluster_canonicals))  # WHY: cross-cluster pass
        logging.info(  # WHY: audit trail with combined group + drift total
            "Deviations found: %d (including cross-cluster drift)",
            len(deviations),
        )
        return deviations

    def _collect_group_deviations(
        self,
        eligible: list[dict[str, Any]],
        template_lookup: dict[str, dict[str, Any]],
        target_ssid: str,
        metadata_fields: set[str],
    ) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        """Iterate groups and collect per-group deviations + canonicals."""
        groups = _group_by_target(eligible)  # WHY: target_group -> rows list
        deviations: list[dict[str, Any]] = []  # WHY: accumulator across all groups
        cluster_canonicals: dict[str, dict[str, Any]] = {}  # WHY: per-group canonicals for drift
        for group_name, rows in groups.items():  # WHY: iterate group buckets once
            group_devs, canonicals = _analyze_group_deviations(
                group_name,
                rows,
                template_lookup,
                target_ssid,
                metadata_fields,
            )
            deviations.extend(group_devs)  # WHY: flatten group deviations into single list
            cluster_canonicals[group_name] = canonicals  # WHY: store canonical dict for drift stage
        return deviations, cluster_canonicals

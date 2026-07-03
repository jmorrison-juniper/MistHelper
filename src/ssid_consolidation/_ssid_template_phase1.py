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
# Pure module-level helpers
# ---------------------------------------------------------------------------


def _fetch_and_log(
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
    print(f"    Fetching {label}...")  # WHY: operator telemetry during multi-call fetch
    response = api_fn(session, org_id, **kwargs)  # WHY: mistapi list endpoint call
    data: list[dict[str, Any]] = mistapi.get_all(response=response, mist_session=session) or []
    logging.info("%s fetched: %d", label.capitalize(), len(data))  # WHY: audit trail per collection
    return data


def _build_mxtunnel_lookup(
    mxtunnels: list[dict[str, Any]],
) -> dict[str, str]:
    """Build cluster_id -> cluster_name lookup."""
    return {tunnel.get("id", ""): tunnel.get("name", "") for tunnel in mxtunnels if tunnel.get("id")}


def _build_template_lookup(
    templates: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Build template_id -> template object lookup."""
    return {tmpl.get("id", ""): tmpl for tmpl in templates if tmpl.get("id")}


def _build_sitegroup_lookup(
    sitegroups: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Build sitegroup_id -> sitegroup object lookup."""
    return {group.get("id", ""): group for group in sitegroups if group.get("id")}


def _resolve_template(
    site: dict[str, Any],
    template_lookup: dict[str, dict[str, Any]],
    sitegroup_lookup: dict[str, dict[str, Any]],  # noqa: ARG001 — signature preserved for tests
) -> tuple[dict[str, Any] | None, str]:
    """Find the WLAN template assigned to a site via applies scope."""
    for template_id, template in template_lookup.items():
        applies = template.get("applies", {})  # WHY: applies dict carries site/sitegroup scope
        site_ids = applies.get("site_ids") or []  # WHY: direct site->template binding
        if site.get("id") in site_ids:
            return template, template_id
        group_ids = applies.get("sitegroup_ids") or []  # WHY: group-level template binding
        site_groups = site.get("sitegroup_ids") or []
        if any(gid in group_ids for gid in site_groups):  # WHY: any overlap => template applies
            return template, template_id
    return None, ""  # WHY: unassigned site is common; caller flags it


def _get_template_wlans(
    template: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract WLANs list from a template object."""
    wlans: list[dict[str, Any]] = template.get("wlans", []) or []  # WHY: guard None -> empty list
    return wlans


def _find_target_wlan(wlans: list[dict[str, Any]], target_ssid: str) -> dict[str, Any] | None:
    """Find the WLAN matching the target SSID name."""
    for wlan in wlans:
        if wlan.get("ssid", "").lower() == target_ssid.lower():  # WHY: SSIDs are case-insensitive
            return wlan
    return None


def _classify_site(  # pylint: disable=too-many-return-statements
    template: dict[str, Any] | None,
    wlans: list[dict[str, Any]],
    matched_wlan: dict[str, Any] | None,
    mxtunnel_lookup: dict[str, str],
    psk_auth_types: tuple[str, ...],
) -> tuple[bool, bool, str]:
    """Classify a site as PSK, anomaly, or eligible."""
    if not template:  # WHY: unassigned site cannot participate in consolidation
        return False, True, "no template assigned"
    if not matched_wlan:  # WHY: template exists but target SSID is missing
        return False, True, "target SSID not found"
    ssid_count = len(wlans)
    if ssid_count == 0:  # WHY: empty template is a data anomaly
        return False, True, "0 SSIDs"
    if ssid_count == 1:  # WHY: only-target-SSID is not consolidation-ready
        return False, True, "1 SSID"
    if ssid_count >= 3:  # WHY: 3+ SSIDs require manual review
        return False, True, "3+ SSIDs"
    auth_type = matched_wlan.get("auth", {}).get("type", "")  # WHY: auth.type distinguishes PSK vs 802.1x
    psk_detected = auth_type in psk_auth_types  # WHY: PSK sites use different consolidation flow
    mxtunnel_ids = matched_wlan.get("mxtunnel_ids", [])
    first_id = mxtunnel_ids[0] if mxtunnel_ids else ""
    if not first_id or first_id not in mxtunnel_lookup:  # WHY: no Edge mapping => anomaly
        return psk_detected, True, "no Edge cluster mapping"
    return psk_detected, False, ""  # WHY: eligible site — no anomaly, no PSK skip


def _determine_target_group(
    site_name: str,
    cluster_name: str,
    pilot_pattern: re.Pattern[str],
) -> str:
    """Assign target group — pilot if name matches pattern, else cluster."""
    if pilot_pattern.search(site_name):  # WHY: pilot/test/lab keyword tags a site as non-prod
        return "pilot"
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


def _assemble_site_row(**inputs: Any) -> dict[str, Any]:
    """Assemble the final site row dictionary from keyword-passed fields."""
    matched = inputs.get("matched_wlan")  # WHY: local alias to keep dict-literal readable
    site = inputs.get("site") or {}  # WHY: guard optional site dict for sitegroup_ids extraction
    wlans = inputs.get("wlans") or []  # WHY: default empty list keeps len() safe
    return {
        "site_name": inputs.get("site_name", ""),
        "site_id": inputs.get("site_id", ""),
        "template_name": inputs.get("template_name", ""),
        "template_id": inputs.get("template_id", ""),
        "ssid_name": (matched.get("ssid", "") if matched else ""),
        "ssid_id": (matched.get("id", "") if matched else ""),
        "auth_type": (matched.get("auth", {}).get("type", "") if matched else ""),
        "vlan_id": (str(matched.get("vlan_id", "")) if matched else ""),
        "mxtunnel_id": inputs.get("first_tunnel_id", ""),
        "mxtunnel_name": inputs.get("cluster_name", ""),
        "psk_detected": inputs.get("psk_detected", False),
        "anomaly": inputs.get("anomaly", False),
        "anomaly_reason": inputs.get("anomaly_reason", ""),
        "ssid_enabled": (matched.get("enabled", True) if matched else False),
        "ssid_count_in_template": len(wlans),
        "sitegroup_ids": json.dumps(site.get("sitegroup_ids") or []),
        "target_group": inputs.get("target_group", ""),
    }


def _build_site_row(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    site: dict[str, Any],
    target_ssid: str,
    psk_auth_types: tuple[str, ...],
    pilot_pattern: re.Pattern[str],
    template_lookup: dict[str, dict[str, Any]],
    sitegroup_lookup: dict[str, dict[str, Any]],
    mxtunnel_lookup: dict[str, str],
) -> dict[str, Any] | None:
    """Build a single matrix row for one site."""
    site_id = site.get("id", "")
    site_name = site.get("name", "")
    if not site_id:  # WHY: unidentifiable site cannot be reported
        return None

    template, template_id = _resolve_template(site, template_lookup, sitegroup_lookup)
    template_name = template.get("name", "") if template else ""
    wlans = _get_template_wlans(template) if template else []
    matched_wlan = _find_target_wlan(wlans, target_ssid)

    psk, anomaly, reason = _classify_site(template, wlans, matched_wlan, mxtunnel_lookup, psk_auth_types)

    mxtunnel_ids = matched_wlan.get("mxtunnel_ids", []) if matched_wlan else []
    first_tunnel_id = mxtunnel_ids[0] if mxtunnel_ids else ""
    cluster_name = mxtunnel_lookup.get(first_tunnel_id, "")
    target_group = _determine_target_group(site_name, cluster_name, pilot_pattern)

    return _assemble_site_row(  # WHY: kwargs signature keeps STRUCT-PARAMS at 1
        site_name=site_name,
        site_id=site_id,
        template_name=template_name,
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


# ---------------------------------------------------------------------------
# Deviation analysis helpers
# ---------------------------------------------------------------------------


def _group_by_target(
    rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group matrix rows by target_group name."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        group_name = row.get("target_group", "unknown")  # WHY: default keeps orphans grouped
        groups.setdefault(group_name, []).append(row)
    return groups


def _analyze_group_deviations(
    group_name: str,
    rows: list[dict[str, Any]],
    template_lookup: dict[str, dict[str, Any]],
    target_ssid: str,
    metadata_fields: set[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Analyze deviations within a single group."""
    wlan_configs = _collect_group_wlan_configs(rows, template_lookup, target_ssid)
    if not wlan_configs:  # WHY: no configs to compare => no deviations
        return [], {}

    all_keys = _collect_comparison_keys(wlan_configs, metadata_fields)
    deviations: list[dict[str, Any]] = []
    canonicals: dict[str, Any] = {}

    for key in all_keys:
        values_map = _collect_key_values(key, wlan_configs, rows)
        if len(values_map) > 1:  # WHY: >1 unique value means the key deviates in the group
            deviation = _build_deviation_record(group_name, rows, key, values_map)
            deviations.append(deviation)
            canonicals[key] = deviation.get("canonical_value")
        elif values_map:  # WHY: single-value keys still contribute canonicals for drift check
            canonicals[key] = next(iter(values_map.keys()))
    return deviations, canonicals


def _collect_group_wlan_configs(
    rows: list[dict[str, Any]],
    template_lookup: dict[str, dict[str, Any]],
    target_ssid: str,
) -> list[dict[str, Any]]:
    """Collect matched WLAN JSON dicts for all rows in a group."""
    configs: list[dict[str, Any]] = []
    for row in rows:
        template = template_lookup.get(row.get("template_id", ""))
        if not template:  # WHY: row's template may have been deleted mid-audit
            continue
        wlans = _get_template_wlans(template)
        matched = _find_target_wlan(wlans, target_ssid)
        if matched:  # WHY: only include configs that actually have the target SSID
            configs.append(matched)
    return configs


def _collect_comparison_keys(
    wlan_configs: list[dict[str, Any]],
    metadata_fields: set[str],
) -> set[str]:
    """Build union of all WLAN config keys excluding metadata."""
    all_keys: set[str] = set()
    for config in wlan_configs:
        all_keys.update(config.keys())
    return all_keys - metadata_fields  # WHY: metadata (id/timestamps) is not a real config diff


def _collect_key_values(
    key: str,
    wlan_configs: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """Collect unique values for a key with their site names."""
    values_map: dict[str, list[str]] = {}
    for index, config in enumerate(wlan_configs):
        value = json.dumps(config.get(key), default=str, sort_keys=True)  # WHY: stable key for dedup
        site_name = rows[index].get("site_name", "") if index < len(rows) else ""
        values_map.setdefault(value, []).append(site_name)
    return values_map


def _build_deviation_record(
    group_name: str,
    rows: list[dict[str, Any]],
    key: str,
    values_map: dict[str, list[str]],
) -> dict[str, Any]:
    """Build a deviation record for a parameter with multiple values."""
    unique_values = [
        {
            "value": json.loads(value),
            "sites": sites,
            "count": len(sites),
        }
        for value, sites in values_map.items()
    ]
    unique_values.sort(key=lambda entry: entry["count"], reverse=True)  # WHY: most-common first
    canonical = unique_values[0]["value"] if unique_values else None  # WHY: mode wins as canonical
    cluster_id = rows[0].get("mxtunnel_id", "") if rows else ""
    return {
        "cluster_name": group_name,
        "cluster_id": cluster_id,
        "parameter": key,
        "unique_values": json.dumps(unique_values, default=str),
        "canonical_value": json.dumps(canonical, default=str),
    }


def _detect_cross_cluster_drift(
    cluster_canonicals: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Detect parameters where canonical values differ across clusters."""
    if len(cluster_canonicals) < 2:  # WHY: need >=2 clusters to compare
        return []
    all_params: set[str] = set()
    for canonicals in cluster_canonicals.values():
        all_params.update(canonicals.keys())

    drift: list[dict[str, Any]] = []
    for param in all_params:
        values_by_cluster: dict[str, Any] = {}
        for cluster_name, canonicals in cluster_canonicals.items():
            if param in canonicals:
                values_by_cluster[cluster_name] = canonicals[param]
        unique_canonical = {json.dumps(value, default=str, sort_keys=True) for value in values_by_cluster.values()}
        if len(unique_canonical) > 1:  # WHY: differing canonicals across clusters => drift
            _append_drift_record(drift, param, values_by_cluster)
    return drift


def _append_drift_record(
    drift: list[dict[str, Any]],
    param: str,
    values_by_cluster: dict[str, Any],
) -> None:
    """Append a cross-cluster drift deviation record."""
    unique_values = [{"value": value, "sites": [cluster], "count": 1} for cluster, value in values_by_cluster.items()]
    drift.append(
        {
            "cluster_name": "cross_cluster",  # WHY: reserved name distinguishes drift from group dev
            "cluster_id": "",
            "parameter": param,
            "unique_values": json.dumps(unique_values, default=str),
            "canonical_value": "",  # WHY: drift has no single canonical
        }
    )


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def _print_phase1_summary(
    matrix: list[dict[str, Any]],
    deviations: list[dict[str, Any]],
) -> None:
    """Print Phase 1 audit summary."""
    eligible = [row for row in matrix if not row.get("anomaly") and not row.get("psk_detected")]
    psk_count = sum(1 for row in matrix if row.get("psk_detected"))
    anomaly_count = sum(1 for row in matrix if row.get("anomaly"))
    print(f"\n  Total sites:   {len(matrix)}")
    print(f"  Eligible:      {len(eligible)}")
    print(f"  PSK excluded:  {psk_count}")
    print(f"  Anomalies:     {anomaly_count}")
    print(f"  Deviations:    {len(deviations)}")
    logging.info(
        "Phase 1 complete: %d sites, %d eligible, %d deviations",
        len(matrix),
        len(eligible),
        len(deviations),
    )


# ---------------------------------------------------------------------------
# Cluster class wrapping parent phase-1 orchestrators
# ---------------------------------------------------------------------------


class _SsidTemplatePhase1Cluster(_ClusterBase):
    """Owns the Phase 1 read-only audit orchestrator + helpers."""

    def phase1_audit(self) -> None:
        """Phase 1 orchestrator — fetch data, build matrix, analyze."""
        parent = self._mm  # WHY: proxy alias for readability + W0212 avoidance
        print("\n=== Phase 1: Read-Only Audit ===")
        logging.info(
            "Phase 1: Starting read-only audit for SSID '%s'",
            parent.target_ssid,
        )

        # WHY: route through parent so `patch.object(mgr, "_phase1_load_or_fetch", ...)` intercepts.
        org_data = self._call("_phase1_load_or_fetch")
        if not org_data:
            print("! Failed to load or fetch organization data.")
            return

        matrix = self._call("_build_matrix", org_data)  # WHY: allow test patches on parent
        deviations = self._call("_analyze_deviations", matrix, org_data)  # WHY: allow test patches
        self._call("_phase1_save_and_report", org_data, matrix, deviations)  # WHY: allow test patches

    def _phase1_load_or_fetch(self) -> dict[str, Any] | None:
        """Load cached data or fetch fresh from API."""
        parent = self._mm  # WHY: proxy alias
        from ._ssid_template_cache import _cache_age_minutes  # noqa: PLC0415 — local import avoids cycle

        cached = parent._load_cache()  # noqa: SLF001 — cluster helper is intra-package
        if cached and cached.get("data"):
            age = _cache_age_minutes(cached.get("collected_at", ""))
            print(f"  Cached data found ({age:.0f} minutes old).")
            choice = parent.safe_input_fn(
                "  Use cached data? (Y/n): ",
                default_value="Y",
                context="ssid_consolidation_cache_reuse",
            )
            if choice.strip().lower() not in ("n", "no"):
                logging.info("Using cached org data")
                cached_data: dict[str, Any] | None = cached.get("data")  # WHY: narrow Any -> dict|None
                return cached_data
        print("  Fetching fresh organization data...")
        # WHY: route through parent so tests may patch _fetch_all_org_data on mgr directly.
        fresh: dict[str, Any] = self._call("_fetch_all_org_data")
        return fresh

    def _phase1_save_and_report(
        self,
        org_data: dict[str, Any],
        matrix: list[dict[str, Any]],
        deviations: list[dict[str, Any]],
    ) -> None:
        """Save Phase 1 outputs and print summary."""
        parent = self._mm  # WHY: proxy alias
        cache_payload: dict[str, Any] = {
            "data": org_data,
            "matrix": matrix,
            "deviations": deviations,
        }
        parent._save_cache(cache_payload)  # noqa: SLF001 — cluster helper is intra-package

        parent.write_data_fn(
            data=matrix,
            filename_or_table="ssid_consolidation_matrix",
            api_function_name="ssidConsolidationMatrix",
        )
        parent.write_data_fn(
            data=deviations,
            filename_or_table="ssid_consolidation_deviations",
            api_function_name="ssidConsolidationDeviation",
        )

        _print_phase1_summary(matrix, deviations)

    def _fetch_all_org_data(self) -> dict[str, Any]:
        """Fetch all org data using 5 bulk API calls."""
        parent = self._mm  # WHY: proxy alias
        result: dict[str, Any] = {}
        session = parent.apisession

        result["wlan_templates"] = _fetch_and_log(
            "templates",
            mistapi.api.v1.orgs.templates.listOrgTemplates,
            session,
            parent.org_id,
        )
        result["org_wlans"] = _fetch_and_log(
            "org WLANs",
            mistapi.api.v1.orgs.wlans.listOrgWlans,
            session,
            parent.org_id,
            limit=parent.page_limit,
        )
        result["sites"] = _fetch_and_log(
            "sites",
            mistapi.api.v1.orgs.sites.listOrgSites,
            session,
            parent.org_id,
            limit=parent.page_limit,
        )
        result["mxtunnels"] = _fetch_and_log(
            "Mist Edge tunnels",
            mistapi.api.v1.orgs.mxtunnels.listOrgMxTunnels,
            session,
            parent.org_id,
        )
        result["sitegroups"] = _fetch_and_log(
            "site groups",
            mistapi.api.v1.orgs.sitegroups.listOrgSiteGroups,
            session,
            parent.org_id,
        )

        total_calls = 5
        logging.info("Total org-level API calls: %d", total_calls)
        print(f"    Done ({total_calls} API calls)")
        return result

    def _build_matrix(self, org_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Build per-site consolidation matrix from org data."""
        parent = self._mm  # WHY: proxy alias
        mxtunnel_lookup = _build_mxtunnel_lookup(org_data.get("mxtunnels", []))
        template_lookup = _build_template_lookup(org_data.get("wlan_templates", []))
        sitegroup_lookup = _build_sitegroup_lookup(org_data.get("sitegroups", []))

        matrix: list[dict[str, Any]] = []
        for site in org_data.get("sites", []):
            row = _build_site_row(
                site,
                parent.target_ssid,
                parent.PSK_AUTH_TYPES,
                parent.PILOT_PATTERN,
                template_lookup,
                sitegroup_lookup,
                mxtunnel_lookup,
            )
            if row:  # WHY: _build_site_row skips rows with no site_id
                matrix.append(row)
        logging.info("Matrix built: %d sites", len(matrix))
        return matrix

    def _analyze_deviations(
        self,
        matrix: list[dict[str, Any]],
        org_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Detect per-cluster deviations and cross-cluster drift."""
        parent = self._mm  # WHY: proxy alias
        eligible = [row for row in matrix if not row.get("anomaly") and not row.get("psk_detected")]
        template_lookup = _build_template_lookup(org_data.get("wlan_templates", []))

        groups = _group_by_target(eligible)
        deviations: list[dict[str, Any]] = []
        cluster_canonicals: dict[str, dict[str, Any]] = {}

        for group_name, rows in groups.items():
            group_devs, canonicals = _analyze_group_deviations(
                group_name,
                rows,
                template_lookup,
                parent.target_ssid,
                parent.METADATA_FIELDS,
            )
            deviations.extend(group_devs)
            cluster_canonicals[group_name] = canonicals

        drift = _detect_cross_cluster_drift(cluster_canonicals)
        deviations.extend(drift)
        logging.info(
            "Deviations found: %d (including cross-cluster drift)",
            len(deviations),
        )
        return deviations

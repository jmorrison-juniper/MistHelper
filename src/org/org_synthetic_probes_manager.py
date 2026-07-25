"""Org-level Zscaler synthetic-probe manager (menu 206).

Builds, merges, or swaps ``synthetic_test.custom_probes`` entries on the
Mist org setting using a curated catalogue of Zscaler Client Connector
destinations shipped with the repo under ``data/``.

Why:
    Operators need a single-command way to keep the Zscaler reachability
    probe fleet in sync with their VLAN topology. Hand-maintaining the
    probe block against Zscaler's evolving Cloud Enforcement Node list is
    error-prone; this module treats the JSON in ``data/`` as the source of
    truth, and marks every probe it writes with the ``zcc-`` name prefix
    so a follow-up run can safely merge or swap without disturbing
    probes authored elsewhere (see FR-010 through FR-015 in the spec).

Module-import must remain side-effect free (issue #1641 --help guard):
    Only ``import`` statements at module scope; all I/O, prompts, and API
    calls live inside functions invoked from the menu dispatch table.
"""

from __future__ import annotations  # PEP 604 unions for future annotations.

import json  # Read curated Zscaler JSON catalogues.
import logging  # Structured trace + info/warn/error logging.
from pathlib import Path  # Cross-platform path handling for data/ files.
from typing import Any  # Precise annotations for setting dicts.

# WHY: Import the mistapi setting modules at module load. Both are
# side-effect free (just re-exports of API callables) and let us
# monkey-patch them cleanly in unit tests via ``patch.object``. Sites
# module is needed for the optional post-PUT site-override flow, and
# ``orgs.sites`` (via ``_mist_orgs_sites``) drives the indexed
# site-picker after the org PUT succeeds.
import mistapi  # WHY: top-level for ``mistapi.get_all`` pagination helper.
from mistapi.api.v1.orgs import setting as _mist_setting
from mistapi.api.v1.orgs import sites as _mist_orgs_sites
from mistapi.api.v1.sites import setting as _mist_site_setting

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_PROBE_SOURCE_FILE = "zscaler_client_connector_probes.json"
_CENR_SOURCE_FILE = "zscaler_cenr_hostnames.json"
_TOOL_NAME_PREFIX = "zcc-"  # FR-010: marks probes authored by this tool.
_TUNNEL_ZEN_ROLE = "tunnel_zen"  # Only role that expands via CENR hostnames.
_VLAN_MIN = 0  # FR-003 lower bound.
_VLAN_MAX = 4094  # FR-003 upper bound.
_CRITICAL_AGGRESSIVENESS = "critical"  # Mist caps priority probes at 5 per org.
_AUTO_AGGRESSIVENESS = "auto"  # Mist's own default for non-priority probes.
# Non-critical probes emit ``aggressiveness=auto`` explicitly.
# Why: Mist itself writes ``"auto"`` on its own auto-generated ``mini-*`` probes
# (verified against a live org config 2026-07-24). Emitting the literal value
# mirrors Mist's convention and avoids ambiguity between "unset" and
# "explicitly default". The 5-priority cap counts ``critical``+``high`` only;
# ``auto`` does not consume a slot, so the curated 5 critical roles remain
# safely under the cap.


def manage_org_synthetic_probes(mist_session: Any, org_id: str) -> None:
    """Interactive entry point for menu 206.

    Why:
        Single public API surface for the feature. The menu dispatch table
        calls this exact callable; keeping it thin and delegating to the
        ``_``-prefixed helpers below preserves testability -- each helper
        can be exercised directly without stubbing the whole flow.

    Args:
        mist_session: Authenticated ``mistapi`` session object used for
            both the ``getOrgSettings`` read and the ``updateOrgSettings``
            write.
        org_id: Mist organisation UUID whose ``synthetic_test.custom_probes``
            block is being managed.

    Returns:
        None. Side effects (API PUT + stdout prints) are the observable
        outcome.

    Raises:
        FileNotFoundError: If either curated JSON file is missing (bubbled
            from ``_load_probe_sources``).
        ValueError: If either curated JSON file is malformed.
    """
    logging.info("Menu 206: starting org Zscaler synthetic-probe manager")
    logging.debug("ENTRY: manage_org_synthetic_probes(org_id=%s)", org_id)

    sources = _load_probe_sources(_DEFAULT_DATA_DIR)  # Fail-fast on missing data.
    vlan_ids = _prompt_vlan_list()  # FR-003.
    setting = _fetch_setting(mist_session, org_id)  # FR-004.
    existing_probes = _detect_existing(setting)  # FR-005 precondition.
    tool_authored, foreign = _partition_tool_authored(existing_probes)

    new_probes = _build_probe_set(sources, vlan_ids)  # FR-006..FR-010.

    if tool_authored:
        mode = _prompt_mode(tool_authored)  # FR-005.
        if mode == "merge":
            merged_tool = _merge_probes(tool_authored, new_probes, vlan_ids)
            if merged_tool == tool_authored:
                # Merge is a no-op only if VLANs, aggressiveness, and every
                # other synced field are already aligned. If a probe lost
                # critical status upstream we still need to write.
                print("  No changes required -- newly-entered VLANs already covered.")
                logging.info("Merge no-op: entered VLANs already covered by all probes")
                return
            resulting_tool = merged_tool
        else:
            resulting_tool = _swap_probes(new_probes)
    else:
        resulting_tool = new_probes  # Fresh deployment path (Story 1).

    demoted_foreign = _demote_stale_critical(foreign)  # Enforce 5-critical cap.
    summary = _summarise(resulting_tool, tool_authored, demoted_foreign, foreign)
    if not _prompt_confirm(summary):  # FR-013.
        print("  Operation cancelled -- no changes were made.")
        logging.info("Operator declined final confirmation; no PUT issued")
        return

    combined = {**demoted_foreign, **resulting_tool}  # FR-012 relaxed for critical demotion.
    _apply(mist_session, org_id, setting, combined, vlan_ids)  # FR-014.

    # Post-PUT site-override flow: give the operator a chance to push the
    # same probe set into one or more site-level settings so specific
    # sites can override the org-wide config.
    _prompt_and_apply_site_overrides(mist_session, org_id, resulting_tool)

    logging.debug("EXIT: manage_org_synthetic_probes - success")


def _load_probe_sources(data_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load the two curated Zscaler JSON files from ``data_dir``.

    Why:
        Centralising the file reads gives a single fail-closed choke point
        (edge case: files missing or malformed) and lets tests point the
        module at a fixture directory.

    Args:
        data_dir: Directory containing both curated files.

    Returns:
        A tuple ``(probes, cenr)`` -- the parsed contents of the client
        connector probe file and the CENR hostnames file, respectively.

    Raises:
        FileNotFoundError: If either source file is missing.
        ValueError: If either source file contains invalid JSON.
    """
    probes_path = data_dir / _PROBE_SOURCE_FILE
    cenr_path = data_dir / _CENR_SOURCE_FILE
    for path in (probes_path, cenr_path):
        if not path.is_file():
            raise FileNotFoundError(f"Required Zscaler source file is missing: {path}")
    try:
        probes = json.loads(probes_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        raise ValueError(f"Malformed JSON in {probes_path}: {err}") from err
    try:
        cenr = json.loads(cenr_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        raise ValueError(f"Malformed JSON in {cenr_path}: {err}") from err
    return probes, cenr


def _validate_vlan_input(raw: str) -> tuple[bool, str, list[int]]:
    """Parse and validate VLAN input string.

    Returns:
        (is_valid, error_message, vlan_ids). If is_valid is True, vlan_ids
        is non-empty and deduplicated; error_message is empty.
    """
    if not raw.strip():
        return False, "VLAN list cannot be empty. Please try again.", []
    parts = [item.strip() for item in raw.split(",") if item.strip()]
    try:
        ids = [int(part) for part in parts]
    except ValueError:
        return False, "Non-integer VLAN id detected. Please try again.", []
    if any(vid < _VLAN_MIN or vid > _VLAN_MAX for vid in ids):
        return False, f"VLAN ids must be in [{_VLAN_MIN}, {_VLAN_MAX}]. Please try again.", []
    return True, "", sorted(set(ids))


def _prompt_vlan_list() -> list[int]:
    """Prompt the operator for a comma-separated VLAN id list.

    Why:
        The VLAN list is the only per-invocation parameter; validating
        the range at prompt time (FR-003) avoids surfacing an opaque
        API-side rejection later.

    Returns:
        Sorted, deduplicated list of VLAN ids in ``[0, 4094]``. Never
        returns an empty list -- the prompt loops until at least one
        valid id is entered.
    """
    while True:
        raw = input("  Enter VLAN ids (comma-separated, each in [0, 4094]): ")
        is_valid, error, ids = _validate_vlan_input(raw)
        if is_valid:
            return ids
        print(f"  {error}")


def _fetch_setting(mist_session: Any, org_id: str) -> dict[str, Any]:
    """Return the current org setting block via mistapi.

    Why:
        Isolating the read call makes it trivial to mock in tests and
        clarifies the FR-004 boundary (get) from the FR-014 boundary
        (put).

    Args:
        mist_session: Authenticated ``mistapi`` session.
        org_id: Mist organisation UUID.

    Returns:
        The parsed JSON payload of ``getOrgSettings`` (defensively an
        empty dict if the API returned no body).
    """
    logging.debug("Calling getOrgSettings(org_id=%s)", org_id)
    response = _mist_setting.getOrgSettings(mist_session, org_id)
    data = getattr(response, "data", None)
    if not isinstance(data, dict):
        logging.warning("getOrgSettings returned non-dict payload; treating as empty")
        return {}
    return data


def _detect_existing(setting: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Extract ``synthetic_test.custom_probes`` from ``setting``.

    Why:
        Guarded accessor so callers don't have to worry about the
        edge case where either ``synthetic_test`` or ``custom_probes``
        is absent.

    Args:
        setting: Org setting block as returned by ``getOrgSettings``.

    Returns:
        The ``custom_probes`` map (``{name: probe_dict}``) if present,
        otherwise an empty dict.
    """
    synthetic = setting.get("synthetic_test") if isinstance(setting, dict) else None
    if not isinstance(synthetic, dict):
        return {}
    probes = synthetic.get("custom_probes")
    if not isinstance(probes, dict):
        return {}
    return probes


def _partition_tool_authored(
    existing: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Split existing probes into tool-authored and foreign sets.

    Why:
        FR-012 mandates that foreign probes (any probe whose name lacks
        the ``zcc-`` prefix) are preserved verbatim through merge and
        swap. Partitioning up-front keeps the downstream helpers pure.

    Args:
        existing: Full ``custom_probes`` map from the org setting.

    Returns:
        ``(tool_authored, foreign)`` -- two disjoint dicts whose union is
        ``existing``.
    """
    tool_authored: dict[str, dict[str, Any]] = {}
    foreign: dict[str, dict[str, Any]] = {}
    for name, probe in existing.items():
        if isinstance(name, str) and name.startswith(_TOOL_NAME_PREFIX):
            tool_authored[name] = probe
        else:
            foreign[name] = probe
    return tool_authored, foreign


def _fqdn_slug(fqdn: str) -> str:
    """Convert an FQDN to the slug segment used in probe names.

    Why:
        The naming rule (FR-010) requires a stable, filesystem-safe
        derivation from the FQDN so tool-authored probes are recognisable
        across re-runs. Lowercase + ``.`` -> ``-`` is sufficient because
        Zscaler FQDNs are ASCII-only.

    Args:
        fqdn: The concrete hostname (never a wildcard by the time this
            is called).

    Returns:
        Lowercased slug with dots replaced by hyphens.
    """
    return fqdn.lower().replace(".", "-")


def _iter_role_fqdns(role: dict[str, Any], cenr: dict[str, Any]) -> list[str]:
    """Yield the concrete FQDN list for a single role, expanding CENR.

    Why:
        Only the ``tunnel_zen`` role expands via the CENR file; every
        other role carries its FQDNs inline. Centralising the branch
        keeps ``_build_probe_set`` readable.

    Args:
        role: One entry from ``roles[]`` in the probe source file.
        cenr: Parsed CENR hostnames file (for the tunnel_zen expansion).

    Returns:
        A list of concrete FQDN strings (may include wildcards which the
        caller will filter).
    """
    if role.get("role") == _TUNNEL_ZEN_ROLE:
        proxy = cenr.get("proxy_hostnames", []) or []
        vpn = cenr.get("vpn_hostnames", []) or []
        return [*proxy, *vpn]
    fqdns = role.get("fqdns") or []
    return list(fqdns)


def _build_probe_set(
    sources: tuple[dict[str, Any], dict[str, Any]],
    vlan_ids: list[int],
) -> dict[str, dict[str, Any]]:
    """Build the full tool-authored probe set from the curated sources.

    Why:
        Pure function -- no I/O -- so the acceptance tests can pin the
        exact probe body produced for a given VLAN list. The
        ``critical`` / ``critical_fqdn`` flags on each role select
        exactly one probe per critical role to receive
        ``aggressiveness=critical`` so the org-wide 5-critical cap on
        the Mist side is respected without runtime discovery.

    Args:
        sources: The ``(probes, cenr)`` tuple from ``_load_probe_sources``.
        vlan_ids: Kept for signature/back-compat with the caller; ignored
            when building probe bodies because VLAN scoping belongs on
            the ``tests[]`` row that references the probe, not on the
            ``custom_probes`` definition itself (matches Mist's own
            ``mini-*`` shape observed 2026-07-24).

    Returns:
        A ``{probe_name: probe_body}`` map ready to be merged into the
        setting block. Wildcard FQDNs are skipped per FR-008.
    """
    probes_source, cenr_source = sources
    result: dict[str, dict[str, Any]] = {}
    for role in probes_source.get("roles", []) or []:
        role_name = role.get("role") or "unknown"
        critical_role = bool(role.get("critical"))
        critical_target = role.get("critical_fqdn")  # None => first eligible fqdn wins.
        critical_assigned = False
        for fqdn in _iter_role_fqdns(role, cenr_source):
            if not isinstance(fqdn, str) or fqdn.startswith("*."):
                continue  # FR-008: wildcards cannot be probed directly.
            # Pick exactly one critical FQDN per critical role. Preference
            # order: explicit ``critical_fqdn`` if it appears in the
            # expanded list, otherwise the first non-wildcard hit.
            is_critical = False
            if critical_role and not critical_assigned:
                if critical_target is None or fqdn == critical_target:
                    is_critical = True
                    critical_assigned = True
            probe_name = f"{_TOOL_NAME_PREFIX}{role_name}-{_fqdn_slug(fqdn)}"
            # Body shape mirrors Mist's own ``mini-*`` custom_probes
            # (live config 2026-07-24): no ``name`` inside the body (the
            # dict key IS the name) and no ``vlan_ids`` (VLAN scoping
            # belongs on the tests[] row that references the probe, not
            # on the probe definition itself).
            probe_body: dict[str, Any] = {
                "type": role.get("type", "application"),  # Match mini-* default.
                "target": f"https://{fqdn}",  # FR-007: prefix, no port.
            }
            # Emit an explicit aggressiveness on every probe: ``critical`` for
            # the curated priority roles, ``auto`` for the rest. Mist itself
            # writes ``"auto"`` on its default probes, so mirroring the value
            # keeps our output consistent with the platform's own convention.
            probe_body["aggressiveness"] = _CRITICAL_AGGRESSIVENESS if is_critical else _AUTO_AGGRESSIVENESS
            result[probe_name] = probe_body
        # Fallback: role declared critical but the requested
        # ``critical_fqdn`` was absent from the expansion. Promote the
        # first probe emitted for the role so we still spend a critical
        # slot on the intended role rather than silently downgrading.
        if critical_role and not critical_assigned:
            for probe_name, probe in result.items():
                slug_prefix = f"{_TOOL_NAME_PREFIX}{role_name}-"
                if probe_name.startswith(slug_prefix):
                    probe["aggressiveness"] = _CRITICAL_AGGRESSIVENESS
                    logging.warning(
                        "Role %s: critical_fqdn %r not found; promoted %s to critical",
                        role_name,
                        critical_target,
                        probe_name,
                    )
                    break
    return result


def _merge_probes(
    existing_tool: dict[str, dict[str, Any]],
    new_probes: dict[str, dict[str, Any]],
    extra_vlans: list[int],
) -> dict[str, dict[str, Any]]:
    """Re-sync tool-authored probes to the mini-* body shape.

    Why:
        Merge is the safe additive path (Story 2). Prior versions of the
        tool wrote ``name`` and ``vlan_ids`` INTO the probe body; the
        live Mist config (observed 2026-07-24) shows the correct shape
        is ``{type, target, aggressiveness}`` only, so this pass strips
        the legacy fields off any existing probe as a migration. The
        ``extra_vlans`` argument is retained purely for signature/back-
        compat with the caller -- VLAN scoping now lives exclusively on
        the ``tests[]`` row (handled by
        ``_merge_zcc_criticals_into_tests``). ``aggressiveness`` is
        re-synced from ``new_probes`` so a probe that lost its
        "critical" designation upstream is demoted here (and the freed
        critical slot re-lands on the correct probe).

    Args:
        existing_tool: Probes currently on the org matching ``zcc-``.
        new_probes: Freshly-built probe set. Used to look up the
            authoritative ``aggressiveness`` (and ``type``/``target``
            when normalising legacy bodies) for each matching probe.
        extra_vlans: Ignored; retained for caller signature back-compat.

    Returns:
        Merged probe map. Bodies conform to the mini-* shape:
        ``{type, target, aggressiveness}`` -- no ``name``, no
        ``vlan_ids``.
    """
    del extra_vlans  # Legacy parameter -- VLANs no longer live on probes.
    merged: dict[str, dict[str, Any]] = {}
    for name, probe in existing_tool.items():
        # Preserve the freshly-built type/target when we know them (the
        # new source of truth); otherwise fall back to the on-org values.
        template = new_probes.get(name, probe)
        merged_probe: dict[str, Any] = {
            "type": template.get("type") or probe.get("type") or "application",
            "target": template.get("target") or probe.get("target"),
        }
        # Sync aggressiveness from the freshly-built set so demotions
        # propagate (a probe that lost ``critical`` upstream should reflect
        # that here). ``_build_probe_set`` always emits an explicit value
        # (``critical`` or ``auto``), so the None branch is defensive only
        # -- it protects the merge if a future refactor drops the key.
        # Probes with no counterpart in ``new_probes`` (e.g. a role we
        # dropped from the JSON) keep their prior value.
        if name in new_probes:
            authoritative = new_probes[name].get("aggressiveness")
            merged_probe["aggressiveness"] = authoritative if authoritative is not None else _AUTO_AGGRESSIVENESS
        elif "aggressiveness" in probe:
            merged_probe["aggressiveness"] = probe["aggressiveness"]
        merged[name] = merged_probe
    return merged


def _swap_probes(
    new_probes: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Return the freshly-built probe set unchanged.

    Why:
        Swap is the destructive path (Story 3). The helper exists purely
        so the dispatch table in ``manage_org_synthetic_probes`` reads
        as a symmetric pair with ``_merge_probes``.

    Args:
        new_probes: Freshly-built probe set from ``_build_probe_set``.

    Returns:
        ``new_probes`` unchanged.
    """
    return new_probes


def _prompt_mode(existing_tool: dict[str, dict[str, Any]]) -> str:
    """Prompt the operator for merge vs. swap.

    Why:
        Explicit two-choice prompt (FR-005). Displaying the existing
        probe count and VLAN union up-front gives the operator the
        context needed to make the call without needing to walk the
        setting themselves.

    Args:
        existing_tool: Tool-authored probes currently on the org.

    Returns:
        Either ``"merge"`` or ``"swap"``.
    """
    all_vlans: set[int] = set()
    for probe in existing_tool.values():
        for vid in probe.get("vlan_ids") or []:
            if isinstance(vid, int):
                all_vlans.add(vid)
    print(f"  Existing tool-authored probes: {len(existing_tool)}")
    print(f"  VLAN union across existing probes: {sorted(all_vlans)}")
    while True:
        choice = input("  Choose action [merge/swap]: ").strip().lower()
        if choice in ("merge", "swap"):
            return choice
        print("  Please answer 'merge' or 'swap'.")


def _summarise(
    resulting_tool: dict[str, dict[str, Any]],
    existing_tool: dict[str, dict[str, Any]],
    resulting_foreign: dict[str, dict[str, Any]],
    original_foreign: dict[str, dict[str, Any]],
) -> str:
    """Build the human-readable confirmation summary string.

    Why:
        FR-013 requires the operator to see counts of add/remove/update
        and the resulting total before authorising the PUT. Splitting
        the summary out keeps ``_prompt_confirm`` reusable. The
        ``resulting_foreign`` vs ``original_foreign`` split lets the
        operator see how many foreign probes we demoted from
        ``critical`` to make room for the 5 tool-owned criticals.

    Args:
        resulting_tool: The tool-authored probe set that will be written.
        existing_tool: The tool-authored probe set currently on the org.
        resulting_foreign: Foreign probes after stale-critical demotion.
        original_foreign: Foreign probes exactly as fetched (baseline).

    Returns:
        A multi-line string suitable for printing.
    """
    added = set(resulting_tool) - set(existing_tool)
    removed = set(existing_tool) - set(resulting_tool)
    updated = {name for name in set(resulting_tool) & set(existing_tool) if resulting_tool[name] != existing_tool[name]}
    demoted_foreign = _count_critical_demotions(original_foreign, resulting_foreign)
    total_after = len(resulting_tool) + len(resulting_foreign)
    lines = [
        f"  Probes to add:        {len(added)}",
        f"  Probes to remove:     {len(removed)}",
        f"  Probes to update:     {len(updated)}",
        f"  Foreign preserved:    {len(resulting_foreign)}",
        f"  Foreign demoted:      {demoted_foreign} (critical key removed)",
        f"  Resulting total:      {total_after}",
    ]
    return "\n".join(lines)


def _count_critical_demotions(
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
) -> int:
    """Count probes whose aggressiveness changed from ``critical``.

    Why:
        Surface the exact number of foreign probes the operator is about
        to demote so the FR-012 relaxation (foreign preservation) is
        visible in the summary rather than silent.

    Args:
        before: Foreign probes as originally fetched.
        after: Foreign probes after ``_demote_stale_critical``.

    Returns:
        Number of shared names whose aggressiveness moved off ``critical``.
    """
    count = 0
    for name, probe in before.items():
        if probe.get("aggressiveness") != _CRITICAL_AGGRESSIVENESS:
            continue
        new_probe = after.get(name)
        if new_probe is None:
            continue
        if new_probe.get("aggressiveness") != _CRITICAL_AGGRESSIVENESS:
            count += 1
    return count


def _demote_stale_critical(
    foreign: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Return ``foreign`` with any ``aggressiveness=critical`` demoted to ``auto``.

    Why:
        Mist caps priority probes (both ``critical`` and ``high``) at 5
        per effective config. The tool now claims all 5 slots for the
        curated Zscaler roles at ``critical``, so any foreign probe
        currently marked critical must be demoted or the PUT is
        rejected. We write the literal ``"auto"`` (Mist's own default
        for non-priority probes) rather than dropping the key: it is
        idempotent across re-runs and mirrors the value Mist itself
        emits on system-generated probes. This intentionally relaxes
        FR-012's strict foreign-preservation guarantee -- the change is
        surfaced in ``_summarise`` so the operator sees it before
        confirming.

    Args:
        foreign: Foreign probe map (probes without the ``zcc-`` prefix).

    Returns:
        A new dict where every probe previously at
        ``aggressiveness=critical`` is copied with aggressiveness set to
        ``"auto"``. All other fields survive untouched.
    """
    result: dict[str, dict[str, Any]] = {}
    for name, probe in foreign.items():
        if isinstance(probe, dict) and probe.get("aggressiveness") == _CRITICAL_AGGRESSIVENESS:
            demoted = dict(probe)
            demoted["aggressiveness"] = _AUTO_AGGRESSIVENESS
            result[name] = demoted
            logging.info(
                "Demoting foreign critical probe %r (aggressiveness -> auto)",
                name,
            )
        else:
            result[name] = probe
    return result


def _prompt_confirm(summary: str) -> bool:
    """Show ``summary`` and ask the operator to confirm.

    Why:
        Isolated so tests can patch ``input`` without touching the rest
        of the flow. Only exact ``y`` / ``yes`` (case-insensitive)
        answers proceed; anything else aborts (FR-013 safe-default).

    Args:
        summary: Multi-line pre-PUT summary from ``_summarise``.

    Returns:
        ``True`` if the operator confirmed, ``False`` otherwise.
    """
    print("  Change summary:")
    print(summary)
    answer = input("  Proceed with PUT to org settings? [y/N]: ").strip().lower()
    return answer in ("y", "yes")


def _merge_zcc_criticals_into_tests(
    existing_tests: list[dict[str, Any]],
    combined_probes: dict[str, dict[str, Any]],
    vlan_ids: list[int],
) -> list[dict[str, Any]]:
    """Emit one ``tests[]`` row per critical tool-authored probe.

    Why:
        Verified against a live Mist ``GET /orgs/{id}/setting`` response
        2026-07-24: Mist itself emits one ``tests[]`` row per probe --
        each row's ``probes`` list contains exactly one probe name and
        the row carries its own ``vlan_ids`` / ``lan_networks`` copy.
        Both the system ``mini-*`` rows and any operator-scheduled probes
        follow this per-probe-per-row convention. Prior iterations of
        this module (a) appended a single tool-authored aggregate row
        named ``zcc-critical-probes`` and (b) merged all tool criticals
        into a single foreign row's ``probes`` list -- both diverge from
        the observed Mist convention and produce shapes operators flag
        as wrong. This function now migrates both legacy shapes and
        emits one nameless row per critical ``zcc-*`` probe, mirroring
        ``vlan_ids`` / ``lan_networks`` from the first surviving foreign
        row when one exists (so the injected rows inherit operator
        scoping) and falling back to the supplied ``vlan_ids`` arg when
        no foreign row is available as a template.

    Args:
        existing_tests: The ``tests[]`` list read from the fetched
            setting (may be empty).
        combined_probes: Union of foreign + tool-authored probes about
            to be written to ``synthetic_test.custom_probes``. Only
            probes with ``aggressiveness=critical`` are scheduled.
        vlan_ids: VLAN ids to attach to injected rows when no foreign
            row is available as a template. Ignored when a template row
            with its own ``vlan_ids`` exists.

    Returns:
        A new list. Foreign rows are preserved (with stale ``zcc-*``
        names stripped from their ``probes`` list). Rows that only ever
        contained ``zcc-*`` probes are dropped so re-injection is
        authoritative. Legacy aggregate rows whose ``name`` starts with
        ``zcc-`` are also dropped. One nameless row is appended per
        critical ``zcc-*`` probe, each carrying only that probe's name
        plus inherited ``vlan_ids`` / ``lan_networks``.
    """
    critical_names = sorted(
        name
        for name, probe in combined_probes.items()
        if isinstance(probe, dict) and probe.get("aggressiveness") == _CRITICAL_AGGRESSIVENESS
    )

    surviving: list[dict[str, Any]] = []
    for row in existing_tests:
        if not isinstance(row, dict):
            continue
        row_name = row.get("name")
        # Legacy cleanup: drop tool-authored aggregate rows written by
        # earlier versions of this module (name="zcc-critical-probes").
        if isinstance(row_name, str) and row_name.startswith(_TOOL_NAME_PREFIX):
            logging.info(
                "Dropping legacy tool-authored tests[] row %r (aggregate-row migration)",
                row_name,
            )
            continue
        cleaned = dict(row)
        probes_field = cleaned.get("probes")
        if isinstance(probes_field, list):
            filtered = [p for p in probes_field if not (isinstance(p, str) and p.startswith(_TOOL_NAME_PREFIX))]
            # A row that only ever held zcc-* names is a prior-run
            # injection; drop it so re-injection below is authoritative.
            if probes_field and not filtered:
                continue
            cleaned["probes"] = filtered
        surviving.append(cleaned)

    if not critical_names:
        return surviving

    # Inherit vlan/lan scoping from the first surviving foreign row so
    # injected zcc-* rows match operator intent. Fall back to the
    # supplied vlan_ids arg when no template is available.
    template_vlan_ids: list[int] | None = None
    template_lan_networks: list[str] | None = None
    for row in surviving:
        row_vlans = row.get("vlan_ids")
        row_lans = row.get("lan_networks")
        if isinstance(row_vlans, list) and template_vlan_ids is None:
            template_vlan_ids = [v for v in row_vlans if isinstance(v, int)]
        if isinstance(row_lans, list) and template_lan_networks is None:
            template_lan_networks = [ln for ln in row_lans if isinstance(ln, str)]
        if template_vlan_ids is not None and template_lan_networks is not None:
            break

    effective_vlans = template_vlan_ids if template_vlan_ids is not None else list(vlan_ids)

    for name in critical_names:
        new_row: dict[str, Any] = {"probes": [name], "vlan_ids": list(effective_vlans)}
        if template_lan_networks:
            new_row["lan_networks"] = list(template_lan_networks)
        surviving.append(new_row)

    return surviving


def _apply(
    mist_session: Any,
    org_id: str,
    setting: dict[str, Any],
    combined_probes: dict[str, dict[str, Any]],
    vlan_ids: list[int],
) -> None:
    """PUT the updated setting block via ``updateOrgSettings``.

    Why:
        Wrapper enforces FR-014 (exactly one PUT) and FR-015 (sibling
        preservation): we deep-copy the fetched ``setting`` block and
        only overwrite ``synthetic_test.custom_probes`` plus regenerate
        ``synthetic_test.tests[]`` for critical probes so the emitted
        probes are actually scheduled to run.

    Args:
        mist_session: Authenticated ``mistapi`` session.
        org_id: Mist organisation UUID.
        setting: The setting block previously returned by
            ``_fetch_setting`` (used as the base for the PUT body so any
            sibling fields under ``synthetic_test`` survive round-trip).
        combined_probes: Union of foreign and (merged/swapped)
            tool-authored probes.
        vlan_ids: VLAN ids to attach to each generated test row.
    """
    body: dict[str, Any] = json.loads(json.dumps(setting)) if setting else {}
    synthetic = body.get("synthetic_test")
    if not isinstance(synthetic, dict):
        synthetic = {}
        body["synthetic_test"] = synthetic
    synthetic["custom_probes"] = combined_probes
    existing_tests = synthetic.get("tests")
    if not isinstance(existing_tests, list):
        existing_tests = []
    synthetic["tests"] = _merge_zcc_criticals_into_tests(existing_tests, combined_probes, vlan_ids)
    logging.debug(
        "Calling updateOrgSettings(org_id=%s, probe_count=%d)",
        org_id,
        len(combined_probes),
    )
    response = _mist_setting.updateOrgSettings(mist_session, org_id, body)
    status = getattr(response, "status_code", None)
    if status is not None and (status < 200 or status >= 300):
        logging.error("updateOrgSettings HTTP %s", status)
        print(f"  updateOrgSettings failed with HTTP {status}")
        return
    print(f"  updateOrgSettings succeeded ({len(combined_probes)} probes written)")
    for probe_name in sorted(combined_probes):
        print(f"    - {probe_name}")
    logging.info("Wrote %d probes via updateOrgSettings", len(combined_probes))


def _prompt_and_apply_site_overrides(
    mist_session: Any,
    org_id: str,
    resulting_tool: dict[str, dict[str, Any]],
) -> None:
    """Offer to push the tool-authored probe set into per-site settings.

    Why:
        Mist site settings can override org-wide ``custom_probes``. After
        a successful org PUT the operator often wants a subset of sites
        (e.g. those with unusual VLAN topology or higher SLE
        expectations) to carry the same probe set locally so
        site-specific probe/VLAN interactions are testable without
        touching org config. Displaying an indexed table (rather than
        asking for raw UUIDs) removes the copy/paste burden and the
        common "typo'd UUID" failure mode operators reported. A separate
        VLAN prompt is issued after site selection because sites picked
        for an override typically have a *different* VLAN topology than
        the org default -- reusing the org list would defeat the point
        of the override. This whole flow is optional (default no) so
        unattended runs do not silently mutate site settings.

    Args:
        mist_session: Authenticated ``mistapi`` session.
        org_id: Mist org UUID -- required for ``listOrgSites`` so the
            index table shows only the sites the operator can actually
            target.
        resulting_tool: The tool-authored probe map just written to the
            org. Used as the source of truth (name/target/type/
            aggressiveness) to push into each chosen site; each probe's
            ``vlan_ids`` is replaced with the freshly-prompted list.
    """
    if not resulting_tool:
        return
    answer = input("  Configure site-level overrides with these same probes? [y/N]: ").strip().lower()
    if answer not in ("y", "yes"):
        logging.info("Operator declined site overrides")
        return
    sites = _list_org_sites(mist_session, org_id)
    if not sites:
        print("  No sites found in this org -- skipping site overrides.")
        return
    site_ids = _prompt_site_indexes(sites)
    if not site_ids:
        print("  No valid site indexes entered -- skipping site overrides.")
        return
    # Site overrides commonly target sites with distinct VLAN topology
    # (that's the reason to override an org-wide default in the first
    # place), so re-prompt for the VLAN list rather than silently reusing
    # the org-scope list. VLANs live on the generated tests[] rows only;
    # probe bodies carry {type, target, aggressiveness} to match mini-*.
    print("  Enter the VLAN ids to apply to the selected sites' tests[] rows.")
    site_vlan_ids = _prompt_vlan_list()
    for site_id in site_ids:
        _apply_to_site(mist_session, site_id, resulting_tool, site_vlan_ids)


def _list_org_sites(mist_session: Any, org_id: str) -> list[dict[str, Any]]:
    """Return every site in ``org_id`` as a paginated list of dicts.

    Why:
        The indexed site picker needs the full site list up-front so the
        operator can see every option in one screen. Isolating the fetch
        keeps ``_prompt_and_apply_site_overrides`` unit-testable via a
        single patch point, and mirrors the pagination pattern used in
        ``APICoreFetchUtils.all_sites_with_limit``. Errors are logged
        and surfaced as an empty list so callers degrade gracefully
        (skipping the site flow) rather than aborting the whole run.

    Args:
        mist_session: Authenticated ``mistapi`` session.
        org_id: Mist org UUID.

    Returns:
        List of site dicts (``id``, ``name`` at minimum). Empty list on
        API failure or when the org has no sites.
    """
    try:
        response = _mist_orgs_sites.listOrgSites(mist_session, org_id)
        sites = mistapi.get_all(response=response, mist_session=mist_session)
    except Exception as err:  # noqa: BLE001 -- surface any transport error.
        logging.error("listOrgSites(%s) failed: %s", org_id, err)
        print(f"  listOrgSites failed ({err}); skipping site overrides.")
        return []
    if not isinstance(sites, list):
        return []
    # Filter to entries that at minimum carry an id we can PUT against.
    return [s for s in sites if isinstance(s, dict) and s.get("id")]


def _prompt_site_indexes(sites: list[dict[str, Any]]) -> list[str]:
    """Display an indexed site table and return the ids the operator picks.

    Why:
        UUID entry proved error-prone in the field (operators pasted
        trailing whitespace, wrong-org UUIDs, or truncated ids). An
        indexed prompt eliminates that class of typo entirely and lets
        the operator eyeball site names before committing. The list is
        sorted by human-readable site name (case-insensitive) so the
        picker matches how operators think about their fleet; unnamed
        sites sink to the bottom. Kept in its own helper so tests can
        patch ``input`` for this stage independently of the earlier y/N
        prompt.

    Args:
        sites: List of site dicts as returned by ``_list_org_sites``. The
            function sorts a local copy by name before display, so the
            caller's ordering is irrelevant.

    Returns:
        Deduplicated list of site id strings corresponding to valid
        1-based indexes (into the *sorted* view) supplied by the
        operator. Empty list if the operator supplied nothing or every
        entry was out of range / non-numeric.
    """
    print("  Available sites:")
    # Sort by human-readable name (case-insensitive) so the picker matches
    # how operators think about their fleet. Unnamed sites sort to the end
    # to keep the deterministic ordering stable regardless of API return
    # order. The sorted list becomes the 1-based index map for the prompt.
    sorted_sites = sorted(
        sites,
        key=lambda s: (
            0 if (s.get("name") or "").strip() else 1,
            (s.get("name") or "").casefold(),
            s.get("id") or "",
        ),
    )
    # 1-based indexes are more natural for humans; keep width consistent
    # for large orgs so the columns line up in a terminal.
    width = len(str(len(sorted_sites)))
    for idx, site in enumerate(sorted_sites, start=1):
        name = site.get("name") or "(unnamed)"
        site_id = site.get("id", "")
        print(f"    [{idx:>{width}}] {name}  ({site_id})")
    raw = input("  Enter comma-separated site indexes to override, or leave blank to cancel: ")
    parts = [item.strip() for item in raw.split(",") if item.strip()]
    seen: dict[str, None] = {}
    for part in parts:
        try:
            idx = int(part)
        except ValueError:
            logging.warning("Ignoring non-numeric site index token: %r", part)
            continue
        if idx < 1 or idx > len(sorted_sites):
            logging.warning("Ignoring out-of-range site index: %d", idx)
            continue
        site_id = sorted_sites[idx - 1].get("id")
        if isinstance(site_id, str) and site_id:
            seen.setdefault(site_id, None)
    return list(seen)


def _apply_to_site(
    mist_session: Any,
    site_id: str,
    tool_probes: dict[str, dict[str, Any]],
    vlan_ids: list[int],
) -> None:
    """PUT ``tool_probes`` into the given site's ``custom_probes`` block.

    Why:
        Site-level custom_probes lives at ``synthetic_test.custom_probes``
        in the site setting, mirroring the org shape. This helper reuses
        the same partition/demote logic as the org path so Mist's
        5-probe priority cap (which counts both ``critical`` and
        ``high``) is respected on the effective (org + site) config:
        any pre-existing foreign probe with
        ``aggressiveness=critical`` has that key stripped, every
        ``zcc-`` probe is authoritatively replaced, and
        ``synthetic_test.tests[]`` gets regenerated for critical
        probes so the site's schedule actually runs them.

    Args:
        mist_session: Authenticated ``mistapi`` session.
        site_id: Mist site UUID.
        tool_probes: Tool-authored probe set to write.
        vlan_ids: VLAN ids to attach to each generated test row.
    """
    logging.info("Applying site override to site_id=%s", site_id)
    try:
        response = _mist_site_setting.getSiteSetting(mist_session, site_id)
    except Exception as err:  # noqa: BLE001 -- surface any transport error.
        print(f"  Site {site_id}: getSiteSetting failed ({err}); skipping.")
        logging.error("getSiteSetting(%s) failed: %s", site_id, err)
        return
    site_setting = getattr(response, "data", None)
    if not isinstance(site_setting, dict):
        site_setting = {}
    existing_probes = _detect_existing(site_setting)
    _, foreign = _partition_tool_authored(existing_probes)
    foreign_demoted = _demote_stale_critical(foreign)
    combined = {**foreign_demoted, **tool_probes}

    body: dict[str, Any] = json.loads(json.dumps(site_setting)) if site_setting else {}
    synthetic = body.get("synthetic_test")
    if not isinstance(synthetic, dict):
        synthetic = {}
        body["synthetic_test"] = synthetic
    synthetic["custom_probes"] = combined
    existing_tests = synthetic.get("tests")
    if not isinstance(existing_tests, list):
        existing_tests = []
    synthetic["tests"] = _merge_zcc_criticals_into_tests(existing_tests, combined, vlan_ids)

    logging.debug(
        "Calling updateSiteSettings(site_id=%s, probe_count=%d)",
        site_id,
        len(combined),
    )
    try:
        put_response = _mist_site_setting.updateSiteSettings(mist_session, site_id, body)
    except Exception as err:  # noqa: BLE001 -- surface any transport error.
        print(f"  Site {site_id}: updateSiteSettings failed ({err}); skipping.")
        logging.error("updateSiteSettings(%s) failed: %s", site_id, err)
        return
    status = getattr(put_response, "status_code", None)
    if status is not None and (status < 200 or status >= 300):
        print(f"  Site {site_id}: updateSiteSettings HTTP {status}")
        logging.error("updateSiteSettings(%s) HTTP %s", site_id, status)
        return
    print(
        f"  Site {site_id}: override applied " f"({len(tool_probes)} tool-authored + {len(foreign_demoted)} preserved)"
    )

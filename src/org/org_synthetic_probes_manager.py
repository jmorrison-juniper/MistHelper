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

# WHY: Import the mistapi setting module at module load. This is
# side-effect free (just a re-export of two API callables) and lets us
# monkey-patch it cleanly in unit tests via ``patch.object``.
from mistapi.api.v1.orgs import setting as _mist_setting

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_PROBE_SOURCE_FILE = "zscaler_client_connector_probes.json"
_CENR_SOURCE_FILE = "zscaler_cenr_hostnames.json"
_TOOL_NAME_PREFIX = "zcc-"  # FR-010: marks probes authored by this tool.
_TUNNEL_ZEN_ROLE = "tunnel_zen"  # Only role that expands via CENR hostnames.
_VLAN_MIN = 0  # FR-003 lower bound.
_VLAN_MAX = 4094  # FR-003 upper bound.


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
                print("  No changes required -- newly-entered VLANs already covered.")
                logging.info("Merge no-op: entered VLANs already covered by all probes")
                return
            resulting_tool = merged_tool
        else:
            resulting_tool = _swap_probes(new_probes)
    else:
        resulting_tool = new_probes  # Fresh deployment path (Story 1).

    summary = _summarise(resulting_tool, tool_authored, foreign)
    if not _prompt_confirm(summary):  # FR-013.
        print("  Operation cancelled -- no changes were made.")
        logging.info("Operator declined final confirmation; no PUT issued")
        return

    combined = {**foreign, **resulting_tool}  # FR-012: foreign preserved.
    _apply(mist_session, org_id, setting, combined)  # FR-014.
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
        raw = input("  Enter VLAN ids (comma-separated, each in [0, 4094]): ").strip()
        if not raw:
            print("  VLAN list cannot be empty. Please try again.")
            continue
        parts = [item.strip() for item in raw.split(",") if item.strip()]
        try:
            ids = [int(part) for part in parts]
        except ValueError:
            print("  Non-integer VLAN id detected. Please try again.")
            continue
        if any(vid < _VLAN_MIN or vid > _VLAN_MAX for vid in ids):
            print(f"  VLAN ids must be in [{_VLAN_MIN}, {_VLAN_MAX}]. Please try again.")
            continue
        if not ids:
            print("  VLAN list cannot be empty. Please try again.")
            continue
        return sorted(set(ids))


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
        exact probe body produced for a given VLAN list.

    Args:
        sources: The ``(probes, cenr)`` tuple from ``_load_probe_sources``.
        vlan_ids: VLAN id list to apply to every emitted probe.

    Returns:
        A ``{probe_name: probe_body}`` map ready to be merged into the
        setting block. Wildcard FQDNs are skipped per FR-008.
    """
    probes_source, cenr_source = sources
    result: dict[str, dict[str, Any]] = {}
    for role in probes_source.get("roles", []) or []:
        role_name = role.get("role") or "unknown"
        for fqdn in _iter_role_fqdns(role, cenr_source):
            if not isinstance(fqdn, str) or fqdn.startswith("*."):
                continue  # FR-008: wildcards cannot be probed directly.
            probe_name = f"{_TOOL_NAME_PREFIX}{role_name}-{_fqdn_slug(fqdn)}"
            result[probe_name] = {
                "name": probe_name,
                "type": role.get("type", "reachability"),  # FR-009 default.
                "target": f"https://{fqdn}",  # FR-007: prefix, no port.
                "vlan_ids": list(vlan_ids),
                "aggressiveness": role.get("aggressiveness", "high"),  # FR-009.
            }
    return result


def _merge_probes(
    existing_tool: dict[str, dict[str, Any]],
    new_probes: dict[str, dict[str, Any]],
    extra_vlans: list[int],
) -> dict[str, dict[str, Any]]:
    """Union ``extra_vlans`` into each existing tool-authored probe.

    Why:
        Merge is the safe additive path (Story 2). Names, targets, and
        siblings are preserved -- only ``vlan_ids`` is rewritten as the
        deduplicated, sorted union.

    Args:
        existing_tool: Probes currently on the org matching ``zcc-``.
        new_probes: Freshly-built probe set (unused for merge -- kept in
            the signature for symmetry with ``_swap_probes`` and to give
            the caller a landing spot for FR-011 future extension).
        extra_vlans: VLAN ids to add.

    Returns:
        Merged probe map. Identical to ``existing_tool`` if no probe
        gained a new VLAN.
    """
    _ = new_probes  # Reserved for future FR-011 extension; keeps API symmetric.
    merged: dict[str, dict[str, Any]] = {}
    for name, probe in existing_tool.items():
        current_vlans = probe.get("vlan_ids") or []
        union = sorted(set(current_vlans) | set(extra_vlans))
        merged_probe = dict(probe)
        merged_probe["vlan_ids"] = union
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
    foreign: dict[str, dict[str, Any]],
) -> str:
    """Build the human-readable confirmation summary string.

    Why:
        FR-013 requires the operator to see counts of add/remove/update
        and the resulting total before authorising the PUT. Splitting
        the summary out keeps ``_prompt_confirm`` reusable.

    Args:
        resulting_tool: The tool-authored probe set that will be written.
        existing_tool: The tool-authored probe set currently on the org.
        foreign: Probes not owned by this tool (preserved unchanged).

    Returns:
        A multi-line string suitable for printing.
    """
    added = set(resulting_tool) - set(existing_tool)
    removed = set(existing_tool) - set(resulting_tool)
    updated = {name for name in set(resulting_tool) & set(existing_tool) if resulting_tool[name] != existing_tool[name]}
    total_after = len(resulting_tool) + len(foreign)
    lines = [
        f"  Probes to add:     {len(added)}",
        f"  Probes to remove:  {len(removed)}",
        f"  Probes to update:  {len(updated)}",
        f"  Foreign preserved: {len(foreign)}",
        f"  Resulting total:   {total_after}",
    ]
    return "\n".join(lines)


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


def _apply(
    mist_session: Any,
    org_id: str,
    setting: dict[str, Any],
    combined_probes: dict[str, dict[str, Any]],
) -> None:
    """PUT the updated setting block via ``updateOrgSettings``.

    Why:
        Wrapper enforces FR-014 (exactly one PUT) and FR-015 (sibling
        preservation): we deep-copy the fetched ``setting`` block and
        only overwrite ``synthetic_test.custom_probes``.

    Args:
        mist_session: Authenticated ``mistapi`` session.
        org_id: Mist organisation UUID.
        setting: The setting block previously returned by
            ``_fetch_setting`` (used as the base for the PUT body so any
            sibling fields under ``synthetic_test`` survive round-trip).
        combined_probes: Union of foreign and (merged/swapped)
            tool-authored probes.
    """
    body: dict[str, Any] = json.loads(json.dumps(setting)) if setting else {}
    synthetic = body.get("synthetic_test")
    if not isinstance(synthetic, dict):
        synthetic = {}
        body["synthetic_test"] = synthetic
    synthetic["custom_probes"] = combined_probes
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

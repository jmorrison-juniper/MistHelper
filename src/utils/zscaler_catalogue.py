"""Multi-cloud Zscaler CENR catalogue refresher with freshness gating.

Why:
    Menu option 206 (org synthetic-probes manager) seeds Mist synthetic tests
    from ``data/zscaler_cenr_hostnames.json``. Historically that file only
    covered a single Zscaler cloud (``zscaler.net``) and was hand-refreshed,
    so ZEN pops in customer tenants on the other six clouds were invisible
    and the cached JSON could drift arbitrarily far from reality.

    This module fixes both problems by lazily refreshing the merged catalogue
    from all seven canonical Zscaler clouds whenever the on-disk copy is more
    than eight hours old, then running a full-fleet port/protocol validation
    pass via :func:`src.utils.zscaler_probe.run_full_validation`. The
    refresher is fail-open: any network or parse failure keeps the stale
    cache and logs a warning rather than blocking the menu.

    The 8h TTL, single-file flat-merged layout, and full-fleet validation
    scope are locked design decisions from the approved plan; do not tighten
    the TTL or shard the file without re-opening that discussion.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# Local repo imports. ``attach_city_metadata`` lives in scripts/ so the
# CLI variant can keep its strict SystemExit; the library form here always
# returns warnings instead of raising, which is what the auto-refresh path
# needs to stay non-fatal.
from scripts.build_zen_city_metadata import attach_city_metadata
from src.utils.zscaler_probe import (
    DEFAULT_TIMEOUT,
    DEFAULT_WORKERS,
    ProbeResult,
    run_full_validation,
)

logger = logging.getLogger(__name__)

# Canonical Zscaler cloud slugs served by ``config.zscaler.com``. Order is
# stable so ``source_urls`` in the written file is reproducible across runs.
_CLOUDS: tuple[str, ...] = (
    "zscaler.net",
    "zscalerone.net",
    "zscalertwo.net",
    "zscalerthree.net",
    "zscloud.net",
    "zscalergov.net",
    "zscalerbeta.net",
)

# Freshness TTL for the merged CENR cache. Set to 8h per the approved plan
# (user tightened from a 1h proposal to reduce API load on ``config.zscaler.com``
# while still guaranteeing at least three refreshes per day).
_FRESHNESS_TTL = timedelta(hours=8)

_CENR_URL_TEMPLATE = "https://config.zscaler.com/api/{cloud}/cenr/json"

# HTTPS GET timeout per cloud fetch. Kept short so a single misbehaving
# cloud endpoint cannot delay menu 206 startup by more than a handful of
# seconds even in the worst case (7 clouds x _FETCH_TIMEOUT).
_FETCH_TIMEOUT = 10.0

_SCHEMA_VERSION = 3  # v3 promotes flat host strings into per-host observation dicts (feature 1023)


def _promote_host_entry(entry: str | dict[str, Any]) -> dict[str, Any]:
    """Promote a v2 flat-string host entry to the v3 per-host object shape.

    Why:
        Feature 1023 (contract ``cenr_cache_schema_v3.md``) upgrades every
        cached hostname bag from ``list[str]`` to
        ``list[{"host": str, "observed_protocol": str|None,
        "observed_port": int|None, "last_probed": str|None}]`` so downstream
        consumers (``_probe_target`` in menu 206) can dispatch on the last
        observed reachability protocol. Existing on-disk caches were written
        as flat strings; a load-time promotion keeps them usable without
        forcing a refresh. FR-006 forbids reading a v2 cache from crashing.

    Args:
        entry: Either the legacy bare hostname string, or an already-v3
            host dict returned unchanged.

    Returns:
        A dict with at minimum ``{"host": <fqdn>}``. When the input is
        already a dict, it is returned as-is (no observation defaults are
        injected; ``_probe_target`` treats missing observation keys as the
        "no observation" branch).
    """
    if isinstance(entry, str):
        # Legacy v2 shape: single hostname string with no observation state.
        # Wrap into the minimal v3 object; observation fields intentionally
        # omitted so downstream callers see them as absent/None per contract.
        return {"host": entry}
    if isinstance(entry, dict):
        # Already v3 (or newer): pass through untouched so re-promotion is a
        # no-op (idempotency required for round-trip write-then-load tests).
        return entry
    # Defensive: unexpected shape (for example int, None). Wrap into a stringified
    # host so downstream code never blows up on malformed cache entries.
    return {"host": str(entry)}


def _promote_cenr_document(doc: dict[str, Any]) -> dict[str, Any]:
    """Walk every host bag in a CENR document and promote v2 -> v3 in-place.

    Why:
        The CENR file has FOUR host bags per contract
        ``cenr_cache_schema_v3.md``: ``proxy_hostnames``, ``vpn_hostnames``,
        and the same two nested under each ``by_city[*]`` slot. Any bag
        containing legacy strings must be promoted so ``_probe_target`` can
        look entries up by ``entry["host"]`` uniformly.

    Args:
        doc: The parsed CENR JSON document. Mutated in place.

    Returns:
        The same ``doc`` after promotion, for chaining convenience.
    """
    for bag_key in ("proxy_hostnames", "vpn_hostnames"):
        bag = doc.get(bag_key)
        if isinstance(bag, list):
            # Rebuild the bag so every element is a v3 host dict; preserves
            # element order (matters for deterministic diff-friendly writes).
            doc[bag_key] = [_promote_host_entry(entry) for entry in bag]
    by_city = doc.get("by_city")
    if isinstance(by_city, dict):
        for city_slot in by_city.values():
            if not isinstance(city_slot, dict):
                continue
            for bag_key in ("proxy_hostnames", "vpn_hostnames"):
                bag = city_slot.get(bag_key)
                if isinstance(bag, list):
                    # Per-city bags follow the same v2 -> v3 shape rule as
                    # the top-level bags; keep the two paths in lockstep.
                    city_slot[bag_key] = [_promote_host_entry(entry) for entry in bag]
    return doc


def _promote_zcc_document(doc: dict[str, Any]) -> dict[str, Any]:
    """Walk every ``roles[*].fqdns`` bag in a ZCC probes document and promote v2 -> v3.

    Why:
        The client-connector probes file (``zscaler_client_connector_probes.json``)
        uses the same v2 -> v3 host-entry shape but nested under
        ``roles[<role_name>].fqdns`` rather than the four CENR bags. Kept
        separate from ``_promote_cenr_document`` because the outer shape
        differs (top-level ``roles`` dict vs top-level host bags).

    Args:
        doc: The parsed ZCC probes JSON document. Mutated in place.

    Returns:
        The same ``doc`` after promotion, for chaining convenience.
    """
    roles = doc.get("roles")
    # The on-disk ZCC schema stores ``roles`` as a list of role objects (each
    # with its own ``fqdns`` bag). Older/hand-authored variants may store it as
    # a dict keyed by role name; support both so promotion is shape-agnostic.
    role_bodies: list[Any] = []
    if isinstance(roles, list):
        role_bodies = list(roles)
    elif isinstance(roles, dict):
        role_bodies = list(roles.values())
    for role_body in role_bodies:
        if not isinstance(role_body, dict):
            continue
        fqdns = role_body.get("fqdns")
        if isinstance(fqdns, list):
            # Same promotion rule as CENR bags; keeps the FQDN element
            # shape uniform across both cache files so downstream code
            # can treat any host entry as ``{"host": <fqdn>, ...}``.
            role_body["fqdns"] = [_promote_host_entry(entry) for entry in fqdns]
    return doc


def _count_cenr_host_entries(doc: dict[str, Any]) -> int:
    """Return the total number of host entries in the top-level CENR bags.

    Why:
        Fed into the mandatory single ``logger.info`` line emitted by
        :func:`promote_cache_document` so operators can eyeball the load
        size without opening the JSON. Only the two top-level bags are
        counted (per-city entries are subsets of the top-level union).

    Args:
        doc: The parsed CENR document.

    Returns:
        Non-negative int count of ``proxy_hostnames`` + ``vpn_hostnames``.
    """
    total = 0
    for bag_key in ("proxy_hostnames", "vpn_hostnames"):
        bag = doc.get(bag_key)
        if isinstance(bag, list):
            total += len(bag)
    return total


def _count_zcc_host_entries(doc: dict[str, Any]) -> int:
    """Return the total number of FQDN entries across all ZCC roles.

    Why:
        Same rationale as :func:`_count_cenr_host_entries` but for the ZCC
        probes file. Emitted in the single INFO line so both cache files
        report a load-size metric consistently.

    Args:
        doc: The parsed ZCC probes document.

    Returns:
        Non-negative int count of every ``roles[*].fqdns`` entry summed.
    """
    total = 0
    roles = doc.get("roles")
    # Same list-vs-dict tolerance as ``_promote_zcc_document`` so the load-size
    # counter never under-reports just because the outer shape is a list.
    role_bodies: list[Any] = []
    if isinstance(roles, list):
        role_bodies = list(roles)
    elif isinstance(roles, dict):
        role_bodies = list(roles.values())
    for role_body in role_bodies:
        if isinstance(role_body, dict):
            fqdns = role_body.get("fqdns")
            if isinstance(fqdns, list):
                total += len(fqdns)
    return total


def _bag_starts_with_str(bag: Any) -> bool:
    """Return True when ``bag`` is a non-empty list whose first entry is a string.

    Why:
        Shape-probe primitive shared by :func:`_cenr_needs_promotion` and
        :func:`_zcc_needs_promotion`. Extracted so the outer helpers stay
        under Radon CC>10 without duplicating the ``isinstance`` chain.

    Args:
        bag: Arbitrary value from a parsed cache document.

    Returns:
        ``True`` when ``bag`` is a non-empty list and ``bag[0]`` is a
        ``str``; ``False`` otherwise.
    """
    return isinstance(bag, list) and bool(bag) and isinstance(bag[0], str)


def _cenr_needs_promotion(doc: dict[str, Any]) -> bool:
    """Return True when any CENR host bag still contains a flat-string entry.

    Why:
        A prior version of :func:`merge_clouds` stamped
        ``schema_version=3`` on a document whose bags were still
        ``list[str]`` (see the fix that emits ``_promote_host_entry`` output
        in the writer). Trusting the version stamp alone caused
        :func:`promote_cache_document` to short-circuit past the promotion,
        and every downstream v3-dict-only walker
        (``_merge_observations_into_cenr``, ``_lookup_v3_observation`` in
        ``org_synthetic_probes_manager``) silently skipped the whole cache.
        Cheap first-entry shape probing across the four bags lets the loader
        self-heal without a mandatory delete-and-refresh.

    Args:
        doc: Parsed CENR document.

    Returns:
        ``True`` if any inspected bag's first element is a bare string;
        ``False`` when every non-empty bag already carries dict entries.
    """
    for bag_key in ("proxy_hostnames", "vpn_hostnames"):
        if _bag_starts_with_str(doc.get(bag_key)):
            return True
    by_city = doc.get("by_city")
    if not isinstance(by_city, dict):
        return False
    for city_slot in by_city.values():
        if not isinstance(city_slot, dict):
            continue
        for bag_key in ("proxy_hostnames", "vpn_hostnames"):
            if _bag_starts_with_str(city_slot.get(bag_key)):
                return True
    return False


def _zcc_needs_promotion(doc: dict[str, Any]) -> bool:
    """Return True when any ``roles[*].fqdns`` bag still contains a flat string.

    Why:
        Symmetric self-heal check for the ZCC probes cache. Same rationale
        as :func:`_cenr_needs_promotion`: a stamp-mismatch caused by a bug
        in an older writer should not make the loader trust a lie and
        strand the observation-merge walkers.

    Args:
        doc: Parsed ZCC probes document.

    Returns:
        ``True`` if any inspected FQDN bag's first element is a bare string.
    """
    roles = doc.get("roles")
    role_bodies: list[Any] = []
    if isinstance(roles, list):
        role_bodies = list(roles)
    elif isinstance(roles, dict):
        role_bodies = list(roles.values())
    for role_body in role_bodies:
        if not isinstance(role_body, dict):
            continue
        fqdns = role_body.get("fqdns")
        if isinstance(fqdns, list) and fqdns and isinstance(fqdns[0], str):
            return True
    return False


def promote_cache_document(doc: dict[str, Any], *, kind: str) -> dict[str, Any]:
    """Public v2 -> v3 loader adapter for either cache file kind.

    Why:
        Single entry point wired into :func:`ensure_fresh` (CENR path) and
        the ZCC probes read in
        :func:`src.org.org_synthetic_probes_manager._load_probe_sources`.
        Detects ``schema_version < 3`` (or missing) and promotes every
        applicable host bag, emitting EXACTLY ONE ``logger.info`` line per
        promotion event so operators have a single grep target for
        "loaded a legacy cache". Idempotent when called against an already
        v3 document (no promotion, no log line).

    Args:
        doc: Parsed JSON document from disk. Mutated in place when promotion
            fires; unmodified when already v3.
        kind: Either ``"cenr"`` (top-level proxy/vpn bags plus by_city) or
            ``"zcc"`` (roles[*].fqdns). Any other value is a caller bug and
            is treated as a no-op so a typo cannot silently drop data.

    Returns:
        The (possibly mutated) ``doc`` for call-site chaining.
    """
    detected = doc.get("schema_version")
    # Coerce missing/non-int schema_version to 0 so the INFO line always
    # reports a numeric version (contract mandates %d formatting).
    detected_int = detected if isinstance(detected, int) else 0
    # Shape-probe the bags rather than trusting the version stamp alone: a
    # prior writer bug produced ``schema_version=3`` documents with flat-
    # string bags, and a stamp-only short-circuit stranded every downstream
    # v3-dict walker. If the stamp says v3 AND the bags actually look v3,
    # we skip; otherwise fall through and (re)promote silently.
    needs_promotion = (
        _cenr_needs_promotion(doc) if kind == "cenr" else _zcc_needs_promotion(doc) if kind == "zcc" else False
    )
    if isinstance(detected, int) and detected >= _SCHEMA_VERSION and not needs_promotion:
        # Already v3 in both stamp and shape -> skip promotion entirely; do
        # NOT log so steady-state loads stay quiet at INFO.
        return doc
    if kind == "cenr":
        # Contract cenr_cache_schema_v3.md: promote all four CENR bags.
        doc = _promote_cenr_document(doc)
        count = _count_cenr_host_entries(doc)
    elif kind == "zcc":
        # Contract cenr_cache_schema_v3.md: promote roles[*].fqdns bag.
        doc = _promote_zcc_document(doc)
        count = _count_zcc_host_entries(doc)
    else:
        # Unknown kind: still emit the diagnostic INFO but skip promotion so
        # nothing silently mutates a document we do not understand.
        count = 0
    # Stamp the current schema version after promotion so the next load short-
    # circuits without re-emitting the INFO line (idempotency contract).
    doc["schema_version"] = _SCHEMA_VERSION
    logger.info(
        "zscaler_catalogue: loaded v%d cache (%d entries); observations absent",
        detected_int,
        count,
    )
    return doc


def _pick_udp_observation(
    udp_states: dict[int, str],
) -> tuple[str, int] | None:
    """Return the winning UDP/IKE observation, or ``None`` when both are silent.

    Why:
        Extracted from :func:`_pick_observation_from_probe_result` so the
        outer priority ladder stays under Radon CC>10. Keeps the fixed order
        (UDP/500 before UDP/4500) with the "silent" filter in one place so
        R-003 does not drift between the two arms.

    Args:
        udp_states: Per-port state map from ``ProbeResult.udp``.

    Returns:
        ``("UDP/500", 500)`` or ``("UDP/4500", 4500)`` when the matching
        port responded non-silently; ``None`` when neither did.
    """
    for port in (500, 4500):
        if port in udp_states and udp_states.get(port) != "silent":
            return f"UDP/{port}", port
    return None


def _pick_observation_from_probe_result(
    pr: ProbeResult,
) -> tuple[str | None, int | None]:
    """Return the (protocol, port) tuple to persist for one probed endpoint.

    Why:
        Implements requirement R-003 (contract
        ``cenr_cache_schema_v3.md`` §"Write Path priority"). The v3 cache
        stores AT MOST ONE observation per host so ``_probe_target`` in
        menu 206 can pick a single, deterministic branch when it later builds
        the synthetic-test URL. Priority is fixed: HTTPS on 443 beats every
        UDP or non-443 TCP result because an HTTPS 200/HEAD is the strongest
        signal that the endpoint is fully alive from the customer's edge.
        UDP/500 (IKE main) is picked before UDP/4500 (NAT-T) because the two
        are always probed together and 500 is the semantically primary IKE
        port; picking 500 first also keeps observation output stable across
        NAT-fronted and non-NAT-fronted sites. Any remaining open TCP port
        wins over a null observation so probing effort never gets discarded.

    Args:
        pr: A single :class:`ProbeResult` from the full-fleet validation
            pass. Only the ``tcp``, ``udp``, and ``https_status`` fields are
            inspected.

    Returns:
        Two-tuple of ``(protocol, port)`` where ``protocol`` is
        ``"HTTPS"``, ``"UDP/500"``, ``"UDP/4500"``, or ``"TCP"`` and
        ``port`` is the corresponding port number. Returns ``(None, None)``
        when no port responded so the caller writes ``observed_protocol =
        None`` per contract.
    """
    tcp_states: dict[int, str] = getattr(pr, "tcp", None) or {}
    https_status = getattr(pr, "https_status", None)
    if tcp_states.get(443) == "open" and https_status is not None:
        return "HTTPS", 443
    udp_pick = _pick_udp_observation(getattr(pr, "udp", None) or {})
    if udp_pick is not None:
        return udp_pick
    for port, state in tcp_states.items():
        if port != 443 and state == "open":
            return "TCP", port
    return None, None


def _merge_observations_into_cenr(
    doc: dict[str, Any],
    observations: dict[str, tuple[str | None, int | None, str]],
) -> int:
    """Stamp per-host observations onto every CENR host bag in ``doc``.

    Why:
        The write-back step of R-003: after the full-fleet validation pass
        finishes, each host's newest observation must land on disk so a
        later menu 206 invocation can dispatch on the persisted state
        without re-probing. Walks the same four bags as
        :func:`_promote_cenr_document` (proxy/vpn top-level plus by_city
        variants) so the on-disk shape stays symmetric with the loader.
        In-place mutation avoids re-allocating the (potentially large)
        merged document.

    Args:
        doc: Fresh CENR document from :func:`refresh_cenr` (already v3).
            Mutated in place.
        observations: Map of ``fqdn`` -> ``(protocol, port, iso8601_utc)``
            built by :func:`ensure_fresh` from the ProbeResult list. Hosts
            absent from the map are left untouched (their observation keys
            simply stay as-is from disk or absent).

    Returns:
        Total number of host entries mutated across all four bags. Used by
        the caller's ``logger.debug`` line so operators can eyeball how much
        of the fleet actually reported back.
    """
    stamped = 0

    def _apply(bag: Any) -> None:
        nonlocal stamped
        # Local closure so we do not duplicate the promotion+stamp logic for
        # each of the four bags. `stamped` is nonlocal so the total survives.
        if not isinstance(bag, list):
            return
        for entry in bag:
            if not isinstance(entry, dict):
                continue
            host = entry.get("host")
            if not isinstance(host, str):
                continue
            obs = observations.get(host)
            if obs is None:
                continue
            protocol, port, ts = obs
            # Always write all three observation keys together so a stale
            # value never survives next to a fresh one; matches contract
            # cenr_cache_schema_v3.md §"Observation triplet". When the host
            # was silent (no responding protocol), the whole triplet is None
            # so the "no observation" branch stays distinguishable on disk.
            entry["observed_protocol"] = protocol
            entry["observed_port"] = port
            entry["last_probed"] = ts if protocol is not None else None
            stamped += 1

    _apply(doc.get("proxy_hostnames"))
    _apply(doc.get("vpn_hostnames"))
    by_city = doc.get("by_city")
    if isinstance(by_city, dict):
        for city_slot in by_city.values():
            if not isinstance(city_slot, dict):
                continue
            _apply(city_slot.get("proxy_hostnames"))
            _apply(city_slot.get("vpn_hostnames"))
    return stamped


def _merge_observations_into_zcc(
    doc: dict[str, Any],
    observations: dict[str, tuple[str | None, int | None, str]],
) -> int:
    """Stamp per-host observations onto every ``roles[*].fqdns`` bag in ``doc``.

    Why:
        Mirror of :func:`_merge_observations_into_cenr` but for the client-
        connector probes file. Kept separate from the CENR walker because
        the outer shape differs (roles list/dict vs top-level bags); merging
        the two into one recursive walker would obscure both paths.

    Args:
        doc: Fresh ZCC probes document (already v3 after promotion). Mutated
            in place.
        observations: Same ``fqdn -> (protocol, port, iso8601_utc)`` map
            built by :func:`ensure_fresh`.

    Returns:
        Total number of FQDN entries mutated across all roles.
    """
    stamped = 0
    for role_body in _iter_zcc_role_bodies(doc):
        fqdns = role_body.get("fqdns")
        if not isinstance(fqdns, list):
            continue
        for entry in fqdns:
            if _stamp_zcc_entry(entry, observations):
                stamped += 1
    return stamped


def _iter_zcc_role_bodies(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the role-body dicts from a ZCC document regardless of container shape.

    Why:
        The ZCC catalogue is shape-tolerant on read: ``roles`` may be
        stored as a list of dicts (the shipped shape) or as a dict of
        role-name -> body (a hand-authored variant). Centralising the
        unwrap here lets ``_merge_observations_into_zcc`` and future
        callers walk role bodies without repeating the isinstance dance.

    Args:
        doc: Parsed ZCC probes document.

    Returns:
        A concrete list of role-body dicts. Non-dict entries and unknown
        container shapes yield an empty list rather than raising, so the
        caller can still return a zero-stamp count.
    """
    roles = doc.get("roles")
    if isinstance(roles, list):
        candidates: list[Any] = list(roles)
    elif isinstance(roles, dict):
        candidates = list(roles.values())
    else:
        candidates = []
    return [item for item in candidates if isinstance(item, dict)]


def _stamp_zcc_entry(
    entry: Any,
    observations: dict[str, tuple[str | None, int | None, str]],
) -> bool:
    """Stamp one ``fqdns[]`` entry with its matching observation, in place.

    Why:
        The inner per-entry logic (v3 dict guard + host lookup + triplet
        write with silent-host null semantics) is trivial on its own but
        pushed ``_merge_observations_into_zcc`` above the CC gate.
        Splitting it keeps the outer walker at the level of "roles ->
        fqdns" and this helper at the level of "one entry -> one
        observation".

    Args:
        entry: Candidate ``fqdns[]`` item. Only dict entries with a
            string ``host`` are eligible; every other shape is skipped.
        observations: The ``fqdn -> (protocol, port, iso8601_utc)`` map
            passed through from :func:`_merge_observations_into_zcc`.

    Returns:
        ``True`` if the entry was stamped (observation matched a probed
        host); ``False`` if it was skipped or had no observation.
    """
    if not isinstance(entry, dict):
        return False
    host = entry.get("host")
    if not isinstance(host, str):
        return False
    obs = observations.get(host)
    if obs is None:
        return False
    protocol, port, ts = obs
    entry["observed_protocol"] = protocol
    entry["observed_port"] = port
    # Match the CENR walker: silent hosts get a null triplet so the
    # on-disk shape between the two files stays symmetric.
    entry["last_probed"] = ts if protocol is not None else None
    return True


def is_stale(cenr: dict[str, Any]) -> bool:
    """Return ``True`` when the cached CENR document is older than the TTL.

    Why:
        The refresh decision must be robust to hand-edited or freshly-created
        cache files that may lack ``fetched_utc`` entirely or store it in an
        unexpected shape. Treating any parse failure as "stale" biases the
        system toward refreshing rather than silently trusting a broken
        timestamp -- worst case is one unnecessary fetch, which is cheap.

    Args:
        cenr: Parsed CENR document. Only the ``fetched_utc`` key is inspected.

    Returns:
        ``True`` if ``fetched_utc`` is missing, malformed, or older than
        :data:`_FRESHNESS_TTL`; ``False`` when it is present, parseable, and
        within the TTL window.
    """
    raw = cenr.get("fetched_utc")
    if not isinstance(raw, str) or not raw:
        return True
    # Accept both ``...Z`` and ``+00:00`` suffixes -- Python 3.11+ handles ``Z``
    # in fromisoformat natively, but be defensive for older writers.
    try:
        text = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
        fetched = datetime.fromisoformat(text)
    except ValueError:
        logger.warning("zscaler_catalogue: unparseable fetched_utc=%r; treating as stale", raw)
        return True
    if fetched.tzinfo is None:
        fetched = fetched.replace(tzinfo=UTC)
    age = datetime.now(UTC) - fetched
    return age >= _FRESHNESS_TTL


def fetch_cloud(cloud: str, *, timeout: float = _FETCH_TIMEOUT) -> dict[str, Any] | None:
    """Fetch and parse the CENR JSON document for a single Zscaler cloud.

    Why:
        Kept as a narrow helper so ``refresh_cenr`` can fan out across all
        seven clouds with a uniform failure model: a bad HTTP status, DNS
        failure, socket timeout, or malformed JSON all return ``None`` and
        emit a warning. Callers can then merge whatever subset succeeded
        without special-casing per-cloud errors.

    Args:
        cloud: One of the canonical Zscaler cloud slugs (for example ``zscaler.net``).
        timeout: Wall-clock timeout for the HTTPS GET in seconds.

    Returns:
        Parsed JSON document on success, or ``None`` when the fetch or parse
        fails for any reason.
    """
    url = _CENR_URL_TEMPLATE.format(cloud=cloud)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MistHelper-menu206/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 -- fixed HTTPS host  # nosec B310
            status = getattr(resp, "status", 200)
            if status != 200:
                logger.warning(
                    "zscaler_catalogue: %s returned HTTP %s; skipping cloud",
                    url,
                    status,
                )
                return None
            body = resp.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        logger.warning("zscaler_catalogue: fetch failed for %s: %s", url, exc)
        return None
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        logger.warning("zscaler_catalogue: JSON parse failed for %s: %s", url, exc)
        return None
    if not isinstance(parsed, dict):
        logger.warning(
            "zscaler_catalogue: %s returned non-object JSON (%s); skipping",
            url,
            type(parsed).__name__,
        )
        return None
    return parsed


def _strip_prefix(key: str, prefix: str) -> str:
    """Strip a ``"prefix : "`` label from a Zscaler CENR JSON key.

    Why:
        The CENR feed labels its continent/city keys as ``"continent : EMEA"``
        and ``"city : Amsterdam II"`` respectively. Downstream code and the
        hand-curated ``_CITY_META`` map want the bare tokens (``EMEA``,
        ``Amsterdam II``). Centralising the strip so the merger stays readable
        and both continent/city keys use one consistent normalisation.

    Args:
        key: Raw key from the CENR JSON (may or may not have the prefix).
        prefix: The label prefix to strip (for example ``"continent"`` or ``"city"``);
            the tool appends ``" : "`` internally.

    Returns:
        The tail after ``"<prefix> : "`` if present, otherwise the key
        unchanged.
    """
    marker = f"{prefix} : "
    if key.startswith(marker):
        return key[len(marker) :]
    return key


def _cloud_root_trees(cloud: str, doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the continent-tree dicts hanging off a per-cloud CENR doc.

    Why:
        Extracted from ``merge_clouds`` so the parent stays under the
        CI cyclomatic-complexity gate. The interesting tree normally
        hangs off a top-level key equal to the cloud slug (Zscaler's
        canonical shape); on unexpected shapes we walk every dict-valued
        top-level key so a partially-broken feed still contributes what
        it can. ``svpnIPs`` is excluded because it is a metadata list,
        not a continent tree.

    Args:
        cloud: Cloud slug (for example ``"zscloud"``).
        doc: Parsed CENR JSON dict for this cloud.

    Returns:
        A list (possibly empty) of continent-tree dicts to walk.
    """
    if isinstance(doc.get(cloud), dict):
        return [doc[cloud]]
    fallback: list[dict[str, Any]] = []
    for top_key, top_val in doc.items():
        if top_key == "svpnIPs":
            continue
        if isinstance(top_val, dict):
            fallback.append(top_val)
    return fallback


def _slot_host_field(entry: Any) -> str:
    """Return the ``host`` string from a v3 dict entry or a legacy flat string.

    Why:
        A city that appears in more than one cloud is revisited by
        ``merge_clouds``: the first pass writes v3 dicts into
        ``slot[*_hostnames]``, so the second pass sees ``list[dict]``.
        ``set(list[dict])`` blows up because dicts are unhashable, so we
        normalise every entry to a string here before dedup.

    Args:
        entry: Either a v3 host dict (``{"host": ...}``) or a legacy
            flat hostname string.

    Returns:
        The hostname string, or empty string when the entry is neither
        a dict-with-host nor a plain string.
    """
    if isinstance(entry, dict):
        h = entry.get("host")
        return h if isinstance(h, str) else ""
    return entry if isinstance(entry, str) else ""


def _seed_slot_host_sets(slot: dict[str, Any]) -> tuple[set[str], set[str]]:
    """Rehydrate proxy/vpn dedup sets from a slot's existing v3 host dicts.

    Why:
        Split out of ``_absorb_city_records`` so the parent stays under the
        CC gate. On the second cloud pass for a shared city the slot lists
        already hold v3 dicts; ``set(list[dict])`` would blow up because
        dicts are unhashable, so we normalise through ``_slot_host_field``
        first.

    Args:
        slot: The per-city slot dict; may hold legacy strings or v3 dicts.

    Returns:
        A ``(proxy_hosts, vpn_hosts)`` tuple of hostname sets, ready to
        receive new hosts by ``.add``.
    """
    slot_proxies: set[str] = {h for h in (_slot_host_field(e) for e in slot.get("proxy_hostnames", []) or []) if h}
    slot_vpns: set[str] = {h for h in (_slot_host_field(e) for e in slot.get("vpn_hostnames", []) or []) if h}
    return slot_proxies, slot_vpns


def _ingest_record(
    record: Any,
    proxies: set[str],
    vpns: set[str],
    slot_proxies: set[str],
    slot_vpns: set[str],
) -> None:
    """Fold one CENR record's ``hostname`` / ``vpn`` fields into the dedup sets.

    Why:
        Split out of ``_absorb_city_records`` so the parent stays under
        the CC gate. The four ``isinstance`` gates each add a branch, and
        moving them here keeps the parent at a simple ``for record in
        records`` loop.

    Args:
        record: Raw CENR record; skipped when not a dict.
        proxies: Global proxy-hostname dedup set; mutated in place.
        vpns: Global vpn-hostname dedup set; mutated in place.
        slot_proxies: Per-city proxy-hostname set; mutated in place.
        slot_vpns: Per-city vpn-hostname set; mutated in place.
    """
    if not isinstance(record, dict):
        return
    host = record.get("hostname")
    if isinstance(host, str) and host:
        proxies.add(host)
        slot_proxies.add(host)
    vpn = record.get("vpn")
    if isinstance(vpn, str) and vpn:
        vpns.add(vpn)
        slot_vpns.add(vpn)


def _finalize_slot(
    slot: dict[str, Any],
    slot_proxies: set[str],
    slot_vpns: set[str],
    cloud: str,
) -> None:
    """Write v3 host dicts and ``seen_in_clouds`` back onto a per-city slot.

    Why:
        Emit v3 dicts (not flat strings) so the on-disk shape stays
        consistent with ``schema_version=3``; writing flat strings under
        a v3 stamp previously broke the loader's idempotency
        short-circuit. ``seen_in_clouds`` lets operators auditing the
        merged file trace an entry back to a specific feed.

    Args:
        slot: The per-city slot dict, mutated in place.
        slot_proxies: Final proxy-hostname set for this city.
        slot_vpns: Final vpn-hostname set for this city.
        cloud: Cloud slug that supplied this pass's records.
    """
    slot["proxy_hostnames"] = [_promote_host_entry(h) for h in sorted(slot_proxies)]
    slot["vpn_hostnames"] = [_promote_host_entry(h) for h in sorted(slot_vpns)]
    seen_clouds: set[str] = set(slot.get("seen_in_clouds", []) or [])
    seen_clouds.add(cloud)
    slot["seen_in_clouds"] = sorted(seen_clouds)


def _absorb_city_records(
    city: str,
    records: list[Any],
    cloud: str,
    proxies: set[str],
    vpns: set[str],
    by_city: dict[str, dict[str, Any]],
) -> None:
    """Fold ``records`` into the per-city slot and the global proxy/vpn sets.

    Why:
        Split out of ``merge_clouds`` so the parent function stays under
        the CC gate. Delegates the three sub-steps (rehydrate slot sets,
        ingest each record, emit v3 dicts + ``seen_in_clouds``) to keep
        this function itself under the gate as well.

    Args:
        city: Prefix-stripped city name (for example ``"Amsterdam"``).
        records: Raw record list from the city bucket.
        cloud: Cloud slug that supplied these records (recorded under
            ``seen_in_clouds`` on the slot).
        proxies: Global proxy-hostname dedup set; mutated in place.
        vpns: Global vpn-hostname dedup set; mutated in place.
        by_city: Merged-by-city map; the target slot is mutated in place.
    """
    slot = by_city.setdefault(city, {"proxy_hostnames": [], "vpn_hostnames": []})
    slot_proxies, slot_vpns = _seed_slot_host_sets(slot)
    for record in records:
        _ingest_record(record, proxies, vpns, slot_proxies, slot_vpns)
    _finalize_slot(slot, slot_proxies, slot_vpns, cloud)


def _walk_city_map(
    city_map: dict[str, Any],
    cloud: str,
    proxies: set[str],
    vpns: set[str],
    by_city: dict[str, dict[str, Any]],
) -> None:
    """Fold every ``city : X`` bucket in a continent tree into the merged view.

    Why:
        Split out of ``merge_clouds`` so the parent stays under the CC
        gate. The ``_strip_prefix`` call drops the ``"city : "``
        namespace prefix so ``by_city`` keys match the plain city names
        used by :func:`scripts.build_zen_city_metadata.attach_city_metadata`.

    Args:
        city_map: One continent's dict of city buckets.
        cloud: Cloud slug supplying these buckets.
        proxies: Global proxy-hostname dedup set; mutated in place.
        vpns: Global vpn-hostname dedup set; mutated in place.
        by_city: Merged-by-city map; mutated in place.
    """
    for city_key, records in city_map.items():
        if not isinstance(records, list):
            continue
        city = _strip_prefix(city_key, "city")
        if not city:
            continue
        _absorb_city_records(city, records, cloud, proxies, vpns, by_city)


def merge_clouds(per_cloud: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Flat-merge per-cloud CENR documents into a single cache-file dict.

    Why:
        The real ``config.zscaler.com/api/<cloud>/cenr/json`` payload is nested
        as ``{<cloud>: {"continent : X": {"city : Y": [record, ...]}}, svpnIPs: [...]}``.
        Each record carries ``hostname`` (proxy FQDN) and ``vpn`` (VPN FQDN),
        both often empty. Downstream consumers in
        :mod:`src.org.org_synthetic_probes_manager` expect a single flat
        ``proxy_hostnames`` / ``vpn_hostnames`` / ``by_city`` surface, and
        :func:`scripts.build_zen_city_metadata.attach_city_metadata` looks up
        bare city names (no ``"city : "`` prefix) against a hand-curated
        ``_CITY_META`` table. Merging here (walk + dedup + prefix-strip + sort)
        translates the raw feed into the shape both callers expect while
        expanding coverage to every cloud.

    Args:
        per_cloud: Mapping of cloud slug -> parsed CENR JSON dict. The dict's
            top-level normally contains one key equal to the cloud slug
            (holding the continent tree) plus a ``svpnIPs`` list; both are
            optional. Clouds that fetched successfully but returned no
            hostnames still contribute their URL to ``source_urls``.

    Returns:
        Merged CENR document with keys ``schema_version``, ``fetched_utc``,
        ``source_urls``, ``proxy_hostnames``, ``vpn_hostnames``, ``by_city``,
        ``description``, and ``probe_default``. Ready to hand to
        :func:`scripts.build_zen_city_metadata.attach_city_metadata`.
    """
    proxies: set[str] = set()
    vpns: set[str] = set()
    by_city: dict[str, dict[str, Any]] = {}

    for cloud, doc in per_cloud.items():
        if not isinstance(doc, dict):
            continue
        for continent_tree in _cloud_root_trees(cloud, doc):
            for continent_key, city_map in continent_tree.items():
                if not isinstance(city_map, dict):
                    continue
                _ = _strip_prefix(continent_key, "continent")  # future: expose continent
                _walk_city_map(city_map, cloud, proxies, vpns, by_city)

    source_urls = sorted(_CENR_URL_TEMPLATE.format(cloud=c) for c in per_cloud)
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "schema_version": _SCHEMA_VERSION,
        "fetched_utc": now,
        "source_urls": source_urls,
        "description": (
            "Merged Zscaler Cloud Enforcement Node Ranges (CENR) hostnames "
            "across all Zscaler public clouds. Auto-refreshed by "
            "src/utils/zscaler_catalogue.py every 8 hours."
        ),
        "probe_default": {
            "protocol": "https",
            "port": 443,
            "ignore_cert": False,
            "reason": (
                "ZEN edges terminate TLS on 443; ignore_cert is left False so "
                "certificate rotations at Zscaler surface as probe failures."
            ),
        },
        "proxy_hostnames": [_promote_host_entry(h) for h in sorted(proxies)],
        "vpn_hostnames": [_promote_host_entry(h) for h in sorted(vpns)],
        "by_city": {city: by_city[city] for city in sorted(by_city)},
    }


def _atomic_write_json(path: Path, doc: dict[str, Any]) -> None:
    """Write ``doc`` to ``path`` atomically via temp-file + rename.

    Why:
        The CENR file is read concurrently by menu 206 and the background
        refresh; a partial write during a crash would poison the next menu
        invocation. ``os.replace`` on the same filesystem is atomic on both
        POSIX and Windows, so a same-directory temp file guarantees readers
        either see the old or the new document, never a half-written one.

    Args:
        path: Destination file path.
        doc: JSON-serialisable dict to write.

    Raises:
        Exception: Re-raises any exception encountered while writing or
            replacing the destination file, after best-effort cleanup of the
            temp file. Callers upstream (``refresh_cenr``) convert this into a
            warning so the auto-refresh path stays fail-open.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(doc, handle, indent=2)
            handle.write("\n")
        os.replace(tmp_name, path)
    except Exception:
        # Best-effort cleanup on failure so we do not leak temp files.
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _load_stale_cenr_cache(cenr_path: Path, warnings: list[str]) -> dict[str, Any]:
    """Return the on-disk stale CENR dict when every cloud fetch fails.

    Why:
        Extracted from :func:`refresh_cenr` so the total-failure fallback
        does not add branches to the outer function (Radon CC>10 gate). Fails
        open: a missing file, an unreadable file, or non-dict JSON all return
        an empty dict plus a captured warning so menu 206 keeps running.

    Args:
        cenr_path: Path to ``data/zscaler_cenr_hostnames.json``. May not
            exist; a missing file is a packaging error, not a crash.
        warnings: Mutable warning list from the caller. Appended in place
            with any read or decode failure so the caller can log them.

    Returns:
        The stale-but-valid CENR dict, or an empty dict when the file is
        missing, unreadable, or does not decode to a dict.
    """
    if not cenr_path.is_file():
        return {}
    try:
        stale = json.loads(cenr_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(f"stale cache read failed: {exc}")
        return {}
    return stale if isinstance(stale, dict) else {}


def refresh_cenr(cenr_path: Path) -> tuple[dict[str, Any], list[str]]:
    """Fetch every Zscaler cloud, merge, decorate, and rewrite ``cenr_path``.

    Why:
        Single entry point for the refresh side-effect. Consolidates the
        fan-out fetch, the merge, the city-metadata decoration, and the
        atomic write so the freshness gate in :func:`ensure_fresh` stays
        tiny. Fails open: if every cloud fetch fails we leave the existing
        cache untouched and return the on-disk dict + a warning, so menu 206
        can keep running against stale-but-valid data during a network
        outage.

    Args:
        cenr_path: Path to ``data/zscaler_cenr_hostnames.json``. Must exist
            already for the fail-open fallback to work; a missing file is a
            packaging error and surfaces as a warning with an empty dict.

    Returns:
        Tuple of ``(new_cenr, warnings)``. ``new_cenr`` is the freshly
        merged and rewritten dict on success, or the untouched stale dict on
        total-failure. ``warnings`` collects non-fatal issues (per-cloud
        fetch failures, unmapped cities from the metadata attach step, and so on)
        for the caller to log.
    """
    warnings: list[str] = []
    per_cloud: dict[str, dict[str, Any]] = {}
    for cloud in _CLOUDS:
        doc = fetch_cloud(cloud)
        if doc is None:
            warnings.append(f"cloud fetch failed: {cloud}")
            continue
        per_cloud[cloud] = doc

    if not per_cloud:
        warnings.append("all Zscaler cloud fetches failed; keeping stale cache at " f"{cenr_path}")
        logger.warning(warnings[-1])
        return _load_stale_cenr_cache(cenr_path, warnings), warnings

    merged = merge_clouds(per_cloud)
    merged, city_warnings = attach_city_metadata(merged)
    warnings.extend(city_warnings)

    try:
        _atomic_write_json(cenr_path, merged)
    except OSError as exc:
        warnings.append(f"CENR write failed for {cenr_path}: {exc}")
        logger.warning(warnings[-1])
    logger.info(
        "zscaler_catalogue: refreshed CENR from %d/%d clouds " "(proxies=%d vpns=%d cities=%d)",
        len(per_cloud),
        len(_CLOUDS),
        len(merged.get("proxy_hostnames", []) or []),
        len(merged.get("vpn_hostnames", []) or []),
        len(merged.get("by_city", {}) or {}),
    )
    return merged, warnings


def _run_probe_validation(
    cenr_path: Path,
    fresh: dict[str, Any],
) -> tuple[dict[str, Any], list[ProbeResult]]:
    """Best-effort probe run; returns ``(probes_v3_dict, results)``.

    Why:
        Extracted from ``ensure_fresh`` so the caller stays under Radon
        CC=10. Validation is best-effort by contract (menu 206 already
        writes probes that self-report failures) so any exception is
        swallowed and returned as an empty ``results`` list rather than
        propagated. The probes dict is still returned so ``ensure_fresh``
        can subsequently stamp observations into it.

    Args:
        cenr_path: Path to the CENR cache; probes cache is resolved as a
            sibling ``zscaler_client_connector_probes.json``.
        fresh: Freshly-refreshed CENR document.

    Returns:
        ``(probes, results)``. ``probes`` is the v3-promoted ZCC roles
        dict (empty when the file is missing). ``results`` is the probe
        result list (empty on any exception path).
    """
    probes: dict[str, Any] = {}
    probes_path = cenr_path.parent / "zscaler_client_connector_probes.json"
    results: list[ProbeResult] = []
    try:
        if probes_path.is_file():
            probes = json.loads(probes_path.read_text(encoding="utf-8"))
        # Promote the ZCC roles cache so run_full_validation and every
        # downstream reader work off the shared v3 dict shape.
        probes = promote_cache_document(probes, kind="zcc")  # v2 -> v3 loader adapter
        results = run_full_validation(
            probes,
            fresh,
            timeout=DEFAULT_TIMEOUT,
            workers=DEFAULT_WORKERS,
        )
        if results and not any(r.responding_protocols for r in results):
            logger.warning(
                "zscaler_catalogue: full-fleet validation showed zero responding "
                "endpoints (n=%d); refresh kept anyway",
                len(results),
            )
    except Exception as exc:  # noqa: BLE001 -- validation is best-effort
        logger.warning("zscaler_catalogue: validation crashed: %s", exc)
    return probes, results


def _build_observations_index(
    results: list[ProbeResult],
) -> dict[str, tuple[str | None, int | None, str]]:
    """Fold ``results`` into an FQDN -> (protocol, port, iso8601_utc) index.

    Why:
        Extracted from ``ensure_fresh`` so both CENR and ZCC observation
        writers can look up in O(1). Timestamp is a single ``now`` per
        refresh cycle so every observation from the same probe pass
        reports the same ``last_probed`` value (deterministic
        snapshotting -- INV-1 byte-stability).

    Args:
        results: Probe results from ``run_full_validation``.

    Returns:
        Mapping FQDN -> (protocol, port, now_iso). Empty when no result
        carried a usable FQDN.
    """
    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    observations: dict[str, tuple[str | None, int | None, str]] = {}
    for pr in results:
        # `getattr` fallback keeps this loop tolerant of duck-typed stubs
        # used in older tests that predate the full ProbeResult shape.
        fqdn = getattr(pr, "fqdn", None)
        if not isinstance(fqdn, str) or not fqdn:
            continue
        protocol, port = _pick_observation_from_probe_result(pr)
        observations[fqdn] = (protocol, port, now_iso)
    return observations


def _persist_observations(
    cenr_path: Path,
    fresh: dict[str, Any],
    probes: dict[str, Any],
    results: list[ProbeResult],
) -> None:
    """Stamp probe observations onto CENR + ZCC caches on disk.

    Why:
        Extracted from ``ensure_fresh`` per contract
        ``cenr_cache_schema_v3.md`` §"Write Path". Both writes must force
        ``schema_version`` to the current constant so the invariant
        "on disk == _SCHEMA_VERSION" holds. Failures on either write are
        logged and swallowed -- refresh already succeeded and the caller
        returns the in-memory ``fresh`` dict regardless.

    Args:
        cenr_path: Path to the CENR cache.
        fresh: Freshly-refreshed CENR document (mutated in place with the
            stamped observations and current schema version).
        probes: v3 ZCC roles dict (mutated in place with observations and
            schema version).
        results: Probe results from ``run_full_validation``. When empty
            this function is a no-op.
    """
    if not results:
        return
    observations = _build_observations_index(results)
    logger.info(
        "zscaler_catalogue: merging %d probe observations into v3 caches",
        len(observations),
    )
    # Stamp CENR (all four bags) then ZCC (roles[*].fqdns). Force
    # schema_version to the current constant on both docs so the write
    # invariant "on disk == _SCHEMA_VERSION" always holds.
    cenr_stamped = _merge_observations_into_cenr(fresh, observations)
    fresh["schema_version"] = _SCHEMA_VERSION
    try:
        _atomic_write_json(cenr_path, fresh)
    except OSError as exc:
        logger.warning("zscaler_catalogue: CENR observation rewrite failed: %s", exc)
    probes_path = cenr_path.parent / "zscaler_client_connector_probes.json"
    zcc_stamped = _merge_observations_into_zcc(probes, observations)
    probes["schema_version"] = _SCHEMA_VERSION
    try:
        _atomic_write_json(probes_path, probes)
    except OSError as exc:
        logger.warning("zscaler_catalogue: ZCC observation rewrite failed: %s", exc)
    logger.debug(
        "zscaler_catalogue: observation merge complete (cenr=%d, zcc=%d stamped)",
        cenr_stamped,
        zcc_stamped,
    )


def ensure_fresh(cenr_path: Path, cenr: dict[str, Any]) -> dict[str, Any]:
    """Return an up-to-date CENR dict, refreshing + validating when stale.

    Why:
        Choke point called from
        :func:`src.org.org_synthetic_probes_manager._load_probe_sources` on
        every menu 206 entry. Combining the freshness check, the multi-cloud
        refresh, and the full-fleet port/protocol validation in one call
        keeps the wire-in at the call site to a single line, so no other
        code path can accidentally bypass the refresh gate.

        Validation runs full-fleet (~1000 endpoints) rather than sampled
        because it only fires on refresh (≤3 times/day). Validation
        failures are logged but never block the return -- menu 206 already
        writes probes into Mist that self-report failures, so double-gating
        here would just add fragility.

    Args:
        cenr_path: Path to ``data/zscaler_cenr_hostnames.json``.
        cenr: Currently-loaded CENR dict from disk. Returned unchanged when
            it is still fresh.

    Returns:
        The fresh dict (either the passthrough when in-TTL, or the refreshed
        merged dict when stale). Never raises; always returns *some* dict so
        the caller can proceed.
    """
    # Promote legacy v2 CENR flat-string bags into v3 dict entries so every
    # downstream consumer sees the same shape regardless of on-disk vintage.
    # Idempotent for v3+ documents, and emits at most one INFO line.
    cenr = promote_cache_document(cenr, kind="cenr")  # v2 -> v3 loader adapter
    if not is_stale(cenr):  # freshness gate stays the sole trigger for refresh
        return cenr

    logger.info(
        "zscaler_catalogue: CENR cache is stale (>%s old); refreshing from %d clouds",
        _FRESHNESS_TTL,
        len(_CLOUDS),
    )
    fresh, warnings = refresh_cenr(cenr_path)
    for warning in warnings:
        logger.warning("zscaler_catalogue: %s", warning)

    if not fresh:
        # Total-failure path returned empty dict; fall back to whatever the
        # caller already loaded so downstream code keeps a usable shape.
        logger.warning("zscaler_catalogue: refresh returned empty document; using in-memory copy")
        return cenr

    # Best-effort probe run; validation failures do not block the return.
    probes, results = _run_probe_validation(cenr_path, fresh)

    # T028/T029: write persisted observations back onto both cache files so a
    # later menu 206 invocation can dispatch on the last observed protocol
    # without re-probing (contract cenr_cache_schema_v3.md §"Write Path").
    _persist_observations(cenr_path, fresh, probes, results)

    return fresh

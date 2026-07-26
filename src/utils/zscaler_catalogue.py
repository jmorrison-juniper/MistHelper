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

_SCHEMA_VERSION = 2


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
        cloud: One of the canonical Zscaler cloud slugs (e.g. ``zscaler.net``).
        timeout: Wall-clock timeout for the HTTPS GET in seconds.

    Returns:
        Parsed JSON document on success, or ``None`` when the fetch or parse
        fails for any reason.
    """
    url = _CENR_URL_TEMPLATE.format(cloud=cloud)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MistHelper-menu206/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 -- fixed HTTPS host
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
        prefix: The label prefix to strip (e.g. ``"continent"`` or ``"city"``);
            the tool appends ``" : "`` internally.

    Returns:
        The tail after ``"<prefix> : "`` if present, otherwise the key
        unchanged.
    """
    marker = f"{prefix} : "
    if key.startswith(marker):
        return key[len(marker) :]
    return key


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
        # The interesting tree hangs off a key equal to the cloud slug; any
        # other top-level key (e.g. ``svpnIPs``) is metadata we ignore. Fall
        # back to walking every dict-valued top-level key so an unexpected
        # cloud response still contributes what it can.
        cloud_roots: list[dict[str, Any]] = []
        if isinstance(doc.get(cloud), dict):
            cloud_roots.append(doc[cloud])
        else:
            for top_key, top_val in doc.items():
                if top_key == "svpnIPs":
                    continue
                if isinstance(top_val, dict):
                    cloud_roots.append(top_val)

        for continent_tree in cloud_roots:
            for continent_key, city_map in continent_tree.items():
                if not isinstance(city_map, dict):
                    continue
                _ = _strip_prefix(continent_key, "continent")  # future: expose continent
                for city_key, records in city_map.items():
                    if not isinstance(records, list):
                        continue
                    city = _strip_prefix(city_key, "city")
                    if not city:
                        continue
                    slot = by_city.setdefault(city, {"proxy_hostnames": [], "vpn_hostnames": []})
                    slot_proxies: set[str] = set(slot.get("proxy_hostnames", []) or [])
                    slot_vpns: set[str] = set(slot.get("vpn_hostnames", []) or [])
                    for record in records:
                        if not isinstance(record, dict):
                            continue
                        host = record.get("hostname")
                        if isinstance(host, str) and host:
                            proxies.add(host)
                            slot_proxies.add(host)
                        vpn = record.get("vpn")
                        if isinstance(vpn, str) and vpn:
                            vpns.add(vpn)
                            slot_vpns.add(vpn)
                    slot["proxy_hostnames"] = sorted(slot_proxies)
                    slot["vpn_hostnames"] = sorted(slot_vpns)
                    # Note the cloud each city was seen in so operators
                    # auditing the merged file can trace an entry back to a
                    # specific feed.
                    seen_clouds: set[str] = set(slot.get("seen_in_clouds", []) or [])
                    seen_clouds.add(cloud)
                    slot["seen_in_clouds"] = sorted(seen_clouds)

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
        "proxy_hostnames": sorted(proxies),
        "vpn_hostnames": sorted(vpns),
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
        # Best-effort cleanup on failure so we don't leak temp files.
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


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
        fetch failures, unmapped cities from the metadata attach step, etc.)
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
        # Total failure: keep whatever is on disk (or an empty dict if the
        # file is missing) so callers can degrade gracefully.
        warnings.append("all Zscaler cloud fetches failed; keeping stale cache at " f"{cenr_path}")
        logger.warning(warnings[-1])
        if cenr_path.is_file():
            try:
                stale = json.loads(cenr_path.read_text(encoding="utf-8"))
                if isinstance(stale, dict):
                    return stale, warnings
            except (OSError, json.JSONDecodeError) as exc:
                warnings.append(f"stale cache read failed: {exc}")
        return {}, warnings

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
    if not is_stale(cenr):
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
    try:
        # Load probes catalogue relative to the CENR path so we don't
        # hard-code a repo layout inside this helper. The probes file sits
        # in the same data/ directory.
        probes_path = cenr_path.parent / "zscaler_client_connector_probes.json"
        if probes_path.is_file():
            probes = json.loads(probes_path.read_text(encoding="utf-8"))
        else:
            probes = {}
        results: list[ProbeResult] = run_full_validation(
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

    return fresh

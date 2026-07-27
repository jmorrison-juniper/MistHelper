"""Extend ``data/zscaler_cenr_hostnames.json`` with per-city geo metadata.

Why:
    The synthetic-probe scheduler needs to pick the ZEN cities nearest to
    each Mist site. The upstream Zscaler CENR feed only gives city display
    names and proxy hostnames, so we hand-curate a ``city_metadata`` map
    (country ISO2, continent bucket, lat/lon) once and store it alongside
    the fetched hostnames. Run this script if the upstream feed adds a new
    city -- it will refuse to overwrite existing metadata and will emit a
    diff summary so unknown cities surface immediately.

    The core attach-metadata logic is also imported by
    ``src/utils/zscaler_catalogue.py`` so the auto-refresh path can
    re-decorate a freshly-fetched CENR file without shelling out.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# City display name -> (country ISO2, continent bucket, lat, lon).
# Continent buckets: NA, SA, EU, AS, AF, OC. Middle East folded into AS
# because Zscaler's routing/regional shape treats those pops that way.
_CITY_META: dict[str, tuple[str, str, float, float]] = {
    "Abu Dhabi II": ("AE", "AS", 24.4539, 54.3773),
    "Amsterdam II": ("NL", "EU", 52.3676, 4.9041),
    "Amsterdam III": ("NL", "EU", 52.3676, 4.9041),
    "Atlanta II": ("US", "NA", 33.7490, -84.3880),
    "Atlanta III": ("US", "NA", 33.7490, -84.3880),
    "Auckland II": ("NZ", "OC", -36.8485, 174.7633),
    "Beijing": ("CN", "AS", 39.9042, 116.4074),
    "Beijing III": ("CN", "AS", 39.9042, 116.4074),
    "Bogota I": ("CO", "SA", 4.7110, -74.0721),
    "Bogota II": ("CO", "SA", 4.7110, -74.0721),
    "Boston I": ("US", "NA", 42.3601, -71.0589),
    "Brussels II": ("BE", "EU", 50.8503, 4.3517),
    "Buenos Aires I": ("AR", "SA", -34.6037, -58.3816),
    "Buenos Aires II": ("AR", "SA", -34.6037, -58.3816),
    "Canberra I": ("AU", "OC", -35.2809, 149.1300),
    "Capetown IV": ("ZA", "AF", -33.9249, 18.4241),
    "Chennai": ("IN", "AS", 13.0827, 80.2707),
    "Chennai II": ("IN", "AS", 13.0827, 80.2707),
    "Chennai III": ("IN", "AS", 13.0827, 80.2707),
    "Chicago": ("US", "NA", 41.8781, -87.6298),
    "Chicago II": ("US", "NA", 41.8781, -87.6298),
    "Copenhagen II": ("DK", "EU", 55.6761, 12.5683),
    "Dallas I": ("US", "NA", 32.7767, -96.7970),
    "Dallas II": ("US", "NA", 32.7767, -96.7970),
    "Denver III": ("US", "NA", 39.7392, -104.9903),
    "Dubai I": ("AE", "AS", 25.2048, 55.2708),
    "Dusseldorf I": ("DE", "EU", 51.2277, 6.7735),
    "Frankfurt IV": ("DE", "EU", 50.1109, 8.6821),
    "Frankfurt VI": ("DE", "EU", 50.1109, 8.6821),
    "Helsinki I": ("FI", "EU", 60.1699, 24.9384),
    "Hong Kong III": ("HK", "AS", 22.3193, 114.1694),
    "Hong Kong IV": ("HK", "AS", 22.3193, 114.1694),
    "Honolulu I": ("US", "NA", 21.3099, -157.8581),
    "Hyderabad I": ("IN", "AS", 17.3850, 78.4867),
    "Jakarta I": ("ID", "AS", -6.2088, 106.8456),
    "Johannesburg III": ("ZA", "AF", -26.2041, 28.0473),
    "Kingdom of Saudi Arabia I": ("SA", "AS", 24.7136, 46.6753),
    "Kolkata I": ("IN", "AS", 22.5726, 88.3639),
    "Kuala Lumpur I": ("MY", "AS", 3.1390, 101.6869),
    "Kuala Lumpur II": ("MY", "AS", 3.1390, 101.6869),
    "Lagos II": ("NG", "AF", 6.5244, 3.3792),
    "Lagos III": ("NG", "AF", 6.5244, 3.3792),
    "Lisbon I": ("PT", "EU", 38.7223, -9.1393),
    "London III": ("GB", "EU", 51.5074, -0.1278),
    "London V": ("GB", "EU", 51.5074, -0.1278),
    "Los Angeles": ("US", "NA", 34.0522, -118.2437),
    "Los Angeles II": ("US", "NA", 34.0522, -118.2437),
    "Madrid III": ("ES", "EU", 40.4168, -3.7038),
    "Madrid IV": ("ES", "EU", 40.4168, -3.7038),
    "Manchester I": ("GB", "EU", 53.4808, -2.2426),
    "Manchester II": ("GB", "EU", 53.4808, -2.2426),
    "Marseille I": ("FR", "EU", 43.2965, 5.3698),
    "Melbourne II": ("AU", "OC", -37.8136, 144.9631),
    "Mexico City I": ("MX", "NA", 19.4326, -99.1332),
    "Mexico City II": ("MX", "NA", 19.4326, -99.1332),
    "Miami III": ("US", "NA", 25.7617, -80.1918),
    "Miami IV": ("US", "NA", 25.7617, -80.1918),
    "Milan III": ("IT", "EU", 45.4642, 9.1900),
    "Milan IV": ("IT", "EU", 45.4642, 9.1900),
    "Montreal I": ("CA", "NA", 45.5017, -73.5673),
    "Mumbai IV": ("IN", "AS", 19.0760, 72.8777),
    "Mumbai VI": ("IN", "AS", 19.0760, 72.8777),
    "Mumbai VII": ("IN", "AS", 19.0760, 72.8777),
    "Munich I": ("DE", "EU", 48.1351, 11.5820),
    "New Delhi I": ("IN", "AS", 28.6139, 77.2090),
    "New York III": ("US", "NA", 40.7128, -74.0060),
    "New York IV": ("US", "NA", 40.7128, -74.0060),
    "Nuevo Laredo I": ("MX", "NA", 27.4767, -99.5164),
    "Osaka I": ("JP", "AS", 34.6937, 135.5023),
    "Oslo III": ("NO", "EU", 59.9139, 10.7522),
    "Paris II": ("FR", "EU", 48.8566, 2.3522),
    "Paris IV": ("FR", "EU", 48.8566, 2.3522),
    "Perth I": ("AU", "OC", -31.9505, 115.8605),
    "Rio de Janeiro I": ("BR", "SA", -22.9068, -43.1729),
    "Rouen I": ("FR", "EU", 49.4432, 1.0993),
    "San Francisco IV": ("US", "NA", 37.7749, -122.4194),
    "Santiago I": ("CL", "SA", -33.4489, -70.6693),
    "Santiago II": ("CL", "SA", -33.4489, -70.6693),
    "Sao Paulo": ("BR", "SA", -23.5505, -46.6333),
    "Sao Paulo II": ("BR", "SA", -23.5505, -46.6333),
    "Sao Paulo IV": ("BR", "SA", -23.5505, -46.6333),
    "Seattle": ("US", "NA", 47.6062, -122.3321),
    "Seoul I": ("KR", "AS", 37.5665, 126.9780),
    "Shanghai": ("CN", "AS", 31.2304, 121.4737),
    "Shanghai II": ("CN", "AS", 31.2304, 121.4737),
    "Singapore IV": ("SG", "AS", 1.3521, 103.8198),
    "Singapore V": ("SG", "AS", 1.3521, 103.8198),
    "Stockholm III": ("SE", "EU", 59.3293, 18.0686),
    "Sydney III": ("AU", "OC", -33.8688, 151.2093),
    "Sydney V": ("AU", "OC", -33.8688, 151.2093),
    "Taipei": ("TW", "AS", 25.0330, 121.5654),
    "Tel Aviv II": ("IL", "AS", 32.0853, 34.7818),
    "Tianjin": ("CN", "AS", 39.3434, 117.3616),
    "Tokyo IV": ("JP", "AS", 35.6762, 139.6503),
    "Tokyo V": ("JP", "AS", 35.6762, 139.6503),
    "Tokyo VI": ("JP", "AS", 35.6762, 139.6503),
    "Toronto III": ("CA", "NA", 43.6532, -79.3832),
    "Vancouver I": ("CA", "NA", 49.2827, -123.1207),
    "Vienna I": ("AT", "EU", 48.2082, 16.3738),
    "Warsaw II": ("PL", "EU", 52.2297, 21.0122),
    "Washington DC": ("US", "NA", 38.9072, -77.0369),
    "Washington DC IV": ("US", "NA", 38.9072, -77.0369),
    "Zurich": ("CH", "EU", 47.3769, 8.5417),
    "Zurich I": ("CH", "EU", 47.3769, 8.5417),
}


_CITY_METADATA_NOTES = (
    "country_code is ISO 3166-1 alpha-2. continent is one of "
    "NA/SA/EU/AS/AF/OC (Middle East folded into AS). lat/lon are "
    "the city centre in decimal degrees. probe_hostnames is the "
    "list of representative hostnames for this city -- first entry "
    "of by_city[city].proxy_hostnames (ZIA HTTPS proxy) followed by "
    "first entry of by_city[city].vpn_hostnames (IPsec/GRE tunnel "
    "initiator). Both are pinned as site-scope critical so proxy "
    "and VPN paths are monitored independently -- they share the "
    "same PoP but different service planes. Legacy probe_hostname "
    "(scalar) is kept for readers that predate the list form."
)


def attach_city_metadata(
    data: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Attach ``city_metadata`` in-place to a CENR ``data`` dict and return warnings.

    Why:
        Split out from ``main()`` so the auto-refresh path in
        ``src/utils/zscaler_catalogue.py`` can re-decorate a freshly
        fetched CENR dict without shelling out. The library variant
        never raises on unmapped cities -- it returns them as warnings so
        the auto-refresh never bricks when Zscaler adds a new pop. The
        strict CLI wrapper in ``main()`` still raises so hand-runs
        surface unmapped cities immediately.

    Args:
        data: Parsed CENR document. Must contain a ``by_city`` mapping;
            missing or empty is treated as no cities and returns an
            empty ``city_metadata`` map.

    Returns:
        Tuple of ``(mutated_data, warnings)``. ``mutated_data`` is the
        same object as *data* with ``city_metadata`` and
        ``city_metadata_notes`` populated. ``warnings`` is a list of
        human-readable strings describing unmapped or stale cities;
        empty when the feed is fully covered by ``_CITY_META``.
    """
    warnings: list[str] = []
    by_city_raw = data.get("by_city", {}) or {}
    if not isinstance(by_city_raw, dict):
        warnings.append(f"by_city has unexpected type {type(by_city_raw).__name__}; " "treating as empty")
        by_city: dict[str, dict[str, object]] = {}
    else:
        by_city = by_city_raw

    live_cities = set(by_city.keys())
    known_cities = set(_CITY_META.keys())
    missing = sorted(live_cities - known_cities)
    stale = sorted(known_cities - live_cities)
    if missing:
        warnings.append(f"Unmapped cities in feed (add to _CITY_META): {missing}")
    if stale:
        warnings.append(f"{len(stale)} mapped cities no longer in feed: {stale}")

    city_metadata: dict[str, dict[str, float | str | list[str]]] = {}
    for city in sorted(live_cities):
        if city not in _CITY_META:
            # Non-fatal in library form; the SystemExit is only in main().
            continue
        country, continent, lat, lon = _CITY_META[city]
        proxy_hostnames_raw = by_city[city].get("proxy_hostnames", []) or []
        proxy_hostnames = list(proxy_hostnames_raw) if isinstance(proxy_hostnames_raw, list) else []
        vpn_hostnames_raw = by_city[city].get("vpn_hostnames", []) or []
        vpn_hostnames = list(vpn_hostnames_raw) if isinstance(vpn_hostnames_raw, list) else []

        def _pick_host(entry: object) -> str:
            """Return the bare FQDN whether the bag entry is a legacy string or a v3 dict.

            Why:
                The upstream CENR merger emits ``list[dict]`` under
                schema_version=3 (per contract cenr_cache_schema_v3.md), but
                hand-authored or legacy caches may still contain flat strings.
                A raw ``str(entry)`` on a dict yields ``"{'host': 'foo.com'}"``
                which then gets stamped as a probe target -- ugly at best,
                and it would break the synthetic-test URL builder in menu 206.
            """
            if isinstance(entry, dict):
                host = entry.get("host")
                return host if isinstance(host, str) else ""
            return str(entry)

        # First proxy + first vpn -- proxy and vpn ride the same PoP but are
        # distinct service planes (ZIA HTTPS proxy vs IPsec/GRE tunnel init),
        # so we pin both as site-scope critical to catch either service failing
        # independently.
        probe_hostnames: list[str] = []
        if proxy_hostnames:
            picked = _pick_host(proxy_hostnames[0])
            if picked:
                probe_hostnames.append(picked)
        if vpn_hostnames:
            picked = _pick_host(vpn_hostnames[0])
            if picked:
                probe_hostnames.append(picked)
        entry: dict[str, float | str | list[str]] = {
            "country_code": country,
            "continent": continent,
            "lat": lat,
            "lon": lon,
        }
        if probe_hostnames:
            entry["probe_hostnames"] = probe_hostnames
            # Retain scalar for back-compat with any reader that predates
            # the list form. Always mirrors probe_hostnames[0] (the proxy).
            entry["probe_hostname"] = probe_hostnames[0]
        city_metadata[city] = entry

    data["city_metadata"] = city_metadata
    data["city_metadata_notes"] = _CITY_METADATA_NOTES
    return data, warnings


def main() -> None:
    """Extend the CENR file in place with ``city_metadata``.

    Why:
        Idempotent -- safe to re-run after upstream re-fetches. Fails loud
        if the fetched feed added a city we haven't hand-mapped yet, so the
        registry never ships with silently-unlocatable ZENs.

    Raises:
        SystemExit: When the fetched feed contains a city not present in
            ``_CITY_META``. The auto-refresh library path deliberately
            downgrades this to a warning; hand-runs stay strict.
    """
    root = Path(__file__).resolve().parent.parent
    path = root / "data" / "zscaler_cenr_hostnames.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    data, warnings = attach_city_metadata(data)

    # CLI stays strict on unmapped cities.
    for warning in warnings:
        if warning.startswith("Unmapped cities in feed"):
            raise SystemExit(warning)

    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    city_metadata = data.get("city_metadata", {}) or {}
    assert isinstance(city_metadata, dict)
    print(f"Wrote city_metadata for {len(city_metadata)} cities.")
    for warning in warnings:
        print(f"NOTE: {warning}")


if __name__ == "__main__":
    main()

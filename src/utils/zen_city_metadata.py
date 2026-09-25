"""Per-city geo metadata for the Zscaler CENR feed.

Why:
    The synthetic-probe scheduler picks the ZEN cities nearest to each Mist
    site. The upstream Zscaler CENR feed gives a city display name and a set
    of proxy hostnames only. It carries no country, no continent, and no
    coordinate. This module holds the hand-curated map that supplies them.

    Issue #3404 moved this code out of `scripts/build_zen_city_metadata.py`.
    That directory holds development tooling, and the container no longer
    ships it. `src/utils/zscaler_catalogue.py` reads `attach_city_metadata`
    on the auto-refresh path, so the function is product code and it must
    live under `src/`.

    The maintenance command still lives in `scripts/build_zen_city_metadata.py`
    and it imports this module. That split follows the precedent of
    `src/utils/zscaler_probe.py`, which was promoted the same way.
"""

from __future__ import annotations

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


def _pick_host(entry: object) -> str:
    """Return the bare FQDN whether the bag entry is a legacy string or a v3 dict.

    Why:
        The upstream CENR merger emits ``list[dict]`` under
        schema_version=3 (per contract cenr_cache_schema_v3.md), but
        hand-authored or legacy caches may still contain flat strings.
        A raw ``str(entry)`` on a dict yields ``"{'host': 'foo.com'}"``
        which then gets stamped as a probe target -- ugly at best,
        and it would break the synthetic-test URL builder in menu 206.

    Args:
        entry: One element of a ``proxy_hostnames`` or ``vpn_hostnames`` bag.

    Returns:
        The hostname, or an empty string when the entry carries none.
    """
    if isinstance(entry, dict):  # Schema version 3 wraps each host in a mapping.
        host = entry.get("host")  # Read the only key that carries the FQDN.
        return host if isinstance(host, str) else ""  # Reject a non-string host.
    return str(entry)  # A legacy cache already holds the bare string.


def _first_host(city_bag: dict[str, Any], key: str) -> str:
    """Return the first hostname in the bag at *key*, or an empty string.

    Args:
        city_bag: One ``by_city`` entry of the CENR document.
        key: Either ``proxy_hostnames`` or ``vpn_hostnames``.

    Returns:
        The first hostname, or an empty string when the bag holds none.
    """
    raw = city_bag.get(key, []) or []  # Read the bag, treating a null value as empty.
    if not isinstance(raw, list) or not raw:  # Reject a malformed bag and an empty bag.
        return ""
    return _pick_host(raw[0])  # The first entry is the site-scope target.


def _probe_hostnames(city_bag: dict[str, Any]) -> list[str]:
    """Return the probe targets for one city.

    Why:
        Proxy and VPN ride the same PoP but are distinct service planes
        (ZIA HTTPS proxy against IPsec or GRE tunnel init), so we pin both
        as site-scope critical to catch either service failing on its own.

    Args:
        city_bag: One ``by_city`` entry of the CENR document.

    Returns:
        The proxy host then the VPN host, with every empty result dropped.
    """
    candidates = [
        _first_host(city_bag, "proxy_hostnames"),  # The ZIA HTTPS proxy plane.
        _first_host(city_bag, "vpn_hostnames"),  # The IPsec or GRE tunnel plane.
    ]
    return [host for host in candidates if host]  # Drop every bag that held no host.


def _city_entry(city_bag: dict[str, Any], meta: tuple[str, str, float, float]) -> dict[str, float | str | list[str]]:
    """Return the ``city_metadata`` record for one city.

    Args:
        city_bag: One ``by_city`` entry of the CENR document.
        meta: The ``_CITY_META`` row holding country, continent, and coordinates.

    Returns:
        The metadata record, including the probe targets when the feed names any.
    """
    country, continent, lat, lon = meta  # Unpack the static geography row.
    entry: dict[str, float | str | list[str]] = {
        "country_code": country,  # ISO 3166-1 alpha-2 code for the city.
        "continent": continent,  # Coarse region label used by the dashboards.
        "lat": lat,  # Latitude of the PoP, for the map view.
        "lon": lon,  # Longitude of the PoP, for the map view.
    }
    probe_hostnames = _probe_hostnames(city_bag)  # Read both service planes.
    if probe_hostnames:  # Only a city with a live host carries probe keys.
        entry["probe_hostnames"] = probe_hostnames  # The list form that readers prefer.
        # Retain scalar for back-compat with any reader that predates
        # the list form. Always mirrors probe_hostnames[0] (the proxy).
        entry["probe_hostname"] = probe_hostnames[0]
    return entry


def _read_by_city(data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Return the ``by_city`` mapping of *data* and any warning about its type.

    Args:
        data: The parsed CENR document.

    Returns:
        The mapping and the warnings. A malformed mapping becomes an empty one.
    """
    raw = data.get("by_city", {}) or {}  # Read the mapping, treating a null value as empty.
    if not isinstance(raw, dict):  # A feed that changed shape must not raise here.
        message = f"by_city has unexpected type {type(raw).__name__}; " "treating as empty"
        return {}, [message]  # Report the shape and continue with no cities.
    return raw, []  # The mapping is well formed, so no warning applies.


def _coverage_warnings(live_cities: set[str], known_cities: set[str]) -> list[str]:
    """Return one warning for each gap between the feed and ``_CITY_META``.

    Args:
        live_cities: Every city name that the feed names.
        known_cities: Every city name that ``_CITY_META`` maps.

    Returns:
        A warning for unmapped cities, a warning for stale rows, or both.
    """
    warnings: list[str] = []  # Collect every gap in one list.
    missing = sorted(live_cities - known_cities)  # Cities the feed added.
    stale = sorted(known_cities - live_cities)  # Rows the feed no longer names.
    if missing:  # A new pop needs a hand-added geography row.
        warnings.append(f"Unmapped cities in feed (add to _CITY_META): {missing}")
    if stale:  # A retired pop leaves a row that maps nothing.
        warnings.append(f"{len(stale)} mapped cities no longer in feed: {stale}")
    return warnings


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
    by_city, warnings = _read_by_city(data)  # Read the feed and report a bad shape.
    live_cities = set(by_city.keys())  # Every city that the feed names.
    warnings.extend(_coverage_warnings(live_cities, set(_CITY_META)))  # Report every gap.

    city_metadata: dict[str, dict[str, float | str | list[str]]] = {}
    for city in sorted(live_cities):  # Sort so the output file stays stable.
        meta = _CITY_META.get(city)  # Read the static geography row.
        if meta is None:
            # Non-fatal in library form; the SystemExit is only in main().
            continue
        city_metadata[city] = _city_entry(by_city[city], meta)  # Build the record.

    data["city_metadata"] = city_metadata  # Attach the map in place.
    data["city_metadata_notes"] = _CITY_METADATA_NOTES  # Explain the map for a reader.
    return data, warnings

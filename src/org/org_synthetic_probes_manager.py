"""Org-level Zscaler synthetic-probe manager (menu 206).

Builds, merges, or swaps ``synthetic_test.custom_probes`` entries on the
Mist org setting using a curated catalogue of Zscaler Client Connector
destinations shipped with the repo under ``data/``.

Why:
    Operators need a single-command way to keep the Zscaler reachability
    probe fleet in sync with their VLAN topology. Hand-maintaining the
    probe block against Zscaler's evolving Cloud Enforcement Node list is
    error-prone. This module treats the JSON in ``data/`` as the source of
    truth, and marks every probe it writes with the ``zcc-`` name prefix
    so a follow-up run can safely merge or swap without disturbing
    probes authored elsewhere.

Module-import must remain side-effect free (--help guard):
    Only ``import`` statements at module scope. All I/O, prompts, and API
    calls live inside functions invoked from the menu dispatch table.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

# Import mistapi setting/sites modules at module load so tests can monkey-patch
# them via ``patch.object``. All four are side-effect free re-exports.
import mistapi
from mistapi.api.v1.orgs import setting as _mist_setting
from mistapi.api.v1.orgs import sites as _mist_orgs_sites
from mistapi.api.v1.sites import setting as _mist_site_setting

from src.utils.zscaler_catalogue import ensure_fresh, promote_cache_document

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_PROBE_SOURCE_FILE = "zscaler_client_connector_probes.json"
_CENR_SOURCE_FILE = "zscaler_cenr_hostnames.json"
_TOOL_NAME_PREFIX = "zcc-"
_TUNNEL_ZEN_ROLE = "tunnel_zen"  # Only role that expands via CENR hostnames.
_VLAN_MIN = 1
_VLAN_MAX = 4094
_CRITICAL_AGGRESSIVENESS = "high"
_AUTO_AGGRESSIVENESS = "auto"
# Priority tiers recognised on READ (schedule/demote decisions). The Mist UI's
# per-probe "Critical" checkbox writes ``"high"`` (verified 2026-07-25 by
# toggling a probe in the UI and dumping the org setting). Older versions of
# this tool wrote ``"critical"`` -- also a real, valid priority tier accepted
# by the API. Both must be treated as priority for read-side decisions so orgs
# carrying the legacy value keep behaving correctly during the transition.
# Writes emit only ``"high"`` (via ``_CRITICAL_AGGRESSIVENESS``) to stay
# byte-identical with UI-authored probes in exported configs and audit dumps.
_PRIORITY_AGGRESSIVENESS: frozenset[str] = frozenset({"critical", "high"})

# Region-scoped Samsung ELM activation roles live in the probe source file with
# names like ``samsung_elm_activation_americas``. They are country-specific
# reachability targets, so pushing them at org scope would spray every region's
# endpoints everywhere -- pointless for sites in the wrong region and noisy for
# operators. Instead the org PUT skips them entirely (see ``_build_probe_set``)
# and the site-override flow injects the one matching region based on each
# picked site's ``country_code``.
_SAMSUNG_ELM_ROLE_PREFIX = "samsung_elm_activation_"
_COUNTRY_CODE_TO_REGION: dict[str, str] = {
    # North America -- pre-1025 baseline.
    "US": "americas",  # United States
    "CA": "americas",  # Canada
    "MX": "americas",  # Mexico
    # South America -- large markets from the pre-1025 baseline.
    "AR": "americas",  # Argentina
    "BR": "americas",  # Brazil
    "CL": "americas",  # Chile
    "CO": "americas",  # Colombia
    "PE": "americas",  # Peru
    "VE": "americas",  # Venezuela
    # South America -- 1025 US2 extension (residual sovereign codes so the
    # continent classifies without falling through to EMEA).
    "BO": "americas",  # Bolivia
    "EC": "americas",  # Ecuador
    "FK": "americas",  # Falkland Islands (Islas Malvinas)
    "GF": "americas",  # French Guiana
    "GY": "americas",  # Guyana
    "PY": "americas",  # Paraguay
    "SR": "americas",  # Suriname
    "UY": "americas",  # Uruguay
    # Central America -- 1025 US2 extension.
    "BZ": "americas",  # Belize
    "CR": "americas",  # Costa Rica
    "GT": "americas",  # Guatemala
    "HN": "americas",  # Honduras
    "NI": "americas",  # Nicaragua
    "PA": "americas",  # Panama
    "SV": "americas",  # El Salvador
    # Caribbean -- 1025 US2 extension (every ISO-listed island so the region
    # never falls through to the EMEA default).
    "AG": "americas",  # Antigua and Barbuda
    "AI": "americas",  # Anguilla
    "AW": "americas",  # Aruba
    "BB": "americas",  # Barbados
    "BL": "americas",  # Saint Barthelemy
    "BM": "americas",  # Bermuda
    "BQ": "americas",  # Bonaire, Sint Eustatius and Saba
    "BS": "americas",  # Bahamas
    "CU": "americas",  # Cuba
    "CW": "americas",  # Curacao
    "DM": "americas",  # Dominica
    "DO": "americas",  # Dominican Republic
    "GD": "americas",  # Grenada
    "GP": "americas",  # Guadeloupe
    "HT": "americas",  # Haiti
    "JM": "americas",  # Jamaica
    "KN": "americas",  # Saint Kitts and Nevis
    "KY": "americas",  # Cayman Islands
    "LC": "americas",  # Saint Lucia
    "MF": "americas",  # Saint Martin (French part)
    "MQ": "americas",  # Martinique
    "MS": "americas",  # Montserrat
    "PR": "americas",  # Puerto Rico
    "SX": "americas",  # Sint Maarten (Dutch part)
    "TC": "americas",  # Turks and Caicos Islands
    "TT": "americas",  # Trinidad and Tobago
    "VC": "americas",  # Saint Vincent and the Grenadines
    "VG": "americas",  # British Virgin Islands
    "VI": "americas",  # United States Virgin Islands
    # China + SARs + Taiwan hit ``.com.cn`` endpoints. EMEA fallback uses
    # ``.com`` so they must be routed to the china role explicitly.
    "CN": "china",  # China (mainland)
    "HK": "china",  # Hong Kong SAR
    "MO": "china",  # Macao SAR
    "TW": "china",  # Taiwan
}
# Anything not listed above falls through to EMEA. EMEA endpoints are the
# broadest surface (Africa, Middle East, Europe, plus every APAC/Oceania code
# we have not explicitly routed to China), so this is the safest default. A
# warning is logged when the fallback fires so operators can spot unmapped
# country codes and extend ``_COUNTRY_CODE_TO_REGION`` if needed.
_DEFAULT_REGION = "emea"

# Deliberately-unmapped ISO-3166-1 alpha-2 codes. These fall through to
# ``_DEFAULT_REGION`` today by design (they map onto EMEA's ``.com`` endpoint
# surface which is the correct behaviour for Africa, the Middle East, Europe,
# Central/South/Southeast/Northeast Asia, Oceania, and Antarctica -- none of
# which have a dedicated regional Samsung ELM role). Enumerating every
# residual code explicitly (rather than leaving them implicit in the fall-
# through) turns the pairing (``_COUNTRY_CODE_TO_REGION``, this set) into a
# machine-checkable coverage contract: together they must cover every ISO
# alpha-2 code exactly once. See ``iso_coverage_invariant.md`` INV-COVER-1..4
# and the regression suite in ``tests/unit/org/test_country_region_coverage.py``
# which fails CI the moment a code is silently added, removed, or duplicated.
# Membership is a frozenset so downstream helpers cannot mutate the coverage
# invariant at runtime.
_COUNTRY_CODE_INTENTIONAL_GAPS: frozenset[str] = frozenset(
    {
        # Africa (EMEA -- broadest fallback surface today)
        "AO",  # Angola
        "BF",  # Burkina Faso
        "BI",  # Burundi
        "BJ",  # Benin
        "BW",  # Botswana
        "CD",  # DR Congo
        "CF",  # Central African Republic
        "CG",  # Congo
        "CI",  # Cote d'Ivoire
        "CM",  # Cameroon
        "CV",  # Cabo Verde
        "DJ",  # Djibouti
        "DZ",  # Algeria
        "EG",  # Egypt
        "EH",  # Western Sahara
        "ER",  # Eritrea
        "ET",  # Ethiopia
        "GA",  # Gabon
        "GH",  # Ghana
        "GM",  # Gambia
        "GN",  # Guinea
        "GQ",  # Equatorial Guinea
        "GW",  # Guinea-Bissau
        "KE",  # Kenya
        "KM",  # Comoros
        "LR",  # Liberia
        "LS",  # Lesotho
        "LY",  # Libya
        "MA",  # Morocco
        "MG",  # Madagascar
        "ML",  # Mali
        "MR",  # Mauritania
        "MU",  # Mauritius
        "MW",  # Malawi
        "MZ",  # Mozambique
        "NA",  # Namibia
        "NE",  # Niger
        "NG",  # Nigeria
        "RE",  # Reunion
        "RW",  # Rwanda
        "SC",  # Seychelles
        "SD",  # Sudan
        "SH",  # Saint Helena
        "SL",  # Sierra Leone
        "SN",  # Senegal
        "SO",  # Somalia
        "SS",  # South Sudan
        "ST",  # Sao Tome and Principe
        "SZ",  # Eswatini
        "TD",  # Chad
        "TG",  # Togo
        "TN",  # Tunisia
        "TZ",  # Tanzania
        "UG",  # Uganda
        "YT",  # Mayotte
        "ZA",  # South Africa
        "ZM",  # Zambia
        "ZW",  # Zimbabwe
        # Middle East (EMEA -- broadest fallback surface today)
        "AE",  # United Arab Emirates
        "AF",  # Afghanistan
        "BH",  # Bahrain
        "IL",  # Israel
        "IQ",  # Iraq
        "IR",  # Iran
        "JO",  # Jordan
        "KW",  # Kuwait
        "LB",  # Lebanon
        "OM",  # Oman
        "PS",  # Palestine
        "QA",  # Qatar
        "SA",  # Saudi Arabia
        "SY",  # Syria
        "TR",  # Turkey
        "YE",  # Yemen
        # Europe + European overseas / crown dependencies (EMEA)
        "AD",  # Andorra
        "AL",  # Albania
        "AT",  # Austria
        "AX",  # Aland Islands
        "BA",  # Bosnia and Herzegovina
        "BE",  # Belgium
        "BG",  # Bulgaria
        "BV",  # Bouvet Island
        "BY",  # Belarus
        "CH",  # Switzerland
        "CY",  # Cyprus
        "CZ",  # Czechia
        "DE",  # Germany
        "DK",  # Denmark
        "EE",  # Estonia
        "ES",  # Spain
        "FI",  # Finland
        "FO",  # Faroe Islands
        "FR",  # France
        "GB",  # United Kingdom
        "GE",  # Georgia
        "GG",  # Guernsey
        "GI",  # Gibraltar
        "GL",  # Greenland
        "GR",  # Greece
        "GS",  # South Georgia
        "HM",  # Heard and McDonald Islands
        "HR",  # Croatia
        "HU",  # Hungary
        "IE",  # Ireland
        "IM",  # Isle of Man
        "IS",  # Iceland
        "IT",  # Italy
        "JE",  # Jersey
        "LI",  # Liechtenstein
        "LT",  # Lithuania
        "LU",  # Luxembourg
        "LV",  # Latvia
        "MC",  # Monaco
        "MD",  # Moldova
        "ME",  # Montenegro
        "MK",  # North Macedonia
        "MT",  # Malta
        "NL",  # Netherlands
        "NO",  # Norway
        "PL",  # Poland
        "PM",  # Saint Pierre and Miquelon
        "PT",  # Portugal
        "RO",  # Romania
        "RS",  # Serbia
        "RU",  # Russia
        "SE",  # Sweden
        "SI",  # Slovenia
        "SJ",  # Svalbard and Jan Mayen
        "SK",  # Slovakia
        "SM",  # San Marino
        "UA",  # Ukraine
        "VA",  # Vatican City
        # Central Asia (EMEA today. No China routing)
        "AM",  # Armenia
        "AZ",  # Azerbaijan
        "KG",  # Kyrgyzstan
        "KZ",  # Kazakhstan
        "TJ",  # Tajikistan
        "TM",  # Turkmenistan
        "UZ",  # Uzbekistan
        # South Asia (EMEA today)
        "BD",  # Bangladesh
        "BT",  # Bhutan
        "IN",  # India
        "LK",  # Sri Lanka
        "MV",  # Maldives
        "NP",  # Nepal
        "PK",  # Pakistan
        # Southeast Asia (EMEA today. Not classified as China)
        "BN",  # Brunei
        "ID",  # Indonesia
        "KH",  # Cambodia
        "LA",  # Laos
        "MM",  # Myanmar
        "MY",  # Malaysia
        "PH",  # Philippines
        "SG",  # Singapore
        "TH",  # Thailand
        "TL",  # Timor-Leste
        "VN",  # Vietnam
        # Northeast Asia (EMEA today. Not classified as China)
        "JP",  # Japan
        "KP",  # North Korea
        "KR",  # South Korea
        "MN",  # Mongolia
        # Oceania + Pacific outposts (EMEA today)
        "AS",  # American Samoa
        "AU",  # Australia
        "CC",  # Cocos (Keeling) Islands
        "CK",  # Cook Islands
        "CX",  # Christmas Island
        "FJ",  # Fiji
        "FM",  # Micronesia
        "GU",  # Guam
        "IO",  # British Indian Ocean Territory
        "KI",  # Kiribati
        "MH",  # Marshall Islands
        "MP",  # Northern Mariana Islands
        "NC",  # New Caledonia
        "NF",  # Norfolk Island
        "NR",  # Nauru
        "NU",  # Niue
        "NZ",  # New Zealand
        "PF",  # French Polynesia
        "PG",  # Papua New Guinea
        "PN",  # Pitcairn
        "PW",  # Palau
        "SB",  # Solomon Islands
        "TF",  # French Southern Territories
        "TK",  # Tokelau
        "TO",  # Tonga
        "TV",  # Tuvalu
        "UM",  # US Minor Outlying Islands
        "VU",  # Vanuatu
        "WF",  # Wallis and Futuna
        "WS",  # Samoa
        # Antarctica -- no plausible Mist site
        "AQ",  # Antarctica
    }
)

# Default URL scheme / port pairs. Mist's ``target`` field is a URL, so a
# per-role ``probe.protocol`` chosen from the curated JSON maps directly to a
# URL scheme -- with two caveats encoded in ``_probe_target``:
#   1. ``tcp`` is not a valid URL scheme for Mist synthetic tests. Roles that
#      the reachability probing showed only respond to raw TCP/443 (for example
#      ``service_discovery_enrollment_login``) still exercise the same TCP
#      handshake path when probed as HTTPS, so we transparently upgrade to
#      ``https`` for URL construction.
#   2. Ports matching the scheme default (80 for http, 443 for https) are
#      elided from the URL to match Mist's own ``mini-*`` shape (which never
#      writes an explicit ``:443`` on HTTPS targets).
_SCHEME_DEFAULT_PORT: dict[str, int] = {"http": 80, "https": 443}

# UDP/500 (IKE_SA_INIT) is the ZEN VPN service plane. When a VPN-bag host has
# no live UDP observation yet, defaulting to bare ``host:500`` is still
# correct -- the alternative (``https://vpn-host``) was the pre-1023 bug that
# emitted 400+ never-succeed HTTPS probes against IPsec/IKE endpoints. See
# probe_target_url_builder.md SC-001 and the 2026-07-26 regression that
# resurfaced after the schema-v3 cache promotion left ``observed_protocol``
# unpopulated on every VPN host.
_VPN_DEFAULT_PORT = 500


def _fqdn_in_vpn_bag(bag: Any, fqdn: str) -> bool:
    """Return True when ``fqdn`` appears as a host entry inside ``bag``.

    Why:
        Extracted from :func:`_is_vpn_host` so the outer classifier stays
        under Radon CC>10. Tolerates both the v2 flat-string bags and the v3
        dict bags because the fallback path fires precisely when the loader
        could not enrich entries with observation metadata.

    Args:
        bag: Candidate list from either the top-level ``vpn_hostnames`` or a
            per-city variant. Non-list values return ``False``.
        fqdn: Hostname to match, case-sensitive.

    Returns:
        ``True`` when any entry (v2 string or v3 ``{"host": str}`` dict)
        matches ``fqdn``; ``False`` otherwise.
    """
    if not isinstance(bag, list):
        return False
    for entry in bag:
        host = entry.get("host") if isinstance(entry, dict) else entry
        if isinstance(host, str) and host == fqdn:
            return True
    return False


def _is_vpn_host(fqdn: str, cenr_source: dict[str, Any]) -> bool:
    """Return True iff ``fqdn`` appears in any ``vpn_hostnames`` bag.

    Why:
        The CENR file classifies every ZEN hostname as either proxy (HTTPS
        service plane) or vpn (IKE/IPsec service plane). When Branch 3's
        fallback fires because no live observation exists yet, the bag
        that the host lives in tells us the correct default port/scheme
        without needing a probe cycle. This is the deterministic, no-
        heuristic classifier -- no ``-vpn.`` string matching, no role
        peek -- so a hostname is treated as VPN iff the operator or the
        CENR feed said so.

    Args:
        fqdn: Hostname to classify.
        cenr_source: Loaded CENR document (v2 flat strings or v3 dicts;
            both are unwrapped by ``_fqdn_in_vpn_bag`` below).

    Returns:
        True when the FQDN appears anywhere in a ``vpn_hostnames`` list
        (top-level or under ``by_city[*]``). False otherwise.
    """
    if _fqdn_in_vpn_bag(cenr_source.get("vpn_hostnames"), fqdn):
        return True
    by_city = cenr_source.get("by_city")
    if not isinstance(by_city, dict):
        return False
    for city_slot in by_city.values():
        if isinstance(city_slot, dict) and _fqdn_in_vpn_bag(city_slot.get("vpn_hostnames"), fqdn):
            return True
    return False


def _probe_type_for_target(target: str, _role_type: str | None = None) -> str:
    """Classify a probe body ``type`` from the emitted target string.

    Why:
        Mist synthetic tests use ``type: "application"`` for URL-based
        checks (HTTP/HTTPS GETs against the ``target`` URL) and
        ``type: "reachability"`` for raw ICMP checks (bare hostname).
        Feature 1024 tightened the classifier to be **shape-based**: the
        target's own shape is the source of truth for the probe type,
        not any upstream ``role_type`` hint. This closes an
        overwrite window where a role tagged ``type: application``
        could re-attach the ``application`` label to a bare-hostname
        VPN target and reintroduce the pre-1024 fake-L4 failure mode
        (INV-2, INV-3). ``role_type`` is retained in the signature for
        backwards compatibility with all three callsites. Its value is
        NOT consulted for the decision.

    Args:
        target: The fully-built probe target string as returned by
            ``_probe_target``. HTTP/HTTPS URLs start with the scheme;
            bare hostnames carry no scheme and no ``":port"`` suffix;
            L4 targets appear as ``host:port`` (no scheme).
        role_type: Legacy hint from role metadata. Ignored — kept only
            so existing callers compile. Removal is a follow-up cleanup.

    Returns:
        ``"application"`` when *target* starts with ``http://`` /
        ``https://`` OR contains a ``":"`` after the last ``"."``
        (a bare ``host:port`` shape). ``"reachability"`` otherwise
        (bare hostname — the post-1024 VPN emission shape).
    """
    # Scheme detection: case-sensitive prefix match. Targets emitted by
    # this codebase are always lowercase. No normalisation required.
    if target.startswith(("http://", "https://")):
        decision = "application"
    else:
        # Port detection: look for ":" AFTER the last "." — a bare host
        # has no ":", a host:port has exactly one ":" after the last dot.
        # This avoids false positives on hypothetical IPv6-literal targets
        # (unsupported by Mist Marvis Minis today. Revisit if support arrives).
        last_dot = target.rfind(".")
        if last_dot != -1 and ":" in target[last_dot:]:
            decision = "application"
        else:
            # Bare hostname — the post-1024 VPN reachability shape.
            decision = "reachability"
    # Debug trace only per contract §Logging. The emitting callsite
    # handles higher-severity logging per Principle VII. Logger is
    # constructed here (not module-scoped) to match the local-scope
    # pattern used by peers like ``_probe_target``.
    logging.getLogger(__name__).debug("probe_type: target=%s -> %s", target, decision)
    return decision


def _find_host_in_bags(container: dict[str, Any], fqdn: str) -> dict[str, Any] | None:
    """Scan ``proxy_hostnames`` / ``vpn_hostnames`` bags on ``container`` for ``fqdn``.

    Why:
        Extracted from ``_lookup_v3_observation`` so top-level and by_city
        walks share one predicate. Keeps the dispatcher below Radon CC=10
        and encapsulates the v2-string guard (bare strings return ``None``
        so the caller can trigger the fallback branch).

    Args:
        container: v3-shaped CENR node with ``proxy_hostnames`` and
            ``vpn_hostnames`` bags (top-level document or per-city slot).
        fqdn: Fully-qualified hostname to match on ``entry["host"]``.

    Returns:
        The matching v3 entry dict, or ``None`` when absent.
    """
    for bag_key in ("proxy_hostnames", "vpn_hostnames"):
        bag = container.get(bag_key) or []
        if not isinstance(bag, list):
            continue
        for entry in bag:
            if isinstance(entry, dict) and entry.get("host") == fqdn:
                return entry
    return None


def _lookup_v3_observation(fqdn: str, cenr_source: dict[str, Any]) -> dict[str, Any] | None:
    """Locate the v3 host-entry for ``fqdn`` in every CENR bag.

    Why:
        Contract ``probe_target_url_builder.md`` Preconditions require
        the URL builder to consult the v3 per-host observation object
        wherever the FQDN lives -- top-level ``proxy_hostnames`` /
        ``vpn_hostnames`` or nested under ``by_city[*]``. Centralising
        the lookup keeps the dispatch in ``_probe_target`` short and
        guarantees identical semantics across bags (contract Non-Goals:
        never mutate ``cenr_source``).

    Args:
        fqdn: Fully-qualified hostname to look up.
        cenr_source: Loaded CENR document, post v2->v3 loader adapter.

    Returns:
        The v3 entry dict when found (``{"host": ..., "observed_protocol":
        ..., "observed_port": ..., "last_probed": ...}``), otherwise
        ``None`` when the FQDN is absent from every bag.
    """
    # Top-level bags are the common case. Iterate them first so the fast
    # path exits before descending into by_city.
    hit = _find_host_in_bags(cenr_source, fqdn)
    if hit is not None:
        return hit
    # by_city bags carry the same shape (per cenr_cache_schema_v3.md). Walk
    # them last because the top-level bags dominate the hit rate.
    by_city = cenr_source.get("by_city")
    if isinstance(by_city, dict):
        for city_slot in by_city.values():
            if not isinstance(city_slot, dict):
                continue
            hit = _find_host_in_bags(city_slot, fqdn)
            if hit is not None:
                return hit
    return None


def _extract_observed_protocol_port(
    entry: Any,
) -> tuple[str | None, int | None]:
    """Pull ``observed_protocol`` and ``observed_port`` from a CENR entry.

    Why:
        Extracted from :func:`_probe_target` so its dispatch body stays under
        the Radon CC gate. The type guards mirror the schema: string protocol
        and integer port. Anything else collapses to ``None`` so the caller's
        Branch 3 fallback triggers.

    Args:
        entry: A per-host observation dict from the v3 CENR document, or
            ``None`` / any non-dict when the host is absent.

    Returns:
        ``(observed_protocol, observed_port)``. Either or both fields may be
        ``None``.
    """
    observed_protocol: str | None = None
    observed_port: int | None = None
    if isinstance(entry, dict):
        raw_protocol = entry.get("observed_protocol")
        if isinstance(raw_protocol, str) and raw_protocol:
            observed_protocol = raw_protocol
        raw_port = entry.get("observed_port")
        if isinstance(raw_port, int):
            observed_port = raw_port
    return observed_protocol, observed_port


def _dispatch_observed_target(
    fqdn: str,
    observed_protocol: str | None,
    observed_port: int | None,
) -> str | None:
    """Apply the non-VPN observation-first Branch 1 / Branch 2 dispatch.

    Why:
        Split out of :func:`_probe_target` so the contract-heavy branch
        selection is one focused function. Returning ``None`` signals that
        the caller must fall through to the Branch 3 role/CENR fallback (no
        recognised observation or missing port).

    Args:
        fqdn: Hostname being rendered.
        observed_protocol: Value from ``observed_protocol`` in the CENR
            observation, or ``None`` when absent.
        observed_port: Value from ``observed_port`` in the CENR observation,
            or ``None`` when absent.

    Returns:
        The composed target string per Branch 1 or Branch 2, or ``None`` when
        the observation is missing / unrecognised (caller runs Branch 3).
    """
    logger = logging.getLogger(__name__)
    if observed_protocol is None:
        return None
    # Branch 2: HTTPS or TCP/443 collapse to the same URL shape so the
    # emitted target matches Mist-authored mini-* rows byte-for-byte
    # (FR-009: any per-run diff of the same host across runs must be
    # empty when the observation is stable).
    if observed_protocol == "HTTPS" or observed_protocol == "TCP/443":
        target = f"https://{fqdn}"
        logger.debug("probe_target: %s -> %s (obs=%s)", fqdn, target, observed_protocol)
        return target
    # Branch 1: UDP family (bare "UDP" or "UDP/<port>") OR non-443 TCP.
    # The port MUST come from observed_port -- observed_protocol may
    # carry no port suffix at all (bare "UDP" token per contract Test
    # Boundaries).
    is_udp = observed_protocol == "UDP" or observed_protocol.startswith("UDP/")
    is_non_443_tcp = observed_protocol.startswith("TCP/") and observed_protocol != "TCP/443"
    if (is_udp or is_non_443_tcp) and observed_port is not None:
        # Bare host:port form. NO scheme so Mist runs a raw probe
        # rather than trying TLS on a UDP/IKE endpoint.
        target = f"{fqdn}:{observed_port}"
        logger.debug("probe_target: %s -> %s (obs=%s)", fqdn, target, observed_protocol)
        return target
    return None


def _resolve_fallback_probe(
    role: dict[str, Any],
    cenr_source: dict[str, Any],
) -> tuple[str, int]:
    """Resolve the Branch 3 fallback ``(protocol, port)`` from role + CENR defaults.

    Why:
        Split out of :func:`_build_fallback_target` so the protocol
        normalisation and port coercion do not push the parent above the
        Radon CC gate. ``tunnel_zen`` still delegates to
        ``cenr_source["probe_default"]``. Unknown protocols still coerce to
        ``https``. Non-integer port values still fall back to the scheme
        default.

    Args:
        role: Role dict; ``role["probe"]`` may carry role-specific overrides.
        cenr_source: Loaded v3 CENR document; ``probe_default`` supplies the
            tunnel_zen delegation only.

    Returns:
        ``(protocol, port)`` where ``protocol`` is one of the keys in
        ``_SCHEME_DEFAULT_PORT`` and ``port`` is an integer.
    """
    probe = role.get("probe") or {}
    if not probe and role.get("role") == _TUNNEL_ZEN_ROLE:
        # tunnel_zen delegates its default to the CENR file (existing
        # convention retained from the pre-1023 implementation).
        probe = cenr_source.get("probe_default") or {}
    protocol = str(probe.get("protocol") or "https").lower()
    # Mist targets are URLs. Raw TCP has no URL scheme, so upgrade to HTTPS
    # which exercises the same TCP/443 handshake path.
    if protocol == "tcp":
        protocol = "https"
    if protocol not in _SCHEME_DEFAULT_PORT:
        protocol = "https"
    port_raw = probe.get("port")
    try:
        port = int(port_raw) if port_raw is not None else _SCHEME_DEFAULT_PORT[protocol]
    except (TypeError, ValueError):
        port = _SCHEME_DEFAULT_PORT[protocol]
    return protocol, port


def _build_fallback_target(
    fqdn: str,
    role: dict[str, Any],
    cenr_source: dict[str, Any],
    observed_protocol: str | None,
) -> str:
    """Compose the Branch 3 fallback target from the role or CENR probe defaults.

    Why:
        Extracted from :func:`_probe_target` so the fallback logic is
        testable in isolation. The VPN pre-check and Branches 1/2 already
        handled everything else. This only fires for non-VPN hosts with
        missing / unrecognised observations.

    Args:
        fqdn: Hostname to render.
        role: Role dict passed through to :func:`_resolve_fallback_probe`.
        cenr_source: Loaded v3 CENR document.
        observed_protocol: Original observation value (may be ``None``). Used
            only in the debug log line.

    Returns:
        Fallback target string, ``"<scheme>://<fqdn>"`` when the port matches
        the scheme default (INV-1 elision) or ``"<scheme>://<fqdn>:<port>"``
        otherwise.
    """
    logger = logging.getLogger(__name__)
    protocol, port = _resolve_fallback_probe(role, cenr_source)
    if port == _SCHEME_DEFAULT_PORT[protocol]:
        # Default-port elision matches Branch 2's convention so both branches
        # emit identical strings for the common case (INV-1: byte-stable
        # output when the same host+protocol combination reoccurs).
        target = f"{protocol}://{fqdn}"
    else:
        target = f"{protocol}://{fqdn}:{port}"
    # NOTE(1025-US1): warning moved to load-time _emit_load_time_cenr_warning to avoid N*M duplication
    logger.debug("probe_target: %s -> %s (obs=%s)", fqdn, target, observed_protocol)
    return target


def _probe_target(fqdn: str, role: dict[str, Any], cenr_source: dict[str, Any]) -> str:
    """Compose the Mist ``target`` string for one FQDN using the observation-first dispatch.

    Why:
        Contract ``probe_target_url_builder.md`` (feature 1023) requires
        three-branch dispatch on the v3 per-host observation for **non-VPN**
        hosts. Contract ``vpn_probe_target_shape.md`` (feature 1024) requires
        the VPN pre-check to run **before** the non-VPN dispatch: a bag
        member always emits as a bare hostname (ICMP reachability), even
        when the host also has a TCP/443 observation (bag wins per
        Ordering Contract).

        Non-VPN dispatch (unchanged from 1023):

        - Branch 1 (UDP-family or non-HTTP TCP): return bare
          ``host:port`` so Mist runs a raw reachability probe (SC-001
          eliminates the ``https://*-vpn.*`` regression).
        - Branch 2 (HTTPS or TCP/443): return ``https://host`` with the
          default port elided (INV-1, FR-009 keep the shipped rows
          byte-identical to previous versions).
        - Branch 3 (no observation, absent key, or unrecognised token):
          fall back to the catalogue default and emit exactly ONE
          ``logger.warning`` so operators notice the cache miss.

        VPN pre-check (new in 1024): if ``_is_vpn_host`` classifies the
        FQDN, return bare ``fqdn`` immediately. Pre-1024 this branch
        returned ``f"{fqdn}:500"`` — the fake-L4 shape that Mist could
        not actually IKE-negotiate. INV-3 forbids any VPN row from
        carrying a scheme or a ``:port`` suffix.

        The function is pure — it never mutates ``cenr_source`` (contract
        Non-Goals) and is deterministic on repeat calls.

    Args:
        fqdn: The hostname to render into a probe target string. Callers
            strip wildcards before invoking this helper.
        role: The role dict from the probe source file. Retained for
            signature parity with previous versions. Branch 3's fallback
            still respects ``role["probe"]`` when present so
            role-specific overrides in the ZCC catalogue continue to
            work.
        cenr_source: Loaded CENR document (v3-shaped). The v2->v3 loader
            adapter guarantees per-host observation objects.

    Returns:
        A non-empty target string. For VPN-classified FQDNs: bare
        ``fqdn`` (no scheme, no port). Otherwise: ``"host:port"``
        (Branch 1) or ``"https://host"`` (Branch 2, default 443 elided)
        or the catalogue default (Branch 3).
    """
    logger = logging.getLogger(__name__)  # module-scoped logger. Matches _warn spec in contract

    # --- VPN pre-check (feature 1024) ---------------------------------------
    # MUST run before the non-VPN 3-branch dispatch so that a host present
    # in a ``vpn_hostnames`` bag AND also observed on TCP/443 (Zscaler admin
    # console) is emitted as a VPN reachability probe. Bag membership wins
    # per contract vpn_probe_target_shape.md §Ordering Contract. Pre-1024
    # this branch returned ``f"{fqdn}:500"``. That fake-L4 shape produced
    # 100% guaranteed-fail probes because Mist cannot speak IKEv2.
    if _is_vpn_host(fqdn, cenr_source):
        logger.info("probe_target(vpn): %s -> bare (reachability)", fqdn)
        return fqdn

    entry = _lookup_v3_observation(fqdn, cenr_source)
    observed_protocol, observed_port = _extract_observed_protocol_port(entry)

    # --- Dispatch on the observed_protocol prefix per contract ---------------
    dispatched = _dispatch_observed_target(fqdn, observed_protocol, observed_port)
    if dispatched is not None:
        return dispatched

    # Branch 3: no observation OR unrecognised token. Compute the fallback
    # from the role's ``probe`` block (if any) or the CENR probe_default,
    # then log exactly one WARNING so operators spot the cache miss. The
    # VPN pre-check above has already handled bag members, so this branch
    # only fires for non-VPN hosts with missing observations.
    return _build_fallback_target(fqdn, role, cenr_source, observed_protocol)


def manage_org_synthetic_probes(mist_session: Any, org_id: str) -> None:
    """Interactive entry point for menu 206.

    Why:
        Single public API surface for the feature. The menu dispatch table
        calls this exact callable. Keeping it thin and delegating to the
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

    sources = _load_probe_sources(_DEFAULT_DATA_DIR)
    # NOTE(1025-US1): dedup state for the load-time CENR WARNING lives here so
    # its lifetime is bounded by the invocation (data-model.md §3 INV-D1;
    # FR-012 requires re-emission across back-to-back operator runs).
    warned_cenr_hosts: set[str] = set()  # mutable dedup set, empty per run
    logging.info(  # Constitution VII: BEFORE the load-time diff
        "computing load-time CENR missing-host set for org_id=%s",
        org_id,
    )
    _emit_load_time_cenr_warning(  # single call site per invocation
        _compute_missing_cenr_hosts(  # inner: set difference over frozen universes
            _collect_catalogue_hosts(sources[0]),  # probes side
            _collect_cenr_observed_hosts(sources[1]),  # observations side
        ),
        warned_cenr_hosts,  # dedup state -- mutated in place
    )
    logging.debug(  # Constitution VII: AFTER the load-time emission
        "load-time CENR check complete; warned_cenr_hosts=%s",
        len(warned_cenr_hosts),
    )
    # NOTE(1025-US2): companion dedup state for the load-time
    # country_code warning lives here so its lifetime is bounded by the invocation
    # (data-model.md §3 INV-D1. FR-012 requires re-emission across
    # back-to-back operator runs). Emission itself is delegated to
    # ``_prompt_and_apply_site_overrides`` because that is where the site
    # list is materialised via ``_list_org_sites`` -- the site list is
    # gated behind the operator's site-override opt-in so it is not fetched
    # unless needed. Threading the empty set from here keeps the set
    # lifetime pinned to this invocation as required by FR-012.
    warned_unmapped_codes: set[str] = set()  # mutable dedup set, empty per run
    vlan_ids = _prompt_vlan_list()
    setting = _fetch_setting(mist_session, org_id)
    existing_probes = _detect_existing(setting)
    tool_authored, foreign = _partition_tool_authored(existing_probes)

    new_probes = _build_probe_set(sources, vlan_ids)

    if tool_authored:
        mode = _prompt_mode(tool_authored)
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
        resulting_tool = new_probes

    demoted_foreign = _demote_stale_critical(foreign)
    summary = _summarise(resulting_tool, tool_authored, demoted_foreign, foreign)
    if not _prompt_confirm(summary):
        print("  Operation cancelled -- no changes were made.")
        logging.info("Operator declined final confirmation; no PUT issued")
        return

    # Foreign demotions are merged with the tool-authored set so demoted
    # entries survive the PUT (strict preservation would keep them at their
    # prior priority tier and re-blow the 5-critical cap).
    combined = {**demoted_foreign, **resulting_tool}
    _apply(mist_session, org_id, setting, combined, vlan_ids)

    # Post-PUT site-override flow: give the operator a chance to push the
    # same probe set into one or more site-level settings so specific
    # sites can override the org-wide config.
    _prompt_and_apply_site_overrides(
        mist_session,
        org_id,
        resulting_tool,
        sources,
        warned_unmapped_codes,  # threaded from load-time scope so lifetime is bounded by this invocation
    )

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
    # Promote both caches to v3 shape at the earliest possible moment so
    # every downstream reader (URL builder, probe fanout, telemetry) works off
    # dict host entries rather than a mix of flat strings and dicts. Both
    # calls are idempotent for v3+ documents.
    probes = promote_cache_document(probes, kind="zcc")  # legacy ZCC roles bag
    cenr = promote_cache_document(cenr, kind="cenr")  # legacy CENR proxy/vpn bags
    cenr = ensure_fresh(cenr_path, cenr)
    return probes, cenr


def _add_observed_hosts_from_container(
    container: dict[str, Any],
    observed: set[str],
) -> None:
    """Add every host string in ``container``'s proxy/vpn bags to ``observed``.

    Why:
        Extracted from ``_collect_cenr_observed_hosts`` so the top-level
        walk and the by_city walk share one predicate (matches the pattern
        used by ``_find_host_in_bags``). Keeps the caller below Radon
        CC=10.

    Args:
        container: v3-shaped node with ``proxy_hostnames`` / ``vpn_hostnames``
            bags (top-level document or per-city slot).
        observed: Set to add hosts into (mutated in place).
    """
    for bag_key in ("proxy_hostnames", "vpn_hostnames"):
        bag = container.get(bag_key) or []
        if not isinstance(bag, list):
            continue
        for entry in bag:
            if isinstance(entry, dict):
                host = entry.get("host")
                if isinstance(host, str):
                    observed.add(host)
            elif isinstance(entry, str):
                # v2 legacy flat string tolerated during migration.
                observed.add(entry)


def _collect_cenr_observed_hosts(cenr_source: dict[str, Any]) -> frozenset[str]:
    """Return every FQDN that has a CENR observation record.

    Why:
        T011 needs the "known observations" side of the catalogue-minus-observations
        set difference. Rather than teaching ``_compute_missing_cenr_hosts`` about
        the four bag locations (``proxy_hostnames``, ``vpn_hostnames``, and each
        ``by_city[*]`` slot's paired bags), we walk them once here and return a
        frozen set. This mirrors ``_lookup_v3_observation``'s bag traversal so
        the two functions agree on which bags are authoritative.

    Args:
        cenr_source: Loaded CENR document, post v2->v3 loader adapter.

    Returns:
        Frozen set of every host string discovered across all CENR bags.
        Non-dict / non-string / missing-``host`` entries are silently skipped
        (defensive against mid-migration flat strings that slipped past the
        loader adapter).
    """
    observed: set[str] = set()  # accumulator. Frozen at return time for immutability
    _add_observed_hosts_from_container(cenr_source, observed)
    # by_city bags carry the same shape per cenr_cache_schema_v3.md.
    by_city = cenr_source.get("by_city")
    if isinstance(by_city, dict):
        for city_slot in by_city.values():
            if not isinstance(city_slot, dict):
                continue
            _add_observed_hosts_from_container(city_slot, observed)
    return frozenset(observed)


def _collect_catalogue_hosts(probes_source: dict[str, Any]) -> frozenset[str]:
    """Return every catalogue FQDN that ``_probe_target`` may consult observations for.

    Why:
        The "catalogue hosts" side of the set difference is every non-wildcard
        FQDN listed on any role in the probe source file. We include role-inline
        FQDNs (all non-tunnel_zen roles) because ``_probe_target`` consults CENR
        for their observed protocol/port even though the role also carries a
        curated ``probe`` block. ``tunnel_zen`` role FQDNs are supplied BY the
        CENR file itself, so by construction they are already observed and
        cannot appear as "missing". Wildcard entries (``"*."``) are filtered
        because they are never emitted as probes (see ``_build_probe_set``
        line ~798).

    Args:
        probes_source: Loaded probe source document (post v2->v3 promotion).

    Returns:
        Frozen set of every non-wildcard catalogue FQDN.
    """
    catalogue: set[str] = set()  # accumulator. Frozen at return time
    for role in probes_source.get("roles", []) or []:  # each catalogue role
        role_name = role.get("role")  # role slug string
        if role_name == _TUNNEL_ZEN_ROLE:  # tunnel_zen sources FQDNs from CENR itself
            continue  # by construction those hosts are already observed
        for entry in role.get("fqdns") or []:  # tolerate missing fqdns key
            # Unwrap v3 dict entries while tolerating legacy flat strings so
            # mid-migration catalogues do not silently drop hosts here.
            fqdn = entry.get("host") if isinstance(entry, dict) else entry  # v3 unwrap
            if not isinstance(fqdn, str) or fqdn.startswith("*."):  # skip wildcards / non-strings
                continue  # wildcards are never emitted as probes
            catalogue.add(fqdn)  # add concrete FQDN to the catalogue universe
    return frozenset(catalogue)  # freeze so callers cannot mutate


def _compute_missing_cenr_hosts(
    catalogue_hosts: frozenset[str],
    cenr_observations: frozenset[str],
) -> frozenset[str]:
    """Return catalogue FQDNs that have no CENR observation record.

    Why:
        This is the load-time replacement for the pre-1025 per-emission WARNING
        storm inside ``_probe_target`` (315 sites x 7 missing hosts = 2205
        WARNINGs on the reference org). Computed exactly once per invocation,
        after ``_load_probe_sources`` returns, so the cap becomes M unique
        hosts instead of N*M repeated emissions (research.md R5).

    Args:
        catalogue_hosts: Non-wildcard FQDN universe from
            ``_collect_catalogue_hosts``.
        cenr_observations: Observed FQDN universe from
            ``_collect_cenr_observed_hosts``.

    Returns:
        Frozen set of catalogue hosts absent from ``cenr_observations``. Empty
        set when every catalogue host has an observation (FR-001 zero-emission
        edge case).
    """
    logging.info(  # Constitution VII action-logging: BEFORE the diff
        "computing missing CENR hosts: catalogue=%s observed=%s",
        len(catalogue_hosts),
        len(cenr_observations),
    )
    missing = frozenset(catalogue_hosts - cenr_observations)  # set difference -> frozen
    logging.debug(  # Constitution VII action-logging: AFTER with result summary
        "computed missing CENR hosts: %s missing",
        len(missing),
    )
    return missing  # frozen so callers cannot smuggle in extra hosts


def _emit_load_time_cenr_warning(
    missing_hosts: frozenset[str],
    warned_cenr_hosts: set[str],
) -> None:
    """Emit exactly one WARNING per invocation naming all unwarned missing hosts.

    Why:
        Contract ``log_record_shape.md`` §1.3 mandates a single load-time
        WARNING record that names every missing host and states catalogue-default
        fallback URLs are in use. ``warned_cenr_hosts`` is the mutable dedup
        state owned by ``manage_org_synthetic_probes`` (data-model.md §3 INV-D1)
        -- we mutate it in place so repeat calls within a single invocation
        are no-ops. FR-012: dedup state does NOT persist across invocations
        (caller supplies a fresh set per run).

    Args:
        missing_hosts: Output of ``_compute_missing_cenr_hosts`` for the
            current run.
        warned_cenr_hosts: Per-invocation dedup set. Hosts added here are
            skipped on any subsequent call within the same invocation.
    """
    logging.info(  # Constitution VII: BEFORE the emission decision
        "evaluating CENR load-time warning: missing=%s already_warned=%s",
        len(missing_hosts),
        len(warned_cenr_hosts),
    )
    unwarned = missing_hosts - warned_cenr_hosts  # subtract already-emitted hosts
    if not unwarned:  # zero-emission edge case (FR-001) or repeat call within run
        logging.debug(  # Constitution VII: AFTER, no-op branch
            "CENR load-time warning: no unwarned missing hosts; skipping emission",
        )
        return  # nothing to warn about
    # Sort for deterministic message shape (test assertions and log-grep audits
    # expect a stable ordering across runs regardless of set iteration order).
    ordered = sorted(unwarned)  # ASCII sort per Constitution V log discipline
    # Single WARNING record naming every host, matching log_record_shape.md §1.3.
    # ASCII-only tokens (CENR, using-catalogue-default-URLs) so ``grep -c CENR``
    # in the operator smoke sequence stays deterministic (SC-001).
    logging.warning(  # exactly-one-per-run WARNING per contract §1.3
        "CENR observations missing for %s catalogue host(s); using catalogue-default URLs: %s",
        len(ordered),
        ", ".join(ordered),
    )
    warned_cenr_hosts.update(unwarned)  # mark as warned so a duplicate call is a no-op
    logging.debug(  # Constitution VII: AFTER, emission branch
        "CENR load-time warning emitted for %s hosts; warned_cenr_hosts now %s",
        len(ordered),
        len(warned_cenr_hosts),
    )


def _compute_unmapped_country_codes(
    sites: list[dict[str, Any]],
    region_map: dict[str, str],
    gap_set: frozenset[str],
) -> frozenset[str]:
    """Return unique ISO codes present in ``sites`` but neither region-mapped nor gap-listed.

    Why:
        Load-time counterpart to ``_compute_missing_cenr_hosts`` for the
        country_code axis. Pre-1025, every site with an unmapped code
        triggered a fresh WARNING inside ``_build_region_probes`` (research.md
        R5 quantifies the N*K duplication: 315 sites * K unmapped codes). By
        collapsing to the set of *unique* codes here -- exactly once per
        invocation -- the downstream emitter caps output at K messages
        regardless of how many sites share each code (FR-004, FR-010).
        Codes appearing in ``gap_set`` are silently classified (they are
        deliberately EMEA today by contract INV-COVER-2) and therefore never
        surface here. Only truly-new codes bubble up so the operator gets a
        signal, not noise.

    Args:
        sites: List of site dicts as returned by ``_list_org_sites``. Each
            dict is expected to carry a ``country_code`` string (missing /
            blank entries are treated as "not classifiable" and skipped
            silently -- the region resolver already falls those through to
            the default region and emitting a WARNING for a null value
            would be indistinguishable from an unmapped-code warning).
        region_map: ``_COUNTRY_CODE_TO_REGION`` (passed as an argument so
            tests can exercise the classifier with fixture-scoped maps
            without patching the module-level constant).
        gap_set: ``_COUNTRY_CODE_INTENTIONAL_GAPS`` (same rationale).

    Returns:
        Frozen set of ISO alpha-2 codes appearing in ``sites`` that are
        neither in ``region_map`` nor in ``gap_set``. Empty set when every
        code is classified (FR-005 zero-emission edge case for the LATAM
        fixture after T020).
    """
    logging.info(  # Constitution VII action-logging: BEFORE the scan
        "computing unmapped country codes: sites=%s region_map=%s gap_set=%s",
        len(sites),
        len(region_map),
        len(gap_set),
    )
    seen: set[str] = set()  # accumulator for unique codes across all sites
    for site in sites:  # single pass over the site list
        raw = site.get("country_code")  # optional field per Mist site schema
        if not isinstance(raw, str):  # non-string / missing -> skip. Region resolver handles it
            continue
        code = raw.strip().upper()  # normalise like _build_region_probes at line 1068
        if not code:  # blank string after normalisation -> skip
            continue
        if code in region_map:  # already region-classified -> silent success
            continue
        if code in gap_set:  # intentional gap -> silently falls through to EMEA
            continue
        seen.add(code)  # genuinely unclassified -> record for warning
    unmapped = frozenset(seen)  # freeze so callers cannot smuggle in extras
    logging.debug(  # Constitution VII: AFTER with unique-code count
        "computed unmapped country codes: %s unique code(s)",
        len(unmapped),
    )
    return unmapped  # frozenset consumed by _emit_load_time_country_code_warning


def _emit_load_time_country_code_warning(
    unmapped_codes: frozenset[str],
    warned_unmapped_codes: set[str],
) -> None:
    """Emit exactly one WARNING per invocation naming all unwarned unmapped codes.

    Why:
        Contract ``log_record_shape.md`` §2.4 mandates a single load-time
        WARNING when at least one site's country_code is neither region-mapped
        nor listed as an intentional gap. The message MUST contain the literal
        token ``country_code`` (test filter anchor from ``_count_country_code_warnings``
        at line 3050) and MUST name every unwarned code plus the default
        region literal so an operator can either extend
        ``_COUNTRY_CODE_TO_REGION`` or add the code to
        ``_COUNTRY_CODE_INTENTIONAL_GAPS`` in the same commit. FR-012 pins
        per-invocation lifetime: ``warned_unmapped_codes`` is caller-owned and
        recreated per run.

    Args:
        unmapped_codes: Output of ``_compute_unmapped_country_codes``.
        warned_unmapped_codes: Per-invocation dedup set (mutated in place).
            Codes added here are skipped on any subsequent call within the
            same invocation. FR-012: caller supplies a fresh empty set per
            run. State MUST NOT persist across runs.
    """
    logging.info(  # Constitution VII: BEFORE the emission decision
        "evaluating country_code load-time warning: unmapped=%s already_warned=%s",
        len(unmapped_codes),
        len(warned_unmapped_codes),
    )
    unwarned = unmapped_codes - warned_unmapped_codes  # subtract codes already emitted this run
    if not unwarned:  # zero-emission (FR-005 LATAM path) or repeat call within run
        logging.debug(  # Constitution VII: AFTER, no-op branch
            "country_code load-time warning: no unwarned unmapped codes; skipping emission",
        )
        return  # nothing to warn about
    # Deterministic ordering so ``grep -c country_code`` in the operator smoke
    # sequence stays stable across runs regardless of set iteration order.
    ordered = sorted(unwarned)  # ASCII sort per Constitution V log discipline
    # Single WARNING record naming every code plus the default region literal
    # so the operator knows exactly which routing decision was made. ASCII
    # tokens only (``country_code``, ``defaulting to region``) so the grep
    # anchor stays deterministic (SC-002, log_record_shape.md §2.4).
    logging.warning(  # exactly-one-per-run WARNING per contract §2.4
        "country_code(s) %s not mapped; defaulting to region %r",
        ", ".join(ordered),
        _DEFAULT_REGION,
    )
    warned_unmapped_codes.update(unwarned)  # mark as warned so a duplicate call is a no-op
    logging.debug(  # Constitution VII: AFTER, emission branch
        "country_code load-time warning emitted for %s code(s); warned_unmapped_codes now %s",
        len(ordered),
        len(warned_unmapped_codes),
    )


def _parse_vlan_token(part: str) -> list[int]:
    """Return the VLAN ids parsed from one comma-split token.

    Why:
        Extracted from :func:`_validate_vlan_input` so the outer parser
        stays under Radon CC>10. Handles both single ids (``"10"``) and
        ranges (``"3-6"``). Invalid tokens return an empty list so the
        caller can drop them silently without adding a branch per case.

    Args:
        part: One already-stripped, non-empty token from the split.

    Returns:
        List of ids from the token, empty on any parse failure or
        reversed range.
    """
    if "-" in part[1:]:
        lo_raw, _, hi_raw = part[1:].partition("-")
        lo_raw = (part[0] + lo_raw).strip()
        hi_raw = hi_raw.strip()
        try:
            lo, hi = int(lo_raw), int(hi_raw)
        except ValueError:
            return []
        return list(range(lo, hi + 1)) if lo <= hi else []
    try:
        return [int(part)]
    except ValueError:
        return []


def _validate_vlan_input(raw: str) -> tuple[bool, str, list[int]]:
    """Parse and validate VLAN input string.

    Why:
        Mist's UI validator rejects VLAN ids outside 1-4094 (0 and 4095
        are 802.1Q-reserved and 4095 is priority-tagged frames), so any
        out-of-range value would produce a red-banner error on the org
        setting push. Operators frequently paste condensed lists like
        ``"3-6, 10, 200-203"``. Expanding ranges here lets them use the
        same shorthand they use in switch configs. Invalid tokens
        (non-integer, out-of-range endpoints, reversed ranges) are
        silently dropped rather than failing the whole entry so a single
        typo in a long list does not force the operator to re-type
        everything.

    Args:
        raw: Comma-separated VLAN ids and/or ranges (for example ``"3-6, 10"``).

    Returns:
        ``(is_valid, error_message, vlan_ids)``. ``is_valid`` is True
        only when at least one in-range id survived parsing;
        ``vlan_ids`` is sorted and deduplicated. Out-of-range or
        unparseable tokens are dropped silently.
    """
    if not raw.strip():
        return False, "VLAN list cannot be empty. Please try again.", []
    ids: list[int] = []
    for part in (item.strip() for item in raw.split(",")):
        if part:
            ids.extend(_parse_vlan_token(part))
    ids = [vid for vid in ids if _VLAN_MIN <= vid <= _VLAN_MAX]
    if not ids:
        return (
            False,
            f"No valid VLAN ids in [{_VLAN_MIN}, {_VLAN_MAX}] parsed. Please try again.",
            [],
        )
    return True, "", sorted(set(ids))


def _prompt_vlan_list() -> list[int]:
    """Prompt the operator for a comma-separated VLAN id list.

    Why:
        The VLAN list is the only per-invocation parameter. Validating
        the range at prompt time avoids surfacing an opaque API-side
        rejection later. Accepts ranges (``3-6`` expands to ``3,4,5,6``)
        because operators paste condensed lists from switch configs.

    Returns:
        Sorted, deduplicated list of VLAN ids in ``[1, 4094]``. Never
        returns an empty list -- the prompt loops until at least one
        valid id is entered.
    """
    while True:
        raw = input("  Enter VLAN ids (comma-separated, ranges ok e.g. 3-6, each in [1, 4094]): ")
        is_valid, error, ids = _validate_vlan_input(raw)
        if is_valid:
            return ids
        print(f"  {error}")


def _fetch_setting(mist_session: Any, org_id: str) -> dict[str, Any]:
    """Return the current org setting block via mistapi.

    Why:
        Isolating the read call makes it trivial to mock in tests and
        clarifies the get boundary from the put boundary.

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
        Guarded accessor so callers do not have to worry about the
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
        Foreign probes (any probe whose name lacks the ``zcc-`` prefix)
        must be preserved verbatim through merge and swap so operator-
        authored config survives the tool run. Partitioning up-front
        keeps the downstream helpers pure.

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
        Probe names need a stable, filesystem-safe derivation from the
        FQDN so tool-authored probes are recognisable across re-runs.
        Lowercase + ``.`` -> ``-`` is sufficient because Zscaler FQDNs
        are ASCII-only.

    Args:
        fqdn: The concrete hostname (never a wildcard by the time this
            is called).

    Returns:
        Lowercased slug with dots replaced by hyphens.
    """
    return fqdn.lower().replace(".", "-")


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres between two lat/lon pairs.

    Why:
        ZEN city ranking uses geodesic distance from a site's Mist-reported
        ``latlng`` to each candidate ZEN city centre. Haversine is the
        standard closed-form solution: no external dep, no earth-model
        approximation error large enough to affect ranking at the
        continental scale we care about (Zscaler cities are hundreds of
        kilometres apart. Sub-percent radius error is invisible).

    Args:
        lat1: First point latitude in decimal degrees.
        lon1: First point longitude in decimal degrees.
        lat2: Second point latitude in decimal degrees.
        lon2: Second point longitude in decimal degrees.

    Returns:
        Distance in kilometres. Always non-negative.
    """
    # Mean earth radius in km. Using the volumetric mean (IUGG) rather than
    # equatorial keeps error symmetric across hemispheres for our use.
    earth_radius_km = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_km * c


def _unwrap_v3_hosts(entries: list[Any]) -> list[str]:
    """Return concrete hostname strings from a mixed v2/v3 CENR host list.

    Why:
        CENR is mid-migration from a flat ``list[str]`` (v2) to a list of
        ``{"host": str, ...}`` dicts (v3). Every consumer must handle
        both shapes or silently drop hosts, so this helper centralises
        the unwrap so ``_iter_role_fqdns`` and future callers do not
        each reinvent the v3-tolerant read.

    Args:
        entries: A raw list from the CENR file or a role's ``fqdns`` --
            a mix of plain strings (v2), dicts with a ``host`` key (v3),
            and possible falsy entries produced by upstream ``... or
            []`` fallbacks.

    Returns:
        The concrete host string for every truthy entry, with v3 dict
        entries unwrapped to their ``host`` value.
    """
    return [e["host"] if isinstance(e, dict) else e for e in entries if e]


def _iter_role_fqdns(role: dict[str, Any], cenr: dict[str, Any]) -> list[str]:
    """Yield the concrete FQDN list for a single role, expanding CENR.

    Why:
        Only the ``tunnel_zen`` role expands via the CENR file. Every
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
        proxy = cenr.get("proxy_hostnames", []) or []  # v3 dicts or v2 flat strings
        vpn = cenr.get("vpn_hostnames", []) or []  # v3 dicts or v2 flat strings
        return _unwrap_v3_hosts([*proxy, *vpn])
    return _unwrap_v3_hosts(role.get("fqdns") or [])


def _emit_probes_for_role(
    role: dict[str, Any],
    cenr_source: dict[str, Any],
    result: dict[str, dict[str, Any]],
) -> tuple[bool, bool]:
    """Emit every probe body for one role into ``result``.

    Why:
        Extracted from ``_build_probe_set`` so the outer function stays
        under Radon CC=10. Encapsulates the per-role loop (wildcard skip,
        one-critical-per-role selection, mini-* body shape). Returns the
        ``(critical_role, critical_assigned)`` pair so the caller can run
        the "critical role but no explicit FQDN matched" fallback in one
        place.

    Args:
        role: One role entry from ``probes_source["roles"]``.
        cenr_source: Loaded CENR document (for FQDN expansion + target
            resolution).
        result: Aggregating map. Probes are inserted under their
            ``zcc-<role>-<slug>`` keys.

    Returns:
        ``(critical_role, critical_assigned)``. ``critical_role`` is True
        when the role carries ``critical: true``; ``critical_assigned``
        is True when this pass already assigned the role's one critical
        slot.
    """
    role_name = role.get("role") or "unknown"
    critical_role = bool(role.get("critical"))
    critical_target = role.get("critical_fqdn")
    critical_assigned = False
    for fqdn in _iter_role_fqdns(role, cenr_source):
        if not isinstance(fqdn, str) or fqdn.startswith("*."):
            continue
        # Pick exactly one critical FQDN per critical role. Preference
        # order: explicit ``critical_fqdn`` if it appears in the
        # expanded list, otherwise the first non-wildcard hit.
        is_critical = False
        if critical_role and not critical_assigned and (critical_target is None or fqdn == critical_target):
            is_critical = True
            critical_assigned = True
        probe_name = f"{_TOOL_NAME_PREFIX}{role_name}-{_fqdn_slug(fqdn)}"
        target = _probe_target(fqdn, role, cenr_source)
        probe_body: dict[str, Any] = {
            # Classify the body type from the target's shape: HTTP/S URLs
            # are ``application`` probes, bare ``host:port`` (VPN, custom
            # UDP) are ``reachability`` probes.
            "type": _probe_type_for_target(target, role.get("type")),
            "target": target,
        }
        probe_body["aggressiveness"] = _CRITICAL_AGGRESSIVENESS if is_critical else _AUTO_AGGRESSIVENESS
        result[probe_name] = probe_body
    return critical_role, critical_assigned


def _promote_first_probe_to_critical(
    result: dict[str, dict[str, Any]],
    role_name: str,
    critical_target: Any,
) -> None:
    """Promote the first probe named for ``role_name`` to critical.

    Why:
        Fallback for ``_build_probe_set`` when a role declared critical
        but the requested ``critical_fqdn`` was absent from the FQDN
        expansion. Extracted so the caller stays under CC=10. Still
        spending the critical slot on the intended role beats silently
        downgrading it.

    Args:
        result: Current probe map (mutated in place).
        role_name: Role slug to search for.
        critical_target: Requested critical FQDN (for the warning only).
    """
    slug_prefix = f"{_TOOL_NAME_PREFIX}{role_name}-"
    for probe_name, probe in result.items():
        if probe_name.startswith(slug_prefix):
            probe["aggressiveness"] = _CRITICAL_AGGRESSIVENESS
            logging.warning(
                "Role %s: critical_fqdn %r not found; promoted %s to critical",
                role_name,
                critical_target,
                probe_name,
            )
            return


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
        vlan_ids: Kept for signature/back-compat with the caller. Ignored
            when building probe bodies because VLAN scoping belongs on
            the ``tests[]`` row that references the probe, not on the
            ``custom_probes`` definition itself (matches Mist's own
            ``mini-*`` shape).

    Returns:
        A ``{probe_name: probe_body}`` map ready to be merged into the
        setting block. Wildcard FQDNs are skipped.
    """
    probes_source, cenr_source = sources
    result: dict[str, dict[str, Any]] = {}
    for role in probes_source.get("roles", []) or []:
        role_name = role.get("role") or "unknown"
        # Region-scoped Samsung ELM roles are injected at site scope only (see
        # ``_build_region_probes``) so pushing them at org scope would spray
        # every region's endpoints everywhere. Skip them here.
        if isinstance(role_name, str) and role_name.startswith(_SAMSUNG_ELM_ROLE_PREFIX):
            continue
        critical_role, critical_assigned = _emit_probes_for_role(role, cenr_source, result)
        # Fallback: role declared critical but the requested
        # ``critical_fqdn`` was absent from the expansion. Promote the
        # first probe emitted for the role so we still spend a critical
        # slot on the intended role rather than silently downgrading.
        if critical_role and not critical_assigned:
            _promote_first_probe_to_critical(result, role_name, role.get("critical_fqdn"))
    return result


def _build_region_probes(
    sources: tuple[dict[str, Any], dict[str, Any]],
    country_code: str | None,
) -> dict[str, dict[str, Any]]:
    """Build the Samsung ELM probe set for the region matching ``country_code``.

    Why:
        Region-scoped Samsung ELM roles (``samsung_elm_activation_americas``,
        ``..._emea``, ``..._china``) are skipped by ``_build_probe_set`` at
        org scope because pushing every region's endpoints to every site is
        wasteful noise. The site-override flow calls this helper instead so
        each picked site only receives the ELM role matching its own
        ``country_code``. Unmapped or missing country codes fall back to
        EMEA (the broadest surface). The operator-visible WARNING for the
        unmapped set is now emitted once at load time by
        ``_emit_load_time_country_code_warning`` (1025-US2, FR-004 / FR-010)
        rather than once per site here, so this helper stays silent on the
        fallback path and returns bytes deterministically for INV-1.

    Args:
        sources: The ``(probes, cenr)`` tuple from ``_load_probe_sources``.
        country_code: ISO 3166-1 alpha-2 code from the site dict (case-
            insensitive. May be ``None`` or an unmapped code -- both fall
            through to EMEA silently. See ``_emit_load_time_country_code_warning``
            for the operator-visible surface).

    Returns:
        A ``{probe_name: probe_body}`` map for the one matching role.
        Empty dict if the probe source file does not ship a role for the
        resolved region (defensive. The shipped catalogue has all three).
    """
    probes_source, _ = sources
    normalised = (country_code or "").strip().upper()
    region = _COUNTRY_CODE_TO_REGION.get(normalised)  # None -> unmapped or intentionally omitted
    if region is None:
        # NOTE(1025-US2): warning moved to load-time
        # ``_emit_load_time_country_code_warning`` to avoid N*K duplication
        # per FR-004 / FR-010 / SC-002. Region-value resolution behaviour is
        # unchanged -- unmapped codes still fall through to _DEFAULT_REGION
        # so regional probes still fire (FR-003 spirit preserved).
        region = _DEFAULT_REGION  # emea fallback -- deliberate, per data-model.md
    target_role_name = f"{_SAMSUNG_ELM_ROLE_PREFIX}{region}"
    for role in probes_source.get("roles", []) or []:
        if role.get("role") == target_role_name:
            return _build_regional_elm_probes(role, sources, target_role_name)
    return {}


def _build_regional_elm_probes(
    role: dict[str, Any],
    sources: tuple[dict[str, Any], dict[str, Any]],
    target_role_name: str,
) -> dict[str, dict[str, Any]]:
    """Emit the ``{probe_name: probe_body}`` map for one Samsung ELM role.

    Why:
        Extracted from ``_build_region_probes`` so the outer helper can
        stay under the project's CC<=10 gate. The inner loop is
        catalogue-shape-specific (v3 dict / v2 flat unwrap plus wildcard
        filtering), and the two concerns read more cleanly split apart.

    Args:
        role: The matched Samsung ELM role dict from ``probes_source``.
        sources: The ``(probes, cenr)`` tuple. Only ``cenr`` (index 1) is
            passed through to ``_probe_target`` for probe-body wiring.
        target_role_name: Precomputed ``samsung_elm_activation_<region>``
            slug so the probe-name builder does not have to reconstruct
            it.

    Returns:
        A ``{probe_name: probe_body}`` map for the resolved role.
    """
    result: dict[str, dict[str, Any]] = {}
    for entry in role.get("fqdns") or []:
        # Accept both v3 dict {"host": ...} and legacy flat strings so a
        # mid-migration CENR cache does not silently drop every regional
        # ELM host. The isinstance guard below already excludes non-strings,
        # so unwrap up-front and let the wildcard filter proceed as before.
        fqdn = entry.get("host") if isinstance(entry, dict) else entry
        if not _is_concrete_probe_fqdn(fqdn):
            continue
        probe_name = f"{_TOOL_NAME_PREFIX}{target_role_name}-{_fqdn_slug(fqdn)}"
        # Regional ELM probes are never critical (source catalogue omits
        # the flag), so aggressiveness is ``auto``.
        target = _probe_target(fqdn, role, sources[1])
        result[probe_name] = {
            # Same target-shape classification as ``_build_probe_set``:
            # HTTP/S URLs stay ``application``, bare host:port becomes
            # ``reachability``. Regional ELM roles ship as HTTPS today
            # but this future-proofs the emit path.
            "type": _probe_type_for_target(target, role.get("type")),
            "target": target,
            "aggressiveness": _AUTO_AGGRESSIVENESS,
        }
    return result


def _is_concrete_probe_fqdn(fqdn: Any) -> bool:
    """Return ``True`` for a plain string FQDN that is not a wildcard.

    Why:
        Every probe-emitting loop drops wildcard entries (``*.example.com``)
        because Mist synthetic probes require a resolvable single host.
        Sharing the check centralises the filter and helps helpers stay
        under the CC gate.

    Args:
        fqdn: A candidate value from a v3-dict unwrap or a v2 flat list.

    Returns:
        ``True`` if ``fqdn`` is a ``str`` and does not start with
        ``"*."``. Otherwise ``False``.
    """
    return isinstance(fqdn, str) and not fqdn.startswith("*.")


# Compression rule: countries with at most this many distinct ZEN locations
# get ALL of their locations scheduled at every site in-country. Above this
# threshold, we fall back to nearest-N-by-haversine. Two is chosen because
# Zscaler almost always deploys a same-city pair (for example Frankfurt IV + VI at
# identical coords), so a country with only a "two location" footprint really
# has one geographic point + a redundant peer -- probing both is cheap and
# gives operators failover signal.
_ZEN_COMPRESSION_THRESHOLD = 2
# When a site's country has more ZEN locations than the compression threshold,
# we pick this many nearest ZENs by geodesic distance. Two matches the
# threshold so a site in a ZEN-dense country (US, DE, IN...) still gets a
# primary+secondary probe pair rather than just one.
_ZEN_NEAREST_COUNT = 2


def _site_latlng(site: dict[str, Any]) -> tuple[float, float] | None:
    """Extract ``(lat, lon)`` from a Mist site dict, or ``None`` if absent.

    Why:
        Mist sites report position under ``latlng: {lat, lng}``. Some sites
        (never-configured stubs, imported inventory) lack the field or ship
        it as null. Callers must handle the None branch, so returning None
        (rather than raising) keeps the resolver flow linear.

    Args:
        site: The site dict as returned by ``_list_org_sites``.

    Returns:
        ``(lat, lon)`` tuple when both floats are present and finite;
        ``None`` otherwise.
    """
    latlng = site.get("latlng")
    if not isinstance(latlng, dict):
        return None
    lat = latlng.get("lat")
    lon = latlng.get("lng")
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return None
    if not math.isfinite(float(lat)) or not math.isfinite(float(lon)):
        return None
    return (float(lat), float(lon))


def _distinct_zen_locations(city_metadata: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    """Group city_metadata entries by unique ``(country_code, lat, lon)``.

    Why:
        Zscaler frequently ships multiple named ZENs at identical coords
        (for example ``Frankfurt IV`` and ``Frankfurt VI`` at the same lat/lon).
        For compression-rule counting ("does this country have <= N ZEN
        locations?") we must dedupe on physical location, not on name --
        otherwise a country with two co-located same-city peers gets
        double-counted and misses the "probe them all" fast path. Names
        within a group are alphabetically ordered so the caller's picks
        are deterministic.

    Args:
        city_metadata: The ``city_metadata`` map from the CENR JSON file.

    Returns:
        ``{"CC:lat:lon" -> [city_name, ...]}`` where each entry lists the
        Zscaler city display names sharing that location, sorted.
    """
    groups: dict[str, list[str]] = {}
    for city, meta in city_metadata.items():
        country = meta.get("country_code")
        lat = meta.get("lat")
        lon = meta.get("lon")
        if not isinstance(country, str) or not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            continue
        # Round to 4 decimal places (~11 m precision) so trivial floating
        # noise does not split a genuine same-coord pair into two groups.
        key = f"{country.upper()}:{round(float(lat), 4)}:{round(float(lon), 4)}"
        groups.setdefault(key, []).append(city)
    for names in groups.values():
        names.sort()
    return groups


def _zens_in_country(
    city_metadata: dict[str, dict[str, Any]],
    normalised_cc: str,
) -> dict[str, dict[str, Any]]:
    """Filter ``city_metadata`` down to entries matching ``normalised_cc``.

    Why:
        Extracted from ``_resolve_zen_cities_for_site`` so the caller stays
        below the Radon CC=10 quality gate. The predicate is one call site
        today but the isolation makes the rule ("case-insensitive match on
        ``country_code`` string") testable in isolation.

    Args:
        city_metadata: ``cenr["city_metadata"]`` mapping.
        normalised_cc: Uppercased ISO country code (empty string disables
            the filter and returns ``{}``).

    Returns:
        Sub-mapping of cities whose ``country_code`` matches. Empty when
        ``normalised_cc`` is empty or no city matches.
    """
    if not normalised_cc:
        return {}
    result: dict[str, dict[str, Any]] = {}
    for city, meta in city_metadata.items():
        meta_cc = meta.get("country_code")
        if isinstance(meta_cc, str) and meta_cc.upper() == normalised_cc:
            result[city] = meta
    return result


def _pick_zens_from_in_country(
    in_country: dict[str, dict[str, Any]],
    site_coords: tuple[float, float] | None,
    normalised_cc: str,
) -> list[str]:
    """Apply the in-country compression rules (rules 1-3 of ZEN selection).

    Why:
        ``_resolve_zen_cities_for_site`` was CC=13 because the in-country
        branch alone stacks three sub-decisions (threshold vs latlng vs
        fallback). Splitting them out drops the outer function to CC<=10
        and keeps the rule numbering discoverable from one place.

    Args:
        in_country: Result of ``_zens_in_country`` (non-empty).
        site_coords: ``(lat, lon)`` for the site, or ``None``.
        normalised_cc: Uppercased ISO country code (for logging only).

    Returns:
        Sorted, deduped list of ZEN city names per rules 1-3.
    """
    location_groups = _distinct_zen_locations(in_country)
    if len(location_groups) <= _ZEN_COMPRESSION_THRESHOLD:
        return sorted(in_country.keys())
    if site_coords is not None:
        return _nearest_zens_from_pool(in_country, site_coords, _ZEN_NEAREST_COUNT)
    logging.info(
        "Site missing latlng but has country %s with %d ZEN locations; " "scheduling all in-country ZENs",
        normalised_cc,
        len(location_groups),
    )
    return sorted(in_country.keys())


def _resolve_zen_cities_for_site(
    site: dict[str, Any],
    cenr: dict[str, Any],
) -> list[str]:
    """Pick the ZEN cities that a site should probe.

    Why:
        Every Mist site probing every one of the ~95 ZEN cities would burn
        bandwidth and generate noisy dashboards. We want the small set that
        matches the site's geography: if the site's country hosts only a
        handful of ZEN locations, probe them all (they are already nearby);
        otherwise pick the geodesically-nearest few. This mirrors what a
        network engineer would do by hand looking at the ZEN map.

    Compression rules (evaluated in order):
        - Country has <= ``_ZEN_COMPRESSION_THRESHOLD`` distinct ZEN
          locations -> return every ZEN name in-country.
        - Country has more, and the site has a valid ``latlng`` -> return
          the ``_ZEN_NEAREST_COUNT`` nearest ZENs by great-circle distance,
          deduped by location (so same-city pairs count once).
        - Country has more but site lacks ``latlng`` -> return the
          country's ZENs anyway (better to over-probe within-country than
          to skip. Operators can trim later).
        - Site has no country match AND has ``latlng`` -> nearest globally.
        - No country match AND no latlng -> empty list + warn.

    Args:
        site: The Mist site dict. Reads ``country_code`` and ``latlng``.
        cenr: Parsed CENR JSON. Reads ``city_metadata``.

    Returns:
        A sorted, deduped list of ZEN city display names. May be empty.
    """
    city_metadata = cenr.get("city_metadata") or {}
    if not isinstance(city_metadata, dict) or not city_metadata:
        # No metadata available -- fail closed (skip ZEN scheduling)
        # rather than emit undefined probes.
        logging.warning("ZEN scheduling skipped: city_metadata missing from CENR file")
        return []
    country_code = site.get("country_code")
    normalised_cc = country_code.strip().upper() if isinstance(country_code, str) else ""
    site_coords = _site_latlng(site)

    in_country = _zens_in_country(city_metadata, normalised_cc)
    if in_country:
        return _pick_zens_from_in_country(in_country, site_coords, normalised_cc)

    if site_coords is not None:
        # Rule 4: no country match but we know where the site is.
        logging.info(
            "Site country %r has no ZEN presence; falling back to nearest " "%d global ZENs by geodesic distance",
            country_code,
            _ZEN_NEAREST_COUNT,
        )
        return _nearest_zens_from_pool(city_metadata, site_coords, _ZEN_NEAREST_COUNT)

    # Rule 5: nothing to work with.
    logging.warning(
        "ZEN scheduling skipped for site id=%r: no country_code match and " "no latlng",
        site.get("id"),
    )
    return []


def _nearest_zens_from_pool(
    pool: dict[str, dict[str, Any]],
    site_coords: tuple[float, float],
    count: int,
) -> list[str]:
    """Return the ``count`` nearest ZEN city names from a pool.

    Why:
        Same-coord peers (for example Frankfurt IV + Frankfurt VI) should count as
        one location when ranking distance -- otherwise "nearest 2" collapses
        to two names at the same spot. We rank by distinct (lat, lon) groups
        and then re-expand the winning groups back to the full name list so
        operators still get the redundant-peer coverage they expect.

    Args:
        pool: Subset of ``city_metadata`` to consider.
        site_coords: ``(lat, lon)`` for the site.
        count: How many distinct locations to return names for.

    Returns:
        Sorted list of ZEN city names covering the nearest ``count``
        distinct locations. Fewer than ``count`` when the pool has fewer
        distinct locations.
    """
    site_lat, site_lon = site_coords
    # Distance per distinct location key -> representative names.
    per_location: dict[str, tuple[float, list[str]]] = {}
    for city, meta in pool.items():
        lat = meta.get("lat")
        lon = meta.get("lon")
        cc = meta.get("country_code")
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            continue
        if not isinstance(cc, str):
            continue
        key = f"{cc.upper()}:{round(float(lat), 4)}:{round(float(lon), 4)}"
        distance = _haversine_km(site_lat, site_lon, float(lat), float(lon))
        existing = per_location.get(key)
        if existing is None:
            per_location[key] = (distance, [city])
        else:
            existing[1].append(city)
    # Sort by (distance, key) so ties are deterministic.
    ranked = sorted(per_location.items(), key=lambda item: (item[1][0], item[0]))
    picked_names: list[str] = []
    for _key, (_distance, names) in ranked[:count]:
        picked_names.extend(names)
    return sorted(picked_names)


def _probe_hostnames_for_city(meta: dict[str, Any]) -> list[str]:
    """Return the ZEN probe hostnames for one ``city_metadata`` entry.

    Why:
        Extracted from ``_zen_probe_names_for_cities`` so the caller stays
        under Radon CC=10. Encapsulates the v3 (``probe_hostnames`` list)
        vs legacy v2 (``probe_hostname`` scalar) fallback in one place so
        future migrations only touch this helper.

    Args:
        meta: One ``city_metadata`` value (already type-checked as dict).

    Returns:
        Non-empty ``str`` hostnames. Empty list when neither v3 nor legacy
        forms are present.
    """
    hostnames_raw = meta.get("probe_hostnames")
    if isinstance(hostnames_raw, list):
        hostnames = [h for h in hostnames_raw if isinstance(h, str) and h]
        if hostnames:
            return hostnames
    legacy = meta.get("probe_hostname")
    if isinstance(legacy, str) and legacy:
        return [legacy]
    return []


def _zen_probe_names_for_cities(
    cities: list[str],
    cenr: dict[str, Any],
) -> list[str]:
    """Map ZEN city names -> the ``zcc-tunnel_zen-<slug>`` probe names.

    Why:
        Org-scope ``_build_probe_set`` already emitted a probe definition
        for every proxy/vpn hostname in the CENR file, named
        ``zcc-tunnel_zen-<fqdn_slug>``. Site-scope scheduling reuses those
        definitions by name -- this helper picks the representative probe
        hostnames for each ZEN city (recorded in ``city_metadata`` by the
        build script) and formats the matching probe names. Proxy
        (``*.sme.zscaler.net``) and VPN (``*-vpn.zscaler.net``) endpoints
        share the same PoP but are distinct service planes, so we emit
        one probe name per hostname listed for the city -- both get
        pinned as site-scope critical by the caller.

    Args:
        cities: ZEN city display names picked by
            ``_resolve_zen_cities_for_site``.
        cenr: Parsed CENR JSON. Reads ``city_metadata`` for each city's
            ``probe_hostnames`` list (falling back to the legacy
            ``probe_hostname`` scalar if the list form is not present, so
            an unrefreshed CENR file keeps working).

    Returns:
        List of probe names (``zcc-tunnel_zen-<slug>`` shape). Cities
        with neither ``probe_hostnames`` nor a legacy ``probe_hostname``
        are silently skipped -- they'd have no defined probe on the org
        anyway.
    """
    city_metadata = cenr.get("city_metadata") or {}
    if not isinstance(city_metadata, dict):
        return []
    result: list[str] = []
    for city in cities:
        meta = city_metadata.get(city)
        if not isinstance(meta, dict):
            continue
        for hostname in _probe_hostnames_for_city(meta):
            result.append(f"{_TOOL_NAME_PREFIX}{_TUNNEL_ZEN_ROLE}-{_fqdn_slug(hostname)}")
    return result


def _merge_probes(
    existing_tool: dict[str, dict[str, Any]],
    new_probes: dict[str, dict[str, Any]],
    extra_vlans: list[int],
) -> dict[str, dict[str, Any]]:
    """Re-sync tool-authored probes to the mini-* body shape.

    Why:
        Merge is the safe additive path. The correct body shape is
        ``{type, target, aggressiveness}`` only, so this pass strips any
        legacy ``name`` / ``vlan_ids`` fields off existing probes as a
        migration. ``aggressiveness`` is re-synced from ``new_probes`` so
        a probe that lost its "critical" designation upstream is demoted
        here (and the freed critical slot re-lands on the correct probe).

    Args:
        existing_tool: Probes currently on the org matching ``zcc-``.
        new_probes: Freshly-built probe set. Used to look up the
            authoritative ``aggressiveness`` (and ``type``/``target``
            when normalising legacy bodies) for each matching probe.
        extra_vlans: Ignored. Retained for caller signature back-compat.

    Returns:
        Merged probe map. Bodies conform to the mini-* shape:
        ``{type, target, aggressiveness}`` -- no ``name``, no
        ``vlan_ids``.
    """
    del extra_vlans
    merged: dict[str, dict[str, Any]] = {}
    for name, probe in existing_tool.items():
        # Prefer freshly-built type/target (new source of truth). Fall back
        # to on-org values when the probe is not in ``new_probes``.
        template = new_probes.get(name, probe)
        # Resolve target first because the ``type`` classification depends
        # on whether the target string carries an HTTP scheme.
        merged_target = template.get("target") or probe.get("target")
        merged_probe: dict[str, Any] = {
            # Prefer explicit type on the new/existing body when present,
            # but reclassify by target-shape so a body inherited from a
            # pre-1023 push (``type: "application"`` + ``target: "host:500"``)
            # gets corrected to ``reachability`` on merge. Passing the
            # existing body's type as the ``role_type`` preserves overrides
            # for HTTP/S targets while still fixing reachability rows.
            "type": _probe_type_for_target(
                merged_target if isinstance(merged_target, str) else "",
                template.get("type") or probe.get("type"),
            ),
            "target": merged_target,
        }
        # Sync aggressiveness from the freshly-built set so demotions
        # propagate. ``_build_probe_set`` always emits an explicit value;
        # the None branch is defensive against a future refactor dropping
        # the key. Probes with no counterpart in ``new_probes`` (for example a
        # role dropped from the JSON) keep their prior value.
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
        Swap is the destructive path. The helper exists purely so the
        dispatch table in ``manage_org_synthetic_probes`` reads as a
        symmetric pair with ``_merge_probes``.

    Args:
        new_probes: Freshly-built probe set from ``_build_probe_set``.

    Returns:
        ``new_probes`` unchanged.
    """
    return new_probes


def _prompt_mode(existing_tool: dict[str, dict[str, Any]]) -> str:
    """Prompt the operator for merge versus swap.

    Why:
        Displaying the existing probe count and VLAN union up-front gives
        the operator the context needed to make the call without needing
        to walk the setting themselves. Swap is the default because the
        typical operator intent for this menu is a clean rebuild from
        the freshly-generated probe set -- merge is the exception path
        used when preserving hand-added foreign probes matters.

    Args:
        existing_tool: Tool-authored probes currently on the org.

    Returns:
        Either ``"merge"`` or ``"swap"``. Empty input returns ``"swap"``.
    """
    all_vlans: set[int] = set()
    for probe in existing_tool.values():
        for vid in probe.get("vlan_ids") or []:
            if isinstance(vid, int):
                all_vlans.add(vid)
    print(f"  Existing tool-authored probes: {len(existing_tool)}")
    print(f"  VLAN union across existing probes: {sorted(all_vlans)}")
    while True:
        choice = input("  Choose action [merge/swap] (default: swap): ").strip().lower()
        if choice == "":
            return "swap"
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
        The operator must see counts of add/remove/update and the
        resulting total before authorising the PUT. Splitting the
        summary out keeps ``_prompt_confirm`` reusable. The
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
        Surface the exact number of foreign probes the operator is
        about to demote so the foreign-preservation relaxation is
        visible in the summary rather than silent.

    Args:
        before: Foreign probes as originally fetched.
        after: Foreign probes after ``_demote_stale_critical``.

    Returns:
        Number of shared names whose aggressiveness moved off ``critical``.
    """
    count = 0
    for name, probe in before.items():
        if probe.get("aggressiveness") not in _PRIORITY_AGGRESSIVENESS:
            continue
        new_probe = after.get(name)
        if new_probe is None:
            continue
        if new_probe.get("aggressiveness") not in _PRIORITY_AGGRESSIVENESS:
            count += 1
    return count


def _demote_stale_critical(
    foreign: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Return ``foreign`` with any ``aggressiveness=critical`` demoted to ``auto``.

    Why:
        Mist caps priority probes (both ``critical`` and ``high``) at 5
        per effective config. The tool now claims all 5 slots for the
        curated Zscaler roles, so any foreign probe currently marked
        critical must be demoted or the PUT is rejected. We write the
        literal ``"auto"`` (Mist's own default for non-priority probes)
        rather than dropping the key: it is idempotent across re-runs
        and mirrors the value Mist itself emits on system-generated
        probes. This intentionally relaxes strict foreign preservation
        -- the change is surfaced in ``_summarise`` so the operator
        sees it before confirming.

    Args:
        foreign: Foreign probe map (probes without the ``zcc-`` prefix).

    Returns:
        A new dict where every probe previously at
        ``aggressiveness=critical`` is copied with aggressiveness set to
        ``"auto"``. All other fields survive untouched.
    """
    result: dict[str, dict[str, Any]] = {}
    for name, probe in foreign.items():
        if isinstance(probe, dict) and probe.get("aggressiveness") in _PRIORITY_AGGRESSIVENESS:
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
        answers proceed. Anything else aborts as safe-default.

    Args:
        summary: Multi-line pre-PUT summary from ``_summarise``.

    Returns:
        ``True`` if the operator confirmed, ``False`` otherwise.
    """
    print("  Change summary:")
    print(summary)
    answer = input("  Proceed with PUT to org settings? [y/N]: ").strip().lower()
    return answer in ("y", "yes")


def _compute_scheduled_probe_names(
    combined_probes: dict[str, dict[str, Any]],
    extra_regular_names: list[str] | None,
) -> tuple[list[str], list[str]]:
    """Return ``(critical_names, regular_names)`` for injection.

    Why:
        Extracted so the parent stays under the CC gate. Sorted output
        gives us stable row ordering across re-injections (Mist compares
        setting blocks by value on PUT, so drift-free sort keeps diffs
        clean). Regular names are deduplicated against the critical set
        so a Samsung ELM probe promoted to critical does not get two
        scheduled rows.

    Args:
        combined_probes: Union of foreign + tool-authored probes about
            to be written to ``synthetic_test.custom_probes``.
        extra_regular_names: Optional additional ``zcc-*`` names to
            schedule at regular (non-critical) priority.

    Returns:
        Tuple ``(critical_names, regular_names)``. Both lists are
        sorted; ``regular_names`` excludes any name already in
        ``critical_names``.
    """
    critical_names = sorted(
        name
        for name, probe in combined_probes.items()
        if isinstance(probe, dict) and probe.get("aggressiveness") in _PRIORITY_AGGRESSIVENESS
    )
    critical_set = set(critical_names)
    regular_names = sorted(
        {name for name in (extra_regular_names or []) if isinstance(name, str) and name not in critical_set}
    )
    return critical_names, regular_names


def _clean_test_row(row: Any) -> dict[str, Any] | None:
    """Return a cleaned row copy, or ``None`` if the row should be dropped.

    Why:
        Extracted from ``_filter_surviving_test_rows`` so both loop and
        drop rules stay under the CC gate. Encapsulates the two drop
        reasons (legacy aggregate row / row that only held ``zcc-*``
        names) so callers see one predicate.

    Args:
        row: A raw entry from the fetched ``tests[]`` list. Non-dict
            entries are accepted and yield ``None``.

    Returns:
        A shallow-copied dict with ``zcc-*`` names stripped from its
        ``probes`` list, or ``None`` when the row should be dropped
        entirely.
    """
    if not isinstance(row, dict):
        return None
    row_name = row.get("name")
    # Drop legacy tool-authored aggregate rows (name="zcc-critical-probes")
    # written by earlier versions -- they diverge from Mist's one-row-per-probe
    # convention and re-injection below is authoritative.
    if isinstance(row_name, str) and row_name.startswith(_TOOL_NAME_PREFIX):
        logging.info(
            "Dropping legacy tool-authored tests[] row %r (aggregate-row migration)",
            row_name,
        )
        return None
    cleaned = dict(row)
    probes_field = cleaned.get("probes")
    if isinstance(probes_field, list):
        filtered = [p for p in probes_field if not (isinstance(p, str) and p.startswith(_TOOL_NAME_PREFIX))]
        # Row that only held zcc-* names is a prior injection. Drop so
        # re-injection is authoritative.
        if probes_field and not filtered:
            return None
        cleaned["probes"] = filtered
    return cleaned


def _filter_surviving_test_rows(existing_tests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop legacy tool-authored rows and strip stale ``zcc-*`` names.

    Why:
        Re-injection below is authoritative -- keeping stale ``zcc-*``
        entries would double-book probes in the eventual PUT body. The
        per-row predicate is delegated to ``_clean_test_row`` so this
        function stays a trivial fold.

    Args:
        existing_tests: The ``tests[]`` list read from the fetched
            setting (may be empty).

    Returns:
        A new list of cleaned row dicts (originals are not mutated).
    """
    surviving: list[dict[str, Any]] = []
    for row in existing_tests:
        cleaned = _clean_test_row(row)
        if cleaned is not None:
            surviving.append(cleaned)
    return surviving


def _first_vlan_template(surviving: list[dict[str, Any]]) -> list[int] | None:
    """Return the first surviving row's ``vlan_ids`` (int-filtered), or ``None``.

    Why:
        Split out of ``_derive_test_row_template`` so each field's
        scanner stays under the CC gate. Non-int entries in ``vlan_ids``
        are dropped defensively -- Mist's schema is ints-only, but
        malformed operator-authored rows should not crash injection.

    Args:
        surviving: Cleaned rows from ``_filter_surviving_test_rows``.

    Returns:
        A copied int-only list, or ``None`` if no surviving row carried
        a ``vlan_ids`` list.
    """
    for row in surviving:
        row_vlans = row.get("vlan_ids")
        if isinstance(row_vlans, list):
            return [v for v in row_vlans if isinstance(v, int)]
    return None


def _first_lan_template(surviving: list[dict[str, Any]]) -> list[str] | None:
    """Return the first surviving row's ``lan_networks`` (str-filtered), or ``None``.

    Why:
        Peer of ``_first_vlan_template``. Non-str entries are dropped
        defensively -- Mist stores network refs as strings but again
        we do not want a malformed row to crash injection.

    Args:
        surviving: Cleaned rows from ``_filter_surviving_test_rows``.

    Returns:
        A copied str-only list, or ``None`` if no surviving row carried
        a ``lan_networks`` list.
    """
    for row in surviving:
        row_lans = row.get("lan_networks")
        if isinstance(row_lans, list):
            return [ln for ln in row_lans if isinstance(ln, str)]
    return None


def _derive_test_row_template(
    surviving: list[dict[str, Any]],
) -> tuple[list[int] | None, list[str] | None]:
    """Return the first surviving row's ``vlan_ids`` and ``lan_networks``.

    Why:
        Injected rows must inherit operator scoping from foreign rows
        so a targeted deployment (for example VLAN 42 only) does not silently
        widen when the tool adds new probes. The two fields are looked
        up independently so a mixed-shape ``tests[]`` list still yields
        a complete template.

    Args:
        surviving: Cleaned rows from ``_filter_surviving_test_rows``.

    Returns:
        Tuple ``(template_vlan_ids, template_lan_networks)`` -- either
        or both may be ``None`` if no surviving row supplied them.
    """
    return _first_vlan_template(surviving), _first_lan_template(surviving)


def _merge_zcc_criticals_into_tests(
    existing_tests: list[dict[str, Any]],
    combined_probes: dict[str, dict[str, Any]],
    vlan_ids: list[int],
    extra_regular_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Emit one ``tests[]`` row per critical (and opt-in regular) zcc probe.

    Why:
        Mist itself emits one ``tests[]`` row per probe -- each row's
        ``probes`` list holds exactly one name and the row carries its
        own ``vlan_ids`` / ``lan_networks`` copy. Both the system
        ``mini-*`` rows and operator-scheduled probes follow this
        convention, so injected rows must match to look native. Rows
        inherit ``vlan_ids`` / ``lan_networks`` from the first surviving
        foreign row (so operator scoping applies) and fall back to the
        supplied ``vlan_ids`` arg when no template exists. The
        ``extra_regular_names`` opt-in schedules region-specific Samsung
        ELM probes -- these carry ``auto`` aggressiveness so they would
        otherwise never receive a scheduled row and would exist in
        ``custom_probes`` but never run.

    Args:
        existing_tests: The ``tests[]`` list read from the fetched
            setting (may be empty).
        combined_probes: Union of foreign + tool-authored probes about
            to be written to ``synthetic_test.custom_probes``. Only
            probes with ``aggressiveness=critical`` are auto-scheduled.
        vlan_ids: VLAN ids to attach to injected rows when no foreign
            row is available as a template. Ignored when a template row
            with its own ``vlan_ids`` exists.
        extra_regular_names: Optional additional ``zcc-*`` probe names
            to schedule at regular (non-critical) priority. Deduplicated
            against the critical set. Ordering-stable via sort. Rows are
            emitted with the same shape/template as critical rows -- the
            tests[] row itself carries no aggressiveness (that lives on
            the probe body in ``custom_probes``).

    Returns:
        A new list. Foreign rows are preserved (with stale ``zcc-*``
        names stripped from their ``probes`` list). Rows that only ever
        contained ``zcc-*`` probes are dropped so re-injection is
        authoritative. Legacy aggregate rows whose ``name`` starts with
        ``zcc-`` are also dropped. One nameless row is appended per
        scheduled ``zcc-*`` probe, each carrying only that probe's name
        plus inherited ``vlan_ids`` / ``lan_networks``.
    """
    critical_names, regular_names = _compute_scheduled_probe_names(combined_probes, extra_regular_names)
    surviving = _filter_surviving_test_rows(existing_tests)

    if not critical_names and not regular_names:
        return surviving

    template_vlan_ids, template_lan_networks = _derive_test_row_template(surviving)
    effective_vlans = template_vlan_ids if template_vlan_ids is not None else list(vlan_ids)

    for name in critical_names + regular_names:
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
        Wrapper enforces exactly-one-PUT and sibling preservation: we
        deep-copy the fetched ``setting`` block and only overwrite
        ``synthetic_test.custom_probes`` plus regenerate
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
    sources: tuple[dict[str, Any], dict[str, Any]],
    warned_unmapped_codes: set[str],
) -> None:
    """Offer to push the tool-authored probe set into per-site settings.

    Why:
        Mist site settings can override org-wide ``custom_probes``. After
        a successful org PUT the operator often wants a subset of sites
        (for example those with unusual VLAN topology or higher SLE
        expectations) to carry the same probe set locally so
        site-specific probe/VLAN interactions are testable without
        touching org config. Displaying an indexed table (rather than
        asking for raw UUIDs) removes the copy/paste burden and the
        common "typo'd UUID" failure mode operators reported. A separate
        VLAN prompt is issued after site selection because sites picked
        for an override typically have a *different* VLAN topology than
        the org default -- reusing the org list would defeat the point
        of the override. Regional Samsung ELM probes are injected per-
        site based on each site's ``country_code`` so a site in Germany
        gets EMEA endpoints while a site in the US gets the Americas
        set. This whole flow is optional (default no) so unattended runs
        do not silently mutate site settings.

        1025-US2: the site list is also the natural anchor for the
        load-time ``country_code`` WARNING dedup path -- every site with
        an unmapped code is visible in one place, so a single
        ``_emit_load_time_country_code_warning`` call names every
        offender once instead of once per site. The ``warned_unmapped_codes``
        set is threaded in from ``manage_org_synthetic_probes`` so its
        lifetime is bounded by the invocation (FR-012).

    Args:
        mist_session: Authenticated ``mistapi`` session.
        org_id: Mist org UUID -- required for ``listOrgSites`` so the
            index table shows only the sites the operator can actually
            target.
        resulting_tool: The tool-authored probe map just written to the
            org. Used as the source of truth (name/target/type/
            aggressiveness) to push into each chosen site. Each probe's
            ``vlan_ids`` is replaced with the freshly-prompted list.
        sources: The ``(probes, cenr)`` tuple from ``_load_probe_sources``.
            Passed through to ``_apply_to_site`` so per-region Samsung
            ELM probes can be built from the same source-of-truth
            catalogue.
        warned_unmapped_codes: Load-time dedup set constructed in
            ``manage_org_synthetic_probes`` (1025-US2). Mutated in place
            by ``_emit_load_time_country_code_warning`` so a subsequent
            call in the same invocation would suppress duplicates.
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
    # NOTE(1025-US2): load-time country_code WARNING emission fires exactly
    # once here, immediately after the site list is materialised and
    # BEFORE per-site region resolution begins in ``_apply_to_site`` ->
    # ``_build_region_probes``. Emitting here (rather than per-site in the
    # resolver) collapses N warnings into 1 (or K, one per distinct
    # unmapped code) and satisfies FR-004 / FR-010 / SC-002.
    logging.info(  # Constitution VII: BEFORE the load-time country_code diff
        "computing load-time country_code unmapped set for %d sites",
        len(sites),
    )
    _emit_load_time_country_code_warning(  # single call site per invocation (FR-012)
        _compute_unmapped_country_codes(  # inner: set difference over frozen universes
            sites,  # the just-loaded site list
            _COUNTRY_CODE_TO_REGION,  # T020-extended region map
            _COUNTRY_CODE_INTENTIONAL_GAPS,  # T021 gap set (Antarctica and so on)
        ),
        warned_unmapped_codes,  # dedup state -- mutated in place
    )
    logging.debug(  # Constitution VII: AFTER the load-time emission
        "load-time country_code check complete; warned_unmapped_codes=%s",
        len(warned_unmapped_codes),
    )
    picked_sites = _prompt_site_indexes(sites)
    if not picked_sites:
        print("  No valid site indexes entered -- skipping site overrides.")
        return
    # Site overrides commonly target sites with distinct VLAN topology, so
    # re-prompt rather than silently reusing the org-scope list.
    print("  Enter the VLAN ids to apply to the selected sites' tests[] rows.")
    site_vlan_ids = _prompt_vlan_list()
    for site in picked_sites:
        _apply_to_site(mist_session, site, resulting_tool, site_vlan_ids, sources)


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
    return [s for s in sites if isinstance(s, dict) and s.get("id")]


def _sort_sites_for_picker(sites: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return ``sites`` sorted for the interactive index picker.

    Why:
        Extracted so the sort key is unit-testable in isolation and so
        the parent picker's cyclomatic complexity stays under the CI
        gate. Unnamed sites sink to the end (secondary key = 1) so the
        named entries operators actually think about lead the list;
        name comparison is case-folded so ``ACME`` and ``acme`` sort
        together. Id is the final tie-break to keep the ordering stable
        across invocations.

    Args:
        sites: Site dicts as returned by ``_list_org_sites``.

    Returns:
        A new list of site dicts sorted by (named-first, name-casefold,
        id). The input is not mutated.
    """
    return sorted(
        sites,
        key=lambda s: (
            0 if (s.get("name") or "").strip() else 1,
            (s.get("name") or "").casefold(),
            s.get("id") or "",
        ),
    )


def _pick_site_by_index(
    idx: int,
    sorted_sites: list[dict[str, Any]],
    picked_by_id: dict[str, dict[str, Any]],
) -> None:
    """Add ``sorted_sites[idx-1]`` to ``picked_by_id`` if the index is in range.

    Why:
        The bounds-check + id-guard + setdefault triad appeared three
        times in ``_prompt_site_indexes`` (single-int branch, range
        branch, ``all`` branch was similar). Deduplicating it into one
        helper keeps the picker's dispatch small and makes the "silently
        ignore garbage" behaviour uniform across all three input shapes.

    Args:
        idx: 1-based index into ``sorted_sites`` as typed by the operator.
        sorted_sites: The sorted site view (from ``_sort_sites_for_picker``).
        picked_by_id: Mutated in place -- new picks are added via
            ``setdefault`` so earlier entries win on duplicate ids and
            operator input order is preserved.
    """
    if idx < 1 or idx > len(sorted_sites):
        logging.warning("Ignoring out-of-range site index: %d", idx)
        return
    candidate = sorted_sites[idx - 1]
    site_id = candidate.get("id")
    if isinstance(site_id, str) and site_id:
        picked_by_id.setdefault(site_id, candidate)


def _expand_range_token(
    part: str,
    sorted_sites: list[dict[str, Any]],
    picked_by_id: dict[str, dict[str, Any]],
) -> None:
    """Parse a ``lo-hi`` range shorthand token and add each in-range index.

    Why:
        Isolates the two-int parse plus reversed-range guard so the
        parent picker stays under the CC gate. The parse uses ``part[1:]``
        so a leading ``-`` is treated as a negative int -- matching
        ``_validate_vlan_input``'s convention: the value will just fail
        the in-range check inside ``_pick_site_by_index``.

    Args:
        part: The raw comma-separated token (already stripped) that
            contains a ``-`` after the first character.
        sorted_sites: Sorted site view for the range to index into.
        picked_by_id: Mutated in place (see ``_pick_site_by_index``).
    """
    lo_raw, _, hi_raw = part[1:].partition("-")
    lo_raw = (part[0] + lo_raw).strip()
    hi_raw = hi_raw.strip()
    try:
        lo = int(lo_raw)
        hi = int(hi_raw)
    except ValueError:
        logging.warning("Ignoring unparseable site index range token: %r", part)
        return
    if lo > hi:
        logging.warning("Ignoring reversed site index range: %r", part)
        return
    for idx in range(lo, hi + 1):
        _pick_site_by_index(idx, sorted_sites, picked_by_id)


def _apply_picker_token(
    part: str,
    sorted_sites: list[dict[str, Any]],
    picked_by_id: dict[str, dict[str, Any]],
) -> None:
    """Route one operator-supplied token to the correct index-picker branch.

    Why:
        Consolidates the ``all`` / range / single-int dispatch so the
        parent function's body reduces to ``for part in parts:
        _apply_picker_token(...)``. Keeps all three token shapes in one
        auditable place and drops the picker's CC well under the gate.

    Args:
        part: Stripped, non-empty token from the comma-split raw input.
        sorted_sites: Sorted site view for indexing.
        picked_by_id: Mutated in place with any successful picks.
    """
    if part.lower() == "all":
        for candidate in sorted_sites:
            site_id = candidate.get("id")
            if isinstance(site_id, str) and site_id:
                picked_by_id.setdefault(site_id, candidate)
        return
    # Range shorthand like "3-6". Leading '-' is treated as a negative int
    # (out of range anyway), matching _validate_vlan_input's convention.
    if "-" in part[1:]:
        _expand_range_token(part, sorted_sites, picked_by_id)
        return
    try:
        idx = int(part)
    except ValueError:
        logging.warning("Ignoring non-numeric site index token: %r", part)
        return
    _pick_site_by_index(idx, sorted_sites, picked_by_id)


def _prompt_site_indexes(sites: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Display an indexed site table and return the site dicts the operator picks.

    Why:
        UUID entry proved error-prone in the field (operators pasted
        trailing whitespace, wrong-org UUIDs, or truncated ids). An
        indexed prompt eliminates that class of typo entirely and lets
        the operator eyeball site names before committing. The list is
        sorted by human-readable site name (case-insensitive) so the
        picker matches how operators think about their fleet. Unnamed
        sites sink to the bottom. Full site dicts are returned (not just
        ids) so downstream code can read per-site fields like
        ``country_code`` without a second API round-trip. Accepts range
        shorthand (``3-6`` expands to ``3,4,5,6``) and a literal
        ``all`` token (case-insensitive) that selects every listed site
        -- operators paste condensed lists and frequently want to push
        the override org-wide. Kept in its own helper so tests can
        patch ``input`` for this stage independently of the earlier
        y/N prompt.

    Args:
        sites: List of site dicts as returned by ``_list_org_sites``. The
            function sorts a local copy by name before display, so the
            caller's ordering is irrelevant.

    Returns:
        Deduplicated list of the full site dicts corresponding to valid
        1-based indexes (into the *sorted* view) supplied by the
        operator, preserving operator input order. Empty list if the
        operator supplied nothing or every entry was out of range /
        non-numeric.
    """
    print("  Available sites:")
    sorted_sites = _sort_sites_for_picker(sites)
    width = len(str(len(sorted_sites)))
    for idx, site in enumerate(sorted_sites, start=1):
        name = site.get("name") or "(unnamed)"
        site_id = site.get("id", "")
        print(f"    [{idx:>{width}}] {name}  ({site_id})")
    raw = input(
        "  Enter comma-separated site indexes (ranges ok e.g. 3-6, 'all' for every site), " "or leave blank to cancel: "
    )
    parts = [item.strip() for item in raw.split(",") if item.strip()]
    picked_by_id: dict[str, dict[str, Any]] = {}
    for part in parts:
        _apply_picker_token(part, sorted_sites, picked_by_id)
    return list(picked_by_id.values())


def _put_site_setting(mist_session: Any, site_id: str, body: dict[str, Any]) -> bool:
    """PUT ``body`` to ``updateSiteSettings`` and log/print any failure.

    Why:
        Extracted from :func:`_apply_to_site` so the outer function stays
        under Radon CC>10. Collapses the transport-error branch and the
        non-2xx status branch into one boolean so the caller has a single
        gate before the success-line print.

    Args:
        mist_session: Authenticated ``mistapi`` session.
        site_id: Site UUID string.
        body: Full site-setting payload to PUT.

    Returns:
        ``True`` when the API returned a 2xx status (or no ``status_code``
        attribute at all — same tolerance the inline code had); ``False``
        on any exception or non-2xx status. Errors are already printed and
        logged before returning.
    """
    try:
        put_response = _mist_site_setting.updateSiteSettings(mist_session, site_id, body)
    except Exception as err:  # noqa: BLE001 -- surface any transport error.
        print(f"  Site {site_id}: updateSiteSettings failed ({err}); skipping.")
        logging.error("updateSiteSettings(%s) failed: %s", site_id, err)
        return False
    status = getattr(put_response, "status_code", None)
    if status is not None and not 200 <= status < 300:
        print(f"  Site {site_id}: updateSiteSettings HTTP {status}")
        logging.error("updateSiteSettings(%s) HTTP %s", site_id, status)
        return False
    return True


def _fetch_site_setting(mist_session: Any, site_id: str) -> dict[str, Any] | None:
    """Return the parsed site-setting dict, or ``None`` on transport failure.

    Why:
        Extracted from :func:`_apply_to_site` so the outer function stays
        under Radon CC>10. Prints and logs the same operator-visible
        message the inline handler used, then returns ``None`` so the
        caller can skip the site without another exception branch.

    Args:
        mist_session: Authenticated ``mistapi`` session.
        site_id: Site UUID string, already validated non-empty by caller.

    Returns:
        The ``response.data`` dict (empty dict when the API returned a
        non-dict payload) or ``None`` on any transport error.
    """
    try:
        response = _mist_site_setting.getSiteSetting(mist_session, site_id)
    except Exception as err:  # noqa: BLE001 -- surface any transport error.
        print(f"  Site {site_id}: getSiteSetting failed ({err}); skipping.")
        logging.error("getSiteSetting(%s) failed: %s", site_id, err)
        return None
    data = getattr(response, "data", None)
    return data if isinstance(data, dict) else {}


def _apply_to_site(
    mist_session: Any,
    site: dict[str, Any],
    tool_probes: dict[str, dict[str, Any]],
    vlan_ids: list[int],
    sources: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    """PUT ``tool_probes`` plus regional Samsung ELM probes into the site.

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
        probes so the site's schedule actually runs them. On top of the
        org-scope tool set, the region-scoped Samsung ELM probes for the
        site's ``country_code`` are injected here (only) so a site in
        Germany gets EMEA ELM endpoints while a site in the US gets the
        Americas set -- these regional roles never appear at org scope
        because pushing every region's endpoints everywhere is wasteful.
        Additionally, the ``tunnel_zen`` role's ~190 probe definitions
        (already emitted at org scope) are selectively SCHEDULED here per
        site: the geodesically-nearest 1-2 ZEN locations for the site's
        country/latlng get explicit ``tests[]`` rows so operators see
        reachability signal only for ZENs their users would actually route
        to, not the entire global ZEN mesh.

    Args:
        mist_session: Authenticated ``mistapi`` session.
        site: The full site dict from ``_list_org_sites`` -- ``id`` is
            required for the PUT, ``country_code`` (may be absent) drives
            regional ELM probe selection.
        tool_probes: Tool-authored probe set to write.
        vlan_ids: VLAN ids to attach to each generated test row.
        sources: The ``(probes, cenr)`` tuple from ``_load_probe_sources``,
            passed to ``_build_region_probes`` so region roles are read
            from the same source-of-truth catalogue.
    """
    site_id = site.get("id")
    if not isinstance(site_id, str) or not site_id:
        logging.error("Site override skipped: site dict missing id (%r)", site)
        return
    country_code = site.get("country_code")
    logging.info(
        "Applying site override to site_id=%s country_code=%r",
        site_id,
        country_code,
    )
    region_probes = _build_region_probes(sources, country_code)
    zen_probe_names = _zen_probe_names_for_cities(
        _resolve_zen_cities_for_site(site, sources[1]),
        sources[1],
    )
    site_setting = _fetch_site_setting(mist_session, site_id)
    if site_setting is None:
        return
    existing_probes = _detect_existing(site_setting)
    _, foreign = _partition_tool_authored(existing_probes)
    foreign_demoted = _demote_stale_critical(foreign)
    combined = {**foreign_demoted, **tool_probes, **region_probes}

    body: dict[str, Any] = json.loads(json.dumps(site_setting)) if site_setting else {}
    synthetic = body.get("synthetic_test")
    if not isinstance(synthetic, dict):
        synthetic = {}
        body["synthetic_test"] = synthetic
    synthetic["custom_probes"] = combined
    existing_tests = synthetic.get("tests")
    if not isinstance(existing_tests, list):
        existing_tests = []
    # Region and ZEN probes are auto-priority, so the default critical-only
    # filter would not schedule them. Pass their names explicitly so each
    # gets a tests[] row and actually runs.
    synthetic["tests"] = _merge_zcc_criticals_into_tests(
        existing_tests,
        combined,
        vlan_ids,
        extra_regular_names=[*region_probes.keys(), *zen_probe_names],
    )

    logging.debug(
        "Calling updateSiteSettings(site_id=%s, probe_count=%d)",
        site_id,
        len(combined),
    )
    if not _put_site_setting(mist_session, site_id, body):
        return
    print(
        f"  Site {site_id}: override applied "
        f"({len(tool_probes)} tool-authored + {len(region_probes)} regional "
        f"+ {len(zen_probe_names)} ZEN scheduled "
        f"+ {len(foreign_demoted)} preserved)"
    )

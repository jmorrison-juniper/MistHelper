# pylint: disable=too-many-lines,logging-fstring-interpolation,implicit-str-concat
"""Address parsing, normalization, and geocoding validation utilities.

Extracted from MistHelper.py monolith. Contains:
- AddressValidationConfig: Configuration dataclass for NominatimValidator.
- AddressUtils: Static address normalization, parsing, and comparison.
- NameNormalizationUtils: Business/org name normalization helpers.
- NominatimValidator: Geocoding-based address validation via Nominatim API.
"""

from __future__ import annotations  # WHY: postponed evaluation keeps forward refs / union syntax cheap

import difflib  # WHY: SequenceMatcher fallback when rapidfuzz is unavailable
import logging  # WHY: structured debug/trace output for parse + geocode diagnostics
import re  # WHY: regex normalization of addresses, zip codes, and business suffixes
import time  # WHY: rate-limit + retry backoff around Nominatim API calls
import traceback  # WHY: capture exception context in geocode debug logs
import unicodedata  # WHY: NFKD normalization strips diacritics before comparison
from collections.abc import Callable  # WHY: Any for opaque JSON payloads. Callable for dispatch map
from dataclasses import dataclass, field  # WHY: config + address/skip bundling for STRUCT-PARAMS compliance
from difflib import SequenceMatcher  # WHY: string-ratio helper used by org-name similarity
from typing import Any

try:  # WHY: HTTP client is optional so the module imports on minimal installs
    import requests  # WHY: bound at module scope for patch-friendliness in tests
except ImportError:  # pragma: no cover  # WHY: fall through to None on stripped envs
    requests = None  # type: ignore[assignment]  # WHY: sentinel checked before every HTTP call

try:  # WHY: urllib3 is only needed for SSL-warning suppression
    import urllib3  # WHY: bound so patches in tests can intercept disable_warnings

    _has_urllib3 = True  # WHY: gate SSL-warning suppression on real presence
except ImportError:  # pragma: no cover  # WHY: absence is non-fatal
    urllib3 = None  # type: ignore[assignment]  # WHY: sentinel checked before disabling warnings
    _has_urllib3 = False  # WHY: skip suppression path when the module is missing

from src.utils.tls_policy import TLSVerificationPolicy  # One control for certificate verification.

try:  # WHY: rapidfuzz is optional. Degrade to difflib on absence
    from rapidfuzz import fuzz  # WHY: faster token-sort ratio when available
except ImportError:  # pragma: no cover  # WHY: keep import graph optional
    fuzz = None  # type: ignore[assignment]  # WHY: sentinel checked before use

try:  # WHY: scourgify is optional. Heuristic parser handles the rest
    from scourgify import normalize_address_record  # WHY: high-quality USPS-style parse
except ImportError:  # pragma: no cover  # WHY: fall back to heuristic parser
    normalize_address_record = None  # WHY: sentinel checked before use


@dataclass
class AddressValidationConfig:
    """Configuration for address validation with Nominatim."""

    timeout: int = 5  # WHY: seconds per HTTP attempt. Retries add linear back-off
    debug: bool = False  # WHY: enables verbose parse + geocode logging
    skip_ssl_verify: bool = False  # WHY: internal MITM proxies sometimes need this
    org_name: str | None = None  # WHY: powers the org-name similarity tiebreaker
    site_name: str | None = None  # WHY: guards duplicate-key checks (must know which site)
    mist_duplicates: dict | None = None  # type: ignore[type-arg]  # WHY: pre-computed dup keys for Mist side
    ref_duplicates: dict | None = None  # type: ignore[type-arg]  # WHY: pre-computed dup keys for ref side


# ---------------------------------------------------------------------------
# Address / skip-entry bundles (collapse STRUCT-PARAMS for skip-check helpers)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _AddressFields:
    """Canonical 4-tuple of upper-cased address parts used by the skip checker."""

    address: str = ""  # WHY: primary street line, upper-cased for O(1) equality
    city: str = ""  # WHY: city component, upper-cased
    state: str = ""  # WHY: state/region, upper-cased (accepts abbr or full name)
    zip_code: str = ""  # WHY: postal code, upper-cased (avoid `zip` builtin shadow)

    def as_list(self) -> list[str]:  # WHY: many helpers still iterate positionally
        """Return the four fields in canonical order for positional consumers."""
        return [self.address, self.city, self.state, self.zip_code]  # WHY: stable order matches _count_field_matches


@dataclass(frozen=True)
class _SkipEntry:
    """A single skip-list entry: address fields plus a human reason."""

    fields: _AddressFields = field(default_factory=_AddressFields)  # WHY: reuse the address bundle for eq semantics
    reason: str = "Address in skip list"  # WHY: default reason keeps callers concise


def _comparison_fields_from_dict(address_dict: dict[str, Any]) -> _AddressFields:
    """Build an ``_AddressFields`` from a raw comparison-address dict."""
    return _AddressFields(  # WHY: normalize once at the boundary so downstream helpers stay pure
        address=str(address_dict.get("address", "")).strip().upper(),  # WHY: upper-case for direct equality
        city=str(address_dict.get("city", "")).strip().upper(),  # WHY: same normalization as skip entries
        state=str(address_dict.get("state", "")).strip().upper(),  # WHY: match skip-entry casing
        zip_code=str(address_dict.get("zip", "")).strip().upper(),  # WHY: preserve dashes for 9-digit ZIPs
    )


def _skip_entry_from_dict(raw: dict[str, Any]) -> _SkipEntry:
    """Build a ``_SkipEntry`` from a raw skip-list row dict."""
    fields = _AddressFields(  # WHY: same normalization as comparison side keeps eq honest
        address=str(raw.get("Skip_Address", "")).strip().upper(),  # WHY: skip-file column
        city=str(raw.get("Skip_City", "")).strip().upper(),  # WHY: skip-file column
        state=str(raw.get("Skip_State", "")).strip().upper(),  # WHY: skip-file column
        zip_code=str(raw.get("Skip_Zip", "")).strip().upper(),  # WHY: skip-file column
    )
    reason = raw.get("Reason", "Address in skip list")  # WHY: preserve caller-provided reason
    return _SkipEntry(fields=fields, reason=reason)  # WHY: bundle fields + reason for downstream


# ---------------------------------------------------------------------------
# US country aliases (frozenset -> O(1) membership, drops _detect_country CC)
# ---------------------------------------------------------------------------
_US_COUNTRY_ALIASES: frozenset[str] = frozenset(  # WHY: shared alias set for country detection
    {
        "usa",  # WHY: common short form
        "united states",  # WHY: common long form
        "united states of america",  # WHY: formal long form
        "us",  # WHY: two-letter code appearing as full country token
        "puerto rico",  # WHY: US territory shows up as country in some feeds
        "pr",  # WHY: PR abbreviation appearing as country token
    }
)


# ---------------------------------------------------------------------------
# Placeholder tokens treated as "unknown" input (drops _unparseable_reason CC)
# ---------------------------------------------------------------------------
_PLACEHOLDER_ADDRESS_TOKENS: frozenset[str] = frozenset(  # WHY: sentinel strings that mean 'no address'
    {"unknown", "n/a", "na", "none", "null", ""}  # WHY: covers common vendor placeholders
)


# ---------------------------------------------------------------------------
# State name <-> abbreviation mapping (US states + DC)
# ---------------------------------------------------------------------------
_STATE_MAPPING: dict[str, str] = {
    "alabama": "al",
    "alaska": "ak",
    "arizona": "az",
    "arkansas": "ar",
    "california": "ca",
    "colorado": "co",
    "connecticut": "ct",
    "delaware": "de",
    "florida": "fl",
    "georgia": "ga",
    "hawaii": "hi",
    "idaho": "id",
    "illinois": "il",
    "indiana": "in",
    "iowa": "ia",
    "kansas": "ks",
    "kentucky": "ky",
    "louisiana": "la",
    "maine": "me",
    "maryland": "md",
    "massachusetts": "ma",
    "michigan": "mi",
    "minnesota": "mn",
    "mississippi": "ms",
    "missouri": "mo",
    "montana": "mt",
    "nebraska": "ne",
    "nevada": "nv",
    "new hampshire": "nh",
    "new jersey": "nj",
    "new mexico": "nm",
    "new york": "ny",
    "north carolina": "nc",
    "north dakota": "nd",
    "ohio": "oh",
    "oklahoma": "ok",
    "oregon": "or",
    "pennsylvania": "pa",
    "rhode island": "ri",
    "south carolina": "sc",
    "south dakota": "sd",
    "tennessee": "tn",
    "texas": "tx",
    "utah": "ut",
    "vermont": "vt",
    "virginia": "va",
    "washington": "wa",
    "west virginia": "wv",
    "wisconsin": "wi",
    "wyoming": "wy",
    "district of columbia": "dc",
    # Abbreviations map to themselves (idempotent lookup)
    "al": "al",
    "ak": "ak",
    "az": "az",
    "ar": "ar",
    "ca": "ca",
    "co": "co",
    "ct": "ct",
    "de": "de",
    "fl": "fl",
    "ga": "ga",
    "hi": "hi",
    "id": "id",
    "il": "il",
    "in": "in",
    "ia": "ia",
    "ks": "ks",
    "ky": "ky",
    "la": "la",
    "me": "me",
    "md": "md",
    "ma": "ma",
    "mi": "mi",
    "mn": "mn",
    "ms": "ms",
    "mo": "mo",
    "mt": "mt",
    "ne": "ne",
    "nv": "nv",
    "nh": "nh",
    "nj": "nj",
    "nm": "nm",
    "ny": "ny",
    "nc": "nc",
    "nd": "nd",
    "oh": "oh",
    "ok": "ok",
    "or": "or",
    "pa": "pa",
    "ri": "ri",
    "sc": "sc",
    "sd": "sd",
    "tn": "tn",
    "tx": "tx",
    "ut": "ut",
    "vt": "vt",
    "va": "va",
    "wa": "wa",
    "wv": "wv",
    "wi": "wi",
    "wy": "wy",
    "dc": "dc",
}

# ---------------------------------------------------------------------------
# Common street address abbreviations
# ---------------------------------------------------------------------------
_ADDRESS_ABBREVIATIONS: dict[str, str] = {
    r"\bstreet\b": "st",
    r"\bst\b": "st",
    r"\bavenue\b": "ave",
    r"\bave\b": "ave",
    r"\bboulevard\b": "blvd",
    r"\bblvd\b": "blvd",
    r"\bbuilding\b": "bldg",
    r"\bsuite\b": "ste",
    r"\bnorth\b": "n",
    r"\bsouth\b": "s",
    r"\beast\b": "e",
    r"\bwest\b": "w",
    r"\bdrive\b": "dr",
    r"\bdr\b": "dr",
    r"\broad\b": "rd",
    r"\brd\b": "rd",
    r"\blane\b": "ln",
    r"\bln\b": "ln",
    r"\bcourt\b": "ct",
    r"\bct\b": "ct",
    r"\bplace\b": "pl",
    r"\bpl\b": "pl",
    r"\bparkway\b": "pkwy",
    r"\bpkwy\b": "pkwy",
    r"\bhighway\b": "hwy",
    r"\bhwy\b": "hwy",
}


class AddressUtils:
    """Centralized address normalization and parsing utilities.

    All methods are static to avoid unnecessary object instantiation.
    """

    @staticmethod
    def normalize_zip(zip_code: Any) -> str:
        """Normalize a zip code to the first 5 digits."""
        if not zip_code:  # WHY: guard empty/None before any string manipulation
            return ""  # WHY: canonical empty return preserves comparability
        zip_str = str(zip_code).strip()  # WHY: coerce numeric inputs and trim padding
        if "-" in zip_str:  # WHY: drop the +4 suffix on 9-digit ZIPs
            zip_str = zip_str.split("-")[0]  # WHY: keep only the leading 5 digits
        zip_digits = "".join(filter(str.isdigit, zip_str))  # WHY: strip stray whitespace/letters
        if len(zip_digits) == 4:  # WHY: some feeds drop the leading zero on East-Coast ZIPs
            zip_digits = "0" + zip_digits  # WHY: restore canonical 5-digit form
        return zip_digits[:5]  # WHY: bound to the first 5 digits regardless of input length

    @staticmethod
    def _normalize_state(state_str: Any) -> str:
        """Normalize state names/abbreviations to lowercase abbreviation."""
        if not state_str:  # WHY: empty/None input maps to empty output
            return ""  # WHY: canonical empty avoids downstream KeyError
        state: str = str(state_str).lower().strip()  # WHY: dict keys are lowercased for case-insensitive lookup
        return str(_STATE_MAPPING.get(state, state))  # WHY: unknown states pass through unchanged

    @staticmethod
    def _normalize_address(address_str: Any) -> str:
        """Normalize an address string for comparison."""
        if not address_str:  # WHY: guard empty input before regex work
            return ""  # WHY: empty stays empty in the similarity math
        normalized: str = str(unicodedata.normalize("NFKD", address_str))  # WHY: decompose diacritics for match
        normalized = normalized.casefold().strip()  # WHY: casefold beats lower() for i18n text
        normalized = re.sub(r"\s+", " ", normalized)  # WHY: collapse repeated whitespace
        for full_form, abbrev in _ADDRESS_ABBREVIATIONS.items():  # WHY: canonicalize suffix words
            normalized = re.sub(full_form, abbrev, normalized)  # WHY: turn "street" -> "st" and so on
        normalized = re.sub(r"[^\w\s]", " ", normalized)  # WHY: drop punctuation before token compare
        normalized = " ".join(normalized.split())  # WHY: re-collapse whitespace introduced by punct strip
        return normalized  # WHY: fully-normalized address string ready for similarity

    @staticmethod
    def _parse_components(
        address_string: str | None,
        debug: bool = False,
    ) -> dict[str, Any]:
        """Parse address components with defensive heuristics."""
        if debug:  # WHY: trace the raw input when debugging the parser
            logging.debug("PARSE_ADDRESS: Input: '%s'", address_string)
        result = AddressUtils._empty_parse_result(address_string)  # WHY: base result skeleton (all fields unset)
        reason = AddressUtils._unparseable_reason(address_string)  # WHY: detect empty/placeholder input early
        if reason:  # WHY: known-unparseable input short-circuits
            result["parse_reason"] = reason  # WHY: record why we bailed
            return result  # WHY: no further parsing attempted
        cleaned_input = str(address_string).strip()  # WHY: normalized input for the heuristic parser
        try:  # WHY: the heuristic parser can raise on pathological input
            return _parse_address_parts(cleaned_input, result, debug)  # WHY: main heuristic path
        except Exception as exception:  # WHY: record the failure reason instead of propagating
            result["parse_reason"] = f"exception: {exception!s}"  # WHY: expose the reason to callers
            if debug:  # WHY: surface the exception detail when debugging
                logging.warning("PARSE_ADDRESS: Exception during parsing: %s", exception)
            return result  # WHY: degrade gracefully with the empty skeleton

    @staticmethod
    def _empty_parse_result(address_string: str | None) -> dict[str, Any]:
        """Return the base (all-unset) parsed-address result skeleton."""
        return {  # WHY: every field starts unset. Parser fills them on success
            "address": None,  # WHY: street line, None until parsed
            "city": None,  # WHY: city component, None until parsed
            "state": None,  # WHY: state/region, None until parsed
            "zip": None,  # WHY: postal code, None until parsed
            "country": None,  # WHY: country, None until parsed
            "is_parseable": False,  # WHY: caller checks this flag
            "parse_reason": "unparsed",  # WHY: default reason before any attempt
            "original": address_string or "",  # WHY: retain the raw input for debugging
        }

    @staticmethod
    def _unparseable_reason(address_string: str | None) -> str:
        """Return a parse_reason when the input is empty/placeholder, else an empty string."""
        if not address_string or not str(address_string).strip():  # WHY: blank/whitespace input
            return "empty_input"  # WHY: canonical reason for callers/tests
        if str(address_string).strip().lower() in _PLACEHOLDER_ADDRESS_TOKENS:  # WHY: placeholder tokens
            return "unknown_address"  # WHY: distinguish placeholder from truly empty
        return ""  # WHY: input looks parseable, no short-circuit

    @staticmethod
    def enhanced_parse(
        address_string: str | None,
        debug: bool = False,
    ) -> dict[str, Any]:
        """Enhanced address parsing using usaddress-scourgify with heuristic fallback."""
        if normalize_address_record is None:  # WHY: optional dependency missing -> heuristic parser
            if debug:  # WHY: trace the missing-dependency fallback
                logging.debug("USADDRESS_PARSE: usaddress-scourgify not available")
            return AddressUtils._parse_components(address_string, debug=debug)  # WHY: heuristic fallback path
        return AddressUtils._scourgify_parse(address_string, debug)  # WHY: library-backed parse with fallback

    @staticmethod
    def _scourgify_parse(address_string: str | None, debug: bool) -> dict[str, Any]:
        """Parse via usaddress-scourgify, falling back to the heuristic parser on any error."""
        try:  # WHY: library parsing can raise on malformed input
            if debug:  # WHY: trace the parse attempt when debugging
                logging.debug("USADDRESS_PARSE: Attempting for: '%s'", address_string)
            parsed = normalize_address_record(address_string)  # WHY: normalize via the optional library
            return AddressUtils._build_scourgify_result(parsed, address_string)  # WHY: shape into result dict
        except Exception:  # nosec B110  # WHY: any library error degrades to the heuristic parser
            return AddressUtils._parse_components(address_string, debug=debug)  # WHY: heuristic fallback path

    @staticmethod
    def _build_scourgify_result(parsed: dict[str, Any], address_string: str | None) -> dict[str, Any]:
        """Shape a usaddress-scourgify record into the standard parsed-address result dict."""
        result: dict[str, Any] = {  # WHY: standard parsed-address shape consumed by callers
            "address": parsed.get("address_line_1", ""),  # WHY: primary line only
            "city": parsed.get("city", ""),  # WHY: city as parsed
            "state": parsed.get("state", ""),  # WHY: state as parsed
            "zip": parsed.get("postal_code", ""),  # WHY: postal code as parsed
            "country": "US",  # WHY: scourgify is US-only, so hard-code
            "is_parseable": True,  # WHY: library success implies parseable
            "parse_reason": "usaddress_success",  # WHY: label the successful branch
            "original": address_string or "",  # WHY: retain the raw input
        }
        if parsed.get("address_line_2"):  # WHY: join lines only when line 2 exists
            parts = [parsed.get("address_line_1", ""), parsed.get("address_line_2", "")]  # WHY: two-line container
            result["address"] = " ".join(p for p in parts if p)  # WHY: drop empty parts when joining
        return result  # WHY: completed parsed-address record

    @staticmethod
    def _calculate_similarity(str1: Any, str2: Any) -> float:
        """Calculate similarity percentage between two strings."""
        if not str1 and not str2:  # WHY: two empties are perfectly similar by convention
            return 100.0  # WHY: match callers' expectation for empty-vs-empty
        if not str1 or not str2:  # WHY: exactly one empty means no similarity
            return 0.0  # WHY: canonical zero for mismatched-population inputs
        norm1 = AddressUtils._normalize_address(str1)  # WHY: shared normalization for comparability
        norm2 = AddressUtils._normalize_address(str2)  # WHY: apply the same normalizer to both sides
        return AddressUtils._fuzz_or_seq_ratio(norm1, norm2)  # WHY: delegate to keep CC below the gate

    @staticmethod
    def _fuzz_or_seq_ratio(norm1: str, norm2: str) -> float:
        """Return a 0-100 similarity ratio using rapidfuzz when available."""
        if fuzz is not None:  # WHY: rapidfuzz path is preferred when installed
            try:  # WHY: fuzz can throw on odd unicode
                return float(fuzz.token_sort_ratio(norm1, norm2))  # WHY: rapidfuzz already returns 0-100
            except Exception:  # nosec B110  # WHY: on any fuzz failure, fall through to SequenceMatcher
                pass  # WHY: intentional silent fall-through to the difflib path
        return difflib.SequenceMatcher(None, norm1, norm2).ratio() * 100  # WHY: fallback ratio scaled to 0-100

    @staticmethod
    def check_should_skip(
        comparison_address: dict[str, Any],
        skip_addresses: list[dict[str, Any]],
        debug: bool = False,
    ) -> tuple[bool, str]:
        """Check if a comparison address should be skipped."""
        if not skip_addresses:  # WHY: empty skip list -> always False
            return False, ""  # WHY: canonical no-skip response
        comp = _comparison_fields_from_dict(comparison_address)  # WHY: normalize once at the boundary
        for raw_entry in skip_addresses:  # WHY: linear search over skip list
            skip = _skip_entry_from_dict(raw_entry)  # WHY: normalize each entry to the shared type
            should_skip, reason = _check_single_skip(comp, skip, debug)  # WHY: unified per-entry check
            if should_skip:  # WHY: first match wins
                return True, reason  # WHY: propagate the reason string
        return False, ""  # WHY: no skip entry matched

    @staticmethod
    def compare_with_threshold(
        mist_address: dict[str, Any],
        comparison_address: dict[str, Any],
        threshold: float,
        debug: bool = False,
    ) -> dict[str, Any]:
        """Enhanced address comparison with similarity metrics."""
        field_weights = {"address": 0.4, "city": 0.3, "state": 0.2, "zip": 0.1}  # WHY: per-field similarity weights
        parse_status = _check_parse_status(mist_address, comparison_address, field_weights)  # WHY: parseability check
        if not parse_status["mist_parseable"] or not parse_status["comparison_parseable"]:  # WHY: unparseable input
            if debug:  # WHY: trace the unparseable short-circuit
                logging.debug("ENHANCED_COMPARE: Unparseable: %s", parse_status)
            return AddressUtils._unparseable_comparison_result(  # WHY: zero-similarity result
                field_weights, parse_status
            )
        similarities, failed = _compare_fields(mist_address, comparison_address, field_weights, threshold, debug)
        overall = sum(similarities[f] * field_weights[f] for f in field_weights)  # WHY: weighted overall similarity
        return {  # WHY: full comparison result with score and per-field detail
            "overall_similarity": overall,  # WHY: weighted score across all fields
            "is_match": overall >= threshold,  # WHY: threshold gate for callers
            "field_similarities": similarities,  # WHY: raw per-field ratios
            "failed_fields": failed,  # WHY: fields below 75% of threshold
            "parse_status": parse_status,  # WHY: keep parse detail for debugging
        }

    @staticmethod
    def _unparseable_comparison_result(
        field_weights: dict[str, float],
        parse_status: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the zero-similarity result returned when either address is unparseable."""
        return {  # WHY: mark every field as failed since no meaningful comparison is possible
            "overall_similarity": 0.0,  # WHY: canonical zero for unparseable pairs
            "is_match": False,  # WHY: never a match when either side is unparseable
            "field_similarities": {f: 0.0 for f in field_weights},  # WHY: all fields zero
            "failed_fields": list(field_weights),  # WHY: every field considered failed
            "parse_status": parse_status,  # WHY: retain reason for callers
        }

    @staticmethod
    def _classify_place_type(place_type: str) -> tuple[bool, bool]:
        """Classify a place type as (is_business, is_residential)."""
        business_types = ["commercial", "office", "retail", "building", "shop", "store"]  # WHY: OSM biz tags
        residential_types = ["house", "residential", "apartment"]  # WHY: OSM residential tags
        place_lower = place_type.lower()  # WHY: single lowercase for repeated substring checks
        is_biz = any(t in place_lower for t in business_types)  # WHY: any biz token match wins
        is_res = any(t in place_lower for t in residential_types)  # WHY: any residential token match wins
        return is_biz, is_res  # WHY: tuple lets callers do combined tiebreaks

    @staticmethod
    def apply_business_context_rules(
        mist_result: dict[str, Any],
        comparison_result: dict[str, Any],  # WHY: no caller ever passed a debug flag, so the parameter went
    ) -> str:
        """Apply business context rules for address tiebreaking."""
        mist_biz, mist_res = AddressUtils._classify_place_type(mist_result.get("place_type", ""))  # WHY: mist tags
        comp_place = comparison_result.get("place_type", "")  # WHY: cache to shorten next call
        comp_biz, comp_res = AddressUtils._classify_place_type(comp_place)  # WHY: comp tags
        if mist_biz and comp_res:  # WHY: mist is biz + comp is home -> prefer mist
            return "mist"  # WHY: biz side wins on residential tiebreak
        if comp_biz and mist_res:  # WHY: comp is biz + mist is home -> prefer comp
            return "comparison"  # WHY: biz side wins the other direction too
        return AddressUtils._confidence_recommendation(  # WHY: fall through to confidence tiebreak
            mist_result["confidence"],  # WHY: mist confidence score
            comparison_result["confidence"],  # WHY: comparison confidence score
        )

    @staticmethod
    def _confidence_recommendation(mist_conf: float, comp_conf: float) -> str:
        """Return recommendation based on a 5%% confidence delta, else 'uncertain'."""
        if abs(mist_conf - comp_conf) <= 0.05:  # WHY: near-tie -> caller needs another tiebreaker
            return "uncertain"  # WHY: refuse to decide within the noise band
        return "mist" if mist_conf > comp_conf else "comparison"  # WHY: pick the higher-confidence side


# ---------------------------------------------------------------------------
# Private helpers for AddressUtils (keep CC low)
# ---------------------------------------------------------------------------


def _peel_last(parts: list[str], condition: Any) -> list[str]:
    """Return ``parts`` with the last element removed when ``condition`` is truthy."""
    return parts[:-1] if condition else parts  # WHY: single-expression helper drops one CC per caller


def _extract_address_components(
    parts: list[str],
) -> dict[str, str | None]:
    """Extract country, zip, state, city, address from comma-split parts."""
    remaining = list(parts)  # WHY: shallow copy so peeling does not mutate caller data
    country = _detect_country(remaining)  # WHY: right-to-left peel starts with country
    remaining = _peel_last(remaining, country)  # WHY: drop country token when detected
    zip_code, country = _detect_zip(remaining, country)  # WHY: ZIP may imply country when absent
    remaining = _peel_last(remaining, zip_code)  # WHY: drop ZIP token when detected
    state = _detect_state(remaining)  # WHY: next-outermost token is the state
    remaining = _peel_last(remaining, state)  # WHY: drop state token when detected
    city = remaining[-1].strip() if remaining else None  # WHY: city is the next inner token
    remaining = _peel_last(remaining, city)  # WHY: drop city token when detected
    address = ", ".join(remaining).strip() if remaining else None  # WHY: rejoin whatever's left as street line
    return {  # WHY: canonical parsed-component shape
        "address": address,  # WHY: street line
        "city": city,  # WHY: city
        "state": state,  # WHY: state/region
        "zip": zip_code,  # WHY: postal code
        "country": country,  # WHY: country
    }


def _parse_address_parts(
    cleaned_input: str,
    result: dict[str, Any],
    debug: bool,
) -> dict[str, Any]:
    """Inner parser for _parse_components (extracted for CC reduction)."""
    normalized = unicodedata.normalize("NFKD", cleaned_input)  # WHY: strip diacritics before splitting
    parts = [p.strip() for p in normalized.split(",") if p.strip()]  # WHY: comma-delimited tokens
    if not parts:  # WHY: nothing to peel means unparseable
        result["parse_reason"] = "no_parts_after_cleaning"  # WHY: label the empty-parts case
        return result  # WHY: bail with the skeleton unchanged
    components = _extract_address_components(parts)  # WHY: right-to-left peel of country/zip/state/city
    result.update(components)  # WHY: merge components into the caller's skeleton
    result["is_parseable"] = True  # WHY: successful parse
    result["parse_reason"] = "success"  # WHY: label the success branch
    if debug:  # WHY: trace parsed result when debugging
        logging.debug("PARSE_ADDRESS: Parsed result: %s", result)
    return result  # WHY: fully-populated parse result


def _detect_country(parts: list[str]) -> str | None:
    """Detect country from last address token."""
    if not parts:  # WHY: empty parts -> no country to detect
        return None  # WHY: canonical no-country marker
    last = parts[-1].strip().lower()  # WHY: lowercase once for set membership
    if last in _US_COUNTRY_ALIASES:  # WHY: single O(1) check replaces prior 4-branch cascade
        return "US"  # WHY: canonical two-letter US code
    if len(last) == 2 and last.isalpha():  # WHY: bare 2-letter alpha token treated as country code
        return last.upper()  # WHY: return uppercased ISO-style code
    return None  # WHY: unknown token -> not a country


def _detect_zip(
    parts: list[str],
    country: str | None,
) -> tuple[str | None, str | None]:
    """Detect ZIP/postal code from remaining parts."""
    if not parts:  # WHY: nothing to inspect
        return None, country  # WHY: preserve caller's existing country hint
    last = parts[-1].strip()  # WHY: last part is the candidate ZIP
    if re.match(r"^\d{5}(-?\d{4})?$", last):  # WHY: 5-digit or 5+4 US ZIP pattern
        if not country:  # WHY: ZIP implies US when no country hint yet
            country = "US"  # WHY: default country when ZIP matches US pattern
        return last, country  # WHY: return the detected ZIP alongside (possibly-updated) country
    return None, country  # WHY: no ZIP match, keep existing country hint


def _detect_state(parts: list[str]) -> str | None:
    """Detect US state from remaining parts."""
    if not parts:  # WHY: nothing to inspect
        return None  # WHY: canonical no-state marker
    last = parts[-1].strip().lower()  # WHY: normalize once
    literal = _state_literal(last)  # WHY: try direct literal (PR / 2-letter) match first
    if literal is not None:  # WHY: literal hit wins over the mapping lookup
        return literal  # WHY: return uppercased literal code
    return _normalize_multipart_state(last, parts)  # WHY: full-name path only when multiple parts remain


def _state_literal(last: str) -> str | None:
    """Return 'PR' or a 2-letter code when ``last`` is a direct state literal."""
    if last == "puerto rico":  # WHY: PR is a US territory but treated as state token
        return "PR"  # WHY: canonical PR marker
    if len(last) <= 2 and last.isalpha():  # WHY: 1- or 2-letter alpha token is a state abbr
        return last.upper()  # WHY: uppercase the abbreviation
    return None  # WHY: not a direct literal


def _normalize_multipart_state(last: str, parts: list[str]) -> str | None:
    """Normalize a full-name state token only when there are multiple parts."""
    if len(parts) <= 1:  # WHY: single-part input is more likely a city than a state
        return None  # WHY: avoid mislabeling "California" as state when it is the only token
    normalized = AddressUtils._normalize_state(last)  # WHY: map full name to abbreviation
    return normalized.upper() if normalized else None  # WHY: canonical uppercase abbr


def _check_single_skip(
    comp: _AddressFields,
    skip: _SkipEntry,
    debug: bool,
) -> tuple[bool, str]:
    """Check one skip entry against comparison address."""
    if comp == skip.fields:  # WHY: dataclass equality replaces 4 explicit field compares
        if debug:  # WHY: trace exact-match skips when debugging
            logging.debug("ADDRESS_SKIP: Exact match - %s", comp.address)
        return True, skip.reason  # WHY: exact hit wins
    return _check_partial_skip(comp, skip, debug)  # WHY: try partial/wildcard match next


def _count_field_matches(
    comp_fields: list[str],
    skip_fields: list[str],
) -> int:
    """Count how many non-empty skip fields match comparison fields."""
    return sum(  # WHY: sum booleans. Only non-empty skip fields with equal comp count
        bool(skip_val and comp_val == skip_val)  # WHY: skip field must be populated to count
        for comp_val, skip_val in zip(comp_fields, skip_fields, strict=True)  # WHY: strict=True catches shape drift
    )


def _count_populated(fields: list[str]) -> int:
    """Return the count of truthy fields in ``fields``."""
    return sum(1 for f in fields if f)  # WHY: 'if f' filters out empty strings cheaply


def _is_sufficient_match(
    matching: int,
    skip_fields: list[str],
) -> bool:
    """Determine if matching field count warrants a skip."""
    populated = _count_populated(skip_fields)  # WHY: how many skip fields carry a real value
    if populated == 1 and matching == 1:  # WHY: single-field wildcard entries skip on that one match
        return True  # WHY: honor the wildcard intent
    return populated >= 2 and matching >= max(2, populated // 2)  # WHY: half-majority rule for multi-field skips


def _check_partial_skip(
    comp: _AddressFields,
    skip: _SkipEntry,
    debug: bool,
) -> tuple[bool, str]:
    """Check partial/wildcard skip match."""
    comp_list = comp.as_list()  # WHY: cache positional views for the counter
    skip_list = skip.fields.as_list()  # WHY: paired with comp_list by _count_field_matches
    matching = _count_field_matches(comp_list, skip_list)  # WHY: how many positions equal-match
    if matching == 0:  # WHY: no field matched at all
        return False, ""  # WHY: nothing to skip
    if _is_sufficient_match(matching, skip_list):  # WHY: apply the wildcard/majority policy
        if debug:  # WHY: trace partial-match skips when debugging
            logging.debug("ADDRESS_SKIP: Partial match - %s", comp.address)
        return True, skip.reason  # WHY: sufficient match -> skip with the entry's reason
    return False, ""  # WHY: match count did not clear the sufficiency bar


def _check_parse_status(
    mist_address: dict[str, Any],
    comparison_address: dict[str, Any],
    field_weights: dict[str, float],
) -> dict[str, Any]:
    """Check if addresses are parseable."""
    status: dict[str, Any] = {  # WHY: default both sides parseable. Downgrade on placeholder tokens
        "mist_parseable": True,  # WHY: assume valid until proven otherwise
        "comparison_parseable": True,  # WHY: assume valid until proven otherwise
        "mist_reason": "valid",  # WHY: default status label
        "comparison_reason": "valid",  # WHY: default status label
    }
    unparseable = {"unknown", "n/a", "na", "none", "null", ""}  # WHY: placeholder tokens shared with parser
    for field_name in field_weights:  # WHY: probe each weighted field
        mist_val = str(mist_address.get(field_name, "")).strip().lower()  # WHY: normalize for set membership
        comp_val = str(comparison_address.get(field_name, "")).strip().lower()  # WHY: normalize for set membership
        if mist_val in unparseable:  # WHY: any placeholder token disqualifies the mist side
            status["mist_parseable"] = False  # WHY: mark mist unparseable
            status["mist_reason"] = "unknown_address"  # WHY: label the reason
        if comp_val in unparseable:  # WHY: any placeholder token disqualifies the comp side
            status["comparison_parseable"] = False  # WHY: mark comp unparseable
            status["comparison_reason"] = "unknown_address"  # WHY: label the reason
    return status  # WHY: full status dict for the caller to gate on


def _compare_fields(
    mist_address: dict[str, Any],
    comparison_address: dict[str, Any],
    field_weights: dict[str, float],
    threshold: float,
    debug: bool,
) -> tuple[dict[str, float], list[str]]:
    """Compare address fields and return similarities + failed fields."""
    similarities: dict[str, float] = {}  # WHY: per-field 0-100 scores
    failed: list[str] = []  # WHY: fields below 75% of threshold
    for field_name in field_weights:  # WHY: honor caller's field order
        mist_val = str(mist_address.get(field_name, "")).strip()  # WHY: coerce+trim
        comp_val = str(comparison_address.get(field_name, "")).strip()  # WHY: coerce+trim
        similarity = _compare_single_field(field_name, mist_val, comp_val)  # WHY: field-specific comparison
        similarities[field_name] = similarity  # WHY: record for weighted overall
        if similarity < threshold * 0.75:  # WHY: 75% of threshold flags as failed
            failed.append(field_name)  # WHY: track for caller diagnostics
        if debug:  # WHY: verbose trace when debugging comparisons
            logging.debug(
                "ENHANCED_COMPARE: %s similarity: %.1f%% (threshold: %.1f%%)",
                field_name,
                similarity,
                threshold * 0.75,
            )
    return similarities, failed  # WHY: pair result for compare_with_threshold


def _exact_match_score(a: str, b: str) -> float:
    """Return 100 when both normalized values are equal and non-empty, else 0."""
    return 100.0 if a and a == b else 0.0  # WHY: exact-match fields use binary scoring


# Dispatch table: fields that use exact-match scoring after normalization.
_EXACT_MATCH_NORMALIZERS: dict[str, Callable[[Any], str]] = {  # WHY: lookup replaces if/elif cascade in comparator
    "zip": AddressUtils.normalize_zip,  # WHY: 5-digit ZIP normalization then equality
    "state": AddressUtils._normalize_state,  # WHY: state-name/abbr normalization then equality
}


def _compare_single_field(field_name: str, mist_val: str, comp_val: str) -> float:
    """Compare a single address field."""
    normalizer = _EXACT_MATCH_NORMALIZERS.get(field_name)  # WHY: dispatch on field name
    if normalizer is None:  # WHY: address/city use fuzzy similarity
        return AddressUtils._calculate_similarity(mist_val, comp_val)  # WHY: string-similarity path
    return _exact_match_score(normalizer(mist_val), normalizer(comp_val))  # WHY: normalized exact-match path


# ============================================================================
# NAME NORMALIZATION UTILITIES
# ============================================================================


class NameNormalizationUtils:
    """General name and token normalization helpers.

    Used for business/org name cleaning and similarity calculation.
    """

    BUSINESS_SUFFIX_PATTERNS = [  # WHY: common business-entity suffixes to strip before matching
        r"\binc\.?$",
        r"\bincorporated$",
        r"\bllc\.?$",
        r"\bcorp\.?$",
        r"\bcorporation$",
        r"\bltd\.?$",
        r"\blimited$",
        r"\bco\.?$",
        r"\bcompany$",
        r"\benterprise$",
        r"\benterprises$",
        r"\bgroup$",
        r"\bholdings$",
        r"\bassociates$",
        r"\bpartners$",
        r"\b& co\.?$",
        r"\b&co\.?$",
    ]

    @staticmethod
    def normalize_business_name(business_name: str) -> str:
        """Strip business suffixes and normalize for comparison."""
        if not business_name:  # WHY: empty in, empty out
            return ""  # WHY: canonical empty
        normalized = business_name.lower().strip()  # WHY: case-insensitive baseline
        for suffix in NameNormalizationUtils.BUSINESS_SUFFIX_PATTERNS:  # WHY: strip each known suffix in turn
            normalized = re.sub(suffix, "", normalized).strip()  # WHY: trim any whitespace revealed by the strip
        normalized = re.sub(r"[^\w\s]", " ", normalized)  # WHY: turn punctuation into spaces
        normalized = re.sub(r"\s+", " ", normalized).strip()  # WHY: collapse whitespace runs
        return normalized  # WHY: normalized business name ready for similarity

    @staticmethod
    def normalize_generic(name: str) -> str:
        """Lightweight generic normalization."""
        if not name:  # WHY: empty in, empty out
            return ""  # WHY: canonical empty
        cleaned = unicodedata.normalize("NFKD", str(name)).casefold().strip()  # WHY: unicode-safe folded form
        return re.sub(r"\s+", " ", cleaned)  # WHY: collapse whitespace runs

    @staticmethod
    def extract_tokens(name: str) -> list[str]:
        """Return lowercase alphanumeric tokens for fuzzy pipelines."""
        if not name:  # WHY: empty input -> empty token list
            return []  # WHY: canonical empty
        return re.findall(r"[a-z0-9]+", NameNormalizationUtils.normalize_generic(name))  # WHY: alnum runs only

    @staticmethod
    def calculate_org_name_similarity(
        org_name: str,
        address_display: str,
    ) -> float:
        """Calculate similarity between org name and address display name."""
        if not org_name or not address_display:  # WHY: either side empty means no similarity
            return 0.0  # WHY: canonical zero
        org_words = set(org_name.split())  # WHY: word set for exact overlap ratio
        address_words = set(re.findall(r"\b\w+\b", address_display.lower()))  # WHY: extract words case-insensitively
        exact_matches = len(org_words.intersection(address_words))  # WHY: count word-level overlaps
        word_sim = (exact_matches / len(org_words)) if org_words else 0.0  # WHY: guard 0-div for empty org
        string_sim = SequenceMatcher(None, org_name, address_display).ratio()  # WHY: raw string ratio
        return min(1.0, (word_sim * 0.7) + (string_sim * 0.3))  # WHY: 70/30 blend, capped at 1.0


# ============================================================================
# NOMINATIM ADDRESS VALIDATOR
# ============================================================================


class NominatimValidator:
    """Validate addresses against Nominatim (OpenStreetMap) geocoding API.

    Compares two address sets (Mist vs reference) and recommends which is
    more accurate based on geocoding confidence, place types, and tiebreakers.
    """

    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"  # WHY: public search endpoint
    USER_AGENT = "MistHelper/1.0 (address validation)"  # WHY: Nominatim ToS requires a UA
    RATE_LIMIT_DELAY = 1.1  # WHY: 1 req/sec limit + buffer
    MAX_RETRIES = 2  # WHY: two extra attempts after initial failure
    RETRY_DELAY = 2  # WHY: seconds between retry attempts
    HIGH_QUALITY_TYPES = ["house", "building", "commercial", "office", "retail", "shop"]  # WHY: POI-level precision
    MEDIUM_QUALITY_TYPES = ["residential", "industrial", "public"]  # WHY: neighborhood-level precision
    QUALITY_CLASSES = ["building", "place", "amenity"]  # WHY: OSM classes used as fallback boost

    def __init__(self, config: AddressValidationConfig | None = None) -> None:
        """Initialize validator with optional config object."""
        cfg = config or AddressValidationConfig()  # WHY: default config avoids seven ternaries + collapses CC
        self.timeout = cfg.timeout  # WHY: shared with retries via linear back-off
        self.debug = cfg.debug  # WHY: gates all trace logging
        self.skip_ssl_verify = cfg.skip_ssl_verify  # WHY: MITM-proxy escape hatch
        self.org_name = cfg.org_name  # WHY: org-name tiebreaker inputs
        self.site_name = cfg.site_name  # WHY: gates duplicate-key check
        self.mist_duplicates = cfg.mist_duplicates  # WHY: pre-computed mist-side dup set
        self.ref_duplicates = cfg.ref_duplicates  # WHY: pre-computed ref-side dup set
        self._suppress_ssl_warnings()  # WHY: silence urllib3 warnings when verify is disabled

    def _suppress_ssl_warnings(self) -> None:
        """Announce a disabled TLS check, then quiet the repeated urllib3 notice.

        The old version silenced the warning and said nothing, so a run with
        no certificate check looked the same as a normal run. Now the run
        states the weakened condition one time. See issue #1914.
        """
        if not self.skip_ssl_verify:  # Nothing to report when the check stays on.
            return  # Normal secure path exits early.
        TLSVerificationPolicy.warn_once()  # State the risk one time for the operator.
        if _has_urllib3 and urllib3 is not None:  # Quiet the per-request repeat, not the warning above.
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # WHY: one notice is enough.

    def _log_entry(
        self,
        mist_address: dict[str, Any],
        comparison_address: dict[str, Any],
    ) -> None:
        """Log entry point with input parameters."""
        if self.debug:  # WHY: only pay for logging when debug is on
            logging.debug("ENTRY: NominatimValidator.validate()")
            logging.debug("  mist_address: %s", mist_address)
            logging.debug("  comparison_address: %s", comparison_address)

    def _build_address_string(
        self,
        address_dict: dict[str, Any],
    ) -> tuple[str | None, list[str]]:
        """Build address string from dictionary components."""
        keys = ("address", "city", "state", "zip")  # WHY: canonical order for reconstruction
        parts = [address_dict.get(k, "") for k in keys if address_dict.get(k)]  # WHY: skip empty fields
        if not parts:  # WHY: nothing to geocode
            return None, []  # WHY: signal empty address to caller
        return ", ".join(parts), parts  # WHY: paired for downstream component matching

    def _create_empty_result(self, error: str) -> dict[str, Any]:
        """Create standardized empty/error result."""
        return {  # WHY: canonical failure shape used across error paths
            "valid": False,  # WHY: no geocode success
            "confidence": 0.0,  # WHY: zero confidence for failures
            "lat": None,  # WHY: no coords available
            "lon": None,  # WHY: no coords available
            "error": error,  # WHY: caller/log-friendly reason
        }

    def _make_api_request(
        self,
        address_string: str,  # WHY: the body builds the query from this string alone, so source left the signature
    ) -> Any | None:
        """Make Nominatim API request with retry logic."""
        if requests is None:  # WHY: missing dependency -> no-op
            return None  # WHY: caller handles None gracefully
        params: dict[str, str | int] = {  # WHY: minimal query params for Nominatim
            "format": "json",
            "q": address_string,
            "limit": 1,
            "addressdetails": 1,
        }
        headers = {"User-Agent": self.USER_AGENT}  # WHY: Nominatim ToS enforcement
        verify_ssl = not self.skip_ssl_verify  # WHY: single boolean threaded to all attempts
        for attempt in range(self.MAX_RETRIES + 1):  # WHY: initial + MAX_RETRIES extra tries
            response = self._try_request_attempt(params, headers, verify_ssl, attempt)  # WHY: per-attempt call
            if response is not None:  # WHY: first success returns immediately
                return response  # WHY: propagate the raw response upstream
        return None  # WHY: all attempts failed

    def _try_request_attempt(
        self,
        params: dict[str, str | int],
        headers: dict[str, str],
        verify_ssl: bool,
        attempt: int,
    ) -> Any | None:
        """Execute one Nominatim attempt with linear back-off on failure."""
        try:  # WHY: any transport error retries or gives up
            timeout = self.timeout + (attempt * 5)  # WHY: grow timeout linearly with each retry
            return requests.get(  # WHY: perform the HTTP GET with configured knobs
                self.NOMINATIM_URL,
                params=params,
                headers=headers,
                timeout=timeout,
                verify=verify_ssl,
            )
        except Exception:  # WHY: catch-all so a bad response does not kill validation
            if attempt < self.MAX_RETRIES:  # WHY: sleep only when another attempt remains
                time.sleep(self.RETRY_DELAY)  # WHY: fixed back-off between attempts
            return None  # WHY: signal caller to retry or terminate

    def _calculate_component_match(
        self,
        address_parts: list[str],
        display_name: str,  # WHY: the score reads the parts and the display name only, so source left the signature
    ) -> float:
        """Calculate match score based on address component matching."""
        total = len(address_parts)  # WHY: number of address parts to score against display name
        if total == 0:  # WHY: avoid division by zero
            return 0.0  # WHY: canonical zero
        lower_display = display_name.lower()  # WHY: lowercase once for case-insensitive matching
        score = sum(self._part_match_score(part, lower_display) for part in address_parts)  # WHY: per-part scores
        return score / total  # WHY: average match score across all parts

    @staticmethod
    def _part_match_score(part: str, lower_display: str) -> float:
        """Score one address part against the lowercased geocoder display name."""
        clean = part.lower().strip()  # WHY: normalize the part for comparison
        if len(clean) <= 2:  # WHY: ignore trivially short tokens (directionals/abbreviations)
            return 0.0  # WHY: too noisy to count
        if clean in lower_display:  # WHY: full-token substring match scores highest
            return 1.0  # WHY: exact substring wins
        if NominatimValidator._has_significant_word(clean, lower_display):  # WHY: partial word match
            return 0.5  # WHY: half credit for word-level overlap
        return 0.0  # WHY: no match for this part

    @staticmethod
    def _has_significant_word(clean: str, lower_display: str) -> bool:
        """Return True when any 3+ character word of ``clean`` appears in the display name."""
        return any(w in lower_display for w in clean.split() if len(w) > 2)  # WHY: skip short/noise words

    def _calculate_quality_boost(
        self,
        result: dict[str, Any],  # WHY: both boost helpers read the result only, so source left the signature
    ) -> float:
        """Calculate quality boost from place type and address details."""
        return self._place_type_boost(result) + self._address_detail_boost(result)  # WHY: sum the two boost sources

    def _place_type_boost(self, result: dict[str, Any]) -> float:
        """Return the geocode-quality boost implied by the place type/class tier."""
        place_type = result.get("type", "").lower()  # WHY: normalized OSM place type
        place_class = result.get("class", "").lower()  # WHY: normalized OSM place class
        if place_type in self.HIGH_QUALITY_TYPES:  # WHY: building/POI-level types are most precise
            return 0.3  # WHY: max type boost
        if place_type in self.MEDIUM_QUALITY_TYPES:  # WHY: street/area types are moderately precise
            return 0.2  # WHY: medium type boost
        if place_class in self.QUALITY_CLASSES:  # WHY: fall back to class-tier boost when type is unranked
            return 0.1  # WHY: class-only boost
        return 0.0  # WHY: unranked place -> no type boost

    @staticmethod
    def _address_detail_boost(result: dict[str, Any]) -> float:
        """Return the boost implied by how many address detail fields are populated."""
        details = result.get("address", {})  # WHY: structured address-component dict
        if not details:  # WHY: no structured details -> no boost
            return 0.0  # WHY: canonical zero
        count = sum(map(bool, details.values()))  # WHY: count populated fields without a branch
        if count >= 5:  # WHY: rich detail set -> strong boost
            return 0.2  # WHY: max detail boost
        if count >= 3:  # WHY: moderate detail set
            return 0.1  # WHY: partial detail boost
        return 0.0  # WHY: sparse details -> no boost

    def _calculate_confidence(
        self,
        result: dict[str, Any],
        address_parts: list[str],  # WHY: both callees below stopped taking source, so this level drops it too
    ) -> float:
        """Calculate overall confidence score for geocode result."""
        importance = float(result.get("importance", 0.0))  # WHY: Nominatim's own importance score
        if importance > 0.01:  # WHY: trust importance when it is non-trivial
            return min(1.0, importance * 2.0)  # WHY: scale + cap at 1.0
        display_name = result.get("display_name", "")  # WHY: cache to shorten next call
        component = self._calculate_component_match(address_parts, display_name)  # WHY: fallback match
        boost = self._calculate_quality_boost(result)  # WHY: quality boost adds to component score
        return min(1.0, component + boost)  # WHY: bound confidence to [0, 1]

    def _parse_geocode_response(
        self,
        response: Any,
        address_parts: list[str],  # WHY: the only callee below stopped taking source, so this level drops it too
    ) -> dict[str, Any]:
        """Parse successful geocode response."""
        if response.status_code != 200:  # WHY: any non-200 is a failure
            return self._create_empty_result(f"HTTP {response.status_code}")  # WHY: surface status in error
        results = response.json()  # WHY: parse JSON body
        if not results:  # WHY: empty result list = no geocode match
            return self._create_empty_result("No results found")  # WHY: canonical no-match error
        result = results[0]  # WHY: use only the top match
        confidence = self._calculate_confidence(result, address_parts)  # WHY: score the match
        return {  # WHY: canonical success shape
            "valid": True,  # WHY: geocode succeeded
            "confidence": confidence,  # WHY: 0-1 score
            "lat": float(result["lat"]),  # WHY: coerce string coord to float
            "lon": float(result["lon"]),  # WHY: coerce string coord to float
            "display_name": result.get("display_name", ""),  # WHY: for downstream tiebreakers/logging
            "place_type": result.get("type", ""),  # WHY: used by business-context tiebreak
            "place_class": result.get("class", ""),  # WHY: used by class-based quality boost
            "address_details": result.get("address", {}),  # WHY: preserved for callers
            "error": None,  # WHY: no error on success
        }

    def _geocode_address(
        self,
        address_dict: dict[str, Any],
        source: str,
    ) -> dict[str, Any]:
        """Geocode a single address using Nominatim API."""
        try:  # WHY: any error yields an empty-result payload
            addr_str, parts = self._build_address_string(address_dict)  # WHY: derive query string + parts list
            if not addr_str:  # WHY: nothing to geocode
                return self._create_empty_result("Empty address")  # WHY: canonical empty-input error
            response = self._make_api_request(addr_str)  # WHY: run the retryable HTTP call. It logs no source label
            if response is None:  # WHY: all retries failed
                return self._create_empty_result("No response received")  # WHY: canonical no-response error
            return self._parse_geocode_response(response, parts)  # WHY: shape the successful body
        except Exception as exc:  # WHY: never let a geocode bubble kill validation
            if self.debug:  # WHY: only log full traceback in debug mode
                logging.debug("GEOCODE [%s]: %s", source, exc)
                logging.debug("GEOCODE [%s]: %s", source, traceback.format_exc())
            return self._create_empty_result(str(exc))  # WHY: surface the exception message

    def _create_address_key(self, address_dict: dict[str, Any]) -> str:
        """Create normalized key for duplicate detection."""
        return (  # WHY: pipe-joined lowercase parts, ZIP kept as-is for dash preservation
            f"{address_dict.get('address', '').lower()}|"
            f"{address_dict.get('city', '').lower()}|"
            f"{address_dict.get('state', '').lower()}|"
            f"{address_dict.get('zip', '')}"
        )

    def _check_duplicate_status(
        self,
        mist_address: dict[str, Any],
        comparison_address: dict[str, Any],
    ) -> tuple[bool, bool]:
        """Check if addresses are duplicates (shared between multiple sites)."""
        mist_dup = bool(  # WHY: mist duplicate iff sets configured AND key present
            self.mist_duplicates and self.site_name and self._create_address_key(mist_address) in self.mist_duplicates
        )
        ref_dup = bool(  # WHY: ref duplicate iff sets configured AND key present
            self.ref_duplicates
            and self.site_name
            and self._create_address_key(comparison_address) in self.ref_duplicates
        )
        return mist_dup, ref_dup  # WHY: pair result for downstream rule application

    def _apply_duplicate_rules(
        self,
        mist_dup: bool,
        ref_dup: bool,
    ) -> tuple[str | None, str | None]:
        """Apply duplicate disqualification rules."""
        if mist_dup and ref_dup:  # WHY: both duplicated -> cannot pick a winner
            return "uncertain", "Both addresses are duplicates"
        if mist_dup:  # WHY: mist alone duplicated -> ref wins by default
            return "comparison", "Mist address is duplicate"
        if ref_dup:  # WHY: ref alone duplicated -> mist wins by default
            return "mist", "Reference address is duplicate"
        return None, None  # WHY: no duplicate signal, caller falls through

    def _apply_confidence_comparison(
        self,
        mist_conf: float,
        comp_conf: float,
    ) -> tuple[str | None, str | None]:
        """Compare confidence scores with 10%% threshold."""
        if mist_conf > comp_conf * 1.1:  # WHY: >10% higher wins outright
            return "mist", f"Mist higher confidence ({mist_conf:.3f} vs {comp_conf:.3f})"
        if comp_conf > mist_conf * 1.1:  # WHY: symmetrical rule for the ref side
            return "comparison", f"Reference higher confidence ({comp_conf:.3f} vs {mist_conf:.3f})"
        return None, None  # WHY: too close -> caller applies further tiebreakers

    def _apply_org_name_tiebreaker(
        self,
        mist_result: dict[str, Any],
        comp_result: dict[str, Any],
    ) -> tuple[str | None, str | None]:
        """Apply organization name similarity tiebreaker."""
        if not self.org_name:  # WHY: no org name configured -> skip this tiebreaker
            return None, None
        norm_org = NameNormalizationUtils.normalize_business_name(self.org_name)  # WHY: strip suffixes for match
        mist_display = mist_result.get("display_name", "").lower()  # WHY: normalize for similarity
        comp_display = comp_result.get("display_name", "").lower()  # WHY: normalize for similarity
        mist_sim = NameNormalizationUtils.calculate_org_name_similarity(norm_org, mist_display)  # WHY: mist score
        comp_sim = NameNormalizationUtils.calculate_org_name_similarity(norm_org, comp_display)  # WHY: comp score
        if mist_sim > comp_sim + 0.1:  # WHY: 10% margin required to declare a winner
            return "mist", f"Mist better matches org '{self.org_name}'"
        if comp_sim > mist_sim + 0.1:  # WHY: symmetrical rule
            return "comparison", f"Reference better matches org '{self.org_name}'"
        return None, None  # WHY: inconclusive, caller applies further tiebreakers

    def _apply_business_context_tiebreaker(
        self,
        mist_result: dict[str, Any],
        comp_result: dict[str, Any],
    ) -> tuple[str, str]:
        """Apply business context rules as final tiebreaker."""
        # WHY: biz/res + conf blend as the final recommendation
        rec = AddressUtils.apply_business_context_rules(mist_result, comp_result)
        if rec == "mist":  # WHY: rule preferred the mist side
            return "mist", f"Mist more business-appropriate ({mist_result.get('place_type', 'unknown')})"
        if rec == "comparison":  # WHY: rule preferred the ref side
            return "comparison", f"Reference more business-appropriate ({comp_result.get('place_type', 'unknown')})"
        mist_c = mist_result["confidence"]  # WHY: include confidence numbers in the uncertain reason
        comp_c = comp_result["confidence"]  # WHY: include confidence numbers in the uncertain reason
        return "uncertain", f"All tiebreakers inconclusive ({mist_c:.3f} vs {comp_c:.3f})"

    def _determine_both_valid(
        self,
        mist_result: dict[str, Any],
        comp_result: dict[str, Any],
        mist_address: dict[str, Any],
        comparison_address: dict[str, Any],
    ) -> tuple[str, str]:
        """Determine recommendation when both addresses are valid."""
        mist_dup, ref_dup = self._check_duplicate_status(mist_address, comparison_address)  # WHY: dup check first
        rec, reason = self._apply_duplicate_rules(mist_dup, ref_dup)  # WHY: hard rule if a dup exists
        if rec:  # WHY: duplicate rule resolved it
            return rec, reason  # type: ignore[return-value]
        rec, reason = self._apply_confidence_comparison(  # WHY: try confidence delta next
            mist_result["confidence"],
            comp_result["confidence"],
        )
        if rec:  # WHY: confidence resolved it
            return rec, reason  # type: ignore[return-value]
        rec, reason = self._apply_org_name_tiebreaker(mist_result, comp_result)  # WHY: try org-name similarity
        if rec:  # WHY: org-name resolved it
            return rec, reason  # type: ignore[return-value]
        return self._apply_business_context_tiebreaker(mist_result, comp_result)  # WHY: final fallback tiebreak

    def _determine_recommendation(
        self,
        mist_result: dict[str, Any],
        comp_result: dict[str, Any],
        mist_address: dict[str, Any],
        comparison_address: dict[str, Any],
    ) -> tuple[str, str]:
        """Determine final recommendation based on validation results."""
        single = _single_valid_recommendation(mist_result, comp_result)  # WHY: shortcut for one-sided validity
        if single is not None:  # WHY: single-valid path already resolved
            return single  # WHY: propagate the resolved pair
        if mist_result["valid"]:  # WHY: since single was None, both are either valid or both invalid
            return self._determine_both_valid(mist_result, comp_result, mist_address, comparison_address)
        return "uncertain", "Both addresses failed validation"  # WHY: both invalid path

    def validate(
        self,
        mist_address: dict[str, Any],
        comparison_address: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate both address sets against Nominatim API."""
        self._log_entry(mist_address, comparison_address)  # WHY: trace inputs when debug is on
        mist_result = self._geocode_address(mist_address, "MIST")  # WHY: geocode mist side
        time.sleep(self.RATE_LIMIT_DELAY)  # WHY: honor Nominatim 1 req/sec ToS
        comp_result = self._geocode_address(comparison_address, "COMPARISON")  # WHY: geocode comparison side
        recommendation, reason = self._determine_recommendation(  # WHY: apply the full tiebreaker chain
            mist_result,
            comp_result,
            mist_address,
            comparison_address,
        )
        return _build_validation_result(mist_result, comp_result, recommendation, reason)  # WHY: canonical output shape


def _single_valid_recommendation(
    mist_result: dict[str, Any],
    comp_result: dict[str, Any],
) -> tuple[str, str] | None:
    """Return a recommendation when exactly one side is valid, else None."""
    mist_valid = mist_result["valid"]  # WHY: cache for two comparisons
    comp_valid = comp_result["valid"]  # WHY: cache for two comparisons
    if mist_valid and not comp_valid:  # WHY: only mist valid -> mist wins
        return "mist", f"Only Mist valid ({mist_result['confidence']:.3f})"
    if comp_valid and not mist_valid:  # WHY: only comp valid -> comp wins
        return "comparison", f"Only reference valid ({comp_result['confidence']:.3f})"
    return None  # WHY: both valid or both invalid -> caller handles


def _build_validation_result(
    mist_result: dict[str, Any],
    comp_result: dict[str, Any],
    recommendation: str,
    reason: str,
) -> dict[str, Any]:
    """Package the final validation dict returned by :meth:`NominatimValidator.validate`."""
    return {  # WHY: canonical output shape consumed by callers/tests
        "mist_validation": mist_result,  # WHY: raw mist-side geocode result
        "comparison_validation": comp_result,  # WHY: raw comp-side geocode result
        "recommendation": recommendation,  # WHY: 'mist' / 'comparison' / 'uncertain'
        "recommendation_reason": reason,  # WHY: human-readable rationale
    }

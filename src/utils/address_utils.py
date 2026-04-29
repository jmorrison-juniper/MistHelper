# pylint: disable=too-many-lines,logging-fstring-interpolation,implicit-str-concat
"""Address parsing, normalization, and geocoding validation utilities.

Extracted from MistHelper.py monolith. Contains:
- AddressValidationConfig: Configuration dataclass for NominatimValidator.
- AddressUtils: Static address normalization, parsing, and comparison.
- NameNormalizationUtils: Business/org name normalization helpers.
- NominatimValidator: Geocoding-based address validation via Nominatim API.
"""

from __future__ import annotations

import difflib
import logging
import re
import time
import traceback
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore[assignment]

try:
    import urllib3

    _has_urllib3 = True
except ImportError:  # pragma: no cover
    urllib3 = None  # type: ignore[assignment]
    _has_urllib3 = False

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover
    fuzz = None  # type: ignore[assignment]

try:
    from scourgify import normalize_address_record
except ImportError:  # pragma: no cover
    normalize_address_record = None  # type: ignore[assignment]


@dataclass
class AddressValidationConfig:
    """Configuration for address validation with Nominatim."""

    timeout: int = 5
    debug: bool = False
    skip_ssl_verify: bool = False
    org_name: str | None = None
    site_name: str | None = None
    mist_duplicates: dict | None = None  # type: ignore[type-arg]
    ref_duplicates: dict | None = None  # type: ignore[type-arg]


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
    # Abbreviations map to themselves
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
        if not zip_code:
            return ""
        zip_str = str(zip_code).strip()
        if "-" in zip_str:
            zip_str = zip_str.split("-")[0]
        zip_digits = "".join(filter(str.isdigit, zip_str))
        if len(zip_digits) == 4:
            zip_digits = "0" + zip_digits
        return zip_digits[:5]

    @staticmethod
    def _normalize_state(state_str: Any) -> str:
        """Normalize state names/abbreviations to lowercase abbreviation."""
        if not state_str:
            return ""
        state = state_str.lower().strip()
        return _STATE_MAPPING.get(state, state)

    @staticmethod
    def _normalize_address(address_str: Any) -> str:
        """Normalize an address string for comparison."""
        if not address_str:
            return ""
        normalized = unicodedata.normalize("NFKD", address_str)
        normalized = normalized.casefold().strip()
        normalized = re.sub(r"\s+", " ", normalized)
        for full_form, abbrev in _ADDRESS_ABBREVIATIONS.items():
            normalized = re.sub(full_form, abbrev, normalized)
        normalized = re.sub(r"[^\w\s]", " ", normalized)
        normalized = " ".join(normalized.split())
        return normalized

    @staticmethod
    def _parse_components(  # noqa: C901, PLR0912, PLR0915
        address_string: str | None,
        debug: bool = False,
    ) -> dict[str, Any]:
        """Parse address components with defensive heuristics."""
        if debug:
            logging.debug(f"PARSE_ADDRESS: Input: '{address_string}'")
        result: dict[str, Any] = {
            "address": None,
            "city": None,
            "state": None,
            "zip": None,
            "country": None,
            "is_parseable": False,
            "parse_reason": "unparsed",
            "original": address_string or "",
        }
        if not address_string or not str(address_string).strip():
            result["parse_reason"] = "empty_input"
            return result
        cleaned_input = str(address_string).strip()
        if cleaned_input.lower() in ["unknown", "n/a", "na", "none", "null", ""]:
            result["parse_reason"] = "unknown_address"
            return result
        try:
            return _parse_address_parts(cleaned_input, result, debug)
        except Exception as exception:
            result["parse_reason"] = f"exception: {exception!s}"
            if debug:
                logging.warning(f"PARSE_ADDRESS: Exception during parsing: {exception}")
            return result

    @staticmethod
    def enhanced_parse(
        address_string: str | None,
        debug: bool = False,
    ) -> dict[str, Any]:
        """Enhanced address parsing using usaddress-scourgify with heuristic fallback."""
        if normalize_address_record is None:
            if debug:
                logging.debug("USADDRESS_PARSE: usaddress-scourgify not available")
            return AddressUtils._parse_components(address_string, debug=debug)
        try:
            if debug:
                logging.debug(f"USADDRESS_PARSE: Attempting for: '{address_string}'")
            parsed = normalize_address_record(address_string)
            result: dict[str, Any] = {
                "address": parsed.get("address_line_1", ""),
                "city": parsed.get("city", ""),
                "state": parsed.get("state", ""),
                "zip": parsed.get("postal_code", ""),
                "country": "US",
                "is_parseable": True,
                "parse_reason": "usaddress_success",
                "original": address_string or "",
            }
            if parsed.get("address_line_2"):
                parts = [parsed.get("address_line_1", ""), parsed.get("address_line_2", "")]
                result["address"] = " ".join(p for p in parts if p)
            return result
        except Exception:
            return AddressUtils._parse_components(address_string, debug=debug)

    @staticmethod
    def _calculate_similarity(str1: Any, str2: Any) -> float:
        """Calculate similarity percentage between two strings."""
        if not str1 and not str2:
            return 100.0
        if not str1 or not str2:
            return 0.0
        norm1 = AddressUtils._normalize_address(str1)
        norm2 = AddressUtils._normalize_address(str2)
        if fuzz is not None:
            try:
                return fuzz.token_sort_ratio(norm1, norm2) / 100.0 * 100
            except Exception:  # nosec B110
                pass
        return difflib.SequenceMatcher(None, norm1, norm2).ratio() * 100

    @staticmethod
    def check_should_skip(  # noqa: C901, PLR0912
        comparison_address: dict[str, Any],
        skip_addresses: list[dict[str, Any]],
        debug: bool = False,
    ) -> tuple[bool, str]:
        """Check if a comparison address should be skipped."""
        if not skip_addresses:
            return False, ""
        comp_addr = str(comparison_address.get("address", "")).strip().upper()
        comp_city = str(comparison_address.get("city", "")).strip().upper()
        comp_state = str(comparison_address.get("state", "")).strip().upper()
        comp_zip = str(comparison_address.get("zip", "")).strip().upper()
        for skip_entry in skip_addresses:
            should_skip, reason = _check_single_skip(
                comp_addr,
                comp_city,
                comp_state,
                comp_zip,
                skip_entry,
                debug,
            )
            if should_skip:
                return True, reason
        return False, ""

    @staticmethod
    def compare_with_threshold(  # noqa: C901, PLR0912
        mist_address: dict[str, Any],
        comparison_address: dict[str, Any],
        threshold: float,
        debug: bool = False,
    ) -> dict[str, Any]:
        """Enhanced address comparison with similarity metrics."""
        field_weights = {"address": 0.4, "city": 0.3, "state": 0.2, "zip": 0.1}
        parse_status = _check_parse_status(mist_address, comparison_address, field_weights)
        if not parse_status["mist_parseable"] or not parse_status["comparison_parseable"]:
            if debug:
                logging.debug(f"ENHANCED_COMPARE: Unparseable: {parse_status}")
            return {
                "overall_similarity": 0.0,
                "is_match": False,
                "field_similarities": {f: 0.0 for f in field_weights},
                "failed_fields": list(field_weights),
                "parse_status": parse_status,
            }
        similarities, failed = _compare_fields(
            mist_address,
            comparison_address,
            field_weights,
            threshold,
            debug,
        )
        overall = sum(similarities[f] * field_weights[f] for f in field_weights)
        return {
            "overall_similarity": overall,
            "is_match": overall >= threshold,
            "field_similarities": similarities,
            "failed_fields": failed,
            "parse_status": parse_status,
        }

    @staticmethod
    def apply_business_context_rules(  # noqa: C901
        mist_result: dict[str, Any],
        comparison_result: dict[str, Any],
        debug: bool = False,
    ) -> str:
        """Apply business context rules for address tiebreaking."""
        business_types = ["commercial", "office", "retail", "building", "shop", "store"]
        residential_types = ["house", "residential", "apartment"]
        mist_place = mist_result.get("place_type", "").lower()
        comp_place = comparison_result.get("place_type", "").lower()
        mist_biz = any(t in mist_place for t in business_types)
        comp_biz = any(t in comp_place for t in business_types)
        mist_res = any(t in mist_place for t in residential_types)
        comp_res = any(t in comp_place for t in residential_types)
        if mist_biz and comp_res:
            return "mist"
        if comp_biz and mist_res:
            return "comparison"
        diff = abs(mist_result["confidence"] - comparison_result["confidence"])
        if diff > 0.05:
            if mist_result["confidence"] > comparison_result["confidence"]:
                return "mist"
            return "comparison"
        return "uncertain"


# ---------------------------------------------------------------------------
# Private helpers for AddressUtils (keep CC low)
# ---------------------------------------------------------------------------


def _parse_address_parts(
    cleaned_input: str,
    result: dict[str, Any],
    debug: bool,
) -> dict[str, Any]:
    """Inner parser for _parse_components (extracted for CC reduction)."""
    normalized = unicodedata.normalize("NFKD", cleaned_input)
    parts = [p.strip() for p in normalized.split(",") if p.strip()]
    if not parts:
        result["parse_reason"] = "no_parts_after_cleaning"
        return result
    remaining = parts[:]
    country = _detect_country(remaining)
    if country:
        remaining = remaining[:-1]
    zip_code, country = _detect_zip(remaining, country)
    if zip_code:
        remaining = remaining[:-1]
    state = _detect_state(remaining)
    if state:
        remaining = remaining[:-1]
    city = remaining[-1].strip() if remaining else None
    if city:
        remaining = remaining[:-1]
    address = ", ".join(remaining).strip() if remaining else None
    result.update(
        {
            "address": address,
            "city": city,
            "state": state,
            "zip": zip_code,
            "country": country,
            "is_parseable": True,
            "parse_reason": "success",
        }
    )
    if debug:
        logging.debug(f"PARSE_ADDRESS: Parsed result: {result}")
    return result


def _detect_country(parts: list[str]) -> str | None:
    """Detect country from last address token."""
    if not parts:
        return None
    last = parts[-1].strip().lower()
    if last in ("usa", "united states", "united states of america", "us"):
        return "US"
    if last in ("puerto rico", "pr"):
        return "US"
    if len(last) == 2 and last.isalpha():
        return last.upper()
    return None


def _detect_zip(
    parts: list[str],
    country: str | None,
) -> tuple[str | None, str | None]:
    """Detect ZIP/postal code from remaining parts."""
    if not parts:
        return None, country
    last = parts[-1].strip()
    if re.match(r"^\d{5}(-?\d{4})?$", last):
        if not country:
            country = "US"
        return last, country
    return None, country


def _detect_state(parts: list[str]) -> str | None:
    """Detect US state from remaining parts."""
    if not parts:
        return None
    last = parts[-1].strip().lower()
    if last == "puerto rico":
        return "PR"
    if len(last) <= 2 and last.isalpha():
        return last.upper()
    if len(parts) > 1:
        normalized = AddressUtils._normalize_state(last)
        if normalized:
            return normalized.upper()
    return None


def _check_single_skip(
    comp_addr: str,
    comp_city: str,
    comp_state: str,
    comp_zip: str,
    skip_entry: dict[str, Any],
    debug: bool,
) -> tuple[bool, str]:
    """Check one skip entry against comparison address."""
    skip_addr = str(skip_entry.get("Skip_Address", "")).strip().upper()
    skip_city = str(skip_entry.get("Skip_City", "")).strip().upper()
    skip_state = str(skip_entry.get("Skip_State", "")).strip().upper()
    skip_zip = str(skip_entry.get("Skip_Zip", "")).strip().upper()
    skip_reason = skip_entry.get("Reason", "Address in skip list")
    if comp_addr == skip_addr and comp_city == skip_city and comp_state == skip_state and comp_zip == skip_zip:
        if debug:
            logging.debug(f"ADDRESS_SKIP: Exact match - {comp_addr}")
        return True, skip_reason
    return _check_partial_skip(
        comp_addr,
        comp_city,
        comp_state,
        comp_zip,
        skip_addr,
        skip_city,
        skip_state,
        skip_zip,
        skip_reason,
        debug,
    )


def _check_partial_skip(
    comp_addr: str,
    comp_city: str,
    comp_state: str,
    comp_zip: str,
    skip_addr: str,
    skip_city: str,
    skip_state: str,
    skip_zip: str,
    skip_reason: str,
    debug: bool,
) -> tuple[bool, str]:
    """Check partial/wildcard skip match."""
    matching = sum(
        [
            bool(skip_addr and comp_addr == skip_addr),
            bool(skip_city and comp_city == skip_city),
            bool(skip_state and comp_state == skip_state),
            bool(skip_zip and comp_zip == skip_zip),
        ]
    )
    if matching == 0:
        return False, ""
    empty_fields = sum(1 for f in [skip_addr, skip_city, skip_state, skip_zip] if not f)
    populated = 4 - empty_fields
    if empty_fields >= 3 and matching == 1:
        if debug:
            logging.debug(f"ADDRESS_SKIP: Wildcard match - {comp_addr}")
        return True, skip_reason
    if populated >= 2 and matching >= max(2, populated // 2):
        if debug:
            logging.debug(f"ADDRESS_SKIP: Specific match - {comp_addr}")
        return True, skip_reason
    return False, ""


def _check_parse_status(
    mist_address: dict[str, Any],
    comparison_address: dict[str, Any],
    field_weights: dict[str, float],
) -> dict[str, Any]:
    """Check if addresses are parseable."""
    status: dict[str, Any] = {
        "mist_parseable": True,
        "comparison_parseable": True,
        "mist_reason": "valid",
        "comparison_reason": "valid",
    }
    unparseable = {"unknown", "n/a", "na", "none", "null", ""}
    for field in field_weights:
        mist_val = str(mist_address.get(field, "")).strip().lower()
        comp_val = str(comparison_address.get(field, "")).strip().lower()
        if mist_val in unparseable:
            status["mist_parseable"] = False
            status["mist_reason"] = "unknown_address"
        if comp_val in unparseable:
            status["comparison_parseable"] = False
            status["comparison_reason"] = "unknown_address"
    return status


def _compare_fields(
    mist_address: dict[str, Any],
    comparison_address: dict[str, Any],
    field_weights: dict[str, float],
    threshold: float,
    debug: bool,
) -> tuple[dict[str, float], list[str]]:
    """Compare address fields and return similarities + failed fields."""
    similarities: dict[str, float] = {}
    failed: list[str] = []
    for field in field_weights:
        mist_val = str(mist_address.get(field, "")).strip()
        comp_val = str(comparison_address.get(field, "")).strip()
        similarity = _compare_single_field(field, mist_val, comp_val)
        similarities[field] = similarity
        if similarity < threshold * 0.75:
            failed.append(field)
        if debug:
            logging.debug(
                f"ENHANCED_COMPARE: {field} similarity: {similarity:.1f}%" f" (threshold: {threshold * 0.75:.1f}%)"
            )
    return similarities, failed


def _compare_single_field(field: str, mist_val: str, comp_val: str) -> float:
    """Compare a single address field."""
    if field == "zip":
        mist_n = AddressUtils.normalize_zip(mist_val)
        comp_n = AddressUtils.normalize_zip(comp_val)
        return 100.0 if mist_n == comp_n and mist_n else 0.0
    if field == "state":
        mist_n = AddressUtils._normalize_state(mist_val)
        comp_n = AddressUtils._normalize_state(comp_val)
        return 100.0 if mist_n == comp_n and mist_n else 0.0
    return AddressUtils._calculate_similarity(mist_val, comp_val)


# ============================================================================
# NAME NORMALIZATION UTILITIES
# ============================================================================


class NameNormalizationUtils:
    """General name and token normalization helpers.

    Used for business/org name cleaning and similarity calculation.
    """

    BUSINESS_SUFFIX_PATTERNS = [
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
        if not business_name:
            return ""
        normalized = business_name.lower().strip()
        for suffix in NameNormalizationUtils.BUSINESS_SUFFIX_PATTERNS:
            normalized = re.sub(suffix, "", normalized).strip()
        normalized = re.sub(r"[^\w\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    @staticmethod
    def normalize_generic(name: str) -> str:
        """Lightweight generic normalization."""
        if not name:
            return ""
        cleaned = unicodedata.normalize("NFKD", str(name)).casefold().strip()
        return re.sub(r"\s+", " ", cleaned)

    @staticmethod
    def extract_tokens(name: str) -> list[str]:
        """Return lowercase alphanumeric tokens for fuzzy pipelines."""
        if not name:
            return []
        return re.findall(r"[a-z0-9]+", NameNormalizationUtils.normalize_generic(name))

    @staticmethod
    def calculate_org_name_similarity(
        org_name: str,
        address_display: str,
    ) -> float:
        """Calculate similarity between org name and address display name."""
        if not org_name or not address_display:
            return 0.0
        org_words = set(org_name.split())
        address_words = set(re.findall(r"\b\w+\b", address_display.lower()))
        exact_matches = len(org_words.intersection(address_words))
        word_sim = (exact_matches / len(org_words)) if org_words else 0.0
        string_sim = SequenceMatcher(None, org_name, address_display).ratio()
        return min(1.0, (word_sim * 0.7) + (string_sim * 0.3))


# Backward-compatible alias
AddressBusinessNameUtils = NameNormalizationUtils


# ============================================================================
# NOMINATIM ADDRESS VALIDATOR
# ============================================================================


class NominatimValidator:
    """Validate addresses against Nominatim (OpenStreetMap) geocoding API.

    Compares two address sets (Mist vs reference) and recommends which is
    more accurate based on geocoding confidence, place types, and tiebreakers.
    """

    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    USER_AGENT = "MistHelper/1.0 (address validation)"
    RATE_LIMIT_DELAY = 1.1
    MAX_RETRIES = 2
    RETRY_DELAY = 2
    HIGH_QUALITY_TYPES = ["house", "building", "commercial", "office", "retail", "shop"]
    MEDIUM_QUALITY_TYPES = ["residential", "industrial", "public"]
    QUALITY_CLASSES = ["building", "place", "amenity"]

    def __init__(self, config: AddressValidationConfig | None = None) -> None:
        """Initialize validator with optional config object."""
        self.timeout = config.timeout if config else 5
        self.debug = config.debug if config else False
        self.skip_ssl_verify = config.skip_ssl_verify if config else False
        self.org_name = config.org_name if config else None
        self.site_name = config.site_name if config else None
        self.mist_duplicates = config.mist_duplicates if config else None
        self.ref_duplicates = config.ref_duplicates if config else None
        self._suppress_ssl_warnings()

    def _suppress_ssl_warnings(self) -> None:
        """Suppress SSL warnings when verification is disabled."""
        if self.skip_ssl_verify and _has_urllib3 and urllib3 is not None:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _log_entry(
        self,
        mist_address: dict[str, Any],
        comparison_address: dict[str, Any],
    ) -> None:
        """Log entry point with input parameters."""
        if self.debug:
            logging.debug("ENTRY: NominatimValidator.validate()")
            logging.debug(f"  mist_address: {mist_address}")
            logging.debug(f"  comparison_address: {comparison_address}")

    def _build_address_string(
        self,
        address_dict: dict[str, Any],
    ) -> tuple[str | None, list[str]]:
        """Build address string from dictionary components."""
        parts = [address_dict.get(k, "") for k in ("address", "city", "state", "zip") if address_dict.get(k)]
        if not parts:
            return None, []
        return ", ".join(parts), parts

    def _create_empty_result(self, error: str) -> dict[str, Any]:
        """Create standardized empty/error result."""
        return {
            "valid": False,
            "confidence": 0.0,
            "lat": None,
            "lon": None,
            "error": error,
        }

    def _make_api_request(  # noqa: C901
        self,
        address_string: str,
        source: str,
    ) -> Any | None:
        """Make Nominatim API request with retry logic."""
        if requests is None:
            return None
        params = {
            "format": "json",
            "q": address_string,
            "limit": 1,
            "addressdetails": 1,
        }
        headers = {"User-Agent": self.USER_AGENT}
        verify_ssl = not self.skip_ssl_verify
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                timeout = self.timeout + (attempt * 5)
                return requests.get(
                    self.NOMINATIM_URL,
                    params=params,
                    headers=headers,
                    timeout=timeout,
                    verify=verify_ssl,
                )
            except Exception:
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY)
                else:
                    return None
        return None  # pragma: no cover

    def _calculate_component_match(
        self,
        address_parts: list[str],
        display_name: str,
        source: str,
    ) -> float:
        """Calculate match score based on address component matching."""
        total = len(address_parts)
        if total == 0:
            return 0.0
        score = 0.0
        lower_display = display_name.lower()
        for part in address_parts:
            clean = part.lower().strip()
            if len(clean) <= 2:
                continue
            if clean in lower_display:
                score += 1.0
            elif any(w in lower_display for w in clean.split() if len(w) > 2):
                score += 0.5
        return score / total

    def _calculate_quality_boost(
        self,
        result: dict[str, Any],
        source: str,
    ) -> float:
        """Calculate quality boost from place type and address details."""
        boost = 0.0
        place_type = result.get("type", "").lower()
        place_class = result.get("class", "").lower()
        if place_type in self.HIGH_QUALITY_TYPES:
            boost += 0.3
        elif place_type in self.MEDIUM_QUALITY_TYPES:
            boost += 0.2
        elif place_class in self.QUALITY_CLASSES:
            boost += 0.1
        details = result.get("address", {})
        if details:
            count = len([v for v in details.values() if v])
            if count >= 5:
                boost += 0.2
            elif count >= 3:
                boost += 0.1
        return boost

    def _calculate_confidence(
        self,
        result: dict[str, Any],
        address_parts: list[str],
        source: str,
    ) -> float:
        """Calculate overall confidence score for geocode result."""
        importance = float(result.get("importance", 0.0))
        if importance > 0.01:
            return min(1.0, importance * 2.0)
        component = self._calculate_component_match(address_parts, result.get("display_name", ""), source)
        boost = self._calculate_quality_boost(result, source)
        return min(1.0, component + boost)

    def _parse_geocode_response(
        self,
        response: Any,
        address_parts: list[str],
        source: str,
    ) -> dict[str, Any]:
        """Parse successful geocode response."""
        if response.status_code != 200:
            return self._create_empty_result(f"HTTP {response.status_code}")
        results = response.json()
        if not results:
            return self._create_empty_result("No results found")
        result = results[0]
        confidence = self._calculate_confidence(result, address_parts, source)
        return {
            "valid": True,
            "confidence": confidence,
            "lat": float(result["lat"]),
            "lon": float(result["lon"]),
            "display_name": result.get("display_name", ""),
            "place_type": result.get("type", ""),
            "place_class": result.get("class", ""),
            "address_details": result.get("address", {}),
            "error": None,
        }

    def _geocode_address(
        self,
        address_dict: dict[str, Any],
        source: str,
    ) -> dict[str, Any]:
        """Geocode a single address using Nominatim API."""
        try:
            addr_str, parts = self._build_address_string(address_dict)
            if not addr_str:
                return self._create_empty_result("Empty address")
            response = self._make_api_request(addr_str, source)
            if response is None:
                return self._create_empty_result("No response received")
            return self._parse_geocode_response(response, parts, source)
        except Exception as exc:
            if self.debug:
                logging.debug(f"GEOCODE [{source}]: {exc}")
                logging.debug(f"GEOCODE [{source}]: {traceback.format_exc()}")
            return self._create_empty_result(str(exc))

    def _create_address_key(self, address_dict: dict[str, Any]) -> str:
        """Create normalized key for duplicate detection."""
        return (
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
        mist_dup = bool(
            self.mist_duplicates and self.site_name and self._create_address_key(mist_address) in self.mist_duplicates
        )
        ref_dup = bool(
            self.ref_duplicates
            and self.site_name
            and self._create_address_key(comparison_address) in self.ref_duplicates
        )
        return mist_dup, ref_dup

    def _apply_duplicate_rules(
        self,
        mist_dup: bool,
        ref_dup: bool,
    ) -> tuple[str | None, str | None]:
        """Apply duplicate disqualification rules."""
        if mist_dup and ref_dup:
            return "uncertain", "Both addresses are duplicates"
        if mist_dup:
            return "comparison", "Mist address is duplicate"
        if ref_dup:
            return "mist", "Reference address is duplicate"
        return None, None

    def _apply_confidence_comparison(
        self,
        mist_conf: float,
        comp_conf: float,
    ) -> tuple[str | None, str | None]:
        """Compare confidence scores with 10% threshold."""
        if mist_conf > comp_conf * 1.1:
            return "mist", f"Mist higher confidence ({mist_conf:.3f} vs {comp_conf:.3f})"
        if comp_conf > mist_conf * 1.1:
            return "comparison", f"Reference higher confidence ({comp_conf:.3f} vs {mist_conf:.3f})"
        return None, None

    def _apply_org_name_tiebreaker(
        self,
        mist_result: dict[str, Any],
        comp_result: dict[str, Any],
    ) -> tuple[str | None, str | None]:
        """Apply organization name similarity tiebreaker."""
        if not self.org_name:
            return None, None
        norm_org = NameNormalizationUtils.normalize_business_name(self.org_name)
        mist_display = mist_result.get("display_name", "").lower()
        comp_display = comp_result.get("display_name", "").lower()
        mist_sim = NameNormalizationUtils.calculate_org_name_similarity(norm_org, mist_display)
        comp_sim = NameNormalizationUtils.calculate_org_name_similarity(norm_org, comp_display)
        if mist_sim > comp_sim + 0.1:
            return "mist", f"Mist better matches org '{self.org_name}'"
        if comp_sim > mist_sim + 0.1:
            return "comparison", f"Reference better matches org '{self.org_name}'"
        return None, None

    def _apply_business_context_tiebreaker(
        self,
        mist_result: dict[str, Any],
        comp_result: dict[str, Any],
    ) -> tuple[str, str]:
        """Apply business context rules as final tiebreaker."""
        rec = AddressUtils.apply_business_context_rules(mist_result, comp_result, self.debug)
        if rec == "mist":
            return "mist", f"Mist more business-appropriate ({mist_result.get('place_type', 'unknown')})"
        if rec == "comparison":
            return "comparison", f"Reference more business-appropriate ({comp_result.get('place_type', 'unknown')})"
        mist_c = mist_result["confidence"]
        comp_c = comp_result["confidence"]
        return "uncertain", f"All tiebreakers inconclusive ({mist_c:.3f} vs {comp_c:.3f})"

    def _determine_both_valid(
        self,
        mist_result: dict[str, Any],
        comp_result: dict[str, Any],
        mist_address: dict[str, Any],
        comparison_address: dict[str, Any],
    ) -> tuple[str, str]:
        """Determine recommendation when both addresses are valid."""
        mist_dup, ref_dup = self._check_duplicate_status(mist_address, comparison_address)
        rec, reason = self._apply_duplicate_rules(mist_dup, ref_dup)
        if rec:
            return rec, reason  # type: ignore[return-value]
        rec, reason = self._apply_confidence_comparison(
            mist_result["confidence"],
            comp_result["confidence"],
        )
        if rec:
            return rec, reason  # type: ignore[return-value]
        rec, reason = self._apply_org_name_tiebreaker(mist_result, comp_result)
        if rec:
            return rec, reason  # type: ignore[return-value]
        return self._apply_business_context_tiebreaker(mist_result, comp_result)

    def _determine_recommendation(
        self,
        mist_result: dict[str, Any],
        comp_result: dict[str, Any],
        mist_address: dict[str, Any],
        comparison_address: dict[str, Any],
    ) -> tuple[str, str]:
        """Determine final recommendation based on validation results."""
        mist_valid = mist_result["valid"]
        comp_valid = comp_result["valid"]
        if mist_valid and not comp_valid:
            return "mist", f"Only Mist valid ({mist_result['confidence']:.3f})"
        if comp_valid and not mist_valid:
            return "comparison", f"Only reference valid ({comp_result['confidence']:.3f})"
        if mist_valid and comp_valid:
            return self._determine_both_valid(
                mist_result,
                comp_result,
                mist_address,
                comparison_address,
            )
        return "uncertain", "Both addresses failed validation"

    def validate(
        self,
        mist_address: dict[str, Any],
        comparison_address: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate both address sets against Nominatim API.

        Returns dict with mist_validation, comparison_validation,
        recommendation, and recommendation_reason.
        """
        self._log_entry(mist_address, comparison_address)
        mist_result = self._geocode_address(mist_address, "MIST")
        time.sleep(self.RATE_LIMIT_DELAY)
        comp_result = self._geocode_address(comparison_address, "COMPARISON")
        recommendation, reason = self._determine_recommendation(
            mist_result,
            comp_result,
            mist_address,
            comparison_address,
        )
        return {
            "mist_validation": mist_result,
            "comparison_validation": comp_result,
            "recommendation": recommendation,
            "recommendation_reason": reason,
        }

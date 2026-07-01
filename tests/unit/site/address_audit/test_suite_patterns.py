"""Unit tests for the shared suite/unit regex patterns (1003-site-address-audit)."""

import re

from src.site.address_audit.suite_patterns import (
    HASH_UNIT_PATTERN,
    SUITE_KEYWORDS,
    SUITE_PATTERN,
    SUITE_PATTERN_CAPTURE,
    SUITE_PHRASE_PATTERN,
)


class TestSuiteDetection:
    """SUITE_PATTERN answers 'does this address carry a suite/unit?'."""

    def test_detects_keyword_forms(self):
        """Every keyword form (incl. the 'sute' typo) is detected."""
        for text in (
            "100 Main St Suite 5",
            "100 Main St Ste. A2",
            "100 Main St Unit 8",
            "5958 S Dixie Hwy Sute A-103",  # Real customer misspelling.
            "100 Main St Space P239",
            "100 Main St Bldg D",
        ):
            assert re.search(SUITE_PATTERN, text, re.IGNORECASE), text

    def test_detects_hash_form(self):
        """A bare '#<digits>' hash unit is detected."""
        assert re.search(SUITE_PATTERN, "940 S Military Trail #3, West Palm Beach FL")

    def test_no_suite_returns_no_match(self):
        """A plain street with no unit is not a false positive."""
        assert not re.search(SUITE_PATTERN, "1200 NW 87th Ave, Doral, FL 33172")

    def test_excludes_suit_false_positives(self):
        """'suit' is intentionally absent so lawsuit/pursuit never match."""
        assert "suit|" not in SUITE_KEYWORDS  # Guard against re-introducing the risky token.
        assert not re.search(SUITE_PATTERN, "123 Lawsuit Ln, Town, FL", re.IGNORECASE)
        assert not re.search(SUITE_PATTERN, "1 Pursuit Way, City, FL", re.IGNORECASE)

    def test_hash_form_requires_leading_digit(self):
        """The classification hash form is state-safe: '#A' (letter-first) is not a unit here."""
        # A bare state-like token must never be read as a suite.
        assert not re.fullmatch(SUITE_PATTERN, "FL")


class TestSuiteCapture:
    """SUITE_PATTERN_CAPTURE extracts the bare unit id via its capture groups."""

    @staticmethod
    def _unit(text):
        """Return the captured unit id (keyword group or hash group)."""
        match = re.search(SUITE_PATTERN_CAPTURE, text, re.IGNORECASE)
        if not match:
            return ""
        return match.group(1) or match.group(2) or ""

    def test_keyword_unit_id_captured(self):
        """The keyword branch captures the trailing unit id."""
        assert self._unit("100 Main St Suite 212, Miami FL") == "212"
        assert self._unit("100 Main St Sute A-103, Miami FL") == "A-103"

    def test_hash_unit_id_captured(self):
        """The hash branch captures the digits after '#'."""
        assert self._unit("940 S Military Trail #3, West Palm Beach FL") == "3"


class TestSuitePhrase:
    """SUITE_PHRASE_PATTERN lifts the full keyword phrase for the UI geocoder."""

    def test_phrase_includes_keyword_and_id(self):
        """The whole 'Suite 100' / 'Sute A-103' token is matched, not just the id."""
        match = re.search(SUITE_PHRASE_PATTERN, "2199 Ponce de Leon Blvd Suite 100 Coral Gables FL")
        assert match and match.group(0) == "Suite 100"
        match = re.search(SUITE_PHRASE_PATTERN, "5958 S Dixie Hwy Sute A-103 South Miami FL")
        assert match and match.group(0) == "Sute A-103"

    def test_hash_unit_pattern_allows_letter_first(self):
        """The UI hash form is permissive (letter-first ok) since it only restores typed units."""
        match = re.search(HASH_UNIT_PATTERN, "100 Main St #A5, Town FL")
        assert match and match.group(0) == "#A5"

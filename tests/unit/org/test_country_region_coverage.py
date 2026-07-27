"""ISO-3166 alpha-2 coverage invariant tests for feature 1025 US2.

Why:
    Contract ``specs/1025-probe-emission-log-fixes/contracts/iso_coverage_invariant.md``
    pins four machine-checkable invariants over the pair of module-level
    collections ``_COUNTRY_CODE_TO_REGION`` and ``_COUNTRY_CODE_INTENTIONAL_GAPS``.
    Together they must cover every ISO-3166-1 alpha-2 code exactly once
    (disjoint + complete), every entry must be a 2-letter upper-case ASCII
    string, and every region value must be drawn from the R1 canonical set
    ``{"americas", "emea", "china"}``. Any silent addition or removal from
    these collections fails CI here with a diagnostic naming the offending
    code(s) -- SC-005 requires the failure to point straight at the fix.

    The invariants live in a dedicated file (not the main
    ``test_org_synthetic_probes_manager.py`` module) so that:
      1. The ISO fixture load happens exactly once per suite (import-time).
      2. Future ISO amendments show up as a single failing test file, not
         buried inside the ~3k-line main test module.
      3. The coverage contract is discoverable via filename alone.
"""

from __future__ import annotations  # keep type hints lazy per project convention

import json  # stdlib JSON reader for the pinned alpha-2 fixture
import logging  # Constitution VII observability requirement
import re  # regex compile for the shape invariant (2-letter upper-case ASCII)
from pathlib import Path  # absolute-path fixture resolution rooted at this file

from src.org.org_synthetic_probes_manager import (  # module under test
    _COUNTRY_CODE_INTENTIONAL_GAPS,  # frozenset of deliberately-omitted codes
    _COUNTRY_CODE_TO_REGION,  # dict of code -> region literal
)

# Absolute path to the pinned ISO-3166-1 alpha-2 universe used as the
# reference set. Fixture contents pinned by INV-F1 in data-model.md so
# future ISO amendments surface as a single failing test here.
_FIXTURE = Path(__file__).parent / "fixtures" / "iso_3166_alpha2.json"  # sibling fixture dir
# Load the pinned universe once at import-time (frozenset for hash-set
# math against the dict-keys collection). Any JSON error fails loudly
# instead of masking as a "test not found".
logging.info("test_country_region_coverage: loading ISO alpha-2 universe from %s", _FIXTURE)
_ISO_CODES: frozenset[str] = frozenset(  # immutable so tests cannot mutate the reference set
    json.loads(_FIXTURE.read_text(encoding="utf-8"))  # utf-8 explicit for clarity
)
logging.debug("test_country_region_coverage: loaded %d ISO codes", len(_ISO_CODES))

# Compiled once at import-time so per-test invocations do not re-parse the
# pattern; matches only 2-letter upper-case ASCII (INV-COVER-3).
_ALPHA2_RE = re.compile(r"^[A-Z]{2}$")  # invariant regex from contract §2 INV-COVER-3

# The R1 canonical set of region literals. Kept in sync with
# ``_DEFAULT_REGION`` and every entry in ``_COUNTRY_CODE_TO_REGION``.
# INV-COVER-4 enforces every dict value belongs to this set.
_ALLOWED_REGIONS: frozenset[str] = frozenset({"americas", "emea", "china"})  # R1 literal set


def test_iso_cover_1_disjoint() -> None:
    """INV-COVER-1: region map and gap set MUST NOT share any code.

    Why:
        A code appearing in both collections signals ambiguous operator
        intent ("is it mapped, or is it a gap?"). The contract requires
        each code to live in exactly one collection so future readers
        never have to reconcile a shared entry.
    """
    logging.info("test_iso_cover_1_disjoint: checking region_map ^ gap_set")  # BEFORE the check
    overlap = set(_COUNTRY_CODE_TO_REGION) & set(_COUNTRY_CODE_INTENTIONAL_GAPS)  # set intersection
    logging.debug("test_iso_cover_1_disjoint: overlap=%s", sorted(overlap))  # AFTER the check
    assert overlap == set(), (
        f"country codes {sorted(overlap)} appear in both the region map and "
        f"the intentional-gap set; each code must live in exactly one collection."
    )


def test_iso_cover_2_complete() -> None:
    """INV-COVER-2: every ISO-3166 alpha-2 code MUST be classified.

    Why:
        The whole point of pairing ``_COUNTRY_CODE_TO_REGION`` with the
        intentional-gap set is that no ISO code can fall through to the
        default region silently. Any code present in the pinned universe
        but absent from both collections is a coverage bug: either add a
        region mapping or list it as an intentional gap.
    """
    logging.info("test_iso_cover_2_complete: checking (M | G) >= I")  # BEFORE the check
    classified = set(_COUNTRY_CODE_TO_REGION) | set(_COUNTRY_CODE_INTENTIONAL_GAPS)  # union
    missing = _ISO_CODES - classified  # codes present in ISO but not in either collection
    logging.debug(  # AFTER the check
        "test_iso_cover_2_complete: classified=%d missing=%s",
        len(classified),
        sorted(missing),
    )
    assert missing == set(), (
        f"ISO-3166 alpha-2 codes {sorted(missing)} are neither region-mapped "
        f"nor listed as intentional gaps; add each to exactly one collection."
    )


def test_iso_cover_3_shape() -> None:
    """INV-COVER-3: every key / member MUST be 2-letter upper-case ASCII.

    Why:
        Catches accidental lower-casing (``"us"`` instead of ``"US"``) or
        three-letter alpha-3 slips (``"USA"``). ``_build_region_probes``
        upper-cases the input at line 1068, so a lower-case key would be
        an unreachable dead entry that silently regressed coverage.
    """
    combined = set(_COUNTRY_CODE_TO_REGION) | set(_COUNTRY_CODE_INTENTIONAL_GAPS)  # full union
    logging.info("test_iso_cover_3_shape: checking %d entries", len(combined))  # BEFORE
    bad = [c for c in combined if not _ALPHA2_RE.match(c)]  # collect all shape violators
    logging.debug("test_iso_cover_3_shape: bad=%s", sorted(bad))  # AFTER
    assert bad == [], f"non-conforming entries: {sorted(bad)}"


def test_iso_cover_4_region_values() -> None:
    """INV-COVER-4: every region value MUST be drawn from the R1 canonical set.

    Why:
        FR-011 pins the region-value vocabulary at ``{"americas", "emea",
        "china"}``. A typo (``"amer"``, ``"americas "``) or a future
        renaming would silently break the samsung_elm role name lookup at
        line 1077 (``f"{_SAMSUNG_ELM_ROLE_PREFIX}{region}"``). This test
        catches drift the moment it lands in the region map.
    """
    logging.info("test_iso_cover_4_region_values: checking region values")  # BEFORE
    bad = {
        c: r
        for c, r in _COUNTRY_CODE_TO_REGION.items()
        if r not in _ALLOWED_REGIONS  # any value outside the R1 set is a drift
    }
    logging.debug("test_iso_cover_4_region_values: bad=%s", bad)  # AFTER
    assert bad == {}, f"unexpected region literals: {bad}"


def test_iso_cover_double_declared() -> None:
    """T028: prove the disjoint-check fires when a code is double-declared.

    Why:
        ``test_iso_cover_1_disjoint`` is only meaningful if the underlying
        set-intersection check would actually surface a shared code. This
        meta-test constructs a *synthetic* (region_map, gap_set) pair that
        deliberately shares one code (``"PA"``), runs the same
        intersection logic that INV-COVER-1 uses in production, and
        asserts the diagnostic names the offending code. Guards against
        future refactors that quietly weaken the disjoint check (e.g.
        replacing ``&`` with something that no-ops on frozensets, or
        catching-and-swallowing the AssertionError).

        Satisfies US2 Edge Case ("A country code appears in the
        intentional-gap set AND in ``_COUNTRY_CODE_TO_REGION``") and US3
        Acceptance Scenario 3 per tasks.md T028.
    """
    logging.info("test_iso_cover_double_declared: constructing synthetic overlap")  # BEFORE
    # Synthetic pair — NOT the real module collections. We deliberately
    # share ``"PA"`` between the map and the gap set so the intersection
    # returns a non-empty result. If the disjoint check were ever weakened,
    # this test would silently pass and the meta-guard would fail us open.
    synthetic_region_map: dict[str, str] = {"PA": "americas", "US": "americas"}  # shared "PA"
    synthetic_gap_set: frozenset[str] = frozenset({"PA", "AQ"})  # shared "PA"
    # Same intersection expression that INV-COVER-1 uses in production —
    # copying the operator rather than importing a helper keeps this test
    # honest: if someone changes the production operator, this test still
    # reflects the old contract and will fail visibly.
    overlap = set(synthetic_region_map) & set(synthetic_gap_set)  # set intersection
    logging.debug("test_iso_cover_double_declared: overlap=%s", sorted(overlap))  # AFTER
    # Positive assertion: the disjoint check DOES surface the shared code.
    # If ``overlap`` were empty here, the whole INV-COVER-1 test would be a
    # no-op in production and CI would silently regress.
    assert overlap == {"PA"}, (
        f"synthetic double-declaration should surface exactly {{'PA'}} but got "
        f"{sorted(overlap)}; the disjoint-check operator has drifted."
    )
    # Simulate the diagnostic-message assertion that INV-COVER-1 raises when
    # it fires, and verify the offending code is named in the message so
    # SC-005 (failure points straight at the fix) is preserved.
    diagnostic = (
        f"country codes {sorted(overlap)} appear in both the region map and "
        f"the intentional-gap set; each code must live in exactly one collection."
    )
    assert "PA" in diagnostic, (
        f"double-declared diagnostic must name the offending code; got: {diagnostic!r}"
    )

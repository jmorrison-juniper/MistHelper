# Contract: ISO-3166 Alpha-2 Coverage Invariant

**Feature**: `1025-probe-emission-log-fixes`
**Scope**: `_COUNTRY_CODE_TO_REGION` and `_COUNTRY_CODE_INTENTIONAL_GAPS`
in `src/org/org_synthetic_probes_manager.py`
**Related FRs**: FR-005, FR-006, FR-007, FR-008, SC-005

This is the CI-enforced completeness invariant on country-code
classification. It guarantees that no valid ISO-3166-1 alpha-2 code can
appear on a Mist site record and silently be classified as "unknown" — every
code is either mapped to a region or explicitly listed as an intentional gap,
and a single test guards both properties.

---

## 1. The three sets

Let:
- `M := set(_COUNTRY_CODE_TO_REGION.keys())` — codes with an explicit
  region mapping (dict).
- `G := _COUNTRY_CODE_INTENTIONAL_GAPS` — codes deliberately excluded
  (frozenset).
- `I := frozenset(load_iso_3166_alpha2())` — the reference universe
  loaded from `tests/unit/org/fixtures/iso_3166_alpha2.json` (fixture
  contents pinned by INV-F1 in `data-model.md`).

## 2. Invariants

- **INV-COVER-1 (disjoint)**: `M & G == frozenset()`
  No code may live in both collections. Attempts to do so signal
  operator-intent ambiguity ("is it mapped, or is it a gap?").

- **INV-COVER-2 (complete)**: `(M | G) >= I`
  Every ISO alpha-2 code appears in at least one of the two collections.
  (The invariant is `>=` rather than `==` to permit `M` or `G` to include
  historical / transitional codes that may not be in the current 249-code
  list, though the initial expectation is exact equality.)

- **INV-COVER-3 (shape)**: Every element of `M | G` matches the regex
  `^[A-Z]{2}$`. This catches accidental lower-casing or three-letter
  entries.

- **INV-COVER-4 (region values)**: Every value in
  `_COUNTRY_CODE_TO_REGION.values()` is one of the string literals
  `"americas"`, `"emea"`, `"china"` (R1).

---

## 3. Test contract

```python
# tests/unit/org/test_country_region_coverage.py

import json
import re
from pathlib import Path

from src.org.org_synthetic_probes_manager import (
    _COUNTRY_CODE_TO_REGION,
    _COUNTRY_CODE_INTENTIONAL_GAPS,
)

_FIXTURE = Path(__file__).parent / "fixtures" / "iso_3166_alpha2.json"
_ISO_CODES = frozenset(json.loads(_FIXTURE.read_text(encoding="utf-8")))
_ALPHA2_RE = re.compile(r"^[A-Z]{2}$")
_ALLOWED_REGIONS = {"americas", "emea", "china"}


def test_iso_cover_1_disjoint():
    """INV-COVER-1: region map and gap set MUST NOT share any code."""
    overlap = set(_COUNTRY_CODE_TO_REGION) & set(_COUNTRY_CODE_INTENTIONAL_GAPS)
    assert overlap == set(), (
        f"country codes {sorted(overlap)} appear in both the region map and "
        f"the intentional-gap set; each code must live in exactly one collection."
    )


def test_iso_cover_2_complete():
    """INV-COVER-2: every ISO-3166 alpha-2 code is classified."""
    classified = set(_COUNTRY_CODE_TO_REGION) | set(_COUNTRY_CODE_INTENTIONAL_GAPS)
    missing = _ISO_CODES - classified
    assert missing == set(), (
        f"ISO-3166 alpha-2 codes {sorted(missing)} are neither region-mapped "
        f"nor listed as intentional gaps; add each to exactly one collection."
    )


def test_iso_cover_3_shape():
    """INV-COVER-3: all keys/members are 2-letter upper-case ASCII."""
    combined = set(_COUNTRY_CODE_TO_REGION) | set(_COUNTRY_CODE_INTENTIONAL_GAPS)
    bad = [c for c in combined if not _ALPHA2_RE.match(c)]
    assert bad == [], f"non-conforming entries: {sorted(bad)}"


def test_iso_cover_4_region_values():
    """INV-COVER-4: region values are drawn from the allowed set."""
    bad = {c: r for c, r in _COUNTRY_CODE_TO_REGION.items() if r not in _ALLOWED_REGIONS}
    assert bad == {}, f"unexpected region literals: {bad}"
```

---

## 4. Failure diagnostics

Each of the four tests fails with a diagnostic that names the specific
offending code(s) — an operator or contributor reading a CI failure gets
the exact set of items to fix, not a boolean "test failed" message. This
matches SC-005's requirement that "the test fails CI on any silent
addition or removal".

## 5. What this contract does NOT cover

- It does NOT validate that the classification of any given code is
  "correct" in a policy sense — only that each code is classified. If
  operators want to argue that `KY` should map to `emea` instead of
  `americas`, that is a spec-level policy discussion, not a test failure.
- It does NOT block the fixture from being updated when ISO publishes an
  amendment. Updating `iso_3166_alpha2.json` will *reveal* missing codes
  via `test_iso_cover_2_complete`, which is the desired behaviour.
- It does NOT constrain any collection outside `_COUNTRY_CODE_TO_REGION`
  and `_COUNTRY_CODE_INTENTIONAL_GAPS` (e.g. Samsung ELM role name
  suffixes are a separate concern).

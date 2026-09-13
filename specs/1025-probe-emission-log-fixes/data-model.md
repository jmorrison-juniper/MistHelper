# Phase 1 Data Model: Menu 206 Probe-Emission Log Quality & Correctness Fixes

**Feature**: `1025-probe-emission-log-fixes`
**Date**: 2026-07-26

This feature adds no persistent-storage entities. All "entities" below are
in-memory Python objects with lifetimes bounded by a single invocation of
`manage_org_synthetic_probes()`. The purpose of this document is to pin the
*shape* and *lifetime* of each so the implementation and its tests agree on
contract.

---

## 1. `_COUNTRY_CODE_TO_REGION` — extended module constant (existing)

**Type**: `Mapping[str, str]` (implemented as a plain `dict[str, str]` at
module scope; effectively read-only after module import).

**Lifetime**: Module scope; created at import, never mutated.

**Keys**: ISO-3166-1 alpha-2 country codes, upper-case (e.g. `"US"`).

**Values**: One of the string literals `"americas"`, `"emea"`, `"china"`
(R1 — these are the concrete literals downstream Samsung-ELM role selection
matches against; DO NOT introduce `"amer"` / `"apac"`).

**Existing entries (from spec 1024, must not change)**:
- `US`, `CA`, `MX` → `"americas"`
- `AR`, `BR`, `CL`, `CO`, `PE`, `VE` → `"americas"`
- `CN`, `HK`, `MO`, `TW` → `"china"`

**New entries added by this feature (FR-005 + FR-006)**:

*Central America (all → `"americas"`)*:
- `BZ` — Belize
- `CR` — Costa Rica
- `GT` — Guatemala
- `HN` — Honduras
- `NI` — Nicaragua
- `PA` — Panama
- `SV` — El Salvador

*Caribbean (all → `"americas"`)*:
- `AG` — Antigua and Barbuda
- `AI` — Anguilla
- `AW` — Aruba
- `BB` — Barbados
- `BL` — Saint Barthélemy
- `BM` — Bermuda
- `BQ` — Bonaire, Sint Eustatius and Saba
- `BS` — Bahamas
- `CU` — Cuba
- `CW` — Curaçao
- `DM` — Dominica
- `DO` — Dominican Republic
- `GD` — Grenada
- `GP` — Guadeloupe
- `HT` — Haiti
- `JM` — Jamaica
- `KN` — Saint Kitts and Nevis
- `KY` — Cayman Islands
- `LC` — Saint Lucia
- `MF` — Saint Martin (French part)
- `MQ` — Martinique
- `MS` — Montserrat
- `PR` — Puerto Rico
- `SX` — Sint Maarten (Dutch part)
- `TC` — Turks and Caicos Islands
- `TT` — Trinidad and Tobago
- `VC` — Saint Vincent and the Grenadines
- `VG` — Virgin Islands (British)
- `VI` — Virgin Islands (U.S.)

*Remaining South America (all → `"americas"`)*:
- `BO` — Bolivia
- `EC` — Ecuador
- `FK` — Falkland Islands
- `GF` — French Guiana
- `GY` — Guyana
- `PY` — Paraguay
- `SR` — Suriname
- `UY` — Uruguay

The precise final list is confirmed at implementation time against the
`iso_3166_alpha2.json` fixture (R3) via the coverage regression test. Any
code the operator team wishes to route via geodesic fallback rather than
force to a region belongs in `_COUNTRY_CODE_INTENTIONAL_GAPS` below, not
absent.

**Invariants**:
- **INV-M1**: All values are one of `{"americas", "emea", "china"}`.
- **INV-M2**: All keys are exactly two upper-case ASCII letters (validated
  by the coverage test).
- **INV-M3**: Disjoint from `_COUNTRY_CODE_INTENTIONAL_GAPS` (see §2).

---

## 2. `_COUNTRY_CODE_INTENTIONAL_GAPS` — new module constant

**Type**: `frozenset[str]`

**Lifetime**: Module scope; created at import, never mutated.

**Members**: ISO-3166-1 alpha-2 codes that are *deliberately* excluded from
the region map. Every member carries an inline `#` comment naming the
reason (Constitution VI, non-negotiable). Candidate rationales:
- Uninhabited or effectively-uninhabited territory (no Mist site can
  plausibly exist there): e.g. `AQ` (Antarctica), `BV` (Bouvet Island),
  `HM` (Heard/McDonald), `TF` (French Southern Territories).
- Codes reserved but not assigned to a tenant country (any that appear in
  ISO-3166-1 but which Zscaler documentation does not enumerate).
- Codes for which the operator team deliberately prefers geodesic-fallback
  routing (documented case-by-case).

**Concrete initial contents** are finalized at implementation time by
running `set(iso_3166_alpha2.json) − set(_COUNTRY_CODE_TO_REGION)` and
manually classifying each residual code with a same-line comment. The
coverage regression test then locks the classification in.

**Invariants**:
- **INV-G1**: All members are exactly two upper-case ASCII letters.
- **INV-G2**: Disjoint from `_COUNTRY_CODE_TO_REGION.keys()` (INV-M3
  restated from the gap side).
- **INV-G3**: `_COUNTRY_CODE_TO_REGION.keys() | _COUNTRY_CODE_INTENTIONAL_GAPS
  == frozenset(iso_3166_alpha2.json)` — full ISO alpha-2 coverage
  (FR-008 / SC-005).

---

## 3. Per-run dedup state (ephemeral)

**Type**: A pair of `set[str]` objects, plus (potentially) a small dataclass
or `TypedDict` bundling them for clean parameter-passing. Exact shape TBD
at implementation time; the contract is that both sets are:
- Created empty in `manage_org_synthetic_probes()` before any per-site work
  begins.
- Mutated only by the load-time WARNING emission helpers.
- Discarded at function return (FR-012).

**Contents**:
- `warned_cenr_hosts: set[str]` — hostnames from
  `catalogue_hosts − cenr_observed_hosts` for which a WARNING has been
  emitted this run.
- `warned_unmapped_codes: set[str]` — ISO alpha-2 codes present in the
  loaded site set that resolve to neither `_COUNTRY_CODE_TO_REGION` nor
  `_COUNTRY_CODE_INTENTIONAL_GAPS`, for which a WARNING has been emitted
  this run.

**Lifetime**: Bounded by one invocation of `manage_org_synthetic_probes()`.
No persistence, no cross-invocation sharing, no thread-local caching.

**Invariants**:
- **INV-D1**: Neither set exists before the function call and neither
  survives after return (verifiable in unit test via `gc.get_referrers`
  or by construction — the sets are local variables).
- **INV-D2**: Membership in either set is idempotent: adding a host or code
  that is already a member is a no-op that produces no additional log
  output. This is what makes the WARNING count `≤ |missing_set|`.
- **INV-D3**: The two sets are only *read* by the WARNING emitter; probe
  payload construction (`_build_probe_set`, `_probe_target`) does NOT read
  them and therefore INV-1 byte-stability is preserved by construction.

---

## 4. Test-only entity: `iso_3166_alpha2.json` fixture

**Location**: `tests/unit/org/fixtures/iso_3166_alpha2.json`

**Format**: A JSON array of exactly 249 two-letter upper-case strings —
the current ISO-3166-1 alpha-2 code list.

```json
["AD", "AE", "AF", "AG", "AI", "AL", "AM", "AO", "AQ", "AR", ... , "ZW"]
```

**Provenance**: Manually curated from the ISO-3166 Maintenance Agency
publication at the date shown in the top-of-file comment (spec date
2026-07-26). Updated in a targeted PR when ISO publishes an amendment
(next update expected ~2030 per historical cadence).

**Consumer**: `tests/unit/org/test_country_region_coverage.py` (new).

**Invariant**:
- **INV-F1**: File contents parse as `list[str]` of length 249; every
  entry matches `^[A-Z]{2}$`.

---

## 5. Test-only entity: `latam_caribbean_org.json` fixture

**Location**: `tests/unit/org/fixtures/latam_caribbean_org.json`

**Format**: Synthetic Mist-shaped org payload containing at minimum one
site per code from FR-005: `{PA, BS, HT, DO, GT, CU, CR, HN}`. Reuses the
site-record schema already established by `smoke_org.json` (from spec
1024) so the same loading helpers work unchanged.

**Consumer**: `test_org_synthetic_probes_manager.py` new US2 test cases.

**Invariant**:
- **INV-F2**: Every site record's `country_code` is present in
  `_COUNTRY_CODE_TO_REGION` after this feature ships; no site record
  triggers the intentional-gap or unmapped path (that behaviour is
  exercised by a separate, smaller unit test that constructs a
  synthetic site dict inline).

---

## Relationships

```text
                   +----------------------------------+
                   | iso_3166_alpha2.json (fixture)   |
                   +----------------------------------+
                                     |
                                     v
+--------------------------+  disjoint  +---------------------------------+
| _COUNTRY_CODE_TO_REGION  |<---------->| _COUNTRY_CODE_INTENTIONAL_GAPS  |
| (dict[str, str])         |  union==   | (frozenset[str])                |
+--------------------------+  fixture   +---------------------------------+
              ^                                       ^
              | read at load-time                     | read at load-time
              |                                       |
      +--------------------------------------------------------+
      |  manage_org_synthetic_probes(mist_session, org_id)      |
      |    - constructs warned_cenr_hosts: set[str]             |
      |    - constructs warned_unmapped_codes: set[str]         |
      |    - passes both to _emit_load_time_warnings(...)       |
      |    - passes both to _probe_target(...) chain            |
      |    - discards both at return                            |
      +--------------------------------------------------------+
              |
              v
      +---------------------------+
      | data/script.log (append)  |
      |   at most |missing| WARNs |
      +---------------------------+
```

## No schema changes

- No change to `synthetic_test.custom_probes` payload shape (INV-1
  byte-stable).
- No new JSONL telemetry sink added by this feature. If a run-summary
  JSONL is added in a future patch, it must reuse the existing
  `TelemetryEmitter` under `data/` per FR-014.

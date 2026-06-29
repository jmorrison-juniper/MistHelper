# Phase 0 Research: Site Address Audit from CSV

All NEEDS CLARIFICATION items and spec Open Questions resolved here. Each entry:
**Decision / Rationale / Alternatives considered**.

---

## R-001: Mist geocoding source (the central constraint)

**Decision**: There is **no Mist geocoding REST endpoint**. Do not call
`apisession.get("/api/v1/utils/geocoding", ...)`. Resolution is tiered across free
sources only.

**Rationale**: Verified absent from the `mistapi` SDK (`api/v1/utils/` contains
only SMS-test endpoints) and from both `documentation/mist-api-openapi3*.{json,yaml}`
specs. The dashboard's address autocomplete is Google Places invoked client-side
with a frontend key that cannot be reused server-side.

**Alternatives considered**: (a) Paid geocoder (Google/Mapbox) -- rejected: no new
paid dependencies. (b) Scrape the frontend key -- rejected: ToS/security risk. (c)
Assume the endpoint exists -- rejected: returns 404, was the original draft's bug.

---

## R-002: Address resolution tiers

**Decision**: Three free tiers with a SQLite cache checked first.
- **Tier 1 (internal, no network)**: Normalize and compare Mist site address vs.
  CSV address vs. SNMP location. The customer CSV already carries suite/unit data
  on most rows (`Unit 200`, `Suite 1019A`), so suite truth is mostly internal. This
  catches the common "Mist missing the suite" case with zero external calls.
- **Tier 2 (Nominatim, free, keyless, <=1 req/sec)**: Reuse `NominatimValidator`
  from `src/utils/address_utils.py`. Validates the base street; drives `WRONG_STREET`.
  OSM does not reliably carry US retail suite numbers, so it validates street not unit.
- **Tier 3 (optional, OFF by default, `--ui-geocode`)**: `MistUIGeocoder` drives the
  live Mist dashboard site-edit autocomplete via Playwright, types
  `"{business_name} {address}"`, captures the top Google-Places suggestion. Only
  free route to Google-quality retail suites. Selective (e.g. `AMBIGUOUS` rows only),
  bounded by per-lookup timeout + max-lookups-per-run cap.

**Rationale**: Internal-first is instant and resolves most rows; Nominatim is the
keyless street validator; the UI tier is the operator-authorized escape hatch for
suite-grade truth without a paid API.

**Alternatives considered**: Nominatim-only -- rejected: cannot recover suites.
UI-only -- rejected: too slow/fragile for every row.

---

## R-003: Reuse `NominatimValidator` (do not reinvent Tier 2)

**Decision**: Tier 2 calls the existing `NominatimValidator` (`address_utils.py`).
Its constants already satisfy ToS: `USER_AGENT = "MistHelper/1.0 (address validation)"`,
`RATE_LIMIT_DELAY = 1.1`, retry logic, `skip_ssl_verify` support, and a
`validate(mist_address: dict, comparison_address: dict) -> dict` entry point.

**Rationale**: Constitution forbids wrapper duplication; the validator already
honors the <=1 req/sec rule and the User-Agent convention (FR-014, security section).
`AddressResolver` composes it, passing dict-shaped addresses
(`{"address","city","state","zip"}`).

**Alternatives considered**: New Nominatim client -- rejected (duplication, ToS
drift risk). Direct `requests` calls -- rejected (re-implements existing retry/rate
logic).

---

## R-004: Site matching strategy (serial golden key + fuzzy fallback)

**Decision**: Serial number is the golden key. Flow: CSV col 0 (serial) ->
Mist device inventory lookup -> `device.site_id` -> site record. On miss, fall back
to `rapidfuzz.process.extractOne(query, choices, score_cutoff=85)` over concatenated
site name+address. On miss of both -> `UNMATCHED`. Threshold is a constant,
overridable via `.env` `FUZZY_MATCH_THRESHOLD`. Device-found-but-`site_id`-null ->
`UNMATCHED` (reason "device unassigned").

**Rationale**: Serial is unambiguous; fuzzy recovers typo'd serials/addresses; the
85% cutoff matches the spec and the existing comparator's tolerance.

**Alternatives considered**: Fuzzy-first -- rejected (slower, less precise). MAC/name
keying -- rejected (CSV has no MAC; names are non-unique).

---

## R-005: rapidfuzz + scourgify optional imports

**Decision**: Import both through `GlobalImportManager`'s existing optional-import
pattern (`MistHelper.py`: `rapidfuzz` -> `fuzz`; `usaddress-scourgify` -> `scourgify`).
If `rapidfuzz` absent: disable fuzzy fallback, log one startup WARNING, rows that
would have fuzzy-matched become `UNMATCHED`. If `scourgify` absent: regex-based
normalization fallback (already present in `AddressUtils`), one startup WARNING.

**Rationale**: Constitution + CR-007 require graceful degradation; the manager
already hoists these globals with direct-import fallbacks
(`_hoist_rapidfuzz_global`, `_hoist_scourgify_global`).

**Alternatives considered**: Hard dependency -- rejected (breaks "no new required
deps"). Local try/except per module -- rejected (duplicates the central manager).

---

## R-006: SNMP location enrichment

**Decision**: For each matched site pull both `site["vars"]["snmp_location"]` and
`snmp_config.location` (from site settings). If both present, prefer
`snmp_config.location` (NOC-authoritative). If neither, SNMP Location column shows
`(none)`. Never raise on absence.

**Rationale**: Matches FR-005 and the spec's authority ordering; SNMP often carries
a richer address than the main site record.

**Alternatives considered**: vars-only -- rejected (misses the OID field). Raising on
absence -- rejected (most sites lack one or both).

---

## R-007: Geocoding cache (SQLite in mist_data.db)

**Decision**: Additive table `geocoding_cache` in `data/mist_data.db`. DDL via
`CREATE TABLE IF NOT EXISTS`; upsert via `INSERT OR REPLACE`. Key = normalized
(lowercased, whitespace-collapsed) query string. Checked before any Tier 2/3 call.
DB located via
`os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..","..","..","mist_data.db"))`
-- but note the constitution mandates the DB lives at `data/mist_data.db`; the
resolver MUST resolve to that canonical `data/` path (see PLAN note below).

**Rationale**: FR-007 + SC-003 (warm-cache rerun < 30 s, zero new external calls).
Upsert avoids duplicate-key errors on rerun.

**PLAN note for tasks**: The spec's AI-hint path walks up from the module to a
repo-root `mist_data.db`, but the constitution fixes the DB at `data/mist_data.db`.
The implementation MUST target `data/mist_data.db` (constitution wins). Capture the
exact path constant in one place in `AddressResolver`.

**Alternatives considered**: New cache DB file -- rejected (constitution: single
`data/mist_data.db`). In-memory cache -- rejected (no cross-run persistence).

**Cache schema** (see data-model.md / geocoding-cache-contract.md):
`query_key TEXT PRIMARY KEY, canonical_addr TEXT, source TEXT, confidence REAL, raw_json TEXT, cached_at TEXT`.

---

## R-008: Business name resolution

**Decision**: Read `BUSINESS_NAME` from `.env`. If blank, prompt once via
`InputUtils.safe_input("Enter business name ... or press Enter to skip: ", context=...)`.
If skipped, geocode with the raw address only (no business prefix). Runtime-only;
never persisted; not logged at INFO.

**Rationale**: FR query construction + security section (treated as non-secret config,
not logged). Private/internal addresses have no public business listing.

**Alternatives considered**: Mandatory business name -- rejected (breaks private
addresses). Persisting the typed value -- rejected (security section forbids).

---

## R-009: OQ-001 -- Tier 3 dashboard authentication

**Decision**: v1 uses **interactive operator login** in the Playwright-launched
browser at run start (spec option a). No new secrets in `.env`. Scripted login from
`.env` credentials (option b) and cookie/profile reuse (option c) are documented as
later opt-ins.

**Rationale**: Lowest risk, no new credential storage, matches Safety-First. The
operator already has an authenticated dashboard session; we borrow it interactively.

**Alternatives considered**: (b) scripted login -- deferred (new secret surface). (c)
profile reuse -- deferred (environment-fragile).

---

## R-010: OQ-002 -- UI selector stability + fail-soft

**Decision**: Capture current site-edit address-field selectors in
`contracts/ui-geocoder-contract.md` with a documented re-capture procedure. Tier 3
MUST fail soft: any selector/timeout/exception logs a WARNING and classifies the row
`NO_RESULT` (or `AMBIGUOUS` when multiple suggestions) -- never crashes the audit.
Bounds: per-lookup timeout (default 20 s, `.env`), max lookups/run (default 50, `.env`).

**Rationale**: Dashboard DOM is not contract-stable; the audit's value is the full
table, so one flaky lookup must not abort the run.

**Alternatives considered**: Hard-fail on selector miss -- rejected (one DOM change
breaks the whole feature). Unbounded retries -- rejected (runaway runtime).

---

## R-011: Classification logic placement (5-Item Rule)

**Decision**: `_classify(mist_addr, csv_addr, snmp_loc, resolver_result)` is a
private method on `AddressAuditEngine` (<=25 lines) that delegates to helpers
(`_addresses_agree()`, `_has_suite_discrepancy()`, `_pick_more_specific()`). `run()`
splits into `_load_csv()`, `_match_sites()`, `_enrich_and_resolve()`,
`_classify_and_render()`. `AddressResolver.resolve()` splits into `_compare_internal()`,
`_validate_nominatim()`, `_build_query_key()`, `_from_cache()`, `_to_cache()`.

**Rationale**: Keeps every method <=5 params / 25 lines / 5 blocks (CR-005).

**Alternatives considered**: Monolithic `run()`/`resolve()` -- rejected (violates the
method-level Five-Item Rule).

---

## R-012: Menu registration + read-only guardrails

**Decision**: Two additive lines in `MistHelper.py`: an import of `AddressAuditEngine`
(in the existing `src.site.*` import block) and one menu dict entry in the
safe-export range 1-59 mapping to `AddressAuditEngine.run`. `AddressCorrector` is a
stub (all methods `raise NotImplementedError`) and is **not** registered. Zero Mist
writes anywhere.

**Rationale**: FR-001/011/012; additive-only change keeps existing paths untouched.

**Open item (PLAN-001)**: A flat scan of quoted-integer keys in `MistHelper.py`
shows dense usage 0-194; the implementation MUST confirm a genuinely free key in the
specific safe-export dict and rely on the framework's startup collision check.

**Alternatives considered**: Wrapper function in `MistHelper.py` -- rejected
(Class-Based, no-wrapper principle). Registering write-back now -- rejected (FR-011).

---

## R-013: Progress + table rendering

**Decision**: `tqdm` progress bar around the resolution loop (suppressed when stdout
is non-interactive/piped). `ComparisonTableRenderer` builds a prettytable with 7
columns and `max_width = 40` on SNMP Location and Suggested Address; full untruncated
values flow to `AddressAuditReporter` for the CSV. Post-table prompt offers
`[1] Save CSV` / `[q] Quit` via `safe_input()` in a loop.

**Rationale**: UI Behavior section + FR-009/010; truncation is terminal-only.

**Alternatives considered**: No progress bar -- rejected (200+ row runs feel hung).
Truncating the CSV too -- rejected (CSV is the shareable artifact, must be full).

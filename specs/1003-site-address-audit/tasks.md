---
description: "Task list for Site Address Audit from CSV"
---

# Tasks: Site Address Audit from CSV

**Input**: Design documents from `specs/1003-site-address-audit/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (class-contracts.md, cli-contract.md, geocoding-cache-contract.md, ui-geocoder-contract.md)
**Branch**: `1003-site-address-audit`

**Tests**: Unit tests ARE requested (spec Test Plan, mandatory). Each user story carries its own test tasks under `tests/unit/site/address_audit/`. Maintain >=70% coverage.

**Organization**: Tasks grouped by user story (P1 -> P4) for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete dependencies)
- **[Story]**: US1 / US2 / US3 / US4 (maps to spec.md user stories)
- Exact file paths included in every task

## Baked-in standards (apply to EVERY production task — non-negotiable)

- Inline why-comment on every executable line (CR-001).
- `logging.info` before / `logging.debug` after every meaningful action (CR-002).
- ASCII-only log strings; `%`-style lazy args in logging calls — f-strings in `logging.*` are BANNED (ruff rule G).
- All input via `InputUtils.safe_input(...)`; no bare `input()` (CR-003).
- Class-based only; one class per module; full-word identifiers; no AI marker text.
- 5-Item Rule: <=5 params, <=25 lines, <=5 nested blocks per method.
- Paths via `os.path.join` / `pathlib`; line length 120; Python 3.13+.
- Read-only: zero Mist writes anywhere in this release.
- Quality gates per task group: `python -m py_compile`, `ruff check`, `black --check` must pass clean.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Subpackage skeleton and test scaffolding.

- [X] T001 Create subpackage `src/site/address_audit/__init__.py` exporting `MistUIGeocoder`, `ResolverResult`, `UIGeocoderConfig` — DONE (commit 3ef899f; will be extended in Phase 2 to also export `AddressAuditEngine` for menu registration).
- [X] T002 [P] Create test packages `tests/unit/site/__init__.py` and `tests/unit/site/address_audit/__init__.py` — DONE (commit 3ef899f).

**Checkpoint**: Package and test directories exist; gates green.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared dataclasses every user story depends on. NO story work can begin until this phase is complete.

**⚠️ CRITICAL**: Blocks all user stories.

- [X] T003 [P] Add `ResolverResult` and `UIGeocoderConfig` dataclasses in `src/site/address_audit/models.py` per data-model.md — DONE (commit 3ef899f).
- [ ] T004 Add remaining dataclasses to `src/site/address_audit/models.py`: `AddressRow`, `MatchedSite`, `AuditResult`, `AuditCounters`, and the `ResolveCandidates` config dataclass (fields/types exactly per data-model.md and class-contracts.md `models.py` section). No behavior beyond trivial defaults; type hints required. (Extends the file alongside the two existing dataclasses from T003.)
- [ ] T005 [P] Add `ambiguous: bool` field to existing `ResolverResult` in `src/site/address_audit/models.py` if not already present, per data-model.md (drives `AMBIGUOUS` classification). Verify against the committed dataclass first; skip if already implemented.

**Checkpoint**: All entities defined; `py_compile`/`ruff`/`black` clean on `models.py`. User stories can now proceed.

---

## Phase 3: User Story 1 — Full Address Audit: CSV to Comparison Table (Priority: P1) 🎯 MVP

**Goal**: Operator drops a tab-delimited CSV into `data/`, runs the menu option, and sees a 7-column prettytable classifying every row into one of the 8 states — end-to-end, read-only, no network beyond Tier 1/Tier 2.

**Independent Test**: Place the 4-row sample CSV in `data/`; run the menu option; confirm the table renders with all four rows classified and no unhandled exceptions.

### Tests for User Story 1 (write FIRST, ensure they FAIL before implementation)

- [ ] T006 [P] [US1] `tests/unit/site/address_audit/test_csv_ingester.py`: 4-row parse -> 4 `AddressRow`; embedded-newline sanitized; empty-serial row skipped (parse_failures=1); whitespace trimmed; file-not-found -> controlled exception (logged, no crash).
- [ ] T007 [P] [US1] `tests/unit/site/address_audit/test_snmp_enricher.py`: both vars present -> returns `snmp_config.location`; only `vars["snmp_location"]` -> returns that; neither -> `None`, no exception.
- [ ] T008 [P] [US1] `tests/unit/site/address_audit/test_address_resolver.py` (Tier 1/Tier 2 only): internal candidate (CSV has suite, Mist does not) -> suite-bearing canonical, zero network; cache miss -> Nominatim (mocked) called, result returned; Nominatim empty -> `canonical_address=None` (row -> `NO_RESULT`); 1s Nominatim delay enforced (monkeypatched `time.sleep` count >=1); assert `MistUIGeocoder` NOT invoked when `ui_geocode=False` (default).
- [ ] T009 [P] [US1] `tests/unit/site/address_audit/test_comparison_display.py`: `render()` returns non-empty prettytable string; SNMP Location truncated at 40 chars; `[1]` and `[q]` options presented after table.
- [ ] T010 [P] [US1] `tests/unit/site/address_audit/test_audit_engine.py` (mocked deps): all 8 classification states reachable via distinct inputs; zero-row CSV -> empty `AuditResult` list, no exception.

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `CSVAddressIngester` in `src/site/address_audit/csv_ingester.py`: `load(path)` opens tab-delimited UTF-8 (no header), yields one `AddressRow` per valid row, returns `(rows, parse_failure_count)`; skip+count empty/non-numeric col-0 serials; file-not-found -> controlled logged exception. `sanitize_address(raw)`: strip, replace `\n`/`\r\n`/`\r` with single space, collapse repeats. Multi-file picker in `data/` via `safe_input` (indexed prompt; single file auto-selected). Per class-contracts.md.
- [ ] T012 [P] [US1] Implement `SNMPLocationEnricher` in `src/site/address_audit/snmp_enricher.py`: `enrich(site_id)` reads `site["vars"]["snmp_location"]` and `snmp_config.location`; prefer `snmp_config.location`; one present -> return it; neither -> `None`; never raises on absence; `info` before / `debug` after (which source won). Per class-contracts.md.
- [ ] T013 [US1] Implement `SiteMatchingEngine.match_serial` in `src/site/address_audit/site_matcher.py`: serial -> Mist device inventory (via `mistapi`) -> `device.site_id` -> site; hit -> `MatchedSite(match_strategy="serial", confidence=1.0)`; device found but `site_id` null -> `unmatched` (reason "device unassigned"); 429/rate-limit back-off, retry up to 3, WARNING per retry. (Fuzzy fallback deferred to US3 T024.)
- [ ] T014 [US1] Implement `AddressResolver` Tier 1 + Tier 2 in `src/site/address_audit/address_resolver.py`: `resolve(candidates: ResolveCandidates)` order = `_compare_internal` (Tier 1, zero network) -> `_validate_nominatim` (Tier 2) reusing `NominatimValidator.validate` from `src/utils/address_utils.py` (enforce <=1 req/sec via guarded `time.sleep`, reuse its User-Agent); `_build_query_key` (lowercase + collapse ws). Any exception -> log + `ResolverResult(canonical_address=None)` (FR-013, never abort). Selective Tier 3 delegation guarded so `MistUIGeocoder` is invoked ONLY when `candidates.ui_geocode is True`. (Cache methods deferred to US4 T031; SQLite read/write is a no-op pass-through in this story.)
- [ ] T015 [US1] Implement `ComparisonTableRenderer` in `src/site/address_audit/comparison_display.py`: `render(results)` builds 7-column prettytable (Site Name, Current Mist Address, CSV Address, SNMP Location, Suggested Address, Source, Issue Type) with `max_width=40` on SNMP Location + Suggested Address; returns string (also printed). `prompt_post_table(results)` prints one-line summary then loops `safe_input` offering `[1]`/`[q]` (Save-CSV wiring lands in US2 T020). Per class-contracts.md.
- [ ] T016 [US1] Implement `AddressAuditEngine` orchestrator in `src/site/address_audit/audit_engine.py`: `run(apisession, org_id)` menu entry point; split into `_load_csv` / `_match_sites` / `_enrich_and_resolve` / `_classify_and_render` (each <=25 lines, 5-Item Rule); `tqdm` progress around resolve loop (suppressed when stdout non-interactive); zero Mist writes. `apply_corrections(*args, **kwargs)` present but raises `NotImplementedError`, NOT menu-registered.
- [ ] T017 [US1] Implement 8-state classifier in `src/site/address_audit/audit_engine.py`: `_classify(mist_addr, csv_addr, snmp_loc, resolver_result)` returns exactly one of `ADDRESS_MATCH`, `MISSING_SUITE`, `WRONG_STREET`, `CSV_BETTER`, `MIST_BETTER`, `AMBIGUOUS`, `NO_RESULT`, `UNMATCHED`; delegate to `_addresses_agree(a, b)` and `_has_suite_discrepancy(base, candidate)` helpers to honor the 25-line limit. 100% row accountability (SC-002).
- [ ] T018 [US1] Extend `src/site/address_audit/__init__.py` to also export `AddressAuditEngine` (additive to the T001 exports) for menu registration.
- [ ] T019 [US1] Register the feature in `MistHelper.py` with EXACTLY TWO additive lines: (1) `import AddressAuditEngine` near other `src.site.*` imports; (2) one menu dict entry in the safe-export range 1-59 bound to `AddressAuditEngine.run`. Implementer MUST first scan the safe-export menu dict for a genuinely free integer key (keys 0-194 densely used) and rely on the startup collision check (PLAN-001). Label: "Audit site addresses from CSV -- compare Mist vs. customer data vs. web". No existing logic modified.

**Checkpoint**: MVP — CSV in `data/` renders a fully classified comparison table end-to-end; gates green; US1 tests pass.

---

## Phase 4: User Story 2 — Save Comparison Report to CSV (Priority: P2)

**Goal**: After the table renders, operator saves a timestamped, full-value CSV to `data/` for customer review.

**Independent Test**: After table renders, select `[1] Save comparison as CSV`; confirm `data/address_audit_*.csv` exists with a header row and one data row per table entry.

### Tests for User Story 2

- [ ] T020 [P] [US2] `tests/unit/site/address_audit/test_audit_reporter.py`: `save()` writes CSV to temp dir with expected 7-column header; filename contains `YYYYMMDD_HHMMSS`; all 8 classification states appear in written CSV when present.

### Implementation for User Story 2

- [ ] T021 [US2] Implement `AddressAuditReporter` in `src/site/address_audit/audit_reporter.py`: `save(results, output_dir="data")` -> `os.makedirs(exist_ok=True)`, timestamped `address_audit_YYYYMMDD_HHMMSS.csv`, header matching the 7 table columns, FULL (untruncated) values; path via `os.path.join`; returns written path. Per class-contracts.md.
- [ ] T022 [US2] Wire the `[1] Save CSV` branch in `ComparisonTableRenderer.prompt_post_table` (`src/site/address_audit/comparison_display.py`) and/or `AddressAuditEngine._classify_and_render` to call `AddressAuditReporter.save`; `[q]` -> "No file saved. Exiting address audit."; invalid -> one-line error + re-prompt. (Depends on T015, T021.)

**Checkpoint**: US1 + US2 both work independently; report persists to `data/`; gates green.

---

## Phase 5: User Story 3 — Unmatched and Fallback Rows (Priority: P3)

**Goal**: Every CSV row accounted for — non-existent serials surface as `UNMATCHED`; serial misses fall back to rapidfuzz >=85% address match.

**Independent Test**: Add a non-existent serial `9999999999` (expect `UNMATCHED`, no geocoding) and a row matching an existing site by address (expect `Source: Fuzzy`); confirm both behave as specified.

### Tests for User Story 3

- [ ] T023 [P] [US3] `tests/unit/site/address_audit/test_site_matcher.py`: serial hit -> `match_strategy="serial"`; serial miss -> fuzzy fallback invoked with site list; fuzzy >=85% -> `match_strategy="fuzzy"`, `confidence=score/100`; fuzzy <85% -> `unmatched`; `rapidfuzz` absent -> `unmatched` + one startup WARNING.

### Implementation for User Story 3

- [ ] T024 [US3] Implement `SiteMatchingEngine.match_fuzzy(address, sites)` in `src/site/address_audit/site_matcher.py`: `rapidfuzz.process.extractOne` with `score_cutoff=THRESHOLD` (default 85, `.env FUZZY_MATCH_THRESHOLD`); >=cutoff -> `match_strategy="fuzzy"`, `confidence=score/100`; below -> `unmatched`. Optional-import `rapidfuzz` via `GlobalImportManager` pattern; absent -> graceful `unmatched` + one-time startup WARNING (no per-call spam). Wire `match_serial` miss to delegate here.
- [ ] T025 [US3] Confirm `UNMATCHED` handling in `AddressAuditEngine`/`csv_ingester` (`src/site/address_audit/`): empty-address rows -> `UNMATCHED` (reason "empty address"), no geocoding attempted; unassigned-device rows -> `UNMATCHED`; address-field newlines/whitespace sanitized before comparison. Ensure `resolver_result is None` for `UNMATCHED` rows (no resolution attempted). (Mostly validation/glue over T011/T013/T017.)

**Checkpoint**: 100% row accountability proven; fuzzy fallback and `UNMATCHED` paths covered; gates green.

---

## Phase 6: User Story 4 — Geocoding Cache and Rerun Efficiency (Priority: P3)

**Goal**: Tier 2/3 results served from a local SQLite `geocoding_cache` so reruns are fast and rate-limit-friendly.

**Independent Test**: Run once, note time; rerun immediately; confirm >=5x faster with "cache hit" DEBUG logs and zero external calls for unchanged addresses.

### Tests for User Story 4

- [ ] T026 [P] [US4] Extend `tests/unit/site/address_audit/test_address_resolver.py`: cache hit -> returns cached result with `source="cache"`, zero network calls; cache miss -> Nominatim called AND result written to `geocoding_cache` (mock/temp SQLite); negative result (no canonical) may be cached.

### Implementation for User Story 4

- [ ] T027 [US4] Implement cache I/O in `src/site/address_audit/address_resolver.py` per geocoding-cache-contract.md: `_ensure_cache_table(conn)` (`CREATE TABLE IF NOT EXISTS geocoding_cache(query_key PRIMARY KEY, canonical_addr, source, confidence, raw_json, cached_at)`); `_from_cache(key)` SELECT (hit -> `source="cache"`, return, zero external calls); `_to_cache(key, result)` `INSERT OR REPLACE` after successful resolve. DB path resolves to `data/mist_data.db` via `os.path.join`. Insert read-before / upsert-after into `resolve()` (replacing the T014 no-op pass-through). Update `AuditCounters.cache_hits` / `external_calls`.

**Checkpoint**: All four user stories independently functional; cache verified; gates green.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Optional Tier 3 flag plumbing, inert write-back stub, env/docs, coverage, gates.

- [ ] T028 [P] Implement `AddressCorrector` STUB in `src/site/address_audit/address_corrector.py`: `apply_correction(site_id, address)` raises `NotImplementedError("Address write-back is not enabled in this release.")`; NOT imported into the menu; documents deferred write-back surface (OQ-003).
- [ ] T029 Add the `--ui-geocode` CLI flag (default OFF) plumbing through `AddressAuditEngine.run` -> `ResolveCandidates.ui_geocode`, plus `.env` bounds `UI_GEOCODE_TIMEOUT_SECONDS` and `UI_GEOCODE_MAX_LOOKUPS` and `BUSINESS_NAME` wiring (business-name prompt shown once/run when `.env BUSINESS_NAME` blank, runtime-only, not logged at INFO). Touches `src/site/address_audit/audit_engine.py` (and resolver guard from T014).
- [ ] T030 [P] Update `deploy/.env.example` with `BUSINESS_NAME`, `UI_GEOCODE_TIMEOUT_SECONDS`, `UI_GEOCODE_MAX_LOOKUPS`, and `FUZZY_MATCH_THRESHOLD` (documented defaults; Tier 3 OFF by default).
- [ ] T031 [X] `MistUIGeocoder` Tier 3 (`src/site/address_audit/ui_geocoder.py`) + `tests/unit/site/address_audit/test_ui_geocoder.py` (14 mocked tests) — DONE (commit 3ef899f; attach/launch modes proven end-to-end; fail-soft; max-lookups cap; per ui-geocoder-contract.md).
- [ ] T032 Run quality gates clean across the subpackage: `python -m py_compile MistHelper.py`, `ruff check src/site/address_audit/`, `black --check src/site/address_audit/`; verify unit-test coverage >=70% under `tests/unit/site/address_audit/`.
- [ ] T033 [P] Execute `specs/1003-site-address-audit/quickstart.md` operator + dev verification walkthrough; confirm acceptance criteria and Success Criteria (SC-001..SC-004) hold.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: DONE — no dependencies.
- **Foundational (Phase 2)**: T004/T005 depend on Setup; BLOCK all user stories.
- **US1 (Phase 3)**: depends on Phase 2. MVP.
- **US2 (Phase 4)**: depends on US1 (renderer + engine).
- **US3 (Phase 5)**: depends on US1 (`SiteMatchingEngine.match_serial`, engine classify).
- **US4 (Phase 6)**: depends on US1 (`AddressResolver.resolve`).
- **Polish (Phase 7)**: depends on the stories it touches (T029 after T014/T016; T032/T033 last).

### Critical Path

T004 -> (T011, T012, T013) -> T014 -> (T015, T016, T017) -> T018 -> T019 (MVP) -> T021/T022 (US2) -> T024 (US3) -> T027 (US4) -> T029 -> T032/T033.

### Within Each User Story

- Tests written FIRST and failing before implementation.
- Models (Phase 2) before services; services before engine/orchestrator; engine before menu registration.

### Parallel Opportunities

- Phase 2: T003 (done), T005 [P] alongside T004 review.
- US1 tests T006-T010 all [P] (distinct files).
- US1 impl: T011 + T012 [P] (independent modules); T013 independent of those two.
- US2 T020, US3 T023, US4 T026 test files are [P] within their phases.
- Polish: T028, T030, T033 are [P].

---

## Parallel Example: User Story 1

```bash
# Tests first (all parallel — distinct files):
Task: "test_csv_ingester.py"      # T006
Task: "test_snmp_enricher.py"     # T007
Task: "test_address_resolver.py"  # T008
Task: "test_comparison_display.py"# T009
Task: "test_audit_engine.py"      # T010

# Then independent modules in parallel:
Task: "csv_ingester.py"   # T011
Task: "snmp_enricher.py"  # T012
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 2 Foundational (T004, T005) — complete `models.py`.
2. Phase 3 US1 (T006-T019) — full pipeline to a rendered, classified table + menu registration.
3. **STOP and VALIDATE**: run the 4-row sample CSV; confirm table + 8-state classification, no exceptions.

### Incremental Delivery

US1 (MVP) -> US2 (save CSV) -> US3 (fuzzy/unmatched) -> US4 (cache) -> Polish (Tier 3 flag, stub, env, gates). Each story is independently testable and adds value without breaking the prior ones.

---

## Notes

- Already-complete tasks are checked `[X]` with a "DONE (commit 3ef899f)" note — do NOT redo; extend only where called out (T001 -> T018 export, T014/T027 resolver, T020 renderer save wiring).
- `[P]` = different files, no incomplete dependencies.
- `[Story]` label maps each task to a spec.md user story for traceability.
- Tier 3 (`ui_geocoder.py`) and its 14 tests are already implemented and proven; remaining Tier 3 work is only flag/env plumbing (T029/T030) and the resolver delegation guard (T014).
- Commit after each task or logical group; gates (`py_compile`/`ruff`/`black`) must pass before each commit.

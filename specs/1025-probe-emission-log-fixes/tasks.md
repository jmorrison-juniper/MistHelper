---

description: "Task list for feature 1025-probe-emission-log-fixes"
---

# Tasks: Menu 206 Probe-Emission Log Quality & Correctness Fixes

**Input**: Design documents from `specs/1025-probe-emission-log-fixes/`

**Prerequisites**: plan.md (required), spec.md (3 user stories US1/US2/US3, 14 FRs, 7 SCs), research.md (R1-R5), data-model.md (5 entities), contracts/ (log_record_shape.md, iso_coverage_invariant.md, byte_stability_invariant.md), quickstart.md

**Tests**: Included. Tests are mandated by FR-008, FR-009, FR-010, FR-011 and by the machine-checkable assertions in every contract file.

**Organization**: Tasks are grouped by user story so each story can be implemented, tested, and shipped independently. US1 (CENR dedup) and US2 (region-map extension) are both P1 and independent; US3 (regression coverage) is P2 and hardens both.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel — either (a) touches a different file than every other `[P]` peer in its phase, OR (b) makes append-only additions (new function, new module-level constant) to a shared file such that a mechanical rebase produces no conflict. Contributors coordinating on the same file MUST reserve function-name slots up front to preserve (b).
- **[Story]**: US1, US2, or US3 (setup / foundational / polish carry no story label)
- All file paths are repository-root-relative

## Path Conventions

- Single-project Python layout, already established.
- Production edit surface: `src/org/org_synthetic_probes_manager.py` (one file).
- Test surface: `tests/unit/org/test_org_synthetic_probes_manager.py` (existing, extended) and `tests/unit/org/test_country_region_coverage.py` (new).
- Fixture surface: `tests/unit/org/fixtures/` (existing directory, reused from spec 1024).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the working environment matches plan.md's Technical Context so no user-story task encounters an avoidable environment surprise.

- [X] T001 Verify branch state and dependency baseline by running `git status`, `git log --oneline -5`, `python --version` (expect >=3.13 per `pyproject.toml`), and `pytest --version`; abort if the current branch is not `1025-probe-emission-log-fixes` or if the tree diverges from the 1024 merge base recorded in plan.md Summary.
- [X] T002 [P] Confirm the fixture directory `tests/unit/org/fixtures/` exists (created by spec 1024) and inventory the pre-existing fixtures with `ls tests/unit/org/fixtures/` so US1 baseline capture (T005) and US2/US3 fixture authoring (T006, T007) know which files already ship.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Author the static test fixtures and capture the byte-stability baseline that every user-story test depends on. No user-story implementation or test can proceed until this phase completes.

**CRITICAL**: User stories US1, US2, and US3 all consume fixtures produced here.

- [X] T003 Read the current `src/org/org_synthetic_probes_manager.py` end to end and record the exact line ranges of (a) `_COUNTRY_CODE_TO_REGION`, (b) the per-site "no observation for" `logger.warning(...)` inside `_probe_target()`, and (c) the per-site "country_code ... not mapped" warning in the region resolver. These are the three edit anchors for US1 and US2 and MUST be identified before code changes to avoid touching neighbouring blocks (Principle I five-item-rule discipline).
- [X] T004 [P] Author `tests/unit/org/fixtures/iso_3166_alpha2.json` as a JSON array of exactly 249 upper-case two-letter ISO-3166-1 alpha-2 strings, sorted alphabetically, matching data-model.md §4 INV-F1 and research.md R3. Include a top-of-file provenance comment naming the ISO Maintenance Agency publication date (2026-07-26 per spec date). This fixture is the reference universe for the ISO coverage regression test (US2 + US3, contract `iso_coverage_invariant.md`).
- [X] T005 [P] Capture or confirm the pre-1025 non-VPN probe-payload baseline at `tests/unit/org/fixtures/smoke_probes_baseline.json` by re-using the artifact produced during spec 1024 if present, otherwise emit it via a temporary capture harness patched onto `manage_org_synthetic_probes` against `tests/unit/org/fixtures/smoke_org.json` on the pinned pre-1025 baseline commit `28fdfe5` (per `spec.md` Assumptions and R1; `git checkout 28fdfe5 -- src/org/org_synthetic_probes_manager.py` in the capture harness so the baseline is reproducible even if `main` advances during 1025 work). This fixture backs the INV-1 / FR-011 / SC-004 byte-stability test consumed by US1 verification (T012) and by US3 hardening (T023).
- [X] T006 [P] Author `tests/unit/org/fixtures/latam_caribbean_org.json` following the site-record schema used by `smoke_org.json`, containing at minimum one site per FR-005 code `{PA, BS, HT, DO, GT, CU, CR, HN}` with distinct site UUIDs and plausible names. Satisfies data-model.md §5 INV-F2 and is consumed by US2 tests (T019, T020) and US3 regression tests (T025).
- [X] T006a [P] Author `tests/unit/org/fixtures/cenr_dedup_org.json` containing exactly 315 site records (site_id uuids, `country_code="US"` for simplicity so region resolution is a no-op) each referencing the SAME 7 catalogue hosts, plus a paired `tests/unit/org/fixtures/cenr_dedup_missing_observations.json` naming the 7 SecB2B hosts (`gslb.secb2b.com`, `us-elm.secb2b.com`, `us-prod-klm-b2c.secb2b.com`, `us-prod-klm.secb2b.com`, `eu-elm.secb2b.com`, `eu-prod-klm-b2c.secb2b.com`, `eu-prod-klm.secb2b.com`) that MUST be omitted from the CENR observation cache when the fixture is loaded. Satisfies U1 remediation (originally implicit under T007). This is the 315-site / 7-missing-host CENR fixture underpinning the log-record-shape §1.4 contract count.

**Checkpoint**: Fixtures ready and edit anchors identified. US1 and US2 may now proceed in parallel (independent code paths, independent test targets).

---

## Phase 3: User Story 1 - Silence the CENR duplicate-warning storm (Priority: P1)

**Goal**: Reduce CENR "no observation for host" WARNINGs from ~1,261/run (N sites x M missing hosts) to at most `M` per run on the ~315-site reference org, without touching any emitted probe payload byte.

**Independent Test**: Run `pytest tests/unit/org/test_org_synthetic_probes_manager.py::test_cenr_warning_dedup_ge_1_missing tests/unit/org/test_org_synthetic_probes_manager.py::test_cenr_warning_zero_when_fully_populated tests/unit/org/test_org_synthetic_probes_manager.py::test_probe_payload_byte_stability_smoke -v` on a fixture with 315 sites and 7 unobserved SecB2B hosts, expect PASS with WARNING count <=7 and empty probe diff.

### Tests for User Story 1 (write first, expect FAIL until T014-T017 complete)

- [X] T007 [US1] Add `test_cenr_warning_dedup_ge_1_missing` to `tests/unit/org/test_org_synthetic_probes_manager.py` per contract `contracts/log_record_shape.md` §1.4 — asserts `<= M` CENR WARNING records for the 315-site / 7-missing-host fixture authored in T006a. Failure message MUST name BOTH the observed count and the cap it exceeded (e.g. `"CENR WARNING count 1261 exceeded unique-missing-host cap 7; per-site duplication regressed"`), per O2 remediation folding the T027 diagnostic-message enhancement into MVP-shipped tests. This task ALSO introduces the module-level constant `EXPECTED_MISSING_HOSTS: frozenset[str] = frozenset({"gslb.secb2b.com", "us-elm.secb2b.com", "us-prod-klm-b2c.secb2b.com", "us-prod-klm.secb2b.com", "eu-elm.secb2b.com", "eu-prod-klm-b2c.secb2b.com", "eu-prod-klm.secb2b.com"})` at the top of `test_org_synthetic_probes_manager.py` so the contract snippet in `log_record_shape.md` §1.4 resolves. Load the fixture via `json.loads(Path("tests/unit/org/fixtures/cenr_dedup_org.json").read_text())` and the paired missing-observations file. Satisfies FR-001, FR-002, FR-009, SC-001, contract §1.4 — U1/A1/O2 remediation.
- [X] T008 [US1] Add `test_cenr_warning_zero_when_fully_populated` to `tests/unit/org/test_org_synthetic_probes_manager.py` per contract `contracts/log_record_shape.md` §1.4 — asserts zero CENR WARNINGs when every catalogue host has a CENR observation. Satisfies FR-001 zero-emission edge case and US1 Acceptance Scenario 3. Note: this task appends to the same file as T007 / T009 / T010; peers are additive (new test functions only) but not truly file-disjoint — see the tightened `[P]` legend in §"Format" above.
- [X] T009 [US1] Add `test_cenr_warning_re_emit_across_runs` to `tests/unit/org/test_org_synthetic_probes_manager.py` — invokes `manage_org_synthetic_probes` twice back to back and asserts both invocations independently emit their load-time WARNING batches (dedup state does NOT persist across invocations). Satisfies FR-012 (CENR side) and US1 Edge Case "Operator runs menu 206 twice in the same session". Symmetric country-code sibling lives at T029a per G1 remediation.
- [X] T010 [US1] Add `test_probe_payload_byte_stability_smoke` to `tests/unit/org/test_org_synthetic_probes_manager.py` per contract `contracts/byte_stability_invariant.md` §3 — asserts `json.dumps(non_vpn_emitted, sort_keys=True) == json.dumps(non_vpn_baseline, sort_keys=True)` against `smoke_probes_baseline.json`. This task ALSO introduces the module-scope helper `_patch_apply_to_capture(monkeypatch, capture_sink: list)` (patches `_apply_probe` to append emitted probe dicts to `capture_sink` instead of writing to Mist) and imports `is_vpn_probe` from `src.org.org_synthetic_probes_manager` (its origin per T003 anchor identification). Satisfies FR-003, FR-011, SC-004, INV-1, A1 remediation.

### Implementation for User Story 1

- [X] T011 [US1] Add module-private helper `_compute_missing_cenr_hosts(catalogue_hosts, cenr_observations)` to `src/org/org_synthetic_probes_manager.py` returning `frozenset[str]` of `catalogue_hosts - cenr_observations.keys()`; place adjacent to `_load_probe_sources` per research.md R5 emission-site decision. Inline `#` comment on every line per Constitution VI.
- [X] T012 [US1] Add module-private helper `_emit_load_time_cenr_warning(missing_hosts, warned_cenr_hosts)` to `src/org/org_synthetic_probes_manager.py` that emits exactly one `logger.warning` naming every host in `missing_hosts - warned_cenr_hosts`, then adds each emitted host to `warned_cenr_hosts` (mutation is the dedup mechanism). Message MUST contain the literal token `CENR`, every unmapped hostname, and a phrase indicating catalogue-default fallback URLs are in use per contract `log_record_shape.md` §1.3. ASCII-only, `%s` formatting only (Constitution V and VII).
- [X] T013 [US1] Modify `manage_org_synthetic_probes` in `src/org/org_synthetic_probes_manager.py` to construct a local `warned_cenr_hosts: set[str] = set()` before per-site iteration and to invoke `_emit_load_time_cenr_warning(_compute_missing_cenr_hosts(...), warned_cenr_hosts)` immediately after `_load_probe_sources` returns. Log the run boundary with `logger.info` per Constitution VII action-logging (before/after). This is the sole owner of the dedup set lifetime per data-model.md §3 INV-D1.
- [X] T014 [US1] Remove the per-site `logger.warning("no observation for %s, using catalogue default %s", ...)` line inside `_probe_target()` in `src/org/org_synthetic_probes_manager.py` identified in T003. Do NOT touch any other line in `_probe_target()` (INV-1 byte-stability requires the probe-payload construction to be untouched). Add a `# NOTE(1025-US1): warning moved to load-time _emit_load_time_cenr_warning to avoid N*M duplication` comment at the deletion site.
- [X] T015 [US1] Run `pytest tests/unit/org/test_org_synthetic_probes_manager.py::test_cenr_warning_dedup_ge_1_missing tests/unit/org/test_org_synthetic_probes_manager.py::test_cenr_warning_zero_when_fully_populated tests/unit/org/test_org_synthetic_probes_manager.py::test_cenr_warning_re_emit_across_runs tests/unit/org/test_org_synthetic_probes_manager.py::test_probe_payload_byte_stability_smoke -v` and confirm all four PASS. If `test_probe_payload_byte_stability_smoke` fails, revert T014 and audit — INV-1 violation is a hard-stop for merge.

**Checkpoint**: User Story 1 fully functional. CENR WARNINGs deduplicated at load time. Non-VPN probe payloads byte-identical to pre-1025 baseline. Ready to demo SC-001 (>=99% CENR WARNING reduction) independently.

---

## Phase 4: User Story 2 - Correctly region-classify LATAM & Caribbean sites (Priority: P1)

**Goal**: Extend `_COUNTRY_CODE_TO_REGION` so `{PA, BS, HT, DO, GT, CU, CR, HN}` (and the rest of the LATAM/Caribbean ISO alpha-2 subset) resolve to `"americas"` not the default `"emea"`; introduce `_COUNTRY_CODE_INTENTIONAL_GAPS` for deliberate omissions; dedup the per-site unmapped-code WARNING to per-code-per-run; and lock the classification with an ISO alpha-2 coverage regression test.

**Independent Test**: Run `pytest tests/unit/org/test_org_synthetic_probes_manager.py::test_latam_caribbean_region_resolution tests/unit/org/test_org_synthetic_probes_manager.py::test_latam_caribbean_no_warnings tests/unit/org/test_country_region_coverage.py -v` — expect PASS with every LATAM/Caribbean fixture site resolving to `"americas"`, zero unmapped WARNINGs, and full ISO alpha-2 coverage.

### Tests for User Story 2 (write first, expect FAIL until T021-T026 complete)

- [X] T016 [US2] Add `test_latam_caribbean_region_resolution` to `tests/unit/org/test_org_synthetic_probes_manager.py` — loads `latam_caribbean_org.json`, resolves each site's region via the same code path menu 206 uses, and asserts `region == "americas"` (R1 literal, not `"amer"`) for every site whose `country_code` is in `{PA, BS, HT, DO, GT, CU, CR, HN}`. Satisfies FR-005, SC-003, and US2 Acceptance Scenario 1. (Not `[P]` — appends to a shared file with T017/T018 within a single contributor's sequential edit stream; use the tightened `[P]` legend if worktrees split the work.)
- [X] T017 [US2] Add `test_latam_caribbean_no_warnings` to `tests/unit/org/test_org_synthetic_probes_manager.py` per contract `log_record_shape.md` §2.4 — asserts zero `country_code`-tokened WARNINGs for the LATAM fixture. Satisfies FR-004, FR-005, SC-002, and US2 Acceptance Scenario 2.
- [X] T018 [US2] Add `test_unmapped_country_warning_dedup` to `tests/unit/org/test_org_synthetic_probes_manager.py` per contract `log_record_shape.md` §2.4 — constructs a synthetic in-line site set with `K` sites sharing one unmapped code and asserts WARNING count `<= K_unique_codes` (`<= 1` in the simple case, `<= K` when multiple distinct unmapped codes appear). Failure message MUST name BOTH the observed count and the cap it exceeded (e.g. `"country_code WARNING count 315 exceeded unique-unmapped-code cap 1; per-site duplication regressed"`), per O2 remediation folding the T027 diagnostic-message enhancement into MVP-shipped tests. Satisfies FR-004, FR-010, SC-002.
- [X] T019 [P] [US2] Create `tests/unit/org/test_country_region_coverage.py` with the four `test_iso_cover_*` functions from contract `iso_coverage_invariant.md` §3: `test_iso_cover_1_disjoint`, `test_iso_cover_2_complete`, `test_iso_cover_3_shape`, `test_iso_cover_4_region_values`. Each test fails with a diagnostic naming the offending code(s). Satisfies FR-007, FR-008, SC-005, and INV-COVER-1 through INV-COVER-4. (Genuinely `[P]` — new file, no shared surface with T016-T018.)

### Implementation for User Story 2

- [X] T020 [US2] Extend `_COUNTRY_CODE_TO_REGION` in `src/org/org_synthetic_probes_manager.py` with the LATAM / Caribbean / remaining South American entries enumerated in `data-model.md` §1: `BZ, CR, GT, HN, NI, PA, SV, AG, AI, AW, BB, BL, BM, BQ, BS, CU, CW, DM, DO, GD, GP, HT, JM, KN, KY, LC, MF, MQ, MS, PR, SX, TC, TT, VC, VG, VI, BO, EC, FK, GF, GY, PY, SR, UY` all mapped to `"americas"` (R1 literal). One entry per line, each with a same-line `#` comment naming the country per Constitution VI (e.g. `"PA": "americas",  # Panama`). Preserves INV-M1, INV-M2.
- [X] T021 [US2] Add module-level constant `_COUNTRY_CODE_INTENTIONAL_GAPS: frozenset[str]` to `src/org/org_synthetic_probes_manager.py` immediately below `_COUNTRY_CODE_TO_REGION`, per research.md R4 and data-model.md §2. Initial members MUST be discovered by running `set(iso_3166_alpha2.json) - set(_COUNTRY_CODE_TO_REGION)` and classifying each residual code as either "add to region map" or "add to gap set with inline rationale" (`AQ  # Antarctica - no plausible Mist site` etc.). Every gap entry carries a same-line `#` comment naming the reason (Constitution VI, NON-NEGOTIABLE). Preserves INV-G1, INV-G2, INV-G3.
- [X] T022 [US2] Add module-private helper `_compute_unmapped_country_codes(sites, region_map, gap_set)` to `src/org/org_synthetic_probes_manager.py` returning `frozenset[str]` of the site country codes that appear in neither `region_map` nor `gap_set`. Place adjacent to the region-resolution helpers. Inline `#` comment on every line per Constitution VI.
- [X] T023 [US2] Add module-private helper `_emit_load_time_country_code_warning(unmapped_codes, warned_unmapped_codes)` to `src/org/org_synthetic_probes_manager.py` that emits exactly one `logger.warning` naming every code in `unmapped_codes - warned_unmapped_codes`, then adds each emitted code to `warned_unmapped_codes`. Message MUST contain the literal token `country_code`, every unmapped code, and the default region that will apply, per contract `log_record_shape.md` §2.3. ASCII-only, `%s` formatting only.
- [ ] T024 [US2] Modify `manage_org_synthetic_probes` in `src/org/org_synthetic_probes_manager.py` to construct a local `warned_unmapped_codes: set[str] = set()` alongside `warned_cenr_hosts` (T013) and invoke `_emit_load_time_country_code_warning(_compute_unmapped_country_codes(...), warned_unmapped_codes)` immediately after the site list is loaded but before per-site region resolution begins. Both dedup sets share the same lifetime bounded by the invocation per FR-012.
- [ ] T025 [US2] Remove the per-site `logger.warning(...)` for unknown `country_code` from the region-resolver call site identified in T003 in `src/org/org_synthetic_probes_manager.py`. Do NOT touch the region-value resolution itself (that behaviour still returns `_DEFAULT_REGION` for unmapped codes per FR-003 spirit — probes still fire, only the warning shape changes). Add a `# NOTE(1025-US2): warning moved to load-time _emit_load_time_country_code_warning to avoid N*K duplication` comment at the deletion site.
- [ ] T026 [US2] Run `pytest tests/unit/org/test_org_synthetic_probes_manager.py::test_latam_caribbean_region_resolution tests/unit/org/test_org_synthetic_probes_manager.py::test_latam_caribbean_no_warnings tests/unit/org/test_org_synthetic_probes_manager.py::test_unmapped_country_warning_dedup tests/unit/org/test_country_region_coverage.py -v` and confirm all seven tests PASS. If `test_iso_cover_2_complete` fails with a "missing codes" diagnostic, iterate T020 / T021 to classify the residual codes until PASS.

**Checkpoint**: User Story 2 fully functional. LATAM/Caribbean sites resolve to `"americas"`. Unmapped-code WARNINGs deduplicated per-code-per-run. Full ISO-3166 alpha-2 coverage locked in by CI-enforced regression test. US1 tests from Phase 3 still green (regression check).

---

## Phase 5: User Story 3 - Fixture-backed regression coverage for both log-noise sources (Priority: P2)

**Goal**: Ensure the US1 and US2 wins are durable — a future refactor that reintroduces the per-site emission pattern (for either warning family) fails CI with a diagnostic that names the observed count and the threshold it exceeded.

**Independent Test**: On a scratch branch, delete `_emit_load_time_cenr_warning` and re-insert the per-site warning at the `_probe_target` call site; re-run the regression tests and confirm they fail with a clear message such as "CENR WARNING count 1261 exceeded unique-missing-host cap 7". Then delete the ISO alpha-2 coverage tests target codes and confirm the coverage regression test fails naming the missing codes. Restore branch.

### Tests for User Story 3 (write these to harden US1 and US2 assertions and add the meta-invariants US3 owns)

- [ ] T027 [US3] Retained as a **no-op / documentation checkpoint** after O2 remediation folded the diagnostic-message wording enhancement directly into T007 and T018 so MVP-shipped tests already carry the actionable failure text. Verify at review time that T007's and T018's failure messages BOTH name the observed count AND the cap-they-exceeded (e.g. `"CENR WARNING count 1261 exceeded unique-missing-host cap 7"`); if either has drifted, re-apply the enhancement inline. This task exists so the FR-009 / FR-010 diagnostic-quality requirement retains a phase-5 audit anchor without a duplicate implementation obligation.
- [X] T028 [US3] Add `test_iso_cover_double_declared` to `tests/unit/org/test_country_region_coverage.py` — constructs a synthetic (region_map, gap_set) pair that shares a code and asserts the disjoint-check test would fire with a "double-declared code" diagnostic naming the offending code. Satisfies US2 Edge Case ("A country code appears in the intentional-gap set AND in `_COUNTRY_CODE_TO_REGION`") and US3 Acceptance Scenario 3.
- [X] T029 [US3] Add `test_regression_runtime_under_budget` to `tests/unit/org/test_org_synthetic_probes_manager.py` — invokes the full 1025 regression subset via `time.perf_counter()` bookends and asserts wall-clock `< 5.0` seconds on the reference dev machine. Satisfies SC-007. Per O1 remediation, SC-007 is annotated in `spec.md` as verified only after US3 lands; if MVP-first ship path is chosen (US1 only), SC-007 remains provably-unverified until this task lands.
- [X] T029a [US3] Add `test_country_warning_re_emit_across_runs` to `tests/unit/org/test_org_synthetic_probes_manager.py` — mirrors T009 but for the country-code dedup path: invokes `manage_org_synthetic_probes` twice back to back against a fixture with the same unmapped `country_code` present in both invocations, asserts both invocations independently emit their load-time WARNING batches (`warned_unmapped_codes` dedup state does NOT persist across invocations). Copy T009 body, swap `warned_cenr_hosts` → `warned_unmapped_codes` and CENR message tokens → `country_code` message tokens. Satisfies FR-012 (country-code side) — G1 remediation for asymmetric FR-012 coverage.
- [X] T030 [US3] Add `test_cenr_warning_re_emit_on_dropout` to `tests/unit/org/test_org_synthetic_probes_manager.py` — fixture where a previously-observed CENR host drops out of the cache between two invocations; assert the WARNING for that host is emitted exactly once per invocation (not per-site). Satisfies US1 Acceptance Scenario 4.

### Verification for User Story 3

- [X] T031 [US3] Run the full org-scoped unit suite: `pytest tests/unit/org/ -v --cov=src.org.org_synthetic_probes_manager --cov-report=term-missing`. Confirm all US1, US2, and US3 tests PASS; confirm pre-existing 1024 tests still PASS (no regression). Record coverage for the touched module.
- [X] T032 [US3] Perform the destructive-regression verification described in US3 Independent Test: on a scratch commit (not to be pushed), revert T013 + T014 (US1 dedup) and re-run T007's test; confirm it fails with the T027-enhanced diagnostic naming the observed count. Restore. Repeat for T024 + T025 (US2 dedup) with T018 / T027. Do not commit the scratch reverts.

**Checkpoint**: All three user stories functionally complete and independently testable. Regression tests fire loudly and specifically when either dedup path is broken.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Meet the project-wide quality gates (docstring coverage, formatter, linter, type-check) before merge and refresh the derived documentation.

- [X] T033 [P] Run `interrogate -v src/org/org_synthetic_probes_manager.py tests/unit/org/test_org_synthetic_probes_manager.py tests/unit/org/test_country_region_coverage.py` and confirm docstring coverage `>= 90 %` per project `DOCS.md`. Add or refine module-, function-, and helper-docstrings for anything introduced by T011, T012, T020, T021, T022, T023 until the gate is green. Every new docstring MUST have a "Why" section per `DOCS.md`.
- [X] T034 [P] Run `black --check src/org/org_synthetic_probes_manager.py tests/unit/org/test_org_synthetic_probes_manager.py tests/unit/org/test_country_region_coverage.py`. If it reports diffs, run `black` (no `--check`) to apply, then re-run `--check` and confirm clean.
- [X] T035 [P] Run `ruff check src/org/org_synthetic_probes_manager.py tests/unit/org/test_org_synthetic_probes_manager.py tests/unit/org/test_country_region_coverage.py` and resolve any findings (no `# noqa` suppressions without an inline `#` comment naming the reason per Constitution VI).
- [X] T036 [P] Run `mypy src/org/org_synthetic_probes_manager.py` and confirm zero new errors introduced by 1025. If the file was previously ignored or excluded, ensure the new helpers (`_compute_missing_cenr_hosts`, `_emit_load_time_cenr_warning`, `_compute_unmapped_country_codes`, `_emit_load_time_country_code_warning`) carry accurate type annotations (`frozenset[str]`, `set[str]`, `Mapping[str, str]`) so future type-check enablement stays clean.
- [X] T037 Verify `src/utils/operation_registry.py` classification for menu 206 (`manage_org_synthetic_probes`) is present and unchanged — 1025 does NOT alter menu registration, but per user MEMORY.md guidance any new menu entry needs a classification and the guardrail test asserts it. Read the registry entry for 206 and confirm still classified appropriately.
- [X] T038 Update `CLAUDE.md` "Active Technologies" and "Recent Changes" sections to add a 1025 entry summarising the single-line diff surface (region map + gap set + dedup helpers in `src/org/org_synthetic_probes_manager.py`). Do NOT rewrite prior entries; append only.
- [ ] T039 Execute the operator-facing smoke sequence from `quickstart.md` §3b against a live target org: run menu 206, then confirm `grep -c "CENR" data/script.log` returns a single-digit count for the current run's slice (SC-001), `grep -c "country_code" data/script.log` returns 0 if the org has no unmapped codes or `<= K` if it has K unique unmapped codes (SC-002), and `tail -100 data/script.log` looks clean (SC-006). Record the numbers in the PR description.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup, T001-T002)**: No dependencies — start immediately.
- **Phase 2 (Foundational, T003-T006)**: Depends on Phase 1. BLOCKS every user story. T003 is sequential (produces the anchor map used by T014, T025); T004, T005, T006 are all `[P]` — different files, no shared state.
- **Phase 3 (US1) and Phase 4 (US2)**: Both depend on Phase 2 completion. US1 and US2 are INDEPENDENT of each other — different code paths (`_probe_target` vs region resolver), different fixtures, different assertion targets. May run fully in parallel with two contributors.
- **Phase 5 (US3)**: Depends on Phase 3 AND Phase 4 completion — US3 hardens the tests introduced by US1 and US2 and adds the destructive-regression verification.
- **Phase 6 (Polish)**: Depends on Phases 3, 4, 5 all complete.

### User Story Dependencies

- **US1 (P1)**: Depends only on Phase 2. Zero dependency on US2 or US3.
- **US2 (P1)**: Depends only on Phase 2. Zero dependency on US1 or US3.
- **US3 (P2)**: Depends on both US1 and US2 landing — its tests reference `warned_cenr_hosts` (US1) and `warned_unmapped_codes` (US2) call sites and diagnostic wording.

### Within Each User Story

- Tests are written FIRST (T007-T010 before T011-T015; T016-T019 before T020-T026) and are expected to FAIL until the implementation tasks land. This is TDD-order per project convention.
- Helpers (`_compute_*`) before emitters (`_emit_load_time_*`) before call-site integration in `manage_org_synthetic_probes`.
- Removal of the per-site warning (T014, T025) MUST be the last implementation step of each story so the byte-stability test (T010) fires cleanly on the finished state, not on a half-migrated intermediate.

### Parallel Opportunities

- **Phase 2**: T004, T005, T006 are `[P]` — three different fixture files.
- **Phase 3 US1 tests**: T007, T008, T009, T010 are all `[P]` — four test functions in the same file but no shared fixture state; they can be written in any order in one editor pass.
- **Phase 4 US2 tests**: T016, T017, T018, T019 are all `[P]` — three functions in the existing test file plus one new test file.
- **Phase 5 US3 tests**: T027, T028, T029, T030 are all `[P]` — different test functions, different assertion targets.
- **Phase 6 Polish**: T033, T034, T035, T036 are all `[P]` — four independent quality-gate commands, no shared state.
- **Cross-story parallelism**: With two contributors, all of Phase 3 can proceed in parallel with all of Phase 4 (independent code paths and independent test files apart from the shared `test_org_synthetic_probes_manager.py`, which supports concurrent function additions in separate git worktrees).

---

## Parallel Example: User Stories 1 and 2 in Parallel

```bash
# After Phase 2 completes, with two contributors:
# Contributor A takes US1:
Task: "T007 [US1] test_cenr_warning_dedup_ge_1_missing"
Task: "T008 [US1] test_cenr_warning_zero_when_fully_populated"
Task: "T009 [US1] test_cenr_warning_re_emit_across_runs"
Task: "T010 [US1] test_probe_payload_byte_stability_smoke"
Task: "T011 [US1] _compute_missing_cenr_hosts helper"
Task: "T012 [US1] _emit_load_time_cenr_warning helper"
Task: "T013 [US1] wire dedup state into manage_org_synthetic_probes"
Task: "T014 [US1] delete per-site warning in _probe_target"

# Contributor B takes US2:
Task: "T016 [US2] test_latam_caribbean_region_resolution"
Task: "T017 [US2] test_latam_caribbean_no_warnings"
Task: "T018 [US2] test_unmapped_country_warning_dedup"
Task: "T019 [US2] test_country_region_coverage.py (four iso_cover tests)"
Task: "T020 [US2] extend _COUNTRY_CODE_TO_REGION"
Task: "T021 [US2] add _COUNTRY_CODE_INTENTIONAL_GAPS"
Task: "T022 [US2] _compute_unmapped_country_codes helper"
Task: "T023 [US2] _emit_load_time_country_code_warning helper"
Task: "T024 [US2] wire country dedup state into manage_org_synthetic_probes"
Task: "T025 [US2] delete per-site warning in region resolver"
```

---

## Implementation Strategy

### MVP First (US1 only)

1. Complete Phase 1 (Setup) — T001, T002.
2. Complete Phase 2 (Foundational) — T003, T004, T005, T006 (the ISO fixture T004 is technically only needed by US2, but Phase 2 keeps the fixture group together for a single reviewable commit).
3. Complete Phase 3 (US1) — T007 through T015.
4. **STOP and VALIDATE**: `pytest tests/unit/org/test_org_synthetic_probes_manager.py -v`. If PASS, US1 is deployable — CENR log storm silenced.
5. Ship US1 as the MVP if US2 needs additional review time.

### Incremental Delivery

1. Setup + Foundational -> foundation ready.
2. Add US1 -> test -> ship (MVP: log storm gone).
3. Add US2 -> test -> ship (LATAM/Caribbean correctly regioned, coverage gate live).
4. Add US3 -> test -> ship (regression hardening).
5. Polish -> final PR merge.

### Parallel Team Strategy

- Both P1 stories can be developed simultaneously by two contributors after Phase 2.
- US3 is a single-contributor task at the end; it depends on both US1 and US2 code landing.

---

## Notes

- `[P]` markers are set conservatively — a task marked `[P]` is confirmed to touch a different file or a different function than the other `[P]` tasks in its phase.
- Every implementation task cites its FR / SC / contract source so `/speckit.analyze` and `/speckit.implement` can trace every task back to spec authority.
- Byte-stability (T010) is the hard-stop guardrail — if T010 fails after T014 lands, the CENR-move implementation touched something it should not have. Revert T014 and audit before proceeding.
- The ISO coverage test (T019) is the durable guardrail — if a future contributor removes a country entry or forgets to classify a new ISO amendment, T019 fires with a diagnostic naming the exact codes.
- Docstring "Why" sections (T033) are enforced per project `DOCS.md`; do not skimp on rationale for helpers that appear trivial — their existence rationale (dedup at load time vs per-site) is exactly the "why" that must be captured.
- Commit cadence: one commit per completed task or per logical group (`test_iso_cover_*` as one commit is acceptable). Do not batch US1 + US2 into one commit.

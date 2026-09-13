# Cross-Artifact Analysis Report: `1025-probe-emission-log-fixes`

**Generated**: 2026-07-26
**Analyzer**: `/speckit.analyze` (read-only, non-destructive)
**Feature dir**: `specs/1025-probe-emission-log-fixes/`
**Artifacts inspected**: `spec.md`, `plan.md`, `research.md`, `data-model.md`,
`contracts/log_record_shape.md`, `contracts/iso_coverage_invariant.md`,
`contracts/byte_stability_invariant.md`, `quickstart.md`, `tasks.md`,
`.specify/memory/constitution.md`.

**Constitution version resolved**: current `.specify/memory/constitution.md`
(Principles I-VII in force).

---

## 1. Specification Analysis Report

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I1 | Inconsistency | HIGH | `spec.md` (Assumptions: "Central America and Caribbean sites route via the `amer` Zscaler region"; user-story acceptance narrative) vs. `research.md` R1, `plan.md`, `tasks.md` T016, T020 (all use `"americas"`) | Spec text uses shorthand `amer`; every downstream artifact uses the actual Zscaler literal `"americas"`. R1 in research.md rationalises the deviation but the spec was not back-annotated. A future reader who cross-references spec ↔ code will hit a false mismatch. | Add a one-line footnote in `spec.md` (Assumptions section) pointing to `research.md` R1 for the canonical literal; OR edit the spec assumption to read `"americas" (the Zscaler literal, colloquially "amer")`. Non-blocking for `/speckit.implement` because R1 is authoritative and tasks are correct, but should be closed to avoid confusing operators. |
| U1 | Underspecification | HIGH | `tasks.md` T007 ("fixture with M=7 unobserved hosts across ~315 sites") vs. Phase 2 (T005 captures `smoke_probes_baseline.json`; T006 authors `latam_caribbean_org.json`; no task authors a 315-site / 7-missing-host CENR fixture) | The 315-site fixture underpinning the CENR-dedup contract count is not produced by any Phase 2 task. Either the test constructs it inline via `fake_session` mocking (implicit) or an unnamed fixture is expected. Contract §1.4 also references a symbol `EXPECTED_MISSING_HOSTS` with no defined origin. | Either (a) add an explicit Phase 2 task "author `tests/unit/org/fixtures/cenr_dedup_org.json` with 315 sites + 7 unobserved catalogue hosts, and define `EXPECTED_MISSING_HOSTS = frozenset({...})` at module scope in the test file", or (b) amend T007 to explicitly document "constructs fake_session in-line; EXPECTED_MISSING_HOSTS is a module-level constant introduced in this task". Currently ambiguous. |
| G1 | Coverage Gap | MEDIUM | FR-012 (dedup state ephemeral, no cross-invocation persistence) tested by T009 (`test_cenr_warning_re_emit_across_runs`) for CENR only; no symmetric `test_country_warning_re_emit_across_runs` for `warned_unmapped_codes` | FR-012 asserts the invariant for BOTH dedup sets. Test coverage is asymmetric — CENR dedup ephemerality is proven; country-code dedup ephemerality is not. A future refactor promoting `warned_unmapped_codes` to a module-level cache would slip through CI. | Add T029.1 (or extend T030) with `test_country_warning_re_emit_across_runs` mirroring T009's shape against `warned_unmapped_codes`. Low effort (copy T009, swap symbol names). |
| P1 | Ordering / Parallelism | MEDIUM | `tasks.md`: `[P]` on T007, T008, T009, T010 (all edit `tests/unit/org/test_org_synthetic_probes_manager.py`); same for T016, T017, T018 (same file); same for T027, T029, T030 (same file) | Task file legend states `[P]` = "different files, no dependencies on incomplete tasks in the same phase". Multiple `[P]`-marked tasks in Phases 3, 4, 5 target the SAME file. In a single-contributor sequential workflow this is harmless; in the documented two-contributor / git-worktree strategy (Phase headings and §"Parallel Team Strategy") the concurrent additions to one file will produce merge conflicts. | Either (a) tighten the `[P]` definition in the file legend to "different files OR appended-only additions to the same file with reserved slot markers", or (b) demote in-file peers to non-`[P]` (sequential) and reserve `[P]` for genuinely file-disjoint tasks. Behaviourally safe today because tests are additive functions; the risk is coordination cost, not correctness. |
| A1 | Ambiguity | LOW | `contracts/log_record_shape.md` §1.4 references `EXPECTED_MISSING_HOSTS`; `contracts/byte_stability_invariant.md` §3 references `patch_apply_to_capture()` and `is_vpn_probe()` | Contract test snippets use three symbols (`EXPECTED_MISSING_HOSTS`, `patch_apply_to_capture`, `is_vpn_probe`) that have no defined home. Contracts explicitly disclaim being test source (§"Do not paste the contract test code into implementation modules"), but the implementer still needs to know where these live. | In each of the three test-authoring tasks (T007, T010), add a same-line note: "define local helper `_patch_apply_to_capture` at module scope; define `EXPECTED_MISSING_HOSTS` from the fixture inventory". Contracts remain illustrative; tasks become self-sufficient. |
| A2 | Ambiguity | LOW | `tasks.md` T005 ("pre-1025 `main` HEAD") vs. spec assumption pinning a specific commit SHA `28fdfe5` as the byte-stability baseline anchor | T005 says "pre-1025 main HEAD" without a specific SHA; spec pins `28fdfe5`. If `main` advances before T005 runs the two become different commits. | Have T005 explicitly cite the SHA from the spec assumption: `git checkout 28fdfe5 -- src/org/org_synthetic_probes_manager.py` in the temporary capture harness. One-line edit. |
| C1 | Constitution alignment | LOW | `plan.md` Constitution Check declares one Complexity Tracking entry (Principle II, "dedup state as function parameter, not class attribute") | Correctly documented and traced through research.md R2, data-model.md §3 INV-D1/D2/D3, and tasks T013 + T024. Not a violation — the exception is explicit, minimal, and consistent. Recording for completeness. | No action. The Complexity Tracking entry is well-formed. |
| O1 | Coverage Gap | LOW | SC-007 ("regression subset runs in `< 5s` wall clock") verified ONLY by T029 in Phase 5 (US3, priority P2). If the MVP-first strategy from Implementation Strategy stops after US1 (Phase 3), or after US1+US2 (Phases 3+4), SC-007 is unverified at ship. | The docs' MVP path lands US1 alone (Implementation Strategy §"MVP First"), which skips T029. SC-007 is a quality-of-life SC not a correctness one, but ship-readiness of the MVP is claimed without it. | Either move `test_regression_runtime_under_budget` (T029) into Phase 3 (attach to US1) as its own MVP-scope check, OR annotate SC-007 in `spec.md` as "verified only after US3 lands" so the MVP claim is defensible. |
| O2 | Coupling risk | LOW | `tasks.md` T027 modifies test bodies previously authored in T007 and T018 | T027 is in Phase 5 (US3, P2). It edits assertions inside T007 (US1, P1) and T018 (US2, P1). If US3 is deferred, the diagnostic-message wording promised by SC-005's phrasing ("names the observed count and the threshold") is not present in the P1 tests. Failure output would be less actionable. | Fold T027's diagnostic-message enhancements INTO T007 and T018 directly, so the MVP-shipped tests already carry the actionable failure text. Move the US3-owned meta-invariants (T028, T029, T030) into their own smaller phase. |

**Findings total**: 8 (2 HIGH, 3 MEDIUM, 3 LOW).
**Critical findings**: 0.
**Constitution violations**: 0.

---

## 2. Coverage Summary — Functional Requirements

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 (CENR dedup, `<= M` WARNINGs) | Yes | T007, T008, T012, T013 | Assertion + implementation + verification. |
| FR-002 (CENR message content: names all hosts + fallback note) | Yes | T007, T012 | Test asserts token+host names; T012 constructs message. |
| FR-003 (probe payload preserved) | Yes | T010, T014 | Byte-stability test + limited-touch note in T014. |
| FR-004 (unmapped country dedup, `<= K` WARNINGs) | Yes | T017, T018, T023, T024 | |
| FR-005 (LATAM/Caribbean set maps to `"americas"`) | Yes | T016, T020 | |
| FR-006 (add `_COUNTRY_CODE_INTENTIONAL_GAPS`) | Yes | T021 | |
| FR-007 (every ISO alpha-2 code classified) | Yes | T019, T021 | INV-COVER-2 test + T021 authoring. |
| FR-008 (CI regression test for coverage) | Yes | T019 | Four `test_iso_cover_*` tests. |
| FR-009 (CENR diagnostic quality) | Yes | T007, T027 | T027 enhances message; may be moved to T007 per O2. |
| FR-010 (unmapped-code diagnostic quality) | Yes | T018, T027 | Same as FR-009 sibling. |
| FR-011 (INV-1 byte-stability restated) | Yes | T010 | |
| FR-012 (dedup state ephemeral per invocation) | Partial | T009 (CENR only) | See finding G1 — country-code side missing. |
| FR-013 (grep-anchor tokens `CENR`, `country_code`) | Yes | T012, T023 | Message-content specification. |
| FR-014 (no new telemetry events introduced) | Vacuously | — | No task adds telemetry; vacuous satisfaction by omission is documented in data-model.md §3. |

**Coverage %** (requirements with `>= 1` task): 14/14 = **100 %** (FR-012 asymmetric but not zero-covered).

---

## 3. Coverage Summary — Success Criteria

| SC Key | Has Verification Task? | Task IDs | Notes |
|--------|------------------------|----------|-------|
| SC-001 (CENR WARNINGs `<= 7` on ref org, >99% reduction) | Yes | T007, T015, T039 | Unit + smoke. |
| SC-002 (country_code WARNINGs `0` when fully mapped) | Yes | T017, T026, T039 | |
| SC-003 (LATAM/Caribbean resolve to `"americas"`) | Yes | T016 | |
| SC-004 (non-VPN probe payloads byte-identical) | Yes | T010, T015 | INV-1 restated. |
| SC-005 (ISO coverage regression fires on silent add/remove) | Yes | T019, T028 | Four tests + double-declared meta-test. |
| SC-006 (log tail visually clean post-run) | Yes | T039 | Operator smoke, manual grep counts. |
| SC-007 (regression subset < 5 s wall clock) | Yes | T029 | See finding O1 — only in US3 (P2). |

---

## 4. Coverage Summary — Contract Invariants

| Invariant | Contract | Verifying Task(s) |
|-----------|----------|-------------------|
| INV-1 (byte-stability) | `byte_stability_invariant.md` | T010, T015 |
| INV-COVER-1 (disjoint) | `iso_coverage_invariant.md` | T019 (`test_iso_cover_1_disjoint`), T028 (double-declared diagnostic) |
| INV-COVER-2 (complete) | `iso_coverage_invariant.md` | T019 (`test_iso_cover_2_complete`) |
| INV-COVER-3 (shape) | `iso_coverage_invariant.md` | T019 (`test_iso_cover_3_shape`) |
| INV-COVER-4 (region values) | `iso_coverage_invariant.md` | T019 (`test_iso_cover_4_region_values`) |
| Log-record-shape §1 CENR count `<= M` | `log_record_shape.md` | T007, T008 |
| Log-record-shape §2 country-code count `<= K` | `log_record_shape.md` | T017, T018 |

**Invariant coverage**: 7/7 = **100 %**.

---

## 5. Coverage Summary — Data-Model Entities & Research Decisions

| Artifact item | Consumer task(s) |
|---------------|------------------|
| Data-model §1 `_COUNTRY_CODE_TO_REGION` extension | T020 |
| Data-model §2 `_COUNTRY_CODE_INTENTIONAL_GAPS` (frozenset[str]) | T021 |
| Data-model §3 per-run dedup state (`warned_cenr_hosts`, `warned_unmapped_codes`) | T012, T013, T023, T024 |
| Data-model §4 `iso_3166_alpha2.json` fixture (INV-F1: 249 codes) | T004 (author), T019 (consume) |
| Data-model §5 `latam_caribbean_org.json` fixture (INV-F2) | T006 (author), T016/T017 (consume) |
| Research R1 (`"americas"` literal, not `"amer"`) | T016, T020 |
| Research R2 (dedup state as function parameter) | T012, T013, T023, T024 |
| Research R3 (checked-in ISO fixture, no `pycountry` dep) | T004 |
| Research R4 (`frozenset[str]` gap set with inline rationale) | T021 |
| Research R5 (WARNING emitted at load time, level unchanged) | T011-T014, T022-T025 |

**Orphan artifacts**: none. Every research decision and every data-model entity is consumed by at least one task.

---

## 6. Constitution Alignment

| Principle | Check | Status |
|-----------|-------|--------|
| I (Five-item rule) | 1 production file + 2 test files + 1 fixture = 4 items. Well under the 5-item limit. | PASS |
| II (No wrapper classes) | Documented exception in `plan.md` Complexity Tracking: dedup state passed as function parameter (`warned_cenr_hosts`, `warned_unmapped_codes`), NOT wrapped in a class. Rationale traced through R2 / data-model.md §3 / tasks T012-T024. | PASS (with explicit tracked exception) |
| III (Test-first with fixtures) | Test tasks (T007-T010, T016-T019, T027-T030) precede implementation tasks in each phase. Fixtures authored in Phase 2 before consumption. | PASS |
| IV (Read-only-by-default) | Menu 206 already registered; no menu-registry changes. T037 verifies unchanged classification. | PASS |
| V (ASCII-only, `%s` formatting) | Explicitly required in T012 and T023 helper-authoring tasks. | PASS |
| VI (Inline `#` comment on every new line, NON-NEGOTIABLE) | Explicitly required in T011, T012, T020, T021, T022, T023. Same-line country-name comments called out in T020. | PASS |
| VII (Action logging BEFORE/AFTER, `%s` formatting) | T013 explicitly notes "Log the run boundary with `logger.info` per Constitution VII action-logging (before/after)". | PASS |

**Constitution violations**: 0. The single Complexity Tracking entry is well-formed, minimally scoped, and traced end-to-end.

---

## 7. Unmapped Tasks

None. All 39 tasks (T001-T039) trace to at least one FR / SC / INV / contract citation, or to a project-wide quality gate (T033-T036 for docstring / formatter / linter / type-check, T037 for operation-registry guardrail, T038 for `CLAUDE.md` refresh, T039 for operator smoke).

---

## 8. Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements | 14 (FR-001..FR-014) |
| Total Success Criteria | 7 (SC-001..SC-007) |
| Total Contract Invariants | 7 |
| Total Tasks | 39 (T001..T039) across 6 phases |
| Requirement coverage (>= 1 task) | 14/14 = 100 % |
| Success-criterion coverage | 7/7 = 100 % (SC-007 only via US3 — see O1) |
| Invariant coverage | 7/7 = 100 % |
| Orphan artifacts | 0 |
| Ambiguity findings | 3 (A1 undefined test symbols, A2 baseline commit vs. HEAD, U1 315-site fixture provenance) |
| Duplication findings | 0 |
| Constitution violations | 0 |
| CRITICAL findings | 0 |
| HIGH findings | 2 (I1 amer/americas, U1 315-site fixture) |
| MEDIUM findings | 3 (G1 country-side FR-012 test gap, P1 `[P]`-in-same-file, plus one carried in P1) |
| LOW findings | 3 (A1 symbols, A2 baseline SHA, O1 SC-007 verified only in US3, O2 T027 diagnostic-move) |

Note: `plan.md` Constitution Check declares one Complexity Tracking exception (Principle II, dedup state as function parameter). This is a *documented, minimal* deviation, not a violation.

---

## 9. Verification of the 8 Requested Criteria

| # | User's ask | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Every FR covered by >=1 task; every task cites FR/SC/INV/contract | PASS with minor gap | 14/14 FRs covered. FR-012 is asymmetrically tested (CENR yes, country-code no — G1). All 39 tasks cite spec authority. |
| 2 | Every SC has measurable acceptance in tasks.md | PASS with caveat | 7/7 SCs have a verifying task. SC-007 is verified only inside US3 (P2) — see O1. |
| 3 | Every contract invariant asserted by >=1 test task | PASS | 7/7 invariants tested. |
| 4 | No orphan artifacts | PASS | All research decisions, data-model entities, and fixtures are consumed by at least one task. |
| 5 | No contradictions between spec and plan | PASS with one deferred inconsistency | Spec uses `amer` shorthand; plan uses `"americas"` per R1. Not a contradiction *in intent* (R1 rationalizes) but a documentation drift — see I1. |
| 6 | Complexity Tracking entry consistent with data-model + tasks | PASS | Principle II deviation is coherent across `plan.md` Complexity Tracking, `research.md` R2, `data-model.md` §3 INV-D1/D2/D3, and tasks T013 + T024. |
| 7 | `[P]` markers safe (no `[P]` peers with mutating dep) | PASS *sequentially*, RISK in parallel | Within a single contributor's sequential edit stream, all `[P]`-marked tasks are additive (new test functions, new module-level constants) so no mutating collision exists. However, several `[P]` peers target the SAME file, which the tasks.md legend claims implies "different files" — see finding P1. Semantically safe; documentation-vs-behaviour mismatch. |
| 8 | MVP (US1 alone) genuinely independently shippable | PASS with caveat | US1 has zero dependency on US2 or US3 per §"User Story Dependencies". Phase 2 T004 (ISO fixture) is technically only needed by US2; Implementation Strategy §"MVP First" acknowledges T004 is kept in the MVP bundle for reviewability, not correctness. So the MVP is deployable. Caveat: SC-007 runtime budget (T029) is in US3 only — if MVP-first ships US1 without US3, SC-007 is unverified (O1). |

---

## 10. Next Actions

Because there are **zero CRITICAL findings and zero constitution violations**, the feature is proceedable to `/speckit.implement`. The following pre-implementation clean-ups are recommended but not blocking:

**Recommended before `/speckit.implement`** (fixes HIGH-severity findings):

1. Resolve **U1** (315-site CENR fixture): either add an explicit Phase 2 task to author `tests/unit/org/fixtures/cenr_dedup_org.json` (315 sites, 7 unobserved catalogue hosts) OR amend T007 to state that the fixture is constructed inline and to define `EXPECTED_MISSING_HOSTS` as a module-level constant.
2. Resolve **I1** (amer vs. americas): add a one-line footnote in `spec.md` Assumptions pointing to `research.md` R1, OR back-annotate the spec text to use `"americas"` with an "aka amer" parenthetical.

**Recommended during Phase 2/3** (fixes MEDIUM-severity findings):

3. Resolve **G1** (FR-012 asymmetry): add `test_country_warning_re_emit_across_runs` alongside T009. Copy T009 body, swap `warned_cenr_hosts` → `warned_unmapped_codes`.
4. Resolve **P1** (`[P]` same-file semantics): tighten legend text in `tasks.md` §"Format" from `[P] = different files` to `[P] = different files OR additive-only additions to the same file (append-safe)`.

**Optional polish** (fixes LOW-severity findings; can be deferred to implementation PR review):

5. Resolve **A1** (undefined test symbols): add same-line clarification in T007 / T010 naming the origin of `EXPECTED_MISSING_HOSTS`, `_patch_apply_to_capture`, `is_vpn_probe`.
6. Resolve **A2** (baseline commit SHA): update T005 to cite the pinned SHA `28fdfe5` from the spec assumption instead of "pre-1025 `main` HEAD".
7. Resolve **O1** (SC-007 verification path): if MVP-first is the intended ship path, move T029 into Phase 3 (attach to US1) so SC-007 is provable at MVP ship.
8. Resolve **O2** (T027 diagnostic-move): fold T027's diagnostic wording enhancements INTO T007 and T018 so MVP-shipped tests already carry the actionable failure text.

**Suggested command sequence** if you accept the above:

```bash
# Edit spec.md to close I1 (footnote or in-place fix)
# Edit tasks.md to close U1 (add fixture task) and P1 (legend tightening)
# Optionally edit tasks.md to close G1, A1, A2, O1, O2
# Then:
/speckit.implement
```

---

## 11. Remediation Offer

Would you like me to produce concrete, ready-to-apply edit patches for any subset of the findings above? Suggested options:

- **Option A (minimum viable)**: patches for HIGH findings only (I1, U1).
- **Option B (recommended)**: patches for HIGH + MEDIUM findings (I1, U1, G1, P1).
- **Option C (full sweep)**: patches for all 8 findings.

Reply with `A`, `B`, or `C` (or a list of finding IDs) and I will draft the edits WITHOUT applying them — you retain final approval before any file is written.

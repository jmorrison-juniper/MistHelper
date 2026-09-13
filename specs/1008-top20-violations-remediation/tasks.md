---
description: "Task list for Top-20 Compliance Violations Remediation"
---

# Tasks: Top-20 Compliance Violations Remediation

**Input**: Design documents from `/specs/1008-top20-violations-remediation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md, contracts/analyzer-rules.md, contracts/required-ci-checks.md

**Tests**: No new tests are written by this initiative. Existing `pytest tests/` runs on every PR as a behavior-parity guard (FR-006). Each PR's post-refactor analyzer output is the primary quality gate (FR-001).

**Organization**: Tasks are grouped by user story (P1 = ranks 1-5, P2 = ranks 6-13, P3 = ranks 14-20). Within each story, tasks are further grouped **one PR per target file** (rank N gets 8 tasks: `T{N}.1`..`T{N}.8`), each corresponding to a step in the per-PR runbook in `quickstart.md`.

**Merge order**: STRICT worst-first (rank 1 -> rank 20). No PR opens for merge until the previous rank has squash-merged with all 234+ required CI checks green on `main` (FR-003).

## Format: `[TaskID] [P?] [Story] Description`

- **[P]**: Truly parallelizable (different files, no ordering dependency on incomplete work). Applied only to the baseline-capture task inside Phase 1 because rank-N baselines are independent reads. Everything after Phase 1 is sequential-per-rank (queue-linear merge is required by FR-003, so no [P] on the refactor / commit / merge tasks).
- **[Story]**: US1 (ranks 1-5, P1), US2 (ranks 6-13, P2), US3 (ranks 14-20, P3). Setup and Polish phases have no story label.
- Every task description includes the exact file path(s) it operates on.

---

## Phase 1: Setup (Campaign Readiness)

**Purpose**: One-time setup performed on `main` before any refactor branch is cut. Freezes the baseline for the whole initiative and confirms the environment satisfies the campaign's read-only invariants.

- [ ] T001 Sync `main` to origin and confirm clean working tree: `git checkout main; git pull --ff-only; git status` in `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\`.
- [ ] T002 Confirm the analyzer package is read-only by recording the current SHAs of `tools/compliance_analyzer/scoring.py`, `tools/compliance_analyzer/models.py`, `tools/compliance_analyzer/analyzers.py`, `tools/compliance_analyzer/engine.py`, and `tools/check_compliance.py` (baseline for SC-004 verification at end).
- [ ] T003 Capture repo-wide baseline: run `python -m tools.compliance_analyzer .` and archive the output as `specs/1008-top20-violations-remediation/baselines/repo_wide_baseline.txt` (baseline for SC-002 delta at T21).
- [ ] T004 [P] Capture per-file baselines for all 20 ranks in parallel (independent file reads, no branch created yet): run `python -m tools.compliance_analyzer <path>` against each of the twenty target paths and archive under `specs/1008-top20-violations-remediation/baselines/rank_{01..20}_pre.txt`.
- [ ] T005 Enumerate the current required-status-checks list from `main` branch protection (`gh api "repos/:owner/:repo/branches/main/protection/required_status_checks" --jq '.contexts[]'`) and record to `specs/1008-top20-violations-remediation/baselines/required_checks_snapshot.txt` (contract snapshot for FR-010, SC-005).

**Checkpoint**: Baselines captured for every rank and for the repo. Analyzer package fingerprint locked. Required-check list enumerated. The queue may now open rank 1.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: This is a refactor initiative on an existing codebase, so there is no new foundational code to write. The only foundational prerequisite is procedural: acknowledge and enforce the four campaign-wide invariants that every subsequent PR obeys.

- [ ] T006 Ratify the four invariants in the PR-author's working notes and the executor's runbook: (a) worst-first merge order rank 1 -> rank 20 (D-001), (b) hard >=95.0/A+ gate no exceptions (D-002), (c) zero suppressions across all diffs (FR-004), (d) zero edits to `tools/compliance_analyzer/**` and `tools/check_compliance.py` (FR-005). This task is administrative; it produces no code diff.

**Checkpoint**: Invariants acknowledged. Rank-1 refactor may begin.

---

## Phase 3: User Story 1 - Top-5 F-Graded Files (Priority: P1)

**Goal**: Lift ranks 1-5 (445 violations combined; ~46% of the top-20 violation debt) from grade F to grade A+/>=95.0. This is the largest single-slice repo-wide improvement and directly drives SC-002.

**Independent Test**: For each of the five files, after its PR merges, `python -m tools.compliance_analyzer <path>` on `main` reports score >=95.0 and grade A+ (spec Acceptance Scenario US1.1). Full `pytest tests/` remains green (FR-006).

### Rank 1: `src/maps/maps_manager.py` (F/54.0, 149 violations, 7243 LOC)

Dominant fix classes (per research.md predicted-fixes table): module split (>500 LOC), function decomposition, class extraction, inline-comment sweep, `LOG-LAZY` conversion, portable-path adoption. Expected extracted siblings (research 6): `src/maps/floorplan_operations.py`, `src/maps/heatmap_orchestration.py`, and `_data.py`/`_constants.py` for large data literals.

- [ ] T1.1 [US1] Analyze `src/maps/maps_manager.py`: re-run `python -m tools.compliance_analyzer src/maps/maps_manager.py`, refresh `specs/1008-top20-violations-remediation/baselines/rank_01_pre.txt`, and write a violations-by-rule-ID summary note to `_annotate_why.py`-adjacent scratch or PR draft (do not commit the scratch).
- [ ] T1.2 [US1] Branch: `git checkout main && git pull --ff-only && git checkout -b refactor/compliance-01-maps-manager`.
- [ ] T1.3 [US1] Refactor `src/maps/maps_manager.py` (and any new sibling modules under `src/maps/`) applying the predicted fix classes: decompose functions >25 LOC / >5 blocks / >5 params into methods on semantically named classes; add inline WHY comments on every touched and adjacent line (Constitution VI); convert every touched log call to lazy `%` formatting (`LOG-LAZY`); add `logging.info`/`logging.debug` pre/post around every touched action (Constitution VII); split into sibling modules only where a natural responsibility boundary exists AND the split does not require a wrapper (D-004, D-005); update callsites in importers (notably `src/maps/launcher/viewer_callbacks.py`) to hit the new real home directly - no thin forwarder left at the old location.
- [ ] T1.4 [US1] Verify locally on `src/maps/maps_manager.py` and any new sibling modules: `python -m py_compile <files>`, `ruff check <files>`, `black --check <files>`, `mypy --strict <files>` (if under strict), `python -m tools.compliance_analyzer src/maps/maps_manager.py` MUST report score >=95.0 / A+, `pytest tests/` MUST be green. Archive post output as `specs/1008-top20-violations-remediation/baselines/rank_01_post.txt`.
- [ ] T1.5 [US1] Commit, push, open PR: `git commit -m "refactor: maps_manager compliance F/54.0 -> A+/<post-score>"`, `git push -u origin refactor/compliance-01-maps-manager`, `gh pr create --base main --title "refactor: maps_manager compliance F/54.0 -> A+/<post-score>" --body-file <pr-body>` where `<pr-body>` embeds the contents of `rank_01_pre.txt`, `rank_01_post.txt`, and a prose structural-change summary (FR-009).
- [ ] T1.6 [US1] Wait for all 234+ required CI checks to go green on the PR: `gh pr checks <pr-number> --watch`. No check may be marked optional or skipped (FR-010, SC-005).
- [ ] T1.7 [US1] Squash-merge and delete branch: `gh pr merge <pr-number> --squash --delete-branch`.
- [ ] T1.8 [US1] Verify `main` is at the merged SHA and `python -m tools.compliance_analyzer src/maps/maps_manager.py` still reports >=95.0 / A+ on `main`; only then may rank 2 begin (FR-003).

### Rank 2: `src/maps/launcher/viewer_callbacks.py` (F/57.0, 96 violations, 3221 LOC)

Dominant fix classes: Plotly callback decomposition, state-machine extraction into a dedicated class, complexity reduction on deeply nested event handlers. Rebases on rank 1 if new helpers were extracted from `maps_manager.py`.

- [ ] T2.1 [US1] Analyze `src/maps/launcher/viewer_callbacks.py`: refresh `rank_02_pre.txt` against current `main` (post rank-1 merge) and record violations-by-rule-ID.
- [ ] T2.2 [US1] Branch: `git checkout main && git pull --ff-only && git checkout -b refactor/compliance-02-viewer-callbacks`.
- [ ] T2.3 [US1] Refactor `src/maps/launcher/viewer_callbacks.py`: extract the Plotly/Dash event-handler state machine into a semantically named class; make each callback signature a thin dispatch to that class's methods (no wrapper functions - method dispatch, not forwarder); flatten nested `if/elif` into dictionary dispatch or `match` where ranges are enumerable; add inline WHY comments per Constitution VI; lazy `%` logging; pre/post action logging.
- [ ] T2.4 [US1] Verify locally: `python -m py_compile`, `ruff check`, `black --check`, `mypy --strict` (if applicable), `python -m tools.compliance_analyzer src/maps/launcher/viewer_callbacks.py` >=95.0 / A+, `pytest tests/` green. Archive as `rank_02_post.txt`.
- [ ] T2.5 [US1] Commit, push, open PR titled `refactor: viewer_callbacks compliance F/57.0 -> A+/<post-score>` with pre/post analyzer output and prose summary in the body.
- [ ] T2.6 [US1] Wait for all 234+ required CI checks green (`gh pr checks --watch`).
- [ ] T2.7 [US1] Squash-merge and delete branch.
- [ ] T2.8 [US1] Confirm `main` at merged SHA and post-merge analyzer score on `main` before starting rank 3.

### Rank 3: `src/capture/packet_capture.py` (F/54.0, 68 violations, 2389 LOC)

Dominant fix classes: threading lifecycle refactor (context-managed capture threads), resource-management extraction (start/stop/teardown into a dedicated class), safe-input hardening for any interactive prompts. Known-tricky pattern (research 3): threaded packet capture teardown races.

- [ ] T3.1 [US1] Analyze `src/capture/packet_capture.py`: refresh `rank_03_pre.txt` and record violations-by-rule-ID.
- [ ] T3.2 [US1] Branch: `git checkout -b refactor/compliance-03-packet-capture` from a fresh `main` pull.
- [ ] T3.3 [US1] Refactor `src/capture/packet_capture.py`: extract capture-thread lifecycle into a class with explicit `start`, `stop`, `__enter__`/`__exit__` methods; adopt `safe_input()` at any interactive prompt sites (`SAFE-INPUT`); adopt `pathlib.Path` for any hard-coded separators (`SAFE-PATH`); decompose long functions; inline WHY comments; lazy `%` logging; pre/post action logging around every capture start/stop.
- [ ] T3.4 [US1] Verify locally: py_compile, ruff, black, mypy (if strict), analyzer >=95.0 / A+, `pytest tests/` green. Archive as `rank_03_post.txt`.
- [ ] T3.5 [US1] Commit, push, open PR titled `refactor: packet_capture compliance F/54.0 -> A+/<post-score>` with pre/post analyzer output and prose summary.
- [ ] T3.6 [US1] Wait for all 234+ required CI checks green.
- [ ] T3.7 [US1] Squash-merge and delete branch.
- [ ] T3.8 [US1] Confirm `main` at merged SHA and post-merge analyzer score before starting rank 4.

### Rank 4: `src/network/routing_utils.py` (F/54.0, 67 violations, 1888 LOC)

Dominant fix classes: long-function decomposition, portable-path adoption where hard-coded separators exist, inline-comment sweep.

- [ ] T4.1 [US1] Analyze `src/network/routing_utils.py`: refresh `rank_04_pre.txt` and record violations-by-rule-ID.
- [ ] T4.2 [US1] Branch: `git checkout -b refactor/compliance-04-routing-utils` from a fresh `main` pull.
- [ ] T4.3 [US1] Refactor `src/network/routing_utils.py`: decompose >25 LOC functions into cohesive helpers on a semantically named class; replace hard-coded `/` and `\\` separators with `pathlib.Path` (D-003) - preserving existing `os.path.join` usage where already behaviorally correct; inline WHY comments; lazy `%` logging; pre/post action logging.
- [ ] T4.4 [US1] Verify locally: py_compile, ruff, black, mypy (if strict), analyzer >=95.0 / A+, `pytest tests/` green. Archive as `rank_04_post.txt`.
- [ ] T4.5 [US1] Commit, push, open PR titled `refactor: routing_utils compliance F/54.0 -> A+/<post-score>` with pre/post analyzer output and prose summary.
- [ ] T4.6 [US1] Wait for all 234+ required CI checks green.
- [ ] T4.7 [US1] Squash-merge and delete branch.
- [ ] T4.8 [US1] Confirm `main` at merged SHA and post-merge analyzer score before starting rank 5.

### Rank 5: `src/device/utility_commands.py` (F/54.0, 65 violations, 1803 LOC)

Dominant fix classes: destructive-op confirmation review (menu 90-100 territory), function split, `safe_input` adoption. Known-tricky pattern (research 4): typed-confirmation patterns MUST be preserved unchanged for destructive operations.

- [ ] T5.1 [US1] Analyze `src/device/utility_commands.py`: refresh `rank_05_pre.txt` and record violations-by-rule-ID. Explicitly enumerate every destructive-operation callsite before refactor to ensure the typed-confirmation pattern is preserved verbatim.
- [ ] T5.2 [US1] Branch: `git checkout -b refactor/compliance-05-utility-commands` from a fresh `main` pull.
- [ ] T5.3 [US1] Refactor `src/device/utility_commands.py`: split long dispatch functions into methods on a semantically named `UtilityCommandRunner`-style class; wrap every `input()` call in `safe_input()` (`SAFE-INPUT`); retain every typed-confirmation guard (`if confirmation != "UPGRADE": return`) byte-identically (`SAFE-DESTRUCTIVE` non-regression); inline WHY comments; lazy `%` logging; pre/post action logging around every destructive dispatch.
- [ ] T5.4 [US1] Verify locally: py_compile, ruff, black, mypy (if strict), analyzer >=95.0 / A+, `pytest tests/` green, and manually smoke-test every menu 90-100 destructive path once via CLI to confirm the typed-confirmation prompts still reject wrong input and accept the exact expected string. Archive as `rank_05_post.txt`.
- [ ] T5.5 [US1] Commit, push, open PR titled `refactor: utility_commands compliance F/54.0 -> A+/<post-score>` with pre/post analyzer output, prose summary, and an explicit note in the body that all typed-confirmation guards remain byte-identical.
- [ ] T5.6 [US1] Wait for all 234+ required CI checks green.
- [ ] T5.7 [US1] Squash-merge and delete branch.
- [ ] T5.8 [US1] Confirm `main` at merged SHA and post-merge analyzer score before starting rank 6.

**Checkpoint (US1)**: Ranks 1-5 all at grade A+/>=95.0 on `main`. Roughly 46% of top-20 violation debt cleared. Repo-wide score should be visibly higher (early SC-002 progress). Ready to begin US2.

---

## Phase 4: User Story 2 - Mid-Tier F/D- Files (Priority: P2)

**Goal**: Lift ranks 6-13 (~299 violations combined) from grade F / D- / D to grade A+/>=95.0. After this slice no F-graded file remains in the top-20 and the D- tier is cleared.

**Independent Test**: Each of the eight files, after its PR merges, `python -m tools.compliance_analyzer <path>` on `main` reports score >=95.0 and grade A+ (spec Acceptance Scenario US2.1). For `tests/unit/test_arango_writer.py` (rank 8) the same test IDs must still execute and `pytest` exit code MUST be 0 (spec Acceptance Scenario US2.2). For `starlink_dashboard.py` (rank 13) the `__main__` entry point and documented CLI flags MUST behave identically (spec Acceptance Scenario US2.3).

### Rank 6: `src/ssid_consolidation/ssid_template_consolidation.py` (F/55.0, 53 violations)

Dominant fix classes: iteration/aggregation function decomposition, inline comments, lazy `%` logging.

- [ ] T6.1 [US2] Analyze `src/ssid_consolidation/ssid_template_consolidation.py`: refresh `rank_06_pre.txt`.
- [ ] T6.2 [US2] Branch: `git checkout -b refactor/compliance-06-ssid-template-consolidation` from a fresh `main`.
- [ ] T6.3 [US2] Refactor `src/ssid_consolidation/ssid_template_consolidation.py`: decompose aggregation loops into named helpers on a `SsidTemplateConsolidator` class; inline WHY comments; lazy `%` logging; pre/post action logging.
- [ ] T6.4 [US2] Verify locally: py_compile, ruff, black, mypy (if strict), analyzer >=95.0 / A+, `pytest tests/` green. Archive as `rank_06_post.txt`.
- [ ] T6.5 [US2] Commit, push, open PR titled `refactor: ssid_template_consolidation compliance F/55.0 -> A+/<post-score>` with pre/post analyzer output and prose summary.
- [ ] T6.6 [US2] Wait for all 234+ required CI checks green.
- [ ] T6.7 [US2] Squash-merge and delete branch.
- [ ] T6.8 [US2] Confirm `main` at merged SHA and post-merge analyzer score before starting rank 7.

### Rank 7: `scripts/mist_ideas_analyzer.py` (F/54.0, 46 violations)

Dominant fix classes: script-to-class extraction, extract business logic from `scripts/` into `src/` if reused, minimal `__main__`-only shim only if externally invoked. Note (research import-graph): rank 9 (`mist_ideas_distiller_v2.py`) may share helpers - extracting to `src/` here lets rank 9 import from the new home.

- [ ] T7.1 [US2] Analyze `scripts/mist_ideas_analyzer.py`: refresh `rank_07_pre.txt`. Identify any helper functions that would be reused by rank 9.
- [ ] T7.2 [US2] Branch: `git checkout -b refactor/compliance-07-mist-ideas-analyzer`.
- [ ] T7.3 [US2] Refactor `scripts/mist_ideas_analyzer.py`: extract business logic into a properly namespaced module under `src/` (e.g., `src/ideas/analyzer.py`) as a class; the script becomes a minimal `__main__` dispatch to that class if externally invoked, otherwise move wholesale (assumption line 155); inline WHY comments; lazy `%` logging; pre/post action logging.
- [ ] T7.4 [US2] Verify locally: py_compile, ruff, black, mypy (if strict), analyzer >=95.0 / A+ on the target path, `pytest tests/` green, `python scripts/mist_ideas_analyzer.py --help` still prints the pre-refactor help text if the script survived. Archive as `rank_07_post.txt`.
- [ ] T7.5 [US2] Commit, push, open PR titled `refactor: mist_ideas_analyzer compliance F/54.0 -> A+/<post-score>` with pre/post analyzer output and prose summary.
- [ ] T7.6 [US2] Wait for all 234+ required CI checks green.
- [ ] T7.7 [US2] Squash-merge and delete branch.
- [ ] T7.8 [US2] Confirm `main` at merged SHA and post-merge analyzer score before starting rank 8.

### Rank 8: `tests/unit/test_arango_writer.py` (D-/62.0, 39 violations)

Dominant fix classes (per research D-008): fixture extraction, parametrize split, scenario grouping. MUST preserve test IDs and coverage (spec Acceptance Scenario US2.2).

- [ ] T8.1 [US2] Analyze `tests/unit/test_arango_writer.py`: refresh `rank_08_pre.txt` and enumerate every existing test ID (nodeid list) via `pytest tests/unit/test_arango_writer.py --collect-only -q` archived to `specs/1008-top20-violations-remediation/baselines/rank_08_test_ids_pre.txt`.
- [ ] T8.2 [US2] Branch: `git checkout -b refactor/compliance-08-test-arango-writer`.
- [ ] T8.3 [US2] Refactor `tests/unit/test_arango_writer.py`: split large `@pytest.parametrize` blocks into cohesive groups, extract shared fixtures into `tests/unit/conftest.py`-adjacent location, group scenarios by behavior; MUST NOT delete tests, weaken assertions, or rename existing test nodeids in a way that removes them from the collection (test IDs are a superset preservation - additions are fine, deletions are not); inline WHY comments; lazy `%` logging on any log calls.
- [ ] T8.4 [US2] Verify locally: py_compile, ruff, black, analyzer >=95.0 / A+, `pytest tests/unit/test_arango_writer.py --collect-only -q` compared against `rank_08_test_ids_pre.txt` MUST be a superset (no removed nodeids), `pytest tests/` overall MUST exit 0. Archive as `rank_08_post.txt`.
- [ ] T8.5 [US2] Commit, push, open PR titled `refactor: test_arango_writer compliance D-/62.0 -> A+/<post-score>` with pre/post analyzer output, prose summary, and an explicit note listing test-ID preservation evidence.
- [ ] T8.6 [US2] Wait for all 234+ required CI checks green.
- [ ] T8.7 [US2] Squash-merge and delete branch.
- [ ] T8.8 [US2] Confirm `main` at merged SHA and post-merge analyzer score before starting rank 9.

### Rank 9: `scripts/mist_ideas_distiller_v2.py` (F/54.0, 34 violations)

Same pattern as rank 7 (script-to-class extraction). If rank 7 extracted shared helpers into `src/ideas/`, this refactor imports them from there directly - no local re-implementation, no forwarder from the old script path.

- [ ] T9.1 [US2] Analyze `scripts/mist_ideas_distiller_v2.py`: refresh `rank_09_pre.txt`. Cross-reference against helpers extracted by rank 7 in `src/ideas/` (if any).
- [ ] T9.2 [US2] Branch: `git checkout -b refactor/compliance-09-mist-ideas-distiller-v2`.
- [ ] T9.3 [US2] Refactor `scripts/mist_ideas_distiller_v2.py`: extract business logic to `src/ideas/distiller_v2.py` as a class (reusing rank-7 helpers directly - no re-implementation); leave a minimal `__main__` dispatch only if externally invoked; inline WHY comments; lazy `%` logging; pre/post action logging.
- [ ] T9.4 [US2] Verify locally: py_compile, ruff, black, mypy (if strict), analyzer >=95.0 / A+, `pytest tests/` green, `python scripts/mist_ideas_distiller_v2.py --help` behaves identically if the script survived. Archive as `rank_09_post.txt`.
- [ ] T9.5 [US2] Commit, push, open PR titled `refactor: mist_ideas_distiller_v2 compliance F/54.0 -> A+/<post-score>` with pre/post analyzer output and prose summary.
- [ ] T9.6 [US2] Wait for all 234+ required CI checks green.
- [ ] T9.7 [US2] Squash-merge and delete branch.
- [ ] T9.8 [US2] Confirm `main` at merged SHA and post-merge analyzer score before starting rank 10.

### Rank 10: `src/gateway/wan2_variable.py` (D-/62.0, 32 violations)

Dominant fix classes: variable-substitution logic decomposition, `LOG-LAZY` conversion. Cross-file note (research import-graph): rank 17 (`src/gateway/template_config.py`) may share helpers in `src/gateway/`. Extract shared logic here so rank 17 imports directly from the new home.

- [ ] T10.1 [US2] Analyze `src/gateway/wan2_variable.py`: refresh `rank_10_pre.txt`. Identify helper candidates that rank 17 would reuse.
- [ ] T10.2 [US2] Branch: `git checkout -b refactor/compliance-10-wan2-variable`.
- [ ] T10.3 [US2] Refactor `src/gateway/wan2_variable.py`: decompose variable-substitution functions into methods on a semantically named class in `src/gateway/`; extract genuinely shared logic to a sibling module (e.g., `src/gateway/_substitution.py`) only when a natural boundary exists AND rank 17 will import from the new home directly; inline WHY comments; lazy `%` logging; pre/post action logging.
- [ ] T10.4 [US2] Verify locally: py_compile, ruff, black, mypy (if strict), analyzer >=95.0 / A+, `pytest tests/` green. Archive as `rank_10_post.txt`.
- [ ] T10.5 [US2] Commit, push, open PR titled `refactor: wan2_variable compliance D-/62.0 -> A+/<post-score>` with pre/post analyzer output and prose summary.
- [ ] T10.6 [US2] Wait for all 234+ required CI checks green.
- [ ] T10.7 [US2] Squash-merge and delete branch.
- [ ] T10.8 [US2] Confirm `main` at merged SHA and post-merge analyzer score before starting rank 11.

### Rank 11: `src/audit/renderer.py` (D-/62.0, 29 violations)

Dominant fix classes: template-render function split, inline comments, lazy logging.

- [ ] T11.1 [US2] Analyze `src/audit/renderer.py`: refresh `rank_11_pre.txt`.
- [ ] T11.2 [US2] Branch: `git checkout -b refactor/compliance-11-audit-renderer`.
- [ ] T11.3 [US2] Refactor `src/audit/renderer.py`: decompose long template-render functions into methods on a `AuditRenderer` class; inline WHY comments; lazy `%` logging; pre/post action logging.
- [ ] T11.4 [US2] Verify locally: py_compile, ruff, black, mypy (if strict), analyzer >=95.0 / A+, `pytest tests/` green. Archive as `rank_11_post.txt`.
- [ ] T11.5 [US2] Commit, push, open PR titled `refactor: audit_renderer compliance D-/62.0 -> A+/<post-score>` with pre/post analyzer output and prose summary.
- [ ] T11.6 [US2] Wait for all 234+ required CI checks green.
- [ ] T11.7 [US2] Squash-merge and delete branch.
- [ ] T11.8 [US2] Confirm `main` at merged SHA and post-merge analyzer score before starting rank 12.

### Rank 12: `src/site/site_config_manager.py` (D/66.0, 29 violations)

Dominant fix classes: config-mutation function split, safety guards preserved (never remove a `SAFE-DESTRUCTIVE` guard - only wrap/decompose around it).

- [ ] T12.1 [US2] Analyze `src/site/site_config_manager.py`: refresh `rank_12_pre.txt`. Enumerate every safety guard site before refactor.
- [ ] T12.2 [US2] Branch: `git checkout -b refactor/compliance-12-site-config-manager`.
- [ ] T12.3 [US2] Refactor `src/site/site_config_manager.py`: decompose config-mutation functions into methods on `SiteConfigManager`; every existing safety guard remains byte-identical (Constitution III, FR-006); inline WHY comments; lazy `%` logging; pre/post action logging around every mutation.
- [ ] T12.4 [US2] Verify locally: py_compile, ruff, black, mypy (if strict), analyzer >=95.0 / A+, `pytest tests/` green. Archive as `rank_12_post.txt`.
- [ ] T12.5 [US2] Commit, push, open PR titled `refactor: site_config_manager compliance D/66.0 -> A+/<post-score>` with pre/post analyzer output and prose summary.
- [ ] T12.6 [US2] Wait for all 234+ required CI checks green.
- [ ] T12.7 [US2] Squash-merge and delete branch.
- [ ] T12.8 [US2] Confirm `main` at merged SHA and post-merge analyzer score before starting rank 13.

### Rank 13: `starlink_dashboard.py` (D/64.0, 28 violations)

Dominant fix classes: root-level script -> extract business logic to `src/`, minimal `__main__` only if externally referenced. CLI flag behavior MUST be preserved byte-identically (spec Acceptance Scenario US2.3).

- [ ] T13.1 [US2] Analyze `starlink_dashboard.py`: refresh `rank_13_pre.txt`. Capture the pre-refactor `--help` output to `rank_13_help_pre.txt` for CLI parity comparison.
- [ ] T13.2 [US2] Branch: `git checkout -b refactor/compliance-13-starlink-dashboard`.
- [ ] T13.3 [US2] Refactor `starlink_dashboard.py`: extract business logic to `src/starlink/dashboard.py` as a class; the root-level script becomes a minimal `__main__` dispatch preserving every existing CLI flag byte-identically (or moves wholesale if no external tooling calls it); inline WHY comments; lazy `%` logging; pre/post action logging.
- [ ] T13.4 [US2] Verify locally: py_compile, ruff, black, mypy (if strict), analyzer >=95.0 / A+, `pytest tests/` green. Diff `python starlink_dashboard.py --help` against `rank_13_help_pre.txt` MUST be empty. Archive as `rank_13_post.txt`.
- [ ] T13.5 [US2] Commit, push, open PR titled `refactor: starlink_dashboard compliance D/64.0 -> A+/<post-score>` with pre/post analyzer output, prose summary, and explicit CLI-parity evidence in the body.
- [ ] T13.6 [US2] Wait for all 234+ required CI checks green.
- [ ] T13.7 [US2] Squash-merge and delete branch.
- [ ] T13.8 [US2] Confirm `main` at merged SHA and post-merge analyzer score before starting rank 14.

**Checkpoint (US2)**: Ranks 6-13 all at grade A+/>=95.0 on `main`. Zero F-graded files remain in the top-20 and the D- tier is fully cleared. Ready to begin US3.

---

## Phase 5: User Story 3 - Tail D/C-Graded Files (Priority: P3)

**Goal**: Lift ranks 14-20 to grade A+/>=95.0 to fully resolve the top-20 list. Smallest per-file score deltas, but required to satisfy SC-008 ("no target file remains on the worst-files list").

**Independent Test**: Each of the seven files, after its PR merges, `python -m tools.compliance_analyzer <path>` on `main` reports score >=95.0 and grade A+ (spec Acceptance Scenario US3.1). For `tools/codemod_logging_lazy.py` (rank 18) a round-trip regression MUST show byte-identical output against a corpus vs the pre-refactor codemod (spec Acceptance Scenario US3.2, research D-009).

### Rank 14: `src/analytics/zone_analyzer.py` (D/65.0, 26 violations)

Dominant fix classes: aggregation/statistics function decomposition, inline comments.

- [ ] T14.1 [US3] Analyze `src/analytics/zone_analyzer.py`: refresh `rank_14_pre.txt`.
- [ ] T14.2 [US3] Branch: `git checkout -b refactor/compliance-14-zone-analyzer`.
- [ ] T14.3 [US3] Refactor `src/analytics/zone_analyzer.py`: decompose aggregation/statistics functions into methods on a `ZoneAnalyzer` class; inline WHY comments; lazy `%` logging; pre/post action logging.
- [ ] T14.4 [US3] Verify locally: py_compile, ruff, black, mypy (if strict), analyzer >=95.0 / A+, `pytest tests/` green. Archive as `rank_14_post.txt`.
- [ ] T14.5 [US3] Commit, push, open PR titled `refactor: zone_analyzer compliance D/65.0 -> A+/<post-score>` with pre/post analyzer output and prose summary.
- [ ] T14.6 [US3] Wait for all 234+ required CI checks green.
- [ ] T14.7 [US3] Squash-merge and delete branch.
- [ ] T14.8 [US3] Confirm `main` at merged SHA and post-merge analyzer score before starting rank 15.

### Rank 15: `src/inventory/csv_comparator.py` (D/64.0, 26 violations)

Dominant fix classes: diff-comparison function decomposition, portable-path adoption.

- [ ] T15.1 [US3] Analyze `src/inventory/csv_comparator.py`: refresh `rank_15_pre.txt`.
- [ ] T15.2 [US3] Branch: `git checkout -b refactor/compliance-15-csv-comparator`.
- [ ] T15.3 [US3] Refactor `src/inventory/csv_comparator.py`: decompose diff-comparison functions into methods on a `CsvComparator` class; replace hard-coded path separators with `pathlib.Path` (`SAFE-PATH`); inline WHY comments; lazy `%` logging; pre/post action logging.
- [ ] T15.4 [US3] Verify locally: py_compile, ruff, black, mypy (if strict), analyzer >=95.0 / A+, `pytest tests/` green. Archive as `rank_15_post.txt`.
- [ ] T15.5 [US3] Commit, push, open PR titled `refactor: csv_comparator compliance D/64.0 -> A+/<post-score>` with pre/post analyzer output and prose summary.
- [ ] T15.6 [US3] Wait for all 234+ required CI checks green.
- [ ] T15.7 [US3] Squash-merge and delete branch.
- [ ] T15.8 [US3] Confirm `main` at merged SHA and post-merge analyzer score before starting rank 16.

### Rank 16: `src/device/prompt_utils.py` (D/66.0, 25 violations)

Dominant fix classes: prompt-parsing decomposition, `safe_input` review at every `input()` site.

- [ ] T16.1 [US3] Analyze `src/device/prompt_utils.py`: refresh `rank_16_pre.txt`. Enumerate every `input()` callsite.
- [ ] T16.2 [US3] Branch: `git checkout -b refactor/compliance-16-prompt-utils`.
- [ ] T16.3 [US3] Refactor `src/device/prompt_utils.py`: decompose prompt-parsing functions into methods on a `PromptUtils` class; wrap every `input()` in `safe_input()` (`SAFE-INPUT`); inline WHY comments; lazy `%` logging; pre/post action logging.
- [ ] T16.4 [US3] Verify locally: py_compile, ruff, black, mypy (if strict), analyzer >=95.0 / A+, `pytest tests/` green. Archive as `rank_16_post.txt`.
- [ ] T16.5 [US3] Commit, push, open PR titled `refactor: prompt_utils compliance D/66.0 -> A+/<post-score>` with pre/post analyzer output and prose summary.
- [ ] T16.6 [US3] Wait for all 234+ required CI checks green.
- [ ] T16.7 [US3] Squash-merge and delete branch.
- [ ] T16.8 [US3] Confirm `main` at merged SHA and post-merge analyzer score before starting rank 17.

### Rank 17: `src/gateway/template_config.py` (D/65.0, 25 violations)

Dominant fix classes: config-template function split. If rank 10 extracted shared helpers in `src/gateway/`, this refactor imports them directly.

- [ ] T17.1 [US3] Analyze `src/gateway/template_config.py`: refresh `rank_17_pre.txt`. Cross-reference against helpers extracted by rank 10 in `src/gateway/`.
- [ ] T17.2 [US3] Branch: `git checkout -b refactor/compliance-17-template-config`.
- [ ] T17.3 [US3] Refactor `src/gateway/template_config.py`: decompose config-template functions into methods on a `TemplateConfig` class; reuse any `src/gateway/` helpers extracted by rank 10 directly (no re-implementation, no wrapper); inline WHY comments; lazy `%` logging; pre/post action logging.
- [ ] T17.4 [US3] Verify locally: py_compile, ruff, black, mypy (if strict), analyzer >=95.0 / A+, `pytest tests/` green. Archive as `rank_17_post.txt`.
- [ ] T17.5 [US3] Commit, push, open PR titled `refactor: template_config compliance D/65.0 -> A+/<post-score>` with pre/post analyzer output and prose summary.
- [ ] T17.6 [US3] Wait for all 234+ required CI checks green.
- [ ] T17.7 [US3] Squash-merge and delete branch.
- [ ] T17.8 [US3] Confirm `main` at merged SHA and post-merge analyzer score before starting rank 18.

### Rank 18: `tools/codemod_logging_lazy.py` (D-/60.0, 23 violations)

Dominant fix classes: codemod visitor decomposition, round-trip regression test (D-009). This file is a codemod itself; behavior parity means byte-identical output against a corpus. Note (analyzer contract line 141): `tools/codemod_logging_lazy.py` is a legitimate refactor target and is NOT part of the frozen `tools/compliance_analyzer/` package.

- [ ] T18.1 [US3] Analyze `tools/codemod_logging_lazy.py`: refresh `rank_18_pre.txt`. Assemble a representative corpus of pre-refactor logging call sites at `specs/1008-top20-violations-remediation/baselines/rank_18_corpus_pre/` (copy of a real-world sample of f-string log calls from the repo).
- [ ] T18.2 [US3] Branch: `git checkout -b refactor/compliance-18-codemod-logging-lazy`. Before refactoring, run the current codemod at `main` against the corpus and save output to `specs/1008-top20-violations-remediation/baselines/rank_18_expected.txt`.
- [ ] T18.3 [US3] Refactor `tools/codemod_logging_lazy.py`: decompose the AST-visitor into methods on a semantically named class; inline WHY comments; lazy `%` logging in the tool's own log calls (self-referential improvement); pre/post action logging around each visitor pass.
- [ ] T18.4 [US3] Verify locally: py_compile, ruff, black, mypy (if strict), analyzer >=95.0 / A+, `pytest tests/` green. Run the refactored codemod against the same corpus, save output to `rank_18_actual.txt`, and `diff rank_18_expected.txt rank_18_actual.txt` MUST be empty (byte-identical - the round-trip regression from spec Acceptance Scenario US3.2). Archive as `rank_18_post.txt`.
- [ ] T18.5 [US3] Commit, push, open PR titled `refactor: codemod_logging_lazy compliance D-/60.0 -> A+/<post-score>` with pre/post analyzer output, prose summary, and the empty round-trip diff attached as evidence in the body.
- [ ] T18.6 [US3] Wait for all 234+ required CI checks green.
- [ ] T18.7 [US3] Squash-merge and delete branch.
- [ ] T18.8 [US3] Confirm `main` at merged SHA and post-merge analyzer score before starting rank 19.

### Rank 19: `src/reports/e911_bssid.py` (D/65.0, 23 violations)

Dominant fix classes: report-generation function split, `LOG-LAZY` conversion.

- [ ] T19.1 [US3] Analyze `src/reports/e911_bssid.py`: refresh `rank_19_pre.txt`.
- [ ] T19.2 [US3] Branch: `git checkout -b refactor/compliance-19-e911-bssid`.
- [ ] T19.3 [US3] Refactor `src/reports/e911_bssid.py`: decompose report-generation functions into methods on an `E911BssidReporter` class; inline WHY comments; lazy `%` logging on every touched log call; pre/post action logging.
- [ ] T19.4 [US3] Verify locally: py_compile, ruff, black, mypy (if strict), analyzer >=95.0 / A+, `pytest tests/` green. Archive as `rank_19_post.txt`.
- [ ] T19.5 [US3] Commit, push, open PR titled `refactor: e911_bssid compliance D/65.0 -> A+/<post-score>` with pre/post analyzer output and prose summary.
- [ ] T19.6 [US3] Wait for all 234+ required CI checks green.
- [ ] T19.7 [US3] Squash-merge and delete branch.
- [ ] T19.8 [US3] Confirm `main` at merged SHA and post-merge analyzer score before starting rank 20.

### Rank 20: `scripts/menu_regroup.py` (C/73.0, 22 violations)

Dominant fix classes: script-to-class extraction, extract business logic to `src/` if reused. This is the smallest per-file delta but is the last item required for SC-008 (top-20 list fully cleared).

- [ ] T20.1 [US3] Analyze `scripts/menu_regroup.py`: refresh `rank_20_pre.txt`.
- [ ] T20.2 [US3] Branch: `git checkout -b refactor/compliance-20-menu-regroup`.
- [ ] T20.3 [US3] Refactor `scripts/menu_regroup.py`: extract business logic into `src/menu/regroup.py` as a class; the script becomes a minimal `__main__` dispatch if externally invoked, otherwise moves wholesale; inline WHY comments; lazy `%` logging; pre/post action logging.
- [ ] T20.4 [US3] Verify locally: py_compile, ruff, black, mypy (if strict), analyzer >=95.0 / A+ on the target path, `pytest tests/` green, `python scripts/menu_regroup.py --help` behaves identically if the script survived. Archive as `rank_20_post.txt`.
- [ ] T20.5 [US3] Commit, push, open PR titled `refactor: menu_regroup compliance C/73.0 -> A+/<post-score>` with pre/post analyzer output and prose summary.
- [ ] T20.6 [US3] Wait for all 234+ required CI checks green.
- [ ] T20.7 [US3] Squash-merge and delete branch.
- [ ] T20.8 [US3] Confirm `main` at merged SHA and post-merge analyzer score. The top-20 list is now fully cleared.

**Checkpoint (US3)**: All 20 target files at grade A+/>=95.0 on `main`. Ready for repo-wide verification.

---

## Phase 6: Polish and Cross-Cutting Verification

**Purpose**: Post-initiative repo-wide checks that all seven Success Criteria hold on `main` after every rank has merged.

- [ ] T21 Re-run the repo-wide compliance analyzer on `main`: `python -m tools.compliance_analyzer .` and diff against `specs/1008-top20-violations-remediation/baselines/repo_wide_baseline.txt`. Verify (a) SC-002: overall repo score improved by >=2.0 points from the 89.8/100 baseline (target A- band or better); (b) SC-001: each of the twenty target paths independently reports >=95.0 / A+; (c) SC-003: `git diff <baseline-commit>..HEAD -- .` grepped for `# noqa|# type: ignore|# pragma: no cover|# pylint: disable|# ruff: noqa|# mypy: ignore|# flake8: noqa|# nosec` returns empty; (d) SC-004: `git diff <baseline-commit>..HEAD -- tools/compliance_analyzer/ tools/check_compliance.py pyproject.toml` returns empty; (e) SC-008: `compliance_report.md` regenerated on `main` contains none of the twenty target file paths in its "worst files" section. Write the verification report to `specs/1008-top20-violations-remediation/baselines/final_verification.md`.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - runs on `main`, produces baselines only.
- **Foundational (Phase 2)**: Administrative acknowledgment; no code diff; unblocks Phase 3.
- **User Story 1 (Phase 3)**: Depends on Setup + Foundational. Ranks 1-5 execute strictly in order.
- **User Story 2 (Phase 4)**: Depends on US1 completing (rank 5 merged with CI green on `main`). Ranks 6-13 execute strictly in order.
- **User Story 3 (Phase 5)**: Depends on US2 completing (rank 13 merged with CI green on `main`). Ranks 14-20 execute strictly in order.
- **Polish (Phase 6)**: Depends on rank 20 merged with CI green on `main`.

### Sequential-merge invariant (FR-003)

For any two ranks A and B where `A < B`, rank A's PR MUST be squash-merged and its required CI green on `main` BEFORE rank B's branch is cut from `main`. This is why almost none of the refactor / commit / merge tasks below carry the [P] marker - the merge queue is linear by contract.

### Within each rank (T{N}.1 -> T{N}.8)

- T{N}.1 (analyze) MUST complete before T{N}.2 (branch).
- T{N}.2 (branch) MUST complete before T{N}.3 (refactor).
- T{N}.3 (refactor) MUST complete before T{N}.4 (verify locally).
- T{N}.4 (verify locally) MUST show analyzer >=95.0 / A+ before T{N}.5 (commit+push+PR).
- T{N}.5 (open PR) MUST complete before T{N}.6 (wait for CI).
- T{N}.6 (CI green) MUST complete before T{N}.7 (squash-merge).
- T{N}.7 (squash-merge) MUST complete before T{N}.8 (confirm main).
- T{N}.8 (confirm main) MUST complete before rank (N+1) begins.

### Import-graph edges to remember (from research.md)

- Rank 1 -> Rank 2: `viewer_callbacks.py` imports from `maps_manager.py`. Sequential merge order handles this automatically.
- Rank 7 -> Rank 9: both `mist_ideas_*` scripts may share helpers. If rank 7 extracts to `src/ideas/`, rank 9 imports directly (no re-implementation).
- Rank 10 -> Rank 17: both live under `src/gateway/`. If rank 10 extracts shared helpers, rank 17 imports directly.
- Rank 8 (`test_arango_writer.py`) has no runtime importers.
- Rank 18 (`codemod_logging_lazy.py`) is a codemod, not called at runtime by any other target file.

### Parallel Opportunities

- **T004 (baseline captures)** is the only [P] task in the whole plan: reading twenty independent files with the analyzer has no ordering dependency.
- **Analysis of rank N+1 (T{N+1}.1)** MAY start during rank N's CI-wait (T{N}.6) provided (a) no branch is created and (b) no code is edited until rank N is fully merged. Drafting only; no commits. This is a soft optimization, not a task-level [P].
- **PR merges are strictly sequential** (FR-003). No two refactor PRs may be in the `open-for-merge` state simultaneously.

---

## Parallel Example: Setup baselines

Because these are independent read-only invocations of the analyzer, they may run concurrently on a single machine (subprocess pool) or as separate CI matrix jobs:

```powershell
# Twenty independent baseline captures (no branches, no writes to the target files):
python -m tools.compliance_analyzer src/maps/maps_manager.py                            > baselines/rank_01_pre.txt
python -m tools.compliance_analyzer src/maps/launcher/viewer_callbacks.py               > baselines/rank_02_pre.txt
python -m tools.compliance_analyzer src/capture/packet_capture.py                       > baselines/rank_03_pre.txt
python -m tools.compliance_analyzer src/network/routing_utils.py                        > baselines/rank_04_pre.txt
python -m tools.compliance_analyzer src/device/utility_commands.py                      > baselines/rank_05_pre.txt
python -m tools.compliance_analyzer src/ssid_consolidation/ssid_template_consolidation.py > baselines/rank_06_pre.txt
python -m tools.compliance_analyzer scripts/mist_ideas_analyzer.py                      > baselines/rank_07_pre.txt
python -m tools.compliance_analyzer tests/unit/test_arango_writer.py                    > baselines/rank_08_pre.txt
python -m tools.compliance_analyzer scripts/mist_ideas_distiller_v2.py                  > baselines/rank_09_pre.txt
python -m tools.compliance_analyzer src/gateway/wan2_variable.py                        > baselines/rank_10_pre.txt
python -m tools.compliance_analyzer src/audit/renderer.py                               > baselines/rank_11_pre.txt
python -m tools.compliance_analyzer src/site/site_config_manager.py                     > baselines/rank_12_pre.txt
python -m tools.compliance_analyzer starlink_dashboard.py                               > baselines/rank_13_pre.txt
python -m tools.compliance_analyzer src/analytics/zone_analyzer.py                      > baselines/rank_14_pre.txt
python -m tools.compliance_analyzer src/inventory/csv_comparator.py                     > baselines/rank_15_pre.txt
python -m tools.compliance_analyzer src/device/prompt_utils.py                          > baselines/rank_16_pre.txt
python -m tools.compliance_analyzer src/gateway/template_config.py                      > baselines/rank_17_pre.txt
python -m tools.compliance_analyzer tools/codemod_logging_lazy.py                       > baselines/rank_18_pre.txt
python -m tools.compliance_analyzer src/reports/e911_bssid.py                           > baselines/rank_19_pre.txt
python -m tools.compliance_analyzer scripts/menu_regroup.py                             > baselines/rank_20_pre.txt
```

---

## Implementation Strategy

### MVP (User Story 1 only)

1. Complete Phase 1: Setup (baselines captured).
2. Complete Phase 2: Foundational (invariants acknowledged).
3. Complete Phase 3: US1 (ranks 1-5). Each rank's 8 tasks execute serially; the next rank does not start until the previous is merged and CI is green on `main`.
4. **STOP and VALIDATE**: `python -m tools.compliance_analyzer <path>` on each of the five paths on `main` reports >=95.0 / A+. Repo-wide analyzer shows measurable score improvement (partial SC-002 progress).
5. Deploy/demo if ready. US1 alone eliminates the five worst files and drives the largest single-slice repo-wide score bump (~46% of top-20 violation debt).

### Incremental Delivery

1. Complete Setup + Foundational.
2. Add US1 (ranks 1-5) -> Validate independently on `main` -> Deploy/Demo (MVP).
3. Add US2 (ranks 6-13) -> Validate independently -> Deploy/Demo (zero F-graded files remain, D- tier cleared).
4. Add US3 (ranks 14-20) -> Validate independently -> Deploy/Demo (top-20 list fully cleared, SC-008 satisfied).
5. Run T21 -> Final verification of SC-001..SC-008.

### Single-executor sequential (recommended)

Because merges are strictly linear (FR-003), the campaign runs most predictably with one executor working one rank at a time. Drafting rank N+1's analyze step during rank N's CI-wait is permitted but MUST NOT touch any file or open any branch until rank N is merged.

---

## Notes

- Every rank has exactly 8 tasks (T{N}.1 through T{N}.8), one per step in the per-PR runbook derived from `quickstart.md`.
- The [P] marker appears ONLY on T004 (setup baselines) because that is the only truly parallelizable operation in the whole initiative. FR-003 sequential merge invariant precludes [P] on refactor / commit / merge tasks.
- Every task description contains the exact repo-relative path(s) it touches, plus the branch name for the corresponding rank.
- PR title format is fixed by the plan (Commit / PR message format section) as `refactor: <file-slug> compliance <old-grade>/<old-score> -> A+/<new-score>`.
- No new tests are written by this initiative. `pytest tests/` runs on every PR as the behavior-parity guard (FR-006). New unit tests are not required to pass compliance - the analyzer is the primary quality gate.
- The rollback / failure handling protocol (plan section) applies at any T{N}.4 that cannot reach >=95.0 without a wrapper: pause the PR, document the specific rule + construct in the PR body, escalate to the human maintainer. Do not add a suppression. Do not lower the threshold.

## Extension Hooks

**Optional Hook**: git
Command: `/speckit.git.commit`
Description: Auto-commit after task generation

Prompt: Commit task changes?
To execute: `/speckit.git.commit`

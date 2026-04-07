# Tasks — SSID Template Consolidation (Feature 018)

Phase 1 — Setup (project initialization)

- [ ] T001 [P] Create/verify feature branch and artifacts in `specs/feat/018-ssid-template-consolidation/` (ensure `spec.md`, `plan.md`, `tasks.md`, `research.md` exist) [specs/feat/018-ssid-template-consolidation/]
- [ ] T002 Fix markdown lint warnings in `specs/feat/018-ssid-template-consolidation/spec.md`, `data-model.md`, and `contracts/api-contract.md` [specs/feat/018-ssid-template-consolidation/]
- [ ] T003 [P] Add `SSID_CONSOLIDATION_CACHE_MINUTES` entry and comment to `deploy/.env.example` (or `deploy/.env.example` if present) [deploy/.env.example]
- [ ] T004 [P] Add menu 159 documentation and brief usage note to `README.md` and link `specs/feat/018-ssid-template-consolidation/quickstart.md` [README.md]
- [ ] T005 [P] Create package directory and module skeleton `src/ssid_consolidation/__init__.py` and `src/ssid_consolidation/manager.py` [src/ssid_consolidation/]

Bootstrap tasks (prerequisites)

- [ ] T034 Implement SSID selector prompt and `.env` default behavior; add unit tests [MistHelper.py, src/ssid_consolidation/utils.py]
- [ ] T035 Implement phase-selection sub-menu and `--phase` flag CLI; add acceptance tests [MistHelper.py]
- [ ] T036 Implement phase prerequisite enforcement checks in `SSIDTemplateConsolidationManager` and unit tests [src/ssid_consolidation/manager.py]
- [ ] T037 Update tasks to require class-based components and document justification in `plan.md` [specs/feat/018-ssid-template-consolidation/plan.md]

Phase 2 — Foundational (blocking prerequisites)

- [ ] T006 [P] Implement base `SSIDTemplateConsolidationManager` class skeleton in `src/ssid_consolidation/manager.py` (class, init, logging hooks) [src/ssid_consolidation/manager.py]
- [ ] T007 Implement `Phase1Matrix` and `DeviationReport` dataclasses in `src/ssid_consolidation/models.py` (fields per `data-model.md`) [src/ssid_consolidation/models.py]
- [ ] T008 Implement `OperationsLog` persistence helper and DB migration helper in `src/ssid_consolidation/logging.py` (sqlite schema) [src/ssid_consolidation/logging.py]

Phase 3 — User Stories (priority order)

- US1 — Discover & Audit All Existing Templates (Priority: P1)
- [ ] T009 [US1] Implement `Collector` class to fetch org templates, site assignments, and SSID data using `mistapi` in `src/ssid_consolidation/collector.py` (respect rate limits) [src/ssid_consolidation/collector.py]
- [ ] T010 [US1] Implement `CacheManager` class (SQLite) honoring `SSID_CONSOLIDATION_CACHE_MINUTES` in `src/ssid_consolidation/cache.py` and integrate with `Collector` [src/ssid_consolidation/cache.py]
- [ ] T011 [US1] Implement `AnalysisManager` class for per-cluster deviation and cross-cluster drift analysis in `src/ssid_consolidation/analysis.py` (FR-010a/FR-010b) [src/ssid_consolidation/analysis.py]
- [ ] T012 [US1] Implement `Exporter` class and `DataExporter` adapter in `src/ssid_consolidation/exporter.py` (CSV+SQLite output to `data/ssid-consolidation/`) [src/ssid_consolidation/exporter.py]
- [ ] T013 [US1] Add unit tests for `analysis.py` and `cache.py` in `tests/unit/test_analysis.py` and `tests/unit/test_cache.py` (pytest + pytest-mock) [tests/unit/]
- [X] T014 [US1] Wire CLI/menu entry in `MistHelper.py` to invoke `SSIDTemplateConsolidationManager.phase1_collect()` via `menu 159` [MistHelper.py]

 - [X] T005 [P] Create package directory and module skeleton `src/ssid_consolidation/__init__.py` and `src/ssid_consolidation/manager.py` [src/ssid_consolidation/]

- [X] T006 [P] Implement base `SSIDTemplateConsolidationManager` class skeleton in `src/ssid_consolidation/manager.py` (class, init, logging hooks) [src/ssid_consolidation/manager.py]
- [X] T007 Implement `Phase1Matrix` and `DeviationReport` dataclasses in `src/ssid_consolidation/models.py` (fields per `data-model.md`) [src/ssid_consolidation/models.py]
- [X] T008 Implement `OperationsLog` persistence helper and DB migration helper in `src/ssid_consolidation/logging.py` (sqlite schema) [src/ssid_consolidation/logging.py]

- [X] T009 [US1] Implement `Collector` class to fetch org templates, site assignments, and SSID data using `mistapi` in `src/ssid_consolidation/collector.py` (respect rate limits) [src/ssid_consolidation/collector.py]
- [X] T010 [US1] Implement `CacheManager` class (SQLite) honoring `SSID_CONSOLIDATION_CACHE_MINUTES` in `src/ssid_consolidation/cache.py` and integrate with `Collector` [src/ssid_consolidation/cache.py]
- [X] T011 [US1] Implement `AnalysisManager` class for per-cluster deviation and cross-cluster drift analysis in `src/ssid_consolidation/analysis.py` (FR-010a/FR-010b) [src/ssid_consolidation/analysis.py]
- [X] T012 [US1] Implement `Exporter` class and `DataExporter` adapter in `src/ssid_consolidation/exporter.py` (CSV+SQLite output to `data/ssid-consolidation/`) [src/ssid_consolidation/exporter.py]
- [X] T013 [US1] Add unit tests for `analysis.py` and `cache.py` in `tests/unit/test_analysis.py` and `tests/unit/test_cache.py` (pytest + pytest-mock) [tests/unit/]
- [X] T014 [US1] Wire CLI/menu entry in `MistHelper.py` to invoke `SSIDTemplateConsolidationManager.phase1_collect()` via `menu 159` [MistHelper.py]

US2 — Configure Site Variables for Consolidation (Priority: P2)
- [ ] T015 [US2] Implement site-variable computation helper in `src/ssid_consolidation/variables.py` (derive VLANs, edge cluster refs) [src/ssid_consolidation/variables.py]
- [ ] T016 [US2] Implement site-variable writer in `src/ssid_consolidation/variables.py` using `mistapi` with idempotence checks and results logging [src/ssid_consolidation/variables.py]
- [ ] T017 [US2] Add typed confirmation using `safe_input()` before any writes and log choices to `OperationsLog` [src/ssid_consolidation/manager.py]
- [ ] T018 [US2] Add unit tests for variable computation and writer in `tests/unit/test_variables.py` [tests/unit/test_variables.py]

US3 — Organize Sites into Template Groups (Priority: P3)
- [ ] T019 [US3] Implement site group creation and assignment in `src/ssid_consolidation/groups.py` (create missing groups, idempotent assignment) [src/ssid_consolidation/groups.py]
- [ ] T020 [US3] Add unit tests for group assignment idempotence in `tests/unit/test_groups.py` [tests/unit/test_groups.py]

US4 — Create Consolidated Templates (Priority: P4)
- [ ] T021 [US4] Implement template creation/updating in `src/ssid_consolidation/templates.py` (append-only SSID addition, variable placeholders) [src/ssid_consolidation/templates.py]
- [ ] T022 [US4] Implement deviation-resolution UI module `src/ssid_consolidation/resolve.py` that prompts engineer for canonical values and records audit choices [src/ssid_consolidation/resolve.py]
- [ ] T023 [US4] Implement `generate_template_name()` and tests per FR-016c in `src/ssid_consolidation/utils.py` and `tests/unit/test_utils.py` [src/ssid_consolidation/utils.py]

US5 — Disable Old Template SSIDs (Priority: P5)
- [ ] T024 [US5] Implement cutover disable flow in `src/ssid_consolidation/cutover.py` that disables old SSIDs (non-destructive) and writes operations to `OperationsLog` [src/ssid_consolidation/cutover.py]
- [ ] T025 [US5] Add integration test that simulates cutover with mocked `mistapi` and verifies `enabled=False` is set for old SSIDs in `tests/integration/test_cutover.py` [tests/integration/test_cutover.py]

Phase 4 — Cross-cutting & polish
- [ ] T026 [P] Ensure `request_with_retries()` rate-limit wrapper from `MistHelper.py` is reused; add `src/ssid_consolidation/api.py` adapter if needed [src/ssid_consolidation/api.py]
- [ ] T027 [P] Persist `OperationsLog` entries to SQLite and add query helpers in `src/ssid_consolidation/logging.py` [src/ssid_consolidation/logging.py]
- [ ] T028 [P] Add integration test harness `tests/integration/conftest.py` that provides a mocked `mistapi` client fixture [tests/integration/]
- [ ] T029 [P] Update `specs/feat/018-ssid-template-consolidation/checklists/requirements.md` and `README.md` with final instructions and safety notes [specs/feat/018-ssid-template-consolidation/checklists/requirements.md, README.md]
- [ ] T030 Prepare PR branch and PR body (link spec, include checklist, add labels `feature,in-progress`) and open the PR or create draft PR instructions in `specs/feat/018-ssid-template-consolidation/pr_instructions.md` [specs/feat/018-ssid-template-consolidation/pr_instructions.md]

Dependencies (story completion order)

- Phase order (blocking): US1 → US2 → US3 → US4 → US5
- Implementation order (parallelizable elements):
  - `models.py` + `logging.py` must exist before collector/analysis/templates
  - Collector and cache must be implemented before deviation analysis and exports
  - Variables computation can be developed in parallel with group assignment once collector outputs are stable

Parallel execution examples

- Example A (parallel): `tests/unit/*` tasks (T013, T018, T020, T023) can be implemented in parallel across different test files. [tests/unit/]
- Example B (parallel): Documentation updates (T004, T029) and `.env.example` update (T003) can be done in parallel. [README.md, deploy/.env.example]

Independent test criteria (per story)

- US1: `tests/unit/test_analysis.py` verifies deviation output shape; `exporter` writes CSV and SQLite; manually run `python MistHelper.py --menu 159 --phase 1 --target-ssid <name>` against mocked API.
- US2: `tests/unit/test_variables.py` verifies idempotence; writer logs `already configured` when values match.
- US3: `tests/unit/test_groups.py` verifies "already assigned" behavior and create-if-missing.
- US4: `tests/unit/test_utils.py` verifies `generate_template_name()` and `templates.py` append-only behavior with mocks.
- US5: `tests/integration/test_cutover.py` verifies disable logic against mocked `mistapi`.

Suggested MVP scope

- MVP: Complete US1 (Phase 1 collection, caching, deviation analysis, CSV/SQLite export) and CLI wiring (T009..T014). This yields an independently useful audit export and allows iterative delivery of writes.

Final Phase — Polish & cross-cutting concerns

- [ ] T031 Run `python -m py_compile MistHelper.py` and fix any syntax issues before merging [MistHelper.py]
- [ ] T032 Run linter (`ruff`) and fix style issues project-wide (focus on `src/ssid_consolidation/` and updated spec files) [project root]
- [ ] T033 Ensure tests run locally: `pytest tests/unit -q` and `pytest tests/integration -q` and add CI job if missing [tests/]


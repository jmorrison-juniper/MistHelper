# Tasks: Site Analytics Package

**Input**: `spec.md` and `plan.md` in this feature directory.

**Authority**: GitHub `main` at `0b04cda81c8ef75096f3bedae0885038c775d665`.

**Tests**: The specification requires focused behavior tests, guard failure proofs, and source-wide quality gates.

## Phase 1: Setup

**Purpose**: Record the approved baseline and protect the worktree scope.

- [X] T001 Verify authority commit `0b04cda81c8ef75096f3bedae0885038c775d665` with `git cat-file -e 0b04cda81c8ef75096f3bedae0885038c775d665^{commit}`
- [X] T002 Record `git status --short` and confirm no unrelated change owns any implementation path in `src/`, `tests/`, `scripts/`, `documentation/`, or `changelog.d/`
- [X] T003 Extract module-level symbols from the authority versions of `mist/intelligence/analytics/site_analytics_configurator.py`, `site_inventory_health_analyzer.py`, and `zone_analyzer.py`
- [X] T004 Confirm authority symbol counts of 16, 14, and 92 before editing `tests/guardrails/test_src_public_symbol_preservation.py`

---

## Phase 2: Foundational Work

**Purpose**: Create the canonical package and move each module without behavior changes.

**Warning**: Complete this phase before any caller update. A partial move breaks imports.

- [X] T005 Add a docstring-only package initializer at `src/mist/intelligence/analytics/site/__init__.py`
- [X] T006 Move `src/mist/intelligence/analytics/site_analytics_configurator.py` to `src/mist/intelligence/analytics/site/site_analytics_configurator.py` without body changes
- [X] T007 Move `src/mist/intelligence/analytics/site_inventory_health_analyzer.py` to `src/mist/intelligence/analytics/site/site_inventory_health_analyzer.py` without body changes
- [X] T008 Move `src/mist/intelligence/analytics/zone_analyzer.py` to `src/mist/intelligence/analytics/site/zone_analyzer.py` without body changes
- [X] T009 Confirm that the three old paths under `src/mist/intelligence/analytics/` are absent and contain no wrapper, alias, forwarding module, or fallback

**Checkpoint**: The canonical package exists. The old module paths do not exist.

---

## Phase 3: User Story 1 - Find Site Analytics in One Package

**Goal**: Give maintainers one bounded package for all site analytics modules.

**Independent Test**: Confirm four analytics root children and three `site` package children after metadata exclusions.

- [X] T010 [US1] Inspect direct children in `src/mist/intelligence/analytics/` and require three modules plus the `site` package
- [X] T011 [US1] Inspect direct children in `src/mist/intelligence/analytics/site/` and require the three moved modules plus metadata-only `__init__.py`
- [X] T012 [US1] Confirm `src/mist/intelligence/analytics/site/__init__.py` contains only its package docstring

**Checkpoint**: User Story 1 is independently inspectable and complete.

---

## Phase 4: User Story 2 - Preserve Analytics Behavior and Symbols

**Goal**: Preserve all behavior, symbols, safety controls, and analytics root exports.

**Independent Test**: Compare authority symbols and run all existing focused analytics tests.

### Symbol and Export Preservation

- [X] T013 [US2] Map `mist/intelligence/analytics/site_analytics_configurator.py` to `mist/intelligence/analytics/site/site_analytics_configurator.py` with 16 symbols in `tests/guardrails/test_src_public_symbol_preservation.py`
- [X] T014 [US2] Map `mist/intelligence/analytics/site_inventory_health_analyzer.py` to `mist/intelligence/analytics/site/site_inventory_health_analyzer.py` with 14 symbols in `tests/guardrails/test_src_public_symbol_preservation.py`
- [X] T015 [US2] Map `mist/intelligence/analytics/zone_analyzer.py` to `mist/intelligence/analytics/site/zone_analyzer.py` with 92 symbols in `tests/guardrails/test_src_public_symbol_preservation.py`
- [X] T016 [US2] Preserve definitions, assignments, annotated assignments, imported names, private names, constants, type aliases, and helpers in `tests/guardrails/test_src_public_symbol_preservation.py`
- [X] T017 [US2] Update imports in `src/mist/intelligence/analytics/__init__.py` to the new configurator and inventory module paths
- [X] T018 [US2] Preserve only `SiteAnalyticsConfigurator`, `SiteAnalyticsConfiguratorDeps`, `SiteInventoryHealthAnalyzer`, and `SiteInventoryHealthAnalyzerDeps` in `src/mist/intelligence/analytics/__init__.py`
- [X] T019 [US2] Add root export identity assertions for the four approved classes in the applicable analytics unit tests under `tests/unit/analytics/`

### Focused Behavior Tests

- [X] T020 [P] [US2] Run `python -m pytest tests/unit/analytics/test_site_analytics_configurator.py`
- [X] T021 [P] [US2] Run `python -m pytest tests/unit/analytics/test_site_inventory_health_analyzer.py`
- [X] T022 [P] [US2] Run `python -m pytest tests/unit/test_zone_analyzer.py`
- [X] T023 [P] [US2] Run `python -m pytest tests/unit/export/test_site_export_utils_extended.py`
- [X] T024 [US2] Run `python -m pytest tests/guardrails/test_src_public_symbol_preservation.py` and require all 122 mapped symbols

**Checkpoint**: User Story 2 preserves symbols, root exports, prompts, logs, outputs, Mist calls, errors, and cancellation behavior.

---

## Phase 5: User Story 3 - Use Only Canonical Site Paths

**Goal**: Replace every active old path with its canonical `analytics.site` path.

**Independent Test**: Search tracked active surfaces and require zero old dotted imports or slash paths.

### Runtime and Script Paths

- [X] T025 [US3] Update both configurator imports and both inventory imports in `MistHelper.py` while preserving names and aliases
- [X] T026 [US3] Update the delayed zone import and its path text in `src/operations/exporting/export/site_export_utils.py`
- [X] T027 [US3] Update the embedded source path and delayed zone import in `scripts/replace_zone.py`

### Test, Mock, and Logger Paths

- [X] T028 [P] [US3] Update imports and patch targets in `tests/unit/analytics/test_site_analytics_configurator.py`
- [X] T029 [P] [US3] Update imports, patch targets, and `_MODULE_LOGGER` in `tests/unit/analytics/test_site_inventory_health_analyzer.py`
- [X] T030 [P] [US3] Update the docstring, imports, patch targets, and logger targets in `tests/unit/test_zone_analyzer.py`
- [X] T031 [P] [US3] Import `zone_analyzer` from `src.mist.intelligence.analytics.site` in `tests/unit/export/test_site_export_utils_extended.py`

### Maintained and Generated Documentation Paths

- [X] T032 [P] [US3] Update only moved source links in `documentation/menu-api/safe.md`
- [X] T033 [P] [US3] Update only moved source links in `documentation/menu-api/destructive.md`
- [X] T034 [P] [US3] Update only moved source links in `documentation/wiki/Menu-API-Endpoints-Safe.md`
- [X] T035 [P] [US3] Update moved source links in `documentation/wiki/Menu-API-Endpoints-Destructive.md`, `documentation/architecture.md`, and `documentation/diagrams/core/architecture-overview.md`
- [X] T036 [US3] Run `python scripts/generate_menu_wiki.py` and reject changes outside the approved source links
- [X] T037 [US3] Run `python -m scripts.menu_api_map` and reject changes outside the four approved endpoint pages
- [X] T038 [US3] Confirm `CHANGELOG.md` and all specification directories outside this feature directory have zero changes

**Checkpoint**: User Story 3 has zero active old-path references and no historical record changes.

---

## Phase 6: User Story 4 - Detect Analytics Structure Drift

**Goal**: Fail clearly when the scoped analytics hierarchy or active path set drifts.

**Independent Test**: Run repository success checks and direct failure proofs for six children, a missing root, and an old path.

### Structural Inspector

- [X] T039 [US4] Add `AnalyticsStructureInspector` with analytics-root and repository-root inputs in `tests/guardrails/test_analytics_package_structure.py`
- [X] T040 [US4] Validate both required analytics directories before returning counts in `tests/guardrails/test_analytics_package_structure.py`
- [X] T041 [US4] Exclude `__init__.py`, `__pycache__`, `.mypy_cache`, and `.pytest_cache` in `tests/guardrails/test_analytics_package_structure.py`
- [X] T042 [US4] Count sorted direct files and directories only under `src/mist/intelligence/analytics` in `tests/guardrails/test_analytics_package_structure.py`
- [X] T043 [US4] Enforce five or fewer structural children and stable repository-relative paths in `tests/guardrails/test_analytics_package_structure.py`
- [X] T044 [US4] Require counts of four for `src/mist/intelligence/analytics` and three for its `site` package in `tests/guardrails/test_analytics_package_structure.py`
- [X] T045 [US4] Require the success report to name exactly two checked package directories in `tests/guardrails/test_analytics_package_structure.py`

### Active Path Inspector

- [X] T046 [US4] Read tracked files with `git ls-files -z` and fail on input errors in `tests/guardrails/test_analytics_package_structure.py`
- [X] T047 [US4] Scan active paths for all three old dotted and slash paths, except exact preservation mappings
- [X] T048 [US4] Exclude `specs/` and `CHANGELOG.md` from the active path scan in `tests/guardrails/test_analytics_package_structure.py`
- [X] T049 [US4] Report each tracked violating file in stable order in `tests/guardrails/test_analytics_package_structure.py`

### Direct Failure Proofs

- [X] T050 [P] [US4] Add a six-child proof that requires one checked directory, its path, and count six in `tests/guardrails/test_analytics_package_structure.py`
- [X] T051 [P] [US4] Add a missing-root proof that requires the absent path and inspection cause in `tests/guardrails/test_analytics_package_structure.py`
- [X] T052 [P] [US4] Add an old-path proof that requires the mocked tracked filename in `tests/guardrails/test_analytics_package_structure.py`
- [X] T053 [US4] Run `python -m pytest tests/guardrails/test_analytics_package_structure.py -q -s` and inspect all success and failure messages

**Checkpoint**: User Story 4 reports two repository directories and proves each required failure.

---

## Phase 7: Integration and Release Record

**Purpose**: Prove that all stories work together and record the user-visible path change.

- [X] T054 Add one `Changed` bullet for issue #3992 under one heading in `changelog.d/issue-3992-site-analytics-package.md`
- [X] T055 Run the seven focused test files together to detect shared state across `tests/unit/`, `tests/unit/export/`, and `tests/guardrails/`
- [X] T056 Search active paths for removed analytics paths and test the historical catalog mapping in `tests/guardrails/test_performance_hook_catalog.py`
- [X] T057 Run `git diff --exit-code -- CHANGELOG.md` and require no change
- [X] T058 Run `git diff --exit-code -- specs ':(exclude)specs/numbered/0/0/1/1/1/4/3/2/3992-site-analytics-package'` and require no change

---

## Phase 8: Focused Quality Gates

**Purpose**: Validate all directly changed Python and Markdown paths.

- [X] T059 Run `python -m py_compile` for `MistHelper.py`, both package initializers, three moved modules, `site_export_utils.py`, and `scripts/replace_zone.py`
- [X] T060 Run Ruff on every changed Python path with `python -m ruff check` and require `All checks passed`
- [X] T061 Run Black on every changed Python path with `python -m black --check --diff` and require no formatting change
- [X] T062 Run mypy with the exact `MYPY_PATHS` from `.github/workflows/ci.yml` and `--config-file pyproject.toml`
- [X] T063 Run Radon JSON output on each changed production module through `complexity-gate --max 10`
- [X] T064 Run `bandit -c pyproject.toml -r` on the changed production paths and require no finding
- [X] T065 Run pydocstyle and Interrogate on the changed production paths and require their configured thresholds
- [X] T066 Run STE lint on changed Markdown and require a score of 80 or more

---

## Phase 9: Source-Wide Quality Gates

**Purpose**: Detect integration failures outside the focused path set.

- [X] T067 Run `python -m ruff check .`
- [X] T068 Run `python -m black --check --diff .`
- [X] T069 Run `python MistHelper.py --test` and accept only documented missing-credential skips
- [ ] T070 Run `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`
- [X] T071 Run source-wide Radon output and `complexity-gate --max 10` with the paths from the plan
- [X] T072 Run `bandit-exclude-check` with both required Zen City sample paths
- [X] T073 Run `bandit -c pyproject.toml -r .`
- [ ] T074 Run `pip-audit -r requirements.txt`. Blocked because temporary environment `ensurepip` exits with `SIGABRT`.
- [X] T075 Run `pylint src/ --fail-under=9.5`
- [X] T076 Run `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70`
- [X] T077 Run `pydocstyle src/ wsgi.py web_portal`
- [X] T078 Run `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90 -v`
- [X] T101 Remove only the resolved analytics entry from `tests/guardrails/nested_package_baseline.json` and update the expected measurement
- [X] T102 Run `python -m pytest tests/guardrails/test_nested_package_structure.py -q -s` and require success

---

## Phase 10: Commit, Generated Documentation, and Test Quality

**Purpose**: Create the implementation commit before the changed-test quality comparison.

- [ ] T079 Inspect `git diff --name-status 0b04cda81c8ef75096f3bedae0885038c775d665...HEAD` and require only the approved implementation file set
- [ ] T080 Stage each approved source, test, script, documentation, and changelog path explicitly with `git add <path>` and do not use `git add .` or `git add -A`
- [ ] T081 Review `git diff --cached --name-status` and `git diff --cached` before the commit
- [ ] T082 Commit with subject `refactor(analytics): group site analytics modules`, body `Closes #3992`, and trailer `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`
- [ ] T083 Run `python scripts/generate_menu_wiki.py` after the commit and require a clean managed-file result
- [ ] T084 Run `python -m scripts.menu_api_map` after the commit and require a clean managed-file result
- [ ] T085 Run `git diff --exit-code HEAD -- documentation/menu-api/safe.md documentation/menu-api/destructive.md documentation/wiki/Menu-API-Endpoints-Safe.md documentation/wiki/Menu-API-Endpoints-Destructive.md documentation/menu_reference.md documentation/wiki/Menu-Reference.md`
- [ ] T086 Fetch `origin/main` with `git fetch --no-tags origin '+refs/heads/main:refs/remotes/origin/main'`
- [ ] T087 Verify the test-quality base with `git rev-parse --verify 'origin/main^{commit}'`
- [ ] T088 Run `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides`
- [ ] T089 Run `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
- [ ] T090 Require `gate: 0 new findings vs baseline` from the changed-test quality gate

---

## Phase 11: Final Verification

**Purpose**: Confirm preservation, generated output stability, and a clean worktree.

- [X] T091 Run `python -m pytest tests/guardrails/test_src_public_symbol_preservation.py tests/guardrails/test_analytics_package_structure.py -q -s`
- [X] T092 Require 122 preserved symbols and exactly two checked analytics package directories from the final guard run
- [X] T093 Repeat the active old-path scan and permit only exact preservation mappings
- [X] T094 Run `git diff --exit-code -- CHANGELOG.md` and require no change
- [X] T095 Run the scoped specification diff and require no change outside `specs/numbered/0/0/1/1/1/4/3/2/3992-site-analytics-package/`
- [ ] T096 Run `git status --short` and require no staged, unstaged, or untracked implementation file
- [ ] T097 Run `git log -1 --format='%s%n%b'` and verify the Conventional Commit subject, `Closes #3992`, and Copilot trailer

---

## Phase 12: Pull Request Handoff

**Purpose**: Publish the validated change without merging it.

- [ ] T098 Use `.github/PULL_REQUEST_TEMPLATE.md` to create or update the issue #3992 pull request
- [ ] T099 Include `Closes #3992`, the changelog fragment, and exact local gate results in the pull request
- [ ] T100 Confirm approval, current base, and required checks plus CodeQL on the current head; do not merge

---

## Dependencies

- Phase 1 has no dependency.
- Phase 2 depends on Phase 1.
- User Story 1 depends on Phase 2.
- User Story 2 depends on Phase 2.
- User Story 3 depends on Phase 2.
- User Story 4 depends on User Stories 1 through 3.
- Phase 7 depends on all four user stories.
- Phases 8 and 9 depend on Phase 7.
- Phase 10 depends on Phases 8 and 9.
- Phase 11 depends on Phase 10.

### User Story Completion Order

```text
Setup -> Foundational -> US1
                      -> US2
                      -> US3
US1 + US2 + US3 -> US4 -> Integration -> Quality Gates -> Commit -> Final Verification
```

## Parallel Execution Examples

### User Story 2

Run T020 through T023 in parallel after T013 through T019 complete. Each command reads a different focused test file.

### User Story 3

Run T028 through T035 in parallel. Each task changes a separate test or documentation file.

### User Story 4

Implement T050 through T052 in parallel only if each proof uses an independent test function and fixture state.

### Quality Gates

Run independent focused gates in parallel only after all implementation edits are complete. Run source-wide gates after focused gates pass.

## Implementation Strategy

### MVP

Complete Phases 1 through 4. This scope moves the modules and preserves symbols, root exports, and focused behavior.

### Incremental Delivery

1. Establish the authority inventory and canonical package.
2. Preserve symbols and behavior.
3. Update all active paths and maintained documentation.
4. Add scoped drift guards and direct failure proofs.
5. Run focused gates, then source-wide gates.
6. Commit once, run the test-quality procedure, and verify a clean worktree.

## Format Validation

Each executable task starts with a checkbox and a sequential task ID. Parallel tasks use `[P]`.

Each user story task uses its `[US1]`, `[US2]`, `[US3]`, or `[US4]` label. Each implementation task names an exact path.

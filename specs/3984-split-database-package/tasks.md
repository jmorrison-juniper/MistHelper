# Tasks: Split Database Package

**Input**: Design documents from `specs/3984-split-database-package/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`quickstart.md`, and `contracts/canonical-imports.md`

**Tests**: The specification requires focused tests, structural guards, symbol
checks, and all quality gates in `quickstart.md`.

**Scope**: Move six modules only. Update canonical imports only. Do not change
database behavior.

## Phase 1: Coordination and Baseline

**Purpose**: Obtain the fixed baseline and record evidence before any source move.

- [ ] T001 Confirm that PR #3980 released the serial slot, obtain the exact `main` SHA from the #3959 coordinator, set `$BASE_SHA`, and record both values in `specs/3984-split-database-package/tasks.md`. Do not fetch or infer the SHA
- [ ] T002 [P] Run `symbol-diff --base $BASE_SHA src/foundation/persistence/db/arango_writer.py` before the move and save the result under `test-artifacts/3984/symbol-diff-arango-writer.txt`
- [ ] T003 [P] Run `symbol-diff --base $BASE_SHA src/foundation/persistence/db/redis_writer.py` before the move and save the result under `test-artifacts/3984/symbol-diff-redis-writer.txt`
- [ ] T004 [P] Run `symbol-diff --base $BASE_SHA src/foundation/persistence/db/router.py` before the move and save the result under `test-artifacts/3984/symbol-diff-router.txt`
- [ ] T005 [P] Run `symbol-diff --base $BASE_SHA src/foundation/persistence/db/retention.py` before the move and save the result under `test-artifacts/3984/symbol-diff-retention.txt`
- [ ] T006 [P] Run `symbol-diff --base $BASE_SHA src/foundation/persistence/db/database_schema_utils.py` before the move and save the result under `test-artifacts/3984/symbol-diff-database-schema-utils.txt`
- [ ] T007 [P] Run `symbol-diff --base $BASE_SHA src/foundation/persistence/db/host_resolver.py` before the move and save the result under `test-artifacts/3984/symbol-diff-host-resolver.txt`
- [ ] T008 Run the focused pytest command from `specs/3984-split-database-package/quickstart.md` before edits and save the result under `test-artifacts/3984/focused-tests-before.txt`

**Checkpoint**: The serial slot is free, `$BASE_SHA` is fixed, and the baseline evidence exists.

---

## Phase 2: User Story 1 - Preserve Database Behavior (Priority: P1) MVP

**Goal**: Move the six modules without a database behavior or public symbol change.

**Independent Test**: Run the focused database tests and compare their result with T008.

### Implementation for User Story 1

- [ ] T009 [P] [US1] Create documentation-only package markers without re-exports in `src/foundation/persistence/db/backends/__init__.py`, `src/foundation/persistence/db/coordination/__init__.py`, and `src/foundation/persistence/db/support/__init__.py`
- [ ] T010 [P] [US1] Move `src/foundation/persistence/db/arango_writer.py` to `src/foundation/persistence/db/backends/arango_writer.py` and move `src/foundation/persistence/db/redis_writer.py` to `src/foundation/persistence/db/backends/redis_writer.py` without logic edits
- [ ] T011 [P] [US1] Move `src/foundation/persistence/db/router.py` to `src/foundation/persistence/db/coordination/router.py` and move `src/foundation/persistence/db/retention.py` to `src/foundation/persistence/db/coordination/retention.py` without logic edits
- [ ] T012 [P] [US1] Move `src/foundation/persistence/db/database_schema_utils.py` to `src/foundation/persistence/db/support/database_schema_utils.py` and move `src/foundation/persistence/db/host_resolver.py` to `src/foundation/persistence/db/support/host_resolver.py` without logic edits
- [ ] T013 [US1] Update only internal canonical imports in `src/foundation/persistence/db/backends/arango_writer.py`, `src/foundation/persistence/db/backends/redis_writer.py`, and `src/foundation/persistence/db/coordination/router.py`
- [ ] T014 [US1] Replace the module import with a private direct resolver-symbol import in `src/foundation/persistence/db/__init__.py`, preserve root behavior, and export no moved module or symbol
- [ ] T015 [US1] Update only canonical database imports in `MistHelper.py`, `src/operations/exporting/export/data_exporter.py`, `src/foundation/runtime/config/source_dependency_resolver.py`, and `scripts/migrate_sqlite_to_polyglot.py`

**Checkpoint**: The six old files do not exist, and the new modules preserve their implementation.

---

## Phase 3: User Story 2 - Use Canonical Module Paths (Priority: P2)

**Goal**: Make each import, patch target, dependency string, and logger expectation use one canonical path.

**Independent Test**: Search `src`, `tests`, `scripts`, and `MistHelper.py` and find no old module path.

### Focused Test Import Updates for User Story 2

- [ ] T016 [P] [US2] Update Arango writer imports and patch targets in `tests/unit/test_arango_writer.py`, `tests/unit/_test_arango_writer_helpers.py`, `tests/unit/arango_indexes/test_retry_concurrency.py`, `tests/unit/arango_indexes/test_preservation.py`, and `tests/unit/arango_indexes/fakes.py`
- [ ] T017 [P] [US2] Update Redis writer imports and patch targets in `tests/unit/test_redis_writer.py`, `tests/unit/test_redis_json_writer.py`, and `tests/unit/test_unparseable_response_guards.py`
- [ ] T018 [P] [US2] Update router and retention imports and patch targets in `tests/unit/test_router.py`, `tests/unit/test_retention.py`, `tests/unit/db/test_retention_redis_scan.py`, and `tests/unit/container/session_database/harness.py`
- [ ] T019 [P] [US2] Update schema and host support imports and patch targets in `tests/unit/db/test_database_schema_utils.py`, `tests/unit/refactors/test_sqlite_database_writer.py`, `tests/unit/db_discovery/test_resolver.py`, `tests/unit/db_discovery/fakes.py`, and `tests/unit/upgrade_portal/test_store.py`
- [ ] T020 [P] [US2] Update canonical imports, patch targets, and dependency strings in `tests/unit/db_discovery/test_probe.py`, `tests/unit/db_discovery/test_config.py`, and `tests/unit/test_standalone.py`
- [ ] T021 [P] [US2] Update canonical imports, patch targets, and logger expectations in `tests/unit/test_webhook_ingestion.py` and `tests/unit/web_portal/test_portal_log_routing.py`
- [ ] T022 [P] [US2] Update canonical imports and patch targets in `tests/contract/test_arango_declared_indexes.py`, `tests/contract/upgrade_portal/test_health.py`, and `tests/integration/test_arango_declared_indexes_live.py`
- [ ] T023 [P] [US2] Update canonical router imports and patch targets in `tests/integration/test_compose_deploy.py` and `tests/test_upgrade_portal_audit.py`
- [ ] T024 [US2] Run the rejection search from `specs/3984-split-database-package/quickstart.md` across `src`, `tests`, `scripts`, and `MistHelper.py` and require zero stale references
- [ ] T025 [US2] Inspect `src/foundation/persistence/db/__init__.py`, `src/foundation/persistence/db/backends/__init__.py`, `src/foundation/persistence/db/coordination/__init__.py`, and `src/foundation/persistence/db/support/__init__.py` and require no moved-module re-export

**Checkpoint**: Each consumer uses only the canonical module path.

---

## Phase 4: User Story 3 - Meet the Package Limit (Priority: P3)

**Goal**: Keep the database root and each new subpackage within the five-child limit.

**Independent Test**: Run the structure guard and confirm the expected four-child and three-child layouts.

### Guard Updates for User Story 3

- [ ] T026 [P] [US3] Extend `tests/guardrails/test_src_domain_structure.py` to measure `src/foundation/persistence/db`, `src/foundation/persistence/db/backends`, `src/foundation/persistence/db/coordination`, and `src/foundation/persistence/db/support`
- [ ] T027 [P] [US3] Extend `tests/guardrails/test_src_public_symbol_preservation.py` with six exact old-to-new path pairs and `$BASE_SHA`, fail on unreadable input, and print six checked modules
- [ ] T028 [US3] Run `python -m pytest tests\guardrails\test_src_domain_structure.py` and require no package level above five direct children
- [ ] T029 [US3] Run `python -m pytest -s tests\guardrails\test_src_public_symbol_preservation.py` with `$BASE_SHA` and require no lost module-level symbol across all six moved modules
- [ ] T030 [US3] Run `Get-ChildItem src\foundation\persistence\db -Recurse -File` and confirm the exact layout defined in `specs/3984-split-database-package/plan.md`

**Checkpoint**: The database root has four direct children, and each new subpackage has three.

---

## Phase 5: Validation, Release Note, and Local Commit

**Purpose**: Run every requested gate, record the internal change, and create one local commit.

- [ ] T031 Run the full focused pytest command in `specs/3984-split-database-package/quickstart.md` and require all selected tests to pass
- [ ] T032 Build the changed Python path list from `git status --short`, then run `python -m py_compile <changed-python-paths>` for each moved module, changed consumer, and changed guard
- [ ] T033 Run `python -m ruff check .` from the repository root and require `All checks passed`
- [ ] T034 Run `python -m black --check .` from the repository root and require no file change
- [ ] T035 Run `python -m mypy src\ MistHelper.py wsgi.py scripts\mist_ideas_analyzer_pkg\__init__.py scripts\mist_ideas_distiller_v2_pkg\__init__.py --config-file pyproject.toml` and require success
- [ ] T036 Run `bandit -c pyproject.toml -r src\foundation\persistence\db -q` and require no finding
- [ ] T037 Run `radon cc src\foundation\persistence\db -j | complexity-gate --max 10` and require no block above complexity 10
- [ ] T038 Create `changelog.d/issue-3984-split-database-package.md` with one `###` heading and one `Changed` bullet that references issue #3984
- [ ] T039 Run `ste-linter --config .ste-linter.toml --min-score 80` for `specs/3984-split-database-package/plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/canonical-imports.md`, `tasks.md`, and `changelog.d/issue-3984-split-database-package.md`
- [ ] T040 Run `python -B -m pytest -p no:cacheprovider -s -q tests\guardrails\local_test_quality_loop\test_guidance.py::TestLiveGuides` and require the input preflight to pass
- [ ] T041 Run `test-quality-analyzer --gate --config .github\test-quality-config.toml --baseline .github\test-quality-baseline.json --changed-from $BASE_SHA --full-gate-path .github\workflows\ci.yml --full-gate-path requirements-dev.txt` and require `gate: 0 new findings vs baseline`
- [ ] T042 Repeat the stale-import search from T024 and require zero matches before staging `src/foundation/persistence/db`, the named consumers, focused tests, guards, `specs/3984-split-database-package/tasks.md`, and `changelog.d/issue-3984-split-database-package.md`
- [ ] T043 Stage only the explicit feature manifest from T042, then create one local commit with subject `refactor(database): split database package`, body line `Refs #3984`, body line `Refs #3824`, and trailer `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`

**Stop Condition**: Stop after T043. Do not fetch, rebase, push, create a pull request, add auto-merge, or merge.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Coordination and Baseline**: T001 blocks all other tasks.
- **User Story 1**: T009-T015 depend on T002-T008.
- **User Story 2**: T016-T025 depend on T009-T015.
- **User Story 3**: T026-T030 depend on T009-T025.
- **Validation and Commit**: T031-T043 depend on T026-T030.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after the fixed baseline exists.
- **User Story 2 (P2)**: Depends on the completed source moves from User Story 1.
- **User Story 3 (P3)**: Depends on the canonical layout and imports from User Stories 1 and 2.

### Parallel Opportunities

- T002-T007 can run in parallel after T001.
- T009-T012 can run in parallel after T008.
- T016-T023 can run in parallel after T015 because they edit separate test files.
- T026 and T027 can run in parallel after T025.

## Parallel Example: User Story 2

```text
Task T016: Update Arango writer test imports and patch targets.
Task T017: Update Redis writer test imports and patch targets.
Task T018: Update router and retention test imports and patch targets.
Task T019: Update schema and host support test imports and patch targets.
Task T020: Update database discovery test references.
Task T021: Update webhook and portal logger references.
Task T022: Update contract and live integration references.
Task T023: Update compose and audit references.
```

## Implementation Strategy

### MVP First

1. Complete T001-T008.
2. Complete User Story 1 in T009-T015.
3. Complete canonical test imports in T016-T023.
4. Run the focused tests in T031.

### Incremental Delivery

1. Fix the baseline and capture symbol evidence.
2. Move the six modules without logic edits.
3. Update all canonical imports and patch targets.
4. Add the structural and symbol guards.
5. Run every gate and create the local commit.

## Notes

- Do not add a compatibility shim, alias, adapter, fallback import, or package re-export.
- Do not change schemas, indexes, stored values, routing, retention, host resolution, or logging.
- Limit consumer edits to imports, patch targets, dependency strings, and logger expectations.
- Keep parent issue #3824 open.

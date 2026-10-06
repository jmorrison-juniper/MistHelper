---

description: "Implementation tasks for the database writers package"
---

# Tasks: Database Writers Package

**Input**: Design documents from `specs/3824-db-writers-package/`

**Prerequisites**: `plan.md` and `spec.md`

**Tests**: The specification requires behavior tests, a scoped guard, and controlled failure proofs.

**Organization**: Tasks follow the required dependency order. Each user story remains independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel with other marked tasks after its dependencies pass.
- **[Story]**: The label maps the task to a user story in `spec.md`.
- Tick a task only after verification. Add `(delivered: path)` to the completed task.

## Scope Controls

- Use the current worktree and branch. Do not create or rename a branch.
- Use `origin/main` commit `2a00e32745472f70764206b060dacc1c4dd13992` as the approved baseline.
- Use `git mv` for both writer moves.
- Keep each writer symbol and behavior unchanged.
- Do not add an alias, wrapper, re-export, forwarding module, shim, or fallback import.
- Keep `MistHelper.py` unchanged.
- Keep historical specifications for all other issues unchanged.
- Do not edit released history or the test-quality baseline.

## Phase 1: Setup and Ownership Checks

**Purpose**: Confirm the approved baseline, clean scope, and file ownership before any edit.

- [ ] T001 Confirm the current branch and baseline with `git branch --show-current`, `git fetch --no-tags origin "+refs/heads/main:refs/remotes/origin/main"`, `git rev-parse --verify "origin/main^{commit}"`, and `test "$(git rev-parse origin/main)" = "2a00e32745472f70764206b060dacc1c4dd13992"`.
- [ ] T002 Confirm no open pull request owns an active candidate path with `gh pr list --json number,headRefName,files` before editing `src/foundation/persistence/db/`, its consumers, tests, documentation, or guard.
- [ ] T003 Record the initial scope with `git status --short` and stop if an unrelated change overlaps an active candidate path.

**Checkpoint**: The branch, baseline, ownership, and worktree scope are safe for implementation.

---

## Phase 2: User Story 1 - Find Database Writers in One Package (Priority: P1)

**Goal**: Put both database writers in one bounded package without behavior changes.

**Independent Test**: Confirm `db` has four direct modules and one `writers` package. Confirm `writers` has two modules and metadata.

### Implementation for User Story 1

- [ ] T004 [US1] Create `src/foundation/persistence/db/writers/`, then run `git mv src/foundation/persistence/db/arango_writer.py src/foundation/persistence/db/writers/arango_writer.py` and `git mv src/foundation/persistence/db/redis_writer.py src/foundation/persistence/db/writers/redis_writer.py`.
- [ ] T005 [US1] Add only `"""Database writers for the MistHelper persistence layer."""` to `src/foundation/persistence/db/writers/__init__.py`.
- [ ] T006 [US1] Preserve the complete bodies and public symbols in `src/foundation/persistence/db/writers/arango_writer.py` and `src/foundation/persistence/db/writers/redis_writer.py`.
- [ ] T007 [US1] Update canonical writer imports in `src/foundation/persistence/db/router.py` without changing router behavior or module-level names.

**Checkpoint**: The bounded `writers` package exists, and the runtime router uses its canonical paths.

---

## Phase 3: User Story 2 - Use Only the New Writer Paths (Priority: P2)

**Goal**: Replace every active old import, patch target, source path, and maintained documentation path.

**Independent Test**: Search active repository content. Confirm zero old writer paths and all required new paths.

### Runtime and Source Updates for User Story 2

- [ ] T008 [US2] Update delayed writer imports in `scripts/migrate_sqlite_to_polyglot.py` to use `src.foundation.persistence.db.writers`.
- [ ] T009 [P] [US2] Update the Redis writer source comment in `src/foundation/support/refactors/endpoint_primary_key_strategies.py` to use `src/foundation/persistence/db/writers/redis_writer.py`.
- [ ] T010 [P] [US2] Update the ArangoDB writer source comment in `src/interfaces/portals/upgrade_portal/capture/store.py` to use `src/foundation/persistence/db/writers/arango_writer.py`.
- [ ] T011 [P] [US2] Update both Redis writer source comments in `src/interfaces/portals/upgrade_portal/compare/clients.py` to use `src/foundation/persistence/db/writers/redis_writer.py`.

### Test Import and Patch-Target Updates for User Story 2

- [ ] T012 [P] [US2] Update imports in `tests/contract/test_arango_declared_indexes.py` and imports plus patch targets in `tests/integration/test_arango_declared_indexes_live.py`.
- [ ] T013 [P] [US2] Update imports and patch targets in `tests/unit/_test_arango_writer_helpers.py`, `tests/unit/arango_indexes/fakes.py`, `tests/unit/arango_indexes/test_preservation.py`, and `tests/unit/arango_indexes/test_retry_concurrency.py`.
- [ ] T014 [P] [US2] Update imports and patch targets in `tests/unit/test_arango_writer.py`, `tests/unit/test_redis_json_writer.py`, `tests/unit/test_redis_writer.py`, `tests/unit/test_unparseable_response_guards.py`, and `tests/unit/test_webhook_ingestion.py`.
- [ ] T015 [P] [US2] Update imports and patch targets in `tests/unit/upgrade_portal/test_compare_clients.py`, `tests/unit/upgrade_portal/test_guardrails.py`, and `tests/unit/web_portal/test_portal_log_routing.py`.
- [ ] T016 [P] [US2] Update writer imports and patch targets in `tests/unit/db_discovery/test_config.py` and `tests/unit/db_discovery/test_probe.py`.
- [ ] T017 [US2] Update `tests/unit/db_discovery/conftest.py` as the fifth additional path that imports a moved writer. Use the canonical `writers` package path.

### Active Documentation Updates for User Story 2

- [ ] T018 [P] [US2] Replace both old writer file paths in `documentation/diagrams/core/data-persistence-routing.md` with their new `writers` paths.
- [ ] T019 [P] [US2] Replace the old ArangoDB writer file path in `documentation/upgrade_capture_portal.md` with its new `writers` path.

**Checkpoint**: Active source, scripts, tests, patch targets, comments, and documentation use only canonical writer paths.

---

## Phase 4: User Story 3 - Detect New Persistence Package Violations (Priority: P3)

**Goal**: Add one scoped guard for package levels under `src/foundation/persistence`.

**Independent Test**: Run the guard normally, with six children, and with an unreadable root.

### Failure Proofs for User Story 3

- [ ] T020 [US3] Add failing tests in `tests/guardrails/test_persistence_package_structure.py` for a sixth child, an unreadable root, and an active old path.
- [ ] T021 [US3] Make the sixth-child proof require one checked directory, the violating relative path, and a measured count of six in `tests/guardrails/test_persistence_package_structure.py`.
- [ ] T022 [US3] Make the missing-root proof require the unreadable root path and a clear cause in `tests/guardrails/test_persistence_package_structure.py`.

### Guard Implementation for User Story 3

- [ ] T023 [US3] Implement a named inspector class in `tests/guardrails/test_persistence_package_structure.py` that accepts a persistence root and fails when it cannot inspect that root.
- [ ] T024 [US3] Recursively inspect package directories under `src/foundation/persistence` in `tests/guardrails/test_persistence_package_structure.py`.
- [ ] T025 [US3] Exclude `__init__.py`, `__pycache__`, and generated cache metadata from direct structural child counts in `tests/guardrails/test_persistence_package_structure.py`.
- [ ] T026 [US3] Enforce five direct structural children and report each checked count, violating path, and measured count in `tests/guardrails/test_persistence_package_structure.py`.
- [ ] T027 [US3] Assert counts of two, one, five, and two for `src/foundation/persistence`, `cache`, `db`, and `db/writers` in `tests/guardrails/test_persistence_package_structure.py`.
- [ ] T028 [US3] Add a tracked-text active-path scan to `tests/guardrails/test_persistence_package_structure.py` for `src/`, `tests/`, `scripts/`, maintained documentation, and `README.md`.
- [ ] T029 [US3] Exclude `specs/` only from the active-path scan in `tests/guardrails/test_persistence_package_structure.py`. Fail if Git cannot list tracked files.

**Checkpoint**: The scoped guard passes on the repository and proves each required failure mode.

---

## Phase 5: Process Record and Required Gates

**Purpose**: Add the release note, run every required gate, and preserve the bounded scope.

### Process Record

- [ ] T030 Add `changelog.d/issue-3824-db-writers-package.md` with heading `### Changed` and bullet `- Changed the ArangoDB and Redis writer paths for #3824.`

### Baseline and Active-Path Gates

- [ ] T031 Run `git grep -n -E 'src\.foundation\.persistence\.db\.(arango_writer|redis_writer)|src/foundation/persistence/db/(arango_writer|redis_writer)\.py' -- src tests scripts documentation README.md` and require no active match.
- [ ] T032 Run `python -c "from src.foundation.persistence.db.writers.arango_writer import ArangoDBWriter; from src.foundation.persistence.db.writers.redis_writer import RedisJSONWriter, RedisTimeSeriesWriter; print('Checked 3 canonical writer imports')"` and require the exact success count.
- [ ] T033 Run `python -m pytest -q tests/guardrails/test_persistence_package_structure.py` and require the normal guard plus controlled failure proofs to pass.

### Focused Behavior Gates

- [ ] T034 Run `python -m pytest -q tests/contract/test_arango_declared_indexes.py tests/unit/db_discovery` and require all selected tests to pass.
- [ ] T035 Run `python -m pytest -q tests/unit/test_arango_writer.py tests/unit/_test_arango_writer_helpers.py tests/unit/arango_indexes` and require all selected tests to pass.
- [ ] T036 Run `python -m pytest -q tests/unit/test_redis_writer.py tests/unit/test_redis_json_writer.py` and require all selected tests to pass.
- [ ] T037 Run `python -m pytest -q tests/unit/test_webhook_ingestion.py tests/unit/test_unparseable_response_guards.py` and require all selected tests to pass.
- [ ] T038 Run `python -m pytest -q tests/unit/web_portal/test_portal_log_routing.py tests/unit/upgrade_portal/test_compare_clients.py tests/unit/upgrade_portal/test_guardrails.py` and require all selected tests to pass.
- [ ] T039 Run `python -m pytest -q tests/integration/test_arango_declared_indexes_live.py`. Permit only its documented service skip.

### Static Quality Gates

- [ ] T040 Run `python -m ruff check .` and require `All checks passed`.
- [ ] T041 Run `python -m black --check .` and require no file change.
- [ ] T042 Run `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` and require success.
- [ ] T043 Run `bandit -c pyproject.toml -r src/foundation/persistence/db src/interfaces/portals/upgrade_portal scripts/migrate_sqlite_to_polyglot.py -q` and require no finding.
- [ ] T044 Run `radon cc src/foundation/persistence/db src/interfaces/portals/upgrade_portal/capture/store.py src/interfaces/portals/upgrade_portal/compare/clients.py scripts/migrate_sqlite_to_polyglot.py tests/guardrails/test_persistence_package_structure.py -j | complexity-gate --max 10` and require no block.
- [ ] T045 Run `symbol-diff --base origin/main src/foundation/persistence/db/router.py` and require no lost module-level name.
- [ ] T046 Run `symbol-diff --base origin/main src/foundation/persistence/db/writers/arango_writer.py` and require the complete old ArangoDB writer symbol set.
- [ ] T047 Run `symbol-diff --base origin/main src/foundation/persistence/db/writers/redis_writer.py` and require the complete old Redis writer symbol set.
- [ ] T048 Run `ste-linter --config .ste-linter.toml --min-score 80 documentation/diagrams/core/data-persistence-routing.md documentation/upgrade_capture_portal.md specs/3824-db-writers-package/spec.md specs/3824-db-writers-package/plan.md specs/3824-db-writers-package/tasks.md changelog.d/issue-3824-db-writers-package.md` and require each score to be at least 80.

### Scope Review, Explicit Staging, and Local Commit

- [ ] T049 Run `git status --short`, `git diff --check`, and `git diff --name-status origin/main...HEAD`. Confirm `MistHelper.py` and all historical specifications remain unchanged.
- [ ] T050 Stage only the explicit manifest with the command below. The `git mv` operations already stage both moves. Do not use `git add .` or `git add -A`.

```bash
git add \
  src/foundation/persistence/db/writers/__init__.py \
  src/foundation/persistence/db/router.py \
  scripts/migrate_sqlite_to_polyglot.py \
  src/foundation/support/refactors/endpoint_primary_key_strategies.py \
  src/interfaces/portals/upgrade_portal/capture/store.py \
  src/interfaces/portals/upgrade_portal/compare/clients.py \
  tests/contract/test_arango_declared_indexes.py \
  tests/integration/test_arango_declared_indexes_live.py \
  tests/unit/_test_arango_writer_helpers.py \
  tests/unit/arango_indexes/fakes.py \
  tests/unit/arango_indexes/test_preservation.py \
  tests/unit/arango_indexes/test_retry_concurrency.py \
  tests/unit/db_discovery/conftest.py \
  tests/unit/db_discovery/test_config.py \
  tests/unit/db_discovery/test_probe.py \
  tests/unit/test_arango_writer.py \
  tests/unit/test_redis_json_writer.py \
  tests/unit/test_redis_writer.py \
  tests/unit/test_unparseable_response_guards.py \
  tests/unit/test_webhook_ingestion.py \
  tests/unit/upgrade_portal/test_compare_clients.py \
  tests/unit/upgrade_portal/test_guardrails.py \
  tests/unit/web_portal/test_portal_log_routing.py \
  documentation/diagrams/core/data-persistence-routing.md \
  documentation/upgrade_capture_portal.md \
  tests/guardrails/test_persistence_package_structure.py \
  specs/3824-db-writers-package/spec.md \
  specs/3824-db-writers-package/plan.md \
  specs/3824-db-writers-package/tasks.md \
  changelog.d/issue-3824-db-writers-package.md
```
- [ ] T051 Verify the staged manifest with `git diff --cached --name-status`. Require only the two moves, `writers/__init__.py`, listed consumers, listed tests, two documentation files, the guard, issue #3824 specification files, and the changelog fragment.
- [ ] T052 Create one local commit with `git commit -m "refactor(db): move database writers into package" -m "Closes #3824" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"`.

### Required Post-Commit Test-Quality Gates

- [ ] T053 Run `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` after the local commit. Stop if it fails.
- [ ] T054 Run `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` only after T053 passes. Require zero new findings.
- [ ] T055 Run `git status --short` and confirm no implementation change remains unstaged, `MistHelper.py` remains unchanged, and historical specifications remain unchanged.

**Checkpoint**: The bounded change has one local commit, all required gates pass, and the working scope is clean.

---

## Dependencies and Execution Order

### Phase Dependencies

- Phase 1 has no dependency.
- User Story 1 depends on T001 through T003.
- User Story 2 depends on T004 through T007 because old paths must exist until both moves complete.
- User Story 3 depends on T017 because its active-path scan must include the complete import manifest.
- Phase 5 depends on T004 through T029.
- Explicit staging depends on every pre-commit gate.
- The local commit depends on explicit staged-manifest verification.
- The test-quality preflight depends on the local commit.
- The changed-file test-quality gate depends on the preflight.

### User Story Dependencies

- **User Story 1**: Establishes the canonical package and is the MVP.
- **User Story 2**: Depends on User Story 1 paths. It remains independently testable with an active-path search.
- **User Story 3**: Depends on the final active path set. It remains independently testable with temporary roots.

### Parallel Opportunities

- T009 through T011 can run in parallel after T008.
- T012 through T016 can run in parallel after T007.
- T018 and T019 can run in parallel after T007.
- T034 through T039 can run separately after T033. Run one heavy command at a time.
- T045 through T047 can run separately after static analysis passes.

## Parallel Examples

### User Story 1

```text
No parallel move is safe. Run T004 before T005 through T007.
```

### User Story 2

```text
Task: "Update source comments in the three listed source files."
Task: "Update independent test import and patch-target groups."
Task: "Update the two active documentation files."
```

### User Story 3

```text
No parallel edit is safe because all guard work uses tests/guardrails/test_persistence_package_structure.py.
```

## Implementation Strategy

### MVP First

1. Complete Phase 1.
2. Complete User Story 1.
3. Verify the bounded package shape and canonical router imports.
4. Continue because the final commit requires all three stories.

### Incremental Delivery

1. Move the writers and establish canonical paths.
2. Update every active consumer and maintained path.
3. Add the scoped guard and failure proofs.
4. Add the changelog fragment.
5. Run each required gate in the listed order.
6. Stage only the explicit manifest.
7. Create the local commit.
8. Run both post-commit test-quality gates.

## Completion Conditions

- `src/foundation/persistence/db` has four modules and the `writers` package.
- `src/foundation/persistence/db/writers` has two writer modules and a docstring-only `__init__.py`.
- Every active import, patch target, comment, script, test, and documentation path uses the new canonical path.
- `tests/unit/db_discovery/conftest.py` is included as the fifth additional import path.
- The scoped guard reports a nonzero checked directory count.
- The sixth-child and missing-root proofs pass.
- Each required gate passes or records its permitted service skip.
- The local commit exists before either test-quality gate runs.
- Historical specifications remain unchanged.
- `MistHelper.py` remains unchanged.

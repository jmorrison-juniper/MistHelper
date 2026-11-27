# Tasks: Redis device event identity

**Input**: Numeric record `specs/numbered/0/0/1/2/2/3/4/4/4724-redis-device-event-identity/`. The plan is `plan.md`, and the requirements are in `spec.md`.

**Preconditions**:

- P-1: Run the open pull request check before the first edit. Stop when an open pull request touches a changed file (decision D-12).
- P-2: Work in a git worktree on branch `fix/4724-redis-device-event-identity`. Branch from `main` only.

**Format**: `[P]` marks a task that can run in parallel with other `[P]` tasks. Each task names its requirements, its paths, its acceptance statement, and its verification command. Each changed line carries an inline comment. Each changed action logs `info` before it and `debug` after it (FR-009).

**Dependencies**: T004 depends on T001 and T002. T005 depends on T002. T006 depends on T001. T007 depends on T003. T008 depends on T004. T009 depends on T005. T013 depends on T004 to T007. The final tasks depend on all earlier tasks.

## Phase 1: Failing tests first

- **T001** [P] Add two Redis regression tests.
  - Requirements: FR-005, FR-006, SC-001, SC-004.
  - Paths: `tests/unit/config/standalone/foundation/persistence/redis/test_redis_json_writer.py`.
  - Acceptance: The equal-timestamp test keeps two documents. The rejection test reports one failed record. Both fail before T006.
  - Verification: `python -m pytest tests/unit/config/standalone/foundation/persistence/redis/test_redis_json_writer.py`.
  - Status: open.

- **T002** [P] Add three router tests for the `record_id` stamp.
  - Requirements: FR-001, FR-002, FR-003, SC-002, SC-003.
  - Paths: `tests/unit/config/standalone/foundation/persistence/database/test_router.py`.
  - Acceptance: Both backends receive the same `record_id`. Identical rows share one digest. Two organizations get two digests. The caller list stays unchanged.
  - Verification: `python -m pytest tests/unit/config/standalone/foundation/persistence/database/test_router.py`.
  - Status: open.

- **T003** [P] Add one graph test for device event vertices and edges.
  - Requirements: FR-007, User Story 3.
  - Paths: `tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_writer.py`.
  - Acceptance: A device event with `record_id` gives one vertex keyed by `record_id`. It also gives one edge to its site.
  - Verification: `python -m pytest tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_writer.py`.
  - Status: open.

## Phase 2: Implementation

- **T004** Change the device event strategy.
  - Requirements: FR-004.
  - Paths: `src/foundation/support/refactors/endpoint_primary_key_strategies.py` lines 265 to 271.
  - Acceptance: The primary key is `["record_id", "org_id", "timestamp"]`. The indexes use `mac` and drop `device_id`.
  - Verification: `python -m pytest tests/unit/config/foundation/persistence/storage/arango_indexes/test_declared_indexes.py`.
  - Status: open.

- **T005** Stamp device event rows in the router.
  - Requirements: FR-001, FR-002, FR-003.
  - Paths: `src/foundation/persistence/db/router.py`, with the class attribute `DEVICE_EVENT_API` and a static method beside `_write_dual`.
  - Acceptance: Each copy adds `record_id` from `_hash_payload`. The caller rows stay unchanged. No module-level name is added.
  - Verification: `python -m pytest tests/unit/config/standalone/foundation/persistence/database/test_router.py`.
  - Status: open.

- **T006** Reject rows with missing key fields in the Redis writer.
  - Requirements: FR-005, FR-006.
  - Paths: `src/foundation/persistence/db/writers/redis_writer.py` in `write`, `_pipeline_write_batch`, `_tally_json_results`, and `_build_key`.
  - Acceptance: No sentinel value appears in a key. A rejected row adds one to `records_failed`. The rejection log names the field only.
  - Verification: `python -m pytest tests/unit/config/standalone/foundation/persistence/redis/test_redis_json_writer.py`.
  - Status: open.

- **T007** Retarget the ArangoDB graph map for device events.
  - Requirements: FR-007.
  - Paths: `src/foundation/persistence/db/writers/arango_writer.py` lines 1487 to 1507.
  - Acceptance: `key_field` and both `from_field` values use `record_id`. The `mac` lookup and the `site_id` target stay unchanged.
  - Verification: `python -m pytest tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_writer.py`.
  - Status: open.

## Phase 3: Existing tests and documentation

- **T008** Update the preservation test record.
  - Requirements: FR-004, SC-003.
  - Paths: `tests/unit/config/foundation/persistence/storage/arango_indexes/test_preservation.py` line 29.
  - Acceptance: The shared record holds `record_id` with the value `record-1`. The `_key` check still passes for all three endpoints.
  - Verification: `python -m pytest tests/unit/config/foundation/persistence/storage/arango_indexes/test_preservation.py`.
  - Status: open.

- **T009** Update the contract test for stamped rows.
  - Requirements: FR-003.
  - Paths: `tests/contract/test_arango_declared_indexes.py` lines 151 to 154.
  - Acceptance: The Redis writer receives copies with `record_id`. The original fields match the input rows.
  - Verification: `python -m pytest tests/contract/test_arango_declared_indexes.py`.
  - Status: open.

- **T010** [P] Update the design guide.
  - Requirements: FR-010.
  - Paths: `documentation/diagrams/core/database-strategy.md` lines 42 to 50 and line 137.
  - Acceptance: The device event block and table row name `record_id`, `org_id`, and `timestamp`. No row names `device_id` as a key.
  - Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation/diagrams/core/database-strategy.md`.
  - Status: open.

- **T011** [P] Update the contributor guide example.
  - Requirements: FR-010.
  - Paths: `.github/copilot-instructions.md` line 205.
  - Acceptance: The `composite_pk` example names `record_id`, `org_id`, and `timestamp`. The row keeps Simplified Technical English.
  - Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 .github/copilot-instructions.md`.
  - Status: open.

- **T012** [P] Add the changelog fragment.
  - Requirements: FR-010.
  - Paths: `changelog.d/issue-4724-redis-device-event-identity.md`.
  - Acceptance: One `###` heading and one `Fixed` bullet name issue 4724. The bullet ends with the issue reference.
  - Verification: `python -m pytest tests/guardrails`.
  - Status: open.

- **T013** Confirm the structure guard.
  - Requirements: SC-005, decision D-8.
  - Paths: `tests/guardrails/test_persistence_package_structure.py` (unchanged).
  - Acceptance: The guard keeps `db` at five and `writers` at two. No new module exists in those folders.
  - Verification: `python -m pytest tests/guardrails/test_persistence_package_structure.py`.
  - Status: open.

## Phase 4: Release

- **T-LOCAL-GATES** Run each applicable gate in the local gates table.
  - Requirements: SC-006.
  - Paths: Every changed file listed in T004 to T012.
  - Acceptance: Each applicable gate prints its expected result. The diff holds no Redis delete, purge, or ArangoDB remove call (FR-008). Each gate records its command and its output.
  - Verification: The commands in `design/quickstart.md`, section "Local gates".
  - Status: open.

- **T-PR** Commit, push, and open the pull request.
  - Requirements: SC-006.
  - Paths: The changed files from T004 to T012.
  - Acceptance: The commit uses a Conventional Commits subject. The pull request body contains `Closes #4724`. The branch name is `fix/4724-redis-device-event-identity`. The body lists each direct caller of `searchOrgDeviceEvents` and its route to the router (research U-11).
  - Verification: The Lint row command `python -m ruff check .` prints `All checks passed` before the push.
  - Status: open.

- **T-REMOTE-CI** Watch the remote checks.
  - Requirements: SC-006.
  - Paths: The pull request from T-PR.
  - Acceptance: Each required check passes. The CodeQL check passes.
  - Verification: The Full tests row commands pass locally before the push. Read remote checks with `gh pr checks <number> --watch`.
  - Status: open.

- **T-MERGE** Enable auto-merge after the orchestrator authorizes the merge.
  - Requirements: SC-006.
  - Paths: The pull request from T-PR.
  - Acceptance: The `auto-merge` label is added only after each remote check shows green. Squash merge is the only merge method.
  - Verification: The Safe sweep row command `python MistHelper.py --test` passes before the authorization.
  - Status: open.

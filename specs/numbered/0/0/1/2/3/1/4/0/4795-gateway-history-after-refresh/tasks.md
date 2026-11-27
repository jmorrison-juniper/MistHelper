# Tasks: Gateway History After an Ordinary Refresh

**Input**: `plan.md`, `spec.md`, and the design documents in `design/`.

**Prerequisite**: The publication head must keep blob `98827fc73a3d241859f539a03451d5cccf4d2e48` for `live_routes.py`. If the blob changes, run T001 and T002 again.

**Tests**: Required. The red proof for the new tests is T008, on the parent commit. On the head, N8 fails until T004 adds the logs.

**Format**: `[ID] [P?] [Story] Description`. `[P]` means the task edits no file that another open task edits. `[US1]`, `[US2]`, and `[US3]` link to the user stories in `spec.md`.

**Status values**: `verified-present` means the candidate already has the item. `absent` means the candidate lacks the item. `open` means the work has not started.

## Test Catalog

The new tests live in `tests/unit/wan_performance/test_gateway_insights.py`. The existing end-to-end tests are E1 at `tests/e2e/web_portal/test_wan_performance_live.py` line 2325, and E2 at the same file, line 2392.

| ID | Test function | Requirements | Assertion |
| - | - | - | - |
| N1 | `test_live_history_reads_circuit_only_selection_once` | FR-001, FR-004, FR-007 | Circuit records of one gateway resolve that gateway. One history read. No snapshot publish. |
| N2 | `test_live_history_reads_peer_only_selection_once` | FR-001, FR-004 | Peer records of one gateway resolve that gateway. One history read. |
| N3 | `test_live_history_accepts_one_gateway_from_mixed_records` | FR-001 | Gateway, circuit, and peer records of one gateway produce one history read. |
| N4 | `test_live_history_refuses_two_gateways_without_reading` | FR-002, FR-007, FR-009 | Two gateways return no summaries, the gateway message, and zero history reads. |
| N5 | `test_live_history_refuses_foreign_organization_without_reading` | FR-003, FR-007 | A gateway of another organization returns the gateway message and zero history reads. |
| N6 | `test_live_history_refuses_empty_selection` | FR-002, FR-009 | No selected records return the gateway message. |
| N7 | `test_port_and_peer_history_keep_single_record_rule` (parametrized by kind) | FR-006 | Two records return the port-or-peer message. One record reads history once. |
| N8 | `test_live_history_logs_resolution_and_read` | FR-008 | Captured logs show info before and debug after each action. Each message carries counts only. |
| N9 | `test_live_history_reports_store_problems_with_exact_text` (parametrized by case) | FR-009 | A missing store and a storage error each return their exact unavailable message. |

## Phase 1: Verify the Candidate

### T001 [P] [US1] Confirm the repair at the candidate head

- **Requirements**: FR-001, FR-005
- **Files**: `src/interfaces/wan_performance/presentation/live_routes.py`
- **Acceptance**: At head `843be63`, `_select_identity` resolves one gateway from gateway, circuit, and peer records. It refuses other counts.
- **Verification**: `python -m py_compile src/interfaces/wan_performance/presentation/live_routes.py`
- **Status**: verified-present (R19 to R23)

### T002 [P] [US1] [US2] Confirm the two route regressions at the candidate head

- **Requirements**: FR-002, FR-003, FR-005
- **Files**: `tests/e2e/web_portal/test_wan_performance_live.py`
- **Acceptance**: E1 covers the scoped-then-ordinary sequence. E2 covers ambiguous and foreign identity, with the exact text at line 2408.
- **Verification**: `python -m pytest tests/e2e/web_portal/test_wan_performance_live.py`
- **Status**: verified-present (R31 to R33)

## Phase 2: Tests First

### T005 [US1] Add the resolution tests N1, N2, and N3

- **Requirements**: FR-001, FR-004, FR-007
- **Files**: `tests/unit/wan_performance/test_gateway_insights.py`
- **Acceptance**: N1 to N3 pass on the head. Each test builds its selected records with `dataclasses.replace`, as E2 does.
- **Verification**: `python -m pytest tests/unit/wan_performance/test_gateway_insights.py`
- **Status**: absent

### T006 [US2] Add the refusal tests N4, N5, N6, and N9

- **Requirements**: FR-002, FR-003, FR-007, FR-009
- **Files**: `tests/unit/wan_performance/test_gateway_insights.py`
- **Acceptance**: Each refusal returns its exact message and reads no history. N9 covers a missing store and a storage error.
- **Verification**: `python -m pytest tests/unit/wan_performance/test_gateway_insights.py`
- **Status**: absent

### T007 [US3] Add the port and peer regression test N7

- **Requirements**: FR-006
- **Files**: `tests/unit/wan_performance/test_gateway_insights.py`
- **Acceptance**: N7 runs for the port kind and the peer kind. Two records return the port-or-peer message. One record reads history once.
- **Verification**: `python -m pytest tests/unit/wan_performance/test_gateway_insights.py`
- **Status**: absent

## Phase 3: Repair the Touched Code

### T004 [US1] [US2] Add inline comments and action logs to the touched methods

- **Requirements**: FR-008
- **Decision**: D-7
- **Files**: `src/interfaces/wan_performance/presentation/live_routes.py`, `tests/unit/wan_performance/test_gateway_insights.py` (adds N8)
- **Acceptance**: Each executable line in `read` and `_select_identity` has an inline comment. Each action logs info before and debug after, with counts only.
- **Verification**: `python -m pytest tests/unit/wan_performance/test_gateway_insights.py`
- **Status**: absent (R26, R27)

### T003 [US1] [US2] Extract the history read and keep the message text

- **Requirements**: FR-008, FR-009
- **Decision**: D-8
- **Files**: `src/interfaces/wan_performance/presentation/live_routes.py`
- **Acceptance**: `LiveHistory.read` holds 25 lines or fewer. A static method `_read_history` holds the history read, the summary build, and the storage-error handling.
- **Caution**: Keep the four message strings byte-identical. Tests N4, N6, N9, and E2 assert them.
- **Verification**: `python -m ruff check .`
- **Status**: absent (R20, R24, R25, R96, R97)

## Phase 4: Proof, Documentation, and Release Note

### T008 Prove that the new tests fail on the parent commit

- **Requirements**: FR-001, FR-002, FR-003
- **Files**: `tests/unit/wan_performance/test_gateway_insights.py` (copied into a parent worktree), `src/interfaces/wan_performance/presentation/live_routes.py` (parent commit `07b7751`)
- **Acceptance**: N1, N2, N4, N5, N6, and N8 fail on `07b7751`. N3, N7, and N9 pass there. Record both counts in the publication pull request.
- **Verification**: `python -m pytest tests/unit/wan_performance/test_gateway_insights.py` (run in the parent worktree)
- **Status**: open

### T009 [P] Confirm that the documented rule matches the final code

- **Requirements**: FR-010
- **Files**: `documentation/wan-performance.md` (lines 391 and 392)
- **Acceptance**: Both lines state the resolution rule and the refusal rule. Edit a line only when the final behavior differs.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 documentation/wan-performance.md`
- **Status**: verified-present (R45, R46)

### T010 [P] Keep one release note fragment for the publication

- **Requirements**: FR-010
- **Files**: `changelog.d/pr-4208.md` (line 19)
- **Acceptance**: The Fixed bullet names issue 4795. Create no new fragment, because pull request #4208 already has one (D-9).
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: verified-present (R47, R81)

## Final Delivery

### T-LOCAL-GATES Run every applicable local gate

- **Requirements**: FR-001 to FR-010
- **Files**: `src/interfaces/wan_performance/presentation/live_routes.py`, `tests/unit/wan_performance/test_gateway_insights.py`, `documentation/wan-performance.md`, `changelog.d/pr-4208.md`
- **Acceptance**: Run each gate in quickstart.md Scenario 5 once. Stop at the first failure. Repair it and record each count.
- **Verification**: `python -m pytest tests/unit/wan_performance/test_gateway_insights.py`
- **Status**: open

### T-PR Update pull request #4208 for publication

- **Requirements**: FR-005, FR-010
- **Decision**: D-2 (HUMAN-DECISION-REQUIRED), D-3
- **Files**: Object `jmorrison-juniper/MistHelper` pull request 4208 body. No repository file changes.
- **Acceptance**: After the owner authorizes publication, the body contains `Closes #4795` and keeps `Refs #4200`. It does not close #4200.
- **Verification**: `python -m pytest tests/e2e/web_portal/test_wan_performance_live.py`
- **Status**: open

### T-REMOTE-CI Watch the required checks

- **Requirements**: FR-001 to FR-010
- **Files**: Object `jmorrison-juniper/MistHelper` pull request 4208 checks. No repository file changes.
- **Acceptance**: Every required check reports success on the publication head. Each skipped check counts as unknown until it reports success.
- **Verification**: `python -m pytest tests/unit/wan_performance/test_gateway_insights.py`
- **Status**: open

### T-MERGE Merge and verify on main

- **Requirements**: FR-005, FR-009
- **Files**: Object `jmorrison-juniper/MistHelper` branch `main`. No repository file changes.
- **Acceptance**: After the orchestrator authorizes the merge, squash-merge. Wait for `container-build.yml` on the merged revision.
- **Acceptance**: Verify that the image revision label equals the merged commit SHA. Deploy, check health, and run E1 and E2 on `main`.
- **Verification**: `python -m pytest tests/e2e/web_portal/test_wan_performance_live.py`
- **Status**: open

## Dependencies and Execution Order

- T001, T002, T009, and T010 may run in parallel.
- T005, T006, and T007 run first in the test phase. They edit one file, so they run in order.
- T004 runs after the tests. It adds N8 and the logs, so N8 fails before T004 finishes.
- T003 runs after T004. The tests guard the extraction.
- T008 runs after T003 and T004, on the parent commit.
- T-LOCAL-GATES runs after T003 to T010.
- T-PR needs T-LOCAL-GATES and the owner decision (D-2).
- T-REMOTE-CI follows T-PR. T-MERGE follows T-REMOTE-CI and the orchestrator authorization.

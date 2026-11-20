# Tasks: Deployed Inventory Report

**Input**: Numeric record at `specs/numbered/0/0/1/2/3/4/1/3/4858-deployed-inventory-report/`
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./design/research.md), [data-model.md](./design/data-model.md), [report contract](./design/contracts/report-contract.md), [quickstart.md](./design/quickstart.md)

**Organization**: Tasks follow user story priority. Tests precede implementation in each story.

## Format

- `[P]` means that the task can run in parallel with other tasks.
- `[US1]` maps to deployed inventory detail and summary.
- `[US2]` maps to deployed and stock separation.
- `[US3]` maps to partial failure and Missing behavior.

## Phase 1: Setup

- [X] T001 Verify the issue 4858 worktree and branch `fix/4858-deployed-inventory-report`. (delivered: worktree and branch)
- [X] T002 Bootstrap the worktree with Python 3.15.2 and UV, then review the existing subscription report package in `src/mist/intelligence/reports/subscription_expiry/`. (delivered: `.venv` and package review)
- [X] T003 [P] Review the MSP inventory pagination pattern in `src/operations/exporting/export/msp_inventory_exporter.py`. (delivered: SDK continuation pattern)

---

## Phase 2: Foundational

**Purpose**: Add shared deployed inventory contracts and test seams.

- [X] T004 [P] Add deployed inventory dataclass expectations in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_model.py`. (delivered: test_model.py)
- [X] T005 [P] Add inventory pagination and Virtual Chassis contract tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`. (delivered: test_client.py)
- [X] T006 [P] Add linked deployed inventory export tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_operation.py`. (delivered: test_operation.py)
- [X] T007 [P] Add primary-key tests for deployed inventory detail and summary in `tests/unit/export/test_pk_strategies.py`. (delivered: test_pk_strategies.py)
- [X] T008 Add deployed detail and summary dataclasses in `src/mist/intelligence/reports/subscription_expiry/model.py`. (delivered: model.py)
- [X] T009 Update inventory pagination in `src/mist/intelligence/reports/subscription_expiry/client.py`. (delivered: client.py)
- [X] T010 Add deployed inventory primary-key strategies in `src/foundation/support/refactors/endpoint_primary_key_strategies.py`. (delivered: endpoint_primary_key_strategies.py)

**Checkpoint**: Shared deployed inventory types, pagination, and primary keys are ready.

---

## Phase 3: User Story 1 - Deployed Inventory Detail and Summary (Priority: P1)

**Goal**: Export deployed devices and one organization/device-type total for each authorized organization.

**Independent Test**: Synthetic inventory yields deployed rows and summary counts while T-Mobile USA Retail has more deployed evidence than the stock-only report.

### Tests for User Story 1

- [X] T011 [P] [US1] Add deployed detail model tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_model.py`. (delivered: test_model.py)
- [X] T012 [P] [US1] Add deployed summary reconciliation tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_model.py`. (delivered: test_model.py)
- [X] T013 [P] [US1] Add deployed detail and summary CSV export tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_operation.py`. (delivered: test_operation.py)

### Implementation for User Story 1

- [X] T014 [US1] Implement deployed inventory row classification in `src/mist/intelligence/reports/subscription_expiry/model.py`. (delivered: model.py)
- [X] T015 [US1] Implement organization/device-type deployed summaries in `src/mist/intelligence/reports/subscription_expiry/model.py`. (delivered: model.py)
- [X] T016 [US1] Add deployed inventory rows and summaries to menu 308 orchestration in `src/mist/intelligence/reports/subscription_expiry/operation.py`. (delivered: operation.py)
- [X] T017 [US1] Export `CrossOrgDeployedInventory.csv` and `CrossOrgDeployedInventorySummary.csv` in `src/mist/intelligence/reports/subscription_expiry/operation.py`. (delivered: operation.py)

**Checkpoint**: User Story 1 works independently for one organization and for synthetic multiple organizations.

---

## Phase 4: User Story 2 - Separate Deployed and Stock Equipment (Priority: P1)

**Goal**: Keep assigned devices in deployed reports and unassigned devices in stock reports.

**Independent Test**: Synthetic assigned and unassigned devices appear in separate outputs without duplicate serial evidence.

### Tests for User Story 2

- [X] T018 [P] [US2] Add site-ID deployed classification tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_model.py`. (delivered: test_model.py)
- [X] T019 [P] [US2] Add no-site-ID stock separation tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_model.py`. (delivered: test_model.py)
- [X] T020 [P] [US2] Add duplicate and Virtual Chassis identity tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_model.py`. (delivered: test_model.py)

### Implementation for User Story 2

- [X] T021 [US2] Separate deployed and stock classification in `src/mist/intelligence/reports/subscription_expiry/model.py`. (delivered: model.py)
- [X] T022 [US2] Prevent deployed and stock double counting in `src/mist/intelligence/reports/subscription_expiry/operation.py`. (delivered: operation.py)
- [X] T023 [US2] Preserve a stable row identity for Virtual Chassis members in `src/mist/intelligence/reports/subscription_expiry/model.py`. (delivered: model.py)

**Checkpoint**: User Story 2 keeps assigned and unassigned equipment separate.

---

## Phase 5: User Story 3 - Missing and Partial Inventory Results (Priority: P2)

**Goal**: Keep denied, failed, and incomplete inventory reads visible without false success or false zero values.

**Independent Test**: Synthetic failed and successful organizations complete with organization status and Missing deployed counts.

### Tests for User Story 3

- [X] T024 [P] [US3] Add HTTP inventory failure tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`. (delivered: test_client.py)
- [X] T025 [P] [US3] Add partial organization failure tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_operation.py`. (delivered: test_operation.py)
- [X] T026 [P] [US3] Add Missing deployed count tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_model.py`. (delivered: test_model.py)

### Implementation for User Story 3

- [X] T027 [US3] Preserve inventory failure status in `src/mist/intelligence/reports/subscription_expiry/client.py`. (delivered: client.py)
- [X] T028 [US3] Export Missing deployed summary values in `src/mist/intelligence/reports/subscription_expiry/model.py`. (delivered: model.py)
- [X] T029 [US3] Continue menu 308 with other organizations after one inventory failure in `src/mist/intelligence/reports/subscription_expiry/operation.py`. (delivered: operation.py)

**Checkpoint**: User Story 3 keeps failed inventory reads visible and continues with partial evidence.

---

## Phase 6: Polish and Cross-Cutting Concerns

- [X] T030 [P] Update menu 308 documentation in `documentation/cross-org-subscription-stock.md`. (delivered: cross-org-subscription-stock.md)
- [X] T031 [P] Add the issue 4858 change fragment under `changelog.d/`. (delivered: issue-4858-deployed-inventory-report.md)
- [X] T032 [P] Add deployed inventory menu and SDK guard coverage in `tests/guardrails/test_endpoint_catalog.py`. (delivered: operation and primary-key tests)
- [X] T033 Run compile, Ruff, Black, mypy, targeted pytest, Radon, Bandit, and test-quality gates. (delivered: compile, Ruff, Black, mypy, Radon, Bandit, 115 focused tests, and test-quality preflight pass)
- [X] T034 Run menu reference generation and verify no menu documentation drift. (delivered: 16 menu maps unchanged)
- [ ] T035 Run an interactive MSP menu 308 report and compare T-Mobile USA Retail deployed inventory with the 2026-11-11 snapshot. (pending: interactive 2FA sign-in; existing snapshot shows 27,030 T-Mobile USA Retail devices)
- [X] T036 Open the pull request for issue 4858 after all required CI checks pass. (delivered: PR #4859)

---

## Dependencies

- Phase 2 blocks all user story work.
- User Story 1 provides deployed detail and summary contracts.
- User Story 2 uses the deployed detail contract and keeps stock separate.
- User Story 3 uses organization status and continues with partial results.
- Documentation and live validation follow implementation.

## Parallel Execution Examples

### User Story 1

```text
Run T011, T012, and T013 in parallel.
Implement T014 and T015 together, then T016 and T017.
```

### User Story 2

```text
Run T018, T019, and T020 in parallel.
Implement T021 and T023 together, then T022.
```

### User Story 3

```text
Run T024, T025, and T026 in parallel.
Implement T027, T028, and T029 after tests fail.
```

## Implementation Strategy

### MVP

1. Complete setup and foundational tasks.
2. Complete User Story 1.
3. Validate deployed detail and summary independently.
4. Release the MVP if User Story 1 passes.

### Incremental Delivery

1. Add User Story 2 for stock separation.
2. Add User Story 3 for Missing and partial failures.
3. Complete documentation and live validation.
4. Open one pull request for the complete fix.

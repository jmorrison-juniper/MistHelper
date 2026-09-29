# Tasks: Subscription Contract Expiry Report

**Input**: Design documents from `specs/3552-subscription-contract-expiry/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`quickstart.md`, `contracts/subscription-expiry-report.md`, and `wiring.md`

**Tests**: Unit tests are required by the feature specification and quickstart.

**Organization**: Tasks are grouped by user story so each story can be
implemented and tested as an independent increment where possible.

**Branch boundary**: This branch may edit only these paths:

- `src/reports/subscription_expiry/**`
- `tests/unit/reports/subscription_expiry/**`
- `changelog.d/issue-3552-subscription-contract-expiry.md`
- `specs/3552-subscription-contract-expiry/**`

**Deferred to the integration pull request**:

- `MistHelper.py` menu registration
- `src/utils/operation_registry.py` registration
- `README.md` operation count and menu table updates
- Generated menu reference updates
- Generated menu API map updates
- Primary key strategy edits

## Format: `[ID] [P?] [Story] Description`

- **[P]**: This task can run in parallel because it edits different files or
  does not depend on an incomplete task.
- **[Story]**: This task maps to a user story from `spec.md`.
- Tick a task only after you verify the delivered file.

---

## Phase 1: Setup

**Purpose**: Create the package and test directories without integration wiring.

- [ ] T001 Create the report package files `src/reports/subscription_expiry/__init__.py`, `src/reports/subscription_expiry/client.py`, `src/reports/subscription_expiry/model.py`, and `src/reports/subscription_expiry/operation.py`
- [ ] T002 Create the unit test files `tests/unit/reports/subscription_expiry/test_client.py`, `tests/unit/reports/subscription_expiry/test_model.py`, and `tests/unit/reports/subscription_expiry/test_operation.py`
- [ ] T003 Review `specs/3552-subscription-contract-expiry/wiring.md` and confirm the deferred integration boundary before implementation starts

---

## Phase 2: Foundational

**Purpose**: Build shared report seams that all user stories need.

**Critical**: Do not start user story implementation until this phase is
complete.

- [ ] T004 [P] Define report constants, missing value markers, band names, bucket names, and status values in `src/reports/subscription_expiry/model.py`
- [ ] T005 [P] Define `ReportContext`, `LicenseSummarySource`, `LicenseUsageSource`, and `JsiContractSource` dataclasses in `src/reports/subscription_expiry/model.py`
- [ ] T006 [P] Define `SubscriptionExpiryRow`, `ContractExpiryRow`, and `ConsoleSummary` dataclasses in `src/reports/subscription_expiry/model.py`
- [ ] T007 Implement date normalization for ISO strings, Unix timestamps, missing values, and invalid values in `src/reports/subscription_expiry/model.py`
- [ ] T008 Implement `SubscriptionExpiryClient` response-wrapper conversion without scoring or export logic in `src/reports/subscription_expiry/client.py`
- [ ] T009 Add client unit tests for plain-container conversion and JSI pagination in `tests/unit/reports/subscription_expiry/test_client.py`

**Checkpoint**: Source data can be normalized and API seams can be tested with
fake client data.

---

## Phase 3: User Story 1 - Score subscription expiry and entitlement risk (Priority: P1) - MVP

**Goal**: Create `SubscriptionExpiry.csv` rows with status, days remaining, and
risk band values.

**Independent Test**: Use fake license summary and usage data that covers
`Active`, `Expired`, `Exceeded`, and `Inactive`. Verify one row per subscription
type and all expected column values.

### Tests for User Story 1

- [ ] T010 [P] [US1] Add failing tests for subscription bands and days remaining in `tests/unit/reports/subscription_expiry/test_model.py`
- [ ] T011 [P] [US1] Add failing tests for `Active`, `Expired`, `Exceeded`, and `Inactive` status scoring in `tests/unit/reports/subscription_expiry/test_model.py`
- [ ] T012 [P] [US1] Add failing tests for empty subscription data, missing end dates, missing entitlement, missing usage, and duplicate subscription types in `tests/unit/reports/subscription_expiry/test_model.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement license usage aggregation by subscription type in `src/reports/subscription_expiry/model.py`
- [ ] T014 [US1] Implement subscription end date selection and days remaining calculation in `src/reports/subscription_expiry/model.py`
- [ ] T015 [US1] Implement subscription status and band scoring in `src/reports/subscription_expiry/model.py`
- [ ] T016 [US1] Implement subscription row ordering and one-row-per-type output in `src/reports/subscription_expiry/model.py`
- [ ] T017 [US1] Add subscription export orchestration for `SubscriptionExpiry.csv` in `src/reports/subscription_expiry/operation.py`
- [ ] T018 [US1] Run `python -m pytest tests\unit\reports\subscription_expiry\test_model.py -k subscription` and fix defects in `src/reports/subscription_expiry/model.py`

**Checkpoint**: User Story 1 produces independently testable subscription rows.

---

## Phase 4: User Story 2 - Score device contract expiry risk (Priority: P2)

**Goal**: Create `ContractExpiry.csv` rows with device identity, contract state,
end date, and expiry bucket values.

**Independent Test**: Use fake JSI contract data that covers supported,
unsupported, expired, near-expiry, and long-term contracts. Verify one row per
device and all expected column values.

### Tests for User Story 2

- [ ] T019 [P] [US2] Add failing tests for contract buckets in `tests/unit/reports/subscription_expiry/test_model.py`
- [ ] T020 [P] [US2] Add failing tests for `Supported` and `Unsupported` state scoring in `tests/unit/reports/subscription_expiry/test_model.py`
- [ ] T021 [P] [US2] Add failing tests for empty contract data, missing end dates, missing serial, missing model, and duplicate devices in `tests/unit/reports/subscription_expiry/test_model.py`

### Implementation for User Story 2

- [ ] T022 [US2] Implement contract end date selection from JSI source fields in `src/reports/subscription_expiry/model.py`
- [ ] T023 [US2] Implement contract status and contract state scoring in `src/reports/subscription_expiry/model.py`
- [ ] T024 [US2] Implement contract bucket scoring with three-month and twelve-month boundaries in `src/reports/subscription_expiry/model.py`
- [ ] T025 [US2] Implement contract row ordering and one-row-per-device output in `src/reports/subscription_expiry/model.py`
- [ ] T026 [US2] Add contract export orchestration for `ContractExpiry.csv` in `src/reports/subscription_expiry/operation.py`
- [ ] T027 [US2] Run `python -m pytest tests\unit\reports\subscription_expiry\test_model.py -k contract` and fix defects in `src/reports/subscription_expiry/model.py`

**Checkpoint**: User Story 2 produces independently testable contract rows.

---

## Phase 5: User Story 3 - Summarize expiry risk in the console (Priority: P3)

**Goal**: Print console summary counts for every subscription band and every
contract bucket.

**Independent Test**: Use fake scored rows with known counts in every band and
bucket. Verify that the summary counts match the row counts.

### Tests for User Story 3

- [ ] T028 [P] [US3] Add failing tests for summary count defaults and counted rows in `tests/unit/reports/subscription_expiry/test_model.py`
- [ ] T029 [P] [US3] Add failing tests for report run orchestration, export calls, and console output in `tests/unit/reports/subscription_expiry/test_operation.py`
- [ ] T030 [P] [US3] Add failing tests for the JSI `400` no-linked-account path in `tests/unit/reports/subscription_expiry/test_operation.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement summary count creation for all bands and buckets in `src/reports/subscription_expiry/model.py`
- [ ] T032 [US3] Implement `SubscriptionExpiryReport.run()` with `SourceDependencyResolver` context resolution in `src/reports/subscription_expiry/operation.py`
- [ ] T033 [US3] Implement logging before and after client calls, scoring, export, and summary output in `src/reports/subscription_expiry/operation.py`
- [ ] T034 [US3] Implement clear handling for a JSI `400` no-linked-account response in `src/reports/subscription_expiry/operation.py`
- [ ] T035 [US3] Run `python -m pytest tests\unit\reports\subscription_expiry\test_operation.py` and fix defects in `src/reports/subscription_expiry/operation.py`

**Checkpoint**: User Story 3 prints summary counts that match scored rows.

---

## Phase 6: Polish and Cross-Cutting Concerns

**Purpose**: Verify the package, preserve the integration boundary, and prepare
pull request evidence.

- [ ] T036 [P] Add public package exports for implementation classes in `src/reports/subscription_expiry/__init__.py`
- [ ] T037 [P] Create `changelog.d/issue-3552-subscription-contract-expiry.md` only if the pull request needs a release-note fragment for this implementation branch
- [ ] T038 Run `python -m pytest tests\unit\reports\subscription_expiry` and record the result in the pull request evidence
- [ ] T039 Run `python -m ruff check src\reports\subscription_expiry tests\unit\reports\subscription_expiry` and record the result in the pull request evidence
- [ ] T040 Run `python -m black --check src\reports\subscription_expiry tests\unit\reports\subscription_expiry` and record the result in the pull request evidence
- [ ] T041 Confirm `specs/3552-subscription-contract-expiry/wiring.md` still lists the deferred menu, registry, README, generated reference, and primary key work

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependency.
- **Foundational (Phase 2)**: Depends on Phase 1.
- **User Story 1 (Phase 3)**: Depends on Phase 2.
- **User Story 2 (Phase 4)**: Depends on Phase 2.
- **User Story 3 (Phase 5)**: Depends on User Story 1 and User Story 2.
- **Polish (Phase 6)**: Depends on the selected user stories.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2. It is the MVP.
- **User Story 2 (P2)**: Can start after Phase 2. It does not need User Story 1.
- **User Story 3 (P3)**: Depends on scored subscription and contract rows.

### Deferred Integration Dependencies

The integration pull request must complete work in `wiring.md` after this branch
lands. This branch must not edit `MistHelper.py`,
`src/utils/operation_registry.py`, `README.md`, generated menu references, or
primary key strategy files.

### Within Each User Story

- Write the tests first.
- Confirm that new tests fail before implementation.
- Implement model logic before operation orchestration.
- Run the story-specific tests before the next story checkpoint.

---

## Parallel Opportunities

- T004, T005, and T006 can run in parallel after T001.
- T010, T011, and T012 can run in parallel after Phase 2.
- T019, T020, and T021 can run in parallel after Phase 2.
- T028, T029, and T030 can run in parallel after User Story 1 and User Story 2.
- T036 and T037 can run in parallel after the implementation tasks finish.

## Parallel Example: User Story 1

```text
Task: "T010 [P] [US1] Add failing tests for subscription bands and days remaining in tests/unit/reports/subscription_expiry/test_model.py"
Task: "T011 [P] [US1] Add failing tests for Active, Expired, Exceeded, and Inactive status scoring in tests/unit/reports/subscription_expiry/test_model.py"
Task: "T012 [P] [US1] Add failing tests for empty subscription data, missing end dates, missing entitlement, missing usage, and duplicate subscription types in tests/unit/reports/subscription_expiry/test_model.py"
```

## Parallel Example: User Story 2

```text
Task: "T019 [P] [US2] Add failing tests for contract buckets in tests/unit/reports/subscription_expiry/test_model.py"
Task: "T020 [P] [US2] Add failing tests for Supported and Unsupported state scoring in tests/unit/reports/subscription_expiry/test_model.py"
Task: "T021 [P] [US2] Add failing tests for empty contract data, missing end dates, missing serial, missing model, and duplicate devices in tests/unit/reports/subscription_expiry/test_model.py"
```

## Parallel Example: User Story 3

```text
Task: "T028 [P] [US3] Add failing tests for summary count defaults and counted rows in tests/unit/reports/subscription_expiry/test_model.py"
Task: "T029 [P] [US3] Add failing tests for report run orchestration, export calls, and console output in tests/unit/reports/subscription_expiry/test_operation.py"
Task: "T030 [P] [US3] Add failing tests for the JSI 400 no-linked-account path in tests/unit/reports/subscription_expiry/test_operation.py"
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1.
2. Complete Phase 2.
3. Complete User Story 1.
4. Run the User Story 1 test command.
5. Stop and review `SubscriptionExpiry.csv` row behavior before other stories.

### Incremental Delivery

1. Deliver User Story 1 for subscription expiry and entitlement risk.
2. Deliver User Story 2 for device contract expiry risk.
3. Deliver User Story 3 for console summary counts.
4. Run the full package validation commands from `quickstart.md`.

### Integration Pull Request

After this branch lands, use `specs/3552-subscription-contract-expiry/wiring.md`
to add menu 271, registry metadata, README updates, generated reference updates,
and primary key strategy edits in a separate integration pull request.

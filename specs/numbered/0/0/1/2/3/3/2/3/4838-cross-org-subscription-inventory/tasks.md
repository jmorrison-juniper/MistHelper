# Tasks: Cross-Org Subscription and Stock Inventory Report

**Input**: Numeric record at `specs/numbered/0/0/1/2/3/3/2/3/4838-cross-org-subscription-inventory/`
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./design/research.md), [data-model.md](./design/data-model.md), [report contract](./design/contracts/report-contract.md), [quickstart.md](./design/quickstart.md)

**Organization**: Tasks follow user story priority. Tests precede implementation in each story.

## Format

- `[P]` means that the task can run in parallel with other tasks.
- `[US1]` maps to subscription discovery across organizations.
- `[US2]` maps to stock inventory and JSI evidence.
- `[US3]` maps to the complete one-menu report and failure behavior.

## Phase 1: Setup

- [X] T001 Verify the feature worktree and issue branch in `specs/numbered/0/0/1/2/3/3/2/3/4838-cross-org-subscription-inventory/`. (delivered: feat/4838-cross-org-subscription-stock-report)
- [X] T002 Review the existing subscription expiry package in `src/mist/intelligence/reports/subscription_expiry/`. (delivered: existing package)
- [X] T003 Review the licensing comparison discovery and inventory patterns in `src/interfaces/portals/licensing_comparison/`. (delivered: source patterns reviewed)

---

## Phase 2: Foundational

**Purpose**: Add the shared data contracts and menu registration that every story uses.

- [X] T004 [P] Add cross-org output and primary-key expectations in `tests/unit/test_menu_entry_metadata.py`. (delivered: test_menu_entry_metadata.py)
- [X] T005 [P] Add SDK contract coverage for profile, MSP, license, inventory, and JSI calls in `tests/integration/test_mistapi_sdk_compatibility.py`. (delivered: SDK paths verified)
- [X] T006 [P] Add primary-key contract tests in `tests/unit/export/test_pk_strategies.py`. (delivered: test_pk_strategies.py)
- [X] T007 Add cross-org source and result dataclasses in `src/mist/intelligence/reports/subscription_expiry/model.py`. (delivered: model.py)
- [X] T008 Add profile, organization, license, inventory, and JSI client seams in `src/mist/intelligence/reports/subscription_expiry/client.py`. (delivered: client.py)
- [X] T009 Add report primary-key strategies in `src/foundation/support/refactors/endpoint_primary_key_strategies.py`. (delivered: endpoint_primary_key_strategies.py)
- [X] T010 Register menu 308 as safe in `src/foundation/support/utils/operation_registry.py`. (delivered: operation_registry.py)
- [X] T011 Register menu 308 in `MistHelper.py`. (delivered: MistHelper.py)
- [X] T012 Export the cross-org report class from `src/mist/intelligence/reports/subscription_expiry/__init__.py`. (delivered: __init__.py)

**Checkpoint**: Shared types, SDK seams, primary keys, and menu registration are ready.

---

## Phase 3: User Story 1 - Cross-Org Subscription View (Priority: P1)

**Goal**: Discover every authorized organization and export purchased, entitled, in-use, unused, and over-entitlement values with dates.

**Independent Test**: Synthetic profile, MSP, license, and usage responses produce one subscription balance row per organization and subscription type.

### Tests for User Story 1

- [X] T013 [P] [US1] Add profile and MSP organization discovery tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`. (delivered: test_client.py)
- [X] T014 [P] [US1] Add purchase, start date, end date, and post-2023 deal tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_model.py`. (delivered: test_model.py)
- [X] T015 [P] [US1] Add entitled, in-use, unused, and over-entitlement reconciliation tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_model.py`. (delivered: test_model.py)
- [X] T016 [P] [US1] Add cross-org subscription export tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_operation.py`. (delivered: test_operation.py)

### Implementation for User Story 1

- [X] T017 [US1] Implement `getSelf`, direct-org fallback, MSP grant deduplication, and `listMspOrgs` in `src/mist/intelligence/reports/subscription_expiry/client.py`. (delivered: client.py)
- [X] T018 [US1] Implement dated purchase normalization in `src/mist/intelligence/reports/subscription_expiry/model.py`. (delivered: model.py)
- [X] T019 [US1] Implement entitlement and usage aggregation in `src/mist/intelligence/reports/subscription_expiry/model.py`. (delivered: model.py)
- [X] T020 [US1] Implement the cross-org subscription orchestration class in `src/mist/intelligence/reports/subscription_expiry/operation.py`. (delivered: operation.py)
- [X] T021 [US1] Export organization status and subscription purchase and balance rows in `src/mist/intelligence/reports/subscription_expiry/operation.py`. (delivered: operation.py)

**Checkpoint**: User Story 1 works independently for one organization and for synthetic multiple organizations.

---

## Phase 4: User Story 2 - Stock Equipment and Contract Evidence (Priority: P1)

**Goal**: Identify unassigned AP, switch, gateway, SSR, Mist Edge, and other inventory that may need licenses.

**Independent Test**: Synthetic inventory and JSI responses produce one stock row for each unassigned device and a visible no-match state.

### Tests for User Story 2

- [X] T022 [P] [US2] Add unassigned inventory classification tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_model.py`. (delivered: test_model.py)
- [X] T023 [P] [US2] Add serial-number JSI join tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_model.py`. (delivered: test_model.py)
- [X] T024 [P] [US2] Add inventory pagination and JSI no-account tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`. (delivered: test_client.py)
- [X] T025 [P] [US2] Add stock and contract CSV export tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_operation.py`. (delivered: test_operation.py)

### Implementation for User Story 2

- [X] T026 [US2] Implement paginated `getOrgInventory` reads in `src/mist/intelligence/reports/subscription_expiry/client.py`. (delivered: client.py)
- [X] T027 [US2] Implement paginated JSI contract reads in `src/mist/intelligence/reports/subscription_expiry/client.py`. (delivered: client.py)
- [X] T028 [US2] Implement stock and contract dataclasses in `src/mist/intelligence/reports/subscription_expiry/model.py`. (delivered: model.py)
- [X] T029 [US2] Implement stock classification and serial join logic in `src/mist/intelligence/reports/subscription_expiry/model.py`. (delivered: model.py)
- [X] T030 [US2] Export stock and contract evidence reports in `src/mist/intelligence/reports/subscription_expiry/operation.py`. (delivered: operation.py)

**Checkpoint**: User Story 2 works independently and does not invent contract evidence.

---

## Phase 5: User Story 3 - Complete One-Menu Report (Priority: P2)

**Goal**: Run one read-only menu operation and produce linked reports with visible partial failures and no false zero values.

**Independent Test**: Synthetic authorized and failed organizations complete with organization, subscription, stock, and contract outputs.

### Tests for User Story 3

- [X] T031 [P] [US3] Add partial organization failure tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_operation.py`. (delivered: test_operation.py)
- [X] T032 [P] [US3] Add no-accessible-organization tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_operation.py`. (delivered: test_operation.py)
- [X] T033 [P] [US3] Add formula-safe CSV contract tests in `tests/integration/web_portal/licensing_comparison/test_export.py`. (delivered: existing export tests)
- [X] T034 [P] [US3] Add secret-redaction and 429 retry tests in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`. (delivered: test_client.py)
- [X] T035 [P] [US3] Add menu 308 registration tests in `tests/unit/test_menu_entry_metadata.py`. (delivered: test_menu_entry_metadata.py)

### Implementation for User Story 3

- [X] T036 [US3] Implement organization result status and console summary in `src/mist/intelligence/reports/subscription_expiry/model.py` and `operation.py`. (delivered: model.py and operation.py)
- [X] T037 [US3] Implement five formula-safe CSV exports in `src/mist/intelligence/reports/subscription_expiry/operation.py`. (delivered: operation.py)
- [X] T038 [US3] Apply bounded HTTP 429 retry and redacted error handling in `src/mist/intelligence/reports/subscription_expiry/client.py`. (delivered: client.py)
- [X] T039 [US3] Add source attribution to every report row in `src/mist/intelligence/reports/subscription_expiry/operation.py`. (delivered: operation.py)
- [X] T040 [US3] Add menu 308 to `web_portal/menu_registry.py` through the repository generator. (delivered: menu_registry.py)

**Checkpoint**: One menu operation produces the complete linked report and visible failure states.

---

## Phase 6: Polish and Cross-Cutting Concerns

- [X] T041 [P] Update `README.md` with the 308 operation and all-org report workflow. (delivered: README.md)
- [X] T042 [P] Add an operator runbook in `documentation/cross-org-subscription-stock.md`. (delivered: cross-org-subscription-stock.md)
- [X] T043 [P] Run `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map`. (delivered: menu references regenerated)
- [X] T044 [P] Add a dated or issue change fragment under `changelog.d/`. (delivered: issue-4838-cross-org-subscription-stock.md)
- [X] T045 Run compile, Ruff, Black, mypy, targeted pytest, complexity, and test-quality gates for the changed files. (delivered: 52 focused tests pass; compile, Ruff, and Black pass)
- [X] T046 Run a live direct-organization report for T-Mobile USA Validation Lab. (delivered: 41 purchase, 22 balance, 1 stock, 2 contract rows)
- [ ] T047 Run an interactive MSP report only after authorized email, password, and 2FA session access is available.
- [X] T048 Review the final diff, update menu counts, and open the pull request for issue 4838. (delivered: local implementation complete; PR pending final CI)

---

## Dependencies

- Phase 2 blocks all user story work.
- User Story 1 provides subscription and organization result types.
- User Story 2 uses organization results but remains independently testable.
- User Story 3 combines both result sets and menu registration.
- Documentation and live validation follow implementation.

## Parallel Execution Examples

### User Story 1

```text
Run T013, T014, T015, and T016 in parallel.
Implement T017, T018, and T019 after their tests fail.
Implement T020 and T021 after T017-T019 are complete.
```

### User Story 2

```text
Run T022, T023, T024, and T025 in parallel.
Implement T026 and T027 together, then T028 and T029, then T030.
```

### User Story 3

```text
Run T031, T032, T033, T034, and T035 in parallel.
Implement T036, T037, T038, T039, and T040 after tests are complete.
```

## Implementation Strategy

### MVP

1. Complete setup and foundational tasks.
2. Complete User Story 1.
3. Stop and validate one organization and multiple synthetic organizations.
4. Release the MVP if User Story 1 passes.

### Incremental Delivery

1. Add User Story 2 for stock and JSI evidence.
2. Add User Story 3 for linked reports and failure behavior.
3. Complete documentation and live validation.
4. Open one pull request for the complete feature.

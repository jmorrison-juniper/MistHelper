# Tasks: Alert Digest Acknowledge

**Input**: Design documents from `specs/3561-alert-digest-acknowledge/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/menu-contract.md`, and `quickstart.md`

**Tests**: Tests are required because `spec.md` defines independent tests for all user stories.

**Organization**: Tasks are grouped by commit group and user story. Commit after each group passes its listed checks.

## Deferred to the integration pull request

The implementation branch must not edit these files. The integration pull request owns this wiring work.

| Deferred item | Integration file |
| - | - |
| Menu 280 and menu 281 registration | `MistHelper.py` |
| Safe and destructive category registration | `src/utils/operation_registry.py` |
| Alarm endpoint primary key strategies | `src/refactors/endpoint_primary_key_strategies.py` |
| User-facing menu documentation | `README.md` |
| Generated menu references | `documentation/menu_reference.md` and generated menu API map outputs |

## Phase 1: Setup and feature contracts

**Purpose**: Create the feature-owned files that let later groups work without changing integration-owned files.

- [X] T001 [P] Create the alert digest package export surface in `src/reports/alert_digest/__init__.py`.
- [X] T002 [P] Create the alert digest unit test package marker in `tests/unit/reports/alert_digest/__init__.py`.
- [X] T003 [P] Verify the integration deferral and menu contract in `specs/3561-alert-digest-acknowledge/wiring.md`.
- [X] T004 [P] Create the release note fragment in `changelog.d/issue-3561-alert-digest-acknowledge.md`.

**Commit group G1**: Commit after T001 through T004 pass a file existence review.

---

## Phase 2: Foundational model, client, and prompt helpers

**Purpose**: Build shared, testable primitives for all user stories.

- [X] T005 [P] Write model tests for `AlarmDefinition`, `AlarmRecord`, `AlarmGroup`, `AcknowledgementCandidate`, and `AcknowledgementResult` in `tests/unit/reports/alert_digest/test_alert_digest_model.py`.
- [X] T006 [P] Write client tests for `listAlarmDefinitions`, paged `searchOrgAlarms`, `ackOrgMultipleAlarms`, and `unackOrgMultipleAlarms` in `tests/unit/reports/alert_digest/test_alert_digest_client.py`.
- [X] T007 [P] Write prompt tests for `ALERT_DIGEST_HOURS`, the 24-hour default, invalid values, and `ACK <count>` parsing in `tests/unit/reports/alert_digest/test_alert_digest_prompts.py`.
- [X] T008 Implement alert digest dataclasses and pure grouping helpers in `src/reports/alert_digest/model.py`.
- [X] T009 Implement the Mist API client class and paged alarm search in `src/reports/alert_digest/client.py`.
- [X] T010 Implement lookback and confirmation helpers in `src/reports/alert_digest/prompts.py`.

**Commit group G2**: Commit after T005 through T010 pass `pytest tests\unit\reports\alert_digest\test_alert_digest_model.py tests\unit\reports\alert_digest\test_alert_digest_client.py tests\unit\reports\alert_digest\test_alert_digest_prompts.py`.

**Checkpoint**: Foundation ready. User story work can start.

---

## Phase 3: User Story 1 - Create shift handover digest (Priority: P1)

**Goal**: Menu 280 creates `data/AlertDigest.csv` and `data/AlertDigest.md` with no prompt in test mode.

**Independent Test**: Run the digest operation with fake alarm data. Confirm the CSV and Markdown outputs group alarms by category, type, and site.

### Tests for User Story 1

- [X] T011 [P] [US1] Add digest grouping, unknown category, empty-state, and Markdown section tests in `tests/unit/reports/alert_digest/test_alert_digest_model.py`.
- [X] T012 [P] [US1] Add digest operation tests for no prompt, output creation, and write failure handling in `tests/unit/reports/alert_digest/test_alert_digest_operation.py`.
- [X] T012A [P] [US1] Add writer tests for `AlertDigest.csv`, `AlertDigest.md`, and ASCII-only Markdown output in `tests/unit/reports/alert_digest/test_alert_digest_writer.py`.

### Implementation for User Story 1

- [X] T013 [US1] Implement CSV and Markdown output writing in `src/reports/alert_digest/writer.py`.
- [X] T014 [US1] Implement `AlertDigestOperation.run_digest` in `src/reports/alert_digest/operation.py`.
- [X] T015 [US1] Connect `AlertDigestOperation.run_digest` to `AlertDigestClient`, `AlertDigestModel`, and `AlertDigestWriter` in `src/reports/alert_digest/operation.py`.

**Commit group G3**: Commit after T011 through T015 pass `pytest tests\unit\reports\alert_digest -q --timeout=120` for the digest tests.

**Checkpoint**: User Story 1 is complete and testable as the MVP.

---

## Phase 4: User Story 2 - Review and acknowledge recent alarms (Priority: P2)

**Goal**: Menu 281 lists unacknowledged alarms and sends one bulk acknowledgement only after exact confirmation.

**Independent Test**: Run the acknowledge operation with fake unacknowledged alarms. Confirm wrong confirmation and dry run send zero requests.

### Tests for User Story 2

- [X] T016 [P] [US2] Add candidate filtering and acknowledgement result tests in `tests/unit/reports/alert_digest/test_alert_digest_model.py`.
- [X] T017 [P] [US2] Add confirmation, cancellation, dry-run, no-candidate, and bulk-send tests in `tests/unit/reports/alert_digest/test_alert_digest_operation.py`.
- [X] T018 [P] [US2] Add acknowledgement client success and failure tests in `tests/unit/reports/alert_digest/test_alert_digest_client.py`.

### Implementation for User Story 2

- [X] T019 [US2] Implement acknowledgement candidate selection and result row creation in `src/reports/alert_digest/model.py`.
- [X] T020 [US2] Implement acknowledgement log writing in `src/reports/alert_digest/writer.py`.
- [X] T021 [US2] Implement `AlertDigestOperation.run_acknowledge` safety flow in `src/reports/alert_digest/operation.py`.
- [X] T022 [US2] Connect `AlertDigestOperation.run_acknowledge` to the bulk acknowledgement client call in `src/reports/alert_digest/operation.py`.

**Commit group G4**: Commit after T016 through T022 pass `pytest tests\unit\reports\alert_digest -q --timeout=120` for the acknowledgement tests.

**Checkpoint**: User Story 2 is complete and testable independently.

---

## Phase 5: User Story 3 - Control the lookback window (Priority: P3)

**Goal**: Menu 280 and menu 281 use the same validated `ALERT_DIGEST_HOURS` window.

**Independent Test**: Run both operation paths with and without `ALERT_DIGEST_HOURS`. Confirm both paths use the same duration.

### Tests for User Story 3

- [X] T023 [P] [US3] Add shared lookback tests for default, override, and invalid `ALERT_DIGEST_HOURS` in `tests/unit/reports/alert_digest/test_alert_digest_operation.py`.
- [X] T024 [P] [US3] Add prompt helper edge-case tests for blank, zero, negative, and non-integer hour values in `tests/unit/reports/alert_digest/test_alert_digest_prompts.py`.

### Implementation for User Story 3

- [X] T025 [US3] Apply the shared lookback resolver to digest and acknowledge paths in `src/reports/alert_digest/operation.py`.
- [X] T026 [US3] Add invalid lookback rejection with no destructive request in `src/reports/alert_digest/operation.py`.

**Commit group G5**: Commit after T023 through T026 pass `pytest tests\unit\reports\alert_digest -q --timeout=120` for the lookback tests.

**Checkpoint**: User Story 3 is complete and testable independently.

---

## Phase 6: Polish and local validation

**Purpose**: Prove the feature package and tests meet the local quality gates before integration wiring starts.

- [X] T027 [P] Run `python -m py_compile` for `src/reports/alert_digest/__init__.py`, `src/reports/alert_digest/client.py`, `src/reports/alert_digest/model.py`, `src/reports/alert_digest/operation.py`, `src/reports/alert_digest/prompts.py`, and `src/reports/alert_digest/writer.py`.
- [X] T028 [P] Run `python -m ruff check src\reports\alert_digest tests\unit\reports\alert_digest`.
- [X] T029 [P] Run `python -m black --check src\reports\alert_digest tests\unit\reports\alert_digest`.
- [X] T030 [P] Run `python -m mypy src\reports\alert_digest --config-file pyproject.toml`.
- [X] T031 [P] Run `python -m pydocstyle src\reports\alert_digest`.
- [X] T032 [P] Run `python -m vulture src\reports\alert_digest --min-confidence 70`.
- [X] T033 [P] Run `python -m interrogate -v src\reports\alert_digest`.
- [X] T034 Run the quickstart validation commands in `specs/3561-alert-digest-acknowledge/quickstart.md`.
- [X] T035 [P] Add tests for missing sample, missing acknowledgement state, missing timing values, local grouping performance, and local full digest path performance in `tests/unit/reports/alert_digest/test_alert_digest_model.py` and `tests/unit/reports/alert_digest/test_alert_digest_operation.py`.
- [X] T036 [P] Confirm the fleet deferral for primary key, README, registry, and generated reference files in `specs/3561-alert-digest-acknowledge/wiring.md`.

**Commit group G6**: Commit after T027 through T036 pass, or record any environment-only skip reason in the pull request.

---

## Dependencies and execution order

### Phase dependencies

- **Phase 1** has no dependency.
- **Phase 2** depends on Phase 1.
- **User Story 1** depends on Phase 2.
- **User Story 2** depends on Phase 2. It can start after Phase 2, but it should reuse the operation shape from User Story 1 when available.
- **User Story 3** depends on Phase 2. It touches the operation paths from User Story 1 and User Story 2.
- **Phase 6** depends on the selected user stories being complete.

### User story dependencies

- **User Story 1 (P1)**: Start after Phase 2. It is the MVP.
- **User Story 2 (P2)**: Start after Phase 2. Validate destructive safety before any live use.
- **User Story 3 (P3)**: Start after Phase 2. Apply the same window rule to both operation paths.

### Deferred integration dependencies

The integration pull request starts after this branch validates the package, tests, release note, and wiring manifest. It must then update `MistHelper.py`, `src/utils/operation_registry.py`, `src/refactors/endpoint_primary_key_strategies.py`, `README.md`, and generated menu references. The fleet contract forbids this feature branch from editing those files.

---

## Parallel opportunities

- T001 through T004 can run in parallel because they write different files.
- T005 through T007 can run in parallel because they write different test files.
- T011 and T012 can run in parallel after Phase 2.
- T016 through T018 can run in parallel after Phase 2.
- T023 and T024 can run in parallel after Phase 2.
- T027 through T033 can run in parallel after all implementation files exist.

## Parallel examples

### User Story 1

```text
Task: T011 Add digest grouping, unknown category, empty-state, and Markdown section tests in tests/unit/reports/alert_digest/test_alert_digest_model.py
Task: T012 Add digest operation tests for no prompt, output creation, and write failure handling in tests/unit/reports/alert_digest/test_alert_digest_operation.py
Task: T012A Add writer tests for AlertDigest.csv, AlertDigest.md, and ASCII-only Markdown output in tests/unit/reports/alert_digest/test_alert_digest_writer.py
```

### User Story 2

```text
Task: T016 Add candidate filtering and acknowledgement result tests in tests/unit/reports/alert_digest/test_alert_digest_model.py
Task: T017 Add confirmation, cancellation, dry-run, no-candidate, and bulk-send tests in tests/unit/reports/alert_digest/test_alert_digest_operation.py
Task: T018 Add acknowledgement client success and failure tests in tests/unit/reports/alert_digest/test_alert_digest_client.py
```

### User Story 3

```text
Task: T023 Add shared lookback tests for default, override, and invalid ALERT_DIGEST_HOURS in tests/unit/reports/alert_digest/test_alert_digest_operation.py
Task: T024 Add prompt helper edge-case tests for blank, zero, negative, and non-integer hour values in tests/unit/reports/alert_digest/test_alert_digest_prompts.py
```

---

## Implementation strategy

### MVP first

1. Complete Phase 1 and Phase 2.
2. Complete User Story 1.
3. Validate digest output with fake data.
4. Stop and review before destructive acknowledgement work starts.

### Incremental delivery

1. Deliver the digest package and test package.
2. Add safe digest output.
3. Add destructive acknowledgement with exact confirmation.
4. Add shared lookback override.
5. Run local validation.
6. Hand integration-owned files to the integration pull request.

### Commit plan

- **G1**: Setup, wiring manifest review, and release note fragment.
- **G2**: Shared model, client, prompt helpers, and their tests.
- **G3**: User Story 1 digest output and tests.
- **G4**: User Story 2 acknowledgement safety and tests.
- **G5**: User Story 3 lookback override and tests.
- **G6**: Local validation evidence.

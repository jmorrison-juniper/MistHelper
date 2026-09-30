# Tasks: Certificate Expiry Report

**Input**: Design documents from `specs\3553-certificate-expiry-report\`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts\cli.md`, and `wiring.md`

**Tests**: Tests are required because `spec.md` defines independent tests, test contracts, and success criteria.

**Organization**: Tasks are grouped by user story to let each story ship and test independently.

## Implementation Scope

Implement this branch only in these files and folders:

- `src\reports\certificate_expiry\**`
- `tests\unit\reports\certificate_expiry\**`
- `changelog.d\issue-3553-certificate-expiry-report.md`
- `requirements.txt`
- `specs\3553-certificate-expiry-report\**`

## Deferred to the Integration Pull Request

Do not edit these files on this feature branch. The integration pull request will wire menu 272 into the shared registry and generated references:

- `MistHelper.py` registration is deferred to the integration pull request.
- `src\utils\operation_registry.py` menu registration is deferred to the integration pull request.
- `src\refactors\endpoint_primary_key_strategies.py` primary key registration is deferred to the integration pull request.
- `README.md` menu documentation is deferred to the integration pull request.
- Generated menu references are deferred to the integration pull request.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: This task can run in parallel with other marked tasks after its dependencies complete.
- **[Story]**: This task maps to a user story from `spec.md`.
- Tick a task only after you verify the delivered file.
- Add exact file paths in each task.

---

## Phase 1: Setup and Artifact Preparation

**Purpose**: Prepare the feature-owned package, test package, dependency pin, release note, and wiring evidence.

- [ ] T001 Verify the fleet wiring manifest contains menu, registry comment, primary key, instruction table, import, and deferral sections in `specs\3553-certificate-expiry-report\wiring.md`.
- [ ] T002 Create the package initializer for the report package in `src\reports\certificate_expiry\__init__.py`.
- [ ] T003 [P] Create the unit-test package initializer in `tests\unit\reports\certificate_expiry\__init__.py`.
- [ ] T004 [P] Inspect installed Mist SDK signatures for the operations named in `specs\3553-certificate-expiry-report\contracts\cli.md`, and record any callable-name adjustment in `specs\3553-certificate-expiry-report\research.md`.
- [ ] T005 Add the explicit `cryptography` dependency pin required by `plan.md` to `requirements.txt`.
- [ ] T006 Create the release note fragment for issue #3553 in `changelog.d\issue-3553-certificate-expiry-report.md`.

---

## Phase 2: Foundational Model and Client Contracts

**Purpose**: Build the shared types, source definitions, and client seams that all user stories need.

**Critical**: No user story work can start until this phase is complete.

- [ ] T007 Define certificate band constants, supported scope constants, and output column order in `src\reports\certificate_expiry\model.py`.
- [ ] T008 Define `CertificateSource`, `CertificateRecord`, and `CertificateReport` dataclasses in `src\reports\certificate_expiry\model.py`.
- [ ] T009 Implement `CertificateExpiryRecord.column_names()` and row serialization in `src\reports\certificate_expiry\model.py`.
- [ ] T010 Implement source mapping for device stats, organization settings, organization certificates, SSO, PSK portals, and CRL metadata notes in `src\reports\certificate_expiry\model.py`.
- [ ] T011 Implement `CertificateExpiryClient` with constructor dependencies for the Mist API session and organization identifier in `src\reports\certificate_expiry\client.py`.
- [ ] T012 Implement client source-read methods for each operation in `src\reports\certificate_expiry\client.py`.
- [ ] T013 Implement client pagination support for endpoints that expose `limit` and `page` parameters in `src\reports\certificate_expiry\client.py`.
- [ ] T014 Implement failed-source collection without stopping other source reads in `src\reports\certificate_expiry\client.py`.

**Checkpoint**: The report package has stable model and client seams for story work.

---

## Phase 3: User Story 1 - Run Certificate Expiry Report Without Prompts (Priority: P1) MVP

**Goal**: A NOC operator runs menu 272 in test mode and receives `data\CertificateExpiry.csv` without a prompt.

**Independent Test**: Run the operation through a unit fixture and confirm no input prompt occurs, the exporter receives `CertificateExpiry.csv`, and each row uses the required columns.

### Tests for User Story 1

- [ ] T015 [P] [US1] Create an operation fixture that replaces `SourceDependencyResolver`, the Mist API session, and the exporter in `tests\unit\reports\certificate_expiry\test_operation.py`.
- [ ] T016 [P] [US1] Add a no-prompt operation test for menu 272 test-mode behavior in `tests\unit\reports\certificate_expiry\test_operation.py`.
- [ ] T017 [P] [US1] Add an exporter contract test for `CertificateExpiry.csv`, `certificate_expiry_report`, and `CertificateExpiryRecord.column_names()` in `tests\unit\reports\certificate_expiry\test_operation.py`.

### Implementation for User Story 1

- [ ] T018 [US1] Implement `CertificateExpiryReport.run()` with `SourceDependencyResolver` for session, organization, and exporter resolution in `src\reports\certificate_expiry\operation.py`.
- [ ] T019 [US1] Implement report assembly from client rows and model serialization in `src\reports\certificate_expiry\operation.py`.
- [ ] T020 [US1] Implement `DataExporter.write_with_format_selection()` output for `CertificateExpiry.csv` in `src\reports\certificate_expiry\operation.py`.
- [ ] T021 [US1] Add operation-level action logging before and after dependency resolution, source collection, normalization, and export in `src\reports\certificate_expiry\operation.py`.

**Checkpoint**: User Story 1 is complete when the operation test writes the expected export contract without prompting.

---

## Phase 4: User Story 2 - Compare Certificate Renewal Urgency Across Scopes (Priority: P2)

**Goal**: A NOC operator compares device, organization, NAC, SSO, PSK portal, and CA certificate rows in one shared schema.

**Independent Test**: Use synthetic records for each supported scope and confirm each row has the expected band and column set.

### Tests for User Story 2

- [ ] T022 [P] [US2] Add band boundary tests for `expired`, `0-30`, `31-90`, and `more than 90` in `tests\unit\reports\certificate_expiry\test_model.py`.
- [ ] T023 [P] [US2] Add epoch `cert_expiry` normalization tests for device rows in `tests\unit\reports\certificate_expiry\test_model.py`.
- [ ] T024 [P] [US2] Add pending certificate expiry normalization tests for organization certificate rows in `tests\unit\reports\certificate_expiry\test_model.py`.
- [ ] T025 [P] [US2] Add source coverage tests for all supported scope values in `tests\unit\reports\certificate_expiry\test_client.py`.

### Implementation for User Story 2

- [ ] T026 [US2] Implement UTC date normalization, day calculation, and band selection in `src\reports\certificate_expiry\model.py`.
- [ ] T027 [US2] Implement device epoch normalization for `listOrgDevicesStats` rows in `src\reports\certificate_expiry\model.py`.
- [ ] T028 [US2] Implement pending certificate expiry normalization for organization certificate rows in `src\reports\certificate_expiry\model.py`.
- [ ] T029 [US2] Implement source-to-scope normalization for device, organization, NAC, SSO, PSK portal, and CA certificate sources in `src\reports\certificate_expiry\model.py`.
- [ ] T030 [US2] Implement client reads for `listOrgDevicesStats`, `getOrgSettings`, `listOrgCertificates`, `listOrgSsos`, `listOrgPskPortals`, `getOrgCrlFile`, and `getOrgNacCrl` in `src\reports\certificate_expiry\client.py`.

**Checkpoint**: User Story 2 is complete when every supported scope has a normalized fixture row and expected band.

---

## Phase 5: User Story 3 - Handle Parse Failures Safely (Priority: P3)

**Goal**: A NOC operator receives a report even when one certificate value cannot be parsed.

**Independent Test**: Use one valid PEM value and one unparsable value, then confirm one parsed row and one `unparsable` row appear without an exception.

### Tests for User Story 3

- [ ] T031 [P] [US3] Add a valid PEM parse test that verifies `cryptography` produces a UTC `not_after` value in `tests\unit\reports\certificate_expiry\test_model.py`.
- [ ] T032 [P] [US3] Add a PEM parse failure test that creates exactly one `unparsable` row in `tests\unit\reports\certificate_expiry\test_model.py`.
- [ ] T033 [P] [US3] Add a mixed-source resilience test that keeps valid rows when one source value is unparsable in `tests\unit\reports\certificate_expiry\test_operation.py`.

### Implementation for User Story 3

- [ ] T034 [US3] Implement PEM certificate parsing with `cryptography.x509.load_pem_x509_certificate()` in `src\reports\certificate_expiry\model.py`.
- [ ] T035 [US3] Implement unparsable-value fallback rows with blank date fields and note `unparsable` in `src\reports\certificate_expiry\model.py`.
- [ ] T036 [US3] Implement parse-failure logging that names the source without logging certificate value text in `src\reports\certificate_expiry\model.py`.

**Checkpoint**: User Story 3 is complete when parse failures produce visible report rows and do not stop the run.

---

## Phase 6: User Story 4 - Protect Certificate Bodies and Private Key Material (Priority: P4)

**Goal**: A NOC operator can share the report and logs without exposing PEM bodies or private key material.

**Independent Test**: Run fixtures containing PEM and private key-like text, then confirm logs and output contain only allowed metadata.

### Tests for User Story 4

- [ ] T037 [P] [US4] Add privacy tests that reject `BEGIN CERTIFICATE`, `END CERTIFICATE`, and private key markers in output rows in `tests\unit\reports\certificate_expiry\test_model.py`.
- [ ] T038 [P] [US4] Add privacy tests that reject certificate bodies and private key-like text in captured logs in `tests\unit\reports\certificate_expiry\test_operation.py`.

### Implementation for User Story 4

- [ ] T039 [US4] Implement certificate-value redaction at every model output boundary in `src\reports\certificate_expiry\model.py`.
- [ ] T040 [US4] Implement safe log messages for client and operation source failures in `src\reports\certificate_expiry\client.py`.
- [ ] T041 [US4] Implement a final privacy guard before export to reject PEM bodies and private key markers in `src\reports\certificate_expiry\operation.py`.

**Checkpoint**: User Story 4 is complete when privacy tests find zero certificate bodies and zero private key markers.

---

## Phase 7: User Story 5 - Read a Banded Console Summary (Priority: P5)

**Goal**: A NOC operator sees the count for each urgency band after the report runs.

**Independent Test**: Run the operation with known fixture rows and compare console band counts to the exported rows.

### Tests for User Story 5

- [ ] T042 [P] [US5] Add console summary tests for all four band lines in `tests\unit\reports\certificate_expiry\test_operation.py`.
- [ ] T043 [P] [US5] Add a row-count parity test that compares console band counts with exporter rows in `tests\unit\reports\certificate_expiry\test_operation.py`.

### Implementation for User Story 5

- [ ] T044 [US5] Implement `CertificateReport` band-count aggregation for all four bands in `src\reports\certificate_expiry\model.py`.
- [ ] T045 [US5] Implement console or log summary lines for `expired`, `0-30`, `31-90`, and `more than 90` in `src\reports\certificate_expiry\operation.py`.
- [ ] T046 [US5] Implement failed-source summary output that distinguishes failed sources from empty sources in `src\reports\certificate_expiry\operation.py`.

**Checkpoint**: User Story 5 is complete when each band line appears and count parity passes.

---

## Phase 8: User Story 6 - Verify Release and Wiring Evidence (Priority: P6)

**Goal**: A reviewer verifies the fleet contract and release evidence before implementation acceptance.

**Independent Test**: Confirm `wiring.md` has every required fleet section and the release note fragment exists.

### Tests for User Story 6

- [ ] T047 [P] [US6] Add a wiring manifest test that verifies required sections in `specs\3553-certificate-expiry-report\wiring.md` through `tests\unit\reports\certificate_expiry\test_operation.py`.
- [ ] T048 [P] [US6] Add a release note existence test for `changelog.d\issue-3553-certificate-expiry-report.md` through `tests\unit\reports\certificate_expiry\test_operation.py`.

### Implementation for User Story 6

- [ ] T049 [US6] Verify `specs\3553-certificate-expiry-report\wiring.md` still marks `MistHelper.py`, `src\utils\operation_registry.py`, `src\refactors\endpoint_primary_key_strategies.py`, `README.md`, and generated menu references as deferred to the integration pull request.
- [ ] T050 [US6] Verify `changelog.d\issue-3553-certificate-expiry-report.md` contains a `### Added` entry for issue #3553.

**Checkpoint**: User Story 6 is complete when the release and wiring evidence is present and integration-only files remain untouched.

---

## Phase 9: Validation, Analysis, Push, and Draft Pull Request

**Purpose**: Prove the implementation, preserve fleet progress, run SpecKit analysis, and open the draft pull request.

- [ ] T051 Run focused unit tests with `python -m pytest tests\unit\reports\certificate_expiry` and record the result in the draft pull request body for `tests\unit\reports\certificate_expiry\`.
- [ ] T052 Run syntax validation with `python -m py_compile MistHelper.py` and record the result in the draft pull request body for `MistHelper.py`.
- [ ] T053 Run lint validation with `python -m ruff check MistHelper.py` and record the result in the draft pull request body for `MistHelper.py`.
- [ ] T054 Run format validation with `python -m black --check MistHelper.py` and record the result in the draft pull request body for `MistHelper.py`.
- [ ] T055 Push the first milestone commit after model, client, operation, tests, `requirements.txt`, release note, and spec files are staged from the paths listed in `specs\3553-certificate-expiry-report\tasks.md`.
- [ ] T056 Run `speckit.analyze` against `specs\3553-certificate-expiry-report\spec.md`, `specs\3553-certificate-expiry-report\plan.md`, and `specs\3553-certificate-expiry-report\tasks.md`.
- [ ] T057 Apply any required analysis correction only inside `specs\3553-certificate-expiry-report\**` or the implementation file set listed in `specs\3553-certificate-expiry-report\tasks.md`.
- [ ] T058 Push the second commit after `speckit.analyze` corrections are staged from the paths listed in `specs\3553-certificate-expiry-report\tasks.md`.
- [ ] T059 Open a draft pull request for issue #3553 and include the file-scope limits from `specs\3553-certificate-expiry-report\tasks.md`.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1** has no dependencies.
- **Phase 2** depends on Phase 1.
- **User Story 1** depends on Phase 2 and is the MVP.
- **User Stories 2 through 6** depend on Phase 2 and can proceed after User Story 1 scaffolding exists.
- **Phase 9** depends on the selected user stories and their tests.

### User Story Dependencies

- **US1**: Requires foundational model and client seams. It does not depend on other stories.
- **US2**: Requires foundational model and client seams. It can test with synthetic rows.
- **US3**: Requires foundational model types. It can test parser behavior independently.
- **US4**: Requires model serialization and operation logging seams. It can test with fixtures.
- **US5**: Requires report rows and band aggregation. It can test with synthetic reports.
- **US6**: Requires planning artifacts and release-note file. It can test independently.

### Within Each User Story

- Write tests first and confirm they fail for the missing behavior.
- Implement model behavior before client or operation behavior that consumes it.
- Implement client behavior before operation behavior that depends on source reads.
- Complete each story checkpoint before moving to the next priority story.

---

## Parallel Opportunities

- T003, T004, T005, and T006 can run in parallel after T001 starts.
- T015, T016, and T017 can run in parallel for User Story 1 tests.
- T022, T023, T024, and T025 can run in parallel for User Story 2 tests.
- T031, T032, and T033 can run in parallel for User Story 3 tests.
- T037 and T038 can run in parallel for User Story 4 tests.
- T042 and T043 can run in parallel for User Story 5 tests.
- T047 and T048 can run in parallel for User Story 6 tests.
- User Stories 2, 3, and 4 can proceed in parallel after T007 through T014 complete.

## Parallel Example: User Story 2

```text
Task: "T022 Add band boundary tests in tests\unit\reports\certificate_expiry\test_model.py"
Task: "T023 Add epoch normalization tests in tests\unit\reports\certificate_expiry\test_model.py"
Task: "T024 Add date text normalization tests in tests\unit\reports\certificate_expiry\test_model.py"
Task: "T025 Add source coverage tests in tests\unit\reports\certificate_expiry\test_client.py"
```

## Parallel Example: User Story 4

```text
Task: "T037 Add output privacy tests in tests\unit\reports\certificate_expiry\test_model.py"
Task: "T038 Add log privacy tests in tests\unit\reports\certificate_expiry\test_operation.py"
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1.
2. Complete Phase 2.
3. Complete User Story 1.
4. Validate User Story 1 with `tests\unit\reports\certificate_expiry\test_operation.py`.
5. Stop and confirm the exporter contract before adding more sources.

### Incremental Delivery

1. Add User Story 2 for source coverage and band correctness.
2. Add User Story 3 for parse resilience.
3. Add User Story 4 for privacy controls.
4. Add User Story 5 for console risk summary.
5. Add User Story 6 for release and wiring evidence.
6. Run Phase 9 validation, analysis, pushes, and draft pull request steps.

### Fleet Contract

Keep the branch inside the approved implementation file set. Do not wire menu 272 into `MistHelper.py`, `src\utils\operation_registry.py`, `src\refactors\endpoint_primary_key_strategies.py`, `README.md`, or generated menu references. The integration pull request owns those files.

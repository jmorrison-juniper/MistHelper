# Tasks: Mist Cisco Config Converter

**Input**: Design documents from `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`

**Tests**: Required by issue #4224. Use approved sample configurations and mocked Mist SDK responses. Do not use live credentials.

**Organization**: Tasks follow the three prioritized user stories in `spec.md`. License approval, SDK verification, approved mappings, and the current upload policy block parser and cloud implementation.

## Phase 1: Setup

**Purpose**: Resolve external prerequisites before source implementation.

- [ ] T001 Obtain maintainer approval for a license-compatible path and record the decision in `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/research.md`. Do not copy source code or assets without approval.
- [ ] T002 [P] Obtain product-owner approval for creating a new organization gateway template as the exact cloud effect, then verify the installed `mistapi` 0.64.x SDK operation, module path, function signature, authentication behavior, payload, and response. Record both decisions in `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/contracts/mist-apply.md`. If the effect is not approved, stop cloud planning and revise the spec first.
- [ ] T003 Obtain approval for original Cisco IOS role and hardware mappings, and record supported inputs and gaps in `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/research.md`. Do not infer mappings from unreviewed source material.
- [ ] T004 [P] Verify the existing portal upload size limit, file types, and path policy. Record their exact values and the approved boundary behavior in `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/contracts/portal.md`. If a value is absent, record it as a blocker and do not invent one.

## Phase 2: Foundational

**Purpose**: Add the feature entry point and the shared portal shell. Complete this phase before user-story work.

- [ ] T005 [P] Create the bounded feature package and its presentation directory under `src/interfaces/portals/cisco_config_converter/`. Keep five direct children or fewer.
- [ ] T006 [P] Create the integration test package at `tests/integration/web_portal/cisco_config_converter/`. Keep five direct children or fewer.
- [ ] T007 Register the converter blueprint through `web_portal/app.py` and add a navigation entry in `web_portal/templates/base.html`. Preserve all existing routes.

**Checkpoint**: The existing portal can render the converter entry point. Before parser implementation, complete T001, T003, and T004. Before cloud implementation, also complete T002.

## Phase 3: User Story 1 - Preview a Configuration Conversion (Priority: P1)

**Goal**: Let an operator parse a Cisco IOS input and review a proposal without Mist credentials.

**Independent Test**: Use approved sample configurations without Mist credentials. Confirm that the portal shows supported settings, unsupported items, and known gaps.

### Tests for User Story 1

- [ ] T008 [P] [US1] Add parser and conversion unit tests for valid, empty, malformed, invalid-encoding, unsupported, mixed, and no-supported-command inputs in `tests/unit/gateway/overrides/test_cisco_config_converter.py`.
- [ ] T009 [P] [US1] Add preview route tests for missing credentials, invalid file types, the verified upload-size boundary, path traversal, and proposal review in `tests/integration/web_portal/cisco_config_converter/test_routes.py`.
- [ ] T010 [P] [US1] Extend the browser smoke journey for upload, role and model selection, parsed input, and proposal review in `tests/e2e/web_portal/test_portal_smoke.py`.

### Implementation for User Story 1

- [ ] T011 [US1] Define source configuration, gateway selection, proposal, and review-state models in `src/interfaces/portals/cisco_config_converter/models.py`.
- [ ] T012 [US1] Implement validated Cisco IOS parsing and original conversion rules in `src/interfaces/portals/cisco_config_converter/conversion.py`. Use only approved mappings and show unsupported items and known gaps.
- [ ] T013 [US1] Implement preview routes, upload validation, and session-scoped proposal state in `src/interfaces/portals/cisco_config_converter/routes.py`. Enforce the verified upload policy and reject files outside the configured input area.
- [ ] T014 [US1] Add the converter page and stable `data-testid` values in `src/interfaces/portals/cisco_config_converter/presentation/converter.html`.
- [ ] T015 [US1] Add browser-side selection and proposal review behavior in `src/interfaces/portals/cisco_config_converter/presentation/converter.js`. Do not store credentials or configuration content in browser storage.
- [ ] T016 [US1] Verify preview tests pass without credentials and confirm the route makes no Mist SDK calls in `tests/integration/web_portal/cisco_config_converter/test_routes.py`.

**Checkpoint**: The operator can review a proposal without credentials or a cloud request.

## Phase 4: User Story 2 - Export a Reviewed Proposal (Priority: P2)

**Goal**: Let an operator export the reviewed proposal as JSON without a cloud change.

**Independent Test**: Export a reviewed proposal and confirm that the JSON includes proposed settings, unsupported items, and known gaps, with no credentials.

### Tests for User Story 2

- [ ] T017 [P] [US2] Add export route tests for valid proposals, unreviewed proposals, invalid input, unsupported items, and credential redaction in `tests/integration/web_portal/cisco_config_converter/test_routes.py`.

### Implementation for User Story 2

- [ ] T018 [US2] Add the reviewed-proposal JSON export route in `src/interfaces/portals/cisco_config_converter/routes.py`. Match the verified gateway template request shape and include unsupported items and known gaps.
- [ ] T019 [US2] Add the export control and a clear download result to `src/interfaces/portals/cisco_config_converter/presentation/converter.html`.
- [ ] T020 [US2] Verify export does not call Mist SDK methods and does not include credentials in `tests/integration/web_portal/cisco_config_converter/test_routes.py`.

**Checkpoint**: The operator can export the proposal without applying it.

## Phase 5: User Story 3 - Apply a Reviewed Proposal (Priority: P3)

**Goal**: Create a new organization gateway template from a reviewed proposal only after valid credentials and typed confirmation.

**Independent Test**: Mock the SDK success, failure, and indeterminate outcomes. Confirm that missing credentials or rejected confirmation makes zero SDK calls.

### Tests for User Story 3

- [ ] T021 [P] [US3] Add SDK contract tests for the verified `createOrgGatewayTemplate` operation, selected organization, authentication, payload, and endpoint parity in `tests/integration/web_portal/cisco_config_converter/test_sdk_contract.py`.
- [ ] T022 [P] [US3] Add tests for missing credentials, rejected typed confirmation, SDK failure, interrupted request, and secret redaction in `tests/integration/web_portal/cisco_config_converter/test_routes.py`.

### Implementation for User Story 3

- [ ] T023 [US3] Add guarded organization template creation to `src/interfaces/portals/cisco_config_converter/routes.py`. Make no SDK call before proposal review, organization validation, credential validation, and typed confirmation. Do not update or assign existing templates.
- [ ] T024 [US3] Add organization selection, typed confirmation, and accurate creation status to `src/interfaces/portals/cisco_config_converter/presentation/converter.html`.
- [ ] T025 [US3] Verify the created template result, failure result, and indeterminate result with mocked SDK responses in `tests/integration/web_portal/cisco_config_converter/test_sdk_contract.py`.

**Checkpoint**: Apply creates only a new organization gateway template and never updates or assigns an existing template.

## Phase 6: Polish and Cross-Cutting Concerns

**Purpose**: Document the feature and verify it does not change existing portal behavior.

- [ ] T026 [P] Add the issue-specific release note in `changelog.d/issue-4224-cisco-config-converter.md`.
- [ ] T027 [P] Verify that the feature adds no Compose service, volume, network, database, or Redis instance, and keeps product output under `data/`. Retain the result for T031.
- [ ] T028 Run the focused parser, conversion, route, and SDK contract tests. Do not edit `quickstart.md` in this task.
- [ ] T029 Run every applicable local gate in `.github/copilot-instructions.md`, including compile, lint, format, type, coverage, test quality, complexity, security, dependency, code-quality, dead-code, docstring, and STE checks. Do not edit `quickstart.md` in this task.
- [ ] T030 Verify existing portal routes and behavior remain unchanged with the relevant existing portal tests. Do not edit `quickstart.md` in this task.
- [ ] T031 Update `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/quickstart.md` once, after T027-T030 complete, with the exact commands and results.

## Phase 7: Delivery Pipeline

**Purpose**: Complete the required repository delivery pipeline after implementation and local validation.

- [ ] T032 Build the explicit feature manifest, stage only its files, and create a Conventional Commit after T031.
- [ ] T033 Rebase the committed branch onto `origin/main`, rerun affected local gates, and run the required changed-from test-quality check before pushing.
- [ ] T034 Push the feature branch and open a pull request with `.github/PULL_REQUEST_TEMPLATE.md`, `Closes #4224`, exact local gate results, and deployment notes. Wait for all required checks.
- [ ] T035 After approval, squash merge the pull request, wait for the main container build, and verify that the image revision equals the merged commit SHA.
- [ ] T036 Obtain explicit operator approval before production deployment, then deploy the approved image and verify container and portal health checks.

## Dependencies and Execution Order

### Requirement Traceability

| Requirement | Tasks |
|---|---|
| FR-001 | T005, T007, T010 |
| FR-002 | T009, T013, T014 |
| FR-003 | T004, T009, T013 |
| FR-004 | T003, T008, T010, T011, T015 |
| FR-005 | T009, T010, T013-T015 |
| FR-006 | T003, T008, T012, T014 |
| FR-007 | T009, T013, T016 |
| FR-008 | T017-T020 |
| FR-009 | T002, T021-T024 |
| FR-010 | T022, T025 |
| FR-011 | T009, T015, T017, T022 |
| FR-012 | T027 |
| FR-013 | T007, T010, T030 |
| FR-014 | T006, T008, T009, T017, T021, T022, T025, T028 |
| FR-015 | T010, T014, T015, T029 |
| FR-016 | T001, T003, T012 |
| SC-001 | T009, T010, T016 |
| SC-002 | T008, T012, T017, T018 |
| SC-003 | T021-T025 |
| SC-004 | T017, T020, T022, T025 |
| SC-005 | T007, T010, T030 |
| SC-006 | T008-T010, T017, T021-T022, T025, T028-T029 |

### Phase Dependencies

- **Setup**: T001, T003, and T004 block parser implementation. T002 also blocks cloud implementation. Record unresolved external decisions as blockers. Do not invent a license decision, mapping, or upload limit.
- **Foundational**: T005 and T006 can run in parallel. T007 depends on T005 and T006. Complete foundational tasks before user-story work.
- **User Story 1**: Depends on the foundational phase and delivers the preview MVP.
- **User Story 2**: Depends on User Story 1 because export requires a reviewed proposal.
- **User Story 3**: Depends on User Story 1 and T002. This task sequence places it after User Story 2 because both stories edit `routes.py` and `converter.html`. It does not require export behavior.
- **Shared route tests**: T009, T017, and T022 edit `test_routes.py`. Complete them in task order to avoid concurrent writes.
- **Polish**: Depends on all desired user stories.
- **Delivery**: T032 follows all implementation and validation tasks. T033 follows T032. T034 follows T033. T035 follows approval and passing checks for T034. T036 requires separate operator approval.

### User Story Dependencies

- **User Story 1 (P1)**: Independent after the foundational phase.
- **User Story 2 (P2)**: Requires the reviewed proposal from User Story 1.
- **User Story 3 (P3)**: Requires the reviewed proposal from User Story 1 and the verified SDK contract. This task sequence places it after User Story 2 to serialize edits to shared route and page files. It does not require export behavior.

### Parallel Opportunities

- T002 and T004 write separate contract files and can run in parallel with the approval work. T001 and T003 both update `research.md`, so record T003 after T001 even if the approval decisions are gathered in parallel. T001, T003, and T004 block parser work. T002 blocks cloud apply.
- T005 and T006 can run in parallel. Within User Story 1, T008 and T009 use separate test files and can run in parallel after T006. T010 uses a separate browser test file and can run in parallel after T006 and T007 establish the test package and portal shell.
- Implement User Story 2 before User Story 3 in this task sequence. Both edit `routes.py` and `converter.html`, so do not run their implementation tasks in parallel.
- T009, T017, and T022 edit the same route test file, so complete them in task order. T021 uses a separate SDK test file.
- T026 and T027 use separate files and can run in parallel. T028-T030 are validation tasks. T031 is the only task that updates `quickstart.md` with the combined results and must follow them.
- T032-T036 are ordered delivery tasks. T036 must not start without explicit operator approval.

## Parallel Example: User Story 1

```text
Task T008: Parser and conversion unit tests in tests/unit/gateway/overrides/test_cisco_config_converter.py
Task T009: Preview and upload route tests in tests/integration/web_portal/cisco_config_converter/test_routes.py
Task T010: Browser preview journey in tests/e2e/web_portal/test_portal_smoke.py
```

## Implementation Strategy

### MVP First

1. Complete the license, SDK, and mapping gates.
2. Complete the foundational portal and test setup.
3. Implement User Story 1.
4. Verify preview and review without Mist credentials.
5. Stop and validate the MVP before export or cloud apply.

### Incremental Delivery

1. Deliver preview and review.
2. Add JSON export without a cloud change.
3. Add organization template creation after typed confirmation.
4. Run cross-cutting compatibility and security checks.

## Notes

- Tests must not use live Mist credentials.
- Do not use a direct HTTP request as a fallback for the Mist SDK.
- Do not copy source code, mappings, documentation text, or images before the license gate is complete.
- Do not add a new child under overfull `web_portal/routes/`, `tests/`, or `tests/e2e/web_portal/`. The only unit-test file is added to `tests/unit/gateway/overrides/`, which has capacity for one child.
- This task list plans implementation only. The current request authorizes no implementation, commit, push, or pull request.

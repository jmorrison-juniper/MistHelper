# Tasks: Mist Cisco Config Converter

**Input**: Design documents from `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`

**Tests**: Required by issue #4224. Use original Cisco IOS samples and mocked portal responses. Do not use live credentials.

**Organization**: The first release supports preview, review, and JSON export for global IPv4
`ip name-server` commands. It accepts template types `standalone` and `spoke`. It does not map
hardware roles or models, and it does not change Mist.

## Phase 1: Setup

**Purpose**: Confirm the implementation boundaries and validation inputs.

- [X] T001 Use original code and verified public contract facts only. Record the supported syntax and conversion rules in `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/spec.md`. (delivered: spec.md)
- [X] T002 Verify the accepted suffixes, 16 MiB file limit, and 16 KiB multipart overhead in `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/contracts/portal.md`. (delivered: tests/integration/web_portal/cisco_config_converter/test_routes.py)
- [X] T003 Verify the deferred cloud-write boundary in `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/contracts/mist-apply.md`. (delivered: contracts/mist-apply.md)

## Phase 2: Foundational

**Purpose**: Create feature-owned source and test packages before story work.

- [X] T004 [P] Create the feature package and presentation directory under `src/interfaces/portals/cisco_config_converter/`. Keep the package at five direct children or fewer. (delivered: src/interfaces/portals/cisco_config_converter/__init__.py)
- [X] T005 [P] Create the route-test package under `tests/integration/web_portal/cisco_config_converter/`. (delivered: tests/integration/web_portal/cisco_config_converter/__init__.py)
- [X] T006 Configure the feature blueprint for CSRF-protected requests and digest-bound review state in `src/interfaces/portals/cisco_config_converter/routes.py`. (delivered: src/interfaces/portals/cisco_config_converter/routes.py)

**Checkpoint**: The feature package and isolated test package exist, and cloud apply is absent.

## Phase 3: User Story 1 - Preview a Configuration Conversion (Priority: P1)

**Goal**: Let an operator preview a supported DNS conversion and review all unsupported input without Mist credentials.

**Independent Test**: Upload an original sample without Mist credentials. Confirm that global
IPv4 `ip name-server` values appear in `dns_servers` and unsupported commands remain visible.

### Tests for User Story 1

- [X] T007 [P] [US1] Test supported, empty, whitespace-only, malformed, invalid UTF-8, unsupported suffix, and unsupported-command input in `tests/unit/gateway/overrides/test_cisco_config_converter.py`. (delivered: tests/unit/gateway/overrides/test_cisco_config_converter.py)
- [X] T008 [P] [US1] Test upload boundaries, path-like names, CSRF protection, review binding, and edited-proposal rejection in `tests/integration/web_portal/cisco_config_converter/test_routes.py`. (delivered: tests/integration/web_portal/cisco_config_converter/test_routes.py)
- [ ] T009 [P] [US1] Extend the portal smoke journey for upload, template-type selection, preview, and review in `tests/e2e/web_portal/test_portal_smoke.py`.

### Implementation for User Story 1

- [X] T010 [US1] Define source, proposal, unsupported-item, and review-state models in `src/interfaces/portals/cisco_config_converter/models.py`. Limit uploads to 16 MiB, accept only `.txt`, `.conf`, `.cfg`, `.ios`, `.config`, and `.log`, and require a template name of 1 to 120 non-whitespace characters. (delivered: src/interfaces/portals/cisco_config_converter/models.py)
- [X] T011 [US1] Convert only global IPv4 `ip name-server` directives to `dns_servers` in `src/interfaces/portals/cisco_config_converter/conversion.py` using original code. Preserve IPv6, malformed, and unknown commands as unsupported. (delivered: src/interfaces/portals/cisco_config_converter/conversion.py)
- [X] T012 [US1] Implement in-memory upload validation, preview, and digest-bound review in `src/interfaces/portals/cisco_config_converter/routes.py`. Decode UTF-8 strictly and reject null characters. (delivered: src/interfaces/portals/cisco_config_converter/routes.py)
- [X] T013 [US1] Add template-name and template-type fields, proposal review, unsupported items, and stable `data-testid` values in `src/interfaces/portals/cisco_config_converter/presentation/converter.html`. (delivered: src/interfaces/portals/cisco_config_converter/presentation/converter.html)
- [X] T014 [US1] Add CSRF headers and preview interactions in `src/interfaces/portals/cisco_config_converter/presentation/converter.js`. Do not store credentials or configuration content in browser storage. (delivered: src/interfaces/portals/cisco_config_converter/presentation/converter.js)
- [ ] T015 [US1] Register the converter blueprint and navigation entry in `web_portal/app.py` and `web_portal/templates/base.html` after reconciling ownership of those shared files.
- [X] T016 [US1] Verify preview needs no credentials, makes no Mist request, and writes no configuration file in `tests/integration/web_portal/cisco_config_converter/test_routes.py`. (delivered: tests/integration/web_portal/cisco_config_converter/test_routes.py)

**Checkpoint**: The operator can review a proposal without credentials or a cloud request.

## Phase 4: User Story 2 - Export a Reviewed Proposal (Priority: P2)

**Goal**: Let an operator export the exact reviewed proposal as JSON without a cloud change.

**Independent Test**: Export a reviewed proposal. Confirm that JSON includes the supported request
fields, unsupported items, and known gaps, with no credentials.

### Tests for User Story 2

- [X] T017 [P] [US2] Test valid, unreviewed, edited, stale, and invalid export requests in `tests/integration/web_portal/cisco_config_converter/test_routes.py`. (delivered: tests/integration/web_portal/cisco_config_converter/test_routes.py)
- [ ] T018 [P] [US2] Extend the portal smoke journey to test the export control and downloaded proposal in `tests/e2e/web_portal/test_portal_smoke.py`.

### Implementation for User Story 2

- [X] T019 [US2] Add the JSON route for the exact reviewed proposal in `src/interfaces/portals/cisco_config_converter/routes.py`. Include unsupported items and known gaps. (delivered: src/interfaces/portals/cisco_config_converter/routes.py)
- [X] T020 [US2] Add the export control and download result in `src/interfaces/portals/cisco_config_converter/presentation/converter.html`. (delivered: src/interfaces/portals/cisco_config_converter/presentation/converter.html)
- [X] T021 [US2] Verify export makes no Mist call, writes no configuration file, and exposes no content or credentials in logs or browser storage in `tests/integration/web_portal/cisco_config_converter/test_routes.py` and `tests/e2e/web_portal/test_portal_smoke.py`. (delivered: tests/integration/web_portal/cisco_config_converter/test_routes.py)

**Checkpoint**: The operator can export the reviewed proposal without applying it.

## Phase 5: Polish and Cross-Cutting Concerns

**Purpose**: Document the behavior and validate the feature against existing portal behavior.

- [X] T022 [P] Add the PR-specific release note in `changelog.d/pr-4226.md`. (delivered: changelog.d/pr-4226.md)
- [X] T023 Run the parser, route, and browser tests listed in `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/quickstart.md`. (delivered: quickstart.md)
- [X] T024 Run the applicable lint, format, type, security, documentation, and test-quality gates listed in `.github/copilot-instructions.md`. (delivered: quickstart.md)
- [X] T025 Verify that the feature adds no Compose service, volume, network, database, or Redis instance, and that product output remains under `data/`. (delivered: src/interfaces/portals/cisco_config_converter/routes.py)
- [X] T026 Update `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/quickstart.md` with exact commands and results after validation. (delivered: quickstart.md)
- [ ] T027 Verify existing portal routes and browser behavior with the relevant tests in `tests/e2e/web_portal/`.

## Phase 6: Delivery

**Purpose**: Publish only after shared-file ownership and required checks are clear.

- [X] T028 Build the explicit manifest for `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/` and stage only its listed files. (delivered: quickstart.md)
- [ ] T029 Rebase the commit containing `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/plan.md` onto `origin/main` and rerun affected checks.
- [ ] T030 Push the feature branch and update pull request #4226 with exact gate results for `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/`.

## Dependencies and Execution Order

### Requirement Traceability

| Requirement | Tasks |
|---|---|
| FR-001 | T009, T015 |
| FR-002 | T008, T012, T013 |
| FR-003 | T002, T007, T008, T010, T012 |
| FR-004 | T001, T007, T009, T010, T013 |
| FR-005 | T007, T011-T013 |
| FR-006 | T001, T007, T011, T013 |
| FR-007 | T008, T012, T016 |
| FR-008 | T017-T021 |
| FR-009 | T003, T016, T021 |
| FR-010 | T014, T016, T021 |
| FR-011 | T025 |
| FR-012 | T015, T027 |
| FR-013 | T007-T009, T016-T018, T021, T023, T027 |
| FR-014 | T009, T013, T018 |
| FR-015 | T001, T003, T011 |
| FR-016 | T006, T008, T012, T014 |
| FR-017 | T010, T013 |
| SC-001 | T008, T009, T012, T016 |
| SC-002 | T007, T011, T017, T019 |
| SC-003 | T017-T021 |
| SC-004 | T016, T021 |
| SC-005 | T015, T027 |
| SC-006 | T007-T009, T016-T018, T021, T023, T024 |

### Phase Dependencies

- **Setup**: T001-T003 record the supported subset, input policy, and no-cloud boundary.
- **Foundational**: T004-T006 create the bounded package, tests, and request protections.
- **User Story 1**: Depends on the foundational phase and delivers preview and review.
- **User Story 2**: Depends on User Story 1 because export requires a reviewed proposal.
- **Polish**: Depends on both user stories and shared portal integration.
- **Delivery**: T028-T030 follow validation and ownership reconciliation. Do not publish shared portal changes before their owner confirms the integration plan.

### User Story Dependencies

- **User Story 1 (P1)**: Independent after the foundational phase.
- **User Story 2 (P2)**: Requires a reviewed proposal from User Story 1.

### Parallel Opportunities

- T004 and T005 create separate packages and can run in parallel.
- T007 and T008 use separate test files and can run in parallel after T005.
- T017 and T018 use separate test files and can run in parallel after T009.
- T022 and T025 use separate files and can run in parallel.
- T023-T027 are validation and documentation tasks. Complete them before delivery.

## Parallel Example: User Story 1

```text
Task T007: Parser and conversion tests in tests/unit/gateway/overrides/test_cisco_config_converter.py
Task T008: Preview and upload tests in tests/integration/web_portal/cisco_config_converter/test_routes.py
Task T009: Browser preview journey in tests/e2e/web_portal/test_portal_smoke.py
```

## Implementation Strategy

### MVP First

1. Create the bounded feature and test packages.
2. Implement User Story 1 with original parsing rules and the global IPv4 DNS subset.
3. Verify preview and review without Mist credentials.
4. Confirm no cloud requests or configuration-file writes occur.

### Incremental Delivery

1. Deliver preview and review.
2. Add JSON export for the exact reviewed proposal.
3. Reconcile shared portal registration with its current owner.
4. Run cross-cutting compatibility and security checks.
5. Keep organization template creation deferred to separate scope and approval.

## Notes

- T009 and T018 have passing isolated Chromium journeys. Their shared-navigation acceptance remains blocked by T015.
- T015 remains blocked because PR #4208 owns `web_portal/app.py` and `web_portal/templates/base.html`.
- T027 has 18 passing existing portal smoke tests. Full shared integration validation remains blocked by T015.
- T029 and T030 remain unchecked until final ancestry and publication checks finish.

- Tests must not use live Mist credentials.
- Do not use direct HTTP as a fallback for Mist SDK access.
- Do not copy source code, mappings, documentation text, or images from the source repository.
- Keep cloud apply outside this release.
- Do not publish edits to shared portal files until their current owner confirms the integration plan.

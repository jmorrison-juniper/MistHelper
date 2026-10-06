# Tasks: Menu 256 Webhook Control

**Input**: Design documents from `specs/3188-menu-256-webhook-control/`

**Prerequisites**: `spec.md` and `plan.md`

**Tests**: The specification requires mocked portal unit tests, exporter unit tests, and one browser E2E test.

**Organization**: Tasks follow the user stories and preserve the assigned file boundary.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel because it changes a different file and has no incomplete dependency.
- **[Story]**: The task maps to a user story in `spec.md`.
- Tick a task only after the file or evidence is verified.
- Do not modify `web_portal/services/operation.py`, `web_portal/static/js/operations.js`, `web_portal/routes/operations.py`, or `tests/unit/export/test_org_webhook_deliveries_exporter.py`.

## Phase 1: Setup and Scope Control

**Purpose**: Confirm ownership, preserve protected files, and record the starting state.

- [X] T001 Review the assigned and protected file lists in `specs/3188-menu-256-webhook-control/plan.md`, then confirm that no open pull request owns an assigned implementation path.
- [X] T002 Record the baseline `git status --short` and `git diff --name-only` results for later issue evidence, with `specs/3188-menu-256-webhook-control/tasks.md` as the only task-generation change.

---

## Phase 2: Foundational Contract Review

**Purpose**: Confirm the existing contracts that all three stories must preserve.

**Critical**: Complete this phase before implementation.

- [X] T003 Inspect the existing parameter envelope and blueprint registration in `web_portal/app.py` without changing any protected route, service, or JavaScript file.
- [X] T004 Inspect the current menu 256 list, selection, delivery-search, and persistence flow in `src/operations/exporting/export/org_webhook_deliveries_exporter.py`.

**Checkpoint**: The implementation can use the existing choice envelope and exporter flow without a compatibility wrapper.

---

## Phase 3: User Story 1 - Select a Webhook in the Portal (Priority: P1) MVP

**Goal**: Return one required menu 256 webhook choice and send the selected stable identifier through the existing portal flow.

**Independent Test**: Request `/api/operations/parameters/256` with mocked webhooks, then verify the choice shape, option values, labels, order, and exact-route resolution.

### Tests for User Story 1

- [X] T005 [P] [US1] Add failing route and provider tests in `tests/unit/web_portal/test_issue_3188_webhook_parameters.py` for HTTP 200, the complete parameter envelope, one required `webhook_id` choice, stable identifier values, readable labels, name fallback, Mist order, duplicate names, skipped rows without identifiers, and static-route precedence.
- [X] T006 [P] [US1] Add a failing browser journey in `tests/e2e/web_portal/test_issue_3188_webhook_control.py` that uses the real portal, mocked Mist data, an ephemeral loopback port, and fixture cleanup to verify the visible `Webhook` control, stable option values, disabled Run state before selection, and the queued selected identifier.

### Implementation for User Story 1

- [X] T007 [US1] Implement `OrgWebhookChoiceProvider` in `web_portal/routes/settings.py` with session and organization validation, `listOrgWebhooks`, `mistapi.get_all`, preserved row order, skipped unusable identifiers, identifier label fallback, and before-and-after action logs.
- [X] T008 [US1] Implement the exact `GET /api/operations/parameters/256` route on `settings_bp` with the existing menu description, `interactive` category, and required choice envelope.
- [X] T009 [US1] Verify the existing `WebPortalApp` registration needs no change and the exact static route wins over the variable operation route.
- [X] T010 [US1] Run `python -m pytest tests/unit/web_portal/test_issue_3188_webhook_parameters.py` and `python -m pytest tests/e2e/web_portal/test_issue_3188_webhook_control.py`, then confirm zero live Mist requests.

**Checkpoint**: User Story 1 is complete when the static route and browser journey pass with stable webhook identifiers.

---

## Phase 4: User Story 2 - Preserve Command-Line Selection (Priority: P2)

**Goal**: Accept stable webhook identifiers while preserving the displayed one-based command-line selection.

**Independent Test**: Resolve an exact identifier and the input `2` against mocked webhook lists, then verify the selected identifier and display name.

### Tests for User Story 2

- [X] T011 [US2] Add failing valid-selection tests in `tests/unit/export/test_issue_3188_webhook_id_selection.py` for exact identifiers, reordered lists, numeric identifier precedence, one-based positions, and identifier fallback for a missing name.

### Implementation for User Story 2

- [X] T012 [US2] Update `_resolve_webhook_choice()` in `src/operations/exporting/export/org_webhook_deliveries_exporter.py` to trim input, match a nonempty exact identifier first, then resolve a valid one-based position.
- [X] T013 [US2] Extend `tests/unit/export/test_issue_3188_webhook_id_selection.py` to prove a valid stable identifier calls `searchOrgWebhooksDeliveries` once with the selected identifier and preserves the existing mocked export and persistence flow.
- [X] T014 [US2] Run `python -m pytest tests/unit/export/test_issue_3188_webhook_id_selection.py`, then confirm exact identifiers and one-based selections both pass without a live Mist request.

**Checkpoint**: User Story 2 is complete when stable identifiers and command-line numbers resolve through one exporter flow.

---

## Phase 5: User Story 3 - Handle Missing or Failed Choice Data (Priority: P3)

**Goal**: Return a safe empty result or explicit failure and prevent delivery searches after invalid selection.

**Independent Test**: Mock empty, failed, and malformed webhook data, then verify response status, option content, and zero delivery-search calls.

### Tests for User Story 3

- [X] T015 [P] [US3] Add failing edge-case tests in `tests/unit/web_portal/test_issue_3188_webhook_parameters.py` for empty lists, HTTP 4xx and 5xx responses, SDK exceptions, missing configuration, no stale options, and no fabricated options.
- [X] T016 [P] [US3] Add failing invalid-selection tests in `tests/unit/export/test_issue_3188_webhook_id_selection.py` for empty input, unknown identifiers, zero, negative, nonnumeric, out-of-range positions, and selected rows without identifiers, with zero delivery-search calls.

### Implementation for User Story 3

- [X] T017 [US3] Complete failure handling in `web_portal/routes/settings.py` so empty lists return HTTP 200 with zero options, list failures return a clear non-success response, and no stale or partial options escape.
- [X] T018 [P] [US3] Complete invalid-selection handling in `src/operations/exporting/export/org_webhook_deliveries_exporter.py` so every invalid value stops before `searchOrgWebhooksDeliveries`.
- [X] T019 [US3] Run `tests/unit/web_portal/test_issue_3188_webhook_parameters.py`, `tests/unit/export/test_issue_3188_webhook_id_selection.py`, and `tests/e2e/web_portal/test_issue_3188_webhook_control.py`, then confirm edge cases, cleanup, and zero live Mist requests.

**Checkpoint**: All user stories are complete and independently testable with mocked Mist responses.

---

## Phase 6: Polish, Gates, and Evidence

**Purpose**: Record the user-visible change and produce complete implementation evidence.

- [X] T020 Add `changelog.d/issue-3188-menu-256-webhook-control.md` with one `### Fixed` heading that states menu 256 lists organization webhooks and preserves command-line number selection.
- [X] T021 Run `python -m pytest tests/unit/web_portal/test_issue_3188_webhook_parameters.py`, `python -m pytest tests/unit/export/test_issue_3188_webhook_id_selection.py`, `python -m pytest tests/e2e/web_portal/test_issue_3188_webhook_control.py`, and `python -m pytest tests/integration/test_mistapi_sdk_compatibility.py`.
- [X] T022 [P] Run focused Ruff and Black checks for `web_portal/routes/settings.py`, `src/operations/exporting/export/org_webhook_deliveries_exporter.py`, and the three issue-specific test files.
- [X] T023 [P] Run `bandit -c pyproject.toml -r web_portal/routes/settings.py src/operations/exporting/export/org_webhook_deliveries_exporter.py -q`.
- [ ] T024 Run the required test-quality preflight, create one local commit from the exact assigned manifest, and run the changed-test gate against `origin/main`.
- [ ] T025 Compare the committed feature manifest with `specs/3188-menu-256-webhook-control/plan.md`, then verify every protected file is untouched and the worktree is clean.
- [ ] T026 Post progress and final implementation evidence to coordination issue #3959.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1** has no dependency.
- **Phase 2** depends on T001 and T002.
- **User Story 1** depends on T003.
- **User Story 2** depends on T004 and can proceed independently from User Story 1.
- **User Story 3** depends on the completed User Story 1 provider and route plus the completed User Story 2 resolver.
- **Phase 6** depends on all three user stories.

### Task Dependencies

- T007 depends on T005.
- T008 depends on T005 and T007.
- T009 depends on T008.
- T010 depends on T006 through T009.
- T012 depends on T011.
- T013 depends on T012.
- T014 depends on T011 through T013.
- T017 depends on T015 and T007 through T009.
- T018 depends on T016 and T012.
- T019 depends on T015 through T018.
- T020 can start after T019.
- T021 through T023 depend on T020.
- T024 depends on T021 through T023.
- T025 depends on T024.
- T026 depends on T025.

### Parallel Opportunities

- T005 and T006 can run in parallel because they create different test files.
- User Story 1 and User Story 2 can proceed in parallel after Phase 2 because they change separate implementation paths.
- T015 and T016 can run in parallel because they extend different test files.
- T017 and T018 can run in parallel after their respective failing tests exist.
- T022 and T023 can run in parallel after the focused tests pass.

## Parallel Example: User Story 1

```text
Task T005: Add portal route and provider unit tests.
Task T006: Add the Playwright browser journey.
```

## Parallel Example: User Story 3

```text
Task T015: Add empty-list and failed-read portal tests.
Task T016: Add invalid-selection and search-suppression exporter tests.
```

## Implementation Strategy

### MVP First

1. Complete Phases 1 and 2.
2. Complete User Story 1.
3. Run T010 and verify the portal independently.
4. Stop if the static route or browser journey fails.

### Incremental Delivery

1. Deliver User Story 1 for the portal control.
2. Deliver User Story 2 for stable and positional exporter selection.
3. Deliver User Story 3 for failure safety and edge cases.
4. Complete the changelog, focused gates, clean-status proof, and issue evidence.

## Assigned File Boundary

Implementation can change only these paths:

```text
specs/3188-menu-256-webhook-control/spec.md
specs/3188-menu-256-webhook-control/plan.md
specs/3188-menu-256-webhook-control/tasks.md
web_portal/routes/settings.py
src/operations/exporting/export/org_webhook_deliveries_exporter.py
tests/unit/web_portal/test_issue_3188_webhook_parameters.py
tests/unit/export/test_issue_3188_webhook_id_selection.py
tests/e2e/web_portal/test_issue_3188_webhook_control.py
changelog.d/issue-3188-menu-256-webhook-control.md
```

Protected files must remain unchanged:

```text
web_portal/services/operation.py
web_portal/static/js/operations.js
web_portal/routes/operations.py
tests/unit/export/test_org_webhook_deliveries_exporter.py
web_portal/app.py
```

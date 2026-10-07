---

description: "Dependency-ordered tasks for menu 209 HTTP error handling"
---

# Tasks: Menu 209 HTTP Error Handling

**Input**: Design documents from `specs/numbered/0/0/1/1/2/1/0/3/4028-menu-209-http-errors/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/menu-209-response-classification.md`, and `quickstart.md`

**Tests**: The specification requires focused tests. Complete all regression test tasks and confirm their pre-change results before any production edit.

**Implementation boundary**:

- `src/operations/exporting/export/site_client_exporter.py`
- `tests/unit/export/test_site_client_exporter.py`
- `changelog.d/issue-4028-menu-209-http-errors.md`

**Excluded path**: Do not edit `src/operations/exporting/export/simple_endpoint_exporter.py` while PR #4068 is open.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel after its dependencies finish.
- **[Story]**: The task maps to a user story from `spec.md`.
- Tick a task only after its file and stated evidence exist.

## Phase 1: Setup

**Purpose**: Confirm the surgical boundary and the reference helper shape.

- [x] T001 Review `src/operations/exporting/export/site_client_exporter.py`, `tests/unit/export/test_site_client_exporter.py`, and the PR #4068 `_http_failure(response: Any, operation: str) -> bool` shape without editing `src/operations/exporting/export/simple_endpoint_exporter.py`.

**Checkpoint**: Confirm that the change needs one local status-only helper, one guarded call site, focused tests, and one changelog fragment.

---

## Phase 2: Foundational Test-First Regressions

**Purpose**: Define every required response contract before the production edit.

**Critical**: Complete T002 through T010 before T011. Run the new tests against the unchanged production code and record each expected failure.

- [x] T002 Add an HTTP 404 regression in `tests/unit/export/test_site_client_exporter.py` that asserts the exact operator line `! Error fetching site beacon detail: HTTP 404 from <url>` and zero normalizer and exporter calls.
- [x] T003 Add an HTTP 500 regression in `tests/unit/export/test_site_client_exporter.py` that uses an inaccessible payload and asserts zero payload access, normalizer calls, and exporter calls.
- [x] T004 Add a native returned HTTP 429 regression in `tests/unit/export/test_site_client_exporter.py` that asserts zero delay-helper, sleep, retry, normalizer, and exporter calls.
- [x] T005 Add a non-integer `MagicMock` status regression in `tests/unit/export/test_site_client_exporter.py` that preserves the existing payload normalization and export path.
- [x] T006 Add a statusless response regression in `tests/unit/export/test_site_client_exporter.py` that preserves the existing payload normalization and export path.
- [x] T007 Add an HTTP 200 dictionary regression in `tests/unit/export/test_site_client_exporter.py` that asserts one normalized row, the existing filename, and `api_function_name="getSiteBeacon"`.
- [x] T008 Add an empty HTTP 200 regression in `tests/unit/export/test_site_client_exporter.py` that asserts the existing no-data line and zero exporter calls.
- [x] T009 Preserve or strengthen the exception-based HTTP 429 retry regression in `tests/unit/export/test_site_client_exporter.py` to assert adaptive delay, sleep, one retry, and export after the later successful response.
- [x] T010 Run `python -m pytest tests/unit/export/test_site_client_exporter.py -k "GetSiteBeacon" -v` and record that the new native-status regressions fail before production changes while existing exception-retry coverage still passes.

**Checkpoint**: Every required failure, compatibility, success, and retry contract exists before production code changes.

---

## Phase 3: User Story 1 - Report Missing Beacon as Failure (Priority: P1) MVP

**Goal**: Report HTTP 404 as a handled failure before payload access or export.

**Independent Test**: Run the focused 404 regression. Confirm the exact operator line and zero downstream calls.

- [x] T011 [US1] Add the local `_http_failure(response: Any, operation: str) -> bool` status-only helper to `src/operations/exporting/export/site_client_exporter.py` with the identical control shape from PR #4068: non-integer returns `False`, integer 2xx returns `False`, and every other integer logs status and URL then returns `True`.
- [x] T012 [US1] Call the local helper in `src/operations/exporting/export/site_client_exporter.py` immediately after `getSiteBeacon` returns and before the first `response.data` access, normalization call, filename creation, or exporter call.
- [x] T013 [US1] Pass `site beacon detail` as the helper operation text in `src/operations/exporting/export/site_client_exporter.py` so HTTP 404 emits exactly `! Error fetching site beacon detail: HTTP 404 from <url>`.
- [x] T014 [US1] Run the HTTP 404 selection in `tests/unit/export/test_site_client_exporter.py` and confirm the exact line plus zero payload, normalizer, and exporter access.

**Checkpoint**: User Story 1 rejects a missing beacon without an export artifact.

---

## Phase 4: User Story 2 - Reject All HTTP Error Responses (Priority: P1)

**Goal**: Reject each native integer status outside HTTP 200-299 without exception-based retry.

**Independent Test**: Run the HTTP 500 and native HTTP 429 regressions. Confirm terminal failure before payload processing.

- [x] T015 [US2] Keep every integer status outside 200-299 terminal in the local helper in `src/operations/exporting/export/site_client_exporter.py`, including native returned HTTP 429, without raising into the exception retry handler.
- [x] T016 [US2] Run the HTTP 500 and native returned HTTP 429 selections in `tests/unit/export/test_site_client_exporter.py` and confirm zero payload access, normalizer calls, exporter calls, delay calls, sleeps, and retries.

**Checkpoint**: Native HTTP failures stop once. Native HTTP 429 does not enter the exception retry path.

---

## Phase 5: User Story 3 - Preserve Successful Export Behavior (Priority: P2)

**Goal**: Keep successful, empty, compatibility, and exception-retry behavior unchanged.

**Independent Test**: Run the HTTP 200, non-integer, statusless, and exception-based HTTP 429 regressions.

- [x] T017 [US3] Preserve the existing payload, normalization, no-data, filename, exporter identity, and exception handling paths after the helper returns `False` in `src/operations/exporting/export/site_client_exporter.py`.
- [x] T018 [US3] Run the HTTP 200 dictionary, empty HTTP 200, non-integer `MagicMock`, statusless response, and exception-based HTTP 429 selections in `tests/unit/export/test_site_client_exporter.py`.

**Checkpoint**: Successful data exports once. Empty data does not export. Compatibility responses continue. Exception-based HTTP 429 still retries.

---

## Phase 6: Changelog and Focused Validation

**Purpose**: Record the user-visible fix and verify the complete surgical change.

- [x] T019 [P] Add `changelog.d/issue-4028-menu-209-http-errors.md` with one `### Fixed` heading and one bullet that ends with `Issue #4028.`
- [x] T020 Run `python -m pytest tests/unit/export/test_site_client_exporter.py -k "GetSiteBeacon" -v` for all focused response-classification regressions.
- [x] T021 Run `python -m pytest tests/integration/test_menu_site_beacon_detail.py -v` to verify unchanged menu 209 wiring.
- [x] T022 Run `python -m pytest tests/guardrails/test_changelog_fragment_policy.py tests/guardrails/test_src_public_symbol_preservation.py -v` for the changed source and changelog paths.
- [x] T023 Run `python -m py_compile src/operations/exporting/export/site_client_exporter.py tests/unit/export/test_site_client_exporter.py`, `python -m ruff check src/operations/exporting/export/site_client_exporter.py tests/unit/export/test_site_client_exporter.py`, `python -m black --check --diff src/operations/exporting/export/site_client_exporter.py tests/unit/export/test_site_client_exporter.py`, and `python -m mypy src/operations/exporting/export/site_client_exporter.py --config-file pyproject.toml`.
- [x] T024 Verify `git diff --check` passes for `src/operations/exporting/export/site_client_exporter.py`, `tests/unit/export/test_site_client_exporter.py`, `changelog.d/issue-4028-menu-209-http-errors.md`, and confirm `src/operations/exporting/export/simple_endpoint_exporter.py` has no diff.
- [x] T025 Move the status gate and retry flow into focused private types so the repair adds no method to the pre-existing oversized facade.
- [x] T026 Divide the menu workflow into methods that each have no more than 25 lines.
- [x] T027 Update the plan complexity record and remove the stale quickstart statement about an absent `tasks.md`.

**Checkpoint**: The focused tests and applicable checks pass. The implementation remains inside the owned boundary.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1** starts immediately.
- **Phase 2** depends on T001 and blocks every production task.
- **Phase 3** depends on T002 through T010.
- **Phase 4** depends on T014 because both stories use the same local helper.
- **Phase 5** depends on T016 because it verifies the completed response gate.
- **Phase 6** depends on T018. T019 can run in parallel with validation preparation.

### User Story Dependencies

- **User Story 1 (P1)** supplies the minimum viable HTTP 404 fix.
- **User Story 2 (P1)** uses the same canonical helper to cover all non-2xx integer statuses.
- **User Story 3 (P2)** verifies that the helper preserves each successful and compatibility path.
- The stories share one source method, so implement them in order.

### Task Dependencies

- T002 through T009 depend on T001 and edit the same test file, so complete them in order.
- T010 depends on T002 through T009.
- T011 depends on T010.
- T012 depends on T011.
- T013 depends on T012.
- T014 depends on T013.
- T015 depends on T014.
- T016 depends on T015.
- T017 depends on T016.
- T018 depends on T017.
- T019 and T020 depend on T018.
- T021 and T023 depend on T020.
- T022 depends on T019.
- T024 depends on T019 through T023.

---

## Parallel Opportunities

- T019 can run in parallel with preparation for T020 because it changes only the unique changelog fragment.
- T021, T022, and T023 can run in parallel after their stated dependencies because they are read-only validation tasks.
- Do not parallelize T002 through T018 because they share the focused test file or production file.

---

## Parallel Example: Final Validation

```text
Task: "Run python -m pytest tests/integration/test_menu_site_beacon_detail.py -v"
Task: "Run the changelog and public-symbol guardrails"
Task: "Run compile, Ruff, Black, and Mypy for the changed Python files"
```

---

## Implementation Strategy

### MVP First

1. Complete T001 through T010.
2. Confirm the new tests fail before any production edit.
3. Complete T011 through T014.
4. Stop and verify User Story 1 independently.

### Incremental Delivery

1. Add all focused regressions before production changes.
2. Add the identical PR #4068 local status-only helper shape in `site_client_exporter.py`.
3. Reject native integer HTTP failures before payload access.
4. Verify successful, compatibility, and exception-retry behavior.
5. Add the issue-specific changelog fragment.
6. Run the focused validation tasks.

## Notes

- Do not edit `src/operations/exporting/export/simple_endpoint_exporter.py`.
- Do not extract, inspect, format, or log response body details.
- Use only `status_code` and the response URL in the local failure helper.
- Use `the requested path` when the response URL is absent.
- Native returned HTTP 429 is terminal.
- Exception-based HTTP 429 keeps the existing adaptive retry.
- Do not edit `CHANGELOG.md`.

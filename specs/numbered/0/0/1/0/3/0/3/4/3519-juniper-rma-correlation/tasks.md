# Tasks: Juniper RMA Correlation for Mist Support Tickets

**Input**: Design documents from `specs/numbered/0/0/1/0/3/0/3/4/3519-juniper-rma-correlation/`

**Prerequisites**: [plan.md](plan.md) (required), [spec.md](spec.md) (required), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Requested. The constitution requires tests for new modules, and the spec requires offline tests (FR-031) and a read-only boundary test (SC-005).

**Organization**: Tasks are grouped by user story. Each story can be tested on its own.

## Format

`- [ ] Tnnn [P?] [USn?] Description with file path`

- `[P]` means the task can run in parallel. It touches different files and has no open dependency.
- `[USn]` names the user story. Setup, foundational, and polish tasks have no story label.
- Tick a task only after you verify the delivered file. Add the evidence note `(delivered: path)`.
- A task that needs a live system or a human decision stays unchecked. The task text states the condition.

## Path Conventions

- Source: `src/operations/exporting/juniper_rma/` (see plan.md, Project Structure).
- Tests: `tests/unit/juniper_rma/` (see plan.md, debt C-1).
- Feature documents: `specs/numbered/0/0/1/0/3/0/3/4/3519-juniper-rma-correlation/`.

---

## Phase 1: Setup

**Purpose**: Create the package layout and the reference inputs.

- [x] T001 Create the Feature Spec issue from `.github/ISSUE_TEMPLATE/feature-spec.yml` and link `specs/numbered/0/0/1/0/3/0/3/4/3519-juniper-rma-correlation/spec.md`. Add labels `feature`, `MistHelper.py`, `tests`, `docs`, and `in-progress`. Requires GitHub access. Checked when the issue exists. (delivered: issue #4139)
- [x] T002 [P] Create the package folders with `__init__.py` files: `src/operations/exporting/juniper_rma/`, `src/operations/exporting/juniper_rma/api/`, `src/operations/exporting/juniper_rma/model/`, `src/operations/exporting/juniper_rma/workflows/`, `tests/unit/juniper_rma/`, `tests/unit/juniper_rma/api/`, `tests/unit/juniper_rma/model/`, `tests/unit/juniper_rma/workflows/`, and `tests/unit/juniper_rma/fixtures/`. (delivered: src/operations/exporting/juniper_rma/ and tests/unit/juniper_rma/ package folders)
- [x] T003 [P] Extract each example body from `Export_JuniperServiceCaseAPI.json` and `Export_JuniperServiceAssetAPI.json` (in `C:\Users\jmorrison\Downloads\`) into `tests/unit/juniper_rma/fixtures/case/` (five files or fewer) and `tests/unit/juniper_rma/fixtures/asset/` (three files). Name each file for its source example. (delivered: eight synthetic replies in tests/unit/juniper_rma/fixtures/case (five) and fixtures/asset (three), shaped from the contract examples per amendment A-5; tests in tests/unit/juniper_rma/api/test_fixture_replies.py)
- [x] T004 [P] Add the Juniper names from `contracts/gateway-and-settings.md` to `deploy/.env.example` as commented lines with no values. (delivered: deploy/.env.example)
- [x] T005 Check whether `pyproject.toml` registers the pytest marker `live`. If it does not, register it there. The quickstart uses `pytest -m live`. (delivered: pyproject.toml)

---

## Phase 2: Foundational (Blocks All Stories)

**Purpose**: Settings, the gateway, the messages, the masking, and the key strategies. Every story uses these pieces.

**Checkpoint**: The gateway and messages pass their tests with the fake gateway before any story starts.

- [x] T006 Add six strategies to `ENDPOINT_PRIMARY_KEY_STRATEGIES` in `src/foundation/support/refactors/endpoint_primary_key_strategies.py`: `juniperQuerySrList`, `juniperQuerySrDetails`, `juniperQueryRmaDetails`, `juniperQueryAssetsDetails`, `juniperCorrelationLinks`, and `juniperRunRecords`. Use the key types in research R-15. (delivered: src/foundation/support/refactors/endpoint_primary_key_strategies.py; seven keys, see amendment A-4)
- [x] T007 [P] Implement `JuniperSettings` (dataclass) and `JuniperSettingsLoader` in `src/operations/exporting/juniper_rma/settings.py`. Validate the names, the HTTPS addresses, the host allowlist, and the numeric ranges. Report missing names only (FR-001 to FR-003). (delivered: src/operations/exporting/juniper_rma/settings.py)
- [x] T008 [P] Write `tests/unit/juniper_rma/api/test_settings.py`. Cover missing names, invalid ranges, non-HTTPS addresses, and the absence of secret values from every message (FR-003). (delivered: tests/unit/juniper_rma/api/test_settings.py)
- [x] T009 [P] Implement `PersonalDataMasker` in `src/operations/exporting/juniper_rma/model/export_rows.py` with the masking formats in research R-14. Include an ASCII-safe output function (FR-014, FR-029). (delivered: src/operations/exporting/juniper_rma/model/export_rows.py; ASCII function PersonalDataMasker.ascii_text)
- [x] T010 [P] Implement `RequestMessageBuilder` in `src/operations/exporting/juniper_rma/api/messages.py`. Build the request envelope. Set the UTC `requestDateTime` with milliseconds. Use a 32-character hex transaction identifier. Place `customerSourceID` and `customerUniqueTransactionID` as contract O-10 requires (FR-027). (delivered: src/operations/exporting/juniper_rma/api/messages.py)
- [x] T011 [P] Implement `ResponseStatusReader` in `src/operations/exporting/juniper_rma/api/messages.py`. Read the body `statusCode` and the `fault` list. Map each code from the two contracts to plain text (FR-026). (delivered: src/operations/exporting/juniper_rma/api/messages.py)
- [x] T012 Implement `JuniperGatewayClient` in `src/operations/exporting/juniper_rma/api/gateway.py`. Enforce HTTPS only and the host allowlist. Request an OAuth 2.0 token and send it as a bearer header. Refuse redirects. Apply the timeouts and the response size cap. Apply the token-bucket rate limit. Retry with a new identifier on each attempt. Verify TLS with `JUNIPER_CA_BUNDLE`. Log actions with structlog (FR-004, FR-005, FR-023 to FR-025, FR-029). (delivered: src/operations/exporting/juniper_rma/api/gateway.py; standard logging per amendment A-1)
- [x] T013 Write `tests/unit/juniper_rma/fixtures/fake_gateway.py`. It replays fixture responses by endpoint name and records each request. It makes no network call. (delivered: tests/unit/juniper_rma/fixtures/fake_gateway.py)
- [x] T014 Write `tests/unit/juniper_rma/api/test_gateway.py`. Cover redirect refusal and host refusal. Cover retries for transient errors only. Cover a new identifier on each attempt. Cover that the key never reaches a log line. Cover the rate limit. The same module covers `RequestMessageBuilder` and `ResponseStatusReader` (FR-004, FR-005, FR-024 to FR-027, FR-029). (delivered: tests/unit/juniper_rma/api/test_gateway.py and test_messages.py)

---

## Phase 3: User Story 1 - Verify Juniper Access (Priority: P1) MVP

**Goal**: An operator confirms access in one action (menu 301).

**Independent Test**: Run menu 301 with fixtures (no network). Remove one setting. Use a wrong identifier fixture. Each run gives a clear result.

- [x] T015 [US1] Implement `JuniperCaseService.check_access()` in `src/operations/exporting/juniper_rma/api/case_service.py`. It sends one list request for a one-day window and returns pass or the fault meaning. (delivered: src/operations/exporting/juniper_rma/api/case_service.py)
- [x] T016 [US1] Implement `AccessCheckWorkflow` in `src/operations/exporting/juniper_rma/workflows/access_check.py` for menu 301. It prints the pass or fail message, stops on a missing setting, and refuses live calls under test modes unless `JUNIPER_LIVE_TESTS=1` (FR-001, FR-031, FR-032). (delivered: src/operations/exporting/juniper_rma/workflows/access_check.py)
- [x] T017 [US1] Write `tests/unit/juniper_rma/workflows/test_access_check.py`. Cover a passing fixture, a missing setting, fault 735, and the test-mode refusal. Add one test with `@pytest.mark.live` that runs only when `JUNIPER_LIVE_TESTS=1` (FR-001 to FR-003). (delivered: tests/unit/juniper_rma/workflows/test_access_check.py)
- [x] T018 [US1] Write the access tests in `tests/unit/juniper_rma/api/test_case_service.py`. Cover the one-day window and the fault mapping for 707, 735, and 932 (FR-001). (delivered: tests/unit/juniper_rma/api/test_case_service.py)

**Checkpoint**: Menu 301 works offline with fixtures. Live checks wait for onboarding.

---

## Phase 4: User Story 2 - Correlate Mist Tickets with Juniper RMAs (Priority: P1)

**Goal**: One run links each Mist support ticket to its Juniper service requests and RMA details (menu 302).

**Independent Test**: Run menu 302 with fixtures for a known set of tickets. Check that each matched ticket shows the expected request number, RMA number, and tracking number.

- [x] T019 [US2] Implement the list and detail operations in `src/operations/exporting/juniper_rma/api/case_service.py`: `list_service_requests(window)`, `get_service_request(case number or request number)`, and `get_rma(request, case number, RMA number)`. (delivered: src/operations/exporting/juniper_rma/api/case_service.py)
- [x] T020 [P] [US2] Implement the parsers in `src/operations/exporting/juniper_rma/model/service_request.py` for requests, RMA records, and RMA items. Accept the variants in research R-09 (flat or nested address, malformed timestamps kept as text, wrapper keys present or absent) (FR-012, FR-013). (delivered: src/operations/exporting/juniper_rma/model/service_request.py)
- [x] T021 [P] [US2] Implement `RunRecord` in `src/operations/exporting/juniper_rma/model/run_record.py`. Track the counts, the status transitions in data-model.md, and the reason text (FR-016). (delivered: src/operations/exporting/juniper_rma/model/run_record.py)
- [x] T022 [P] [US2] Implement the row builders in `src/operations/exporting/juniper_rma/model/export_rows.py` for correlation rows, RMA item rows, and service request rows. Apply masking before a row leaves the model (FR-013, FR-014). (delivered: src/operations/exporting/juniper_rma/model/export_rows.py)
- [x] T023 [US2] Implement `MistTicketReader` in `src/operations/exporting/juniper_rma/workflows/correlation.py`. Call `listOrgTickets` with `duration="365d"` through mistapi. Resolve the organization with `ConfigUtils.get_cached_or_prompted_org_id()`. Return only `id`, `case_number`, `status`, `subject`, and `created_at` (FR-008). (delivered: src/operations/exporting/juniper_rma/workflows/correlation.py)
- [x] T024 [US2] Implement `CorrelationEngine` in `src/operations/exporting/juniper_rma/workflows/correlation.py`. Apply the exact join on the field named by `JUNIPER_TICKET_KEY_FIELD` (R-05). Produce the matched, ambiguous, and unmatched outcomes with a reason. For tickets older than 90 days, use a detail lookup by case number (R-06) (FR-009 to FR-011). (delivered: src/operations/exporting/juniper_rma/workflows/correlation.py)
- [x] T025 [US2] Add the RMA fan-out to `CorrelationEngine`. For each unique match, read the request details. Then read the details of each RMA in the request's RMA list (FR-012). (delivered: src/operations/exporting/juniper_rma/workflows/correlation.py)
- [x] T026 [US2] Implement `PersonalDataRetention` in `src/operations/exporting/juniper_rma/model/export_rows.py`. Delete stored personal fields older than `JUNIPER_PII_RETENTION_DAYS`. Return the count for the run record (FR-014). (delivered: src/operations/exporting/juniper_rma/model/export_rows.py (PersonalDataRetention))
- [x] T027 [US2] Implement `CorrelationWorkflow` in `src/operations/exporting/juniper_rma/workflows/correlation.py` for menu 302. Run the retention purge first. Log before and after each read and write. Write the outputs through `DataExporter.write_with_format_selection()` as listed in `contracts/menu-and-exports.md`. Print the summary line (FR-015, FR-016). (delivered: src/operations/exporting/juniper_rma/workflows/correlation.py)
- [x] T028 [US2] Register menu 302 in `src/foundation/support/utils/operation_registry.py` with category `interactive_safe` and skip reason "Requires Juniper settings". Add the dispatch line in `MistHelper.py` (C-2: only one open pull request may change this file). (delivered: src/foundation/support/utils/operation_registry.py; MistHelper.py)
- [x] T029 [P] [US2] Write `tests/unit/juniper_rma/model/test_service_request.py`. Cover the parser variants, a malformed timestamp, and an empty RMA list (FR-012, FR-013). (delivered: tests/unit/juniper_rma/model/test_service_request.py)
- [x] T030 [P] [US2] Write `tests/unit/juniper_rma/model/test_export_rows.py`. Cover the masking formats, ASCII-safe output, and the absence of unmasked personal fields in every row (FR-014, FR-029, SC-004). (delivered: tests/unit/juniper_rma/model/test_export_rows.py)
- [x] T031 [P] [US2] Write `tests/unit/juniper_rma/model/test_run_record.py`. Cover the status transitions and the counts (FR-016). (delivered: tests/unit/juniper_rma/model/test_run_record.py)
- [x] T032 [US2] Write `tests/unit/juniper_rma/workflows/test_correlation.py`. Cover a matched ticket. Cover an ambiguous ticket with fault 763 candidates. Cover an unmatched ticket with a reason. Cover one row for each RMA item. Cover a detail lookup for an older ticket. Cover an incomplete run after retries run out. Cover zero tickets (FR-009 to FR-012, SC-002, SC-003). (delivered: tests/unit/juniper_rma/workflows/test_correlation.py)
- [x] T033 [US2] Write `tests/unit/juniper_rma/workflows/test_read_only_boundary.py`. The test fails if a write operation name appears. The names come from the Case API: create, update, escalate, close, attach, and upload token. The test checks the client, the workflows, and the registry entries (FR-006, FR-007, SC-005). (delivered: tests/unit/juniper_rma/workflows/test_read_only_boundary.py)

**Checkpoint**: Menus 301 and 302 are the MVP. Correlation outputs match the contract.

---

## Phase 5: User Story 3 - Look Up One Service Request or RMA (Priority: P2)

**Goal**: An operator looks up one request, one case number, or one RMA (menu 303).

**Independent Test**: Look up a known request and a known RMA with fixtures. Each lookup shows the shipping details and the tracking numbers.

- [x] T034 [US3] Implement `LookupWorkflow` in `src/operations/exporting/juniper_rma/workflows/lookup.py` for menu 303. Accept a request number or a case number. Accept an RMA number only with one of those two values. Validate each input with `safe_input()` before any call. Report a number that Juniper does not know as not found (FR-017 to FR-019). (delivered: src/operations/exporting/juniper_rma/workflows/lookup.py)
- [x] T035 [US3] Register menu 303 in `src/foundation/support/utils/operation_registry.py` and add the dispatch line in `MistHelper.py`. (delivered: src/foundation/support/utils/operation_registry.py; MistHelper.py)
- [x] T036 [US3] Write `tests/unit/juniper_rma/workflows/test_lookups.py`. Cover a valid request lookup. Cover an RMA lookup that needs a request or case number. Cover a not-found result, which is not a fault. Cover an invalid input that the system rejects before any call (FR-017 to FR-019). (delivered: tests/unit/juniper_rma/workflows/test_lookups.py)

---

## Phase 6: User Story 4 - Add Asset and Warranty Data (Priority: P2)

**Goal**: An operator adds warranty, contract, and status data for serial numbers (menu 304).

**Independent Test**: Look up 350 serial numbers with fixtures. The lookup sends two batches and merges the results.

- [x] T037 [US4] Implement `JuniperAssetService.query_assets()` in `src/operations/exporting/juniper_rma/api/asset_service.py`. Send batches of 300 or fewer. Repeat the not-processed serials for up to three passes. Keep the invalid and not-found lists. Keep partial results when a later pass fails (FR-020 to FR-022). (delivered: src/operations/exporting/juniper_rma/api/asset_service.py; methods query_batch and query_all)
- [x] T038 [US4] Implement the asset parser in `src/operations/exporting/juniper_rma/model/asset.py`. Accept `rmaInfo` as an object or a list. Parse the warranty list and the contract list with its contract details (FR-020). (delivered: src/operations/exporting/juniper_rma/model/asset.py)
- [x] T039 [US4] Implement `AssetLookupWorkflow` in `src/operations/exporting/juniper_rma/workflows/asset_lookup.py` for menu 304. Validate the serial input. Batch the serials. Write `JuniperAssets.csv` and `JuniperAssetCoverage.csv` through `DataExporter` (FR-020, FR-022). (delivered: src/operations/exporting/juniper_rma/workflows/asset_lookup.py)
- [x] T040 [US4] Register menu 304 in `src/foundation/support/utils/operation_registry.py` and add the dispatch line in `MistHelper.py`. (delivered: src/foundation/support/utils/operation_registry.py; MistHelper.py)
- [x] T041 [P] [US4] Write `tests/unit/juniper_rma/api/test_asset_service.py`. Cover 350 serials in two batches. Cover the not-processed retry and the three-pass limit. Cover both response shapes, `data` and top level. Cover a batch of 300 or fewer (FR-020 to FR-022). (delivered: tests/unit/juniper_rma/api/test_asset_service.py)
- [x] T042 [P] [US4] Write `tests/unit/juniper_rma/model/test_asset.py`. Cover `rmaInfo` as an object and as a list, plus the warranty and contract parsing (FR-020). (delivered: tests/unit/juniper_rma/model/test_asset.py)
- [x] T043 [US4] Add the menu 304 cases to `tests/unit/juniper_rma/workflows/test_lookups.py`. Cover the not-found list and the export shape. (delivered: tests/unit/juniper_rma/workflows/test_lookups.py)

---

## Phase 7: Polish and Cross-Cutting Concerns

**Purpose**: Documentation, gates, the audit of the constitution rules, and the release path.

- [x] T044 Update `README.md`. Change the operation count and add four rows for menus 301 to 304. (delivered: README.md states 273 operations and lists four rows for menus 301 to 304, each linking to the generated menu reference from T045)
- [x] T045 Regenerate the menu reference. Run `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map`. Commit only the pages that changed. (delivered: documentation/menu_reference.md; documentation/wiki/Menu-Reference.md)
- [x] T046 Add one release-note fragment under `changelog.d/`. Name it by the pull request or the issue, as `changelog.d/README.md` explains. (delivered: changelog.d/2026-10-08-juniper-rma-correlation.md)
- [ ] T047 Point the SPECKIT block in `.github/copilot-instructions.md` to `specs/numbered/0/0/1/0/3/0/3/4/3519-juniper-rma-correlation/plan.md`. (open: main keeps its SPECKIT pointer to the active feature, so the pointer stays unchanged)
- [x] T048 Run the quality gates in plan.md. Start with ruff and black. Run mypy with `MYPY_PATHS`. Run pytest with at least 80 percent coverage on the new modules. Then run radon, pylint, interrogate, pydocstyle, bandit, pip-audit, and vulture. Use the thresholds in plan.md. (delivered: ruff, black, mypy, pytest (package coverage 92 percent), radon, pylint 9.87, interrogate, pydocstyle, bandit, pip-audit, vulture)
- [ ] T049 Run the STE linter on every Markdown file in `specs/numbered/0/0/1/0/3/0/3/4/3519-juniper-rma-correlation/`. Repair the findings with the `ste-writing` skill. (open: the gate floor passes and the spec files score 91 to 99, but 179 findings remain. They are 91 noun clusters, 43 long paragraphs, 25 passive voice sentences, 11 semicolons, 4 tense, 3 long sentences, and 2 warnings without a consequence. Repair them with the ste-writing skill, or accept them with a recorded decision.)
- [x] T050 Audit every new file. Confirm an inline comment on each executable line (Principle VI). Confirm an action log before and after each call and each write (Principle VII). (delivered: tokenizer audit: 0 production and 0 test statements without an inline comment)
- [x] T051 Scan a fixture run's logs and default exports for secret values, full email addresses, and full telephone numbers (SC-004). (delivered: SC-004 log scan: 0 e-mail, 0 synthetic personal, 0 credential values)
- [ ] T052 [After onboarding] Run menu 301 in the container with `deploy/compose.corporate-ca.yml` to confirm the TLS path (R-13). (open: needs onboarding)
- [ ] T053 [After onboarding] Replace the assumptions O-1 to O-10 with the confirmed values. Update the fixtures and the contracts. Record each outcome in `research.md`. (open: needs onboarding; the live check failed with fault 906)
- [ ] T054 File a separate remediation issue R-1 for `tests/unit/` (debt C-1). Do not implement it in this feature. (open: needs a GitHub issue, publication not authorized)
- [ ] T055 Run the full deployment pipeline (Principle IV). Commit the manifest, rebase on `origin/main`, push the branch, open the pull request with `Closes #<issue>`, pass CI, squash merge, and verify the image revision. (open: pipeline excluded by instruction)

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. T002, T003, and T004 can run in parallel.
- **Foundational (Phase 2)**: Depends on Phase 1. Blocks every story.
- **User Stories (Phases 3 to 6)**: Each depends on Phase 2. US3 also needs T019 and T020 from US2. US4 is independent of US2 except for the menu registry and dispatch.
- **Polish (Phase 7)**: Depends on the stories that ship in the release.

### Story Dependencies

- **US1 (P1)**: Needs T007 to T014 and T015. Independent of the other stories.
- **US2 (P1)**: Needs T006 to T014, T019 to T028. Independent of US1 after the foundation.
- **US3 (P2)**: Needs T019 and T020. Independent of US4.
- **US4 (P2)**: Needs T009 and T037 to T042. Independent of US2 and US3.

### Within Each Story

- Services before workflows.
- Parsers before correlation.
- Registry and dispatch after the workflow exists.
- Tests after the code they cover, and before the story checkpoint.

## Parallel Examples

```text
Phase 1:   T002, T003, T004 at the same time.
Phase 2:   T007 and T008 with T009, T010, and T011 after T006.
US2:       T020, T021, and T022 at the same time. Then T029, T030, and T031.
US4:       T041 and T042 at the same time after T037 and T038.
```

## Implementation Strategy

### MVP First (US1 and US2)

1. Complete Phases 1 and 2.
2. Complete Phase 3 (menu 301).
3. Complete Phase 4 (menu 302).
4. Stop and validate with the fixtures and the quickstart steps 1 to 4.
5. Confirm the onboarding items O-1 to O-4 before a production run.

### Incremental Delivery

1. The MVP delivers access checking and correlation.
2. Add US3 (menu 303) for one-off lookups.
3. Add US4 (menu 304) for warranty and contract data.
4. Run Phase 7 once for all shipped stories.

## Notes

- Keep each task to one file where possible.
- Every new Python function uses at most five parameters and at most 25 lines (Principle I).
- Every new executable line gets an inline comment (Principle VI).
- No task adds a write call to Juniper. T033 enforces this rule.
- Total tasks: 55. Setup 5. Foundational 9. US1 4. US2 15. US3 3. US4 7. Polish 12.

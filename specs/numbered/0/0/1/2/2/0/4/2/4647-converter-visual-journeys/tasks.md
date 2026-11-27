# Tasks: Add independently authored converter visual journeys

**Input**: Numeric record `specs/numbered/0/0/1/2/2/0/4/2/4647-converter-visual-journeys/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/contracts/` (required for the test IDs and the host), and `design/research.md` (required for the remote checks).

Status values are `open`, `verified-present`, `partial`, and `absent`. A task carries `[P]` only when it touches different files from every other open task.

## Phase 1: Preconditions

- [ ] T001 [FR-017, FR-019] Confirm the test layout before any edit.
  - Files: `tests/e2e/`, `tests/e2e/web_portal/`
  - Acceptance: `tests/e2e/` holds five entries (RC-47). `tests/e2e/web_portal/` holds 32 direct children (RC-48).
  - Verification: `python -m pytest tests/guardrails/test_e2e_package_structure.py`
  - Status: verified-present

- [ ] T002 [FR-001, FR-018, FR-020] Replace the isolated converter setup in the smoke module with the test host.
  - Files: `tests/e2e/web_portal/test_portal_smoke.py`
  - Acceptance: The `cisco_routes` import (RC-26) and the `cisco_client` alias leave the module. The test class builds the portal host with `WebPortalApp.create_app`, registers `ConverterRoutes.blueprint()` before the first request, serves on loopback, and stops the host (RC-44, RC-45). See `contracts/test-host.md`.
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py -k CiscoConverterJourneys`
  - Status: partial

## Phase 2: Presentation

- [ ] T003 [P] [FR-002, FR-004, FR-014] Rewrite the converter markup as independent HTML.
  - Files: `src/interfaces/portals/cisco_config_converter/presentation/converter.html`
  - Acceptance: The page extends the host base template (RC-08). It contains every ID in `contracts/portal-journey.md`, including `cisco-confirm`, `cisco-cancel`, and `cisco-reset`. The current IDs stay in place (RC-10, RC-11).
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py -k CiscoConverterJourneys`
  - Status: partial

- [ ] T004 [P] [FR-007, FR-009, FR-015, FR-016] Create the converter stylesheet.
  - Files: `src/interfaces/portals/cisco_config_converter/presentation/converter.css`
  - Acceptance: The file uses only `var(--portal-*)` tokens and a fallback focus color. It holds no color literal, no image reference, no font, and no `@keyframes` rule. It wraps long command text (RC-03, RC-35).
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py -k host_theme_tokens`
  - Status: absent

- [ ] T005 [FR-002, FR-003, FR-004, FR-005, FR-006, FR-010] Rewrite the converter script.
  - Files: `src/interfaces/portals/cisco_config_converter/presentation/converter.js`
  - Acceptance: The script renders the structured review with DOM text APIs (RC-12, RC-15). It keeps the generation guard (RC-13). It gates export on the exact word `EXPORT`. It handles cancel and reset (RC-14). It writes no browser storage (RC-15). It sends the CSRF header (RC-23).
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py -k CiscoConverterJourneys`
  - Status: partial

  Depends on T003 and T004.

## Phase 3: Journey tests

- [ ] T006 [FR-001, FR-002, FR-012, FR-014, FR-018] Add the structured review and typed export journey.
  - Files: `tests/e2e/web_portal/test_portal_smoke.py`
  - Acceptance: The test uses a synthetic file and the TEST-NET address `192.0.2.1` (RC-27 replaced). It checks the host theme switcher (RC-99), each control, the download name, and the storage rule (only `misthelper-theme`, RC-32).
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py -k structured_review_and_typed_export`
  - Status: absent

  Depends on T002, T003, and T005.

- [ ] T007 [FR-003, FR-004] Add the typed-word and reset journeys.
  - Files: `tests/e2e/web_portal/test_portal_smoke.py`
  - Acceptance: A wrong word keeps export disabled. Cancel clears the typed word and keeps the review. Reset and an input change clear the proposal and the review.
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py -k "typed_word or reset_and_input"`
  - Status: absent

  Depends on T006.

- [ ] T008 [FR-005, FR-013] Add the stale-response journey with a held route.
  - Files: `tests/e2e/web_portal/test_portal_smoke.py`
  - Acceptance: The first preview response stays held until the second response renders. The newer proposal remains visible after the older response arrives (RC-74, RC-75).
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py -k stale_preview_response`
  - Status: absent

  Depends on T006.

- [ ] T009 [FR-006, FR-013] Add the server failure journey with two mocked failures.
  - Files: `tests/e2e/web_portal/test_portal_smoke.py`
  - Acceptance: A JSON 500 and a non-JSON 502 each show a status that starts with `Error:`. No proposal appears, and the review control stays disabled (RC-16, RC-17).
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py -k server_failures`
  - Status: absent

  Depends on T006.

- [ ] T010 [FR-010] Add the markup-as-text journey.
  - Files: `tests/e2e/web_portal/test_portal_smoke.py`
  - Acceptance: A template name and a command line that contain markup appear as text. The test counts zero injected elements (SC-003).
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py -k markup_renders_as_text`
  - Status: absent

  Depends on T006.

- [ ] T011 [FR-007] Add the keyboard-only journey with a focus check.
  - Files: `tests/e2e/web_portal/test_portal_smoke.py`
  - Acceptance: Tab, Enter, and Space complete the journey. Each focused control shows a non-zero outline width in each shipped theme (RC-35 to RC-38).
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py -k keyboard_only_journey`
  - Status: absent

  Depends on T006.

- [ ] T012 [FR-008, FR-009] Add the shipped-theme and viewport matrix.
  - Files: `tests/e2e/web_portal/test_portal_smoke.py`
  - Acceptance: Eight cases run, one for each of the four shipped themes at the phone viewport and the desktop viewport (RC-34, RC-40). Each case shows zero horizontal overflow.
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py -k shipped_theme_at_viewport`
  - Status: absent

  Depends on T006.

- [ ] T013 [FR-011] Add the cloud guard journey.
  - Files: `tests/e2e/web_portal/test_portal_smoke.py`
  - Acceptance: The page-level route aborts each non-loopback request and counts it. A clean journey records zero such requests (SC-004).
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py -k cloud_guard`
  - Status: absent

  Depends on T006.

## Phase 4: Static and host checks

- [ ] T014 [FR-015, FR-016, FR-020] Add three non-browser checks.
  - Files: `tests/e2e/web_portal/test_portal_smoke.py`
  - Acceptance: The three checks pass. `test_presentation_uses_host_theme_tokens` finds no color literal. `test_presentation_adds_no_image_font_or_animation` finds no asset reference. `test_production_host_serves_no_converter_route` gets a 404 for `/cisco-config-converter/` (RC-30).
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py -k "host_theme_tokens or no_image_font or no_converter_route"`
  - Status: absent

  Depends on T002, T004.

- [ ] T015 [P] [FR-013] Confirm the failure evidence options in the CI command.
  - Files: `.github/workflows/ci.yml` (read only)
  - Acceptance: The browser command keeps `--screenshot only-on-failure` and `--tracing retain-on-failure` (RC-52). The shard guard still requires the tracing option (RC-55).
  - Verification: `python -m pytest tests/guardrails/test_e2e_shard_partition.py`
  - Status: verified-present

- [ ] T016 [FR-019] Run the existing smoke classes after the edit.
  - Files: `tests/e2e/web_portal/test_portal_smoke.py`
  - Acceptance: `TestDashboardPage`, `TestDataBrowserPage`, `TestOperationsPage`, `TestMapViewerPage`, `TestHealthEndpoint`, `TestAPIEndpoints`, and `TestLicensingComparisonPage` pass.
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py`
  - Status: open

  Depends on T006 to T014.

## Phase 5: Delivery

- [ ] T-LOCAL-GATES [FR-001 to FR-020] Run each local gate that applies to the changed files.
  - Files: `src/interfaces/portals/cisco_config_converter/presentation/converter.html`, `converter.js`, `converter.css`, and `tests/e2e/web_portal/test_portal_smoke.py`
  - Acceptance: Lint (RC-91) passes. Format (RC-92) passes. The Tests gate (RC-93) passes for the changed test file. The test quality gate (RC-95) reports zero new findings. The STE gate (RC-94) is not applicable because no listed document changes. The compile, complexity, bandit, symbol, and type gates are not applicable because no production Python changes. Each result is recorded in the pull request body.
  - Verification: `python -m ruff check .`
  - Status: open

  Depends on T016.

- [ ] T-PR [FR-020] Commit, push, and open the pull request.
  - Files: `changelog.d/issue-4647-converter-visual-journeys.md`
  - Acceptance: The branch is `feat/4647-converter-visual-journeys` (RC-85). The commit and the pull request title use the form `feat(web-portal): add converter visual journeys` (RC-98). The body contains `Closes #4647` (RC-88). The fragment names issue 4647.
  - Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
  - Status: open

  Depends on T-LOCAL-GATES.

- [ ] T-REMOTE-CI [FR-013, SC-005] Watch the remote checks.
  - Files: none changed
  - Acceptance: The `E2E smoke tests` check and every required check pass on the latest commit (RC-89). The `web_portal` shard stays within 20 minutes (RC-54). The run keeps artifacts for failed tests only.
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py`
  - Status: open

  Depends on T-PR.

- [ ] T-MERGE [FR-017, FR-020] Merge through the serial merge slot.
  - Files: none changed
  - Acceptance: The orchestrator authorizes the merge. The branch is current with `main`, and no other merge is in progress (RC-97). The `auto-merge` label is added only after every check is green (RC-89). The squash merge is the only merge type (RC-90). After the merge, `tests/guardrails/test_e2e_package_structure.py` still passes on `main`.
  - Verification: `python -m pytest tests/guardrails/test_e2e_package_structure.py`
  - Status: open

  Depends on T-REMOTE-CI and the orchestrator authorization.

## Dependencies and execution order

- T001 runs first. T002 depends on T001.
- T003 and T004 run in parallel after T002.
- T005 depends on T003 and T004.
- T006 depends on T002, T003, and T005. T007 to T013 depend on T006 and can run in any order.
- T014 depends on T002 and T004.
- T015 runs in parallel with any task.
- T016 depends on T006 to T014.
- T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run in order.
- External prerequisites: issues #4636, #4641, and #4642 merge before T002 starts (AS-001 in `spec.md`).

## Requirement coverage

Every FR maps to at least one task and at least one test. The full matrix is in `analysis.md`.

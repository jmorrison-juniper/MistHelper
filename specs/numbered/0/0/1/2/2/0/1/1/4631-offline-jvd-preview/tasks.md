# Tasks: Offline Dynamic JVD Labs Preview

**Input**: Design documents in `specs/numbered/0/0/1/2/2/0/1/1/4631-offline-jvd-preview/`.

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/contracts/`, and `design/quickstart.md`.

**Tests**: Required by FR-018 and SC-001. Write each test module before its source task. Confirm the import failure first.

**Ownership**: No task edits `web_portal/app.py` or `web_portal/templates/base.html` before the shared-file handover. T013 and T014 wait for it.

**Format**: `[P]` means the task edits a different file and can run in parallel. Each task lists its requirements, paths, acceptance, verification, and status.

**Status meanings**: `open` means an action is pending. `absent` means the artifact is not on `main` yet. `verified-present` means the artifact exists and passed its check.

## Phase 1: Setup

- [ ] T001 Claim issue #4631 with `in-progress`. Create `feat/4631-offline-jvd-preview` from `main`.
  - Requirements: FR-023 (process).
  - Paths: none.
  - Acceptance: The branch starts from `main`. The branch name follows the Branch Naming rule (R-49).
  - Verification: `python -m py_compile MistHelper.py`
  - Status: open

## Phase 2: Tests First

- [ ] T002 [P] Create `tests/integration/web_portal/labs/__init__.py` as the package marker.
  - Requirements: FR-025.
  - Paths: `tests/integration/web_portal/labs/__init__.py`.
  - Acceptance: The file has a module docstring and an inline comment for each executable line. The folder holds five children after T006.
  - Verification: `python -m ruff check .`
  - Status: absent

- [ ] T003 [P] Create `tests/integration/web_portal/labs/harness.py` with the synthetic fixtures and `build_labs_test_app`.
  - Requirements: FR-018, FR-017.
  - Paths: `tests/integration/web_portal/labs/harness.py`.
  - Acceptance: The file defines three synthetic results from `design/contracts/synthetic-fixtures.md`. `build_labs_test_app` calls `WebPortalApp.create_app` with `apisession=None`. The helper sets `PORTAL_TITLE` and `PORTAL_THEME` only when absent. It registers the Labs blueprint only when the factory does not. Teardown calls `WebPortalApp.shutdown_app`.
  - Verification: `python -m ruff check .`
  - Status: absent

- [ ] T004 Create `tests/integration/web_portal/labs/test_labs_units.py` with tests TU-01 to TU-14 in classes.
  - Requirements: FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-020, FR-022.
  - Paths: `tests/integration/web_portal/labs/test_labs_units.py`.
  - Acceptance: Classes `TestRunNameForm`, `TestPlanResultProjector`, `TestFingerprint`, `TestPlannerGateway`, and `TestPackageBoundary` hold the tests. The module fails with `ModuleNotFoundError` before T008 and T009.
  - Verification: `python -m pytest tests/integration/web_portal/labs/test_labs_units.py`
  - Status: absent

- [ ] T005 Create `tests/integration/web_portal/labs/test_labs_routes.py` with tests TR-01 to TR-12 in one class.
  - Requirements: FR-001 to FR-009, FR-010, FR-012, FR-014, FR-019, FR-020, FR-021, FR-026.
  - Paths: `tests/integration/web_portal/labs/test_labs_routes.py`.
  - Acceptance: The class `TestLabsRoutes` uses the module-scoped client from `harness.py`. The module fails before T011 with the route results missing.
  - Verification: `python -m pytest tests/integration/web_portal/labs/test_labs_routes.py`
  - Status: absent

- [ ] T006 Create `tests/integration/web_portal/labs/test_labs_browser.py` with tests TB-01 to TB-03.
  - Requirements: FR-021, FR-026.
  - Paths: `tests/integration/web_portal/labs/test_labs_browser.py`.
  - Acceptance: Each test skips with a stated cause when Chromium is absent. The failed-step test writes a screenshot to `test-artifacts/labs-preview/`.
  - Verification: `python -m pytest tests/integration/web_portal/labs/test_labs_browser.py`
  - Status: absent

## Phase 3: Source Package

- [ ] T007 [P] Create `src/interfaces/labs/__init__.py` with a module docstring.
  - Requirements: FR-025.
  - Paths: `src/interfaces/labs/__init__.py`.
  - Acceptance: The file exports nothing. Each executable line has an inline comment.
  - Verification: `python -m ruff check .`
  - Status: absent

- [ ] T008 [P] Create `src/interfaces/labs/run_name_form.py` with `RUN_NAME_PATTERN`, `RunNameRejection`, and `RunNameForm`.
  - Requirements: FR-008, FR-009, FR-010.
  - Paths: `src/interfaces/labs/run_name_form.py`.
  - Acceptance: `RunNameForm.parse` accepts exactly `run_name` and `csrf_token`. It rejects other fields and repeated `run_name` fields. It validates the pattern in `design/data-model.md` with `re.fullmatch`. The module holds three top-level names.
  - Verification: `python -m pytest tests/integration/web_portal/labs/test_labs_units.py`
  - Status: absent

- [ ] T009 [P] Create `src/interfaces/labs/planner.py` with `PlannerOutcome`, `PlannerGateway`, `PlanResultProjector`, and `SERVER_EXAMPLE`.
  - Requirements: FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-020, FR-022.
  - Paths: `src/interfaces/labs/planner.py`.
  - Acceptance: The gateway imports `vmm_topology` inside its method. Absence reports `absent`. Other failures report `failed`. The projector applies the allow-list in `design/contracts/plan-result.md`. The fingerprint follows D-13. The module holds four top-level names. The module imports no Mist or provider module.
  - Verification: `bandit -c pyproject.toml -r src/interfaces/labs -q`
  - Status: absent

- [ ] T010 [P] Create `src/interfaces/labs/presentation/labs_page.html` with the stable `data-testid` values.
  - Requirements: FR-004, FR-005, FR-006, FR-021, FR-026.
  - Paths: `src/interfaces/labs/presentation/labs_page.html`.
  - Acceptance: The template follows `design/contracts/labs-page.md`. Jinja autoescape stays on. The template renders `csrf_token()` in the form. The copy uses plain ASCII words.
  - Verification: `python -m pytest tests/integration/web_portal/labs/test_labs_routes.py`
  - Status: absent

- [ ] T011 Create `src/interfaces/labs/routes.py` with `LABS_URL_PREFIX` and `LabsBlueprintFactory`.
  - Requirements: FR-001, FR-002, FR-003, FR-004, FR-007, FR-011, FR-014, FR-019.
  - Paths: `src/interfaces/labs/routes.py`.
  - Acceptance: The factory creates the blueprint `labs` with URL prefix `/labs` and the template folder `presentation`. The factory checks `"csrf" in app.extensions` and fails at registration when absent. It defines three routes only. Each view logs an info line before its action and a debug line after it.
  - Verification: `python -m pytest tests/integration/web_portal/labs/test_labs_routes.py`
  - Status: absent

## Phase 4: Changelog

- [ ] T012 [P] Create `changelog.d/issue-4631-offline-jvd-preview.md` with one `###` heading and one bullet.
  - Requirements: FR-024.
  - Paths: `changelog.d/issue-4631-offline-jvd-preview.md`.
  - Acceptance: The heading names the change type `Added`. The bullet names issue #4631. The file holds no version stamp.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
  - Status: absent

## Phase 5: Shared-File Integration (Blocked)

- [ ] T013 Register the Labs blueprint in `web_portal/app.py` after the registrations on lines 200 to 207.
  - Requirements: FR-001, FR-023.
  - Paths: `web_portal/app.py`.
  - Acceptance: The change adds one import and one `register_blueprint` call. No other line changes. The change waits for the shared-file handover.
  - Verification: `symbol-diff --base origin/main web_portal/app.py`
  - Status: absent (blocked by the shared-file handover)

- [ ] T014 Add the `nav-labs` anchor in `web_portal/templates/base.html` after the `nav-websockets` anchor on line 74.
  - Requirements: FR-021, FR-023.
  - Paths: `web_portal/templates/base.html`.
  - Acceptance: The anchor uses `url_for('labs.page')`, `data-testid="nav-labs"`, and the label "Labs preview". The change waits for the shared-file handover. T013 merges first.
  - Verification: `python -m pytest tests/integration/web_portal/labs/test_labs_routes.py`
  - Status: absent (blocked by the shared-file handover)

- [ ] T015 Add one Labs row to the Open a portal table in `documentation/operator-guide.md`.
  - Requirements: FR-024.
  - Paths: `documentation/operator-guide.md`.
  - Acceptance: The row names `<http://127.0.0.1:8055/labs/>` and states that the page contacts no Mist cloud, device, or provider. The row follows T013.
  - Verification: `python -m pytest tests/guardrails/test_markdown_links.py`
  - Status: absent (blocked by T013)

## Phase 6: Gates and Delivery

- [ ] T-LOCAL-GATES Run each gate in the local gates table that applies to the changed files.
  - Requirements: FR-001 to FR-026.
  - Paths: every path in the file change map.
  - Acceptance: Each applicable gate exits 0. Record the examined count of each gate. Mark each gate not applicable with its reason in `design/quickstart.md`. Run the gates listed in `design/quickstart.md`.
  - Verification: the commands in `design/quickstart.md`, section "Run the gates".
  - Status: open

- [ ] T-PR Commit with a Conventional Commits message. Push the branch. Open the pull request.
  - Requirements: FR-023, FR-024, and the full record.
  - Paths: every changed path.
  - Acceptance: The title is `feat(web-portal): add offline Dynamic JVD Labs preview`. The body contains `Closes #4631`, the files summary, the gate results, and the rollback notes. The body follows `.github/PULL_REQUEST_TEMPLATE.md` (R-82). Record the number as `PULL_REQUEST_NUMBER`.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
  - Status: open

- [ ] T-REMOTE-CI Watch the remote checks of the pull request until each check ends.
  - Requirements: FR-001 to FR-026.
  - Paths: none.
  - Acceptance: Each required check reports success. A failed check stops the task until a fix commit passes. Each root-shard test runs under `tests/integration`.
  - Verification: `gh pr checks $PULL_REQUEST_NUMBER --watch`
  - Status: open

- [ ] T-MERGE Squash-merge the pull request after review and authorization.
  - Requirements: FR-023 and Principle IV steps 9 to 11 (R-47).
  - Paths: none.
  - Acceptance: A human clears `needs-human-review`. The orchestrator authorizes the merge. Add `auto-merge` only after each check passes (R-50). After the merge, wait for `container-build.yml` on the merged revision. The image revision label equals the merge commit. Deployment waits for the orchestrator.
  - Verification: `gh pr view $PULL_REQUEST_NUMBER --json state,mergedAt`
  - Status: open

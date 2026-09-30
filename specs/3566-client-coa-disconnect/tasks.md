# Tasks: Client CoA Disconnect

**Input**: Design artifacts from `specs/3566-client-coa-disconnect/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/client-session-control.md`, `quickstart.md`, and `wiring.md`

**Tests**: Required. Each acceptance criterion has a no-network unit test.

**Organization**: Tasks are grouped so each group can commit independently.

## Phase 1: Research Verification

- [X] T001 Read `src/device/` helper files before code work starts.
- [X] T002 Record the existing MAC normalization and client lookup findings in `research.md`.
- [X] T003 Verify these operation IDs in `documentation/mist-api-openapi3json.json`: `reauthSiteDot1xWirelessClient`, `reauthSiteDot1xWiredClient`, `reauthOrgDot1xWirelessClient`, `reauthOrgDot1xWiredClient`, `disconnectSiteWirelessClient`, `unauthorizeSiteWirelessClient`, and `deauthSiteWirelessClientsConnectedToARogue`.
- [X] T004 Verify the same seven operation IDs in installed `mistapi` with `C:\Users\jmorrison\mh-fleet\3566-client-coa-disconnect\.venv\Scripts\python.exe`.
- [X] T005 Commit the updated research artifacts.

## Phase 2: Wiring Manifest

- [X] T006 Update `specs/3566-client-coa-disconnect/wiring.md` to include every exact section from the fleet contract.
- [X] T007 Add menu 286 with category `destructive`, handler import, handler attribute, skip reason, destructive flag, and `supports_fast` value.
- [X] T008 State that `MistHelper.py` registration is deferred to the integration pull request.
- [X] T009 Describe the `--dry-run` handler lambda pattern that passes `dry_run` to `ClientSessionControl.run()`.
- [X] T010 Commit the wiring manifest update.

## Phase 3: Test Scaffolding

- [X] T011 Create `tests/unit/device/client_session_control/__init__.py`.
- [X] T012 Create `tests/unit/device/client_session_control/test_client_session_control_confirmation.py` for exact confirmation tests.
- [X] T013 Create `tests/unit/device/client_session_control/test_client_session_control_dry_run.py` for dry run tests.
- [X] T014 Create `tests/unit/device/client_session_control/test_client_session_control_log.py` for CSV audit tests.
- [X] T015 Create `tests/unit/device/client_session_control/test_client_session_control_normalization.py` for colon, hyphen, dotted, bare, and invalid MAC tests.
- [X] T016 Create `tests/unit/device/client_session_control/test_client_session_control_wiring.py` for destructive registration and deferred wiring proof.
- [X] T017 Commit the failing test scaffold after confirming it fails for missing implementation.

## Phase 4: Package Implementation

- [X] T018 Create `src/device/client_session_control/__init__.py`.
- [X] T019 Create `src/device/client_session_control/models.py` with dataclasses and pure functions for target normalization, confirmation, request records, and log rows.
- [X] T020 Create `src/device/client_session_control/actions.py` with the action catalog and Mist API client class.
- [X] T021 Create `src/device/client_session_control/audit.py` with the CSV audit writer.
- [X] T022 Create `src/device/client_session_control/handler.py` with class `ClientSessionControl` and static `run()`.
- [X] T023 Ensure each executable line of new code has an inline comment.
- [X] T024 Ensure the package logs before and after prompts, validation, API calls, dry runs, and CSV writes.
- [X] T025 Commit the package implementation after the focused tests pass.

## Phase 5: Release Note

- [X] T026 Add `changelog.d/issue-3566-client-coa-disconnect.md` with one `### Added` heading and one bullet that names issue #3566.
- [X] T027 Commit the release note.

## Phase 6: Quality Gates

- [ ] T028 Run `C:\Users\jmorrison\mh-fleet\3566-client-coa-disconnect\.venv\Scripts\python.exe -m py_compile src\device\client_session_control\__init__.py src\device\client_session_control\models.py src\device\client_session_control\actions.py src\device\client_session_control\audit.py src\device\client_session_control\handler.py`.
- [ ] T029 Run `C:\Users\jmorrison\mh-fleet\3566-client-coa-disconnect\.venv\Scripts\python.exe -m ruff check src\device\client_session_control tests\unit\device\client_session_control`.
- [ ] T030 Run `C:\Users\jmorrison\mh-fleet\3566-client-coa-disconnect\.venv\Scripts\python.exe -m black --check src\device\client_session_control tests\unit\device\client_session_control`.
- [ ] T031 Run `C:\Users\jmorrison\mh-fleet\3566-client-coa-disconnect\.venv\Scripts\python.exe -m mypy src\device\client_session_control --config-file pyproject.toml`.
- [ ] T032 Run `C:\Users\jmorrison\mh-fleet\3566-client-coa-disconnect\.venv\Scripts\python.exe -m pydocstyle src\device\client_session_control`.
- [ ] T033 Run `C:\Users\jmorrison\mh-fleet\3566-client-coa-disconnect\.venv\Scripts\python.exe -m pytest tests\unit\device\client_session_control -q --timeout=120`.
- [ ] T034 Run `C:\Users\jmorrison\mh-fleet\3566-client-coa-disconnect\.venv\Scripts\python.exe -m vulture src\device\client_session_control --min-confidence 70`.
- [ ] T035 Run `C:\Users\jmorrison\mh-fleet\3566-client-coa-disconnect\.venv\Scripts\python.exe -m interrogate -v src\device\client_session_control`.
- [ ] T036 Commit any repairs from the quality gates.

## Phase 7: Analyze, Push, and Pull Request

- [ ] T037 Run the SpecKit analyze step against `specs/3566-client-coa-disconnect/`.
- [ ] T038 Repair each analyze finding and commit the repairs.
- [ ] T039 Push the branch after implementation gates pass.
- [ ] T040 Push once more after analyze repairs land.
- [ ] T041 Write `specs/3566-client-coa-disconnect/pr-body.md` with `Closes #3566`, the file list, the destructive operation warning, and the deferred wiring note.
- [ ] T042 Open a draft pull request against `main`.
- [ ] T043 Add labels `feature`, `src`, and `tests`.

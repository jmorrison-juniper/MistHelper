# Tasks: Upgrade Portal Session Recovery

**Input**: `plan.md`, `spec.md`, and the design documents under `design/`.

**Format**: Each task names its requirements, exact paths, an acceptance statement, one verification command, and a status. Status values are `open`, `verified-present`, `partial`, and `absent`. A task marked `[P]` can execute in parallel with other `[P]` tasks that touch different files.

**Tests**: Tests are required by the constitution and the spec. The planned tests use IDs TP-01 to TP-28 in the table at the end of this file.

## Phase 0: Gates and Coordination

### T001 Record human approval of decisions D-1 and D-2

- **Requirements**: FR-009, FR-022
- **Files**: none. The approval appears as a comment on issue #3714.
- **Acceptance**: The issue states approval, or a changed option, for D-1 and D-2. The approval names the recommended option or a different option.
- **Verification**: `gh issue view 3714 -R jmorrison-juniper/MistHelper --json comments --jq ".comments[-1].body"`
- **Status**: open

### T002 Confirm the handoff for the reserved contract test file

- **Requirements**: FR-023
- **Files**: `tests/contract/upgrade_portal/test_no_credential_leak.py` (not edited by this feature)
- **Acceptance**: Issue #2708 states a handoff or a closure for the file. Until then, no task edits the file.
- **Verification**: `gh issue view 2708 -R jmorrison-juniper/MistHelper --json state,updatedAt`
- **Status**: open

### T003 Check open pull request overlap before editing shared files

- **Requirements**: FR-020
- **Files**: `deploy/.env.example`, `compose.yml`
- **Acceptance**: Draft PR #4208 no longer changes `deploy/.env.example`, or the owner of PR #4208 agrees to the edit. Each planned file has no other open pull request.
- **Verification**: `gh pr list -R jmorrison-juniper/MistHelper --state open --limit 100 --json number,title,files`
- **Status**: open

### T004 Measure the protected handlers on the implementation base

- **Requirements**: FR-015
- **Files**: `src/interfaces/portals/upgrade_portal/app/routes/*.py` (read only)
- **Acceptance**: The count of `@identity.require_session` decorators equals 51. The per-file counts match RC-23 to RC-29 in `design/research.md`.
- **Verification**: `git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" grep -c "@identity.require_session" -- src/interfaces/portals/upgrade_portal/app/routes`
- **Status**: verified-present (measured on remote main `f03c6c9`, total 51)

## Phase 1: Store Foundation

### T005 [P] Add the shared session store boundary

- **Requirements**: FR-001, FR-002, FR-003, FR-004, FR-014
- **Files**: `src/interfaces/portals/upgrade_portal/persistence/session_store.py` (add)
- **Acceptance**: The class `SessionRecordStore` derives the key from a SHA-256 digest of the owner key. It encrypts with `MultiFernet`. It writes with `EX` set to the remaining absolute lifetime. It reads, writes, and deletes one key each. Typed errors cover missing, undecryptable, and unavailable states. Each executable line has an inline comment. Each store action logs before and after.
- **Verification**: `python -m ruff check src\interfaces\portals\upgrade_portal\persistence\session_store.py`
- **Status**: absent

### T006 [P] Add and validate the session settings

- **Requirements**: FR-013, FR-019, FR-022
- **Files**: `src/interfaces/portals/upgrade_portal/app/config.py` (modify), `tests/unit/upgrade_portal/test_config.py` (modify, with T006 tests TP-15 to TP-17 and TP-26)
- **Acceptance**: The settings `CAPTURE_SESSION_ENCRYPTION_KEY`, `CAPTURE_SESSION_ENCRYPTION_KEY_PREVIOUS`, `CAPTURE_SESSION_TTL_SECONDS`, and `CAPTURE_SESSION_IDLE_SECONDS` load with the defaults in `design/contracts/settings.md`. Invalid values raise `SettingsError`. A container start without the key raises `SettingsError`. A container start with the compose default Redis password raises `SettingsError` when D-2 is approved.
- **Verification**: `python -B -m pytest -p no:cacheprovider -q tests\unit\upgrade_portal\test_config.py`
- **Status**: open

### T007 Build the store in the application factory

- **Requirements**: FR-019
- **Files**: `src/interfaces/portals/upgrade_portal/app/factory.py` (modify)
- **Acceptance**: `create_app` builds one `SessionRecordStore` for each application. The factory injects the recovery builder and a clock into the identity module. Teardown closes the store client. The module keeps the existing lock client unchanged.
- **Verification**: `python -B -m pytest -p no:cacheprovider -q tests\unit\upgrade_portal\test_factory_route_registration.py`
- **Status**: open

### T008 [P] Declare the variables in compose and the environment template

- **Requirements**: FR-019, FR-020, FR-022
- **Files**: `compose.yml` (modify, `misthelper` environment block, lines 96 to 112), `deploy/.env.example` (modify)
- **Acceptance**: `compose.yml` requires `CAPTURE_SESSION_ENCRYPTION_KEY` with the same pattern as `CAPTURE_SECRET_KEY` at line 109. The optional lifetime variables use defaults. `deploy/.env.example` documents each variable and holds no value. Task T003 completes first.
- **Verification**: `python -B -m pytest -p no:cacheprovider -q tests\guardrails\test_container_policy_docs.py`
- **Status**: open

## Phase 2: Identity and Sign-In

### T009 Recover, expire, and delete sessions in the identity guard

- **Requirements**: FR-005, FR-006, FR-007, FR-008, FR-009, FR-011, FR-012, FR-013, FR-017, FR-024
- **Files**: `src/interfaces/portals/upgrade_portal/runtime/identity.py` (modify)
- **Acceptance**: A registry hit keeps the current path. A registry miss reads the store record for the owner key. The guard checks the browser digest, the mode, both deadlines, and the token name returned by the cloud. Any failure deletes the record and returns `401`. A store read failure returns `503 session_store_unavailable`. The idle refresh runs at most once each 60 seconds. `sign_out` deletes the store record. The page redirect keeps status 303.
- **Verification**: `python -B -m pytest -p no:cacheprovider -q tests\unit\upgrade_portal\test_identity.py`
- **Status**: open

### T010 Write the store record at environment token sign-in

- **Requirements**: FR-001, FR-006, FR-009, FR-010, FR-024
- **Files**: `src/interfaces/portals/upgrade_portal/app/routes/auth.py` (modify)
- **Acceptance**: `sign_in_with_environment_token` writes the store record before the registry registration. A failed write returns `503 session_store_unavailable` and registers no session. Browser token and provider login paths do not write a record. The provider login builder and the browser token builder keep their current behavior.
- **Verification**: `python -B -m pytest -p no:cacheprovider -q tests\contract\upgrade_portal\test_auth.py`
- **Status**: open

### T011 Confirm that no route module and no capture command changes

- **Requirements**: FR-015, FR-018
- **Files**: `src/interfaces/portals/upgrade_portal/app/routes/` (read only), `container/scripts/start.sh` (read only)
- **Acceptance**: `git diff --name-only origin/main` lists no file under `app/routes/` except `auth.py`. It lists no change to `container/scripts/start.sh`.
- **Verification**: `git diff --name-only origin/main -- src/interfaces/portals/upgrade_portal/app/routes container/scripts/start.sh`
- **Status**: open

## Phase 3: Tests and Documentation

### T012 [P] Replace the defect checks and add the store unit tests

- **Requirements**: FR-016, FR-013, FR-007, FR-008, FR-012
- **Files**: `tests/unit/upgrade_portal/test_identity.py` (modify, lines 1505 to 1520 and line 1647, plus new test functions)
- **Acceptance**: The check at lines 1505 to 1520 asserts recovery for a stored record and refusal for a missing record. The check at line 1647 asserts that sign-out after recovery returns True. The new tests TP-01 to TP-14 and TP-25 pass. The tests use an in-memory store double and an injected clock.
- **Verification**: `python -B -m pytest -p no:cacheprovider -q tests\unit\upgrade_portal\test_identity.py`
- **Status**: partial (the defect checks exist at lines 1505 to 1520 and 1647, and the replacement is absent)

### T013 [P] Add the restart contract for each credential mode

- **Requirements**: FR-001, FR-006, FR-009, FR-010, FR-011, FR-017
- **Files**: `tests/contract/upgrade_portal/test_auth.py` (modify, new tests TP-18 to TP-21)
- **Acceptance**: Application A authenticates with synthetic cloud transport. Application B uses the same signing key and the same store double. Application B returns 200 for the environment token cookie. It returns 401 for browser token and provider login cookies. A store outage returns 503 on a JSON request and on a page request. A page request without a session returns 303 to `/auth/signin`.
- **Verification**: `python -B -m pytest -p no:cacheprovider -q tests\contract\upgrade_portal\test_auth.py`
- **Status**: absent

### T014 Add the redaction and payload contract

- **Requirements**: FR-002, FR-005, FR-014
- **Files**: `tests/contract/upgrade_portal/test_security.py` (modify, new test TP-22)
- **Acceptance**: Synthetic token values, the encryption key, and the browser identifier never appear in logs or response bodies. They also never appear in cookies beyond the owner key or in the decrypted payload. The stored value holds no plaintext field with a credential.
- **Verification**: `python -B -m pytest -p no:cacheprovider -q tests\contract\upgrade_portal\test_security.py -k redaction`
- **Status**: absent

### T015 Add the guard count, worker, and documentation contracts

- **Requirements**: FR-015, FR-018, FR-021
- **Files**: `tests/contract/upgrade_portal/test_security.py` (modify, new tests TP-23, TP-24, TP-27)
- **Acceptance**: TP-23 finds 51 decorated handlers. TP-24 finds `--workers 1` and no `--max-requests` in the capture command. TP-27 finds the restart statement for each credential mode in `documentation/upgrade_capture_portal.md`.
- **Verification**: `python -B -m pytest -p no:cacheprovider -q tests\contract\upgrade_portal\test_security.py`
- **Status**: absent

### T016 Update the operator guide

- **Requirements**: FR-020, FR-021
- **Files**: `documentation/upgrade_capture_portal.md` (modify, lines 128 to 134 and 181 to 192)
- **Acceptance**: The environment table lists the four new variables with defaults and ranges. The credential mode section states the restart result for each mode. The text states that the portal stores no token. The text names the one-time sign-in at deployment. The text uses approved STE sentences.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 documentation\upgrade_capture_portal.md`
- **Status**: open

### T017 [P] Add the release note fragment

- **Requirements**: FR-020
- **Files**: `changelog.d/issue-3714-portal-session-recovery.md` (add)
- **Acceptance**: The fragment has one `### Security` heading and one bullet. The bullet names issue #3714 and states the recovery result.
- **Verification**: `python -B -m pytest -p no:cacheprovider -q tests\guardrails\test_changelog_fragment_policy.py`
- **Status**: absent

## Phase 4: Delivery

### T-LOCAL-GATES Run every applicable local gate

- **Requirements**: SC-007, SC-008
- **Files**: every changed file in T005 to T017
- **Acceptance**: Each applicable gate in `design/quickstart.md` prints its expected result. The diff check TP-28 passes. Gates that do not apply state the reason in the pull request body.
- **Verification**: the commands in `design/quickstart.md`, section "Gate commands"
- **Status**: open

### T-PR Commit and open the pull request

- **Requirements**: SC-007
- **Files**: the branch `fix/3714-upgrade-portal-session-recovery`
- **Acceptance**: The commit subject is `fix(portal): recover operator sessions after worker replacement`. The body contains `Closes #3714` and the co-author trailer. The pull request title uses the same subject. The body lists the gate results and the reason for each skipped gate.
- **Verification**: `gh pr view <number> -R jmorrison-juniper/MistHelper --json title,body --jq ".body"`
- **Status**: open

### T-REMOTE-CI Watch the remote checks

- **Requirements**: SC-008
- **Files**: the pull request from T-PR
- **Acceptance**: Every required check reports success on the latest commit. CodeQL completes before the `auto-merge` label is added.
- **Verification**: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch`
- **Status**: open

### T-MERGE Enable auto-merge after authorization

- **Requirements**: SC-007, SC-008
- **Files**: the pull request from T-PR
- **Acceptance**: The orchestrator authorizes the merge. The `auto-merge` label is added only after T-REMOTE-CI passes. The pull request merges as one squash commit.
- **Verification**: `gh pr view <number> -R jmorrison-juniper/MistHelper --json state,mergedAt,labels`
- **Status**: open

## Dependencies

- T005 depends on T001 and T003.
- T006 depends on T001.
- T007 depends on T005 and T006.
- T008 depends on T003 and T006.
- T009 depends on T005 and T007.
- T010 depends on T007 and T009.
- T011 depends on T009 and T010.
- T012 depends on T009. T012 and T013 execute in parallel because they edit different files.
- T013 depends on T007 and T010.
- T014 depends on T005 and T009.
- T015 depends on T008 and T009.
- T016 depends on T001 and T008.
- T017 depends on T016.
- T-LOCAL-GATES depends on T005 to T017.
- T-PR depends on T-LOCAL-GATES and T002.
- T-REMOTE-CI depends on T-PR.
- T-MERGE depends on T-REMOTE-CI and the orchestrator authorization.

The dependency graph has no cycle.

## Requirement Coverage

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 | T005, T010 | TP-01, TP-18 |
| FR-002 | T005 | TP-22 |
| FR-003 | T005 | TP-01 |
| FR-004 | T005 | TP-01, TP-02, TP-03 |
| FR-005 | T009 | TP-18, TP-22 |
| FR-006 | T009, T010 | TP-18 |
| FR-007 | T009 | TP-06, TP-07 |
| FR-008 | T009 | TP-02, TP-04, TP-05, TP-06, TP-07, TP-08 |
| FR-009 | T010 | TP-07, TP-19 |
| FR-010 | T010 | TP-09 |
| FR-011 | T009 | TP-10, TP-20 |
| FR-012 | T009 | TP-11, TP-12 |
| FR-013 | T006, T009 | TP-04, TP-05, TP-15, TP-25 |
| FR-014 | T005, T014 | TP-22 |
| FR-015 | T004, T011, T015 | TP-23 |
| FR-016 | T012 | TP-13, TP-14 |
| FR-017 | T009, T013 | TP-21 |
| FR-018 | T011, T015 | TP-24 |
| FR-019 | T006, T007, T008 | TP-16 |
| FR-020 | T008, T016, T017 | TP-26 |
| FR-021 | T015, T016 | TP-27 |
| FR-022 | T006 | TP-17 |
| FR-023 | T002 | TP-28 |
| FR-024 | T010 | TP-08, TP-18 |

Each requirement maps to at least one task and at least one test.

| Success criterion | Tests or gates |
| - | - |
| SC-001 | TP-18 |
| SC-002 | TP-19 |
| SC-003 | TP-09, TP-10, TP-20 |
| SC-004 | TP-04, TP-05 |
| SC-005 | TP-22 |
| SC-006 | TP-23 |
| SC-007 | TP-28 and T-LOCAL-GATES |
| SC-008 | T-LOCAL-GATES |

## Planned Tests

| ID | Test | File | Requirements |
| - | - | - | - |
| TP-01 | Store round trip, and the stored key equals the SHA-256 digest of the owner key | `tests/unit/upgrade_portal/test_identity.py` | FR-001, FR-003, FR-004 |
| TP-02 | A wrong key refuses a stored record and deletes it | `tests/unit/upgrade_portal/test_identity.py` | FR-004, FR-008 |
| TP-03 | The previous key decrypts a record, and the next refresh writes with the active key | `tests/unit/upgrade_portal/test_identity.py` | FR-004 |
| TP-04 | An idle deadline in the past returns 401 and deletes the record | `tests/unit/upgrade_portal/test_identity.py` | FR-008, FR-013 |
| TP-05 | An absolute deadline in the past returns 401 and deletes the record | `tests/unit/upgrade_portal/test_identity.py` | FR-008, FR-013 |
| TP-06 | A browser digest mismatch returns 401 and deletes the record | `tests/unit/upgrade_portal/test_identity.py` | FR-007, FR-008 |
| TP-07 | A record with a mode other than `environment_token` is refused and deleted | `tests/unit/upgrade_portal/test_identity.py` | FR-007, FR-009 |
| TP-08 | A changed token name at recovery returns 401 and deletes the record | `tests/unit/upgrade_portal/test_identity.py` | FR-024 |
| TP-09 | A store write failure during sign-in returns 503 and registers no session | `tests/unit/upgrade_portal/test_identity.py` | FR-010 |
| TP-10 | A store read failure during recovery returns 503 and creates no local session | `tests/unit/upgrade_portal/test_identity.py` | FR-011 |
| TP-11 | Sign-out deletes the store record and the registry record | `tests/unit/upgrade_portal/test_identity.py` | FR-012 |
| TP-12 | A failed store delete at sign-out clears the browser session and logs an error | `tests/unit/upgrade_portal/test_identity.py` | FR-012 |
| TP-13 | The replaced defect check: a missing record returns 401, and a stored record recovers | `tests/unit/upgrade_portal/test_identity.py` | FR-016 |
| TP-14 | The replaced sign-out check: sign-out after recovery returns True | `tests/unit/upgrade_portal/test_identity.py` | FR-016 |
| TP-15 | Settings reject a lifetime outside the allowed range and an idle lifetime above the absolute lifetime | `tests/unit/upgrade_portal/test_config.py` | FR-013 |
| TP-16 | A container start without the encryption key raises `SettingsError` | `tests/unit/upgrade_portal/test_config.py` | FR-019 |
| TP-17 | A container start with the default Redis password raises `SettingsError` when the store is enabled | `tests/unit/upgrade_portal/test_config.py` | FR-022 |
| TP-18 | Application B recovers an environment token session and returns 200 for a protected page | `tests/contract/upgrade_portal/test_auth.py` | FR-001, FR-005, FR-006, FR-024 |
| TP-19 | Browser token and provider login cookies return 401 in application B | `tests/contract/upgrade_portal/test_auth.py` | FR-009 |
| TP-20 | A store outage returns 503 on a JSON request and on a page request | `tests/contract/upgrade_portal/test_auth.py` | FR-011 |
| TP-21 | A page request without a session returns 303 to `/auth/signin` | `tests/contract/upgrade_portal/test_auth.py` | FR-017 |
| TP-22 | Synthetic credential values never appear in logs, responses, cookies beyond the owner key, or the plaintext payload | `tests/contract/upgrade_portal/test_security.py` | FR-002, FR-014 |
| TP-23 | The guard count equals 51 decorated protected handlers | `tests/contract/upgrade_portal/test_security.py` | FR-015 |
| TP-24 | The capture command keeps `--workers 1` and has no `--max-requests` | `tests/contract/upgrade_portal/test_security.py` | FR-018 |
| TP-25 | The idle refresh writes at most once each 60 seconds | `tests/unit/upgrade_portal/test_identity.py` | FR-013 |
| TP-26 | `deploy/.env.example` names each new variable and holds no value for it | `tests/unit/upgrade_portal/test_config.py` | FR-020 |
| TP-27 | The operator guide states the restart result for each credential mode | `tests/contract/upgrade_portal/test_security.py` | FR-021 |
| TP-28 | `git diff --name-only` lists only the files in the change map, and `test_no_credential_leak.py` is unchanged | repository diff | FR-023, SC-007 |

The planned tests total 28. The table lists 15 tests for `test_identity.py`, 4 for `test_config.py`, 4 for `test_auth.py` (contract), 4 for `test_security.py` (contract), and 1 diff check.

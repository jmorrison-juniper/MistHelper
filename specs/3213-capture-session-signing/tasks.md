# Tasks: Stable capture session signing

**Input**: [spec.md](spec.md) and [plan.md](plan.md).

**Prerequisites**: The live issue claim and exact file reservations.

**Tests**: The assignment requires deployment contracts, actual restart tests, negative controls, and credential checks.

## Phase 1: Setup

- [x] T001 Verify issue ownership and all paginated open pull request files before the claim. (delivered: `spec.md`)
- [x] T002 Record the bounded feature-only specification, plan, and capability limits. (delivered: `spec.md`, `plan.md`)
- [x] T003 Confirm the operator guide reservation before editing its existing path. (delivered: `documentation/upgrade_capture_portal.md`)

## Phase 2: Foundational

- [x] T004 Create the owned real-application fixtures in `tests/contract/upgrade_portal/session_signing/conftest.py`. (delivered: `tests/contract/upgrade_portal/session_signing/conftest.py`)
- [x] T005 Keep cloud transport synthetic and registry semantics real in the owned fixtures. (delivered: `tests/contract/upgrade_portal/session_signing/conftest.py`)

## Phase 3: User Story 1 - Configure a stable signing key

**Independent Test**: Check both deployment inputs and a missing-variable control.

- [x] T006 [US1] Add the deployment contract in `tests/contract/upgrade_portal/session_signing/test_deployment.py`. (delivered: `tests/contract/upgrade_portal/session_signing/test_deployment.py`)
- [x] T007 [US1] Record a failing contract run against the unchanged `deploy/.env.example`. (delivered: `tests/contract/upgrade_portal/session_signing/test_deployment.py`)
- [x] T008 [US1] Add the optional commented blank setting and safe generation command to `deploy/.env.example`. (delivered: `deploy/.env.example`)
- [x] T009 [US1] Add the key storage, Compose forwarding, and registry limits to the confirmed operator guide. (delivered: `documentation/upgrade_capture_portal.md`)

## Phase 4: User Story 2 - Keep the signed cookie valid

**Independent Test**: Transfer actual cookies and form tokens between independently created applications.

- [x] T010 [US2] Prove same-key application recreation in `tests/contract/upgrade_portal/session_signing/test_restart.py`. (delivered: `tests/contract/upgrade_portal/session_signing/test_restart.py`)
- [x] T011 [US2] Prove changed-key, missing-browser, and registry-loss controls in the same test module. (delivered: `tests/contract/upgrade_portal/session_signing/test_restart.py`)

## Phase 5: User Story 3 - Preserve development and credential safety

**Independent Test**: Check configured, missing, empty, and whitespace keys without a real credential.

- [x] T012 [US3] Preserve key reading and warning behavior in `tests/unit/upgrade_portal/session_signing/test_key_configuration.py`. (delivered: `tests/unit/upgrade_portal/session_signing/test_key_configuration.py`)
- [x] T013 [US3] Check logs, HTML, HTTP bodies, and decoded cookies in `tests/contract/upgrade_portal/session_signing/test_no_leak.py`. (delivered: `tests/contract/upgrade_portal/session_signing/test_no_leak.py`)

## Phase 6: Local completion

- [x] T014 Add `changelog.d/issue-3213-capture-session-signing.md` with the issue reference. (delivered: `changelog.d/issue-3213-capture-session-signing.md`)
- [x] T015 Run focused tests, adjacent contracts, local gates, the ratchet preflight, and the supported dependency audit. (delivered: `tests/contract/upgrade_portal/session_signing/`, `tests/unit/upgrade_portal/session_signing/`)
- [x] T016 Preserve all 23 checklist items of `.github/PULL_REQUEST_TEMPLATE.md` in the offline draft. (delivered: session artifact `issue3213-pr-draft.md`)

## Phase 7: Deferred release

These tasks are outside the local preparation assignment.
Both tasks require the parent's explicit full verified-main SHA grant.

- [ ] T017 After the grant, repeat current-base checks and prepare protected publication for the exact owned file set.
- [ ] T018 After the grant, complete the protected merge, actual merged-main tests, and persistent pull request receipt.

## Dependencies & Execution Order

T003 precedes the operator guide edit.
T004 and T005 precede the route tests.
T006 and T007 precede T008.
All test and documentation tasks precede T015.
T015 and T016 precede the local commit and external handoff.
The parent release grant precedes T017.
T017 precedes T018.

The unit configuration tests and the deployment contracts are independent after setup.
The restart and credential tests share the real application fixtures.
The separate authentication issue records the three-mode registry-loss proof without authorizing a production implementation.

## Implementation Strategy

Prove the existing signing behavior first.
Repair its missing deployment guidance without changing the production source.
Keep authenticated access and signed-cookie validity as separate measured results.

Publication, protected merge, deployment, and actual merged-main tests require the later parent release grant.
They are not local preparation tasks.

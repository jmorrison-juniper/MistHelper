# Tasks: Browser Token and Safe Device Selection

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, and contracts.
**Size**: oversized.
**Rule**: Do not start a real firmware upgrade.

## Phase 1: Setup

**Wave 1 — independent (different files):**

- [x] **T001** [P] [US1] Add browser-token fixtures and safe-leak assertions to `tests/unit/upgrade_portal/test_auth.py`.
- [x] **T002** [P] [US1] Add browser-token page and response contract cases to `tests/contract/upgrade_portal/test_auth.py`.
- [x] **T003** [P] [US2] Add selected-type and plan-rejection cases to `tests/unit/upgrade_portal/test_upgrade_options.py`.
- [x] **T004** [P] [US3] Add safe-target and unknown-version cases to `tests/contract/upgrade_portal/test_upgrade_options.py`.

**⟶ Wait for Wave 1 to finish, then:**

- [x] **T005** [US1] Add registry identity and token-name lifetime cases to `tests/unit/upgrade_portal/test_identity.py`.
- [x] **T006** [US1] Extend credential-leak coverage for browser tokens in `tests/contract/upgrade_portal/test_no_credential_leak.py`.

## Phase 2: Foundational

**Wave 1 — independent (different files):**

- [x] **T007** [P] [US1] Freeze environment-token presence at portal startup in `src/upgrade_portal/app/config.py`.
- [x] **T008** [P] [US1] Extend session identity and credential modes for safe token-name ownership in `src/upgrade_portal/runtime/identity.py`.
- [x] **T009** [P] [US2] Define selected-type validation and safe model fallback helpers in `src/upgrade_portal/upgrade/options.py`.

**⟶ Wait for Wave 1 to finish, then:**

- [x] **T010** [US1] Build browser-token sessions, call `GetSelf`, and keep raw tokens out of output in `src/upgrade_portal/app/routes/auth.py`.
- [x] **T011** [US2] Enforce selected types while saving upgrade options in `src/upgrade_portal/app/routes/upgrade.py`.

## Phase 3: User Story 1 - Sign in with a browser token

### Tests

- [x] **T012** [US1] Run the focused authentication and identity tests in `tests/unit/upgrade_portal/test_auth.py`.

### Implementation

**Wave 1 — independent (different files):**

- [x] **T013** [P] [US1] Add the startup-gated browser-token control and safe guidance to `src/upgrade_portal/app/assets/templates/auth/signin.html`.
- [x] **T014** [P] [US1] Add client-side sign-in support that submits the token only to the sign-in route in `src/upgrade_portal/app/assets/static/js/portal.js`.

**⟶ Wait for Wave 1 to finish, then:**

- [x] **T015** [US1] Verify every guarded portal route receives the active registry session in `src/upgrade_portal/app/wiring.py`.

**Checkpoint**: Browser-token sign-in is safe and independently testable.

## Phase 4: User Story 2 - Select the device types for an upgrade

### Tests

- [x] **T016** [US2] Run selected-type option and route cases in `tests/unit/upgrade_portal/test_upgrade_options.py`.

### Implementation

**Wave 1 — independent (different files):**

- [x] **T017** [P] [US2] Add all, selected, and single type checkboxes to `src/upgrade_portal/app/assets/templates/upgrade/options.html`.
- [x] **T018** [P] [US2] Submit selected types and filter rows in `src/upgrade_portal/app/assets/static/js/portal.js`.

**⟶ Wait for Wave 1 to finish, then:**

- [x] **T019** [US2] Preserve complete capture rows and selected plan targets in `src/upgrade_portal/capture/assembly.py`.

**Checkpoint**: Type selection limits targets and plans but not capture completeness.

## Phase 5: User Story 3 - See devices that differ from the safe target

### Tests

- [x] **T020** [US3] Run safe target and mismatch contract cases in `tests/contract/upgrade_portal/test_upgrade_options.py`.

### Implementation

**Wave 1 — independent (different files):**

- [x] **T021** [P] [US3] Add target source and mismatch fields to option records in `src/upgrade_portal/upgrade/options.py`.
- [x] **T022** [P] [US3] Show known firmware mismatch markers in `src/upgrade_portal/app/assets/templates/upgrade/options.html`.

**⟶ Wait for Wave 1 to finish, then:**

- [x] **T023** [US3] Keep known and unknown running firmware behavior in `src/upgrade_portal/capture/devices.py`.

**Checkpoint**: The inventory clearly marks known differences and preserves unknown values.

## Phase 6: Polish and Delivery

**Wave 1 — independent (different files):**

- [x] **T024** [P] [US1] Document browser-token safety and safe identity behavior in `documentation/upgrade_capture_portal.md`.
- [x] **T025** [P] [US2] Document selected types and mismatch markers in `README.md`.
- [x] **T026** [P] [US3] Add the feature release note to `CHANGELOG.md`.

**⟶ Wait for Wave 1 to finish, then:**

- [x] **T027** [US1] Run focused unit, contract, browser, syntax, and secret-scan validation from `tests/`.
- [ ] **T028** [US1] Create, label, validate, and squash merge the pull request that closes #2133, #2134, and #2135 using `.github/workflows/`.
- [ ] **T029** [US1] Pull the merged image, restart the container, and verify container and local portal readiness using `compose.yml`.

## Dependencies and Execution Order

Setup establishes failing coverage. Foundational work supplies startup state,
safe identity, and selection rules. Story 1 builds the credential path. Story 2
adds server-side type enforcement. Story 3 adds truthful mismatch display.
Polish documents, validates, merges, deploys, and verifies the result.

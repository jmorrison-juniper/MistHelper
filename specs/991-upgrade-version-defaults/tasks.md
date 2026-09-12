# Tasks: Per-Type Upgrade Version Defaults

**Feature**: `991-upgrade-version-defaults`  
**Input**: [spec.md](spec.md), [plan.md](plan.md), [data-model.md](data-model.md), and [contracts/](contracts/)

## Phase 1: Setup

No shared project structure or tooling changes are required.

## Phase 2: Foundational

### Tests

**Wave 1 — independent (different files):**

- [x] **T001** [US1] Write failing selector unit tests for eligible-device grouping, normalized intersections, numeric ordering, and no-common-candidate warnings · tests/unit/upgrade_portal/test_upgrade_options.py

### Implementation

**⟶ Wait for Wave 1 to finish, then:**

**Wave 2 — selector implementation:**

- [x] **T002** [US1] Implement the typed compatibility selector, safe candidate ranking, warnings, and action logging without creating an upgrade submission path · src/upgrade_portal/upgrade/options.py

## Phase 3: User Story 1 — Receive safe defaults for each device type (Priority: P1)

**Goal**: Present independently selectable safe targets for APs, switches, and gateways.

**Independent Test**: Open options with overlapping multi-model availability and verify each type selects its highest numeric common version while the retired global selector is absent.

### Tests

**Wave 1 — independent (different files):**

- [x] **T003** [P] [US1] Write failing browser tests for the three fixed type controls, their test IDs, scoped device-row updates, no-common-candidate messaging, and absent global control · tests/e2e/upgrade_portal/test_upgrade.py
- [x] **T004** [P] [US1] Write failing options-read contract tests for typed candidates/defaults and assert that reading options never invokes the upgrade launcher · tests/contract/upgrade_portal/test_upgrade_options.py

### Implementation

**⟶ Wait for Wave 1 to finish, then:**

**Wave 2 — independent (different files):**

- [x] **T005** [P] [US1] Replace the all-device version control with AP, switch, and gateway controls, per-type warnings, and stable contract test IDs while retaining individual and save controls · src/upgrade_portal/app/assets/templates/upgrade/options.html
- [x] **T006** [P] [US1] Supply typed candidates, calculated defaults, saved choices, and warnings to the options render boundary without calling the upgrade launcher · src/upgrade_portal/app/routes/upgrade.py

**⟶ Wait for Wave 2 to finish, then:**

**Wave 3 — integration:**

- [x] **T007** [US1] Bind each type control to only same-type device rows that offer the exact selected version, preserving individual controls and save behavior · src/upgrade_portal/app/assets/static/js/portal.js

**Checkpoint**: The options page is independently functional: it renders three safe, type-scoped controls with warnings where no common target exists.

## Phase 4: User Story 3 — Validate selections without triggering an upgrade (Priority: P1)

**Goal**: Reject stale, tampered, unknown, and incompatible save targets before persistence, with no upgrade submission.

**Independent Test**: Submit an unavailable target after availability changes and verify the existing record remains unchanged and no launcher call occurs.

### Tests

**Wave 1 — independent (different files):**

- [x] **T008** [P] [US3] Write failing unit tests for save-time inventory and availability re-reads, missing/cross-type/unavailable targets, atomic rejection, and no launcher invocation · tests/unit/upgrade_portal/test_upgrade_options.py
- [x] **T009** [P] [US3] Write failing save-route contract tests for `400 bad_option`, unchanged plans, stale availability, and preserved explicit-confirmation-only start behavior · tests/contract/upgrade_portal/test_upgrade_options.py

### Implementation

**⟶ Wait for Wave 1 to finish, then:**

**Wave 2 — save validation:**

- [x] **T010** [US3] Re-read current inventory and model availability on save; validate every submitted target before any record write; reject failures atomically and keep validation read-only · src/upgrade_portal/upgrade/options.py

**⟶ Wait for Wave 2 to finish, then:**

**Wave 3 — route integration:**

- [x] **T011** [US3] Keep the save route on the existing individual-target body and `bad_option` response contract while ensuring confirmation remains the only upgrade-start boundary · src/upgrade_portal/app/routes/upgrade.py

**Checkpoint**: A submitted plan is independently safe: current availability is checked before persistence and options reads/saves cannot start an upgrade.

## Phase 5: User Story 2 — Apply an approved operational override safely (Priority: P2)

**Goal**: Honor one approved override per device type only when it is exactly compatible with every eligible device of that type.

**Independent Test**: Set each override to compatible, incompatible, blank, and malformed values and verify only the associated type changes or safely falls back.

### Tests

**Wave 1 — independent (different files):**

- [x] **T012** [US2] Write failing selector unit tests for all three override variables, exact compatible acceptance, type isolation, and safe fallback for blank, malformed, unavailable, and incompatible values · tests/unit/upgrade_portal/test_upgrade_options.py

### Implementation

**⟶ Wait for Wave 1 to finish, then:**

**Wave 2 — independent (different files):**

- [x] **T013** [P] [US2] Read and validate the three type-specific environment overrides only against normalized common candidates, then retain the safe fallback and selection logs · src/upgrade_portal/upgrade/options.py
- [x] **T014** [P] [US2] Document the three optional type-default variables, exact-compatibility rule, and safe fallback behavior · deploy/.env.example
- [x] **T015** [P] [US2] Document per-type safe defaults, override behavior, no-common-target handling, and the unchanged confirmation gate · documentation/upgrade_capture_portal.md

**Checkpoint**: An administrator can independently configure a compatible override for one type without weakening compatibility or affecting the other types.

## Phase 6: Polish

**Wave 1 — independent (different files):**

- [x] **T016** [P] Run focused unit, route-contract, and browser suites covering all acceptance scenarios and no-upgrade guarantees · tests/unit/upgrade_portal/test_upgrade_options.py, tests/contract/upgrade_portal/test_upgrade_options.py, tests/e2e/upgrade_portal/test_upgrade.py
- [x] **T017** [P] Run lint and format checks for changed Python, template, and browser assets · pyproject.toml, src/upgrade_portal/upgrade/options.py, src/upgrade_portal/app/routes/upgrade.py, src/upgrade_portal/app/assets/templates/upgrade/options.html, src/upgrade_portal/app/assets/static/js/portal.js
- [x] **T018** [P] Verify the documented configuration variables and examples match the implementation and configuration contract · deploy/.env.example, documentation/upgrade_capture_portal.md, specs/991-upgrade-version-defaults/contracts/http-api.md

**⟶ Wait for Wave 1 to finish, then:**

**Wave 2 — final validation:**

- [x] **T019** Validate all Success Criteria with the project test, lint, format, and configuration checks; record any remaining gaps · specs/991-upgrade-version-defaults/spec.md, pyproject.toml

## Dependencies & Execution Order

- Setup has no work. Foundational Wave 1 blocks Wave 2; foundational completion blocks every story.
- User Story 1: test Wave 1 blocks implementation Wave 2, which blocks the browser integration task.
- User Story 3: test Wave 1 blocks save validation, which blocks route preservation.
- User Story 2: override tests block the independent code, environment, and documentation wave.
- Polish Wave 1 blocks the final Success-Criteria validation task.

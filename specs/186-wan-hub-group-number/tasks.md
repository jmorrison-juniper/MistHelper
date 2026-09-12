# Tasks: WAN Hub Group Number Manager

**Input**: Design documents from `/specs/186-wan-hub-group-number/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Included — unit tests with mocked API calls per research.md R8.

**Organization**: Tasks grouped by user story. US1-US3 are P1 (MVP). US4 is P2 (architecture).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3, US4)
- Exact file paths included in all descriptions

---

## Phase 1: Setup

**Purpose**: Create the external module file and class skeleton

- [X] T001 Create module file with class skeleton and imports in src/wan_hub_group_manager.py
- [X] T002 Add import and menu_actions entry "163" in MistHelper.py (line ~75 for import, line ~58131 for menu entry, line ~58869 for test classification)

**Checkpoint**: Module imports without error, menu 163 dispatches to `WanHubGroupNumberManager.execute`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core helpers that ALL user stories depend on — API data fetching and path matching

- [X] T003 [P] Implement `_fetch_profiles()` in src/wan_hub_group_manager.py — call `listOrgDeviceProfiles(apisession, org_id, type="gateway")`, handle pagination via `mistapi.get_all()`, sort alphabetically by name, handle empty result (FR-001, FR-010)
- [X] T004 [P] Implement `_fetch_hub_spoke_vpns()` in src/wan_hub_group_manager.py — call `listOrgVpns(apisession, org_id)`, filter to `type == "hub_spoke"`, handle empty result (FR-001a)
- [X] T005 Implement `_find_matching_paths(profile_name, vpns)` in src/wan_hub_group_manager.py — prefix match `f"{profile_name}-"` against VPN path keys, return list of `(vpn_id, vpn_name, path_key, current_pod)` tuples, detect inconsistent pod values and log warning (FR-001b)

**Checkpoint**: All three helpers return correct data structures from mocked API responses. Prefix matching correctly differentiates `DC1-` from `DC1-BACKUP-`.

---

## Phase 3: User Story 1 — View and Select a WAN Hub Profile (Priority: P1) MVP

**Goal**: NOC engineer sees alphabetized gateway profiles with current pod values and selects one by index number.

**Independent Test**: Run menu 163 → verify alphabetized list with pod values displays → select valid index → profile confirmed. Invalid index shows error and reprompts.

### Tests for User Story 1

- [X] T006 [P] [US1] Write unit tests for profile listing and selection in tests/unit/test_wan_hub_group_manager.py — test alphabetical sort, pod cross-reference display, empty profile list handling, valid/invalid index selection, non-numeric input rejection. Also covers foundational helpers (`_fetch_profiles`, `_fetch_hub_spoke_vpns`, `_find_matching_paths`) transitively via mocked API responses.

### Implementation for User Story 1

- [X] T007 [US1] Implement `_display_profile_list(profiles, vpn_data)` in src/wan_hub_group_manager.py — format numbered list with profile name and current pod value (or "default (1)"), handle profiles with no matching VPN paths (FR-002)
- [X] T008 [US1] Implement profile selection input loop in `run()` in src/wan_hub_group_manager.py — use `safe_input()` for index entry, validate range 1-N, support 'q' to cancel, reprompt on invalid input (FR-003)
- [X] T009 [US1] Implement `execute()` static entry point in src/wan_hub_group_manager.py — resolve org_id via `ConfigUtils.get_cached_or_prompted_org_id()`, instantiate class, call `run()`, wrap in try/except for API errors with user-friendly messages (FR-008, FR-009)

**Checkpoint**: Menu 163 shows alphabetized profiles with pod values. Selection works with full input validation. No VPN update functionality yet.

---

## Phase 4: User Story 2 — Set the WAN Hub Group Number (Priority: P1) MVP

**Goal**: After selecting a profile, user enters a new pod value (1-128) and all matching VPN paths are batch-updated.

**Independent Test**: Select profile → choose "Set" → enter valid pod → confirm → API updates all matching paths. Invalid pod rejected with range message.

### Tests for User Story 2

- [X] T010 [P] [US2] Write unit tests for set_pod in tests/unit/test_wan_hub_group_manager.py — test pod validation (1-128, non-numeric, 0, negative, >128), batch update of all matching paths, confirmation prompt, API call payload structure, inconsistent pod warning. Include assertion verifying updateOrgVpn payload contains correct pod values on all matching paths (SC-003 coverage).

### Implementation for User Story 2

- [X] T011 [US2] Implement `_prompt_action()` in src/wan_hub_group_manager.py — display current pod value + path count, show set/clear/cancel menu, validate selection via `safe_input()` (FR-004)
- [X] T012 [US2] Implement `set_pod(profile, vpn_data, new_pod)` in src/wan_hub_group_manager.py — validate pod 1-128 (FR-005), deep-copy VPN paths dict, update pod on all matching path keys (FR-005a), call `updateOrgVpn` per VPN object (FR-006), display confirmation with path count and VPN name (FR-007)
- [X] T013 [US2] Implement pod value input prompt in `run()` in src/wan_hub_group_manager.py — prompt for integer input via `safe_input()`, validate range, confirm before update with y/N prompt (FR-005)

**Checkpoint**: Full set workflow works end-to-end. Profile selection → set action → pod input → confirmation → API update → success message.

---

## Phase 5: User Story 3 — Clear the WAN Hub Group Number (Priority: P1) MVP

**Goal**: After selecting a profile, user clears the pod (resets to 1) on all matching VPN paths.

**Independent Test**: Select profile → choose "Clear" → confirm → pod reset to 1. Already-default pod shows "already at default" message.

### Tests for User Story 3

- [X] T014 [P] [US3] Write unit tests for clear_pod in tests/unit/test_wan_hub_group_manager.py — test reset to 1, already-at-default detection, confirmation prompt, delegation to set_pod

### Implementation for User Story 3

- [X] T015 [US3] Implement `clear_pod(profile, vpn_data)` in src/wan_hub_group_manager.py — check if pod is already 1 and inform user if so, otherwise confirm reset and delegate to `set_pod(profile, vpn_data, 1)` (FR-005)

**Checkpoint**: Full clear workflow works end-to-end. "Already at default" case handled. Delegates correctly to set_pod.

---

## Phase 6: User Story 4 — External Module Architecture (Priority: P2)

**Goal**: Establish the pattern for external modules so future operations only need a new file + menu registration line.

**Independent Test**: Import `src.wan_hub_group_manager` in a clean Python session. Verify class instantiates. Verify MistHelper.py dispatches to it without code duplication.

### Tests for User Story 4

- [X] T016 [P] [US4] Write import and integration tests in tests/unit/test_wan_hub_group_manager.py — test module imports cleanly, class instantiates with mock apisession, execute() calls ConfigUtils and run(), no circular import issues

### Implementation for User Story 4

- [X] T017 [US4] Verify no circular imports between src/wan_hub_group_manager.py and MistHelper.py — ensure module receives apisession as parameter, does not import MistHelper at module level, uses lazy imports if needed for ConfigUtils/safe_input

**Checkpoint**: Module architecture clean. No circular imports. Pattern documented and repeatable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, error handling hardening, and deployment readiness

- [X] T018 [P] Add error handling for API failures in src/wan_hub_group_manager.py — wrap API calls in try/except, handle 401 (auth expired), 403 (permissions), network errors, log at Error level with traceback, display user-friendly ASCII-only messages (SC-005)
- [X] T019 [P] Update README.md — bump operation count from 163 to 164, add menu 163 entry to operation table with description "WAN Hub Group Number Manager"
- [X] T020 [P] Update CHANGELOG.md — add version entry with UTC timestamp format (YY.MM.DD.HH.MM) documenting new menu 163 operation
- [X] T021 Run quality gates: `python -m py_compile src/wan_hub_group_manager.py && python -m py_compile MistHelper.py && python -m ruff check src/wan_hub_group_manager.py MistHelper.py && python -m black --check src/wan_hub_group_manager.py MistHelper.py`

**Checkpoint**: All quality gates pass. README and CHANGELOG updated. Feature ready for PR.

---

## Dependencies

```text
T001 ──► T002 ──► T003 (parallel with T004)
                  T004 ──► T005
                           T005 ──► T007 ──► T008 ──► T009 (US1 complete)
                                    T009 ──► T011 ──► T012 ──► T013 (US2 complete)
                                             T012 ──► T015 (US3 complete)
                                                      T009 ──► T017 (US4 complete)
T006, T010, T014, T016 are parallel test tasks (can start after T001)
T018, T019, T020 are parallel polish tasks (can start after US1-US3 complete)
T021 is the final gate (after all other tasks)
```

### Story Completion Order

1. **US1** (T007-T009): View/select profiles — unlocks US2 and US3
2. **US2** (T011-T013): Set pod — depends on US1 completion
3. **US3** (T015): Clear pod — depends on US2 (delegates to set_pod)
4. **US4** (T017): Architecture validation — depends on US1 (execute() exists)

### Parallel Execution Opportunities

| Parallel Group | Tasks | Condition |
| - | - | - |
| API helpers | T003, T004 | After T002 |
| All test tasks | T006, T010, T014, T016 | After T001 (class skeleton exists) |
| Polish tasks | T018, T019, T020 | After US1-US3 complete |

## Implementation Strategy

**MVP Scope**: US1 + US2 + US3 (Phase 1-5) — delivers full set/clear functionality.

**Incremental Delivery**:
1. Phase 1-2: Skeleton + helpers → verify imports and API calls work
2. Phase 3: Profile listing → verify interactive display
3. Phase 4: Set pod → verify end-to-end write workflow
4. Phase 5: Clear pod → verify reset workflow
5. Phase 6: Architecture validation → confirm pattern is clean
6. Phase 7: Polish → docs, error hardening, quality gates

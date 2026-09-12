# Tasks: Menu 164 - WAN Hub-Spoke VPN Builder

**Input**: Design documents from `/specs/187-wan-vpn-builder/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Included — spec requires SC-005 (unit test coverage >= 70%).

**Organization**: Tasks grouped by user story (P1, P2, P3) for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3)
- Exact file paths included in descriptions

---

## Phase 1: Setup

**Purpose**: Create module file, class skeleton, and test file

- [X] T001 Create `src/wan_vpn_builder.py` with `WanVpnBuilder` class skeleton, constants (`POD_MIN=1`, `POD_MAX=128`, `POD_DEFAULT=1`), `__init__` accepting `apisession`, `org_id`, `safe_input_func`, and `execute()` static entry point
- [X] T002 [P] Create `tests/unit/test_wan_vpn_builder.py` with test class skeleton and imports

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Pure-logic methods shared by all user stories — no API calls, no user interaction

**CRITICAL**: These are the building blocks. All user story tasks depend on them.

- [X] T003 Implement `_extract_wan_suffix()` static method in `src/wan_vpn_builder.py` — extract suffix after last `_` (e.g., `HE_WAN1` -> `WAN1`, `HE_5G` -> `5G`, `WAN1` -> `WAN1`)
- [X] T004 [P] Implement `_classify_interfaces()` static method in `src/wan_vpn_builder.py` — extract WAN and LAN interface lists from a profile's `port_config` using the `usage` field
- [X] T005 [P] Implement `_suggest_pod()` static method in `src/wan_vpn_builder.py` — extract trailing digits from profile name via regex `r"(\d+)$"`, return int if 1-128, else return fallback sequential value
- [X] T006 Write unit tests for `_extract_wan_suffix()`, `_classify_interfaces()`, and `_suggest_pod()` in `tests/unit/test_wan_vpn_builder.py`

**Checkpoint**: All pure-logic helpers tested and passing. User story implementation can begin.

---

## Phase 3: User Story 1 — Create a Hub-Spoke VPN from Gateway Profiles (Priority: P1) MVP

**Goal**: Engineer launches Menu 164, names a VPN, assigns hub/spoke roles to gateway profiles, reviews auto-generated paths, confirms, and the VPN is created via API.

**Independent Test**: Run `--menu 164`, enter a VPN name, assign roles, confirm preview, verify VPN created via API.

### Path Generation (US1 core logic)

- [X] T007 [US1] Implement `_collect_wan_suffixes()` in `src/wan_vpn_builder.py` — collect union of WAN suffixes from all non-skip assignments using `_extract_wan_suffix()`
- [X] T008 [US1] Implement `_generate_hub_paths()` in `src/wan_vpn_builder.py` — for each WAN interface: 1 direct path + N cross-connect paths (one per suffix from `_collect_wan_suffixes()`, which is the global set across all non-skip profiles); for each LAN interface: 1 direct path. All paths get profile's pod value.
- [X] T009 [US1] Implement `_generate_spoke_paths()` in `src/wan_vpn_builder.py` — for each WAN and LAN interface: 1 direct path only. All paths get profile's pod value.
- [X] T010 [US1] Implement `_build_vpn_body()` in `src/wan_vpn_builder.py` — assemble full VPN API body (`name`, `type: hub_spoke`, `path_selection: {strategy: simple}`, `paths` dict) by iterating assignments and calling hub/spoke generators
- [X] T011 [US1] Write unit tests for path generation (`_collect_wan_suffixes`, `_generate_hub_paths`, `_generate_spoke_paths`, `_build_vpn_body`) in `tests/unit/test_wan_vpn_builder.py`

### API Helpers (US1)

- [X] T012 [US1] Implement `_fetch_profiles()` in `src/wan_vpn_builder.py` — call `listOrgDeviceProfiles(type="gateway")` with `mistapi.get_all(response=response, mist_session=apisession)`, sort alphabetically, return list
- [X] T013 [US1] Implement `_fetch_existing_vpns()` in `src/wan_vpn_builder.py` — call `listOrgVpns()` with `mistapi.get_all()`, return full list
- [X] T014 [US1] Implement `_create_vpn()` in `src/wan_vpn_builder.py` — call `createOrgVpn(body=vpn_body)`, return created VPN dict (with `id`) on success, handle API errors with logging

### User Interaction (US1)

- [X] T015 [US1] Implement `_display_existing_vpns()` in `src/wan_vpn_builder.py` — show summary table of existing VPNs (name, type, path count) or "No existing VPNs" message
- [X] T016 [US1] Implement `_prompt_vpn_name()` in `src/wan_vpn_builder.py` — prompt for name, validate non-empty and unique (case-insensitive) against existing VPNs, support 'q' to cancel, loop on invalid
- [X] T017 [US1] Implement `_display_profile_list()` in `src/wan_vpn_builder.py` — show numbered list of gateway profiles with WAN/LAN interface counts using `_classify_interfaces()`. Warn user if any profile has 0 WAN interfaces (edge case: profile with LAN-only config).
- [X] T018 [US1] Implement `_prompt_role_assignments()` in `src/wan_vpn_builder.py` — for each profile, prompt user to assign Hub/Spoke/Skip, validate at least 1 non-skip, return list of assignment dicts
- [X] T019 [US1] Implement `_prompt_pod_values()` in `src/wan_vpn_builder.py` — for each non-skip assignment, show auto-suggested pod from `_suggest_pod()`, allow override, validate 1-128
- [X] T020 [US1] Implement `_display_preview()` in `src/wan_vpn_builder.py` — display full VPN definition (name, type, all path keys with pod values, total path count). Warn if path count exceeds 500. Prompt user to type `CREATE` to confirm (per FR-007), or any other input to cancel.

### Main Workflow (US1)

- [X] T021 [US1] Implement `run()` main workflow in `src/wan_vpn_builder.py` — orchestrate: fetch profiles -> fetch VPNs -> display existing -> prompt name -> display profiles -> assign roles -> assign pods -> generate paths -> preview -> confirm -> create VPN
- [X] T022 [US1] Write unit tests for user interaction and workflow in `tests/unit/test_wan_vpn_builder.py` — mock API calls and `safe_input`, test cancellation flows, empty profile handling, duplicate name rejection, and verify that API failure in `_create_vpn()` skips the profile update offer

**Checkpoint**: Menu 164 creates VPNs end-to-end. Can be tested independently.

---

## Phase 4: User Story 2 — Update Device Profile vpn_paths After VPN Creation (Priority: P2)

**Goal**: After creating a VPN, optionally update each selected profile's `port_config` to add `vpn_paths` references linking ports to the new VPN.

**Independent Test**: Create a VPN (US1), accept profile update prompt, verify each profile's `port_config` has correct `vpn_paths` entries.

### Implementation (US2)

- [X] T023 [US2] Implement `_build_port_vpn_paths()` in `src/wan_vpn_builder.py` — for a single profile+port, generate the `vpn_paths` dict entries with format `{PathName}.{VPNName}`, `key` indexing, and `role`
- [X] T024 [US2] Implement `_update_single_profile()` in `src/wan_vpn_builder.py` — fetch fresh profile via `getOrgDeviceProfile()`, merge new `vpn_paths` into existing `port_config`, call `updateOrgDeviceProfile()`, handle errors
- [X] T025 [US2] Implement `_prompt_profile_updates()` in `src/wan_vpn_builder.py` — prompt user to update profiles (y/N), iterate assignments, call `_update_single_profile()` for each non-skip, report success/failure summary
- [X] T026 [US2] Add profile update call to `run()` after successful VPN creation in `src/wan_vpn_builder.py` — if VPN created successfully, offer profile updates
- [X] T027 [US2] Write unit tests for vpn_paths generation and profile update logic in `tests/unit/test_wan_vpn_builder.py` — test `_build_port_vpn_paths()` key format, partial failure handling, decline flow

**Checkpoint**: Full end-to-end: create VPN + update profiles. Both US1 and US2 independently testable.

---

## Phase 5: User Story 3 — Review Existing VPNs Before Creating (Priority: P3)

**Goal**: Display existing VPN summary at the start of Menu 164 for reference.

**Independent Test**: Run Menu 164 in org with existing VPNs, verify summary table appears before name prompt.

### Implementation (US3)

- [X] T028 [US3] Enhance `_display_existing_vpns()` in `src/wan_vpn_builder.py` — show name, type, and path count per VPN (per spec US3 acceptance criteria). Profile associations and pod values are out of scope for initial implementation.
- [X] T029 [US3] Write unit tests for enhanced VPN display in `tests/unit/test_wan_vpn_builder.py`

**Checkpoint**: All 3 user stories complete and independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Integration into MistHelper, documentation, quality gates

- [X] T030 Add import for `wan_vpn_builder` in `MistHelper.py` (after the `wan_hub_group_manager` import block)
- [X] T031 Add menu entry `"164"` to `menu_actions` dict in `MistHelper.py` with lambda calling `WanVpnBuilder.execute(apisession, get_org_id, safe_input)`
- [X] T032 Add test classification for `"164"` as interactive/skip in `MistHelper.py` test section
- [X] T033 [P] Update operation count in `README.md` (164 -> 165 operations or current count + 1)
- [X] T034 [P] Add version entry to `CHANGELOG.md` with `version YY.MM.DD.HH.MM` format
- [X] T035 [P] Update documentation files (`documentation/Menu-Reference.md`, `documentation/Home.md`, `documentation/architecture-overview.md`) with Menu 164 entry
- [X] T036 Run quality gates: `python -m py_compile src/wan_vpn_builder.py`, `python -m ruff check src/wan_vpn_builder.py`, `python -m black src/wan_vpn_builder.py`
- [X] T037 Run full test suite: `python -m pytest tests/unit/test_wan_vpn_builder.py -v`
- [X] T038 Run quickstart.md validation: verify `python MistHelper.py --menu 164` launches without import errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1 - P1)**: Depends on Phase 2 — core VPN creation
- **Phase 4 (US2 - P2)**: Depends on Phase 3 (needs VPN creation flow) — profile updates
- **Phase 5 (US3 - P3)**: Depends on Phase 2 only — enhanced display (can parallel with US1/US2)
- **Phase 6 (Polish)**: Depends on Phase 3 minimum (MVP integration)

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational only — no cross-story dependencies
- **US2 (P2)**: Depends on US1 completion (needs `run()` workflow and VPN creation result)
- **US3 (P3)**: Depends on Foundational only — can start parallel with US1

### Within Each User Story

- Path generation methods before user interaction methods
- API helpers before workflow orchestration
- Core implementation before tests (tests reference implementation)
- Story complete = checkpoint validated

### Parallel Opportunities

Within Phase 2:
- T004 (`_classify_interfaces`) and T005 (`_suggest_pod`) are [P] — different methods, no dependencies

Within Phase 3 (US1):
- T012, T013 (API helpers) can parallel with T007-T010 (path generation)
- T015-T020 (interaction) depend on T007-T010 (path generation) and T012-T013 (API)

Across phases:
- US3 (Phase 5) can start after Phase 2, parallel with US1

---

## Parallel Example: Phase 2

```text
# These can run simultaneously:
T003: _extract_wan_suffix() in src/wan_vpn_builder.py
T004: _classify_interfaces() in src/wan_vpn_builder.py  [P]
T005: _suggest_pod() in src/wan_vpn_builder.py          [P]

# Then sequentially:
T006: Unit tests for all three (depends on T003-T005)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T006)
3. Complete Phase 3: User Story 1 (T007-T022)
4. **STOP and VALIDATE**: Test VPN creation end-to-end
5. Complete Phase 6: Polish (T030-T038) — integrate into MistHelper
6. Deploy MVP

### Incremental Delivery

1. Setup + Foundational -> Foundation ready
2. Add US1 -> Test VPN creation independently -> Deploy (MVP!)
3. Add US2 -> Test profile updates independently -> Deploy
4. Add US3 -> Test enhanced display independently -> Deploy
5. Each story adds value without breaking previous stories

---

## Notes

- All `safe_input` calls use context parameter for EOF logging (e.g., `context="wan_vpn_name"`)
- All API calls use keyword args: `mistapi.get_all(response=response, mist_session=apisession)`
- Path generation methods are pure functions (no side effects) — easy to test
- Profile update (US2) re-fetches profile before update to avoid stale data conflicts
- Follows Menu 163 (`wan_hub_group_manager.py`) patterns exactly

# Tasks: Bulk RADIUS WLAN Configuration (Menu 122)

**Input**: Design documents from `/specs/001-radius-wlan-config/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: Not explicitly requested - test tasks omitted per SpecKit guidelines.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3)
- All paths relative to repository root

---

## Phase 1: Setup

**Purpose**: Environment configuration and .env variable setup

- [X] T001 Add RADIUS configuration variables to .env.template (RADIUS_AUTH_TIMEOUT=3, RADIUS_AUTH_RETRIES=2, RADIUS_FAST_DOT1X=true)
- [X] T002 Add RADIUS configuration variables to user's .env file with default values

**Checkpoint**: .env variables configured for RADIUS settings

---

## Phase 2: Foundational (Core Class Structure)

**Purpose**: Create BulkRadiusWLANConfigManager class skeleton with environment loading

**⚠️ CRITICAL**: Class structure must be complete before implementing user story features

- [X] T003 Create BulkRadiusWLANConfigManager class skeleton after line ~46060 in MistHelper.py
- [X] T004 Implement `__init__` method with mistapi_session parameter
- [X] T005 Implement `_load_env_config()` method to read RADIUS_AUTH_TIMEOUT, RADIUS_AUTH_RETRIES, RADIUS_FAST_DOT1X from .env
- [X] T006 Implement `_display_config()` method to show loaded .env values at startup (FR-005a)
- [X] T007 Register Menu 122 in menu_actions dict at line ~50400 in MistHelper.py

**Checkpoint**: Menu 122 accessible, displays loaded .env configuration values

---

## Phase 3: User Story 1 - Scan and Configure RADIUS WLANs (Priority: P1) 🎯 MVP

**Goal**: NOC engineer can scan org WLANs, select RADIUS-enabled networks, and apply timer configuration

**Independent Test**: Run Menu 122 → see RADIUS WLANs listed → select one → confirm changes applied

### Implementation for User Story 1

- [X] T008 [US1] Implement `_scan_org_wlans()` method using listOrgWlans API (FR-001)
- [X] T009 [US1] Implement `_filter_radius_wlans()` method reusing `_uses_radius_auth()` helper at line ~45627; exclude WLANs already at target settings (FR-002, FR-009)
- [X] T010 [US1] Implement `_display_wlans()` method showing indexed list with SSID name/ID and inheritance level (site vs template) (FR-003, FR-007)
- [X] T011 [US1] Implement `_parse_selection()` method reusing `_parse_selection_input()` at line ~37313 (FR-003a)
- [X] T012 [US1] Implement `_apply_changes()` method using updateOrgWlan API with 300ms delay (FR-005)
- [X] T013 [US1] Implement `manage()` main entry point orchestrating scan→filter→display→select→apply flow
- [X] T014 [US1] Add safe_input wrapper for all user input with EOF handling (FR-010)
- [X] T015 [US1] Add logging for all operations (debug: API responses, info: user progress)

**Checkpoint**: User Story 1 complete - can scan, select, and configure RADIUS WLANs

---

## Phase 4: User Story 2 - Preview Changes Before Apply (Priority: P1)

**Goal**: NOC engineer sees exactly what will change before confirming

**Independent Test**: Run Menu 122 → select WLANs → see preview with SSID names and target values → cancel or proceed

### Implementation for User Story 2

- [X] T016 [US2] Implement `_display_preview()` method showing affected SSIDs, current values, target values (FR-004, FR-005b)
- [X] T017 [US2] Add confirmation prompt with explicit "Type 'APPLY' to proceed" pattern (FR-006)
- [X] T018 [US2] Integrate preview step into `manage()` flow between selection and apply
- [X] T019 [US2] Handle cancellation gracefully with informative message

**Checkpoint**: User Story 2 complete - changes previewed before application

---

## Phase 5: User Story 3 - Audit Trail Export (Priority: P2)

**Goal**: NOC engineer has CSV record of all changes for compliance/troubleshooting

**Independent Test**: Run Menu 122 → apply changes → verify CSV file created in data/ with before/after values

### Implementation for User Story 3

- [X] T020 [US3] Implement `_export_audit_trail()` method generating CSV in data/ directory (FR-008)
- [X] T021 [US3] Define CSV columns: timestamp, wlan_id, wlan_ssid, field_name, old_value, new_value, status
- [X] T022 [US3] Integrate audit export into `manage()` flow after successful apply
- [X] T023 [US3] Add success message showing audit file path

**Checkpoint**: User Story 3 complete - audit CSV generated after each bulk operation

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, edge cases, and documentation updates

- [X] T024 [P] Add error handling for API failures with retry logic
- [X] T025 [P] Handle edge case: no RADIUS WLANs found in org (display message, exit gracefully)
- [X] T026 [P] Handle edge case: invalid selection input (re-prompt with helpful message)
- [X] T027 [P] Handle edge case: partial update failure (report which WLANs failed, continue with others)
- [X] T028 Update README.md operation count and Menu 122 description
- [X] T029 Add version changelog entry with UTC timestamp format (version YY.MM.DD.HH.MM)
- [X] T030 Run quickstart.md validation scenarios to verify implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User Story 1 (P1): Must complete first (MVP)
  - User Story 2 (P2): Can start after Foundational, but integrates with US1 flow
  - User Story 3 (P2): Can start after Foundational, integrates with US1 flow
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Core functionality - must complete first as MVP
- **User Story 2 (P1)**: Adds preview to US1 flow - logically depends on US1
- **User Story 3 (P2)**: Adds audit to US1 flow - logically depends on US1

### Within Each User Story

- Core methods before orchestration
- `manage()` method integrates all pieces
- Error handling added in Polish phase

### Parallel Opportunities

- T001 and T002 can run in parallel (different files)
- T024, T025, T026, T027 can run in parallel (independent error handlers)
- Within US1: T008, T009, T010 can run in parallel (independent methods)

---

## Parallel Example: User Story 1 Methods

```bash
# Launch independent methods together:
Task T008: "Implement _scan_org_wlans() method"
Task T009: "Implement _filter_radius_wlans() method" 
Task T010: "Implement _display_wlans() method"
Task T011: "Implement _parse_selection() method"

# Then sequentially:
Task T012: "Implement _apply_changes() method"
Task T013: "Implement manage() entry point"  # Depends on all above
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T007)
3. Complete Phase 3: User Story 1 (T008-T015)
4. **STOP and VALIDATE**: Test Menu 122 end-to-end
5. Run syntax check: `python -m py_compile MistHelper.py`

### Incremental Delivery

1. Setup + Foundational → Class registered, .env loaded
2. Add User Story 1 → Functional scan/select/apply (MVP!)
3. Add User Story 2 → Preview before apply
4. Add User Story 3 → Audit CSV export
5. Polish → Error handling, docs, deployment

### Single Developer Strategy (Recommended)

1. Complete Setup + Foundational (T001-T007)
2. Implement US1 core methods (T008-T012)
3. Wire up US1 manage() flow (T013-T015)
4. Test MVP locally
5. Add US2 preview (T016-T019)
6. Add US3 audit (T020-T023)
7. Polish and deploy (T024-T030)

---

## Code Insertion Points

| Task | Location in MistHelper.py |
|------|---------------------------|
| T003-T015 | After line ~46060 (after WLANRadiusTimerManager class) |
| T007 | Line ~50400 (menu_actions dict) |

## Reusable Code References

| Pattern | Location | Used In |
|---------|----------|---------|
| `_parse_selection_input()` | Line ~37313 | T011 |
| `_uses_radius_auth()` | Line ~45627 | T009 |
| `listOrgWlans` usage | Line ~45605 | T008 |
| `updateOrgWlan` usage | Line ~46042 | T012 |
| Safe input pattern | agents.md | T014 |

---

## Notes

- All methods belong to `BulkRadiusWLANConfigManager` class
- No additional dependencies required (uses existing mistapi)
- Follows MistHelper class-based architecture (no wrapper functions)
- CSV output to data/ directory per project conventions
- Rate limiting: 300ms delay between API updates (FR-007)
- Total tasks: 30
- Estimated parallel opportunities: 8

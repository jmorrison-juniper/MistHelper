# Tasks: Offline Device Report

**Input**: Design documents from `/specs/015-offline-device-report/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: Unit tests included -- plan.md specifies pytest in `tests/unit/` and CI requires >=70% coverage.

**Organization**: Tasks grouped by user story. US1 (P1) is the MVP; US2 and US3 (P2) add enhancements independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files or non-overlapping regions, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths included in descriptions

---

## Phase 1: Setup

**Purpose**: Create the class skeleton and wire it into MistHelper's menu system and operation registry.

- [X] T001 Create `OfflineDeviceReporter` class with `__init__(self, apisession, org_id)` and `execute()` stub in MistHelper.py (insert after `OrgDeviceStatsExporter` class, ~line 12100)
- [X] T002 [P] Add menu dispatch dict entry `"158": (OfflineDeviceReporter.execute, "Offline Device Report")` in MistHelper.py (~line 54879, after entry "157")
- [X] T003 [P] Add `OperationRegistry._REGISTRY["158"] = {"category": "safe"}` in MistHelper.py (~line 55280, after entry "157")

**Checkpoint**: `python MistHelper.py --menu 158` invokes the stub without errors.

---

## Phase 2: User Story 1 - View Devices Offline Beyond Threshold (Priority: P1) -- MVP

**Goal**: NOC engineer selects menu 158, enters a threshold (default 48h), sees a PrettyTable of offline devices sorted by duration, and gets a CSV saved to `data/`.

**Independent Test**: Run `python MistHelper.py --menu 158`, accept default 48h, verify on-screen table + CSV file in `data/`.

### Implementation for User Story 1

- [X] T004 [US1] Implement `_prompt_threshold()` in MistHelper.py -- use `safe_input()` with default 48h, validate range 1-8760, re-prompt up to 3 times on invalid input then fall back to default 48h, skip prompt entirely in `--test` mode (return 48h immediately), return threshold in hours (FR-002, FR-008, FR-010)
- [X] T005 [US1] Implement `_fetch_data()` in MistHelper.py -- log info "Fetching device stats...", call `APICoreFetchUtils.all_sites_with_limit(org_id)` to build `{site_id: site_name}` lookup dict, then call `listOrgDevicesStats` with `type="all"`, `status="all"`, `limit=1000` + `mistapi.get_all()` for pagination, log info with device count, return `(site_lookup, all_devices)` (FR-001, FR-001a; pattern: lines 42501-42530)
- [X] T006 [US1] Implement `_process_devices()` in MistHelper.py -- filter devices where status != `connected` and `last_seen` older than threshold, handle never-connected (`last_seen` null/0 treated as epoch 0), enrich each device with site name from lookup (fallback `"Unknown Site"`), format `last_seen` as `YYYY-MM-DD HH:MM:SS` (or `"Never Connected"`), compute offline duration as `"X days Y hours"`, sort by duration descending (FR-003, FR-007, FR-009)
- [X] T007 [US1] Implement `_present_results()` in MistHelper.py -- build PrettyTable with columns matching spec (Device Name, Device Type, Site Name, MAC Address, Serial Number, Model, Last Seen, Offline Duration, Status), display max 50 rows with total count note, save full results via `DataExporter.write_with_format_selection(data, filename, api_function_name="listOrgDevicesStats")` with timestamped filename `OfflineDeviceReport_YYYYMMDD_HHMMSS.csv`, write UTF-8 with BOM for Excel compatibility (FR-004, FR-005, SC-003)
- [X] T008 [US1] Wire `execute()` in MistHelper.py -- orchestrate: `_prompt_threshold()` -> `_fetch_data()` -> `_process_devices()` -> `_display_summary()` -> `_present_results()`, pass both `all_devices` (total count for summary) and `offline_records` (filtered list) through the chain, log elapsed time at end for SC-001 performance monitoring, handle edge cases: no devices in org (log info + return), no offline devices beyond threshold (display message + skip CSV), API errors (log error + user-friendly message)

**Checkpoint**: US1 fully functional. Engineer can run menu 158, see offline device table, and find CSV in `data/`.

---

## Phase 3: User Story 2 - Summary Statistics on Screen (Priority: P2)

**Goal**: Before the detail table, display a summary: total devices, offline count, per-type breakdown, top 5 sites.

**Independent Test**: Run report against org with known device states, verify summary counts match.

### Implementation for User Story 2

- [X] T009 [US2] Implement `_display_summary()` as a new method in MistHelper.py -- receives `total_device_count` (int from all_devices length) and `offline_records` (filtered list), prints: total devices in org, total offline beyond threshold, per-type breakdown (APs: X, Switches: Y, Gateways: Z), top 5 sites with most offline devices. Called by `execute()` before `_present_results()` (FR-006)

**Checkpoint**: Summary block displays above the detail table. Counts match actual filtered data.

---

## Phase 4: User Story 3 - Human-Friendly CSV Output (Priority: P2)

**Goal**: CSV file is readable by non-technical staff in Excel/Sheets with clear headers, formatted timestamps, and no overwrite risk.

**Independent Test**: Open generated CSV in Excel/Sheets, verify column headers, timestamp readability, duration formatting.

### Implementation for User Story 3

- [X] T010 [US3] Enhance CSV output in `_present_results()` in MistHelper.py -- ensure UTF-8 with BOM encoding for Excel compatibility (SC-003), confirm column headers exactly match spec order (Device Name, Device Type, Site Name, MAC Address, Serial Number, Model, Last Seen, Offline Duration, Status), verify timestamped filename prevents overwrite across multiple runs, add info log "CSV saved: {path} ({count} devices)" (FR-005, FR-009, SC-003)

**Checkpoint**: CSV opens cleanly in Excel with readable headers and formatted values. Multiple runs produce distinct files.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, tests, and validation across all user stories.

- [X] T011 [P] Update README.md menu table -- add row for operation 158 "Offline Device Report" in the correct position
- [X] T012 [P] Update README.md -- increment operation count and add changelog entry with `version YY.MM.DD.HH.MM` (UTC timestamp)
- [X] T013 [P] Add unit tests in tests/unit/test_offline_device_reporter.py -- test `_prompt_threshold()` validation (valid, boundary, invalid, default, test-mode bypass, 3-retry fallback), `_process_devices()` filtering (threshold boundary, never-connected, all-online, mixed types), `_display_summary()` output (per-type counts, top 5 sites, zero-offline case), `_present_results()` output (50-row cap, empty list), duration/timestamp formatting edge cases
- [X] T014 Run quickstart.md validation -- execute the three usage modes (interactive, direct `--menu 158`, `--test`) and compare output against quickstart.md examples

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies -- start immediately
- **US1 (Phase 2)**: Depends on Phase 1 (class skeleton + menu wiring)
- **US2 (Phase 3)**: Depends on Phase 2 (_present_results() must exist to add summary block)
- **US3 (Phase 4)**: Depends on Phase 2 (CSV output must exist to enhance)
- **Polish (Phase 5)**: Depends on Phases 2-4 (all user stories complete)

### User Story Dependencies

- **US1 (P1)**: Depends only on Setup. This is the MVP -- can ship standalone.
- **US2 (P2)**: Depends on US1 (adds to existing _present_results). Cannot run in parallel with US1.
- **US3 (P2)**: Depends on US1 (enhances CSV from _present_results). Can run in parallel with US2 (different code region within _present_results).

### Within User Story 1

- T004 (threshold) and T005 (fetch) are independent of each other -- could be written in parallel
- T006 (process) depends on T005 (needs data structures from fetch)
- T007 (present) depends on T006 (needs processed records)
- T008 (execute wiring) depends on T004-T007 (orchestrates all methods)

### Parallel Opportunities

```text
# Phase 1: T002 and T003 can run in parallel (different file regions)
T002: Menu dispatch entry (~line 54879)
T003: OperationRegistry entry (~line 55280)

# Phase 2: T004 and T005 can run in parallel (independent methods)
T004: _prompt_threshold() -- user input logic
T005: _fetch_data() -- API call logic

# Phase 5: T011, T012, T013 can all run in parallel (different files)
T011: README menu table
T012: README changelog
T013: Unit tests in tests/unit/
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: User Story 1 (T004-T008)
3. **STOP and VALIDATE**: `python MistHelper.py --menu 158` works end-to-end
4. Can ship with just US1 if needed

### Incremental Delivery

1. Setup + US1 -> Core report functional (MVP)
2. Add US2 -> Summary stats enhance readability
3. Add US3 -> CSV polished for external sharing
4. Polish -> README updated, tests passing, validated

### Class Method Summary (5-Item Rule)

`OfflineDeviceReporter` targets 6 methods. The 5-item rule applies per hierarchy level; the class itself is one item at the Classes level, and its methods are at the Methods level (6 methods is acceptable when each stays under 25 lines):

| Method | US | Responsibility | Lines (est.) |
|--------|----|---------------|-------------|
| `execute()` | All | Orchestrator: prompt -> fetch -> process -> summary -> present | ~15 |
| `_prompt_threshold()` | US1 | Input validation, default 48h, test-mode bypass | ~15 |
| `_fetch_data()` | US1 | Site lookup + device stats API calls + logging | ~15 |
| `_process_devices()` | US1 | Filter, enrich, format, sort | ~25 |
| `_display_summary()` | US2 | Summary block: totals, per-type, top 5 sites | ~20 |
| `_present_results()` | US1+US3 | PrettyTable display + CSV export | ~20 |

---

## Notes

- [P] tasks = different files or non-overlapping file regions, no dependencies
- [Story] labels map tasks to user stories from spec.md for traceability
- All code changes in MistHelper.py -- no new files except tests
- Existing `ENDPOINT_PRIMARY_KEY_STRATEGIES["listOrgDevicesStats"]` PK already defined (composite: `device_id`, `timestamp`) -- no new PK entry needed
- `OperationRegistry` safe classification enables auto-run in `--test` mode with default 48h threshold
- Commit after each phase checkpoint to maintain clean git history

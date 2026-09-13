# Tasks: E911 BSSID Compliance Report

**Input**: Design documents from `specs/182-e911-bssid-report/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files or independent code sections)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- All code changes are in MistHelper.py unless otherwise noted

---

## Phase 1: Setup (Registration & Configuration)

**Purpose**: Register Menu 160 in infrastructure dictionaries that use string keys (no class references yet).

- [X] T001 Add primary key strategy entry `"generateE911BSSIDReport"` to `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict in MistHelper.py
- [X] T002 [P] Add `"160": {"category": "safe"}` to `OperationRegistry._REGISTRY` dict in MistHelper.py

**Checkpoint**: PK strategy and OperationRegistry entries are in place. The `menu_actions` entry (T003) is deferred to Phase 3 after the class exists to avoid a module-level NameError.

---

## Phase 2: Foundational (Not needed)

**Purpose**: No foundational prerequisites — this feature uses existing infrastructure (DataExporter, ConfigUtils, mistapi, OperationRegistry). Proceed directly to User Story 1.

---

## Phase 3: User Story 1 — Generate E911 BSSID Compliance Report (Priority: P1) MVP

**Goal**: Menu 160 queries all AP radio MACs, resolves site/map/AP context, derives BSSIDs, and writes a sorted CSV to `data/`.

**Independent Test**: Run `python MistHelper.py --menu 160`, verify CSV is generated in `data/` with correct columns (Site Name, Site Address, Map Name, AP Name, BSSID), colon-separated BSSID format, and location-hierarchy sort order.

### Implementation for User Story 1

- [X] T004 [US1] Create `E911BSSIDReportGenerator` class skeleton with docstring and class constants in MistHelper.py (place near `OfflineDeviceReporter` class, ~line 12586)
- [X] T005 [US1] Implement `_format_bssid(radio_base_mac: str) -> list[str]` static method — derives 16 colon-separated BSSIDs from a radio base MAC by enumerating last nibble 0x0-0xF in MistHelper.py
- [X] T006 [US1] Implement `_fetch_lookups(org_id: str) -> tuple[dict, dict, dict, list]` static method — calls listOrgSites, listOrgDevicesStats(type=ap), listSiteMaps (per site with APs), listOrgApsMacs; returns site_lookup, ap_lookup, map_lookup, radio_macs_data. Include `logging.info()` progress messages for each API fetch and `logging.debug()` for response counts in MistHelper.py
- [X] T007 [US1] Implement `_build_bssid_rows(radio_macs_data, site_lookup, ap_lookup, map_lookup) -> tuple[list[dict], list[dict]]` static method — iterates radio_macs_data, resolves context via lookups, calls _format_bssid, builds sorted output rows and compliance_gaps list. Handle edge cases: AP MACs missing from device stats (AP Name = "Unknown", flagged as data discrepancy), map_ids missing from map_lookup (Map Name = "Unknown Map", flagged in gaps) in MistHelper.py
- [X] T008 [US1] Implement `_display_summary(total_sites, total_aps, total_bssids, compliance_gaps)` static method — prints site/AP/BSSID counts + compliance gap section listing AP names without map assignments in MistHelper.py
- [X] T009 [US1] Implement `execute()` static method — orchestrates get org_id, call `_fetch_lookups`, call `_build_bssid_rows`, handle empty-org case, call `DataExporter.write_with_format_selection` with `api_function_name="generateE911BSSIDReport"`, call `_display_summary`. Include `logging.info()` for report generation progress in MistHelper.py
- [X] T003 [US1] Add `"160": (E911BSSIDReportGenerator.execute, "E911 BSSID Compliance Report")` to `menu_actions` dict in MistHelper.py (placed after class definition to avoid NameError)

**Checkpoint**: Menu 160 produces a complete E911 BSSID CSV with correct columns, sort order, and BSSID format. On-screen summary shows site/AP/BSSID counts and compliance gaps. `--test` mode runs without interaction.

---

## Phase 4: User Story 3 — SQLite Dual Output (Priority: P3)

**Goal**: BSSID data is written to SQLite when user selects SQLite output mode, with `bssid` as natural primary key for upsert.

**Independent Test**: Configure `--output-format sqlite`, run Menu 160, verify data appears in `data/mist_data.db` with correct table and primary key.

### Implementation for User Story 3

- [X] T010 [US3] Verify `DataExporter.write_with_format_selection()` call in T009 passes `api_function_name="generateE911BSSIDReport"` matching the `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry (type `natural_pk`) added in T001 in MistHelper.py

**Checkpoint**: SQLite output works. Re-running Menu 160 upserts (no duplicate BSSIDs).

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates and deployment validation.

- [X] T011 [P] Update README.md menu table: add Menu 160 row, increment operation count
- [X] T012 [P] Update README.md changelog: add `version YY.MM.DD.HH.MM - E911 BSSID Compliance Report (Menu 160)` entry
- [X] T013 Validate syntax with `python -m py_compile MistHelper.py`
- [X] T014 Run `python MistHelper.py --test` and confirm Menu 160 executes in safe category

**Checkpoint**: All code compiles, tests pass, documentation is updated, ready for deployment pipeline.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — can start immediately
- **Phase 3 (US1+US2 - Core Report + Gap Detection)**: Depends on Phase 1 (T001-T002 register PK and category)
- **Phase 4 (US3 - SQLite)**: Depends on T001 (PK strategy) and T009 (execute calls DataExporter)
- **Phase 5 (Polish)**: Depends on all user stories complete

### Within Phase 3 (User Story 1 + 2)

```text
T004 (class skeleton)
  ├── T005 (_format_bssid) — no other dependencies
  ├── T006 (_fetch_lookups) — no other dependencies
  │     └── T007 (_build_bssid_rows) — depends on T005, T006
  │           └── T008 (_display_summary) — no external deps, can parallel with T007
  │                 └── T009 (execute) — depends on T007, T008
  │                       └── T003 (menu_actions entry) — depends on T004 (class must exist)
```

### Parallel Opportunities

- T001 and T002 can run in parallel (different dicts in MistHelper.py)
- T005 and T006 can run in parallel (independent methods)
- T007 and T008 can run in parallel (independent methods)
- T011 and T012 can run in parallel (different README sections)

---

## Implementation Strategy

**MVP**: Phase 1 + Phase 3 (T001-T002, T004-T009, T003) delivers the core E911 report with compliance gap detection. A NOC engineer can generate the CSV and file it for compliance immediately.

**Incremental delivery**:
1. T001-T002, T004-T009, T003: Core report generation + gap detection (MVP)
2. T010: SQLite dual output verification (historical tracking)
3. T011-T014: Documentation and validation

**Total tasks**: 14
**Tasks per user story**: US1+US2: 8 (T004-T009, T003, and T008 covers US2), US3: 1
**Parallel opportunities**: 4 groups (T001+T002, T005+T006, T007+T008, T011+T012)
**Suggested MVP scope**: Phase 1 + Phase 3 (all core functionality)

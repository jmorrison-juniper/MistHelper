# Tasks: Org Config Export/Import (Cross-Org Migration)

**Input**: Design documents from `/specs/191-org-config-export-import/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/export-bundle-schema.md

**Tests**: Not explicitly requested in the spec. Test metadata entries are included as part of menu registration (T001). Manual testing via quickstart.md.

**Organization**: Tasks follow the dependency graph from plan.md. All code goes into MistHelper.py (single-file architecture). The class `OrgConfigMigrationManager` is added near `WAN2MigrationManager` (~line 22783).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Class Skeleton & Menu Registration)

**Purpose**: Create the class skeleton, CONFIG_TYPES registry, constants, menu entries, and test metadata so subsequent tasks have a structure to build on.

- [ ] T001 Create `OrgConfigMigrationManager` class skeleton in MistHelper.py near `WAN2MigrationManager` (~line 22783) with: `__init__(self, apisession, org_id_fn, safe_input_fn)`, empty public methods `export_config()` and `import_config()`, `CONFIG_TYPES` class-level list (6 entries with key/list_fn/create_fn/import_order/display_name/has_subnet/has_addresses/list_kwargs per plan.md), `STRIP_FIELDS` constant set (`{"id", "org_id", "created_time", "modified_time", "for_site"}`), menu entries 176 and 177 in the OPERATIONS dict (lambda pattern per plan.md), and `TEST_OPERATION_METADATA` entries (176=safe, 177=destructive with skip_reason)

**Checkpoint**: MistHelper.py compiles (`python -m py_compile MistHelper.py`), menu 176/177 appear in menu listing, `--test` recognizes new entries

---

## Phase 2: User Story 1 - Export Org WAN/Gateway Configuration (Priority: P1)

**Goal**: Menu 176 fetches all 6 config types from the current org and saves a timestamped JSON bundle to `data/`.

**Independent Test**: Run `--menu 176` against any org. Verify the output JSON contains metadata + all 6 type keys with correct counts.

- [ ] T002 [US1] Implement `_fetch_config_type(self, config_type_entry)` private method in `OrgConfigMigrationManager` in MistHelper.py — calls `config_type_entry["list_fn"](self.apisession, self.org_id, limit=1000, **config_type_entry.get("list_kwargs", {}))`, extracts the list from API response, handles API errors with try/except (logs error, returns empty list), returns `list[dict]`

- [ ] T003 [US1] Implement `_build_export_bundle(self, results: dict)` and `_save_bundle_to_file(self, bundle: dict)` private methods in MistHelper.py — `_build_export_bundle` wraps results dict with metadata (source_org_id, source_org_name via `self.apisession`, export_timestamp ISO 8601, misthelper_version from VERSION constant, object_counts per type); `_save_bundle_to_file` writes to `data/OrgConfig_Export_{org_name}_{YYYYMMDD_HHMMSS}.json` using `json.dump(indent=2)` with `os.path.join()` for path

- [ ] T004 [US1] Implement `_display_export_summary(self, bundle: dict)` and wire up `export_config(self)` public method in MistHelper.py — `_display_export_summary` prints a table of type names and counts from metadata; `export_config` gets org_id, iterates CONFIG_TYPES calling `_fetch_config_type`, builds bundle, saves file, displays summary; handles partial failures (continues on per-type errors)

**Checkpoint**: `python MistHelper.py --menu 176` produces a valid JSON file in `data/` with all 6 type arrays and metadata

---

## Phase 3: User Story 2 - Import Org Config Into Destination Org (Priority: P1)

**Goal**: Menu 177 loads an export bundle, creates all non-conflicting objects in the destination org in dependency order, and displays a summary report.

**Independent Test**: Export from org A (Menu 176), switch `.env` to org B, run Menu 177 with dry-run. Verify report shows all objects as "would import".

- [ ] T005 [US2] Implement `_select_import_file(self)` and `_load_and_validate_bundle(self, filepath: str)` private methods in MistHelper.py — `_select_import_file` globs `data/OrgConfig_Export_*.json` using `glob.glob()` + `os.path.join()`, numbers files for selection, uses `safe_input()` for user choice, auto-selects if only one file; `_load_and_validate_bundle` parses JSON, validates required keys per contracts/export-bundle-schema.md (metadata with source_org_id, all 6 type keys), checks version mismatch (warning only), returns parsed bundle dict or raises ValueError

- [ ] T006 [US2] Implement `_strip_source_fields(self, obj: dict)` helper, `_prompt_dry_run(self)`, `_confirm_import(self)`, and `_display_import_report(self, results: list)` private methods in MistHelper.py — `_strip_source_fields` removes STRIP_FIELDS keys from a copy of obj and returns the cleaned copy; `_prompt_dry_run` uses `safe_input()` to ask "Run as dry-run? [Y/n]", returns bool; `_confirm_import` requires user to type "IMPORT" via `safe_input()`, returns bool; `_display_import_report` prints three-section table (imported/skipped/failed) with object_type, object_name, status, and reason columns

- [ ] T007 [US2] Implement `_execute_import(self, bundle: dict, dry_run: bool)` and wire up `import_config(self)` public method in MistHelper.py — `_execute_import` iterates CONFIG_TYPES sorted by import_order, for each object: strips source fields, checks conflicts (calls T008 methods, initially stub returns None), if no conflict and not dry_run: calls `create_fn(self.apisession, self.org_id, body=obj)`, records ImportResult (imported/skipped/failed) with new_id, builds remap table entries; `import_config` calls `_select_import_file` → `_load_and_validate_bundle` → `_fetch_existing_objects` → `_prompt_dry_run` → `_confirm_import` (if not dry_run) → `_execute_import` → `_display_import_report`

**Checkpoint**: Menu 177 can load a bundle, prompt for dry-run/confirmation, create objects (when conflict detection returns None), and display the report

---

## Phase 4: User Story 3 - Conflict Detection and Reporting (Priority: P1)

**Goal**: Before creating objects, detect name matches and IP/subnet overlaps. Skipped objects include conflict reasons in the report.

**Independent Test**: Import the same bundle twice into the same org. Second run should show 100% skipped with conflict reasons.

- [ ] T008 [US3] Implement `_fetch_existing_objects(self)`, `_detect_conflicts(self, new_obj, existing_list, type_key)`, `_check_name_conflict(self, new_obj, existing_list)`, and `_check_subnet_overlap(self, new_obj, existing_list, type_key)` private methods in MistHelper.py — `_fetch_existing_objects` calls each CONFIG_TYPE's list_fn against destination org and stores results in `self._existing` dict keyed by type key; `_check_name_conflict` compares `new_obj.get("name")` against existing names (case-insensitive); `_check_subnet_overlap` uses `ipaddress.ip_network(strict=False).overlaps()` for networks (subnet field) and services (addresses[] field) per plan.md algorithm; `_detect_conflicts` orchestrates both checks and returns first ConflictRecord found or None; wire conflict detection into T007's `_execute_import` loop (replace stub)

**Checkpoint**: Importing the same bundle twice results in all objects skipped with "name_match" conflict reasons. Network subnet overlaps are detected.

---

## Phase 5: User Story 4 - Cross-Reference ID Remapping (Priority: P2)

**Goal**: When importing objects that reference other objects by source-org ID, remap those IDs to the newly created destination-org IDs.

**Independent Test**: Export config where service policies reference services, import into clean org, verify service policies reference the new service IDs.

- [ ] T009 [US4] Implement `_build_remap_entry(self, source_id, dest_id)` and `_remap_object_references(self, obj, type_key)` private methods in MistHelper.py — `_build_remap_entry` adds source_id→dest_id to `self._remap_table` dict; `_remap_object_references` walks known reference fields per type (VPNs: network IDs in `networks` dict; gateway_templates: network/VPN IDs; device_profiles: `gateway_template_id`; service_policies: service IDs in `services[]`), replaces source IDs with destination IDs from remap table, logs warning if referenced ID not found in remap table; also populate remap table for skipped-by-name objects (look up existing object's ID by name match); wire into T007's `_execute_import` loop — call `_remap_object_references` before `create_fn` for tier 1+ objects, call `_build_remap_entry` after successful creates and after name-match skips

**Checkpoint**: Service policies imported with correct destination service IDs. Gateway templates reference correct destination network/VPN IDs.

---

## Phase 6: Polish & Validation

**Purpose**: Final quality gates, documentation updates, and end-to-end verification.

- [ ] T010 Update README.md operation count and menu table to include Menu 176 and Menu 177 entries, update CHANGELOG.md with new version entry documenting the Org Config Export/Import feature, and run quality gates (`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`)

**Checkpoint**: All quality gates pass, README reflects new operations, CHANGELOG has version entry

---

## Dependencies

```text
T001 (skeleton) ──────────────────────────────────────────────────────┐
  │                                                                   │
  ├── T002 (fetch) ── T003 (bundle/save) ── T004 (export_config)     │
  │                        US1 complete ✓                             │
  │                                                                   │
  ├── T005 (file select/validate) ── T006 (helpers) ── T007 (import) │
  │                                       US2 complete ✓              │
  │                                                                   │
  ├── T008 (conflict detection) ─────────── wires into T007           │
  │                                       US3 complete ✓              │
  │                                                                   │
  └── T009 (ID remapping) ──────────────── wires into T007            │
                                          US4 complete ✓              │
                                                                      │
  T010 (polish) ◄─────────────────────────────────────────────────────┘
```

**User Story 5 (Idempotent Re-Import)** is satisfied by User Stories 2+3 combined — no additional tasks needed. Conflict detection (T008) ensures re-importing the same bundle skips all objects.

## Parallel Opportunities

| Tasks | Why Parallelizable |
| - | - |
| T002, T005 | After T001: export fetch and import file selection work on different concerns |
| T003, T006 | After T002/T005 respectively: bundle building and import helpers are independent |

## Implementation Strategy

1. **MVP (Phase 1-2)**: Menu 176 export works end-to-end. Immediately useful for config snapshots.
2. **Core Import (Phase 3)**: Menu 177 creates objects without conflict detection (trusts clean destination org).
3. **Safety Layer (Phase 4)**: Conflict detection prevents duplicates and overlaps.
4. **Fidelity (Phase 5)**: ID remapping ensures cross-references are correct.
5. **Ship (Phase 6)**: Documentation and quality gates.

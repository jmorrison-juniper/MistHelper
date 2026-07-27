---

description: "Task list for feature 1029-ap-profile-migration"
---

# Tasks: Migrate APs Between Device Profiles (with Revert)

**Input**: Design documents from `/specs/1029-ap-profile-migration/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Included. Unit tests plus one integration-style test per user story (US1 / US2 / US3) are called out in `plan.md` (Technical Context / Testing) and are required by SC-006.

**Organization**: Tasks are grouped by user story so each story can be delivered and validated independently. Menu 207 (migrate) is the MVP. Menu 208 (revert) is the safety-net add-on. Dry-run (US3) rides on menu 207.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Different file, no dependency on incomplete tasks — safe to parallelize.
- **[Story]**: `US1`, `US2`, or `US3` maps to the user stories in `spec.md`.

## Path Conventions

Single-project CLI layout. Source under `src/`, tests under `tests/`, telemetry / backups under `data/`. All paths in this file are relative to the repository root
`c:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify the environment and existing helpers are ready. No source changes here.

- [X] T001 Verify Python 3.13+ is on `PATH` (`python --version`); verify `pip install -e .` succeeds in a clean venv; verify `mistapi>=0.63.1` is importable — no new dependency is added by this feature (FR-003).
- [X] T002 [P] Verify existing helpers this feature depends on are present and importable: `safe_input` at `src/utils/input_utils.py`, `TelemetryEmitter` at `src/analytics/telemetry_emitter.py`, and the guardrail lives at `src/utils/operation_registry.py`. Record their import paths in a short scratchpad under `specs/1029-ap-profile-migration/` if any drifted from `plan.md`.
- [X] T003 [P] Confirm `data/` exists at the repository root and is writable (`mkdir -p data && test -w data`). The migration backup writer and the revert audit line both write under this directory.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Register the two new menu entries in the destructive guardrail and skeleton the module + test file so every user-story phase can add methods and cases without stepping on unrelated code.

**CRITICAL**: No US1 / US2 / US3 task may start until this phase is complete. Menu numbers 207 and 208 MUST be classified `destructive` before any handler code is committed, or the CI guardrail fails (SC-006).

- [X] T004 Add entries `"207"` and `"208"` to `OPERATION_CATEGORIES` in `src/utils/operation_registry.py`, both with `category = "destructive"` and a `skip_reason` string that names the operation (STE-compliant): 207 = "Menu 207 mutates AP-to-device-profile bindings across every site in the selected organization; requires a live Mist test tenant.", 208 = "Menu 208 reverts a prior AP-to-device-profile migration by reassigning each listed AP back to its original device profile; requires the backup file written by menu 207." (FR-001, SC-006).
- [X] T005 Create the empty class skeleton `src/device/ap_profile_migration_manager.py` with a module docstring, `class APProfileMigrationManager`, class docstring, and two placeholder public static methods (`migrate_aps_between_device_profiles`, `revert_ap_profile_migration`) each returning `None` and each carrying a Google-style docstring with a "Why" section (FR-004). Ensure `interrogate` sees the file at 100 percent.
- [X] T006 [P] Create the test-file skeleton `tests/unit/device/test_ap_profile_migration_manager.py` with an empty pytest module, module docstring, and one `test_placeholder_manager_importable()` case that only imports `APProfileMigrationManager` — this proves T005 is wired up so downstream test tasks have somewhere to add cases without merge conflicts.
- [X] T007 [P] Add a registry classification test at `tests/unit/utils/test_operation_registry_1029.py` that asserts entry `"207"` and entry `"208"` both exist in `OPERATION_CATEGORIES` with `category == "destructive"` and non-empty `skip_reason`. This locks in FR-001 and gives the guardrail a direct assertion beyond the existing lint (SC-006).
- [X] T008 Wire menu options 207 and 208 into `MistHelper.py` menu dispatch (matching the existing pattern used by menu 206 / menu 174). Both entries invoke the corresponding static methods on `APProfileMigrationManager`. Menu label text MUST be STE-compliant: 207 = "Migrate APs between device profiles", 208 = "Revert an AP profile migration from a backup file" (FR-002, SC-007).

**Checkpoint**: Guardrail passes for the two new entries. Module and test skeletons import cleanly. US1 / US2 / US3 phases can now proceed in parallel (T009+ / T017+ / T028+).

---

## Phase 3: User Story 1 - Bulk migrate APs to a new device profile (Priority: P1) - MVP

**Goal**: Give the operator one menu selection that discovers every AP bound to a chosen source device profile, writes a full pre-change JSON backup under `data/`, then per-AP PUT-s each AP to the chosen target profile with bounded retry and stop-on-first-failure semantics.

**Independent Test**: Run menu 207 against a Mist test org where at least one AP is bound to a source profile (see `quickstart.md` Scenario 1). Confirm every AP moves to the target profile, a single backup file appears under `data/` with `outcome == "success"`, and progress prints at least every 10 APs.

### Tests for User Story 1 (write FIRST; must FAIL before implementation)

- [X] T009 [P] [US1] Unit test in `tests/unit/device/test_ap_profile_migration_manager.py`: `test_migrate_refuses_when_source_equals_target()` — with a mocked `mistapi` session, selecting the same profile for source and target MUST print an STE-compliant error and issue zero PUT calls (FR-008, Acceptance Scenario 3).
- [X] T010 [P] [US1] Unit test: `test_migrate_reports_nothing_to_migrate_when_source_empty()` — when the AP-discovery helper returns an empty list, the migration MUST print "No APs bound to source profile. Nothing to migrate.", write zero files under `data/`, and issue zero PUT calls (FR-010, Acceptance Scenario 2).
- [X] T011 [P] [US1] Unit test: `test_migrate_writes_backup_before_any_put()` — patch `updateSiteDevice` and the backup writer so the backup writer records a call-order marker. Assert the backup file write happens strictly before the first `updateSiteDevice` call (FR-011).
- [X] T012 [P] [US1] Unit test: `test_migrate_backup_shape_matches_data_model_section_1_3()` — build a fixture with two APs across two sites, run migration, load the written JSON, and assert every top-level field named in `data-model.md` section 1.3 is present with the correct type (`schema_version == 1`, `org_id`, `migration_timestamp_utc`, `source_profile_id`, `target_profile_id`, `source_profile_snapshot.id == source_profile_id`, `target_profile_snapshot.id == target_profile_id`, `aps_planned` is a list of `APRecord`, `aps_reassigned` is a list, `outcome`, `failure_detail`) (FR-013, data-model 1.3 / 1.4 / 1.6).
- [X] T013 [P] [US1] Unit test: `test_migrate_retries_transient_put_failure_then_succeeds()` — patch `updateSiteDevice` to raise a transient exception twice then return success. Assert the AP is recorded as reassigned, the retry cadence matches the plan (2 retries with 0.5 s then 1.0 s backoff — verify via a patched `time.sleep` capturing the sequence `[0.5, 1.0]`), and no failure is reported (research.md Decision 2).
- [X] T014 [P] [US1] Unit test: `test_migrate_stops_on_second_retry_exhaustion_and_records_partial_success()` — with 5 planned APs, patch `updateSiteDevice` to succeed for APs 0 and 1 and always fail for AP 2. Assert exactly APs 0 and 1 appear in `aps_reassigned`, `outcome == "partial"`, `failure_detail.failed_device_id == aps[2].device_id`, `failure_detail.reassigned_count == 2`, `failure_detail.planned_count == 5`, and no PUT is issued for APs 3 or 4 (FR-017, data-model 1.5 / 1.7).
- [X] T015 [P] [US1] Unit test: `test_migrate_progress_prints_at_least_every_10_aps()` — with 27 planned APs, capture `caplog` at INFO and assert progress lines appear at N=1, at every N%10==0, and at N=27 (research.md Decision 3, SC-004).
- [X] T016 [P] [US1] Integration-style test: `test_us1_end_to_end_with_mocked_mistapi_session()` — one test that drives the full public entry point `APProfileMigrationManager.migrate_aps_between_device_profiles()` against a fully mocked `mistapi` session that returns 2 sites and 3 APs bound to the source profile plus 1 AP bound to the target profile. Feeds a stubbed `safe_input` that returns `"MIGRATE"`. Asserts: 3 APs reassigned, backup file written under a `tmp_path`-monkeypatched `data/` directory, `outcome == "success"`, and the printed summary lines include the source name, target name, backup absolute path, and online/offline split (US1 Acceptance Scenario 1, quickstart.md Scenario 1).

### Implementation for User Story 1

- [X] T017 [US1] Add private static helper `_pick_ap_device_profile(session, org_id, prompt_text)` on `APProfileMigrationManager` in `src/device/ap_profile_migration_manager.py`. Wraps `mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles`, filters to `type == "ap"`, presents the operator picker via the existing MistHelper selection helper, and returns `(profile_id, profile_name, profile_json)`. Google-style docstring with a "Why" section (FR-007, FR-004).
- [X] T018 [US1] Add private static helper `_discover_aps_on_source_profile(session, org_id, source_profile_id)` that walks every site in the org (`mistapi.api.v1.orgs.sites.listOrgSites`) and lists AP devices per site (`mistapi.api.v1.sites.devices.listSiteDevices(..., type="ap")`), filters to `deviceprofile_id == source_profile_id`, and returns a list of `APRecord` dicts shaped per `data-model.md` §1.4 (device_id, site_id, mac, hostname). Emits `logger.info` progress per site scanned. Docstring per DOCS.md (FR-009).
- [X] T019 [US1] Add private static helper `_render_migration_plan(source, target, ap_records)` that prints the operator-visible plan block (device_id, hostname or "-", site) and the total line `Total: N APs will be reassigned from <source-name> to <target-name>` — all strings STE-compliant (FR-002).
- [X] T020 [US1] Add private static helper `_confirm_migration(count, source_name, target_name)` that calls `safe_input(...)` from `src/utils/input_utils.py` and accepts one of the exact uppercase keywords `MIGRATE` or `DRY-RUN`. Returns `"live"`, `"dry_run"`, or `"cancel"`. Docstring lists all three return values and their meaning (FR-005, FR-015, research Decision 5).
- [X] T021 [US1] Add private static helper `_build_backup_payload(org_id, source_id, source_json, target_id, target_json, ap_records)` returning the dict described in `data-model.md` §1.3, with `schema_version = 1`, `migration_timestamp_utc = datetime.now(timezone.utc).isoformat(...)` normalized to `Z`, `aps_reassigned = []`, `outcome = "success"`, `failure_detail = None`. Docstring with Why (FR-013).
- [X] T022 [US1] Add private static helper `_write_backup_file(payload, data_dir)` that computes the filename per `data-model.md` §1.1 (`ap-profile-migration_<YYYYMMDDTHHMMSSZ>_<source>_to_<target>.json`), writes with `pathlib.Path.write_text(json.dumps(payload, indent=2, sort_keys=False), encoding="utf-8")`, and returns the absolute path. Raises `OSError` on write failure (FR-011, FR-012, research Decision 7).
- [X] T023 [US1] Add private static helper `_reassign_one_ap(session, ap_record, target_profile_id, *, sleeper=time.sleep)` that PUT-s the AP via `mistapi.api.v1.sites.devices.updateSiteDevice(session, ap_record["site_id"], ap_record["device_id"], body={"deviceprofile_id": target_profile_id})` with bounded retry: 2 retries, backoff `[0.5, 1.0]` seconds via the injected `sleeper` (test seam). Returns on success; re-raises the last exception after retry exhaustion. Add a short `#` comment explaining the bounded-retry constraint (Constitution Principle VI, research Decision 2).
- [X] T024 [US1] Add private static helper `_run_reassignment_loop(session, ap_records, target_id, backup_path, progress_stride=10)` that iterates `ap_records`, calls `_reassign_one_ap` per element, appends the device_id to the on-disk backup's `aps_reassigned` list after each success (re-serialize the file), prints progress at N=1, every `progress_stride`, and at N=len, and on any exception updates `outcome`, `failure_detail.*` per `data-model.md` §1.5, re-writes the backup file, and re-raises. Add `#` comment explaining why the file is re-written after every success (safety for interrupted runs) (FR-017, SC-004).
- [X] T025 [US1] Implement the public entry point `APProfileMigrationManager.migrate_aps_between_device_profiles(session=None)` orchestrating: org selection (reuse existing helper), `_pick_ap_device_profile` twice, refuse if source == target (FR-008), `_discover_aps_on_source_profile`, nothing-to-migrate short circuit (FR-010), `_render_migration_plan`, `_confirm_migration`, dry-run short circuit (FR-015), `_build_backup_payload`, `_write_backup_file` (raise before any PUT if this fails per FR-011), `_run_reassignment_loop`, then print the end-of-run summary line (source name/ID, target name/ID, planned, reassigned, online/offline, backup path). Log `logger.warning("Menu #207 DESTRUCTIVE: migrate APs started")` at start (Constitution Principle V) (FR-005, FR-006, FR-010, FR-011, FR-015, FR-016, FR-017, FR-018).
- [X] T026 [US1] Run `pytest tests/unit/device/test_ap_profile_migration_manager.py -v` for T009-T016; iterate until all pass. Then run `ruff check .`, `black --check .`, `mypy src/device/ap_profile_migration_manager.py`, `interrogate -f 90 src/device/ap_profile_migration_manager.py`, `pydoclint --style=google src/device/ap_profile_migration_manager.py`, and the ASD-STE100 lint from feature 1026 against the new module — every command MUST exit 0 (FR-002, FR-004, SC-007).
- [ ] T027 [US1] Manual live-run validation: execute `quickstart.md` Scenario 1 against a Mist test org. Confirm the backup file, the progress cadence, the summary content, and that every AP moved to the target profile (US1 Acceptance Scenario 1, SC-001, SC-002).

**Checkpoint (MVP)**: Menu 207 works end-to-end against a live test org. Stop here and demo if the revert (US2) is not yet ready — Story 1 delivers standalone value per `spec.md` "Why this priority".

---

## Phase 4: User Story 2 - Revert a prior migration from its backup file (Priority: P2)

**Goal**: Give the operator one menu selection that reads a backup file written by menu 207 and reassigns each listed AP back to its original source device profile, with strict backup-schema validation, source-profile-still-exists guard, per-AP missing-AP tolerance, and a JSONL audit line appended via the existing `TelemetryEmitter`.

**Independent Test**: Run menu 207 once (Phase 3 must be complete), then run menu 208 against the produced backup and confirm every listed AP is back on the original source profile and a JSONL audit line was appended (see `quickstart.md` Scenario 3).

### Tests for User Story 2 (write FIRST; must FAIL before implementation)

- [X] T028 [P] [US2] Unit test: `test_revert_rejects_backup_with_wrong_schema_version()` — a backup fixture with `schema_version = 99` MUST cause the revert to fail with a message naming `schema_version` and issue zero PUTs (FR-020, data-model 1.6 rule 1).
- [X] T029 [P] [US2] Unit test: `test_revert_rejects_backup_with_missing_required_fields()` — for each required field (`org_id`, `source_profile_id`, `target_profile_id`, `migration_timestamp_utc`, `aps_planned`), remove it and assert the revert refuses with an error naming that field and issues zero PUTs (FR-020, data-model 1.6 rules 2-4).
- [X] T030 [P] [US2] Unit test: `test_revert_rejects_backup_when_aps_reassigned_contains_unknown_id()` — a backup whose `aps_reassigned` lists a `device_id` that is not in `aps_planned` MUST be refused (FR-020, data-model 1.6 rule 5).
- [X] T031 [P] [US2] Unit test: `test_revert_refuses_when_source_profile_deleted_from_org()` — patch `getOrgDeviceProfile(source_profile_id)` to raise 404. Assert the revert names the missing profile ID, tells the operator to recreate the profile or edit the backup file, issues zero PUTs, and (per T036 audit implementation) records `outcome == "failure"` in the JSONL audit line (FR-021, Acceptance Scenario 2, quickstart Scenario 6).
- [X] T032 [P] [US2] Unit test: `test_revert_skips_missing_ap_and_reports_partial()` — a 5-AP backup where one AP returns 404 on PUT MUST reassign the other 4, report the missing AP by ID in the summary, return success with a warning, and record `outcome == "partial"`, `missing_count == 1` in the audit line (FR-023, Acceptance Scenario 3, quickstart Scenario 7).
- [X] T033 [P] [US2] Unit test: `test_revert_never_touches_aps_not_in_backup()` — patch `updateSiteDevice` and assert it is only invoked for `device_id` values that appear in `aps_planned` (FR-022, Acceptance Scenario 4).
- [X] T034 [P] [US2] Unit test: `test_revert_appends_jsonl_audit_line_via_telemetry_emitter()` — patch `TelemetryEmitter.emit` and assert one call whose payload matches `data-model.md` §2.2 exactly: `event_type == "ap_profile_migration_revert"`, `timestamp_utc`, `org_id`, `backup_file_path`, `source_profile_id`, `planned_count`, `reverted_count`, `missing_count`, `failed_count`, `outcome` (FR-025).
- [X] T035 [P] [US2] Integration-style test: `test_us2_end_to_end_with_mocked_mistapi_session()` — produce a valid backup fixture on `tmp_path`, drive the full public entry point `APProfileMigrationManager.revert_ap_profile_migration()` with a stubbed `safe_input` returning `"REVERT"` and a mocked `mistapi` session where `getOrgDeviceProfile(source_id)` succeeds and every `updateSiteDevice` succeeds. Assert every listed AP was PUT with `deviceprofile_id = <original source>`, one telemetry emission recorded `outcome == "success"`, and the summary print names the backup path (US2 Acceptance Scenario 1, quickstart Scenario 3).

### Implementation for User Story 2

- [X] T036 [US2] Add private static helper `_list_backup_files(data_dir)` in `src/device/ap_profile_migration_manager.py` that globs `data/ap-profile-migration_*.json`, parses the timestamp and source-to-target profile IDs from the filename, and returns a list sorted newest-first. Docstring with Why (FR-019).
- [X] T037 [US2] Add private static helper `_pick_backup_file(candidates)` that renders the candidate list with timestamps + source/target IDs and returns the chosen `pathlib.Path` (FR-019).
- [X] T038 [US2] Add private static helper `_load_and_validate_backup(path)` that reads the JSON, runs every rule in `data-model.md` §1.6 (1-6), and raises `ValueError` with the offending field named. Return the validated `dict` (FR-020).
- [X] T039 [US2] Add private static helper `_verify_source_profile_exists(session, org_id, source_profile_id)` that calls `mistapi.api.v1.orgs.deviceprofiles.getOrgDeviceProfile` and returns `True` on 200 / `False` on 404. On any other error, re-raise (FR-021).
- [X] T040 [US2] Add private static helper `_confirm_revert(count, source_name, backup_path)` that calls `safe_input(...)` with the exact uppercase keyword `REVERT`. Returns `"live"` or `"cancel"` (FR-005, research Decision 5).
- [X] T041 [US2] Add private static helper `_revert_one_ap(session, device_id, site_id, source_profile_id, *, sleeper=time.sleep)` mirroring T023 (2 retries with `[0.5, 1.0]` backoff). Distinguishes a 404 (AP no longer exists — return `"missing"`) from any other failure (raise after retry exhaustion) so T032 can drive the missing-AP path (FR-023).
- [X] T042 [US2] Add private static helper `_emit_revert_audit(payload)` that writes one JSONL row via the existing `TelemetryEmitter` in `src/analytics/telemetry_emitter.py`. Field set matches `data-model.md` §2.2. Add a `#` comment explaining that the emit is best-effort and MUST NOT raise (Constitution Principle VI, FR-025).
- [X] T043 [US2] Implement the public entry point `APProfileMigrationManager.revert_ap_profile_migration(session=None)` orchestrating: `_list_backup_files`, `_pick_backup_file`, `_load_and_validate_backup`, `_verify_source_profile_exists` (fail loudly + audit `outcome="failure"` and return per FR-021), `_confirm_revert`, iterate `aps_reassigned` (defensively fall back to `aps_planned` if `aps_reassigned` is empty per T014's partial-success semantics), call `_revert_one_ap` per entry, aggregate counts (`reverted_count`, `missing_count`, `failed_count`), decide `outcome` (success / partial / failure), print the summary (FR-024), and finally call `_emit_revert_audit`. Start with `logger.warning("Menu #208 DESTRUCTIVE: revert AP profile migration started")` (Constitution Principle V) (FR-005, FR-019, FR-020, FR-021, FR-022, FR-023, FR-024, FR-025).
- [X] T044 [US2] Run `pytest tests/unit/device/test_ap_profile_migration_manager.py -v` for T028-T035 plus the still-green US1 cases from T026; iterate until all pass. Re-run `ruff / black / mypy / interrogate / pydoclint / STE lint` against the updated module — every command MUST exit 0.
- [ ] T045 [US2] Manual live-run validation: execute `quickstart.md` Scenario 3 (revert), then Scenario 6 (revert refuses when source deleted), then Scenario 7 (revert skips missing APs). Confirm each expected outcome, and confirm the JSONL audit line appears in the latest telemetry file with `event_type == "ap_profile_migration_revert"` (US2 Acceptance Scenarios 1-4).

**Checkpoint**: Menu 207 and menu 208 both work independently. The migrate-then-revert round trip is safe.

---

## Phase 5: User Story 3 - Preview a migration without making any change (Priority: P3)

**Goal**: Let the operator pick the dry-run option at the menu-207 confirmation prompt. The tool prints the same AP list the live run would print, then exits without writing a backup and without issuing any PUT.

**Independent Test**: Run menu 207, at the confirmation prompt type `DRY-RUN`. Confirm no new file appears under `data/`, no PUT is issued, and the printed AP list matches the live-run plan (see `quickstart.md` Scenario 2).

Dry-run is a small branch on the migration entry point, not a separate module — the confirmation helper already returns `"dry_run"` (T020) and the entry-point orchestration already short-circuits on it (T025). This phase locks that behavior with targeted tests and validation.

### Tests for User Story 3 (write FIRST; must FAIL before implementation)

- [X] T046 [P] [US3] Unit test: `test_migrate_dry_run_writes_no_file_and_issues_no_put()` — with `safe_input` stubbed to return `"DRY-RUN"`, assert: `updateSiteDevice` was never called, no `ap-profile-migration_*.json` file was created under the `tmp_path`-monkeypatched data directory, and the printed output contains the exact line `Dry run: no changes made` (STE-compliant) (FR-015, SC-005, Acceptance Scenario 1).
- [X] T047 [P] [US3] Unit test: `test_migrate_dry_run_ap_list_matches_live_run_plan()` — capture the plan-render output for a mocked 5-AP org in dry-run mode and in live mode (with all PUTs mocked to succeed). Assert the pre-confirmation AP list block is byte-identical between the two runs (SC-005).
- [X] T048 [P] [US3] Integration-style test: `test_us3_end_to_end_dry_run_with_mocked_mistapi_session()` — one test drives the full public entry point in dry-run mode against a fully mocked `mistapi` session with 2 sites and 3 APs on the source profile. Asserts return without exception, zero `updateSiteDevice` calls, zero files under `tmp_path` data dir, and the `Dry run: no changes made` line in captured output (quickstart Scenario 2).

### Implementation for User Story 3

- [X] T049 [US3] Confirm T020's `_confirm_migration` helper returns `"dry_run"` when the operator types `DRY-RUN` (uppercase, exact match) and returns `"cancel"` on any other input; if T020 landed with a narrower keyword set, extend it here. Update the docstring to state all three return values.
- [X] T050 [US3] Confirm T025's entry point handles `"dry_run"` by printing `Dry run: no changes made` and returning immediately, without calling `_build_backup_payload`, `_write_backup_file`, or `_run_reassignment_loop`. If T025 handled only `"cancel"`, add the `"dry_run"` branch here. Add a `#` comment noting FR-015 (Constitution Principle VI).
- [X] T051 [US3] Run `pytest tests/unit/device/test_ap_profile_migration_manager.py -v` for T046-T048; iterate until all pass. Confirm every earlier test (T009-T016 and T028-T035) still passes.
- [ ] T052 [US3] Manual live-run validation: execute `quickstart.md` Scenario 2 (dry-run). Confirm no file is written under `data/` and no PUT is issued.

**Checkpoint**: All three user stories are independently functional. Menu 207 (live + dry-run) and menu 208 both work against a test org.

---

## Phase 6: Polish and Cross-Cutting Concerns

**Purpose**: Final gate checks that span the whole feature — every operator-visible string is STE-compliant, docstring coverage is above 90 percent, the guardrail and registry tests are green, and the quickstart flows land.

- [X] T053 [P] Run the feature-1026 ASD-STE100 lint over the new module and the two modified files (`src/device/ap_profile_migration_manager.py`, `src/utils/operation_registry.py`, `MistHelper.py` menu additions only). Fix every violation. All operator-visible strings — menu labels, plan text, prompts, progress lines, error text, summary text — MUST pass (FR-002, SC-007).
- [X] T054 [P] Run `interrogate -f 90` and `pydoclint --style=google` over the new module. Coverage MUST stay at or above 90 percent and every added function, method, class, and module MUST carry a Google-style docstring with a "Why" section (FR-004, DOCS.md).
- [X] T055 [P] Run `ruff check .`, `black --check .`, and `mypy src/device/ap_profile_migration_manager.py src/utils/operation_registry.py` — every command MUST exit 0.
- [X] T056 Run the full pytest suite (`cd src && pytest`) and confirm the new tests plus every existing test is green (SC-006 — no coverage regression). Confirm the destructive-registry guardrail from `src/utils/operation_registry.py` passes without modification.
- [X] T057 Update `CLAUDE.md` "Recent Changes" section with a one-line entry naming feature 1029, its two menu numbers (207 / 208), and its two persisted artifacts (JSON backup + JSONL audit). Keep the entry under 25 words per the STE style guide.
- [ ] T058 Final live-run validation: execute every scenario in `quickstart.md` (1 through 7) in order against a Mist test org. Confirm every "Expected outcome" line for every scenario. Attach the output as an artifact on the PR.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — starts immediately.
- **Foundational (Phase 2)**: Depends on Phase 1. Blocks every US phase.
- **US1 (Phase 3)**: Depends on Phase 2. Can run in parallel with US2 (Phase 4) once T005/T006 land, but the tests in US2 depend on shared fixture patterns established by US1, so sequential US1 → US2 is safer with a small team.
- **US2 (Phase 4)**: Depends on Phase 2. May run in parallel with US1 if two developers split the work.
- **US3 (Phase 5)**: Depends on US1 (Phase 3), because T049 / T050 confirm and extend helpers landed by T020 / T025. Do not start US3 until US1 is code-complete.
- **Polish (Phase 6)**: Depends on US1, US2, US3 all complete.

### Task-Level Dependencies (within phases)

- T005 blocks T009-T016, T028-T035, T046-T048 (module must import).
- T006 blocks T009-T016, T028-T035, T046-T048 (test file must import).
- T004 blocks T007 (registry entries must exist before the test asserts them).
- T017-T023 must land before T024 (loop calls the helpers).
- T024 blocks T025 (entry point calls the loop).
- T025 blocks T026 and T049 / T050 (US3 branches on T025's logic).
- T036-T042 must land before T043 (entry point calls the helpers).
- T043 blocks T044.

### Parallel Opportunities

- Every task marked [P] within the same phase can run in parallel.
- T009 through T016 (US1 unit and integration tests) can all be authored in parallel on the shared skeleton from T006 — each test hits a different scenario and asserts on different mock configurations.
- T028 through T035 (US2 tests) likewise parallelize.
- T046 through T048 (US3 tests) parallelize.
- Polish gates T053, T054, T055 all read the same files but do not modify them and can run in parallel.

---

## Parallel Example: User Story 1 Tests

```bash
# Author all US1 test cases in parallel (each hits a distinct scenario in the same file):
Task: "T009 test_migrate_refuses_when_source_equals_target in tests/unit/device/test_ap_profile_migration_manager.py"
Task: "T010 test_migrate_reports_nothing_to_migrate_when_source_empty in tests/unit/device/test_ap_profile_migration_manager.py"
Task: "T011 test_migrate_writes_backup_before_any_put in tests/unit/device/test_ap_profile_migration_manager.py"
Task: "T012 test_migrate_backup_shape_matches_data_model_section_1_3 in tests/unit/device/test_ap_profile_migration_manager.py"
Task: "T013 test_migrate_retries_transient_put_failure_then_succeeds in tests/unit/device/test_ap_profile_migration_manager.py"
Task: "T014 test_migrate_stops_on_second_retry_exhaustion_and_records_partial_success in tests/unit/device/test_ap_profile_migration_manager.py"
Task: "T015 test_migrate_progress_prints_at_least_every_10_aps in tests/unit/device/test_ap_profile_migration_manager.py"
Task: "T016 test_us1_end_to_end_with_mocked_mistapi_session in tests/unit/device/test_ap_profile_migration_manager.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 (Setup).
2. Phase 2 (Foundational: registry + skeletons + guardrail test).
3. Phase 3 (US1: migrate).
4. STOP and validate against `quickstart.md` Scenario 1 in a Mist test org.
5. Ship the MVP if the revert is not yet ready — the migration operation delivers standalone value per `spec.md` "Why this priority".

### Incremental Delivery

1. Ship US1 (menu 207 live) as MVP.
2. Add US2 (menu 208 revert) — closes the safety net.
3. Add US3 (dry-run) — quality-of-life on top of US1.
4. Ship Polish (Phase 6) once all three land.

### Parallel Team Strategy

- Developer A: Phase 2 (T004-T008), then US1 (Phase 3).
- Developer B: US2 (Phase 4) tests (T028-T035) can start once T005 / T006 / T007 land. Wait for US1 implementation helpers before authoring US2 helpers.
- Developer C: US3 (Phase 5) must wait for US1 code-complete (T025).

---

## Notes

- [P] tasks touch different files or different independent scenarios in the shared test file and have no dependencies on incomplete work.
- The two operations MUST stay in one module (`src/device/ap_profile_migration_manager.py`) per research Decision 6 — the shared helpers (backup schema, AP-record shape, retry policy) live once.
- Every operator-visible string added by this feature MUST pass the ASD-STE100 lint (SC-007). Prefer short imperative sentences with the condition first ("If X, do Y").
- The retry backoff sequence is `[0.5, 1.0]` seconds. Do not change these values without updating `research.md` Decision 2 and the T013 test assertion.
- The backup file writer MUST succeed before any PUT is issued. If T022 raises, T025 MUST NOT enter T024.
- The revert audit emit is best-effort. A failed emit MUST NOT change the observable outcome of the revert operation (Constitution Principle VI comment on T042).
- Menu numbers 207 and 208 are the next available slots after menu 206 (per `plan.md` Structure Decision). If a concurrent feature branch claims 207 or 208, coordinate before Phase 2 lands.
- Commit after each task or logical group. Do not amend commits after CI runs (per user memory `feedback_prepush_black_ruff.md`).

# Feature Specification: Migrate APs Between Device Profiles (with Revert)

**Feature Branch**: `1029-ap-profile-migration`

**Created**: 2026-07-27

**Status**: Implemented and merged in pull request #1691. Menus 207 and 208 ship. Four manual live run tasks stay open, because they need a Mist test organization. Issue #1700 reports that a menu 207 PUT returns 200 without a persisted profile change, so keep that issue open.

**Input**: User description: "Add two new MistHelper menu operations. (1) Migrate all Access Points from a source device profile to a target device profile within one Mist organization, with a full pre-change backup written to `data/`. (2) Revert a prior migration by reading its backup file and reassigning each listed AP back to its original device profile. Both operations mutate Mist cloud configuration and MUST be classified as destructive in `src/utils/operation_registry.py`."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bulk migrate APs to a new device profile (Priority: P1)

A network engineer must retire a device profile ("Data-Transfer-Device-Profile") and move every AP that currently uses it onto a replacement profile ("Main-Device-Profile"). Doing this by hand in the Mist UI is slow and error-prone, and there is no built-in undo. The engineer picks the source and target profiles from a menu, reviews the list of APs that will be reassigned, confirms the change, and MistHelper reassigns each AP and writes a backup file that captures the full state before the change.

**Why this priority**: This is the primary reason the feature exists. Without it there is no migration capability at all. It delivers standalone value even if the revert operation is added later.

**Independent Test**: Run the migration option against a test organization, pick a source profile that has at least one AP, pick a different target profile, confirm the prompt. Verify that (a) every AP that had `deviceprofile_id == source` now has `deviceprofile_id == target`, (b) a backup file exists under `data/` containing the source profile JSON, the target profile JSON, and the list of migrated AP IDs, and (c) counts printed to the operator match the counts recorded in the backup.

**Acceptance Scenarios**:

1. **Given** an org with a source device profile that has 5 APs bound to it and a target profile that has 2 APs bound to it, **When** the operator picks the source profile and the target profile and confirms the migration, **Then** all 5 APs move to the target profile, the target profile ends with 7 APs, and one backup file appears under `data/` that contains the source profile JSON, the target profile JSON, and the 5 AP IDs.
2. **Given** an org with a source device profile that has 0 APs bound to it, **When** the operator picks that profile as the source, **Then** the tool reports "No APs bound to source profile. Nothing to migrate." and exits without writing a backup and without making any API PUT calls.
3. **Given** the operator picks the same profile as both source and target, **When** the confirmation prompt appears, **Then** the tool refuses the operation with a clear error and does not call the API.
4. **Given** an org with 100 APs on the source profile where 30 APs are offline, **When** the migration runs, **Then** the tool reassigns all 100 APs (offline APs receive the new assignment on next cloud check-in), records all 100 IDs in the backup, and prints a summary that separates the online count from the offline count.
5. **Given** an operator selects source and target profiles and Mist rejects the PUT for one AP mid-run, **When** the failure occurs, **Then** the tool stops issuing further PUTs, prints which AP failed, records the partial success list in the backup file (so a follow-up revert or retry can act on the exact set of APs that were actually changed), and returns a non-zero exit path from the operation.

---

### User Story 2 - Revert a prior migration from its backup file (Priority: P2)

Some hours or days after a migration, the engineer discovers a regression on the newly assigned profile and must roll every affected AP back to its original profile. The engineer picks the revert menu option, selects the backup file that the migration wrote, confirms, and MistHelper reassigns each listed AP back to the source profile ID that was captured at migration time.

**Why this priority**: This is a safety net for Story 1. Story 1 delivers value on its own, but the revert operation is what makes the migration safe to attempt in production; it is the second most important slice.

**Independent Test**: Run Story 1 once against a test org. Then run the revert option, point it at the backup file that Story 1 produced, confirm. Verify that every AP listed in the backup is now assigned back to the original source profile ID that the backup recorded.

**Acceptance Scenarios**:

1. **Given** a backup file that lists 5 AP IDs and the original source profile ID, **When** the operator runs the revert operation and selects that file, **Then** all 5 APs are reassigned to the original source profile ID and a summary shows 5 successes and 0 failures.
2. **Given** the backup file references a source profile ID that has since been deleted from the org, **When** the operator runs the revert, **Then** the tool fails loudly before making any AP changes, names the missing profile ID, and instructs the operator to recreate the profile or edit the backup file. No AP is changed.
3. **Given** the backup file lists 5 AP IDs but 1 of those APs has since been removed from the org, **When** the operator runs the revert, **Then** the 4 APs that still exist are reassigned to the original source profile, the missing AP is reported by ID in the summary, and the operation returns success for the 4 and a warning for the 1.
4. **Given** APs were added to the target profile after the migration ran (APs that are not in the backup), **When** the revert runs, **Then** those newer APs are not touched. The summary states that the revert reassigned only the APs that the backup file listed.

---

### User Story 3 - Preview a migration without making any change (Priority: P3)

Before performing a destructive migration in production, the engineer wants to see exactly which APs would move. A dry-run mode prints the same list and counts that the real operation would print, and skips both the backup write and the API PUT calls.

**Why this priority**: This is a quality-of-life addition that lowers the risk of the destructive operations. It is not required for the feature to be usable but is standard practice for MistHelper destructive operations.

**Independent Test**: Invoke the migration option in dry-run mode against a test org. Verify that (a) no backup file is written, (b) no PUT call is issued, and (c) the printed AP list matches what a live run would report.

**Acceptance Scenarios**:

1. **Given** an org with 5 APs on a source profile, **When** the operator runs the migration option in dry-run mode, **Then** the tool prints the 5 AP IDs, hostnames, and site names that would be reassigned, prints "Dry run: no changes made", writes no backup file, and issues no PUT calls.

---

### Edge Cases

- The source device profile does not exist in the org (was deleted between listing and confirmation): the tool must detect this and refuse to proceed without making any change.
- The target device profile does not exist in the org: same behavior as above.
- The source device profile has `type != "ap"` (for example a switch profile): the tool must filter the profile picker to `type == "ap"` only, so this case cannot be selected.
- An AP object in the site inventory has `deviceprofile_id == null`: it is skipped by the migration (it is not bound to any profile so it does not match the source).
- Two backup files exist in `data/` with the same source and target profile IDs but different timestamps: the revert file picker must show timestamps clearly so the operator can pick the right one.
- The backup file is corrupt or missing required fields (source profile ID, target profile ID, AP ID list): the revert must fail before touching any AP and must name the missing field.
- Mist API returns an authorization error partway through a migration: the tool stops immediately, records the partial success list in the backup file, and reports which AP was the last successful reassignment so the operator can resume.
- The operator's session token expires during the migration: same behavior as the authorization error case.
- A network hiccup causes one PUT to time out: the tool retries a small, bounded number of times per AP before recording that AP as a failure and stopping.
- The org contains many sites (100+) and many APs (1000+): the tool must show progress rather than appearing frozen.

## Requirements *(mandatory)*

### Functional Requirements

#### Common to both operations

- **FR-001**: Both new operations MUST be added as menu entries in MistHelper and MUST be registered in `src/utils/operation_registry.py` with `category = "destructive"` and a `skip_reason` that names the operation. The CI guardrail MUST accept the new entries.
- **FR-002**: All operator-visible strings (menu labels, prompts, log lines, summary text, error text) MUST follow the Simplified Technical English writing guide at `documentation/ASD-STE100_writing-guide.md`.
- **FR-003**: The feature MUST use only the Python 3.13+ standard library and the already-installed `mistapi>=0.63.1`. No new third-party dependencies are permitted.
- **FR-004**: Every function, method, class, and module added or modified by the feature MUST carry a docstring that follows the DOCS.md rules (one-line summary + Why + Args/Returns/Raises where applicable). Docstring coverage for changed files MUST stay at or above 90 percent.
- **FR-005**: Both operations MUST require an explicit typed confirmation from the operator before any API PUT is issued, and the confirmation prompt MUST state the exact count of APs that will be affected and name the source and target profile IDs and names.

#### Migration operation

- **FR-006**: The migration operation MUST let the operator pick a Mist organization (using the existing MistHelper org-selection flow).
- **FR-007**: The migration operation MUST list only device profiles whose `type == "ap"` for source and target selection, using `mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles`.
- **FR-008**: The migration operation MUST refuse to run if the operator picks the same profile as source and target.
- **FR-009**: The migration operation MUST discover every AP currently bound to the source profile by walking every site in the org and reading `deviceprofile_id` on each AP device object (per Mist API `GET /api/v1/sites/{site_id}/devices?type=ap`). It MUST NOT rely on the profile object itself carrying a list of AP IDs.
- **FR-010**: The migration operation MUST NOT write a backup and MUST NOT issue any PUT if the discovered AP set is empty; it MUST print a clear "nothing to migrate" message and exit.
- **FR-011**: The migration operation MUST write exactly one backup file per successful invocation, before issuing the first PUT, and MUST refuse to proceed with any PUT if the backup file write fails.
- **FR-012**: The backup file MUST be written under `data/` with a name that includes a UTC timestamp, the source profile ID, and the target profile ID (naming pattern chosen during planning; see Assumptions).
- **FR-013**: The backup file MUST contain: the full JSON of the source device profile (as returned by the get-profile endpoint), the full JSON of the target device profile, the org ID, the source profile ID, the target profile ID, the migration UTC timestamp, and the ordered list of AP records to be reassigned (each record: AP ID, hostname if known, site ID, MAC).
- **FR-014**: The migration operation MUST reassign each AP by PUT-ing the device object with `deviceprofile_id` set to the target profile ID. It MUST use whatever `mistapi` device-update helper is already available in the codebase and MUST NOT add a new HTTP client.
- **FR-015**: The migration operation MUST offer a dry-run mode selectable at the confirmation prompt. In dry-run mode it prints the plan, writes no backup, and issues no PUT.
- **FR-016**: The migration operation MUST print live progress (for example "reassigning AP 3 of 27") so long-running migrations do not appear frozen.
- **FR-017**: If any PUT fails, the migration operation MUST stop immediately (no further PUTs), MUST update the backup file to record which APs were actually reassigned successfully before the failure, MUST name the failing AP and the error, and MUST make it explicit that the recorded partial-success list is the correct input for a subsequent revert.
- **FR-018**: At end of run the migration operation MUST print a summary that includes: source profile name and ID, target profile name and ID, total APs planned, total APs reassigned, total online at reassignment time, total offline at reassignment time, and the absolute path to the backup file.

#### Revert operation

- **FR-019**: The revert operation MUST let the operator pick a backup file from `data/` and MUST show timestamps and source/target profile IDs so the operator can distinguish backup files.
- **FR-020**: The revert operation MUST read the selected backup file and validate that all required fields (see FR-013) are present; on any missing or malformed field, it MUST fail before touching any AP and MUST name the missing or malformed field.
- **FR-021**: Before issuing any PUT, the revert operation MUST verify that the original source profile ID recorded in the backup still exists in the org. If it does not, the revert MUST fail loudly and MUST instruct the operator to either recreate the profile or edit the backup file, without changing any AP.
- **FR-022**: The revert operation MUST reassign each AP listed in the backup to the original source profile ID recorded in the backup. It MUST NOT touch any AP that is not listed in the backup, even if that AP is currently bound to the target profile.
- **FR-023**: If an AP listed in the backup no longer exists in the org, the revert MUST skip that AP, record the skip in the summary by AP ID, and continue with the rest. The overall operation returns success with a warning count.
- **FR-024**: The revert operation MUST print a summary that includes: backup file path, original source profile ID, total APs in backup, total reassigned successfully, total missing APs, and total failures.
- **FR-025**: The revert operation MUST write an append-only audit line to `data/` (matching the existing telemetry pattern used by other MistHelper operations) that records: revert timestamp, backup file used, org ID, source profile ID, count of reassigned APs, and outcome (success, partial, failure).

### Key Entities

- **Device profile**: A named configuration object in a Mist org (e.g., "Main-Device-Profile") with an ID, a name, and a `type` (this feature only touches `type == "ap"`). APs are bound to a device profile through the AP device object's `deviceprofile_id` field, not through a list on the profile.
- **AP (Access Point) device**: A network device object at a Mist site. Relevant fields for this feature: device ID, hostname, MAC, site ID, and `deviceprofile_id` (the profile the AP is currently bound to, or null if unassigned).
- **Migration backup**: A single JSON file under `data/` written once per successful migration invocation. It contains the pre-change state that a revert operation needs: source profile JSON, target profile JSON, org ID, migration timestamp, and the ordered list of AP records that the migration reassigned.
- **Revert audit record**: An append-only telemetry line under `data/` that records that a revert ran (timestamp, backup file, org ID, source profile ID, count, outcome), matching the JSONL telemetry pattern already used by other MistHelper operations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An engineer can migrate every AP from one device profile to another (up to 500 APs) using a single MistHelper menu selection and one typed confirmation, without editing any file by hand and without calling any Mist API directly.
- **SC-002**: 100 percent of migrations that reach the PUT phase produce a backup file under `data/` before any AP is changed. No migration ever changes an AP without first writing its backup file.
- **SC-003**: A backup file written by the migration operation is sufficient input for the revert operation, with no other data source required. Running the revert against a backup returns every listed AP to its original device profile ID, or reports precisely which AP could not be reverted and why.
- **SC-004**: The migration operation shows progress at least every 10 APs so that an operator running a 500-AP migration always sees the tool is still working (no perceived freeze longer than a few seconds under normal API latency).
- **SC-005**: A dry-run of the migration operation completes with zero writes to `data/` and zero PUT calls to Mist, and its printed AP list exactly matches what a live run would report against the same org state.
- **SC-006**: Both new menu options are registered in `src/utils/operation_registry.py` as destructive, and the existing CI guardrail passes without modification (no new destructive-registry lint failures, no new coverage regressions).
- **SC-007**: 100 percent of new operator-visible strings pass the existing ASD-STE100 lint check (introduced in feature 1026) without STE violations.

## Assumptions

- Menu option numbers for the two new operations will be assigned in the planning phase, following the existing MistHelper numbering convention. The registry entries in `operation_registry.py` will use whatever numbers the planning phase picks.
- The migration operation walks every site in the selected org to build the AP list. This is preferred over asking the operator to pick sites, because a device profile is an org-level object and partial migrations would leave the org in a mixed state that the backup file would not correctly describe. A future enhancement could add an optional site filter, but v1 is org-wide only.
- Backups are stored as a single JSON file per migration under `data/` (not JSONL), because each migration produces one logical snapshot, not a stream of events. The revert-side audit line is JSONL because it matches the existing telemetry pattern already used elsewhere in MistHelper.
- Backup file naming pattern: `ap-profile-migration_<UTC-timestamp>_<source-profile-id>_to_<target-profile-id>.json`. Timestamps are ISO 8601 basic format (`YYYYMMDDTHHMMSSZ`) so file names sort chronologically.
- Reassigning an offline AP is a supported Mist behavior: the assignment is cloud state, applied when the AP next connects. The tool reports offline counts but does not refuse to reassign offline APs.
- Retry policy for a failed PUT: at most 2 retries with a short backoff, then treat the AP as failed and stop the run. The exact backoff values are an implementation detail for the planning phase.
- The revert operation does not attempt to restore the source profile object itself. If the source profile has been deleted, the revert refuses to run and asks the operator to recreate it. Restoring a full device profile from the backup JSON is a separate feature and is out of scope for v1.
- APs added to the source profile after the migration runs are correctly not touched by a later revert. The backup captures the AP list as of migration time only. This is documented behavior and is called out in the summary text so the operator is not surprised.
- The feature uses the existing MistHelper org and menu selection flows; no new interactive helpers are introduced.
- Telemetry emissions from both operations reuse the existing `TelemetryEmitter` pattern, keeping shape stable per feature 1020's data-model.

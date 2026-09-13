# Quickstart Validation Guide: 1029-ap-profile-migration

**Date**: 2026-07-27
**Purpose**: Runnable scenarios that prove the feature works end-to-end
against a Mist test organization. Each scenario maps directly to a user
story or acceptance test in `spec.md`.

Implementation details (models, service internals, PUT wrappers) live in
the source under `src/device/ap_profile_migration_manager.py` and in
`data-model.md`. This document is a validation and run guide, not an
implementation reference.

---

## Prerequisites

1. Python 3.13+ available on `PATH`. Verify:
   ```bash
   python --version
   ```
2. MistHelper repository checked out on branch `1029-ap-profile-migration`
   with dependencies installed:
   ```bash
   pip install -e .
   ```
3. A Mist API token with write access to a **test** organization (never
   run these scenarios against production the first time). The token
   goes into the standard MistHelper session file (see MistHelper's
   existing auth flow — no new setup required for this feature).
4. In the test org, prepare **two** device profiles of `type == "ap"`:
   - **Source profile**: name it something like
     `Data-Transfer-Device-Profile-TEST`. Bind at least 2 APs to it.
   - **Target profile**: name it something like
     `Main-Device-Profile-TEST`. Optionally bind 1 AP to it, so the test
     verifies both an existing-APs case and a fresh-target case.
5. Ensure `data/` exists and is writable:
   ```bash
   mkdir -p data
   ```

---

## Scenario 1 — US1 P1: Bulk migrate APs (live run)

**Maps to**: `spec.md` User Story 1, Acceptance Scenario 1; FR-005 through FR-018; SC-001, SC-002, SC-004, SC-006.

**Steps**:

1. Start MistHelper:
   ```bash
   python MistHelper.py
   ```
2. Log in and select the test organization when prompted.
3. From the main menu, pick menu option `207` (`Migrate APs between
   device profiles`).
4. When the source profile picker appears, choose the test source
   profile.
5. When the target profile picker appears, choose the test target
   profile.
6. Review the printed plan: it must list every AP with device ID,
   hostname (or `-` if unknown), and site name, followed by a summary
   line like `Total: N APs will be reassigned from <source-name> to
   <target-name>`.
7. At the confirmation prompt, type `MIGRATE` exactly (uppercase) and
   press Enter.

**Expected outcome**:

- MistHelper writes a backup file under `data/` named
  `ap-profile-migration_<UTC-timestamp>_<source-profile-id>_to_<target-profile-id>.json`.
- MistHelper prints progress lines at least every 10 APs
  (`reassigning AP N of M: ...`).
- Every AP that was on the source profile now reports
  `deviceprofile_id == <target-profile-id>` in the Mist UI (or via
  `GET /sites/{site_id}/devices/{device_id}`).
- The end-of-run summary lists source and target profile name and ID,
  total planned count, total reassigned count, online / offline split,
  and the absolute path to the backup file.
- The backup file's `outcome` field is `"success"` and its
  `aps_reassigned` list has the same length as `aps_planned`.

**Verification commands**:

```bash
ls -1 data/ap-profile-migration_*.json | head -1
python -c "import json, sys; d=json.load(open(sys.argv[1])); print('planned', len(d['aps_planned']), 'reassigned', len(d['aps_reassigned']), 'outcome', d['outcome'])" "$(ls -1t data/ap-profile-migration_*.json | head -1)"
```

---

## Scenario 2 — US3 P3: Dry run

**Maps to**: `spec.md` User Story 3, Acceptance Scenario 1; FR-015; SC-005.

**Prerequisite**: Reset the test org so at least 2 APs are on the source
profile again (or run Scenario 3 first to revert).

**Steps**:

1. Repeat steps 1-6 from Scenario 1.
2. At the confirmation prompt, choose the dry-run option (the prompt
   offers `MIGRATE` or `DRY-RUN` — pick `DRY-RUN`).

**Expected outcome**:

- MistHelper prints the same AP list that a live run would print,
  followed by the line `Dry run: no changes made`.
- No new file appears under `data/` (verify with `ls data/`).
- No PUT is issued (verify by checking Mist audit logs, or by
  observing that AP `deviceprofile_id` values are unchanged).

**Verification commands**:

```bash
before=$(ls -1 data/ap-profile-migration_*.json 2>/dev/null | wc -l)
# ... run the dry-run scenario ...
after=$(ls -1 data/ap-profile-migration_*.json 2>/dev/null | wc -l)
test "$before" -eq "$after" && echo "PASS: no backup file created"
```

---

## Scenario 3 — US2 P2: Revert from a backup file

**Maps to**: `spec.md` User Story 2, Acceptance Scenario 1; FR-019 through FR-025; SC-003.

**Prerequisite**: Scenario 1 has run successfully and produced a backup
file. Every AP is now on the target profile.

**Steps**:

1. Start MistHelper and log into the same test org.
2. From the main menu, pick menu option `208` (`Revert an AP profile
   migration from a backup file`).
3. When the backup file picker appears, pick the file produced by
   Scenario 1 (files are shown in newest-first order with timestamp and
   source-to-target profile IDs).
4. Review the printed plan and summary.
5. At the confirmation prompt, type `REVERT` exactly (uppercase) and
   press Enter.

**Expected outcome**:

- Every AP listed in the backup file now reports
  `deviceprofile_id == <original-source-profile-id>` in the Mist UI.
- MistHelper prints a summary line with backup file path, original
  source profile ID, planned count, reassigned count, missing count
  (should be 0 for a clean test), and failed count (should be 0).
- One JSONL row is appended to the existing MistHelper telemetry file
  under `data/` with `"event_type": "ap_profile_migration_revert"`
  and `"outcome": "success"`.

**Verification**:

```bash
# Confirm the audit line was appended (grep the newest telemetry file):
grep '"event_type": "ap_profile_migration_revert"' data/*.jsonl | tail -1
```

---

## Scenario 4 — Empty source set (nothing to migrate)

**Maps to**: `spec.md` User Story 1, Acceptance Scenario 2; FR-010.

**Prerequisite**: A source device profile in the test org that has zero
APs bound to it.

**Steps**:

1. Run menu 207 as in Scenario 1.
2. Pick the empty profile as the source.
3. Pick any other AP profile as the target.

**Expected outcome**:

- MistHelper prints
  `No APs bound to source profile. Nothing to migrate.` and exits the
  operation.
- No file appears under `data/`.
- No PUT is issued.

---

## Scenario 5 — Source equals target (refusal)

**Maps to**: `spec.md` User Story 1, Acceptance Scenario 3; FR-008.

**Steps**:

1. Run menu 207.
2. Pick the same profile for both source and target.

**Expected outcome**:

- MistHelper prints an error like
  `Source and target must be different profiles.` and exits the
  operation.
- No PUT is issued.

---

## Scenario 6 — Revert refuses when source profile was deleted

**Maps to**: `spec.md` User Story 2, Acceptance Scenario 2; FR-021.

**Prerequisite**: A backup file from a completed migration
(Scenario 1), and then the source profile has been deleted from the
org (delete it in the Mist UI).

**Steps**:

1. Run menu 208.
2. Pick the backup file that references the now-deleted source profile.

**Expected outcome**:

- MistHelper prints an error naming the missing profile ID and
  instructs the operator to recreate the profile or edit the backup
  file.
- No PUT is issued.
- The JSONL audit line records `"outcome": "failure"`.

---

## Scenario 7 — Revert skips APs that no longer exist

**Maps to**: `spec.md` User Story 2, Acceptance Scenario 3; FR-023.

**Prerequisite**: A backup file from a completed migration
(Scenario 1). Manually delete one of the listed APs from the org (in
the Mist UI, remove one AP from its site).

**Steps**:

1. Run menu 208 against that backup file.

**Expected outcome**:

- MistHelper reassigns every still-present AP back to the source
  profile.
- The summary reports `missing_count == 1` and names the missing AP ID.
- The overall operation reports success with a warning, not a failure.
- The JSONL audit line records `"outcome": "partial"`.

---

## Automated test suite

The scenarios above validate the feature end-to-end against a live
Mist org. The `pytest` suite under
`tests/unit/device/test_ap_profile_migration_manager.py` covers the
same behaviors with mocked `mistapi` sessions and does not require
network access. Run:

```bash
cd src && pytest ../tests/unit/device/test_ap_profile_migration_manager.py -v
ruff check .
```

Both commands MUST exit 0 before the feature is considered ready for
review.

---

## Rollback

If a live-run test produces an unexpected state:

1. Locate the backup file:
   `ls -1t data/ap-profile-migration_*.json | head -1`
2. Run Scenario 3 (revert) against it.

If the backup file itself is unreadable or malformed, restore each AP's
device profile binding manually in the Mist UI — the backup file's
`aps_planned` list is human-readable JSON and lists every affected AP
ID and site.

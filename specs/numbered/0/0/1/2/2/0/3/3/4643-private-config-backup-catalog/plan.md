# Implementation Plan: Private Configuration Backup and Verified Catalog

**Branch**: `feat/4643-private-config-backup-catalog` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric record at `specs/numbered/0/0/1/2/2/0/3/3/4643-private-config-backup-catalog/`. The route follows the base-5 rule in `.github/copilot-instructions.md`, line 159. Decimal 4643 equals `122033` in base 5. Padded to eight levels, it gives `0/0/1/2/2/0/3/3`.

## Summary

Add the private backup and verified catalog as offline code in the converter state package. The backup captures three object families with explicit pages. It writes sealed JSON files only under `data/.cisco-config-converter-backups/`. The catalog lists only verified files and returns metadata only. This change adds no route, no browser exposure, and no Mist write. Product code keeps persistence disabled until the gates in FR-026 pass.

## Technical Context

- **Language/Version**: Python 3.15 or newer. Source: `pyproject.toml`, line 23.
- **Primary Dependencies**: `mistapi==0.64.1`. Source: `requirements.txt`, line 129. Standard library modules `hashlib`, `hmac`, `json`, `os`, `stat`, `pathlib`, `datetime`, and `uuid`. Reused firmware helpers `BackupAccess`, `PolicyAdmission`, `PolicyResponse`, and `SettingsRequestGuard`. Reused issue 4636 types `BackupManifest`, `CanonicalDigest`, `RecordSeal`, `PersistenceUnavailable`, and `StateRefused`.
- **Storage**: Sealed JSON files under `data/.cisco-config-converter-backups/`. No database. No compose change. No storage migration.
- **Testing**: pytest in `tests/integration/web_portal/cisco_config_converter/backup/`. Two more tests run in shared modules from the integration pull request.
- **Target Platform**: Windows 11, macOS, Linux, and the Podman container that runs as UID 1000.
- **Project Type**: Feature code inside the converter package. The converter package is inside the web portal interface package.
- **Performance Goals**: None set. Each capture makes one request for each page of 1000 objects. Shared admission controls the request rate.
- **Constraints**: Fail closed. No automatic purge. No route registration. No shared-file change in the feature pull request. Synthetic data only.
- **Scale/Scope**: Three object families. One module with five top-level names. Four test modules with 25 test functions.

## Constitution Check

| Rule | Result | Reason |
| --- | --- | --- |
| I. Five-item rule, levels | Pass | The change adds no direct child to any directory. `state/lifecycle/backup.py` keeps five top-level names (D-11). |
| I. Five-item rule, functions and classes | Pass | Each class has five members or fewer. Each function has five parameters or fewer. T008 to T011 check the limits. |
| II. Class-based architecture | Pass | Each behavior sits in a named class. No wrapper function is planned. |
| III. Safety-first input | Pass | The organization ID parses as a UUID before any request. The family must match one of three values. A file name must match the identifier pattern before any path is built. |
| III. Destructive operations | Pass | The change adds no delete, restore, or Mist write. |
| III. Secrets in logs | Pass | FR-024 and `test_writer_keeps_unverified_file_and_logs_without_bodies` cover logs. The reused SDK guard replaces SDK diagnostics (`sdk.py`, line 30). |
| IV. Deployment pipeline | Pending | The pipeline applies to the implementation pull request. Tasks T-LOCAL-GATES to T-MERGE cover it. |
| V. ASCII logs | Pass | Each planned log message uses ASCII text only. |
| V. Structured logs | Fail until U-13 closes | The plan uses standard `logging` with `%s` values. The constitution asks for structlog or an equivalent. The owner must accept the equivalence. |
| VI. Inline comments | Pending | Each new or changed line carries a comment. The privacy checklist checks each line in review. |
| VII. Action logging | Pending | Each capture, write, read-back, and catalog action logs before and after. The writer test checks the captured records for each action. |
| Technology: Python | Pass | Python 3.15 standard library and pinned mistapi only. |
| Technology: mistapi | Pass | Three list methods only. The contract is in `design/contracts/mist-list-reads.md`. |
| Technology: owned WebSocket | Not applicable | The change opens no WebSocket transport. |
| Technology: UV and requirements | Pass | No dependency changes. `requirements.txt` stays unchanged. |
| Technology: Podman | Pass | No container file changes. The container checks are in `design/quickstart.md`. |
| Technology: test containers | Not applicable | The tests start no container. |
| Technology: file paths | Pass | The code uses `pathlib.Path` and `os` calls. No separator is hard-coded. |
| Technology: operational store | Pass | No declared operational store exists. The backup defines refusal (FR-014, FR-015), retention (FR-021), and verified persistence (FR-015). Production use waits for gate G4 evidence. |
| Technology: export boundary | Pass | The change adds no export. FR-019 keeps backups out of every export. |
| Technology: database keys | Pass | Object IDs are Mist natural IDs. Relationship targets use names and carry the key type `name` (D-7). |
| Technology: data directory | Pass | Backup files stay under `data/`. `.gitignore` line 95 ignores that directory. |
| Technology: container security | Pending | UID 1000 must write the backup directory. The POSIX owner and mode check runs in the container. Open item U-08 tracks it. |
| Technology: Zscaler | Not applicable | The change pushes no image. |
| Development: documentation | Pass | This record documents the change. The feature pull request adds no user-visible text. The integration pull request adds one changelog fragment because it changes what the portal lists. |
| Development: testing skip list | Not applicable | The change adds no menu operation. |
| Escalation | Pass | The change touches more than three files and two classes. This record exists for that reason. |
| Multi-agent git: issue first | Pending | The issue exists. The `in-progress` label is claimed before the branch starts. Task T-PR records the claim. |
| Multi-agent git: branch | Pending | The branch is `feat/4643-private-config-backup-catalog`, created from `main`. |
| Multi-agent git: overlap | Pass at drafting time | An open-PR scan found only PR 4208 with a converter-related path (`web_portal/app.py`). This change does not edit that file. |
| Owner gates | Pass for offline work | Offline code and tests are authorized (issue 4633). Persistence and catalog exposure are blocked (FR-026). |

## Capacity and Structure Inventory

The counts use the GitHub tree of `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Remote evidence appears in the remote verification table of `design/research.md`.

| Directory | Children on main | Limit | Status | Change in this record |
| --- | --- | --- | --- | --- |
| `src/interfaces/portals/cisco_config_converter/` | 5: `__init__.py`, `conversion.py`, `models.py`, `presentation`, `routes.py` | 5 | At limit | None. Issue 4636 replaces `models.py` with `state/`, which keeps five children. |
| `src/interfaces/portals/cisco_config_converter/state/lifecycle/` | Not on main. Five children after issue 4636. | 5 | Pending issue 4636 | Edits `backup.py` only. Adds no child. |
| `src/interfaces/portals/` | 6 | 5 | Over limit, grandfathered | None. |
| `tests/integration/web_portal/cisco_config_converter/` | 2: `__init__.py`, `test_routes.py` | 5 | Compliant | Adds `backup/`. Four children with issue 4636's `state/`. |
| `tests/integration/web_portal/cisco_config_converter/backup/` | Not on main | 5 | New | Five children: `__init__.py` and four test modules. |
| `tests/unit/web_portal/` | 52 | 5 | Over limit, grandfathered | The integration pull request adds functions to existing modules only. |
| `documentation/` | 73 | 5 | Over limit, grandfathered | None. |
| `tests/contract/` | 17 | 5 | Over limit, grandfathered | None. The full-parity T023 path is rejected (E-01). |

## Placement Decision (D-11)

Issue 4636 fills every structural slot in the converter state package. `state/` holds five children, `state/lifecycle/` holds five, and `state/storage/` holds five. The backup classes therefore go into `state/lifecycle/backup.py`, the module that issue 4636 creates for `BackupManifest`. That module then holds five top-level names: `BackupManifest`, `BackupDirectory`, `BackupCapture`, `BackupWriter`, and `BackupCatalog`. A sixth name needs a structure decision before implementation.

```text
src/interfaces/portals/cisco_config_converter/
  state/                          issue 4636 package, unchanged in shape
    lifecycle/
      backup.py                   4636: BackupManifest. 4643: four classes below.

tests/integration/web_portal/cisco_config_converter/
  backup/                         new test package
    __init__.py
    test_backup_capture.py        10 test functions
    test_backup_directory.py      7 test functions
    test_backup_writer.py         4 test functions
    test_backup_catalog.py        4 test functions
```

Each class holds five members or fewer:

- `BackupDirectory` holds `NAME`, `__init__`, `ensure`, `verify_root`, and `verify_file`.
- `BackupCapture` holds `PAGE_LIMIT`, `__init__`, `capture`, `_page`, and `_reported_total`.
- `BackupWriter` holds `__init__`, `write`, `_create`, and `_read_back`.
- `BackupCatalog` holds `MAX_BYTES`, `__init__`, `entries`, `_verify_file`, and `_verify_document`.

## Reuse Map

| Symbol | Location | Use in this change |
| --- | --- | --- |
| `BackupAccess.verify` | `src/operations/execution/firmware_policy/recovery/backup.py`, line 151. POSIX check at line 162. Windows query through `BackupAccess.windows`, line 117. | Checks ownership, link counts, reparse points, and Windows ACLs. The change adds an exact-mode check (D-2). |
| `PolicyAdmission` | `src/operations/execution/firmware_policy/sdk.py`, line 86. `request` at line 151. | Admits each page read through shared pacing and quota (D-4). |
| `PolicyResponse.request` | `sdk.py`, line 189 | Checks the HTTP status of each page (D-4). |
| `PolicyResponse.rows` | `sdk.py`, line 212 | Checks that each page holds a list of objects (D-4). |
| `SettingsRequestGuard` | `sdk.py`, line 30 | Replaces SDK diagnostics during each read (D-4). |
| `PolicyResponse.collect` | `sdk.py`, line 219 | Not reused. It discards the reported total (D-3). |
| `BackupManifest` | Issue 4636, `state/lifecycle/backup.py` | Manifest type. Two fields are added (E-04). |
| `CanonicalDigest` and `RecordSeal` | Issue 4636, `state/storage/integrity.py` | Canonical SHA-256 digests and the HMAC-SHA256 seal (D-8). |
| `PersistenceUnavailable` and `StateRefused` | Issue 4636, `state/storage/store.py` and `state/lifecycle/transitions.py` | Storage refusals and content refusals. |
| `ReviewState.digest` | `src/interfaces/portals/cisco_config_converter/models.py`, line 88 | Digest form that `CanonicalDigest` must match (issue 4636, FR-005). |
| `DEFAULT_API_PAGE_LIMIT` | `src/foundation/runtime/config/runtime_settings.py`, line 14 | Repository page limit of 1000. The capture uses the same value as a constant (D-3). |
| `EXCLUDED_DIR_NAMES` | `web_portal/services/output_scan.py`, line 84 | The integration pull request adds the converter directory name (D-13). |
| Containment check | `web_portal/services/data_browser.py`, line 154 | The integration pull request adds the converter directory name (D-13). |

## Architecture

1. The caller passes an organization ID, an object family, and the data directory. `BackupCapture.capture` validates both values first. It raises `StateRefused` on any invalid value.
2. `BackupCapture` reads pages 1 to N with `listOrgNetworks`, `listOrgServices`, or `listOrgServicePolicies`. Each call uses `limit=1000` and an explicit `page`. `PolicyAdmission.request` admits each call. `PolicyResponse.request` checks its status.
3. The reported total comes from the `X-Page-Total` header of each page. Every page must report the same total. The capture stops after the page that holds the total.
4. The capture builds the complete objects, the object digests, and the relationships. It refuses a relationship target that matches zero or several objects.
5. `BackupWriter.write` calls `BackupDirectory.ensure`, seals the document with `RecordSeal`, creates the file with exclusive creation, and reads the file back.
6. The read-back recomputes every digest, the count, each relationship, and the seal. A success returns the backup ID. A failure raises `PersistenceUnavailable`, keeps the file, and logs the reason.
7. `BackupCatalog.entries` scans the directory. It skips names that fail the pattern. It checks the size before any parse. It refuses duplicate keys, verifies the digests and seal, and returns metadata only.

## File-by-File Change Map

| Path | Action | Content | Task |
| --- | --- | --- | --- |
| `src/interfaces/portals/cisco_config_converter/state/lifecycle/backup.py` | Modify, after issue 4636 lands | Adds `BackupDirectory`, `BackupCapture`, `BackupWriter`, and `BackupCatalog`. Keeps `BackupManifest` with two added fields, `page_limit` and `reported_total` (E-04). | T008, T009, T010, T011 |
| `tests/integration/web_portal/cisco_config_converter/backup/__init__.py` | Add | Package marker. | T004 |
| `tests/integration/web_portal/cisco_config_converter/backup/test_backup_capture.py` | Add | 10 test functions for capture behavior. | T004 |
| `tests/integration/web_portal/cisco_config_converter/backup/test_backup_directory.py` | Add | 7 test functions for path and permission behavior. | T005 |
| `tests/integration/web_portal/cisco_config_converter/backup/test_backup_writer.py` | Add | 4 test functions for write and read-back behavior. | T006 |
| `tests/integration/web_portal/cisco_config_converter/backup/test_backup_catalog.py` | Add | 4 test functions for catalog behavior. | T007 |
| `web_portal/services/output_scan.py` | Modify, integration pull request | Adds the converter directory name to `EXCLUDED_DIR_NAMES`. | T013 |
| `web_portal/services/data_browser.py` | Modify, integration pull request | Adds the converter directory name to the containment check at line 154. | T013 |
| `tests/unit/web_portal/test_output_scan_runtime_files.py` | Modify, integration pull request | Adds `test_output_scan_prunes_converter_backup_directory`. | T013 |
| `tests/unit/config/standalone/foundation/persistence/database/test_data_browser_path_guard.py` | Modify, integration pull request | Adds `test_data_browser_refuses_converter_backup_path`. | T013 |
| `changelog.d/pr-<number>.md` | Add, integration pull request | One fragment. It names issue 4643 and the exclusion change. | T013 |
| `specs/numbered/0/0/1/2/2/0/3/3/4643-private-config-backup-catalog/` | Add | This record. | T001 |

Unchanged paths: `src/interfaces/portals/cisco_config_converter/routes.py`, `src/interfaces/portals/cisco_config_converter/conversion.py`, `web_portal/app.py`, `web_portal/templates/base.html`, `compose.yml`, `.gitignore`, `requirements.txt`, `pyproject.toml`, and `documentation/`.

## Dependencies

- Issue 4636 merge. It blocks T008 to T011, and every test import in T004 to T007.
- Issue 4634 evidence for the three list operations. It blocks T009 and the relationship table in `design/data-model.md`.
- Issue 4633 shared-file handover. It blocks T013, the integration pull request, but not the feature pull request.
- No package change. No pin change. No new environment variable.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| The state module reaches five top-level names. | A sixth name needs a new module or a structure decision. | D-11. Review of T008 checks the top-level name count. |
| The `X-Page-Total` header is absent in live responses. | Every capture refuses. | FR-008 fails closed. T003 records the header evidence before T009. |
| Relationship names are not unique in live data. | A capture refuses. | D-7. Restore in issue 4646 must resolve names to IDs before any write. |
| The POSIX check refuses a bind-mounted directory in the container. | Backups refuse in that container. | U-08 checks the container path before enablement. FR-002 stays strict. |
| The Windows ACL query fails on the owner host. | Backups refuse on Windows. | `test_directory_checks_real_windows_acl` runs on Windows. FR-003 stays strict. |
| The `PORTAL_SECRET_KEY` value changes after a backup. | Sealed backups fail verification. | D-18 is a human decision. The catalog excludes such files. No automatic re-seal runs. |
| A backup reaches a browser before the integration pull request merges. | Private settings reach portal users. | FR-020 and FR-026 block persistence until the merge. The gating checklist checks this rule. |
| The firmware helpers change later. | Converter tests fail. | T002 runs the firmware SDK contract test. `test_capture_calls_only_list_functions_with_explicit_arguments` pins the call pattern. |
| The 128 MiB file bound refuses a valid large file. | The catalog excludes a valid backup. | D-15. U-09 requires evidence before enablement. |
| A failed read-back leaves a private file. | A file holds settings without a verified state. | D-14. The catalog excludes the file. The log names the refusal. |

## Rollback Steps

1. Revert the feature pull request with `git revert <commit>`, and merge the revert through a pull request.
2. Confirm that `state/lifecycle/backup.py` returns to the issue 4636 content. It must hold `BackupManifest` only.
3. Confirm that the backup test folder is gone. Confirm that `tests/integration/web_portal/cisco_config_converter/` holds three children.
4. Revert the integration pull request to restore the previous output-scan and browser behavior.
5. Remove files from `data/.cisco-config-converter-backups/` only when a test or manual run created them.

Warning: removing a backup file is irreversible. Keep each file that a recovery record references before you remove anything.

## Complexity Tracking

| Item | Type | Reason | Action |
| --- | --- | --- | --- |
| `src/interfaces/portals/` has six children. | Grandfathered, not touched | Predates this change. | Remediation R-01 (issue 4636, R-1). |
| `tests/unit/web_portal/` has 52 children. | Grandfathered, not touched | Predates this change. | The integration pull request adds functions to existing modules only (R-05). |
| `documentation/` has 73 children. | Grandfathered, not touched | Predates this change. | This record adds no document there (R-06). |
| `tests/contract/` has 17 children. | Grandfathered, not touched | Predates this change. | The full-parity T023 path is rejected (E-01). |
| `state/lifecycle/` has five children after issue 4636. | New design at the limit | Issue 4636 keeps five children. | No child is added in this change. |

This change adds no structural violation.

# Feature Specification: Private Configuration Backup and Verified Catalog

**Feature Branch**: `feat/4643-private-config-backup-catalog`

**Created**: 2026-11-26

**Status**: Draft. Offline code and synthetic tests only. Persistence and catalog exposure stay blocked.

**Input**: GitHub issue 4643, "[Spec]: Add private configuration backup and verified catalog". Complete tasks T023 and T024 of the full-parity task map in `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md`. Parent issue: 4224.

## Clarifications

### Session 2026-11-26

- Q: Did the owner approve the private storage policy? A: Yes. Owner comment IC_kwDOQltU8c8AAAABkRDV7A, dated 2026-11-08T23:37:41Z, approves the local policy. Coordinator decision G4 in issue 4633 repeats the approval.
- Q: May persistence start after that approval? A: No. Owner correction IC_kwDOQltU8c8AAAABkRD3aQ, dated 2026-11-08T23:38:30Z, permits policy documentation and test design only.
- Q: Does file ownership release T023 or T024? A: No. The correction also requires contract evidence from issue 4634 and state and identity evidence from issue 4636.
- Q: Do file permissions prove encryption at rest? A: No. Decision D-19 records the open encryption question for a human decision.
- Q: May a catalog endpoint exist now? A: No. The owner blocks a catalog endpoint until issue 4636 approves the design. Decision D-10 applies.
- Q: May backups purge automatically? A: No. The owner forbids automatic and age-based purge. Decision D-14 applies.
- Q: Which directory holds backups? A: `data/.cisco-config-converter-backups/`. Decision D-1 applies.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep backup files private on disk (Priority: P1)

An engineer starts a backup. The backup stops unless the backup directory passes each permission and path check.

**Why this priority**: A backup holds complete settings. An unsafe directory exposes those settings to other accounts.

**Independent Test**: Create each unsafe directory shape in a temporary data directory. Confirm each refusal and confirm that no backup file appears.

**Acceptance Scenarios**:

1. **Given** a backup directory with a group or other access bit, **When** a backup starts, **Then** the backup stops and writes no file.
2. **Given** a backup path that is a symbolic link or a hard link, **When** a backup starts, **Then** the backup stops and writes no file.
3. **Given** a missing data directory, **When** a backup starts, **Then** the backup stops and creates no directory.

---

### User Story 2 - Capture every page or refuse the backup (Priority: P1)

A maintainer captures one object family. The capture reads each page with explicit page numbers. It refuses any capture that lacks a complete and consistent page set.

**Why this priority**: A restore needs complete data. A partial backup can hide data loss until a restore fails.

**Independent Test**: Use mocked list responses for complete, short, repeated, changed, and failed pages.

**Acceptance Scenarios**:

1. **Given** a reported total of 1001 objects, **When** the capture runs, **Then** it reads pages 1 and 2 and keeps all 1001 objects.
2. **Given** no reported total header, **When** the capture runs, **Then** it refuses the capture.
3. **Given** an HTTP 429 response on page 2, **When** the capture runs, **Then** it refuses the capture and writes no file.

---

### User Story 3 - List only verified backups (Priority: P1)

A maintainer lists the backups for one organization and one object family. The catalog returns only backup files that pass every check.

**Why this priority**: A catalog that shows damaged or wrong-scope files can lead to a wrong recovery choice.

**Independent Test**: Place valid, tampered, wrong-organization, wrong-family, and oddly named files in one directory. List one organization and one family.

**Acceptance Scenarios**:

1. **Given** one valid and one tampered file, **When** the catalog lists the family, **Then** it returns only the valid file. The tampered file counts as excluded under one fixed reason.
2. **Given** a valid file for another organization, **When** the catalog lists this organization, **Then** it excludes that file with the reason `organization-mismatch`.

---

### User Story 4 - Keep backup content off every browser and log surface (Priority: P2)

Backup content and catalog metadata never reach a browser listing, preview, download, export, cookie, browser storage entry, or log line.

**Why this priority**: The portal has no authenticated operator identity. Any exposure reaches every user of the portal.

**Independent Test**: Read the log records of a backup run. Run the two integration exclusion tests after the integration pull request merges.

**Acceptance Scenarios**:

1. **Given** a completed backup, **When** its log records are read, **Then** no object body, digest, relationship, or seal appears.
2. **Given** the integration pull request is merged, **When** the output scan or the data browser runs, **Then** neither returns a file from the backup directory.

---

### User Story 5 - Keep restore and deletion out of scope (Priority: P2)

The backup feature reads Mist objects and writes private files only. It does not restore, delete, unassign, or write to Mist.

**Why this priority**: Restore and deletion need separate approvals, typed confirmations, and recovery evidence.

**Independent Test**: Run each capture test with a call recorder. Confirm that the recorder shows only list calls.

**Acceptance Scenarios**:

1. **Given** any capture test, **When** the test ends, **Then** the recorder shows zero write calls.
2. **Given** a backup file that is older than any retention period, **When** no operator requests deletion, **Then** the feature keeps the file.

### Edge Cases

- A reported total of 0 yields an empty and complete capture. A total of 1000 reads one page. A total of 1001 reads two pages.
- A duplicate object identifier on two pages refuses the capture.
- A total that changes between pages refuses the capture.
- A service policy names a service or tenant that the capture does not contain. The capture refuses.
- Two captured networks share a name that a relationship uses. The capture refuses.
- The seal key is absent. The writer creates no file.
- Read-back fails after a write. The file stays on disk, the writer reports failure, and the catalog excludes the file.
- A backup file is larger than 128 MiB. The catalog excludes the file before it parses the content.
- A file name is not 32 lowercase hexadecimal characters followed by `.json`. The catalog excludes the file.
- The Windows access query fails or names another account. The feature refuses access.

## Requirements *(mandatory)*

### Functional Requirements

| ID | Requirement |
| --- | --- |
| FR-001 | The feature MUST store each backup file only under `data/.cisco-config-converter-backups/`. |
| FR-002 | On POSIX, the directory and each file MUST have the current account as owner, with modes 0700 and 0600. |
| FR-003 | On Windows, the current account MUST own each path, and only the current account, SYSTEM, and local Administrators may have access. |
| FR-004 | The feature MUST refuse symbolic links, hard links, reparse points, traversal segments, and paths outside the backup directory. |
| FR-005 | The feature MUST NOT change a permission, owner, or ACL. It creates only a missing backup directory with mode 0700. |
| FR-006 | Each backup file MUST have a name of 32 lowercase hexadecimal characters followed by `.json`, created with exclusive creation. |
| FR-007 | The capture MUST read every page of one object family with explicit `limit` and `page` arguments until the reported total is reached. |
| FR-008 | The capture MUST refuse a missing or invalid reported total, an early empty page, extra rows, a repeated identifier, or a changed total. |
| FR-009 | The capture MUST refuse a page with a non-2xx status, an SDK error, or a body that is not a list of objects. It MUST write no file. |
| FR-010 | The capture MUST accept only the `service-policy`, `service`, and `network` object families. |
| FR-011 | Each backup file MUST record its schema version, object family, organization ID, and UTC capture time. |
| FR-012 | Each backup file MUST record the page limit, reported total, pagination flag, object count, object digests, relationships, and complete objects. |
| FR-013 | The capture MUST record each relationship with its key type and MUST refuse a target name that matches zero or several captured objects. |
| FR-014 | Each backup file MUST carry an HMAC-SHA256 seal. The writer and the capture MUST refuse when the seal key is absent. |
| FR-015 | The writer MUST report success only after it reads the file back and recomputes each digest, the count, each relationship, and the seal. |
| FR-016 | The catalog MUST list only verified files that match the requested organization ID and object family, and MUST count each exclusion by reason. |
| FR-017 | The catalog MUST exclude corrupt JSON, duplicate keys, non-finite numbers, files above 128 MiB, unknown schema versions, unexpected names, bad seals, and incomplete pagination. |
| FR-018 | The catalog MUST return only the backup ID, object family, UTC capture time, object count, and a verified flag. |
| FR-019 | The feature MUST add no browser route, listing, preview, download, export, cookie, or browser storage entry for backup content or catalog metadata. |
| FR-020 | The output scan and the data browser MUST exclude the backup directory in a separate integration pull request. Persistence MUST wait for that merge. |
| FR-021 | The feature MUST NOT delete a backup file automatically, by age, or by count. It keeps verified and unverified files. |
| FR-022 | The feature MUST NOT restore, delete, unassign, or write to Mist. |
| FR-023 | The feature MUST call only `listOrgNetworks`, `listOrgServices`, and `listOrgServicePolicies`, with explicit keyword arguments and shared request admission. |
| FR-024 | Logs MUST name the action, family, backup ID, counts, and refusal reason. Logs MUST NOT contain objects, digests, relationships, or seals. |
| FR-025 | Each new executable line MUST carry an inline comment. Each action MUST write a log line before and after the action. |
| FR-026 | This change MUST add no production caller. Enabling persistence or catalog reads requires gates G2, G3, and G4 and the issue 4636 gate. |
| FR-027 | Tests MUST use synthetic data, mocked SDK responses, `tmp_path`, and no network socket. No test MUST use a live credential. |
| FR-028 | Each directory that this change touches MUST hold five children or fewer. No new child MUST enter a noncompliant parent. |

### Mist Cloud Transport Requirements

- The feature uses three mistapi list methods from the pinned package `mistapi==0.64.1`: `listOrgNetworks`, `listOrgServices`, and `listOrgServicePolicies`.
- The feature opens no owned WebSocket transport and sends no direct HTTP request to a Mist endpoint.
- SDK authentication uses the existing session through the shared admission helper. The contract file `design/contracts/mist-list-reads.md` records the endpoint parity evidence.
- Failure safety tests: `test_capture_refuses_absent_or_invalid_reported_total`, `test_capture_refuses_failed_or_malformed_page`, and `test_capture_refuses_repeated_object_identifier`.
- Secret redaction tests: `test_writer_keeps_unverified_file_and_logs_without_bodies` and `test_catalog_returns_only_allowlisted_metadata`.

### Key Entities *(include if feature involves data)*

- **BackupDirectory**: The private directory under the data directory. It holds backup files only and enforces FR-001 through FR-006.
- **BackupFile**: One sealed JSON document. It holds the manifest fields, the complete objects, and the seal.
- **BackupObject**: One captured Mist object with its digest. Its natural key is the Mist object ID.
- **BackupRelationship**: One reference from a captured object to a target name in the same capture.
- **CatalogEntry**: The metadata of one verified backup file. It holds no object body.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each FR maps to at least one task and at least one test or gate. The coverage table in `analysis.md` lists each mapping.
- **SC-002**: Every refusal case in FR-004, FR-008, FR-009, FR-013, FR-014, and FR-017 leaves zero new files and zero catalog entries.
- **SC-003**: The backup test folder contains 25 test functions. Each test runs, or it skips with a printed reason.
- **SC-004**: The backup tests open zero network sockets and record zero Mist write calls.
- **SC-005**: The two integration tests show zero backup-directory entries in output-scan results and data-browser listings.
- **SC-006**: The nested package guard and the mistapi SDK compatibility guard pass.
- **SC-007**: The coverage gate for `src` stays at 80 percent or above with the new code included.

## Assumptions

- Issue 4636 merges its `state/` package before this change starts. This change reuses its `BackupManifest` type, `CanonicalDigest`, and `RecordSeal`.
- The shipped container runs one Gunicorn worker. `container/scripts/start.sh` line 225 sets `--workers 1`. Host deployments can run more workers, so the writer uses exclusive creation and no shared counter.
- The owner sets `PORTAL_SECRET_KEY` in production. Open item U-04 records this assumption.
- UID 1000 can write the mounted `data` directory in the container. `documentation/container-deployment.md` line 114 names UID 1000.
- The list responses carry the complete object body and the reported total header. Open items U-01 and U-02 record these assumptions until issue 4634 closes.

## Out of Scope

- Restore, delete, unassign, and every Mist write operation. These belong to issues 4645 and 4646.
- A catalog endpoint, a browser page, and any operator identity. These wait for issue 4636.
- The other object families that issue 4636 enumerates: `gateway-template`, `device-profile`, and `site-setting`.
- Encryption at rest. Decision D-19 records the open question.
- Changes to `web_portal/app.py`, `web_portal/templates/base.html`, and the firmware-policy backup format.
- A new environment variable. The seal key uses the existing `PORTAL_SECRET_KEY` variable.

Warning: a purge removes the only copy of a backup for an object. Purge stays out of scope until an owner-approved workflow exists.

Caution: a refused backup can leave an unverified file in the backup directory. The catalog excludes that file, and no operator action removes it automatically.

## Dependencies

- Issue 4633 (closed): coordinator decisions that authorize offline implementation and name the shared-file rule.
- Issue 4634 (open): API contract evidence for the three list operations.
- Issue 4636 (open): state package, seal, identity, and secret-stability decisions.
- PR 4596 (merged 2026-11-13): full-parity specification and task map.
- PR 4615 (merged 2026-11-13T06:20:12Z): owned `web_portal/services/data_browser.py` in the 2026-11-08 coordinator decision. A scan at drafting time found no open PR that touches that file or `output_scan.py`.
- PR 4208 (open): owns `web_portal/app.py`. This change does not touch that file.

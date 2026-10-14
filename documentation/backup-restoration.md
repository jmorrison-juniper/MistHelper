# Backup restoration: Menu 306

Warning: restoration replaces complete writable organization and site settings.
It can remove changes made after the selected backup.
Examine the preview and verify the backup source before you type `RESTORE`.

Menu 306 restores selected records from the private complete backups that menu 305 creates.
It does not send a firmware execution request or a device-push request.
Restored firmware policies can permit later cloud-managed upgrades.

## Select and preview

1. Select menu 306, or run `python MistHelper.py --menu 306 --dry-run`.
2. Select an existing private bundle.
3. Select the organization records and site records to restore.
4. Type the active cloud hostname to bind the legacy backup to that cloud.
5. Examine every scope, field count, deletion count, and warning.

A selected site requires its saved organization record.
The tool verifies current membership through the complete organization site list.
For a legacy site without saved ownership, the bundle must contain exactly one organization.
The tool refuses ambiguous ownership and mismatched scopes.

The v1 bundle has no authenticated cloud provenance.
A valid checksum proves neither the author nor the original cloud.
Verify the bundle source outside the tool.
The cloud confirmation does not convert a checksum into an authentic signature.

## Exact restoration scope

The tool restores complete saved writable settings, not only firmware policy fields.
Unselected organizations and sites remain unchanged.
Selected settings intentionally return to saved values, including unrelated historical settings.

The local OpenAPI 3.1 schemas define the writable fields.
Known top-level read-only fields remain under server control.
These include identifiers and creation or modification timestamps.
The tool refuses unknown fields, invalid values, nested server-managed content, and unsupported schema shapes.
It does not silently remove an unsafe writable field from the restoration.

A secret placeholder is not a recoverable credential.
The tool refuses recognized masked or redacted values.
Some returned credentials can be unavailable or indistinguishable from real values.
The tool cannot reconstruct a credential that the backup never contained.
Verify the backup source and completeness before restoration.

An absent top-level site `auto_upgrade` field uses the existing `-auto_upgrade` deletion contract.
This restores organization inheritance, not a disabled local policy.
Other absent current fields have no general proven deletion contract.
The tool stops before writes rather than inventing null or deletion behavior.
Named parent objects restore their complete saved writable content.

## Confirm and restore

1. Prepare the plan and wait for every complete recovery backup to pass verification.
2. Examine the sorted scope table, then type `RESTORE` exactly.
3. Examine progress and the completed, failed, and remaining scopes.

The tool checks the source bundle, cloud, membership, and complete current settings again before changes.
Every target needs a durable verified recovery record before the first write.
Each recovery bundle must pass the same format, integrity, and private-access checks as a selected source bundle.
Organization writes precede site writes.
Each target gets another freshness check immediately before its settings write.
Each write requires a saved-state check.
The tool does not retry a settings write automatically.

Warning: the first failed write or saved-state check stops later writes, but earlier changes can remain.
An attempted failed target can also contain an unverified saved change.
The result does not count that target as completed.
Remaining targets have no attempted writes.
No automatic rollback occurs.

The SDK settings endpoints do not provide a conditional update contract.
A separate operator can change settings between the last read and the write.
Freshness checks reduce this interval but do not make the cloud operation atomic.
Keep other settings changes stopped during restoration.

## Graphical workflow

Open **Operations**, expand **Firmware Policies & Recovery**, then select menu **306**.
The workflow occupies the right workspace beside the left menu.
Use the dynamic backup and saved-record controls.
Use **Select all saved records** when the complete bundle is required.
Type the active cloud hostname, then select **Prepare verified recovery backups**.
Preparation creates and verifies recovery before the confirmation controls appear.
Examine the compact, site-name-sorted table and progress below the controls.
Type `RESTORE` exactly to enable **Restore verified plan**.
Use **Cancel prepared plan** to invalidate a plan without writes.

The portal keeps settings and credentials on the server.
Plans belong to one browser session. Active preparation remains valid through long request allowance waits.
Each preview permits one application.
Status polling survives a page refresh. A worker interruption stops the plan without automatic write replay.
Existing portal access controls and request protection apply.
No upload or arbitrary file path is accepted.

## Private files and recovery

Original bundles remain unchanged in `data/.firmware-policy-backups/`.
On POSIX systems, the directory requires mode `0700` and each file requires mode `0600`.
The files must belong to the current account.
On Windows, a fixed Windows PowerShell query reads the owner and access rules through the supported Windows security interface.
It compares SID values, not translated account names.
The current account must own the directory and file.
Only that account, SYSTEM, and the local Administrators group can have access grants.
Windows junctions and other reparse points are refused before the ACL query.
The tool changes no permissions.
If the query is unavailable or access cannot be proven, restoration stops before writes.
Windows ACL decisions have mocked automated coverage. An actual Windows host check remains unverified in this macOS development session.
The loader rejects symbolic links, hard links, duplicate JSON keys, and invalid records.
Legacy JSON bundles have no arbitrary aggregate byte or record-count limit.
The reader validates bounded individual records and complete checksums instead of loading unbounded JSON text.
Large organizations require sufficient private storage and time for every settings read, recovery backup, freshness check, write, and readback.
Existing API usage tools control request admission and report allowance waits.
The private files do not appear in output downloads or previews.

The tool uses the same private format for new recovery bundles.
Keep both the original bundle and each recovery bundle.
Offline automated acceptance uses fixture settings and mocked SDK transport.
It does not establish user approval or a successful production restoration.

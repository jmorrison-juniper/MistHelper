# Backup restoration: Menu 306

Warning: restoration replaces organization and site firmware policies.
It can remove later firmware policy changes and permit cloud-managed upgrades.
Examine the preview and verify the backup source before you type `RESTORE`.

Menu 306 restores firmware policies from selected records in the complete private backups that menu 305 creates.
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

The user selected firmware-policy-only restoration. Complete settings restoration is outside this scope.
Unselected organizations and sites remain unchanged.
Only these firmware policy paths can return to saved values:

| Hardware | Policy path |
| - | - |
| AP | `auto_upgrade` |
| Switch | `switch.auto_upgrade` |
| SSR | `ssr.auto_upgrade` |
| SRX | `juniper_srx.auto_upgrade` |

Unrelated current settings remain unchanged, including credentials and nested parent siblings.
Complete source and recovery snapshots remain private and unchanged.
Unknown or nullable unrelated fields do not enter policy validation or historical restoration requests.
The local public schema validates firmware policy content only.
Malformed, masked, or unsupported firmware policy values stop preparation before writes.
Menu 168 provides the AP policy request pattern, not a complete settings replacement contract.
Missing or empty AP schedule choices use the documented menu 168 defaults.
The preview states those defaults before confirmation.

An absent saved top-level site `auto_upgrade` field uses the existing `-auto_upgrade` deletion contract when a current override exists.
This restores organization inheritance, not a disabled local policy.
An absent saved organization AP policy has no proven unset contract.
The tool stops before writes rather than inventing null or deletion behavior.
Nested policy removal replaces the current parent object without its `auto_upgrade` member.
The replacement retains current unrelated siblings, never historical unrelated siblings.
Saved nested policies replace only that member within the current parent.

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
Expand **Inspect firmware policies** before confirmation.
The comparison distinguishes the historical source, verified recovery backup,
current observation, and proposed policy.
It labels each snapshot time and current observation time.
Missing source fields remain missing. Proposed schedule defaults appear as normalization notices.
Text and bold emphasis identify changed fields without relying on color.
Type `RESTORE` exactly to enable **Restore verified firmware policies**.
Use **Cancel prepared plan** to invalidate a plan without writes.

The portal keeps settings and credentials on the server.
Plans belong to one browser session. Active preparation remains valid through long request allowance waits.
Each preview permits one application.
Status polling survives a page refresh. A worker interruption stops the plan without automatic write replay.
Workers on the same host route requests to the live plan owner through authenticated loopback communication.
They require the same private `data/` directory.
Organization write locks refuse overlapping policy or restoration changes across browser sessions and workers.
Existing portal access controls and request protection apply.
No upload or arbitrary file path is accepted.

## Historical firmware inspection

In menu 306, select a private backup and one saved record under
**Inspect historical firmware policies without restoration**.
Select **View saved firmware policies** to inspect its saved firmware fields.
This action checks source integrity, authenticated organization access, and current membership.
It does not read current settings or prepare restoration.

Select **Compare with current settings** to request an explicit current observation.
The comparison labels current differences and the actual observation time.
Missing policies, empty policies, disabled policies, and inherited site policies remain distinct.
No effective organization values are invented for an absent site override.
The controls remain available after settings changes, while the private bundle remains retained.

Inspection creates no backup, changes no settings, and consumes no restoration proof.
It does not authorize restoration or change a prepared plan.
Unknown policy fields and private siblings never appear.
An unavailable current read reports an error, not an empty policy.
The source bundle remains unchanged.
The private file remains excluded from the general data browser and raw downloads.

The [preparation phases and request counts](org-auto-upgrade-policy.md#preparation-phases-and-request-counts)
explain why initial capture and freshness verification each read complete settings.
Preparation stays locked through pending, ready, and uncertain status.
Only definite preparation failure or a deliberate selection change permits another preparation.

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

## Scope decision and contract limits

The earlier complete-settings implementation rejected both actual 145-record bundles before writes.
Public writable schemas did not establish complete restoration of unknown, nullable, and nested server-managed settings.
The user explicitly selected firmware-policy-only restoration instead.
This decision does not authorize guesses about unrelated writable fields.
Policy preparation requires backup integrity and firmware policy recovery projection before confirmation.

The [public Mist schema at revision `79274e6`](https://github.com/mistsys/mist_openapi/blob/79274e6cd85327ef51a9ab99a9c40a999d4b669a/mist.openapi.json)
does not resolve every observed difference.
All 3,133 upstream property names already occur in the checked-in public schemas.

Complete restoration would require vendor evidence for unrelated fields and their accepted types, replacement rules, and deletion rules.
This remains outside menu 306.
Do not send private settings, credentials, identifiers, or complete backups to obtain this evidence.
Do not remove unknown fields, invent replacement values, or attempt speculative settings writes.
Unsupported firmware policy deletion or content still blocks preparation.
Fixture tests do not establish successful connected restoration. The parent verifies the committed candidate before merge or deployment.

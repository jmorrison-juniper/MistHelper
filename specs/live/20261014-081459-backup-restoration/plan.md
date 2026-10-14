# Implementation Plan: Backup restoration

**Branch**: `jmorrison-juniper-backup-restoration` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

## Summary

Implement a settings-only recovery service shared by menu 306 and the existing protected Flask operations portal.
Validate complete writable snapshots against the checked-in OpenAPI 3.1 schemas.
Reject any setting whose safe restoration cannot be proven.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing mistapi and Flask. Add jsonschema for OpenAPI 3.1 value validation.

**Storage**: Existing private menu 305 bundles under product data. Expiring server-side preview references.

**Testing**: pytest, real SDK request construction with mock sessions, Flask security middleware, and Chromium.

**Target Platform**: Windows, macOS, Linux, and the product container.

Windows ownership uses a fixed Windows PowerShell security query with untranslated SID values.
The query uses an absolute executable, a fixed argument array, a literal environment path, and a ten-second timeout.
Only the current owner, SYSTEM, and Administrators can receive access grants.
Private access verification precedes recovery-file contents and cloud writes.
Mocked decisions run on macOS. Native Windows execution remains unverified.

**Project Type**: Numbered CLI operation and graphical portal.

**Performance Goals**: Bounded bundle size, record count, nesting, preview lifetime, and preview count.

**Constraints**: Zero production writes during development. No secret values outside private server memory and backup files.

**Scale/Scope**: One selected private bundle per plan. Sequential writes. Stop on the first failed operation.

Settings requests redact SDK logger and console diagnostics.
The pinned SDK retries HTTP 429 writes by default.
The guarded settings boundary disables those retries and restores the original SDK setting afterward.
Contract tests exercise the actual SDK retry loop without network access.

## Constitution Check

- Reuse SDK settings methods and SDK pagination. No owned transport is necessary.
- Require exact typed confirmation, complete verified recovery backups, freshness checks, and saved-state checks.
- Move `firmware_policy/backup.py` into `firmware_policy/recovery/backup.py`.
  Update every import and remove the old path without a compatibility wrapper.
  This keeps the parent at five children and gives recovery five modules.
- The moved module logger changes from `firmware_policy.backup` to `firmware_policy.recovery.backup`.
  No persisted class identity or serialized Python object uses that name.
- Nest the new blueprint under the existing firmware policy blueprint. Do not edit contested app or base template files.
- Keep the feature record at five direct children: spec, plan, tasks, evidence, and checklists.
- Existing root and process-folder debt remains unchanged. Incremental remediation is the nested recovery package.
- Keep outputs under product data and failed browser evidence under ignored test artifacts.
- Use the Conventional Commit form and the complete deployment sequence. The parent owns runtime deployment.
- Preserve the private persistent runtime volume.

## Project Structure

- `src/operations/execution/firmware_policy/recovery/`: backup, bundle, schema, workflow, and CLI modules.
- `web_portal/routes/firmware_policy/restore/`: dedicated protected routes and template.
- Existing menu, registry, generated references, and private output denial remain authoritative.
- Add bounded restore-specific unit, integration, contract, and graphical tests inside existing firmware-policy test packages.
- [Research](evidence/research.md), [data model](evidence/data-model.md), [contract](evidence/contract.md), and [validation](evidence/quickstart.md).

## Complexity Tracking

No new hierarchy baseline exception is permitted.
Existing menu and route functions already exceed some historical size limits.
New recovery logic uses named helpers and bounded methods rather than increasing those violations.

## Workflow Execution

PowerShell is unavailable. Safe direct prerequisite checks and explicit artifact paths replace the PowerShell setup command.
The unsafe shell branch script is not executed.
Optional commit hooks remain deferred. Disabled companion hooks remain disabled.
The selector ownership handover from PR #4223 permits this branch to select this feature.

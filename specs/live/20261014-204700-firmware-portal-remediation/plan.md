# Implementation Plan: Firmware portal remediation

**Branch**: `jmorrison-juniper-firmware-portal-remediation` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

## Summary

Replace raw portal output with integrated operation workspaces and pollable, session-owned jobs.
Prepare and verify every backup before confirmation. Preserve complete recovery, freshness, and readback checks.
Stream legacy bundle parsing by record instead of rejecting aggregate sizes. Reuse the shared API usage tools for every request.

## Technical Context

**Language/Version**: Python 3.13 and browser JavaScript.
**Primary Dependencies**: mistapi 0.64, Flask, existing shared API usage tools, and existing portal styles.
**Storage**: Private backups and job status beneath DATA_DIR. No production volume changes.
**Testing**: pytest unit, contract, integration, and fixture Playwright browser tests.
**Target Platform**: Windows 11, macOS, and Linux.
**Project Type**: Existing CLI and web portal.
**Performance Goals**: More than 4,000 sites, no quadratic source parsing or membership reads per target.
**Constraints**: No raw settings in status. No uncertain write retry. No firmware execution endpoints.
**Scale/Scope**: Menus 305 and 306 only.

## Constitution Check

- Reuse the authenticated SDK and existing settings safeguards.
- Keep runtime records private beneath data. Commit fixture UI evidence only.
- Add compliant nested modules where existing packages already contain five modules.
- Preserve existing package names and call sites. Incrementally reduce touched oversized methods.
- Existing process-folder debt remains. This change adds only its unique changelog and managed timestamp record.
- Existing operations.js and operation.py exceed structural limits. Make narrow integration changes, not unrelated restructuring.
- Preserve the separate generic safe-operation gate. Dedicated destructive workflows must never enter that runner.
- Commit milestones with Conventional Commit subjects and the required coauthor trailer.
- The parent owns live acceptance and deployment. Do not merge or enable automatic merge.

## Project Structure

- Domain: `src/operations/execution/firmware_policy/` and its recovery package.
- Portal: `web_portal/routes/firmware_policy/`, operation categories, operations template and scripts.
- Tests: existing firmware policy unit, contract, integration, and web portal E2E directories.
- Documents: this directory, operator guides, wiki pages, and a narrow README link.

## Design

Domain workflows expose an optional sanitized progress callback. A callback receives an event dictionary.
Events describe phase, scope, identifier, name, completed count, total, and waiting seconds when known.
The portal uses these events to persist sanitized status while a bounded executor owns work.
Preparation captures complete snapshots and writes verified backups. Apply reuses that recovery proof and rechecks durable files and current settings.
Preparation also projects every snapshot through the restoration schema before it permits confirmation.
The user-directed revision restricts that projection to firmware policies.
Complete source and recovery records remain private and unchanged.
Restoration projects only `auto_upgrade` and nested `switch`, `ssr`, and `juniper_srx` auto-upgrade policies.
Required nested parent replacements retain current siblings, not historical unrelated siblings.
Readback checks the planned policies and preservation of unrelated current fields.
Whole-settings unknown fields, nullable fields, and read-only metadata do not enter policy projection or restoration requests.
Only proven policy deletion contracts are permitted.
Any AP schedule defaults from menu 168 appear in the preview before confirmation.
Existing CLI apply calls still perform the complete backup gate.

Portal preparation returns HTTP 202 with `job_id`. Status returns state, progress, sanitized rows, and a token only when ready.
Apply consumes that token once and retains the same pollable job identifier. Active preparation does not expire after ten minutes.
Status survives a worker restart and reports interrupted work explicitly. Private executable plans do not resume automatically.
Native lifetime locks identify live same-host owners. Authenticated loopback requests reach the worker that owns the private plan.
All workers require the same private DATA_DIR.
Shared cloud and organization locks exclude overlapping writers across both workflows and browser sessions.
The locks remain held through proof checks, freshness checks, writes, and readback.
Preparation remains concurrent because it performs no cloud writes.

Bundle readers preserve the existing JSON envelope and canonical checksum. They stream records and validate each bounded record.
Reject duplicate JSON keys, invalid shapes, invalid private access, partial files, and mismatched checksums.
Do not replace the 8 MiB limit with another aggregate threshold.

Organization settings writes precede site writes across each complete run.
Freshness checks remain at each write boundary. Source verification occurs at the apply boundary and detects later modification without repeated complete parses.
Request admission includes reads, pagination, usage probes, and writes. Valid waits update progress instead of expiring plans.

## Complexity Tracking

Mist transport remains exclusively in the SDK. Internal same-host worker routing uses authenticated loopback communication.
No external service or separately deployed worker is necessary.
PowerShell is unavailable on this host. The setup-plan script only resolves feature paths and copies the template.
This phase performs those steps directly using the existing feature pointer and the resolved local template.

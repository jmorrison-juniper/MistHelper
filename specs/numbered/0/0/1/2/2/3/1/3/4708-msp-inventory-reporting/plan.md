# Implementation Plan: Accurate MSP inventory coverage

**Branch**: `jmorrison-juniper-msp-inventory-reporting` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

## Summary

Calculate coverage from collected successful results. Pass a console-only coverage label to all three combined-report renderers.
Preserve complete-report headings and every export field and filename.

## Technical Context

**Language/Version**: Python 3.13 or newer. The local environment uses Python 3.14.

**Primary Dependencies**: Existing PrettyTable rendering, injected runner, and injected exporter.

**Storage**: No new storage. Tests capture exporter calls without writes.

**Testing**: Pytest, mocked collaborators, blocked DNS and sockets.

**Target Platform**: Windows, macOS, Linux.

**Project Type**: Command-line operation.

**Performance Goals**: Retain the existing sequential batch behavior.

**Constraints**: Local repair only. No live Mist, SSH, firmware, or production database access.

**Scale/Scope**: One existing source module, one existing test module, one unique release note, and this feature record.

## Constitution Check

- No export schema, transport, or destructive-operation change.
- No new dependency or public entry point.
- New feature directories remain within five children.
- Existing source module and orchestrator exceed structural limits. Preserve their existing names and avoid unrelated restructuring.
- Incremental remediation: keep the new coverage helper below 25 lines and each changed signature at five parameters or fewer.
- The established release-note directory has existing process-folder debt. Add only the required unique issue fragment.
- Separate remediation remains outside this reservation: migrate existing process records through their managed maintenance process.
- Product export paths and fields remain unchanged.
- Optional commit hooks are deferred to one final local commit.
- The branch-creation hook conflicts with the assigned app-managed worktree and is not executed.
- PowerShell is unavailable. The route follows the verified eight-digit algorithm in `spec-route.ps1`.
- Do not modify the shared `.specify/feature.json` or generated agent context.

## Project Structure

- Source: `src/mist/resources/inventory/org_device_inventory_msp.py`.
- Tests: `tests/unit/inventory/test_org_device_inventory_msp.py`.
- Release note: `changelog.d/issue-4708-msp-inventory-reporting.md`.
- Feature records: this managed root, with supporting records under `design/`.

## Complexity Tracking

The existing module has many functions and the orchestrator has many methods.
The repair adds one cohesive coverage helper without moving unrelated code or adding compatibility layers.
No new function exceeds five parameters or 25 lines.

## Design Review

The coverage label reaches model, firmware, and pivot headings through explicit parameters.
No shared mutable report state is necessary.
The default label preserves existing direct renderer calls and complete-report behavior.

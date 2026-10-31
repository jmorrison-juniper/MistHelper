# Implementation Plan: AP discovery failure

**Branch**: `jmorrison-juniper-audit-missing-input-defaults`
**Date**: 2026-10-30
**Spec**: [Specification](spec.md)

## Summary

Remove the first-page fallback after a failed organization site read.
Log the failure and raise the original exception before AP discovery continues.

## Technical Context

- Language: Python 3.13 or newer.
- Dependency: the existing mistapi 0.64 SDK.
- Storage: no schema or persistence change.
- Testing: pytest with mocked SDK responses.
- Platforms: Windows, macOS, and Linux.
- Scope: one exception boundary in one existing manager.
- Performance: no added request, retry, or site scan.
- Constraint: no live Mist access, identifier validation, or credential change.

## Constitution Check

The app manages the existing branch. Do not execute a second branch creation.
The PowerShell route helper verified the managed destination.
Use a command-scoped feature selector. Do not change the shared feature pointer.
Optional commit hooks are deferred until the complete local validation.
Disabled companion hooks remain disabled.

The existing manager and test module exceed structural limits.
This repair adds no production declaration or hierarchy child.
The independent remediation action is to divide discovery responsibilities during a separately reserved manager refactor.
Do not include that refactor here.
The release note uses the required unique process-record exception.

Preserve typed confirmation and all successful discovery paths.
Do not run menu 207 against Mist. Mock every external request.
No new transport is necessary.
Before and after the design, the bounded scope satisfies the safety and ownership checks.

## Project Structure

- Source: `src/mist/resources/device/ap_profile_migration_manager.py`.
- Tests: `tests/unit/device/test_ap_profile_migration_manager.py`.
- Release note: `changelog.d/issue-2753-ap-discovery-failure.md`.
- Records: this feature root and its `design/` directory.

## Implementation Sequence

1. Add direct failure cases for absent, empty, and populated first-page data.
2. Add a migration entry-point refusal case with real discovery and mocked SDK calls.
3. Demonstrate failures before the repair.
4. Remove the fallback, log the site-pagination error, and raise the original error.
5. Verify empty and populated successful reads, run local checks, and publish without automatic merge.

## Complexity Tracking

The existing discovery helper exceeds 25 physical lines.
Removing the fallback reduces executable statements and preserves its current responsibility.
The broad catch remains solely to log and immediately raise.
It returns no substituted value and does not permit discovery after failure.

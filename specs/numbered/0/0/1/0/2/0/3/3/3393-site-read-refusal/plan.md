# Implementation Plan: Site read refusal

**Branch**: `jmorrison-juniper-fix-org-upgrade-cloud-read` | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

## Summary

Catch `RequestException` at the three affected route boundaries.
Return the existing 503 service status with a fixed cloud-read message.
Keep the save refusal before all plan and session writes.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: Flask, requests, and the unchanged mistapi SDK.

**Storage**: Existing run store and signed browser session. No schema change.

**Testing**: pytest contract tests and Playwright browser tests with local mocks.

**Target Platform**: Windows, macOS, and Linux.

**Project Type**: Existing firmware planning portal.

**Performance Goals**: No additional cloud request.

**Constraints**: No Mist cloud access, firmware execution, or issue #3394 changes.

**Scale/Scope**: One save route and two page routes.

## Constitution Check

- The route change preserves validation, successful responses, and existing broad exception handlers.
- The existing worktree branch remains active. A branch hook must not replace the app-managed branch.
- The managed route resolves through `create-new-feature.ps1 -DryRun -Number 3393`.
- The command-scoped feature selector leaves `.specify/feature.json` unchanged.
- No SDK call, credential handling, storage schema, or production confirmation changes.
- No new product module or class increases structural debt.
- The route module already exceeds the top-level declaration limit.
  Add only fixed error constants and narrow handlers. A separate incremental action can extract planning routes after human review.
- Existing route functions exceed 25 lines. A separate route-division change must address that debt without mixing firmware behavior.
- The contract-test folder and changelog folder already exceed five children.
  Add only the required issue-owned test and release fragment. Their separate migration must preserve existing discovery and release rules.
- Test artifacts remain in ignored directories.
- The commit uses the Conventional Commits format.
- Human review blocks merge and deployment. The user explicitly prohibits issue closure, merge, and automatic merge.

## Project Structure

### Documentation (this feature)

The feature root contains `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`.
The design directory contains the research, data model, validation guide, contracts, and requirements checklist.

### Source Code (repository root)

- `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`: three narrow transport handlers and shared refusal constants.
- `tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py`: real routes with the existing site-reader seam.
- `tests/e2e/upgrade_portal/test_org_upgrade_flow.py`: browser preservation of form values after the same 503 envelope.
- `changelog.d/issue-3393-site-read-refusal.md`: operator-visible recovery behavior.

**Structure Decision**: Reuse current routes and test fixtures. Do not change the reader or firmware target selection.

## Complexity Tracking

Three short handlers avoid a new exception hierarchy and avoid a blueprint-wide handler that could change unrelated transport failures.
Each handler logs the organization, action, and exception class without raw transport text.
No compatibility layer or new transport is necessary.

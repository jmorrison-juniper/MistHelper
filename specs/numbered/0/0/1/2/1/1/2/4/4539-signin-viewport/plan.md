# Implementation Plan: Sign-in viewport fit

**Branch**: `jmorrison-juniper-upgrade-portal-sign-in-overflow` | **Date**: 2026-10-31 | **Spec**: [spec.md](spec.md)

## Summary

Allow long service-check text to wrap inside the sign-in card. Strengthen the reported browser journey without removing existing viewport coverage.

## Technical Context

**Language/Version**: CSS and Python 3.13.
**Primary Dependencies**: Existing Flask templates, Bootstrap, pytest, and Playwright Chromium.
**Storage**: No changes. Browser fixtures use local test stores.
**Testing**: The reported history, comparison, error, and viewport journey.
**Target Platform**: Existing desktop and phone browsers.
**Project Type**: Web portal.
**Performance Goals**: No additional request or script.
**Constraints**: Preserve authentication and #4541 ownership limits.
**Scale/Scope**: One CSS rule and assertions in one released test file.

## Constitution Check

- The eight-level numeric route comes from `Resolve-SpecFeaturePath` through `create-new-feature.ps1 -DryRun -Number 4539`.
- The feature hook ran with `--dry-run` to preserve the app-managed branch.
- Command-scoped `SPECIFY_FEATURE_DIRECTORY` avoids a shared selector change.
- Existing source files gain no new hierarchy child.
- The required unique changelog fragment enters the established process folder.
- Existing process-folder debt remains outside scope. Incremental remediation belongs to the established managed-route migration.
- The existing journey exceeds the function-size limit. This change adds assertions only and preserves its coverage.
- Separate incremental remediation: divide the existing journey after its current owner releases the remaining file scope.
- No Mist Cloud transport, production credential, schema, or destructive operation changes.
- Browser evidence stays in the existing ignored artifact folder.
- Recheck after design: the same constraints hold.

## Project Structure

### Documentation

The feature root holds `spec.md`, `plan.md`, `tasks.md`, and `design/`.
Supporting records remain under `design/`, with at most five children per new level.

### Source Code

- `src/interfaces/portals/upgrade_portal/app/assets/static/css/portal.css`
- `tests/e2e/upgrade_portal/journeys/test_crosscut_journeys.py`
- `changelog.d/issue-4539-upgrade-portal-sign-in-overflow.md`

No open pull request owned the CSS path at the pre-edit check.
Draft #4541 owns the test file and granted the scoped handoff stated in the request.
Its workflow, fixtures, and parity records remain unchanged.

## Complexity Tracking

The fix uses one selector and one wrapping declaration. It adds no abstraction, dependency, or production Python symbol.

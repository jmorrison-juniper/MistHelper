# Implementation Plan: Busy-site refusal

**Branch**: `jmorrison-juniper-4540-busy-site-refusal` | **Date**: 2026-10-31 | **Spec**: [spec.md](spec.md)

## Summary

Move the existing busy-refusal declaration into the scope of its caller.
Keep its behavior and address validation unchanged.
Add synthetic browser coverage in the released journey file.

## Technical Context

**Language/Version**: JavaScript and Python 3.13.
**Primary Dependencies**: Existing Flask portal, pytest, and Playwright.
**Storage**: No product storage change.
**Testing**: Synthetic browser responses and existing portal contract tests.
**Target Platform**: Chromium against an isolated loopback portal.
**Project Type**: Existing web application.
**Performance Goals**: Preserve the current refusal rendering and scroll behavior.
**Constraints**: No live cloud requests, firmware writes, merge, or auto-merge.
**Scale/Scope**: One JavaScript declaration and the released browser test file.

## Constitution Check

- The numeric route uses eight base-5 segments.
- Feature selection remains command-scoped. The tracked feature pointer remains unchanged.
- The mandatory branch hook ran in dry-run mode because the app already owns this branch.
- Optional commit hooks remain deferred until validation.
- No Mist transport, public response, storage, or permission changes are required.
- Existing source and journey modules exceed the five-member limit. This change does not restructure unrelated behavior.
- Separate incremental remediation: divide these established modules in a separately owned issue, not this repair.
- The changelog directory has existing child-count debt. Add only the required issue-specific fragment.
- Separate incremental remediation: retain the existing process-folder migration policy for that debt.
- Preserve the retrying viewport assertion with `ratio=1`.
- The user prohibits merge and auto-merge. Stop after the verified feature commit.

## Project Structure

- Source: `src/interfaces/portals/upgrade_portal/app/assets/static/js/portal.js`.
- Browser tests: `tests/e2e/upgrade_portal/journeys/test_upj_multisite_journeys.py`.
- Release note: `changelog.d/issue-4540-busy-site-refusal.md`.
- Feature records: `spec.md`, `plan.md`, `tasks.md`, and supporting records under `design/`.

## Design and Validation

The [research record](design/research.md) records the scope defect.
The [response contract](design/contracts/refusal.md) defines the synthetic cases.
The [validation guide](design/quickstart.md) gives focused commands.

Run the new browser cases before the source repair to prove they detect the missing declaration.
After the repair, run the focused browser cases, relevant contract tests, formatting, lint, and test-quality checks.

## Complexity Tracking

No new product function or abstraction is required.
The existing busy-refusal declaration becomes a sibling of the replay-refusal declaration.

# Implementation Plan: Licensing comparison layout

**Branch**: `jmorrison-juniper-fix-4258-licensing-comparison-layout`
**Date**: 2026-10-16
**Spec**: [Requirements](spec.md)

## Summary

Restore the source visual hierarchy within the existing portal shell.
Render the existing comparison response as numeric columns, totals, and summary cards.
Keep transport, authorization, export, and purchase calculations unchanged.

## Technical Context

**Language/Version**: Python 3.13, JavaScript, CSS, Jinja.
**Primary Dependencies**: Existing Flask, mistapi, and Playwright dependencies.
**Storage**: Existing browser sessionStorage. Exports use the shared data exporter.
**Testing**: pytest integration tests and Playwright browser tests.
**Target Platform**: Existing MistHelper web portal on supported host platforms.
**Project Type**: Existing portal blueprint.
**Performance Goals**: No extra comparison requests for client-side rendering.
**Constraints**: No edits to `web_portal/app.py` or `web_portal/templates/base.html`.
**Scale/Scope**: One licensing page and focused offline tests.

## Constitution Check

The feature uses the managed numeric route with eight base-5 levels.
The existing licensing package exceeds five children. Modify its existing template and assets only.
Keep rendering functions small and group related page, data, and form behavior in the existing feature script.
The process folder exception permits only this issue's unique specification and release fragment.
Incremental remediation: keep future licensing modules inside compliant child packages rather than adding package-level siblings.
No Python production symbols, transport, database, or cloud mutation changes are planned.
Existing mistapi calls, session authorization, CSRF, and CSV neutralization remain authoritative.
Use explicit staging paths and a Conventional Commit with `Closes #4258`.
Reevaluate these constraints after browser validation.

## Project Structure

- `src/interfaces/portals/licensing_comparison/templates/licensing_comparison.html`: extend `base.html` and define accessible panels.
- `src/interfaces/portals/licensing_comparison/static/licensing_comparison.css`: scope charcoal and magenta styles to the dashboard.
- `src/interfaces/portals/licensing_comparison/static/licensing_comparison.js`: normalize display data and connect safe DOM controls.
- `tests/e2e/web_portal/licensing_comparison/`: extend existing fixtures and add a focused browser regression file.
- `changelog.d/issue-4258-licensing-comparison-layout.md`: explain the user-visible repair.
- `design/`: data model, UI contract, and validation guide.

## Validation

Run existing licensing integration and E2E tests, then all new browser cases.
Verify desktop and narrow layouts through computed styles and screenshots.
Run Ruff, Black, targeted types, Bandit, docstrings, symbol checks, STE, and the test quality ratchet where applicable.
Inspect the final diff to confirm no shared files or security services changed.

## Tooling Constraints

PowerShell is absent, so resolve prerequisites and composed local templates directly.
The branch hook is not executed because its script uses prohibited indirect shell expansion.
The app-managed isolated branch already exists at the project default branch revision.

## Deployment Boundary

The requested delivery ends with a checked pull request and safe merge.
No production deployment or container replacement is authorized by this repair.
The standard main container build remains the repository deployment path.
Do not replace a running production container from this session.

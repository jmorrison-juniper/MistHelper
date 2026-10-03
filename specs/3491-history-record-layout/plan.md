# Implementation Plan: Compact history records

**Branch**: `jmorrison-juniper-history-record-layout` | **Date**: 2026-10-03 | **Spec**: [spec.md](spec.md)

**Input**: [Issue #3491](https://github.com/jmorrison-juniper/MistHelper/issues/3491) and its complete comments.

## Summary

Add a history component stylesheet through the existing `head_extra` block.
Give Runs, Multi-site upgrades, and Audit log fixed column budgets and whole-value titles.
Use the existing theme tokens for all row surfaces.
Keep every source and scope decision unchanged.

## Technical Context

**Language/Version**: Python 3.13, Jinja HTML, and CSS.
**Primary Dependencies**: Existing Flask, Gunicorn, pytest, and Playwright pins.
**Storage**: Existing records only. Tests use process-owned native records and a private temporary audit trail.
**Testing**: Native Chromium journeys, Flask asset contracts, adjacent tests, and current quality gates.
**Target Platform**: The shipped browser application. Local verification uses macOS and installed Chromium.
**Project Type**: Existing web application.
**Performance Goals**: Record rows do not exceed 48 pixels.
**Constraints**: Local-only work. No shared asset, route, model, fixture, dependency, policy, or deployment edits.
**Scale/Scope**: Two scopes, three widths, two themes, and three record tables.

## Constitution Check

- Product changes contain no Python code or new service.
- Test helpers use semantic classes and bounded methods.
- Existing large asset and test directories remain outside this repair's restructuring scope.
- The explicit file reservation permits the new component and two test modules in those existing directories.
- A separate structural repair must address those existing directory limits.
- Add comments only for non-obvious intent.
- Use ASCII action logs with measured counts and no credentials.
- Keep shared `.specify` state unchanged.
- The user's local-only grant excludes publication and deployment.

## Project Structure

### Documentation (this feature)

```text
specs/3491-history-record-layout/
  .spec-context.json
  spec.md
  plan.md
  tasks.md
  research.md
  data-model.md
  quickstart.md
  contracts/presentation.md
  checklists/requirements.md
```

### Source Code (repository root)

```text
src/upgrade_portal/app/assets/templates/review/history.html
src/upgrade_portal/app/assets/static/css/history_records.css
tests/e2e/upgrade_portal/test_history_record_layout_journey.py
tests/contract/upgrade_portal/test_history_record_layout_assets.py
changelog.d/issue-3491-history-record-layout.md
```

**Structure Decision**: Keep all product rules inside one history component.
Use a private native browser server for controlled audit records.
The server imports the canonical native fixture once in its own child process.
The parent reads its already-loaded pytest fixture module without another import.
A release record supplies an audit digest without a held lock or shared audit change.
All browser requests remain on the exact owned loopback origin.

## Verification Order

1. Record the unchanged native browser measurements before product edits.
2. Execute the new failing browser guard.
3. Apply the component and presentation changes.
4. Execute the same guard and bounded negative mutations.
5. Execute adjacent tests and compare complete original browser membership and skips.
6. Verify resources, gates, screenshots, cleanup, and a clean unpublished commit.

## Complexity Tracking

No product class, wrapper, source adapter, or compatibility path is necessary.
The feature-specific browser process exists only to isolate controlled records from the shared 603-case server.

# Implementation Plan: Generated Operations control labels

**Branch**: `jmorrison-jnpr-fix-generated-control-labels` | **Date**: 2026-10-13 | **Spec**: [spec.md](spec.md)

**Input**: `specs/live/20261013-182828-fix-generated-control-labels/spec.md`

## Summary

Set the existing generated label's `htmlFor` to `param-` plus the unchanged parameter name.
Extend the existing browser proof and remove its strict expected-failure marker.

## Technical Context

**Language/Version**: JavaScript and Python 3.13.
**Primary Dependencies**: Browser DOM, Flask, pytest, and Playwright.
**Storage**: No storage changes.
**Testing**: Focused browser tests, existing portal unit tests, and relevant local gates.
**Target Platform**: Desktop and mobile browsers.
**Project Type**: Existing web portal.
**Performance Goals**: No additional requests or asynchronous work.
**Constraints**: Preserve identifiers, field names, values, dependencies, payloads, classes, and layout.
**Scale/Scope**: One shared label builder. Regression coverage includes menus 257 through 268.

## Constitution Check

- Modify existing source and test children. Add only this unique managed specification and release-note fragment.
- Existing process folders contain grandfathered child-count debt. Do not alter their baseline.
- Incremental remediation: contain this record within the managed `specs/live/` root and keep its own levels bounded.
- Existing JavaScript uses standalone functions. This one-line correction adds no function or structural debt.
- Browser tests use an isolated Flask application with no Mist session.
- No environment variables, API methods, schema, container, or production operations change.
- Use a Conventional Commit and a template-based PR closing #4059.
- The user requests a PR, not deployment. Do not merge or deploy production software.
- PowerShell is absent. Create the template-based artifacts directly and retain the app-managed worktree branch.
- Optional commit hooks are deferred to the requested tested commit. Disabled companion hooks do not execute.

## Project Structure

```text
web_portal/static/js/operations.js
tests/e2e/web_portal/test_operations_accessible_names.py
changelog.d/issue-4059-fix-generated-control-labels.md
specs/live/20261013-182828-fix-generated-control-labels/
  spec.md
  plan.md
  tasks.md
  checklists/requirements.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/labels.md
    analysis.md
```

**Structure Decision**: Keep the shared source change minimal. Use existing tests and nested process records.

## Complexity Tracking

No new abstraction, parameter, request, or product file is needed.
The existing large JavaScript module remains unchanged except for one association assignment.

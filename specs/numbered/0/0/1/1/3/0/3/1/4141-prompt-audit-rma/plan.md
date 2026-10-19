# Implementation Plan: Juniper RMA prompt audit

**Branch**: `jmorrison-juniper-prompt-audit-rma-paths`
**Date**: 2026-10-19
**Spec**: [Specification](spec.md)

## Summary

Repair shared prompt traversal before removing seven exemptions.
Expand each selectable dependent control path in the existing guard.
Compare exact Juniper prompt counts and retain the browser scenarios.

## Technical Context

**Language/Version**: Python 3.13.
**Primary Dependencies**: pytest, Playwright, and the pinned `misthelper-devtools` package.
**Storage**: No schema or product data changes.
**Testing**: Focused guard tests and the existing synthetic Juniper browser suite.
**Target Platform**: Windows, macOS, and Linux.
**Project Type**: Development guard for a browser portal.
**Performance Goals**: Parse the source index once per test module.
**Constraints**: No live credentials, service calls, runtime changes, or new exemptions.
**Scale/Scope**: Seven affected menus and both key choices in three menus.

## Constitution Check

The managed allocator returned the numeric route.
The command-scoped selector leaves `.specify/feature.json` unchanged.
The feature root will have five children: specification, plan, tasks, analysis, and design.
The design directory will have four children: checklist directory, research, data model, and quickstart.

The existing test module exceeds the module name limit.
The repair extends that established guard without adding another test-directory child.
Incremental remediation: separate its audit comparison responsibilities in a future scoped issue.
The release-note directory has existing process-folder debt.
This change adds only its required unique fragment.
Incremental remediation: the release coordinator removes merged fragments during release preparation.

No product code, cloud transport, confirmation, output path, or secret handling changes.
No container deployment is necessary for a development-only dependency and guard change.
Use a Conventional Commit subject and the existing pull request template.
The shared-tool prerequisite owns its own specification, tests, and reviewed merge.

**Post-design result**: Pass with the recorded existing structural debt.

## Project Structure

```text
requirements-dev.txt
tests/unit/web_portal/test_portal_required_controls.py
tests/e2e/web_portal/test_juniper_menus_browser.py  (preserved)
changelog.d/issue-4141-prompt-audit-rma.md
specs/numbered/0/0/1/1/3/0/3/1/4141-prompt-audit-rma/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    checklists/requirements.md
    research.md
    data-model.md
    quickstart.md
```

**Structure Decision**: Keep guard logic with its existing tests.
Change the dependency pin only after the shared repair merges.

## Complexity Tracking

| Existing violation | Reason for narrow change | Incremental action |
| --- | --- | --- |
| Large test module | The exemption set and comparison already live there. | Separate comparison responsibilities in a later issue. |
| Release-note directory size | The repository requires one unique fragment. | Remove merged fragments during release preparation. |

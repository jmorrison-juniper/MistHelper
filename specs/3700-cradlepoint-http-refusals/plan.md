# Implementation Plan: Cradlepoint HTTP refusals

**Branch**: `jmorrison-juniper-verbose-succotash` | **Date**: 2026-10-01

**Spec**: [spec.md](spec.md)

**Input**: Issue #3700 and the coordinator's bounded offline assignment.

## Summary

Add one genuine status-validation method to the existing exporter.
Call it immediately after the endpoint returns.
Use the existing menu exception boundary for visible failures.
Preserve the row builder, persistence method, menu method, and shared response helpers.

## Technical Context

**Language/Version**: Python `3.13.13`.

**Primary Dependencies**: Existing `mistapi` `0.64.0`, `requests`, and logging.

**Storage**: No new storage behavior. Tests replace the shared writer.

**Testing**: Existing pytest, coverage, Ruff, Black, mypy, Bandit, and repository analyzers.

**Target Platform**: macOS validation with unchanged cross-platform production code.

**Project Type**: Menu-driven command-line application.

**Performance Goals**: One endpoint call for each operation. No additional requests.

**Constraints**: No live cloud or production store access. No publication grant exists.

**Scale/Scope**: One exporter, its owned positive doubles, and one dedicated test module.

## Constitution Check

The exporter currently has four semantic methods.
The status validator becomes its fifth method.
No wrapper, alias, adapter class, or default-success path is necessary.

The existing export and test directories exceed five children.
This surgical change does not restructure those existing directories.
The new tests occupy one dedicated nested directory.
The feature root has five children. The design directory has five children.
Separate directory consolidation belongs to a later structural repair.

The existing `_fetch` docstring makes its full source span exceed 25 lines.
Its executable body remains below 25 lines.
The new method remains below 25 lines.
Do not rewrite unrelated methods to reduce documentation line counts.

The deployment pipeline remains incomplete by explicit assignment.
The coordinator owns sequential publication at position 33.
No push, pull request, merge, workflow, or deployment is authorized.

### Feature-only workflow

Apply the current repository custom-agent procedures and templates.
The active template resolver returned `.specify/templates/spec-template.md`.
The mandatory `speckit.git.feature` hook failed with exit `1`:

```text
Error: Branch 'jmorrison-juniper-verbose-succotash' already exists. Please use a different feature name or specify a different number with --number.
```

The hook received the exact existing branch through `GIT_BRANCH_NAME`.
The branch remained unchanged.
Use feature-only template artifacts instead of changing the app branch or shared feature state.
Do not write `.specify/feature.json`, common agent context, or shared handoff records.
No successful custom-agent or deployment run is claimed.

## Project Structure

### Documentation (this feature)

```text
specs/3700-cradlepoint-http-refusals/
|-- spec.md
|-- plan.md
|-- tasks.md
|-- checklists/
|   `-- requirements.md
`-- design/
    |-- research.md
    |-- data-model.md
    |-- quickstart.md
    |-- verification.md
    `-- contracts/
        `-- status.md
```

### Source Code (repository root)

```text
src/export/org_cradlepoint_connection_exporter.py
tests/unit/export/test_org_cradlepoint_connection_exporter.py
tests/unit/export/cradlepoint_http_refusals/test_native_responses.py
changelog.d/issue-3700-cradlepoint-http-refusals.md
```

**Structure Decision**: Keep all production logic in the existing semantic class.
Place native-response evidence in a dedicated test module.
Keep gate artifacts and the offline pull request draft outside the tracked feature.

## Complexity Tracking

| Existing constraint | Bounded decision | Separate repair |
| --- | --- | --- |
| Export directories exceed five children. | Edit only the owned exporter and use nested native tests. | Consolidate directories in a separate issue. |
| `_fetch` has a long descriptive docstring. | Preserve the docstring and keep the executable body bounded. | Review documentation spans separately. |
| Deployment requires remote actions. | Prepare only the authorized local commit. | The coordinator performs protected publication after a grant. |

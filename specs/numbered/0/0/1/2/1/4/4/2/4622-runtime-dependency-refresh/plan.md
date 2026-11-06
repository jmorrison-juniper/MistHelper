# Implementation Plan: Runtime Dependency Refresh

**Branch**: `chore/4622-runtime-dependency-refresh` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification under `specs/numbered/0/0/1/2/1/4/4/2/4622-runtime-dependency-refresh/`.

## Summary

Refresh the requested runtime package versions. Preserve all platform markers. Resolve one lock and generate both dependency exports from it. Keep the change limited to the lock, exports, and one issue-specific release note.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: The 23 runtime package updates requested in `requirements.txt`, plus required transitive packages.

**Storage**: `uv.lock`, `requirements.txt`, and `requirements-dev.txt`.

**Testing**: Existing pytest dependency and SDK checks, dependency audit, package consistency check, and import checks.

**Target Platform**: Windows, macOS, and Linux.

**Project Type**: Python command-line and web application.

**Performance Goals**: No runtime performance change is in scope.

**Constraints**: Preserve all 11 platform markers and package identities. Resolve against the public package index when the machine mirror rewrites package identity. Do not change source, manifests, tests, workflows, or governance settings.

**Scale/Scope**: 23 requested runtime updates, existing locked packages, and required transitive packages.

## Constitution Check

- **Managed records**: This feature uses the required eight-level base-5 route. It does not change `.specify/feature.json`.
- **Process folders**: The specification adds no direct child under `specs/`. The parent owns the required unique `changelog.d/issue-4622-runtime-dependency-refresh.md` record.
- **Existing process-folder debt**: The process-folder baseline remains the authority. Track any existing excess in a separate remediation change. This feature adds no excess under `specs/`.
- **Code structure**: No source code, class, function, or test changes are in scope.
- **Mist Cloud transport**: This feature does not contact Mist Cloud.
- **Output and data safety**: The refresh does not change product output paths, databases, or operational data.
- **Release pipeline**: The parent owns validation, commit, pull request, and merge steps. Enable squash auto-merge only after all required checks and CodeQL pass on a branch current with `main`.

**Gate result**: Pass for the bounded dependency refresh. The parent must complete the remaining release pipeline.

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/2/1/4/4/2/4622-runtime-dependency-refresh/
  spec.md
  plan.md
  tasks.md
  design/
    checklists/requirements.md
    data-model.md
    quickstart.md
    research.md
```

### Dependency files

```text
uv.lock
requirements.txt
requirements-dev.txt
changelog.d/issue-4622-runtime-dependency-refresh.md
```

**Structure Decision**: Keep the three planning files at the managed feature root. Keep supporting documents under `design/`. The parent owns dependency files and the release note.

## Complexity Tracking

No code structure change or constitution exception is required.

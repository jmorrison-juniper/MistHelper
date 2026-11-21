# Implementation Plan: Refresh And Pin Project Dependencies

**Branch**: `4867-refresh-dependencies`

**Date**: 2026-11-21

**Spec**: [spec.md](spec.md)

## Summary

Refresh compatible packages across the root Python project, Mist Ops Platform, and Ops Portal.
The refresh keeps the Python 3.15 floor, regenerates exact lock exports, and preserves package constraints that protect existing behavior.

## Technical Context

**Language/Version**: Python 3.15.2, JavaScript and TypeScript for the Ops Portal

**Primary Dependencies**: UV, pytest, mistapi, FastAPI, React, Vite, npm

**Storage**: No application storage change

**Testing**: UV lock checks, pytest, npm audit, npm typecheck, npm lint, npm tests, pip-audit

**Target Platform**: Windows 11, macOS, Linux, Podman container

**Project Type**: Python CLI, Flask portal, React portal, FastAPI platform

**Performance Goals**: No package update adds an avoidable runtime or test delay

**Constraints**: Python 3.15 support, package API compatibility, exact pip exports, synchronized npm lock

**Scale/Scope**: Root package manifests, Ops Platform manifests, Ops Portal manifests, CI package install paths

## Constitution Check

The package refresh meets the repository constitution.

- The change preserves the Python 3.15 floor.
- The change adds no Mist API method or owned WebSocket transport.
- The change creates no root-level direct child and uses the managed Spec Kit route.
- The change adds no application output under a directory outside `data/`.
- The change uses Conventional Commit and pull request forms.
- The change must complete local gates before commit and hosted checks before merge.

The stale dependency PR 4806 is coordinated first because it overlaps root lock and export files.

## Project Structure

### Documentation for this feature

```text
specs/numbered/0/0/1/2/3/4/3/2/4867-refresh-dependencies/
├── spec.md
├── plan.md
├── tasks.md
└── design/
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    └── checklists/
        └── requirements.md
```

### Package files

```text
pyproject.toml
uv.lock
requirements.txt
requirements-dev.txt
mist-ops-platform/
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
ops-portal/
├── package.json
└── package-lock.json
.github/workflows/ci.yml
changelog.d/
```

**Structure Decision**: This change only updates package manifests, lock files, exports, one CI package install path, and verification records.

## Complexity Tracking

No constitution violation is expected.

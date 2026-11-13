# Implementation Plan: Locked Dependency Exports

**Branch**: `3999-locked-dependency-exports` | **Date**: 2026-11-12 | **Spec**: [spec.md](./spec.md)

**Input**: Numeric specification under the managed eight-level base-5 route.

## Summary

Update the locked runtime packages and regenerate both requirements exports from `uv.lock`. Keep each version within `pyproject.toml` limits and preserve platform markers.

## Technical Context

**Language/Version**: Python 3.15.2  
**Primary Dependencies**: UV 0.13.7 and the locked Python packages  
**Storage**: `uv.lock` and the two pip requirements exports  
**Testing**: Pytest dependency guards and `pip-audit`  
**Target Platform**: Windows, macOS, Linux, and the Podman container  
**Project Type**: Python command-line application  
**Performance Goals**: No runtime performance change  
**Constraints**: Keep package versions within `pyproject.toml` limits and preserve platform markers  
**Scale/Scope**: Update the lock and both generated requirements files

## Constitution Check

- The feature uses the required numeric route under `specs/numbered/`.
- The feature adds no source module, function, class, API, or product data.
- The change does not add a direct child outside a managed process route.
- The commit subject and pull request title will use an accepted Conventional Commit form.
- The feature uses no Mist Cloud API and changes no destructive operation.
- The runtime and development exports must both match the lock.
- Gunicorn remains below version 27 because the project declares that limit.
- The user authorized deployment after required checks pass. The production target and access method remain unspecified. Confirm them before deployment.

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/2/3/1/2/0/4785-locked-dependency-exports/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    checklists/requirements.md
    data-model.md
    quickstart.md
    research.md
```

### Source Files

```text
pyproject.toml
uv.lock
requirements.txt
requirements-dev.txt
tests/guardrails/test_dependency_export.py
tests/guardrails/test_dependency_lock_file.py
tests/guardrails/test_dependency_declaration_parity.py
```

**Structure Decision**: Update the tracked lock and its two generated exports. Keep project version limits unchanged. Validate with the existing dependency guards.

## Phase 0: Research

See [research.md](./design/research.md) for the locked export decisions and rejected alternatives.

## Phase 1: Design

See [data-model.md](./design/data-model.md) for the lock and export relationship. See [quickstart.md](./design/quickstart.md) for validation commands.

## Complexity Tracking

No source structure changes. No constitution exception is required.

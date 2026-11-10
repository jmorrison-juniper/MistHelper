# Implementation Plan: Python 3.15 Baseline

**Branch**: `3999-python-315-baseline` | **Date**: 2026-11-10 | **Spec**: [spec.md](./spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/2/2/4/1/4/4734-python-315-baseline/spec.md`.

## Summary

Set Python 3.15 as the minimum for both Python projects. Align package metadata, development tools, setup instructions, CI, release builds, and container images. Create a fresh local environment with stable Python 3.15.2 and verify that MistHelper starts.

## Technical Context

**Language/Version**: Python 3.15 or newer

**Primary Dependencies**: Existing MistHelper and Mist Ops Platform dependencies

**Storage**: No data or schema changes

**Testing**: pytest, UV, configured CI quality gates, and container build checks

**Target Platform**: Windows 11, macOS, Linux, and Podman containers

**Project Type**: Python command-line tool and separately configured service package

**Performance Goals**: No performance change
**Constraints**: Preserve dependency markers and open pull request ownership. Remove only the root checkout `.venv`. Keep Python 3.15 as the minimum across both packages.
**Scale/Scope**: Two package roots, setup and support documentation, CI and release workflows, container images, and related guards

## Constitution Check

- **Structure**: Pass. The feature adds one managed numeric specification. It adds no product package or module.
- **Support policy**: Pass. The Python baseline changes to 3.15 in both package roots.
- **Environment safety**: Pass. Remove only the root checkout `.venv`. Preserve environments in other worktrees.
- **Dependency safety**: Open pull request ownership was rechecked. Pull request #4322 owns `documentation/development-setup.md`, #4358 owns `pyproject.toml`, #4617 and #4208 own `.github/workflows/ci.yml`, and #4668 owns `.github/workflows/container-build.yml` and `.github/workflows/release.yml`. Pull request #4676 merged and #4678 closed, so rebase onto current `main` before editing the dependency exports. Recheck ownership before each shared-file edit.
- **Export integrity**: Pass. Generate pip exports from the resolved lock and preserve platform markers. Retain the staged dependency intent from issue #4727.
- **API and data safety**: Pass. The change adds no Mist API calls, data writes, schema changes, or destructive product operation.
- **Required documentation**: Pass. Update support and setup references. Add a release-note fragment for issue #4734.
- **Merge safety**: Pass. Use a pull request and required checks. Do not bypass branch protection.

## Phase 0: Research

See [research.md](./design/research.md). It verifies the current stable Python release, the container image tag, and the worktree bootstrap behavior.

## Phase 1: Design

See [quickstart.md](./design/quickstart.md) for environment creation and validation.

No data model is required because the feature changes no stored data. No separate interface contract is required because it changes no CLI argument, API, or service endpoint. Package metadata remains the compatibility contract.

## Project Structure

```text
pyproject.toml
requirements.txt
requirements-dev.txt
uv.lock
scripts/bootstrap_worktree.py
scripts/bootstrap_worktree.ps1
.github/copilot-instructions.md
.github/workflows/ci.yml
.github/workflows/container-build.yml
.github/workflows/pull-request-title.yml
.github/workflows/release.yml
documentation/development-setup.md
documentation/release-notes.md
Containerfile
Dockerfile
mist-ops-platform/pyproject.toml
mist-ops-platform/deploy/Containerfile.api
mist-ops-platform/deploy/Containerfile.worker
mist-ops-platform/docs/operations.md
tests/guardrails/test_pr_title_workflow.py
changelog.d/issue-4734-python-315.md
```

Update only files with an active Python support declaration or a test that records one. Keep historical feature specifications unchanged.

## Validation Strategy

1. Install stable Python 3.15.2 with UV and remove the root checkout's existing `.venv`.
2. Create a new environment through the documented bootstrap path.
3. Check package metadata, dependency resolution, and pip exports on Python 3.15.
4. Run the startup command and focused bootstrap, title workflow, and container tests.
5. Run both projects' required tests and the local gates that apply to changed files.
6. Confirm all active support declarations use Python 3.15 or newer.
7. Open a pull request with the repository template and merge only after required checks pass.

## Risks and Dependencies

- Python 3.15.2 is available through UV 0.13.7, and the official `python:3.15-slim` tag exists.
- Pull request ownership may change. Recheck #4322, #4358, #4617, #4208, and #4668 before editing their files.
- The main checkout contains staged dependency changes from issue #4727. Preserve that file and integrate its intent through a valid lock and export.
- Other worktrees contain virtual environments. Preserve them because separate tasks may use them.

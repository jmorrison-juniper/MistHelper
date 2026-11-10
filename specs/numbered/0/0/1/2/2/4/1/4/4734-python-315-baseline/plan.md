# Implementation Plan: Python 3.15 Baseline

**Branch**: `4734-python-315-baseline` | **Date**: 2026-11-10 | **Spec**: [spec.md](./spec.md)

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
**Constraints**: Preserve dependency markers and open pull request ownership. Remove pre-existing registered worktree `.venv` directories only after an active-process check. Keep Python 3.15 as the minimum across both packages. Deploy only after explicit approval.
**Scale/Scope**: Two package roots, setup and support documentation, CI and release workflows, container images, and related guards

## Constitution Check

- **Structure**: Pass. The feature adds one managed numeric specification. It adds no product package or module.
- **Support policy**: Pass. The Python baseline changes to 3.15 in both package roots.
- **Environment safety**: Pass. Remove pre-existing registered worktree `.venv` directories only after confirming that no process uses them. Preserve environments outside registered MistHelper worktrees.
- **Dependency safety**: Open pull request ownership was rechecked. Pull request #4322 owns `documentation/development-setup.md`, #4358 owns `pyproject.toml`, #4617 and #4208 own `.github/workflows/ci.yml`, and #4668 owns `.github/workflows/container-build.yml` and `.github/workflows/release.yml`. Pull request #4676 merged and #4678 closed, so rebase onto current `main` before editing the dependency exports. Recheck ownership before each shared-file edit.
- **Export integrity**: Pass. Resolve `importlib-metadata` 10.2.0, `openai` 3.49.0, and `pypdfium2` 5.15.2 from issue #4727. Generate both exports from the lock and preserve all 11 runtime platform markers.
- **API and data safety**: Pass. The change adds no Mist API calls, data writes, schema changes, or destructive product operation.
- **Required documentation**: Pass. Update support and setup references. Add a release-note fragment for issue #4734.
- **Merge safety**: Pass. Use a pull request and required checks. Do not bypass branch protection.
- **Deployment pipeline**: Pending. After merge, verify the image revision and health checks. Deploy only after explicit approval.

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

1. List `.venv` directories in registered worktrees and remove each only after confirming that no process uses it.
2. Create a new environment through the documented bootstrap path.
3. Check package metadata, dependency resolution, and pip exports on Python 3.15.
4. Run the startup command and focused bootstrap, title workflow, and container tests.
5. Run both projects' required tests and the local gates that apply to changed files.
6. Confirm all active support declarations use Python 3.15 or newer.
7. Build the explicit feature manifest and stage only its files.
8. Commit the feature with an accepted Conventional Commit subject.
9. Rebase onto `origin/main` and rerun affected local gates.
10. Push the branch and open a pull request with the issue closure, file summary, gate results, and deployment notes.
11. Wait for all required checks, then squash-merge the approved pull request.
12. Wait for the main image build and confirm its revision matches the merge commit.
13. Request explicit approval before production deployment.
14. After approval, deploy the image and verify container and portal health.

## Risks and Dependencies

- Python 3.15.2 is available through UV 0.13.7, and the official `python:3.15-slim` tag exists.
- Pull request ownership may change. Recheck #4322, #4358, #4617, #4208, and #4668 before editing their files.
- Issue #4727 has an uncommitted export that removes 11 markers and differs from the lock. Do not copy it. Regenerate both exports from the Python 3.15 lock.
- Registered worktree `.venv` directories require an active-process check before removal. Preserve environments outside registered MistHelper worktrees.
- Production deployment remains blocked until an operator gives explicit approval.

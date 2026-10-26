# Implementation Plan: Bootstrap pip security

**Branch**: `jmorrison-juniper-bootstrap-pip-security` | **Date**: 2026-10-26 | **Spec**: [Specification](spec.md)

## Summary

Require `pip>=26.2.2` beside each existing requirement-file argument.
Both selected installers enforce the minimum in the existing package transaction.
Do not upgrade all product dependencies or add another source-policy path.

## Technical Context

**Language/Version**: Python 3.13 or newer.
**Primary Dependencies**: Standard library, uv when available, environment-local pip otherwise.
**Storage**: Existing worktree environment.
**Testing**: pytest command contracts and actual bootstrap audits.
**Target Platform**: Windows, macOS, and Linux.
**Project Type**: Internal development script.
**Performance Goals**: Preserve the existing subprocess count and bounded transport settings.
**Constraints**: Preserve source isolation and failure propagation. Change no runtime requirement declaration.
**Scale/Scope**: One installation method and its existing command-contract tests.

## Constitution Check

- The repair changes an existing source child and an existing test child.
- New process files use the bounded numeric route and one unique changelog fragment.
- Existing debt: the bootstrap module, test module, and changelog directory exceed the structural limits.
- Incremental remediation: group future bootstrap tests within the existing nested classes. Do not add a top-level declaration.
- The repair adds no production operation, network service, persistent data model, or Mist request.
- Use the existing error logging and subprocess failure handling.
- Keep the Conventional Commit subject and preserve all existing module-level names.
- The app owns the existing branch. Do not execute the branch-creation script.
- PowerShell is absent. Apply its documented eight-digit base-5 route algorithm without changing the shared feature selector.
- Optional commit hooks before and after planning remain deferred until the coherent repair is ready.

The design passes these checks before and after planning.

## Project Structure

- `scripts/bootstrap_worktree.py`: Add the pip minimum to `InstallationPolicy.install`.
- `tests/unit/bootstrap/test_pip_index_probe.py`: Extend the real-dispatch command expectation.
- `tests/contract/packaging/test_bootstrap_compose_provider.py`: Preserve the Windows command contract with safe pip.
- `changelog.d/issue-4255-bootstrap-pip-security.md`: Describe the installer security repair.
- This feature directory: Keep the specification, plan, tasks, analysis, and supporting design records.

## Complexity Tracking

The change adds no branch, method, class, process, or source-policy path.
Existing structural debt remains unchanged.

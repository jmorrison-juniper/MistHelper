# Implementation Plan: Runtime Dependency Exports

**Branch**: `chore/4727-runtime-dependency-exports` | **Date**: 2026-11-10 | **Spec**: [spec.md](./spec.md)

## Summary

Rebase the branch onto current `main`, review a new dependency preview, then update the lock with the approved compatible releases. Regenerate both pip exports from the lock. Preserve all 11 runtime platform markers.

The issue requests `importlib-metadata` 10.2.0, `openai` 3.48.0, and `pypdfium2` 5.15.2. A prior preview predates current `main` and is not authoritative. Review the refreshed preview before changing the lock. Keep existing package constraints in force. Do not edit `pyproject.toml` while open PR #4358 owns it.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: UV 0.13.7, the existing lock, and the two generated pip exports.

**Storage**: Dependency records in `uv.lock`, `requirements.txt`, and `requirements-dev.txt`.

**Testing**: Existing pytest guardrails, `uv lock --check`, and separate `pip-audit` runs for both exports.

**Target Platform**: Windows, macOS, and Linux with Python 3.13 or newer.

**Project Type**: Python command-line application.

**Performance Goals**: Not applicable. This update changes no runtime behavior.

**Constraints**: Preserve all 11 runtime markers. Keep existing package constraints. Do not edit files owned by another open pull request. Report audit coverage gaps.

**Scale/Scope**: Update only the package changes approved in the refreshed preview. Regenerate two exports and add one release note.

## Constitution Check

*Gate before research and after design: PASS.*

- The change adds no Mist Cloud requests, application code, or runtime data.
- The lock and both generated exports remain the dependency source and supported installation outputs.
- The update preserves 11 runtime markers and existing package constraints.
- The change adds one unique issue release note and does not edit `CHANGELOG.md`.
- The existing parity, lock, and export guards prove the requested invariants.
- Audit both exports. Report findings for auditable packages and name each source that the audit cannot inspect.
- Open PR #4358 owns `pyproject.toml`. This plan does not edit that file.
- Follow the repository release pipeline. Use a Conventional Commit subject and the repository pull request template.

## Project Structure

### Feature Documentation

```text
specs/numbered/0/0/1/2/2/4/0/2/4727-runtime-dependency-exports/
  spec.md
  plan.md
  tasks.md
  design/
    checklists/requirements.md
    contracts/dependency-exports.md
    data-model.md
    quickstart.md
    research.md
```

### Dependency Files and Existing Checks

```text
uv.lock
requirements.txt
requirements-dev.txt
changelog.d/issue-4727-runtime-dependency-exports.md
tests/guardrails/test_dependency_declaration_parity.py
tests/guardrails/test_dependency_lock_file.py
tests/guardrails/test_dependency_export.py
```

The three guardrail modules already test the dependency declarations, lock, and generated exports. Run them without changing their source.

# Implementation Plan: Reject Conflicting Mist Token Values

**Branch**: `3996-mist-token-conflict` | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/0/4/2/4/2/1/2861-token-conflict/spec.md`.

## Summary

Reject conflicting Mist token variables before authentication. Keep single-variable and equal-value migration behavior. Normalize token lists before selecting a value so delimiter-only canonical input cannot hide a usable legacy value.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: Python standard library and existing project helpers
**Storage**: N/A
**Testing**: pytest, Ruff, Black, mypy, Bandit, and repository quality gates
**Target Platform**: Windows 11, macOS, and Linux
**Project Type**: Python CLI application
**Performance Goals**: Local validation must not add a network request.
**Constraints**: Never log token values. Refuse conflicts before session or organization lookup.
**Scale/Scope**: One entry-point credential path, its unit tests, and one issue release note.

## Constitution Check

- Keep the edit inside the approved MistHelper.py slice.
- Preserve module-level names in `MistHelper.py`.
- Use local environment values only. Make no Mist Cloud request.
- Test conflicting values, equal values, either variable alone, empty normalized values, login mode, and pre-session refusal.
- Keep token values out of error messages and logs.
- Keep issue #2861 open. Do not push or open a pull request before owner approval.

**Gate result**: Pass. The implementation adds no external interface, storage, or network behavior.

## Research

See [design/research.md](design/research.md). The approved policy and the existing token parser provide the needed decisions.

## Design

- **Data model**: See [design/data-model.md](design/data-model.md).
- **Contracts**: No public API contract changes. The internal refusal contract appears in the feature requirements.
- **Validation guide**: See [design/quickstart.md](design/quickstart.md).

## Project Structure

```text
MistHelper.py
tests/unit/test_credential_preflight.py
changelog.d/issue-2861-mist-token-conflict.md
specs/numbered/0/0/0/4/2/4/2/1/2861-token-conflict/
  spec.md
  plan.md
  tasks.md
  design/
    data-model.md
    quickstart.md
    research.md
    checklists/requirements.md
  checklists/security.md
```

**Structure Decision**: Keep runtime behavior in the established entry point and tests in its existing unit test module. Store feature records under the managed numeric route.

## Complexity Tracking

No constitution exception is required.

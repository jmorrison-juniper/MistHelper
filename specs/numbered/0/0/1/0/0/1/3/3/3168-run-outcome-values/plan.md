# Implementation Plan: Explicit Portal Run Outcomes

**Branch**: `jmorrison-juniper-resolve-3168-outcome-state` | **Date**: 2026-10-20 | **Spec**: [spec.md](spec.md)

**Input**: Issue #3168 and its acceptance criteria 1 through 4.

## Summary

Read a handler's existing `OperationOutcome` value before the portal classifies its logs. Keep log-marker classification for handlers without that value and count each legacy empty-result fallback.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Primary Dependencies**: Existing `OperationOutcome` model and Flask portal services

**Storage**: In-memory operation run records and application logs

**Testing**: pytest unit tests for the portal executor

**Target Platform**: Windows 11, macOS, and Linux

**Project Type**: Python application with a web portal

**Performance Goals**: Add no external request. Keep fallback telemetry to one cumulative counter per executor.

**Constraints**: Preserve marker behavior for handlers without a typed outcome. Do not change `.specify/feature.json`. Stop after one local commit until the user approves publication.

## Constitution Check

- The feature uses the managed eight-segment base-five route for issue 3168.
- The feature root has four children: `spec.md`, `plan.md`, `tasks.md`, and `design/`.
- The `design/` directory has five children: `checklists/`, `contracts/`, `data-model.md`, `quickstart.md`, and `research.md`.
- The source change adds no module, class, or package. It changes existing methods in `OperationExecutor`.
- The executor class and service module already exceed some structural guidance. This change will not expand the class hierarchy. Track that existing debt for a separate refactor.
- The implementation adds no direct Mist Cloud call and changes no destructive behavior.
- The active `.specify/feature.json` belongs to another feature and remains unchanged.
- The worktree already provides an isolated branch based on `main`. The branch hook would create a second branch and is not run.
- The user requires review before publication. Do not rebase, push, open a pull request, merge, or deploy in this task.

## Design Decisions

- Reuse the existing immutable `OperationOutcome` contract.
- Keep a typed outcome on the run record only for its classification lifetime.
- Use a lock-protected per-executor counter for legacy empty-result marker matches.
- Make the existing alert digest handler the migrated example because it already returns `no_output`.
- Add a source-wording contract test for current legacy empty-result markers because direct inspection found no existing coverage.
- Preserve logs, discovered output names, missing-input classification, handled-error classification, and the legacy marker lists for handlers without a typed result.

## Project Structure

```text
web_portal/services/operation.py
tests/unit/web_portal/test_portal_silent_completion.py
tests/e2e/web_portal/test_issue_4037_menu_93_output.py
changelog.d/issue-3168-explicit-handler-outcomes.md
specs/numbered/0/0/1/0/0/1/3/3/3168-run-outcome-values/
  spec.md
  plan.md
  tasks.md
  design/
    checklists/requirements.md
    contracts/handler-outcome.md
    data-model.md
    quickstart.md
    research.md
```

## Complexity Tracking

| Violation | Why Needed | Separate Remediation |
|---|---|---|
| Existing `OperationExecutor` class and service module exceed structural guidance. | The fix belongs in the existing run lifecycle and must preserve compatibility for unmigrated handlers. | Track a separate decomposition of portal result classification. |

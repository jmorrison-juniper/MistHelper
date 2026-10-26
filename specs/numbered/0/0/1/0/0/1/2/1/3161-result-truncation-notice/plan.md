# Implementation Plan: Result clipping notice

**Branch**: `jmorrison-juniper-portal-result-truncation-notice` | **Date**: 2026-10-26 | **Spec**: [spec.md](spec.md)

## Summary

Measure current result cells in Chromium before changing production code.
Extend the existing notice with actual clipping detection and complete-value controls.
Preserve the existing sort warning and result operations.

## Technical Context

**Language/Version**: Existing browser JavaScript and Python 3.13 tests.

**Primary Dependencies**: Existing Flask, Playwright, pytest, and Bootstrap.

**Storage**: Temporary CSV files only. No production store or Mist request.

**Testing**: Browser geometry, native preview responses, Node lifecycle checks, and current related regressions.

**Target Platform**: Existing desktop browsers on Windows, macOS, and Linux.

**Project Type**: Web application.

**Performance Goals**: One clipping scan per animation frame, limited to the current page.

**Constraints**: One production file. No template, CSS, dependency, shared fixture, baseline, or policy change.

**Scale/Scope**: Thirty controlled records across pages of 25 and five.

## Constitution Check

- Preserve the app-managed branch and shared `.specify` state.
- Use the eight-segment base-5 route for issue 3161.
- PowerShell is absent. Calculate the documented route and check every parent before creating the feature directory.
- Keep the feature root and each new supporting directory within five children.
- Add only the unique release fragment to the existing release directory.
- Existing release-directory and JavaScript module structure debt remain unchanged.
- Separate remediation: divide the existing result module only under a future ownership grant.
- Use existing result behavior instead of a new adapter.
- No Mist transport, device changes, production data, deployment, or container change applies.
- Optional commit hooks remain deferred until the feature passes local checks.
- Use a Conventional Commit and complete the existing pull request template.
- The user prohibits browser screenshots, traces, and video. Keep those outputs disabled.

## Project Structure

### Documentation (this feature)

The managed feature root contains `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`.
The design directory contains research, data model, quickstart, contracts, and the requirements checklist.

### Source Code (repository root)

- `web_portal/static/js/operation_results.js`
- `tests/e2e/web_portal/result_truncation_notice/`
- `tests/unit/web_portal/result_truncation_notice/`
- `changelog.d/issue-3161-result-truncation-notice.md`

**Structure Decision**: Keep new tests within the released namespaces. Leave existing tests and fixtures unchanged.
The user approved the nested browser-test namespace after the current shard guard rejected the earlier top-level namespace.

## Design

Use a private notice controller within the existing module.
Measure only data cells with positive visible width.
Use a cancellable animation frame and one resize observer while results are active.
Disconnect the observer and cancel scheduled work on load, error, empty run, or reset.
Reject stale fetch responses with a request generation counter.
Cancel pending search work when changing or clearing a run.
Compose clipping and sort messages independently.
Give the existing notice a status role and stable complete-value controls.
Open the first clipped row through the existing detail renderer.
Focus Output Files through its existing destination.

## Complexity Tracking

The existing module exceeds five declarations and several existing functions exceed 25 lines.
This bounded repair keeps its public interface unchanged and does not restructure unrelated code.

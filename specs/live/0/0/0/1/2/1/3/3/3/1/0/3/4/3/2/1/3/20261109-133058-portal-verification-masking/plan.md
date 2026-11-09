# Implementation Plan: Portal verification masking

**Branch**: `jmorrison-juniper-portal-verification-masking` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

## Summary

Add `input_type: password` to the verification parameter. Let the existing text renderer accept only that display override.
Keep `param_type: text` and the existing positional submission contract.

## Technical Context

**Language/Version**: Python 3.13 or newer and browser JavaScript.
**Primary Dependencies**: Existing Flask, pytest, and Playwright packages.
**Storage**: No new storage.
**Testing**: Dedicated unit tests and an offline browser journey using Flask request dispatch.
**Target Platform**: Existing supported portal browsers.
**Project Type**: Web portal.
**Performance Goals**: No new request or background work.
**Constraints**: Local only. No credentials, Mist calls, Git configuration changes, or publication.
**Scale/Scope**: One metadata entry and one input renderer.

## Constitution Check

- The app already created and renamed the worktree branch. Do not execute a second branch-creation command.
- PowerShell is absent. Calculate the same seventeen-digit timestamp route as `spec-route.ps1` and check each existing parent.
- Keep the feature selector command-scoped. Do not change `.specify/feature.json`.
- Decline optional intermediate commit hooks. Commit only complete local work.
- New process records use the managed route. Each new record directory has five children or fewer.
- Established portal test directories exceed five children. Add dedicated nested test directories instead of changing another owner's tests.
- Separate remediation: a future owner can group existing portal tests. This mitigation must not restructure those tests.
- Existing production modules exceed current structure limits. Make no new declaration and do not increase that declaration count.
- Separate remediation: a future owner can divide the parameter registry and renderer by domain.
- No Mist transport changes apply. Tests dispatch portal requests locally and replace the operation executor.
- Use a unique dated changelog fragment because this slice has no publishable issue or pull request.
- The publication hold overrides deployment and public issue requirements.
- Recheck after design: the scope remains limited to display masking and unchanged submission.

## Project Structure

```text
web_portal/services/operation.py
web_portal/static/js/operations.js
tests/unit/web_portal/verification_masking/test_controls.py
tests/e2e/web_portal/verification_masking/test_submission.py
changelog.d/2026-11-09-portal-verification-masking.md
```

The design records remain under this feature's `design/` directory.

## Complexity Tracking

The display override accepts only `password`. Every other metadata value retains `text`.
No new helper, input API, parameter type, or dependency is necessary.

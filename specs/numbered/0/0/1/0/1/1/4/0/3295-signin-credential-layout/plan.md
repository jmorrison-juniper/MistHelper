# Implementation Plan: Sign-in Credential Layout

**Branch**: `jmorrison-juniper-3295-upgrade-portal-sign-in-credential-l` | **Date**: 2026-10-26 | **Spec**: [spec.md](spec.md)

## Summary

Issue #3295 needs a separate token field group, mode-aware visibility, and matching warning-prefix weight. Keep all sign-in decisions unchanged.

## Technical Context

**Language/Version**: Python 3.13+, HTML, CSS, and JavaScript.

**Primary Dependencies**: Existing Flask portal and Playwright browser test setup.

**Storage**: None. The change adds no stored data.

**Testing**: Pytest with the existing upgrade-portal browser fixture.

**Target Platform**: Supported desktop browsers.

**Project Type**: Web application.

**Performance Goals**: No change to request count or response time.

**Constraints**: Preserve server-side authentication, credential validation, and routes. Tests must not submit credentials or contact Mist.

**Scale/Scope**: One sign-in form and its warning prefix.

## Constitution Check

- The feature uses the managed numeric route `specs/numbered/0/0/1/0/1/1/4/0/3295-signin-credential-layout/`.
- The new feature root has four planned children: `spec.md`, `plan.md`, `tasks.md`, and `design/`.
- The `specs/` root has legacy direct-child debt. This change adds no direct feature child and does not change the baseline.
- The required issue changelog fragment adds one unique record under the established `changelog.d/` process folder.
- The existing `initBrowserTokenSignIn` function exceeds the repository function-length limit. This issue adds only mode-state synchronization. A separate follow-up can reduce that existing function without changing sign-in behavior here.
- No Mist Cloud call, data write, external interface, or destructive action is added.
- The plan keeps existing sign-in routes and preserves current validation.
- The branch name and any pull request title use an accepted Conventional Commit form.

**Gate result**: Pass. No new design decision or transport contract is required.

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/0/1/1/4/0/3295-signin-credential-layout/
  spec.md
  plan.md
  tasks.md
  design/
    checklists/requirements.md
    contracts/presentation.md
    data-model.md
    quickstart.md
    research.md
```

### Source and Tests

```text
src/interfaces/portals/upgrade_portal/app/assets/
  templates/auth/signin.html
  static/css/portal.css
  static/js/portal.js

tests/e2e/upgrade_portal/test_signin.py
changelog.d/issue-3295-signin-credential-layout.md
```

**Structure Decision**: Update the existing sign-in template, stylesheet, browser script, and browser test. Add no new application module or service.

## Complexity Tracking

| Existing condition | Scope decision | Separate remediation |
| --- | --- | --- |
| `initBrowserTokenSignIn` already exceeds the 25-line function limit. | Add only the visibility and disabled-state updates needed by this issue. | Refactor that existing function in a separate, behavior-preserving change. |
| `specs/` has legacy direct-child debt. | Add this record only under its managed numeric route. | Migrate legacy records through the existing baseline process. |

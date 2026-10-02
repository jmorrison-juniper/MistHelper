# Implementation Plan: Sign-in credential layout

**Branch**: `jmorrison-juniper-sign-in-credential-layout` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)
**Input**: Issue #3295 and the feature specification.

## Summary

Move the token controls outside the mode fieldset.
Extend the existing mode callback to hide and disable only the inactive token.
Share the existing bold signal-word rule with sign-in danger alerts.
Keep server behavior and credential transport unchanged.

## Technical Context

**Language/Version**: Existing Jinja HTML, CSS, plain JavaScript, and Python 3.13.13 for local checks.
**Primary Dependencies**: Existing Flask, Flask-WTF, vendored Bootstrap, pytest, Playwright, Node, and pinned development tools.
**Storage**: No schema or storage change. Synthetic values remain temporary browser values.

**Testing**: Dedicated contract, actual-script unit, and Chromium tests with existing process-owned fixtures.
**Target Platform**: Native loopback fixtures in this macOS worktree. No production container or store.
**Project Type**: A server-rendered interface with an existing browser controller.

**Performance Goals**: Zero mode-change requests, zero added listeners, and exactly one nonempty token request after ten cycles.
**Constraints**: Three source surfaces, exact owned test paths, preserved auth decisions, and a local commit only.
**Scale/Scope**: Four native geometry cells across two themes and two viewports. Eight genuine main-asset cells are supplemental.

## Constitution Check

The source edits are surgical changes to existing children.
The existing initializer and source directories already exceed the general structural limits.
Do not restructure them or add a production class, wrapper, alias, or compatibility path.
New test support uses semantic classes and bounded methods.
The explicitly reserved feature artifacts follow the current SpecKit templates.

Use safe action logs in test support. Do not log form values.
Pure DOM visibility changes add no credential logging.
Keep all server logging, startup guards, transport helpers, and session decisions unchanged.
The user restricts deployment and publication until the later parent grant.
Do not treat that restriction as a completed deployment or governance change.

## Project Structure

### Documentation (this feature)

```text
specs/3295-signin-credential-layout/
  spec.md
  plan.md
  tasks.md
  research.md
  data-model.md
  quickstart.md
  contracts/presentation.md
  checklists/requirements.md
```

### Source Code (repository root)

```text
src/upgrade_portal/app/assets/templates/auth/signin.html
src/upgrade_portal/app/assets/static/css/portal.css
src/upgrade_portal/app/assets/static/js/portal.js
tests/contract/upgrade_portal/test_issue_3295_signin_layout.py
tests/unit/upgrade_portal/test_issue_3295_signin_modes.py
tests/e2e/upgrade_portal/test_issue_3295_signin_layout.py
tests/e2e/upgrade_portal/issue_3295_signin_support.py
changelog.d/issue-3295-signin-credential-layout.md
```

**Structure Decision**: Edit only the reserved source regions. Keep existing tests and shared fixtures unchanged.

## Design

Use a hidden `div.signin-token-group` after the complete credential fieldset.
Name it through the token label. Keep the label, masked input, and note as direct children.
Render the input disabled. Use no `value` attribute or inline script.

Locate the group inside `initBrowserTokenSignIn`.
The existing callback restores two required-field baselines, then synchronizes group visibility and token eligibility.
Keep the submit handler, clear-before-fetch assignment, refusal renderer, and listener registrations unchanged.

Use `.flash-item::before, .flash-danger.alert::before` for the existing weight and whitespace declarations.
The compound selector retains the existing standalone signal-word rule and its unchanged source tests.
Do not add a prefix to message text.

Run real red measurements before source edits.
Use the actual two native themes for acceptance.
The measured dependency table ends at `399.71875` pixels on a `360`-pixel viewport.
Require no new form or token-group overflow. Preserve that unrelated table.

## Workflow Limitations

The mandatory PowerShell hook returned exit 1 because `pwsh` is absent.
The custom specification, plan, and task agents used the authorized feature-only equivalent.
No shared state, optional commit hook, companion state, or agent context changed.
The standard workflow did not complete.

The Python 3.13 bootstrap failed in `ensurepip` with `SIGABRT`.
UV restored only this worktree's ignored `.venv`, with seed packages, copies, and system certificates.
No dependency manifest changed.

## Complexity Tracking

| Existing constraint | Bounded decision | Separate remediation |
| --- | --- | --- |
| Large initializer and shared source files | Change one group lookup, guard, and five-operation mode callback. | Restructure the controller through a separate owned feature. |
| Existing test directories exceed five children | Add only the four explicitly reserved issue files. | Reorganize test packages separately with their owners. |
| Template workflow normally changes shared state | Use the authorized feature-only equivalent. | Restore compatible tooling separately. |

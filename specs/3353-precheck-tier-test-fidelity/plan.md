# Implementation Plan: Pre-check tier test fidelity

**Branch**: `jmorrison-juniper-precheck-tier-test-fidelity` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

## Summary

Add the production tier API to the process-owned browser store.
Keep the existing capture selection and reuse the production tier conversion.
Add exact pair assertions and visible tier-cell assertions.
Change no production behavior.

## Technical Context

**Language/Version**: Python 3.13.13.

**Primary Dependencies**: The current pinned pytest, coverage, Flask, Playwright, and development tools.

**Storage**: The existing process-owned `PortalRecordStore`.

**Testing**: Focused unit and contract tests, followed by isolated Chromium journeys.

**Target Platform**: The local macOS worktree and the existing Linux CI configuration.

**Project Type**: A test-only repair of an existing web application stand-in.

**Performance Goals**: Select one capture for each pair read.

**Constraints**: Use no live cloud calls, production stores, containers, or production local ports.

**Scale/Scope**: Three existing Python test files, one release fragment, and three specifications in unique files.

## Constitution Check

- The new reader belongs to the existing semantic store class.

- Limit the method to five parameters, five logical blocks, and 25 lines.

- The existing store class and test modules exceed the hierarchy limits.
  A class split would exceed this issue's scope.
  A separate structural repair must address that existing debt.

- The existing browser journey exceeds the function-length limit.
  Add only direct tier-cell assertions. Preserve its current operation and cleanup.

- Reuse the existing tier helper instead of duplicating its policy.

- Preserve the current standalone origin, time, and verification rules.

- Use ASCII action logs. Comment only the non-obvious selection and conversion decisions.

- Obey the parent's sole publication grant on main `5d38898af5639e90715ec57eb8d48d2985e1acf8`.
- Preserve the approved `ModelVersionPicker` call from pull request #3633.
- Keep the same three run-owned capture exclusions without importing a second conftest instance.

## Project Structure

### Documentation

```text
specs/3353-precheck-tier-test-fidelity/
  spec.md
  plan.md
  tasks.md
```

### Test Code

```text
tests/support/upgrade_portal_e2e/records/portal.py
tests/unit/upgrade_portal/test_e2e_standin_precheck_adopter.py
tests/e2e/upgrade_portal/test_org_missing_precheck_journey.py
changelog.d/issue-3353-precheck-tier-test-fidelity.md
```

## Implementation and Evidence

1. Add the pair tests and rendered-cell assertions before the reader.
2. Record the unit failures and the tier 3 browser-cell failure.
3. Add the pair reader to the stand-in store.
4. Run the focused tests and inspect changed-method coverage.
5. Run the adjacent capture, adoption, tier, and organization browser journeys.

6. Run the configured quality checks without changing any threshold.
7. Record unavailable dictionary or PowerShell capabilities explicitly.
8. Add the issue-owned release fragment and complete the task evidence.
9. Commit the exact reserved file set and report its clean SHA to the parent.

## Authorized Publication

The parent released position 14 on 2026-10-02.
The granted base is `5d38898af5639e90715ec57eb8d48d2985e1acf8`.
The temporary browser-file handoff is complete. The seven issue-owned paths remain the full change scope.

Repeat the red pair and rendered-cell failures on an owned export of that exact base.
Keep its production source, stand-in selection, model controls, and conftest unchanged.
Run the required green cases under full collection and the CI package name.
Remove the temporary source export before the complete quality scan.

Preserve the complete pull request template and record exact local results.
Keep auto-merge disabled.
Require all fresh protected statuses on the exact head and granted base.
Use the protected squash merge without an administrator bypass or branch-deletion argument.

After the merge, select and test the exact resulting main revision locally.
Record its full SHA, tree, local results, and cleanup in a persistent pull request receipt.
Only the parent can release the next issue.

## Complexity Tracking

| Existing violation | Scope decision | Separate remediation |
| - | - | - |
| The store class exceeds five methods. | Add the required pair API without moving unrelated behavior. | Split record responsibilities in a dedicated structural issue. |
| The existing test modules exceed five children. | Extend the existing issue-related tests only. | Organize the tests during a dedicated structural repair. |
| The browser journey exceeds 25 lines. | Add direct cell assertions without changing cleanup or shared helpers. | Extract journey phases in a separate test-maintenance issue. |

# Implementation Plan: Windows Audit Report Portability

**Branch**: `jmorrison-juniper-windows-audit-report-portability` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

**Input**: Issue #4771, routed to `specs/numbered/0/0/1/2/3/0/4/1/4771-windows-audit-report-portability/`.

## Summary

Make the restricted audit writer work on Windows without weakening owner-only permissions or link rejection. Stage both reports in private, exclusive files, then replace the report pair only after both writes succeed. Open each staged file with `WRITE_DAC` and `FILE_READ_ATTRIBUTES` through `FILE_FLAG_OPEN_REPARSE_POINT` before applying its protected owner-only access control list. Add a separate optional Windows workflow that runs the real helper and writer regressions only when a feature-branch push changes a listed test input.

## Technical Context

**Language/Version**: Python 3.15 or newer.

**Primary Dependencies**: Python standard library, pytest, and Windows system APIs accessed through `ctypes`.

**Storage**: Two local files in the ignored `test-artifacts/websocket-dialog-audit` directory.

**Testing**: Focused pytest tests in the existing dialog audit test module and workflow contract tests in the existing workflow guard module.

**Target Platform**: Windows 11, macOS, and Linux. Native API acceptance runs on `windows-latest`.

**Project Type**: Test support code.

**Performance Goals**: Write two small local reports without network access.

**Constraints**: Keep the exact approved directory, owner-only access, symlink and reparse-point rejection, safe handling of existing reports, and cleanup after failure. Add no dependency. Keep the new workflow read-only, optional, and limited to relevant test inputs. Do not edit `ci.yml`, branch protection, required status names, or other product source. Do not call Mist endpoints or use credentials, production data, or services.

**Scale/Scope**: One writer regression, one workflow contract, one optional workflow, one release fragment, and the routed Spec Kit record.

## Constitution Check

*Gate before research*: Pass.

- The change adds one feature record under the managed eight-level base-5 route. The PowerShell dry run accepted the route and reported the exact `spec.md` path.
- The change adds one uniquely named issue release fragment. This is a required record under the established `changelog.d/` process folder.
- Existing process-folder debt remains governed by `tests/guardrails/process_folder_baseline.json`. This change does not alter the baseline. A separate future task can reduce any recorded debt.
- Generated test reports remain in the ignored `test-artifacts/` directory. This change creates no product data.
- The new optional workflow runs only on relevant feature-branch pushes, has read-only repository access, and does not change required status names.
- No Mist Cloud API, menu operation, production source package, dependency, `ci.yml`, branch protection, or public symbol changes.
- Keep each new class and method within the repository limits. Refactor the existing long `AuditReportWriter.write` method into bounded methods. This plan records that existing method-length violation as a directly touched issue.
- Use a Conventional Commit subject and include the required Copilot co-author trailer.

## Phase 0: Research

See [research.md](design/research.md). It confirms exclusive staging and POSIX mode checks, Windows reparse-point attributes, native ACL checks, and a feature-push trigger for the new workflow. It selects standard-library file staging and native Windows security calls without a dependency change.

## Phase 1: Design

- [data-model.md](design/data-model.md) defines the report pair, staging files, and approved destination.
- [quickstart.md](design/quickstart.md) defines the focused regression and the native Windows workflow path.
- No external contract artifact is needed. The writer is private test support, not a public API.

### Post-Design Constitution Check

Pass. The design changes only focused test support, one separate optional workflow, and the feature records. Staging files stay in the approved directory, receive owner-only access, and are removed after errors. The workflow uses synthetic data and read-only access. The feature pointer remains unchanged.

## Project Structure

### Documentation

```text
.github/workflows/
  windows-audit-report.yml
tests/guardrails/
  test_ci_gate_triggers.py
tests/e2e/websockets_tab/dialog_audit/
  support/reporting.py
  test_inventory.py
specs/numbered/0/0/1/2/3/0/4/1/4771-windows-audit-report-portability/
  spec.md
  plan.md
  tasks.md
  design/
    data-model.md
    quickstart.md
    research.md
```

### Source Code

```text
tests/e2e/websockets_tab/dialog_audit/
  test_inventory.py
changelog.d/
  issue-4771-windows-audit-report-portability.md
```

**Structure Decision**: Keep the Windows access helper in the existing report support module. Add the native writer regression to the existing inventory test module, the workflow contract to the existing workflow guard module, and the native job in one new optional workflow. Add no package or test directory.

## Complexity Tracking

No new dependency or public abstraction is required. The Windows-specific helper is justified because Windows has no `O_NOFOLLOW` or `fchmod` path, and the replacement must retain both link protection and owner-only access. The workflow contract test protects the native runner, access boundary, and zero-skip result.

# Implementation Plan: Windows Audit Report Portability

**Branch**: `jmorrison-juniper-windows-audit-report-portability` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

**Input**: Issue #4771, routed to `specs/numbered/0/0/1/2/3/0/4/1/4771-windows-audit-report-portability/`.

## Summary

Make the restricted audit writer work on Windows without weakening owner-only permissions or link rejection. Stage both reports in private, exclusive files, then replace the report pair only after both writes succeed. Use Windows file attributes and native handles for reparse-point checks and a protected owner-only access control list. Keep POSIX mode checks, reject links before replacement, and use atomic replacement instead of opening existing report files.

## Technical Context

**Language/Version**: Python 3.15 or newer.

**Primary Dependencies**: Python standard library, pytest, and Windows system APIs accessed through `ctypes`.

**Storage**: Two local files in the ignored `test-artifacts/websocket-dialog-audit` directory.

**Testing**: Focused pytest tests in the existing dialog audit test module.

**Target Platform**: Windows 11, macOS, and Linux.

**Project Type**: Test support code.

**Performance Goals**: Write two small local reports without network access.

**Constraints**: Keep the exact approved directory, owner-only access, symlink and reparse-point rejection, safe handling of existing reports, and cleanup after failure. Add no dependency and do not run a Mist operation.

**Scale/Scope**: One writer, its focused tests, one release fragment, and the routed Spec Kit record.

## Constitution Check

*Gate before research*: Pass.

- The change adds one feature record under the managed eight-level base-5 route. The PowerShell dry run accepted the route and reported the exact `spec.md` path.
- The change adds one uniquely named issue release fragment. This is a required record under the established `changelog.d/` process folder.
- Existing process-folder debt remains governed by `tests/guardrails/process_folder_baseline.json`. This change does not alter the baseline. A separate future task can reduce any recorded debt.
- Generated test reports remain in the ignored `test-artifacts/` directory. This change creates no product data.
- No Mist Cloud API, menu operation, production source package, dependency, workflow, or public symbol changes.
- Keep each new class and method within the repository limits. Refactor the existing long `AuditReportWriter.write` method into bounded methods. This plan records that existing method-length violation as a directly touched issue.
- Use a Conventional Commit subject and include the required Copilot co-author trailer.

## Phase 0: Research

See [research.md](design/research.md). It confirms exclusive staging and POSIX mode checks, Windows reparse-point attributes, and the existing repository pattern for Windows ACL checks. It selects standard-library file staging and native Windows security calls without a dependency change.

## Phase 1: Design

- [data-model.md](design/data-model.md) defines the report pair, staging files, and approved destination.
- [quickstart.md](design/quickstart.md) defines the focused regression and platform checks.
- No external contract artifact is needed. The writer is private test support, not a public API.

### Post-Design Constitution Check

Pass. The design changes only the writer and its focused tests. Staging files stay in the approved directory, receive owner-only access, and are removed after errors. The test scope includes failure handling, path safety, and report contents. The feature pointer will be restored to its prior value before commit, so this change does not claim another feature's tracked selector.

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/2/3/0/4/1/4771-windows-audit-report-portability/
  spec.md
  plan.md
  tasks.md
  design/
    checklists/requirements.md
    data-model.md
    quickstart.md
    research.md
```

### Source Code

```text
tests/e2e/websockets_tab/dialog_audit/
  support/reporting.py
  test_inventory.py
changelog.d/
  issue-4771-windows-audit-report-portability.md
```

**Structure Decision**: Keep the Windows access helper in the existing report support module. Add the focused tests to the existing inventory test module. Add no new package or test directory.

## Complexity Tracking

No new dependency or public abstraction is required. The Windows-specific helper is justified because Windows has no `O_NOFOLLOW` or `fchmod` path, and the replacement must retain both link protection and owner-only access.

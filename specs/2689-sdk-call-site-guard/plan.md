# Implementation Plan: mistapi SDK call-site guard

**Branch**: `test/2689-sdk-call-site-guard` | **Date**: 2026-09-16 | **Spec**: `specs/2689-sdk-call-site-guard/spec.md`

**Input**: Feature specification from `specs/2689-sdk-call-site-guard/spec.md`

## Summary

Replace the skipped SDK compatibility test with an AST-based guard that resolves MistHelper `mistapi` calls against the installed SDK package. The guard fails on missing functions and on zero resolved call sites. It reports dynamic SDK references and blocks growth beyond a baseline of 10.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Standard library `ast`, `importlib.util`, `pathlib`, `dataclasses`, and pytest.

**Storage**: Not applicable.

**Testing**: pytest, ruff, black, mypy, radon, and `tools.guard_proof_audit`.

**Target Platform**: Windows local development and Linux CI.

**Project Type**: Python CLI and test suite.

**Performance Goals**: Complete the compatibility guard in less than 10 seconds on a local worktree.

**Constraints**: No live Mist API request. No source execution during scanning. Do not edit API documentation snapshots.

**Scale/Scope**: `MistHelper.py`, all Python files under `src/`, and the installed `mistapi` package.

## Constitution Check

- Five-Item Rule: The feature edits existing files only and adds one spec directory for issue #2689.
- Class-Based Architecture: New guard behavior lives in named classes.
- Safety-First: The guard reads files only and sends no live API request.
- Full Deployment Pipeline: Local gates, pull request checks, and merge verification are required.
- Observability: The guard logs each scan phase and prints measured call-site counts.
- Inline Comments: New executable lines carry inline comments that explain purpose.
- Action Logging: Meaningful scan actions log before and after execution.

## Project Structure

### Documentation (this feature)

```text
specs/2689-sdk-call-site-guard/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code (repository root)

```text
src/firmware/site_auto_upgrade.py

tests/integration/test_mistapi_sdk_compatibility.py

tests/unit/test_site_auto_upgrade.py

tools/guard_proof_audit.py

tests/guardrails/test_guard_proof_audit.py

changelog.d/issue-2689-sdk-guard.md
```

**Structure Decision**: Keep the guard in the existing integration test file because it is the named SDK compatibility test. The guard found one real SDK typo in `src/firmware/site_auto_upgrade.py`, so this plan includes that direct repair and its existing unit mock names.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Existing `tests/integration` directory has many children | This change repairs the named existing guard file | Moving the guard would leave the dead named file in place |
| Existing `src/firmware` directory has many children | The guard found one broken SDK call there | Leaving the call broken would keep the guard red |

## Changed Files

- `tests/integration/test_mistapi_sdk_compatibility.py`: Replace the skipped guard with an AST call-site guard and negative tests.
- `src/firmware/site_auto_upgrade.py`: Change `getSiteSettings` to `getSiteSetting` after the guard found the missing SDK function.
- `tests/unit/test_site_auto_upgrade.py`: Update mocks to the installed SDK function name.
- `tools/guard_proof_audit.py`: Remove the issue #2689 known-debt baseline after the guard repair.
- `tests/guardrails/test_guard_proof_audit.py`: Assert that the SDK compatibility guard no longer appears as known debt.
- `specs/2689-sdk-call-site-guard/spec.md`: Record requirements and decisions.
- `specs/2689-sdk-call-site-guard/plan.md`: Record the implementation plan and file list.
- `specs/2689-sdk-call-site-guard/tasks.md`: Record the dependency-ordered task list.
- `changelog.d/issue-2689-sdk-guard.md`: Record the user-visible guard repair.

## Decisions

- Unresolved dynamic SDK references report loudly and fail only when the count grows beyond 10. This prevents new silent misses without blocking existing dynamic paths.
- Signature checks are deferred to issue #2726. The current issue is function existence. Signature compatibility needs a separate issue because it must model optional parameters and SDK helper conventions.

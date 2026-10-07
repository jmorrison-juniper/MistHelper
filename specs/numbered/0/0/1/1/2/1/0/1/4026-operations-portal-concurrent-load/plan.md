# Implementation Plan: Operations Portal Concurrent Load

**Branch**: `jmorrison-juniper-assessment-4026` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification at `specs/numbered/0/0/1/1/2/1/0/1/4026-operations-portal-concurrent-load/spec.md`

## Summary

Protect lazy `OperationExecutor` construction with one module-level `threading.Lock`.
Keep the existing unlocked fast read, then repeat the read while the lock is held.
Construct and store the executor only when the protected read still finds no value.
Add one forced-race unit test that controls the first configuration read for each caller.
Preserve the `list_msps` route from PR #4065 and all unrelated route behavior.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Flask 3.1, Python `threading`, pytest 9

**Storage**: Flask application configuration for the process-local executor reference

**Testing**: pytest unit test with controlled configuration, a barrier, and concurrent callers

**Target Platform**: Windows development and Linux Gunicorn deployment

**Project Type**: Flask web service in the existing MistHelper repository

**Performance Goals**: Keep the initialized fast path to one configuration read with no lock acquisition

**Constraints**: Use one module-level lock. Keep one accessor. Do not change `web_portal/services/operation.py`.

**Scale/Scope**: One route helper, one deterministic unit test, and one changelog fragment during implementation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-design gate

- **Five-item rule**: PASS. The specification uses the managed eight-level base-5 route.
- **Existing hierarchy debt**: PASS WITH RECORDED DEBT. `web_portal/routes/` and `tests/unit/web_portal/` exceed five children.
- **Incremental remediation**: Record a separate future issue to reorganize portal route and test modules. Do not include that work in issue #4026.
- **Class architecture**: PASS. This repair changes an existing Flask route helper and does not add a wrapper.
- **Safety**: PASS. The change adds no input, destructive action, external request, or secret handling.
- **Deployment pipeline**: PASS FOR PLANNING. Implementation must use a valid Conventional Commit and complete the applicable pipeline.
- **Observability**: PASS. Lock acquisition is internal synchronization, not a separate operator action. No new log is required.
- **Inline comments**: PASS. Implementation must comment each changed executable line with its synchronization purpose.
- **Action logging**: PASS. The constructor behavior and existing logging contract remain unchanged.
- **Testing**: PASS. The plan requires one deterministic test that fails without synchronization.
- **Release note**: PASS. Implementation will add `changelog.d/issue-4026-operation-executor-race.md`.
- **Mist Cloud contract**: NOT APPLICABLE. The change adds no Mist API request or transport.
- **Product output location**: NOT APPLICABLE. The change writes no product output.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/2/1/0/1/4026-operations-portal-concurrent-load/
├── contracts/
│   └── executor-initialization.md
├── data-model.md
├── plan.md
├── quickstart.md
├── research.md
└── spec.md
```

### Source Code (repository root)

```text
web_portal/
└── routes/
    └── operations.py

tests/
└── unit/
    └── web_portal/
        └── test_operation_executor_concurrency.py

changelog.d/
└── issue-4026-operation-executor-race.md
```

**Structure Decision**: Keep the repair in the existing route module.
Place the race regression in the existing portal concurrency test module.
Create the changelog fragment only during implementation.
Do not create `tasks.md` during this workflow.

## Phase 0: Research

Use [research.md](research.md) as the decision record.
The research resolves the lock type, lock location, double-check sequence, test forcing method, and preservation boundary.

## Phase 1: Design and Contracts

Use [data-model.md](data-model.md) for the logical initialization state.
Use [contracts/executor-initialization.md](contracts/executor-initialization.md) for the accessor contract.
Use [quickstart.md](quickstart.md) for implementation validation.

### Implementation sequence

1. Import `threading` in `web_portal/routes/operations.py`.
2. Create one private module-level lock near the logger and existing module constants.
3. Keep the first `OPERATION_EXECUTOR` configuration read outside the lock.
4. Acquire the lock only when the first read returns `None`.
5. Repeat the configuration read while the lock is held.
6. Keep the existing lazy import and constructor call behind the second empty check.
7. Store the constructed executor before the lock is released.
8. Return the stored executor for every path.
9. Add one forced-race unit test in `tests/unit/web_portal/test_operation_executor_concurrency.py`.
10. Preserve `list_msps` and all unrelated route lines.
11. Add `changelog.d/issue-4026-operation-executor-race.md`.
12. Do not modify `web_portal/services/operation.py`.

### Deterministic test design

The test must replace the route module `current_app` proxy with a controlled application object.
Its configuration mapping must block the first executor read from each caller on one barrier.
Later reads must return the stored value without using the barrier.
The test must replace `OperationExecutor` with a constructor that records each call and returns a unique marker.
Concurrent callers must start together and complete within a fixed timeout.
The assertions must prove one constructor call, one stored marker, and identity equality for all results.
The uncontrolled implementation constructs one marker per caller after the forced empty reads.

## Complexity Tracking

No new structural violation is planned.
The touched route and test directories contain grandfathered hierarchy debt.
Issue #4026 must not reorganize those directories because that work is unrelated to the concurrency defect.

## Post-design Constitution Check

- **Scope**: PASS. The design touches one route module, one existing unit-test module, and one implementation-time changelog fragment.
- **Five-item rule**: PASS WITH EXISTING DEBT. The plan adds no new child to the overfull route or test directories.
- **Function limits**: PASS. `_get_executor()` remains under 25 lines and uses at most two conditional blocks.
- **Synchronization**: PASS. One module lock and one protected second read meet the concurrency requirement.
- **Testing**: PASS. The controlled configuration read makes the race deterministic without production timing assumptions.
- **Preservation**: PASS. The contract forbids changes to `list_msps`, unrelated routes, and `web_portal/services/operation.py`.
- **Release process**: PASS. The design defers the unique changelog fragment to implementation as requested.
- **Unresolved clarifications**: NONE.

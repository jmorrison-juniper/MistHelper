# Tasks: Single console output

**Input**: [Specification](spec.md) and [plan](plan.md).
**Tests**: Required by the repository constitution.

## Phase 1: Setup

- [x] T001 Record the confirmed cause in research.md and claim the repair issue. (delivered: research.md)

## Phase 2: Foundation

- [x] T002 Add failing routing tests in tests/unit/utils/test_console.py and tests/unit/refactors/test_main_entrypoint.py. (delivered: tests/unit/refactors/test_main_entrypoint.py)

## Phase 3: User Story 1 - Read each menu line once

**Independent test**: Render the actual menu at each console threshold and assert one copy per row.

- [x] T003 [US1] Add the console-only filter in src/foundation/support/utils/console.py. (delivered: src/foundation/support/utils/console.py)
- [x] T004 [US1] Attach the filter in src/foundation/support/refactors/main_entrypoint.py. (delivered: src/foundation/support/refactors/main_entrypoint.py)

## Phase 4: User Story 2 - Retain operational evidence

**Independent test**: Assert one file copy and visible unrelated warnings and errors.

- [x] T005 [US2] Verify file records and diagnostics in tests/unit/refactors/test_main_entrypoint.py. (delivered: tests/unit/refactors/test_main_entrypoint.py)

## Phase 5: Documentation and validation

- [x] T006 Document the output behavior in src/foundation/support/utils/console.py and changelog.d/issue-4257-single-console-output.md. (delivered: changelog.d/issue-4257-single-console-output.md)
- [x] T007 Run the focused checks from quickstart.md and compare implementation with spec.md. (delivered: tests/unit/refactors/test_main_entrypoint.py)

## Dependencies and execution order

T002 follows T001. T003 follows the failing tests. T004 depends on T003.
T005 depends on T004. T006 and T007 follow both user stories.
The source and integration edits are small and sequential. No parallel implementation is needed.

## Implementation strategy

First prove the duplicate path with real handlers. Add the narrow filter, then verify display and log preservation together.

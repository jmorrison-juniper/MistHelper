# Specification Analysis Report: Locked Bootstrap With a Configured Pip Index

## Scope

This review checks spec.md, plan.md, tasks.md, and the design files against the remote code at main commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Row numbers R01 to R93 refer to `design/research.md`, section 7.

## Findings

### A-1 Requirement coverage

- The spec defines 19 functional requirements. Each requirement maps to at least one task and one test (tasks.md, "Requirement coverage").
- TST-05 passes on main by design. It guards an invariant that already holds. FR-015 applies to the other behavior tests, which fail on main.

### A-2 Plan and task consistency

- The plan file map lists 15 rows. Each path appears in tasks.md.
- Each removed name appears in a task. `INDEX_MISMATCH_MESSAGE` and `configured_index` appear in T013. `_effective_sources` appears in T011. The precedence test and the mismatch test appear in T009 and T010.
- The plan and tasks both name the decision gate D-1 before T011.

### A-3 Decision and gate consistency

- D-1 is the only human decision. The spec, plan, tasks, and summary each name it.
- The plan assumes option C. The change scope changes for the other options:
  - Option A removes no test assertion and changes no source file. The work becomes documentation only.
  - Option B keeps the extra mapping. TST-01 and TST-07 change their expected values.
  - Option P needs a preview configuration task that the tasks do not contain. A new task must precede any option P work.

### A-4 Remote evidence

- Each spec claim cites a row. The spec cites R41, R43, and R44. The plan cites every constitution rule by row.
- The row count is 93. The research table, the STATUS file, and the summary must each state 93.

### A-5 Defects in existing work

1. Existing tests encode the old mapping as expected behavior. R51 asserts the configured index as the uv primary. R52 asserts the configured sources as the uv primary. R53 asserts the uv primary after apply. R55 asserts no inherited uv primary. R57 asserts the mismatch message. Severity: medium. Resolution: T009 and T010.
2. The development guide describes the old mapping as intended (R67, R68). Resolution: T015.
3. The module docstring states the old stop behavior (R28). Resolution: T013.
4. The mismatch branch and its message fire only for the old mapping (R30, R38). Under option C they become unreachable. Resolution: T013.
5. The owner Windows output shows the generic failure text (comment 6847333228). The current code path (R38) would name the mismatch. The cause is unresolved (research.md, U-3). The repair removes the mismatch branch either way.
6. `read_lock_registry` reads only the first registry line (R31). A second registry would pass unnoticed. Resolution: TST-05 guards the repository state. The residual risk is recorded in the spec edge cases.
7. Version drift is recorded but not fixed. pyproject states `>=0.64.1,<0.65` (R47). requirements states `0.64.1` (R48). The development guide states `0.64.0` (R89). The constitution states `0.59` or newer (R27). The brief text names `>=0.64.0`, which differs from pyproject. Resolution: D-11, a separate issue.
8. The bootstrap module holds 17 top-level names (R40). This violates the five-item rule. It predates this change. Resolution: D-11, a separate issue.
9. The symbol gate reports the two removed names by design (D-9). The pull request records the exception.

### A-6 Unresolved items

- Owner decision D-1 (HUMAN-DECISION-REQUIRED).
- Unverified items U-1 to U-9 (research.md, section 10).
- The owner Windows result for SC-002.
- The label `needs-human-review` stays until the owner decides D-1 (D-13).

### A-7 Coverage notes

- Mist API: no claim depends on it (R41).
- Runtime package `src/foundation/runtime/bootstrap/`: no change (D-8).
- Containers: no claim depends on a container run.
- Pull request overlap: no open pull request changes a planned path (research.md, section 4).

## Metrics

| Measure | Value |
| - | - |
| Functional requirements | 19 |
| Success criteria | 6 |
| Tasks | 21 (4 verified-present, 17 open) |
| Planned behavior tests | 9 (6 new, 3 rewritten) |
| Planned test removals | 2 |
| Existing tests kept | 8 (KT-01 to KT-08) |
| Remote checks | 93 |
| Decisions | 14 (1 human) |

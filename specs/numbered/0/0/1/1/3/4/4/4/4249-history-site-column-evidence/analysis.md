# Specification Analysis Report: History Site Column Failure Evidence

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, `design/contracts/diagnostics-artifact.md`, the state of `main` on 2026-11-26, and the local third-party files that `design/research.md` names.

**Method**: A read-only pass compared the issue, the job log, the remote tree, and the code. Each finding names its evidence. No command ran a test, a build, or a repository script.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
|---|---|---|---|---|---|
| A-01 | Verified | INFO | Issue body and job log | The issue cites run 38860502112, job 116842182317, and log line 1252. The job log confirms each one. | None needed. |
| A-02 | Inconsistency | LOW | Issue body, silence | The issue states 107 seconds of silence. The log gives 104.12 seconds, from line 1770 to line 1771. | The record uses the measured value (R1). |
| A-03 | Inconsistency | LOW | Issue body, outcome count | The issue states 530 outcomes. The loose pattern gives 530. The node-id pattern gives 527. | The record gives both counts (R1). |
| A-04 | Defect in reasoning | MEDIUM | Issue body, silence | The issue links the silence to the page-close hang of issue #4247. The silence starts at 06:41:23. The failed line is at 06:25:04. The silence does not explain the failure. | Candidate H-3 is excluded for this line (R3). |
| A-05 | Gap | HIGH | Job log | The job log holds no `AssertionError`, no `Traceback`, and no `short test summary` line. The failing assertion cannot be named from CI evidence. | The record names two candidate statements, lines 283 and 284 (R3). FR-011 requires the check that decides between them. |
| A-06 | Method defect | MEDIUM | Reproduction command | `gh run view --log-failed` printed zero lines for this run. The test step ended as `cancelled`, not `failure`. | The quickstart uses `--job` with `--log` (R1). |
| A-07 | Gap | MEDIUM | CI guard | No guard checks the `Upload shard diagnostics` step. The shard guard checks the pytest options, the partition, and the gate. | T002 and T003 add the check (RC-34). |
| A-08 | Gap | MEDIUM | Pytest output | Pytest prints failure details only in its terminal summary (RC-68). A canceled shard log therefore lacks the traceback. | Accepted under D-2. FR-007 and the gate page state the limit. |
| A-09 | Conflict | LOW | Changelog rule | `changelog.d/README.md` line 58 exempts internal-only changes (RC-44). The constitution line 409 requires one fragment for each change (RC-50). The constitution governs (RC-51). | Decision D-6. One fragment is added. |
| A-10 | Conflict | MEDIUM | Pull request body | The brief requires `Closes #4249`. The owner comments keep the issue open. | Decision D-5. A follow-up issue is required before the merge. |
| A-11 | Constraint | MEDIUM | Folder limits | `tests/guardrails` holds 79 direct entries on `main` (RC-36). A new file there breaks the five-item rule. | Decision D-3. The guard goes in the existing file. |
| A-12 | Constraint | LOW | Class limits | `ShardPartitionAudit` holds six methods on `main` (RC-35). A seventh method adds to the debt. | The audit gets its own class. |
| A-13 | Discrepancy | LOW | Run head | The issue names PR #4248 head `e4487cd`. The run ran `e4487cd`, which is not on `main` (RC-59). The PR head now reads `07edd50`. | Recorded in R1. No action. |
| A-14 | Unverified claim | LOW | Issue body | The issue states that the test passed in the PR #4242 E2E run before its merge. No log was read. | Listed as U-1. |
| A-15 | Unverified claim | LOW | Issue body | The issue states that a container run at `e4487cd` passed with 922 passed and 51 skipped. No log was read. | Listed as U-2. |
| A-16 | Unverified claim | LOW | Owner comment | The owner comment of 2026-10-25 shows `1 passed in 4.00s` for a local run. No log exists on GitHub. | Listed as U-4. |
| A-17 | Assumption | LOW | Seed data | The seed comment says no other journey reads the seed site (RC-16). Whether another journey writes to it was not read. | Listed as U-5. |
| A-18 | Gap | LOW | Gate page | The gate page does not name the diagnostics artifact (RC-38). | T005 adds the paragraph. |
| A-19 | Timing | INFO | Failed line | The failed line follows the previous PASSED line by 0.80 seconds. A failing wait takes at least 5 seconds (RC-70). The failure came from a statement without a wait. | Used in R2. |
| A-20 | Verified | INFO | Current main | The current shard configuration keeps the diagnostics after a failed or canceled shard (RC-23 to RC-27). It also keeps the traces and the failure screenshots (RC-66, RC-67). | No product change is needed. |

## Coverage Summary

| Requirement | Has task | Task IDs | Test IDs | Notes |
|---|---|---|---|---|
| FR-001 | Yes | T001, T002, T003 | TP-01 | |
| FR-002 | Yes | T002, T003 | TP-01, TP-02 | |
| FR-003 | Yes | T001 | TP-03 | Existing test. |
| FR-004 | Yes | T002, T003, T004 | TP-01, TP-02 | |
| FR-005 | Yes | T007 | TP-04 | |
| FR-006 | Yes | T005 | TP-06 | |
| FR-007 | Yes | T005 | TP-06 | |
| FR-008 | Yes | T006 | TP-05 | |
| FR-009 | Yes | T007 | TP-07 | |
| FR-010 | Yes | T-FOLLOW, T-PR, T-MERGE | TP-08 | |
| FR-011 | Yes | T008 | TP-09 | |
| SC-001 | Yes | T003 | TP-01, TP-02 | |
| SC-002 | Yes | T-LOCAL-GATES | Gate commands | |
| SC-003 | Yes | T-REMOTE-CI, T-MERGE | Remote checks | |
| SC-004 | Outside this change | None | None | Needs a future failed run (A-05). |
| SC-005 | Outside this change | None | None | Needs a future failed run (A-05). |

## Constitution Alignment

- Principle I: The plan adds no child to a full folder. The new class has one method.
- Principles VI and VII: T002 requires inline comments and action logging for the new code.
- Principle IV: T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover the agent steps. Steps 10 to 12 need the owner.
- Release notes: T006 adds one fragment (RC-50).

## Unresolved Items

1. The root cause stays unverified (A-05). The follow-up issue keeps it open (D-5).
2. The failing assertion stays unnamed until a failed run keeps a traceback or a failure screenshot (SC-004, SC-005).
3. A canceled shard log can still lack the traceback (A-08). Decision D-2 defers the hook.

## Metrics

- Functional requirements: 11. Success criteria: 5. Tasks: 13. Planned tests: 9.
- Decisions: 6. Human decisions: 0.
- Remote checks: 70. Each check has a row in `design/research.md`.
- Critical issues: 0.

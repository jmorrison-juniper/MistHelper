# Specification Analysis Report: SpecKit Task Audit Link and Legend Classification

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, `design/data-model.md`, `design/contracts/speckit-audit-report.md`, and the remote state of `main` and the pinned upstream commit.

**Method**: A read-only pass compared the issue text, the spec, the plan, the tasks, and the remote evidence. Each remote check appears in the table in `design/research.md`. This report lists the state after the review.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
|----|----------|----------|----------|---------|------------|
| A1 | Inconsistency | MEDIUM | Issue #4703 body | The issue names `TaskFileScanner._count_line`. That method exists at `e8e093d` (RC-22). At `2239e7bd` the logic sits in `_count_lines` and `_is_malformed` (RC-27, RC-23). | Resolved. The record cites both names and both commits. |
| A2 | Inconsistency | LOW | Issue #4703 body and CI log at 3964d21 | The issue body reports 885 records, 407 task files, 11029 markers, 7520 checked, and 3473 unchecked. The CI log reports 884, 405, 10942, 7512, and 3394. Both report 36 malformed markers. | Resolved. The record uses the CI log values, which come from the run itself. |
| A3 | Inconsistency | LOW | PR #4836 body and upstream commit `2239e7bd` | The PR body names misthelper-devtools PR #84 for commit `2239e7bd`. GitHub returns no pull request for number 84. The commit message names PR #95. | Resolved for this record. The commit SHA is the authority. The PR body is not edited by this change. |
| A4 | Underspecification | HIGH | Issues #4703 and #4765 | Issue #4703 requires an authorized dependency update (comment of 2026-11-16). PR #4836 merged the pin change on 2026-11-19 under issue #4765. Neither issue holds a comment that authorizes that change. | Unverified (design/research.md, U1). Decision D-6 gates closure on orchestrator authorization. |
| A5 | Defect in existing work | MEDIUM | `.github/workflows/ci.yml` line 750 | The step `speckit-task-audit || true` masks the exit code. The source returns 1 for a complete record with open tasks or bad citations (RC-28). The main run shows open findings and a passing job. | Out of scope. Decision D-2 keeps the advisory design. T005 documents the masking. |
| A6 | Defect in existing work | HIGH | Pull request #4888 and run 45064243269 | The audit job fails at the install step. `mando==0.8.2` (RC-16) conflicts with `radon==6.0.1` (RC-17), because radon requires `mando<0.8`. The audit never runs in that run. | Out of scope. Decision D-7 requires a separate issue. Pull request #4888 stays open. |
| A7 | Coverage | LOW | Local `.venv` copy of `misthelper_devtools` | The local copy holds the same repair at lines 122, 288 to 299, 318, and 427. The copy is local-only evidence. | Recorded as local-only. It is not used as proof for any remote claim. |
| A8 | Unverified claim | LOW | Issue #4703 body | The split of the 36 markers into 27 legend bullets and nine links is not re-derived. The CI log shows only the total. | Listed as Unverified (U2). |
| A9 | Coverage | LOW | Issue #4703 acceptance criteria | The criteria require retained completed-spec and citation decisions. The pinned upstream tests cover them (RC-31, RC-32). | Verified. Both behaviors have upstream tests at `2239e7bd`. |
| A10 | Dependency on upstream names | LOW | Design of the positive test | The positive test reads `malformed_lines`. That field exists at `2239e7bd` (RC-24) and not at `e8e093d` (RC-21). | Accepted. The field name is part of the pinned contract. Upstream renames require a test update. |
| A11 | Ambiguity | LOW | FR-003 | The phrase "a commit that contains the repair" needs proof. Commit `2239e7bd` contains `da96d6e`, because the comparison reports two commits ahead and none behind. | Resolved. The comparison result is in design/research.md, section R3. |
| A12 | Consistency | LOW | Route of the record | The route `0/0/1/2/2/3/0/3` equals the base-five digits of 4703 (`122303`), padded to eight digits (RC-45). | Verified. |
| A13 | Coverage | LOW | Upstream CI | The upstream CI run on `2239e7bd` concluded success (run 44580808631). | Verified at the conclusion level. Job-level test logs were not read. U3 records this limit. |
| A14 | Consistency | LOW | Changelog fragment name | The README table names the issue form for a change without a pull request. The policy test accepts that form (RC-42, RC-43). | Resolved by decision D-4. |

## Coverage Summary

| Requirement | Has task | Task IDs | Test | Notes |
|-------------|----------|----------|------|-------|
| FR-001 | Yes | T002, T003, T004, T006, T-REMOTE-CI | Negative regression test | Legend and link lines count as zero. |
| FR-002 | Yes | T002, T004, T005, T006 | Positive regression test | The positive test checks `malformed_lines == (3,)`. |
| FR-003 | Yes | T001, T004, T-REMOTE-CI | Negative and positive regression tests | The tests fail under a pin that lacks the repair (static proof, U4). |

## Constitution Alignment

`design/checklists/requirements.md` and `plan.md` record the constitution check. The check finds no violation. Two rules pass with a stated reason: Principle VII for test code, and the container build rule for documentation-only changes.

## Unmapped Tasks

- T007, T-PR, T-REMOTE-CI, and T-MERGE map to process requirements, not to behavior. Each process task still names its verification command.
- T-LOCAL-GATES maps to all three requirements, because it runs the gates that check each one.

## Metrics

- Requirements: 3 (FR-001 to FR-003).
- Success criteria: 3 (SC-001 to SC-003).
- Tasks: 11, including the four final tasks.
- Planned tests: 2.
- Remote checks: 48, the same count as the remote table in `design/research.md` and `remote_checks` in the status file.
- Decisions: 7 (D-1 to D-7). Decisions that need a human: 0.

## Unresolved Items

1. **Authorization of the pin update (A4).** The orchestrator must confirm the authorization before T-MERGE. Unverified item U1 holds the reason.
2. **Masked exit code (A5).** The step hides the audit exit code by design. Decision D-2 keeps that design. The risk remains, and T005 documents it.
3. **Dependency conflict (A6).** Pull request #4888 stays open and blocked. A separate issue must track it, as decision D-7 requires.
4. **Unverified split and execution (A8, U2 to U4).** The record does not verify the 27 and nine split. It does not run the tests. The implementer confirms the tests during T-LOCAL-GATES.

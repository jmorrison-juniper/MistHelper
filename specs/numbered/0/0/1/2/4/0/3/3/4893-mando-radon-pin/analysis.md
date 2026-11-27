# Analysis: Hold mando below 0.8 for the mypy gate

## 1. Consistency across spec, plan, and tasks

| Requirement | Tasks | Tests or gates | Result |
| - | - | - | - |
| FR-001 pins resolve | T002, T004, T009 | Guard tests 1 and 2 (T004), Types row | Consistent |
| FR-002 Dependabot holds mando | T003, T004 | Guard tests 3 and 4 (T004) | Consistent |
| FR-003 mypy gate passes | T001, T009, T-LOCAL-GATES, T-REMOTE-CI | Types row, remote `mypy (strict)` status | Consistent |
| FR-004 one fragment | T005 | `tests/guardrails/test_changelog_fragment_policy.py` | Consistent |
| FR-005 local gates pass | T006, T007, T008, T010, T-LOCAL-GATES | Lint, Format, STE, Test quality, and the other applicable rows | Consistent |
| FR-006 PR #4888 closes with proof | T-MERGE steps 5 and 6 | `gh pr view 4888` acceptance check | Consistent |

Success criteria:

- SC-001 maps to T-REMOTE-CI and T001.
- SC-002 maps to T-REMOTE-CI and the run log count (26 jobs).
- SC-003 maps to T-MERGE step 4.
- SC-004 maps to T-MERGE steps 5 and 6.

Counts:

- Requirements: 6 (FR-001 to FR-006). Matches `requirements` in STATUS.
- Tasks: 14 (T001 to T010, T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE). Matches `tasks` in STATUS.
- Planned tests: 4 new guard tests (T004). Matches `tests_planned` in STATUS.
- Remote checks: 71 (research.md section 5). Matches `remote_checks` in STATUS and `4893-summary.md`.

Record shape:

- The feature root holds five children: `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`.
- `design/` holds four children: `research.md`, `data-model.md`, `quickstart.md`, and `checklists/`. `contracts/` is omitted, and `plan.md` says why.
- `checklists/` holds one file, `requirements.md`.

## 2. Defects in existing work

| ID | Defect | Evidence | Action |
| - | - | - | - |
| AD-1 | PR #4888 changes one pin and does not check the radon constraint. | research.md section 2, RC-09, RC-14, RC-67 | Fixed by D-1. The pin stays at 0.7.1. |
| AD-2 | Dependabot has no ignore entry for `mando` in the pip block. | RC-25 | Fixed by T003. |
| AD-3 | The issue cites the merge revision. The run head is the PR head revision. | RC-65, RC-66 | Reported in section 2 of research.md, and D-6 records the choice. The issue text is unchanged. |
| AD-4 | The issue title names `mypy`. The failing job is `mypy (strict)`. | RC-03, job 137338084785 | The record names the exact job. No issue text is changed. |
| AD-5 | `dependency_lock` runs `uv lock --check` after pip install (RC-04). The install failure hides the lock result. | Step list of job 137338980629 | Not changed. `main` runs pass, so the lock result is known there. |
| AD-6 | 15 quality-gate issues (#4891 to #4905) have one root cause. | research.md section 3 | Out of scope. Each keeps its record. A separate issue can group them. |
| AD-7 | `tests/guardrails/` holds 79 children and `changelog.d/` holds 335. | RC-34, RC-35 | Recorded as debt in plan.md, with a separate remediation action. |
| AD-8 | `pytest (coverage gate)` fails through the `dependency_lock` result. | RC-08 | Not a separate defect. It clears when `dependency_lock` passes. |

## 3. Unresolved items

- U-1 and U-2 (Dependabot classification and syntax): verified by T-MERGE step 4 after the merge.
- U-3 (guard test runtime behavior): verified by T004 and T-LOCAL-GATES.
- U-4 (cause of `E2E smoke tests`): not read. Its record needs its own issue, which the orchestrator files.
- U-5 (`pytest (coverage gate)` after the fix): verified by T-REMOTE-CI.
- U-6 and U-7 (Bandit scope, symbol output): verified by T-LOCAL-GATES.
- Radon watch: when radon releases a version that accepts `mando` 0.8, a new decision must remove the ignore entry and update the pin.

## 4. Conflict handling

- AGENTS.md (RC-42) and `.github/copilot-instructions.md` (RC-39) both warn against closing update pull requests for title repair. Closing PR #4888 is a different action. It rejects an update that cannot resolve. D-4 records this, and the pip update stream stays on.
- The constitution and the local gates table both require each gate for each changed file. T-LOCAL-GATES covers each applicable row, and it lists each row that does not apply with its reason.
- The constitution requires a fragment for each change (RC-46). The brief marks no human category, so D-5 keeps the fragment.

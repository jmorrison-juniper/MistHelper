# Analysis: Merge queue rollout and acceptance

## Scope and method

The review read these sources on 2026-11-26:

- Issue #3071 (body and 22 comments). Issue comments are cited by URL in `design/research.md`.
- PRs #4362, #4483, #4208, #4306, #4498, #4513, #4515, and the 14 PRs that the issue search returned.
- The legacy record `specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/` (nine files).
- The repository files on `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Each cited local file has the same Git blob SHA as the remote file (`git hash-object`).
- The shared workflows of `misthelper-devtools` at the pinned commits `d63a120487cecf750184cb178387cdc25c0a7635` and `79a5e45970e876f1656d69520d9635cea1aa25ef`.
- The public `github/docs` repository, read through the GitHub API.

No gate ran. No file, label, setting, branch, or pull request changed.

## Consistency review: specification, plan, tasks, and remote code

| Item | Specification | Plan | Tasks | Remote evidence | Result |
| - | - | - | - | - | - |
| FR-001 `merge_group` on both workflows | Required | No change | Checked by T-LOCAL-GATES | R-01, R-10 | Consistent |
| FR-002 Required names unchanged | Required | No change | T001 | R-09, R-52 | Consistent. The `CodeQL` context is verified only live (U-3). |
| FR-003 Queue candidate checkout | Required | No change | T-REMOTE-CI | R-06, R-21 | Consistent |
| FR-004 Separate groups | Required | No change | T-LOCAL-GATES | R-02, R-11, R-33 | Consistent |
| FR-005 Existing triggers | Required | No change | T007 | R-03, R-04, R-05, R-12, R-13 | Consistent |
| FR-006 Workflow table | Required | Rows 467 and 468 | T004 | R-27, R-28 | Inconsistent on `main` until T004. Defect DF-1. |
| FR-007 Procedure headings | Required | Procedure update | T005 | R-23, R-25 | Partly consistent. The preparation text is in the future tense. Defect DF-5. |
| FR-008 Guard fails on drift | Required | New guard method | T003 | R-30 to R-33 (existing methods only) | Open. No drift guard exists for the table or the heading. |
| FR-009 No setting change | Required | No change | T001 | R-52, R-54, R-55 | Consistent on the baseline. The post-change check is in T001 rerun. |
| FR-010 No workflow edit | Required | No change | T007 | R-17 (the rule that blocks such a pull request) | Consistent |
| FR-011 `Refs #3071` | Required | T-PR | T-PR | R-40 (constitution asks for `Closes`) | Conflict. Defect DF-7 and decision D-5. |
| FR-012 Owner evidence | Required | O-4 and O-5 | Owner steps, not tasks | R-56 | Open. Owner action. |
| FR-013 Candidate rule | Required | O-4 and O-5 | Owner steps, not tasks | R-61 to R-63 | Consistent with the GitHub docs. Batch limits and failure removal match. |
| FR-014 Review rule | Required | O-1 | T002 | R-53 | Open. The three reads disagree. Defect DF-9. |

## Defects in existing work

Each defect has an ID, a location, a remote row, and a planned fix or an owner action.

- **DF-1. Stale workflow table.** `.github/copilot-instructions.md` rows 467 and 468 say `ci.yml` and `codeql.yml` run on pull requests and pushes to `main` only (R-27, R-28). The rows omit merge queue candidates. Fix: T004. Impact: a contributor reads an incomplete trigger list.
- **DF-2. Wrong Python version in the legacy plan.** The legacy plan names Python 3.13 (R-45). `pyproject.toml` requires Python 3.15 or newer (R-39). The legacy local runs used Python 3.13.13 (L-28, unverified). Fix: the revised plan names Python 3.15. T-LOCAL-GATES runs on Python 3.15.
- **DF-3. Stale task status.** Legacy task T012 says the pull request is pending (R-46). PR #4362 merged on 2026-10-20 (R-48). Fix: the revised tasks mark the preparation as complete.
- **DF-4. Stale reservation for PR #4208.** The legacy record says PR #4208 holds the browser evidence section in `ci.yml` (L-12). PR #4208 is an open draft and it does not change `ci.yml` (R-50). `ci.yml` on `main` already holds the browser evidence upload steps (R-08). Fix: the revised record drops the reservation. No code change is needed.
- **DF-5. Future-tense preparation text.** `documentation/quality-gates.md` lines 111 to 120 describe the preparation as work to do, while PR #4362 completed it (R-23, R-48). Fix: T005.
- **DF-6. Acceptance text names an absent path.** Issue #3071 acceptance criterion 4 names `.github/instructions/git-flow-multi-agent.instructions.md`. The path is absent on `main` (R-42). The owner approved `documentation/quality-gates.md` as the replacement (R-24, owner comment at `https://github.com/jmorrison-juniper/MistHelper/issues/3071#issuecomment-6296715182`). Fix: owner step. The owner edits the acceptance text on the issue. Agents cannot edit the issue body.
- **DF-7. Constitution conflicts with the owner on `Closes`.** The constitution requires the Closes keyword with the issue number in each pull request body (R-40). `documentation/contributing.md` step 6 asks for the same (R-66). The owner requires issue #3071 to stay open until the evidence exists (`https://github.com/jmorrison-juniper/MistHelper/issues/3071#issuecomment-6309236843`, and `documentation/quality-gates.md` line 118, R-25). Decision D-5 uses `Refs`. Fix: the coordinator accepts the deviation, or the constitution and `documentation/contributing.md` get an amendment that allows `Refs` for an issue that stays open.
- **DF-8. README and constitution conflict on release notes.** The changelog README rule 4 says no fragment for an internal-only change (R-34). The constitution requires one fragment for each change (R-65). Decision D-6 follows the constitution. Fix: owner aligns the README.
- **DF-9. Review rule reads disagree.** The full protection read says `required_pull_request_reviews` is null (R-53). The separate reviews endpoint says the required approving review count is 1 (R-53). GraphQL says `requiresApprovingReviews` is false (R-53). The owner reported the same conflict on 2026-10-30 (`https://github.com/jmorrison-juniper/MistHelper/issues/3071#issuecomment-6516090555`). Fix: owner step O-1.
- **DF-10. Local STE scope gap.** The STE gate in `ste-lint.yml` lists five files (R-15). `documentation/quality-gates.md` is not in that list. The `AGENTS.md` rule still applies. Fix: T-LOCAL-GATES item 11 runs the local STE gate. The owner may add the file to the CI list.
- **DF-11. Non-required job failure on a merged pull request.** PR #4483 merged with one failed job, `ops-portal (npm audit, types, lint, tests)` (R-49). The job is not a required context. The cause is not investigated in this record (U-8). Fix: none in this change. The owner may open a separate issue.
- **DF-12. Shared auto-merge has no queue or canceled-result handling.** The pinned shared auto-merge workflow contains no `merge_group` or merge queue text (R-19). It contains no handling for `CANCELLED`, `TIMED_OUT`, or `STALE` conclusions. The repository procedure treats these results as unresolved. The residual risk sits in `misthelper-devtools` (U-4). Fix: none in this repository. A follow-up issue in `misthelper-devtools` is recommended. This run does not create it.
- **DF-13. Guard module and changelog debt.** `tests/guardrails/test_ci_gate_triggers.py` holds more than five top-level names. `changelog.d` holds 335 top-level entries (R-35). The constitution grandfathers both under Principle I. Fix: none in this change. The plan records the debt.
- **DF-14. Legacy fragment heading.** `changelog.d/issue-3071-merge-queue-support.md` uses the heading `### Changed`, which names the type and not the change (R-36). The changelog README asks for a heading that names the change (R-34). Fix: none in this change. The new fragment follows the README.

## Legacy record verification

The legacy record holds 28 claims that this review checked. The details are in `design/research.md` section "Legacy record verification."

- Verified: 22 claims (L-01 to L-10, L-14 to L-21, L-24 to L-27).
- Stale: 4 claims (L-11, L-12, L-13, L-22).
- Absent: 1 claim (L-23, owner activation).
- Unverified: 1 claim (L-28, local test and lint results). Reason: the local runs used Python 3.13.13, and this review did not re-run them.

## Unresolved items

These items need owner action or owner evidence. Each one has an owner step in `plan.md`.

- Review rule (DF-9). Owner step O-1.
- Owner activation approval. Owner step O-3.
- `CodeQL` context on a queue commit (U-3). Owner step O-4.
- Shared auto-merge behavior under an active queue (U-2). Owner step O-4 and O-5 (manual enqueue first).
- Acceptance text on issue #3071 (DF-6). Owner edit.
- Constitution `Closes` rule (DF-7). Coordinator decision or amendment.
- Changelog README rule 4 (DF-8). Owner edit.
- STE scope for `documentation/quality-gates.md` (DF-10). Owner may add the file.
- Follow-up issue for shared canceled-result handling (DF-12). Owner or orchestrator files it.

## Residual risk after this change

The change alters documentation and one guard method. No runtime path changes. The residual risk is the owner activation. The queue can stall if the owner enables it before its prerequisites hold, or if an unverified GitHub behavior differs from the public docs. The procedure in `documentation/quality-gates.md` and the owner steps in `plan.md` bound that risk.

## Local gate evidence

The legacy analysis lists local results: 1,060 guardrail tests, Ruff, Black, mypy, Bandit, pip-audit, and the test quality ratchet. Those runs used Python 3.13.13 on macOS (L-28, U-6). This review did not run any gate. T-LOCAL-GATES reruns every applicable gate on Python 3.15.

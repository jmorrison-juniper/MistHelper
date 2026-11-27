# Specification Analysis Report: Backlog Handoff Recovery

## Method

This review compares spec.md, plan.md, tasks.md, and design/research.md with the state of GitHub main on 2026-11-26. Each finding cites its evidence row in design/research.md. Severity values are high, medium, low, and info. A high severity finding blocks a routine action until its resolution task runs.

## Findings

| ID | Area | Finding | Evidence | Severity | Resolution |
| - | - | - | - | - | - |
| A-01 | Handoff count | The handoff gives three open issue counts: 127 in the inventory, 132 in comment 3, and 133 in comment 5. GitHub holds 166 open issues. | R-10, R-11 | High | T022 and T023 replace the counts. |
| A-02 | Open PRs | The handoff lists two open PRs. GitHub holds seven. Five Dependabot PRs, 4886 to 4890, are open and BEHIND. | R-12 | High | T004 records the set. T026 refreshes the Dependabot PRs. |
| A-03 | Inventory | Issue 4867 is closed by PR 4871, but the inventory lists it as open. | R-09 | Medium | T023 removes the row. |
| A-04 | Body section 10 | The body says issue 4762 is CLOSED. Comment 3 reopened it, and GitHub holds it OPEN. | R-08 | Medium | The decision comment supersedes section 10. T022 corrects the body. |
| A-05 | Held-by claim | Comment 3 says PRs 4322, 4358, 4493, and 4799 to 4820 hold the old commits. Six of the 25 numbers are issues, not PRs. | R-21 | Medium | T014 records the split. T022 corrects the claim. |
| A-06 | Devtools pins | The Python pins name 2239e7bd. Nine uses lines name the v0.6.4 commit 79a5e459. One uses line, in auto-merge.yml line 61, names d63a1204. The handoff names one pin and does not name this drift. | R-46 to R-51 | High | D-7 aligns the pins. T027 applies the change. |
| A-07 | Changelog rule | The constitution says each change adds one fragment (constitution.md:409). Copilot-instructions line 451 says a fragment is for a change that a user sees. The constitution governs, because its governance section names it as the authority (constitution.md:529). | R-64, and R-55 blob at line 451 | Low | T-PR adds one fragment, and the plan records the choice. |
| A-08 | mistapi floor | Copilot-instructions line 21 says `mistapi>=0.64.0,<0.65`. The pyproject line 29 says `>=0.64.1,<0.65`. The installed SDK is 0.64.1. | R-54, R-55, R-74 | Medium | D-8 names pyproject as the pin of record. T029 corrects the instruction file. |
| A-09 | Hold rule | Handoff section 4 step 5 requires a hold-phrase check, but it names no phrases. | Handoff section 4 | Medium | D-9 and FR-023 define four phrases. T030 applies them. |
| A-10 | Token rule | The handoff prefixes each gh command with `env -u GH_TOKEN -u GITHUB_TOKEN`. The authoring brief sets the account token for each gh call. The two rules conflict. | Handoff section 2, incident 1893 (R-61) | Medium | D-10 and FR-018 use an identity check before each write. |
| A-11 | List limit | Handoff section 2 lists open issues with `--limit 300`. The open count of 166 is near that limit. | R-10 | Low | TST-03 uses a limit of 1000. T022 changes the body command. |
| A-12 | Recovery refs | Section 11 names seven refs without a suffix. Comment 3 names six refs with the `-wip-20261122` suffix. GitHub holds 63 refs under recovery/, so 50 refs have no name in any handoff comment. | R-24, R-25 | Medium | T028 gives each ref a review decision. |
| A-13 | Archive tags | Comment 3 says 47 new archive tags were pushed. GitHub holds 169 archive tags, and the 47 names are not listed. | R-26 | Low | U-08 keeps the subset unverified. T007 records the count. |
| A-14 | Route helper | PR 4909 changed `common.ps1` and `create-new-feature.ps1`, but not `spec-route.ps1`. The current blobs are cited. | R-34 to R-36 | Info | The record uses the current blobs. TST-09 runs before T-PR. |
| A-15 | Route regression | Issue 4910 reports that the routed setup scripts dropped the 1.4.3 hardening. | Open issue list (R-10) | Medium | TST-22 runs before T-PR. |
| A-16 | Windows gates | Issues 4877, 4878, and 4917 report guard failures on Windows. The coordinator host is Windows. | Open issues 4877, 4878, and 4917 | Medium | The local result is recorded as it is. CI decides. |
| A-17 | Dependabot gates | PR 4886 has a failing pytest gate. PR 4888 has 15 failing gate issues. PRs 4889 and 4890 have failing ops_platform_pytest gates. PR 4887 has no gate issue. | R-28 | High | D-6 blocks merges while a gate fails. T026 refreshes the PRs. |
| A-18 | Issue 4825 | The claim that mistapi lacks listOrgInvites is true (R-74). Main already logs an error and skips the call (R-73). The open issue asks for a different outcome. | R-73, R-74 | Info | Triage in T024 decides the outcome. |
| A-19 | Issue 4721 | Main already appends rows on resume (R-75). The defect may be fixed already. | R-75 | Medium | T025 writes a failing test first. No code changes before the test shows the defect. |
| A-20 | Quality Gates history | Section 14 says Quality Gates was green at 260f4bcf. Main is green at f03c6c9b3. The historical run was not checked. | R-04, U-06 | Low | T022 replaces the statement with the current run. |
| A-21 | Devtools PR 95 | The handoff calls PR 95 a changed-API gate fallback. The PR title says it scans the full gate scope when changed tests are excluded. | R-53 | Low | T022 corrects the note. |
| A-22 | Laptop state | Branch counts, worktrees, stash counts, Podman volumes, and the secret scan describe another host. | U-01, U-02, U-03 | Medium | T036 verifies them on that host. |
| A-23 | Pointer target | The feature pointer names the record of issue 4785. This record does not change that target. | R-33 | Info | FR-006 and TST-29 keep the pointer unchanged. |
| A-24 | Cross-repo numbers | The handoff names juniper-agent-skills PRs 823 and 825. MistHelper numbers 823 and 825 are unrelated. | research.md named claim counts | Low | The counts exclude them. |
| A-25 | Tests on Windows | Section 6 says 41 spec-route tests fail without pwsh. The tests were not run. | U-04 | Low | T-LOCAL-GATES runs the route contract test on the implementer machine. |
| A-26 | Recovery duplicates | The six wip refs repeat six named refs with the suffix. Both sets exist on origin. | R-24, R-25 | Low | T028 reviews both sets together. |

## Consistency Review

The review checks the four documents against each other and against the remote evidence.

- **Requirements to tasks**: Each FR-001 to FR-025 maps to at least one task and one check. The coverage table in tasks.md shows the mapping.
- **Tasks to checks**: Each task names a check in design/quickstart.md, and each task names a file for the STE row or the Tests row.
- **Route**: spec.md, plan.md, and tasks.md name the same route, 0/0/1/2/3/4/4/0. TST-19 derives the route by base-5 arithmetic.
- **Counts**: The STATUS file reports 25 requirements, 42 tasks, 37 planned checks, and 22 decisions. Four decisions need a human. The remote table holds 79 rows.
- **Decisions to tasks**: D-1 maps to T008 and T-PR. D-2 maps to T004 and T032. D-4 maps to T028. D-6 maps to T026. D-7 maps to T027. D-8 maps to T029. D-9 maps to T030. D-10 maps to T021. D-11 maps to T036. D-12 maps to T033. D-13 maps to T034. D-14 maps to T035. D-17 maps to T038.
- **Human decisions**: H-1 covers D-2, H-2 covers D-12, H-3 covers D-13, and H-4 covers D-14.
- **Constitution**: Each rule in plan.md has a result and a reason. The plan lists no failed rule.

## Unresolved Items

- H-1: The user supplies staging credentials for PR 4813, or confirms the hold. The user also confirms the acceptance of PR 4806.
- H-2: The owner records the licensing decision for issue 4635.
- H-3: The owner decides whether PR 4208 continues or closes.
- H-4: The owner names a destination for the `.env` file of worktree live-deploy-aa0762d.
- The mistapi floor correction (D-8) needs a separate documentation change.
- The 50 recovery refs that no handoff comment names need a review decision (A-12).
- The 47 archive tags named in comment 3 need a name list (A-13).
- The coordinator laptop claims need verification on that host (A-22).
- The routed layout port (issue 4873) and the hardening regression (issue 4910) need closure before the route helper is trusted (A-15).

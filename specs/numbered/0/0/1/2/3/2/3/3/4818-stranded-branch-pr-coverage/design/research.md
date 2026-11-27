# Research: Stranded branch pull request coverage

This file holds the evidence, the decisions, the remote checks, the branch evidence, the sources, and the unverified items for issue 4818. Each claim cites a remote check (RC-###) or a source (S-#). The replica is a read-only reproduction of the report rule. It uses `gh api` reads only. The replica ran on 2026-11-26 against remote `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

## R1. Issue facts

- Issue 4818 has the title `chore(git): a branch holds work with no pull request`. It opened on 2026-11-16 and remains open. Its labels are `ci`, `chore`, and `in-progress` (RC-117, RC-055).
- The report workflow created the issue body. The body lists 54 branches. The author is `app/github-actions`.
- Eleven owner comments track a preservation campaign. The comments state that no branch was deleted and no pull request was opened in that phase.
- The only pull request that the search for `4818` returns is pull request #4819. It merged on 2026-11-16 (`gh pr list`, state `MERGED`).
- Pull request #4819 changed two test files only, according to the owner comments (S-5). It did not change the report or the workflows.

## R2. Scope evidence

The stranded set grew after the issue opened. The snapshots below come from the report output.

| Date | Source | Rows or count |
| - | - | - |
| 2026-11-16 | Issue 4818 body (RC-055) | 54 rows |
| 2026-11-23 | Issue 4911 body, from report run 45242632367 (RC-056, RC-057) | 505 rows |
| 2026-11-26 | Replica on remote `main` (RC-049) | 537 stranded branches |

The replica classified the 597 branch names other than `main`. The table below gives the counts. The counts sum to 597, because `main` is not counted (RC-047, RC-049).

| Class | Count | Rule |
| - | - | - |
| Ignored by prefix | 8 | Name starts with `dependabot/`, `gh-readonly-queue/`, or `revert-` (RC-041) |
| Not ahead of main | 11 | Zero commits above `main` (RC-042) |
| Quiet | 34 | Last commit is younger than 7 days (RC-040) |
| Protected by an open pull request | 2 | Open pull request names the branch head (RC-044) |
| Protected by a closed pull request | 5 | Closed pull request head holds every branch commit (RC-044) |
| Unreadable | 0 | Compare call failed |
| Stranded | 537 | None of the above applies |

Stranded branch breakdown:

| Group | Count | Note |
| - | - | - |
| Names in the issue 4818 body | 54 | All 54 remain stranded (RC-058 to RC-111) |
| `archive/laptop-20261121/` without `dependabot/` | 449 | Owner backup copies created on 2026-11-21 |
| `archive/laptop-20261121/dependabot/` | 16 | Backup copies of dependency branches |
| `recovery/` names outside the issue body | 16 | Not in the 54 rows |
| Other names outside the issue body | 2 | `jmorrison-juniper-capture-lock-holder-test-isolation`, `preserve/pr4823-before-rebase` |
| Other names in the issue body | 20 | Non-recovery names from RC-058 to RC-077 |

The 537 stranded branches carry 1,720 commits above `main`. The 54 issue names carry 206 of them. The 537 branches point to 526 distinct head commits. Two branches, `recovery/4208-original-before-review-fbb23f8` and `recovery/4208-pre-reconstruction-20261113`, share one head (RC-109, RC-110).

Open pull requests: 7 (RC-048). Two open pull requests protect a stranded branch. They are #4813 (2 commits above `main`) and #4208 (33 commits above `main`). The other five open pull requests have Dependabot heads, which the report ignores by prefix (RC-041).

## R3. Report rule

The installed report has these rules. The source file is `.venv\Lib\site-packages\misthelper_devtools\stranded_branch_report.py` in version 0.6.4 (RC-045). The documented rule matches it (RC-023, RC-025).

- A branch is stranded when it holds at least one commit above `main` (RC-042).
- A branch with an open pull request head does not count as stranded (RC-043).
- A bot prefix does not count as stranded (RC-041).
- A branch younger than the quiet period does not count as stranded (RC-040).
- A closed pull request protects a branch when the closed head holds every branch commit (RC-044).
- The report reads every remote branch name through `repos/{repository}/branches` (RC-039).

The report closes or updates the tracker issue. The reusable workflow at `79a5e45970e876f1656d69520d9635cea1aa25ef` searches open issues with its title (RC-035). It comments on the found issue, or it opens a new issue when none is found (RC-036). It closes the found issue when no branch needs a pull request (RC-037).

## R4. Tracker issue defect

The title search in the reusable workflow returns no open tracker. The same title in a quoted phrase returns all five open trackers.

- The reusable workflow query is `chore(git): a branch holds work with no pull request in:title`. It returns zero open issues (RC-053).
- The query `in:title "a branch holds work with no pull request"` returns issues 4911, 4818, 4719, 4583, and 4302 (RC-054).
- Five issues with the same title stay open: 4302, 4583, 4719, 4818, and 4911 (RC-052). The weekly runs on 2026-10-19, 2026-11-02, 2026-11-09, 2026-11-16, and 2026-11-23 each opened one issue with this title.
- The workflow cannot close issue 4818 while the query returns no open tracker (RC-037, RC-053).

Cause: the colon and the parentheses in the title break the search query. This finding is a defect in `misthelper-devtools`. The record treats the fix as a follow-up (FR-017).

## R5. Quality-gate issue effect

The pull request workflow `ci.yml` runs on every pull request, with no branch filter (RC-018). Its `quality_gate_issues` job calls the reusable quality-gate workflow (RC-019). The reusable workflow opens an issue for a failed gate on a pull request. The issue title names the pull request number (RC-038).

The repository has 18 open issues labelled `quality-gate` that name pull request numbers (RC-051). A single pull request can open several gate issues. The repository is public, so standard runners cost no minutes (RC-006, RC-050). The cost is the queue, the issue count, and the review noise.

## R6. Route verification

The route `0\0\1\2\3\2\3\3` is the eight-digit base-5 value of 4818.

- The function `Get-SpecRadixSegments` uses base 5 and width 8 (RC-009, RC-010, RC-011).
- The base-5 arithmetic gives the digits `0 0 1 2 3 2 3 3`. The formula is `4818 = 1 x 5^5 + 2 x 5^4 + 3 x 5^3 + 2 x 5^2 + 3 x 5 + 3`.
- The Python helper `python_route` in `tests/guardrails/test_spec_route_contract.py` uses the same arithmetic (RC-026).
- The route leaf holds no entry on remote `main` (RC-034).

## R7. Template deviation for the record pull request

The brief asks for a body that contains `Closes #4818`. This record does not use that text. A merged `Closes` line closes the tracker. The report then has no open tracker when it still names branches. The next weekly run opens a new tracker (RC-036). The record pull request uses `Refs #4818` instead. Decision D-8 records the reason.

## R8. External sources

- The secondary limits for content creation are 80 content-generating requests per minute and 500 per hour (S-2). The docs page for the REST rate limits links to this reusable text (S-4).
- Skip instructions apply to `push` and `pull_request` events (S-3). The documentation does not state whether a `[skip ci]` line in a pull request head commit prevents the pull request run. This item is unverified (U-2).

## R9. Scope exclusions

- Mist API and `mistapi`: Not applicable. The record makes no Mist endpoint claim and no SDK function claim.
- Skill tool: No skill loaded. The issue concerns git and GitHub state. It does not concern Podman or Juniper device behavior.
- Local gates: The record runs the Markdown gate, the process folder guard, the spec route guard, and the changelog fragment guard (quickstart.md).

## Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk. Decision D-12 is the only human decision.

### D-1 Scope of the rollout

- Alternatives:
  - (a) the 54 rows in the issue body.
  - (b) the 505 rows of the 2026-11-23 report.
  - (c) the live report at each batch start.
  - (d) one branch named by the orchestrator message.
- Chosen: (c). The report rule is the documented authority (RC-023). Snapshots went stale: 54, then 505, then 537.
- Risk: The scope grows between approval and each batch. Mitigation: rerun the replica before each batch (tasks T011, T012).
- Human decision: no.

### D-2 Protection mechanism

- Alternatives: (a) pushed annotated tags, (b) owner bundles and archive branches (the current owner method), (c) one draft pull request for each stranded branch.
- Chosen: (c). The report counts only pull requests (RC-043, RC-044). Tags and bundles do not clear the report. The documented rule requires a pull request (RC-023, RC-025).
- Risk: CI and issue load (D-5, D-6). Protection depends on GitHub keeping `refs/pull/<n>/head` (RC-025).
- Human decision: no.

### D-3 State of each preservation pull request

- Alternatives:
  - (a) close each pull request after it opens.
  - (b) mark each pull request ready for review.
  - (c) keep each pull request as a draft until the owner decides its disposition.
- Chosen: (c). An open pull request protects the head (RC-043). Closing needs a preservation proof in the closing comment (RC-002). A draft cannot receive a review request, and no agent adds the auto-merge label (RC-020).
- Risk: 537 open drafts make the pull request list long. Mitigation: the owner campaign sets each disposition.
- Human decision: no.

### D-4 Content and labels of each preservation pull request

- Alternatives:
  - (a) reuse the report row as the body.
  - (b) write `Closes #4818` in each body.
  - (c) write `Refs #4818` with a fixed body.
  - (d) add no labels.
- Chosen: (c) with labels `chore` and `ci`. Labels match the tracker (RC-117). `Refs` does not close the tracker. A merged `Closes` line would close the tracker on merge. Preservation pull requests do not merge, but the wording stays the same across all pull requests.
- Title form: `chore(git): preserve the head of` followed by the branch name. The form passes the Conventional Commits check, and RC-112 quotes the accepted forms in the repository instructions.
- Risk: A branch name with unusual characters breaks the title form. Mitigation: all 537 names use ASCII letters, digits, slashes, hyphens, and periods.
- Human decision: no.

### D-5 Pace of the rollout

- Alternatives:
  - (a) all 537 pull requests at once.
  - (b) batches of 50.
  - (c) a pilot of five, then batches of 10. Each batch completes before the next.
  - (d) batches of one.
- Chosen: (c). The content limit of 500 per hour blocks a burst of 537 (S-2). A batch of 10 bounds the concurrent runs. A batch of one takes too long for the owner review.
- Risk: The full rollout takes many hours. Mitigation: the owner approves the volume (D-12).
- Human decision: no. D-12 covers the volume.

### D-6 Handling of quality-gate issues

- Alternatives:
  - (a) change `ci.yml` to skip preservation pull requests.
  - (b) add `[skip ci]` to each branch head.
  - (c) run CI as it runs now and measure the pilot.
  - (d) disable the gates.
- Chosen: (c). Option (a) changes a shared required-check workflow (RC-018). That change needs its own issue. Option (b) rewrites a branch head, which the rules forbid (FR-004). Option (d) stops work for the whole repository.
- Risk: Many gate issues open. Mitigation: the pilot counts gate issues (T007), and the owner closes each issue after the disposition.
- Human decision: no. D-12 covers the volume.

### D-7 Tracker issue and duplicates

- Alternatives:
  - (a) close issue 4818 now.
  - (b) let the report close issue 4818.
  - (c) keep issue 4818 open until the replica finds no stranded branch. Then the owner closes it and the four duplicates.
  - (d) change the reusable workflow in this issue.
- Chosen: (c). Option (a) causes a new tracker on the next run (RC-036). Option (b) cannot work with the current query (RC-053). Option (d) changes another repository (FR-016, FR-017).
- Risk: Four duplicate trackers stay open for a while. Mitigation: the owner closes them after authorization (T019).
- Human decision: no.

### D-8 Record pull request wording and changelog fragment

- Alternatives: (a) use the `Closes` line from the brief, (b) use `Refs #4818`, (c) add no changelog fragment, (d) add one fragment.
- Chosen: (b) and (d). A merged `Closes` line closes the tracker early (R7). The constitution says each change adds one fragment (RC-113), and the changelog README says each change owns one file (RC-031). The repository instructions narrow the rule to user-visible changes. This record follows the stricter rule.
- Risk: A reviewer may read the fragment as noise. Mitigation: the fragment names issue 4818 and uses the `Changed` heading.
- Human decision: no.

### D-9 Boundary of the repository change

- Alternatives:
  - (a) change `ci.yml` or the reusable workflow in this issue.
  - (b) align the devtools pin in this issue.
  - (c) add only the record and one fragment.
- Chosen: (c). The repository rules require one concern for each issue (RC-004 cites the issue-first rule in AGENTS.md). Options (a) and (b) need separate issues (T021, T022).
- Risk: The defects stay open for longer. Mitigation: the analysis names each defect with its evidence.
- Human decision: no.

### D-10 Local-only branches

- Alternatives:
  - (a) push local-only branches so the report names them.
  - (b) leave them out without a record.
  - (c) list them as out of scope and forbid a push.
- Chosen: (c). The report reads remote names only (RC-039). A push to a public repository makes the content visible. The owner excluded two private-corpus branches on 2026-11-16 (issue 4818 comments). The branch names do not identify them.
- Risk: The owner must identify the two branches before any later action. Mitigation: task T023 checks for a 404 on each name the owner provides.
- Human decision: no.

### D-11 Branch deletion

- Alternatives: (a) delete each stranded branch after its pull request opens, (b) delete the archive copies at once, (c) delete nothing in this issue.
- Chosen: (c). The owner campaign classifies each branch first. The documentation allows a deletion only after a pull request exists (RC-024).
- Risk: The remote branch count stays high. Mitigation: the owner campaign sets the later disposition.
- Human decision: no.

### D-12 Approval of the rollout volume

- Alternatives:
  - (a) approve the full 537 pull request rollout after the pilot passes.
  - (b) approve the oldest 100 pull requests and decide again.
  - (c) defer the rollout and keep the owner bundles as the only protection.
- Chosen recommendation: (a), after the pilot passes its stop rule. Option (b) is the fallback when the pilot shows heavy gate-issue churn.
- Reason for the human decision: The rollout creates 537 pull requests, 537 CI runs, and gate issues on a shared public repository. The owner sets the priority of shared CI capacity.
- Risk: The rollout waits for the owner. Mitigation: the tracker keeps the pilot result, and no other task depends on the rollout.
- Human decision: yes. The decision category is product priority.

## Remote verification table

Rows RC-001 to RC-057 are file, workflow, route, and live-state checks. Rows RC-058 to RC-111 are one check for each branch in the issue body. The claim for each branch row is that the branch holds commits above `main` and has no pull request. Rows RC-112 to RC-118 check the title rule, changelog rules, container build trigger, escalation rule, STE gate, tracker labels, and user-visible changelog rule. The count of rows is 118. The same count appears in `4818-STATUS.json` and in `4818-summary.md`.

| ID | Claim | Path or object | Ref | Blob or object SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-001 | AGENTS.md states the rule to preserve work before closing an unmerged pull request | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 271 |
| RC-002 | AGENTS.md accepts a pushed tag as a preservation proof | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 275 |
| RC-003 | AGENTS.md states that a merged body with Closes closes the issue | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 224 |
| RC-004 | AGENTS.md requires an issue claim before a branch | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 187 |
| RC-005 | Repository instructions list the stranded report workflow | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 475 |
| RC-006 | Repository instructions state that the repository is public | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 478 |
| RC-007 | Constitution requires managed roots for new specs records | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 57 |
| RC-008 | Constitution forbids a feature workflow push to main | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 173 |
| RC-009 | Route script defines the radix segment function | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 4 |
| RC-010 | Route script default width is eight | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| RC-011 | Route script base is five | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-012 | Spec template exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| RC-013 | Plan template exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| RC-014 | Tasks template states the delivered evidence rule | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 25 |
| RC-015 | Checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| RC-016 | Stranded report workflow runs on a weekly cron | .github/workflows/stranded-branch-report.yml | main | 0fde8b4e98edcc111425e3a385e42075cf43595f | present | 20 |
| RC-017 | Stranded report workflow calls the reusable workflow at 79a5e45 | .github/workflows/stranded-branch-report.yml | main | 0fde8b4e98edcc111425e3a385e42075cf43595f | present | 47 |
| RC-018 | CI runs on every pull request with no branch filter | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 16 |
| RC-019 | CI calls the reusable quality-gate issue workflow at 79a5e45 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1317 |
| RC-020 | Auto-merge workflow uses the auto-merge label | .github/workflows/auto-merge.yml | main | 9d26134dd84cf50008a17fd878772102ce355983 | present | 14 |
| RC-021 | Close-linked-issues workflow runs on pull request events | .github/workflows/close-linked-issues.yml | main | 42a085ac6240518b028862c290ec9502a5b13b2a | present | 4 |
| RC-022 | Pull request template exists | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 5 |
| RC-023 | Contributing guide says to open a pull request for every branch the report names | documentation/contributing.md | main | 3b455b6d6730e16972540f14f7f654462b1c27bd | present | 76 |
| RC-024 | Contributing guide says to delete a branch only after its pull request exists | documentation/contributing.md | main | 3b455b6d6730e16972540f14f7f654462b1c27bd | present | 79 |
| RC-025 | Stranded review says to open a pull request before any cleanup | documentation/stranded-branch-review.md | main | 8091539c31ff8648d0426f4a8a92e01e0eb902b4 | present | 46 |
| RC-026 | Route contract test defines python_route | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 33 |
| RC-027 | Planning guard lists the required planning files | tests/guardrails/test_labs_planning_record.py | main | 0fb295333256e4f468d17832d681c0f7d954ed14 | present | 12 |
| RC-028 | Folder guard names the numbered records | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 26 |
| RC-029 | Folder baseline file exists | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| RC-030 | Development requirements pin misthelper-devtools at 2239e7b | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 197 |
| RC-031 | Changelog README says each change owns one file | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 3 |
| RC-032 | Reference record spec exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-033 | Reference record research exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/research.md | main | 2e4aaa714e56fff7f96a2af9e686e9f5c06224a7 | present | 0 |
| RC-034 | Route leaf for 4818 holds no entry | specs/numbered/0/0/1/2/3/2/3/3 | main | none | absent | 0 |
| RC-035 | Reusable report searches open issues by title | misthelper-devtools .github/workflows/reusable-stranded-branch-report.yml at 79a5e45 | 79a5e45970e876f1656d69520d9635cea1aa25ef | b8ca235c93beddef9307d797da87223a920df729 | present | 156 |
| RC-036 | Reusable report opens a new tracker when no open tracker is found | misthelper-devtools .github/workflows/reusable-stranded-branch-report.yml at 79a5e45 | 79a5e45970e876f1656d69520d9635cea1aa25ef | b8ca235c93beddef9307d797da87223a920df729 | present | 174 |
| RC-037 | Reusable report closes the tracker only when no branch needs a pull request | misthelper-devtools .github/workflows/reusable-stranded-branch-report.yml at 79a5e45 | 79a5e45970e876f1656d69520d9635cea1aa25ef | b8ca235c93beddef9307d797da87223a920df729 | present | 178 |
| RC-038 | Reusable quality-gate workflow titles a pull request issue with its number | misthelper-devtools .github/workflows/reusable-quality-gate-issues.yml at 79a5e45 | 79a5e45970e876f1656d69520d9635cea1aa25ef | 9a46074e9baee83afb3405d7c51fd4e21797f17c | present | 123 |
| RC-039 | Installed report lists every remote branch | .venv\Lib\site-packages\misthelper_devtools\stranded_branch_report.py (local, version 0.6.4) | installed | none | present | 161 |
| RC-040 | Installed report uses a quiet period of 7 days | .venv\Lib\site-packages\misthelper_devtools\stranded_branch_report.py (local) | installed | none | present | 49 |
| RC-041 | Installed report ignores three bot prefixes | .venv\Lib\site-packages\misthelper_devtools\stranded_branch_report.py (local) | installed | none | present | 53 |
| RC-042 | Installed report requires at least one commit above main | .venv\Lib\site-packages\misthelper_devtools\stranded_branch_report.py (local) | installed | none | present | 102 |
| RC-043 | Installed report exempts a branch with an open pull request head | .venv\Lib\site-packages\misthelper_devtools\stranded_branch_report.py (local) | installed | none | present | 96 |
| RC-044 | Installed report exempts a branch held by a closed pull request | .venv\Lib\site-packages\misthelper_devtools\stranded_branch_report.py (local) | installed | none | present | 192 |
| RC-045 | Installed package version is 0.6.4 | .venv\Lib\site-packages\misthelper_devtools-0.6.4.dist-info\METADATA (local) | installed | none | present | 3 |
| RC-046 | Remote main head is f03c6c9 | refs/heads/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-047 | Remote lists 598 branch names | refs/heads (all names) | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-048 | Remote lists 7 open pull requests | pulls with state open | main | none | present | 0 |
| RC-049 | Replica classes sum to 597 without main, with 537 stranded | replica output on 2026-11-26 | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-050 | Repository is public and its default branch is main | repository metadata | main | none | present | 0 |
| RC-051 | Open issues labelled quality-gate number 18 | issues with label quality-gate | live | none | present | 0 |
| RC-052 | Five open issues carry the report title | issues 4302, 4583, 4719, 4818, 4911 | live | none | present | 0 |
| RC-053 | The reusable query returns zero open trackers | issue search with the reusable query | live | none | present | 0 |
| RC-054 | A quoted phrase returns five open trackers | issue search with the quoted phrase | live | none | present | 0 |
| RC-055 | Issue 4818 body lists 54 rows | issue 4818 body | live | none | present | 0 |
| RC-056 | Issue 4911 body lists 505 rows | issue 4911 body | live | none | present | 0 |
| RC-057 | Latest weekly report run succeeded on 2026-11-23 | workflow run 45242632367 | live | 45242632367 | present | 0 |
| RC-058 | docs/3818-campaign-stop-20261004 holds 1 commit above main with no pull request | refs/heads/docs/3818-campaign-stop-20261004 | main | 8c3e6cacc6d101c3b4356369f94b2f50039f987b | present | 0 |
| RC-059 | fix/3158-wip-controls holds 1 commit above main with no pull request | refs/heads/fix/3158-wip-controls | main | 0f6b375e71243311b5cf5856fe9f220842a14e3b | present | 0 |
| RC-060 | fix/3168-structured-signals holds 1 commit above main with no pull request | refs/heads/fix/3168-structured-signals | main | 69d19411fbc13c0b0ab55b10d49ae7ec177024c0 | present | 0 |
| RC-061 | fix/3183-status-fallback holds 1 commit above main with no pull request | refs/heads/fix/3183-status-fallback | main | 0c46332ad00b2c9131f29fba218400ba7ece8f51 | present | 0 |
| RC-062 | fix/3222-confirm-details holds 1 commit above main with no pull request | refs/heads/fix/3222-confirm-details | main | 18138f9b28173c969a57d447291ffebcd6daa029 | present | 0 |
| RC-063 | fix/3292-isolate-retry-e2e-sites holds 2 commits above main with no pull request | refs/heads/fix/3292-isolate-retry-e2e-sites | main | f706902a5af34e272583b45686fd60b4e1225fed | present | 0 |
| RC-064 | fix/3506-site-lock-logs holds 1 commit above main with no pull request | refs/heads/fix/3506-site-lock-logs | main | 8c8fc28d452126a0e42c98040f8edf56d11a412f | present | 0 |
| RC-065 | jmorrison-jnpr-snmp-fallback-delivery holds 1 commit above main with no pull request | refs/heads/jmorrison-jnpr-snmp-fallback-delivery | main | 73a1edaa973b4fb5110d9d3607377e42773d8445 | present | 0 |
| RC-066 | jmorrison-jnpr-test-4035-menu-92-selection-result holds 1 commit above main with no pull request | refs/heads/jmorrison-jnpr-test-4035-menu-92-selection-result | main | 9851ed28ced6f6d0909fe529e0a8f43c1a412bed | present | 0 |
| RC-067 | jmorrison-juniper-assessment-4026 holds 3 commits above main with no pull request | refs/heads/jmorrison-juniper-assessment-4026 | main | 83d197e30fd9519521697154036eadf4e52a2850 | present | 0 |
| RC-068 | jmorrison-juniper-coordinate-issue-work holds 1 commit above main with no pull request | refs/heads/jmorrison-juniper-coordinate-issue-work | main | 29c5489751ed84a8595cefe85f0e2aa7716b8608 | present | 0 |
| RC-069 | jmorrison-juniper-false-success-family-4028 holds 2 commits above main with no pull request | refs/heads/jmorrison-juniper-false-success-family-4028 | main | 4be5f321a3ba26c136c541e062c7aa4e7442aae9 | present | 0 |
| RC-070 | jmorrison-juniper-fix-2863-identifier-defaults-batch-1 holds 1 commit above main with no pull request | refs/heads/jmorrison-juniper-fix-2863-identifier-defaults-batch-1 | main | 6eec0e4bf09a6ca5deb1bb78c008337bab6e7464 | present | 0 |
| RC-071 | jmorrison-juniper-fix-4494-csrf-warning-prefix holds 1 commit above main with no pull request | refs/heads/jmorrison-juniper-fix-4494-csrf-warning-prefix | main | 862f1a8ce6254fa836a780623b462d3140c35292 | present | 0 |
| RC-072 | jmorrison-juniper-issue-2746 holds 2 commits above main with no pull request | refs/heads/jmorrison-juniper-issue-2746 | main | 4ebe402c19de77a546960896ef70bb3286860f13 | present | 0 |
| RC-073 | jmorrison-juniper-issue-2747-wan-probe-test-quality holds 1 commit above main with no pull request | refs/heads/jmorrison-juniper-issue-2747-wan-probe-test-quality | main | db030903fb77beca6c57d7bb10f356cbc290bd58 | present | 0 |
| RC-074 | jmorrison-juniper-issue-3416-lint-pattern holds 2 commits above main with no pull request | refs/heads/jmorrison-juniper-issue-3416-lint-pattern | main | 3d51242e41f2815bbcaeaa076a2c1e60b2fd9550 | present | 0 |
| RC-075 | jmorrison-juniper-issue-4269-runtime-nested-feature-identity-in-speck-4a6090 holds 1 commit above main with no pull request | refs/heads/jmorrison-juniper-issue-4269-runtime-nested-feature-identity-in-speck-4a6090 | main | d8a7b9c71583668b7284c81ab69cc9f1a5dbba78 | present | 0 |
| RC-076 | jmorrison-juniper-local-build-revision holds 1 commit above main with no pull request | refs/heads/jmorrison-juniper-local-build-revision | main | c80f23510a679985f9892ee59f0c181a8cdaa953 | present | 0 |
| RC-077 | jmorrison-juniper-startup-dependency-reassessment holds 3 commits above main with no pull request | refs/heads/jmorrison-juniper-startup-dependency-reassessment | main | e849f3fe4e0734f54de76a0b171390674555ca2b | present | 0 |
| RC-078 | recovery/2708-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/2708-handoff-20261004 | main | f195788a090d6ace8f2f320dc1f96a413876e2c4 | present | 0 |
| RC-079 | recovery/2711-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/2711-handoff-20261004 | main | 9e943bfe30d9ab4513ba1d595e844fd8c1c080d0 | present | 0 |
| RC-080 | recovery/2747-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/2747-handoff-20261004 | main | 2d5695fb4ed00411e5dbaf0d2b03539e3aff4863 | present | 0 |
| RC-081 | recovery/2752-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/2752-handoff-20261004 | main | 024d42ff7f840becd7583433d502fbdf453594a3 | present | 0 |
| RC-082 | recovery/2861-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/2861-handoff-20261004 | main | 6cea98a9794d87e0ed3738bf331afff51280f76c | present | 0 |
| RC-083 | recovery/2863-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/2863-handoff-20261004 | main | 188956f937019a0e07cab73919ebd289179c5def | present | 0 |
| RC-084 | recovery/2977-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/2977-handoff-20261004 | main | d6e8eb8672edfa1c5123df03294ecd8daa98a051 | present | 0 |
| RC-085 | recovery/3158-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/3158-handoff-20261004 | main | ecb0bc87ceafe3f5024d678bdc99ad4b159fad7c | present | 0 |
| RC-086 | recovery/3161-handoff-20261004 holds 2 commits above main with no pull request | refs/heads/recovery/3161-handoff-20261004 | main | 33141f05cd19c509f723c57534edd2900b4ecde3 | present | 0 |
| RC-087 | recovery/3213-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/3213-handoff-20261004 | main | 8090bc7d195407ecafe62fd16f38847ae18b5170 | present | 0 |
| RC-088 | recovery/3295-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/3295-handoff-20261004 | main | b1fe853fb26f4f4c7efd82148e5af14084a313ae | present | 0 |
| RC-089 | recovery/3326-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/3326-handoff-20261004 | main | fa25a39cd3d77a9a9fc4c5d5327ba9c2e6c1c499 | present | 0 |
| RC-090 | recovery/3329-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/3329-handoff-20261004 | main | 7332749c6cf0344a2e7fdcbe02e1948f450d6b2c | present | 0 |
| RC-091 | recovery/3375-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/3375-handoff-20261004 | main | 499b764f16fee9a465c9c789f3806ad9c0cdae1c | present | 0 |
| RC-092 | recovery/3380-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/3380-handoff-20261004 | main | a3af99af23ba29e31725673a87e0f771293ba985 | present | 0 |
| RC-093 | recovery/3388-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/3388-handoff-20261004 | main | ea0a7467b81b297580f7a264658bd15fbf442c1e | present | 0 |
| RC-094 | recovery/3436-handoff-20261004 holds 2 commits above main with no pull request | refs/heads/recovery/3436-handoff-20261004 | main | 0a032e83ab7cde0faec752258971df7b6b657d0c | present | 0 |
| RC-095 | recovery/3491-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/3491-handoff-20261004 | main | 97139eb2c6dc667d456c2fce420f8c57f6c67025 | present | 0 |
| RC-096 | recovery/3575-handoff-20261004 holds 2 commits above main with no pull request | refs/heads/recovery/3575-handoff-20261004 | main | 5746418f8cd77fa1ccd6cc004fd5f07a20ddaffb | present | 0 |
| RC-097 | recovery/3699-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/3699-handoff-20261004 | main | c0261d9fba897fb6339c46d26e465bcc3703ac1d | present | 0 |
| RC-098 | recovery/3700-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/3700-handoff-20261004 | main | f253dd3b5533b63f0e75047e3fb918d976311b58 | present | 0 |
| RC-099 | recovery/3701-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/3701-handoff-20261004 | main | d2d2421da64d7884f7988321197dec066accb9f7 | present | 0 |
| RC-100 | recovery/3728-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/3728-handoff-20261004 | main | 533ced96928dd51dc68a139d20c9476d08e87eb8 | present | 0 |
| RC-101 | recovery/3738-handoff-20261004 holds 2 commits above main with no pull request | refs/heads/recovery/3738-handoff-20261004 | main | c70007d407c5cd58ef08901832806120175d49b3 | present | 0 |
| RC-102 | recovery/3743-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/3743-handoff-20261004 | main | 4ecd16c7e409e88899e46b105e5ec0b3e67b875c | present | 0 |
| RC-103 | recovery/3745-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/3745-handoff-20261004 | main | 50e3d841dfbbcfb89fd0b419ce5631c5bd1068bd | present | 0 |
| RC-104 | recovery/3749-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/3749-handoff-20261004 | main | 9f930182fa5349ebf59fac3e8c9830327f4116b4 | present | 0 |
| RC-105 | recovery/3760-handoff-20261004 holds 2 commits above main with no pull request | refs/heads/recovery/3760-handoff-20261004 | main | 12f10ece0901452bd71eb1baa563ee77de5687db | present | 0 |
| RC-106 | recovery/3761-handoff-20261004 holds 1 commit above main with no pull request | refs/heads/recovery/3761-handoff-20261004 | main | ebc40dac8dcb47b0c835bf45b7474dde1732669f | present | 0 |
| RC-107 | recovery/3769-handoff-20261004 holds 2 commits above main with no pull request | refs/heads/recovery/3769-handoff-20261004 | main | 54188ffcaffc18e3d5ced162fc64ef1762a90b70 | present | 0 |
| RC-108 | recovery/3818-handoff-20261004 holds 2 commits above main with no pull request | refs/heads/recovery/3818-handoff-20261004 | main | 0bb3149476b5658f8dc9ce44661d4c90dadc3669 | present | 0 |
| RC-109 | recovery/4208-original-before-review-fbb23f8 holds 42 commits above main with no pull request | refs/heads/recovery/4208-original-before-review-fbb23f8 | main | fbb23f8a2348e6840caf479dc10d8841635ea91e | present | 0 |
| RC-110 | recovery/4208-pre-reconstruction-20261113 holds 42 commits above main with no pull request | refs/heads/recovery/4208-pre-reconstruction-20261113 | main | fbb23f8a2348e6840caf479dc10d8841635ea91e | present | 0 |
| RC-111 | recovery/4358-pre-reconstruction-20261113 holds 56 commits above main with no pull request | refs/heads/recovery/4358-pre-reconstruction-20261113 | main | b1c4998f00b141d65e7a0bb3188f394f1d6c7e90 | present | 0 |
| RC-112 | Repository instructions define the four accepted pull request title forms | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 507 |
| RC-113 | Constitution requires one changelog fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| RC-114 | Container build workflow starts only for product file changes | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 473 |
| RC-115 | Constitution requires a specification for a change that touches three or more files | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 431 |
| RC-116 | Local gates table lists the STE gate command | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| RC-117 | Issue 4818 carries the labels ci, chore, and in-progress | issue 4818 labels | live | none | present | 0 |
| RC-118 | Repository instructions limit the changelog fragment rule to a change that a user sees | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |

## Branch evidence for the issue body names

The table gives the commits above `main`, the files changed against `main`, the age in days, and the head subject. The commit counts match the replica. The file counts come from `git diff --name-only` with the local objects for `main` and each branch. No checkout occurred. Rows follow the same order as RC-058 to RC-111.

| Row | Branch | Commits above main | Files changed | Age in days | Head subject |
| - | - | - | - | - | - |
| RC-058 | docs/3818-campaign-stop-20261004 | 1 | 1 | 53 | docs(handoff): preserve the paused repair campaign |
| RC-059 | fix/3158-wip-controls | 1 | 7 | 58 | chore(web-portal): keep the uncommitted draft of #3158 [skip ci] |
| RC-060 | fix/3168-structured-signals | 1 | 4 | 58 | chore(web-portal): keep the uncommitted draft of #3168 [skip ci] |
| RC-061 | fix/3183-status-fallback | 1 | 10 | 58 | chore(web-portal): keep the uncommitted draft of #3183 [skip ci] |
| RC-062 | fix/3222-confirm-details | 1 | 7 | 57 | fix(upgrade-portal): show complete confirmation plan |
| RC-063 | fix/3292-isolate-retry-e2e-sites | 2 | 6 | 53 | fix(upgrade-portal): order retry imports |
| RC-064 | fix/3506-site-lock-logs | 1 | 3 | 57 | fix(upgrade-portal): record site lock actions and refusals |
| RC-065 | jmorrison-jnpr-snmp-fallback-delivery | 1 | 3 | 57 | fix(snmp): align the container base OID fallback |
| RC-066 | jmorrison-jnpr-test-4035-menu-92-selection-result | 1 | 5 | 50 | test(web-portal): record menu 92 completion defect |
| RC-067 | jmorrison-juniper-assessment-4026 | 3 | 12 | 50 | docs(spec): record issue 4026 validation |
| RC-068 | jmorrison-juniper-coordinate-issue-work | 1 | 3 | 50 | fix(org): handle http refusal in org name lookup |
| RC-069 | jmorrison-juniper-false-success-family-4028 | 2 | 12 | 50 | test(export): strengthen client abort assertion |
| RC-070 | jmorrison-juniper-fix-2863-identifier-defaults-batch-1 | 1 | 13 | 50 | fix(upgrade-portal): refuse missing scope identifiers |
| RC-071 | jmorrison-juniper-fix-4494-csrf-warning-prefix | 1 | 1 | 28 | test(upgrade-portal): wait for the accessible CSRF warning |
| RC-072 | jmorrison-juniper-issue-2746 | 2 | 42 | 50 | test: preserve HTTP proof symbols |
| RC-073 | jmorrison-juniper-issue-2747-wan-probe-test-quality | 1 | 1 | 37 | test(gateway): cover HTTP 503 template refusal |
| RC-074 | jmorrison-juniper-issue-3416-lint-pattern | 2 | 1 | 50 | test(docs): hold complete diagram reference names |
| RC-075 | jmorrison-juniper-issue-4269-runtime-nested-feature-identity-in-speck-4a6090 | 1 | 8 | 40 | fix(specs): remove nested duplicate feature record |
| RC-076 | jmorrison-juniper-local-build-revision | 1 | 13 | 26 | fix(container): label local builds with their source revision |
| RC-077 | jmorrison-juniper-startup-dependency-reassessment | 3 | 18 | 51 | fix(upgrade-portal): build request dependencies lazily |
| RC-078 | recovery/2708-handoff-20261004 | 1 | 1 | 53 | test(mist): assert the complete list error text |
| RC-079 | recovery/2711-handoff-20261004 | 1 | 1 | 55 | test(export): require the error record for template failures |
| RC-080 | recovery/2747-handoff-20261004 | 1 | 1 | 54 | test(ssh): verify native CLI shell refusals |
| RC-081 | recovery/2752-handoff-20261004 | 1 | 9 | 55 | fix(api): preserve HTTP status in retry diagnostics |
| RC-082 | recovery/2861-handoff-20261004 | 1 | 11 | 55 | fix(mist-session): reject unusable required tokens |
| RC-083 | recovery/2863-handoff-20261004 | 1 | 8 | 55 | fix(api): refuse invalid tenant request identifiers |
| RC-084 | recovery/2977-handoff-20261004 | 1 | 24 | 55 | fix(juniper-docs): prevent duplicate corpus payload writes |
| RC-085 | recovery/3158-handoff-20261004 | 1 | 18 | 54 | fix(web-portal): add WIP target controls and result guidance |
| RC-086 | recovery/3161-handoff-20261004 | 2 | 9 | 54 | test(web-portal): cover stale clipping frame race |
| RC-087 | recovery/3213-handoff-20261004 | 1 | 13 | 55 | fix(upgrade-portal): document the stable capture session signing key |
| RC-088 | recovery/3295-handoff-20261004 | 1 | 16 | 55 | fix(upgrade-portal): repair the sign-in credential layout |
| RC-089 | recovery/3326-handoff-20261004 | 1 | 16 | 55 | fix(upgrade-portal): hide the failure percentage for Big bang |
| RC-090 | recovery/3329-handoff-20261004 | 1 | 8 | 55 | fix(upgrade-portal): count targets of known refused children |
| RC-091 | recovery/3375-handoff-20261004 | 1 | 12 | 54 | fix(tests): align capture seeds with lifecycle contracts |
| RC-092 | recovery/3380-handoff-20261004 | 1 | 7 | 54 | fix(upgrade-portal): verify capture click journey controls |
| RC-093 | recovery/3388-handoff-20261004 | 1 | 14 | 54 | fix(upgrade-portal): refuse unsafe option number tokens |
| RC-094 | recovery/3436-handoff-20261004 | 2 | 27 | 55 | fix(upgrade-portal): keep paged read results passive |
| RC-095 | recovery/3491-handoff-20261004 | 1 | 14 | 54 | fix(upgrade-portal): keep history records compact |
| RC-096 | recovery/3575-handoff-20261004 | 2 | 39 | 55 | test(websockets): prove failed capture response bodies |
| RC-097 | recovery/3699-handoff-20261004 | 1 | 18 | 55 | fix(export): retain documented SLE trend objects |
| RC-098 | recovery/3700-handoff-20261004 | 1 | 13 | 55 | fix(export): reject native Cradlepoint HTTP refusals |
| RC-099 | recovery/3701-handoff-20261004 | 1 | 10 | 55 | fix(bootstrap): preserve macOS interpreter library paths |
| RC-100 | recovery/3728-handoff-20261004 | 1 | 2 | 55 | test(web-portal): skip Maps title collection when Playwright is absent |
| RC-101 | recovery/3738-handoff-20261004 | 2 | 9 | 53 | test(export): preserve CSV suffix qualification WIP |
| RC-102 | recovery/3743-handoff-20261004 | 1 | 14 | 54 | fix(export): reject failed WiFi response pages |
| RC-103 | recovery/3745-handoff-20261004 | 1 | 13 | 54 | fix(export): refuse failed organization webhook responses |
| RC-104 | recovery/3749-handoff-20261004 | 1 | 1 | 54 | test(scripts): use native title guard path expectations |
| RC-105 | recovery/3760-handoff-20261004 | 2 | 2 | 54 | test(websocket_streams): correct the loopback client response handling |
| RC-106 | recovery/3761-handoff-20261004 | 1 | 5 | 54 | test(websocket): structure shell log assertions |
| RC-107 | recovery/3769-handoff-20261004 | 2 | 9 | 54 | fix(websocket): freeze cleanup terminal decisions |
| RC-108 | recovery/3818-handoff-20261004 | 2 | 1 | 53 | test(export): assert Cradlepoint status behavior |
| RC-109 | recovery/4208-original-before-review-fbb23f8 | 42 | 67 | 19 | docs(wan): distinguish external source paths |
| RC-110 | recovery/4208-pre-reconstruction-20261113 | 42 | 67 | 19 | docs(wan): distinguish external source paths |
| RC-111 | recovery/4358-pre-reconstruction-20261113 | 56 | 470 | 27 | docs(test): record firmware move quality gate |

The 54 names carry 206 commits above `main` in total. Each of the three branches with 42 or more commits lists its commits with `git log --no-merges main..$branch` in quickstart.md.

## Sources

- S-1 Installed report source: `.venv\Lib\site-packages\misthelper_devtools\stranded_branch_report.py`, version 0.6.4, local file.
- S-2 Secondary rate limits for content creation: https://github.com/github/docs/blob/main/data/reusables/rest-api/secondary-rate-limit-rest-graphql.md (read through `gh api` from the `github/docs` repository at `main`).
- S-3 Skip instructions for workflow runs: https://github.com/github/docs/blob/main/content/actions/how-tos/manage-workflow-runs/skip-workflow-runs.md (read through `gh api`).
- S-4 REST rate limits page: https://github.com/github/docs/blob/main/content/rest/using-the-rest-api/rate-limits-for-the-rest-api.md (read through `gh api`). The docs.github.com page did not load from the fetch tool, so the source file serves this record.
- S-5 Tracker issue 4818: https://github.com/jmorrison-juniper/MistHelper/issues/4818
- S-6 Tracker issue 4911, the 2026-11-23 report: https://github.com/jmorrison-juniper/MistHelper/issues/4911
- S-7 Reusable report workflow at 79a5e45: https://github.com/jmorrison-juniper/misthelper-devtools/blob/79a5e45970e876f1656d69520d9635cea1aa25ef/.github/workflows/reusable-stranded-branch-report.yml
- S-8 Reusable quality-gate workflow at 79a5e45: https://github.com/jmorrison-juniper/misthelper-devtools/blob/79a5e45970e876f1656d69520d9635cea1aa25ef/.github/workflows/reusable-quality-gate-issues.yml
- S-9 Repository files at `main`: AGENTS.md, .github/copilot-instructions.md, .specify/memory/constitution.md, .specify/scripts/powershell/spec-route.ps1, documentation/contributing.md, documentation/stranded-branch-review.md, and the other paths in RC-001 to RC-045.

## Unverified

- U-1 The content-creation limit applies to each pull request creation at the same rate as the documented content limit. The docs state the limit for content-generating requests. The rate for pull request creation was not tested.
- U-2 A `[skip ci]` line in the head commit of a pull request prevents the `pull_request` run. The skip page states the rule for `pull_request` events (S-3). The head commit case was not tested. The branch heads with the skip line are RC-059, RC-060, and RC-061.
- U-3 The two private-corpus branches that the owner excluded from review. The owner did not name them in issue 4818. Their identity and remote status are unknown.
- U-4 GitHub accepts two pull requests with one head commit. Branches RC-109 and RC-110 share a head. The pilot does not test this case.
- U-5 The quality-gate issue count per preservation pull request. The count depends on each branch content and was not measured. The pilot measures it (T007).
- U-6 The reusable workflow closes or reopens the tracker as the code reads. The workflow was not run. Its search behavior was tested through `gh issue list` only.
- U-7 The owner intent for the 434 archive backup copies counted in the 2026-11-23 snapshot. The owner did not state a disposition for them.
- U-8 The reason for the growth from 505 rows on 2026-11-23 to 537 stranded branches on 2026-11-26. The record did not trace each branch to its cause.

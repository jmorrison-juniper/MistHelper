# Research: Stranded branch preservation

This research uses remote evidence first. It reads GitHub with `gh api`, `gh pr`, and `git ls-remote`, and it reads the pinned upstream files at commit `79a5e45970e876f1656d69520d9635cea1aa25ef`. Local git commands show commits and files without a checkout. The remote main commit on 2026-11-26 is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

Mist API material does not apply. The change makes no Mist API call, so the OpenAPI file, the endpoint catalogs, and the `mistapi` source are not cited. No local skill applies. The change concerns Git refs and GitHub workflows, not Podman or Juniper devices.

## R1. What the report names

The issue names no file, symbol, or test. Its named objects are branches. No pull request links to issue 4911, because `gh pr list --state all --search 4911` returned no record. No folder under `specs` starts with `4911-`, so no legacy record exists and the record starts new.

The report in issue 4911 was created on 2026-11-23 by the `github-actions` bot. It names 505 rows. Each row holds a branch name, a commit count, and an age in days. The rows total 1,616 commits above `main`. The ages run from 7 to 65 days, and 274 rows are 30 days old or more.

Each name exists on origin. The GitHub tip of each name equals the local tracking ref. The local count from `origin/main` equals the table count for all 505 rows (RC-02, RC-03, RC-04). The report is accurate about the names and the counts. The report is not accurate about protection (R2).

The report source is `src/misthelper_devtools/stranded_branch_report.py` in `misthelper-devtools` (RC-66 to RC-69). It treats a branch as protected in two cases. An open PR head name equals the branch name. Or a closed PR head name equals the branch name, and the PR head contains the branch (RC-67, RC-68). Each check compares names. None compares a commit.

## R2. Which tips a PR already holds

A tip is held when it equals the head commit of a pull request (`headRefOid`). The check found 248 held tips and 257 tips that are not held (RC-05). The 248 held tips match 248 PR records. The records are 236 merged, 11 closed, and 1 open. They belong to 244 distinct PRs.

The report names none of the 248 held tips as protected, because no PR head name equals a named branch name (RC-06). For 227 of the 248 held rows, the name without the `archive/laptop-20261121/` prefix equals a PR head name. The archive names copy the PR branch names.

The check of 257 not held tips found 84 rows whose name without the archive prefix equals a PR head name. A sample of 20 of those 84 rows found one tip that is an ancestor of the same-name PR head. The other 19 tips are not ancestors. The sample does not decide the whole set (U-03).

## R3. Exemplar A: a held row

The first table row is `archive/laptop-20261121/preservation/2746-pr3011-turn0`. Its tip is `560f0eff3134dcb6fb08acaee85a5146597d6147`. The tip has one commit above `main`, which is the commit `test(api): cover HTTP failure modes in exports` from 2026-09-18 19:17 -0700. The commit changes 13 files with 242 insertions and one deletion (RC-14).

PR 3954 is closed without a merge. Its head name is `preservation/2746-pr3011-turn0`, and its head commit is the same tip (RC-08, RC-09, RC-10). The remote ref `refs/pull/3954/head` points to the tip (RC-08). The report treats this row as stranded, so it is a false positive for the protection rule.

PR 3011 is merged with merge commit `fbb07426b47f57195a5d6f2826f5c326fd81603a` (RC-12). Its head commit is `b4ad2f71c2e51e1a37e6797a6e2b0b5f0b3ee55a`. Four of its seven files have the same blob SHA as the exemplar A tip (RC-13). Nine of the 13 exemplar A files are not in PR 3011. The exemplar A tip therefore holds work that PR 3011 did not merge.

## R4. Exemplar B: a true unheld row

The oldest unheld row is `fix/3158-wip-controls`. Its tip is `0f6b375e71243311b5cf5856fe9f220842a14e3b` (RC-15). The tip has one commit above `main`. The commit subject is `chore(web-portal): keep the uncommitted draft of #3158 [skip ci]`, and it dates from 2026-09-28 16:33:52 -0500.

The branch changes seven files with 62 insertions and two deletions (RC-18). No PR head commit equals the tip (RC-16). No PR has the head name `fix/3158-wip-controls` (RC-17). Issue 3158 is closed (RC-20). The branch is an unmerged work-in-progress copy with no PR, so the report is correct for this row.

The branch adds `specs/3158-wip-controls/spec.md`, `plan.md`, and `tasks.md` (RC-19). The constitution requires new records under the managed roots `numbered/`, `live/`, `skills/`, or `indexes/` (RC-36). A merge as it stands would break that rule. Decision D-12 keeps the branch out of this change.

## R5. Why the record does not open one PR per named branch

The issue body says to open one pull request for each named branch. The plan rejects that rule for these reasons.

- Each PR starts `ci.yml`. The file has 28 job keys (RC-47), and `quality_gate_issues` runs on each PR run (RC-47, RC-48).
- `quality_gate_issues` uses scope `all` (RC-49). The reusable workflow opens one issue for each failed gate of a PR run (RC-50, RC-51). The two exemplars are 688 and 794 commits behind `main`, so gate failures are likely. The failure rate is unverified (U-06).
- Four more workflows start on a PR event: CodeQL, STE lint, the PR title check, and auto-merge on open (RC-52 to RC-55).
- A 257-PR batch would create at least 257 pull request threads for the owner to close.

The cost argument rests on the run count and the issue count, not on minutes. The plan rejects PRs for that volume of runs and issues.

## R6. Why a tag keeps the commits

`AGENTS.md` lists a pushed tag as a preservation proof (RC-28). A tag keeps its commit reachable after the branch is deleted. The tag form is a lightweight tag at the tip. The prefix `preserve/` keeps the tags apart from the version tags.

No workflow starts from a `preserve/` tag if the event filters behave as the workflow files state. Each push trigger names `main` or ignores `main` (RC-46, RC-57 to RC-63). Only `release.yml` names tags, and its pattern is `v*.*.*` (RC-56). GitHub documentation for the filter behavior was not readable through the fetch tool (U-01). The pilot checks the behavior before the batches (T006).

The repository states that `refs/pull/<n>/head` is the only permanent copy (RC-27). `AGENTS.md` accepts a pushed tag (RC-28). The guide follows the stricter statement. This research treats the tag as a second durable copy for every row (D-3). The tag does not depend on the unverified PR ref behavior (U-02).

## R7. Remote refs and tags before the change

- The remote has 598 branches and 2,396 `refs/pull/*/head` refs (RC-05 and the PR count of R2).
- The remote has no `refs/tags/preserve/*` tag (RC-22).
- All 505 names pass `git check-ref-format` for `refs/tags/preserve/<name>`. The longest name has 150 characters.
- All 505 tips are present in the local object store. The check used `git rev-list` for each tip.

## R8. The report rule and the upstream fix

The report protection test has two defects. The test compares names, not commits (RC-66, RC-67, RC-68). The test does not read preservation tags. The upstream request in T013 asks for two rules. A tip that equals a PR head commit is held. A tip with a `preserve/` tag at the same commit is held.

The scheduled workflow in this repository pins `misthelper-devtools` at `79a5e45970e876f1656d69520d9635cea1aa25ef` (RC-42). The local development tool pin is `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` (RC-40). The two pins differ (U-09). The change keeps both pins (FR-016).

## R9. Duplicate tracking issues

Five open issues share the report title. The tracking issue is 4911. The other four are 4302 (48 rows), 4583 (52 rows), 4719 (51 rows), and 4818 (54 rows) (RC-21). The reusable workflow searches open issues by title and reuses the first match (RC-64, RC-65). The workflow comment promises one open issue. The cause of the duplicates is unverified (U-04).

## R10. Guide and changelog rules

The branch cleanup section of `documentation/contributing.md` starts at line 52 (RC-23). The section warns that deletion removes the only copy (RC-24). Step 2 says to open a PR for each named branch (RC-26). The change edits this section (T009).

The changelog guide allows the name forms `pr-<number>.md`, `issue-<number>-<slug>.md`, and `<YYYY-MM-DD>-<slug>.md` (RC-33). The fragment guard test checks each name form and the change types (RC-70). Rule 4 of the guide allows no fragment for an internal change (RC-34). The constitution requires one fragment for each change (RC-35). The constitution governs, so the change adds one fragment (D-10).

The Markdown link guard checks every relative link in each tracked Markdown file (RC-71). The STE gate runs on each changed Markdown file (RC-31).

## R11. Record route and folder debt

The route for issue 4911 is `0/0/1/2/4/1/2/1`. The script `spec-route.ps1` converts a number to base 5 with eight digits (RC-38, RC-39). The number 4911 equals `124121` in base 5, which pads to `00124121`. The reference record for issue 4920 uses the same method, and its route is `0/0/1/2/4/1/4/0`.

The route parent folders do not exist before this change. The feature root and the design folder each hold five children. The folder debt is recorded in `plan.md`. `changelog.d` holds 335 children. `specs` holds 813 direct children, and 525 of them are legacy folders. Constitution rule I requires the record of that debt (RC-37).

## Decisions

| ID | Decision | Alternatives | Rationale | Risk |
| - | - | - | - | - |
| D-1 | The procedure preserves named branches. It does not delete, merge, or close any branch or pull request. | Include deletion. Include merges. | Deletion is destructive. `AGENTS.md` requires confirmation for destructive operations. | Named branches stay on origin, and their names still appear in the report. |
| D-2 | Use one lightweight tag `preserve/<branch name>` for each named branch. | One PR for each named branch (R5). A custom ref namespace such as `refs/preserve/`. No durable copy. | `AGENTS.md` accepts a pushed tag (RC-28). Tags start no workflow if the filters behave as stated (U-01). | Tag listings show 505 new tags. The pilot checks the workflow behavior. |
| D-3 | Tag all 505 named branches, including the 248 held tips. | Tag only the 257 not held tips. | Independent of the unverified PR ref behavior (U-02). One rule covers every row. The extra 248 tags cost little. | Duplicate durable copies for held tips. |
| D-4 | Read each tip from GitHub in the same session as its push. Verify each batch with `git ls-remote`. | Use local tracking refs for the tips. Trust a push exit code. | The truth order puts GitHub first. Local refs can lag. | The report holds no tip IDs, so a rewrite after the report is not visible (U-10). |
| D-5 | Push a 5-tag pilot first. Push later batches of at most 50 tags. | One push of 505 tags. One API write for each tag. | The pilot checks workflow behavior. Batches bound the effect of a failure. | Eleven pushes instead of one. |
| D-6 | Update `documentation/contributing.md` only. Leave the historical review unchanged. | Rewrite `documentation/stranded-branch-review.md`. Leave the guide unchanged. | The guide is the current rule. The review states its own date (RC-27). | The review still says a PR is the only permanent copy. |
| D-7 | Use `Refs #4911` in the record PR until the report names no row. Then use `Closes #4911`. | Use `Closes #4911` now. | A merge with the keyword closes issue 4911. The next weekly run then opens a new tracking issue (RC-43, RC-44). | Issue 4911 stays open after the record merges. |
| D-8 | Keep issue 4911 as the one open tracking issue. Close the four duplicates with a link. | Close issue 4911. Keep all five. | Issue 4911 holds the current table. The workflow promises one open issue (RC-64). | Closing four issues changes the list that other readers saw. |
| D-9 | File one upstream issue for held tips and preservation tags. Keep both pins. | Change the report in this repository. Accept permanent extra rows. | The tool lives upstream, and the workflow pins a shared commit. | The report stays noisy until the upstream change ships and the pin changes. |
| D-10 | Add one changelog fragment with the `issue-` name form. | No fragment. | The constitution requires one fragment for each change (RC-35). | Rule 4 of the guide conflicts with the constitution (F-08). |
| D-11 | Use the slug `stranded-branch-preservation`. | Use the issue title as the slug. Use a date route. | The slug names the subject. The numeric route applies to issues (RC-38, RC-39). | None known. |
| D-12 | Do not merge `fix/3158-wip-controls` as it stands. | Merge it. Delete it. | The branch adds specs outside the managed roots (RC-19, RC-36). Deletion is out of scope (D-1). | The branch stays unmerged, and the report keeps naming it. |

## Remote verification

Each row records one check. The `claim` column states what the check expects. The `result` column reports whether the named item exists on the remote. The value `present` means the item exists. The value `absent` means the item does not exist. The `blob SHA` column holds a blob SHA, a commit SHA, or `none` when no object applies. The `line` column holds the line number in the file body, or `0` when the claim concerns a ref or a list.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Issue 4911 names 505 branch rows | issues/4911 body | issue-4911 | none | present | 0 |
| RC-02 | All 505 named branch names exist on origin | refs/heads/* (505 names of issue 4911) | main | none | present | 0 |
| RC-03 | GitHub tips of the 505 names equal the local tracking refs | refs/remotes/origin/* (505 names of issue 4911) | main | none | present | 0 |
| RC-04 | Local commit counts from origin/main equal all 505 table counts | git rev-list origin/main..TIP (505 names) | main | none | present | 0 |
| RC-05 | 248 named tips equal a PR head commit | refs/pull/*/head (2,396 refs) | main | none | present | 0 |
| RC-06 | No named branch name equals a PR head name | pulls headRefName (2,396 records) | main | none | absent | 0 |
| RC-07 | Remote main is commit f03c6c9b | refs/heads/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-08 | The ref refs/pull/3954/head points to the tip of exemplar A | refs/pull/3954/head | refs/pull/3954/head | 560f0eff3134dcb6fb08acaee85a5146597d6147 | present | 0 |
| RC-09 | PR 3954 is closed without a merge | pulls/3954 state | refs/pull/3954/head | 560f0eff3134dcb6fb08acaee85a5146597d6147 | present | 0 |
| RC-10 | PR 3954 head name is the exemplar A name without the archive prefix | pulls/3954 headRefName | preservation/2746-pr3011-turn0 | 560f0eff3134dcb6fb08acaee85a5146597d6147 | present | 0 |
| RC-11 | Exemplar A tip exists on origin under the archive name | refs/heads/archive/laptop-20261121/preservation/2746-pr3011-turn0 | archive/laptop-20261121/preservation/2746-pr3011-turn0 | 560f0eff3134dcb6fb08acaee85a5146597d6147 | present | 0 |
| RC-12 | PR 3011 is merged with merge commit fbb07426b47f57195a5d6f2826f5c326fd81603a | pulls/3011 state | refs/pull/3011/head | b4ad2f71c2e51e1a37e6797a6e2b0b5f0b3ee55a | present | 0 |
| RC-13 | Four PR 3011 file blobs equal exemplar A file blobs | pulls/3011/files | refs/pull/3011/head | b4ad2f71c2e51e1a37e6797a6e2b0b5f0b3ee55a | present | 0 |
| RC-14 | Exemplar A changes 13 files with 242 insertions and 1 deletion | compare of main with archive/laptop-20261121/preservation/2746-pr3011-turn0 | archive/laptop-20261121/preservation/2746-pr3011-turn0 | 560f0eff3134dcb6fb08acaee85a5146597d6147 | present | 0 |
| RC-15 | Exemplar B tip is commit 0f6b375e on origin | refs/heads/fix/3158-wip-controls | fix/3158-wip-controls | 0f6b375e71243311b5cf5856fe9f220842a14e3b | present | 0 |
| RC-16 | No PR head commit equals the exemplar B tip | pulls headRefOid (2,396 records) | fix/3158-wip-controls | 0f6b375e71243311b5cf5856fe9f220842a14e3b | absent | 0 |
| RC-17 | No PR has the head name fix/3158-wip-controls | pulls with head fix/3158-wip-controls | fix/3158-wip-controls | none | absent | 0 |
| RC-18 | Exemplar B changes 7 files with 62 insertions and 2 deletions | compare of main with fix/3158-wip-controls | fix/3158-wip-controls | 0f6b375e71243311b5cf5856fe9f220842a14e3b | present | 0 |
| RC-19 | Exemplar B adds specs/3158-wip-controls/spec.md | specs/3158-wip-controls/spec.md | fix/3158-wip-controls | 0f8225efef186de7515df325de38caca0911bb59 | present | 0 |
| RC-20 | Issue 3158 is closed | issues/3158 state | issue-3158 | none | present | 0 |
| RC-21 | Five open issues carry the report title | issues open with the report title | issue-4911 | none | present | 0 |
| RC-22 | No preservation tag exists on origin | refs/tags/preserve/* | main | none | absent | 0 |
| RC-23 | The guide has the Branch cleanup heading | documentation/contributing.md | main | 3b455b6d6730e16972540f14f7f654462b1c27bd | present | 52 |
| RC-24 | The guide warns that deletion removes the only copy | documentation/contributing.md | main | 3b455b6d6730e16972540f14f7f654462b1c27bd | present | 54 |
| RC-25 | The guide says the PR ref survives a branch deletion | documentation/contributing.md | main | 3b455b6d6730e16972540f14f7f654462b1c27bd | present | 58 |
| RC-26 | The guide step 2 opens a PR for each named branch | documentation/contributing.md | main | 3b455b6d6730e16972540f14f7f654462b1c27bd | present | 76 |
| RC-27 | The historical review says the PR ref is the only permanent copy | documentation/stranded-branch-review.md | main | 8091539c31ff8648d0426f4a8a92e01e0eb902b4 | present | 46 |
| RC-28 | AGENTS.md accepts a tag that you push as a preservation proof | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 275 |
| RC-29 | The agent guide lists stranded-branch-report as a shared command | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 41 |
| RC-30 | The agent guide Local gates table has the Tests row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| RC-31 | The agent guide Local gates table has the STE row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| RC-32 | The agent guide says release.yml runs on tags that match v*.*.* | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 474 |
| RC-33 | The changelog guide names issue-<number>-<slug>.md when no PR exists | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| RC-34 | Changelog rule 4 allows no fragment for an internal-only change | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| RC-35 | The constitution requires one fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| RC-36 | The constitution requires managed roots for new specs records | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 57 |
| RC-37 | The constitution requires a folder debt record and a remediation action | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 49 |
| RC-38 | spec-route.ps1 defines Get-SpecRadixSegments | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 4 |
| RC-39 | spec-route.ps1 uses base 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-40 | requirements-dev.txt pins misthelper-devtools at 2239e7bd | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 197 |
| RC-41 | The weekly stranded report runs on the cron 0 7 * * 1 | .github/workflows/stranded-branch-report.yml | main | 0fde8b4e98edcc111425e3a385e42075cf43595f | present | 20 |
| RC-42 | The weekly stranded report pins the reusable workflow at 79a5e459 | .github/workflows/stranded-branch-report.yml | main | 0fde8b4e98edcc111425e3a385e42075cf43595f | present | 47 |
| RC-43 | close-linked-issues.yml runs on closed pull requests | .github/workflows/close-linked-issues.yml | main | 42a085ac6240518b028862c290ec9502a5b13b2a | present | 20 |
| RC-44 | The close-linked-issues job skips a PR that closed without a merge | .github/workflows/close-linked-issues.yml | main | 42a085ac6240518b028862c290ec9502a5b13b2a | present | 46 |
| RC-45 | ci.yml runs on pull_request | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 16 |
| RC-46 | The ci.yml push trigger names main only | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 23 |
| RC-47 | ci.yml declares 28 job keys from ruff to quality_gate_issues | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 140 |
| RC-48 | The ci.yml quality_gate_issues job begins at line 1293 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1293 |
| RC-49 | The ci.yml quality_gate_issues job uses scope all | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1321 |
| RC-50 | The reusable gate issue workflow opens an issue for a PR run | .github/workflows/reusable-quality-gate-issues.yml (misthelper-devtools) | 79a5e45970e876f1656d69520d9635cea1aa25ef | 9a46074e9baee83afb3405d7c51fd4e21797f17c | present | 25 |
| RC-51 | The reusable gate issue workflow opens an issue for each failed gate | .github/workflows/reusable-quality-gate-issues.yml (misthelper-devtools) | 79a5e45970e876f1656d69520d9635cea1aa25ef | 9a46074e9baee83afb3405d7c51fd4e21797f17c | present | 215 |
| RC-52 | codeql.yml runs on pull_request | .github/workflows/codeql.yml | main | 2ef072fbddd473f841c5877f4d89b7c7760aeaf0 | present | 9 |
| RC-53 | ste-lint.yml runs on pull_request | .github/workflows/ste-lint.yml | main | abaeff6d5e299bfa7de4dc15d04f4ef31cf13b5f | present | 26 |
| RC-54 | pull-request-title.yml runs on pull_request opened and edited | .github/workflows/pull-request-title.yml | main | 6b161b5a7dd71a0f0c9c0f38b750a7322ae8704e | present | 4 |
| RC-55 | auto-merge.yml runs on pull_request opened and closed | .github/workflows/auto-merge.yml | main | 9d26134dd84cf50008a17fd878772102ce355983 | present | 22 |
| RC-56 | release.yml triggers on tags that match v*.*.* only | .github/workflows/release.yml | main | e81c05798c7609344d2d59b94114d7d9f76263be | present | 5 |
| RC-57 | The ste-lint.yml push trigger names main only | .github/workflows/ste-lint.yml | main | abaeff6d5e299bfa7de4dc15d04f4ef31cf13b5f | present | 25 |
| RC-58 | The codeql.yml push trigger names main only | .github/workflows/codeql.yml | main | 2ef072fbddd473f841c5877f4d89b7c7760aeaf0 | present | 14 |
| RC-59 | The container-build.yml push trigger names main only | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 5 |
| RC-60 | The wiki-publish.yml push trigger names main only | .github/workflows/wiki-publish.yml | main | 212707cfe8b7c7809f4a7992fe96ea8dd71e171b | present | 22 |
| RC-61 | The windows-audit-report.yml push trigger ignores main | .github/workflows/windows-audit-report.yml | main | 2d4e608b038dbe20f522bd296f707126a0ad37bb | present | 5 |
| RC-62 | The windows-timeout-budget.yml push trigger ignores main | .github/workflows/windows-timeout-budget.yml | main | 1caf671d77b9a4462a7cd06aa4c3fe481023aaa0 | present | 5 |
| RC-63 | The auto-merge.yml push trigger ignores main | .github/workflows/auto-merge.yml | main | 9d26134dd84cf50008a17fd878772102ce355983 | present | 34 |
| RC-64 | The reusable stranded report reuses one open issue | .github/workflows/reusable-stranded-branch-report.yml (misthelper-devtools) | 79a5e45970e876f1656d69520d9635cea1aa25ef | b8ca235c93beddef9307d797da87223a920df729 | present | 153 |
| RC-65 | The reusable stranded report searches open issues by title | .github/workflows/reusable-stranded-branch-report.yml (misthelper-devtools) | 79a5e45970e876f1656d69520d9635cea1aa25ef | b8ca235c93beddef9307d797da87223a920df729 | present | 156 |
| RC-66 | The report ignores only the dependabot/ prefix | src/misthelper_devtools/stranded_branch_report.py (misthelper-devtools) | 79a5e45970e876f1656d69520d9635cea1aa25ef | dad8d5081a3f716363408f3e25d92898054953d3 | present | 53 |
| RC-67 | The report tests open PR head names by branch name | src/misthelper_devtools/stranded_branch_report.py (misthelper-devtools) | 79a5e45970e876f1656d69520d9635cea1aa25ef | dad8d5081a3f716363408f3e25d92898054953d3 | present | 104 |
| RC-68 | The report tests closed PRs by a head name filter | src/misthelper_devtools/stranded_branch_report.py (misthelper-devtools) | 79a5e45970e876f1656d69520d9635cea1aa25ef | dad8d5081a3f716363408f3e25d92898054953d3 | present | 210 |
| RC-69 | The report prints the rule about PR heads before cleanup | src/misthelper_devtools/stranded_branch_report.py (misthelper-devtools) | 79a5e45970e876f1656d69520d9635cea1aa25ef | dad8d5081a3f716363408f3e25d92898054953d3 | present | 302 |
| RC-70 | The changelog fragment guard names the issue fragment pattern | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 39 |
| RC-71 | The Markdown link guard tests each relative link | tests/guardrails/test_markdown_links.py | main | cafefdac69006ddf7544e5a57a101f0f63fbcc38 | present | 79 |
| RC-72 | The reference record spec names its user stories | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 26 |

Rows RC-02 to RC-22 read GitHub through the API or through `git ls-remote`. Rows RC-23 to RC-49, RC-70, RC-71, and RC-72 read repository files. The local hash of each file matches the remote blob SHA. The line numbers therefore match the remote files. Rows RC-50 to RC-69 read the pinned devtools commit through the API. Rows RC-52 to RC-63 read repository workflow blobs through the API. Row RC-04 reads local git objects, and row RC-03 compares GitHub with local refs.

## Sources

Local repository files, read on 2026-11-26 with blob SHAs that match the remote tree:

- `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`.
- `.specify/scripts/powershell/spec-route.ps1`.
- `documentation/contributing.md`, `documentation/stranded-branch-review.md`.
- `changelog.d/README.md`, `tests/guardrails/test_changelog_fragment_policy.py`, `tests/guardrails/test_markdown_links.py`.
- `.github/workflows/ci.yml`, `stranded-branch-report.yml`, `close-linked-issues.yml`, and the other workflow files named in the table.
- `requirements-dev.txt`.
- The reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv`. Its shape was copied. Its content was not copied.

Searched and not used as sources: `documentation/quality-gates.md`, `documentation/development-setup.md`, `documentation/architecture.md`, `documentation/container-deployment.md`, and `documentation/operator-guide.md`. A search of these files for the ref rule terms found no rule that applies to this change.

GitHub API reads through `gh` and the git reads listed below:

- `gh issue view 4911`, `gh issue list`, and the open issue counts of issues 4302, 4583, 4719, 4818, and 4911.
- `gh api repos/jmorrison-juniper/MistHelper/branches` with pagination, which gives 598 names and their tips.
- `gh pr list --state all`, which gives 2,396 PR records with `headRefName` and `headRefOid`.
- `gh pr view 3011` and `gh pr view 3954`, and the files endpoint of PR 3011 at `repos/jmorrison-juniper/MistHelper/pulls/3011/files`.
- The compare endpoint of the repository, for `main` and each exemplar branch, for the exemplar files and counts.
- The git trees endpoint of the repository for `main` with recursive listing, for the remote blob SHAs.
- The blob endpoint of the repository, for each workflow blob SHA of MistHelper.
- `gh api repos/jmorrison-juniper/misthelper-devtools/git/trees/79a5e45970e876f1656d69520d9635cea1aa25ef?recursive=1` and the blobs at that commit.
- `git ls-remote origin` for `refs/pull/3954/head`, `refs/heads/main`, and the count of `refs/pull/*/head`.
- `git rev-list --count`, `git log`, `git show --stat`, `git for-each-ref`, `git check-ref-format`, and `git hash-object` without `-w`. No fetch, checkout, or write command ran.

URLs: `https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows` was requested through the fetch tool. The tool blocked the address as private, so no page was read (U-01).

## Unverified

- U-01: The GitHub rule for tag and branch filters on a push event. The fetch tool blocked the documentation URL. The pilot in T006 verifies the behavior.
- U-02: That `refs/pull/<n>/head` survives a branch deletion. The repository states it, and this research did not check it against GitHub documentation. The tags in D-3 do not depend on it.
- U-03: The ancestry of the 257 not held tips in their same-name PR heads. The sample covered 20 of 84 rows. The result was one ancestor and 19 non-ancestors. No decision depends on the rest.
- U-04: The cause of the five open tracking issues. The workflow run history was not read.
- U-05: The date `2026-11-21` in the archive prefix. The date comes from the branch name, not from a push event.
- U-06: Gate outcomes for a PR on each named branch. No PR was opened, so the gate results are unknown.
- U-07: That GitHub accepts 50 lightweight tags in one push. The size was chosen as a bound and was not tested.
- U-08: The convention for the ledger comment on the tracking issue. The convention belongs to this record and is not a repository rule.
- U-09: Whether the local tool pinned at `2239e7bd` behaves like the workflow pin at `79a5e459`. The two commits were not compared.
- U-10: Whether a branch was rewritten after the report. The report holds no tip IDs. The spec records this as an edge case.

## Test count

The count of new test functions is 0. The change adds no code. The existing guard modules in T-LOCAL-GATES verify the Markdown and the fragment.

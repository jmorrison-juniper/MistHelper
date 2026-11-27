# Research: Stranded Branch Preservation

## Method

The record reads three sources. The GitHub API gives remote state: refs, PRs, issues, commits, compare data, and blob SHAs on `main`. Local git gives read-only confirmation that each local remote-tracking ref equals its GitHub head. Repository files give the policy. The record did not switch to any branch, fetch any ref, or change any ref.

The scope is report #4911, the newest tracking issue. It lists 505 rows. The annotated table in #4302 lists 48 rows. Each annotated row gets its own remote check. Each report row gets a PR-kept or unkept class, and the groups are counted.

A report row is PR-kept when its head commit equals the head commit of some PR. A PR keeps that commit under `refs/pull/<n>/head`. The report matches branch names, so a PR-kept row still appears in the report. The report counts the name match, not the commit.

## Issue Facts

- Issue #4302 is OPEN. Its labels are `ci`, `chore`, and `in-progress`. Its author is `app/github-actions`, and it was created on 2026-10-19.
- The issue holds 29 comments. All 29 come from the owner account, `jmorrison-juniper`, between 2026-10-20 and 2026-11-09.
- The body is a bot table of 48 rows, with commits ahead and age in days. It names no reproduction steps, and it holds no error text.
- The owner comments record holds, reservations, and the request to open a PR before any cleanup.
- Linked PRs: only PR #4318 contains the number 4302 in its body, found by a title and body search. It is MERGED, and its head is `fix/3417-snmp-base-oid`. No other PR matches the search.
- Legacy record: none. No folder under `specs\` starts with `4302-`, so no legacy verification applies.

## Decisions

| ID | Decision | Alternatives | Rationale | Risk | Human |
| - | - | - | - | - | - |
| D-1 | Scope is the 505 rows of report #4911. The 48 rows of #4302 are the annotated subset. | (a) The 48 annotated rows only. (b) The report rows only. | 47 of 48 annotated rows appear in #4911. Option (a) misses 458 rows. Option (b) drops the owner dispositions. | Large scope. Groups limit the work per step. | No |
| D-2 | No branch ref changes. No deletion, rewrite, rebase, merge, or force-push. | (a) Delete archive copies. (b) Rewrite stale heads. | `refs/pull/<n>/head` is the only permanent copy (RC-02). A deletion can remove the only copy of an unkept commit. | The report keeps listing rows until the fix. | No |
| D-3 | Publication uses draft PRs. The owner selects each batch. One PR serves each distinct head. Group N waits for the owner. | (a) One PR for each of 257 unkept rows. (b) One PR for each of 251 distinct heads. (c) Annotated tags, with no PR. (d) Keep refs and publish nothing. | Recommended: option (b), one batch at a time, after the owner selects it. The owner rule requires a PR before cleanup (RC-03, RC-04). The repository is public (RC-25). Tags do not clear the report, because it checks PRs. | Public exposure of unreleased work. A wrong batch cannot be recalled. | HUMAN-DECISION-REQUIRED |
| D-4 | A PR-kept row needs no new PR. Its PR number is the proof. | (a) Open duplicate PRs. (b) Ignore PR-kept rows. | The PR head already keeps the commit (RC-41). Option (b) leaves no proof. | The report keeps listing the row until D-11 is fixed. | No |
| D-5 | Counts come from GitHub compare and tree data. Owner comments and the body table are not counts of record. | (a) Use owner comments. (b) Use the body table. | The owner counts are stale. Example: 411 against 562 for `jmorrison-jnpr-snmp-fallback-delivery`. | GitHub rate limits. Retry rules apply. | No |
| D-6 | `fix/3417-snmp-base-oid` needs no action. | (a) Open a PR from the absent ref. (b) Restore the ref. | The ref is absent (RC-50). PR #4318 merged and kept head `9bae89aa` (RC-29). | None. | No |
| D-7 | Hold H1 waits for a human review. | (a) Publish after an agent review. (b) Delete the refs. | Recommended: keep H1 on hold. The upgrade path runs destructive operations (repository instructions, lines 309 to 320). Issues #2863 and #3222 carry `needs-human-review` (RC-45). | Delay in the H1 publication. | HUMAN-DECISION-REQUIRED |
| D-8 | Hold H2 waits for the holder release. | (a) Ignore the reservations. (b) Publish after a set period. | Owner comments say not to remove these refs without owner authorization. Two cited issues are closed, so the claims need the owner (RC-45). | Report noise continues for six rows. | No |
| D-9 | Hold H3 waits for the owner review of documentation deltas. | (a) Publish now. (b) Drop the deltas. | Owner comments say review the deltas first. The deltas hold distinct text (RC-58, RC-59, RC-88). | Delay in the H3 publication. | No |
| D-10 | The record PR refers to #4302 with `Refs`. It does not close #4302. | (a) `Closes #4302`, as the repository rules require. (b) No reference. | Recommended: option `Refs`. The owner keeps #4302 open (comments of 2026-10-20 to 2026-11-09). `close-linked-issues.yml` closes the issue on merge (repository instructions, line 472). | Conflicts with `AGENTS.md` and the constitution. | HUMAN-DECISION-REQUIRED |
| D-11 | A separate issue fixes the duplicate tracking issues. This record does not change the report. | (a) Fix the shared workflow here. (b) Change the MistHelper caller. | `AGENTS.md` requires one concern for each issue. The title search lives in the shared workflow (RC-23). The caller passes no search input. | Duplicates continue until the fix. | No |
| D-12 | Names. Route: the managed route for 4302. Branch: `docs/4302-stranded-branch-preservation`. Slug: `stranded-branch-preservation`. | (a) A slug that names the audit. (b) A slug from the title. | The route follows the base-5 rule (RC-10). The slug names the body of work. | None. | No |
| D-13 | One changelog fragment is added for this change. | (a) No fragment, under the user-visible rule. (b) One fragment, under the constitution. | The constitution supersedes the practice documents (constitution, Governance). Naming follows RC-16. | Low. | No |
| D-14 | No MistHelper code, test, or workflow changes. | (a) Add a guard for the title search here. (b) Change the report workflow here. | The owner states that no tooling change is needed for the policy (comment of 2026-10-20). The defect goes to D-11. | None. | No |
| D-15 | Labels: keep `ci`, `chore`, and `in-progress`. Add `needs-human-review` while D-3, D-7, and D-10 are open. | (a) Add no label. (b) Add `needs-human-review` now. | Three human decisions are open. The label already exists (RC-45). | None. | No |
| D-16 | Content scan: read the diff of each head, then search the head with `git grep` for secret patterns. A finding stops the batch. | (a) Run a scanner from the devtools package. (b) Skip the scan. | Rule 2 forbids a tool run in this record. `git grep` reads a commit without a checkout. A finding needs the credential policy. | A pattern can miss a secret. | No |
| D-17 | No Mist API, SDK, container, Juniper device, or skill work applies. No skill was loaded. | (a) Load a Juniper skill. (b) Load a container skill. | No claim in this record concerns those domains. | None. | No |

## Sources

Local sources in the repository. Line numbers refer to the `main` blob shown in the remote table.

- `AGENTS.md`, lines 260 and 271 (handoff and preservation rules).
- `.github/copilot-instructions.md`, lines 41 (devtools list), 50 to 76 (local gates), 309 to 320 (safety), 465 to 476 (workflow table), 471 to 472 (auto-merge and close-linked issues), 475 (stranded report row), and 478 (public repository).
- `.specify/memory/constitution.md`, line 57 (managed roots) and lines 453 to 526 (multi-agent workflow and PR checklist).
- `.specify/scripts/powershell/spec-route.ps1`, lines 4, 7, and 17 (radix route and width).
- `.specify/templates/plan-template.md`, line 9 (five children).
- `.specify/templates/spec-template.md`, `tasks-template.md`, and `checklist-template.md` (headings).
- `documentation/stranded-branch-review.md`, lines 4 and 46 (the historical review and the permanent-copy rule).
- `documentation/contributing.md`, lines 54, 58, and 76 (deletion and PR rule).
- `.github/workflows/stranded-branch-report.yml`, lines 20, 47, and 50 (schedule, pinned call, and quiet period).
- `changelog.d/README.md`, line 27 (naming rule) and lines 37 to 39 (fragment shape).
- `.pre-commit-config.yaml`, lines 31 and 37 (hook IDs).
- `tests/guardrails/test_spec_route_contract.py`, line 45, and `tests/guardrails/test_process_folder_structure.py`, line 133.
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`, the reference record shape.

Remote sources, read through the GitHub API:

- `repos/jmorrison-juniper/MistHelper/issues/4302` (body and comments), `issues/4911` (body), and the issue list with title search.
- `repos/jmorrison-juniper/MistHelper/git/matching-refs/heads/` (598 head refs, including `main`).
- `repos/jmorrison-juniper/MistHelper/git/ref/heads/fix/3417-snmp-base-oid` (HTTP 404).
- `repos/jmorrison-juniper/MistHelper/compare/{basehead}` (ahead, behind, commits, and files). The basehead joins `main` and the branch name with three dots.
- `repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1` (blob SHAs on `main`).
- `repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main` (decoded text, for line numbers).
- `repos/jmorrison-juniper/MistHelper/pulls` and `pull/<number>` (PR state, head commit, and merge commit).
- `repos/jmorrison-juniper/MistHelper/commits/<sha>` (commit presence).
- `repos/jmorrison-juniper/misthelper-devtools/contents/.github/workflows/reusable-stranded-branch-report.yml?ref=79a5e45970e876f1656d69520d9635cea1aa25ef`.
- `actions/runs/45242632367` (log of the report run of 2026-11-23).

Local git, read-only: `for-each-ref`, `rev-list --count`, and `log --no-walk`. The local heads equal the remote heads for all 598 refs (RC-27).

## Remote Verification

The columns are: ID, claim, path, ref, blob or head SHA, result, and line. A branch row holds the head commit in the SHA column. A file row holds the blob SHA. The value `none` means that no SHA applies. The result `absent` means that the checked item does not exist, or that no matching item exists.

| ID | Claim | Path | Ref | Blob or head SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | `AGENTS.md` section "Preserve work before you close an unmerged pull request" | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 271 |
| RC-02 | Stranded review: `refs/pull/<n>/head` is the only permanent copy | documentation/stranded-branch-review.md | main | 8091539c31ff8648d0426f4a8a92e01e0eb902b4 | present | 46 |
| RC-03 | Contributing: never delete a branch that reached no pull request | documentation/contributing.md | main | 3b455b6d6730e16972540f14f7f654462b1c27bd | present | 54 |
| RC-04 | Contributing: open a pull request for every branch the report names | documentation/contributing.md | main | 3b455b6d6730e16972540f14f7f654462b1c27bd | present | 76 |
| RC-05 | Report schedule is `0 7 * * 1`, Monday at 07:00 UTC | .github/workflows/stranded-branch-report.yml | main | 0fde8b4e98edcc111425e3a385e42075cf43595f | present | 20 |
| RC-06 | Report calls the shared workflow pinned at `79a5e459` | .github/workflows/stranded-branch-report.yml | main | 0fde8b4e98edcc111425e3a385e42075cf43595f | present | 47 |
| RC-07 | Repository instructions state that MistHelper is a public repository | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 478 |
| RC-08 | Repository instructions list the stranded report workflow | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 475 |
| RC-09 | Constitution requires managed roots for new specs records | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 57 |
| RC-10 | Route script sets base 5 at line 17 and default width 8 at line 7 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-11 | Plan template requires five children or fewer per directory | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 9 |
| RC-12 | Route contract guard tests exist | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 45 |
| RC-13 | Folder structure guard compares specs with the baseline | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 133 |
| RC-14 | Process folder baseline file exists | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| RC-15 | STE gate configuration file exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| RC-16 | Changelog rule: `issue-<number>-<slug>.md` when only the issue exists | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| RC-17 | Pre-commit hooks `ste-linter` and `markdown-link-check` | .pre-commit-config.yaml | main | 1f0e25544b2f347d8791dec74b7a233c681488ac | present | 31 |
| RC-18 | Reference record spec exists at its managed route | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-19 | Target route has no path on `main` | specs/numbered/0/0/1/1/4/2/0/2 | main | none | absent | 0 |
| RC-20 | Directory `0/0/1/1` holds five children, so no child can be added | specs/numbered/0/0/1/1 | main | none | present | 0 |
| RC-21 | Directory `0/0/1/1/4` holds three children, 0, 1, and 3 | specs/numbered/0/0/1/1/4 | main | none | present | 0 |
| RC-22 | Shared workflow closes the tracking issue when a PR holds every branch | misthelper-devtools .github/workflows/reusable-stranded-branch-report.yml | 79a5e45970e876f1656d69520d9635cea1aa25ef | b8ca235c93beddef9307d797da87223a920df729 | present | 178 |
| RC-23 | Shared workflow searches for the tracking issue by title | misthelper-devtools .github/workflows/reusable-stranded-branch-report.yml | 79a5e45970e876f1656d69520d9635cea1aa25ef | b8ca235c93beddef9307d797da87223a920df729 | present | 156 |
| RC-24 | Shared workflow dry-run input defaults to false | misthelper-devtools .github/workflows/reusable-stranded-branch-report.yml | 79a5e45970e876f1656d69520d9635cea1aa25ef | b8ca235c93beddef9307d797da87223a920df729 | present | 65 |
| RC-25 | Repository visibility is PUBLIC | repos/jmorrison-juniper/MistHelper | main | none | present | 0 |
| RC-26 | Remote `main` head commit | refs/heads/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-27 | Local `origin` refs equal GitHub heads for 598 of 598 refs | refs/remotes/origin | main | none | present | 0 |
| RC-28 | No open PR touches the route, AGENTS.md, or the constitution, for 0 of 7 open PRs | repos/jmorrison-juniper/MistHelper/pulls?state=open | main | none | absent | 0 |
| RC-29 | PR #4318 is merged, its body contains 4302, and its head is `9bae89aa` | pull/4318 | main | a0fac53c5b5d5f57e6d05ff2d6225570cda07691 | present | 0 |
| RC-30 | Commit `a0fac53c` exists on GitHub | commits/a0fac53c5b5d5f57e6d05ff2d6225570cda07691 | main | a0fac53c5b5d5f57e6d05ff2d6225570cda07691 | present | 0 |
| RC-31 | PR #4507 is merged as commit `296b977e`, from `jmorrison-juniper-2861-credential-token-slice` | pull/4507 | main | 296b977e28be50cd9ddcca57c46b35bb029afe27 | present | 0 |
| RC-32 | Commit `296b977e` exists on GitHub | commits/296b977e28be50cd9ddcca57c46b35bb029afe27 | main | 296b977e28be50cd9ddcca57c46b35bb029afe27 | present | 0 |
| RC-33 | Owner-cited PR set: 26 PRs checked. 21 cited merge commits match. 4 merged without a cited commit. PR #4039 closed unmerged. | pulls, 26 numbers | main | none | present | 0 |
| RC-34 | Latest report run 45242632367 found branches and opened issue #4911 | actions/runs/45242632367 | main | none | present | 0 |
| RC-35 | The report's title search returns no open issue | issues search with parentheses and a colon in the title | main | none | absent | 0 |
| RC-36 | Quoted title search returns five open tracking issues: #4302, #4583, #4719, #4818, and #4911 | issues search with a quoted phrase | main | none | present | 0 |
| RC-37 | Issues with the report title: 7 in total, 5 open, and 2 closed (#4184 and #4486) | issues, state all | main | none | present | 0 |
| RC-38 | Report #4911 lists 505 rows: 434 archive, 50 recovery, and 21 other | issues/4911 | main | none | present | 0 |
| RC-39 | Every row of #4911 names a remote ref that exists, for 0 absent | refs/heads, 505 names | main | none | present | 0 |
| RC-40 | No row of #4911 has a PR with the same branch name | PR head names, 505 rows | main | none | absent | 0 |
| RC-41 | 248 rows of #4911 are PR-kept: their head commit equals a PR head commit | PR head commits | main | none | present | 0 |
| RC-42 | 257 rows are unkept: 251 distinct head commits, and 1059 commits ahead summed over rows | refs/heads, 257 names | main | none | present | 0 |
| RC-43 | 458 rows of #4911 are outside the annotated table: 434 archive and 24 other | issues/4911 compared with issues/4302 | main | none | present | 0 |
| RC-44 | 47 of 47 present annotated rows are unkept | refs/heads, 47 names | main | none | present | 0 |
| RC-45 | #2863 and #3222 carry `needs-human-review`. #2711 and #2977 carry no `needs-human-review` label. #3575 and #3700 are CLOSED. | issues 2711, 2863, 2977, 3222, 3575, and 3700 | main | none | present | 0 |
| RC-46 | Annotated row, batch B1. 1 ahead, 688 behind. Files 7: identical 0, differs 3, absent 4. | refs/heads/fix/3158-wip-controls | main | 0f6b375e71243311b5cf5856fe9f220842a14e3b | present | 0 |
| RC-47 | Annotated row, batch B1. 1 ahead, 688 behind. Files 4: identical 0, differs 2, absent 2. | refs/heads/fix/3168-structured-signals | main | 69d19411fbc13c0b0ab55b10d49ae7ec177024c0 | present | 0 |
| RC-48 | Annotated row, batch B1. 1 ahead, 688 behind. Files 10: identical 0, differs 1, absent 9. | refs/heads/fix/3183-status-fallback | main | 0c46332ad00b2c9131f29fba218400ba7ece8f51 | present | 0 |
| RC-49 | Annotated row, hold H1. 1 ahead, 579 behind. Files 7: identical 0, differs 2, absent 5. | refs/heads/fix/3222-confirm-details | main | 18138f9b28173c969a57d447291ffebcd6daa029 | present | 0 |
| RC-50 | Annotated row. The ref returns HTTP 404. PR #4318 merged and kept head `9bae89aa`. | refs/heads/fix/3417-snmp-base-oid | main | none | absent | 0 |
| RC-51 | Annotated row, hold H2. 1 ahead, 562 behind. Files 3: identical 0, differs 3, absent 0. | refs/heads/jmorrison-jnpr-snmp-fallback-delivery | main | 73a1edaa973b4fb5110d9d3607377e42773d8445 | present | 0 |
| RC-52 | Annotated row, batch B1. 1 ahead, 562 behind. Files 3: identical 0, differs 1, absent 2. | refs/heads/fix/3506-site-lock-logs | main | 8c8fc28d452126a0e42c98040f8edf56d11a412f | present | 0 |
| RC-53 | Annotated row, hold H1. 1 ahead, 531 behind. Files 8: identical 0, differs 0, absent 8. | refs/heads/recovery/2863-handoff-20261004 | main | 188956f937019a0e07cab73919ebd289179c5def | present | 0 |
| RC-54 | Annotated row, hold H2. 1 ahead, 530 behind. Files 1: identical 0, differs 1, absent 0. | refs/heads/recovery/2711-handoff-20261004 | main | 9e943bfe30d9ab4513ba1d595e844fd8c1c080d0 | present | 0 |
| RC-55 | Annotated row, hold H2. 2 ahead, 532 behind. Files 39: identical 0, differs 3, absent 36. | refs/heads/recovery/3575-handoff-20261004 | main | 5746418f8cd77fa1ccd6cc004fd5f07a20ddaffb | present | 0 |
| RC-56 | Annotated row, hold H2. 1 ahead, 530 behind. Files 13: identical 0, differs 1, absent 12. | refs/heads/recovery/3700-handoff-20261004 | main | f253dd3b5533b63f0e75047e3fb918d976311b58 | present | 0 |
| RC-57 | Annotated row, batch B2. 1 ahead, 528 behind. Files 10: identical 0, differs 2, absent 8. | refs/heads/recovery/3701-handoff-20261004 | main | d2d2421da64d7884f7988321197dec066accb9f7 | present | 0 |
| RC-58 | Annotated row, hold H3. 1 ahead, 527 behind. Files 9: identical 0, differs 1, absent 8. | refs/heads/recovery/2752-handoff-20261004 | main | 024d42ff7f840becd7583433d502fbdf453594a3 | present | 0 |
| RC-59 | Annotated row, hold H3. 1 ahead, 525 behind. Files 11: identical 5, differs 1, absent 5. | refs/heads/recovery/2861-handoff-20261004 | main | 6cea98a9794d87e0ed3738bf331afff51280f76c | present | 0 |
| RC-60 | Annotated row, hold H2. 1 ahead, 532 behind. Files 24: identical 0, differs 0, absent 24. | refs/heads/recovery/2977-handoff-20261004 | main | d6e8eb8672edfa1c5123df03294ecd8daa98a051 | present | 0 |
| RC-61 | Annotated row, batch B2. 1 ahead, 512 behind. Files 13: identical 0, differs 2, absent 11. | refs/heads/recovery/3213-handoff-20261004 | main | 8090bc7d195407ecafe62fd16f38847ae18b5170 | present | 0 |
| RC-62 | Annotated row, batch B2. 1 ahead, 509 behind. Files 16: identical 0, differs 0, absent 16. | refs/heads/recovery/3326-handoff-20261004 | main | fa25a39cd3d77a9a9fc4c5d5327ba9c2e6c1c499 | present | 0 |
| RC-63 | Annotated row, batch B2. 1 ahead, 509 behind. Files 8: identical 0, differs 0, absent 8. | refs/heads/recovery/3329-handoff-20261004 | main | 7332749c6cf0344a2e7fdcbe02e1948f450d6b2c | present | 0 |
| RC-64 | Annotated row, batch B2. 1 ahead, 509 behind. Files 16: identical 0, differs 1, absent 15. | refs/heads/recovery/3295-handoff-20261004 | main | b1fe853fb26f4f4c7efd82148e5af14084a313ae | present | 0 |
| RC-65 | Annotated row, batch B2. 1 ahead, 508 behind. Files 2: identical 0, differs 0, absent 2. | refs/heads/recovery/3728-handoff-20261004 | main | 533ced96928dd51dc68a139d20c9476d08e87eb8 | present | 0 |
| RC-66 | Annotated row, batch B2. 2 ahead, 509 behind. Files 27: identical 0, differs 7, absent 20. | refs/heads/recovery/3436-handoff-20261004 | main | 0a032e83ab7cde0faec752258971df7b6b657d0c | present | 0 |
| RC-67 | Annotated row, batch B2. 1 ahead, 505 behind. Files 18: identical 0, differs 3, absent 15. | refs/heads/recovery/3699-handoff-20261004 | main | c0261d9fba897fb6339c46d26e465bcc3703ac1d | present | 0 |
| RC-68 | Annotated row, batch B2. 1 ahead, 502 behind. Files 12: identical 0, differs 4, absent 8. | refs/heads/recovery/3375-handoff-20261004 | main | 499b764f16fee9a465c9c789f3806ad9c0cdae1c | present | 0 |
| RC-69 | Annotated row, batch B2. 1 ahead, 501 behind. Files 18: identical 4, differs 6, absent 8. | refs/heads/recovery/3158-handoff-20261004 | main | ecb0bc87ceafe3f5024d678bdc99ad4b159fad7c | present | 0 |
| RC-70 | Annotated row, batch B2. 1 ahead, 500 behind. Files 14: identical 0, differs 4, absent 10. | refs/heads/recovery/3743-handoff-20261004 | main | 4ecd16c7e409e88899e46b105e5ec0b3e67b875c | present | 0 |
| RC-71 | Annotated row, batch B2. 1 ahead, 500 behind. Files 14: identical 0, differs 0, absent 14. | refs/heads/recovery/3491-handoff-20261004 | main | 97139eb2c6dc667d456c2fce420f8c57f6c67025 | present | 0 |
| RC-72 | Annotated row, hold H2. 1 ahead, 499 behind. Files 1: identical 0, differs 1, absent 0. | refs/heads/recovery/2747-handoff-20261004 | main | 2d5695fb4ed00411e5dbaf0d2b03539e3aff4863 | present | 0 |
| RC-73 | Annotated row, batch B2. 1 ahead, 499 behind. Files 13: identical 0, differs 4, absent 9. | refs/heads/recovery/3745-handoff-20261004 | main | 50e3d841dfbbcfb89fd0b419ce5631c5bd1068bd | present | 0 |
| RC-74 | Annotated row, batch B2. 1 ahead, 497 behind. Files 1: identical 0, differs 1, absent 0. | refs/heads/recovery/3749-handoff-20261004 | main | 9f930182fa5349ebf59fac3e8c9830327f4116b4 | present | 0 |
| RC-75 | Annotated row, batch B2. 2 ahead, 497 behind. Files 9: identical 0, differs 2, absent 7. | refs/heads/recovery/3161-handoff-20261004 | main | 33141f05cd19c509f723c57534edd2900b4ecde3 | present | 0 |
| RC-76 | Annotated row, batch B2. 1 ahead, 496 behind. Files 14: identical 0, differs 12, absent 2. | refs/heads/recovery/3388-handoff-20261004 | main | ea0a7467b81b297580f7a264658bd15fbf442c1e | present | 0 |
| RC-77 | Annotated row, batch B2. 1 ahead, 496 behind. Files 7: identical 0, differs 2, absent 5. | refs/heads/recovery/3380-handoff-20261004 | main | a3af99af23ba29e31725673a87e0f771293ba985 | present | 0 |
| RC-78 | Annotated row, batch B2. 1 ahead, 494 behind. Files 5: identical 0, differs 1, absent 4. | refs/heads/recovery/3761-handoff-20261004 | main | ebc40dac8dcb47b0c835bf45b7474dde1732669f | present | 0 |
| RC-79 | Annotated row, batch B2. 2 ahead, 492 behind. Files 2: identical 0, differs 1, absent 1. | refs/heads/recovery/3760-handoff-20261004 | main | 12f10ece0901452bd71eb1baa563ee77de5687db | present | 0 |
| RC-80 | Annotated row, batch B2. 2 ahead, 492 behind. Files 9: identical 0, differs 2, absent 7. | refs/heads/recovery/3769-handoff-20261004 | main | 54188ffcaffc18e3d5ced162fc64ef1762a90b70 | present | 0 |
| RC-81 | Annotated row, batch B2. 1 ahead, 490 behind. Files 1: identical 1, differs 0, absent 0. | refs/heads/recovery/2708-handoff-20261004 | main | f195788a090d6ace8f2f320dc1f96a413876e2c4 | present | 0 |
| RC-82 | Annotated row, batch B2. 2 ahead, 486 behind. Files 1: identical 0, differs 1, absent 0. | refs/heads/recovery/3818-handoff-20261004 | main | 0bb3149476b5658f8dc9ce44661d4c90dadc3669 | present | 0 |
| RC-83 | Annotated row, batch B2. 2 ahead, 501 behind. Files 9: identical 0, differs 1, absent 8. | refs/heads/recovery/3738-handoff-20261004 | main | c70007d407c5cd58ef08901832806120175d49b3 | present | 0 |
| RC-84 | Annotated row, batch B3. 1 ahead, 485 behind. Files 1: identical 0, differs 0, absent 1. | refs/heads/docs/3818-campaign-stop-20261004 | main | 8c3e6cacc6d101c3b4356369f94b2f50039f987b | present | 0 |
| RC-85 | Annotated row, batch B1. 2 ahead, 485 behind. Files 6: identical 1, differs 5, absent 0. | refs/heads/fix/3292-isolate-retry-e2e-sites | main | f706902a5af34e272583b45686fd60b4e1225fed | present | 0 |
| RC-86 | Annotated row, batch B1. 3 ahead, 421 behind. Files 18: identical 0, differs 18, absent 0. | refs/heads/jmorrison-juniper-startup-dependency-reassessment | main | e849f3fe4e0734f54de76a0b171390674555ca2b | present | 0 |
| RC-87 | Annotated row, hold H1. 1 ahead, 398 behind. Files 13: identical 0, differs 12, absent 1. | refs/heads/jmorrison-juniper-fix-2863-identifier-defaults-batch-1 | main | 6eec0e4bf09a6ca5deb1bb78c008337bab6e7464 | present | 0 |
| RC-88 | Annotated row, hold H3. 3 ahead, 393 behind. Files 12: identical 0, differs 7, absent 5. | refs/heads/jmorrison-juniper-assessment-4026 | main | 83d197e30fd9519521697154036eadf4e52a2850 | present | 0 |
| RC-89 | Annotated row, batch B1. 2 ahead, 397 behind. Files 1: identical 0, differs 0, absent 1. | refs/heads/jmorrison-juniper-issue-3416-lint-pattern | main | 3d51242e41f2815bbcaeaa076a2c1e60b2fd9550 | present | 0 |
| RC-90 | Annotated row, batch B1. 2 ahead, 400 behind. Files 12: identical 0, differs 2, absent 10. | refs/heads/jmorrison-juniper-false-success-family-4028 | main | 4be5f321a3ba26c136c541e062c7aa4e7442aae9 | present | 0 |
| RC-91 | Annotated row, batch B1. 1 ahead, 391 behind. Files 5: identical 0, differs 1, absent 4. | refs/heads/jmorrison-jnpr-test-4035-menu-92-selection-result | main | 9851ed28ced6f6d0909fe529e0a8f43c1a412bed | present | 0 |
| RC-92 | Annotated row, batch B1. 2 ahead, 397 behind. Files 42: identical 0, differs 28, absent 14. | refs/heads/jmorrison-juniper-issue-2746 | main | 4ebe402c19de77a546960896ef70bb3286860f13 | present | 0 |
| RC-93 | Annotated row, batch B1. 1 ahead, 430 behind. Files 3: identical 0, differs 2, absent 1. | refs/heads/jmorrison-juniper-coordinate-issue-work | main | 29c5489751ed84a8595cefe85f0e2aa7716b8608 | present | 0 |

## Unverified

Each item below stays unverified in this record. The reason follows each item.

- U-1: GitHub keeps `refs/pull/<n>/head` after a branch deletion. Source: `documentation/stranded-branch-review.md`, line 46. Reason: no GitHub document was checked in this run.
- U-2: Git removes an unreachable commit after 90 days. Source: `documentation/stranded-branch-review.md`, section "What the review proved". Reason: no git document was checked in this run.
- U-3: The owner reservations on #2711 and #3700, and the "active owner" note on #3575. Reason: the labels and states are verified (RC-45), but the reservation text exists only in owner comments.
- U-4: PR #3772 stays separate from `recovery/3700`. Reason: PR #3772 is MERGED (state verified), but its content was not compared with the branch.
- U-5: The content safety of each head. Reason: no scan ran. Tasks T008 to T010 record the scan results.
- U-6: The report's quiet-period and bot-branch rules. Reason: only lines 1 to 184 of the shared workflow were read in part. The command in misthelper-devtools was not read.
- U-7: The file content of the 188 unkept archive rows and the 22 unkept new rows beyond the named set. Reason: not enumerated row by row in this record. TST-02 regenerates the list.
- U-8: The cause of the four duplicate tracking issues. Reason: only the run log of 2026-11-23 was read. Earlier logs were not read.
- U-9: The owner note that PR #4396 changes a different test path. Reason: the PR is MERGED (state verified), but the path comparison was not run.

## Not Applicable

- Mist API and mistapi SDK: no claim in this record concerns a Mist REST endpoint or an SDK function.
- Podman and containers: no container is started, built, or pushed.
- Juniper device behavior: no device claim is made. No `juniper-*` skill was loaded.
- Local gates for code: compile, lint, format, types, coverage, complexity, bandit, pip-audit, pylint, vulture, docstrings, menu reference, symbols, the ops portal, and the ops platform do not apply, because no code changes.

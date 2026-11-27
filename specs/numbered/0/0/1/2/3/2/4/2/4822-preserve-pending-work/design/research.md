# Research: Preserve Pending Work Before Branch Cleanup

This record lists each decision with its alternatives and reason. It also lists each remote check and local read. Remote checks use the GitHub API against the default branch. Local reads use read-only Git commands.

## Evidence Rules

- The main commit read for this record is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.
- Ref `main` in the remote table means the default branch.
- A blob SHA of `none` means the path is absent on main.
- A blob SHA of `not applicable` means the check reads an object that is not a blob.
- Local evidence does not prove that GitHub holds an object. Only a remote check proves that.

## Decisions

### D-1 Record route and slug

- Decision: Use the record folder `specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work`.
- Alternatives: A timestamp record under `specs/live/`. A different slug.
- Reason: Issue numbers use the numbered route. The route is free on main (RC-04, RC-05).
- Risk: None known.
- Human decision: No.

### D-2 Hold publication of recovery copies

- Decision: Keep snapshot tags and recovery branches local. Publish only after a secret review and owner approval.
- Alternatives: Publish now as draft pull requests. Push only the tags. Keep copies local with no approval step.
- Reason: The issue forbids a push before a secret review. The repository is public (RC-51). Private output must stay local.
- Risk: Warning: Loss of the local copies cannot be undone from Git.
- Human decision: Yes. Category: credential and data policy. Recommended option: publish after a clean review, as draft pull requests, with owner approval.

### D-3 Archive location disclosure

- Decision: Name each archive only as part of the private recovery store. Publish hashes and counts, not paths.
- Alternatives: Publish literal paths. Publish hashes only. Keep paths in tracked files.
- Reason: The issue forbids publication of operational data. The repository is public (RC-51).
- Risk: A reader must ask the owner for the store location.
- Human decision: No.

### D-4 Deletion command

- Decision: Delete merged local branches with `git branch -d` only. Never use `-D` or the devtools `--delete-branch` option.
- Alternatives: Run `worktree-cleanup merged --delete-branch --apply`. Run `git branch -D`. Delete the branch on GitHub.
- Reason: The `-d` option refuses an unmerged branch. The devtools command runs `-D` at line 237 (RC-80).
- Risk: The `-d` option refuses a squash-merged branch. The branch then stays, and the owner reviews it.
- Human decision: No.

### D-5 Archive ignored output before removal

- Decision: Archive the ignored output of each worktree before any folder removal. Do not rely on the devtools dirty check.
- Alternatives: Trust the devtools dirty check at line 228 (RC-79). Remove folders with no archive of logs and reports.
- Reason: The devtools check runs `git status --porcelain`, which omits ignored files. The issue requires preservation of ignored output.
- Risk: The archive uses storage in the private recovery store.
- Human decision: No.

### D-6 Locked admin directories

- Decision: Close the app sessions. Then run `git worktree prune -v` (RC-81). Do not change permissions or force-delete a directory.
- Alternatives: Use the devtools stale-admin command with its force removal. Widen the folder permissions. Stop the process that holds the lock.
- Reason: The safety section forbids widening permissions (RC-46). A forced delete can leave a partial admin directory.
- Risk: Caution: The lock may persist. The owner reports it as a blocker (B-01).
- Human decision: No.

### D-7 Labs comparison source

- Decision: Compare the Git snapshots now (TST-004). Require the private SHA-256 comparison before publication (T005).
- Alternatives: Accept the owner statement only. Compare only the Git snapshots.
- Reason: The snapshots show 29 identical files. The private folders are the raw copies that the owner names.
- Risk: The private result stays open until the owner runs T005.
- Human decision: No.

### D-8 Keep recovery branch commits unchanged

- Decision: Keep each recovery branch and its commit. Do not rebase or squash.
- Alternatives: Rebase onto current main. Squash each branch into one commit.
- Reason: The issue already publishes the commit identifiers. Each branch holds one commit above `b7a18b7ead7b` (RC-02).
- Risk: Caution: Each branch stays 42 commits behind main. A later merge needs a rebase.
- Human decision: No.

### D-9 Closing keyword and blocker issue

- Decision: Keep `Closes #4822` in the pull request body. Create a blocker issue before the merge.
- Alternatives: Use `Relates to #4822`. Use no closing keyword.
- Reason: The task list of this record requires the closing keyword. A blocker issue keeps open work tracked after the merge closes issue #4822.
- Risk: Caution: The merge closes #4822 before the removal work ends.
- Human decision: No.

### D-10 No changelog fragment

- Decision: Add no changelog fragment. State the reason in the pull request.
- Alternatives: Add `changelog.d/issue-4822-preserve-pending-work.md`.
- Reason: The record change has no user-visible effect. `changelog.d/README.md` line 58 asks for this statement (RC-62).
- Risk: None known.
- Human decision: No.

### D-11 Run recovered tests from exports

- Decision: Export each recovery tree with `git archive` into `test-artifacts/`. Run the tests in that export.
- Alternatives: Add a worktree for each branch. Switch the main checkout. Copy files by hand.
- Reason: The main checkout must stay unchanged (FR-010). The constitution allows the git-ignored `test-artifacts/` folder (RC-55).
- Risk: The export does not include the `.venv`. Run the tests with the existing `.venv`.
- Human decision: No.

### D-12 Mark owner claims as open

- Decision: Record each owner claim as an open item. Do not mark an owner claim as verified.
- Alternatives: Copy the owner claims as verified facts.
- Reason: The agent rules forbid a claim that a gate passed without a run (RC-44).
- Risk: The record lists more open items.
- Human decision: No.

### D-13 Keep recovery branches until publication

- Decision: Keep the four recovery branches until T012 and T013 finish.
- Alternatives: Delete the branches now. The snapshot tags remain, but they name different commits.
- Reason: Each recovery commit is contained by its own recovery branch and by no tag. Warning: Git can remove an unreachable commit during garbage collection.
- Risk: Warning: Deleting a recovery branch makes its commit unreachable from any ref.
- Human decision: No.

### D-14 Exclude the feature state file

- Decision: Exclude `.specify/feature.json` from every restore from a snapshot.
- Alternatives: Restore the file from the http-tests and pdf-dedup snapshots.
- Reason: Read-only commands must not change this file (RC-52).
- Risk: The main feature state stays unchanged.
- Human decision: No.

## Remote Verification

Each row is one remote check. The same 84 checks appear in `STATUS.json`.

| Check | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Main head commit is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` | refs/heads/main | main | not applicable | present | 0 |
| RC-02 | Base commit `b7a18b7ead7b1de5882bcd288203c015b1eef792` is an ancestor of main (compare status ahead, behind 0) | commits/b7a18b7ead7b1de5882bcd288203c015b1eef792 | main | not applicable | present | 0 |
| RC-03 | PR #4823 merge commit `b6347ec7374c2a3c1c8ba1f2482aed52cbc81fe6` is on main (compare status ahead, behind 0) | commits/b6347ec7374c2a3c1c8ba1f2482aed52cbc81fe6 | main | not applicable | present | 0 |
| RC-04 | The 4822 route folder does not exist on main | specs/numbered/0/0/1/2/3/2/4/2/ | main | none | absent | 0 |
| RC-05 | No path on main contains the text 4822 | specs tree filtered for 4822 | main | none | absent | 0 |
| RC-06 | PR #4823 guard for a moved canonical PDF is on main | src/mist/intelligence/juniper_docs/harvest/content_index.py | main | bf1e1fb669efd7b13a821c5b1766e32d4f9753bf | present | 36 |
| RC-07 | PR #4823 refresh helper for a size group is on main | src/mist/intelligence/juniper_docs/harvest/content_index.py | main | bf1e1fb669efd7b13a821c5b1766e32d4f9753bf | present | 51 |
| RC-08 | PR #4823 test for a moved canonical file is on main | tests/unit/juniper_docs/test_content_dedup.py | main | 5aa083f7177ccc92b3208029f79c10c4f44c1db5 | present | 74 |
| RC-09 | PR #4823 test for a remaining duplicate is on main | tests/unit/juniper_docs/test_content_dedup.py | main | 5aa083f7177ccc92b3208029f79c10c4f44c1db5 | present | 87 |
| RC-10 | PR #4823 changelog fragment for issue 2977 is on main | changelog.d/issue-2977-harvest-index-moves.md | main | f1b62abb5238f0d69c5b911f1596bdd281be804d | present | 0 |
| RC-11 | PR #4823 spec file for issue 2977 is on main | specs/numbered/0/0/0/4/3/4/0/2/2977-harvest-index-moves/spec.md | main | 803982a1fd96f8e426ba0404fd13cc6153ab30fc | present | 0 |
| RC-12 | Only one of seven issue 2977 record files is on main | specs/numbered/0/0/0/4/3/4/0/2/2977-harvest-index-moves/ | main | not applicable | partial | 0 |
| RC-13 | No Labs source package is on main | src/interfaces/labs/ | main | none | absent | 0 |
| RC-14 | No Labs integration tests are on main | tests/integration/web_portal/labs/ | main | none | absent | 0 |
| RC-15 | No issue 4631 record is on main | specs/numbered/0/0/1/2/2/0/1/1/4631-offline-jvd-preview/ | main | none | absent | 0 |
| RC-16 | No issue 2746 record is on main | specs/numbered/0/0/0/4/1/4/4/1/2746-fm-http-4xx-repair/ | main | none | absent | 0 |
| RC-17 | No VMM export document is on main | documentation/vmm-editor-export.md | main | none | absent | 0 |
| RC-18 | No issue 4624 changelog fragment is on main | changelog.d/issue-4624-ap-warning-window.md | main | none | absent | 0 |
| RC-19 | No Dynamic JVD live record is on main | specs/live/0/0/0/1/2/1/3/3/0/4/3/0/3/3/0/1/3/20261030-031943-dynamic-jvd-labs/ | main | none | absent | 0 |
| RC-20 | No GitHub branch named chore/2746-recovered-specification | refs/heads/chore/2746-recovered-specification | main | none | absent | 0 |
| RC-21 | No GitHub branch named fix/2977-recovered-content-dedup | refs/heads/fix/2977-recovered-content-dedup | main | none | absent | 0 |
| RC-22 | No GitHub branch named feat/4631-recovered-offline-preview | refs/heads/feat/4631-recovered-offline-preview | main | none | absent | 0 |
| RC-23 | No GitHub branch named docs/4822-recovered-vmm-export | refs/heads/docs/4822-recovered-vmm-export | main | none | absent | 0 |
| RC-24 | No GitHub tag under recovery/4822 | refs/tags/recovery/4822 | main | none | absent | 0 |
| RC-25 | GitHub holds no commit c06ea6ce1bb58a0881719b728677cae9573562c7 | commits/c06ea6ce1bb58a0881719b728677cae9573562c7 | main | not applicable | absent | 0 |
| RC-26 | GitHub holds no commit 591b6b86697ba7c924d9e5238b7ed634f8cec275 | commits/591b6b86697ba7c924d9e5238b7ed634f8cec275 | main | not applicable | absent | 0 |
| RC-27 | GitHub holds no commit a9a2d36dfc7555f0107ec7162d04c6348229c056 | commits/a9a2d36dfc7555f0107ec7162d04c6348229c056 | main | not applicable | absent | 0 |
| RC-28 | GitHub holds no commit 01e0a701608dc82e09403186d2f2eb285fc29f91 | commits/01e0a701608dc82e09403186d2f2eb285fc29f91 | main | not applicable | absent | 0 |
| RC-29 | GitHub holds no snapshot commit 2f549a95ec402c12787ed1020bc4bcc238427178 (ap-report) | commits/2f549a95ec402c12787ed1020bc4bcc238427178 | main | not applicable | absent | 0 |
| RC-30 | GitHub holds no snapshot commit 3507045565bcee50be0e3043f6435fe1f6b7be23 (http-tests) | commits/3507045565bcee50be0e3043f6435fe1f6b7be23 | main | not applicable | absent | 0 |
| RC-31 | GitHub holds no snapshot commit 2b10a07f4580567f2e35091bd6c0f5cc53482db1 (labs-original) | commits/2b10a07f4580567f2e35091bd6c0f5cc53482db1 | main | not applicable | absent | 0 |
| RC-32 | GitHub holds no snapshot commit 6c66f04c21d219cbf936f6c5a03bab891f74dafc (labs-preview) | commits/6c66f04c21d219cbf936f6c5a03bab891f74dafc | main | not applicable | absent | 0 |
| RC-33 | GitHub holds no snapshot commit 61eec0829b28db796901d95aff2472020eef1b53 (pdf-dedup) | commits/61eec0829b28db796901d95aff2472020eef1b53 | main | not applicable | absent | 0 |
| RC-34 | GitHub holds no snapshot commit 69a51a9c63dcd3ee372e84dc3bc2ebc98f61c022 (release) | commits/69a51a9c63dcd3ee372e84dc3bc2ebc98f61c022 | main | not applicable | absent | 0 |
| RC-35 | GitHub holds no snapshot commit 6256c776a7e466d7b95e97196df5a52c51a19545 (requirements) | commits/6256c776a7e466d7b95e97196df5a52c51a19545 | main | not applicable | absent | 0 |
| RC-36 | GitHub holds no snapshot commit 61de973cfd6375898b7bb9319ca08ad49240f247 (sync) | commits/61de973cfd6375898b7bb9319ca08ad49240f247 | main | not applicable | absent | 0 |
| RC-37 | GitHub holds no snapshot commit f4d8922b838e6f83f428e3bcb7171584638d410e (vmm) | commits/f4d8922b838e6f83f428e3bcb7171584638d410e | main | not applicable | absent | 0 |
| RC-38 | Owner comment 6961771807 exists on issue 4822 | issues/comments/6961771807 | main | not applicable | present | 0 |
| RC-39 | Owner comment 6962335264 exists on issue 4822 | issues/comments/6962335264 | main | not applicable | present | 0 |
| RC-40 | Owner comment 6968818805 exists on issue 4822 | issues/comments/6968818805 | main | not applicable | present | 0 |
| RC-41 | Owner comment 6962287755 exists on issue 2746 | issues/comments/6962287755 | main | not applicable | present | 0 |
| RC-42 | Owner comment 6962287494 exists on issue 4631 | issues/comments/6962287494 | main | not applicable | present | 0 |
| RC-43 | Owner comment 6962288232 exists on issue 4504 | issues/comments/6962288232 | main | not applicable | present | 0 |
| RC-44 | AGENTS.md section Report honestly exists | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 31 |
| RC-45 | AGENTS.md section Writing style exists | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| RC-46 | AGENTS.md section Safety forbids widening permissions | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 157 |
| RC-47 | AGENTS.md section on preservation proof exists | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 271 |
| RC-48 | AGENTS.md section Specifications exists | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 345 |
| RC-49 | Copilot instructions section Local gates exists | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| RC-50 | Copilot instructions STE gate command exists | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| RC-51 | Copilot instructions state that MistHelper is a public repository | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 478 |
| RC-52 | Copilot instructions forbid read-only commands from changing feature.json | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 169 |
| RC-53 | Constitution Principle I, the five-item rule and the managed route | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-54 | Constitution Principle IV, the full deployment pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| RC-55 | Constitution allows the git-ignored test-artifacts folder | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 328 |
| RC-56 | Constitution version 1.9.0 | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 562 |
| RC-57 | Contributing guide section Branch cleanup exists | documentation/contributing.md | main | 3b455b6d6730e16972540f14f7f654462b1c27bd | present | 52 |
| RC-58 | Contributing guide forbids deleting a branch with no pull request | documentation/contributing.md | main | 3b455b6d6730e16972540f14f7f654462b1c27bd | present | 54 |
| RC-59 | Contributing guide step three deletes a branch only after a pull request | documentation/contributing.md | main | 3b455b6d6730e16972540f14f7f654462b1c27bd | present | 79 |
| RC-60 | Development setup removes the worktree after the merge | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 187 |
| RC-61 | Stranded branch review states that a dangling commit is not a backup | documentation/stranded-branch-review.md | main | 8091539c31ff8648d0426f4a8a92e01e0eb902b4 | present | 43 |
| RC-62 | Changelog README says to add no fragment for an internal-only change | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| RC-63 | Pull request template exists | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 0 |
| RC-64 | Spec route function Resolve-SpecFeaturePath exists | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 34 |
| RC-65 | Spec template exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| RC-66 | Plan template exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| RC-67 | Tasks template exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| RC-68 | Checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| RC-69 | Reference record spec file exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-70 | Reference record tasks file exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/tasks.md | main | 72bd85483706269fdf809322b2dca38a0e1d5698 | present | 0 |
| RC-71 | Spec route guard test exists | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 0 |
| RC-72 | Process folder guard test exists | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 0 |
| RC-73 | Process folder baseline file exists | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| RC-74 | STE linter configuration exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| RC-75 | STE writing guide exists | documentation/ASD-STE100_writing-guide.md | main | b464165aae116a17bb3031d3cef9b84a95589c0a | present | 0 |
| RC-76 | Bootstrap script runs a locked uv sync | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 466 |
| RC-77 | Lock file uv.lock exists | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 0 |
| RC-78 | Runtime requirements file exists | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 0 |
| RC-79 | Devtools dirty check runs git status porcelain | .venv\Lib\site-packages\misthelper_devtools\worktree_cleanup.py | local .venv | not applicable | present | 228 |
| RC-80 | Devtools branch deletion runs branch -D | .venv\Lib\site-packages\misthelper_devtools\worktree_cleanup.py | local .venv | not applicable | present | 237 |
| RC-81 | Devtools prune runs git worktree prune -v | .venv\Lib\site-packages\misthelper_devtools\worktree_cleanup.py | local .venv | not applicable | present | 248 |
| RC-82 | Quality gates guide section The writing gate exists | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 277 |
| RC-83 | Quality gates guide gives the local writing gate command | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 283 |
| RC-84 | Quality gates guide requires each file to pass in both modes | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 290 |

## Local Evidence

Local reads are not remote proof. The commits below match the remote checks where a remote row exists.

### Snapshot inventory

Each snapshot is the commit that a snapshot tag names. Each parent is the commit that the snapshot follows. File counts compare each snapshot with its parent.

| Snapshot | Commit | Parent | Parent state | Files | Identical to main | Different from main | Absent from main |
| - | - | - | - | - | - | - | - |
| ap-report | 2f549a95ec40 | d29cfd3984bc | Tip of `agents/ok-make-that-change-then-reun-that-report`. Git merges it into main. | 18 | 6 | 11 | 1 |
| http-tests | 3507045565bc | 93ce37ef692f | No local branch | 4 | 0 | 1 | 3 |
| labs-original | 2b10a07f4580 | 87d74a673d30 | No local branch | 29 | 0 | 1 | 28 |
| labs-preview | 6c66f04c21d2 | 02d7d1798d9d | Tip of `feat/4631-offline-jvd-preview`. Git merges it into main. | 31 | 0 | 1 | 30 |
| pdf-dedup | 61eec0829b28 | 93ce37ef692f | No local branch | 10 | 2 | 2 | 6 |
| release | 69a51a9c63dc | 8dd9998f10cb | No local branch | 0 | 0 | 0 | 0 |
| requirements | 6256c776a7e4 | 0cde9362c499 | No local branch | 2 | 0 | 2 | 0 |
| sync | 61de973cfd63 | 6ea93b107455 | Tip of `jmorrison-juniper-github-sync-update-merge`. Git merges it into main. | 0 | 0 | 0 | 0 |
| vmm | f4d8922b838e | 87d74a673d30 | No local branch | 1 | 0 | 0 | 1 |

The `ap-report` differences are these files. Eleven files differ. Six match main. One is absent, `changelog.d/issue-4624-ap-warning-window.md`. The differing files are `documentation/ap-warning-report.md`, four files of the issue 4590 record, `src/foundation/support/refactors/endpoint_primary_key_strategies.py`, `src/operations/exporting/ap_warning_report/client.py`, `src/operations/exporting/ap_warning_report/codes.py`, and three unit test files.

The `pdf-dedup` snapshot differs in `.specify/feature.json` and in the issue 2977 `spec.md`. Six of its files are absent from main.

### Recovery branch inventory

| Branch | Tip | Base | Commits above base | Changed files |
| - | - | - | - | - |
| chore/2746-recovered-specification | c06ea6ce1bb5 | b7a18b7ead7b | 1 | 3 added |
| fix/2977-recovered-content-dedup | 591b6b86697b | b7a18b7ead7b | 1 | 7 added and 2 modified |
| feat/4631-recovered-offline-preview | a9a2d36dfc75 | b7a18b7ead7b | 1 | 30 added and 1 modified |
| docs/4822-recovered-vmm-export | 01e0a701608d | b7a18b7ead7b | 1 | 1 added |

Each recovery branch starts at `b7a18b7ead7b`. Main holds 42 commits that the branches lack. No tag contains any recovery commit.

### Labs comparison

- The `labs-original` snapshot has 29 paths. The `labs-preview` snapshot contains the same 29 paths with identical blobs. The result is 29 identical, zero different, and zero absent.
- The `labs-preview` snapshot adds two issue 4631 record files.
- The private folder comparison remains open (T005).

### Shared issue 2977 source

The blobs of `src/mist/intelligence/juniper_docs/harvest/content_index.py` and `tests/unit/juniper_docs/test_content_dedup.py` are identical in three places. The places are the `pdf-dedup` snapshot, the recovery branch, and main (RC-06 and RC-08).

The main `spec.md` for issue 2977 differs from the snapshot by three insertions and three deletions.

### Registrations and merge state

- `git worktree list` reports 34 entries. One is the main checkout.
- Two linked entries are prunable. Their folders are gone, and their admin directories remain.
- `dynamic-jvd-labs-offline-preview` names `feat/4631-offline-jvd-preview`. The branch tip is `02d7d1798d9d5ab17d9de33da122d0b224adaf64`. It has zero commits above main and 98 below.
- `ok-make-that-change-then-reun-that-report` names `agents/ok-make-that-change-then-reun-that-report`. The tip is `d29cfd3984bcd00074d7b73c6d786be9edce249c`. It has zero commits above main and 100 below.
- One live registration names `jmorrison-juniper-github-sync-update-merge`. The tip is `6ea93b1074550ea5d89fbdb661e3c3b6e00cc38b`. It has zero commits above main and 425 below.
- No pull request names any of the three branch heads. The GitHub search returned zero pull requests for each.
- The repository has 330 local branches. Only the branches named in this record are in scope.

### Requirements snapshot

The `requirements` snapshot changes `requirements.txt` by three insertions and three deletions. It changes `uv.lock` by 40 insertions and 38 deletions.

### Devtools behavior

- `_plan_worktree` removes a worktree only when its branch is merged or squash-merged. It also requires a clean `git status --porcelain` result (RC-79).
- `_delete_branch` runs `git branch -D` (RC-80).
- `_prune` runs `git worktree prune -v` (RC-81).
- The command reports dry-run plans unless `--apply` appears.

## Research Items

- R1 Issue facts. The issue body and three owner comments state the scope and the claims. The comments are RC-38 to RC-40.
- R2 Linked pull request. PR #4823 merged on 2026-11-19 and carries the issue 2977 source and one record file. Its body says `Relates to #2977 and #4822`.
- R3 Legacy record. No folder name starts with 4822 on main or in the local checkout. The route is free (RC-04, RC-05).
- R4 Remote scope. The remote check reads the default branch tree at `f03c6c9`. The tree has 11,404 entries and no truncation.
- R5 Snapshot inventory. The nine tags exist locally. Their commits have one parent each. Their file counts are in the snapshot table.
- R6 Labs comparison. The Labs snapshots agree on 29 paths. The private folders stay open (D-7).
- R7 Registrations. The two prunable admin directories are the two blocked directories from the owner comment.
- R8 Devtools command. The cleanup command does not read ignored files, and it force-deletes branches with `-D`. The record uses its dry-run output only, if at all (D-4, D-5).
- R9 Repository rules. The contributing guide requires a pull request before deletion (RC-57 to RC-59). The stranded branch review says a dangling commit is not a backup (RC-61).
- R10 Writing and changelog rules. The writing gate and the changelog rule apply to this record (RC-62, RC-82 to RC-84).
- R11 Route. The base-5 digits of 4822 are 1, 2, 3, 2, 4, 2. Padded to eight digits, the route is 0, 0, 1, 2, 3, 2, 4, 2. The constitution requires this fixed route (RC-53). The route for issue 4920 uses the same rule (RC-69).

## Repository Rules

- Warning: Deleting a branch that reached no pull request destroys its only copy (RC-58).
- A dangling commit is not a backup. Warning: Git can remove an unreachable object (RC-61).
- A preservation proof names a merged replacement pull request, a surviving remote branch, or a pushed recovery branch or tag (RC-47).
- Do not widen file permissions to repair a permission error (RC-46).
- Each record file must pass the writing gate in each mode (RC-82, RC-83, RC-84).
- A change with no user-visible effect adds no changelog fragment (RC-62).

## Skills, Mist API, and Other Sources

- Skills: none loaded. The issue has no Podman question and no Juniper device question.
- Mist API and mistapi: not used. No claim in this record depends on them.
- `documentation/quality-gates.md`: read in the writing gate section (RC-82 to RC-84).
- `documentation/operator-guide.md`: searched for backup and recovery terms. The only match describes menu 306, which is out of scope.
- `documentation/architecture.md` and `documentation/container-deployment.md`: not read. No claim in this record depends on them.
- Web sources: none fetched. The record cites no upstream URL.

## Unverified

Each item below remains open. This record did not verify it, and the reason is stated.

- U-01 Archive SHA-256 values and entry counts. The private store is outside this agent's access.
- U-02 The private Labs folder comparison. The private store is outside this agent's access.
- U-03 The bundle verification and restore counts. The bundle is in the private store.
- U-04 The names and pull request state of the four removed branches. The public record does not name them, and no tool output names them.
- U-05 The identity of the three old session or release branches named in the issue body. The issue body and its comments give no names.
- U-06 The ignored output inside each worktree folder. The folders moved to the private store.
- U-07 The owner statement that the VMM registration stays broken. No current registration names VMM.
- U-08 The owner statements of 50,654 file entries, 122,022 Git objects, and 2,142 references. The private store holds these values.
- U-09 The owner statement that 414 `.github` entries match main. This record did not count them.
- U-10 The writing gate scores of the record files. This agent ran no linter.
- U-11 The cause of the bootstrap failure the owner reports. This agent ran no command.
- U-12 The meaning of the three-line difference in the issue 2977 `spec.md`. The content review is open.
- U-13 Whether the issue 4624 content in the `ap-report` snapshot belongs on main. The content review is open.
- U-14 Whether an app session still uses the folder of the `sync` branch. No session data is available here.
- U-15 The owner-reported test counts of 43 passed and 1 skipped. This agent ran no test.
- U-16 Gate coverage for Git and GitHub evidence tasks. The local gates table has no row for them (F-17).

## Sources

Repository files read, with the remote blob SHA recorded in the remote table:

- `AGENTS.md`, sections Your role, Report honestly, Writing style, Safety, Specifications, and the preservation rule.
- `.github/copilot-instructions.md`, sections Local gates, the read-only rule, and the public repository statement.
- `.specify/memory/constitution.md`, Principle I, Principle IV, the Data Directory rule, and the version line.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`.
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md`, `tasks.md`, and `design/research.md`. These files give the shape only, and no content was copied.
- `documentation/contributing.md`, the Branch cleanup section.
- `documentation/stranded-branch-review.md`, the dangling commit section.
- `documentation/development-setup.md`, the Work on a change section.
- `documentation/quality-gates.md`, the writing gate section.
- `changelog.d/README.md`, the rule list.
- `.specify/scripts/powershell/spec-route.ps1`, the function declaration.
- `.venv\Lib\site-packages\misthelper_devtools\worktree_cleanup.py`, the command, the dirty check, the branch deletion, and the prune.

Remote reads use the GitHub tree of `main` and the contents API for each cited file. The compare API checks the base and merge commits. Branch, commit, tag, and comment endpoints check the recovery copies. Pull request endpoints check PR #4823.

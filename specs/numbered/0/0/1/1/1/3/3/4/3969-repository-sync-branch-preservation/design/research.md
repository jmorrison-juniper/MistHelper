# Research: Repository Sync Branch Preservation

Each decision names the chosen option, the reason, the other options, and the risk. Remote checks read GitHub. Local checks read this clone. Sources name local paths with line numbers or URLs.

## Evidence snapshot

- Checked: 2026-11-27 UTC. This is the evening of 2026-11-26 in UTC-6. Every check read data only.
- Clone: C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper. HEAD equals main at f03c6c9b36d612a48d7b9652998c2fd87dd777ca.
- GitHub repository: jmorrison-juniper/MistHelper.
- Sync window: 2026-10-06T08:00Z to 2026-10-06T10:00Z. The report start time is 2026-10-06T08:29Z.
- One large pull request query returned HTTP 504. The record uses smaller queries for each result.

## Decisions

### D-1 Scope of this run

- **Decision**: Write the record only. Change no branch, tag, or pull request in this run.
- **Rationale**: The author role is read-only. The owner has not confirmed the claim. The report asks for verification before any cleanup.
- **Alternatives considered**: Run the cleanup now. Rejected, because the author role forbids writes and the worktree state is unverified. Post a summary comment only. Rejected, because the owner needs a runnable plan with gates.
- **Risk**: The owner must run the tasks. Mitigation: design/quickstart.md gives each command.
- **Human decision**: Not required.

### D-2 Preservation mechanism

- **Decision**: Use lightweight tags under archive/preservation. Each tag name starts with 3969-, then the branch slug, then the UTC date in YYYYMMDD form.
- **Rationale**: The repository already holds tags in archive/preservation (R91). AGENTS.md accepts a pushed tag as proof (R15). A tag keeps its commits. A tag creates no branch, so stranded-branch-report (R22) does not list it.
- **Alternatives considered**: Recovery branches under recovery/3969. Rejected, because stranded-branch-report reports each branch with no pull request (R22). Original branch names. Rejected, because AGENTS.md forbids a push to a branch that another agent owns (R11). Annotated tags. Rejected, because this record needs no tag message. A new namespace named preserve. Rejected, because a second namespace splits the audit trail.
- **Risk**: The tag count grows by 181. Mitigation: the prefix 3969- groups every new tag for later review.
- **Human decision**: Not required.

### D-3 Tag scope

- **Decision**: Create 129 tags at class C tips and 47 tags at class D tips. Create 5 tags at the heads of pull requests #3954, #3955, #3956, #3957, and #3973. Classes A, B, and E need no tag.
- **Rationale**: Class C and class D tips can hold commits that GitHub does not hold as a branch (L3, R89). The five heads have no GitHub branch, or the branch differs from the head (R93 to R96, L5). Class A commits lie in origin/main (L8). Class B tips equal a merged pull request head (L3). Class E commits have equivalent patches on origin/main (L9).
- **Alternatives considered**: Tag only the 12 branches that the report names. Rejected, because 47 class D branches hold unique patches. Tag every local branch. Rejected, because 135 class B tips add tags without a gain.
- **Risk**: 67 class C pull request heads are absent from the local object store (L4). The tag uses the local tip, so the tag does not depend on those heads.
- **Human decision**: Not required.

### D-4 Deletion gates

- **Decision**: Delete classes A and B after their rechecks. Delete classes C and D after the tag check. Delete class E after a recheck with no merge commit and one minus line. Keep class F. The plan deletes 322 local branches.
- **Rationale**: Each gate tests the commits that the deletion removes. A name match alone misleads (DEF-3). The git-branch reference says `--merged` lists branches whose tip commits are reachable from the named commit (https://git-scm.com/docs/git-branch). Class B and class C tips are not reachable from origin/main. Each merged match has commits beyond origin/main (L3). A merge test therefore does not cover them.
- **Alternatives considered**: Delete every branch whose name matches a merged pull request. Rejected, because fix/2746-fm-http-status matches merged #3077, while its tip equals the head of closed #3956 (L5). Keep every local branch. Rejected, because the cleanup goal needs local cleanup, and the gates protect the commits. Use the merge test for every class. Rejected, for the reason above.
- **Risk**: A deletion removes a branch that a worktree uses. Mitigation: gate G3 and decision D-5.
- **Human decision**: Not required.

### D-5 Worktree inventory and modified paths

- **Decision**: The owner records the worktree inventory before any deletion. The owner decides each discard. The default keeps every modified path.
- **Rationale**: The five modified paths hold edits that no commit records (L1). AGENTS.md tells an agent to leave a file that it did not change (R09). This record cannot observe worktrees (U-1).
- **Alternatives considered**: Discard the five modified paths. Rejected, because the paths belong to other work. Warning: a discard removes their edits. Commit the five modified paths. Rejected, because the author role cannot commit, and the owner decides the content.
- **Risk**: Warning: a discarded modified path loses its edits. Mitigation: the owner approves each discard in writing.
- **Human decision**: HUMAN-DECISION-REQUIRED. Category: destruction of data. The edits exist only in the working tree.

### D-6 Disposition of fix/3217-access-log-fields-update

- **Decision**: Preserve the branch with a tag under D-3. Keep the tag until the owner confirms the disposition.
- **Rationale**: The branch has 3 commits that GitHub does not hold (L7). Its name has no GitHub branch and no pull request (R49). Merged pull request #3778 used the head fix/3217-access-log-fields, which differs from this branch (R98, L6).
- **Alternatives considered**: Discard the branch. Rejected. Warning: a discard removes 3 unique commits. Treat pull request #3778 as proof. Rejected, because the tip of fix/3217-access-log-fields-update has 3 commits beyond the pull request head. Its tip also lacks 29 head commits (L6).
- **Risk**: The owner must still confirm the disposition. Mitigation: the tag keeps the commits.
- **Human decision**: Not required.

### D-7 Write claim

- **Decision**: One writer at a time. The writer comments one claim on issue #3969 before any write. The report's claim is not reused, because its session state cannot be observed.
- **Rationale**: The issue body describes a stop caused by another sync session (R88). Claim first is the repository rule (R27).
- **Alternatives considered**: Reuse the report's named session. Rejected, because its state is unverifiable (U-2). Let each run claim on arrival. Rejected, because that rule created the collision that the report describes.
- **Risk**: A claim comment can go stale. Mitigation: the writer comments the release when the writer finishes.
- **Human decision**: Not required.

### D-8 Container refresh

- **Decision**: Refresh the misthelper service after the claim is released. Use the service name with the --no-deps option. Never remove a named volume. Never run a prune command. Check both named volumes after the refresh.
- **Rationale**: The volumes hold every capture and every upgrade run (R19). The caution at R21 names the --no-deps option. AGENTS.md forbids prune commands on a shared host (R01). Warning: direct storage deletion can destroy data, according to the loaded container-storage skill. The same skill says that consumers must stop before backend maintenance.
- **Alternatives considered**: Refresh now. Rejected, because the container state is unverified (U-3), and another agent owns the container. Skip the refresh. Rejected, because the report names the refresh as a skipped step that the owner must review.
- **Risk**: Warning: a refresh during a capture can stop the capture. Mitigation: the owner confirms that no capture runs before the refresh.
- **Human decision**: Not required.

### D-9 Verification commands

- **Decision**: Each sync task names a read-only command from design/quickstart.md. The STE gate runs on the record files. No other gate applies.
- **Rationale**: The local gates table (R17) has no gate for branch or tag state. Its STE row names Markdown files.
- **Alternatives considered**: Add a new repository gate. Rejected, because a new gate needs a code change and its own record. Use stranded-branch-report for branch checks. Rejected, because its arguments are unverified (U-9), and the workflow runs on a schedule (R22).
- **Risk**: The owner may reject the read-only command set. Mitigation: analysis item U-GAP-1.
- **Human decision**: Not required.

### D-10 Record shape

- **Decision**: Omit the contracts folder. Include data-model.md and one requirements checklist.
- **Rationale**: The record changes no menu, command, API request, or output format. The reference record holds a contracts folder because its feature changes an interface (L12).
- **Alternatives considered**: Add a tag-name contract. Rejected, because FR-004 and D-2 already state the tag rule.
- **Risk**: A reviewer expects contracts. Mitigation: plan.md states the omission.
- **Human decision**: Not required.

### D-11 Metadata

- **Decision**: Set size L. Add labels stage:speckit-artifacts-emitted and needs-human-review. Remove label needs-investigation. Link issue #2295 as a related issue.
- **Rationale**: The work covers 329 local branches, 14 pull requests, 106 remote checks, and one human decision. The three labels exist in the repository label list (R106). The investigation step completes with this record. The human decision remains.
- **Alternatives considered**: Keep needs-investigation. Rejected, because this record completes the investigation step.
- **Risk**: The owner disagrees with the label change. Mitigation: the orchestrator can reverse each label change.
- **Human decision**: Not required.

## Report claims against current state

| # | Sync report claim (2026-10-06) | Current result | Evidence |
| - | - | - | - |
| 1 | 268 local branches | 330 refs under refs/heads, including main. 329 besides main | L2 |
| 2 | 15 linked worktrees | Unverified. The author role cannot run git worktree | U-1 |
| 3 | 2 dirty worktrees | Unverified | U-1 |
| 4 | 18 uncommitted paths in the main checkout | 5 modified paths | L1 |
| 5 | Main checkout 158 commits behind origin/main | 0 behind. Local HEAD equals GitHub main | R45, L1 |
| 6 | 217 branches with squash-merged work | 264 local branches match a merged pull request head name | L3, R89 |
| 7 | 4 branches belong to a closed pull request | Each name matches a closed unmerged pull request. All four are absent on GitHub | R61 to R64, L3 |
| 8 | 14 branches hold commits that no remote holds | 58 local branches have no pull request and no GitHub branch. 47 hold unique patches. 7 hold patch-equivalent commits only. 4 hold no commit beyond origin/main | L3, R89 |
| 9 | 2 branches carry no new patch | Both confirmed. A third branch, test/2743-timeout-failure-mode, also carries no new patch | R59, R60, R63, L7 |
| 10 | 12 unpublished branches | All 12 are absent on GitHub, have no pull request, and hold unique patches | R47 to R58, L7 |
| 11 | PR #3967, #3964, and #3963 are BEHIND | All three merged on 2026-10-06 | R70 to R72 |
| 12 | PR #3966 fails the E2E smoke tests | Merged on 2026-10-06. Its 45 checks pass | R73 |
| 13 | PR #3965 has no conclusion | Merged on 2026-10-06 | R74 |
| 14 | PR #3961, #3933, and #3928 are BLOCKED | All three merged on 2026-10-06 | R75 to R77 |
| 15 | PR #3958, #3957, #3956, #3955, and #3954 are DIRTY drafts | All five closed without a merge | R79 to R83 |
| 16 | PR #3820 is DIRTY | Merged on 2026-10-06 | R78 |
| 17 | Branch protection requires strict checks, linear history, and admin enforcement, with no review | Confirmed | R44 |
| 18 | The sync run pushed 0 branches, created 0 pull requests, and merged 0 pull requests | In the sync window, 2 pull requests were created and 4 were merged, all by the owner account. The run's share is unverified | R84, R85, R86, U-4 |
| 19 | The Podman refresh was skipped, and the pod belongs to the owning agent | Unverified. The governing documents contain no word "pod" | U-3, L10 |
| 20 | fix/3217-access-log-fields-update is absent on GitHub and has no pull request | Confirmed. The branch holds 3 unique patches | R49, L6, L7 |
| 21 | Coordination issue #2295 | Closed. Its body asks to keep it open. It does not list #3969 | R87 |
| 22 | Two sessions run in this repository | Local branch jmorrison-juniper-github-sync-update-merge has no commit beyond origin/main. Branch jmorrison-jnpr-didactic-robot is not a local ref | R68, R69, L8, U-5 |
| 23 | Five more worktrees changed files | Unverified | U-1 |

## Remote verification table

Each row is one remote check. Blob or commit values are full SHAs unless the row shows ten characters. Ten-character values abbreviate pull request head commits. The value `none` marks an object that GitHub did not return. Line 0 marks a check with no file line.

| Row | Claim | Path | Ref | Blob or commit SHA | Result | Line |
| - | - | - | - | - | - | - |
| R01 | Shared host: no system prune or volume prune | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 169 |
| R02 | Secrets stay in environment variables | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 174 |
| R03 | Branch name uses type/issue-slug | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 194 |
| R04 | Commit messages use Conventional Commits | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 210 |
| R05 | Pull request body names the closed issue | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 224 |
| R06 | Wait for checks with gh pr checks and the watch option | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 229 |
| R07 | Squash merge only, and never push to main | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 235 |
| R08 | A commit pushed after a squash merge becomes an orphan | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 239 |
| R09 | Run git status before editing a shared file | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 248 |
| R10 | No staging, reset, or clean in a shared checkout | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 251 |
| R11 | No push to a branch owned by another agent | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 254 |
| R12 | Handoff goes in a comment, and a comment is not replaced | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 260 |
| R13 | Conflict over 20 lines: abandon the branch and restart from main | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 268 |
| R14 | Preserve work before closing an unmerged pull request | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 271 |
| R15 | Proof is a surviving remote branch or a pushed tag | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 274 |
| R16 | Remove a branch only after a second copy keeps the work | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 275 |
| R17 | STE gate command row in the local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| R18 | Spec Kit records use managed roots and the base-5 route | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 159 |
| R19 | Volumes hold every capture and upgrade run. Warning: removing a volume is not recoverable | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 347 |
| R20 | Build and start the product container with the compose script | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 405 |
| R21 | Caution: start the service with the --no-deps option | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 415 |
| R22 | stranded-branch-report flags a branch with no pull request | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 475 |
| R23 | Pitfall: GH_TOKEN or GITHUB_TOKEN may name another account | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 546 |
| R24 | Five-Item Rule for each hierarchy level | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R25 | Managed specs roots and the route | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 57 |
| R26 | Test containers join the compose group | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 303 |
| R27 | Claim first in the multi-agent workflow | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 500 |
| R28 | Each change gets its own worktree and branch | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 178 |
| R29 | Worktree removal command | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 191 |
| R30 | Test and debug containers section | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 141 |
| R31 | The route base is 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R32 | The route digits run from the most significant place | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 25 |
| R33 | Spec template is present | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| R34 | Plan template is present | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| R35 | Tasks template is present | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| R36 | Checklist template is present | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| R37 | Stranded-branch workflow is present | .github/workflows/stranded-branch-report.yml | main | 0fde8b4e98edcc111425e3a385e42075cf43595f | present | 0 |
| R38 | Compose file is present | compose.yml | main | b3944fc9f994ca149974072b1a9c8f13797d7924 | present | 0 |
| R39 | Compose script is present | scripts/compose.ps1 | main | d58a2b1065d53ce9ae971a733e09aec3cbbcc6a5 | present | 0 |
| R40 | Process folder baseline is present | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| R41 | STE linter configuration is present | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| R42 | Reference record specification is present | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| R43 | Reference record research is present | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/research.md | main | 2e4aaa714e56fff7f96a2af9e686e9f5c06224a7 | present | 0 |
| R44 | Branch protection on main: strict checks, linear history, admins enforced, no review required | branches/main/protection | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R45 | Local HEAD equals GitHub main | compare (base f03c6c9b36d612a48d7b9652998c2fd87dd777ca, head main) | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R46 | GitHub holds 598 branches, including main | branches | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R47 | Named branch backup/3671-pre-subject-rewrite-20261003 is absent on GitHub | refs/heads/backup/3671-pre-subject-rewrite-20261003 | main | none | absent | 0 |
| R48 | Named branch rescue/code-misthelper-dirty-20260912 is absent on GitHub | refs/heads/rescue/code-misthelper-dirty-20260912 | main | none | absent | 0 |
| R49 | Named branch fix/3217-access-log-fields-update is absent on GitHub | refs/heads/fix/3217-access-log-fields-update | main | none | absent | 0 |
| R50 | Named branch fix/3745-webhook-delivery-refusals-local is absent on GitHub | refs/heads/fix/3745-webhook-delivery-refusals-local | main | none | absent | 0 |
| R51 | Named branch fix/3745-webhook-delivery-refusals-push is absent on GitHub | refs/heads/fix/3745-webhook-delivery-refusals-push | main | none | absent | 0 |
| R52 | Named branch jmorrison-juniper-fix/3390-confirm-strategy-wording is absent on GitHub | refs/heads/jmorrison-juniper-fix/3390-confirm-strategy-wording | main | none | absent | 0 |
| R53 | Named branch pr/3933/chore/3896-symbol-guard-merge-base-2 is absent on GitHub | refs/heads/pr/3933/chore/3896-symbol-guard-merge-base-2 | main | none | absent | 0 |
| R54 | Named branch pr3781-rebase is absent on GitHub | refs/heads/pr3781-rebase | main | none | absent | 0 |
| R55 | Named branch repair/3802-quality is absent on GitHub | refs/heads/repair/3802-quality | main | none | absent | 0 |
| R56 | Named branch chore/2689-sdk-guard is absent on GitHub | refs/heads/chore/2689-sdk-guard | main | none | absent | 0 |
| R57 | Named branch copilot/vscode-mu2wi6bp-23x9 is absent on GitHub | refs/heads/copilot/vscode-mu2wi6bp-23x9 | main | none | absent | 0 |
| R58 | Named branch backup/main-local-2026-09-24 is absent on GitHub | refs/heads/backup/main-local-2026-09-24 | main | none | absent | 0 |
| R59 | Named branch agents/kms-optic-health-ping-commands is absent on GitHub | refs/heads/agents/kms-optic-health-ping-commands | main | none | absent | 0 |
| R60 | Named branch tmp/2729-rebase is absent on GitHub | refs/heads/tmp/2729-rebase | main | none | absent | 0 |
| R61 | Named branch fix/2566-scheduled-reboot-settle is absent on GitHub | refs/heads/fix/2566-scheduled-reboot-settle | main | none | absent | 0 |
| R62 | Named branch test/2743-missing-failure-modes is absent on GitHub | refs/heads/test/2743-missing-failure-modes | main | none | absent | 0 |
| R63 | Named branch test/2743-timeout-failure-mode is absent on GitHub | refs/heads/test/2743-timeout-failure-mode | main | none | absent | 0 |
| R64 | Named branch test/3149-harness-scope is absent on GitHub | refs/heads/test/3149-harness-scope | main | none | absent | 0 |
| R65 | Named branch feat/3357-marvis-alarm-acknowledge is absent on GitHub | refs/heads/feat/3357-marvis-alarm-acknowledge | main | none | absent | 0 |
| R66 | Named branch chore/3910-stale-comments is absent on GitHub | refs/heads/chore/3910-stale-comments | main | none | absent | 0 |
| R67 | Named branch jmorrison-juniper-chore/3718-websocket-constitution is absent on GitHub | refs/heads/jmorrison-juniper-chore/3718-websocket-constitution | main | none | absent | 0 |
| R68 | Named branch jmorrison-juniper-github-sync-update-merge is absent on GitHub | refs/heads/jmorrison-juniper-github-sync-update-merge | main | none | absent | 0 |
| R69 | Named branch jmorrison-jnpr-didactic-robot is absent on GitHub | refs/heads/jmorrison-jnpr-didactic-robot | main | none | absent | 0 |
| R70 | Report state BEHIND for PR 3967 is current | pulls/3967 | main | fbf9fc2605 | stale | 0 |
| R71 | Report state BEHIND for PR 3964 is current | pulls/3964 | main | 531e9428ba | stale | 0 |
| R72 | Report state BEHIND for PR 3963 is current | pulls/3963 | main | fb3be911ce | stale | 0 |
| R73 | Report state FAILURE for PR 3966 is current | pulls/3966 | main | cfff5c1873 | stale | 0 |
| R74 | Report state with no conclusion for PR 3965 is current | pulls/3965 | main | 4e37301d56 | stale | 0 |
| R75 | Report state BLOCKED for PR 3961 is current | pulls/3961 | main | babb5daabe | stale | 0 |
| R76 | Report state BLOCKED for PR 3933 is current | pulls/3933 | main | bd951943bf | stale | 0 |
| R77 | Report state BLOCKED for PR 3928 is current | pulls/3928 | main | 7ca8b0fc27 | stale | 0 |
| R78 | Report state DIRTY for PR 3820 is current | pulls/3820 | main | ab4b11b501 | stale | 0 |
| R79 | Report state DIRTY draft for PR 3958 is current | pulls/3958 | main | c5846e4d08 | stale | 0 |
| R80 | Report state DIRTY draft for PR 3957 is current | pulls/3957 | main | 2569a15adb | stale | 0 |
| R81 | Report state DIRTY draft for PR 3956 is current | pulls/3956 | main | 94cc4e17db | stale | 0 |
| R82 | Report state DIRTY draft for PR 3955 is current | pulls/3955 | main | 21d2d65598 | stale | 0 |
| R83 | Report state DIRTY draft for PR 3954 is current | pulls/3954 | main | 560f0eff31 | stale | 0 |
| R84 | Two PRs created in the sync window, #3968 and #3971, both by the owner account | search of pull requests created in the sync window | main | none | partial | 0 |
| R85 | Four PRs merged in the sync window, #3961, #3963, #3964, and #3965 | search of pull requests merged in the sync window | main | none | partial | 0 |
| R86 | Four main commits in the sync window, each a squash merge of a PR in R85 | commits (sha main, sync window) | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | partial | 0 |
| R87 | Coordination issue #2295 names the sync coordination record, and its body asks to keep it open | issues/2295 | main | none | partial | 0 |
| R88 | Issue #3969 body and both owner comments name no workflow run | issues/3969 | main | none | absent | 0 |
| R89 | Report counts for local branches, squash matches, and unpublished branches are current | refs/heads (local clone, compared with GitHub PR lists) | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | stale | 0 |
| R90 | Preservation tags for issue #3969 exist | refs/tags/archive/preservation/3969- | main | none | absent | 0 |
| R91 | Namespace archive/preservation is in use | refs/tags/archive/preservation/ | main | none | present | 0 |
| R92 | Pull request 3958 head branch exists on GitHub | refs/heads/recovery/3151-portal-controls-wip | main | c5846e4d08 | present | 0 |
| R93 | Pull request 3957 head branch is absent on GitHub | refs/heads/test/3164-harness-controls | main | none | absent | 0 |
| R94 | Pull request 3956 head branch is absent on GitHub | refs/heads/fix/2746-fm-http-status | main | none | absent | 0 |
| R95 | Pull request 3955 head branch is absent on GitHub | refs/heads/refactor/2926-portal-handlers-c | main | none | absent | 0 |
| R96 | Pull request 3954 head branch is absent on GitHub | refs/heads/preservation/2746-pr3011-turn0 | main | none | absent | 0 |
| R97 | Seven open pull requests exist, and none names issue #3969 | pulls with state open | main | none | present | 0 |
| R98 | Pull request 3778 merged on 2026-10-05 from head fix/3217-access-log-fields | pulls/3778 | main | 3f8fd48abd | present | 0 |
| R99 | Class F tip equals GitHub branch tip | refs/heads/jmorrison-jnpr-test-4035-menu-92-selection-result | main | 9851ed28ced6f6d0909fe529e0a8f43c1a412bed | present | 0 |
| R100 | Class F tip equals GitHub branch tip | refs/heads/jmorrison-juniper-assessment-4026 | main | 83d197e30fd9519521697154036eadf4e52a2850 | present | 0 |
| R101 | Class F tip equals GitHub branch tip | refs/heads/jmorrison-juniper-false-success-family-4028 | main | 4be5f321a3ba26c136c541e062c7aa4e7442aae9 | present | 0 |
| R102 | Class F tip equals GitHub branch tip | refs/heads/jmorrison-juniper-fix-2863-identifier-defaults-batch-1 | main | 6eec0e4bf09a6ca5deb1bb78c008337bab6e7464 | present | 0 |
| R103 | Class F tip equals GitHub branch tip | refs/heads/jmorrison-juniper-fix-4031-partial-failure | main | d89f552440377bee9caa4e8eada8871c68e67958 | present | 0 |
| R104 | Class F tip equals GitHub branch tip | refs/heads/jmorrison-juniper-issue-2746 | main | 4ebe402c19de77a546960896ef70bb3286860f13 | present | 0 |
| R105 | Class F tip equals GitHub branch tip | refs/heads/jmorrison-juniper-issue-3416-lint-pattern | main | 3d51242e41f2815bbcaeaa076a2c1e60b2fd9550 | present | 0 |
| R106 | Labels stage:speckit-artifacts-emitted, needs-human-review, and needs-investigation exist in the repository label list | labels (repository label list) | main | none | present | 0 |

Note on rows R01 to R16: each row reads one line of the remote AGENTS.md file. Rows R17 to R23 read the remote copilot-instructions file. Rows R24 to R27 read the remote constitution. Rows that share a file share its blob SHA.

Note on rows R47 to R69: the report names 23 branches. Row R69 is absent from this clone too (U-5).

## Local checks

These checks read this clone. They do not count in the remote verification table.

- L1 HEAD and working tree: HEAD is f03c6c9b36d612a48d7b9652998c2fd87dd777ca on branch main. Five modified paths appear:
  - src/foundation/support/utils/logger_utils.py
  - src/interfaces/wan_performance/collection/request_admission.py
  - src/mist/intelligence/reports/subscription_expiry/client.py
  - tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py
  - tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py
- L2 Local branch count: 330 refs under refs/heads, including main. 329 besides main.
- L3 Class counts: class A 4, class B 135, class C 129, class D 47, class E 7, class F 7, and class G 0. The sum is 329. Merged pull request head names match 264 local refs. No head name matches 65 local refs. Each merged match has commits beyond origin/main.
- L4 Class C pull request heads: 62 heads exist as commit objects in the local object store. 67 heads are absent.
- L5 Closed pull request heads: commit objects exist for #3954 (560f0eff31), #3955 (21d2d65598), #3956 (94cc4e17db), #3957 (2569a15adb), and #3973 (1c98c29480). Name reuse example: the local branch fix/2746-fm-http-status has tip 94cc4e17db. That tip equals the head of closed #3956. Merged #3077 used the same name with head a7767c9ca0. The tip has 1 commit beyond the #3077 head. 9 head commits are missing from the tip.
- L6 Pull request #3778: merged on 2026-10-05T02:09:29Z from head fix/3217-access-log-fields at 3f8fd48abd. Local fix/3217-access-log-fields (tip 8d0f78f33c) has 1 commit beyond the head. 3 head commits are missing from its tip. Local fix/3217-access-log-fields-update (tip 8047fa6b10) has 3 commits beyond the head. 29 head commits are missing from its tip.
- L7 Patch equivalence for the 18 named branches of classes D and E. Counts come from git cherry against origin/main, plus lines and minus lines:
  - backup/3671-pre-subject-rewrite-20261003: plus 23, minus 0
  - rescue/code-misthelper-dirty-20260912: plus 9, minus 0
  - fix/3217-access-log-fields-update: plus 3, minus 0
  - fix/3745-webhook-delivery-refusals-local: plus 3, minus 0
  - fix/3745-webhook-delivery-refusals-push: plus 3, minus 0
  - jmorrison-juniper-fix/3390-confirm-strategy-wording: plus 3, minus 0
  - pr/3933/chore/3896-symbol-guard-merge-base-2: plus 3, minus 0
  - pr3781-rebase: plus 2, minus 0
  - repair/3802-quality: plus 2, minus 0
  - chore/2689-sdk-guard: plus 1, minus 0
  - copilot/vscode-mu2wi6bp-23x9: plus 1, minus 1
  - backup/main-local-2026-09-24: plus 1, minus 0
  - fix/2566-scheduled-reboot-settle: plus 1, minus 0
  - test/2743-missing-failure-modes: plus 2, minus 0
  - test/3149-harness-scope: plus 1, minus 0
  - agents/kms-optic-health-ping-commands: plus 0, minus 1
  - tmp/2729-rebase: plus 0, minus 1
  - test/2743-timeout-failure-mode: plus 0, minus 1
- L8 Branch jmorrison-juniper-github-sync-update-merge: tip 6ea93b1074. That value equals GitHub main at 2026-10-06T07:58:29Z, the commit before the sync window. The branch has zero commits beyond origin/main, so it is class A. Branch jmorrison-jnpr-didactic-robot is not a local ref.
- L9 Merge commits and cherry output: branch backup/main-local-2026-09-24 has 3 commits beyond origin/main. Two of them are merge commits. git cherry lists one line for it. Each class E branch has one commit and zero merge commits.
- L10 Word search: the word "pod" has no match in AGENTS.md, .github/copilot-instructions.md, .specify/memory/constitution.md, or documentation/container-deployment.md.
- L11 Class F tips: each of the seven local tips equals its GitHub tip. The comparison rows are R99 to R105.
- L12 Reference record contracts: the reference record folder design/contracts holds four files. They are report-xml.md, report-csv.md, portal.md, and cli-menu.md. This check reads the local listing only.

## Class lists

Class A (4 branches, no commit beyond origin/main):

- agents/ok-make-that-change-then-reun-that-report
- feat/4631-offline-jvd-preview
- fix/4863-interactive-login-output
- jmorrison-juniper-github-sync-update-merge

Class E (7 branches, patch-equivalent commits only):

- agents/kms-optic-health-ping-commands
- chore/4569-hypothesis-rebase
- chore/4570-react-router-rebase
- jmorrison-juniper-fix-3168-silent-completion-classifier
- jmorrison-juniper-fix-3380-skip-visibility
- test/2743-timeout-failure-mode
- tmp/2729-rebase

Class F (7 branches, GitHub copy with the same tip):

- jmorrison-jnpr-test-4035-menu-92-selection-result
- jmorrison-juniper-assessment-4026
- jmorrison-juniper-false-success-family-4028
- jmorrison-juniper-fix-2863-identifier-defaults-batch-1
- jmorrison-juniper-fix-4031-partial-failure
- jmorrison-juniper-issue-2746
- jmorrison-juniper-issue-3416-lint-pattern

Class D (47 branches, unique patches, tag required):

- 3999-transceiver-master-report
- 4000-fix-confirmation-scope
- backup/3519-pre-squash
- backup/3671-pre-subject-rewrite-20261003
- backup/main-before-sync-20261104
- backup/main-local-2026-09-24
- backup/pr-4569-before-conflict-repair
- backup/pr-4570-before-conflict-repair
- chore/2689-sdk-guard
- chore/2746-recovered-specification
- chore/4873-routed-git-extension
- chore/4945-smoke-package-conformance
- copilot/vscode-mu2wi6bp-23x9
- docs/4822-recovered-vmm-export
- feat/4631-recovered-offline-preview
- feat/4769-ex-hardware-xml
- fix/2566-scheduled-reboot-settle
- fix/2977-recovered-content-dedup
- fix/3217-access-log-fields-update
- fix/3745-webhook-delivery-refusals-local
- fix/3745-webhook-delivery-refusals-push
- fix/4758-pylance-diagnostics
- jmorrison-juniper-3714-session-persistence
- jmorrison-juniper-audit-3168-structured-signals
- jmorrison-juniper-cradlepoint-transport-status-3819
- jmorrison-juniper-credential-defaults-spec
- jmorrison-juniper-fix-2926-upgrade-blind-handlers
- jmorrison-juniper-fix-3070-blind-handler-ratchet
- jmorrison-juniper-fix-3394-multi-site-empty-version
- jmorrison-juniper-fix-3417-snmp-base-oid-default
- jmorrison-juniper-fix-3506-site-lock-logging
- jmorrison-juniper-fix-4061-api-failure-test
- jmorrison-juniper-fix-4061-native-http-response
- jmorrison-juniper-fix/3390-confirm-strategy-wording
- jmorrison-juniper-primary-key-strategy-spec-4003
- jmorrison-juniper-refactor-3984-split-database-package
- jmorrison-juniper-typed-outcome-spec-3168b
- pr/3933/chore/3896-symbol-guard-merge-base
- pr/3933/chore/3896-symbol-guard-merge-base-2
- pr/4086/jmorrison-juniper-issue-2753-batch-two
- pr3781-rebase
- recovery/local-main-20261106-3c058deb1
- refactor/2926-portal-handlers-c
- repair/3802-quality
- rescue/code-misthelper-dirty-20260912
- test/2743-missing-failure-modes
- test/3149-harness-scope

Classes B (135) and C (129) are not listed here. The classification loop in design/quickstart.md produces each list. The counts appear in L3.

## Sources

Local sources. The local clone equals GitHub main at the commit in the evidence snapshot. Each line number matches the remote file at the blob SHA in the remote verification table.

- AGENTS.md lines 169, 174, 194, 210, 224, 229, 235, 239, 248, 251, 254, 260, 268, 271, 274, and 275 (rows R01 to R16).
- .github/copilot-instructions.md lines 74, 159, 347, 405, 415, 475, and 546 (rows R17 to R23). Line 347 describes the volumes. Line 415 gives the caution.
- .specify/memory/constitution.md lines 38, 57, 303, and 500 (rows R24 to R27).
- documentation/development-setup.md lines 178 and 191 (rows R28 and R29).
- documentation/container-deployment.md line 141 (row R30).
- .specify/scripts/powershell/spec-route.ps1 lines 17 and 25 to 27 (rows R31 and R32). The loop at lines 25 to 27 starts at the most significant position.
- Template files in rows R33 to R36. The record follows their headings.
- Reference record files in rows R42 and R43. They set the record shape.
- Loaded skill: container-storage, section "Authority and loss boundary". The section supports decision D-8.

URL sources. Each page was fetched during this run.

- https://git-scm.com/docs/git-cherry. The page says that git cherry prefixes a minus for a commit with an equivalent in upstream. It prefixes a plus for a commit without one. Its equivalence test removes whitespace and line numbers from the diff. Decision D-3 and check L7 use this meaning.
- https://git-scm.com/docs/git-branch. The page says that `--merged` lists branches whose tip commits are reachable from the named commit. Decision D-4 uses this meaning.
- https://git-scm.com/docs/git-push. The page lists `--tags` as one option that decides which refs to push. Explicit refspecs follow the same selection rules. Decision D-2 and the edge cases use this meaning.

## Not applicable

- Mist API OpenAPI files and the mistapi SDK. No claim depends on an endpoint or an SDK function.
- Juniper device skills. The issue concerns repository state only.
- Podman engine behavior beyond the repository runbook. The record uses only the repository commands.

## Unverified

- U-1 Worktrees. The report names 15 worktrees, 2 dirty worktrees, and 5 more worktrees that changed files. The author role cannot run git worktree commands. The owner runs the inventory in task T003.
- U-2 Session states. The report names the sessions "GitHub Sync, Update, and Merge for MH (15)" and "Github sync and merge". Session state lives outside the repository.
- U-3 Container state. The report says a pod named misthelper was skipped. The governing documents contain no word "pod" (L10). Container state needs a container command, which the author role cannot run. The previous image tag is also unverified.
- U-4 Attribution. The four merges and two pull request creations in the sync window used the owner account. Their head names differ from the sync branch name. Attribution to the sync run is unverified.
- U-5 Other clone. Branch jmorrison-jnpr-didactic-robot is absent from this clone's refs. The branch may exist in another clone.
- U-6 Patch equivalence. Class E depends on git cherry, which removes whitespace and line numbers before it compares patches. A reformatted change can hide a unique edit. Task T012 adds a merge-commit check. The owner reviews each class E branch before its deletion.
- U-7 Class C pull request heads. 67 of 129 class C pull request heads are absent from the local object store (L4). The tag rule uses the local tip. The tags do not depend on those heads.
- U-8 Class B and class C names. The names of the 135 class B and 129 class C branches are not listed here. The classification loop in design/quickstart.md produces them.
- U-9 Shared command arguments. The stranded-branch-report workflow (R22) reports branches with no pull request. This record does not run its command. The command arguments are not verified.
- U-10 Tool install state. The ste-linter command on the writer host is unverified. The author role runs no linter.
- U-11 Rate limits. One large pull request query returned HTTP 504. The record uses smaller queries. Rate-limit status at the time of writing is unverified.
- U-12 Time sensitivity. Every value in this record reflects the evidence snapshot. Any later change requires task T002 before a write.

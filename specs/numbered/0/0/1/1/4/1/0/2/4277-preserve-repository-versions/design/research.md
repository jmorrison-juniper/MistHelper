# Research: Preserve Repository Versions and Update the Local Main Checkout

**Issue**: #4277, "chore: preserve repository versions and update the local main checkout"

**Measurement date**: 2026-11-26, UTC. Remote values are read from the GitHub API. Local values are read by read-only Git commands.

**Scope of this file**: It records each decision, each remote check, each local observation, each source, and each claim that remains unverified.

## 1. Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk. The recommended option is the chosen option in every case.

### D-1 Record route and folder

- Alternatives: (a) numbered route under `specs\numbered`. (b) Timestamp route under `specs\live`. (c) A folder outside `specs`.
- Chosen: (a). Recommended: (a).
- Reason: Issue 4277 is numbered. The base-5 digits of 4277 are 00114102, which gives the route 0\0\1\1\4\1\0\2. The route function reads base 5 with eight digits (R-30, R-31). Numbered records must use the numbered route (R-20, R-26). The folder `0\0\1\1\4\1\0` does not exist yet (R-47).
- Risk: Low. A future record with the same number would collide. The tree holds no such path (R-48).

### D-2 Issue closure keyword

- Alternatives: (a) `Refs #4277` in the commit body and the pull request body. (b) `Closes #4277`, which the brief names as the default.
- Chosen: (a). Recommended: (a).
- Reason: The owner wrote "Keep #4277 open" on 2026-10-21 and on 2026-10-30. The owner comments are IC_kwDOQltU8c8AAAABeBAB8Q and IC_kwDOQltU8c8AAAABhZRUIg. A closing keyword closes the issue when the pull request merges. Recovery items U-001 to U-009 remain unresolved. `documentation\quality-gates.md` line 118 (R-36) uses `Refs` for the same reason.
- Risk: The orchestrator must close #4277 by hand when the owner records the recovery items as resolved. This deviation from the brief needs orchestrator confirmation.

### D-3 Disposition of refs

- Alternatives: (a) Keep every ref, tag, stash, preserved ref, and worktree entry. (b) Delete merged local heads. (c) Prune worktree admin entries.
- Chosen: (a). Recommended: (a).
- Reason: The issue forbids deletion of branches, archive tags, stashes, and worktrees. The register records each item. AGENTS.md line 251 (R-16) forbids stash, clean, and reset in a shared checkout.
- Risk: The local head count remains high, at 330 (L-04). Recovery item U-004 tracks the owner review.

### D-4 Publication boundary

- Alternatives: (a) Publish no private ref, backup, patch, or register. (b) Push the 322 local-only heads to GitHub. (c) Move the work to a private repository.
- Chosen: (a). Recommended: (a).
- Reason: The repository is public (R-23, L-14). The issue forbids publication of private backups and checkpoint objects. Option (b) would publish unmerged work. Option (c) needs owner approval and a new repository.
- Risk: The 322 local-only heads rely on the owner backup and the same disk (U-002).

### D-5 Backup evidence handling

- Alternatives: (a) Record the owner-reported evidence and do not open the backup. (b) Create a new backup now. (c) Open the owner bundle and run `git bundle verify`.
- Chosen: (a). Recommended: (a).
- Reason: The backup is private and absent from the repository (UV-01, UV-02). A new backup adds one more copy on the same disk. The owner accepted the same-disk risk on 2026-10-21 (IC_kwDOQltU8c8AAAABeBAB8Q). The accepted recovery window is 24 hours, the maximum stated backup interval.
- Risk: The backup claims stay unverified. Validation V-05 is not run (validation report).

### D-6 Baseline validation location

- Alternatives: (a) Detached baseline worktree at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` in a sibling folder. (b) Run the gates in the primary checkout. (c) Reuse the 2026-10-17 results at `9ba3a7e5ca8f3c371e58887531623a249510d7df`.
- Chosen: (a). Recommended: (a).
- Reason: Option (b) conflicts with five modified files (L-07) and with the preservation rule. Option (c) is 313 commits behind GitHub main (R-02). A detached worktree creates no branch and no tag.
- Risk: A new worktree has no `.venv` (R-38). The bootstrap script (R-43) must run first. OneDrive file locks can slow the run.

### D-7 Unpublished privacy commits

- Alternatives: (a) Record recovery item U-001 and do not rebuild the commits. (b) Rebuild the three commits from the merged code. (c) Treat merged PR 4404 as complete for every privacy claim.
- Chosen: (a). Recommended: (a).
- Reason: Commits `7d16297d`, `3cf37c7c`, and `d8900984` are absent from GitHub (R-07, R-08, R-09) and from the primary object store (L-06). The merged code covers `_get_org_name` (R-13, R-14). The equivalence of the absent commits to the merged code is unverified (UV-04).
- Risk: Unique work might exist in the owner backup or in another clone.

### D-8 Release-note fragment

- Alternatives: (a) Add no fragment, with the reason in the pull request body. (b) Add one fragment under `changelog.d`, as the constitution wording requires.
- Chosen: (a). Recommended: (a).
- Reason: `changelog.d\README.md` line 58 (R-39) names internal-only changes. This record changes no user-visible behavior. The constitution line 409 (R-29) uses broader wording. Analysis item A-003 records the conflict.
- Risk: A reviewer may apply the constitution wording. The pull request body states the rule.

### D-9 Labels

- Alternatives: (a) Replace `tools` with `docs`. (b) Keep `tools`. (c) Add `docs` and keep `tools`.
- Chosen: (a). Recommended: (a).
- Reason: The documented scope labels are `MistHelper.py`, `tests`, `ci`, `container`, `docs`, and `web-portal` (R-21). Each issue carries one scope label. The label `tools` is not in that set. The record changes documentation only.
- Risk: The owner may prefer another scope label. The change is reversible.

### D-10 Merge authority

- Alternatives: (a) Add the `auto-merge` label only after each required check is green and the orchestrator authorizes the merge. (b) Add the label when the pull request opens. (c) Merge without the label.
- Chosen: (a). Recommended: (a).
- Reason: AGENTS.md lines 229-230 (R-15) require green checks before the label. The brief requires orchestrator authorization.
- Risk: The merge waits for the checks. This delay is accepted.

### D-11 Deployment pipeline steps 10 to 12

- Alternatives: (a) Mark the steps as not triggered. (b) Start a manual container build. (c) Build the image on the local machine.
- Chosen: (a). Recommended: (a).
- Reason: `container-build.yml` runs on a push that changes a product file, or on a manual dispatch (R-22). This record changes no product file. Constitution line 143 (R-27) describes steps 10 to 12 for product changes.
- Risk: None for this record.

### D-12 Standalone Git operations

- Alternatives: (a) Document the owner operations and add none to the primary checkout. (b) Run the preservation work through a pull request. (c) Ignore the constitution wording.
- Chosen: (a). Recommended: (a).
- Reason: The owner completed the backup, the fast-forward, and the validation on 2026-10-17 (IC_kwDOQltU8c8AAAABc1rixg and IC_kwDOQltU8c8AAAABc1wR8A). Constitution line 175 (R-28) says no standalone Git operations exist. Analysis item A-004 keeps this conflict with the owner.
- Risk: Policy drift between the constitution and owner practice.

### D-13 Preservation of modified files

- Alternatives: (a) Copy the five modified files and write a git-ignored patch under `test-artifacts`. (b) Commit the files to a branch. (c) Stash the files.
- Chosen: (a). Recommended: (a).
- Reason: Option (b) publishes unfinished owner work in a public repository (D-4). Option (c) is forbidden by AGENTS.md line 251 (R-16).
- Risk: The copies drift if the owner edits a file. A SHA-256 manifest records the state at copy time.

## 2. Remote verification table

The table holds 50 rows. The count matches `remote_checks` in the STATUS file and the count in `summary.md`. The Blob or commit SHA column holds a commit SHA for a commit row. Local rows use the Git blob hash of the local file. The remote tree holds 11404 entries and is not truncated.

| Row | Claim | Path | Ref | Blob or commit SHA | Result | Line | Evidence |
| - | - | - | - | - | - | - | - |
| R-01 | GitHub main head is `f03c6c9b` | `repos/jmorrison-juniper/MistHelper/git/ref/heads/main` | main | `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` | present | 0 | Git ref API read on 2026-11-26. |
| R-02 | Baseline commit `9ba3a7e5` is an ancestor of GitHub main. GitHub main is 313 commits ahead of it. | `repos/jmorrison-juniper/MistHelper/commits/9ba3a7e5ca8f3c371e58887531623a249510d7df` | main | `9ba3a7e5ca8f3c371e58887531623a249510d7df` | present | 0 | Commit API read. Compare API with base `9ba3a7e5` and head main returned ahead 313, behind 0. |
| R-03 | PR 4404 merge commit is an ancestor of GitHub main. GitHub main is 55 commits ahead of it. | `repos/jmorrison-juniper/MistHelper/commits/31b752f060d4d10cbe87b5880b071b6570d0b3c9` | main | `31b752f060d4d10cbe87b5880b071b6570d0b3c9` | present | 0 | Compare API with base merge commit and head main returned ahead 55, behind 0. |
| R-04 | PR 4404 final head `85086493` was merged | `repos/jmorrison-juniper/MistHelper/commits/850864931c3af94fbe5ff1c73678e0141cf3ffb4` | main | `850864931c3af94fbe5ff1c73678e0141cf3ffb4` | present | 0 | Pull request API reported merged true, merged at 2026-11-13T11:22:46Z, merged by `jmorrison-juniper`. |
| R-05 | PR 4404 earlier head `3ead4ec4` existed on 2026-10-30 | `repos/jmorrison-juniper/MistHelper/commits/3ead4ec424bfbda1c3edb739c963d02604201c4a` | main | `3ead4ec424bfbda1c3edb739c963d02604201c4a` | present | 0 | Commit API read. The SHA is named in comment IC_kwDOQltU8c8AAAABhZPzKQ. |
| R-06 | PR 4404 draft head `6e197710` existed on 2026-11-09 | `repos/jmorrison-juniper/MistHelper/commits/6e1977105d0b5c4fad2a3018f070fd601b2ada4b` | main | `6e1977105d0b5c4fad2a3018f070fd601b2ada4b` | present | 0 | Commit API read. The SHA is named in issue 4280 comment IC_kwDOQltU8c8AAAABkZuqdA. |
| R-07 | Local privacy commit `7d16297d` is not on GitHub | `repos/jmorrison-juniper/MistHelper/commits/7d16297d4314113287c7c78851ebdfa643800278` | main | `7d16297d4314113287c7c78851ebdfa643800278` | absent | 0 | Commit API returned HTTP 422, No commit found for SHA. |
| R-08 | Local commit `3cf37c7c` is not on GitHub | `repos/jmorrison-juniper/MistHelper/commits/3cf37c7cf2ef5e9d42f9ca550172cda6ca4d0f5b` | main | `3cf37c7cf2ef5e9d42f9ca550172cda6ca4d0f5b` | absent | 0 | Commit API returned HTTP 422, No commit found for SHA. |
| R-09 | Local commit `d8900984` is not on GitHub | `repos/jmorrison-juniper/MistHelper/commits/d89009846b648aae15ce05a36cc02f053f83cab8` | main | `d89009846b648aae15ce05a36cc02f053f83cab8` | absent | 0 | Commit API returned HTTP 422, No commit found for SHA. |
| R-10 | Preserved branch commit `29c54897` is on GitHub | `repos/jmorrison-juniper/MistHelper/commits/29c5489751ed84a8595cefe85f0e2aa7716b8608` | main | `29c5489751ed84a8595cefe85f0e2aa7716b8608` | present | 0 | The short form `29c5489751ed` resolved to the full SHA. |
| R-11 | Remote branch `jmorrison-juniper-coordinate-issue-work` points to `29c54897` | `repos/jmorrison-juniper/MistHelper/git/ref/heads/jmorrison-juniper-coordinate-issue-work` | jmorrison-juniper-coordinate-issue-work | `29c5489751ed84a8595cefe85f0e2aa7716b8608` | present | 0 | Git ref API read returned the SHA. The branch is not a local head in the primary checkout (L-04). |
| R-12 | Issue 4280 record was merged to main | `specs/numbered/0/0/1/1/4/1/1/0/4280-organization-metadata-refusal/spec.md` | main | `d169ecd85531d526bcc1d02a3a265786a5dff2c2` | present | 0 | Contents API returned the blob SHA. PR 4404 lists this path as added. |
| R-13 | Method `_get_org_name` is defined on main | `src/mist/resources/org/org_config_migration_manager.py` | main | `358a2cc226d550a0d838b10ae0738944894f5655` | present | 150 | The method spans lines 150 to 173. The local blob hash matches (L-16). |
| R-14 | Main checks the HTTP status before it reads metadata | `src/mist/resources/org/org_config_migration_manager.py` | main | `358a2cc226d550a0d838b10ae0738944894f5655` | present | 159 | Lines 159 to 162 return `Unknown` for any status outside 200 to 299. |
| R-15 | Rule: wait with `gh pr checks --watch`, then add the `auto-merge` label after green checks | `AGENTS.md` | main | `44a9afffb5bd6f774973a845d27343e4e528b6ad` | present | 229 | Lines 229 and 230. The local blob hash matches (L-16). |
| R-16 | Rule: add files by explicit path, and never stash in a shared checkout | `AGENTS.md` | main | `44a9afffb5bd6f774973a845d27343e4e528b6ad` | present | 251 | Line 251 names `git add -A`, `git stash`, and `git reset --hard`. |
| R-17 | Rule: preserve work before closing an unmerged pull request | `AGENTS.md` | main | `44a9afffb5bd6f774973a845d27343e4e528b6ad` | present | 271 | Section heading at line 271. |
| R-18 | Section `Local gates` begins at line 50 | `.github/copilot-instructions.md` | main | `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` | present | 50 | The local blob hash matches (L-16). |
| R-19 | STE gate command | `.github/copilot-instructions.md` | main | `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` | present | 74 | Row `STE` names `ste-linter --config .ste-linter.toml --min-score 80`. |
| R-20 | Numbered records use managed roots and the eight-level route | `.github/copilot-instructions.md` | main | `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` | present | 159 | Lines 159 to 160. |
| R-21 | Each issue carries one scope label from a fixed set | `.github/copilot-instructions.md` | main | `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` | present | 439 | Scope row lists `MistHelper.py`, `tests`, `ci`, `container`, `docs`, and `web-portal`. |
| R-22 | `container-build.yml` runs on a product-file push or a manual dispatch | `.github/copilot-instructions.md` | main | `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` | present | 473 | Workflow table row. |
| R-23 | The repository is public | `.github/copilot-instructions.md` | main | `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` | present | 478 | The sentence reads "MistHelper is a public repository". Repository visibility also reads PUBLIC (L-14). |
| R-24 | `test-artifacts/` holds generated evidence and Git ignores it | `.github/copilot-instructions.md` | main | `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` | present | 339 | Data location table row. |
| R-25 | Principle I, five-item rule | `.specify/memory/constitution.md` | main | `4584997a264c5a7ade2ca7441246e1f067083aa1` | present | 38 | Heading `I. Five-Item Rule`. |
| R-26 | New `specs/` records use managed roots | `.specify/memory/constitution.md` | main | `4584997a264c5a7ade2ca7441246e1f067083aa1` | present | 57 | Line 57 names `numbered/`, `live/`, `skills/`, and `indexes/`. |
| R-27 | Principle IV, full deployment pipeline | `.specify/memory/constitution.md` | main | `4584997a264c5a7ade2ca7441246e1f067083aa1` | present | 143 | Heading `IV. Full Deployment Pipeline`. |
| R-28 | Constitution says no standalone Git operations exist | `.specify/memory/constitution.md` | main | `4584997a264c5a7ade2ca7441246e1f067083aa1` | present | 175 | Sentence at line 175. |
| R-29 | Each change adds one release-note fragment | `.specify/memory/constitution.md` | main | `4584997a264c5a7ade2ca7441246e1f067083aa1` | present | 409 | Bullet `Release notes` at line 409. |
| R-30 | Route base is 5 with eight digits | `.specify/scripts/powershell/spec-route.ps1` | main | `37293a255f9b5de20ccb2b3ef0ad15717bab2826` | present | 17 | Line 17 reads `$base = 5`. Width default is 8 at line 7. |
| R-31 | `Resolve-SpecFeaturePath` places numbered records under `numbered` | `.specify/scripts/powershell/spec-route.ps1` | main | `37293a255f9b5de20ccb2b3ef0ad15717bab2826` | present | 34 | Function spans lines 34 to 51. |
| R-32 | Spec template exists | `.specify/templates/spec-template.md` | main | `083ef123c7a2e56e21f3062173fb003258f927e2` | present | 0 | File exists. |
| R-33 | Plan template exists | `.specify/templates/plan-template.md` | main | `1a54553bd85cbef2178aa55efbeeb0c1942ffdde` | present | 0 | File exists. |
| R-34 | Tasks template exists | `.specify/templates/tasks-template.md` | main | `7e5170324d41a6736c498d6b9fc83651f31d0778` | present | 0 | File exists. |
| R-35 | Checklist template exists | `.specify/templates/checklist-template.md` | main | `806657da09d1058823923e346a323b633114971a` | present | 0 | File exists. |
| R-36 | Precedent: an open issue uses `Refs` instead of a closing keyword | `documentation/quality-gates.md` | main | `6776d334cca5d9b43273473a06da367a65605c6d` | present | 118 | Line 118 reads "must use `Refs #3071`". |
| R-37 | STE command for a single file | `documentation/quality-gates.md` | main | `6776d334cca5d9b43273473a06da367a65605c6d` | present | 283 | Line 283 names the `.venv\Scripts\ste-linter.exe` form. |
| R-38 | A new worktree has no `.venv` | `documentation/development-setup.md` | main | `1733975a7e0a0962fe5367e165a21f5831f8c3e5` | present | 37 | Warning at line 37. |
| R-39 | An internal-only change adds no release-note fragment | `changelog.d/README.md` | main | `fcbde10e0c293390bd9df8d62a5d61f158eca384` | present | 58 | Rule 4 at line 58. |
| R-40 | STE configuration file exists | `.ste-linter.toml` | main | `d9f28ef8faf4a4c36a4e967d5b978f96eb306253` | present | 0 | File exists. |
| R-41 | Rule ignores `/test-artifacts/` | `.gitignore` | main | `17eadfadb35a59e191a61c78877569ad747ddcc7` | present | 107 | Line 107. |
| R-42 | Value of `MYPY_PATHS` for the type gate | `.github/workflows/ci.yml` | main | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 93 | Line 93 lists five paths. |
| R-43 | Bootstrap script exists | `scripts/bootstrap_worktree.py` | main | `e16515ffa789cca7d0bdd7e9789898588e5f1312` | present | 0 | File exists. |
| R-44 | Process folder baseline exists | `tests/guardrails/process_folder_baseline.json` | main | `f3eb8a7b6c62f3154ac6fa867a8948504818798b` | present | 0 | File exists. |
| R-45 | Process folder guard test reads the baseline | `tests/guardrails/test_process_folder_structure.py` | main | `f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5` | present | 15 | Line 15 sets `BASELINE_PATH`. Local HEAD equals GitHub main and the file has no local change (L-07). |
| R-46 | Reference record shape | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | main | `83b950279e45704943ad6942d23c8fc99cced492` | present | 0 | Read for shape only (lines 1 to 30). No content is copied. |
| R-47 | Route folder for issue 4277 does not exist | `specs/numbered/0/0/1/1/4/1/0/2` | main | none (path absent) | absent | 0 | No tree path starts with this prefix. |
| R-48 | Record file for issue 4277 does not exist | `specs/numbered/0/0/1/1/4/1/0/2/4277-preserve-repository-versions/spec.md` | main | none (path absent) | absent | 0 | No tree path contains `4277`. This record creates the path. |
| R-49 | Installed `mistapi` version is 0.64.1 | `.venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA` | local | `86b3b7003d569a1311af4085e7e269a52decd795` | present | 0 | Local installed SDK. The pin is `mistapi>=0.64.0,<0.65`. Blob hash by `git hash-object` without a write. |
| R-50 | SDK function `getOrg` takes a session and an organization identifier | `.venv\Lib\site-packages\mistapi\api\v1\orgs\orgs.py` | local | `e08585784e20246bdfb509e3e1e85e4d0528764c` | present | 42 | Local installed SDK source. The org manager calls this function at remote line 154. |

## 3. Local evidence

Local evidence supports the decisions. It does not replace a remote check. The table does not count toward the 50 remote rows.

| Row | Observation | Command class | Result |
| - | - | - | - |
| L-01 | Primary checkout HEAD is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` on branch `main`. `origin/main` points to the same commit. | `rev-parse` | Equal. |
| L-02 | Commits in `origin/main` that `main` lacks, and commits in `main` that `origin/main` lacks | `rev-list --count` with exclusion | `0` and `0`. |
| L-03 | Repository shallow status | `rev-parse --is-shallow-repository` | `false`. |
| L-04 | Local heads: 330 in total. 5 are merged into `main`. 8 have a same-tip counterpart on origin. 322 have no origin counterpart. | `for-each-ref` with `--merged` and origin comparison | Cross tab: not merged and absent 318. Not merged and same tip 7. Merged and absent 4. Merged and same tip 1 (`main`). |
| L-05 | Other ref counts: remote-tracking refs 599. Tags 190. Stash refs 1. `refs/copilot-preserved` 6. `refs/copilot` 1123. `refs/agents` 434. | `for-each-ref` by namespace | Counts as stated. |
| L-06 | Object presence in the primary object store: `9ba3a7e5`, `3ead4ec4`, `6e197710`, `29c54897`, and `31b752f0` are present. `7d16297d`, `3cf37c7c`, and `d8900984` are absent. | `cat-file -t` | Three absent commits. |
| L-07 | Five modified entries, and no staged or untracked entry: `src\foundation\support\utils\logger_utils.py`, `src\interfaces\wan_performance\collection\request_admission.py`, `src\mist\intelligence\reports\subscription_expiry\client.py`, `tests\unit\marvis\mist\intelligence\reports\audits\credentials\subscription_expiry\test_client.py`, and `tests\unit\wan_dashboard\wan_performance\collection\test_request_admission.py`. | `status --porcelain` with no optional locks | Five `M` entries. |
| L-08 | Worktree admin entries under the common Git directory | Directory listing of `.git\worktrees` | 33 entries. Names are not copied to this record. |
| L-09 | Git version | `git --version` | `2.49.0.windows.1`. |
| L-10 | Primary `.git` is a directory | Directory check | Directory, not a gitfile. |
| L-11 | Child counts along the numbered route before the change: `specs` 813, `specs\numbered` 1, `0` 1, `0\0` 2, `0\0\1` 3, `0\0\1\1` 5, `0\0\1\1\4` 3, `0\0\1\1\4\1` 1. The next levels are absent. | Directory listing | Full level `0\0\1\1` receives no child. |
| L-12 | Open pull requests: 7. Pull requests that name the route prefix: 0. | `gh pr list` with file lists | No overlap. |
| L-13 | Review entries on PR 4404 | `gh pr view` with reviews field | None returned. |
| L-14 | Repository visibility | `gh repo view` with visibility field | `PUBLIC`. |
| L-15 | Blob hash of 17 cited files matched the GitHub tree SHA | `git hash-object` compared with tree SHAs | All 17 equal. |
| L-16 | Matching files: `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, the four templates, `.specify/scripts/powershell/spec-route.ps1`, `documentation/quality-gates.md`, `documentation/development-setup.md`, `changelog.d/README.md`, `.ste-linter.toml`, `.gitignore`, `src/mist/resources/org/org_config_migration_manager.py`, `.github/workflows/ci.yml`, `scripts/bootstrap_worktree.py`, and `tests/guardrails/process_folder_baseline.json`. | Blob comparison | Equal. Local line numbers equal remote line numbers. |
| L-17 | Commit time of GitHub main head | `git log -1` and API | `2026-11-26T07:15:01Z`. |
| L-18 | Issue 4277 state | Issue API | Open. Labels `chore`, `in-progress`, and `tools`. Last update 2026-10-30. |
| L-19 | Issue 4280 state | Issue API | Closed. Last update 2026-11-13. Labels `bug`, `MistHelper.py`, `in-progress`, and `needs-human-review`. |
| L-20 | Issue 4707 state | Issue API | Open. Title: "Runtime: organization export treats refused endpoints as empty configuration". |
| L-21 | PR 4404 state | PR API | Merged on 2026-11-13. Base `main`. Head `850864931c3af94fbe5ff1c73678e0141cf3ffb4`. Merged by `jmorrison-juniper`. Thirteen files changed. |
| L-22 | Owner-reported backup figures | Issue comment IC_kwDOQltU8c8AAAABc1wR8A | 3,718 references restored. 75,803 objects verified. 54,109 working files from seven dirty worktrees. 3,947 version catalog rows. These are not checked locally. |

## 4. Sources

### 4.1 Local sources

- `AGENTS.md`: lines 40-59 (writing style), 157-160 (safety), 179-251 (Git flow and staging rules), 229-230 (checks and auto-merge), 271 (preservation rule), 345 (specifications).
- `.github\copilot-instructions.md`: lines 18-25 (language and environment), 50-74 (local gates), 159 (managed roots), 339 (test-artifacts row), 431-440 (labels), 473 (container build row), 478 (public repository).
- `.specify\memory\constitution.md`: lines 38 (principle I), 57 (managed roots), 143 (principle IV), 175 (no standalone Git operations), 409 (release notes).
- `.specify\scripts\powershell\spec-route.ps1`: lines 4-51 (route digits and destination).
- `.specify\templates\spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md`: read for section headings.
- `documentation\quality-gates.md`: lines 118 (Refs precedent), 220-235 (branch protection read), 277-283 (writing gate).
- `documentation\development-setup.md`: lines 37 (worktree warning) and 176 (section Work on a change).
- `changelog.d\README.md`: lines 58 (rule 4).
- `.github\workflows\ci.yml`: lines 93 (MYPY_PATHS) and 237 (mypy command).
- `.gitignore`: line 107.
- `tests\guardrails\test_process_folder_structure.py`: line 15.
- `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv\spec.md` and `tasks.md`: read for shape only.
- `.venv\Lib\site-packages\mistapi\api\v1\orgs\orgs.py`: line 42.
- `.venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA`: read for the installed version.
- `documentation\mist-api-openapi31yaml.yaml`: searched for the organization path. No claim in this record depends on the Mist endpoint behavior.
- `documentation\MIST_API_GET_ENDPOINTS.md`, `MIST_API_MISSING_ENDPOINTS.md`, `architecture.md`, `container-deployment.md`, `operator-guide.md`: headings reviewed. None applies to this issue, because the issue changes no endpoint, container, or operator behavior.
- `.spec-context.json`: reviewed. It describes issue 1823, a different feature. It is not used.

### 4.2 GitHub sources

- Issue 4277, issue 4280, and issue 4707 JSON records, read on 2026-11-26.
- Pull request 4404 JSON record, with files, commits, merge commit, and head commit.
- Comment IDs cited in this file: IC_kwDOQltU8c8AAAABc1mRQg, IC_kwDOQltU8c8AAAABc1p4oQ, IC_kwDOQltU8c8AAAABc1rixg, IC_kwDOQltU8c8AAAABc1wR8A, IC_kwDOQltU8c8AAAABeBAB8Q, IC_kwDOQltU8c8AAAABhZPzKQ, IC_kwDOQltU8c8AAAABhZRUIg, IC_kwDOQltU8c8AAAABkZuqdA, IC_kwDOQltU8c8AAAABkZYhlQ, IC_kwDOQltU8c8AAAABkd-rbw, and IC_kwDOQltU8c8AAAABkeY58w.

### 4.3 Web sources

- https://git-scm.com/docs/git-bundle was fetched. It describes `git bundle verify` as a check of prerequisites and exit status, and `list-heads` as the reference listing.
- https://git-scm.com/docs/git-merge was fetched. It describes `--ff-only` as a refusal when a fast-forward is not possible.
- https://git-scm.com/docs/git-for-each-ref was fetched. It describes `--merged` and `--no-merged` as reachability filters on refs.
- https://git-scm.com/docs/git-worktree was fetched. It describes `add --detach` as a worktree with a detached HEAD and no branch. It describes `remove` as refusing an unclean worktree unless `--force` is given.

### 4.4 Skills

No local skill matches Git preservation or repository backup. No skill was loaded.

## 5. Unverified

| Row | Claim | Reason it is unverified |
| - | - | - |
| UV-01 | Owner backup holds 3,718 references, 75,803 objects, 54,109 working files, and seven dirty worktrees (IC_kwDOQltU8c8AAAABc1wR8A). | The backup is private. The bundle is absent from the repository, so `git bundle verify` cannot run. |
| UV-02 | Backup location, encryption, and storage class beyond the same-disk statement | The owner did not state these details in a repository file. |
| UV-03 | Owner of each of the five modified files | Git does not record ownership. Commit authors on these changes are not in the record. |
| UV-04 | The three absent commits `7d16297d`, `3cf37c7c`, and `d8900984` match the merged code | The commits are absent from GitHub and from this object store. |
| UV-05 | The three absent commits exist in another clone or in the owner backup | This session cannot read another clone or the private backup. |
| UV-06 | Namespaces `refs/copilot` and `refs/agents` hold private checkpoint references named in the issue | The issue names "private checkpoint references", but no repository file maps the namespace to that term. |
| UV-07 | Skipped tests of the owner baseline and their causes | The owner listed the causes in the issue comments but did not list each skipped test. |
| UV-08 | A human reviewed PR 4404 before merge | GitHub returned no review entries. The owner account merged the pull request. |
| UV-09 | The 33 worktree admin entries are live or stale | The entries sit outside the record scope. Their paths were not inspected, and `git worktree list` is forbidden in this procedure. |
| UV-10 | Branch `jmorrison-juniper-coordinate-issue-work` holds the saved version of the issue 4280 work, as the issue 4280 body states | The branch exists on GitHub (R-11). Its content was not compared with the merged code. |

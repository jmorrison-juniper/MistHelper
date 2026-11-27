# Research: Port the routed layout and the git extension to Spec Kit 1.4.3

**Scope**: Issue #4873. The record covers git extension 1.0.8, the git skills and agents, the integration manifests, and the feature ignore file. Part 1 (PR #4909) is merged.

**Remote convention**: `main` is the truth for code. Each row gives a git blob SHA. A repository row uses the `jmorrison-juniper/MistHelper` tree at `main`. An upstream row uses the `github/spec-kit` tree at the tag shown. `Result` gives the state of the checked item. For a negative claim, `absent` means that main lacks the item. `Line` is 0 when the check covers the whole file or no line applies.

## Decisions

Each decision has alternatives, the chosen option, the reason, and the risk. No decision needs a human.

### D-1 Keep the merged routed core unchanged

- Alternatives: Take the upstream core scripts. Rejected, because the routed lines in `create-new-feature.ps1` and `common.ps1` would be replaced (R-009, R-014).
- Chosen: Keep the part 1 code on `main`.
- Reason: Rows R-009 to R-024 show each rule on `main`. The guard tests R-024 and R-025 read those lines.
- Risk: Low. Later upstream syncs can replace the lines. FR-018 detects that drift.

### D-2 Keep the repository templates and change no template file

- Alternatives: Adopt the upstream v1.4.3 templates. Rejected, because the routed guidance in the repository templates differs from upstream (R-069 to R-071). Alternative two: Rewrite the manifest hashes to upstream bytes. Rejected, because the manifest base cannot be reproduced (F-06).
- Chosen: Keep the repository templates.
- Reason: Upstream v1.1.2 and v1.4.3 template blobs are identical (R-066 to R-068). The 1.4.3 release adds no template change.
- Risk: Drift at the next upstream sync. FR-017 and FR-018 detect the drift.

### D-3 Do not adopt the 1.4.3 template priority and composition engine

- Alternatives: Adopt the engine now. Rejected, because no test covers the routed template path, and PR #4909 deferred it. Defer it to a separate issue.
- Chosen: Defer.
- Reason: `Get-SortedExtensionIds` is absent from `common.ps1` (R-020). The guard in `test_routed_core_port.py` asserts the absence (R-024).
- Risk: The 1.4.3 template features are unavailable until the separate issue lands.

### D-4 Adopt the git extension bundled with upstream Spec Kit v1.4.3 (version 1.0.8), as a full tree

- Alternatives: Keep version 1.0.0 and patch it. Rejected, because version 1.0.0 lacks the 1.4.3 changes named in the issue. Alternative two: Adopt version 1.0.9 from v1.4.4. Rejected, because the issue names 1.0.8 and the 1.4.3 release bundles 1.0.8. Alternative three: Adopt only the PowerShell and bash scripts. Rejected, because the upstream tree holds the Python scripts too (R-077).
- Chosen: The full upstream v1.4.3 tree.
- Reason: Upstream `extension.yml` reads version `1.0.8` at tag `v1.4.3` (R-072).
- Risk: Four Python scripts enter the Ruff and Black scope (F-13). T-LOCAL-GATES runs both commands (U-7).

### D-5 Use the 1.0.8 script names and remove the 1.0.0 names

- Alternatives: Keep the 1.0.0 names. Rejected, because the upstream command text calls the new names (R-078). Alternative two: Keep both names. Rejected, because two scripts would hold the same logic.
- Chosen: `create-new-feature-branch.ps1` and `create-new-feature-branch.sh`. The core script `create-new-feature.ps1` keeps its name.
- Reason: Upstream holds both new names (R-073, R-076). The 1.0.0 git names exist only in the local extension (R-083, R-086).
- Risk: An external caller of the old git name breaks. FR-012 checks the skills. Search the repository before the merge.

### D-6 Apply the routed port to the 1.0.8 scripts in the same change, before merge

- Alternatives: Port the 1.0.0 script first and update later. Rejected, because the 1.0.0 file is replaced by the update. Alternative two: Update first and port later. Rejected, because one merge would leave the numbering unrouted. Alternative three: Keep upstream unchanged. Rejected, because the numbering would ignore routed records (F-02).
- Chosen: One change set. The routed lines go into the 1.0.8 files before the merge.
- Reason: Issue item 3 asks for the port before the update. The single change set meets that goal in the final state. The local commit `76b920fbc` holds a port of both scripts. It is evidence only (U-6).
- Risk: Caution: the order differs from the literal issue text. No merge stores an unrouted 1.0.8 script. Reviewers check the final files.

### D-7 Scan `specs\` recursively for the highest number in both git scripts

- Alternatives: Scan `specs\numbered\` only. Rejected, because the core scan covers all of `specs\` (R-009) and the two scans would disagree. Alternative two: Keep the direct-children scan. Rejected, because routed records sit at depth (F-02).
- Chosen: Recursive scan of `specs\`. The existing pattern excludes timestamp names.
- Reason: The routed core uses the same scope (R-009). The local commit uses the same scan (evidence).
- Risk: A longer scan on a large `specs\` tree. The scan reads folder names only.

### D-8 The git script creates the branch and the number. The core step creates the record

- Alternatives: The git script also creates the record. Rejected, because the core step already creates it, and the hook order would duplicate the work. Alternative two: Predict the path in the git script. Rejected, because a prediction has no test.
- Chosen: Branch and number only. FR-011 tests the full flow.
- Reason: The 1.0.0 script returns `BRANCH_NAME`, `FEATURE_NUM`, and `HAS_GIT` and writes no spec file (`.specify/extensions/git/scripts/powershell/create-new-feature.ps1`, final output block, local view).
- Risk: The owner expects a record from the git step. The test in FR-011 shows the routed record after the core step. Owner review can change this.

### D-9 Defer companion 0.27.0 and keep companion 0.24.0

- Alternatives: Install 0.27.0 from a reviewed URL, as issue item 5 asks. Rejected by the owner comment. Alternative two: Install with a registry cleanup in this change. Rejected by the same comment.
- Chosen: Defer. Companion 0.24.0 stays.
- Reason: The owner comment on issue #4873, dated 2026-11-21, lists the reasons (URL https://github.com/jmorrison-juniper/MistHelper/issues/4873#issuecomment-7072822441). The registry holds seven living commands (R-082).
- Risk: The companion stays older than 0.27.0. The comment lists the conditions for a new review.

### D-10 Keep the `.specify/.gitignore` re-include from issue #4882

- Alternatives: Adopt the upstream ignore file. Rejected, because the upstream rule alone ignores the pointer, and the guard test asserts that behavior. Alternative two: Remove the file. Rejected, because the integration reports a missing managed file as an error (docstring of `test_specify_gitignore_keeps_feature_json.py`, R-026).
- Chosen: Keep the file with the `!feature.json` re-include.
- Reason: Issue #4882 is closed (R-006). Its fix commit `e0a36ce6d` is on GitHub (R-007). The re-include is on `main` (R-029).
- Risk: An upstream regeneration drops the re-include. The guard test fails in that case.

### D-11 Regenerate both manifests from the committed content, and list each local rule

- Alternatives: Keep the manifests and document only. Rejected, because fourteen hashes already differ (F-05). Alternative two: Edit hashes by hand. Rejected, because the CLI owns the format (U-2). Alternative three: Restore upstream hashes. Rejected, because the routed files differ by design.
- Chosen: Regenerate from the final commit. List each file that differs from upstream in `.github/copilot-instructions.md`.
- Reason: Acceptance criterion 1 requires a clean status with documented local rules. Rows R-041 to R-062 show the current state.
- Risk: The CLI hash method may differ from the byte hash used here (U-2). SC-001 requires the CLI output in the PR.

### D-12 Update five `speckit-git-*` skills and remove five `speckit.git.*` agents

- Alternatives: Keep the agents and update them. Rejected, because two entry points for one command create drift. Alternative two: Keep the agents unchanged. Rejected, because the local agent files name the removed script (`.github/agents/speckit.git.feature.agent.md`, local view, lines 49 to 52).
- Chosen: Skills stay. Agents go.
- Reason: The copilot integration manifest lists skill files as managed entries (R-039, R-041 to R-049). The agent files are not managed.
- Risk: Caution: a user who calls the `/speckit.git.*` agents loses that entry point. The skills keep each command.

### D-13 Remove the `speckit-taskstoissues` skill and its agent

- Alternatives: Keep the skill. Rejected, because it creates one issue for each task, and it sets no label (R-099, R-100). AGENTS.md requires a type label and a scope label. Alternative two: Keep the skill with a label rule. Rejected, because the owner has no use case in this record. A later issue can restore it.
- Chosen: Remove both files.
- Reason: AGENTS.md states that labels are mandatory. The issue-first rule requires one subject for each issue.
- Risk: Caution: an automation that creates issues from tasks is gone. Git history restores the files.

### D-14 Use the record folder `4873-routed-git-port`. Do not use the local draft folder `4873-routed-git-extension`

- Alternatives: Create `4873-routed-git-extension`. Rejected, because the route of issue 4873 is one leaf, and two folders would share it. Alternative two: Keep both folders. Rejected, because one issue would hold two records.
- Chosen: `specs\numbered\0\0\1\2\3\4\4\3\4873-routed-git-port`.
- Reason: The route digits are the base-5 digits of 4873. `Resolve-SpecFeaturePath` calls `Get-SpecRadixSegments` (R-022). The folder exists on `main` (R-001 to R-003). The local draft exists only in a worktree (R-008).
- Risk: The folder name does not name templates or manifests. The title in `spec.md` names them.

### D-15 Build the new guard tests from source contracts and `pwsh` behavior runs

- Alternatives: Source contracts only. Rejected, because a text check cannot prove the numbering. Alternative two: Run the full git flow in CI only. Rejected, because the result would not appear in the local gates. Alternative three: Use a real remote repository. Rejected, because it needs remote state.
- Chosen: Source contracts for each script. `pwsh` runs for the numbering and the flow.
- Reason: `test_spec_route_contract.py` already runs `pwsh` (R-025). The repository idiom uses module functions in guard tests (R-024).
- Risk: `pwsh` must exist on the runner (U-8). Bash behavior runs only on macOS and Linux (U-5).

### D-16 Run only the gates that apply to the changed files

- Alternatives: Run every gate. Rejected, because most gates test product code that this change does not touch. Alternative two: Run no gate beyond the tests. Rejected, because Ruff and Black scan `.specify` (F-13, R-117).
- Chosen: Ruff, Black, the named guard tests, the test quality gate, and STE. Each other gate gets a recorded reason in the PR body.
- Reason: The gate scopes in `.github/copilot-instructions.md` (local gates table) limit each gate to a path set.
- Risk: A gate that applies is missed. The PR body lists each skipped gate with its reason.

### D-17 Keep `.specify/feature.json` unchanged and use `SPECIFY_FEATURE_DIRECTORY` for each run

- Alternatives: Point the pointer at 4873. Rejected, because later commands would read the new feature. Alternative two: Delete the pointer. Rejected, because core commands read it.
- Chosen: The pointer stays at record 4785 (R-036). Each run sets `SPECIFY_FEATURE_DIRECTORY`.
- Reason: The read-only rule in `.github/copilot-instructions.md` (R-034). Commit `00d9a16e9` restored the pointer after a merge changed it (R-118).
- Risk: Caution: a command that is not read-only still writes the pointer. `quickstart.md` checks the file after each read-only run.

### D-18 Add inline comments and action logs to changed lines. Record the untouched upstream lines

- Alternatives: Comment every upstream line. Rejected, because the diff would be large and unreviewed. Alternative two: Add no comments. Rejected, because Principles VI and VII then fail without a record.
- Chosen: Comments and logs on changed lines. A written justification in the complexity table for the untouched lines.
- Reason: The constitution allows a written justification in the Complexity Tracking table.
- Risk: A reviewer rejects the justification. The follow-up issue in plan row C-4 covers that case.

### D-19 Set the scope label to `tests` and remove `docs`

- Alternatives: Keep `docs`. Rejected, because the change adds guard tests, which the `tests` label names. Alternative two: Keep both labels. Rejected, because AGENTS.md asks for one scope label.
- Chosen: Add `tests`. Remove `docs`. The orchestrator applies the labels.
- Reason: The issue JSON lists `chore`, `docs`, and `in-progress` (issue #4873 labels). The label rule is in AGENTS.md.
- Risk: The orchestrator must apply the change. This record only proposes it in `STATUS.json`.

## Remote Verification

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
|----|-------|------|-----|----------|--------|------|
| R-001 | Legacy spec.md exists | specs/numbered/0/0/1/2/3/4/4/3/4873-routed-git-port/spec.md | main | 00eb7bd7fe9fe4db511eee05fc88c38dc1df4ac5 | present | 1 |
| R-002 | Legacy plan.md exists | specs/numbered/0/0/1/2/3/4/4/3/4873-routed-git-port/plan.md | main | 499297ff287231e54545a9b0c537c000971dafae | present | 1 |
| R-003 | Legacy tasks.md exists | specs/numbered/0/0/1/2/3/4/4/3/4873-routed-git-port/tasks.md | main | 73e57e1c77da14035f5d5ff5bd6c6728bdeb9bbb | present | 1 |
| R-004 | PR #4909 merge commit is on main | commit 1d478930cdbe583ec5f320b1929142fd9a74ee79 | main | none | present | 0 |
| R-005 | PR #4874 merge commit is on main | commit 1982b7e8412160f81cb19e8113d784a65b7853b9 | main | none | present | 0 |
| R-006 | Issue #4882 is closed | issue #4882 | GitHub | none | present | 0 |
| R-007 | Commit e0a36ce6d (PR #4885) is on GitHub | commit e0a36ce6d1d13548a493c6f2c6097fd0b40f1970 | GitHub | none | present | 0 |
| R-008 | Local commit 76b920fbc is not on GitHub | commit 76b920fbc2e0c429694645c0814eec803cc93c8d | GitHub | none | absent | 0 |
| R-009 | Recursive numbering scan | .specify/scripts/powershell/create-new-feature.ps1 | main | e5a18bf8e9b6fcb0163fc405a4166e7d68c1b9f8 | present | 57 |
| R-010 | Dot-source of spec-route.ps1 | .specify/scripts/powershell/create-new-feature.ps1 | main | e5a18bf8e9b6fcb0163fc405a4166e7d68c1b9f8 | present | 77 |
| R-011 | Set-Location with -LiteralPath | .specify/scripts/powershell/create-new-feature.ps1 | main | e5a18bf8e9b6fcb0163fc405a4166e7d68c1b9f8 | present | 82 |
| R-012 | JSON output through ConvertTo-AsciiJson | .specify/scripts/powershell/create-new-feature.ps1 | main | e5a18bf8e9b6fcb0163fc405a4166e7d68c1b9f8 | present | 244 |
| R-013 | Route resolver call | .specify/scripts/powershell/create-new-feature.ps1 | main | e5a18bf8e9b6fcb0163fc405a4166e7d68c1b9f8 | present | 192 |
| R-014 | Routing assertion call | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | present | 195 |
| R-015 | Design artifact selection call | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | present | 218 |
| R-016 | Read-only switch in the path function | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | present | 162 |
| R-017 | Pointer write guarded by the switch | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | present | 196 |
| R-018 | Test-FileExists uses -LiteralPath | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | present | 271 |
| R-019 | Test-DirHasFiles uses -LiteralPath | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | present | 288 |
| R-020 | 1.4.3 template engine is absent (Get-SortedExtensionIds) | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | absent | 0 |
| R-021 | ConvertTo-AsciiJson is defined | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | present | 636 |
| R-022 | Resolve-SpecFeaturePath is defined | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 34 |
| R-023 | Assert-SpecFeatureDestination is defined | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 76 |
| R-024 | Routed core guard file with five tests | tests/guardrails/test_routed_core_port.py | main | 458c160ecc25c85d60bb7242cf2f8814b921f85f | present | 36 |
| R-025 | Spec-route contract test requires pwsh | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 66 |
| R-026 | Pointer ignore guard file | tests/guardrails/test_specify_gitignore_keeps_feature_json.py | main | b452a5059806a280158f264c6dbfd22ec36b4ccb | present | 76 |
| R-027 | Folder structure guard file | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 1 |
| R-028 | Folder baseline file | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 1 |
| R-029 | Re-include rule for feature.json | .specify/.gitignore | main | 7631c6a7cbe067d4b1b78a0e62a3424730626d3c | present | 8 |
| R-030 | Changelog fragment for part 1 | changelog.d/issue-4873-routed-core-port.md | main | 751d9bd74d0f149ccda5a8e9edce69a5a100e180 | present | 1 |
| R-031 | Changelog fragment for issue 4882 | changelog.d/issue-4882-speckit-gitignore.md | main | e1691944733eb5841b6c02c2fb472e69d8c6eec4 | present | 1 |
| R-032 | CI pytest shard includes tests/guardrails | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 255 |
| R-033 | Managed roots rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 159 |
| R-034 | Read-only commands must not change the pointer | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 169 |
| R-035 | Constitution version 1.9.0 | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 562 |
| R-036 | Pointer names record 4785 | .specify/feature.json | main | b86bcad085666bd0aeb3ac2244c914908dc7fa70 | present | 2 |
| R-037 | Part 2 of the Spec Kit upgrade (issue 4869) record exists | specs/numbered/0/0/1/2/3/4/3/4/4869-speckit-1-4-3-upgrade/spec.md | main | 169130e5a966cdbce2f86aa276b6fd324219f6e9 | present | 1 |
| R-038 | PR #4909 changed no template file | PR #4909 file list | GitHub | none | present | 0 |
| R-039 | Copilot manifest version 1.4.3 | .specify/integrations/copilot.manifest.json | main | 71f96459b6da444bf4b9729107ddea3ca4dcc036 | present | 3 |
| R-040 | Speckit manifest version 1.4.3 | .specify/integrations/speckit.manifest.json | main | 7f7bc8c7d5e170863aaf8eec0ff27897ffd6c737 | present | 3 |
| R-041 | Copilot managed hash: analyze skill matches | .github/skills/speckit-analyze/SKILL.md | main | ae11b9b697d57c2f3ddc801327387423635ae3ac | present | 0 |
| R-042 | Copilot managed hash: clarify skill matches | .github/skills/speckit-clarify/SKILL.md | main | bf4882878aab6a2072b583e51d5800d27c2f17e5 | present | 0 |
| R-043 | Copilot managed hash: constitution skill matches | .github/skills/speckit-constitution/SKILL.md | main | aef845404a54f3f71630bda1fc9f284f5120312b | present | 0 |
| R-044 | Copilot managed hash: implement skill matches | .github/skills/speckit-implement/SKILL.md | main | 826e692494856c2c50313d0d77d7e64ad0ddbdaa | present | 0 |
| R-045 | Copilot managed hash: converge skill matches | .github/skills/speckit-converge/SKILL.md | main | c733f4b6ffcee6dd44ff21dbe6197d49aa61f56b | present | 0 |
| R-046 | Copilot managed hash: plan skill differs | .github/skills/speckit-plan/SKILL.md | main | 54d7dbc62aae22a85423dbb5c2e34e3437d8decd | stale | 0 |
| R-047 | Copilot managed hash: checklist skill matches | .github/skills/speckit-checklist/SKILL.md | main | fa2759ee7326d579b9f06cead9eb9c5d3d01d327 | present | 0 |
| R-048 | Copilot managed hash: specify skill differs | .github/skills/speckit-specify/SKILL.md | main | 4b0c25dedcd6465afda5a26cdef9308fb693a7af | stale | 0 |
| R-049 | Copilot managed hash: tasks skill differs | .github/skills/speckit-tasks/SKILL.md | main | 5ce43d7e5307df99921f343958f5b424ca6b3f78 | stale | 0 |
| R-050 | Speckit managed hash: check-prerequisites differs | .specify/scripts/powershell/check-prerequisites.ps1 | main | 32229f3f5bdf5104684c21408f025be53e6724f1 | stale | 0 |
| R-051 | Speckit managed hash: common.ps1 differs from manifest, which equals upstream | .specify/scripts/powershell/common.ps1 | main | 4b8adcdafc6b276fd0d1656665ff0f4226a9053e | stale | 0 |
| R-052 | Speckit managed hash: create-new-feature.ps1 differs from manifest, which equals upstream | .specify/scripts/powershell/create-new-feature.ps1 | main | e5a18bf8e9b6fcb0163fc405a4166e7d68c1b9f8 | stale | 0 |
| R-053 | Speckit managed hash: resolve-template.ps1 matches | .specify/scripts/powershell/resolve-template.ps1 | main | f12b313dfe198c7a4fd89a3fecd9bbab9fb50158 | present | 0 |
| R-054 | Speckit managed hash: setup-plan.ps1 differs from manifest, which equals upstream | .specify/scripts/powershell/setup-plan.ps1 | main | 77c52390bd327f5a7e93588a72ef5e1f9f5d80ab | stale | 0 |
| R-055 | Speckit managed hash: setup-tasks.ps1 differs | .specify/scripts/powershell/setup-tasks.ps1 | main | 0b708b39e1e2faaeff6c6dd523dd776ff13aeb83 | stale | 0 |
| R-056 | Speckit managed hash: checklist template differs | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | stale | 0 |
| R-057 | Speckit managed hash: constitution template matches | .specify/templates/constitution-template.md | main | a4670ff46919b276a4c9663b4ca51830108fcfc0 | present | 0 |
| R-058 | Speckit managed hash: plan template differs | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | stale | 0 |
| R-059 | Speckit managed hash: spec template differs from manifest, which equals upstream | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | stale | 0 |
| R-060 | Speckit managed hash: tasks template differs | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | stale | 0 |
| R-061 | Speckit managed hash: .specify/.gitignore differs (documented local rule, issue 4882) | .specify/.gitignore | main | 7631c6a7cbe067d4b1b78a0e62a3424730626d3c | stale | 0 |
| R-062 | Speckit managed hash: markdown_sections.py differs | .specify/scripts/powershell/markdown_sections.py | main | 95ac9c1c5e2b051f954c3c7c71e0c789bc01d8a1 | stale | 0 |
| R-063 | Manifest hash of plan template does not match upstream bytes | templates/plan-template.md | v1.4.3 | 36f2eab16880bac670fe43cbe7ef2b9bc8c3aa2f | stale | 0 |
| R-064 | Manifest hash of tasks template does not match upstream bytes | templates/tasks-template.md | v1.4.3 | 7fff087cc5a3c51a889d865fd9126607a032d233 | stale | 0 |
| R-065 | Manifest hash of checklist template does not match upstream bytes | templates/checklist-template.md | v1.4.3 | 9d1e801c3e168869a04ab60c66ca0dae4a77614f | stale | 0 |
| R-066 | Upstream plan template is identical in v1.1.2 | templates/plan-template.md | v1.1.2 | 36f2eab16880bac670fe43cbe7ef2b9bc8c3aa2f | present | 0 |
| R-067 | Upstream tasks template is identical in v1.1.2 | templates/tasks-template.md | v1.1.2 | 7fff087cc5a3c51a889d865fd9126607a032d233 | present | 0 |
| R-068 | Upstream checklist template is identical in v1.1.2 | templates/checklist-template.md | v1.1.2 | 9d1e801c3e168869a04ab60c66ca0dae4a77614f | present | 0 |
| R-069 | Repository plan template differs from upstream | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | stale | 0 |
| R-070 | Repository tasks template differs from upstream | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | stale | 0 |
| R-071 | Repository checklist template differs from upstream | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | stale | 0 |
| R-072 | Upstream git extension version is 1.0.8 | extensions/git/extension.yml | v1.4.3 | 7ef2740a9216043a8b634740733649936a239b4c | present | 0 |
| R-073 | Upstream PowerShell script create-new-feature-branch.ps1 exists | extensions/git/scripts/powershell/create-new-feature-branch.ps1 | v1.4.3 | 697ae9c426bc75abd0460989e6a2b7bf70224585 | present | 0 |
| R-074 | Upstream PowerShell scan reads direct children only | extensions/git/scripts/powershell/create-new-feature-branch.ps1 | v1.4.3 | 697ae9c426bc75abd0460989e6a2b7bf70224585 | present | 71 |
| R-075 | Upstream ScopePrefix defaults to an empty string | extensions/git/scripts/powershell/create-new-feature-branch.ps1 | v1.4.3 | 697ae9c426bc75abd0460989e6a2b7bf70224585 | present | 86 |
| R-076 | Upstream bash script create-new-feature-branch.sh exists | extensions/git/scripts/bash/create-new-feature-branch.sh | v1.4.3 | ca3101f2de44cd4ba9b91507ec6e9a147a99424b | present | 0 |
| R-077 | Upstream Python script create_new_feature_branch.py exists | extensions/git/scripts/python/create_new_feature_branch.py | v1.4.3 | 0cf87c8dace34dc3017ce998a8358e4e70e8c984 | present | 0 |
| R-078 | Upstream feature command calls the 1.0.8 script names | extensions/git/commands/speckit.git.feature.md | v1.4.3 | 01f664f84ba1c4996d8370ad27bc526758497c3b | present | 62 |
| R-079 | Repository git extension version is 1.0.0 | .specify/extensions/git/extension.yml | main | 13c1977ea173a6b6dcf0aa4cea649a6ae75508d5 | present | 6 |
| R-080 | Registry git version is 1.0.0 | .specify/extensions/.registry | main | 9182c5c5bb820aa447e382daefe6b5fb2c467be1 | present | 5 |
| R-081 | Registry companion version is 0.24.0 | .specify/extensions/.registry | main | 9182c5c5bb820aa447e382daefe6b5fb2c467be1 | present | 23 |
| R-082 | Registry lists seven living companion commands | .specify/extensions/.registry | main | 9182c5c5bb820aa447e382daefe6b5fb2c467be1 | present | 46 |
| R-083 | Repository PowerShell git script scans direct children only | .specify/extensions/git/scripts/powershell/create-new-feature.ps1 | main | b579f051608e02cabc45f9bc4b00e3314de2f8bf | present | 56 |
| R-084 | Repository PowerShell git script has no routed resolver | .specify/extensions/git/scripts/powershell/create-new-feature.ps1 | main | b579f051608e02cabc45f9bc4b00e3314de2f8bf | absent | 0 |
| R-085 | Repository has no create-new-feature-branch.ps1 | .specify/extensions/git/scripts/powershell/create-new-feature-branch.ps1 | main | none | absent | 0 |
| R-086 | Repository bash git script scans direct children only | .specify/extensions/git/scripts/bash/create-new-feature.sh | main | f7aa31610e35e4a721514970c575cf8a13e8ba3e | present | 110 |
| R-087 | Repository has no create-new-feature-branch.sh | .specify/extensions/git/scripts/bash/create-new-feature-branch.sh | main | none | absent | 0 |
| R-088 | Feature skill calls the 1.0.0 script | .github/skills/speckit-git-feature/SKILL.md | main | aaaeb231da6157a0680d4d22d4903fbd42b368e9 | present | 55 |
| R-089 | Feature command calls the 1.0.0 script | .specify/extensions/git/commands/speckit.git.feature.md | main | 5bed9e5e57be5694dab3f5de8eee9c0081136f7f | present | 46 |
| R-090 | Skill speckit-git-commit exists | .github/skills/speckit-git-commit/SKILL.md | main | dafb5a8f3417872171c583ff16521a5463485535 | present | 0 |
| R-091 | Skill speckit-git-initialize exists | .github/skills/speckit-git-initialize/SKILL.md | main | 4d66af2e5b4e631fadd644884d93cc76038748d5 | present | 0 |
| R-092 | Skill speckit-git-remote exists | .github/skills/speckit-git-remote/SKILL.md | main | 61e9623bc39c5129ed800131244cceee556c06b8 | present | 0 |
| R-093 | Skill speckit-git-validate exists | .github/skills/speckit-git-validate/SKILL.md | main | 556d2b3128ec75a8f688f3e09e2154992e0a0fda | present | 0 |
| R-094 | Agent speckit.git.commit exists | .github/agents/speckit.git.commit.agent.md | main | c7de63ee014d61b2e3a74b92edffdc3343142889 | present | 0 |
| R-095 | Agent speckit.git.feature exists | .github/agents/speckit.git.feature.agent.md | main | 080b52c9a65451699438775e87305e9448a2eaae | present | 0 |
| R-096 | Agent speckit.git.initialize exists | .github/agents/speckit.git.initialize.agent.md | main | f7522c105a88c6445babc7fe55497cb70e99b8e4 | present | 0 |
| R-097 | Agent speckit.git.remote exists | .github/agents/speckit.git.remote.agent.md | main | b8f0fb8b8e9ef20f4e91c001d2aba1a0e9aeffec | present | 0 |
| R-098 | Agent speckit.git.validate exists | .github/agents/speckit.git.validate.agent.md | main | dfd751f2af0cb09ae74a5dd52c13b6141f55e5da | present | 0 |
| R-099 | Skill speckit-taskstoissues creates one issue for each task | .github/skills/speckit-taskstoissues/SKILL.md | main | 8c69275b7b8d5c1367ab0d0ea9a63d0a8ccf3d6c | present | 70 |
| R-100 | Skill speckit-taskstoissues sets no label | .github/skills/speckit-taskstoissues/SKILL.md | main | 8c69275b7b8d5c1367ab0d0ea9a63d0a8ccf3d6c | absent | 0 |
| R-101 | Agent speckit.taskstoissues exists | .github/agents/speckit.taskstoissues.agent.md | main | 5fdd1654d3d7266e91e7be9ef0c38837812d282b | present | 0 |
| R-102 | Repository extension.yml differs from upstream 1.0.8 | .specify/extensions/git/extension.yml | main | 13c1977ea173a6b6dcf0aa4cea649a6ae75508d5 | stale | 0 |
| R-103 | Repository README differs from upstream | .specify/extensions/git/README.md | main | 31ba75c30f23e1af082a405c24260b75305582fe | stale | 0 |
| R-104 | Repository config-template differs from upstream | .specify/extensions/git/config-template.yml | main | 8c414babe65d0045d7afc817582cd142c3e925bc | stale | 0 |
| R-105 | Repository git-config differs from upstream | .specify/extensions/git/git-config.yml | main | 8c414babe65d0045d7afc817582cd142c3e925bc | stale | 0 |
| R-106 | Repository commit command differs from upstream | .specify/extensions/git/commands/speckit.git.commit.md | main | e606f911df9d85bd6adcb94ec282f4a70940d996 | stale | 0 |
| R-107 | Repository feature command differs from upstream | .specify/extensions/git/commands/speckit.git.feature.md | main | 5bed9e5e57be5694dab3f5de8eee9c0081136f7f | stale | 0 |
| R-108 | Repository initialize command differs from upstream | .specify/extensions/git/commands/speckit.git.initialize.md | main | 4451ee6b77cb73331d0696ca55742497c7f7db38 | stale | 0 |
| R-109 | Remote command is identical to upstream | .specify/extensions/git/commands/speckit.git.remote.md | main | 712a3e8b8c7853a3360814e6465f58575ac9a28c | present | 0 |
| R-110 | Repository validate command differs from upstream | .specify/extensions/git/commands/speckit.git.validate.md | main | dd84618cb81bc0b1e1d8f7b034855965a4f7228d | stale | 0 |
| R-111 | Repository PowerShell auto-commit differs from upstream | .specify/extensions/git/scripts/powershell/auto-commit.ps1 | main | 4a8b0e00cdf05d3658aeaadd3d8b9f73da8fa5cb | stale | 0 |
| R-112 | Repository PowerShell git-common differs from upstream | .specify/extensions/git/scripts/powershell/git-common.ps1 | main | 82210000b696db8649607d16f3e18990280c01ad | stale | 0 |
| R-113 | Repository PowerShell initialize-repo differs from upstream | .specify/extensions/git/scripts/powershell/initialize-repo.ps1 | main | 324240a3e745357ffb40f1834d31aebf5c5bf182 | stale | 0 |
| R-114 | Repository bash auto-commit differs from upstream | .specify/extensions/git/scripts/bash/auto-commit.sh | main | f0b423187b6ec5f46a03faddb08f183c84ec6413 | stale | 0 |
| R-115 | Repository bash git-common differs from upstream | .specify/extensions/git/scripts/bash/git-common.sh | main | b78356d1c6914121921325d0f69031193604a817 | stale | 0 |
| R-116 | Repository bash initialize-repo differs from upstream | .specify/extensions/git/scripts/bash/initialize-repo.sh | main | 296e363b94d0732f52ab65f84f7412daa9cf8c12 | stale | 0 |
| R-117 | Ruff excludes four paths and not .specify (extend-exclude) | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | absent | 206 |
| R-118 | Commit 00d9a16e9 (PR #4884) is on GitHub | commit 00d9a16e998b0cb5e10b6ed77da0fa909670d64f | GitHub | none | present | 0 |

Count: 118 rows. `STATUS.json` lists the same 118 checks in the same order.

Notes on the table:

- R-117 uses `absent` because the claim is negative. Ruff does not exclude `.specify`.
- R-085 and R-087 have no blob SHA because the paths do not exist on main.
- Rows R-063 to R-065 show manifest mismatches with upstream bytes. The raw, LF, and CRLF forms were all tested. None matched.

## Sources

Local sources:

- `AGENTS.md` (repository root), read in full.
- `.github/copilot-instructions.md`, read in full. The local gates table and the Spec Kit layout rules are the basis of T-LOCAL-GATES.
- `.specify/memory/constitution.md` (version 1.9.0), read in full.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`, read in full. They define the headings of this record.
- The reference record `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`, read for `spec.md`, `tasks.md`, and `analysis.md`. Its shape was copied. Its content was not.
- The legacy record `specs\numbered\0\0\1\2\3\4\4\3\4873-routed-git-port`, read in full. It is a draft, and each claim is in `analysis.md`.
- The local git extension files and the routed core files. Each cited line comes from the remote blob, as rows R-009 to R-118 show.
- `documentation\quality-gates.md` lines 9, 14, and 18 name the advisory `speckit_task_audit` job. No decision depends on that job.
- `documentation\development-tooling-migration.md` line 18 names `specs\` as the SpecKit record root. No decision depends on that line.
- The reference set in `documentation\mist-api-openapi31yaml.yaml` and `.venv\Lib\site-packages\mistapi` was not read. No claim in this record depends on a Mist API endpoint or an SDK function.
- Local worktrees sit in `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\`. They serve as evidence only, and read-only commands read them.
- Worktree `MistHelper-4873-git-extension` holds branch `chore/4873-routed-git-extension` at `76b920fbc`. That commit is not on GitHub.
- Worktree `MistHelper-4873-routed-git-port` holds branch `chore/4873-routed-git-port` at `340a7ac39`. That commit is on GitHub.
- Local main worktree status. Five unrelated source files show local edits. They are not part of this record.
- Read-only `git` commands used: `worktree list`, `rev-parse`, `log`, `show`, `ls-tree`, and `grep`. The `--no-optional-locks` flag was used for `status`.

Remote sources (fetched with `gh api`, read only):

- `https://api.github.com/repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1` (11,404 entries, not truncated).
- `https://api.github.com/repos/jmorrison-juniper/MistHelper/git/blobs/<sha>` for each row in the table.
- `https://api.github.com/repos/github/spec-kit/git/trees/v1.4.3?recursive=1` (not truncated).
- `https://api.github.com/repos/github/spec-kit/git/trees/v1.1.2?recursive=1` (not truncated).
- `https://api.github.com/repos/github/spec-kit/git/blobs/<sha>` for each upstream row.
- `https://api.github.com/repos/github/spec-kit/tags` (tags v1.4.3, v1.4.4, and v1.4.5 exist).
- `https://github.com/jmorrison-juniper/MistHelper/issues/4873#issuecomment-7072822441` (owner comment on companion deferral).
- GitHub pull request records for #4909, #4874, and #2323 (`gh pr view`).

Skills: No skill was loaded. No Podman or Juniper device behavior is in scope.

## Unverified

- **U-1**: The output of `specify integration status` and of every other Specify CLI command. This record did not run any CLI command. The brief allows reads only. SC-001 requires the PR to hold the output.
- **U-2**: The hash method and the regeneration command of the Specify CLI for the manifests. The record used byte hashes in raw, LF, and CRLF forms. Rows R-063 to R-065 do not match any form. The cause is not known. Affects FR-016 and D-11.
- **U-3**: The `manifest_hash` value for the git extension in `.specify/extensions/.registry`. The hash method is not known. T011 uses the CLI output.
- **U-4**: The generator that writes the `speckit-git-*` skill bodies. The skills are not byte-equal to the upstream commands. T009 uses the 1.0.8 command text, and the generator is not checked.
- **U-5**: Bash behavior tests run only on macOS and Linux. On Windows, the bash script receives a source check only (T004).
- **U-6**: Local commit `76b920fbc` was not diffed against upstream v1.4.3. Hunks may be reused only after a line-level review.
- **U-7**: The Ruff and Black results on the four upstream Python scripts. Neither command ran in this record.
- **U-8**: The presence of `pwsh` on the CI runner that runs `tests/guardrails`. Assumed from A-2. PR #4909 checks passed, but the run log was not read.
- **U-9**: The FR-015, FR-020, and FR-021 checks are manual. No automated test covers them.

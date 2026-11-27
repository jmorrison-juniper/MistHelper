# Tasks: Port the routed layout and the git extension to Spec Kit 1.4.3

**Input**: `spec.md` and `plan.md` in this folder. The record folder is `specs\numbered\0\0\1\2\3\4\4\3\4873-routed-git-port\`.

**Status values**: `verified-present` means main holds the result. `partial` means some of the result is on main. `absent` means main does not hold the result yet.

**Verification rule**: Each task names one command from the local gates table in `.github/copilot-instructions.md`. The commands run from the repository root in `.venv`.

**Test first**: T004 and T005 write the failing tests. Tasks T006 to T012 make those tests pass.

## Format: `[ID] [P?] Description`

- **[P]**: The task edits files that no other parallel task edits.

## Phase 1: Verify delivered work

- [ ] **T001** [P] (verified-present). Confirm the routed core on `main`.
  - Requirements: FR-001, FR-002, FR-003, FR-004, FR-005.
  - Paths: `.specify/scripts/powershell/create-new-feature.ps1`, `.specify/scripts/powershell/common.ps1`, `.specify/scripts/powershell/spec-route.ps1`, `tests/guardrails/test_routed_core_port.py`.
  - Acceptance: Rows R-009 to R-024 in `design/research.md` show each rule on `main`.
  - Verification: `python -m pytest tests/guardrails/test_routed_core_port.py`.

- [ ] **T002** [P] (verified-present). Confirm the feature pointer ignore rule from issue #4882.
  - Requirements: FR-019, FR-020.
  - Paths: `.specify/.gitignore`, `tests/guardrails/test_specify_gitignore_keeps_feature_json.py`.
  - Acceptance: `.specify/.gitignore` line 8 re-includes `feature.json`. Row R-029 shows it on `main`.
  - Verification: `python -m pytest tests/guardrails/test_specify_gitignore_keeps_feature_json.py`.

- [ ] **T003** [P] (verified-present). Confirm the routed templates keep their repository content.
  - Requirements: FR-006.
  - Paths: `.specify/templates/plan-template.md`, `.specify/templates/tasks-template.md`, `.specify/templates/checklist-template.md`.
  - Acceptance: No template file changes in this change. Rows R-056, R-058, R-060, R-069 to R-071 record the repository content.
  - Verification: `python -m pytest tests/guardrails/test_integration_local_rules.py`.

## Phase 2: Write the failing tests

- [ ] **T004** [P] (absent). Write `tests/guardrails/test_routed_git_extension_port.py` before any script change.
  - Requirements: FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-022.
  - Paths: `tests/guardrails/test_routed_git_extension_port.py`.
  - Acceptance: The file holds these tests: `test_powershell_numbering_scans_the_routed_tree`, `test_bash_numbering_scans_the_routed_tree`, `test_powershell_feature_number_follows_routed_records`, `test_git_then_core_dry_run_routes_the_record`, `test_skills_name_the_1_0_8_scripts`, `test_removed_agents_and_taskstoissues_are_absent`, and `test_adopted_scripts_are_ascii_only`. The run fails before T006 to T010. Each failure prints the file and the rule.
  - Verification: `python -m pytest tests/guardrails/test_routed_git_extension_port.py`.
  - Depends on: none.

- [ ] **T005** [P] (absent). Write `tests/guardrails/test_integration_local_rules.py` before any manifest change.
  - Requirements: FR-016, FR-017, FR-018.
  - Paths: `tests/guardrails/test_integration_local_rules.py`.
  - Acceptance: The file holds these tests: `test_managed_hashes_match_or_have_a_local_rule`, `test_local_rule_list_names_only_managed_files`, and `test_routed_templates_keep_local_rule`. The run fails before T012 and T013. The failure names each mismatched file, with its count.
  - Verification: `python -m pytest tests/guardrails/test_integration_local_rules.py`.
  - Depends on: none.

## Phase 3: Git extension 1.0.8

- [ ] **T006** (absent). Adopt the upstream v1.4.3 git extension tree.
  - Requirements: FR-010, FR-022.
  - Paths: modify `.specify/extensions/git/extension.yml`, `README.md`, `config-template.yml`, `git-config.yml`, `commands/speckit.git.commit.md`, `commands/speckit.git.feature.md`, `commands/speckit.git.initialize.md`, `commands/speckit.git.validate.md`, `scripts/powershell/auto-commit.ps1`, `scripts/powershell/git-common.ps1`, `scripts/powershell/initialize-repo.ps1`, `scripts/bash/auto-commit.sh`, `scripts/bash/git-common.sh`, `scripts/bash/initialize-repo.sh`. Delete `scripts/powershell/create-new-feature.ps1` and `scripts/bash/create-new-feature.sh`. Add `scripts/powershell/create-new-feature-branch.ps1`, `scripts/bash/create-new-feature-branch.sh`, and `scripts/python/auto_commit.py`, `create_new_feature_branch.py`, `git_common.py`, `initialize_repo.py`. Keep `commands/speckit.git.remote.md`.
  - Acceptance: Each adopted path matches its upstream v1.4.3 blob, except the two routed scripts changed by T007 and T008. `extension.yml` reads version `1.0.8`.
  - Verification: `python -m pytest tests/guardrails/test_routed_git_extension_port.py`.
  - Depends on: T004.

- [ ] **T007** (absent). Apply the routed numbering to the PowerShell 1.0.8 script.
  - Requirements: FR-008, FR-011, FR-021.
  - Paths: `.specify/extensions/git/scripts/powershell/create-new-feature-branch.ps1`.
  - Acceptance: `Get-HighestNumberFromSpecs` scans `specs\` with `Get-ChildItem -LiteralPath $SpecsDir -Directory -Recurse`. The script dot-sources `spec-route.ps1` when the routed core exists. Each changed line has an inline comment.
  - Verification: `python -m pytest tests/guardrails/test_routed_git_extension_port.py`.
  - Depends on: T006.

- [ ] **T008** [P] (absent). Apply the routed numbering to the bash 1.0.8 script.
  - Requirements: FR-009, FR-021.
  - Paths: `.specify/extensions/git/scripts/bash/create-new-feature-branch.sh`.
  - Acceptance: `get_highest_from_specs` reads `find "$specs_dir" -mindepth 1 -type d` with a line-by-line loop over `specs/`. The loop handles spaces in paths. Each changed line has an inline comment.
  - Verification: `python -m pytest tests/guardrails/test_routed_git_extension_port.py`.
  - Depends on: T006.

- [ ] **T009** [P] (absent). Update the five `speckit-git-*` skills.
  - Requirements: FR-012.
  - Paths: `.github/skills/speckit-git-commit/SKILL.md`, `.github/skills/speckit-git-feature/SKILL.md`, `.github/skills/speckit-git-initialize/SKILL.md`, `.github/skills/speckit-git-remote/SKILL.md`, `.github/skills/speckit-git-validate/SKILL.md`.
  - Acceptance: `speckit-git-feature/SKILL.md` names `create-new-feature-branch.ps1` and `create-new-feature-branch.sh`. No skill names `create-new-feature.ps1`.
  - Verification: `python -m pytest tests/guardrails/test_routed_git_extension_port.py`.
  - Depends on: T006.

- [ ] **T010** [P] (absent). Remove the agents, the taskstoissues skill, and the taskstoissues agent.
  - Requirements: FR-013, FR-014.
  - Paths: delete `.github/agents/speckit.git.commit.agent.md`, `.github/agents/speckit.git.feature.agent.md`, `.github/agents/speckit.git.initialize.agent.md`, `.github/agents/speckit.git.remote.agent.md`, `.github/agents/speckit.git.validate.agent.md`, `.github/agents/speckit.taskstoissues.agent.md`, and `.github/skills/speckit-taskstoissues/SKILL.md`.
  - Acceptance: None of the seven paths exists. Caution: the git history keeps each file.
  - Verification: `python -m pytest tests/guardrails/test_routed_git_extension_port.py`.
  - Depends on: T004.

- [ ] **T011** [P] (absent). Move the `git` registry entry to version 1.0.8.
  - Requirements: FR-010, FR-015.
  - Paths: `.specify/extensions/.registry`.
  - Acceptance: The `git` entry reads version `1.0.8`. The `companion` entry still reads `0.24.0` and keeps its 23 commands. The `manifest_hash` value comes from the Specify CLI, as U-3 records.
  - Verification: `python -m pytest tests/guardrails/test_integration_local_rules.py`.
  - Depends on: T006.

## Phase 4: Integration state and documentation

- [ ] **T012** (partial). Regenerate both integration manifests from the committed content.
  - Requirements: FR-016.
  - Paths: `.specify/integrations/copilot.manifest.json`, `.specify/integrations/speckit.manifest.json`.
  - Acceptance: Eight of twenty-two hashes match today. Rows R-041 to R-062 record each result. After T006 to T011, every managed hash matches its committed file. Both versions read `1.4.3`. The Specify CLI writes the hashes, as U-2 records.
  - Verification: `python -m pytest tests/guardrails/test_integration_local_rules.py`.
  - Depends on: T006, T007, T008, T009, T010, T011.

- [ ] **T013** (absent). List each local rule in `.github/copilot-instructions.md`.
  - Requirements: FR-017.
  - Paths: `.github/copilot-instructions.md`.
  - Acceptance: A new table lists each managed file that differs from upstream, with its reason. The table holds the routed core files, the routed templates, and `.specify/.gitignore`. The text passes the STE gate.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md`.
  - Depends on: T012.

- [ ] **T014** [P] (absent). Add the changelog fragment.
  - Requirements: FR-007.
  - Paths: `changelog.d/issue-4873-routed-git-extension.md`.
  - Acceptance: The fragment has one `###` heading. It has one bullet for each change type that applies. The bullet names issue 4873.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`.
  - Depends on: none.

- [ ] **T015** (partial). Publish the record at the route.
  - Requirements: FR-001 to FR-022 (record copy).
  - Paths: `specs\numbered\0\0\1\2\3\4\4\3\4873-routed-git-port\spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design\`.
  - Acceptance: Part 1 files exist (rows R-001 to R-003). `analysis.md` and `design\` are absent until this task copies them. The folder holds five children or fewer at each level.
  - Verification: `python -m pytest tests/guardrails/test_process_folder_structure.py`.
  - Depends on: T013.

## Phase 5: Final gates

- [ ] **T-LOCAL-GATES** (absent). Run each local gate that applies to the changed files.
  - Requirements: FR-001 to FR-022.
  - Paths: every path in `plan.md` and the test files of T004 and T005.
  - Acceptance: Ruff passes on `.specify/` and `tests/`. Black passes. Each guard test passes. The test quality gate reports zero new findings. STE scores 80 or above. Each gate that does not apply is listed with its reason in the PR body. The quickstart lists the exact commands.
  - Verification: `python -m ruff check .`
  - Depends on: T004, T005, T006, T007, T008, T009, T010, T011, T012, T013, T014, T015.

- [ ] **T-PR** (absent). Commit, push, and open the pull request.
  - Requirements: FR-007.
  - Paths: the branch `chore/4873-routed-git-extension` and the PR body.
  - Acceptance: One Conventional Commit, `chore(spec-kit): port the git extension to 1.0.8 with routed numbering`. The PR body contains `Closes #4873`. The body lists the gate results. The test quality gate passes after the commit and before the push.
  - Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
  - Depends on: T-LOCAL-GATES.

- [ ] **T-REMOTE-CI** (absent). Wait for every required check on the PR.
  - Requirements: FR-001 to FR-022.
  - Paths: the PR created by T-PR.
  - Acceptance: Every required check reports success. Run `gh pr checks <number> --watch` before the merge request. Record each failure with its cause.
  - Verification: `python -m pytest tests/guardrails/test_ci_gate_triggers.py`
  - Depends on: T-PR.

- [ ] **T-MERGE** (absent). Enable auto-merge after the orchestrator authorizes the merge.
  - Requirements: FR-001 to FR-022.
  - Paths: the PR created by T-PR and the branch `chore/4873-routed-git-extension`.
  - Acceptance: The squash commit lands on `main`. The branch and the worktree are removed after the merge. The guard tests pass on the merged `main`.
  - Verification: `python -m pytest tests/guardrails/test_integration_local_rules.py`
  - Depends on: T-REMOTE-CI.

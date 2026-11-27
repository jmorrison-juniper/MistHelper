# Specification Analysis Report: Port the routed layout and the git extension to Spec Kit 1.4.3

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, the remote evidence rows R-001 to R-118, and the constitution (version 1.9.0).

**Method**: A read-only pass. It read the issue, the linked PRs, the remote tree at `main`, the upstream tree at tag `v1.4.3`, and two local worktrees as evidence only. No script ran, and no file in the repository changed.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
|----|----------|----------|----------|---------|------------|
| F-01 | Inconsistency | HIGH | Issue item 3 and `main` | The issue names `create-new-feature-branch.ps1`. `main` holds `create-new-feature.ps1` (version 1.0.0). Upstream v1.4.3 holds the new name (R-073, R-076). | D-5. FR-010 adopts the 1.0.8 names. |
| F-02 | Defect | HIGH | `.specify/extensions/git/scripts/powershell/create-new-feature.ps1` line 56 (R-083), `bash/create-new-feature.sh` line 110 (R-086) | Both scripts scan direct children of `specs\`. Routed records sit deeper, so numbering ignores them. Upstream line 71 repeats the scan (R-074). | D-7. FR-008 and FR-009. |
| F-03 | Inconsistency | HIGH | Issue item 5 and the issue comment of 2026-11-21 | The item asks to install companion 0.27.0. The comment defers it and keeps 0.24.0. | D-9. FR-015. |
| F-04 | Inconsistency | MEDIUM | Issue item 2 and PR #4909 | The item asks to port template changes. Upstream 1.1.2 and 1.4.3 template blobs are identical (R-066 to R-068). PR #4909 kept the repository templates. | D-2. FR-006. |
| F-05 | Defect | HIGH | Both manifests (R-041 to R-062) | Fourteen of twenty-two managed hashes differ from the committed content. Acceptance criterion 1 cannot pass today. | D-11. FR-016 and FR-017. |
| F-06 | Unverified | MEDIUM | Manifest hashes for plan, tasks, and checklist (R-056, R-058, R-060, R-063 to R-065) | The manifest hash matches neither upstream nor `main`, in raw, LF, or CRLF form. The cause is not known. | U-2. Regenerate from committed bytes. |
| F-07 | Stale | MEDIUM | Legacy tasks T005, T007, and T008 | The tasks stay unchecked. The test file, the changelog fragment, and PR #4909 exist (R-024, R-030, R-004). | T015 replaces the legacy record. |
| F-08 | Conflict | MEDIUM | Local commit `76b920fbc` and its record `4873-routed-git-extension` | The commit is not on GitHub (R-008). It uses a second record folder for the same issue. | D-14. The folder is not used. Hunks may be reused after review. |
| F-09 | Defect | MEDIUM | `.github/skills/speckit-taskstoissues/SKILL.md` (R-099, R-100) | The skill creates one issue for each task and sets no label. AGENTS.md requires a type label and a scope label. | D-13. FR-014. |
| F-10 | Resolved elsewhere | LOW | Issue item 7 | The `.gitignore` re-include exists (R-029). Issue #4882 is closed (R-006), and its fix commit `e0a36ce6d` is on GitHub (R-007). | D-10. FR-019 keeps the re-include. |
| F-11 | Ambiguity | MEDIUM | Acceptance criterion 4 | The criterion asks that the git extension create a routed record. Upstream 1.0.8 creates the branch and the number only (R-073). | D-8. FR-011 tests the git flow followed by the core step. |
| F-12 | Constitution gap | MEDIUM | Principles VI and VII | Untouched upstream lines lack inline comments and action logs. | D-18. Complexity rows C-4 and C-5. |
| F-13 | Gate scope | MEDIUM | `pyproject.toml` `[tool.ruff]` `extend-exclude` (line 206) | The exclude list omits `.specify`. Ruff and Black scan the upstream Python scripts. | T-LOCAL-GATES runs both commands. |
| F-14 | Pointer | LOW | `.specify/feature.json` (R-036) | The pointer names record 4785. Commit `00d9a16e9` restored the pointer after a merge changed it. | D-17. FR-020. |
| F-15 | Labels | LOW | Issue labels | The issue holds `docs` and `in-progress`. AGENTS.md asks for one scope label. | D-19. Add `tests`, remove `docs`. |
| F-16 | Search noise | LOW | PR #2323 | A search for `4873` returned PR #2323. Its body does not name the issue. | Excluded from linked work. |
| F-17 | Scope | MEDIUM | Upstream 1.0.8 tree (R-077) | Upstream adds four Python scripts. The repository holds none. | D-4. The full tree is adopted. |
| F-18 | Documentation gap | MEDIUM | Local rules | Four speckit managed files equal upstream content but differ from the routed content (R-051, R-052, R-054, R-059). No file lists them. | D-11. FR-017. |
| F-19 | Remote skill | LOW | `speckit.git.remote.md` (R-109) | The upstream command text is unchanged. The remote skill needs only a header check. | T009 checks the header. |
| F-20 | Config | LOW | `git-config.yml` and `config-template.yml` (R-104, R-105) | Both files hold the same bytes on `main`. Upstream 1.0.8 keeps them equal. | T006 replaces both with the upstream bytes. |

## Legacy Record Claims

Each claim comes from the part 1 record folder on `main`. Counts in `STATUS.json` come from this table.

| Claim | Source | Result | Evidence |
|-------|--------|--------|----------|
| L-01 Recursive numbering scan | spec FR-001 | verified | R-009 |
| L-02 Routing assertion and design artifact selection | spec FR-002 | verified | R-014, R-015 |
| L-03 `-LiteralPath` hardening | spec FR-003 | verified | R-011, R-018, R-019 |
| L-04 `SPECIFY_FEATURE_NO_PERSIST` switch | spec FR-004 | verified | R-016, R-017 |
| L-05 No 1.4.3 template engine | spec FR-005 | verified | R-020 |
| L-06 Part 1 leaves templates unchanged | spec FR-006 | verified | R-038 |
| L-07 CLI 1.1.2 template matches the manifest | spec FR-006 | stale | R-056, R-058, R-060, R-063 to R-065 |
| L-08 One changelog fragment | spec FR-007 | verified | R-030 |
| L-09 Change table matches merged files | plan Changes | verified | R-012, R-016, R-024, R-030 |
| L-10 T001 `-LiteralPath` in common functions | tasks T001 | verified | R-018, R-019 |
| L-11 T002 `NO_PERSIST` in path function | tasks T002 | verified | R-016 |
| L-12 T003 routed core hardening and JSON output | tasks T003 | verified | R-011, R-012 |
| L-13 T005 add the test file | tasks T005 | stale | R-024 |
| L-14 T007 add the changelog fragment | tasks T007 | stale | R-030 |
| L-15 T008 open the pull request | tasks T008 | stale | R-004 |
| L-16 T004 run the dry run and setup scripts | tasks T004 | unverified | Not counted. No run in this record. |
| L-17 T006 run the guardrail tests | tasks T006 | unverified | Not counted. No run in this record. |
| L-18 SC-002 setup scripts exit 0 | spec SC-002 | unverified | Not counted. No run in this record. |
| L-19 SC-003 spec-route guard passes | spec SC-003 | unverified | Not counted. No run in this record. |

Counts: verified 11, stale 4, absent 0.

## Coverage Summary

| Requirement | Tasks | Tests or checks |
|-------------|-------|-----------------|
| FR-001 to FR-005 | T001 | `test_routed_core_port.py` (existing) |
| FR-006 | T003 | `test_routed_templates_keep_local_rule` |
| FR-007 | T014 | `test_changelog_fragment_policy.py` (existing) |
| FR-008 | T004, T007 | `test_powershell_numbering_scans_the_routed_tree`, `test_powershell_feature_number_follows_routed_records` |
| FR-009 | T004, T008 | `test_bash_numbering_scans_the_routed_tree` |
| FR-010 | T006, T011 | `test_skills_name_the_1_0_8_scripts`, `test_adopted_scripts_are_ascii_only`, and the blob check in `quickstart.md` |
| FR-011 | T004, T007 | `test_git_then_core_dry_run_routes_the_record` |
| FR-012 | T009 | `test_skills_name_the_1_0_8_scripts` |
| FR-013, FR-014 | T010 | `test_removed_agents_and_taskstoissues_are_absent` |
| FR-015 | T011 | Registry check in `quickstart.md` (manual) |
| FR-016 | T012 | `test_managed_hashes_match_or_have_a_local_rule` |
| FR-017 | T013 | `test_local_rule_list_names_only_managed_files` |
| FR-018 | T005 | `test_managed_hashes_match_or_have_a_local_rule` |
| FR-019 | T002 | `test_specify_gitignore_keeps_feature_json.py` (existing) |
| FR-020 | T-LOCAL-GATES | `quickstart.md` read-only check (SC-006) |
| FR-021 | T007, T008 | PR review (manual) |
| FR-022 | T004 | `test_adopted_scripts_are_ascii_only` |

## Unresolved Items

- **U-2**: The Specify CLI hash method. Not verified. Affects FR-016.
- **U-3**: The `manifest_hash` value of the git registry entry. Written by the CLI. Not verified.
- **U-4**: The generator that writes the `speckit-git-*` skill bodies. Not verified.
- **U-5**: The bash behavior test runs only on macOS and Linux. The Windows run covers the source contract only.
- **U-6**: Local commit `76b920fbc` has not been diffed against upstream. Hunks need review before reuse.
- **U-7**: Ruff and Black results on the upstream Python scripts. Not run.
- **U-8**: `pwsh` on the CI runner. Assumed (A-2 in `spec.md`).
- **FR-015, FR-020, FR-021** rely on a manual check. No automated test covers them.

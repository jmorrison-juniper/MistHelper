# Specification Analysis Report: Release Publication

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, the two contracts, and the remote code at `main` commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

**Method**: A read-only pass built the requirement inventory, the task coverage map, and the premise check. The pass compared each issue claim with remote evidence. Each evidence row is in `design/research.md`.

## Tests

- **TEST-1**: `tests/guardrails/test_changelog_fragment_policy.py`. An existing guard. It checks fragment names, content, the release-branch edit rule (RC-35), and the `changelog.d` text in `CHANGELOG.md` (RC-36). CI runs it (RC-33).
- **TEST-2**: `tests/guardrails/test_markdown_links.py`. An existing guard. It checks every relative link in the tree (RC-37). CI runs it in the shard paths (RC-34).
- **TEST-3**: `tests/contract/test_release_body_workflow.py`. An existing contract test. It proves the release body source without a release run (RC-70). CI runs it in the shard paths (RC-34).
- **TEST-4**: A one-time reconciliation. The implementer runs it and does not commit it. It checks the fragment count, the entry count, the verbatim text, the empty Unreleased section, the changed paths, the package version, the stamp order, the absent tag, and the list of GitHub write commands. Output goes to `test-artifacts/release-4756/`.
- **TEST-5**: Owner checks. The owner runs OWN-001 to OWN-005 and records each result in the summary comment.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
| - | - | - | - | - | - |
| A1 | Inconsistency | HIGH | Issue 4756 title and plan step 1 | The tag `v26.11.10.22.38` sorts before the latest release `v26.11.21.06.27` (RC-02). The stamp equals the issue creation time (RC-59). | D-1. A new stamp is set at T003. FR-004 requires a later stamp. |
| A2 | Inconsistency | HIGH | Issue 4756 body, "Current state" | The issue names `v26.09.28.19.49` as the latest release. The latest release is `v26.11.21.06.27` (RC-02). The issue body is stale (RC-60). | Spec Clarifications and FR-016. |
| A3 | Inconsistency | HIGH | Issue 4756 body, "Current state" | The issue counts 288 fragments. The current count is 334 (RC-15). | FR-001 collects every fragment at branch time. The count is recorded in T001. |
| A4 | Inconsistency | MEDIUM | Issue 4756, owner comment 1 | The comment says a clean release branch exists. No `release/` branch exists on the remote (RC-05). | T002 creates the branch. |
| A5 | Defect | MEDIUM | Release `v26.11.21.06.27` | `CHANGELOG.md` did not change after `v26.09.28.19.49` (RC-07 and RC-08). The release body footer links to a `CHANGELOG.md` section at that tag that does not exist (RC-69). | This release adds the section (FR-001). The old release stays unchanged. |
| A6 | Defect | LOW | Issue 4756, owner comment 1 | The comment says the 14 hold pull requests modify fragments on `main`. They add fragments. Thirteen merged, and PR 4208 is open (RC-17, RC-18, RC-19). | The hold list is recounted in T001. |
| A7 | Conflict | MEDIUM | Brief and AGENTS line 194 | The AGENTS branch pattern, which uses a type, the issue number, and a slug, conflicts with the changelog guard. The guard allows a `CHANGELOG.md` edit only on a `release/` head (RC-35). | D-3. The branch is `release/4756-release-publication`. |
| A8 | Conflict | MEDIUM | PR template item 38 (RC-40) | The template requires `CHANGELOG.md` unchanged on a branch. The release pull request changes it by design. | T-PR marks items 36 and 38 as not applicable, with the reason. |
| A9 | Risk | HIGH | `auto-merge.yml` line 65 and `container-build.yml` line 114 (RC-30, RC-31) | Each merge to `main` dispatches the container build with an automatic stamp. The merge of the release pull request therefore moves `latest` before the release tag build does. | D-11. Recorded in the edge cases, risks, and summary. A separate issue tracks the workflow change. |
| A10 | Risk | MEDIUM | `close-linked-issues.yml` line 46 (RC-32) | `Closes #4756` closes the issue at merge, before the owner steps finish. | D-7 keeps `Closes` as the brief requires. The summary comment lists OWN steps as open. |
| A11 | Risk | MEDIUM | `Containerfile` line 27 (RC-42) and `pyproject.toml` line 3 (RC-41) | The image version label and the package version both read `2.1.0`. The release stamp differs from both. The source of the image version label after the build is unverified. | D-5 keeps the package version. OWN-004 records the observed label. U-3 stays unverified. |
| A12 | Risk | MEDIUM | 334 fragments (RC-15) | A fragment may hold a relative link that resolves from `changelog.d/` and breaks at the root. The links were not counted. | T004 rewrites each relative link. TEST-2 proves the result (RC-37). U-8 stays open until TEST-2 passes. |
| A13 | Gap | LOW | `changelog.d/README.md` lines 67 to 72 (RC-44) | The README gives the coordinator the aggregate step but no reconciliation check. | TEST-4 supplies the check. |
| A14 | Open | HIGH | PR 4208 (RC-19) | PR 4208 is open. The owner hold asks for a merge or a close before release preparation continues. | D-6 is HUMAN-DECISION-REQUIRED. T001 and T-PR wait for the decision. |
| A15 | Open | MEDIUM | Branch protection (RC-22) | `main` requires 15 checks, strict up-to-date branches, and admin enforcement. A stale branch or an admin bypass cannot merge. | D-9 requires one serial slot. No bypass is in scope. |
| A16 | Open | LOW | `tasks.md` owner steps | Owner steps use `git`, `gh`, and `podman`. The local gates table has no row for these checks. | plan.md Verification Approach documents the exception. |

## Coverage Summary

| Requirement | Has task | Task IDs | Tests | Notes |
| - | - | - | - | - |
| FR-001 | Yes | T004, T005, T007 | TEST-4, TEST-2 | Collects every fragment at branch time. |
| FR-002 | Yes | T006 | TEST-1, TEST-4 | Keeps `README.md`. |
| FR-003 | Yes | T005 | TEST-4 | Unreleased stays empty. |
| FR-004 | Yes | T003 | TEST-4 | Stamp is later and unused. |
| FR-005 | Yes | T002 | TEST-1 | Release branch name. |
| FR-006 | Yes | T-PR | TEST-1 | Title, `Closes`, counts, and gate results. |
| FR-007 | Yes | T-LOCAL-GATES | TEST-1, TEST-2, TEST-3 | Local gates before push. |
| FR-008 | Yes | T-REMOTE-CI | TEST-1, TEST-2, TEST-3 | Required checks in CI. |
| FR-009 | Yes | T-MERGE | TEST-4 | Serial slot and inventory re-check. |
| FR-010 | Yes | OWN-001 | TEST-5 | Peeled tag equals the merge commit. |
| FR-011 | Yes | OWN-002, OWN-003 | TEST-3, TEST-5 | Workflow success and three assets. |
| FR-012 | Yes | OWN-004 | TEST-5 | Digest and revision label. |
| FR-013 | Yes | OWN-005 | TEST-3, TEST-5 | Title pattern and links. |
| FR-014 | Yes | T005, T007 | TEST-4 | Only the section changes. |
| FR-015 | Yes | T007 | TEST-4 | Package version stays `2.1.0`. |
| FR-016 | Yes | T001 | TEST-4 | Premise rows in research. |
| FR-017 | Yes | T001, T-PR | TEST-4 | PR 4208 gate. |
| FR-018 | Yes | T-PR, T-MERGE | TEST-4 | GitHub write log. |

Every requirement maps to at least one task and at least one test. Every task maps to at least one requirement. No task is unmapped.

## Constitution Alignment

- Principle I (five-item rule): the release lowers the `changelog.d/` child count from 334 to one (RC-62 and RC-15). The plan records the debt.
- Principle IV (deployment pipeline): the release follows the gate, pull request, CI, squash, main build, and revision steps. Step 12 is out of scope.
- Principles V to VII: no code is committed, so logging and comment rules do not apply to committed files.
- Principle III: the reconciliation reads files and writes only under `test-artifacts/`.

## Metrics

- Requirements: 18. Success criteria: 6. Tasks: 16 (11 agent and 5 owner). Tests: 5.
- Decisions: 11. Human decisions: 1 (D-6).
- Remote checks: 70 (research table rows RC-01 to RC-70).
- Findings: 16.

## Unresolved Items

- D-6: merge or close PR 4208. This needs the owner decision.
- The stamp value. T003 sets it when the branch opens.
- The release summary words for the title. OWN-005 sets them.
- The observed image version label. OWN-004 records it.
- The observed `latest` digest after the merge build and the release build. OWN-004 records it.
- The relative-link count in the fragments. T004 and TEST-2 settle it.

## Convergence

Repeat T001 and quickstart Scenario 1 before T002, and again before T-MERGE. Compare the main head, the fragment count, PR 4208 state, and the tag and branch absence with research rows RC-01, RC-15, RC-19, RC-04, and RC-05. If a value changed, update the research table and repeat T004 to T007.

# Specification Analysis Report: Isolate Marvis Alarm Handling Modules

**Scope**: The consistency review of `spec.md`, `plan.md`, and `tasks.md` against the remote code on `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, and against the archive branches. Each finding cites a row of `design/research.md`.

**Method**: Remote tree reads, remote contents reads, GitHub compare and pull request reads, and read-only local views. No test, lint, build, or container command ran in this research. Every test count in this report is a count of source lines, not a test result.

## Findings

| ID | Area | Finding | Evidence | Action |
| - | - | - | - | - |
| F-01 | Hold | Open PR #4208 changes the symbol guard file that the move must edit. | R44, R77 | Wait for the release or a handoff (FR-011, T002, T010, D-3). |
| F-02 | Candidate base | The later candidate starts 43 commits behind main. PR #4607 changed Marvis action tests on main after that base. | R68, R69, R75 | Start a fresh branch from main (D-9). |
| F-03 | Working tree | The shared checkout holds five unrelated modified files. | E-2 | Use a new worktree (T001). Never stage those files. |
| F-04 | Legacy record | The archive record holds three verified claims, five stale claims, and two absent claims. Its Python version is wrong. | Legacy record check L1 to L10 and R48 to R57 | Replace the record. Reuse only the folder name and the git mv instruction. |
| F-05 | Governance | The changelog rules conflict. The constitution requires one fragment for each change. Rule 4 of the changelog README exempts internal changes. The copilot instructions limit the rule to user-visible changes. | R35, R34, R36, R62 | Add one fragment (D-7). Flag the wording for the release coordinator. |
| F-06 | Governance | The constitution states a mistapi 0.59 floor. The copilot instructions pin 0.64. The installed version 0.64.1 satisfies both. | R32, R30, R60 | Record only. No edit in this change. |
| F-07 | Gate documentation | The nested source package row names `test_move_module_guidance.py`. The ratchet itself is `test_nested_package_structure.py`. | R28, R19 | Run both files (T011 and T-LOCAL-GATES). |
| F-08 | Gate documentation | The symbols row applies plain `symbol-diff` to each changed file. A renamed path cannot use plain `symbol-diff`. | R29, R96, R21 | Use the rename-aware test for the moved modules (D-2). |
| F-09 | Debt | `_send_batches` holds 28 lines, and `apply` holds 29 lines. The limit is 25. | R02, R03, R88, E-6 | Record and remediate under #3824 (D-6). |
| F-10 | Debt | The top-level name counts are 7, 6, and 25. The limit is 5. | E-6, R31 | Record and remediate under #3824 (D-6). |
| F-11 | Unverified claim | The batch-size comment cites a 1,000 alarm ID document limit. The OpenAPI acknowledge description and the `alarm_ids` schema do not state that limit. | R73, R38, R39 | Unverified (U-1). No edit to the comment. |
| F-12 | Unverified claim | The candidate issue comments report test counts and failure counts. This research ran no test. | U-2, U-3 | Re-measure in T-LOCAL-GATES. |
| F-13 | Content | The moved modules match main byte for byte after the move. | R46, R47, R02, R03 | Reuse the verified content. |
| F-14 | Historical record | Record 3339 cites the old module path. | R43 | Do not edit it. The issue forbids historical edits. The old-path search excludes `specs/`. |
| F-15 | Route | The route is the base-5 expansion of 4008. The route parents hold capacity for one new child at depth eight. | R33, R41, R64, E-8 | No change. |
| F-16 | Symbol proof | Without a mapping, the rename-aware test checks the old path, and the old path fails its file check. | R65, R21 | Add the two mappings (D-2). |
| F-17 | Logger names | Both moved modules create a logger from `__name__`, so each logger name changes. The focused test reads `__name__`. | R71, R72, R67, E-3 | Accept and record the change (D-10). |
| F-18 | Menu map | The interactive-safe map row for acknowledge cites `client.py`. No row names a moved module. | R63, E-14 | Expect no change. Verify in T012 (U-5). |
| F-19 | Historical PR | PR #4372 matched the issue number only inside a session identifier. | R76 | Not linked. No action. |

## Coverage Summary

Each functional requirement maps to at least one task and at least one verification command. The verification commands come from `design/quickstart.md`.

| Requirement | Tasks | Verification |
| - | - | - |
| FR-001 | T003, T004 | Blob hashes and the import smoke test (quickstart steps 8 to 10). |
| FR-002 | T003, T009, T011 | `tests/guardrails/test_src_domain_structure.py` and `tests/guardrails/test_nested_package_structure.py`. |
| FR-003 | T005, T006, T007, T008 | The `symbol-diff` checks, `tests/unit/marvis/actions`, and the old-path search. |
| FR-004 | T004, T010 | `tests/guardrails/test_src_public_symbol_preservation.py`, function `test_moved_modules_lose_no_module_level_symbol`. |
| FR-005 | T007, T-PR | `test_the_join_logs_before_and_after` in `tests/unit/marvis/actions/test_alarms.py` (research R67). The pull request body lists the logger change. |
| FR-006 | T008 | The old-path search, and `test_tracked_text_uses_only_canonical_source_paths` (research R66). |
| FR-007 | T012 | `python -m scripts.menu_api_map --check`. |
| FR-008 | T011 | `tests/guardrails/test_nested_package_structure.py`, function `test_nested_package_ratchet_matches_main`. |
| FR-009 | T013 | `tests/guardrails/test_changelog_fragment_policy.py` (research R62). |
| FR-010 | T009, T010, T011 | `python -m pytest tests\guardrails -q`. |
| FR-011 | T001, T002, T-PR, T-MERGE | The open pull request scan (research R77) and the orchestrator authorization. |
| FR-012 | T-LOCAL-GATES, T-REMOTE-CI, T-MERGE | The gate rows of `design/quickstart.md`, and `gh pr checks --watch`. |
| FR-013 | T-PR | The touched-debt table in `plan.md`. Guard regression is covered by `python -m pytest tests\guardrails -q`. No guard measures function length or name counts. |

## Constitution Alignment

The plan's constitution table gives one verdict for each rule. Three verdicts fail because of pre-existing debt: the two function lengths and the top-level name counts. The move adds no new violation. The remediation action is recorded in the plan and in finding F-09 and F-10.

## Defects in the Archive Record

These defects belong to the archive record at commit `b571d2e7`. This record replaces that content.

- The feature branch uses a bare slug. AGENTS requires a type prefix (R49, R93).
- The plan states Python 3.13 or newer. The repository requires 3.15 (R50, R30).
- The plan states that logger names do not change. Both modules create loggers from `__name__` (R51, R71, R72).
- The plan limits the change to three specification files. The record layout needs five or more (R54 and the brief, section 4).
- The changelog fragment uses a bare heading, and it omits the bold change-type bullet (R56, R34).

## Unresolved Items

1. PR #4208 must release the symbol guard file, or the coordinator must issue a file-scoped handoff (FR-011, D-3).
2. The remediation child issue under #3824 must exist before the pull request opens (T-PR, D-6).
3. The governance text conflicts in finding F-05 and finding F-06 need the release coordinator.
4. The 1,000 alarm ID comment is unverified (U-1). A later change can correct the comment.
5. The candidate test counts are unverified (U-2). T-LOCAL-GATES measures the counts.
6. The nested ratchet and the test counts must be measured again on the rebased tree before the pull request opens.

## Metrics

| Metric | Value |
| - | - |
| Functional requirements | 13 |
| Success criteria | 5 |
| Tasks, including final tasks | 17 |
| Focused test functions, including the new test | 223 |
| Remote checks | 98 |
| Decisions | 12 |
| Human decisions | 0 |

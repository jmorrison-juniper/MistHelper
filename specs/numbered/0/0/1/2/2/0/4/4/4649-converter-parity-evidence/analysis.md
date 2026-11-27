# Specification Analysis Report

## Result

This record defines the evidence gate for parity task T033. Parity T033 stays partial. The register holds 40 open rows. Six gates stay open: G1, G2, G3, G4, G5, and GV. Of the 33 parity tasks, 11 are partial, 22 are absent, and none is verified-present. This change adds no product behavior and makes no cloud call.

## Evidence Boundary

| Evidence | Value |
| --- | --- |
| MistHelper main commit | `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, committed 2026-11-26T07:15:01Z (R-checks read this revision) |
| Remote tree | 11404 entries, `truncated` is false |
| Upstream source revision | `d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c` (MistCiscoConfigConverter) |
| Installed SDK | mistapi 0.64.1 in `.venv\Lib\site-packages\mistapi-0.64.1.dist-info` (R77) |
| Presence rule | A local worktree never proves presence on main (decision D-4) |

## Findings

| ID | Severity | Location | Finding | Disposition |
| --- | --- | --- | --- | --- |
| F-01 | High | Parity `design/contracts/mist.md` lines 57 to 77 (R10). Parity `analysis.md` line 227 (R09). OpenAPI (R64). SDK (R75). | The 21-row write inventory omits `deleteOrgServicePolicy`. The OpenAPI file and the installed SDK both expose it. | Keep the operation open. Gates G2 and G4 decide its scope (parity T003). |
| F-02 | High | Parity `design/research.md` evidence paths and parity `plan.md` project structure. Main tree (R35, R33). | The parity files cite `tests/unit/gateway/overrides/test_cisco_config_converter.py`. That path is absent on main. The file exists at `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`. | Correct the path in parity T004 and T008 work. The audit checks each cited path on main. |
| F-03 | High | Parity `tasks.md` T006 to T027 (R36). Constitution Principle I (R18). | The parity tasks plan 11 direct test files under `tests/contract/cisco_config_converter/`. A folder with more than five children breaks the five-child rule. The parity plan does not record this debt. | Add nested packages before the first contract test (parity T006). This record does not edit the parity plan. |
| F-04 | Medium | Feature test folder (R39). Parity T017 and T031. Record 4636 `state/` package. | Projected direct children: `__init__.py`, `test_routes.py`, `test_proposals.py` (T017), `test_parity.py` (T031), `state/` (record 4636), and `evidence/` (this record). That makes six. | Nest parity T017 and T031 before the sixth child appears. |
| F-05 | High | `models.py` (R28). Parity T006. | `models.py` holds five top-level classes at lines 13, 21, 29, 38, and 84. Parity T006 adds private types to the same file. | Parity T004 defines a bounded layout before T006. Record 4636 proposes a `state/` package for this purpose. |
| F-06 | Medium | Issue 4224 `plan.md` line 15 (R12). Copilot instructions line 20 (R14). | Issue 4224 states Python 3.13. The repository requires Python 3.15. This check is stale. | Correct the statement in a separate change. This record does not edit issue 4224. |
| F-07 | Medium | Parity `analysis.md` validation section, line 90 (R09). | The recorded results (43, 20, and 74 passed) describe earlier revisions. This drafting pass ran no tests. Parity T005 needs a current run. | Run the baseline during parity T005 execution. |
| F-08 | High | Parity `design/research.md` readiness boxes at lines 191 and 193 (R07). Parity `plan.md` gate table (R08). | The storage box (line 191) and the visual box (line 193) have no gate number. The gate table lists five gates. | This record maps storage to G4 and adds GV for visual acceptance (D-7). The parity plan needs the same mapping. |
| F-09 | Medium | Constitution line 409 (R19). Copilot instructions line 451 (R17). | The constitution requires one fragment for each change. The copilot instructions require one fragment only for a change that a user sees. | Decision D-14. The owner clarifies the rule. |
| F-10 | High | `web_portal/services/config.py` line 12 (R43). `deploy/.env.example` line 155 (R45). Parity `design/contracts/portal.md` line 28 (R11). | The portal has no user authentication. The address allowlist is the only access control. Cloud writes need an operator identity that the portal does not provide. | Decision D-10 (HUMAN-DECISION-REQUIRED). |
| F-11 | High | `web_portal/services/config.py` line 113 (R44). | The secret falls back to a random UUID when `PORTAL_SECRET_KEY` is unset. Session-bound approvals fail after a restart or across workers. | Decision D-10 (HUMAN-DECISION-REQUIRED). Parity T006 adds the restart test. |
| F-12 | Medium | Issue #4649 body (GitHub). Parity `tasks.md` dependency rows at lines 156 and 157 (R04). | The issue names #4635 and #4648 as prerequisites. Parity T033 depends on T002 and T032. T032 depends on T001, T022, T028, T030, and T031. | Decision D-12 lists the open program issues as dependencies. |
| F-13 | Medium | Issue 4224 `tasks.md` lines 42, 51, 66, and 85 (R13). | Issue 4224 leaves T009, T015, T018, and T027 unchecked. T015 registers the converter blueprint and navigation. Parity T032 needs the same change. | Track under parity T032. This record does not edit issue 4224. |
| F-14 | Low | Parity `design/research.md` row C36 (R05). | The row states that the host `/health` route exists. This pass did not find that route in `web_portal/app.py`. | Unverified item U1. Parity T032 verifies the route. |

## Requirement and Task Coverage

| Requirement | Tasks | Tests |
| --- | --- | --- |
| FR-001 | T005, T008 | `test_register_lists_each_comparison_row_once` |
| FR-002 | T005, T008 | `test_each_row_has_one_allowed_disposition` |
| FR-003 | T003, T005, T008 | `test_accepted_row_cites_blob_line_and_check` |
| FR-004 | T001, T007, T008 | `test_unsupported_row_requires_owner_decision_and_limit` |
| FR-005 | T005, T008 | `test_open_row_cites_remaining_task` |
| FR-006 | T001, T002, T003, T008 | `test_gate_without_decision_stays_open` |
| FR-007 | T004, T008 | `test_task_status_uses_four_values` |
| FR-008 | T008, T012 | `test_completion_refused_while_row_or_gate_open` |
| FR-009 | T008 | `test_audit_fails_on_missing_input_or_zero_rows` |
| FR-010 | T008, T009 | `test_broken_local_link_fails_audit` |
| FR-011 | T006, T008, T010, T012 | `test_completion_phrase_refused_while_claim_refused` |
| FR-012 | T008, T010 | `test_secret_like_value_fails_audit` |
| FR-013 | T011 | `test_converter_guide_absent_without_approval` |

Every requirement maps to at least one task and at least one test. The test count is 13, and the task count is 16.

## Parity Task Status Summary

| Status | Count | Parity tasks |
| --- | --- | --- |
| partial | 11 | T001, T003, T005, T006, T008, T012, T014, T017, T018, T030, T033 |
| absent | 22 | T002, T004, T007, T009, T010, T011, T013, T015, T016, T019, T020, T021, T022, T023, T024, T025, T026, T027, T028, T029, T031, T032 |
| verified-present | 0 | None |

The evidence for each status appears in the parity status table in `design/research.md`.

## Constitution Alignment

- Structure: the record root and the `design` folder each hold five children or fewer.
- Safety: this change makes no cloud write and no live Mist request.
- Deployment: final tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE follow Principle IV.
- Observability and inline comments: this change adds no code. The future audit must satisfy Principles V to VII.
- Secrets: FR-012 forbids secret-like values in the register, and a test enforces the rule.

## Validation Performed

| Action | Result |
| --- | --- |
| Read the brief and its required files | Complete. Includes AGENTS.md, the repository instructions, the constitution, the templates, the reference record headings, and the quality-gate command at line 283 |
| Read GitHub issues with `gh issue view` (#4224, #4632 to #4649) | Read-only. States are in `design/research.md` |
| Read GitHub pull requests with `gh pr list` and `gh pr view 4596` | Read-only. PR #4596 is MERGED. No pull request links issue #4649 |
| Read the remote tree with `git/trees/main?recursive=1` | 11404 entries, not truncated |
| Decode remote files and search for lines | Completed for each cited file. Results are in the remote table |
| Read the OpenAPI blob | 4317370 bytes, 125048 lines. The 23 operation IDs each occur once |
| Search the installed mistapi package (read-only) | The 23 functions exist. The dist-info version is 0.64.1 |
| Read the upstream source at `d9be92f9` | LICENSE declares CC BY-NC 4.0. `app.py` holds 24 route decorators. The tests folder holds 8 files |
| Run tests, linters, or builds | Not run. Brief rule 2 forbids them for this drafting pass |
| Write to the repository | None. Writes stay in the draft folder and the meta folder |
| Self-review (brief section 3, step 8) | Passed after corrections. Text checks ran as PowerShell reads over the draft files only. Corrections covered one semicolon, one long sentence, one long instruction, one checklist link, and one blob SHA typo. Results: 13 requirements mapped to tasks and tests, 16 tasks with paths and verification lines, five children or fewer at each level, 77 remote checks matching across the status file and the research table, and every main-tree blob SHA matching the live tree |

## Unresolved Items

- Human decisions: D-7 (owner dispositions and visual acceptance), D-8 (legal reuse), D-9 (converter guide), and D-10 (credential policy).
- Open gates: G1, G2, G3, G4, G5, and GV.
- Findings F-01 to F-14 stay open until the parity T004 to T006 work records their dispositions.
- Unverified items U1 to U10 stay listed in `design/research.md`.

## Next Actions

1. Owners decide D-7, D-8, D-9, and D-10.
2. The parity work starts T001 to T004 after the gate evidence exists.
3. The pull request keeps the Caution line from D-11.

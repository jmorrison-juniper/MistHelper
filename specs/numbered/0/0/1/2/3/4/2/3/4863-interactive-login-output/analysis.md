# Specification Analysis Report: Interactive Login Output

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, `design/data-model.md`, and the two contracts under `design/contracts/`. The remote code was checked against the verification table of `design/research.md`.

**Method**: A read-only pass built the requirement inventory, the task coverage map, the test map, and the remote evidence map. The pass found the items below. The author fixed the items that the spec, plan, or tasks could fix. The remaining items are listed as accepted or unresolved, with the reason.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
|----|----------|----------|----------|---------|------------|
| A1 | Inconsistency | MEDIUM | `.github/copilot-instructions.md` line 21, `pyproject.toml` line 29, `requirements.txt` line 129 | The guide states `mistapi>=0.64.0,<0.65`. The package range states `>=0.64.1,<0.65`. The pin is `0.64.1`. The brief also states `>=0.64.0`. | Fixed in the record. The plan uses the pin `0.64.1` (RC-45, RC-46). The guide statement is recorded as stale (RC-47). The guide change is not made here because it is outside this issue. |
| A2 | Defect in existing tests | MEDIUM | `test_login_orchestrator.py` lines 191, 456, 594, 604. `test_msp_org_selector.py` lines 83, 244, 284, 338 to 340, 348. | Thirteen assertions read warning records for lines that become direct output. The assertions fail after the change. | Fixed by T005 and T009. Failure assertions stay unchanged. |
| A3 | Defect in existing code | LOW | `login_orchestrator.py` (22 methods), `msp_org_selector.py` (13 methods) | Both classes exceed the five-method limit. Both counts predate this change. | Recorded in Complexity Tracking, with remediation R-1 and R-2. No method is added. |
| A4 | Defect in existing comments | LOW | Each changed line in the four source files | Many comments read "routed via logger" or "legacy console message". They describe the old channel. | Fixed by T004, T007, T010, and T012. FR-017 requires new comments. |
| A5 | Inconsistency in wording | LOW | `login_orchestrator.py` line 192, prompt in `credential_prompter.py` | The legacy text mixes "Two-factor authentication" and "2FA". The new line uses "2FA". | Accepted. FR-003 and FR-020 keep the legacy wording. A later wording change is outside this issue. |
| A6 | Coverage gap | LOW | `clouds.py` | No test module covers `CloudSelector`. | Fixed by T003 with the new module `test_clouds.py`. |
| A7 | Risk to a gate | MEDIUM | `symbol-diff` gate, `login_orchestrator.py`, `msp_org_selector.py` | The added `echo` import may appear as a changed module-level name. | Accepted as a risk in `plan.md`. The gate runs as written, and its exact result goes into the pull request. No suppression is added. |
| A8 | Consistency check | PASS | `spec.md` FR-005, `plan.md` change map, `tasks.md` T007 | The five removed progress lines are the same in all three files: lines 86, 136, 169, 197, and 236. The spacer at line 85 is removed with line 86. | None needed. |
| A9 | Consistency check | PASS | `spec.md` FR-007, `plan.md`, `research.md` D-5, `tasks.md` T007 | The 2FA success line follows the debug record at line 204 in each file. | None needed. |
| A10 | Consistency check | PASS | `status file`, `spec.md`, `tasks.md`, `research.md` | Counts: 20 requirements, 21 tasks, 13 decisions, 10 new tests, and 79 remote checks. | Checked again in the final review. |
| A11 | Process limit | LOW | `_meta\validate-drafts.ps1` | The draft validator was not run. Rule 2 prohibits running scripts. | Accepted. Its checks were repeated with search. Results are in the self-review of this record. |

## Unresolved items

- U1: `mistapi/__api_session.py` line 1137 calls raw `input()` in `_getself` for a 2FA code. This call does not wrap `safe_input`. Constitution Principle III requires the wrapper. The interactive login path does not reach this call, because `login_with_return` (lines 804 to 937) does not call `_getself`. This statement comes from reading the code and was not executed. The owner decides on an upstream report.
- U2: MSP and organization names from Mist print as received. AGENTS.md asks for ASCII in printed output. The problem predates this change. It is outside this issue.
- U3: The process-wide SDK console level stays at 30 until the next SDK session construction. Caution: SDK info lines stay hidden in the same process. The risk is accepted in D-4. The mitigation is the constructor test in T006.
- U4: The browser sign-in of the operations portal (issue #4936) has its own 2FA page. It is outside this issue.
- U5: The upgrade capture portal (`auth.py` line 98) sets its own console level of 20. Its SDK lines may still print. It is outside this issue.

## Coverage Summary

| Requirement | Tasks | Tests (new or updated) | Remote evidence |
|-------------|-------|------------------------|-----------------|
| FR-001 | T003, T004, T017 | `test_render_menu_prints_direct_output_without_warning` (new) | RC-19 |
| FR-002 | T003, T004 | `test_default_cloud_choice_echoes_selection` (new) | RC-18 |
| FR-003 | T002, T016 | `test_prompt_two_factor_returns_trimmed_value` (unchanged, asserts the prompt text) | RC-41 |
| FR-004 | T005, T007 | `test_none_when_user_aborts` (updated) | RC-10 |
| FR-005 | T005, T007, T008 | `test_happy_path_delegates_to_pipeline` (updated) | RC-05, RC-06, RC-07, RC-09, RC-11, RC-15 |
| FR-006 | T006, T007 | `test_finalize_session_prints_success_without_warning` (new) | RC-14 |
| FR-007 | T006, T007 | `test_accepted_2fa_code_prints_success_line` (new) | RC-12, RC-13, RC-75 |
| FR-008 | T006, T007 | `test_refused_2fa_code_prints_no_success_line` (new) | RC-75 |
| FR-009 | T005, T006, T007 | `test_returns_session_and_clears_token` (updated), `test_sdk_success_line_stays_off_console` (new) | RC-08, RC-68 |
| FR-010 | T006 | `test_sdk_success_line_stays_off_console` (new, also checks the SDK error line) | RC-66, RC-67, RC-70, RC-80 |
| FR-011 | T002, T008, T016 | `test_http_503_login_clears_session_and_reports_server_failure` (unchanged), `test_prompt_email_returns_none_on_blank` (unchanged) | RC-04, RC-17, RC-21, RC-26 |
| FR-012 | T009, T010 | `test_banner_and_selection_print_direct_output` (new), `test_render_msp_menu_prints_all_msps` (updated) | RC-20, RC-22, RC-24, RC-25 |
| FR-013 | T009, T010 | `test_select_single_msp_autopicks_and_selects_org` (updated, asserts the progress info record) | RC-23 |
| FR-014 | T005, T007 | `test_with_grants_populates_state_and_echoes_each` (updated), `test_no_grants_prints_org_level_message` (updated) | RC-16 |
| FR-015 | T011, T012 | `test_cancel_logs_info_record` (new) | RC-01, RC-02 |
| FR-016 | T006, T015 | `test_sentinel_password_and_2fa_code_stay_out_of_output` (new) | RC-56 (secrets rule of Principle V) |
| FR-017 | T004, T007, T010, T012, T017 | Review and `rg` search in T017 | Plan change map |
| FR-018 | T017 | ASCII search in T017 | Constitution Principle V (RC-56) |
| FR-019 | T013, T014, T-PR | Documentation check (`ste-linter`) and changelog check (`ste-linter`) | RC-43, RC-53, RC-54 |
| FR-020 | T001, T-LOCAL-GATES | Full test shards and unchanged tests | RC-45 (pin unchanged) |
| SC-001 | T003, T005, T006, T009 | Each new and updated test asserts no warning record | Spec |
| SC-002 | T006 | `test_accepted_2fa_code_prints_success_line` | Spec |
| SC-003 | T016, T-LOCAL-GATES | Failure tests unchanged and passing | Spec |
| SC-004 | T015 | `test_sentinel_password_and_2fa_code_stay_out_of_output` | Spec |
| SC-005 | T-LOCAL-GATES, T-REMOTE-CI | Gate results in the pull request | Spec |

# Analysis: Multi-Site Confirm Page Plan Detail

This review checks the spec, the plan, the tasks, the design files, and the remote code against each other. It also records the defects in the existing work and the open items.

## 1. Issue Claim Check

Issue #3222 claims that the confirm page shows counts only. The claim is not confirmed in full on `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

- Confirmed: the page shows no device row, no child route row, and no phase row. The template renders only counts and summary lines for devices and child routes (research R-14 to R-16, R-20).
- Not confirmed: the page does show site names, in the pre-check table (research R-63). It shows the start time line and the reboot line (research R-64, R-65). Issue comment 6 reports the same result.
- Partly confirmed: the page shows raw family tokens, such as `ap`, in the device families line (research R-14). The issue names this defect in its acceptance criteria.

## 2. Acceptance Criteria Mapping

| Issue acceptance criterion | Spec requirement | Status on main |
| - | - | - |
| The page lists each site, each child route, each family with its versions, and every option. | FR-001, FR-002, FR-003, FR-006, FR-007 | Absent for sites beyond the pre-check table, child routes, devices, and versions. The advanced summary covers the options that child bodies send. |
| The page uses the words AP, switch, and gateway, and plain strategy names. | FR-006 | Absent. The page shows raw tokens. The strategy names already read as plain words (research R-14). |

"Every option" in the criterion means each option that a child body sends. The advanced summary already follows that rule (research R-32). Clarification C-2 in `spec.md` records this reading.

## 3. Consistency Across Spec, Plan, Tasks, and Design

- Requirements: the spec defines 16 functional requirements, FR-001 to FR-016. The traceability table in `tasks.md` maps each one to tasks and to tests.
- Tests: the spec and the tasks name 16 tests, U1 to U8, C1 to C6, E1, and J1. The list in `tasks.md` names each test. Test C3 covers FR-009. Test C2 covers FR-008.
- Tasks: the tasks file defines 19 tasks. Each task names exact repository paths and one verification command from the local gates table.
- Class design: the plan allows five members for the new class. The design names `build`, `_site_rows`, `_route_rows`, `_device_rows`, and `_missing_details`. The data model names the same keys as the contract.
- Labels: the plan places the labels in the template. The contract `design/contracts/confirm-page.md` names the labels, and the test C1 checks them.
- Decisions: the spec cites D-2, D-4, D-5, and D-10. Research section "Decisions" defines each of them with the same numbers.
- Remote counts: the STATUS file, the research table, and the summary must each state 77 remote checks. The self-review in section 8 checks this count.

## 4. Consistency with the Constitution and the Repository Rules

- Five-item rule: the plan adds no file and no directory. The plan records the existing violations as debt, with remediation actions RA-1, RA-2, and RA-3. The constitution requires this record (Principle I, research R-51).
- Test location: the issue comment proposes two new test modules. Both paths are absent on `main` (research R-09 and R-10). The spec rejects both paths (decision D-5).
- Specification threshold: AGENTS requires a specification for a change that touches three or more files (research R-52). This record meets that rule.
- Changelog: the issue-only fragment name follows the rule in `changelog.d/README.md` (research R-50).
- Destructive operation: AGENTS forbids the auto-merge label on a change to a destructive operation without a human review (research R-67). Decision D-11 applies that rule.

## 5. Defects in the Existing Work

- **Issue comment 5 cites stale lines.** It cites `org_upgrade.py:188-190` for the `CONFIRM` requirement, and `:1307-1321` for the route data. On `main`, the requirement sits at lines 191 and 192, and its check sits at line 2185 (research R-23). The route data sits at lines 1349 to 1375 (research R-19, R-21). Action: the spec cites only current lines.
- **Issue comment 5 proposes new test modules.** The proposed paths break the five-item rule in noncompliant folders. Action: decision D-5 rejects them.
- **Issue comment 12 reports local validation for commits that GitHub does not hold.** Commits `c744312c4` and `d2fc3ede8` return HTTP 422 on GitHub (research R-03, R-04). The branch `4000-fix-confirmation-scope` returns HTTP 404 (research R-05). The reported test counts and gate results have no remote evidence. Action: the spec treats them as reference evidence only.
- **The legacy record in commit `c744312c4` says the change uses the saved plan and the pre-check data only.** The current confirm route also reads the site list and the device counts through `selected_rows` (research R-21, R-55). The legacy statement omits those reads. The spec now says that the change adds no request (FR-013, decision D-3).
- **The legacy record plans unit tests in `tests/unit/upgrade_portal/test_confirm_warning.py`.** That module renders the single-site template (research R-47). Action: decision D-1 places the tests in `test_org_child_controls.py`.
- **The legacy record tasks carry completion marks.** The marks cover commits that GitHub does not hold. Action: every task in this record starts as `absent`.
- **The legacy plan blocks edits to `org_upgrade.py` while PR #4547 owns it.** PR #4547 merged on 2026-11-13 (research sources). No open pull request touches the portal paths today (research sources). Action: the plan allows the three route edits. T-PR runs an overlap check first.
- **The strict expected-failure reason for the journey is stale.** It reads "counts only, not the sites or the schedule" (research R-37). The page already shows site names and the start line. Action: task T004 removes the marker and replaces the assertion.
- **The strict expected-failure reason for the parity pair is stale.** It reads "omits warnings and advanced summary" (research R-38). The multi-site page renders the scope warning and the advanced summary under other identifiers. Action: out of scope (decision D-9).
- **The parity row C25 cites an evidence line that no longer describes the page.** Row C25 cites `org_confirm.html:8` (research R-39). Action: task T012 updates the row after the journey passes.
- **The test `test_confirm_page_names_the_sites_and_the_schedule` checks the text "10".** It does not select the canary strategy, so the failure limit is not sent. The substring can match unrelated text. Action: task T004 selects the canary strategy and asserts a named row.
- **The class docstring of `OrgUpgradeSession` names mistapi 0.63.3.** The class starts at `org_upgrade_service.py` line 34. The pinned version is `>=0.64.0,<0.65`, and the installed version is 0.64.1 (research section 10). Action: unresolved item UR-4.
- **The site list read goes through the `cloud_reader` seam.** The seam calls `mistapi.api.v1.orgs.sites.listOrgSites` (research R-55). This change does not alter that read. Action: none.

## 6. Reuse Decision for the Legacy Record

The legacy record lives in local commit `c744312c4`. It is not on GitHub (research R-03). The verification table in `design/research.md` tests each of its ten claims. The record reuses the verified claims LC-01, LC-02, LC-03, and LC-09. It rejects the stale claims LC-04 and LC-05. It rejects the claims that depend on the absent commit and branch.

## 7. Unresolved Items

- **UR-1: Follow-up issue for the parity pair.** The pair test `test_confirm_page_pair_has_the_same_review_content` needs its own issue. The orchestrator must file it. This agent cannot create issues.
- **UR-2: Family labels across pages.** The options page uses "Access points", "Switches", and "Gateways" (`org_upgrade.py` line 921, `FAMILY_LABELS`). The confirm page uses AP, switch, gateway, and session smart router (decision D-4). Recommended option: keep the issue wording now. Unify the labels in a follow-up issue.
- **UR-3: Family omitted from the stored plan.** Issue #3394 owns this defect. This change cannot show a family that the stored plan omits.
- **UR-4: The mistapi docstring.** `src/operations/execution/firmware/org_upgrade_service.py` names mistapi 0.63.3 in a docstring. Recommended option: correct the docstring in a separate documentation change.
- **UR-5: Remediation actions RA-1, RA-2, and RA-3.** The orchestrator files each follow-up issue. This record does not create them.
- **UR-6: The human safety review.** The `needs-human-review` label requires a human review before the merge. Decision D-11 keeps auto-merge disabled until the review completes.

## 8. Self-Review Results

The self-review follows section 3, step 8 of the brief.

- (a) Requirements to tasks and tests: the traceability table in `tasks.md` maps each of FR-001 to FR-016 to at least one task. Each one also maps to a planned test, an existing test, or a gate. Result: pass.
- (b) Tasks name exact paths and one verification command. Each task names exact repository paths, except T-REMOTE-CI and T-MERGE. Those two tasks change no repository file and name the pull request instead. Each verification command is a gate or test command from the local gates table. Result: pass.
- (c) Placeholders and Latin abbreviations: the review searches for the placeholder markers and the abbreviations that the brief forbids. Result: no hit in the record after the repairs in this section.
- (d) Child limits: the feature folder holds five children, the design folder holds five, the contracts folder holds three, and the checklists folder holds two. Result: pass.
- (e) Style rules: the scan found no semicolon, no contraction, no phrasal verb, no present perfect form, and no empty section. Each FR and SC line holds 25 words or fewer. Each harm statement starts with `Warning:` or `Caution:`. Result: pass.
- (f) Counts: the STATUS file, the research table, and the summary each report 77 remote checks. The STATUS file reports 12 decisions, 0 human decisions, 16 requirements, and 19 tasks. Result: pass.

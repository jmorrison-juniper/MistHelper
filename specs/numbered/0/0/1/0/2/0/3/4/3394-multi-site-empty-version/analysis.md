# Analysis: Multi-Site Save and the Empty Target Version

## Consistency Review

| Area | Spec | Plan | Tasks | Remote evidence | Result |
| - | - | - | - | - | - |
| Refusal rule (FR-001, FR-006 to FR-008) | User Story 1 and 3 | Design of the Check | T002, T004, T008 | RC20 to RC25 | Consistent |
| Refusal code and text (FR-002, FR-003) | Functional Requirements | Summary and Design | T001, T002, T007 | RC17, RC28, RC46 | Consistent |
| No stored state on refusal (FR-004) | User Story 1 | Design, last paragraph | T001, T007 | RC29, RC30 | Consistent |
| Retry view (FR-009) | Edge Cases | Design, `_selected_target_rows` paragraph | T006 | RC96, RC100 | Consistent |
| xfail replacement (FR-010) | Clarifications | Change Map | T001 | RC51, RC52 | Consistent |
| Changelog name (FR-011) | Functional Requirements | Change Map | T009 | RC11, RC57, RC58 | Consistent |
| Branch name (FR-015) | Feature Branch | Dependencies | T-PR | RC12 | Consistent |
| Route folder | Input line in `plan.md` | Project Structure | Not used by a task | RC08, RC10, RC70, RC71 | Consistent. The folder is absent today. |
| Five-item debt | Out of Scope | Complexity Tracking | Not used by a task | RC81, RC82 | Consistent |
| Counts | 15 FR, 7 SC | Not stated | 15 tasks, 7 test tasks | 105 remote rows | Consistent |

The counts are fixed as follows. The spec holds 15 functional requirements and 7 success criteria. The tasks hold 15 entries. Seven tasks create tests (T001 to T007). The remote table holds 105 rows, with 92 present, 8 absent, and 5 stale.

## Defects in Existing Work

- **A1. Stale issue path.** The issue body names the retired path `upgrade_portal/app/routes/org_upgrade.py`. That path is absent on `main` [RC01]. The current file is `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` [RC02]. The local retired folder `upgrade_portal/` holds only untracked `__pycache__` files. The local `git ls-files` check returned zero tracked files.
- **A2. Stale line numbers.** The issue body places `_selected_target_rows` near line 510. The issue comment of 2026-10-06 places it at line 755, the save handler at 1204 to 1219, and `_aggregate_option_record` at 648. The current lines are 775, 1215 to 1232, and 634 [RC03 to RC06]. The browser target filter is at line 3332, not 3311 to 3330 [RC07]. This record uses only the current lines.
- **A3. Stale pull request state.** The comment of 2026-11-11 says PRs #4701 and #4547 are draft and hold the shared files. Both merged on 2026-11-13. PRs #3996 and #3997 were open on 2026-10-06 and merged that day. On 2026-11-26, seven open pull requests exist. None touches the seven shared paths. The check used the file list of each pull request.
- **A4. Closed attempt PR 4005.** PR #4005 closed on 2026-10-06 without a merge. Its closing comment says the head commit stays preserved. The head branch returns HTTP 404 today [RC13]. Commit `f8edcb4` still resolves [RC14]. The attempt differs from this design in four ways:
  - It checks the device type across all sites. A type dropped at one site passes when another site holds a target. This design checks each site (D-2).
  - It calls `aggregate_options_view` for each selected site before the normal loop. The loop calls the same view again. This design adds no view call.
  - Its text reads `"Device target versions" requires a target version for the checked switch device type.` The text names the table label, not the version control. This design uses the text in FR-003 (D-5).
  - Its branch is not available. This design starts a new branch from `main` (D-9).
- **A5. Existing per-site guard misses a type drop.** `OrgSiteRecords.add` marks a site as unplanned only when the site has no planned row [RC37]. The refusal at `OrgSiteRecords.refusal` names only those sites [RC38]. A site with a planned access point and no planned switch passes that guard. This is the root cause of the gap. The route filter alone does not explain it.
- **A6. The xfail test conflicts with the required contract.** The xfail test expects a switch with an empty `version_switch` to reach the stored plan [RC51, RC52]. The issue requires a refusal, and it warns against any guessed version. A correct fix makes the xfail test fail with status 400, so the xfail test cannot pass. FR-010 replaces it.
- **A7. Message translation cannot name a device type.** `OrgOptionRefusal.page_field` maps every `version_target` refusal to the table label `targets` [RC19]. A reuse of `BadOptionError` therefore names no device type. This design uses a `ValueError` path with its own text (D-4).
- **A8. The browser path never reaches the mapper refusal.** The page disables the controls of unchecked types [RC42]. It sends only enabled, non-empty choices [RC43]. The mapper refusal for an empty version [RC34] never sees an empty browser choice. The issue states that the mapper refuses an empty version [RC35]. That statement is true for direct calls, not for the browser path.
- **A9. The confirmation page shows child groups.** The issue says the confirmation page shows only the device count. The template lists one group row for each planned child [RC95]. A type with no child has no row. The statement is partly accurate. This design does not change the confirmation page.
- **A10. Related issue states conflict with merged code.** Issue #3393 is open on GitHub. Its code change merged in PR #4413 on 2026-10-28. Issues #3396, #3326, and #3329 are closed. The landing order in the issue body is therefore obsolete. The only related issue that stays open is #3393, and it does not block this change.
- **A11. Example text uses the wrong verb.** The issue example says "Type the switch target version". The target version control is a list [RC47, RC48]. This design uses "Choose" (D-5).
- **A12. Existing five-item debt.** `org_upgrade.py` defines 147 top-level names [RC81]. The `upgrade` package holds 22 children [RC82]. The debt predates this issue. This change adds no debt, and the remediation is a separate action.

## Unresolved Items

- **U-1. Pytest cannot prove FR-013 and FR-014.** FR-013 relies on the scope check at task T010. FR-014 relies on review at task T011. These checks are scripted or manual.
- **U-2. Browser seed mapping.** The browser test at task T007 uses seeded constants. The mapping between each seeded site and its switch is unverified (research U1).
- **U-3. No site in the text.** The refusal names no site (D-5). An operator must find the site on the page. The risk is accepted (R2).
- **U-4. Deliberate all-opt-out refusal.** An operator who sets every device of one type to "Do not upgrade this device" at one site is refused (D-2). The risk is accepted (R1). The rule follows the issue safety rule, and no product priority decision changes it.
- **U-5. Five-item debt.** The debt in A12 remains after this change. A separate remediation action must track it.
- **U-6. Preserved attempt.** Commit `f8edcb4` resolves, but its branch does not [RC13, RC14]. This record does not reuse it. The orchestrator decides whether another reference must stay.
- **U-7. No test run in this phase.** Rule 2 forbids running tests during authoring. Each expected test result is a prediction. The implementation phase must observe the results.
- **U-8. Session database note.** The session database already held a table named `remote_checks` with 105 rows for other issues. Those rows are not evidence for issue 3394. They remain unchanged. This record stores its checks in a separate table.

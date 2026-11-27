# Research: Multi-Site Confirm Page Plan Detail

This file holds the research for issue #3222. It records the method, the issue facts, the linked work, and the existing record search. It also records the remote verification, the code path, the decisions, the legacy record check, the sources, and the unverified items.

## 1. Method

- **Required reading**: `AGENTS.md` in full. `.github/copilot-instructions.md` for the local gates table, the Spec Kit layout, and the changelog rule. `.specify/memory/constitution.md` for Principles I, III, and IV. The four templates. The reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv`, for its shape only. `documentation/upgrade_capture_portal.md`, section "Confirm and start the upgrade". The OpenAPI file for the organization upgrade schema.
- **Remote truth**: one `gh api` call fetched the main tree. The tree holds 11,404 entries, and GitHub reported no truncation. Per-path `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main --jq .sha` calls confirmed the other paths. Absent paths returned HTTP 404.
- **Local equality**: `git hash-object` on each tracked file matched its remote blob SHA. Local `HEAD` equals `origin/main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The working tree therefore matches the remote tree for each cited tracked file.
- **Limits**: no build, test, linter, formatter, install, container, repository script, or live Mist call ran. No web source was fetched, so no URL is cited.

## 2. Issue Facts

Source: `gh issue view 3222 --json number,title,body,state,labels,comments,createdAt,updatedAt,author`.

- **Title**: "Multi-site: the confirm page shows counts only, not the sites, the schedule, the phases, or the child plan".
- **State**: OPEN. Created 09/23/2026 09:50:47. Updated 11/13/2026 08:21:37. Author `jmorrison-juniper`.
- **Labels**: bug, safety, web-portal, in-progress, upgrade-portal, frontend, priority:P1, severity:high, needs-human-review.
- **Body**: the page shows the organization, the site count, and the device count. The families, the firmware line, and the strategy appear as raw words. The body lists the missing site names, schedule, phases, and child plan. Its acceptance criteria require each site, each child route, each family with its versions, and every option. The body cites old paths under the retired `upgrade_portal/` path. It was found by the journey harness of #3200.
- **Comments (12)**:
  1. 09/24/2026 13:00:08. Pull request #3322 for #3247 added the start-time line. The sites, phases, and child plan remain missing.
  2. 09/25/2026 16:15:26. Pull request #3391 merged as `b85d9118` and added four advanced lines. A site with no device of a checked type adds no child, and the page shows no sign of it. Related issue #3389.
  3. 09/26/2026 06:00:25. Pull request #3426 fixed #3389. A plain save refuses a site with no planned device. A retry skips that rule, and issue #3396 tracks the retry case.
  4. 09/30/2026 06:57:36. Branch `fix/3222-confirm-details` at `18138f9` was called ready. No pull request was opened because five open pull requests touched the same files.
  5. 10/06/2026 21:16:30. An assessment found the counts claim not confirmed. It confirmed that site and device details are missing. It cited old line numbers and proposed two new test modules.
  6. 10/06/2026 21:55:01. A second assessment found the counts claim not confirmed as written. It proposed a template-only change and reported that the route passes only the site count.
  7. 11/09/2026 17:57:12. The preserved branch uses former paths. Its new view lacks device identity rows. The issue requires a written specification and a human safety review before implementation.
  8. 11/13/2026 07:22:53. Work began in a local worktree. No pull request will be opened while `org_upgrade.py` is owned.
  9. 11/13/2026 08:12:00. Ruff failed on twelve long lines in two test files.
  10. 11/13/2026 08:19:10. The test-quality gate found three weak assertions.
  11. 11/13/2026 08:20:14. The focused tests passed after the assertion repair. Ruff found one more long line.
  12. 11/13/2026 08:21:37. The local fix was called complete. It cites commits `c744312c4` and `d2fc3ede8`. Nothing was pushed.

## 3. Linked Work

Source: `gh pr list -R jmorrison-juniper/MistHelper --state all --search "3222"` and `gh pr view`.

| Pull request | State | Title or purpose | Relevance |
| - | - | - | - |
| #4541 | MERGED, 11/05/2026 18:26:05 | "test(upgrade-portal): prove end-to-end upgrade journeys" | Its body names #3222 as a known defect. It added the journey tests. |
| #3391 | MERGED, 09/25/2026 16:08:28 | "feat(upgrade-portal): offer the advanced controls on the multi-site page" | It added the advanced lines and closes #3383. Its files use former paths. |
| #4547 | MERGED, last update 11/13/2026 08:07:43 | "fix(upgrade-portal): limit retry scope to planned sites" | It changed `org_upgrade.py`, which this change edits. |
| #4701 | MERGED, last update 11/13/2026 04:56:26 | "fix(upgrade-portal): keep site locks after uncertain replies" | It changed `org_upgrade.py` and `org_devices.py`. |
| #3955 | CLOSED, draft | "refactor(upgrade-portal): preserve lock handlers" | It uses former paths. It is closed. |

- **Open pull request scan**: `gh pr list --state open --limit 200 --json number,title,headRefName,isDraft,files` returned seven open pull requests. None lists a path that matches `upgrade_portal`, `firmware`, `test_org_`, or `confirm`. The overlap is zero.
- **Preserved branch**: the compare endpoint of the repository, with base `main` and head `fix/3222-confirm-details`, returned status `diverged`, `ahead_by` 1, and `behind_by` 579. Its single commit is `18138f9b28173c969a57d447291ffebcd6daa029`, titled "fix(upgrade-portal): show complete confirmation plan". It changes seven files under former paths, including the retired `upgrade_portal/app/assets/templates/upgrade/org_confirm.html` path.
- **Related issues**: #3200 CLOSED. #3247 CLOSED. #3383 CLOSED. #3389 CLOSED. #3393 OPEN, a server fault at the multi-site options save. #3394 OPEN, a selected family with no version is omitted from the stored plan. #3396 CLOSED. #3726 CLOSED. #4539 CLOSED. #4540 CLOSED. #4719 OPEN, "chore(git): a branch holds work with no pull request".
- **Labels in the repository**: the list includes `feature-spec`, `stage:speckit-artifacts-emitted`, `needs-human-review`, and `status:in-progress`. Each added label in the STATUS file exists in this list.

## 4. Existing Record Search

Brief section 3, step 3.

- **Working tree**: the search for any file or folder that starts with `3222` under `specs` found nothing. The search used `glob` and `Get-ChildItem -Recurse -Filter 3222*`. The working tree equals `main` at the base commit, so the remote `specs` tree matches.
- **Route folder**: `specs\numbered\0\0\1\0\0\3\4\2` does not exist on disk or on `main` (research R-07).
- **Legacy record in a commit only**: commit `c744312c4`, by Joseph Morrison, holds `specs/numbered/0/0/1/0/0/3/4/2/3222-multi-site-confirmation-scope/` with eight files: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, `design/contracts/confirmation-page.md`, and `design/checklists/requirements.md`. The same commit adds `changelog.d/issue-3222-multi-site-confirmation-scope.md`, edits `org_confirm.html`, and edits two test modules. Commit `d2fc3ede8` edits the two test modules.
- **Read and verified**: every file of the legacy record was read with `git show`. Section 8 verifies its claims. Step 4 of the brief applies: the commit is absent on GitHub (research R-03).
- **Result**: `existing_record.found` is `true` for the commit-only record. The counts are verified 4, stale 2, and absent 4.

## 5. Remote Verification

Brief section 3, step 4.

- **Tree call**: `gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1"` returned 11,404 entries and no truncation.
- **Path calls**: `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main --jq .sha` confirmed each path that the tree filter did not cover. Each absent path returned HTTP 404.
- **Commit and branch calls**: `gh api repos/jmorrison-juniper/MistHelper/commits/<sha> --jq .sha` and `gh api repos/jmorrison-juniper/MistHelper/branches/<name> --jq .commit.sha`.
- **Untracked files**: the mistapi and Flask files live under `.venv`, which git does not track. Their blob SHA is the value of `git hash-object` on the local file. The row marks the ref as `local`, so no row claims a repository commit for them.
- **Rate limits**: no HTTP 403 or HTTP 429 occurred. No retry ran.
- **Counts**: the table in section 9 holds 77 rows. The STATUS file lists the same 77 checks. The summary reports 77.

## 6. Code Path Trace

Brief section 3, step 5. Each step cites a path and a line from the blob named in section 9.

1. **Options page**: `options_page()` at `org_upgrade.py:1139` renders the form.
   - `save_options()` at line 1215 validates the form.
   - The aggregate plan builds at `_aggregate_saved_options()` at line 1273.
   - The plan persists through `_write_operation()` at line 1015.
2. **Confirmation page**: `confirm_page()` at line 1339 carries `@identity.require_session` at line 1338.
   - It reads the active context, the stored options, and the owned plan at line 1528.
   - It applies `OrgRetrySiteScope.effective_ids()` at line 1262.
   - It reads the site rows through `selected_rows()` at line 496 and `build_site_rows()` at `select.py:1044`.
   - The render call at lines 1362 to 1375 passes the counts, `strategy_children`, `advanced_summary`, `schedule`, and `prechecks`.
3. **Submit route**: `submit_upgrade()` at line 2151 calls `_submission_guard()` at line 2175.
   - The typed check is at line 2185.
   - The owned plan read is at line 2163.
   - Then `_submission_prechecks()` at line 1402, `_precheck_refusal()` at line 1417, and `_submit_aggregate()` at line 1847 run in order.
4. **Aggregate send**: `_send_child()` in `aggregate_upgrade_service.py` at line 913 routes the organization AP child to `OrgUpgradeService.submit()`.
   - That method calls `org_devices.upgradeOrgDevices()` at `org_upgrade_service.py:328`.
   - The module is imported at line 25.
5. **SDK routes**: `ENDPOINT_SITE_DEVICES = "upgradeSiteDevices"` at `upgrade_service.py:47`. `ENDPOINT_SITE_DEVICE = "upgradeDevice"` at line 48. `ENDPOINT_ORG_SSRS = "upgradeOrgSsrs"` at line 49.

## 7. Decisions

Brief section 3, step 6. Each decision names the alternatives, the choice, the reason, and the risk. No decision requires a human decision under section 6 of the brief.

**D-1. Where the view lives and how it reaches the page.**

- Alternatives: (a) template-only logic, as the legacy record planned. (b) A new module under `upgrade/`. (c) A class inside `org_upgrade.py`.
- Choice: class `OrgConfirmPlanView` in the existing module `org_child_controls.py`. `confirm_page()` passes one new argument. `submit_upgrade()` adds one refusal.
- Reason: (a) puts the completeness rules in Jinja, which tests cannot call as units. (b) adds a child to `upgrade/`, which already has at least 14 direct entries (R-69). The constitution forbids a new child in a noncompliant parent (R-51). (c) enlarges the route file that holds the write path.
- Risk: the module gains a sixth top-level name (R-68). Mitigation: remediation action RA-1 in `plan.md`.

**D-2. Fail closed in the browser and on the server.**

- Alternatives: (a) disable the typed field in the template only. (b) refuse on the server only.
- Choice: both.
- Reason: a disabled attribute does not stop a direct request to the submit route. A server refusal alone gives the operator no reason on the page.
- Risk: a stored plan with a missing field is refused. Mitigation: FR-012 limits the refusal to plans that hold child routes.

**D-3. Read the device identities, child routes, and phases from the stored plan only.**

- Alternatives: (a) read the devices from the cloud when the page renders. (b) read the phases from the options form.
- Choice: the stored plan record (R-19, R-26, R-27, R-30).
- Reason: (a) adds a cloud read. It can also show a device list that differs from the saved plan. Issue comment 5 states that no new read is required. (b) can differ from the body that the planner built. The advanced summary already follows the body rule (R-32).
- Risk: the page shows the plan as saved. Mitigation: the operator confirms that saved plan.

**D-4. Family words on the confirm page.**

- Alternatives: (a) the options page labels "Access points", "Switches", and "Gateways" (`org_upgrade.py` line 921). (b) the raw family tokens, which the page shows today (R-14).
- Choice: AP, switch, gateway, and session smart router.
- Reason: the issue acceptance criterion names AP, switch, and gateway. The token `ssr` names the session smart router family (`upgrade_service.py` line 49 and the child family rule).
- Risk: the same concept has two labels on two pages. Mitigation: unresolved item UR-2 in `analysis.md`.

**D-5. Tests in existing modules only.**

- Alternatives: (a) the new modules that issue comment 5 proposes. (b) new modules in a new folder.
- Choice: the tests extend `tests/unit/upgrade_portal/test_org_child_controls.py`, `tests/contract/upgrade_portal/test_org_upgrade_routes.py`, `tests/e2e/upgrade_portal/test_org_upgrade_flow.py`, and `tests/e2e/upgrade_portal/journeys/test_upj_multisite_journeys.py`.
- Reason: the three portal test folders already hold more than five direct files (R-70, R-71). Principle I forbids a new direct child in a noncompliant parent (R-51).
- Risk: the modules grow. Mitigation: each new test belongs to one class.

**D-6. Stable build text.**

- Alternatives: (a) show the typed version. The cloud ignores it when the stable choice is set (R-29, and the comment at `upgrade_service.py` lines 156 to 160). (b) show the token `stable`.
- Choice: "The vendor stable build" for each switch and gateway device whose child body sends the stable version.
- Reason: the text states what the cloud does and gives no number that the cloud ignores. The existing firmware summary already uses this text (`STABLE_BUILD_TEXT` at `org_upgrade.py` line 923).
- Risk: a device row shows no typed version. Mitigation: the child route row keeps the route name and the count.

**D-7. Phases from each child body.**

- Alternatives: (a) show the values of the options form. (b) show one phase list for the whole page.
- Choice: each child body's `canary_phases`, `max_failures`, and `max_failure_percentage` (R-30, R-31).
- Reason: the body is the exact request that the cloud receives. The advanced summary follows the same rule (R-32).
- Risk: a child body with no phase list shows no phase row. Mitigation: FR-004 states that each child route sends the phase list before the row appears.

**D-8. Keep the existing schedule lines.**

- Alternatives: (a) add a schedule table. (b) keep the start line, the reboot line, and the reschedule control.
- Choice: (b). The start line renders at template line 82 (R-64). The reboot line renders at line 58 (R-65). The builder names the start time (R-33).
- Reason: the issue lists the schedule as missing. Main already renders both lines. A table would repeat them.
- Risk: a reviewer may expect a separate table. Mitigation: `spec.md` records the reading in its clarifications.

**D-9. The parity pair stays out of scope.**

- Alternatives: (a) align the identifiers of the pair in this change. (b) leave the pair alone and name a follow-up issue.
- Choice: (b). The pair test expects single-site identifiers, such as `upgrade-warning-list` and `upgrade-advanced-summary`, on the multi-site page (R-38). Aligning them changes the parity contract, which needs its own issue.
- Risk: the expected failure stays. Mitigation: unresolved item UR-1 in `analysis.md`.

**D-10. The preserved branch and the local commits are reference only.**

- Alternatives: (a) rebase `fix/3222-confirm-details`. (b) cherry-pick `c744312c4` and `d2fc3ede8`. (c) start a new branch from `origin/main`.
- Choice: (c). Options (a) and (b) serve as reference.
- Reason: the preserved branch is 579 commits behind `main` and uses former paths (section 3). Both local commits are absent on GitHub (R-03, R-04). Issue comment 7 asks to keep the branch intact.
- Risk: some work repeats. Mitigation: the reference files show the intended behavior.

**D-11. Auto-merge waits for the human review.**

- Alternatives: (a) enable auto-merge after remote CI passes. (b) enable auto-merge after remote CI passes, the orchestrator authorizes the merge, and a human completes the review.
- Choice: (b).
- Reason: AGENTS forbids the auto-merge label on a change to a destructive operation without human examination (R-67). The issue carries `needs-human-review`. This rule is not a category in section 6 of the brief, so it does not set a human decision marker.
- Risk: the merge waits longer. Mitigation: task T-MERGE names the exact conditions.

**D-12. The parity matrix changes only after the journey passes.**

- Alternatives: (a) change row C25 in this change before the journey runs. (b) change row C25 only after the journey passes.
- Choice: (b).
- Reason: row C25 records a defect for the multi-site mode (R-39). A change before the proof would record an unmeasured pass. The parity contract checks that the JSON and the Markdown rows agree (R-48).
- Risk: the matrix stays stale for a short period. Mitigation: task T012 runs after task T010.

## 8. Legacy Record Verification

Brief section 3, steps 3 and 4. The legacy record is commit `c744312c4`. Each claim below comes from its files. Each result cites a remote row or a GitHub read.

| ID | Legacy claim | Result | Evidence | Reuse decision |
| - | - | - | - | - |
| LC-01 | The route passes `strategy_children` from the saved aggregate operation. | verified | R-19 | Reuse as a fact. |
| LC-02 | Each child mapping includes its route, device family, and target data. | verified | R-26, R-27 | Reuse as a fact. |
| LC-03 | The typed field stays disabled while writes are disabled or pre-checks are not ready. | verified | R-17 | Reuse as a fact. |
| LC-04 | Do not edit `org_upgrade.py` while PR #4547 owns it. | stale | PR #4547 merged, and no open pull request owns the route (section 3). | Do not reuse. |
| LC-05 | Add unit tests for the organization confirm page to `test_confirm_warning.py`. | stale | R-47 shows that the module renders `upgrade/confirm.html`. | Do not reuse. |
| LC-06 | Commit `c744312c4` holds the implementation. | absent | R-03 | Do not reuse. |
| LC-07 | Branch `4000-fix-confirmation-scope` holds the work. | absent | R-05 | Do not reuse. |
| LC-08 | The change adds no Mist cloud request. | absent | No commit on GitHub holds it. The record adopts the rule as FR-013 with its own evidence (R-21, R-55). | Reuse the requirement, not the evidence. |
| LC-09 | The typed word `CONFIRM` stays required. | verified | R-23 | Reuse as a fact. |
| LC-10 | The changelog fragment name follows the issue rule. | absent | R-08 shows that the fragment is absent. The rule itself is present (R-50). | Reuse the rule only. |

Counts: verified 4 (LC-01, LC-02, LC-03, LC-09). Stale 2 (LC-04, LC-05). Absent 4 (LC-06, LC-07, LC-08, LC-10).

## 9. Remote Verification Table

Columns: ID, claim, path, ref, blob or commit SHA, result, line, evidence. The result values are `present`, `absent`, `partial`, or `stale`. The `line` column gives the line of the claim, or 0 when the claim concerns the whole file or the absence of content. The "local" ref marks an untracked file.

| ID | Claim | Path | Ref | Blob or commit SHA | Result | Line | Evidence |
| - | - | - | - | - | - | - | - |
| R-01 | Main head is the base of this record | repos/jmorrison-juniper/MistHelper/commits/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 | gh api commits/main |
| R-02 | Preserved branch head is commit 18138f9b | repos/jmorrison-juniper/MistHelper/branches/fix/3222-confirm-details | fix/3222-confirm-details | 18138f9b28173c969a57d447291ffebcd6daa029 | present | 0 | gh api branches |
| R-03 | Legacy local commit c744312c4 exists on GitHub | repos/jmorrison-juniper/MistHelper/commits/c744312c4 | main | c744312c4 | absent | 0 | HTTP 422, no commit found |
| R-04 | Local commit d2fc3ede8 exists on GitHub | repos/jmorrison-juniper/MistHelper/commits/d2fc3ede8 | main | d2fc3ede8 | absent | 0 | HTTP 422, no commit found |
| R-05 | Legacy branch 4000-fix-confirmation-scope exists on GitHub | repos/jmorrison-juniper/MistHelper/branches/4000-fix-confirmation-scope | 4000-fix-confirmation-scope | none | absent | 0 | HTTP 404, branch not found |
| R-06 | Commit b85d9118 exists on GitHub, as issue comment 2 names for PR 3391 | repos/jmorrison-juniper/MistHelper/commits/b85d9118 | main | b85d91182381f5ab664148f432bec6c06942e26b | present | 0 | gh api commits lookup |
| R-07 | Route folder specs/numbered/0/0/1/0/0/3/4/2 exists on main | specs/numbered/0/0/1/0/0/3/4/2 | main | none | absent | 0 | HTTP 404 |
| R-08 | Legacy changelog fragment exists on main | changelog.d/issue-3222-multi-site-confirmation-scope.md | main | none | absent | 0 | HTTP 404 |
| R-09 | Proposed unit module exists on main | tests/unit/upgrade_portal/test_issue_3222_confirm_page.py | main | none | absent | 0 | HTTP 404 |
| R-10 | Proposed browser module exists on main | tests/e2e/upgrade_portal/test_issue_3222_confirm_page.py | main | none | absent | 0 | HTTP 404 |
| R-11 | Proposed view module exists on main | src/interfaces/portals/upgrade_portal/upgrade/org_confirm_view.py | main | none | absent | 0 | HTTP 404 |
| R-12 | Reference record spec exists on main | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 | remote tree |
| R-13 | Route rule uses base five and eight digits | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 | `$base = 5` and `[int]$Width = 8` at line 7 |
| R-14 | Template renders raw family tokens | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_confirm.html | main | bb388fd2845aa235c5d802fe58bbd7e981f10015 | present | 54 | device_families joined as raw text |
| R-15 | Template has no device table | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_confirm.html | main | bb388fd2845aa235c5d802fe58bbd7e981f10015 | absent | 0 | no device table testid in the file |
| R-16 | Template renders no phase list | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_confirm.html | main | bb388fd2845aa235c5d802fe58bbd7e981f10015 | absent | 0 | canary phases not rendered |
| R-17 | Template disables the typed field unless writes and pre-checks are ready | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_confirm.html | main | bb388fd2845aa235c5d802fe58bbd7e981f10015 | present | 189 | disabled condition |
| R-18 | Template renders the scope warning | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_confirm.html | main | bb388fd2845aa235c5d802fe58bbd7e981f10015 | present | 106 | org-upgrade-scope-warning |
| R-19 | Confirm route passes strategy children to the template | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1369 | strategy_children argument |
| R-20 | Confirm route passes no device or phase rows | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | absent | 0 | render_page arguments at lines 1362 to 1375 |
| R-21 | Confirm route reads the approved site rows through selected_rows | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1349 | selected_rows call |
| R-22 | Submit route has no plan completeness check | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | absent | 0 | submit_upgrade at lines 2151 to 2172 |
| R-23 | Submit route checks the typed CONFIRM word | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 2185 | confirmation check |
| R-24 | Submit route loads the owned durable plan | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 2163 | _owned_operation call |
| R-25 | Organization AP child uses the route name upgradeOrgDevices | src/operations/execution/firmware/aggregate_upgrade_service.py | main | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 674 | _base_child call |
| R-26 | Child records store route, scope, and device family | src/operations/execution/firmware/aggregate_upgrade_service.py | main | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 773 | route and device_family fields |
| R-27 | Child records store each planned device | src/operations/execution/firmware/aggregate_upgrade_service.py | main | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 787 | _target_record method |
| R-28 | Durable record stores site identifiers and names | src/operations/execution/firmware/aggregate_upgrade_service.py | main | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 202 | site_ids and site_names keys |
| R-29 | The stable choice replaces the typed version in the request body | src/operations/execution/firmware/upgrade_service.py | main | 24825d192e4988ce408b92e9a3be6f5fb10b6d90 | present | 925 | version assignment |
| R-30 | The canary phase list is written for the canary strategy | src/operations/execution/firmware/upgrade_service.py | main | 24825d192e4988ce408b92e9a3be6f5fb10b6d90 | present | 810 | canary_phases key |
| R-31 | The failure limit percentage is written for each strategy above big_bang | src/operations/execution/firmware/upgrade_service.py | main | 24825d192e4988ce408b92e9a3be6f5fb10b6d90 | present | 813 | max_failure_percentage key |
| R-32 | The advanced summary lists only values that child bodies send | src/interfaces/portals/upgrade_portal/upgrade/org_advanced_options.py | main | fab86177b1c617f028ae39f338db195946b8203b | present | 244 | lines method |
| R-33 | The schedule builder names the start time | src/interfaces/portals/upgrade_portal/upgrade/org_child_controls.py | main | 3679f08f96abac99607d2e78ee6f1bbc7ac31062 | present | 32 | class OrgScheduleView |
| R-34 | The pre-check state reports whether each site holds a capture | src/interfaces/portals/upgrade_portal/upgrade/org_precheck.py | main | 32af6518834dd467ffbb65fd0e059091a7054392 | present | 54 | ready property |
| R-35 | The save refuses a site with no planned device | src/interfaces/portals/upgrade_portal/upgrade/org_site_records.py | main | be7954035bd921c214dc69307d6ad916cadf0c2d | present | 189 | unplanned site rule |
| R-36 | Progress page device rows are built by OrgDeviceRows | src/interfaces/portals/upgrade_portal/upgrade/org_devices.py | main | 7aadf3e2b2091b6e145dd27fbce027c6efd7801e | present | 294 | class OrgDeviceRows |
| R-37 | The journey test carries a strict expected failure for issue 3222 | tests/e2e/upgrade_portal/journeys/test_upj_multisite_journeys.py | main | c63af9fad1ff6ba3def9a8f6165edeef1737c5a9 | present | 415 | xfail marker |
| R-38 | The parity pair test carries a strict expected failure for issue 3222 | tests/e2e/upgrade_portal/journeys/test_parity_pages.py | main | afd90f6c0e22cdc9d385d3c8f7db6ae8561cbf27 | present | 122 | xfail marker |
| R-39 | Parity matrix row C25 names issue 3222 | tests/e2e/upgrade_portal/journeys/parity_matrix.json | main | 8d67df755c596c5b56925c8ecac688f357ebbd60 | present | 1097 | issue field |
| R-40 | The contract fixture builds the organization upgrade client | tests/contract/upgrade_portal/test_org_upgrade_routes.py | main | d026c23ca2c0abe647fc8106bea5ce8a88442bcf | present | 470 | org_upgrade_client fixture |
| R-41 | Contract tests reach the confirmation page | tests/contract/upgrade_portal/test_org_upgrade_routes.py | main | d026c23ca2c0abe647fc8106bea5ce8a88442bcf | present | 537 | test_valid_options_reach_the_confirmation_page |
| R-42 | The browser flow reaches the confirmation page and types CONFIRM | tests/e2e/upgrade_portal/test_org_upgrade_flow.py | main | bdfa090c1542807897afb2c2dfb7fe9ba128de2f | present | 99 | test_multisite_options_confirmation_progress_and_cancel |
| R-43 | The wording helper renders org_confirm.html with strict undefined | tests/contract/upgrade_portal/test_issue_3390_confirm_strategy_wording.py | main | 590722103b4da465990d699a28349d7d87b0c3c3 | present | 34 | template name in the render helper |
| R-44 | The scope text contract pins the warning and the pre-check text | tests/contract/upgrade_portal/test_issue_3452_confirm_scope_text.py | main | 70d0756833dfad21a030274203095290fde978ae | present | 44 | WARNING_ID constant |
| R-45 | The empty-site browser test reads the confirm summary | tests/e2e/upgrade_portal/test_org_empty_site.py | main | 6ab78ecaba0e8379212d2e4f9624850c3b84e587 | present | 125 | confirm card locator |
| R-46 | The unit module for org child controls exists | tests/unit/upgrade_portal/test_org_child_controls.py | main | 576e87c077000e10d22a32ba7fe6d148f1097868 | present | 0 | module exists |
| R-47 | The single-site unit module renders the single-site template | tests/unit/upgrade_portal/test_confirm_warning.py | main | b07230b5cd5de3f814593ad6495724e41c13d787 | present | 44 | _TEMPLATE_NAME is upgrade/confirm.html |
| R-48 | The parity structure test reads both matrix files | tests/contract/upgrade_portal/test_journey_parity_matrix.py | main | 66adc8c7004ac98c103c053ae539163960f2ece7 | present | 0 | module reads JSON and Markdown |
| R-49 | The portal document has the confirm section | documentation/upgrade_capture_portal.md | main | 97fc51f98df43dff874b22330efb274e625054a8 | present | 339 | heading Confirm and start the upgrade |
| R-50 | The changelog rule names the issue fragment form | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 | issue-<number>-<slug>.md row |
| R-51 | Principle I forbids a new direct child in a noncompliant parent | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 42 | Five-Item Rule text |
| R-52 | AGENTS requires a specification for three or more files | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 348 | Specifications section |
| R-53 | The repository instructions name the changelog fragment rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 | changelog paragraph |
| R-54 | CI names the mypy paths | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 | MYPY_PATHS value |
| R-55 | The site list read runs inside the confirm path | src/interfaces/portals/upgrade_portal/app/routes/select.py | main | 604f8a5e1b6f72b6df860cf1ae03d0ffbc01055c | present | 1060 | listOrgSites read in build_site_rows at line 1044 |
| R-56 | The SDK defines upgradeOrgDevices | .venv/Lib/site-packages/mistapi/api/v1/orgs/devices.py | local | 90fe126e9c3e34d7784644016e12833b7359737d | present | 840 | def upgradeOrgDevices |
| R-57 | The SDK defines upgradeSiteDevices and upgradeDevice | .venv/Lib/site-packages/mistapi/api/v1/sites/devices.py | local | fd3faa0988e688c1cac4e21f22ebe22693f77409 | present | 1230 | def upgradeSiteDevices, and def upgradeDevice at line 3433 |
| R-58 | The SDK defines upgradeOrgSsrs | .venv/Lib/site-packages/mistapi/api/v1/orgs/ssr.py | local | aaddfbb833275a87b63105cd3e40d4c82fdc03fb | present | 114 | def upgradeOrgSsrs |
| R-59 | The organization service imports the SDK organization devices module | src/operations/execution/firmware/org_upgrade_service.py | main | d2a2605394bfb8d2dc0699ad7b1cf6e5745a3dcf | present | 25 | import of devices as org_devices |
| R-60 | The OpenAPI file defines operation upgradeOrgDevices | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9260 | operationId upgradeOrgDevices |
| R-61 | The OpenAPI organization upgrade body accepts canary phases | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 115961 | canary_phases in schema upgrade_org_devices |
| R-62 | Flask selects Jinja autoescape for html templates by default | .venv/Lib/site-packages/flask/sansio/app.py | local | 58cb87306293c40ad3f6f4082ec7beb74e3885d1 | present | 536 | def select_jinja_autoescape |
| R-63 | The pre-check table renders each site name | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_confirm.html | main | bb388fd2845aa235c5d802fe58bbd7e981f10015 | present | 135 | site name cell in the pre-check table |
| R-64 | The template renders the start time line | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_confirm.html | main | bb388fd2845aa235c5d802fe58bbd7e981f10015 | present | 82 | org-upgrade-start-line |
| R-65 | The template renders the reboot line | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_confirm.html | main | bb388fd2845aa235c5d802fe58bbd7e981f10015 | present | 58 | org-upgrade-reboot-at |
| R-66 | The template renders the advanced summary block | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_confirm.html | main | bb388fd2845aa235c5d802fe58bbd7e981f10015 | present | 68 | org-upgrade-advanced-summary |
| R-67 | AGENTS forbids the auto-merge label on a destructive-operation change without human review | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 230 | auto-merge rule |
| R-68 | The module org_child_controls.py defines six top-level names | src/interfaces/portals/upgrade_portal/upgrade/org_child_controls.py | main | 3679f08f96abac99607d2e78ee6f1bbc7ac31062 | present | 22 | names at lines 22, 24, 25, 26, 32, and 78 |
| R-69 | The folder upgrade/ holds at least 14 direct entries | src/interfaces/portals/upgrade_portal/upgrade/ | main | directory listing | present | 0 | org_advanced_options, org_cancel_outcomes, org_cancel_text, org_cascade, org_child_controls, org_devices, org_history, org_postcheck, org_postcheck_view, org_precheck, org_reconcile, org_retry, org_site_records, and org_versions |
| R-70 | The folder tests/unit/upgrade_portal holds more than five direct files | tests/unit/upgrade_portal/ | main | directory listing | present | 0 | for example test_confirm_warning.py, test_org_advanced_summary.py, test_org_child_controls.py, and test_org_devices.py |
| R-71 | The folders tests/contract/upgrade_portal and tests/e2e/upgrade_portal hold more than five direct files | tests/contract/upgrade_portal/ and tests/e2e/upgrade_portal/ | main | directory listing | present | 0 | for example test_org_upgrade_routes.py and test_org_upgrade_flow.py |
| R-72 | The worktree bootstrap script exists | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 0 | file exists |
| R-73 | The STE linter configuration exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 | file exists |
| R-74 | The test quality configuration exists | .github/test-quality-config.toml | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 0 | file exists |
| R-75 | The test quality baseline exists | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 0 | file exists |
| R-76 | The Markdown parity matrix exists | specs/3200-upgrade-portal-journeys/parity-matrix.md | main | edaf47f7f042c4085342e7640540565bb9ca3032 | present | 0 | file exists |
| R-77 | The later site checks test module exists | tests/contract/upgrade_portal/test_issue_3439_later_site_checks.py | main | d3214a9a4b6b9c7636633f081c3130c16f5f3475 | present | 0 | file exists |

Counts: 77 rows. Present 65. Absent 12. Partial 0. Stale 0. The local rows are R-56, R-57, R-58, and R-62.

## 10. Sources

- **Local paths and lines**: every line in section 9 cites a file in the working tree that matches its blob. Additional local lines used in the text are these.
  - `org_upgrade.py` line 146 (`CONFIRM_PAGE_PATH`), line 153 (`CONFIRM_TEMPLATE`), and line 191 (`CONFIRMATION_REQUIRED`).
  - `org_upgrade.py` line 192 (`CONFIRMATION_MESSAGE`), line 921 (`FAMILY_LABELS`), and line 923 (`STABLE_BUILD_TEXT`).
  - `org_upgrade.py` line 1338 (`@identity.require_session`) and line 2714 (`_wants_html`).
- **Local lines in other files**: `aggregate_upgrade_service.py` line 913 (`_send_child`) and line 1847 (`_submit_aggregate` in `org_upgrade.py`). `upgrade_service.py` lines 47 to 49 (route names). `org_upgrade_service.py` line 34 (`OrgUpgradeSession`), whose docstring names mistapi 0.63.3.
- **GitHub reads**: the following read-only commands ran.
  - `gh issue view 3222` read the body and the comments.
  - `gh pr list` and `gh pr view` read the pull requests in section 3.
  - `gh api` read the tree, the contents, the commits, the branches, and the compare view.
  - `gh label list` read the labels.
- **Installed packages**: `.venv\Lib\site-packages\mistapi-0.64.1.dist-info` gives the installed version. The pin in `.github/copilot-instructions.md` allows that version.
- **Web sources**: none. No URL was fetched.

## 11. Unverified

These items stay unverified. Each reason is stated.

- **U-1**: The runtime outcome of the two strict expected failures on `main`. The tests were not run (brief rule 2).
- **U-2**: The values of `version_before` for live devices. No live read was made (no live Mist call under rule 2).
- **U-3**: The ste-linter score of each Markdown file. The linter was not run (brief rule 2). The prose follows the STE rules by manual review.
- **U-4**: The rendered HTML for attribute values under autoescape. No page was rendered. The result follows from the Flask default (R-62).
- **U-5**: The CI result of the merged pull requests #4547 and #4701. Only the merge states were read.
- **U-6**: The duration and the result of the full test shards. The shards were not run (brief rule 2).

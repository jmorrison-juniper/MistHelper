# Research: Multi-Site Save and the Empty Target Version (Issue 3394)

Measured on 2026-11-26. Remote facts come from the GitHub API for `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Local reads match `main` for each file that this record cites. Local blob SHAs equal the remote blob SHAs. The local `git hash-object` check did not write to the repository.

## 1. Linked Work

| Item | State on 2026-11-26 | Relevance |
| - | - | - |
| Issue #3394 | Open. Labels `bug`, `web-portal`, `upgrade-portal`, `priority:P1`, `severity:high`, `needs-human-review`. | The subject of this record. |
| PR #4005 | Closed without merge on 2026-10-06. Head branch `jmorrison-juniper-fix-3394-multi-site-empty-version` is absent [RC13]. Head commit `f8edcb4ff03e4db2be8777d1130ff46e68b6d9f7` resolves [RC14]. | Earlier attempt. Analysis item A4. |
| PR #4413 (issue #3393) | Merged on 2026-10-28. Changes `org_upgrade.py`. | Related change in the same save path. |
| PR #4701 | Merged on 2026-11-13. Changes `org_upgrade.py` and the contract test file. | Earlier comment that calls it a draft is stale. |
| PR #4547 (issue #3396) | Merged on 2026-11-13. Changes `org_upgrade.py`. | Earlier comment that calls it a draft is stale. |
| PR #4606 (issue #4540) | Merged on 2026-11-09. Changes `portal.js`. | Changes the browser script. |
| PR #4541 (issue #3200) | Merged on 2026-11-05. Changes the contract test file. | Changes the contract test file. |
| PR #3426 (issue #3389) | Merged on 2026-09-26 under the retired folder `upgrade_portal/`, which no longer exists on `main`. | Earlier multi-site save change. |
| PR #3075 | Merged on 2026-09-20 under the retired folder `upgrade_portal/`, which no longer exists on `main`. | Historical move. |
| PRs #3996 and #3997 | Merged on 2026-10-06. Neither touches a shared path. | The earlier comment that calls them open is stale. |

Open pull requests on 2026-11-26: #4890, #4889, #4888, #4887, #4886, #4813 (draft), and #4208 (draft). Their file counts are 1, 1, 1, 2, 1, 15, and 82. None touches the seven shared paths: `org_upgrade.py`, the contract test module, `options.py`, `org_options.html`, `portal.js`, the e2e flow module, and the changelog fragment. The dependency bumps #427, #952, and #537 matched the search text "3394". They are not linked to this issue.

Related issues on 2026-11-26: #3389 closed on 2026-09-26. #3393 is open. #3396 closed on 2026-11-13. #3326 and #3329 closed on 2026-10-23. #3204 closed on 2026-10-02. #3200 closed on 2026-11-05. #4540 closed on 2026-11-09. No open issue must land before this change.

## 2. Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk. No decision needs a human marker. The decisions cover technical scope and process only.

### D-1 Enforcement boundary

- **Decision**: Refuse the save on the server. Change no template and no JavaScript file.
- **Alternatives**: A client-side check in `portal.js` [RC40 to RC44]. A `required` attribute on each target version control [RC47, RC49].
- **Rationale**: The server decides which rows reach the plan [RC30]. A client check can be bypassed. A `required` attribute cannot state a rule for each device type. The page already offers a valid "Do not upgrade this device" choice [RC48].
- **Risk**: The operator sees the refusal after a server round trip. The flash message and kept values reduce that cost [RC41, RC44].

### D-2 Scope of the rule

- **Decision**: Apply the rule to each selected site and to each checked device type that has devices at that site.
- **Alternatives**: Apply the rule to the whole plan. Require a target for every device.
- **Rationale**: The existing guard works per site [RC37, RC38]. A plan-wide rule lets one site drop a type silently. A per-device rule removes the per-device choice that the page offers [RC48].
- **Risk**: An operator who sets every device of one type to "Do not upgrade this device" at one site is refused. The operator must clear that type box for the plan.

### D-3 Checked device type with no device

- **Decision**: Do not refuse a checked device type that has no device at any selected site.
- **Alternatives**: Refuse every checked type that has no target.
- **Rationale**: No device drops in that case. The issue defines the failure as a dropped device. The confirmation page lists one group for each planned child [RC95].
- **Risk**: An operator may expect an upgrade for that type. The plan then shows no group for it.

### D-4 Response shape

- **Decision**: Return HTTP 400 with code `org_upgrade_options_invalid` through the existing `ValueError` path.
- **Alternatives**: A new error code. A `BadOptionError` that the route translates.
- **Rationale**: The save route already maps `ValueError` to that status and code [RC27, RC28, RC17]. The envelope builder fixes the shape [RC39]. The browser shows the envelope message [RC40, RC41]. A translated `BadOptionError` returns the table label, not the device type [RC19].
- **Risk**: The generic clause returns the text of any `ValueError` to the operator. The new text is plain, so the risk is small.

### D-5 Message text

- **Decision**: Use "Choose the {noun} target version, or clear {label}." The pairs are access point and Access points, switch and Switches, and gateway and Gateways [RC46]. The text names no site.
- **Alternatives**: The word "Type", as in the issue example. A site name in the text.
- **Rationale**: The target version control is a list, so "Choose" fits [RC47, RC48]. The labels match the page exactly. A site name adds a lookup and a longer message. The issue does not ask for it.
- **Risk**: The operator must find the site on the page. This risk is accepted (R2 in the plan).

### D-6 Placement

- **Decision**: Add a static method to the existing class `OrgOptionRefusal`. Call it from `_selected_target_rows`.
- **Alternatives**: A new module under `upgrade/`. An extension of `OrgSiteRecords`.
- **Rationale**: The `upgrade` package already holds 22 children [RC82]. A new module would add a child to a noncompliant parent, and the constitution forbids that [RC59]. `OrgSiteRecords` holds no device type and no selected type. `OrgOptionRefusal` already names the multi-site controls in each option refusal [RC18].
- **Risk**: The module keeps its size. The debt is recorded in analysis item A12.

### D-7 Retry plan

- **Decision**: Apply the same rule to the narrowed view of a retry plan.
- **Alternatives**: Skip the rule for a retry plan.
- **Rationale**: A retry narrows the view to failed devices [RC100, RC96]. The same function receives the narrowed view [RC20]. A silent drop in a retry is equally harmful.
- **Risk**: A retry in which the operator clears a whole type loses that type. The result matches D-3.

### D-8 Test boundary

- **Decision**: Replace the xfail test [RC51, RC52]. Add five contract tests and one browser test. Tasks T001 to T007 hold the cases.
- **Alternatives**: Keep the xfail test. Delete the xfail test.
- **Rationale**: The xfail test expects the unsafe result (analysis item A6). A deletion would lose the switch case. A replacement keeps the case with the correct result.
- **Risk**: The rename triggers a symbol report (task T010). The pull request explains the rename.

### D-9 Branch

- **Decision**: Start the branch `fix/3394-multi-site-empty-version` from `main`. Do not revive the PR 4005 branch.
- **Alternatives**: Rebase commit `f8edcb4`. Reuse the PR 4005 patch.
- **Rationale**: The PR 4005 branch is absent [RC13]. The commit still resolves [RC14], but its design differs (analysis item A4). The repository rules require a branch from `main` [RC88].
- **Risk**: None significant. The old commit remains in the history.

### D-10 Changelog fragment name

- **Decision**: Use `changelog.d/issue-3394-multi-site-empty-version.md`.
- **Alternatives**: A date and slug name.
- **Rationale**: The issue exists and no pull request exists. The README gives the issue form for that case [RC57]. The name is free [RC11].
- **Risk**: The name changes when the pull request opens. The README rule covers that case.

### D-11 Documentation

- **Decision**: Make no change to the README or to the operator guide.
- **Alternatives**: Add a README note about the refusal.
- **Rationale**: The README has no text about the multi-site page or the target version [RC78]. A note would document an area that the README does not cover. The constitution asks for a README update for each behavior change [RC62]. The plan records the reason in its Constitution Check.
- **Risk**: A reviewer may ask for a README note. This decision answers that request.

### D-12 Review gate

- **Decision**: Keep the `needs-human-review` label. Add the `auto-merge` label only after a human approves the change and the orchestrator authorizes the merge.
- **Alternatives**: Enable auto-merge after the checks pass.
- **Rationale**: The issue requires a human review before implementation and before merge. The change touches the firmware save path.
- **Risk**: The merge waits for the human review.

## 3. Remote Verification

The table holds 105 checks. Each row matches one row of the `remote_checks` array in `3394-STATUS.json`. The `result` column uses `present`, `absent`, `partial`, or `stale`. Rows RC79 and RC80 use the local worktree because the third-party package is not in the repository tree.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC01 | Issue body cause path exists on main | retired upgrade_portal/app/routes/org_upgrade.py | main | none | absent | 0 |
| RC02 | Save handler file exists and defines save_options | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1215 |
| RC03 | Issue body line near 510 for _selected_target_rows is stale | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | stale | 775 |
| RC04 | Issue comment line 755 for _selected_target_rows is stale | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | stale | 775 |
| RC05 | Issue comment lines 1204-1219 for the save handler are stale | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | stale | 1215 |
| RC06 | Issue comment line 648 for _aggregate_option_record is stale | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | stale | 634 |
| RC07 | Issue comment lines 3311-3330 for the browser target list are stale | src/interfaces/portals/upgrade_portal/app/assets/static/js/portal.js | main | 03ed368d398f4074894ee041de6900ac7fbd8b4c | stale | 3332 |
| RC08 | Route folder for issue 3394 exists | specs/numbered/0/0/1/0/2/0/3/4 | main | none | absent | 0 |
| RC09 | Any path on main contains 3394 | tree search for 3394 | main | none | absent | 0 |
| RC10 | Route parent holds one child folder | specs/numbered/0/0/1/0/2/0/3 | main | none (directory listing) | present | 0 |
| RC11 | Changelog fragment for issue 3394 is free | changelog.d/issue-3394-multi-site-empty-version.md | main | none | absent | 0 |
| RC12 | Branch fix/3394-multi-site-empty-version is free | refs/heads/fix/3394-multi-site-empty-version | main | none | absent | 0 |
| RC13 | Head branch of PR 4005 exists (its closing comment says the head commit stays preserved) | refs/heads/jmorrison-juniper-fix-3394-multi-site-empty-version | main | none | absent | 0 |
| RC14 | PR 4005 head commit resolves | commits/f8edcb4ff03e4db2be8777d1130ff46e68b6d9f7 | main | f8edcb4ff03e4db2be8777d1130ff46e68b6d9f7 | present | 0 |
| RC15 | Main head commit resolves | commits/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC16 | OPTIONS_API_PATH names the save route | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 145 |
| RC17 | OPTIONS_INVALID names the refusal code | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 184 |
| RC18 | OrgOptionRefusal groups the option refusal helpers | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 342 |
| RC19 | page_field maps a version refusal to the targets label | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 386 |
| RC20 | _site_option_record calls _selected_target_rows | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 760 |
| RC21 | _selected_target_rows definition | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 775 |
| RC22 | Explicit path builds the version map from the request | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 783 |
| RC23 | Legacy fallback keeps a device only when its type field is non-empty | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 791 |
| RC24 | _explicit_target_versions keeps only non-empty targets | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 800 |
| RC25 | _site_explicit_target_rows keeps only addresses in the version map | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 817 |
| RC26 | _complete_aggregate_options refuses only when no target exists | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 703 |
| RC27 | save_options maps BadOptionError to status 400 | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1226 |
| RC28 | save_options maps other ValueError to status 400 with its text | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1231 |
| RC29 | save_options writes browser session state after success | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1232 |
| RC30 | _write_operation writes the durable plan | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1015 |
| RC31 | aggregate_options_view reads the cached organization inventory in production | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 429 |
| RC32 | ORG_OPTION_HELP labels the targets control Device target versions | src/interfaces/portals/upgrade_portal/upgrade/options.py | main | 6a1446c99a1f03b6c2110df3030bd860c3c9ca3a | present | 268 |
| RC33 | Row builder selects the safe target when no selected version exists | src/interfaces/portals/upgrade_portal/upgrade/options.py | main | 6a1446c99a1f03b6c2110df3030bd860c3c9ca3a | present | 864 |
| RC34 | _resolve_choice refuses an empty version | src/interfaces/portals/upgrade_portal/upgrade/options.py | main | 6a1446c99a1f03b6c2110df3030bd860c3c9ca3a | present | 1871 |
| RC35 | build_options_record documents the empty version refusal | src/interfaces/portals/upgrade_portal/upgrade/options.py | main | 6a1446c99a1f03b6c2110df3030bd860c3c9ca3a | present | 2086 |
| RC36 | read_upgrade_inventory calls getOrgInventory | src/interfaces/portals/upgrade_portal/upgrade/options.py | main | 6a1446c99a1f03b6c2110df3030bd860c3c9ca3a | present | 727 |
| RC37 | OrgSiteRecords add counts a site with no planned device | src/interfaces/portals/upgrade_portal/upgrade/org_site_records.py | main | be7954035bd921c214dc69307d6ad916cadf0c2d | present | 155 |
| RC38 | OrgSiteRecords refusal names unplanned sites | src/interfaces/portals/upgrade_portal/upgrade/org_site_records.py | main | be7954035bd921c214dc69307d6ad916cadf0c2d | present | 161 |
| RC39 | json_error builds the one JSON error shape | src/interfaces/portals/upgrade_portal/app/factory.py | main | 5729127f3b4a0d25f45a33e8ef79a4e460d8be92 | present | 322 |
| RC40 | buildRequestError copies the envelope message | src/interfaces/portals/upgrade_portal/app/assets/static/js/portal.js | main | 03ed368d398f4074894ee041de6900ac7fbd8b4c | present | 348 |
| RC41 | showRequestError shows the error message in the page | src/interfaces/portals/upgrade_portal/app/assets/static/js/portal.js | main | 03ed368d398f4074894ee041de6900ac7fbd8b4c | present | 504 |
| RC42 | updateOrgOptionsVisibility disables selects of cleared device types | src/interfaces/portals/upgrade_portal/app/assets/static/js/portal.js | main | 03ed368d398f4074894ee041de6900ac7fbd8b4c | present | 3297 |
| RC43 | orgFormBody sends only enabled non-empty target choices | src/interfaces/portals/upgrade_portal/app/assets/static/js/portal.js | main | 03ed368d398f4074894ee041de6900ac7fbd8b4c | present | 3332 |
| RC44 | sendOrgForm reopens the form and shows the refusal | src/interfaces/portals/upgrade_portal/app/assets/static/js/portal.js | main | 03ed368d398f4074894ee041de6900ac7fbd8b4c | present | 3482 |
| RC45 | Template form posts to the options API | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_options.html | main | 2675897ed0a835538b084673b8c1f628dbaff612 | present | 91 |
| RC46 | Template labels the device types | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_options.html | main | 2675897ed0a835538b084673b8c1f628dbaff612 | present | 98 |
| RC47 | Template target version select has no name attribute | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_options.html | main | 2675897ed0a835538b084673b8c1f628dbaff612 | present | 608 |
| RC48 | Template offers Do not upgrade this device as the first choice | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_options.html | main | 2675897ed0a835538b084673b8c1f628dbaff612 | present | 613 |
| RC49 | Template has no required marker on the device table | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_options.html | main | 2675897ed0a835538b084673b8c1f628dbaff612 | present | 243 |
| RC50 | Multi-site selection routes to the options page | src/interfaces/portals/upgrade_portal/app/routes/select.py | main | 604f8a5e1b6f72b6df860cf1ae03d0ffbc01055c | present | 127 |
| RC51 | Contract test marks the checked switch case as xfail | tests/contract/upgrade_portal/test_org_upgrade_routes.py | main | d026c23ca2c0abe647fc8106bea5ce8a88442bcf | present | 65 |
| RC52 | Contract test expects the switch in the stored plan | tests/contract/upgrade_portal/test_org_upgrade_routes.py | main | d026c23ca2c0abe647fc8106bea5ce8a88442bcf | present | 98 |
| RC53 | Existing unit test covers _selected_target_rows | tests/contract/upgrade_portal/test_org_upgrade_routes.py | main | d026c23ca2c0abe647fc8106bea5ce8a88442bcf | present | 47 |
| RC54 | org_upgrade_client fixture is defined | tests/contract/upgrade_portal/test_org_upgrade_routes.py | main | d026c23ca2c0abe647fc8106bea5ce8a88442bcf | present | 470 |
| RC55 | Browser test pattern exists in the e2e flow file | tests/e2e/upgrade_portal/test_org_upgrade_flow.py | main | bdfa090c1542807897afb2c2dfb7fe9ba128de2f | present | 50 |
| RC56 | Changelog policy guard test exists | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| RC57 | Changelog README gives the issue-number file rule | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| RC58 | Changelog README requires one heading and one bullet for each type | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 37 |
| RC59 | Constitution defines the Five-Item Rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC60 | Constitution requires inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| RC61 | Constitution requires action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| RC62 | Constitution requires a README update for each behavior change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 400 |
| RC63 | Constitution requires SpecKit escalation for three or more files | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 420 |
| RC64 | copilot-instructions Tests row names the changed test file | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| RC65 | copilot-instructions Symbols row names symbol-diff | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 73 |
| RC66 | copilot-instructions defines the pull request title rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 501 |
| RC67 | AGENTS defines the writing style | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| RC68 | AGENTS defines inline comments | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 97 |
| RC69 | AGENTS defines action logging | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 104 |
| RC70 | spec-route defines Get-SpecRadixSegments | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 4 |
| RC71 | spec-route uses base 5 for numeric routes | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC72 | Reference record spec.md exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC73 | Reference record design/research.md exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/research.md | main | 2e4aaa714e56fff7f96a2af9e686e9f5c06224a7 | present | 0 |
| RC74 | Reference record design/checklists/requirements.md exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/checklists/requirements.md | main | 4a53b89939bb523902efeaaffd1d7b12221c717b | present | 0 |
| RC75 | MIST API GET table lists getOrgInventory | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 607 |
| RC76 | MIST API missing list does not name getOrgInventory | documentation/MIST_API_MISSING_ENDPOINTS.md | main | e4949ef2ab2ed1d86e6309bd919401d65b2c0ae0 | absent | 0 |
| RC77 | OpenAPI defines the inventory path | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 10639 |
| RC78 | README has no multi-site or target version text | README.md | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | absent | 0 |
| RC79 | Installed mistapi version is 0.64.1 inside the pin | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | local-worktree | not-applicable-local | present | 3 |
| RC80 | Installed mistapi defines getOrgInventory | .venv\Lib\site-packages\mistapi\api\v1\orgs\inventory.py | local-worktree | not-applicable-local | present | 17 |
| RC81 | org_upgrade.py defines 147 top-level functions and classes, far above the five-item limit | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 187 |
| RC82 | upgrade package holds 22 children, above the five-item limit | src/interfaces/portals/upgrade_portal/upgrade | main | none (directory listing) | present | 0 |
| RC83 | Constitution Principle II Class-Based Architecture is present | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 91 |
| RC84 | Constitution Principle V Observability and Logging is present | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 182 |
| RC85 | Constitution defines Branch Naming for MistHelper | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 476 |
| RC86 | Constitution defines Required Labels | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 487 |
| RC87 | copilot-instructions states the Python 3.15 requirement | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 20 |
| RC88 | AGENTS defines the branch rule that starts from main | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 197 |
| RC89 | AGENTS defines the pull request rules | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 221 |
| RC90 | AGENTS defines the tests rules | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 133 |
| RC91 | AGENTS defines the secrets rule | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 172 |
| RC92 | Browser test module imports Playwright through pytest importorskip | tests/e2e/upgrade_portal/test_org_upgrade_flow.py | main | bdfa090c1542807897afb2c2dfb7fe9ba128de2f | present | 14 |
| RC93 | Constitution Principle IV Full Deployment Pipeline is present | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| RC94 | Constitution Principle III Safety-First is present | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 113 |
| RC95 | Confirmation template names each planned child group by its device family | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_confirm.html | main | bb388fd2845aa235c5d802fe58bbd7e981f10015 | present | 30 |
| RC96 | narrowed_view is defined for the device view of a retry | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 880 |
| RC97 | options_page renders the multi-site options template | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1139 |
| RC98 | Browser test class holds the organization flow tests | tests/e2e/upgrade_portal/test_org_upgrade_flow.py | main | bdfa090c1542807897afb2c2dfb7fe9ba128de2f | present | 47 |
| RC99 | refused_message helper asserts status 400 for a refused body | tests/contract/upgrade_portal/test_org_upgrade_routes.py | main | d026c23ca2c0abe647fc8106bea5ce8a88442bcf | present | 836 |
| RC100 | Retry view is narrowed before target rows are selected | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 759 |
| RC101 | Contract test defines the confirmation path constant | tests/contract/upgrade_portal/test_org_upgrade_routes.py | main | d026c23ca2c0abe647fc8106bea5ce8a88442bcf | present | 34 |
| RC102 | Contract test reads the error code from the response envelope | tests/contract/upgrade_portal/test_org_upgrade_routes.py | main | d026c23ca2c0abe647fc8106bea5ce8a88442bcf | present | 841 |
| RC103 | Contract test reads the error message from the response envelope | tests/contract/upgrade_portal/test_org_upgrade_routes.py | main | d026c23ca2c0abe647fc8106bea5ce8a88442bcf | present | 842 |
| RC104 | Save route answers the confirmation path after a valid save | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1235 |
| RC105 | Contract helper asserts the next page answer for a valid save | tests/contract/upgrade_portal/test_org_upgrade_routes.py | main | d026c23ca2c0abe647fc8106bea5ce8a88442bcf | present | 520 |

Counts: 105 rows. Present 92. Absent 8. Stale 5. Every row carries an ID that matches the STATUS file.

Method notes:

- The tree call listed 11,404 entries with `truncated` set to false. The filter matched the claimed paths.
- Each file body came from the GitHub contents API. The base64 text decoded in memory. A search of the decoded lines gave each line number.
- Row RC09 is a negative search over the tree. The search pattern is the number 3394. It matched no path.
- Rows RC13 and RC12 returned HTTP 404 for the branch name. Row RC11 returned HTTP 404 for the fragment name.
- Row RC76 and row RC78 are negative text searches over the cited documents. No match appeared.
- A remote call that returned the HTTP 403 or 429 status would have triggered the retry rule. No such response appeared.

## 4. Local Sources

- The local worktree blobs equal the main blobs for these files: `org_upgrade.py` (11c839db), `select.py` (604f8a5e), `options.py` (6a1446c9), and `org_options.html` (2675897e). The remaining files also equal the main blobs: `portal.js` (03ed368d), `test_org_upgrade_routes.py` (d026c23c), `tests/e2e/conftest.py` (e450e185), and the OpenAPI file (b7fc2bfb).
- The local retired `upgrade_portal/` folder holds only untracked `__pycache__` files. A read-only `git ls-files` check returned zero tracked files.
- The reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv` has these children: `analysis.md`, `plan.md`, `spec.md`, `tasks.md`, and `design/`. The `design/` folder holds `checklists/`, `contracts/`, `data-model.md`, `quickstart.md`, and `research.md`. This record copies that depth and that shape. No content is copied [RC72, RC73, RC74].
- The OpenAPI file defines the inventory path at line 10639 [RC77]. The local mistapi package defines `getOrgInventory` at line 17 [RC80]. The installed version is 0.64.1 [RC79].

## 5. Sources and Links

- Issue: https://github.com/jmorrison-juniper/MistHelper/issues/3394
- Closed attempt: https://github.com/jmorrison-juniper/MistHelper/pull/4005
- Related merged changes: https://github.com/jmorrison-juniper/MistHelper/pull/4413, https://github.com/jmorrison-juniper/MistHelper/pull/4547, https://github.com/jmorrison-juniper/MistHelper/pull/4701, https://github.com/jmorrison-juniper/MistHelper/pull/3426
- Commit of the closed attempt: https://github.com/jmorrison-juniper/MistHelper/commit/f8edcb4ff03e4db2be8777d1130ff46e68b6d9f7

The `web_fetch` tool was not used. Every remote fact came from the GitHub API or a local file.

## 6. Skills

No skill was loaded. The issue concerns portal validation code and tests. It does not concern containers, Podman, or Juniper device behavior.

## 7. Unverified

- **U1. Browser seed mapping.** The browser test uses the constants `SITE_ID` and the seeded switch addresses at `tests/e2e/upgrade_portal/test_org_upgrade_flow.py:17` and `:25-28`. The seed definitions in `tests/e2e/upgrade_portal/conftest.py` were not read in this phase. Reason: the file was outside the verified set. The implementer must check the mapping before task T007.
- **U2. Browser display.** The flash message and the kept form values follow from the code paths in RC40, RC41, and RC44. No browser run occurred. Reason: rule 2 forbids running a test during authoring.
- **U3. Test outcomes.** Each expected pass and fail in the task list is a prediction. Reason: rule 2 forbids running a test during authoring.
- **U4. Live Mist behavior.** The record does not prove what `getOrgInventory` returns for a live site. Reason: no live Mist call is allowed in this phase. The source line is verified (RC80).
- **U5. Continuous integration.** The Playwright and Chromium steps in the remote workflow were not inspected. Reason: the workflow files are outside the verified set.

## 8. Tool Notes

- The session database held a table named `remote_checks` with 105 rows for other issues. Those rows are not evidence for issue 3394. They were left unchanged. This record stores its 105 checks in its own table.
- No file was written under the repository. Only the draft folder and the meta folder received output.

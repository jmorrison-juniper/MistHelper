# Research: Persist resumable firmware phase state

## R1. Scope and method

- **Truth order**: Remote `main` outranks local files. Every code, test, configuration, and document claim cites an RC row below.
- **Local match**: Local `HEAD` is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Remote `main` is the same commit. Nineteen source and test files have the same git blob hash locally and remotely.
- **Remote bodies**: Each line number comes from a decoded remote body (`gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main`). The OpenAPI file is 4.3 MB. The contents API omits bodies above 1 MB, so the git blob API read it (`repos/jmorrison-juniper/MistHelper/git/blobs/b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14`).
- **Installed SDK**: The SDK sits under `.venv/Lib/site-packages/mistapi`. Its blob value is the local `git hash-object` result. The SDK is not a repository path.
- **Commits**: A commit counts as present when `gh api repos/jmorrison-juniper/MistHelper/commits/<sha>` returns it and the compare endpoint reports `ahead` against `main`.
- **Rate limits**: No request hit a 403, 429, or rate-limit message.

## R2. Issue facts

- **Issue**: #4022, "feat(upgrade): persist resumable firmware phase state". State: open. Labels: `feature`, `web-portal`, `upgrade-portal`, `database`, `firmware`, `needs-human-review`. Parent: #3332 (closed). Created 2026-10-06. Last updated 2026-11-10.
- **Body**: Child 4 of 4. The body asks for durable resume state for a stopped firmware phase. The body names six files. It requires a specification. It warns that a wrong resume rule can repeat a write or skip a device.
- **Comment 2026-10-07 (read-only assessment)**: Durable phase data already exists. The issue body misstates the state. The durable authorization model and reconciliation rules are missing. The comment gives the conditional repair manifest and seven failure modes.
- **Comment 2026-11-10 (dependency status)**: Issue #4020 decisions are recorded. PR #4109 merged. The comment says that issue #3726 remains open. That statement is outdated (see R3). The comment keeps the resume implementation on hold and requires a managed specification, file handoffs, and human safety review.
- **Owner decision 4 (issue body)**: Resume behavior after a stopped phase. The recommended option is: resume from the stopped phase only after the operator confirms the repair. Never repeat a settled phase. Never skip a phase without a settled result.
- **Issue #4020 (closed 2026-10-12)**: Owner approved three single-site decisions in comment 6031475938. The retry rule is "Do not retry a destructive write automatically. Stop the cascade, persist the failure, and require an explicit operator resume." The comment states that issue #4022 owns the resume semantics.
- **Issue #4021 (open)**: Multi-site sequencing. The 2026-11-10 comment says the complete multi-site gate contract is not established.
- **Issue #3726 (closed 2026-11-13)**: Ambiguous submission replies entered the site-lock release path. Pull request #4701 merged its fix.
- **Issue #3332 (closed)**: Parent. Its evidence cites line numbers that predate PR #4109.

## R3. Linked work

| Item | State | Merged or closed | Commit | Relevance |
| - | - | - | - | - |
| PR #4109 | merged | 2026-10-12 | `acaae1adbd22b3875db850ab4026bb2922491ec6` (RC-095) | Single-site ordered submission (#4020) |
| PR #4075 | merged | 2026-10-07 | `44e509a28cf8150c346ffbd55b3e97ee9ca25c3f` (RC-096) | Documentation boundary for the phase watch |
| PR #4701 | merged | 2026-11-13 | `53ad73cc37dc0821faca093441ecd12268e6a75d` (RC-097) | Site lock keeps the lock after uncertain replies (#3726). Adds `submission_certainty.py` and changes org files. |
| PR #4085 | merged | 2026-10-09 | none recorded here | Route handler cause naming |
| PR #4089 | merged | 2026-10-10 | none recorded here | Fallback failure causes |
| PR #4068 | merged | 2026-10-07 | none recorded here | Export HTTP failure |
| PR #3997 | merged | 2026-10-06 | none recorded here | Org cascade error reporting |
| PR #4005 | closed, not merged | none | none | Flash message regression example (issue body) |

- `gh pr list --search 4022` returned no pull request. The linked pull request count for this issue is zero.
- `gh pr list --state open` returned seven open pull requests. No file in those pull requests appears in the manifest of this change.

## R4. Existing record

- `specs\` on local disk: a glob for `**/4022-*` returned no folder.
- Remote tree: the path filter for `4022` returned no entry (RC-094).
- The route folder `specs/numbered/0/0/1/1/2/0/4/2` is absent on `main` (RC-094).
- Result: no legacy record exists. Steps 3 and 4 of the brief apply to a legacy record, so they do not apply here.

## R5. Remote verification table

The table has 144 rows. Each row is one check. Column `Result` is `present` or `absent`. Column `Line` is the first matching line. A `0` line marks a file, directory, commit, or absence check.

| ID | Claim | Path | Blob SHA | Result | Line |
| - | - | - | - | - | - |
| RC-001 | PHASE_ORDER declares gateways, switches, aps, clients | src/interfaces/portals/upgrade_portal/runtime/runs.py | fe273eb405880ce70f6697becbef042c9429589c | present | 58 |
| RC-002 | PhaseState enum is declared | src/interfaces/portals/upgrade_portal/runtime/runs.py | fe273eb405880ce70f6697becbef042c9429589c | present | 118 |
| RC-003 | PhaseState.FAILED member is "failed" | src/interfaces/portals/upgrade_portal/runtime/runs.py | fe273eb405880ce70f6697becbef042c9429589c | present | 132 |
| RC-004 | RunState.STOPPED member is "stopped" | src/interfaces/portals/upgrade_portal/runtime/runs.py | fe273eb405880ce70f6697becbef042c9429589c | present | 109 |
| RC-005 | initial_phases builds one entry for each phase | src/interfaces/portals/upgrade_portal/runtime/runs.py | fe273eb405880ce70f6697becbef042c9429589c | present | 347 |
| RC-006 | RunStateMachine.TERMINAL includes stopped | src/interfaces/portals/upgrade_portal/runtime/runs.py | fe273eb405880ce70f6697becbef042c9429589c | present | 397 |
| RC-007 | allowed_next returns no move from a final state | src/interfaces/portals/upgrade_portal/runtime/runs.py | fe273eb405880ce70f6697becbef042c9429589c | present | 457 |
| RC-008 | No resuming state and no resume transition exist | src/interfaces/portals/upgrade_portal/runtime/runs.py | fe273eb405880ce70f6697becbef042c9429589c | absent | 0 |
| RC-009 | Stopped message reads "The run stopped." | src/interfaces/portals/upgrade_portal/runtime/runs.py | fe273eb405880ce70f6697becbef042c9429589c | present | 650 |
| RC-010 | PHASE_ENDED_STATES holds settled, skipped, and failed | src/interfaces/portals/upgrade_portal/upgrade/org_cascade/record.py | ce54e6050a102da7ef38549e440bfdf58768f17a | present | 56 |
| RC-011 | Watch loop skips a phase whose state is ended (resume rule) | src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py | 55a3f353ca5c20931533fbe40b8f99c3e225d9ec | present | 245 |
| RC-012 | Watch finish and stop call lock_lease.release() | src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py | 55a3f353ca5c20931533fbe40b8f99c3e225d9ec | present | 175 |
| RC-013 | org_cascade/locks.py has no settlement predicate | src/interfaces/portals/upgrade_portal/upgrade/org_cascade/locks.py | 0fe92b2393d8bc44f6d1e3a50aa91d26e035fd52 | absent | 0 |
| RC-014 | Run finally block frees the site lock | src/interfaces/portals/upgrade_portal/upgrade/driver.py | 0279d399396fed1253d46cf525d65f15ff61a6c1 | present | 1459 |
| RC-015 | _free_lock releases the lock at a final state | src/interfaces/portals/upgrade_portal/upgrade/driver.py | 0279d399396fed1253d46cf525d65f15ff61a6c1 | present | 1518 |
| RC-016 | _final_state accepts every TERMINAL state | src/interfaces/portals/upgrade_portal/upgrade/driver.py | 0279d399396fed1253d46cf525d65f15ff61a6c1 | present | 1567 |
| RC-017 | Cascade loops over PHASE_ORDER | src/interfaces/portals/upgrade_portal/upgrade/driver.py | 0279d399396fed1253d46cf525d65f15ff61a6c1 | present | 1736 |
| RC-018 | Submit call runs before each phase settles | src/interfaces/portals/upgrade_portal/upgrade/driver.py | 0279d399396fed1253d46cf525d65f15ff61a6c1 | present | 1609 |
| RC-019 | Gate returns early on a stop request (lines 1771 to 1773) | src/interfaces/portals/upgrade_portal/upgrade/driver.py | 0279d399396fed1253d46cf525d65f15ff61a6c1 | present | 1771 |
| RC-020 | driver.py holds no SubmissionCertainty reference | src/interfaces/portals/upgrade_portal/upgrade/driver.py | 0279d399396fed1253d46cf525d65f15ff61a6c1 | absent | 0 |
| RC-021 | CloudUpgradeSubmitter class | src/interfaces/portals/upgrade_portal/app/wiring.py | 78a1f4c825fb10f5e4ae7c2ef689ef01c45ecc85 | present | 962 |
| RC-022 | _send returns None when the call raises | src/interfaces/portals/upgrade_portal/app/wiring.py | 78a1f4c825fb10f5e4ae7c2ef689ef01c45ecc85 | present | 1233 |
| RC-023 | _send treats each non-accepted status as a refusal | src/interfaces/portals/upgrade_portal/app/wiring.py | 78a1f4c825fb10f5e4ae7c2ef689ef01c45ecc85 | present | 1236 |
| RC-024 | PHASE_REFUSED_REASON reads "The cloud refused the {phase} upgrade call" | src/interfaces/portals/upgrade_portal/app/wiring.py | 78a1f4c825fb10f5e4ae7c2ef689ef01c45ecc85 | present | 124 |
| RC-025 | _persist_refusal writes refusal evidence | src/interfaces/portals/upgrade_portal/app/wiring.py | 78a1f4c825fb10f5e4ae7c2ef689ef01c45ecc85 | present | 1090 |
| RC-026 | RunDispatchGate.fence blocks later dispatch after a store failure | src/interfaces/portals/upgrade_portal/app/wiring.py | 78a1f4c825fb10f5e4ae7c2ef689ef01c45ecc85 | present | 1161 |
| RC-027 | wiring.py holds no SubmissionCertainty reference | src/interfaces/portals/upgrade_portal/app/wiring.py | 78a1f4c825fb10f5e4ae7c2ef689ef01c45ecc85 | absent | 0 |
| RC-028 | RunDispatchGate class | src/interfaces/portals/upgrade_portal/runtime/signals.py | 65d37ab5f6ff24452c272b99e03a72da5c646b9c | present | 345 |
| RC-029 | ACCEPTED_STATUS equals (200, 202) | src/operations/execution/firmware/upgrade_service.py | 24825d192e4988ce408b92e9a3be6f5fb10b6d90 | present | 81 |
| RC-030 | ENDPOINT_SITE_DEVICE equals "upgradeDevice" | src/operations/execution/firmware/upgrade_service.py | 24825d192e4988ce408b92e9a3be6f5fb10b6d90 | present | 48 |
| RC-031 | invoke_upgrade sends one plan and never retries | src/operations/execution/firmware/upgrade_service.py | 24825d192e4988ce408b92e9a3be6f5fb10b6d90 | present | 1377 |
| RC-032 | Response validity uses SubmissionCertainty.response_data_is_valid | src/operations/execution/firmware/upgrade_service.py | 24825d192e4988ce408b92e9a3be6f5fb10b6d90 | present | 1310 |
| RC-033 | SubmissionCertainty class | src/foundation/support/submission_certainty.py | 488641368f4c370aeef58973665f5937b5ba87af | present | 9 |
| RC-034 | REFUSAL_STATUSES equals 400, 401, 403, 404 | src/foundation/support/submission_certainty.py | 488641368f4c370aeef58973665f5937b5ba87af | present | 12 |
| RC-035 | Contract row: 400, 401, 403, or 404 with no conflict is rejected | specs/numbered/0/0/1/0/4/4/0/1/3726-site-lock-safety/design/contracts/submission-certainty.md | 1fd9237f5e543242f9093abadbdee98c879367bd | present | 14 |
| RC-036 | Contract row: transport exception, 408, 429, 499, or any 5xx is submission_unknown | specs/numbered/0/0/1/0/4/4/0/1/3726-site-lock-safety/design/contracts/submission-certainty.md | 1fd9237f5e543242f9093abadbdee98c879367bd | present | 18 |
| RC-037 | Contract: lock release checks status with the shared settlement helper | specs/numbered/0/0/1/0/4/4/0/1/3726-site-lock-safety/design/contracts/submission-certainty.md | 1fd9237f5e543242f9093abadbdee98c879367bd | present | 23 |
| RC-038 | Site lock contract: key expiry is 3600 seconds | specs/1823-upgrade-capture-portal/contracts/site-lock.md | c06893f066c98f65d3c3ab00d72d2a5560d03851 | present | 23 |
| RC-039 | Site lock contract: lock releases at complete, stopped, or failed | specs/1823-upgrade-capture-portal/contracts/site-lock.md | c06893f066c98f65d3c3ab00d72d2a5560d03851 | present | 105 |
| RC-040 | Site lock contract: quiet holder waits 300 seconds before takeover | specs/1823-upgrade-capture-portal/contracts/site-lock.md | c06893f066c98f65d3c3ab00d72d2a5560d03851 | present | 113 |
| RC-041 | LOCK_TTL_SECONDS equals 3600 | src/interfaces/portals/upgrade_portal/runtime/lock.py | 1b9a4a2916ab3ffe3a5835c69db7220902c5e8c7 | present | 144 |
| RC-042 | COOLDOWN_SECONDS equals 300 | src/interfaces/portals/upgrade_portal/runtime/lock.py | 1b9a4a2916ab3ffe3a5835c69db7220902c5e8c7 | present | 190 |
| RC-043 | RESUME_CONFIRMATION_TEXT equals "continue" | src/interfaces/portals/upgrade_portal/runtime/lock.py | 1b9a4a2916ab3ffe3a5835c69db7220902c5e8c7 | present | 204 |
| RC-044 | Multi-site submit loop sends each child with no phase order | src/operations/execution/firmware/aggregate_upgrade_service.py | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 232 |
| RC-045 | Org submission sets submission_unknown when refusal is not proven | src/operations/execution/firmware/aggregate_upgrade_service.py | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 966 |
| RC-046 | Device submission sets submission_unknown when refusal is not proven | src/operations/execution/firmware/aggregate_upgrade_service.py | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 999 |
| RC-047 | _operation_is_settled requires final states and settlement proof | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1803 |
| RC-048 | release_operation_locks releases locks after settlement | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1782 |
| RC-049 | Multi-site confirm check requires the word CONFIRM | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 2185 |
| RC-050 | CONFIRM_TEXT equals "CONFIRM" | src/interfaces/portals/upgrade_portal/app/routes/upgrade.py | ac87e5dda78b77a7856d410668185f1f9df788c1 | present | 172 |
| RC-051 | LIVE_UPGRADE_STATES is a frozenset of live states | src/interfaces/portals/upgrade_portal/app/routes/upgrade.py | ac87e5dda78b77a7856d410668185f1f9df788c1 | present | 184 |
| RC-052 | UPGRADE_RUNNING_CODE names the active-run refusal | src/interfaces/portals/upgrade_portal/app/routes/upgrade.py | ac87e5dda78b77a7856d410668185f1f9df788c1 | present | 209 |
| RC-053 | Start route is POST UPGRADE_START_PATH | src/interfaces/portals/upgrade_portal/app/routes/upgrade.py | ac87e5dda78b77a7856d410668185f1f9df788c1 | present | 2286 |
| RC-054 | retry_run builds a new run from an unsuccessful run | src/interfaces/portals/upgrade_portal/app/routes/upgrade.py | ac87e5dda78b77a7856d410668185f1f9df788c1 | present | 2808 |
| RC-055 | retry_run forgets the source run dispatch fence | src/interfaces/portals/upgrade_portal/app/routes/upgrade.py | ac87e5dda78b77a7856d410668185f1f9df788c1 | present | 2850 |
| RC-056 | RECONCILE_PATH names the reconcile route | src/interfaces/portals/upgrade_portal/api/run_controls/routes.py | 38ad8dfd9ce91aa7289a95d2753bb47d2bb64aee | present | 47 |
| RC-057 | Reconcile route reads listSiteDevicesStats | src/interfaces/portals/upgrade_portal/api/run_controls/routes.py | 38ad8dfd9ce91aa7289a95d2753bb47d2bb64aee | present | 135 |
| RC-058 | ReconciliationEvidence class | src/interfaces/portals/upgrade_portal/api/run_controls/services/reconciliation.py | 1e881aa7027c416de17f14ee1e416499abedfca7 | present | 245 |
| RC-059 | StoppingRunReconciler class | src/interfaces/portals/upgrade_portal/api/run_controls/services/reconciliation.py | 1e881aa7027c416de17f14ee1e416499abedfca7 | present | 316 |
| RC-060 | StoppingRunReconciler.reconcile method | src/interfaces/portals/upgrade_portal/api/run_controls/services/reconciliation.py | 1e881aa7027c416de17f14ee1e416499abedfca7 | present | 334 |
| RC-061 | Failed run reconciliation writes the outcome complete | src/interfaces/portals/upgrade_portal/api/run_controls/services/reconciliation.py | 1e881aa7027c416de17f14ee1e416499abedfca7 | present | 465 |
| RC-062 | OrgReconcileCheck class | src/interfaces/portals/upgrade_portal/upgrade/org_reconcile.py | f4f8310e93f5fd1dd3cfc80607ec4f2a1a4a4e17 | present | 67 |
| RC-063 | RunningFirmwareVersionResolver class | src/operations/execution/firmware/running_version.py | c25d183e1498e79a6f612a0087f370cf904ba3f8 | present | 64 |
| RC-064 | RUN_COLLECTION equals "upgrade_runs" | src/interfaces/portals/upgrade_portal/capture/store.py | febef2d25a1abb1239053fbd93fa811bae501bea | present | 40 |
| RC-065 | verify_write reads a stored record back | src/interfaces/portals/upgrade_portal/capture/store.py | febef2d25a1abb1239053fbd93fa811bae501bea | present | 1148 |
| RC-066 | write_run stores a run document | src/interfaces/portals/upgrade_portal/capture/store.py | febef2d25a1abb1239053fbd93fa811bae501bea | present | 1421 |
| RC-067 | Multi-site cadence warning, first line | src/interfaces/portals/upgrade_portal/app/assets/templates/partials/org_phase_list.html | bb5be8aa9538182734736f600ffac105c1a87fab | present | 76 |
| RC-068 | Multi-site cadence warning, second line | src/interfaces/portals/upgrade_portal/app/assets/templates/partials/org_phase_list.html | bb5be8aa9538182734736f600ffac105c1a87fab | present | 77 |
| RC-069 | Single-site cadence paragraph | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/progress.html | a2a6b7bf5db75ecaf8ee488893ae24b568636b3d | present | 236 |
| RC-070 | Single-site retry controls for failed, stopped, and cancelled runs | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/progress.html | a2a6b7bf5db75ecaf8ee488893ae24b568636b3d | present | 491 |
| RC-071 | Test: a stopped run releases the site lock | tests/unit/upgrade_portal/test_upgrade_driver.py | 3a8d182485ac606233dafdfe2582dbb15a858b88 | present | 1992 |
| RC-072 | Test: a failed run releases the site lock | tests/unit/upgrade_portal/test_upgrade_driver.py | 3a8d182485ac606233dafdfe2582dbb15a858b88 | present | 2009 |
| RC-073 | Test: a failed phase does not stop the later phases | tests/unit/upgrade_portal/test_org_cascade_walk.py | a352992e1b27208073ed26c17a36b39575cdac0e | present | 217 |
| RC-074 | Test: a resumed walk keeps the ended phases | tests/unit/upgrade_portal/test_org_cascade_walk.py | a352992e1b27208073ed26c17a36b39575cdac0e | present | 331 |
| RC-075 | Refused fixture uses status 400 | tests/unit/upgrade_portal/test_wiring_submitter.py | fc6f500f54f0cb98bf77fff0229d4173403d6110 | present | 46 |
| RC-076 | Aggregate firmware test file exists | tests/unit/firmware/test_aggregate_upgrade_service.py | 323ca22161c07b54c0a39b4e4a5a662745ddceb5 | present | 0 |
| RC-077 | Parity test asserts the observes-the-submitted-work text | tests/unit/upgrade_portal/test_org_phase_list_parity.py | d7f0cf05ced527176f3a8bf278a1cbcccff9c918 | present | 145 |
| RC-078 | Contract test asserts the uncertain-submission warning text | tests/contract/upgrade_portal/test_org_phase_watch_contract.py | 4906854c4db4dc3785e2aea8742000e81606be4c | present | 471 |
| RC-079 | E2E postcheck test asserts the watch state Stopped | tests/e2e/upgrade_portal/test_org_postcheck_journey.py | 9f297a567d532d7436c2ef4b97181a93561c6777 | present | 166 |
| RC-080 | E2E multi-site class TestMultiSitePhaseCascade | tests/e2e/upgrade_portal/test_org_phase_cascade_journey.py | 925284153ae01d828c84fd74bf161bea007cedbb | present | 164 |
| RC-081 | Run controls E2E test file exists | tests/e2e/upgrade_portal/test_run_controls/test_existing.py | 2f9d91a74e30fde59cd451945f06a7b899d1c340 | present | 0 |
| RC-082 | Single-site retry contract test file exists | tests/contract/upgrade_portal/test_retry_failed_run.py | 46a38a7f222930c5c29776f544bd41b9a42dc46f | present | 0 |
| RC-083 | Reconciliation unit test file exists | tests/unit/upgrade_portal/test_runs/test_reconciliation.py | 99843269050ad4a26a233296c6f26ed056388190 | present | 0 |
| RC-084 | Signals unit test file exists | tests/unit/upgrade_portal/test_signals.py | 5ad385292b701c4c17e066d5bbb4adb1cbc2a10f | present | 0 |
| RC-085 | Destructive menu guard test file exists | tests/guardrails/test_destructive_menu_docs.py | 7acb28a5879b6634850f3558e636d6b798695fe8 | present | 0 |
| RC-086 | SDK compatibility guard test file exists | tests/integration/test_mistapi_sdk_compatibility.py | cab2d602113012729f6c392dff43197d05913a38 | present | 0 |
| RC-087 | Operator guide has the STOP phrase row | documentation/upgrade_capture_portal.md | 97fc51f98df43dff874b22330efb274e625054a8 | present | 61 |
| RC-088 | Operator guide lock table gives lock life 300 | documentation/upgrade_capture_portal.md | 97fc51f98df43dff874b22330efb274e625054a8 | present | 625 |
| RC-089 | Spec route uses base 5 | .specify/scripts/powershell/spec-route.ps1 | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-090 | Process folder baseline file exists | tests/guardrails/process_folder_baseline.json | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| RC-091 | changelog.d README exists | changelog.d/README.md | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 0 |
| RC-092 | Pull request template exists | .github/PULL_REQUEST_TEMPLATE.md | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 0 |
| RC-093 | STE linter configuration exists | .ste-linter.toml | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| RC-094 | No ROUTE folder for 4022 and no tree path containing 4022 on main | specs/numbered/0/0/1/1/2/0/4/2 | bdb46615f769b9aa1a75b8b734e9553329eb9bb0 | absent | 0 |
| RC-095 | Commit acaae1ad is an ancestor of main | git commit acaae1adbd22b3875db850ab4026bb2922491ec6 | acaae1adbd22b3875db850ab4026bb2922491ec6 | present | 0 |
| RC-096 | Commit 44e509a2 is an ancestor of main | git commit 44e509a28cf8150c346ffbd55b3e97ee9ca25c3f | 44e509a28cf8150c346ffbd55b3e97ee9ca25c3f | present | 0 |
| RC-097 | Commit 53ad73cc is an ancestor of main | git commit 53ad73cc37dc0821faca093441ecd12268e6a75d | 53ad73cc37dc0821faca093441ecd12268e6a75d | present | 0 |
| RC-098 | SDK upgradeSiteDevices | .venv/Lib/site-packages/mistapi/api/v1/sites/devices.py | fd3faa0988e688c1cac4e21f22ebe22693f77409 | present | 1230 |
| RC-099 | SDK getSiteDeviceUpgrade | .venv/Lib/site-packages/mistapi/api/v1/sites/devices.py | fd3faa0988e688c1cac4e21f22ebe22693f77409 | present | 1261 |
| RC-100 | SDK cancelSiteDeviceUpgrade | .venv/Lib/site-packages/mistapi/api/v1/sites/devices.py | fd3faa0988e688c1cac4e21f22ebe22693f77409 | present | 1289 |
| RC-101 | SDK listSiteDeviceUpgrades | .venv/Lib/site-packages/mistapi/api/v1/sites/devices.py | fd3faa0988e688c1cac4e21f22ebe22693f77409 | present | 1196 |
| RC-102 | SDK listSiteDevicesStats | .venv/Lib/site-packages/mistapi/api/v1/sites/stats.py | bce91c2c8ff2c793190c2afb3548ae83e15322c2 | present | 1051 |
| RC-103 | SDK upgradeOrgDevices | .venv/Lib/site-packages/mistapi/api/v1/orgs/devices.py | 90fe126e9c3e34d7784644016e12833b7359737d | present | 840 |
| RC-104 | SDK getOrgDeviceUpgrade | .venv/Lib/site-packages/mistapi/api/v1/orgs/devices.py | 90fe126e9c3e34d7784644016e12833b7359737d | present | 871 |
| RC-105 | SDK listOrgDeviceUpgrades | .venv/Lib/site-packages/mistapi/api/v1/orgs/devices.py | 90fe126e9c3e34d7784644016e12833b7359737d | present | 815 |
| RC-106 | OpenAPI operation upgradeSiteDevices | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 28859 |
| RC-107 | OpenAPI operation getSiteDeviceUpgrade | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 28885 |
| RC-108 | OpenAPI operation cancelSiteDeviceUpgrade | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 28912 |
| RC-109 | OpenAPI operation listSiteDeviceUpgrades | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 28830 |
| RC-110 | OpenAPI operation listSiteDevicesStats | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 39555 |
| RC-111 | OpenAPI operation upgradeOrgDevices | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9260 |
| RC-112 | OpenAPI operation getOrgDeviceUpgrade | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9286 |
| RC-113 | OpenAPI operation listOrgDeviceUpgrades | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9236 |
| RC-114 | Portal root folder holds 12 children (noncompliant) | src/interfaces/portals/upgrade_portal | 9f69e75110e889343b9a81f62c774f60fd1ebe33 | present | 0 |
| RC-115 | api/run_controls folder holds 5 children (full) | src/interfaces/portals/upgrade_portal/api/run_controls | cdfe2b889fd55afa47dd609afef43b0a1b27ef85 | present | 0 |
| RC-116 | api/run_controls/services folder holds 5 children (full) | src/interfaces/portals/upgrade_portal/api/run_controls/services | e33652de8414de1a54a5fbce943383910ad252e0 | present | 0 |
| RC-117 | upgrade folder holds 22 children (noncompliant) | src/interfaces/portals/upgrade_portal/upgrade | 4523cb1c518d4a6c85b719a956478a40384c076e | present | 0 |
| RC-118 | upgrade/org_cascade folder holds 7 children (noncompliant) | src/interfaces/portals/upgrade_portal/upgrade/org_cascade | f4283272eaca0e8ba2c1910d6ce8390fd85dbd32 | present | 0 |
| RC-119 | runtime folder holds 10 children (noncompliant) | src/interfaces/portals/upgrade_portal/runtime | 6603e5cd07604509e51b07689609de824a4c2d91 | present | 0 |
| RC-120 | app folder holds 10 children (noncompliant) | src/interfaces/portals/upgrade_portal/app | 5050b006f776a8b4031cbc64293c4c52ddc646fa | present | 0 |
| RC-121 | app/routes folder holds 13 children (noncompliant) | src/interfaces/portals/upgrade_portal/app/routes | 6c14ca92440a688b6e56687c4e8648b7e439b886 | present | 0 |
| RC-122 | capture folder holds 10 children (noncompliant) | src/interfaces/portals/upgrade_portal/capture | 2767a3cd5c8cad30939290d2c04086f4f8c4e791 | present | 0 |
| RC-123 | Firmware folder holds 12 children (noncompliant) | src/operations/execution/firmware | 414a7e58ca8202cb4d000c6900685bc484fb6810 | present | 0 |
| RC-124 | tests/unit/upgrade_portal folder holds 168 children (noncompliant) | tests/unit/upgrade_portal | 4a51282e64576c2deb09060a34997275fcc4603a | present | 0 |
| RC-125 | tests/contract/upgrade_portal folder holds 66 children (noncompliant) | tests/contract/upgrade_portal | 0d329a2d3c0e8e6b3811fab73b0a62f28fa1f6b7 | present | 0 |
| RC-126 | tests/e2e/upgrade_portal folder holds 68 children (noncompliant) | tests/e2e/upgrade_portal | d2ccab20f48271223a422fb95cd58abc685370d3 | present | 0 |
| RC-127 | changelog.d process folder holds 335 children (allowed process folder) | changelog.d | ece56396f47d31dfed7bebe6c69f6dda39f53d83 | present | 0 |
| RC-128 | README names the upgrade capture portal | README.md | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | present | 12 |
| RC-129 | portal.js declares initRunReconciliation | src/interfaces/portals/upgrade_portal/app/assets/static/js/portal.js | 03ed368d398f4074894ee041de6900ac7fbd8b4c | present | 4806 |
| RC-130 | AGENTS.md exists | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| RC-131 | Repository instructions exist and hold the gate table | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 0 |
| RC-132 | Constitution exists | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 0 |
| RC-133 | Spec template exists | .specify/templates/spec-template.md | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| RC-134 | Plan template exists | .specify/templates/plan-template.md | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| RC-135 | Tasks template exists | .specify/templates/tasks-template.md | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| RC-136 | Checklist template exists | .specify/templates/checklist-template.md | 806657da09d1058823923e346a323b633114971a | present | 0 |
| RC-137 | Quality gates document exists | documentation/quality-gates.md | 6776d334cca5d9b43273473a06da367a65605c6d | present | 0 |
| RC-138 | Architecture document exists | documentation/architecture.md | b4cab54be36d223b7eba879ca99b838f508938ce | present | 0 |
| RC-139 | Development setup document exists | documentation/development-setup.md | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 0 |
| RC-140 | Container deployment document exists | documentation/container-deployment.md | f06228bc6bbe77cc009f956403872a06462466ea | present | 0 |
| RC-141 | Operator guide exists | documentation/operator-guide.md | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 0 |
| RC-142 | Mist GET endpoint coverage document exists | documentation/MIST_API_GET_ENDPOINTS.md | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 0 |
| RC-143 | Mist missing endpoint coverage document exists | documentation/MIST_API_MISSING_ENDPOINTS.md | e4949ef2ab2ed1d86e6309bd919401d65b2c0ae0 | present | 0 |
| RC-144 | Reference record spec exists (shape only) | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |

## R6. Decisions

Each decision names the chosen option, the alternatives, the reason, and the risk. Decision D-11 carries the human flag.

- **D-1 (sequence)**: Single-site work comes first. Multi-site resume waits for issue #4021 (RC-044). Alternatives: ship both flows now (rejected, because the multi-site gate contract is not defined). Single-site only (rejected, because multi-site has the same defect class). Risk: the multi-site path stays exposed until #4021 merges. Human decision: no.
- **D-2 (resume rule)**: Resume applies to stopped runs only. The operator confirms the repair first. A settled phase never repeats. A phase with no settled result never gets skipped. Basis: the owner rule on #4020 (comment 6031475938) and owner decision 4 in the #4022 body. Alternatives: automatic resume after reconciliation (rejected, because the owner rule forbids automatic retry). Re-run the whole cascade (rejected, because it repeats settled phases). Risk: operators must act. Human decision: no.
- **D-3 (mechanism)**: The resume runs in place on the stopped run. It enters a new `resuming` state (RC-006, RC-007, RC-008). Alternatives: a child run (rejected, because it duplicates the lock owner and the tracker row). Reuse the retry flow (rejected, because the retry creates a new run after a fresh capture, RC-054). Risk: the terminal-state rules change. Mitigation: T005 tests and TC-09 to TC-16. Human decision: no.
- **D-4 (typed word)**: The typed word is `RESUME`, with exact case. Alternatives: `CONFIRM` (rejected, because the start route uses it, RC-050, and a repeated start could follow). `continue` (rejected, because the lock contract uses it for the same operator returning, RC-043). `CANCEL` (rejected, because it means cancel, RC-049). Risk: one more operator word to learn. Mitigation: the run page names the word. Human decision: no.
- **D-5 (classification)**: Every firmware reply uses the shared certainty rule. A documented refusal (400, 401, 403, 404) with no conflict is `refused`. Every other reply and each transport fault is `unknown` (RC-035, RC-036, RC-034). Alternatives: keep the current refusal for all non-2xx replies (rejected, because it misstates the outcome, RC-023). Treat every non-accepted reply as unknown (rejected, because it makes a proven refusal need reconciliation). Risk: a new classification changes the page text. Mitigation: TC-01 to TC-04. Human decision: no.
- **D-6 (site hold)**: A stopped or failed run keeps a durable site hold while a phase is `unknown` or `accepted` and unsettled. Start, pre-check, takeover, retry, and resume honor the hold. Alternatives: rely on the Redis lock (rejected, because the key expires after 3600 seconds and the quiet period opens a takeover after 300 seconds). Sources: RC-038, RC-040, RC-041. Keep the driver thread alive (rejected, because the thread lifetime and resource use grow). Risk: a site stays blocked until reconciliation. Mitigation: the run page shows the proof and the next step. Human decision: no.
- **D-7 (reconciliation)**: The reconciler reuses the read-only reconcile evidence (RC-057) and the SDK job listing (RC-101). It reads running versions through `RunningFirmwareVersionResolver` (RC-063). Alternatives: stored state only (rejected, because the issue requires live reconciliation). A write probe (rejected, because a write is destructive). Risk: a job listing can miss a new job (U-02). Mitigation: FR-014 and the operator review. Human decision: no.
- **D-8 (observation)**: Observation keeps a failed phase as ended. The resume resets the recovery phase to `pending` before any observation (RC-010, RC-011, RC-073). Alternatives: remove failed from the ended states (rejected, because each restart waits again for a phase that has no pending write). Risk: an operator who reads only the observation page sees a failed phase as ended. Mitigation: the run page names the recovery phase. Human decision: no.
- **D-9 (code placement)**: The change adds no file and no folder. New classes go into existing modules. The reconciler joins `reconciliation.py`, which sits in a five-child folder (RC-116). Alternatives: a new package under `upgrade/` (rejected, because `upgrade/` already holds 22 children, RC-117). A new file in `services/` (rejected, because `services/` is full, RC-116). Risk: the modules grow. Human decision: no.
- **D-10 (logging)**: New code uses the standard `logging` module with `%s` values and key=value fields. Alternatives: add `structlog` (rejected, because it adds a dependency and the portal logs use the standard module). The constitution accepts "structlog or equivalent" (`constitution.md`, Principle V). Risk: logs are less structured than a JSON logger. Human decision: no.
- **D-11 (start)**: HUMAN-DECISION-REQUIRED. Hold the implementation until the owner approves D-1 to D-12 in a comment. The owner must also file the separate single-site unknown-outcome issue (AGENTS.md issue-first rule). Recommended option: keep the hold until issue #4021 merges and the owner approves the start. Alternatives: start now (rejected, because #4021 is open and the issue body says to hold). Close the issue (rejected, because the owner still needs the resume). Risk: the operator stays without a resume path for longer. Human decision: yes. The rule is product priority for a destructive path.
- **D-12 (operator text)**: Every stop, failure, and unknown message names the phase, the reason, and one next step. Each changed string updates its test in the same change (RC-077, RC-078, RC-079). Alternatives: keep the current text (rejected, because RC-009 gives no next step). Change the text without the test update (rejected, because the test suite fails in CI, as pull request #4005 showed). Risk: more test edits. Human decision: no.

## R7. Sources

Local files read as evidence. Each file's remote blob SHA appears in R5.

- `AGENTS.md` (RC-130)
- `.github/copilot-instructions.md` (RC-131)
- `.specify/memory/constitution.md` (RC-132)
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md` (RC-133 to RC-136)
- `documentation/quality-gates.md`, `architecture.md`, `development-setup.md`, `container-deployment.md`, `operator-guide.md` (RC-137 to RC-141). The operator guide and the architecture document hold no section on the upgrade portal that this change alters. The record cites the upgrade capture portal document instead (RC-087, RC-088).
- `documentation/upgrade_capture_portal.md` (RC-087, RC-088)
- `documentation/mist-api-openapi31yaml.yaml` (RC-106 to RC-113)
- `documentation/MIST_API_GET_ENDPOINTS.md`, `MIST_API_MISSING_ENDPOINTS.md` (RC-142, RC-143). These files list GET endpoint coverage and missing endpoints. The record checks the presence of each file only.
- `specs/1823-upgrade-capture-portal/contracts/site-lock.md` (RC-038 to RC-040)
- `specs/numbered/0/0/1/0/4/4/0/1/3726-site-lock-safety/design/contracts/submission-certainty.md` (RC-035 to RC-037)
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/` (shape only, RC-144)
- `.venv/Lib/site-packages/mistapi/api/v1/` (RC-098 to RC-105). Local `mistapi` version: the distribution directory is `mistapi-0.64.1.dist-info`, which meets the pin `mistapi>=0.64.0,<0.65` named in `copilot-instructions.md`.

External URLs: none. `web_fetch` was not used. The local sources answered every question.

## R8. Skills

No local skill was loaded. The issue asks no Podman question and no Juniper device behavior question.

## R9. Unverified

- **U-01**: The owner approval (T000) and the separate issue for the single-site unknown outcome. The brief forbids GitHub writes in this run. The owner must act.
- **U-02**: Whether the Mist job listing shows a job created moments before an `unknown` reply. No live Mist request ran. FR-014 requires operator review of the evidence.
- **U-03**: Whether `walk.py` lease release can run while a multi-site child has an `unknown` status. The code path (RC-012, RC-013) shows the release has no settlement check. The reachability was not proven in this record. T015 adds a test to settle it.
- **U-04**: The implementation of `RunningFirmwareVersionResolver` beyond its class line (RC-063). The record did not read its methods.
- **U-05**: The bodies of the tests named TC-07, TC-08, and TC-17. The record read only their names and line numbers. T003 and T004 audit each body before the change.
- **U-06**: How the new controls render in a browser. No browser ran.
- **U-07**: The phase deadline value and the settle timing in `phase_gate.py`. The spec does not depend on them.
- **U-08**: The wording of the new operator text. The record gives the required content (FR-025). The final words are set during T013.

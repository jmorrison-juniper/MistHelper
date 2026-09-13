# Tasks: Stale and Bulk Run Controls

**Input**: All documents in `specs/2447-stale-bulk-run-controls/`

**Execution rule**: Run tasks in order unless a task names a safe parallel
group. No browser command can run before Phase 2 completes.

**Failure rule**: Fix a feature-caused failure in this feature. Create one
GitHub issue before a repair of an unrelated failure.

## Phase 1: Ownership, Scope, Debt Boundary, and Terminal Authority

**Goal**: Claim the work, freeze the complete scope, and remove divergent
terminal-state checks.

- [x] T001 Fetch `origin/main`. Confirm the active branch is `fix/2447-stale-bulk-run-controls` and that `HEAD` starts at current `origin/main`.
- [x] T002 Claim issue #2447, add `in-progress`, and confirm that no conflicting owner holds the implementation.
- [x] T003 Check active worktrees, active branches, and open pull request files against the complete feature manifest. Stop on an overlap without a recorded handoff.
- [x] T004 Confirm that `feature-files.txt` contains all 79 planned paths before the first source or test edit. Compare current tracked and untracked feature changes with it. Exclude unrelated pre-existing untracked files.
- [x] T005 Record the grandfathered hierarchy violations as separate remediation actions. Confirm every new package and subpackage uses the child budget in `plan.md`.
- [x] T006 Create and verify the ArangoDB backup before any action schema or persistence change.
- [x] T007 Write tests that prove `complete`, `failed`, `stopped`, and `cancelled` are terminal in stop, history, stale, and live-run decisions.
- [x] T008 Change `runtime/signals.py` to use `RunStateMachine.TERMINAL` and remove `TERMINAL_RUN_STATES`.
- [x] T009 Change `app/routes/review.py` to use `RunStateMachine.TERMINAL` and remove `FINISHED_RUN_STATES`.
- [x] T010 Search the upgrade portal for every terminal-state set and replace each run-state decision with `RunStateMachine.TERMINAL`.
- [x] T011 Run the focused terminal-state unit and contract tests.

**Checkpoint**: One canonical terminal set controls all run-state decisions.

## Phase 2: E2E Isolation Before Browser Execution

**Goal**: Install all isolation controls before a browser process starts.

- [x] T012 Replace `tests/unit/upgrade_portal/test_runs.py` with the same-name package. Move existing tests before adding new tests.
- [x] T013 Replace `tests/contract/upgrade_portal/test_upgrade_routes.py` with the same-name package. Move existing tests before adding new tests.
- [x] T014 Replace `tests/e2e/upgrade_portal/test_run_controls.py` with the same-name package. Move existing tests into `test_existing.py`.
- [x] T015 Create the integration and support packages with every exact child from the layouts in `plan.md`.
- [x] T016 Write failing unit tests for override completeness, trap calls, credential scrub, unique ports, unique artifacts, and record ownership.
- [x] T017 Write failing contract tests for override installation before route registration.
- [x] T018 Implement the E2E override value classes in the new run-controls API package.
- [x] T019 Edit `app/factory.py` surgically so it validates and installs overrides before blueprint registration.
- [x] T020 Edit `app/wiring.py` surgically so it injects all action, access, cloud, audit, connector, and file seams.
- [x] T021 Implement process-owned run, action, access, cloud, and audit stores under `tests/support/upgrade_portal_e2e/records/`.
- [x] T022 Implement ArangoDB, Redis, and Mist connector traps under `tests/support/upgrade_portal_e2e/traps/`.
- [x] T023 Implement the portal record file trap and zero-call assertions.
- [x] T024 Implement credential scrub and explicit loopback port-1 sentinels.
- [x] T025 Implement unique port, test identifier, record store, log, process file, and artifact allocation.
- [x] T026 Reset cached storage and readiness state in `tests/e2e/upgrade_portal/conftest.py` before application construction.
- [x] T027 Add `X-MistHelper-E2E-Run-ID` only when E2E overrides are active.
- [x] T028 Run only the isolation unit and contract tests. Do not run a browser test.

**Checkpoint**: Every connector and file path fails closed before route
registration. Browser execution is now permitted.

## Phase 3: Shared Stale Policy

**Goal**: Give every page the same stale decision.

- [x] T029 Write stale policy tests for boundaries, terminal states, offsets, malformed times, and future times.
- [x] T030 Write stale view contracts for the history and run pages.
- [x] T031 Implement `StaleAssessment` and `RunStalePolicy` in the compliant run-controls API package.
- [x] T032 Edit `app/routes/review.py` to call the shared stale policy without adding a top-level helper.
- [x] T033 Edit `app/routes/upgrade.py` to call the same stale policy without adding a top-level helper.
- [x] T034 Add age and stale markup to the history and progress templates.
- [x] T035 Add display-only age updates to `portal.js`.
- [x] T036 Add accessible stale styles to `portal.css`.
- [x] T037 Add browser stale tests and run them with all isolation traps active.

## Phase 4: Operational Store and Durable Actions

**Goal**: Create one durable action and one durable item for each accepted run.

- [x] T038 Add the `upgradeRunActions` composite key strategy before action persistence.
- [x] T039 Write action model tests for bulk and single-run source fields.
- [x] T040 Write tests that prove reconciliation needs no preview and stores null preview fields.
- [x] T041 Write tests for duplicate identifiers, durable actor scope, ordered placeholders, item claims, action leases, evidence fields, and evidence digests.
- [x] T042 Implement action value records in `persistence/actions/models.py`.
- [x] T043 Implement the ArangoDB action repository and actor-scoped result reads.
- [x] T044 Implement action initialization with ordered `pending` items and durable unknown placeholders.
- [x] T045 Implement an item claim with compare-and-swap from `pending` to `claimed`.
- [x] T046 Implement outcome-only writes for `refused`, `failed`, and `unknown` items.
- [x] T047 Implement atomic run mutation and successful outcome transactions.
- [x] T048 Implement processing-to-complete finalization after all items become final.
- [x] T049 Implement read-back verification before any success response.
- [x] T050 Write unavailable-store tests that prove no SQLite, Redis, memory, or file fallback.
- [x] T051 Write tests that prove API exports and data collection still use `DataExporter`.

**Checkpoint**: The operational store can initialize, claim, finalize, and read
an action. It cannot lose an item outcome.

## Phase 5: Replay, Crash Recovery, and Safe Resumption

**Goal**: Resume only work that has no possible prior mutation.

- [x] T052 Write tests for same-key replay, request mismatch, active lease, lease expiry, and compare-and-swap takeover.
- [x] T053 Write crash tests for a stop before claim, after claim, before transaction commit, and after transaction commit.
- [x] T054 Implement actor-scoped replay in `persistence/actions/replay.py`.
- [x] T055 Implement lease takeover with compare-and-swap.
- [x] T056 Finalize each abandoned `claimed` item as `unknown` with `processing_interrupted`.
- [x] T057 Resume only `pending` items and never repeat a `claimed` or `final` item.
- [x] T058 Persist site blocks and finalize later blocked items as `not_processed_after_site_guard_loss`.
- [x] T059 Finalize every remaining item and change the action to `complete`.
- [x] T060 Run the replay and crash-recovery unit and integration tests.

## Phase 6: Authoritative Bulk Preview

**Goal**: Remove hidden selections before phrase entry.

- [x] T061 Write preview tests for scope, hidden identifiers, duplicates, exact counts, expiry, and token binding.
- [x] T062 Write preview API contracts.
- [x] T063 Implement preview request and response values in the run-controls API package.
- [x] T064 Implement `BulkActionPreviewService`.
- [x] T065 Implement the preview route and signed token response.
- [x] T066 Edit `app/factory.py` and `app/wiring.py` only as needed to register the new blueprint and dependencies.
- [x] T067 Update `portal.js` to request preview, replace stored identifiers, and show server counts.
- [x] T068 Update the history template for preview counts, removed identifiers, and phrase entry.
- [x] T069 Add browser preview tests.

## Phase 7: Atomic Cancel and Reconciliation

**Goal**: Store each cancel or reconciliation result durably.

- [x] T070 Write cancel, site guard, and outcome-only unit tests.
- [x] T071 Write reconciliation decision tests for pre-cloud and `stopping` runs.
- [x] T072 Write cancel and reconciliation integration tests.
- [x] T073 Implement the permission and exact lock-token recheck.
- [x] T074 Implement stable site processing and the durable site stop rule.
- [x] T075 Implement the cancel transaction with verified persistence.
- [x] T076 Implement `TargetEvidence`, `ReconciliationEvidence`, and `ReconciliationEvidenceSummary` with the required types, null rules, safe fields, and canonical serializer.
- [x] T077 Implement the single-run reconciliation action initializer with no preview dependency.
- [x] T078 Implement the atomic reconciliation transaction and outcome-only paths. Store the summary and matching action digest in the same write unit.
- [x] T079 Implement cancel and reconciliation routes.
- [x] T080 Add reconciliation controls and results to the run page.
- [x] T081 Add browser cancel and reconciliation tests.

## Phase 8: Atomic Retry

**Goal**: Copy only valid options and preserve one live run for each site.

- [x] T082 Write retry source time, allowlist, validator, winner, and live-run tests.
- [x] T083 Write retry API reason and response contracts.
- [x] T084 Write concurrent retry, rollback, outcome-only, and crash-recovery integration tests.
- [x] T085 Implement `RetryCopyPolicy`.
- [x] T086 Implement the live-run check, retry insert, and successful outcome transaction.
- [x] T087 Add retry processing to the durable bulk service.
- [x] T088 Add retry result links and fresh pre-check navigation.
- [x] T089 Add browser retry tests.

## Phase 9: Browser Lifecycle and Persistent-Store Proof

**Goal**: Prove browser behavior without persistent data changes.

- [x] T090 Add browser tests for reload, navigation, two tabs, session renewal, another actor, response loss, keyboard use, and three viewports.
- [x] T091 Add browser header and trap assertions.
- [x] T092 Complete focus, alert, dialog, and narrow viewport behavior.
- [x] T093 Reverify the backup and record its freshness before the full E2E and deployment sequence.
- [x] T094 Record the persistent run, action, and audit baselines before the full E2E suite.
- [x] T095 Run the complete `tests/e2e/upgrade_portal` suite with strict mode and all traps active.
- [x] T096 Compare persistent run, action, and audit counts with the T094 baseline immediately after the suite.
- [x] T097 Stop the workflow and create an issue if any persistent count changed.

## Phase 10: Recovery Drill, Performance, and Traceability

**Goal**: Prove store recovery, fixed workloads, and complete requirement
coverage.

- [x] T098 Restore the verified backup to an isolated ArangoDB target.
- [x] T099 Verify run and action collection counts, keys, indexes, and sample records on the isolated target.
- [x] T100 Record that action retention matches the lifetime of referenced run records and that no cleanup job exists.
- [x] T101 Add the fixed 50-row history measurement.
- [x] T102 Add the fixed 50-run no-cloud batch measurement.
- [x] T103 Run both measurements with the warm-up and sample counts from `research.md`.
- [x] T104 Add requirement identifiers to named tests and update the traceability matrix.
- [x] T105 Review FR-001 through FR-076 against unit, contract, integration, browser, or manual evidence.
- [x] T106 Re-run `checklists/requirements.md` and leave no unchecked item.

## Phase 11: Manifest, Quality Gates, and Documentation

**Goal**: Gate and stage every feature file without touching unrelated work.

- [x] T107 Update `README.md` with the operator controls and governed deployment sequence.
- [x] T108 Update `documentation/upgrade_capture_portal.md` with stale, preview, reconciliation, result, retention, and recovery behavior.
- [x] T109 Add the feature entry to `CHANGELOG.md` with the required version format.
- [x] T110 Update `feature-files.txt` before any path differs from the 79-path plan.
- [x] T111 Build the changed-file set from the merge base, staged changes, unstaged changes, and untracked files.
- [x] T112 Compare the changed-file set with `feature-files.txt`. Reject an unlisted feature path and exclude unrelated pre-existing untracked paths.
- [x] T113 Run all applicable Python gates for each changed Python file in the manifest.
- [x] T114 Run all applicable JavaScript and browser gates for each changed JavaScript file in the manifest.
- [x] T115 Review each changed executable line for required comments and each meaningful action for required logs.
- [x] T116 Run all targeted unit, contract, integration, and browser tests.
- [x] T117 Run the full existing CI-equivalent local gates that apply to the manifest.
- [x] T118 Fix a feature-caused failure and rerun its gate.
- [x] T119 Create one GitHub issue before any repair of an unrelated failure. Record the issue URL.
- [x] T120 Run the STE linter for every Markdown file in the feature package and the amended constitution.
- [x] T121 Stage all feature files with `git add -A --pathspec-from-file=specs/2447-stale-bulk-run-controls/feature-files.txt`.
- [x] T122 Compare the manifest with the staged diff and prove that every changed feature path is staged.

## Phase 12: Commit, Rebase, Pull Request, Merge, and Deployment

**Goal**: Merge and deploy the exact approved revision.

- [x] T123 Commit the verified staged feature with the required UTC version title, `Closes #2447`, and co-author trailer.
- [x] T124 Fetch `origin/main` and rebase `fix/2447-stale-bulk-run-controls` onto `origin/main`.
- [x] T125 Rerun affected local gates after the rebase.
- [x] T126 If conflict repair changes a feature file, rebuild the manifest, stage all feature paths, verify the staged diff, and commit the repair.
- [x] T127 Push `fix/2447-stale-bulk-run-controls` with `--force-with-lease`. Do not push directly to `main`.
- [x] T128 Open a pull request to `main` with the exact title from `plan.md`. Include `Closes #2447`, the spec link, changed-file summary, acceptance evidence, local gates, CI status, security results, UI evidence, deployment notes, rollback notes, and every applicable template item. Add `bug`, `web-portal`, and `in-progress`.
- [x] T129 Wait for required human approval and every required pull request check, including CodeQL. Repair only feature-caused failures.
- [x] T130 Add the `auto-merge` label only after T129 completes.
- [x] T131 Confirm that the repository squash-merges the approved pull request to `main`.
- [x] T132 Record the exact merged commit SHA from `origin/main`.
- [x] T133 Wait for `.github/workflows/container-build.yml` on that merged commit.
- [x] T134 Pull `latest` and verify its `org.opencontainers.image.revision` label equals the merged commit SHA.
- [x] T135 Deploy the verified image with the existing Podman compose workflow.
- [x] T136 Confirm container health and the portal health and readiness checks.
- [x] T137 Record the optional Morrison House live check as skipped or authorized. Never run it automatically.

## Dependencies

- T001 through T011 complete before feature behavior.
- T012 through T028 complete before any browser execution.
- T038 completes before T042 through T051.
- T044 through T049 complete before cancel, retry, or reconciliation mutations.
- T052 through T060 complete before browser response-loss tests.
- T061 through T069 complete before bulk phrase entry tests.
- T070 through T081 complete before retry implementation.
- T094 completes before T095.
- T095 completes before T096.
- T098 through T106 complete before final quality gates.
- T107 through T110 complete before T111 through T122.
- T122 completes before the feature commit.
- T123 completes before the rebase.
- T129 completes before the auto-merge label.
- T130 completes before the squash merge.
- T132 completes before the main image wait.
- T134 completes before deployment.

## Safe Parallel Groups

Only these groups can run in parallel:

1. T016 and T017, because they change separate test paths.
2. T029 and T030, because they change separate test paths.
3. T070 and T071, because they change separate unit files.
4. T101 and T102, because they measure separate fixed workloads.

A shared file or incomplete dependency removes parallel eligibility.

## Delivery and deployment record, measured 2026-09-13

This record holds the evidence for Phase 12.

| Task | Evidence |
|---|---|
| T124 to T127 | Branch `feat/2447-bulk-preview-services` rebased onto `main`. One conflict in `persistence/actions/replay.py` kept both the action logging and the atomic refusal handling. |
| T128 | Pull request #2544 carried the preview, bulk, reconciliation, and retry services. |
| T129 | Every required check passed. The count was 28 success, 11 skipped, and no failure. |
| T130 and T131 | The repository squash-merged the pull request. |
| T132 | The merged commit is `5f1b38f6f25305af11583fd2af86d817c08ef794`. |
| T133 | The container build workflow succeeded for that commit and for each later commit on `main`. |
| T134 | The published image label `org.opencontainers.image.revision` reads `91775b5289628a34a0ff22072b20c01a9dd0c93c`. That value equals the head of `main`. |
| T135 | The portal container runs image `0cf03d5d69fe`. The deployment used `--no-deps`, so the document store and the lock store kept their records. |
| T136 | The container reports healthy. `GET /healthz` answered 200, `GET /readyz` answered 200, and the web portal answered 200. |
| T137 | **Skipped.** No live upgrade ran on the Morrison House site. The task forbids an automatic run. An operator must authorize that check. |

### Proof that the new code serves traffic

`POST /api/runs/bulk-actions/preview` answered 400, which shows the route exists and validates its body. An absent path answered 404 for comparison. The running container reports `run_controls` inside `BLUEPRINT_NAMES`.

### Browser evidence on main

The complete browser suite passed on `main`: **209 passed and 4 skipped**. All 19 multi-operator tests passed, which proves the site lock releases correctly. The four remaining skips describe a run state and never a defect.

## Phase 1 and Phase 10 evidence, measured 2026-09-13

| Task | Evidence |
|---|---|
| T001 | The work reached `main` through pull requests #2476, #2539, #2544, #2555, and #2559. Each one started at the head of `main` at that time. |
| T002 | Issue #2447 carries the assignee `jmorrison-juniper` and the label `in-progress`. The issue is closed now, because the work landed. |
| T003 | No open pull request touches `src/upgrade_portal/api/run_controls` or `src/upgrade_portal/persistence/actions`. The check found no overlap and no missing handoff. |
| T005 | Each new package holds five children or fewer. `api/run_controls` holds 4 files and 2 folders. `api/run_controls/services` holds 5 files. `persistence/actions` holds 5 files. `tests/support/upgrade_portal_e2e` holds 3 files and 3 folders. |
| T098 | The backup restored to an isolated ArangoDB container on port 9531. The restore reported 77 collections from 1 database. |
| T099 | The isolated target holds `upgrade_runs` 60, `upgrade_captures` 26, and `capture_for_run` 15. Every index survived, including the composite index on `site_id` and `created_at`. A sample read returned a complete run, a complete capture, and a complete edge. The edge check found 0 dangling edges. |

Warning: the drill used an isolated container, and the drill container is gone
now. A restore into the live store can cause the loss of every upgrade run
record, so the drill never touched the production store. A separate read
confirmed the production store kept 66 runs and 35 captures.

## Live site upgrade, T137

The live check ran on the Morrison House site. The gateway `SRX-1500` with the
address `5800bb5ee100` upgraded from version `23.4R2-S5.5` to version
`24.2R2-S3.3`.

| Field | Value |
|---|---|
| Mist audit record | "Upgrade scheduled by user", admin `workvscode` |
| Firmware result | `success`, progress 100, "Upgraded" |
| Device state after the restart | `connected`, version `24.2R2-S3.3` |
| Portal run record | `run-51f8c319224a4db099ea2e3b14a16233` |

Issue #2564 records a defect that this check found. An unattended driver renews
the site lock without limit, so an operator can never take the site.

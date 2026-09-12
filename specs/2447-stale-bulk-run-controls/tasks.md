# Tasks: Stale and Bulk Run Controls

**Input**: All documents in `specs/2447-stale-bulk-run-controls/`

**Execution rule**: Run tasks in order unless a task names a safe parallel
group. No browser command can run before Phase 2 completes.

**Failure rule**: Fix a feature-caused failure in this feature. Create one
GitHub issue before a repair of an unrelated failure.

## Phase 1: Ownership, Scope, Debt Boundary, and Terminal Authority

**Goal**: Claim the work, freeze the complete scope, and remove divergent
terminal-state checks.

- [ ] T001 Fetch `origin/main`. Confirm the active branch is `fix/2447-stale-bulk-run-controls` and that `HEAD` starts at current `origin/main`.
- [ ] T002 Claim issue #2447, add `in-progress`, and confirm that no conflicting owner holds the implementation.
- [ ] T003 Check active worktrees, active branches, and open pull request files against the complete feature manifest. Stop on an overlap without a recorded handoff.
- [ ] T004 Confirm that `feature-files.txt` contains all 79 planned paths before the first source or test edit. Compare current tracked and untracked feature changes with it. Exclude unrelated pre-existing untracked files.
- [ ] T005 Record the grandfathered hierarchy violations as separate remediation actions. Confirm every new package and subpackage uses the child budget in `plan.md`.
- [ ] T006 Create and verify the ArangoDB backup before any action schema or persistence change.
- [ ] T007 Write tests that prove `complete`, `failed`, `stopped`, and `cancelled` are terminal in stop, history, stale, and live-run decisions.
- [ ] T008 Change `runtime/signals.py` to use `RunStateMachine.TERMINAL` and remove `TERMINAL_RUN_STATES`.
- [ ] T009 Change `app/routes/review.py` to use `RunStateMachine.TERMINAL` and remove `FINISHED_RUN_STATES`.
- [ ] T010 Search the upgrade portal for every terminal-state set and replace each run-state decision with `RunStateMachine.TERMINAL`.
- [ ] T011 Run the focused terminal-state unit and contract tests.

**Checkpoint**: One canonical terminal set controls all run-state decisions.

## Phase 2: E2E Isolation Before Browser Execution

**Goal**: Install all isolation controls before a browser process starts.

- [ ] T012 Replace `tests/unit/upgrade_portal/test_runs.py` with the same-name package. Move existing tests before adding new tests.
- [ ] T013 Replace `tests/contract/upgrade_portal/test_upgrade_routes.py` with the same-name package. Move existing tests before adding new tests.
- [ ] T014 Replace `tests/e2e/upgrade_portal/test_run_controls.py` with the same-name package. Move existing tests into `test_existing.py`.
- [ ] T015 Create the integration and support packages with every exact child from the layouts in `plan.md`.
- [ ] T016 Write failing unit tests for override completeness, trap calls, credential scrub, unique ports, unique artifacts, and record ownership.
- [ ] T017 Write failing contract tests for override installation before route registration.
- [ ] T018 Implement the E2E override value classes in the new run-controls API package.
- [ ] T019 Edit `app/factory.py` surgically so it validates and installs overrides before blueprint registration.
- [ ] T020 Edit `app/wiring.py` surgically so it injects all action, access, cloud, audit, connector, and file seams.
- [ ] T021 Implement process-owned run, action, access, cloud, and audit stores under `tests/support/upgrade_portal_e2e/records/`.
- [ ] T022 Implement ArangoDB, Redis, and Mist connector traps under `tests/support/upgrade_portal_e2e/traps/`.
- [ ] T023 Implement the portal record file trap and zero-call assertions.
- [ ] T024 Implement credential scrub and explicit loopback port-1 sentinels.
- [ ] T025 Implement unique port, test identifier, record store, log, process file, and artifact allocation.
- [ ] T026 Reset cached storage and readiness state in `tests/e2e/upgrade_portal/conftest.py` before application construction.
- [ ] T027 Add `X-MistHelper-E2E-Run-ID` only when E2E overrides are active.
- [ ] T028 Run only the isolation unit and contract tests. Do not run a browser test.

**Checkpoint**: Every connector and file path fails closed before route
registration. Browser execution is now permitted.

## Phase 3: Shared Stale Policy

**Goal**: Give every page the same stale decision.

- [ ] T029 Write stale policy tests for boundaries, terminal states, offsets, malformed times, and future times.
- [ ] T030 Write stale view contracts for the history and run pages.
- [ ] T031 Implement `StaleAssessment` and `RunStalePolicy` in the compliant run-controls API package.
- [ ] T032 Edit `app/routes/review.py` to call the shared stale policy without adding a top-level helper.
- [ ] T033 Edit `app/routes/upgrade.py` to call the same stale policy without adding a top-level helper.
- [ ] T034 Add age and stale markup to the history and progress templates.
- [ ] T035 Add display-only age updates to `portal.js`.
- [ ] T036 Add accessible stale styles to `portal.css`.
- [ ] T037 Add browser stale tests and run them with all isolation traps active.

## Phase 4: Operational Store and Durable Actions

**Goal**: Create one durable action and one durable item for each accepted run.

- [ ] T038 Add the `upgradeRunActions` composite key strategy before action persistence.
- [ ] T039 Write action model tests for bulk and single-run source fields.
- [ ] T040 Write tests that prove reconciliation needs no preview and stores null preview fields.
- [ ] T041 Write tests for duplicate identifiers, durable actor scope, ordered placeholders, item claims, action leases, evidence fields, and evidence digests.
- [ ] T042 Implement action value records in `persistence/actions/models.py`.
- [ ] T043 Implement the ArangoDB action repository and actor-scoped result reads.
- [ ] T044 Implement action initialization with ordered `pending` items and durable unknown placeholders.
- [ ] T045 Implement an item claim with compare-and-swap from `pending` to `claimed`.
- [ ] T046 Implement outcome-only writes for `refused`, `failed`, and `unknown` items.
- [ ] T047 Implement atomic run mutation and successful outcome transactions.
- [ ] T048 Implement processing-to-complete finalization after all items become final.
- [ ] T049 Implement read-back verification before any success response.
- [ ] T050 Write unavailable-store tests that prove no SQLite, Redis, memory, or file fallback.
- [ ] T051 Write tests that prove API exports and data collection still use `DataExporter`.

**Checkpoint**: The operational store can initialize, claim, finalize, and read
an action. It cannot lose an item outcome.

## Phase 5: Replay, Crash Recovery, and Safe Resumption

**Goal**: Resume only work that has no possible prior mutation.

- [ ] T052 Write tests for same-key replay, request mismatch, active lease, lease expiry, and compare-and-swap takeover.
- [ ] T053 Write crash tests for a stop before claim, after claim, before transaction commit, and after transaction commit.
- [ ] T054 Implement actor-scoped replay in `persistence/actions/replay.py`.
- [ ] T055 Implement lease takeover with compare-and-swap.
- [ ] T056 Finalize each abandoned `claimed` item as `unknown` with `processing_interrupted`.
- [ ] T057 Resume only `pending` items and never repeat a `claimed` or `final` item.
- [ ] T058 Persist site blocks and finalize later blocked items as `not_processed_after_site_guard_loss`.
- [ ] T059 Finalize every remaining item and change the action to `complete`.
- [ ] T060 Run the replay and crash-recovery unit and integration tests.

## Phase 6: Authoritative Bulk Preview

**Goal**: Remove hidden selections before phrase entry.

- [ ] T061 Write preview tests for scope, hidden identifiers, duplicates, exact counts, expiry, and token binding.
- [ ] T062 Write preview API contracts.
- [ ] T063 Implement preview request and response values in the run-controls API package.
- [ ] T064 Implement `BulkActionPreviewService`.
- [ ] T065 Implement the preview route and signed token response.
- [ ] T066 Edit `app/factory.py` and `app/wiring.py` only as needed to register the new blueprint and dependencies.
- [ ] T067 Update `portal.js` to request preview, replace stored identifiers, and show server counts.
- [ ] T068 Update the history template for preview counts, removed identifiers, and phrase entry.
- [ ] T069 Add browser preview tests.

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
- [ ] T096 Compare persistent run, action, and audit counts with the T094 baseline immediately after the suite.
- [ ] T097 Stop the workflow and create an issue if any persistent count changed.

## Phase 10: Recovery Drill, Performance, and Traceability

**Goal**: Prove store recovery, fixed workloads, and complete requirement
coverage.

- [ ] T098 Restore the verified backup to an isolated ArangoDB target.
- [ ] T099 Verify run and action collection counts, keys, indexes, and sample records on the isolated target.
- [ ] T100 Record that action retention matches the lifetime of referenced run records and that no cleanup job exists.
- [ ] T101 Add the fixed 50-row history measurement.
- [ ] T102 Add the fixed 50-run no-cloud batch measurement.
- [ ] T103 Run both measurements with the warm-up and sample counts from `research.md`.
- [ ] T104 Add requirement identifiers to named tests and update the traceability matrix.
- [ ] T105 Review FR-001 through FR-076 against unit, contract, integration, browser, or manual evidence.
- [ ] T106 Re-run `checklists/requirements.md` and leave no unchecked item.

## Phase 11: Manifest, Quality Gates, and Documentation

**Goal**: Gate and stage every feature file without touching unrelated work.

- [ ] T107 Update `README.md` with the operator controls and governed deployment sequence.
- [ ] T108 Update `documentation/upgrade_capture_portal.md` with stale, preview, reconciliation, result, retention, and recovery behavior.
- [ ] T109 Add the feature entry to `CHANGELOG.md` with the required version format.
- [ ] T110 Update `feature-files.txt` before any path differs from the 79-path plan.
- [ ] T111 Build the changed-file set from the merge base, staged changes, unstaged changes, and untracked files.
- [ ] T112 Compare the changed-file set with `feature-files.txt`. Reject an unlisted feature path and exclude unrelated pre-existing untracked paths.
- [ ] T113 Run all applicable Python gates for each changed Python file in the manifest.
- [ ] T114 Run all applicable JavaScript and browser gates for each changed JavaScript file in the manifest.
- [ ] T115 Review each changed executable line for required comments and each meaningful action for required logs.
- [ ] T116 Run all targeted unit, contract, integration, and browser tests.
- [ ] T117 Run the full existing CI-equivalent local gates that apply to the manifest.
- [ ] T118 Fix a feature-caused failure and rerun its gate.
- [ ] T119 Create one GitHub issue before any repair of an unrelated failure. Record the issue URL.
- [ ] T120 Run the STE linter for every Markdown file in the feature package and the amended constitution.
- [ ] T121 Stage all feature files with `git add -A --pathspec-from-file=specs/2447-stale-bulk-run-controls/feature-files.txt`.
- [ ] T122 Compare the manifest with the staged diff and prove that every changed feature path is staged.

## Phase 12: Commit, Rebase, Pull Request, Merge, and Deployment

**Goal**: Merge and deploy the exact approved revision.

- [ ] T123 Commit the verified staged feature with the required UTC version title, `Closes #2447`, and co-author trailer.
- [ ] T124 Fetch `origin/main` and rebase `fix/2447-stale-bulk-run-controls` onto `origin/main`.
- [ ] T125 Rerun affected local gates after the rebase.
- [ ] T126 If conflict repair changes a feature file, rebuild the manifest, stage all feature paths, verify the staged diff, and commit the repair.
- [ ] T127 Push `fix/2447-stale-bulk-run-controls` with `--force-with-lease`. Do not push directly to `main`.
- [ ] T128 Open a pull request to `main` with the exact title from `plan.md`. Include `Closes #2447`, the spec link, changed-file summary, acceptance evidence, local gates, CI status, security results, UI evidence, deployment notes, rollback notes, and every applicable template item. Add `bug`, `web-portal`, and `in-progress`.
- [ ] T129 Wait for required human approval and every required pull request check, including CodeQL. Repair only feature-caused failures.
- [ ] T130 Add the `auto-merge` label only after T129 completes.
- [ ] T131 Confirm that the repository squash-merges the approved pull request to `main`.
- [ ] T132 Record the exact merged commit SHA from `origin/main`.
- [ ] T133 Wait for `.github/workflows/container-build.yml` on that merged commit.
- [ ] T134 Pull `latest` and verify its `org.opencontainers.image.revision` label equals the merged commit SHA.
- [ ] T135 Deploy the verified image with the existing Podman compose workflow.
- [ ] T136 Confirm container health and the portal health and readiness checks.
- [ ] T137 Record the optional Morrison House live check as skipped or authorized. Never run it automatically.

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

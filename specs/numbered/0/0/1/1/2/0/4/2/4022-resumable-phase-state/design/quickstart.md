# Quickstart: Persist resumable firmware phase state

This file lists the reproduction steps for the current behavior and the verification commands for the change. No command in this file ran during the record. Run each command from the repository root on the feature branch.

## Prerequisites

1. Run the bootstrap for the worktree as `.github/copilot-instructions.md` describes (RC-131).
2. Activate the environment with `.venv\Scripts\Activate.ps1` on Windows.
3. Do not start a container. The unit, contract, and end-to-end tests in this change use no container.

## Reproduce the current behavior on main

Run each command. The expected result describes main before the change.

1. Show that no test covers a 5xx reply from the single-site submitter. Expected: one refusal test passes. The fixture uses status 400 (RC-075).

   ```powershell
   python -m pytest tests/unit/upgrade_portal/test_wiring_submitter.py -k "cloud_refuses"
   ```

2. Show that a failed run releases the site lock today. Expected: the test passes (RC-072).

   ```powershell
   python -m pytest tests/unit/upgrade_portal/test_upgrade_driver.py -k "failed_run_releases_the_site_lock"
   ```

3. Show that observation treats a failed phase as ended. Expected: both tests pass (RC-073, RC-074).

   ```powershell
   python -m pytest tests/unit/upgrade_portal/test_org_cascade_walk.py -k "failed_phase_does_not_stop or resumed_walk_keeps"
   ```

4. Show the stop message that names no next step. Expected: the text appears once in the run status module (RC-009).

   ```powershell
   Select-String -Path src/interfaces/portals/upgrade_portal/runtime/runs.py -Pattern "The run stopped"
   ```

5. Show that the driver never imports the certainty rule. Expected: no match (RC-020).

   ```powershell
   Select-String -Path src/interfaces/portals/upgrade_portal/upgrade/driver.py -Pattern "SubmissionCertainty"
   ```

## Verify the change (single site)

1. Run the changed unit tests. Each new case in tasks.md passes.

   ```powershell
   python -m pytest tests/unit/upgrade_portal/test_wiring_submitter.py tests/unit/upgrade_portal/test_upgrade_driver.py tests/unit/upgrade_portal/test_org_cascade_walk.py tests/unit/upgrade_portal/test_runs/test_reconciliation.py
   ```

2. Run the changed contract tests. The start, retry, and resume routes refuse each case in TC-20 to TC-22.

   ```powershell
   python -m pytest tests/contract/upgrade_portal/test_retry_failed_run.py
   ```

3. Run the changed end-to-end test for the run page. The stopped page shows the phase, the reason, and the next step.

   ```powershell
   python -m pytest tests/e2e/upgrade_portal/test_run_controls/test_existing.py
   ```

4. Run the parity and contract tests for the changed text.

   ```powershell
   python -m pytest tests/unit/upgrade_portal/test_org_phase_list_parity.py tests/contract/upgrade_portal/test_org_phase_watch_contract.py
   ```

5. Run the guards for the SDK and the destructive menu.

   ```powershell
   python -m pytest tests/integration/test_mistapi_sdk_compatibility.py tests/guardrails/test_destructive_menu_docs.py
   ```

## Verify the change (multi-site, after issue #4021 merges)

```powershell
python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py tests/e2e/upgrade_portal/test_org_phase_cascade_journey.py
```

## Verify the documentation

```powershell
ste-linter --config .ste-linter.toml --min-score 80 documentation/upgrade_capture_portal.md README.md specs/1823-upgrade-capture-portal/contracts/site-lock.md changelog.d/issue-4022-resumable-phase-state.md
```

## Operator check on a stopped run

1. Start a single-site run in a test site. Stop the run at the settle wait.
2. Open the run page. Expected: the recovery card names the phase, the reason, and the next step.
3. Read the resume control. Expected: the control stays disabled until the word `RESUME` is typed exactly.
4. Read the start control for the same site. Expected: the start control refuses while the hold is active.

Warning: Run the operator check on a test site only. A resume on a production site writes firmware to production hardware.

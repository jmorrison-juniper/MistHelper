# Quickstart: Ordered Multi-Site Firmware Families

This guide gives the exact commands for reproduction and verification. Run each command from the repository root. Each command uses doubles only. No command starts a firmware operation or sends a live Mist request.

## 1. Prepare the Environment

Create the worktree environment with the repository bootstrap. Activate the environment on Windows.

```powershell
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

Do not set `MIST_API_TOKEN` or `MIST_APITOKEN` for these commands. The tests do not need a credential.

## 2. Reproduce the Current Defect

Run the two tests that lock the defect. Both tests pass on the current code. A pass proves the defect.

```powershell
python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py::test_partial_submission_keeps_each_child_and_blocks_replay -q
python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py::test_lock_loss_marks_current_and_untouched_children -q
```

Expected result: each command reports `1 passed`. The first test asserts that three non-AP device submissions continue after one refusal (research rows 30 and 31). The second test assumes that the access point child writes first (research row 32).

## 3. Verify the Change

Run the new order tests after the change.

```powershell
python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py -q -k "families_build or ssr_child or next_family_waits"
```

Run the stop tests after the change.

```powershell
python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py -q -k "refused or unknown_outcome or failed_family or unknown_family or empty_family or clients or stop_record or process_loss or stop_sentences"
```

Run the portal tests after the change.

```powershell
python -m pytest tests/unit/upgrade_portal/test_org_cascade_walk.py -q -k "stored_family or renew"
python -m pytest tests/contract/upgrade_portal/test_org_upgrade_routes.py -q -k returns_before
```

Run the affected files after the change.

```powershell
python -m pytest tests/contract/upgrade_portal tests/unit/prod_readiness/operations/execution/firmware/upgraders -q
```

Expected result for each command: zero failed tests. A failed test names the rule that the change broke.

## 4. Check the Family Order Without a Cloud Call

The aggregate tests build the children with stand-ins. Each stand-in records one call and returns one fixed reply. The test asserts the order of the recorded calls. No command reads a live Mist endpoint.

## 5. Run the Local Gates

Run the gates in the order of `tasks.md`, task T-LOCAL-GATES. Each gate prints its expected result from the local gates table in `.github/copilot-instructions.md`.

The safe sweep `python MistHelper.py --test` runs only the safe menu operations. It skips the Mist API checks when no credential exists.

Warning: a destructive menu, including menu 239, changes production firmware. Do not run any destructive menu for this change.

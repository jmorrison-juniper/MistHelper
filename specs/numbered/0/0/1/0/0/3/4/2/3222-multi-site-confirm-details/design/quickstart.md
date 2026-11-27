# Quickstart: Multi-Site Confirm Page Plan Detail

This file gives the exact steps to reproduce the defect and the exact commands to verify the change. Run each command in the worktree root. The worktree branch is `fix/3222-multi-site-confirm-details`.

## Prerequisites

Install Python 3.15.2 and create the environment. The repository instructions give these commands.

```powershell
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

## Reproduce the Defect

1. Run the journey test. Its expected-failure marker hides the defect at this stage.

```powershell
python -m pytest tests\e2e\upgrade_portal\journeys\test_upj_multisite_journeys.py
```

Expected result before the change: the test that carries the marker reports as an expected failure.

2. Run the contract tests for the confirmation route. The saved plan renders without device rows.

```powershell
python -m pytest tests\contract\upgrade_portal\test_org_upgrade_routes.py
```

Expected result before the change: the existing confirmation tests pass. No device table exists in the HTML.

3. Optional visual check with a stand-in cloud. Follow the operator path from the issue comment, step by step.

- Open `/select/mode`. Choose the multi-site mode. Continue.
- Select two sites. Continue.
- Choose a version for each family. Choose the canary strategy. Enter the phases `10,100`. Enter the failure limit `0`.
- Choose review. The confirm page opens.

Warning: typing `CONFIRM` starts a firmware write on each selected device. Stop at the confirm page. Do not type `CONFIRM` against a production tenant.

## Verify Each Change

Run each command after the matching task. Each command names one changed file.

```powershell
python -m pytest tests\unit\upgrade_portal\test_org_child_controls.py
python -m pytest tests\contract\upgrade_portal\test_org_upgrade_routes.py
python -m pytest tests\contract\upgrade_portal\test_issue_3390_confirm_strategy_wording.py
python -m pytest tests\contract\upgrade_portal\test_issue_3452_confirm_scope_text.py
python -m pytest tests\e2e\upgrade_portal\test_org_upgrade_flow.py
python -m pytest tests\e2e\upgrade_portal\journeys\test_upj_multisite_journeys.py
python -m pytest tests\contract\upgrade_portal\test_journey_parity_matrix.py
ste-linter --config .ste-linter.toml --min-score 80 documentation/upgrade_capture_portal.md
ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-3222-multi-site-confirm-details.md
```

Expected results after the change:

- The unit file reports eight passed tests. Tests U1 to U8 are the new tests.
- The route contract file reports the six new tests C1 to C6 as passed, and the existing tests pass.
- The wording helper file passes without changes to its assertions.
- The scope text file passes with the same warning text and pre-check text as before.
- The browser flow file reports test E1 as passed.
- The journey file reports test J1 as passed, and it carries no expected-failure marker.
- The parity contract file passes after task T012.
- Each STE command reports a score of 80 or higher.

## Full Local Gates

Run each gate in the section "Local Gates for This Change" of `plan.md`. Record the actual output in the pull request. The repository measured 1,179 and 366 seconds for the two shards on 2026-09-17.

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

Expected result: each shard prints one summary line with zero failures.

## Confirm the Safety Refusal

Use the contract test C3. It posts an incomplete saved plan and checks the response.

```powershell
python -m pytest tests\contract\upgrade_portal\test_org_upgrade_routes.py -k incomplete
```

Expected result: the response has HTTP status 409. The code is `org_upgrade_plan_incomplete`. The stand-in upgrade service receives no call.

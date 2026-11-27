# Quickstart: Reproduce and Verify Issue 3394

These steps reproduce the defect and verify the fix. Run them from a worktree of the branch `fix/3394-multi-site-empty-version`. The worktree starts from `main`. The bootstrap steps follow the section "Language and environment" in `.github/copilot-instructions.md` (RC87 covers the Python 3.15 requirement).

## Preconditions

1. Create the worktree from `main`: `git worktree add ..\MistHelper-fix-3394 -b fix/3394-multi-site-empty-version main`.
2. Change to the worktree folder: `cd ..\MistHelper-fix-3394`.
3. Create the environment: `uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py`.
4. Activate the environment: `.venv\Scripts\Activate.ps1`.

## Reproduce the Defect (Before the Fix)

1. Run the contract tests for the three failing cases: `python -m pytest tests/contract/upgrade_portal/test_org_upgrade_routes.py -k "checked_switch_without_target_version or explicit_targets or narrowed_retry_view"`.
2. Expect three failures. Each save answers HTTP 200, not HTTP 400. The retry case raises no `ValueError`.
3. Run the browser test: `python -m pytest tests/e2e/upgrade_portal/test_org_upgrade_flow.py -k checked_switch_without_target`.
4. Expect a failure. The confirmation page loads, and no refusal text appears.

## Verify the Fix (After the Change)

1. Run the full contract module: `python -m pytest tests/contract/upgrade_portal/test_org_upgrade_routes.py`. All tests pass.
2. Run the browser test: `python -m pytest tests/e2e/upgrade_portal/test_org_upgrade_flow.py -k checked_switch_without_target`. The test passes after Playwright and Chromium are installed.
3. Run the changelog guard: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`. The test passes.
4. Run the lint gate: `python -m ruff check .`. The output is `All checks passed`.
5. Run the format gate: `python -m black --check .`. No file needs a change.
6. Run the symbol gate: `symbol-diff --base origin/main src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`. The output is `no module-level name changed`, with exit code 0.
7. Run the docstring gate with the value of `INTERROGATE_PATHS` from `.github/workflows/ci.yml`: `interrogate $INTERROGATE_PATHS --fail-under 90`.

## Check the Message

The exact refusal text is: `Choose the switch target version, or clear Switches.`

Verify the text in the response body with the contract test at `tests/contract/upgrade_portal/test_org_upgrade_routes.py:841-842` (RC102, RC103).

## Manual Operator Path

1. Open the multi-site options page for two sites. Each site holds one access point and one switch.
2. Check "Access points" and "Switches".
3. Choose a target version for one access point. Leave each switch at "Do not upgrade this device".
4. Choose Review.
5. Expect the flash message `Choose the switch target version, or clear Switches.` The access point target version keeps its value.

## Remove Temporary Items After the Merge

1. Remove the worktree: `git worktree remove ..\MistHelper-fix-3394`.
2. Delete the local branch: `git branch -D fix/3394-multi-site-empty-version`.

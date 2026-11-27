# Quickstart: Site read refusal

This guide gives the exact steps to reproduce the original fault and to verify the repair. It starts no container and makes no live Mist call. Run each command from the root of a worktree of `main`. Do not run `git checkout` in a shared checkout.

## Prerequisites

1. Create a worktree at the head of `main`. Use a worktree for each branch, as `AGENTS.md` requires.
2. Create the environment in a new worktree with `uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py`.
3. Activate the environment with `.venv\Scripts\Activate.ps1`.
4. For the browser test, prepare the browser stack that `documentation/development-setup.md` section "Run the browser tests" describes (RC-62).

## Reproduce the original fault

Use the base commit of PR 4413, `064cec47524fa6b3e820bddd4525d01a791cbecc` (RC-05).

1. Create a second worktree at that commit.
2. Copy `tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py` from `main` into the second worktree. Do not commit the copy.
3. Run `python -m pytest tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py`.
4. Expected from the base code: the save and page cases fail. The base code does not catch `RequestException`, so the response is a 500 or an unhandled exception. The exact result depends on the Flask testing setting. This expectation comes from the source and was not run in this record.

## Verify the repair on main

1. Run `python -m pytest tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py`. The file holds 10 cases: 3 for the save, 1 for the replacement, 4 for the page reads, 1 for the recovery, and 1 for the empty selection.
2. Run `python -m pytest tests/contract/upgrade_portal/test_org_site_records_routes.py tests/contract/upgrade_portal/test_org_upgrade_routes.py`. These regression cases keep the 404, 400, and device family answers.
3. Run `python -m pytest tests/e2e/upgrade_portal/test_org_upgrade_flow.py -k cloud_read_refusal`. The filter selects the one browser case of issue 3393 (`test_org_upgrade_flow.py` line 50).

## Verify the production path (after T008)

1. Run `python -m pytest tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py`. The three new cases of T008 run with the rest of the module.
2. Read the observed status and code of each case in the test output. Record the values in `design/contracts/refusal.md`.
3. If the save answers something other than 400 `options_invalid`, or a page answers something other than 503 `site_list_incomplete`, revisit D-10 and D-11 in `design/research.md`.

## Gates

Run each gate of the gate map in `plan.md` section "Gate Map for T-LOCAL-GATES". Start with the lint and the format gates:

1. `python -m ruff check .`
2. `python -m black --check .`

## Containers

No container is needed for these steps. If a container becomes necessary, follow `documentation/container-deployment.md` section "Test and debug containers" (RC-63). That section sets the compose group, the name pattern, and the removal steps.

## Clean up

Remove the second worktree after the reproduction. Use `git worktree remove <path>` from the main checkout.

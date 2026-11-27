# Quickstart: Batch target site snapshot

This guide shows the exact steps to reproduce the defect and to verify the fix. Every test uses a fake Mist harness. No live Mist credential is needed.

## Prerequisites

1. Create the Python environment as `.github/copilot-instructions.md` describes in "Language and environment". Run `uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py`, then activate `.venv`.
2. Use a worktree for branch `fix/4923-batch-site-snapshot`. Do not run `git checkout` in a shared checkout.

## Scenario 1: Reproduce the defect

Apply only the test changes from tasks T003 and T004. Keep the code unchanged.

1. Run the integration test:

   `python -m pytest tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py -q`

   Expected result: the read-order test fails. The organization read list has more than three entries, because organizations A and B are read again for their site checks.

2. Run the routing test:

   `python -m pytest tests/unit/ex_hardware_inventory/run/test_hardware_routing.py -q`

   Expected result: the read-count assertion for organization B fails. Organization B shows two reads.

## Scenario 2: Verify the unit behavior

After tasks T005 to T007, run the batch target unit tests:

`python -m pytest tests/unit/websocket_streams/web/test_ws_web_services.py -q`

Expected result: the seven new tests and the existing foreign-site test pass. The existing foreign-site test still asserts that no device read occurs for a foreign site.

## Scenario 3: Verify the MSP read count

Run the integration test again:

`python -m pytest tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py -q`

Expected result: the read-order test passes. The organization read list equals `[ORG_A, ORG_B, ORG_C]`.

## Scenario 4: Verify the failure path

The unit test `test_failed_refresh_clears_the_snapshot_and_raises` covers a failed organization read after the lifetime ends. Run it with the unit file:

`python -m pytest tests/unit/websocket_streams/web/test_ws_web_services.py -q`

Expected result: the test shows that the check raises the picker error and does not return rows from the earlier read.

## Scenario 5: Verify the guards

Run the guard tests, which include the changelog fragment policy:

`python -m pytest tests/guardrails -q`

Expected result: every guard passes. The changelog guard accepts `changelog.d/issue-4923-batch-site-snapshot.md`.

## Verification commands

| Purpose | Command |
| - | - |
| Unit behavior | `python -m pytest tests/unit/websocket_streams/web/test_ws_web_services.py -q` |
| Routing read count | `python -m pytest tests/unit/ex_hardware_inventory/run/test_hardware_routing.py -q` |
| MSP read order | `python -m pytest tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py -q` |
| Changelog guard | `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q` |
| Type check | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` |

## Live check

No live check is required for this change. The live read count after merge is an open item (U-1 in `design/research.md`). The orchestrator decides whether to run it.

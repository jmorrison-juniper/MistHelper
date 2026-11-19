# Validation and execution guide

## Start conditions

Use this record as the command-scoped feature directory.
Do not change another owner's planning record or feature pointer.
Confirm the worktree, current PR head, source revision, and shared-file ownership before implementation.
Read the task dependencies and evidence ledger first.

If PowerShell becomes available, run prerequisite and setup checks with this explicit feature directory.
Then run Spec Kit consistency analysis without changing the documents during analysis.
Until then, report manual validation separately from command execution.

## Skill-guided checks without PowerShell

Read the spec, plan, tasks, constitution, and all returned design files directly.
Map each FR/SC to task IDs and identify missing or contradictory dependencies.
Check required artifacts exist, task IDs are unique, paths are explicit, and new directories remain bounded.
Run installed task-audit, Markdown-link, and STE tools with examined counts.
Report unresolved evidence separately from document consistency.
Do not change the feature pointer or add a replacement setup script.
This process uses the local skills but does not reproduce every PowerShell prerequisite check.

## Existing regression commands

Use the worktree environment:

```bash
.venv/bin/python -m pytest tests/unit/wan_performance tests/e2e/web_portal/test_wan_performance_offline.py tests/e2e/web_portal/test_wan_performance_live.py tests/guardrails/test_e2e_shard_partition.py tests/e2e/web_portal/test_portal_smoke.py tests/integration/web_portal/cisco_config_converter/test_routes.py tests/unit/websocket_streams/web/test_ws_blueprint_routes.py
.venv/bin/python -m ruff check src/interfaces/wan_performance tests/unit/wan_performance
.venv/bin/python -m black --check src/interfaces/wan_performance tests/unit/wan_performance
git diff --check
```

Expected result: all selected tests and gates pass.
These commands do not prove full source parity.
Run new tests from each task pair before its production changes.
Use all applicable gates and the exact test-quality procedure in repository instructions before publication.

## Four-journey acceptance

1. Open the synthetic overview and verify its origin label.
2. Select a gateway and verify preserved site and gateway scope.
3. Open its WAN port and verify encoded identity and metric units.
4. Return to the gateway and open a VPN peer.
5. Return to the overview and verify filters and browser-back behavior.

Repeat with independently authored normal, empty, stale, partial-history, and error scenarios.
Repeat mocked live journeys with authorized and denied sessions.
Assert no production request, secret disclosure, unexpected storage write, or unbounded refresh.
Compare every inventoried control and layout region, not only the five navigation steps.

## Completion evidence

Record exact commands, exit codes, examined counts, source revision, destination revision, and retained artifacts.
Run source-to-task and source-to-test coverage checks.
A missing source contract, rights decision, or accepted deviation remains a blocker.
Keep PR #4208 draft until the owner accepts the complete evidence.
Record recovery progress on issue #4200. Do not create another issue for the same subject.

## Original-application cycle prerequisites

Verify a rights grant for pinned source execution and the permitted evidence scope before any source import or capture.
Use [the exploration matrix](contracts/parity.md#original-application-exploration-plan) to cover every accessible control.
Do not use source fixture data, existing `.env` files, production clients, or default persistent volumes.
Prepare dependencies separately from execution. Verify the execution environment blocks outbound traffic before starting any source process.
Run the browser inside that isolated environment when a host browser would require exposing an additional network path.
Record a successful local connectivity check and a failed outbound connectivity check before the application cycle.
Use independent synthetic scenarios and record unimplemented controls separately from working controls.
Run each source test module, then each browser journey, without treating skipped tests as passed.
Keep exact test output, application errors, interaction notes, and permitted captures in the session artifact directory.
Stop each started process and verify exact temporary-resource cleanup before reporting completion.
If rights or isolation cannot be verified, record the missing prerequisite and do not claim source execution.

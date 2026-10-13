# Validation Guide: Mist WAN Performance

## Current Planning Change

This branch contains documents only.
Do not start the implementation workflow or run future collection commands.
Read [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), and [the contract](contracts/wan-performance.md).
Use [tasks.md](tasks.md) for future execution order.
Read [analysis.md](analysis.md) for the final consistency decision.

If the worktree lacks its validation environment, run `python3 scripts/bootstrap_worktree.py`.
Then run `source .venv/bin/activate` on macOS or Linux.
Windows uses `.venv\Scripts\Activate.ps1`.

Run these documentation commands from the repository root:

```bash
ste-linter --config .ste-linter.toml --min-score 80 specs/live/20261013-182629-mist-wan-performance
markdown-link-check specs/live/20261013-182629-mist-wan-performance
speckit-task-audit --root specs/live/20261013-182629-mist-wan-performance
git diff --check
```

Expected results: Every Markdown file scores at least 80, local links resolve, no task claims delivered implementation, and whitespace checks pass.
Stage the dedicated feature directory before the link check because that tool reads tracked Markdown.
The final PR contains only this directory. Temporary feature selection must not enter the commit.
Product tests and database operations are not applicable to this documentation-only change.

## Future Implementation Prerequisites

Obtain written implementation approval.
Complete T001 through T010 with evidence before product work.
Confirm the current API session, selected application store, approved metric contracts, and shared request-admission behavior.
Never configure Snowflake or a second application database.
Use controlled responses and independently authored fixtures.

## Future Test Commands

These paths are planned. The files do not exist in this planning PR.
Run them only after the corresponding implementation tasks create them:

```bash
python -m pytest tests/unit/wan_performance tests/contract/wan_performance tests/integration/wan_performance
python -m pytest tests/e2e/wan_performance
python -m pytest tests/integration/test_mistapi_sdk_compatibility.py
```

Also run the applicable quality gates from [repository instructions](../../../.github/copilot-instructions.md).
Run the committed-test quality procedure before pushing future tests.

## Future End-to-End Scenarios

1. Open WAN Performance from the current portal. Verify overview metrics and shared navigation.
2. Select a gateway. Verify its site identity, health, ports, and peer paths.
3. Select `ge-0/0/1`. Verify exact decoding, gateway query context, and receive/transmit units.
4. Open peer `11:22:33:44:55:66`. Verify loss, latency, jitter, tunnel separation, and return navigation.
5. Select hourly, daily, weekly, and monthly records. Verify UTC boundaries, incomplete coverage, and duplicate upserts.
6. Simulate HTTP failures, cache loss, storage loss, quota exhaustion, and competing workers. Verify explicit states and bounded requests.
7. Run synthetic mode without service connections. Verify every page identifies synthetic history.
8. Compare four screens at 1440 by 1100 pixels and a 390-pixel viewport. Retain failed-flow screenshots or traces.

No scenario uses production credentials.
Use existing fixtures and scoped local test resources.
Do not start a separate application service, Redis service, public port, or Compose group.

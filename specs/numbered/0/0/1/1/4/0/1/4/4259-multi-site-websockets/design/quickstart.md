# Validation Guide: Multi-site WebSocket operations

**Issue**: #4259

## Scope

This guide describes validation after implementation.
The new routes and controls do not exist because this work creates planning documents only.
Do not interpret this guide as a completed test report.

Use [batch-api.md](contracts/batch-api.md) for route details.
Use [discovery.md](contracts/discovery.md) for SDK fixtures.
Use [output-and-ui.md](contracts/output-and-ui.md) for file and UI checks.
Use [data-model.md](data-model.md) for identities and state transitions.

## 1. Prerequisites

Use an isolated worktree and Python 3.13 or newer.
Run commands from the repository root.
Use mocked Mist credentials and SDK responses for automated checks.
Do not copy a production token into a command, fixture, log, or artifact.

If the environment is absent, use the existing bootstrap command:

```bash
python3 scripts/bootstrap_worktree.py
source .venv/bin/activate
```

Use a temporary directory for mocked output.
Do not create product output folders with test names under `data/`.
Keep optional browser traces under ignored `test-artifacts/`.

Do not change `.specify/feature.json`.
Do not use `tests/unit/websocket_streams/web/test_ws_blueprint_routes.py`.
PR #4260 owns the pointer.
PR #4208 owns the route test file.

## 2. Validate Planning Documents

Run `git diff --check`.
Inspect the explicit issue-owned file list before staging any later change.
Verify every local Markdown link.
Use the repository STE linter with a minimum score of 80.

```bash
git diff --check
ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/1/4/0/1/4/4259-multi-site-websockets/*.md specs/numbered/0/0/1/1/4/0/1/4/4259-multi-site-websockets/design/*.md specs/numbered/0/0/1/1/4/0/1/4/4259-multi-site-websockets/design/contracts/*.md
```

Expected result: no whitespace error, no broken local link, and every examined file scores at least 80.
If a tool is unavailable, report the missing tool.
Do not claim a skipped gate passed.

## 3. Prove the Existing Transport Exception

After implementation prerequisites are available, run:

```bash
python -m pytest tests/contract/websocket_streams/test_ws_sdk_contract.py -q
python -m pytest tests/unit/websocket_streams/live/transport tests/unit/websocket_streams/live/runners -q
```

Expected results:

- The SDK first-output proof demonstrates the existing limitation.
- The owned transport retains the early output.
- The split-control proof demonstrates intact owned output.
- Private session authentication, cloud endpoint, cookie, and TLS contracts remain valid.
- Shell input waits for initial output.
- Closing, stopping, and delayed terminal completion preserve target outcomes.

Stop implementation approval if either SDK insufficiency proof is absent or fails.

## 4. Validate Complete Discovery

Extend the current intake tests without adding a child to a full directory.
Then run:

```bash
python -m pytest tests/unit/websocket_streams/intake -q
python -m pytest tests/contract/websocket_streams -q
```

Use two site pages, two device pages, and two wired-client pages.
Include mixed device families, duplicate identities, and missing associations.
Run once with a validated page limit of 250.
Run once with the default page limit of 1000.

Expected results:

- Every applicable SDK call receives the configured limit.
- Device calls include `type="all"`.
- Every later page uses `mistapi.get_next` with the authenticated session.
- Every page status and response shape is checked before the service accepts its records.
- Wired-client search follows every documented SDK cursor and preserves device association.
- Every eligible identity appears exactly once.
- Cross-site clients remain distinct.
- A failed later page returns an error instead of a complete preview.
- A complete empty response remains distinct from an upstream failure.
- A repeated unchanged preview reuses complete reads.

## 5. Validate Admission and Target Execution

Use Flask test-client fixtures through the existing service injection point.
Place route and service tests in the unowned existing service test module.

```bash
python -m pytest tests/unit/websocket_streams/web/test_ws_web_services.py -q
python -m pytest tests/unit/websocket_streams/live/sessions -q
```

Create a preview with at least six deterministic targets.
Use one immediate success, one failure, one delayed success, and three queued targets.
Set concurrency to two.
Start the batch through `POST /api/websockets/batches`.
Read its summary and target list.
Poll the existing session messages route.

Expected results:

- The public list contains one batch parent.
- Active target work never exceeds two or the shared transport budget.
- Every output and error has the full target identity.
- One failure does not discard successful output.
- Counts always sum to the admitted target count.
- Each target receives one terminal outcome.
- A foreign site, unknown operation, locked utility, or invalid parameter starts no runner.

Change the target set, command list, or parameters after preview.
Expected result: the old confirmation cannot authorize the changed work.
Try the same consumed preview again.
Expected result: `409` with `preview_consumed`, with no duplicate execution.

## 6. Validate Cancellation and Existing Limits

Stop a batch while two targets run and other targets wait.
Use the existing parent stop endpoint.
Repeat the stop request.

Expected results:

- The response uses `202`.
- No queued target starts after the cancellation boundary.
- Every active runner receives a stop request.
- Previously completed target results remain available.
- Stopped targets retain their identities.
- Parent idle and maximum lifetime stops use the same behavior.
- Transport permits return after completion, failure, or cancellation.

Fill the public session limit with mocked Single Site sessions.
Expected result: batch admission returns `429` without starting a target.
Run two batches with shared capacity.
Expected result: combined active target work respects the existing transport budget.

## 7. Validate Finite Shell Batches

Use mock shell transports and a locked-then-unlocked shell feature flag.
Select two explicit devices.
Supply `show route` and `show arp` as the finite ordered command list.
Enter the preview phrase `RUN 2 TARGETS`.

Expected results:

- A locked shell starts no trigger.
- Confirmation binds to the exact operation, commands, and device set.
- Each selected device receives each command once and in order.
- The collector captures the normalized prompt before it sends the first command.
- Each command completes only after the same prompt returns and output stays quiet for two seconds.
- The collector preserves partial output and skips later commands after either 30-second deadline.
- A missing device exit status does not imply command success.
- Each shell closes after final collection or a terminal error.
- Output remains separate per device and command index.
- Interactive input and resize return `409` for a batch.

Run a separate Single Site shell fixture.
Expected result: its interactive input, paste, resize, history, and stop remain unchanged.
Do not test live device changes.

## 8. Validate Saved Files and Cleanup

Use a temporary output root with the same containment rules as `data/`.
Repeat the mixed-outcome batch for combined, grouped, and both modes.
Exercise each permitted grouping.

```bash
python -m pytest tests/unit/websocket_streams/web/test_ws_output_boundaries.py tests/unit/websocket_streams/web/test_ws_secret_guard.py -q
```

Expected results:

- Saved records retain parent sequence and target identity.
- Grouped copies match combined record keys.
- Empty and failed targets appear in terminal outcome metadata.
- Grouped-only downloads merge records without creating a permanent combined file.
- Downloads include a partial flag when collection is incomplete.
- Unsafe labels, traversal, symlinks, and reserved names cannot change the output boundary.
- Split tokens and shell secrets appear in no public output or log.
- A full disk or quota stops work and reports `output_failed`.

Advance the mocked clock beyond 600 seconds.
Create enough ended sessions to exceed five.
Delete a retained ended session.
Simulate restart cleanup.

Expected result: each applicable cleanup removes only its session-owned files.
Simulate an active download and a failed file removal.
Expected result: bounded pinning and cleanup retry preserve truthful status.

## 9. Validate the Browser

Add checks to existing browser test modules.
Do not add a direct child to a full browser folder.

```bash
python -m pytest tests/e2e/websockets_tab -q
```

Expected results:

- Single Site is the initial tab.
- Existing repeatable channel selections accept 10 paths and reject 11.
- Each tab retains independent form state.
- Changing tabs does not stop a session.
- Multi Site shows catalog-derived fields and complete target identities.
- Stale discovery responses do not replace current selections.
- The preview shows exact commands and targets before confirmation.
- Progress retains success and failure rows.
- The stop and download controls operate on the parent session.
- Keyboard navigation and stable test IDs support repeatable checks.

Retain a screenshot or trace when a browser flow fails.

## 10. Run Implementation Gates

After an authorized code change, run each applicable repository gate.
Include compile, Ruff, Black, types, tests, coverage, test quality, complexity, security, and documentation checks.
Run the structure guard before adding any module.
Use the current repository commands instead of a copied CI configuration.
Do not lower a threshold or suppress a real finding.

This planning task does not run the code pipeline, create a commit, or publish a GitHub update.
Report exact commands and results during later implementation.

## Optional Live Validation

Live validation requires separate approval and a configured development portal.
Use an existing read-only operation or the approved finite read-only command list.
The specification permits the Morrison House Oregon site for read-only checks.
Do not change Mist cloud configuration or device state.
Do not create a container or publish a production port for this planning task.

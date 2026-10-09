# Quickstart: Validate Operation Stream Recovery

## Purpose

Use this guide during implementation.
It proves the #4027 and #4032 browser contracts without a Mist credential.

## Prerequisites

Build the worktree environment one time:

```powershell
python scripts\bootstrap_worktree.py
```

Use the worktree Python environment for each command.
Do not change the server operation service or output scan service.

## Required File Check

Before each commit, inspect the changed files:

```powershell
git status --short
git diff --name-only
```

The product and browser test diff can contain only:

```text
web_portal/static/js/operations.js
tests/e2e/web_portal/test_operation_stream_recovery.py
changelog.d/issue-4027-operation-stream-recovery.md
changelog.d/issue-4032-output-replay-deduplication.md
```

The feature planning records can also change.

Confirm that these excluded files remain unchanged:

```text
web_portal/services/operation.py
web_portal/services/output_scan.py
MistHelper.py
tests/e2e/web_portal/test_operations_panel_workflow.py
```

## Commit 1: Prove the #4027 Failure

Add only the #4027 cases to the dedicated Playwright module.
Keep the controlled event stream open.
Do not call its error handler.

Run:

```powershell
python -m pytest tests\e2e\web_portal\test_operation_stream_recovery.py -q -s
```

Expected result before the repair:

- The browser remains in `Running`.
- The failure output reports the status checks it examined.
- The stream error call count is zero.

Commit the failing proof separately:

```text
test(web-portal): reproduce operation stream recovery failure
```

## Commit 2: Repair #4027

Implement the five-second status check in `operations.js`.
Keep one request active.
Add run identity guards.
Clear the timer and close the stream at each terminal transition.

Run the same command.

Expected result after the repair:

- The running response keeps the stream active.
- The completed response reaches `Complete`.
- The failed response reaches `Error`.
- No stream error or manual reconnect occurs.
- A late running result cannot replace a terminal result.

Commit the repair separately:

```text
fix(web-portal): recover terminal operation status
```

Include `changelog.d/issue-4027-operation-stream-recovery.md`.

## Commit 3: Prove the #4032 Failure

Add only the #4032 cases to the same dedicated module.
Send one exact path through status replay and terminal stream replay.
Send two distinct paths with the same base file name.
Send a terminal empty set after a loading presentation.

Run:

```powershell
python -m pytest tests\e2e\web_portal\test_operation_stream_recovery.py -q -s
```

Expected result before the repair:

- The repeated identity creates two links or two preview loads.
- The terminal empty set leaves stale output loading state.
- The failure output reports each measured replay count.

Commit the failing proof separately:

```text
test(web-portal): reproduce output replay duplication
```

## Commit 4: Repair #4032

Use `run_id` and each exact server path for identity.
Replace changed output sets.
Skip repeated identical sets.
Apply a terminal empty set to the output presentation.

Run the dedicated module again.

Expected result after the repair:

- One repeated identity creates one link.
- One repeated identity starts one preview load.
- Two distinct exact paths remain visible.
- The same exact path can belong to two runs.
- A terminal empty set clears stale loading state.
- The terminal message remains visible.

Commit the repair separately:

```text
fix(web-portal): make output replay idempotent
```

Include `changelog.d/issue-4032-output-replay-deduplication.md`.

## Final Focused Gates

Run:

```powershell
python -m ruff check tests\e2e\web_portal\test_operation_stream_recovery.py
python -m black --check tests\e2e\web_portal\test_operation_stream_recovery.py
python -m pytest tests\e2e\web_portal\test_operation_stream_recovery.py -q -s
python -m pytest tests\guardrails\test_changelog_fragment_policy.py -q
```

Run the required test quality preflight.
Then run the changed-test gate against `origin/main`.

## Final Diff Check

Run:

```powershell
git diff --name-only origin/main...HEAD
```

Verify that no excluded file appears.
Verify that each issue has its own changelog fragment.
Verify that the two failing tests and two repairs remain separate commits.

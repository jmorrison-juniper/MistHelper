# Quickstart: WebSocket Audit Compatibility

Use these steps after implementation to validate the change. They use the isolated browser and synthetic responses. They do not require a Mist credential, a live portal, or a running service.

## Prerequisites

- Create the repository virtual environment with `python3 scripts/bootstrap_worktree.py`.
- Use the installed Playwright browser from the bootstrap.
- Keep the default audit mode, `isolated`.

## Validate the request scope

Run the isolated inventory tests:

```text
python -m pytest tests/e2e/websockets_tab/dialog_audit/test_inventory.py
```

The tests must allow the exact client GET only after valid site and same-site device responses. They must deny missing, malformed, unrelated, cross-site, encoded, redirected, queried, or non-GET requests before transmission.

The approved device response supplies device UUIDs only for its authorized site.
An empty response remains valid no-data evidence and grants no client access.
Client response rows cannot authorize device reads.
The SDK check reads nine installed GET implementations without invoking them.

## Validate dialog cancellation evidence

Run the isolated dialog tests:

```text
python -m pytest tests/e2e/websockets_tab/dialog_audit/test_dialogs.py
```

The audit record must report zero, one, or multiple visible exact-name Cancel controls accurately. A hidden control must not count. A zero count must include the `operation-cancel` finding.

The count uses `ws-cancel-selection-button` inside `#wsStartForm`.
The `cancel` field and the utility review use the same measurement.

## Run combined targeted checks

Run the two isolated test modules together, then run the compile, Ruff, and Black commands listed in [plan.md](plan.md).

Do not select `test_live.py` or pass a live audit mode. Do not start, submit, or operate a WebSocket action.

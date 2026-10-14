# Validation: Backup restoration

## Prerequisites

Use the worktree `.venv` created by `python3 scripts/bootstrap_worktree.py`.
Use fixture settings and mocked SDK transport.
Do not provide production credentials.

## Commands

Run the feature unit, integration, contract, and graphical tests together.
Record exact commands and results in the acceptance report after execution.
Run related metadata, endpoint catalog, private output, menu, and structural guards.
Run the committed-test quality procedure before push.
Run the full analyzer before push.

## Expected outcomes

Every invalid or stale preview sends zero writes.
Every current target has a verified recovery record before the first write.
The exact writable restoration body excludes server-managed fields.
The first failed write or saved-state check stops later targets.
Chromium completes selection, preview, confirmation, completion, and partial reporting without secret values.
Original input bundle bytes remain unchanged.

## Acceptance limits

Automated offline evidence does not prove a production restoration or actual user approval.
Keep any such acceptance explicitly unverified.

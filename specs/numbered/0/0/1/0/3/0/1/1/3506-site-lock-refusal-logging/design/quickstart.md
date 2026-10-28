# Quickstart: Site Lock Refusal Logging

## Prerequisites

Use the project virtual environment created by `python3 scripts/bootstrap_worktree.py`.

## Validate the lock behavior

Run the focused contract and unit tests:

```sh
python -m pytest tests/contract/upgrade_portal/test_lock.py tests/unit/upgrade_portal/test_lock.py -q
```

Expected result: all tests pass. The tests use fake lock stores and make no Mist Cloud request.

## Validate the refusal log guard

Run the structural guard:

```sh
python -m pytest tests/guardrails/test_site_lock_refusal_logging.py -q
```

Expected result: the guard reports 10 functions and 18 refusal exits, with zero silent exits. Its failure proof rejects source that lacks a required log call.

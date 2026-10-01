# Validation Guide: Declared ArangoDB indexes

## Prepare the owned environment

If the worktree lacks runtime packages, run the repository bootstrap command.

```bash
rtk proxy python3.13 scripts/bootstrap_worktree.py
```

Use the worktree's `.venv/bin/python` for every local Python check.

## Run the focused tests

```bash
rtk proxy .venv/bin/python -m pytest tests/unit/arango_indexes tests/contract/test_arango_declared_indexes.py --no-cov
```

The tests must compare exact index requests, failure and retry counts, concurrent writes, and unchanged document imports.
They must use the actual writer path rather than only the index manager.

## Run adjacent database tests

```bash
rtk proxy .venv/bin/python -m pytest tests/unit/test_arango_writer.py tests/unit/test_router.py tests/unit/db tests/unit/refactors/test_sqlite_database_writer.py --no-cov
```

## Run an isolated integration test

The session-only compose overlay defines the test service and its issue-specific profile.
The service owns its named volume and network.
It publishes only a test port on `127.0.0.1`.

Warning: a production database connection can create indexes during a normal write.
Do not use a production URL for this test.

Set `MISTHELPER_ISSUE3309_ARANGO_URL` to the explicitly owned test service URL.
The integration test rejects production hosts and ports.

```bash
rtk proxy .venv/bin/python -m pytest tests/integration/test_arango_declared_indexes_live.py --no-cov
```

The test must prove an index-based query plan and equal-index reuse.
Remove only the explicitly owned container, volume, and network after the test.
Confirm their absence by their exact names.

## Run the quality gates

Use the exact configured scopes in `.github/workflows/ci.yml`.
Use `.github/test-quality-config.toml` and the unchanged `.github/test-quality-baseline.json` for the test-quality ratchet.
Use `.ste-linter.toml` for the writing check.
Report a missing licensed dictionary as partial writing coverage.

Record each exact command and its result in [validation.md](validation.md).
Do not push or create a pull request before the coordinator grants the verified main revision.

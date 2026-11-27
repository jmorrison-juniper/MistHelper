# Quickstart: OSPF Peer Identity Keys

These steps reproduce the defect and verify the fix. Run each command from the repository root with the `.venv` environment active. No step starts a container. No step contacts Mist Cloud.

## Prerequisites

1. Activate the environment with `.venv\Scripts\Activate.ps1`.
2. Confirm the pinned SDK with `python -m pip show mistapi`. The output must show version 0.64.1 (RV-85).
3. Confirm that the working tree has no change in the files of the change map. Run `git --no-optional-locks status --porcelain`.

## Scenario 1: Reproduce the Defect Before the Fix

The three test groups fail before the change. Each failure names one collision case.

```powershell
python -m pytest tests/unit/db/test_ospf_peer_identity.py tests/unit/config/foundation/support/refactors/data/storage/test_sqlite_database_writer.py tests/unit/config/standalone/foundation/persistence/database/test_router.py
```

Expected result before implementation: the identity tests and the new SQLite and router tests fail. The existing tests pass.

The collision cases are these test functions:

- `test_ospf_records_with_same_mac_and_timestamp_keep_distinct_neighbors` (SQLite). Before the fix, one row remains.
- `test_ospf_composite_write_uses_identity_key_for_redis_and_arango` (router). Before the fix, one Redis document remains.
- `test_absent_scope_is_distinct_from_literal_unknown` (identity). Before the fix, the class does not exist.

## Scenario 2: Verify the Identity Contract

```powershell
python -m pytest tests/unit/db/test_ospf_peer_identity.py
```

Expected result after T004: all sixteen tests pass. Each test covers one rule in `design/contracts/ospf-peer-identity.md`.

## Scenario 3: Verify the SQLite v2 Table and the Legacy Table

```powershell
python -m pytest tests/unit/config/foundation/support/refactors/data/storage/test_sqlite_database_writer.py
```

Expected result after T006: the four new tests pass. The legacy table keeps its schema and row count (`test_ospf_legacy_table_is_unchanged_after_v2_write`). The `_v2` table rejects a wrong primary key (`test_ospf_v2_table_with_wrong_primary_key_fails_closed`).

## Scenario 4: Verify the Redis and ArangoDB Keys

```powershell
python -m pytest tests/unit/config/standalone/foundation/persistence/database/test_router.py
```

Expected result after T007: the Redis key starts with `searchSiteOspfStats:ospf_` or `searchOrgOspfStats:ospf_`. The ArangoDB `_key` equals the identity key. An invalid record returns a failed write result, and no fake backend receives a call.

## Scenario 5: Verify the CSV Contracts

```powershell
python -m pytest tests/unit/export/test_site_search_exporter.py tests/unit/export/test_site_export_utils_extended.py tests/unit/export/test_org_export_utils.py
```

Expected result after T008: all tests pass without edits. The CSV file names and the export call names for menus 55, 70, and 225 stay unchanged.

## Scenario 6: Verify the Shared Strategy Contract

```powershell
python -m pytest tests/contract/test_arango_declared_indexes.py tests/guardrails/test_endpoint_catalog.py
```

Expected result after T005: both files pass. If the first file fails, apply the contingency in task T005 and run again.

## Scenario 7: Run the Lint, Format, and Type Gates

```powershell
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
```

Expected results: `All checks passed` for ruff, `No file needs a change` for black, and `Success` for mypy.

## Scenario 8: Verify the Symbol Surface of Each Changed Module

```powershell
symbol-diff --base origin/main src/foundation/support/refactors/endpoint_primary_key_strategies.py
symbol-diff --base origin/main src/foundation/support/refactors/sqlite_database_writer.py
symbol-diff --base origin/main src/foundation/persistence/db/router.py
```

Expected result: `no module-level name changed` and exit code 0 for each file.

## Scenario 9: Run the Guardrails

```powershell
python -m pytest tests/guardrails
```

Expected result: the guardrails pass. The structure guard accepts the new package `src/foundation/persistence/identity/` because `persistence` then holds four children.

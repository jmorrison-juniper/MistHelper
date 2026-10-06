# Quickstart: Validate the Database Package Split

## Prerequisites

1. Wait until PR #3980 releases the serial slot.
2. Get the exact `main` commit SHA from the #3959 coordinator.
3. Set `$BASE_SHA` to that exact SHA.
4. Do not fetch, rebase, push, create a pull request, arm auto-merge, or merge.
5. Keep #3824 open.

## Verify the Six Moves

Confirm that only these source paths exist:

```powershell
Get-ChildItem src\foundation\persistence\db -Recurse -File
```

Expected structure:

- The database root has `__init__.py`, `backends`, `coordination`, and `support`.
- Each subpackage has `__init__.py` and two approved modules.
- None of the six old module files exists.

## Reject Old Imports

```powershell
rg "src\.foundation\.persistence\.db\.(arango_writer|redis_writer|router|retention|database_schema_utils|host_resolver)|src\.foundation\.persistence\.db import (arango_writer|redis_writer|router|retention|database_schema_utils|host_resolver)" src tests MistHelper.py
```

Expected result: no matches.

## Run Focused Tests

```powershell
python -m pytest `
  tests\unit\test_arango_writer.py `
  tests\unit\_test_arango_writer_helpers.py `
  tests\unit\arango_indexes `
  tests\unit\test_redis_writer.py `
  tests\unit\test_redis_json_writer.py `
  tests\unit\test_unparseable_response_guards.py `
  tests\unit\test_router.py `
  tests\unit\test_retention.py `
  tests\unit\db\test_retention_redis_scan.py `
  tests\unit\db\test_database_schema_utils.py `
  tests\unit\refactors\test_sqlite_database_writer.py `
  tests\unit\db_discovery `
  tests\unit\test_standalone.py `
  tests\unit\container\session_database `
  tests\unit\test_webhook_ingestion.py `
  tests\unit\upgrade_portal\test_store.py `
  tests\contract\test_arango_declared_indexes.py `
  tests\contract\upgrade_portal\test_health.py `
  tests\integration\test_compose_deploy.py `
  tests\integration\test_arango_declared_indexes_live.py `
  tests\test_upgrade_portal_audit.py
```

Expected result: all selected tests pass.

## Run the Source Structure Guard

```powershell
python -m pytest tests\guardrails\test_src_domain_structure.py
```

Expected result: the guard reports no level with more than five direct children.

## Run Six Symbol Preservation Checks

Extend `tests/guardrails/test_src_public_symbol_preservation.py` with these exact pairs:

| Baseline path | Current path |
|---|---|
| `src/foundation/persistence/db/arango_writer.py` | `src/foundation/persistence/db/backends/arango_writer.py` |
| `src/foundation/persistence/db/redis_writer.py` | `src/foundation/persistence/db/backends/redis_writer.py` |
| `src/foundation/persistence/db/router.py` | `src/foundation/persistence/db/coordination/router.py` |
| `src/foundation/persistence/db/retention.py` | `src/foundation/persistence/db/coordination/retention.py` |
| `src/foundation/persistence/db/database_schema_utils.py` | `src/foundation/persistence/db/support/database_schema_utils.py` |
| `src/foundation/persistence/db/host_resolver.py` | `src/foundation/persistence/db/support/host_resolver.py` |

Run the guard against `$BASE_SHA`. The guard must compare each pair and print six checked modules.

```powershell
python -m pytest -s tests\guardrails\test_src_public_symbol_preservation.py
```

Expected result: six moved database modules lose no module-level name.

## Compile Changed Python Files

Build the changed Python file list from the feature manifest. Compile each path:

```powershell
python -m py_compile <changed-python-paths>
```

Expected result: no output.

## Run Ruff and Black

```powershell
python -m ruff check .
python -m black --check .
```

Expected results: Ruff reports `All checks passed`. Black reports no file change.

## Run mypy

```powershell
python -m mypy src\ MistHelper.py wsgi.py scripts\mist_ideas_analyzer_pkg\__init__.py scripts\mist_ideas_distiller_v2_pkg\__init__.py --config-file pyproject.toml
```

Expected result: mypy reports success.

## Run Bandit

```powershell
bandit -c pyproject.toml -r src\foundation\persistence\db -q
```

Expected result: no finding.

## Run Complexity

```powershell
radon cc src\foundation\persistence\db -j | complexity-gate --max 10
```

Expected result: no block exceeds complexity 10.

## Run STE

```powershell
ste-linter --config .ste-linter.toml --min-score 80 `
  specs\3984-split-database-package\plan.md `
  specs\3984-split-database-package\research.md `
  specs\3984-split-database-package\data-model.md `
  specs\3984-split-database-package\quickstart.md `
  specs\3984-split-database-package\contracts\canonical-imports.md
```

Expected result: each file scores 80 or higher.

## Run Test Quality

Run the required input preflight first:

```powershell
python -B -m pytest -p no:cacheprovider -s -q tests\guardrails\local_test_quality_loop\test_guidance.py::TestLiveGuides
```

Then run the changed-test gate against the exact coordinator SHA:

```powershell
test-quality-analyzer --gate `
  --config .github\test-quality-config.toml `
  --baseline .github\test-quality-baseline.json `
  --changed-from $BASE_SHA `
  --full-gate-path .github\workflows\ci.yml `
  --full-gate-path requirements-dev.txt
```

Expected result: `gate: 0 new findings vs baseline`.

## Stop Condition

Stop after the artifacts and local evidence are complete. Do not perform an integration or repository publication step.

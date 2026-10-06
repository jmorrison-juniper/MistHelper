# Implementation Plan: Database Writers Package

**Branch**: `jmorrison-juniper-database-package-split-3824`

**Date**: 2026-10-06

**Spec**: `specs/3824-db-writers-package/spec.md`

**Baseline**: `origin/main` at `2a00e32745472f70764206b060dacc1c4dd13992`

## Summary

Move the ArangoDB and Redis writers into one bounded `writers` package.
Update each active import, patch target, source path, and documentation path.
Add one scoped persistence structure guard with a controlled failure proof.
Keep both writer module bodies and all database behavior unchanged.

## Technical Context

**Language**: Python 3.13 or newer.

**Primary dependencies**: `python-arango`, `redis`, `structlog`, and existing MistHelper database types.

**Storage**: ArangoDB, Redis TimeSeries, Redis JSON, SQLite, and CSV fallback output.

**Testing**: pytest with focused import, database writer, integration, and guard tests.

**Target platforms**: Windows 11, macOS, Linux, and the Podman product container.

**Project type**: Python command-line tool with web portals and database persistence.

**Performance goal**: Preserve all current batch sizes, concurrency limits, and persistence behavior.

**Constraints**: Move modules only. Do not add aliases, forwarding modules, shims, or fallback imports.

**Scope**: Two module moves, active path updates, one guard, focused tests, two documentation updates, and one changelog fragment.

## Constitution Check

- The repaired `db` package will have five direct structural children.
- The new `writers` package will have two modules and one metadata file.
- The change will add no wrapper, alias, re-export, compatibility shim, or fallback.
- The writer classes, functions, constants, and database results will remain unchanged.
- The change will add one unique changelog fragment for issue #3824.
- The guard will check only package levels under `src/foundation/persistence`.
- The implementation will not change `MistHelper.py` or unrelated hierarchy levels.
- The implementation will use explicit file staging and one Conventional Commit.

The existing `specs/` and `changelog.d/` folder debt is grandfathered process debt.
This change adds only its unique process records.
Issue #3824 is the incremental remediation record for the `db` package violation.

## Active Candidate Paths

### Module moves and package metadata

- `src/foundation/persistence/db/arango_writer.py`
- `src/foundation/persistence/db/redis_writer.py`
- `src/foundation/persistence/db/writers/__init__.py`
- `src/foundation/persistence/db/writers/arango_writer.py`
- `src/foundation/persistence/db/writers/redis_writer.py`

### Runtime imports and active source paths

- `src/foundation/persistence/db/router.py`
- `scripts/migrate_sqlite_to_polyglot.py`
- `src/foundation/support/refactors/endpoint_primary_key_strategies.py`
- `src/interfaces/portals/upgrade_portal/capture/store.py`
- `src/interfaces/portals/upgrade_portal/compare/clients.py`

### Test imports and patch targets

- `tests/contract/test_arango_declared_indexes.py`
- `tests/integration/test_arango_declared_indexes_live.py`
- `tests/unit/_test_arango_writer_helpers.py`
- `tests/unit/arango_indexes/fakes.py`
- `tests/unit/arango_indexes/test_preservation.py`
- `tests/unit/arango_indexes/test_retry_concurrency.py`
- `tests/unit/db_discovery/test_config.py`
- `tests/unit/db_discovery/test_probe.py`
- `tests/unit/test_arango_writer.py`
- `tests/unit/test_redis_json_writer.py`
- `tests/unit/test_redis_writer.py`
- `tests/unit/test_unparseable_response_guards.py`
- `tests/unit/test_webhook_ingestion.py`
- `tests/unit/upgrade_portal/test_compare_clients.py`
- `tests/unit/upgrade_portal/test_guardrails.py`
- `tests/unit/web_portal/test_portal_log_routing.py`

### Active documentation paths

- `documentation/diagrams/core/data-persistence-routing.md`
- `documentation/upgrade_capture_portal.md`

### Guard and process records

- `tests/guardrails/test_persistence_package_structure.py`
- `specs/3824-db-writers-package/spec.md`
- `specs/3824-db-writers-package/plan.md`
- `specs/3824-db-writers-package/tasks.md`
- `changelog.d/issue-3824-db-writers-package.md`

No other path is an active candidate.
Historical specifications for other issues will remain unchanged.

## Move Operations

Create the destination package before the moves.
Use these exact move commands:

```bash
mkdir -p src/foundation/persistence/db/writers
git mv src/foundation/persistence/db/arango_writer.py src/foundation/persistence/db/writers/arango_writer.py
git mv src/foundation/persistence/db/redis_writer.py src/foundation/persistence/db/writers/redis_writer.py
```

Add `src/foundation/persistence/db/writers/__init__.py` after the moves.
The file will contain only this package docstring:

```python
"""Database writers for the MistHelper persistence layer."""
```

Do not re-export a writer name from the package initializer.
Do not leave either old module path in the tree.

## Import and Patch-Target Updates

Replace each active Python module path with its canonical new path:

```text
src.foundation.persistence.db.arango_writer
-> src.foundation.persistence.db.writers.arango_writer

src.foundation.persistence.db.redis_writer
-> src.foundation.persistence.db.writers.redis_writer
```

Update normal imports in `router.py`, the migration script, and all listed tests.
Update delayed imports in the migration script and test functions.
Update string patch targets in these files:

- `tests/integration/test_arango_declared_indexes_live.py`
- `tests/unit/arango_indexes/fakes.py`
- `tests/unit/arango_indexes/test_preservation.py`
- `tests/unit/db_discovery/test_probe.py`
- `tests/unit/test_arango_writer.py`
- `tests/unit/test_redis_json_writer.py`
- `tests/unit/test_redis_writer.py`
- `tests/unit/test_unparseable_response_guards.py`
- `tests/unit/web_portal/test_portal_log_routing.py`

Keep each symbol name unchanged.
Keep each moved module body unchanged, except for a required import repair.
The current module imports remain valid after the move and need no behavior change.

Update active source comments in the three listed source files.
Replace each slash path with `src/foundation/persistence/db/writers/`.
Do not change line references unless the move changes the referenced line.

## Documentation Updates

Update only these two active documentation files:

1. `documentation/diagrams/core/data-persistence-routing.md`
2. `documentation/upgrade_capture_portal.md`

Replace each old writer file path with its new `writers` path.
Do not change historical specifications, archived evidence, or released history.

## Scoped Guard Design

Add `tests/guardrails/test_persistence_package_structure.py`.
Keep the guard independent from the broader source domain guard.

The guard will use a named inspector class.
The class will accept a persistence root path for normal and controlled tests.
It will find package directories recursively under `src/foundation/persistence`.
It will count direct structural children in each package directory.
It will exclude `__init__.py`, `__pycache__`, and generated cache metadata.
It will enforce a maximum count of five.
It will report the checked directory count in each result message.
It will report each violating relative path and measured child count.
It will fail with a clear message when the required root cannot be read.

The normal repository test will check these package levels after the move:

- `src/foundation/persistence`
- `src/foundation/persistence/cache`
- `src/foundation/persistence/db`
- `src/foundation/persistence/db/writers`

The expected direct structural child counts are two, one, five, and two.
The `db` count will include four modules and the `writers` package.

The active-path test will read tracked text paths from Git.
It will scan active source, scripts, tests, and maintained documentation.
It will reject both old dotted module paths and old slash file paths.
It will exclude `specs/` because those directories are immutable process records.
It will not exclude any active candidate root.
It will fail if Git cannot provide its tracked file list.

## Controlled Failure Proof

Build a temporary package root with one package level and six structural children.
Run the same inspector against that temporary root.
Assert that the result fails.
Assert that the message reports one checked directory.
Assert that the message names the violating package path.
Assert that the message reports a measured count of six.

Add a separate missing-root test.
Give the inspector a path that does not exist.
Assert that it fails with the unreadable root path and cause.

These tests prove the guard can fail without changing the repository tree.

## Changelog Fragment

Add `changelog.d/issue-3824-db-writers-package.md`.
Use this content:

```markdown
### Changed

- Changed the ArangoDB and Redis writer paths for #3824.
```

## Implementation Order

1. Confirm the branch and approved baseline.
2. Confirm that no active pull request owns a candidate path.
3. Run the two `git mv` commands.
4. Add the docstring-only package initializer.
5. Update runtime imports, delayed imports, and patch targets.
6. Update active source comments and the two documentation paths.
7. Add the scoped guard and controlled failure tests.
8. Add focused canonical import coverage.
9. Add the changelog fragment.
10. Run the validations below in order.
11. Stage only the active candidate paths.
12. Create the local commit.
13. Run the test-quality preflight and changed-file gate.

Run one heavy command at a time.
Do not run the full repository test suite.

## Validation Commands

### Baseline and active-path scan

```bash
git fetch --no-tags origin "+refs/heads/main:refs/remotes/origin/main"
git rev-parse --verify "origin/main^{commit}"
test "$(git rev-parse origin/main)" = "2a00e32745472f70764206b060dacc1c4dd13992"
git grep -n -E 'src\.foundation\.persistence\.db\.(arango_writer|redis_writer)|src/foundation/persistence/db/(arango_writer|redis_writer)\.py' -- src tests scripts documentation README.md
```

The final `git grep` command must return no active match.
Do not use it to edit or validate historical specifications.

### Focused canonical import and guard tests

```bash
python -c "from src.foundation.persistence.db.writers.arango_writer import ArangoDBWriter; from src.foundation.persistence.db.writers.redis_writer import RedisJSONWriter, RedisTimeSeriesWriter; print('Checked 3 canonical writer imports')"
python -m pytest -q tests/guardrails/test_persistence_package_structure.py
python -m pytest -q tests/contract/test_arango_declared_indexes.py tests/unit/db_discovery
```

### Focused database behavior tests

Run each command separately:

```bash
python -m pytest -q tests/unit/test_arango_writer.py tests/unit/_test_arango_writer_helpers.py tests/unit/arango_indexes
python -m pytest -q tests/unit/test_redis_writer.py tests/unit/test_redis_json_writer.py
python -m pytest -q tests/unit/test_webhook_ingestion.py tests/unit/test_unparseable_response_guards.py
python -m pytest -q tests/unit/web_portal/test_portal_log_routing.py tests/unit/upgrade_portal/test_compare_clients.py tests/unit/upgrade_portal/test_guardrails.py
python -m pytest -q tests/integration/test_arango_declared_indexes_live.py
```

The live integration test may skip only for its documented service requirement.
It must not fail because of an import or patch target.

### Ruff, Black, and mypy

Run each command separately:

```bash
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
```

### Bandit and complexity

Run each command separately:

```bash
bandit -c pyproject.toml -r src/foundation/persistence/db src/interfaces/portals/upgrade_portal scripts/migrate_sqlite_to_polyglot.py -q
radon cc src/foundation/persistence/db src/interfaces/portals/upgrade_portal/capture/store.py src/interfaces/portals/upgrade_portal/compare/clients.py scripts/migrate_sqlite_to_polyglot.py tests/guardrails/test_persistence_package_structure.py -j | complexity-gate --max 10
```

### Public symbol preservation

Run each command separately:

```bash
symbol-diff --base origin/main src/foundation/persistence/db/router.py
symbol-diff --base origin/main src/foundation/persistence/db/writers/arango_writer.py
symbol-diff --base origin/main src/foundation/persistence/db/writers/redis_writer.py
```

The router must lose no module-level name.
Each moved module must preserve its complete module-level symbol set.

### Simplified Technical English

```bash
ste-linter --config .ste-linter.toml --min-score 80 documentation/diagrams/core/data-persistence-routing.md documentation/upgrade_capture_portal.md specs/3824-db-writers-package/spec.md specs/3824-db-writers-package/plan.md specs/3824-db-writers-package/tasks.md changelog.d/issue-3824-db-writers-package.md
```

Each listed file must score 80 or higher.

## Local Commit

Review the explicit manifest before staging:

```bash
git status --short
git diff --check
git diff --name-status origin/main...HEAD
```

Stage only the active candidate paths.
Do not use `git add .` or `git add -A`.
Create one local commit after all preceding gates pass:

```bash
git commit -m "refactor(db): move database writers into package" -m "Closes #3824" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
```

## Test-Quality Gates After the Commit

Run the required preflight first:

```bash
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

Run the changed-file gate only after the preflight passes:

```bash
test-quality-analyzer --gate \
  --config .github/test-quality-config.toml \
  --baseline .github/test-quality-baseline.json \
  --changed-from "origin/main" \
  --full-gate-path .github/workflows/ci.yml \
  --full-gate-path requirements-dev.txt
```

The gate must report zero new findings.
Do not change the test-quality baseline.

## Completion Conditions

- The `db` package has exactly five direct structural children.
- The `writers` package contains both moved modules and the docstring-only initializer.
- Every active import and patch target uses the new canonical module path.
- Both active documentation files use the new slash paths.
- The scoped guard passes and reports a nonzero checked directory count.
- The controlled sixth-child proof fails with the expected path and count.
- The missing-root proof fails with a clear cause.
- Each required validation command passes or records its documented skip.
- The local commit exists before the two test-quality gates run.
- Historical specifications for all other issues remain unchanged.

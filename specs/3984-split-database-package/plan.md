# Implementation Plan: Split Database Package

**Branch**: `jmorrison-juniper-refactor-3984-split-database-package` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/3984-split-database-package/spec.md`

## Summary

Move exactly six database modules into three canonical subpackages. Update each direct import, patch target, and dependency string. Preserve all behavior and module-level symbols. Add no compatibility path or package re-export.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Primary Dependencies**: `python-arango`, `redis`, `structlog`, and existing MistHelper support modules

**Storage**: Existing ArangoDB, Redis JSON, Redis TimeSeries, and SQLite behavior remains unchanged

**Testing**: pytest, source structure guard, moved-module symbol guard, Ruff, Black, mypy, Bandit, radon, STE linter, and test-quality analyzer

**Target Platform**: Windows 11, macOS, Linux, and the existing Podman container

**Project Type**: Python command-line application with web portals

**Performance Goals**: No measurable persistence, routing, retention, import-time, or host-resolution regression

**Constraints**: Move only the six approved modules. Change consumers only for canonical imports or patch targets. Add no shims, aliases, adapters, fallback imports, schema changes, index changes, or behavior changes.

**Scale/Scope**: Six source moves, three package initializers, direct consumer updates, focused tests, two guard updates, and no production feature work

## Constitution Check

*GATE: Passed before research. Rechecked after design.*

- **Five-item rule**: PASS. The database root will contain `__init__.py` and three subpackages. Each subpackage will contain `__init__.py` and two modules.
- **Class architecture**: PASS. The move changes no class ownership and adds no wrapper.
- **Safety**: PASS. The plan changes no input, secret, destructive operation, database value, or production action.
- **Deployment pipeline**: DEFERRED BY USER. This planning session will not fetch, rebase, push, create a pull request, arm auto-merge, or merge.
- **Observability**: PASS. Existing log messages, levels, names, redaction, and routing must remain unchanged.
- **Inline comments**: PASS. The move must preserve existing comments. Import-only edits need concise cause comments where the current block requires them.
- **Action logging**: PASS. The move adds no action and must not change existing logging.
- **Process-folder debt**: The existing `specs/` child count is grandfathered. This feature adds only its required unique issue folder. Repository-wide process-folder remediation remains separate.
- **Mist transport**: Not applicable. The feature makes no Mist API or WebSocket change.
- **Release note**: No fragment is planned because this is an internal-only structural refactor.
- **Issue state**: Keep parent issue #3824 open. Do not use `Closes #3824`.
- **Serial coordination**: PR #3980 owns the serial slot. Do not start later integration steps until it releases the slot.
- **Baseline coordination**: The #3959 coordinator must provide the exact `main` commit SHA before later symbol and integration checks.

### Post-Design Recheck

The design keeps the canonical `backends`, `coordination`, and `support` layout. It adds no constitutional exception. The gates remain passed with the user limits above.

## Project Structure

### Documentation

```text
specs/3984-split-database-package/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── canonical-imports.md
```

### Source Code

```text
src/foundation/persistence/db/
├── __init__.py
├── backends/
│   ├── __init__.py
│   ├── arango_writer.py
│   └── redis_writer.py
├── coordination/
│   ├── __init__.py
│   ├── retention.py
│   └── router.py
└── support/
    ├── __init__.py
    ├── database_schema_utils.py
    └── host_resolver.py
```

**Structure Decision**: Use the approved three-subpackage layout. Keep database configuration and result types in the root initializer. Make each new initializer empty except for its module documentation. Do not re-export moved modules or symbols.

## Exact Source Moves

| Current path | Canonical path |
|---|---|
| `src/foundation/persistence/db/arango_writer.py` | `src/foundation/persistence/db/backends/arango_writer.py` |
| `src/foundation/persistence/db/redis_writer.py` | `src/foundation/persistence/db/backends/redis_writer.py` |
| `src/foundation/persistence/db/router.py` | `src/foundation/persistence/db/coordination/router.py` |
| `src/foundation/persistence/db/retention.py` | `src/foundation/persistence/db/coordination/retention.py` |
| `src/foundation/persistence/db/database_schema_utils.py` | `src/foundation/persistence/db/support/database_schema_utils.py` |
| `src/foundation/persistence/db/host_resolver.py` | `src/foundation/persistence/db/support/host_resolver.py` |

The complete consumer inventory and canonical replacements are in [contracts/canonical-imports.md](contracts/canonical-imports.md).

## Implementation Sequence

1. Wait until PR #3980 releases the serial slot.
2. Obtain the exact `main` commit SHA from the #3959 coordinator. Record it as `BASE_SHA`. Do not fetch or infer it.
3. Capture the six baseline module-level symbol sets from `BASE_SHA`.
4. Create the three package directories and documentation-only initializers.
5. Move the six modules without logic edits.
6. Update the internal imports in the moved modules and the database root initializer.
7. Update every production import, test import, patch target, dynamic dependency string, and logger-name expectation in the contract.
8. Remove all six old files. Add no compatibility file at an old path.
9. Extend `tests/guardrails/test_src_domain_structure.py` to measure the database root and each new subpackage.
10. Extend `tests/guardrails/test_src_public_symbol_preservation.py` with six exact old-to-new paths.
11. Update focused tests only for canonical paths or preserved behavior.
12. Run the validation sequence in [quickstart.md](quickstart.md).
13. Stop before fetch, rebase, push, pull request creation, auto-merge, or merge.

## Focused Test Scope

- Backend behavior: `tests/unit/test_arango_writer.py`, `tests/unit/_test_arango_writer_helpers.py`, `tests/unit/arango_indexes/`, `tests/unit/test_redis_writer.py`, `tests/unit/test_redis_json_writer.py`, and `tests/unit/test_unparseable_response_guards.py`.
- Coordination behavior: `tests/unit/test_router.py`, `tests/unit/test_retention.py`, `tests/unit/db/test_retention_redis_scan.py`, `tests/unit/container/session_database/`, and `tests/unit/test_webhook_ingestion.py`.
- Support behavior: `tests/unit/db/test_database_schema_utils.py`, `tests/unit/refactors/test_sqlite_database_writer.py`, `tests/unit/db_discovery/`, `tests/unit/test_standalone.py`, and `tests/unit/upgrade_portal/test_store.py`.
- Index contracts: `tests/contract/test_arango_declared_indexes.py` and `tests/integration/test_arango_declared_indexes_live.py`.
- Import integration: `tests/integration/test_compose_deploy.py`, `tests/contract/upgrade_portal/test_health.py`, and `tests/test_upgrade_portal_audit.py`.
- Guards: `tests/guardrails/test_src_domain_structure.py` and `tests/guardrails/test_src_public_symbol_preservation.py`.

## Required Gates

Run each exact command from [quickstart.md](quickstart.md). The required set is:

- Focused pytest tests.
- Source structure guard.
- Six moved-module symbol preservation checks.
- Compile for each moved source module and each changed Python consumer.
- Ruff.
- Black.
- mypy with the workflow `MYPY_PATHS`.
- Bandit.
- Complexity with `complexity-gate --max 10`.
- STE for the changed Markdown artifacts.
- Test-quality preflight and changed-test gate against the coordinator-provided `BASE_SHA`.

## Complexity Tracking

No new violation is planned. The existing `specs/` process-folder count is grandfathered debt. Its remediation remains a separate repository action.

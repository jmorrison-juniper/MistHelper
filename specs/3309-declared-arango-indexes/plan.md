# Implementation Plan: Declared ArangoDB indexes

**Branch**: `jmorrison-juniper-declared-arangodb-indexes` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/3309-declared-arango-indexes/spec.md`.

## Summary

Add semantic index coordination to the existing database schema module.
The real writer opens collections under a shared reentrant guard and ensures the strategy's declared indexes before import.
The cache records only complete checks.
Expected database and transport failures retain their original exceptions.

## Technical Context

**Language/Version**: Python 3.13 or newer. The owned environment uses Python 3.13.13.

**Primary Dependencies**: Existing `python-arango`, `structlog`, `requests`, `pytest`, and Hypothesis.
The installed SDK is `python-arango` 8.3.5.

**Storage**: Existing ArangoDB collections and persistent secondary indexes. No schema declaration or primary key changes.

**Testing**: Real writer calls with strict fake SDK handles, real SDK request contracts, and an owned isolated ArangoDB store.

**Target Platform**: Existing macOS, Windows, Linux, and container paths.

**Project Type**: Existing Python command-line application and shared database backend.

**Performance Goals**: One index request per distinct unconfirmed field within each process-local database and collection scope.

**Constraints**: Preserve all document behavior. Access no production store. Add no dependency, baseline, suppression, or exclusion change.

**Scale/Scope**: Existing exporter collections only. Create no field index outside the supplied strategy.

## Constitution Check

The repair uses semantic classes, typed SDK collection interfaces, and the existing structured logger pattern.
New methods remain within five parameters, five logical blocks, and 25 lines.
The new unit package contains five files.
Feature documentation uses five direct children and a nested design directory.

`src/foundation/persistence/db` already contains six module files.
The repair adds no file there.
It adds the index state and manager to the existing `database_schema_utils.py`.
The existing schema utility class and writer already exceed the class method limit.
The repair does not increase their method counts.
An independent future refactor can separate their existing responsibilities.
That refactor does not belong to issue #3309.

Existing test roots exceed five children.
The requested dedicated tests use one bounded feature package and separate contract and integration files.
Their existing parent counts remain technical debt, not grounds for unrelated test moves.

The app owns the branch.
The legacy Git hook uses raw branch creation, and PowerShell is unavailable.
This workflow applies the repository templates directly to feature-owned files.
It changes no `.specify` state or shared agent instructions.
The coordinator's explicit remote grant controls the later push and protected merge.

The post-design review confirms the same constraints.

## Project Structure

### Documentation (this feature)

```text
specs/3309-declared-arango-indexes/
├── spec.md
├── plan.md
├── tasks.md
├── checklists/requirements.md
└── design/
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── validation.md
    └── contracts/indexes.md
```

### Source Code (repository root)

```text
src/foundation/persistence/db/
├── arango_writer.py
└── database_schema_utils.py

tests/unit/arango_indexes/
├── conftest.py
├── fakes.py
├── test_declared_indexes.py
├── test_retry_concurrency.py
└── test_preservation.py

tests/contract/test_arango_declared_indexes.py
tests/integration/test_arango_declared_indexes_live.py
```

**Structure Decision**: Keep collection ownership in `ArangoDBWriter`.
Keep index normalization, shared state, and confirmation in semantic schema classes.
Do not add a wrapper or change graph, snapshot, key, or import responsibilities.

## Complexity Tracking

| Existing constraint | Narrow decision | Separate remediation |
| - | - | - |
| Six files in `src/foundation/persistence/db` | Use the existing schema module | Separate existing backend packages in an independent refactor |
| Existing classes exceed five methods | Add no writer or schema utility method | Divide existing responsibilities in an independent refactor |
| Existing test roots exceed five children | Keep five feature unit files | Reorganize existing test roots in an independent refactor |

## Workflow

The specification defines the behavior before code changes.
Research verifies the actual SDK and the existing router failure result.
Tasks require failing tests against the unchanged writer before implementation.
Implementation uses the approved scope and tests the complete write path.
Analysis checks requirement coverage and records exact evidence in [design/validation.md](design/validation.md).

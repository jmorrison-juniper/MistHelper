# Implementation Plan: Redis Time-Series Entity Identifier Fallback

**Branch**: `feat/990-redis-entity-id` | **Date**: 2026-07-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/990-redis-entity-id/spec.md`

## Summary

`RedisTimeSeriesWriter._extract_chunk` reads the entity identifier from one field.
When a record omits that field, the writer buckets the record under the text
`unknown`. Many unrelated records then collapse into one time-series key.

The fix adds one resolution rule to `RedisTimeSeriesWriter`. The rule reads the
strategy field first. When that field holds no usable value, the rule walks the
ordered fallback list `device_id`, `site_id`, `org_id`, `mac`, `id`. The rule
returns the text `unknown` only when no field holds a usable value.

The rule also reports which branch produced the identifier. The writer tallies
those branches per chunk and emits one debug summary for each extraction call.
The tally travels back through the return value, so no thread shares a mutable
counter.

## Technical Context

**Language/Version**: Python 3.13 or newer. The project interpreter is
`.venv\Scripts\python.exe`. The global interpreter is broken on this host.

**Primary Dependencies**: The standard library only. The change adds
`collections.Counter`. The target file already imports `redis` and `structlog`.
The change adds no package to `requirements.txt` or `pyproject.toml`.

**Storage**: Redis TimeSeries through the `redis-stack` service. The change adds
no key, no index, and no migration. Keys that the store already holds under the
text `unknown` stay as they are.

**Testing**: pytest. The target test file is `tests/unit/test_redis_writer.py`.
All Redis calls are mocked, so no live Redis server is required.

**Target Platform**: Windows 11 for local development. Linux container for
production.

**Project Type**: Single project. The source package sits under `src/`, and the
test package sits under `tests/`.

**Performance Goals**: The writer emits no log line for each record. The writer
emits one summary line for each extraction call. An extraction of 10000 records
therefore produces one summary line.

**Constraints**: `_extract_chunk` runs inside a thread pool when the input holds
more than 1000 records. The new rule must stay pure and must hold no shared
state. The three-part key shape must not change. A record that carries a usable
value in the strategy field must produce a byte-identical key.

**Scale/Scope**: One source file, one test file, and one changelog entry. The
change touches about 40 lines of source code.

## Constitution Check

*GATE: This check ran before Phase 0 and again after Phase 1. The result did not
change.*

| Principle | Result | Evidence |
| - | - | - |
| I. Five-Item Rule | PASS with one recorded deviation | `_resolve_entity_id` takes 2 parameters. `_is_usable` takes 1 parameter. Every changed method stays under 25 lines and under 5 logical blocks. The class-level method count is a pre-existing deviation. See Complexity Tracking. |
| II. Class-Based Architecture | PASS | The new methods are static methods on `RedisTimeSeriesWriter`. They sit beside `_pick_webhook_entity` and `_pick_entity_field`. The change adds no standalone wrapper function. Every name uses full words. |
| III. Safety-First | PASS | The change reads record fields only. It calls no `input()`, runs no destructive operation, and touches no credential. It validates each candidate value before use and returns early on the first usable value. |
| IV. Full Deployment Pipeline | PASS at plan time | The pipeline runs during the implement phase. The quality gate commands sit in `quickstart.md`. |
| V. Observability and Logging | PASS | The summary event uses ASCII text only. The event uses the `structlog` keyword style that the file already uses. The event reports counts only and reports no record content. |
| VI. Inline Comments | PASS | Every changed line carries a same-line `# WHY:` comment. The file already uses that exact style. |
| VII. Action Logging | PASS | `_extract_all_adds` logs an info event before the extraction and a debug summary after the extraction. |

**Technology constraints**: The change targets Python 3.13 or newer. It adds no
dependency. It calls no Mist API method. It builds no file path, so the
`os.path.join` rule does not apply.

## Project Structure

### Documentation (this feature)

```text
specs/990-redis-entity-id/
├── plan.md                          # This file
├── research.md                      # Phase 0 output
├── data-model.md                    # Phase 1 output
├── quickstart.md                    # Phase 1 output
├── contracts/
│   └── entity-id-resolution.md      # Phase 1 output
├── spec.md                          # Feature specification
├── checklists/
│   └── requirements.md              # Existing requirements checklist
└── tasks.md                         # Phase 2 output. The /speckit.tasks command creates it.
```

### Source Code (repository root)

```text
src/
└── db/
    ├── __init__.py                  # DatabaseConfig and WriteResult. No change.
    └── redis_writer.py              # The only source file that changes.

tests/
└── unit/
    └── test_redis_writer.py         # The only test file that changes.

CHANGELOG.md                         # One new entry under the [Unreleased] heading.
```

**Structure Decision**: The project keeps a single source package under `src/`.
The database writers sit under `src/db/`. This feature stays inside the existing
layout. It adds no directory and no module.

## Design

### Change 1 - Promote the fallback order to a module constant

The helper `_pick_entity_field` declares the order as an inline tuple at line
446. The new rule needs the same order. Requirement FR-013 states that the file
must hold one rule for the batch path.

Add a module-level constant beside `WEBHOOK_ENTITY_KEYS`:

```text
BATCH_ENTITY_FALLBACK_KEYS = ("device_id", "site_id", "org_id", "mac", "id")
```

Then read that constant from `_pick_entity_field` and from the new rule. The
constant mirrors the shape and the naming style of `WEBHOOK_ENTITY_KEYS`.

### Change 2 - Add the usable-value test

Add a static method `_is_usable(value)` to `RedisTimeSeriesWriter`. The method
returns `False` when the value is `None`. The method returns `False` when the
text form of the value holds only blank space. The method returns `True` in
every other case. The method therefore accepts the number `0`.

### Change 3 - Add the resolution rule

Add a static method `_resolve_entity_id(record, entity_key_field)` to
`RedisTimeSeriesWriter`. The method returns a pair. The first item is the entity
identifier. The second item is the name of the branch that produced it. The
branch names are `strategy`, `fallback`, and `unknown`.

The method reads the strategy field first. When that field holds a usable value,
the method returns the text form of the value and the branch name `strategy`.
The method then walks `BATCH_ENTITY_FALLBACK_KEYS` and returns the first usable
value with the branch name `fallback`. The method returns the text `unknown`
with the branch name `unknown` when no field holds a usable value.

### Change 4 - Replace the direct lookup

Line 190 inside `_extract_chunk` reads:

```text
entity_id = str(record.get(ctx.entity_key_field, "unknown"))
```

Replace that line with a call to `_resolve_entity_id`. Tally the branch name
into a local `Counter` inside the loop. Return the counter as a third item from
`_extract_chunk`.

### Change 5 - Merge the counts and emit one summary

`_extract_parallel` already merges the adds and the key records from each chunk.
Merge the counters there with `Counter.update`. Then return the merged counter as
a third item.

`_extract_all_adds` is the single entry point for both the sequential path and
the parallel path. Log an info event before the extraction. Unpack the three
items from the chosen path. Emit one debug summary with the three counts. Return
the first two items, so the signature that `write` consumes does not change.

### Blast radius

| File | Change |
| - | - |
| `src/db/redis_writer.py` | One new constant, two new static methods, one replaced line, and three touched method signatures. |
| `tests/unit/test_redis_writer.py` | New tests for the three branches. One existing mock return value changes from a pair to a triple. |
| `CHANGELOG.md` | One entry under the `## [Unreleased]` heading. |

The existing test `test_over_1000_records_uses_thread_pool` patches
`_extract_chunk` with the return value `([], {})`. The return value must become
`([], {}, Counter())`. That mock produces no time-series key, so Success
Criterion SC-002 still holds.

### Complexity headroom

The radon gate fails a block whose complexity is above 10. A measurement of the
current file reports a highest block score of 5. The new methods score 4 and 2.
The touched methods gain at most one branch each. The file therefore keeps a
wide margin.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| The class `RedisTimeSeriesWriter` already holds more than 25 methods. Principle I caps a level at five children. This change adds two more. | Requirement FR-013 states that the batch path must hold one rule for the choice of an entity identifier. The sibling helpers `_pick_entity_field` and `_pick_webhook_entity` already live on this class. A reader finds one idea in one place. | A new helper class would hold two methods that only the writer calls. Principle II forbids a wrapper, and the Non-Goals section forbids a restructure of this file. A split would move one idea into two files and would raise the reading cost for the operator. A full decomposition of the class is a separate refactor with its own issue. |

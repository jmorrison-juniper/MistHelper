# Phase 0 Research: Redis Time-Series Entity Identifier Fallback

**Feature**: `990-redis-entity-id` | **Date**: 2026-07-29

The Technical Context in `plan.md` holds no open question. The specification
names the target file, the target line, the pattern to copy, and the fallback
order. This document records the design decisions that the specification left to
the plan, and it records the measurements that ground them.

---

## Measurements taken against the current checkout

| Item | Measured value | Source |
| - | - | - |
| Target line | `entity_id = str(record.get(ctx.entity_key_field, "unknown"))` | `src/db/redis_writer.py` line 190 |
| Existing fallback order | `("device_id", "site_id", "org_id", "mac", "id")` | `_pick_entity_field`, line 446 |
| Existing webhook helper | Walks `WEBHOOK_ENTITY_KEYS` and returns `"unknown"` last | `_pick_webhook_entity`, line 431 |
| Webhook candidate constant | `WEBHOOK_ENTITY_KEYS = ("mac", "device_id")` | Module level, line 45 |
| Sentinel dependency | `str(record.get(field, "unknown"))` | `RedisJSONWriter._build_key`, line 592 |
| Highest complexity block in the file | 5 | `radon cc src/db/redis_writer.py -s` |
| Radon gate limit | A block above 10 fails the gate | `.github/workflows/ci.yml` line 318 |
| Ruff line length | 120 | `pyproject.toml` line 137 |
| mypy target and mode | `mypy src/ --config-file pyproject.toml`, strict | `.github/workflows/ci.yml` line 156 |
| mypy relaxation for this package | `src.db` and `src.db.*` turn off `disallow_untyped_calls`, `disallow_any_generics`, and `warn_return_any` | `pyproject.toml` line 315 |
| Coverage gate | `pytest --cov=src/ --cov-fail-under=80` | `.github/workflows/ci.yml` line 190 |

---

## Decision 1 - Promote the fallback order to a module constant

**Decision**: Add `BATCH_ENTITY_FALLBACK_KEYS` at module level beside
`WEBHOOK_ENTITY_KEYS`. Read that constant from `_pick_entity_field` and from the
new rule.

**Rationale**: Requirement FR-006 sets the order `device_id`, `site_id`,
`org_id`, `mac`, `id`. A measurement confirms that `_pick_entity_field` already
declares that exact order. Requirement FR-013 states that the file must not hold
two different rules for the batch path. One constant that both readers share
meets both requirements. The constant also mirrors `WEBHOOK_ENTITY_KEYS`, so the
file holds one shape for one idea.

**Alternatives considered**:

- **Copy the tuple into the new method**. Rejected. The file would then hold the
  same order in two places, and a later edit could move them apart.
- **Share one constant across the batch path and the webhook path**. Rejected.
  The Assumptions section states that a webhook event carries a different field
  set, and the Non-Goals section forbids a change to `_pick_webhook_entity`.

---

## Decision 2 - Test each candidate with a usable-value helper

**Decision**: Add a static method `_is_usable(value)`. The method returns `False`
for `None` and for a text form that holds only blank space. The method returns
`True` in every other case.

**Rationale**: The Requirements section defines a usable value with three
conditions. A named helper states that definition once. Each caller then reads as
one line.

**Alternatives considered**:

- **Use a plain truth test such as `if value:`**. Rejected. A truth test rejects
  the number `0`, and the Assumptions section states that `0` is a valid entity
  identifier.
- **Inline the three conditions at every candidate**. Rejected. The loop body
  would grow past the readable limit, and the rule would appear twice inside one
  method.

---

## Decision 3 - Carry the branch tally in the return value

**Decision**: `_resolve_entity_id` returns a pair. The pair holds the identifier
and the branch name. `_extract_chunk` tallies the branch names into a local
counter. The worker returns that counter as a third item. `_extract_parallel`
then merges the counters from every chunk.

**Rationale**: `_extract_chunk` runs inside a thread pool. The specification
states that the counter for Requirement FR-007 must not become shared mutable
state. A local counter travels back through the return value. Each worker
therefore stays pure. The counter type from the standard library merges two
counters in one call. The merge adds no new type and no new operator.

**Alternatives considered**:

- **Store the counter on the frozen `_ExtractContext`**. Rejected. Every worker
  thread would write to one object, which is the shared mutable state that the
  specification forbids.
- **Store the counter on the writer instance**. Rejected for the same reason.
  The instance is also reused across calls, so the counts would accumulate across
  extractions and would break Requirement FR-007.
- **Classify the records a second time after the extraction**. Rejected. A second
  pass repeats the work for every record, and it re-evaluates the rule outside
  the single place that Requirement FR-013 demands.
- **Return the counts from a mutable default argument**. Rejected. A mutable
  default is shared across calls and is a known defect pattern.

---

## Decision 4 - Emit the summary from `_extract_all_adds`

**Decision**: Emit one info event before the extraction and one debug summary
after the extraction, both inside `_extract_all_adds`.

**Rationale**: `_extract_all_adds` is the only entry point that both the
sequential path and the parallel path pass through. One summary per call
therefore follows from the placement. Principle VII asks for an info event before
an action and a debug event after it, and this placement satisfies both.

**Alternatives considered**:

- **Emit the summary from `_extract_chunk`**. Rejected. A large input runs many
  chunks, so the writer would emit one line per chunk instead of one line per
  call.
- **Add the counts to the existing `extraction_complete` info event**. Rejected.
  That event fires only on the parallel path, so a small input would emit no
  summary. Requirement FR-007 asks for a summary on every extraction call.

---

## Decision 5 - Keep the sentinel as a literal inside the new rule

**Decision**: Write the text `unknown` as a literal inside `_resolve_entity_id`.
Do not introduce a shared sentinel constant.

**Rationale**: The Non-Goals section forbids a change to `_pick_webhook_entity`
and to `RedisJSONWriter._build_key`. Both hold the same literal. A shared
constant that skips those two sites would create a third form of one idea. A
shared constant that includes them would break the Non-Goals section.

**Alternatives considered**:

- **Add `UNKNOWN_ENTITY_ID` and update all three sites**. Rejected. It edits two
  methods that the Non-Goals section places out of scope.

---

## Decision 6 - Do not skip the strategy field inside the fallback walk

**Decision**: Let the fallback walk read every name in
`BATCH_ENTITY_FALLBACK_KEYS`, even when the strategy field name matches one of
them.

**Rationale**: The Edge Cases section states that a matching name must return the
same value and must not read the field twice. The early return on the strategy
branch already covers that case. The walk reaches a matching name only after the
strategy branch found the field unusable. A second read of an unusable field
returns the same answer and changes no behavior.

**Alternatives considered**:

- **Add a branch that skips the matching name**. Rejected. The branch raises the
  complexity score and adds a line that no observable behavior needs.

---

## Decision 7 - Update the one existing mock that unpacks `_extract_chunk`

**Decision**: Change the mock return value in
`test_over_1000_records_uses_thread_pool` from `([], {})` to `([], {}, Counter())`.

**Rationale**: The test patches `_extract_chunk` and lets `_extract_parallel`
unpack the result. The new third item makes the pair too short to unpack. Success
Criterion SC-002 covers generated keys. This mock produces no key, so the update
does not weaken that criterion.

**Alternatives considered**:

- **Keep the pair and find another route for the counts**. Rejected. Decision 3
  already rejected every route that avoids the return value.
- **Make `_extract_parallel` accept both shapes**. Rejected. A tolerant unpack
  hides a real signature change and adds a branch that production code never
  takes.

---

## Decision 8 - Return a pair from the resolution rule

**Decision**: `_resolve_entity_id` returns `tuple[str, str]`. The first item is
the entity identifier. The second item is the branch name.

**Rationale**: The caller needs both the identifier and the branch. A single
return value would force the caller to work out the branch again, which
Requirement FR-013 forbids.

**Alternatives considered**:

- **Return only the identifier and compare it against the strategy value**.
  Rejected. The comparison gives a wrong answer when the strategy field and a
  fallback field hold the same value.
- **Return a small dataclass**. Rejected. A pair of two text values needs no new
  type, and a new type would add a name that only one caller reads.

---

## Open questions

None. Every entry in the Technical Context holds a resolved value.

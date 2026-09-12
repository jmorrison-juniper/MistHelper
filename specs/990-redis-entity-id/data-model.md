# Phase 1 Data Model: Redis Time-Series Entity Identifier Fallback

**Feature**: `990-redis-entity-id` | **Date**: 2026-07-29

This feature stores no new data. It changes how the writer chooses one value that
already travels through the extraction path. The entities below describe the
values in memory. No table, no index, and no migration changes.

---

## 1. Record

One row of exported data from a Mist API endpoint.

| Property | Type | Notes |
| - | - | - |
| Shape | `dict[str, Any]` | The writer reads the record and never writes to it. |
| Identifier fields | Text values | Named by the primary key strategy or by the fallback list. |
| Numeric fields | Integer or float values | The writer turns each one into a time-series point. |

**Validation rules**:

- The writer accepts an empty record and produces the `unknown` identifier.
- The writer never raises an error for a missing field.
- The writer treats a boolean value as non-numeric, which the existing
  `_extract_numeric` helper already enforces.

---

## 2. Primary key strategy

The table entry that names the primary key fields for one endpoint.

| Property | Type | Notes |
| - | - | - |
| `primary_key` | `list[str]` | The writer passes this list to `_pick_entity_field`. |
| `ts_value_fields` | `list[str]` or `None` | Optional allow-list of numeric fields. |
| `ts_label_fields` | `list[str]` or `None` | Optional label fields. This feature does not read it. |

**Validation rules**:

- `_pick_entity_field` reads the `primary_key` list.
- It returns the first matching name from the fallback list.
- It returns the first primary key when no name matches.
- It returns the text `id` for an empty list.

---

## 3. Entity identifier

The text value that names the subject of one time series.

| Property | Type | Notes |
| - | - | - |
| Value | `str` | The writer always converts the source value with `str()`. |
| Source field | `str` | Either the strategy field or one fallback field. |
| Sentinel | `"unknown"` | The final fallback. It keeps the key length stable. |

**Validation rules (the usable-value test)**:

A field holds a usable value when all three conditions are true.

1. The record carries the field.
2. The value is not `None`.
3. The text form of the value is not empty after the removal of the surrounding
   blank space.

The number `0` therefore holds a usable value. The text `""` and the text `"   "`
do not.

---

## 4. Fallback list

The ordered list of common entity identifier field names.

| Property | Value |
| - | - |
| Name | `BATCH_ENTITY_FALLBACK_KEYS` |
| Type | `tuple[str, ...]` |
| Order | `device_id`, `site_id`, `org_id`, `mac`, `id` |
| Scope | Module level in `src/db/redis_writer.py` |
| Readers | `_pick_entity_field` and `_resolve_entity_id` |

**Validation rules**:

- The order decides the winner when a record carries two fallback fields.
- The list is a tuple, so no caller can change it at run time.

---

## 5. Resolution source

The name of the branch that produced the entity identifier.

| Value | Meaning |
| - | - |
| `strategy` | The strategy field held a usable value. |
| `fallback` | A field in `BATCH_ENTITY_FALLBACK_KEYS` held a usable value. |
| `unknown` | No field held a usable value. |

**Validation rules**:

- The rule returns exactly one of the three values for every record.
- The counts of the three values always sum to the record count of the chunk.

---

## 6. Resolution summary

The aggregate count of the three branches for one extraction call.

| Property | Type | Notes |
| - | - | - |
| Container | `collections.Counter[str]` | Keyed by the resolution source. |
| Scope of a chunk counter | One worker thread | The worker never shares it. |
| Scope of the merged counter | One extraction call | `_extract_parallel` merges the chunk counters. |
| Emission | One `structlog` debug event | `_extract_all_adds` emits it once per call. |

**Validation rules**:

- The writer emits no log line for a single record.
- The writer emits one summary event for each extraction call.
- The summary reports counts only. It reports no record content.

---

## 7. Time-series key

The three-part key that Redis TimeSeries uses for one metric of one entity.

| Property | Value |
| - | - |
| Shape | `{api_function_name}:{entity_id}:{field_name}` |
| Separator | The colon character |
| Part count | Always three |

**Validation rules**:

- The shape does not change. A change would orphan every stored series.
- A record that carries a usable value in the strategy field produces a
  byte-identical key before and after this change.

---

## Resolution decision table

The table below is the complete behavior of `_resolve_entity_id`. The
implementation and the tests must agree with it.

| Strategy field | First usable fallback field | Returned identifier | Returned source |
| - | - | - | - |
| Holds a usable value | Not read | The text form of the strategy value | `strategy` |
| Absent from the record | Present | The text form of the fallback value | `fallback` |
| Present with the value `None` | Present | The text form of the fallback value | `fallback` |
| Present with an empty text value | Present | The text form of the fallback value | `fallback` |
| Present with a blank-space text value | Present | The text form of the fallback value | `fallback` |
| Holds the number `0` | Not read | The text `0` | `strategy` |
| Not usable | None of the five names is usable | The text `unknown` | `unknown` |
| Absent from an empty record | Absent | The text `unknown` | `unknown` |

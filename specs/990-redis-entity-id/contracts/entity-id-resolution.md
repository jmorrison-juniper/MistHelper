# Contract: Entity Identifier Resolution

**Feature**: `990-redis-entity-id` | **Date**: 2026-07-29

MistHelper is a command-line tool. It exposes no public network interface for
this feature. The contract below therefore covers two internal surfaces. The
first surface is the resolution rule inside `RedisTimeSeriesWriter`. The second
surface is the time-series key that a downstream reader queries.

---

## Surface 1 - `RedisTimeSeriesWriter._resolve_entity_id`

### Signature

```text
@staticmethod
def _resolve_entity_id(record: dict[str, Any], entity_key_field: str) -> tuple[str, str]
```

### Inputs

| Name | Type | Contract |
| - | - | - |
| `record` | `dict[str, Any]` | One exported row. The method reads it and never changes it. An empty dictionary is valid input. |
| `entity_key_field` | `str` | The field name that `_pick_entity_field` chose from the primary key strategy. |

### Outputs

| Position | Type | Contract |
| - | - | - |
| 0 | `str` | The entity identifier. Never `None`. Never an empty text value. |
| 1 | `str` | The resolution source. Exactly one of `strategy`, `fallback`, or `unknown`. |

### Behavior

1. Read `entity_key_field` from the record. If that field holds a usable value,
   return the text form of the value and the source `strategy`.
2. Walk `BATCH_ENTITY_FALLBACK_KEYS` in order. Return the text form of the first
   usable value and the source `fallback`.
3. Return the text `unknown` and the source `unknown`.

A field holds a usable value when all three conditions are true. The record
carries the field. The value is not `None`. The text form of the value is not
empty after the removal of the surrounding blank space.

### Invariants

- **INV-1**: The method raises no exception for any dictionary input.
- **INV-2**: The method changes no input and holds no state between calls. It is
  safe to call from many threads at the same time.
- **INV-3**: When the strategy field holds a usable value, the returned
  identifier equals `str(record[entity_key_field])`. This invariant guards
  Success Criterion SC-002 and Functional Requirement FR-005.
- **INV-4**: The returned identifier is never an empty text value, so the key
  always holds three non-empty parts.
- **INV-5**: The number `0` resolves to the text `0` and not to the text
  `unknown`.

### Errors

The method defines no error path. It returns the sentinel instead of raising.

---

## Surface 2 - `RedisTimeSeriesWriter._is_usable`

### Signature

```text
@staticmethod
def _is_usable(value: Any) -> bool
```

### Behavior

| Input | Result |
| - | - |
| `None` | `False` |
| `""` | `False` |
| `"   "` | `False` |
| `0` | `True` |
| `0.0` | `True` |
| `False` | `True` |
| `"dev-1"` | `True` |
| `" dev-1 "` | `True` |

The value `False` returns `True`, because the rule tests for absence and for an
empty text value only. The rule does not test for a false value. An entity
identifier is never a boolean in practice.

---

## Surface 3 - The time-series key

### Shape

```text
{api_function_name}:{entity_id}:{field_name}
```

### Contract

| Rule | Statement |
| - | - |
| Part count | The key always holds three parts that a colon separates. |
| Part 1 | The API function name. This feature does not change it. |
| Part 2 | The entity identifier from Surface 1. |
| Part 3 | The numeric field name. This feature does not change it. |
| Stability | A record that carries a usable value in the strategy field produces a byte-identical key before and after this change. |
| Sentinel | The text `unknown` stays as the final fallback, because `RedisJSONWriter._build_key` depends on a stable key length. |

### Compatibility

The change is backward compatible for every record that already resolved to a
real identifier. The change alters the key only for a record that previously
landed in the `unknown` bucket. Those records had no usable series before, so no
correct history splits.

No migration runs. A key that the store already holds under the text `unknown`
stays as it is.

---

## Surface 4 - The resolution summary event

### Emission point

`RedisTimeSeriesWriter._extract_all_adds` emits the event once for each call.

### Event contract

| Property | Value |
| - | - |
| Level | Debug |
| Logger | `redis_writer` |
| Field 1 | The count of records that used the strategy field. |
| Field 2 | The count of records that used a fallback field. |
| Field 3 | The count of records that used the `unknown` sentinel. |

### Rules

- The writer emits no log line for a single record.
- The three counts sum to the record count of the extraction call.
- The event carries counts only. It carries no record content and no credential.
- The event text uses ASCII characters only.

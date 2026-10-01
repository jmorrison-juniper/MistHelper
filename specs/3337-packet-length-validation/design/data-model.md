# Data Model: Packet Length Validation

**Issue**: #3337

This correction uses existing values and return types.
It adds no entity class, field, schema, storage, or migration.

## Packet Length Selection

| Existing value | Type | Rule |
| --- | --- | --- |
| Terminal response | `str` | The real `InputUtils.safe_input` trims surrounding whitespace. |
| Shared `default` | `int` | Preserve 128 unless the caller supplies another valid default, including 1300. |
| Wireless specification default | `str` | Preserve `"1300"`. |
| Valid packet length | `int` | Accept 64 through 1536, inclusive. Return the integer unchanged. |
| Invalid selection | `None` | Reject conversion failure or an integer outside the range. |

The existing `int()` conversion defines the accepted integer text.
Do not add a regular expression, rounding, clamping, or another conversion policy.
Do not substitute a default for invalid nonblank input.

## Wireless Bounded Settings

The existing collection return type is `tuple[int, ...] | None`.
A successful collection contains exactly these three values, in this order:

| Position | Existing field | Unchanged validation | Unchanged default |
| --- | --- | --- | --- |
| 1 | `duration` | 60 through 86400 seconds | 60 |
| 2 | `num_packets` | 0 through 10000 packets | 1024 |
| 3 | `max_pkt_len` | 64 through 1536 bytes | 1300 |

The existing `_Settings` object receives the complete valid tuple.
Its unrelated fields remain unchanged.
The collector returns `None` after any invalid value.
It never returns a partial result.

## State Transitions

1. The existing prompt sends its text to `InputUtils.safe_input`.
2. Normal input returns trimmed text.
3. Empty or whitespace-only input selects the existing default.
4. EOF returns the existing default and logs the disconnect notice.
5. `KeyboardInterrupt` returns an empty string and logs the cancellation notice.

The existing validator converts that result with `int()`.
Successful conversion reaches the inclusive range check.
A valid integer returns unchanged.
Conversion failure or range failure returns `None`.
After an interruption, the validator rejects the empty string.
It returns `None`, not a default.

The wireless collector processes the duration, packet count, and packet length in order.
It stops on `None`.
Otherwise, it returns the three integers.

## Capture Relationship

The shared prompt serves existing site and organization capture paths.
The organization path stops before payload creation on `None`.
The wireless collector stops before later settings or capture actions on `None`.
Existing fixed lengths of 1300 and 1500 do not pass through a new validator.
They remain unchanged and already satisfy the maximum.

See [contracts/prompt-limits.md](contracts/prompt-limits.md) for messages and return behavior.

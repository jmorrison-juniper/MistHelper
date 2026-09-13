# Contract: Filter Operator Semantics

## Scope

Defines required behavior for MAC and manufacturer operator evaluation.

## Shared Operators

- `is`
- `is not`
- `contains`
- `doesn't contain`
- `starts with`
- `doesn't start with`
- `ends with`
- `doesn't end with`
- `is blank`
- `is not blank`
- `is null`
- `is not null`

## Required Rules

1. MAC and manufacturer must support identical operator catalogs.
2. Value-based operators require non-empty normalized values.
3. Null/blank operators execute without requiring values.
4. MAC comparison is case-insensitive and delimiter-insensitive.
5. Manufacturer comparison is case-insensitive with positional semantics equivalent to MAC operators.
6. If both fields are filtered, final result is `MAC_MATCH AND MFG_MATCH`.
7. Remote filtering may pre-reduce candidates, but local evaluation is authoritative.
8. For value-based manufacturer operators (including negated forms), blank/missing manufacturer values are non-matches; blank/null records match only when blank/null operators are explicitly selected.

## Remote Prefilter Subset (Optimization-Only)

To avoid semantic drift between Mist query behavior and local operator semantics, remote prefiltering is limited to this positive subset when endpoint behavior supports equivalent meaning:

- `is`
- `contains`
- `starts with`
- `ends with`

All negated operators and blank/null operators are evaluated locally only. Even when remote prefiltering is used, the final inclusion decision must be produced by local operator evaluation.

## Failure Behavior

- Invalid operator/value combinations must fail fast with clear user-facing validation messaging.
- No records should be emitted as matched when validation fails.

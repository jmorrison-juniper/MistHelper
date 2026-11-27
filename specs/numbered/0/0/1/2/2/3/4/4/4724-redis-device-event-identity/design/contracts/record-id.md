# Contract: record_id derivation

This contract defines the `record_id` field that the router adds to each device event row. The router applies the contract before both backend writes (decision D-5).

## Scope

- Applies to each row of `searchOrgDeviceEvents` that `DatabaseRouter.write` receives (RC-09, RC-10).
- Does not apply to other endpoints. Decision D-9 limits the scope.

## Input

- One mapping as the export path passes it (RC-18).
- The mapping may hold any JSON-compatible value. A value that JSON cannot encode converts with `str`.

## Output

- A new mapping. It holds every input field with the same value, plus one field named `record_id`.
- The input mapping does not change. The router writes only the copy to the backends.

## Derivation

1. Serialize the input with `json.dumps(row, sort_keys=True, default=str)`. This matches `_hash_payload` (RC-11).
2. Hash the serialized text with SHA-256.
3. Store the hexadecimal digest as `record_id`. The digest has 64 lowercase characters.

## Invariants

- The same input gives the same `record_id` in every run.
- The order of keys in the input does not change the result.
- Two rows that differ in any field get different values.
- CSV and SQLite outputs use the original rows, so they never receive `record_id`.

Caution: A change in exporter flattening changes the input. Each changed input produces a new `record_id`, and the old document stays until its TTL ends.

## Errors

- A row that is not a mapping fails the write before any backend call. The router does not catch this error.
- A value that JSON cannot encode does not raise an error, because `default=str` converts it.

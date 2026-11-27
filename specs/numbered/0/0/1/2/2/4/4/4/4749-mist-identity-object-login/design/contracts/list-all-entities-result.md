# Contract: ApiResult from list_all_entities

## Inputs

- `entity_type`: the registry key, for example `self_identity`.
- `ids`: a dictionary of the identifiers that the registry entry needs. The entry `self_identity` needs none.

## Output

- `ApiResult` with two fields: `status_code` (an integer) and `data` (a list of records, or the error body of a failed call).

## Rules for Object Endpoints

An object endpoint has `object_response` set to true (decision D-1).

- The service makes one protected SDK call and never follows a `next` cursor (decision D-2, FR-005).
- A 2xx response with a non-empty dictionary yields one record. A 2xx response with a list yields the list records. Any other body yields no record (decision D-3).
- The status is the status of that one response (FR-002).

## Rules for List Endpoints

An endpoint without the flag keeps the rule of issue #1884.

- The service follows the `next` cursor for each page (research row 3).
- Each page contributes its list body only. A dictionary body contributes no record (research row 1).
- The status is the status of the last page (research row 2).

## Guarantees That Do Not Change

- A failed call returns the error body and no record. The existing tests cover this rule (research rows 19, 21, and 22).
- The retry loop for HTTP 429 keeps its bounded count and its backoff.

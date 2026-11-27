# Contract: Gateway Selection for History

## Function

- `LiveHistory.read(service, records, kind, cache_only=False, window=None)` returns `(summaries, error)`. The class and the method are at `src/interfaces/wan_performance/presentation/live_routes.py` (R19, R20).
- `service` supplies `org_id` and `history`.
- `records` is the tuple of selected records (R94).
- `kind` is `gateway`, `port`, or `peer`.
- The optional parameters `cache_only` and `window` do not change in this issue (F-14).

## Ordered Rules

1. When `cache_only` is true, when `window` is set, or when `kind` is not one of the three kinds, return no summaries and no error.
2. Resolve the identity with `_select_identity`.
3. For the gateway kind, collect the distinct gateway identities of the gateway, circuit, and peer records (R22). Return the gateway only when exactly one exists (R23) and it belongs to `service.org_id` (R99).
4. For the port and peer kinds, require exactly one selected record (R100). Return its identity when its gateway belongs to `service.org_id` (R99).
5. When no identity resolves, return no summaries and the refusal message for the kind (R24, R25).
6. When `service.history` is absent, return no summaries and the store-missing message (R96).
7. Read the history of the identity over the thirteen-month window. Build the summaries. Return them with no error (R20).
8. When the store read raises a listed error, log the exception. Return no summaries and the store-error message (R97).

## Exact Messages

| Name | Text |
| - | - |
| Gateway refusal | Select records for exactly one full gateway identity to read history. |
| Port-or-peer refusal | Select one port or peer path to read history. |
| Store missing | History is unavailable. The selected application store is not available. |
| Store error | History is unavailable. The selected application store did not return valid records. |

Caution: do not change any text in this table. Tests N4, N6, N9, and E2 compare these strings exactly.

## Log Events (T004)

| Event | Level | Content |
| - | - | - |
| Before the resolution | info | The count of selected records and the kind. |
| After the resolution | debug | The count of distinct gateway identities. |
| Before the history read | info | The window name. No identifier. |
| After the history read | debug | The count of summaries built. |
| Storage error | error | The existing exception message and traceback. |

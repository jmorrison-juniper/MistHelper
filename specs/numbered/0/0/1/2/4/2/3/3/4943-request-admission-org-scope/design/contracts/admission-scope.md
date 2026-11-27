# Contract: Organization Scope and Shared Admission

This contract defines the public behavior of `OrganizationScope` and the attribution rules of `RequestLedger.admit`. The names match the ship design in `plan.md`.

## Interface

- `OrganizationScope.block(org_id)`: A context manager. It accepts one organization identifier. It refuses an empty identifier before it changes the context value. It ends the scope on every exit path, including an exception.
- `OrganizationScope.current()`: Returns the active organization identifier, or `None` when no scope is active.
- `RequestLedger.admit(request)`: Reserves one request attempt. It returns nothing when it admits the request. It raises `ConnectionError` when it refuses the request.

## Refusal of an empty identifier

- Input: an empty string, or a string that holds only white space.
- Result: `ValueError` with the message "Organization scope requires a non-empty organization identifier."
- Effect: The context value does not change. No block starts.

## Attribution rules

| Request path | Ledger organization | Active scope | Attribution | Result |
|--------------|---------------------|--------------|-------------|--------|
| The fourth segment is `orgs` | Any | Any | The organization in the fifth segment | Admitted |
| The fourth segment is `sites` | Set | Any | The ledger organization | Admitted |
| The fourth segment is `sites` | Unset | Active | The scope organization | Admitted |
| The fourth segment is `sites` | Unset | Unset | None | Refused with the message below |
| Any other segment | Any | Any | The ledger organization, which can be none | Admitted |

Refused message: "Site API request admission requires a selected organization."

## Credential rules

- A request with neither an `Authorization` header nor a `Cookie` header is refused with "Shared API admission requires configured authentication."
- The ledger stores the SHA-256 hex digest of the header value. The ledger never stores the header value.

## Quota rule

- A request is refused with "The shared Mist API hourly quota is exhausted." when the reservation returns a result other than 1.

## Thread rule

- A scope applies to the context that set it. A new thread starts with no active scope. A site request in that thread is refused.

## Evidence

- Branch source: `src/interfaces/wan_performance/collection/request_admission.py`, lines 22 to 55 and 133 to 143.
- Main source for the attribution path: `src/interfaces/wan_performance/collection/request_admission.py`, lines 102 to 109.
- Tests: `test_site_request_uses_the_scoped_organization`, `test_organization_scope_ends_with_its_block`, `test_nested_organization_scope_restores_outer_value`, `test_organization_scope_resets_after_exception`, and `test_organization_scope_rejects_empty_identifier`.

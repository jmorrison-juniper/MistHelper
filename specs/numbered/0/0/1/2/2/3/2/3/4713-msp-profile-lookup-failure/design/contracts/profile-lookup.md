# Contract: Profile Lookup

This contract defines the profile lookup in `src/foundation/support/refactors/msp_privilege_detection.py`. It names the call, the result, the accepted responses, and the log text. Log text is ASCII. Log text carries no response body, no exception message, and no secret.

## Identity

- Module: `src.foundation.support.refactors.msp_privilege_detection`
- New public names:
  - `MspPrivilegeLookup`, a frozen dataclass with `succeeded: bool` and `grants: list[dict[str, Any]]`.
  - `lookup_msp_privileges(session: Any) -> MspPrivilegeLookup`.
- Kept public name:
  - `detect_msp_privileges(session: Any) -> list[dict[str, Any]]`. It returns `lookup_msp_privileges(session).grants`.
- Kept private helper:
  - `_msp_fetch_user_data(session: Any) -> dict[str, Any] | None`. It keeps its name and its return type. It now checks the status and the `privileges` list before it returns the body.
- SDK call: `mistapi.api.v1.self.self.getSelf(session)` (RC-51). The path is `/api/v1/self` (RC-52).

## Accepted Responses

| Condition | Result | Log level and text |
| - | - | - |
| Session is falsy | Failed lookup. No API call. | Warning: `MSP profile lookup failed: no active session.` |
| `getSelf` raises | Failed lookup | Warning: `MSP profile lookup failed: getSelf raised %s.` The argument is the exception class name only. |
| Response is None or has no `data` attribute | Failed lookup | Warning: `MSP profile lookup failed: getSelf returned no response.` |
| Status is not an integer | Failed lookup | Warning: `MSP profile lookup failed: getSelf returned no HTTP status.` |
| Status is outside 200 through 299 | Failed lookup | Warning: `MSP profile lookup failed: getSelf returned HTTP %s. MSP access is not confirmed.` The argument is the status code. |
| Body is not a JSON object | Failed lookup | Warning: `MSP profile lookup failed: profile body is not a JSON object.` |
| Body has no `privileges` list | Failed lookup | Warning: `MSP profile lookup failed: profile has no privileges list.` |
| Status is 2xx, body is a JSON object, `privileges` is a list of zero entries | Valid profile. `grants` is empty. | Debug: `MSP profile lookup succeeded with %d MSP grant(s).` The argument is 0. |
| Status is 2xx, body is a JSON object, `privileges` is a list with MSP grants | Valid profile. `grants` holds the parsed MSP grants. | Debug: `MSP profile lookup succeeded with %d MSP grant(s).` |

## Rules

1. The lookup never raises. Every error path returns a failed lookup.
2. The lookup sends one API call for each call to `lookup_msp_privileges`, except for a missing session, which sends none.
3. A failed lookup always has `grants` set to an empty list.
4. `detect_msp_privileges` never raises, and it returns an empty list for every failed lookup.
5. The warning text does not change between runs. An operator can search the log for the prefix `MSP profile lookup failed`.

## Example Lookup Results

- HTTP 403 with body `{"detail": "You do not have permission to perform this action."}`: failed lookup. The warning reads `getSelf returned HTTP 403`.
- HTTP 200 with body `{"privileges": []}`: valid profile with zero MSP grants.
- HTTP 200 with body `{"privileges": [{"msp_id": "msp-1234abcd", "msp_name": "Acme MSP", "role": "admin", "scope": "msp"}]}`: valid profile with one MSP grant.

# Contract: MSP organization listing right

## Identity

- **Subject**: `SubscriptionExpiryClient` in `src/mist/intelligence/reports/subscription_expiry/client.py`.
- **Members**: the class attribute `MSP_GRANT_SCOPE`, the static method `_has_msp_listing_right`, and the MSP branch in `discover_organizations`.

## Input

- One profile grant from the `GET /api/v1/self` response.
- Only mapping grants reach the check. Other values are ignored before the check.

## Rule

| Grant state | Listing right | Listing call | Result |
| - | - | - | - |
| `msp_id` is a non-empty string, and `scope` is `msp` | Present | Sent (`listMspOrgs`) | Organizations are added. An HTTP error adds a failed row. |
| `msp_id` is a non-empty string, and no `scope` key exists | Present (D3) | Sent | Same as above |
| `msp_id` is a non-empty string, and `scope` is `org`, `orggroup`, `site`, `sitegroup`, or None | Absent | Not sent | A skipped row, unless another grant for the same MSP holds the right |
| `msp_id` is absent, empty, or not a string | Not applicable | Not sent | No MSP row, as before |

## Reason Text

The reason text for a skipped row reads as follows:

The account lacks the MSP organization listing right. The grant scope is "org", not "msp". The MSP organization list was not requested.

The quoted scope value comes from the profile grant. The sentence order does not change.

## Outputs

- The check returns True or False. It changes no state.
- The check logs an `info` line before the decision and a `debug` line after it (FR-011).
- The check never logs a token, a request header, or the full profile.

## Examples

| Grant | Result |
| - | - |
| `{"msp_id": "msp-1", "scope": "msp", "role": "read"}` | Listing call sent for `msp-1` |
| `{"msp_id": "msp-1", "scope": "org", "org_id": "org-1", "role": "read"}` | Skipped row for `msp-1` |
| `{"msp_id": "msp-1", "role": "admin"}` | Listing call sent for `msp-1` (D3) |

# Data Model: WAN VPN Update Response

This feature adds no stored entity or schema.

## Update response

| Field | Type | Rule |
| --- | --- | --- |
| `status_code` | Integer or `None` | Values from 200 through 299 confirm success. `None` and all other values fail. |
| VPN identifier | String | Include it in the failure log to identify the rejected update. |

The response is the existing `APIResponse` returned by `updateOrgVpn`. The tool does not store its body.

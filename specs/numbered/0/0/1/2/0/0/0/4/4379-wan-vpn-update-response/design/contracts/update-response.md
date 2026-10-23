# VPN Update Response Contract

The manager calls the existing `mistapi.api.v1.orgs.vpns.updateOrgVpn` method.

| SDK result | Manager result | Operator log |
| --- | --- | --- |
| HTTP status from 200 through 299 | Return the changed path count | Keep the existing success message |
| HTTP status below 200 or at least 300 | Fail the VPN update and stop later updates | Include the VPN identifier and status |
| Missing HTTP status | Fail the VPN update and stop later updates | Include the VPN identifier and `None` status |
| SDK exception | Keep existing exception handling | Include the exception and VPN identifier |

Log no response body, API token, or other credential. Unit tests must mock every SDK call.

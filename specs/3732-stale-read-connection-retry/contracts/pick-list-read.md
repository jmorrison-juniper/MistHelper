# Contract: Portal pick-list reads

## Mist SDK methods

| Picker | SDK method |
| - | - |
| Organization sites | `mistapi.api.v1.orgs.sites.listOrgSites` |
| Site devices | `mistapi.api.v1.sites.devices.listSiteDevices` |
| Wireless clients | `mistapi.api.v1.sites.clients.searchSiteWirelessClients` |
| Wired clients | `mistapi.api.v1.sites.wired_clients.searchSiteWiredClients` |

The site device call passes `type="all"` when no narrower type is selected.
No picker adds a direct HTTP call.

## Response contract

| Status | Data | Portal result |
| - | - | - |
| `None` | Any value | Failed read |
| Missing or unusable | Any value | Failed read |
| 200 through 299 | Rows | Successful rows |
| 200 through 299 | Empty | Valid empty result |
| 300 through 399 | Any value | Failed read |
| 400 or more | Any value | Failed read |

## Failure output

The route returns an empty list for list compatibility.
It also returns this reason:

> The portal could not reach the Mist API. Try again.

The route does not use the no-rows reason for a failed read.
The log names the picker operation, target identifier, and status.
The log contains no secret.

## Valid empty output

An empty HTTP 2xx response uses the existing reason:

> The Mist API answered with no rows for this request.

This result does not contain the reachability reason.

## Client merge contract

- Return valid rows when either client source returns rows.
- Log a failed source even when the other source returns rows.
- Return a valid empty result when both sources return empty HTTP 2xx answers.
- Return a failed result when no source returns rows and at least one source fails.
- Keep wireless and wired row labels unchanged.

# Contract: The simulated cloud

**Feature**: #3200 | **Package**: `tests/support/upgrade_portal_e2e/harness/cloud/`

This contract states what `SimulatedMistSession` gives to the shipped code.
The shipped code sees the session through `identity.OperatorSession` and
through the sign-in seams. See [journey-server.md](journey-server.md).

## The session object

| Member | Value | Why the shipped code reads it |
| - | - | - |
| `privileges` | One `org` privilege for each organization of the fleet | The organization picker |
| `_MAX_429_RETRIES` | `0` | The destructive-write guard |
| `_session` | An object with `adapters == {}` | The destructive-write guard |
| `mist_get(uri, query=None)` | A `SimulatedResponse` | Each read, and each page of `mistapi.get_all` |
| `mist_post(uri, body=None)` | A `SimulatedResponse` | Each write and each cancel |
| `mist_put(uri, body=None)` | A `SimulatedResponse` | No shipped call today. The router answers 404. |
| `mist_delete(uri, query=None)` | A `SimulatedResponse` | No shipped call today. The router answers 404. |

Each session belongs to one operator. Each session reads the same
`SimulatedOrganization` and the same ledger.

## The answer object

`SimulatedResponse` has the members that the shipped code reads.

| Member | Rule |
| - | - |
| `status_code` | The HTTP status. `None` for an `uncertain` answer. |
| `data` | A deep copy of the answer body. An empty dictionary for an `uncertain` answer. |
| `raw_data` | The JSON text of `data`. |
| `next` | The URI of the next page, or `None`. |
| `headers` | `X-Page-Total`, `X-Page-Limit`, and `X-Page-Page` for a list read. |
| `url` | The URI and the query of the call. |
| `proxy_error` | `False`. |

## Paging

- A list read takes `limit` and `page`. When more rows exist, `next` holds the
  same URI with `page` plus one.
- A search read takes `limit` and `search_after`. The body holds `results`,
  `total`, `limit`, `start`, `end`, and `next`.
- The default page size is the `limit` of the call. With no `limit`, the page
  size is 100.

## The route table

The URI templates come from the installed `mistapi` package. The handler
modules live in `handlers/`.

| SDK call | Method | URI template | Handler |
| - | - | - | - |
| `getSelf` | GET | `/api/v1/self` | `inventory` |
| `getOrg` | GET | `/api/v1/orgs/{org_id}` | `inventory` |
| `listOrgSites` | GET | `/api/v1/orgs/{org_id}/sites` | `inventory` |
| `listOrgSiteStats` | GET | `/api/v1/orgs/{org_id}/stats/sites` | `statistics` |
| `getOrgInventory` | GET | `/api/v1/orgs/{org_id}/inventory` | `inventory` |
| `listSiteDevices` | GET | `/api/v1/sites/{site_id}/devices` | `inventory` |
| `listSiteDevicesStats` | GET | `/api/v1/sites/{site_id}/stats/devices` | `statistics` |
| `listOrgDevicesStats` | GET | `/api/v1/orgs/{org_id}/stats/devices` | `statistics` |
| `listSiteAvailableDeviceVersions` | GET | `/api/v1/sites/{site_id}/devices/versions` | `inventory` |
| `listOrgAvailableDeviceVersions` | GET | `/api/v1/orgs/{org_id}/devices/versions` | `inventory` |
| `listOrgAvailableSsrVersions` | GET | `/api/v1/orgs/{org_id}/ssr/versions` | `inventory` |
| `searchOrgDeviceEvents` | GET | `/api/v1/orgs/{org_id}/devices/events/search` | `events` |
| `searchSiteDeviceEvents` | GET | `/api/v1/sites/{site_id}/devices/events/search` | `events` |
| `listDeviceEventsDefinitions` | GET | `/api/v1/const/device_events` | `events` |
| `searchSiteAlarms` | GET | `/api/v1/sites/{site_id}/alarms/search` | `statistics` |
| `searchOrgTunnelsStats` | GET | `/api/v1/orgs/{org_id}/stats/tunnels/search` | `statistics` |
| `searchSiteBgpStats` | GET | `/api/v1/sites/{site_id}/stats/bgp_peers/search` | `statistics` |
| `searchSiteSwOrGwPorts` | GET | `/api/v1/sites/{site_id}/stats/ports/search` | `statistics` |
| `searchSiteWiredClients` | GET | `/api/v1/sites/{site_id}/wired_clients/search` | `statistics` |
| `listSiteWirelessClientsStats` | GET | `/api/v1/sites/{site_id}/stats/clients` | `statistics` |
| `searchSiteWirelessClients` | GET | `/api/v1/sites/{site_id}/clients/search` | `statistics` |
| `searchSiteGuestAuthorization` | GET | `/api/v1/sites/{site_id}/guests/search` | `statistics` |
| `upgradeOrgDevices` | POST | `/api/v1/orgs/{org_id}/devices/upgrade` | `upgrades` |
| `getOrgDeviceUpgrade` | GET | `/api/v1/orgs/{org_id}/devices/upgrade/{upgrade_id}` | `upgrades` |
| `cancelOrgDeviceUpgrade` | POST | `/api/v1/orgs/{org_id}/devices/upgrade/{upgrade_id}/cancel` | `upgrades` |
| `upgradeSiteDevices` | POST | `/api/v1/sites/{site_id}/devices/upgrade` | `upgrades` |
| `listSiteDeviceUpgrades` | GET | `/api/v1/sites/{site_id}/devices/upgrade` | `upgrades` |
| `getSiteDeviceUpgrade` | GET | `/api/v1/sites/{site_id}/devices/upgrade/{upgrade_id}` | `upgrades` |
| `cancelSiteDeviceUpgrade` | POST | `/api/v1/sites/{site_id}/devices/upgrade/{upgrade_id}/cancel` | `upgrades` |
| `upgradeDevice` | POST | `/api/v1/sites/{site_id}/devices/{device_id}/upgrade` | `upgrades` |
| `upgradeOrgSsrs` | POST | `/api/v1/orgs/{org_id}/ssr/upgrade` | `upgrades` |
| `listOrgSsrUpgrades` | GET | `/api/v1/orgs/{org_id}/ssr/upgrade` | `upgrades` |
| `getSiteSsrUpgrade` | GET | `/api/v1/sites/{site_id}/ssr/upgrade/{upgrade_id}` | `upgrades` |
| `cancelOrgSsrUpgrade` | POST | `/api/v1/orgs/{org_id}/ssr/upgrade/{upgrade_id}/cancel` | `upgrades` |

A static route wins over a route with a variable. For example,
`/devices/versions` and `/devices/upgrade` win over `/devices/{device_id}`.

## The answer rules

- Each answer follows the answer schema of the local OpenAPI 3.1 file and the
  rules of `src/upgrade_portal/app/seam_shapes.py` (FR-012).
- The capture reads and the upgrade reads use the same device state (FR-017).
- The event search filters by `device_type`, `type`, `start`, and `end`. It
  answers in pages (FR-018). The event type names come from the answer of
  `listDeviceEventsDefinitions`. The handler holds no copy of a settle rule
  (FR-013).
- The account read gives the stand-in operator address and the account label
  (FR-019).

## The write rules

1. The router finds the write call.
2. `WriteShapeCheck` examines the body against the request schema of research
   R-05. A break gets status 400. The answer names the key.
3. The fault book gives the answer: `accept`, `reject`, or `uncertain`.
4. For `accept` and `uncertain`, the organization makes one `UpgradeJob` and
   moves each device to `queued`.
5. For `uncertain`, the caller gets `status_code` `None` and empty `data`.
6. The ledger records the call, the write key, and the answer.

## The cancel rules

- A cancel moves each device in `queued` to `cancelled`.
- A cancel reports each device in `downloading` or `rebooting` as a device that
  continues (FR-035).
- The answer follows the `OK` answer of the OpenAPI file.

## The unknown URI rule

An unknown method and URI get status 404 and the body
`{"detail": "not modeled by the journey harness"}`. The ledger records a
`HarnessGap`. The check at the end of the step fails, and the failure names
the call (SR-004).

## Threads

One lock guards the state of the organization. Each handler holds that lock.
Each answer is a deep copy, so no caller can change the state.

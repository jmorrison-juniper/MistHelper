# Research: WebSocket Client Selection

## Decision: Use the wired-client search only for a selected EX switch

The local endpoint reference documents `GET /api/v1/sites/{site_id}/wired_clients/search`. It documents an optional `device_mac` filter. Its response contains `site_id`, `mac`, `device_mac`, and `device_mac_port` fields. The response records can support a device-scoped list when each row also passes explicit site and device association checks.

Before implementation, the picker stored an `id`, label, family, and detail in each device row. It did not retain a distinct device MAC field. The new lookup resolves the selected device ID against the site-scoped cache and reads an explicit MAC from the original Mist record. It does not split or reinterpret `device_id`.

The endpoint reference names the SDK path `mistapi.api.v1.sites.clients_-_wired.searchSiteWiredClients()`. Existing repository code calls `mistapi.api.v1.sites.wired_clients.searchSiteWiredClients(...)`. The checked-in source proves an existing call path, but not the signature of the pinned SDK version.

**Rationale**: The query and response both carry device association data. A filter alone is not enough evidence. The response must match the selected site and selected device.

**Alternatives considered**: Treat every site wired client as belonging to the selected switch. Rejected because it can show clients from another switch.

## Decision: Keep SRX and SSR discovery unavailable until association is proven

The local WAN-client reference documents `GET /api/v1/sites/{site_id}/wan_clients/search`. Its schema does not document a selected-gateway identifier. The endpoint reference names `mistapi.api.v1.sites.clients_-_wan.searchSiteWanClients()`. The feature specification names `mistapi.api.v1.sites.wan_clients.searchSiteWanClients`. This module-path difference remains unverified.

The available WAN response schema also does not document a client `mac` field. Its context text says that WAN-client search returns MAC data, but the schema lists `wcid` instead. Do not treat `wcid` as a MAC without SDK evidence.

The initial local interpreter was Python 3.9.6 with mistapi 0.55.14. The repository requires Python 3.13 or newer and mistapi 0.64.x. The normal worktree bootstrap created `.venv` with Python 3.13 and mistapi 0.64.0. No live API call was made.

**Rationale**: Site membership does not prove that a client belongs to one selected gateway. An unsupported selector can direct a disruptive release at the wrong client.

**Alternatives considered**: Use all site WAN clients for every SRX or SSR device. Rejected because the association is unproven. Infer association from a device ID or client history. Rejected because neither proves current target membership.

## Decision: Preserve manual input and request bodies

`UtilityFieldFactory` defines optional `macs` as `FieldKind.MAC_LIST` and optional `mac_address` as `FieldKind.MAC`. `CommandBodyBuilder` copies `macs` into DHCP-release requests and `mac_address` into MAC-table requests. Empty optional values are omitted by the current field checker.

The DHCP list checker accepts one to 48 unique, complete MAC addresses. It normalizes them. The scalar MAC checker also accepts a complete MAC and normalizes it. It does not accept a partial or wildcard filter.

The current WebSocket scalar validator accepts complete MAC addresses and normalizes them. The pinned SDK documentation does not define partial or wildcard `mac_address` filters. The implementation leaves validation unchanged and does not claim support for undocumented forms.

**Rationale**: Suggestions must not remove the existing text field or silently change values that reach the SDK.

**Alternatives considered**: Replace the text input with a closed selection list. Rejected because it excludes disconnected clients and arbitrary supported filters. Change the SDK body or trigger path. Rejected because it changes utility meaning.

## Decision: Add no new transport and make lookup failures explicit

The existing picker route calls an app-scoped picker service. The picker service uses the authenticated SDK session. The existing page uses JSON requests and a serial counter to reject older picker responses.

Discovery uses that route and service pattern. It does not use a direct `fetch` to Mist, a raw HTTP client, a WebSocket trigger, or a device utility. It distinguishes successful empty results, 4xx errors, 5xx errors, timeout, and unavailable support.

The client lookup must have a ten-second limit. If supported pagination cannot finish in that limit, the page must show an unavailable state. It must not show partial rows as a complete list.

**Rationale**: The existing app owns credentials, error handling, and picker access. Reusing it avoids a second authentication path.

**Alternatives considered**: Call the Mist REST endpoint from browser JavaScript. Rejected because it would expose transport details and bypass the app's authenticated SDK boundary. Return an empty list on every failure. Rejected because it hides access and service errors.

## Evidence Sources

- `src/mist/realtime/websocket_streams/catalog/utilities/utility_fields.py`
- `src/mist/realtime/websocket_streams/intake/fields/scalar_checker.py`
- `src/mist/realtime/websocket_streams/intake/fields/list_checker.py`
- `src/mist/realtime/websocket_streams/intake/fields/checker.py`
- `src/mist/realtime/websocket_streams/live/runners/utility/triggers/body_builder.py`
- `src/mist/realtime/websocket_streams/intake/pickers/devices.py`
- `src/mist/realtime/websocket_streams/intake/pickers/records.py`
- `src/mist/realtime/websocket_streams/web/blueprint/routes/pickers.py`
- `src/mist/realtime/websocket_streams/web/static/websockets.js`
- `documentation/api/sites/GET_sites_site_id_wired_clients_search.md`
- `documentation/api/sites/GET_sites_site_id_wan_clients_search.md`
- `requirements.txt`

## SDK Verification Result

The worktree uses Python 3.13 with mistapi 0.64.0. Mocked tests verify the wired callable and scoped response handling. WAN search has no device filter and does not prove selected-gateway association. No credentials or live Mist calls were used.

## Subsequent Offline SDK Inspection

The normal worktree bootstrap created `.venv` with Python 3.13 and mistapi 0.64.0 after the initial environment probe failed.
No dependency manifest changed.

Offline source inspection verified these callable paths:

- `mistapi.api.v1.sites.wired_clients.searchSiteWiredClients` accepts `device_mac`, `limit`, and `search_after`. It calls `mist_get`.
- `mistapi.api.v1.sites.wan_clients.searchSiteWanClients` accepts client filters, `limit`, and `search_after`. It calls `mist_get` without a device filter.
- `mistapi.device_utils.__tools.mac.retrieve_mac_table` copies a nonempty `mac_address` string into the request body without normalization.

Source inspection does not prove that a device accepts every arbitrary string as a filter. It does not prove selected-gateway association in WAN results. Mocked association and payload regression tests pass. No SDK function or device utility was invoked during this inspection.

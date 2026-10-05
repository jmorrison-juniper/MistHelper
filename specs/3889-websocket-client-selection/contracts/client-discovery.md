# Client Discovery Contract

This document records the read-only discovery contract implemented for issue #3889.

## Request

The browser requests suggestions through an app-owned JSON route. The route accepts the selected `site_id`, `device_id`, and operation context. It does not accept a browser-supplied device MAC as proof of target association.

The server validates both identifiers. It resolves the device MAC from the existing site-scoped device record and uses the shared authenticated `mistapi` session.

## Wired Client Source

The local endpoint reference documents:

```text
GET /api/v1/sites/{site_id}/wired_clients/search
```

The endpoint accepts an optional `device_mac` query parameter. The response documents `site_id`, client `mac`, `device_mac`, and `device_mac_port` association fields.

Before a wired row becomes a choice, the server must verify:

1. The response site matches the selected site.
2. The response `mac` is a valid client MAC.
3. The association fields identify the selected device MAC.
4. The record is complete and not malformed.
5. The row belongs to the current operation and device family.

Do not trust the query filter as the only association check. Do not display a page of results as complete when the response indicates more data.

The documentation names `mistapi.api.v1.sites.clients_-_wired.searchSiteWiredClients()`. Existing repository code calls `mistapi.api.v1.sites.wired_clients.searchSiteWiredClients(...)`. The exact callable and supported pagination parameters require verification in mistapi 0.64.x.

## WAN Client Source

The local endpoint reference documents:

```text
GET /api/v1/sites/{site_id}/wan_clients/search
```

The documented response does not establish an association with one selected gateway. It also does not define `wcid` as a client MAC. The docs name `mistapi.api.v1.sites.clients_-_wan.searchSiteWanClients()`. The feature specification names a different module path.

Therefore, do not use this endpoint to populate SRX or SSR client choices until the pinned SDK and response contract establish the method, MAC field, and selected-gateway association. Keep manual fields available.

## Response States

The route returns a clear state for a complete result, an empty result, a request error, a service error, or an unavailable lookup.
Timeout uses `unavailable` with a distinct timeout reason and visible message. Do not convert an error into an empty list.

The page shows an accessible status message for each state. It keeps manual fields editable. It does not start, retry, or schedule a utility after a lookup failure.

Every request is bound to the selected site, device, operation, and generation. A stale result cannot change the current state or values.

## Submission Compatibility

The lookup is not a utility start. Selecting a result updates only the existing field.

- DHCP release sends selected and manually entered values through the existing optional `macs` list.
- MAC table retrieval sends the manually entered or selected value through the existing optional `mac_address` string.
- Empty optional fields remain omitted.
- The SDK request body and utility target remain unchanged.
- Existing confirmation, locks, validation, and cancellation behavior remain active.

The current checker rejects partial and wildcard `mac_address` values. The pinned SDK documentation does not define those forms. The implementation leaves this validator unchanged.

## Safety

Tests use fake SDK responses and intercepted browser requests. They make no live Mist calls and start no device utility. They do not invoke DHCP release, packet capture, or remote shell.

Require a human review before a DHCP release change merges. Do not use auto-merge.

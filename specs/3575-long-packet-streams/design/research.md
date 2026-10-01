# Research: Long packet streams

## Decision: Use the installed SDK without its utility wrapper

The installed SDK is `mistapi` 0.64.0.
Its `WebSocketWrapper` defaults `max_duration` to 60.
Its `start_with_trigger` calls the capture trigger before it creates the stream.
The existing `UtilityRunner` also supplies `duration=60`.

The dedicated runner uses `_MistWebsocket`.
It registers callbacks before `connect(run_in_background=True)`.
It requires `channel_subscribed` for the exact channel before capture start.

Changing the shared utility wrapper would change unrelated commands.
That alternative does not meet the scope requirement.

## Decision: Preserve verified scope and regional authentication

The SDK builds the stream host from the current session's `_cloud_uri`.
It changes `api.` to `api-ws.` and retains the regional suffix.
It retains token selection, cookies, TLS, and proxy context.
Do not construct a Global 01 host.

Site captures subscribe to `/sites/{site_id}/pcaps`.
The installed organization `PcapEvents` subscribes to `/orgs/{org_id}/pcaps`.
The bundled organization example confirms that organization channel.
Keep this organization scope for `mxedge.orgRemotePcap`.

## Decision: Use the capture status endpoint for stop

The SDK exposes `getSiteCapturingStatus` and `getOrgCapturingStatus`.
Both read `/pcaps/capture` in their own scope.
The bundled `response_pcap_status` schema identifies the active capture with `id`.

`listSitePacketCaptures` and `listOrgPacketCaptures` list stored captures.
A matching stored record does not authorize a scope-wide stop.
Use the active status instead.

Start uses `startSitePacketCapture` or `startOrgPacketCapture`.
Stop uses `stopSitePacketCapture` or `stopOrgPacketCapture`.
Pass explicit SDK arguments for each action.
Check both status and identity.
Reject failed, malformed, or uncertain responses.

## Decision: Bound HTTP work without changing the shared session

The SDK HTTP helper has no request timeout.
It also waits for an unrestricted `Retry-After` value.
A dedicated worker therefore needs a private bounded HTTP transport.

Copy the current SDK session context without changing the original.
Keep its authentication, regional host, cookies, TLS, proxies, and permissions.
Keep SDK token rotation and bounded rate-limit retries.
Bound each HTTP phase and reject a retry outside its remaining time.
Refuse an unsupported custom transport instead of removing its filters.
Never retry an uncertain capture start or cloud stop.

The SDK socket factory also has no connection timeout.
Give only the capture client a private socket factory.
Use the installed WebSocket library's connector with the SDK's regional URL and TLS context.
Bound connection and handshake waits without changing the global socket timeout.
Retain the SDK's original application callbacks, headers, and cookies.
Close and release each owned socket before worker completion.

## Decision: Correlate and bound immediate records

The SDK supplies outer event objects.
Their `data` can be another JSON string.
Decode that string before reading `capture_id` and `pcap_dict`.
Keep early events in a bounded buffer until the start response supplies `id`.

Require the exact scope channel and capture identifier.
Store the decoded packet dictionary through the existing session buffer.
Keep raw packet bytes out of logs and evidence.
Reuse the existing credential redactor and packet summary.

The cloud stop endpoint accepts a scope, not a capture identifier.
The active status read therefore precedes the stop.
The portal also refuses a duplicate capture in the same scope.
This check does not create an atomic cloud lock across independent operators.

## Decision: Test the actual controller and card

Use fake SDK responses at the transport boundary, not a replacement service.
Use the real checker, manager, routes, JavaScript, and card.
Use a controlled clock for 120 and 3600 seconds.
Use one short local stream for the real SDK connection.
Block browser requests to external hosts.
Keep CSRF and target checks active.

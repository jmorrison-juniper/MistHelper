# Research: Independent WebSocket Dialog Audit

## Evidence boundary

Repository revision: `06c92559cd043dff755c665c6934a0d100dc99fd`.
No deployed revision or live catalog has been observed.
Source observations are not live evidence.
The existing `FakeWebSocketServices` tests are isolated prior art only.

## Decision 1: Inspect the real catalog and form

**Decision**: Use the real `StreamCatalog`, `UtilityDiscovery`, blueprint, template, and browser assets.
In isolated mode, replace only selector data and execution boundaries.
Do not inject a smaller catalog or rewrite the dialog builder.

**Rationale**: `ChannelCatalog._ROWS` has 18 static entries.
Utility discovery reads installed `mistapi.device_utils` facades and signatures.
`StreamCatalog.page_payload()` deliberately excludes private channel paths.
The oracle must join the public payload to source definitions and actual runner behavior.

The page uses an inline operation form, not a universal modal dialog.
`selectEntry()` displays `entry.description`.
`renderStartForm()` creates targets from `identifiers` or `targets` and parameters from `fields`.
Controls use `wsField-{name}`, `data-testid="ws-field-{name}"`, labels, and the `required` property.
Site changes load device, map, and asset choices.
SDK client choices depend on site and map.
Serial markers reject some outdated responses.
The template has no general operation-form Cancel button.
Its terminal paste Cancel control is not a substitute.
Record cancellation behavior as an inspection result. Do not invent a passing cancel action.

**Alternatives considered**: The existing fixed fake catalog misses SDK drift and real form construction.
Checking only source misses actual displayed labels and browser behavior.
Replacing JavaScript would test the replacement rather than the portal.

## Decision 2: Use the smallest repository-compatible environment

**Decision**: Use a local Python 3.13+ worktree environment through `scripts/bootstrap_worktree.py`.
Use its uv-backed runtime and development installation.
Use only Playwright Chromium, not Chrome or a test container.
Do not install the repository wheel with `pip install .`.

**Rationale**: `tests/conftest.py` requires `mistapi`, `structlog`, `dotenv`, and `paramiko`.
It also imports `MistHelper.py` and checks source resolution.
A Playwright-only environment cannot satisfy this bootstrap contract.
The bootstrap installs both requirement files and downloads Chromium.
It also configures the local Git credential username. Record this local side effect before execution.
No installation occurs during planning.

**Alternatives considered**: An ad hoc minimal environment bypasses repository prerequisites.
Chrome requires a separate installation and is not needed for Playwright Chromium.
A container adds storage, networking, and lifecycle work without improving this audit.

## Decision 3: Verify SDK channels before live permission

**Decision**: Compare installed SDK definitions and behavior with the portal's selected revision.
Use exact versions and digests. Never permit a key solely because it appears in this table.

Primary reference: [mistapi v0.64.0](https://github.com/tmunzer/mistapi_python/tree/66a57a64f2cae222da36c3a45a639c2a70c54156/src/mistapi).
Commit: `66a57a64f2cae222da36c3a45a639c2a70c54156`.
The bounded SDK research inspected `websockets/orgs.py`, `sites.py`, `location.py`, `session.py`, and `__ws_client.py`.

| Portal keys | SDK class in `mistapi.websockets` | Required target | Planning classification |
|---|---|---|---|
| `org.insights.summary` | `orgs.InsightsEvents` | Existing organization | Candidate read-only subscription |
| `org.stats.mxedges`, `org.mxedges` | `orgs.MxEdgesStatsEvents`, `orgs.MxEdgesEvents` | Existing organization | Candidate read-only subscriptions |
| `site.stats.clients`, `site.stats.devices`, `site.devices` | `sites.ClientsStatsEvents`, `sites.DeviceStatsEvents`, `sites.DeviceEvents` | Site | Candidate read-only subscriptions |
| `site.stats.mxedges`, `site.mxedges` | `sites.MxEdgesStatsEvents`, `sites.MxEdgesEvents` | Site | Candidate read-only subscriptions |
| `location.assets`, `location.clients`, `location.sdkclients` | `location.BleAssetsEvents`, `location.ConnectedClientsEvents`, `location.SdkClientsEvents` | Site and map | Candidate read-only subscriptions |
| `location.unconnected_clients`, `location.discovered_assets` | `location.UnconnectedClientsEvents`, `location.DiscoveredBleAssetsEvents` | Site and map | Candidate read-only subscriptions |
| `org.pcaps`, `site.pcaps` | `orgs.PcapEvents`, `sites.PcapEvents` | Organization or site | Live denied under capture exclusion |
| `site.devices.cmd` | `sites.DeviceCmdEvents` | Site and device | Live denied under utility/command exclusion |
| `diag.asset` | No matching definition verified | Site and asset | Unverified, live blocked |
| `diag.sdkclient` | No matching definition verified | Site, map, and SDK client | Unverified, live blocked |

The candidate set has 13 keys. It is not an executable allowlist.
Organization entries require no site selector.
Site client statistics require a site, not a selected individual client.
Location entries require a map, not an individual client selector.
Diagnostic requirements remain inspectable even when live execution is blocked.

SDK code constructs `wss://{api-ws host}/api-ws/v1/stream`.
It sends `{"subscribe": channel}` and handles `channel_subscribed` or `subscribe_failed`.
Token headers or session cookies supply authentication.
`disconnect()` closes the socket. It does not send a channel unsubscribe frame.
The base channel client exposes no arbitrary publish interface.
These facts do not prove a surrounding utility wrapper is harmless.
SDK shell sessions are bidirectional. Capture helpers trigger REST jobs.
`SessionWithUrl` sends credentials to its supplied host, so arbitrary URLs must remain blocked.
SDK site capture source uses `/pcaps`, while its README table uses `/pcap`.
Prefer versioned source. Capture remains denied regardless.

Portal `SessionRunnerFactory` chooses `ChannelStreamRunner` for channel starts.
The portal owns an existing `StreamClient` and subscription handshake.
It sends subscribe frames and builds paths on the server.
Browser interception alone cannot enforce its Mist-side behavior.
For the exact authorized `site.stats.devices` journey, verify the checked-request/runner source,
installed SDK path, and deployed/base revision match before observing its actual live/output/stop states.
Do not impose a generalized runtime-attestation framework as an extra authorization condition.
No new owned transport is proposed.

**Alternatives considered**: A badge-based allowlist permits device utilities marked `read`.
A raw browser WebSocket test bypasses the actual portal journey.
Adding missing diagnostic definitions would be transport work outside this audit.

## Decision 4: Verify all selector GET paths

**Decision**: Record these existing SDK calls as the selector-read candidates.
Verify their complete deployed call paths before allowing live picker requests.

| Portal request | Existing SDK method | Verified SDK REST path |
|---|---|---|
| GET `/api/operations/sites` | `api.v1.orgs.sites.listOrgSites` | `/api/v1/orgs/{org_id}/sites` |
| Same site request, default filtering | `api.v1.orgs.stats.listOrgSiteStats` | `/api/v1/orgs/{org_id}/stats/sites` |
| GET `/api/websockets/sites/{site_id}/devices` | `api.v1.sites.devices.listSiteDevices` | `/api/v1/sites/{site_id}/devices` |
| GET `/api/websockets/sites/{site_id}/maps` | `api.v1.sites.maps.listSiteMaps` | `/api/v1/sites/{site_id}/maps` |
| GET `/api/websockets/sites/{site_id}/assets` | `api.v1.sites.assets.listSiteAssets` | `/api/v1/sites/{site_id}/assets` |
| GET `/api/websockets/sites/{site_id}/maps/{map_id}/sdkclients` | `api.v1.sites.stats.getSiteSdkStatsByMap` | `/api/v1/sites/{site_id}/stats/maps/{map_id}/sdkclients` |
| GET `/api/websockets/mxedges?site_id={site_id}` | `api.v1.sites.mxedges.listSiteMxEdges` | `/api/v1/sites/{site_id}/mxedges` |
| GET `/api/websockets/mxedges` | `api.v1.orgs.mxedges.listOrgMxEdges` | `/api/v1/orgs/{org_id}/mxedges` |

All eight versioned functions call `mist_session.mist_get`.
Evidence files use [the SDK REST source directory](https://github.com/tmunzer/mistapi_python/tree/66a57a64f2cae222da36c3a45a639c2a70c54156/src/mistapi/api/v1).
Repository call sites are `intake/pickers/resources.py`, `intake/pickers/devices.py`, and `web_portal/routes/operations.py`.
The latter can hide sites with proven zero hardware counts.
Treat filtered choices, pagination limits, empty choices, and failures separately.
Do not infer complete organization coverage from one page of results.

**Alternatives considered**: Allowing every GET is unsafe because handlers can have side effects.
Direct Mist REST requests violate the SDK boundary.
Using only `listOrgSites` evidence misses the additional statistics call.

## Decision 5: Enforce browser and server boundaries

**Decision**: Install a context-wide default-deny browser policy before navigation.
Block service workers and unsolicited WebSockets.
Block Python egress in isolated inventory and use no forwarding branch for isolated browser work.
The reviewed exact-key live channel needs source/revision verification, not a whole-server guard.

The policy must inspect exact origin, method, normalized path, query, body, operation key, scope, and owned session.
GET selectors need explicit method evidence.
POST session start and stop are local lifecycle actions, not permission for Mist REST writes.
Allow start only for approved channel keys with exact selected targets.
Allow stop only for the session created by that journey.
Reject utilities regardless of `safety="read"`.
Reject shell input, resize, capture, mutation, generic operations, download, and delete.

If an existing remote portal cannot provide verified server enforcement or an equivalent trusted network boundary, live subscriptions remain blocked.
Browser interception still permits safe dialog inspection with execution denied.
Never weaken that requirement to obtain a live pass.

**Rationale**: The browser cannot see server-side Mist requests or frames.
Opening a form starts picker requests automatically.
Session lists can include other users' sessions and private details.
Use exact owned-session filtering and do not interact with unrelated sessions.

**Alternatives considered**: Broad POST denial prevents safe local subscription lifecycle.
Broad POST allowance permits utilities through the same session endpoint.
A page-only fetch patch misses popup, worker, redirect, and transport paths.

## Decision 6: Keep evidence and repair gates separate

**Decision**: Report source inventory, isolated inspection, live inspection, and live subscription as separate evidence dimensions.
Use passed, failed, blocked, and skipped statuses with explicit reasons.
Record no-data independently from connection or rendering failure.
A connected socket without subscription acknowledgement is not a pass.

Keep screenshots, traces, raw events, authentication state, and private selectors local.
Use run-local aliases in sanitized reports.
Deduplicate defects by proven cause, affected behavior, and repair boundary.
Link one issue per confirmed defect before repair.
Do not create an issue for an environment blocker or an unverified source suspicion.

**Alternatives considered**: One aggregate green result falsely converts fake results into live evidence.
One repair issue for the whole audit obscures independently testable defects.

## Historical execution blockers at planning time

- The parent is obtaining the authorized portal URL. No URL is guessed.
- The reported local portal is unreachable. No production service is started.
- Chrome is absent. Future Playwright Chromium setup avoids that dependency.
- The worktree has no `.venv`. uv is available. Bootstrap has not run.
- Existing authentication must be usable without printing credentials.
- Deployed revision, SDK version and operation-specific runtime evidence were not yet verified.
  A proposed whole-server guard was later removed as unnecessary for the exact authorized observation path.
- Any PR #3814 file overlap requires ownership coordination.

These bullets record the original planning environment, not current capability.
The parent subsequently installed the environment/Chromium and started the user-authorized normal portal.
Deployed/local base equality was verified at `2900f56`.
Current GET inspection measured 72 forms and the exact `site.stats.devices` journey verified
subscribed/live, bounded no-data observation, one owned stop and stopped state.
Three empty-everywhere target blockers and the tracked UX work remain distinct from that verified lifecycle.

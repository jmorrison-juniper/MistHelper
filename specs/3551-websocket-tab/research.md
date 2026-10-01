# Research: WebSockets tab in the Operations portal

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-09-29

This file records each design decision, the reason for it, and the options that the design rejected. The SDK facts come from `mistapi` 0.64.0 in the worktree virtual environment.

## R-01: Put the engine and the blueprint in `src/websocket_streams/`

**Decision**: Put the catalog, the checks, the sessions, the runners, and the blueprint in one new package `src/websocket_streams/`. The blueprint carries its own `templates/` and `static/` folders.

**Rationale**:

- The lint gates do not read the `web_portal/` folder. The new code opens network connections and runs device commands, so the gates must read it.
- The `src/upgrade_portal/` package already ships a Flask app with templates and static files. Hatch packs every file in `src/`, so the wheel holds the page files.
- The portal folders `web_portal/routes/` and `web_portal/templates/` hold 7 and 5 children. A blueprint with its own folders adds no child to them.

**Alternatives rejected**:

- `web_portal/routes/websockets.py` with a template in `web_portal/templates/`. The gates skip this code, and the folders pass the Five-Item limit.
- A nested package in `src/websocket/`. That package holds 7 children, and its `__init__.py` imports the CLI manager.

## R-02: Use the SDK WebSocket client for all 18 channels

**Decision**: The channel runner creates `_MistWebsocket(apisession, channels=[path])` from `mistapi.websockets.__ws_client`. The catalog builds each path from a key and checked identifiers.

**Rationale**:

- One code path serves the 16 channels that have a public SDK class and the 2 diagnostic channels that have no class.
- The client picks the regional host from the session cloud address. It sends the token in a header, and a filter removes the header from the SDK log.
- The client delivers each message to `on_message`, each error to `on_error`, and one final close to `on_close`.

**Risk and control**: `_MistWebsocket` is a private name. Two contract tests control the risk:

1. A signature test pins the constructor parameters and the callback methods.
2. A parity test creates each public channel class with test identifiers. It then compares the channel list of the class with the path that the catalog builds.

A `mistapi` upgrade that breaks the private name fails these tests before a release.

**Settings for a channel stream**: `auto_reconnect=True`, `max_reconnect_attempts=3`, `ping_interval=30`, and `queue_maxsize=1000`.

**Alternatives rejected**:

- One runner class for each public SDK class. This gives 16 code paths and still needs a second path for the 2 diagnostic channels.
- A raw `websocket-client` connection in the portal. The constitution forbids a direct call when a `mistapi` method exists, and the portal then holds the token logic.

## R-03: Use the SDK device utilities for the command utilities

**Decision**: The utility runner calls the facade function in `mistapi.device_utils` (`ap`, `ex`, `srx`, `ssr`, or `mxedge`). It passes an `on_message` callback that writes to the session buffer. The call returns a `UtilResponse` at once.

**SDK behavior that the runner must handle**:

- The SDK sends the REST trigger in a background thread and then subscribes. Output that arrives before the subscription is lost. The live check must confirm that ping and ARP output arrives.
- Three SDK timers close the connection. The inactivity timer uses the `timeout` parameter, and each message restarts it. The first-message timer is 30 seconds. The maximum-duration timer is 60 seconds.
- A trigger with a status other than 200 leaves `ws_error` empty. The runner must read `trigger_api_response.status_code`.
- `UtilResponse.disconnect()` does nothing until the connection starts. The runner repeats the stop request until the response reports `done`.
- `top` and `monitor traffic` send a full screen in each message. The page must replace the view and not add lines.

**End states**:

| Condition | End state |
| - | - |
| The trigger status is not 200, or `ws_error` holds a value | `failed` |
| The operator stopped the session | `stopped` |
| No output arrived | `timed out` |
| Output arrived | `finished` |

When a finished session ran for 59 seconds or more, the card states that the session reached the 60-second limit.

**Timeouts**: The runner uses the SDK default timeout for each utility, except ping. For ping, the timeout is the packet count plus 5 seconds, so the summary line arrives.

**Alternatives rejected**:

- A trigger call and a separate `DeviceCmdEvents` subscription in the portal. This copies SDK logic for 52 utilities.
- A blocking `wait()` in the request thread. A request then holds a Gunicorn thread for up to 70 seconds.

## R-04: Run each packet capture for 60 seconds at most

**Decision**: The capture utilities use the same device utility path as R-03. The capture duration is fixed at 60 seconds. The operator sets the packet count, the packet length, and an optional capture filter.

**Rationale**: The SDK closes each utility connection after 60 seconds. Mist accepts a capture from 60 to 86400 seconds. A duration of 60 seconds is therefore the only value that both accept. Issue #3575 tracks a subscribe-first runner for a longer capture.

**Limits from the Mist API**:

| Field | Range | Default |
| - | - | - |
| `num_packets` | 1 to 10000 | 1024 |
| `max_pkt_len` | 64 to 2048, and 64 to 1520 on a gateway | 512 |
| `tcpdump_expression` | Up to 256 characters from a fixed set | None |

**Early stop**: The runner calls `UtilResponse.disconnect()`. It then reads the capture status of the site or the organization. If the status shows the capture of this session, the runner calls `stopSitePacketCapture` or `stopOrgPacketCapture`. A stop request ends every capture at the site, so the runner never sends it for a capture of another session.

**Packet summary**: The `pcap_dict` record of a wired capture holds `src_ip`, `dst_ip`, `src_port`, `dst_port`, `proto`, `length`, `timestamp`, and `info`. A wireless record holds `src`, `dst`, `bssid`, `frame_type`, `frame_subtype`, `rssi`, `channel`, and `info`. The summary shows the time, the source, the destination, the protocol, and the length when the record holds them.

## R-05: Use the SDK shell session for the remote shell

**Decision**: The shell runner calls `createShellSession(apisession, site_id, device_id, rows, cols)` from `ex` or `srx`. A reader thread calls `recv(timeout=1)` in a loop and writes the output to the session buffer.

**SDK behavior that the runner must handle**:

- The shell is not safe for two threads before the first output. The SDK reads the socket from the sender thread while it waits for the prompt. The runner refuses input until the reader thread receives the first output.
- The SDK logs the shell address at the INFO level on the `mistapi` logger. The address holds a session credential. A logging filter on that logger replaces each `wss://` address with a mark.
- The output holds ANSI escape codes. The server removes them and sends plain text.

**Input**: The page sends a command line or one of five keys: the interrupt key (`\x03`), Tab, Space, `q`, and Enter. The portal log records the open and the close of each shell with the device and the site. The log never records the text that the operator sends.

**Alternatives rejected**: A terminal emulator in the browser. The portal has no terminal library, and a plain transcript covers the CLI commands that a NOC engineer runs.

## R-06: Deliver messages to the page with short requests

**Decision**: The page reads new messages with `GET /api/websockets/sessions/<id>/messages?after=<seq>` once each second. The server answers at once with the messages after the sequence number.

**Rationale**: Gunicorn runs 1 worker with 24 threads. A request that waits for messages holds one thread. Five open streams that wait would hold 5 of the 24 threads.

**Alternatives rejected**:

- Server-sent events. Each open stream holds one Gunicorn thread for its full life.
- A browser WebSocket to Mist. The CSP allows `connect-src 'self'` only. The browser would also need the token.
- A browser WebSocket to the portal. Gunicorn with `gthread` does not serve WebSocket upgrades.

## R-07: Bound every session

**Decision**: The manager enforces these limits. Each limit has an environment variable with a safe range.

| Limit | Default | Environment variable | Range |
| - | - | - | - |
| Live sessions | 5 | `PORTAL_WS_MAX_SESSIONS` | 1 to 20 |
| Idle stop | 120 seconds | `PORTAL_WS_IDLE_SECONDS` | 30 to 3600 |
| Messages in a buffer | 500 | `PORTAL_WS_BUFFER_MESSAGES` | 50 to 5000 |
| Bytes in a buffer | 8 MB | `PORTAL_WS_BUFFER_MB` | 1 to 64 |
| Life of a channel stream or a shell | 30 minutes | `PORTAL_WS_MAX_STREAM_MINUTES` | 1 to 240 |

**Other rules**:

- One message larger than 256 KB is shortened, and the server marks it.
- A reaper thread runs every 5 seconds. It stops each idle session and each session past its life.
- The manager keeps an ended session for 10 minutes, so the operator can read it and download it. It keeps 5 ended sessions at most and removes the oldest first.
- `shutdown_app` in `web_portal/app.py` stops every session and the reaper.

## R-08: Fill the pickers from the Mist API

**Decision**: The blueprint gives one picker route for each identifier kind. Each route answers with rows and a plain reason when the list is empty.

| Picker | SDK function |
| - | - |
| Sites | `/api/operations/sites`, which already exists |
| Devices at a site | `sites.devices.listSiteDevices(type="all")` |
| Maps at a site | `sites.maps.listSiteMaps` |
| Assets at a site | `sites.assets.listSiteAssets` |
| SDK clients on a map | `sites.stats.getSiteSdkStatsByMap` |
| Mist Edges | `orgs.mxedges.listOrgMxEdges` and `sites.mxedges.listSiteMxEdges` |

The device picker adds a family to each row. An AP is `ap`, and a switch is `ex`. A gateway with `SRX` in the model is `srx`, and every other gateway is `ssr`. A device of another type has no family, and the page offers it no utility.

## R-09: Scope of the catalog

**Decision**: The catalog holds every SDK stream that sends output on a WebSocket.

| Group | Count | Source |
| - | - | - |
| Organization channels | 4 | `mistapi.websockets.orgs` |
| Site channels | 7 | `mistapi.websockets.sites` |
| Location channels | 5 | `mistapi.websockets.location` |
| Diagnostic channels | 2 | The Mist WebSocket documentation, with no SDK class |
| AP utilities | 5 | `mistapi.device_utils.ap` |
| EX utilities and shell | 13 | `mistapi.device_utils.ex` |
| SRX utilities and shell | 18 | `mistapi.device_utils.srx` |
| SSR utilities | 16 | `mistapi.device_utils.ssr` |
| Mist Edge captures | 2 | `mistapi.device_utils.mxedge` |

**Diagnostic channel source**: The Juniper Mist WebSocket reference lists the two diagnostic channels. The `juniper-mist-automation` skill holds a copy of that table in `05-websocket-streaming/01-websocket-api-and-streaming-channels.md`.

| Channel | Path | What streams |
| - | - | - |
| BLE asset RF Glass information | `/sites/{site_id}/assets/{asset_id}/diag` | `map_id`, a `grid`, a `motion` flag, and `vbles` |
| SDK client RF Glass information and location | `/sites/{site_id}/sdkclients/{sdkclient_id}/diag` | The same grid and `vbles` shape, with `motion` and `avg_duration` |

The same reference states that each `data` event carries its record as a JSON string. The message shaper therefore parses the `data` field a second time when the field holds a JSON string.

**Exclusions**: The catalog leaves out these SDK names. The SC-003 test lists them by name.

- `clearBpduError`, `clearDot1xSessions`, `clearLearnedMac`, `clearMacTable`, and `clearHitCount`. These send a REST call only and open no WebSocket.
- `interactiveShell`. It reads the local keyboard of a terminal.
- `ShellSession`, `Node`, `RouteProtocol`, and `TracerouteProtocol`. These are types, not streams.
- `SessionWithUrl`. It sends the token to any address that the caller gives.
- The DNS test in `device_utils/__tools/dns.py`. The SDK marks it as "NO DATA" and keeps it in comments.

## R-10: Lock the state-changing utilities and the shell

**Decision**: The catalog gives each utility a safety class: `read`, `capture`, `change`, or `shell`.

- The `change` class holds bounce port, cable test, DHCP release, and clear sessions. `PORTAL_WS_ENABLE_CHANGES` unlocks it.
- The `shell` class holds the two shells. `PORTAL_WS_ENABLE_SHELL` unlocks it.
- Both flags are off by default. The server reads the flags at each start request, so the page cannot unlock a class.
- When a flag is on, the start request must hold the device name, typed by the operator. The server compares it with the name from the Mist API.

**Rationale**: The portal has no user login. These commands interrupt traffic or give full CLI access.

## R-11: Test without a Mist connection

**Decision**: The unit tests replace the SDK with fakes at one seam for each runner. The fakes deliver messages, errors, and closes on a thread, as the SDK does.

- The catalog tests read the real SDK modules. They prove the counts, the paths, and the parameter names.
- The blueprint tests use the Flask test client with a fake manager.
- The browser test starts the portal with a fake engine that sends messages on a timer.
- The live check uses the real organization with read-only channels, one ping, and one ARP table.

# Web Portal

MistHelper includes a Flask-based web portal for browser access to data, operations, and map viewing.

## Quick Start

```powershell
# Local development (Windows)
python MistHelper.py --web-portal

# Container (runs automatically alongside SSH)
podman compose up -d
```

Open http://localhost:8055 in your browser.

Caution: the command above starts the production local stack. If you start a
container for a test, for a debug session, or for an end-to-end run, obey the
policy in [Container Setup](Container-Setup#test-and-debug-containers). Start
the container inside the compose group. Name it
`misthelper-tmp-<issue|pr><number>-<slug>`. Publish a port in the range 9600
through 9699. Remove the container when the test ends. A test container that
publishes 8055 takes the port from the running portal, and the portal then stops
answering.

## Features

- **Data Browser**: Browse, preview, search, and download the CSV and SQLite output files.
- **Operations**: Run the operations whose registry category is `safe` or `interactive_safe`.
- **Map Viewer**: View a floor plan in an interactive Plotly.js viewer with device markers.
- **WebSockets**: Open a live Mist API stream, read its messages, and stop it. Run a device utility, such as a ping or an ARP table. See [WebSockets Tab](#websockets-tab).
- **Themes**: Brand Magenta, Dark, Light, and High Contrast themes with instant switching (persisted in localStorage). Brand Magenta is the default and matches the upgrade capture portal.
- **Branding**: Customize the title, the logo, and the accent color with environment variables.

## WebSockets Tab

The WebSockets tab at `/websockets` opens the live streams of the Mist API. The
portal server holds each stream. The browser reads the new messages of the
selected session one time each second.

The tab gives three kinds of entry.

| Kind | Action | Examples |
| - | - | - |
| Channel | Subscribes to one Mist API stream and shows each message. | Device statistics, client statistics, and map locations |
| Utility | Runs one command on one device and shows the output. | Ping, traceroute, ARP table, and packet capture |
| Shell | Opens a command shell on one device. | The device shell |

The catalog holds 18 channels and 54 utilities. One channel session can follow
1 to 10 sites, devices, or maps. Each message shows the site, the device, or the
map that sent it.

Each utility has one safety class.

| Class | Effect on the device | Default state |
| - | - | - |
| `read` | Reads the device state. It changes nothing. | Available |
| `capture` | Captures packets for 60 seconds or less. It changes nothing. | Available |
| `change` | Bounces a port, runs a cable test, releases a DHCP lease, or clears sessions. | Locked |
| `shell` | Opens a command shell on the device. | Locked |

Warning: a `change` utility can stop the traffic on a production port. A shell
can change any device setting. Unlock a class only when an operator needs it.

To unlock a class, do these steps.

1. Set `PORTAL_WS_ENABLE_CHANGES` or `PORTAL_WS_ENABLE_SHELL` to `true`.
2. Restart the portal.
3. Type the device name when the tab asks for it.

The portal writes one audit line at the WARNING level for each start of a
`change` utility or a shell. The line never holds the text that you type in a
shell.

The tab obeys these session limits.

- The tab keeps 5 live sessions or fewer.
- A session stops when no page reads it for 120 seconds.
- A session stops after 30 minutes.
- You can download the messages of a session as a JSON Lines file.

### Known limits

The `mistapi` 0.64.0 SDK causes two limits.

- A read utility that answers fast can end with no output, or with a part of a
  table. The SDK sends the command before it subscribes to the answer. The ARP
  table and the routes of a gateway show this limit. If a table is empty or
  short, run the utility again. Issue #3660 records the defect and the repair.
- The `topCommand` screen can show parts of terminal control codes, such as
  `[21;65H`. The SDK draws the screen before the portal receives it. Issue #3659
  records the defect.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORTAL_TITLE` | `MistHelper` | Browser tab and navbar title |
| `PORTAL_LOGO_URL` | `/static/img/logo-default.svg` | Logo image URL |
| `PORTAL_ACCENT_COLOR` | `#E20074` | Accent color for buttons and highlights |
| `PORTAL_THEME` | `magenta` | Default theme (magenta, dark, light, high-contrast) |
| `WEB_PORT` | `8055` | Web portal listen port |
| `PORTAL_ALLOWED_IPS` | *(empty = all)* | Comma-separated CIDR allowlist |
| `PORTAL_SECRET_KEY` | *(auto-generated)* | Flask session secret key |
| `PORTAL_WS_ENABLE_CHANGES` | `false` | Unlocks the `change` utilities of the WebSockets tab |
| `PORTAL_WS_ENABLE_SHELL` | `false` | Unlocks the device shell of the WebSockets tab |
| `PORTAL_WS_MAX_SESSIONS` | `5` | Live WebSockets sessions, 1 to 20 |
| `PORTAL_WS_IDLE_SECONDS` | `120` | Seconds without a page read before a session stops, 30 to 3600 |
| `PORTAL_WS_BUFFER_MESSAGES` | `500` | Messages that each session keeps, 50 to 5000 |
| `PORTAL_WS_BUFFER_MB` | `8` | Megabytes that each session keeps, 1 to 64 |
| `PORTAL_WS_MAX_STREAM_MINUTES` | `30` | Minutes before a session stops, 1 to 240 |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard with data summary |
| `/data` | GET | Data browser page |
| `/operations` | GET | Operations page |
| `/maps` | GET | Map viewer page |
| `/health` | GET | Liveness probe. Reports that the process runs. Reads no disk. |
| `/ready` | GET | Readiness probe. Tests the data directory, the database, and the Mist session. Returns code 503 and names each failed check. |
| `/api/data/files` | GET | List data files |
| `/api/operations/list` | GET | List available operations |
| `/api/operations/run` | POST | Run an operation |
| `/api/operations/stream` | GET | SSE event stream |
| `/websockets` | GET | WebSockets page |
| `/api/websockets/catalog` | GET | List the channels, the utilities, and the state of each flag |
| `/api/websockets/sessions` | GET | List the sessions and the session limits |
| `/api/websockets/sessions` | POST | Start a session |
| `/api/websockets/sessions/<session_id>/messages` | GET | Read the new messages of a session |
| `/api/websockets/sessions/<session_id>/stop` | POST | Stop a session |
| `/api/websockets/sessions/<session_id>/input` | POST | Send one line or one key to a shell |
| `/api/websockets/sessions/<session_id>` | DELETE | Remove an ended session |
| `/api/websockets/sessions/<session_id>/download` | GET | Download the messages of a session |
| `/api/websockets/sites/<site_id>/devices` | GET | List the devices of a site for a picker |
| `/api/websockets/sites/<site_id>/maps` | GET | List the maps of a site for a picker |
| `/api/websockets/sites/<site_id>/assets` | GET | List the BLE assets of a site for a picker |
| `/api/websockets/sites/<site_id>/maps/<map_id>/sdkclients` | GET | List the SDK clients of a map for a picker |
| `/api/websockets/mxedges` | GET | List the Mist Edges for a picker |

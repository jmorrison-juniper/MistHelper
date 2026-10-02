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
- **WebSockets**: Open a live Mist API stream, run a device utility, or use a terminal session. See [WebSockets Tab](#websockets-tab).
- **Themes**: Brand Magenta, Dark, Light, and High Contrast themes with instant switching (persisted in localStorage). Brand Magenta is the default and matches the upgrade capture portal.
- **Branding**: Customize the title, the logo, and the accent color with environment variables.

## WebSockets Tab

The WebSockets tab at `/websockets` opens the live streams of the Mist API. The
portal server holds each stream. The browser reads message sessions one time
each second. It reads terminal sessions with a long poll.

The tab gives three kinds of entry.

| Kind | Action | Examples |
| - | - | - |
| Channel | Subscribes to one Mist API stream and shows each message. | Device statistics, client statistics, and map locations |
| Utility | Runs one command on one device and shows the output. | Ping, traceroute, ARP table, packet capture, Top, and Monitor Traffic |
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

Warning: a shell sends each key to a live device. A command can change the
device configuration.

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
- A terminal session keeps 1,024 KiB of output bytes by default.

### Terminal panel

The tab shows an xterm.js terminal panel for a shell session. It shows a
read-only xterm.js panel for Top and Monitor Traffic. The panel has a toolbar,
a terminal screen, a status line, a time notice, and a gap notice.

Top and Monitor Traffic use a fixed device screen of 80 columns and 40 rows.
The page does not fit this screen to the panel, and it sends no resize request.
The warning line says, "This view is read-only. The device sends the screen."
The Paste toolbar button and the Paste menu item are disabled.

The status line shows the session state, the terminal size, and the end reason.
The session header shows the same state names, such as `Live` and `Finished`.
For a terminal session, the header counter shows `Output: N bytes`. `N` is the
newest terminal read position. The session list item shows the state only. The
Stop button is disabled after a final state.

Select a session in the session list to show its output. The page then scrolls
to the terminal panel and replays the output that the portal holds.

A new terminal can wait for the first output from the device. Until the output
arrives, the header shows this notice.

```text
The portal waits for the first output from the device.
```

If no output arrives in 20 seconds, the header shows this notice.

```text
The device sent no output in 20 seconds. Stop this session. Start a new session after one minute.
```

A device can accept a terminal and send no output. This can occur after three
or four quick shells on one device. The Mist cloud then closes the terminal
after approximately 90 seconds. The session ends as `Failed` with this reason.

```text
The device sent no output before the Mist cloud closed the terminal. Start a new session after one minute.
```

Issue #3710 records this behavior.

The time notice appears when less than two minutes remain. The gap notice shows
how many terminal bytes the portal no longer holds.

Use these copy actions.

- Select text to copy it. This setting is on by default.
- Press Ctrl+Shift+C or Ctrl+Insert to copy selected text.
- Press Ctrl+C with selected text to copy it.
- Press Ctrl+C with no selected text to send the interrupt character.
- Select Copy from the right-click menu.

Use these paste actions.

- Press Ctrl+V, Ctrl+Shift+V, or Shift+Insert.
- Select Paste from the toolbar or from the right-click menu.
- If the browser blocks clipboard read, paste text into the dialog.
- If the text has more than one line, confirm the paste first.
- `Lines: N` counts the lines. A line end at the end of the text adds no line.
- The `Paste text` label appears only with the paste text box.
- If the text is larger than 256 KiB, the page refuses it.

The page sends pasted text through xterm.js. xterm.js changes the text to the
terminal bytes that the device receives. For large paste text, the page sends
parts of 4 KiB or less. It shows a progress bar above 16 KiB.

For Ctrl+Shift+V and Shift+Insert, the page reads the clipboard directly. For
Ctrl+V, the page can use the native paste event. The preference
`ctrlVBehavior` controls that behavior.

The right-click menu has Copy, Paste, Select all, and Clear. Clear removes only
the local terminal screen. It does not stop the session.

The terminal settings are stored in browser local storage under
`misthelper.wsTerminal.prefs`. The visible settings keep copy on select,
multi-line paste confirmation, and font size. The stored settings also keep
`ctrlVBehavior` and `rightClickAction`. The A+ and A- buttons change the font
size from 10 to 28.

Select Download in the terminal toolbar to save the visible terminal history as
a text file. The file contains the xterm.js buffer text and no terminal control
codes.

### WebSockets repair notes

The WebSockets tab now owns the Mist live connections for terminal and command
sessions. This repairs two defects in the Mist software kit path.

- A device command subscribes before the trigger request. This prevents lost
  first output lines. Issue #3660 records the defect.
- Top and Monitor Traffic now use the terminal parser in xterm.js. This prevents
  split terminal control sequences from showing as stray text. Issue #3659
  records the defect.
- A terminal that gets no output from the device now shows a notice and a
  plain failed reason. Before this repair, the page showed `Live` and an empty
  screen for 90 seconds. Issue #3710 records the defect.

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
| `PORTAL_WS_TERMINAL_HISTORY_KB` | `1024` | KiB of terminal output bytes per session, 256 to 8192 |

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
| `/api/websockets/sessions/<session_id>/messages` | GET | Read the new messages of a message session |
| `/api/websockets/sessions/<session_id>/terminal` | GET | Read the terminal bytes of a terminal session |
| `/api/websockets/sessions/<session_id>/stop` | POST | Stop a session |
| `/api/websockets/sessions/<session_id>/input` | POST | Send terminal input text to a shell |
| `/api/websockets/sessions/<session_id>/resize` | POST | Send the terminal size to a shell |
| `/api/websockets/sessions/<session_id>` | DELETE | Remove an ended session |
| `/api/websockets/sessions/<session_id>/download` | GET | Download the messages of a session |
| `/api/websockets/sites/<site_id>/devices` | GET | List the devices of a site for a picker |
| `/api/websockets/sites/<site_id>/maps` | GET | List the maps of a site for a picker |
| `/api/websockets/sites/<site_id>/assets` | GET | List the BLE assets of a site for a picker |
| `/api/websockets/sites/<site_id>/maps/<map_id>/sdkclients` | GET | List the SDK clients of a map for a picker |
| `/api/websockets/mxedges` | GET | List the Mist Edges for a picker |

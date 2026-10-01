# Contract: Terminal Page

The page shows a terminal panel for each session with `terminal: true`. Browser
tests use the `data-testid` values in this file. A change to a value needs a
change to the tests.

## Elements

| `data-testid` | Element | Behavior |
| - | - | - |
| `ws-terminal-panel` | The panel | Holds the toolbar, the screen, the status line, and notices |
| `ws-terminal-warning` | The warning line | Shows the shell warning or the read-only screen message |
| `ws-terminal-copy` | Toolbar button | Copies the selection |
| `ws-terminal-paste` | Toolbar button | Pastes the clipboard. It is disabled for a read-only screen. |
| `ws-terminal-download` | Toolbar button | Saves the visible history as a text file |
| `ws-terminal-font-up` | Toolbar button | Makes the text larger |
| `ws-terminal-font-down` | Toolbar button | Makes the text smaller |
| `ws-terminal-settings` | Toolbar button | Opens the settings |
| `ws-terminal-copy-on-select` | Check box | Turns copy by selection on or off |
| `ws-terminal-confirm-paste` | Check box | Turns the paste confirmation on or off |
| `ws-terminal-screen` | The xterm.js host | Gets the focus when the session opens |
| `ws-terminal-status` | The status line | Shows the state, the size, and the end reason |
| `ws-terminal-expiry` | The time notice | Shows when less than 2 minutes remain |
| `ws-terminal-gap` | The gap notice | Shows the count of bytes that the portal no longer holds |
| `ws-terminal-progress` | Progress bar | Shows the send progress of pasted text larger than 16 KiB |
| `ws-terminal-toast` | Notice | Has `aria-live="polite"`. Shows copy and paste notices. |
| `ws-terminal-menu` | Right-click menu | Holds Copy, Paste, Select all, and Clear |
| `ws-terminal-menu-copy` | Menu item | Copies the selection |
| `ws-terminal-menu-paste` | Menu item | Pastes the clipboard. It is disabled for a read-only screen. |
| `ws-terminal-menu-select-all` | Menu item | Selects all text |
| `ws-terminal-menu-clear` | Menu item | Clears the local history only |
| `ws-terminal-paste-dialog` | Dialog | Shows paste confirmation or manual paste input |
| `ws-terminal-paste-lines` | Text | Shows the paste line count or manual paste instruction |
| `ws-terminal-paste-preview` | Text | Shows the first 5 lines of the pasted text |
| `ws-terminal-paste-input` | Text area | Holds manual paste text when clipboard read is unavailable |
| `ws-terminal-paste-cancel` | Button | Cancels the paste. It has the focus when the dialog opens. |
| `ws-terminal-paste-send` | Button | Sends the pasted text |

The paste input label has the id `wsTerminalPasteInputLabel`. It has no
`data-testid`. The page shows the label only with the paste text box.

The old shell line field `wsTerminalInput` and its key buttons are removed.

## Page context test identifiers

The template and the page script also use these `data-testid` values.

| `data-testid` | Element | Behavior |
| - | - | - |
| `websockets-title` | Page heading | Names the WebSockets tab |
| `websockets-intro` | Intro text | Explains the page |
| `ws-ready-alert` | Alert | Shows why the engine cannot start streams |
| `websockets-page` | Page grid | Holds the catalog, start form, and session list |
| `ws-catalog-count` | Badge | Shows the catalog entry count |
| `ws-catalog-filter` | Search box | Filters the catalog |
| `ws-catalog` | Catalog accordion | Holds channel and utility entries |
| `ws-catalog-loading` | Loading text | Shows until the catalog arrives |
| `ws-start-card` | Start card | Holds the selected entry form |
| `ws-safety-warning` | Warning | Shows risky utility or shell text |
| `ws-start-form` | Form | Starts the selected entry |
| `ws-target-fields` | Form group | Holds target fields |
| `ws-parameter-fields` | Form group | Holds parameter fields |
| `ws-confirmation-group` | Form group | Holds the typed confirmation |
| `ws-confirmation-input` | Text input | Holds the confirmation value |
| `ws-start-button` | Button | Starts the selected entry |
| `ws-start-error` | Alert | Shows start refusals |
| `ws-session-list-card` | Card | Holds the session list |
| `ws-session-limit` | Badge | Shows live sessions and the limit |
| `ws-session-list` | List | Holds the session buttons |
| `ws-session-<session_id>` | Button | Selects one session. The script creates this value. |
| `ws-message-panel` | Panel | Holds the selected session output |
| `ws-session-title` | Header | Shows the session title |
| `ws-session-state` | Header text | Shows the session state |
| `ws-session-reason` | Header text | Shows the end reason |
| `ws-message-controls` | Toolbar | Holds output buttons |
| `ws-pause-button` | Button | Pauses message polling |
| `ws-resume-button` | Button | Resumes message polling |
| `ws-clear-button` | Button | Clears local message rows |
| `ws-download-link` | Link | Downloads JSON Lines for message sessions |
| `ws-stop-button` | Button | Stops a live session |
| `ws-message-filter` | Search box | Filters message rows |
| `ws-counters` | Text | Shows message counters or terminal output bytes |
| `ws-output` | Message area | Holds message rows |

## Screen sessions

Top and Monitor Traffic are read-only screen sessions. The warning line says,
`This view is read-only. The device sends the screen.`

The screen size is exactly 80 columns and 40 rows. The page does not load the
fit add-on for the screen. It does not fit the terminal to the panel. It sends
no resize request for the screen.

The Paste toolbar button and the Paste menu item are disabled. The menu item
also gets `aria-disabled="true"`.

## Shell sessions

The shell warning line says, `Warning: Each command runs on the live device.`
A shell loads the fit add-on, fits to the panel, and sends resize requests when
the size changes.

Warning: a shell sends each key to a live device. A command can change the
device configuration.

## Header and status

The status line and the session header use the same state labels. Examples are
`Live` and `Finished`.

The status line text has this shape.

```text
State: Live | Size: 120 x 40 | Reason: The device closed the shell.
```

The session header counter shows `Output: N bytes` for a terminal session. `N`
is the `next` value from the latest terminal read. The session list item shows
the state only for a terminal session. The Stop button is disabled after a
final state.

## Session switch

A click on a `ws-session-<session_id>` button selects that session. The page
then scrolls `ws-message-panel` into view, because xterm.js does not draw a
screen that is out of view.

A switch obeys these rules.

- The page cancels the terminal read of the old session.
- The page drops the keys that the old session did not send yet.
- The page closes the paste dialog and clears the paste text.
- The page reads the new session from position 0 and replays the output that
  the portal holds.
- A later end of the old session does not change the header of the new session.

## Key rules

| Key | Selection | Result |
| - | - | - |
| Ctrl+C | Yes | Copy, clear the selection, and send nothing |
| Ctrl+C | No | Send `\x03` for a shell. Do nothing for a read-only screen. |
| Ctrl+Shift+C or Ctrl+Insert | Any | Copy |
| Cmd+C on macOS | Yes | Copy |
| Ctrl+V or Cmd+V | Any | Use the native paste event when `ctrlVBehavior` is `paste` |
| Ctrl+Shift+V or Shift+Insert | Any | Read the clipboard directly, then paste |
| Any other key | Any | xterm.js makes the key bytes, and the page sends them for a shell |

For a read-only screen, paste keys do nothing. Other keys do not send input.

## Paste rules

1. If the text is larger than 256 KiB, refuse it and show the limit in the
   notice.
2. If the text has more than 1 line and confirmation is on, open the dialog.
3. Count lines with `Lines: N`. A line end at the end of the text adds no line.
4. Show the paste text box and the `Paste text` label only for manual paste.
5. Send the text through `term.paste()`.
6. Split the output of xterm.js into parts of 4 KiB or less. Keep one request
   in flight.
7. If the text is larger than 16 KiB, show the progress bar.
8. If the server returns `rate_limited`, wait 1 second and retry the same part.
9. If one pasted part fails with another error, drop the rest of that paste.

## Copy rules

- On a secure page, use `navigator.clipboard.writeText`.
- On a page without TLS, use a hidden text area and `document.execCommand('copy')`.
- After each copy, show the notice `Copied N characters.`
- When copy on select is on, a mouse selection copies text and keeps the
  selection.

## Right-click menu

The default right-click action opens the menu. The menu has Copy, Paste, Select
all, and Clear. Clear removes only the local xterm.js buffer.

If `rightClickAction` is `paste`, right-click reads the clipboard directly for a
shell. A read-only screen still opens the menu.

## Read loop

1. Read with `after = next` and `wait = 20`.
2. Decode the base64 data and write the bytes to xterm.js.
3. If `gap` is more than 0, show the gap notice.
4. Show the expiry notice only when less than 2 minutes remain.
5. Update the status line and the session header from each read answer.
6. If the state is final, disable input and stop the read loop.
7. If a live read returns no data, wait 250 ms before the next read.
8. If a read fails, wait 1 second, then read again.
9. After 5 read failures in a row, show the error in the status line.

## Preferences

The page keeps these preferences under the local storage key
`misthelper.wsTerminal.prefs`.

| Key | Default | Rule |
| - | - | - |
| `copyOnSelect` | `true` | Copy by selection |
| `confirmPaste` | `true` | Confirm paste text with more than 1 line |
| `ctrlVBehavior` | `paste` | Ctrl+V and Cmd+V use the native paste event |
| `fontSize` | `14` | The A+ and A- buttons keep it from 10 through 28 |
| `rightClickAction` | `menu` | Right-click opens the menu unless the value is `paste` |

The visible settings show `copyOnSelect`, `confirmPaste`, and `fontSize`. The
other settings can exist in local storage.

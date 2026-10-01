# Contract: Terminal Page

The page shows a terminal panel for each session with `terminal: true`. The browser tests
use the `data-testid` values in this file. A change to a value needs a change to the tests.

## Elements

| `data-testid` | Element | Behavior |
| - | - | - |
| `ws-terminal-panel` | The panel | Holds the toolbar, the screen, and the status line |
| `ws-terminal-screen` | The xterm.js host | Gets the focus when the session opens |
| `ws-terminal-warning` | The warning line | States that each command runs on the live device |
| `ws-terminal-status` | The status line | Shows the state, the size, and the end reason |
| `ws-terminal-expiry` | The time notice | Shows when less than 2 minutes of the session life remain |
| `ws-terminal-gap` | The gap notice | Shows the count of bytes that the portal no longer holds |
| `ws-terminal-copy` | Toolbar button | Copies the selection |
| `ws-terminal-paste` | Toolbar button | Pastes the clipboard |
| `ws-terminal-download` | Toolbar button | Saves the history as a text file |
| `ws-terminal-font-up` | Toolbar button | Makes the text larger |
| `ws-terminal-font-down` | Toolbar button | Makes the text smaller |
| `ws-terminal-settings` | Toolbar button | Opens the settings |
| `ws-terminal-copy-on-select` | Check box | Turns copy by selection on or off |
| `ws-terminal-confirm-paste` | Check box | Turns the paste confirmation on or off |
| `ws-terminal-menu` | Right-click menu | Holds Copy, Paste, Select all, and Clear |
| `ws-terminal-menu-copy` | Menu item | Copies the selection |
| `ws-terminal-menu-paste` | Menu item | Pastes the clipboard |
| `ws-terminal-menu-select-all` | Menu item | Selects all text |
| `ws-terminal-menu-clear` | Menu item | Clears the local history only |
| `ws-terminal-paste-dialog` | Dialog | The paste confirmation |
| `ws-terminal-paste-lines` | Text | The line count of the pasted text |
| `ws-terminal-paste-preview` | Text | The first 5 lines of the pasted text |
| `ws-terminal-paste-send` | Button | Sends the pasted text |
| `ws-terminal-paste-cancel` | Button | Cancels the paste. It has the focus when the dialog opens. |
| `ws-terminal-paste-input` | Text area | The paste field for a page without TLS |
| `ws-terminal-progress` | Progress bar | Shows the send progress of pasted text larger than 16 KiB |
| `ws-terminal-toast` | Notice | Has `aria-live="polite"`. Shows the copy count and the paste limit. |

The old shell line field `wsTerminalInput` and its key buttons go away.

## Key rules

| Key | Selection | Result |
| - | - | - |
| Ctrl+C | Yes | Copy, clear the selection, send nothing |
| Ctrl+C | No | Send `\x03` |
| Ctrl+Shift+C or Ctrl+Insert | Any | Copy |
| Cmd+C on macOS | Yes | Copy |
| Ctrl+V, Ctrl+Shift+V, Shift+Insert, or Cmd+V | Any | Paste through the native paste event |
| Any other key | Any | xterm.js makes the key bytes, and the page sends them |

## Paste rules

1. If the text is larger than 256 KiB, refuse it and show the limit in the notice.
2. If the text has more than 1 line and the confirmation is on, open the dialog.
3. Send the text through `term.paste()`.
4. Split the output of xterm.js into parts of 4 KiB or less. Keep one request in flight.
5. If the text is larger than 16 KiB, show the progress bar.

## Copy rules

- On a secure page, use `navigator.clipboard.writeText`.
- On a page without TLS, use a hidden text area and `document.execCommand('copy')`.
- After each copy, show the notice "Copied N characters."

## Read loop

1. Read with `after = next` and `wait = 20`.
2. Decode the base64 data and write the bytes to xterm.js.
3. If `gap` is more than 0, show the gap notice.
4. If the state is not live, stop input and show the reason.
5. If a read fails, wait 1 second, then read again. After 5 failures in a row, show the
   error in the status line.

## Preferences

The page keeps `copyOnSelect`, `confirmPaste`, and `fontSize` under the local storage key
`misthelper.wsTerminal.prefs`.

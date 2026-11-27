# Contract: MSP console lines for menu 309

This contract lists the console lines that the owner reads during the live check. Each line gives its source. The letter N stands for a whole number. The lines are ASCII text. A quoted line must match the source exactly.

## Login lines

| Order | Line | Source |
| - | - | - |
| 1 | `  Password: ` (the password prompt, input hidden) | `src/mist/access/auth/interactive/credential_prompter.py` line 38 |
| 2 | `  Enter 2FA code: ` (asked only when Mist requires a second factor) | `src/mist/access/auth/interactive/credential_prompter.py` line 57 |
| 3 | `  + Login successful!` | `src/mist/access/auth/interactive/login_orchestrator.py` line 230 |
| 4 | `  + MSP access detected: N MSP(s) available` | `src/mist/access/auth/interactive/login_orchestrator.py` line 243 |

The email prompt is the method `prompt_email` in `src/mist/access/auth/interactive/credential_prompter.py` at line 19.

## Step 1 lines

| Order | Line | Source |
| - | - | - |
| 1 | `Step 1 of 4: Check the credential` | `src/operations/exporting/ex_hardware_inventory/console.py` line 43 |
| 2 | `  Credential: interactive login (user account)` | `src/operations/exporting/ex_hardware_inventory/console.py` lines 41, 42, and 44 |
| 3 | `  Scope: MSP` | `src/operations/exporting/ex_hardware_inventory/console.py` lines 40 and 45 |
| 4 | `  Organizations in scope: N` | `src/operations/exporting/ex_hardware_inventory/console.py` line 46 |
| 5 | `  Note: ` followed by one sentence, only when a note exists | `src/operations/exporting/ex_hardware_inventory/console.py` lines 47 and 48 |

The credential line changes with the sign-in. It reads `API token` and `organization token` for a token run.

## Step 2 lines

| Order | Line | Source |
| - | - | - |
| 1 | `Step 2 of 4: Find the connected EX switches` | `src/operations/exporting/ex_hardware_inventory/operation.py` line 272 |
| 2 | `  <organization name>: N connected EX switches` | `src/operations/exporting/ex_hardware_inventory/console.py` line 62 |
| 3 | `  Left out: offline N, unknown status N, other device types N, repeated chassis N` | `src/operations/exporting/ex_hardware_inventory/console.py` line 65 |
| 4 | `  <organization name> was not read, because Mist limited the requests.` | `src/operations/exporting/ex_hardware_inventory/console.py` line 34 |
| 5 | `  <organization name> was not read, because Mist could not list its switches. See the log for the cause.` | `src/operations/exporting/ex_hardware_inventory/console.py` line 35 |
| 6 | `No connected EX switch was found. No file was written.` | `src/operations/exporting/ex_hardware_inventory/operation.py` line 291 |

The step 2 line of each organization comes from `operation.py` lines 277 and 282. Each organization in scope gets one step 2 line.

## Step 3 lines

| Order | Line | Source |
| - | - | - |
| 1 | `Step 3 of 4: Confirm` | `src/operations/exporting/ex_hardware_inventory/console.py` line 83 |
| 2 | `  This run opens a read-only shell on each switch and runs one command:` | `src/operations/exporting/ex_hardware_inventory/console.py` line 85 |
| 3 | `  Type RUN N TARGETS to start, or press Enter to cancel: ` | `src/operations/exporting/ex_hardware_inventory/console.py` lines 81 and 90 |
| 4 | `Cancelled. No shell was opened and no file was written.` | `src/operations/exporting/ex_hardware_inventory/console.py` line 96 |

## Step 4 and end lines

| Order | Line | Source |
| - | - | - |
| 1 | `Step 4 of 4: Collect` | `src/operations/exporting/ex_hardware_inventory/operation.py` line 298 |
| 2 | `  <organization name>: collected N, failed N, skipped N, cancelled N` | `src/operations/exporting/ex_hardware_inventory/console.py` lines 99 to 102 |
| 3 | `Report: <path> (N rows)` where the path names the CSV file | `src/operations/exporting/ex_hardware_inventory/console.py` line 115 |
| 4 | `Master XML: <path> (N devices)` where the path names the XML file | `src/operations/exporting/ex_hardware_inventory/console.py` line 117 |
| 5 | `Run status: complete` or `Run status: partial` | `src/operations/exporting/ex_hardware_inventory/console.py` line 118 |

## Portal lines

| Order | Line | Source |
| - | - | - |
| 1 | The preview scope line starts with `Scope: MSP,` and then the organization count | `src/mist/realtime/websocket_streams/web/static/websockets.js` line 784 |
| 2 | The preview scope line of one organization starts with `Scope: One organization` | `src/mist/realtime/websocket_streams/web/static/websockets.js` line 785 |
| 3 | The output choice `One combined CSV report (.csv)` | `src/mist/realtime/websocket_streams/web/templates/websockets_page.html` line 194 |

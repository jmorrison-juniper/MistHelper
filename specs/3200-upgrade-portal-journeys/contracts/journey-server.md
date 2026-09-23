# Contract: The journey server

**Feature**: #3200 | **Package**: `tests/support/upgrade_portal_e2e/harness/server/`

This contract states how the runner starts the journey server, which seams the
server replaces, and the test-only journey control.

## The process

`JourneyServer` follows the pattern of `capture_portal_server` in
`tests/e2e/upgrade_portal/conftest.py:585-610`.

| Item | Rule |
| - | - |
| Command | `python -m tests.support.upgrade_portal_e2e.harness.server.app` with the options below |
| Options | `--run-dir <path>`, `--port <number>`, `--fleet default\|large`, `--multiple <number>`, `--seed-defect <name>` |
| Address | `127.0.0.1` and a free port from the isolated resources (FR-001) |
| Environment | The child environment of `isolation/environment.py`, with each credential variable removed (SR-003) |
| Gate | `UPGRADE_PORTAL_E2E_SESSION` from the browser suite (SR-013) |
| Control token | `UPGRADE_PORTAL_JOURNEY_TOKEN`, a random value for each server |
| Owner record | `server.pid` in the run directory. The runner stops only the process that this record names. |
| Server log | `server.log` in the run directory, ASCII only (FR-069) |
| Readiness | `GET /healthz` answers in the budget of `UPGRADE_PORTAL_E2E_READY_SECONDS` |
| Stop | Terminate, wait, then kill. Remove the owner record. |
| Restart | If the process stops during a journey, the runner fails that journey, keeps the log, and starts a new server (FR-011). |

## The seams

The server replaces four things only: the cloud boundary, the record stores,
the time source, and the registration of the test operators (FR-005).

| Seam | Value in the journey server |
| - | - |
| The record stores, the lock reader, the lock client, the authorization reader, the audit reader, and the file opener | The process-owned values of `build_e2e_overrides` |
| `mist_connector` | `MistConnectorTrap` of `build_e2e_overrides` |
| The cloud reader, the device reader, the versions reader, the options builder, the options view, the capture runner, and the stop runner | Production default. The server removes these seams from the overrides, so `install_seams` sets the default. |
| `ORG_UPGRADE_SERVICE`, `AGGREGATE_UPGRADE_SERVICE`, `ORG_UPGRADE_OPTIONS_VIEW`, `ORG_UPGRADE_OPTIONS_BUILDER` | Production default |
| `ORG_UPGRADE_WRITES_ENABLED` | `True`, in this process only (FR-010) |
| `RUN_LAUNCHER` | `JourneyLauncher`, with the four time seats of research R-04 |
| `CLOUD_LOGIN`, `CLOUD_BROWSER_TOKEN_SESSION`, `CLOUD_TOKEN_IDENTITY` | Factories that give a `SimulatedMistSession`. These seams are part of the cloud boundary. |
| `identity.SESSION_REGISTRY` | Operator A, operator B, and the operator of a reserved domain, each with a `SimulatedMistSession` |
| `driver.data_root` | The run directory (FR-008) |
| The browser poll interval | 5 seconds, the lowest value that the settings accept |

A contract test proves that each seam outside this table keeps its production
value.

## The guards of the server process

- The server process refuses each socket connection to an address other than
  `127.0.0.1`. Each refusal counts as a trap hit (SR-002).
- The traps of `tests/support/upgrade_portal_e2e/traps/` stay active.
- An unknown cloud URI gets status 404 and a harness gap. See
  [simulated-cloud.md](simulated-cloud.md).

## The journey control

The server registers the blueprint only when the gate variable is set. The
portal code never imports the blueprint. Each request must hold the header
`X-Journey-Token` with the control token. Each body is JSON.

| Method | Path | Body | Effect |
| - | - | - | - |
| POST | `/__journey/marker` | `journey`, `step` | Sets the marker of the request log |
| GET | `/__journey/clock` | None | Gives `now`, `multiple`, and each move |
| POST | `/__journey/clock/advance` | `seconds`, more than zero | Moves the journey clock forward (FR-038) |
| POST | `/__journey/faults/device` | `mac`, `outcome`, `cause`, `version` | Sets the outcome of one device (FR-030) |
| POST | `/__journey/faults/write` | `call`, `match`, `answer`, `status`, `uses` | Sets the answer of one write (FR-031) |
| POST | `/__journey/faults/clear` | None | Removes each fault |
| POST | `/__journey/sessions/expire` | `owner` | Ends one operator session at once (FR-040) |
| POST | `/__journey/sessions/abandon` | `owner` | Marks one session as abandoned |
| POST | `/__journey/locks/expire` | `site_id` | Ends one site lock at once |
| GET | `/__journey/ledger` | Query `since` | Gives each `CallRecord` after that sequence number |
| GET | `/__journey/gaps` | None | Gives each `HarnessGap` |

| Status | Meaning |
| - | - |
| 200 | The control made the change. |
| 400 | The body breaks this contract. |
| 403 | The token is missing or wrong. |
| 404 | The gate variable is not set, so the blueprint does not exist. |

The journey control changes only the simulated cloud, the journey clock, the
test sessions, and the site locks (FR-041). A seeded defect is a start option
of the server. The control cannot set a seeded defect.

## The seeded defects

| Name | What the server changes at start | Journeys that must fail |
| - | - | - |
| `second-child-write` | One child gets a second write | `F-DOUBLE-M`, `F-REPLAY-M`, and each `M-*` case |
| `gateway-on-ap-route` | A gateway child goes through the organization AP route | `M-G`, `M-AG`, `M-SG`, `M-ASG` |
| `dropped-option` | The write loses one upgrade option | Each happy path that sets that option |

## The request log line

The middleware writes one line for each request (FR-009). The line holds no
query string and no credential.

```text
journey-request run=<run_id> journey=<case> step=<number> method=<method> path=<path> status=<code> server_ms=<float> cloud_calls=<count> cloud_ms=<float>
```

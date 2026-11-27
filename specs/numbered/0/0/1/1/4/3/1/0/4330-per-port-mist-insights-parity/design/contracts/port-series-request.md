# Contract: Port Series Request

The method is defined in the installed SDK with the `port_id` argument at line 295 (R-45). The SDK adds each query value only when the value is set (R-85). The OpenAPI operation defines `port_id` as a query field (R-38).

## Call Shape

| Argument | Value | Source | Requirement |
| - | - | - | - |
| `mist_session` | The shared session of the portal | Service instance | FR-006 |
| `site_id` | Site identifier of the gateway | Bulk `gateways` dataset (R-82) | FR-001 |
| `device_id` | Gateway device UUID | Bulk `gateways` dataset (R-82) | FR-001 |
| `metrics` | `rx_bps,tx_bps` | Fixed string | FR-002 |
| `port_id` | Mist port name, for example `ge-0/0/1` | Bulk `ports` dataset with usage `wan` (R-13) | FR-001 |
| `start` | Epoch seconds for the window start | Window rules in `design/data-model.md` | FR-002 |
| `end` | Epoch seconds for the window end, at a UTC hour | Window rules in `design/data-model.md` | FR-002 |
| `interval` | `1h` | Fixed string | FR-002 |
| `limit` | `168` | Fixed integer, one page for seven days (R-40) | FR-003 |
| `page` | `1` | Fixed integer | FR-003 |
| `duration` | Not set | The window uses `start` and `end` | FR-002 |

The SDK adds each query value only when the value is set (R-85). The SDK sends `port_id` as one query field (R-38). The `limit` value overrides the SDK default of 100 (R-46).

## Window

- The end equals the latest completed UTC hour, as an integer epoch.
- The start equals the end minus 604800 seconds, as an integer epoch.
- Both values use `str(int(value))` before the call, as the SDK expects text.

## Request Rules

- The call runs inside the organization scope for the gateway site (D-7).
- The call goes through the service request method once for each token (R-75 and R-11).
- The call starts only when the phase holds the worker lease (TC-17).
- The call counts toward the planned calls for the refresh (D-8).
- The call never uses direct HTTP (R-69).

Caution: a call that starts without the organization scope fails closed under shared admission (R-22). The failure looks like a missing series.

## Logging

- Before the call, the worker logs one info line with the organization, the gateway identifier, and the port name.
- After the call, the worker logs one debug line with the status, the sample count, and the coverage.
- The log lines carry no token, cookie, URL with credentials, or response body (FR-017).

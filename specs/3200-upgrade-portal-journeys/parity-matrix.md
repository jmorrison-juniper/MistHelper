# Parity matrix: single-site mode and multi-site mode

**Feature**: #3200 | **Measured**: 2026-09-23 | **Sources**: the journeys of
`tests/e2e/upgrade_portal/journeys/`, the live read-only journey of port 8056,
the container logs, and the code at `origin/main` 87254831.

Status words: **present** (the capability works), **partial** (it exists with
a defect), **absent** (the mode has no such capability).

## Summary

| Mode | Present | Partial | Absent |
| - | - | - | - |
| Single-site | 36 | 4 | 0 |
| Multi-site | 4 | 19 | 17 |

The multi-site mode reaches full parity on 4 of 40 capabilities. Two defects
block every live multi-site write: #3203 (the write gate has no setting) and
#3220 (a running job releases its site locks). Fix #3220 before #3203.

## Scope and selection

| ID | Capability | Single-site | Multi-site | Gap owner |
| - | - | - | - | - |
| P-01 | Select an organization | present | present | - |
| P-02 | Select the mode | present | partial: the help text is wrong about one organization job | #3215 |
| P-03 | Select the sites | present (one site) | partial: no sort, no device filter, raw JSON for an empty selection | #3216, #3240 |
| P-04 | Read the site inventory | present (inventory page) | partial: no running version, no selection, a router with no note | #3209 |
| P-05 | Select single devices | present | absent | #3209 |
| P-06 | Site lock with heartbeat before the work | present | partial: locks start at submit only | #3220 |
| P-07 | Lock conflict names the holder | present | partial: the refusal names no job | #3224 |

## Options

| ID | Capability | Single-site | Multi-site | Gap owner |
| - | - | - | - | - |
| P-08 | Select the device families | present | present | - |
| P-09 | Choose a version from the offered list | present | absent: free text | #3205 |
| P-10 | Choose a version for each model or each device | present | absent: one version for each family | #3204 |
| P-11 | Separate SRX and SSR gateway versions | present (SSR channel, #2157) | absent: one gateway field | #3204 |
| P-12 | Show only the controls of the chosen families | present | partial: cleared families keep their controls | #3207 |
| P-13 | Strategy (canary, big bang, RRM, serial) | present | partial: canary phases stay visible for every strategy | #3207 |
| P-14 | Canary phase rule | partial: no rise-to-100 rule | partial: no rise-to-100 rule | #3223 (PR #3235) |
| P-15 | Reboot choice and reboot delay | present | partial: the placeholder looks like a value | #3208 |
| P-16 | Junos file action, force | present | partial: Back resets both | #3221 |
| P-17 | Start time | present | partial: a forced malformed value reaches the confirm page (a real browser input cannot hold it, so not filed) | - |
| P-18 | Advanced AP controls (P2P, RRM batches, mesh) | present | absent | #3204 |
| P-19 | Refusal message names the control | partial: `version_target` | partial: `version_target`, and the message is above the fold | #3206 |
| P-20 | Back from confirm keeps every choice | present | absent | #3221 |

## Confirmation and start

| ID | Capability | Single-site | Multi-site | Gap owner |
| - | - | - | - | - |
| P-21 | Pre-check capture before the start | present | absent | #3243 |
| P-22 | Confirm page shows the whole plan | present (advanced summary, warnings) | partial: counts only, raw words | #3222 |
| P-23 | Typed confirmation word | present | present | - |
| P-24 | One write for each claimed child, replay refusal | present | present (server) | - |
| P-25 | Start closes after the first click | present | partial: a double click strands the operator | #3242 |
| P-26 | Deployment write gate can open | present | absent: no setting | #3203 |

## Progress and control

| ID | Capability | Single-site | Multi-site | Gap owner |
| - | - | - | - | - |
| P-27 | Phase cascade with a settle gate | present | absent | #3245 |
| P-28 | Running state stays running | present | absent: `attention_required` | #3220 (PR #3234) |
| P-29 | Device table with versions before and after | present | absent | #3249 |
| P-30 | Mist account label and last update time | present | absent | #3249 |
| P-31 | Poll that stops at a final state | present | partial: stops at `attention_required` | #3220 (PR #3234) |
| P-32 | Stop with outcome lists | present | partial: one cancel form | #3246 |
| P-33 | Cancel hidden after the end | present | partial: offered after completion | #3225 |
| P-34 | Retry, reschedule, reconciliation | present | absent | #3247 |
| P-35 | Owner check on the progress page | present | partial: any job ID renders | #3241 |

## After the upgrade

| ID | Capability | Single-site | Multi-site | Gap owner |
| - | - | - | - | - |
| P-36 | Post-check capture | present | absent | #3244 |
| P-37 | Comparison of the two captures | present | absent | #3244 |
| P-38 | History entry | present | absent | #3248 |
| P-39 | Export of the captures | partial: a verified export answered 404 in the stand-in server | absent | #3244 |
| P-40 | Session expiry leads to the sign-in form | partial: raw JSON | partial: raw JSON | #3214 (PR #3239) |

## Journeys that prove each row

| Rows | Journey file |
| - | - |
| P-01 to P-26, multi-site | `test_upj_multisite_journeys.py`, `test_multisite_journeys.py` |
| P-01 to P-40, single-site | `test_upj_single_site_journeys.py`, `test_single_site_journeys.py` |
| P-28, P-31, P-33, P-35 | `test_upj_multisite_journeys.py::TestMultiSiteFamilyJourneys` (strict xfail) |
| P-03, P-04, P-09, P-15, P-19, P-40 | live read-only journey, screenshots in `.playwright-mcp/upj-live/` |

Each strict xfail names the issue of its row. When a fix lands, the xfail turns
red, and the fix author removes the marker.

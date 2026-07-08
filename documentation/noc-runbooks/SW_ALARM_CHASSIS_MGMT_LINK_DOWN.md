# SW_ALARM_CHASSIS_MGMT_LINK_DOWN

## Overview

| Field | Value |
|---|---|
| **Alert Name** | SW_ALARM_CHASSIS_MGMT_LINK_DOWN |
| **Mist alarm key** | `sw_alarm_chassis_mgmt_link_down` |
| **Platform** | Juniper Mist EX Series Switch |
| **Mist native severity** | `warn` |
| **NOC severity** | **Critical** (override — see rationale below) |
| **Group** | `infrastructure` |
| **Clear event key** | `sw_alarm_chassis_mgmt_link_down_clear` |
| **Correlated alarms** | `switch_down`, `vc_master_changed`, `vc_backup_failed`, `sw_alarm_chassis_pem`, `sw_alarm_chassis_psu` |
| **Prerequisites** | None — fires automatically when the dedicated management (`me0` / `vme`) interface goes down. |
| **Description** | The dedicated chassis management Ethernet link is down. Remote management via the out-of-band management network may be unavailable. Data forwarding on production interfaces may continue if only the management interface has failed. |

### Severity rationale (Mist `warn` → NOC `critical`)

Mist ships this alarm at `warn` because the production data plane typically keeps forwarding when only `me0`/`vme` drops. We escalate to **critical** because loss of out-of-band management removes our ability to remediate the device if a production-side issue subsequently develops. If you are running with no OOB dependency (in-band management only), consider aligning the NOC severity back to `warn`.

## Impact

- Loss of out-of-band management connectivity.
- Unable to reach the switch through the MGMT interface (`me0` on standalone, `vme` on Virtual Chassis).
- Potential loss of remote monitoring paths that depend on the OOB network.
- Data forwarding on production ports may continue normally.
- Delayed troubleshooting if in-band remote access becomes unavailable.
- On a Virtual Chassis, if the master's `me0` drops, VME may fail over to another member — verify which member is currently master.

## Required Information

| Category | Data to capture |
|---|---|
| Device | Site, Hostname, Serial Number, Software Version, Mist device ID |
| Management | MGMT IP, Gateway, VLAN (if applicable), Link Status, `me0` vs `vme` |
| Physical | Connected management switch/router, cable, port |
| Virtual Chassis | VC role of affected member (master / backup / linecard); is `vme` still reachable via another member? |
| Timeline | Alert time (UTC), recent changes (last 24 h), audit logs |
| Correlated Alarms | Any active alarms on the device or its management upstream within the last 15 min |

See Shared Appendix §5 for the always-required ticket fields.

## Validation

| Check | Command / Action |
|---|---|
| Switch reachable in Mist? | Mist UI → Switches → *device* → Health |
| Management interface state (standalone) | `show interfaces me0` |
| Management interface state (VC) | `show interfaces vme` |
| Chassis and VC role | `show virtual-chassis` and `show chassis hardware` |
| Management routing | `show route table inet.0 <management-gateway>` |
| Peer switch/router port state | Verify management switch port is up (via that device) |
| Recent logs (interface-scoped) | `show log messages \| match me0` (or `vme`) |
| Chassis alarms | `show chassis alarms` |
| Reachability from switch | `ping <management-gateway>` and `ping <mist-cloud-reachable-host>` |

See Shared Appendix §6 for the full Junos command reference.

## Resolution

| Area | Action |
|---|---|
| Cable | Reseat or replace the management cable. |
| Remote device | Verify the connected management switch/router port is up and not err-disabled. |
| Configuration | Verify MGMT IP, gateway, and interface configuration against source-of-truth. |
| Hardware | Replace failed NIC/port if hardware fault is confirmed (see `show chassis alarms` for physical-layer indicators). |
| Virtual Chassis | If master role has moved, confirm intended master and re-elect if operationally required (planned change only). |
| Audit | Review Mist audit logs for recent changes that may have affected management config. |
| Recovery | Confirm management interface is up, reachable from the OOB network, and the paired clear event has fired. |

## Closure Criteria

- Management interface (`me0` or `vme`) is operational.
- Remote access from the OOB management network is restored.
- **The paired clear event `sw_alarm_chassis_mgmt_link_down_clear` has been received** — this is the machine-verifiable close signal.
- No recurrence of `sw_alarm_chassis_mgmt_link_down` within a 30-minute debounce window.
- Root cause is documented on the ticket.

## Mist GUI Navigation

| Task | Navigation |
|---|---|
| Verify alert | Monitor → Alerts (Alarms) → filter by `sw_alarm_chassis_mgmt_link_down` |
| Switch health | Switches → *device* → Health / Insights |
| Management status | Switches → *device* → Front Panel / Details |
| Events (raw) | Monitor → Events |
| Audit logs | Organization → Audit Logs |

## Junos Commands (quick reference)

| Purpose | Command |
|---|---|
| System info | `show system information` |
| Version | `show version` |
| Chassis hardware / FRUs | `show chassis hardware` |
| Chassis alarms | `show chassis alarms` |
| Management interface (standalone) | `show interfaces me0` |
| Management interface (VC) | `show interfaces vme` |
| Virtual Chassis state | `show virtual-chassis` |
| Routing | `show route` |
| Logs | `show log messages \| match <interface>` |
| Ping gateway | `ping <management-gateway>` |
| Ping known-reachable host | `ping <reachable-management-host>` |

## Escalation

Per Shared Appendix §8. Tier 1 NOC can self-clear cable, port, and configuration causes. Escalate to Tier 2 for hardware replacement, VC master election changes, or when the OOB management upstream is itself impaired.

# SW_ALARM_CHASSIS_MGMT_LINK_DOWN

## Overview

| Field | Value |
|---|---|
| **Alert Name** | SW_ALARM_CHASSIS_MGMT_LINK_DOWN |
| **Mist alarm key** | `sw_alarm_chassis_mgmt_link_down` |
| **Platform** | Juniper EX4100 Virtual Chassis (2-member pair at a retail branch). Standalone EX4100 uses `me0`; a VC uses `vme`. |
| **Mist native severity** | `warn` |
| **NOC severity** | **Critical** (override — see rationale below) |
| **Group** | `infrastructure` |
| **Clear event key** | `sw_alarm_chassis_mgmt_link_down_clear` |
| **Correlated alarms** | `switch_down`, `vc_master_changed`, `vc_backup_failed`, `sw_alarm_chassis_pem`, `sw_alarm_chassis_psu` |
| **Prerequisites** | None — fires automatically when the dedicated management (`me0` / `vme`) interface goes down. |
| **Description** | The dedicated chassis management Ethernet link is down. On the retail-branch EX4100 VC this is the `vme` (VC-shared virtual management) interface, backed by the current master's physical `me0` port. Remote management via the out-of-band management network may be unavailable. Data forwarding on production interfaces (uplink to SSR130, downstream AP / POS / user ports) may continue if only the management interface has failed. |

### Severity rationale (Mist `warn` → NOC `critical`)

Mist ships this alarm at `warn` because the production data plane typically keeps forwarding when only `me0`/`vme` drops. We escalate to **critical** because loss of out-of-band management removes our ability to remediate the switch if a production-side issue develops on top of it — and at a single-SSR retail branch, in-band remote access rides the very uplink most likely to fail next.

**Retail-branch note:** many of our retail sites have no separate OOB management network — mgmt rides the same site LAN as production. In that case there is no independent path to lose, and `warn` is appropriate. Confirm the branch's OOB posture with your SOR before treating this as `critical`.

## Impact

- Loss of out-of-band management connectivity to the branch EX4100 VC (if the branch has an OOB path).
- Unable to reach the switch through the MGMT interface — `vme` on the 2-member VC (backed by whichever member is currently master).
- Potential loss of remote monitoring paths that depend on the OOB network.
- Data forwarding on production ports (uplink to SSR130, AP / POS / user ports) usually continues normally.
- Delayed troubleshooting if in-band remote access — which at most retail branches rides the same LAN — becomes unavailable.
- **VC-specific:** if the master's `me0` drops, `vme` can fail over to the backup member's `me0`. Check `show virtual-chassis` for the current master; the outage may effectively resolve itself if the peer member's `me0` is healthy.

## Required Information

| Category | Data to capture |
|---|---|
| Device | Site, Hostname, Serial Number, Junos version, Mist device ID (both VC members) |
| Management | MGMT IP, Gateway, VLAN (if applicable), Link Status. **Always `vme` on the retail branch VC** — capture which member's `me0` currently backs it. |
| Physical | Connected upstream device / port for the master's `me0`, and for the backup's `me0` if wired. Cable / patch panel path. |
| Virtual Chassis | Current master / backup roles (`show virtual-chassis`); is `vme` still reachable via the peer member's `me0`? |
| OOB context | Does this branch have a dedicated OOB path, or is management in-band? (Determines effective severity.) |
| Timeline | Alert time (UTC), recent changes (last 24 h), audit logs |
| Correlated Alarms | Any active alarms on the VC or the SSR130 in the last 15 min (particularly `sw_vc_port_down`, `vc_master_changed`, `switch_down`) |

See Shared Appendix §5 for the always-required ticket fields.

## Validation

| Check | Command / Action |
|---|---|
| Switch reachable in Mist? | Mist UI → Switches → *device* → Health |
| Virtual Chassis management interface | `show interfaces vme` |
| Underlying master `me0` | `show interfaces me0` (run on the current master member) |
| Backup member `me0` (fallback path) | `show interfaces me0` from the backup — is its `me0` wired and up? |
| VC roles and members | `show virtual-chassis` and `show chassis hardware` |
| Management routing | `show route table inet.0 <management-gateway>` |
| Peer switch/router port state | Verify management switch port is up (via that device) |
| Recent logs (interface-scoped) | `show log messages \| match vme` (and `me0`) |
| Chassis alarms | `show chassis alarms` |
| Reachability from switch | `ping <management-gateway>` |

See Shared Appendix §6 for the full Junos command reference.

## Resolution

| Area | Action |
|---|---|
| Fast triage | Check `show virtual-chassis`: if `vme` failed over to the backup member and management is reachable, the alarm may already be resolvable — the underlying `me0` still needs repair, but there is no service impact. |
| Cable | Reseat or replace the management cable on the affected member's `me0` port. |
| Remote device | Verify the connected management switch/router port is up and not err-disabled. |
| Configuration | Verify `vme` and per-member `me0` config against source-of-truth. |
| Hardware | Replace failed NIC/port if hardware fault is confirmed (see `show chassis alarms` for physical-layer indicators). |
| Virtual Chassis | If master role has moved and this is operationally undesired, plan a controlled re-election — do not force one to resolve this alarm. |
| Audit | Review Mist audit logs for recent changes that may have affected management config. |
| Recovery | Confirm management interface is up, reachable from the OOB network (or from the branch LAN if in-band), and the paired clear event has fired. |

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

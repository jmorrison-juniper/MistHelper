# SW_CRITICAL_PORT_DOWN

> **Renamed from `INTERFACE_DOWN`.** Mist does not emit a generic "any interface down" alarm — such an alarm would be pure noise (endpoints unplug all day). The closest useful Mist alarm is `sw_critical_port_down`, which fires only for ports explicitly flagged as **critical** in the port profile. Related port-issue alarms (`port_flap`, `port_stuck`, `bad_cable`, `sw_bad_optics`, `sw_negotiation_incomplete`) each have their own runbook — see cross-references below.

## Overview

| Field | Value |
|---|---|
| **Alert Name** | SW_CRITICAL_PORT_DOWN |
| **Mist alarm key** | `sw_critical_port_down` |
| **Platform** | Juniper Mist EX Series Switch (validated against EX4400) |
| **Mist native severity** | `warn` |
| **NOC severity** | **Critical** (override — see rationale below) |
| **Group** | `infrastructure` |
| **Clear event key** | `sw_critical_port_up` |
| **Correlated alarms** | `port_flap`, `port_stuck`, `bad_cable`, `sw_bad_optics`, `sw_negotiation_incomplete`, `sw_mtu_mismatch`, `sw_port_storm_control`, `switch_down`, `ap_offline` |
| **Prerequisites** | **The port must be flagged as "critical" in the Mist port profile.** Without this flag the alarm will not fire. Configure via Site → Switch → Port Configuration → *Critical Port*, or via port profile template. |
| **Description** | An EX physical or logical port marked as **critical** has transitioned to the Down state. Critical ports typically include uplinks, IDF/MDF links, LAG members, and ports serving essential downstream devices (APs, IP phones, servers, downstream switches). The failure of a critical port implies loss of connectivity for connected devices or network services. |

### Severity rationale (Mist `warn` → NOC `critical`)

Mist ships this as `warn` because port-down events span a wide impact range. Because only *critical* ports fire this alarm, we escalate to **critical** — the port has been explicitly designated as important. If any critical-port designations turn out to be over-tagged (e.g. every access port), retune the port profile rather than lowering NOC severity.

## Impact

- Loss of endpoint or uplink connectivity for the affected port.
- Client, AP, IP phone, or downstream switch may become unreachable.
- Potential loss of VLAN or trunk connectivity if the port is a trunk.
- LACP bundle degradation if the port is a LAG member.
- Reduced network redundancy on the affected fabric segment.
- Possible site outage if the port is the sole/primary uplink.
- If the port is a member of an ESI-LAG in an EVPN fabric, traffic reconverges via the peer, but redundancy is degraded.

## Required Information

| Category | Data to capture |
|---|---|
| Device | Site Name, Hostname, Serial Number, Junos Version, Mist device ID |
| Port classification | `access` / `uplink` / `IDF-MDF` / `server-edge` / `AP` / `VCP` / `LAG-member` |
| Interface | Interface Name, Description, Admin Status, Oper Status, VLAN(s), Speed, Duplex |
| Connected device | LLDP neighbor, MAC address, previous known device |
| Optics (if fiber) | Media type, DDM Tx/Rx power, laser bias, temperature |
| Timeline | Alert timestamp (UTC), recent configuration changes, related audit log entries |
| Correlated Alarms | Any active alarms on the device or connected downstream device in the last 15 min |

## Validation

| Check | Command / Action |
|---|---|
| Switch online in Mist | Mist UI → Switches → *device* → Health |
| Interface state summary | `show interfaces terse` |
| Interface detail | `show interfaces <interface> extensive` |
| Interface configuration (admin-down vs link-down) | `show configuration interfaces <interface>` |
| Live counters (errors, CRC, drops) | `monitor interface <interface>` |
| Optics DDM (fiber only) | `show interfaces diagnostics optics <interface>` |
| Neighbor discovery | `show lldp neighbors` |
| MAC learning (post-recovery) | `show ethernet-switching table interface <interface>` |
| LACP status (if LAG) | `show lacp interfaces` |
| LACP PDU stats | `show lacp statistics interfaces <interface>` |
| Storm control state | `show ethernet-switching interface <interface>` |
| Chassis / port alarms | `show chassis alarms` |
| Logs (interface-scoped) | `show log messages \| match <interface>` |
| Ping neighbor (if L3) | `ping <neighbor-ip>` |

See Shared Appendix §6 for the full Junos command reference.

## Resolution

| Area | Action |
|---|---|
| Cable / optics | Inspect and reseat / replace cable, DAC, or SFP. For fiber, verify DDM levels are within manufacturer spec. |
| Connected device | Verify endpoint or upstream/downstream device is powered on and its port is up. |
| Interface configuration | Verify interface is `admin up`, VLAN/LAG configuration is correct, and no unintended `disable` in config. |
| Speed / duplex | If `sw_negotiation_incomplete` is co-firing, verify auto-neg / hard-set speed matches the peer. |
| Storm control | If `sw_port_storm_control` is co-firing, identify and stop the storm source before clearing. |
| PoE (if applicable) | Verify PoE status for APs or IP phones; check budget (`show poe interface`). |
| Hardware | Replace faulty transceiver, cable, or switch port if hardware fault is confirmed. |
| Configuration changes | Review Mist audit logs; restore configuration if a recent change caused the outage. |
| Recovery | Confirm the port returns to Up, traffic flows, and the paired clear event has fired. |

## Closure Criteria

- Affected port is operational (`admin up`, `oper up`).
- Connected device is reachable, VLAN and LACP membership function normally.
- **The paired clear event `sw_critical_port_up` has been received.**
- No recurrence of `sw_critical_port_down` within a 30-minute debounce window.
- No related Marvis alarms (`port_flap`, `port_stuck`, `bad_cable`) active on the same port.
- Root cause is documented on the ticket.

## Mist GUI Navigation

| Task | Navigation |
|---|---|
| Verify alert | Monitor → Alerts (Alarms) → filter by `sw_critical_port_down` |
| Switch health | Switches → *device* → Health |
| Port status / front panel | Switches → *device* → Front Panel / Port Configuration |
| Critical port flag | Switches → *device* → Port Configuration → *Critical Port* toggle |
| Connected clients on the port | Clients → Connected Devices |
| Switch events | Monitor → Events |
| Audit logs | Organization → Audit Logs |

## Junos Commands (quick reference)

| Purpose | Command |
|---|---|
| System info | `show system information` |
| Version | `show version` |
| Chassis hardware | `show chassis hardware` |
| Interface summary | `show interfaces terse` |
| Interface details | `show interfaces <interface> extensive` |
| Interface configuration | `show configuration interfaces <interface>` |
| Live counters | `monitor interface <interface>` |
| Optics DDM | `show interfaces diagnostics optics <interface>` |
| LLDP neighbors | `show lldp neighbors` |
| MAC table | `show ethernet-switching table interface <interface>` |
| LACP | `show lacp interfaces` |
| LACP stats | `show lacp statistics interfaces <interface>` |
| Logs | `show log messages \| match <interface>` |
| Chassis alarms | `show chassis alarms` |
| Ping | `ping <neighbor-ip>` |

## Cross-references (sibling alarms)

If the current alarm co-fires with any of these, resolve the co-fired alarm first — it is usually the root cause:

- `port_flap` — repeated up/down flapping
- `port_stuck` — port up but traffic broken (Marvis)
- `bad_cable` — Marvis-identified physical fault
- `sw_bad_optics` — DDM thresholds crossed
- `sw_negotiation_incomplete` — speed/duplex mismatch (Marvis)
- `sw_mtu_mismatch` — MTU mismatch (Marvis)
- `sw_port_storm_control` — storm control holding port down

## Escalation

Per Shared Appendix §8. Tier 1 NOC can self-clear cable, optic, and remote-device causes. Escalate to Tier 2 for hardware replacement or when the port is part of an EVPN fabric with unclear failover behavior.

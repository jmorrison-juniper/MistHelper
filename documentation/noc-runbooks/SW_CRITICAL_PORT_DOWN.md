# SW_CRITICAL_PORT_DOWN

> **Renamed from `INTERFACE_DOWN`.** Mist does not emit a generic "any interface down" alarm — such an alarm would be pure noise (endpoints unplug all day). The closest useful Mist alarm is `sw_critical_port_down`, which fires only for ports explicitly flagged as **critical** in the port profile. Related port-issue alarms (`port_flap`, `port_stuck`, `bad_cable`, `sw_bad_optics`, `sw_negotiation_incomplete`) each have their own runbook — see cross-references below.

## 1. Overview

| Field | Value |
|---|---|
| **Alert Name** | SW_CRITICAL_PORT_DOWN |
| **Mist alarm key** | `sw_critical_port_down` |
| **Platform** | Juniper EX4100 (2-member Virtual Chassis at a retail branch — typically EX4100-48P for PoE). |
| **Mist native severity** | `warn` |
| **NOC severity** | **Critical** (override — see rationale below) |
| **Group** | `infrastructure` |
| **Clear event key** | `sw_critical_port_up` |
| **Correlated alarms** | `port_flap`, `port_stuck`, `bad_cable`, `sw_bad_optics`, `sw_negotiation_incomplete`, `sw_mtu_mismatch`, `sw_port_storm_control`, `switch_down`, `ap_offline` |
| **Prerequisites** | **The port must be flagged as "critical" in the Mist port profile.** Without this flag the alarm will not fire. Configure via Site → Switch → Port Configuration → *Critical Port*, or via port profile template. At a retail branch, ports typically flagged critical are: the uplink LAG to the SSR130, PoE-served AP ports, POS terminal ports, IP-phone ports, and any back-office server port. |
| **Description** | An EX4100 physical or logical port marked as **critical** has transitioned to Down. At a retail branch the impact of a critical-port failure is typically visible to the store immediately — an AP drops, a POS lane stops taking cards, a phone goes offline, or in the worst case the uplink to the SSR130 loses a member and store traffic reconverges (or, if the uplink is a single link rather than a LAG, the store loses WAN). |

### Severity rationale (Mist `warn` → NOC `critical`)

Mist ships this as `warn` because port-down events span a wide impact range. Because only *critical* ports fire this alarm, we escalate to **critical** — the port has been explicitly designated as important. If any critical-port designations turn out to be over-tagged (e.g. every access port), retune the port profile rather than lowering NOC severity.

## 2. Impact

- Loss of endpoint or uplink connectivity for the affected port.
- **Uplink to SSR130.** If the port is a member of the LAG to the SSR130, the LAG loses a member and forwards on the survivor; if the LAG is down to zero members (or the uplink is a single link), the branch loses WAN.
- **Downstream device offline.** A critical port serving a Mist AP, POS terminal, IP phone, or back-office server takes that device offline. In a store this is user-visible immediately.
- Potential loss of VLAN or trunk connectivity if the port is a trunk.
- LACP bundle degradation if the port is a LAG member (uplink or member-to-server bundle).
- Reduced fabric redundancy on the affected segment.
- PoE loss on the affected port for AP / phone / camera endpoints.

## 3. Required Information

| Category | Data to capture |
|---|---|
| Device | Site Name, Hostname (which EX4100 member), Serial Number, Junos Version, Mist device ID |
| Port classification | `uplink-to-SSR130` / `AP` / `POS` / `IP-phone` / `server` / `back-office` / `access` / `VCP` / `LAG-member` |
| Interface | Interface Name (e.g. `ge-0/0/47`, `xe-0/2/0`), Description, Admin Status, Oper Status, VLAN(s), Speed, Duplex, PoE state (if applicable) |
| Connected device | LLDP neighbor (SSR130 hostname if uplink, AP name if AP), MAC address, previous known device |
| Optics (if fiber) | Media type, DDM Tx/Rx power, laser bias, temperature |
| Timeline | Alert timestamp (UTC), recent configuration changes, related audit log entries |
| Correlated Alarms | Any active alarms on the EX4100 or on the connected downstream device (e.g. `ap_offline`) in the last 15 min |

## 4. Validation

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

## 5. Resolution

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

## 6. Closure Criteria

- Affected port is operational (`admin up`, `oper up`).
- Connected device is reachable, VLAN and LACP membership function normally.
- **The paired clear event `sw_critical_port_up` has been received.**
- No recurrence of `sw_critical_port_down` within a 30-minute debounce window.
- No related Marvis alarms (`port_flap`, `port_stuck`, `bad_cable`) active on the same port.
- Root cause is documented on the ticket.

## 7. Mist GUI Navigation

| Task | Navigation |
|---|---|
| Verify alert | Monitor → Alerts → filter by `sw_critical_port_down` |
| Switch health | Switches → *device* → Insights |
| Port status / front panel | Switches → *device* → Front Panel |
| Critical port flag | Switches → *device* → Port Configuration → *Critical Port* toggle |
| Connected clients on the port | Clients → Wired Clients |
| Switch events | Monitor → Events |
| Audit logs | Organization → Audit Logs |

## 8. Junos Commands (quick reference)

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

## 9. Cross-references (sibling alarms)

If the current alarm co-fires with any of these, resolve the co-fired alarm first — it is usually the root cause:

- `port_flap` — repeated up/down flapping
- `port_stuck` — port up but traffic broken (Marvis)
- `bad_cable` — Marvis-identified physical fault
- `sw_bad_optics` — DDM thresholds crossed
- `sw_negotiation_incomplete` — speed/duplex mismatch (Marvis)
- `sw_mtu_mismatch` — MTU mismatch (Marvis)
- `sw_port_storm_control` — storm control holding port down

## 10. Escalation

Per Shared Appendix §8. Tier 1 NOC can self-clear cable, optic, and remote-device causes. Escalate to Tier 2 for hardware replacement, or when the affected port is a member of the uplink LAG to the SSR130 and the LAG is currently at zero surviving members (store WAN down).

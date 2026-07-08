# SW_VC_PORT_DOWN

## Overview

| Field | Value |
|---|---|
| **Alert Name** | SW_VC_PORT_DOWN |
| **Mist alarm key** | `sw_vc_port_down` |
| **Mist display name** | Virtual Chassis Port Down |
| **Platform** | Juniper Mist EX Series switches configured as a Virtual Chassis (VC) — e.g. EX4400 VC |
| **Mist native severity** | `critical` |
| **NOC severity** | **Critical** (native — no override) |
| **Group** | `infrastructure` |
| **Clear event key** | `sw_vc_port_up` |
| **Correlated alarms** | `vc_master_changed`, `vc_backup_failed`, `vc_member_deleted`, `vc_member_restarted`, `switch_down`, `sw_alarm_chassis_mgmt_link_down` |
| **Prerequisites** | The switch must be part of a Virtual Chassis (2+ members). Alarm fires when a VC port (VCP) between members goes down. Standalone switches cannot fire this alarm. |
| **Description** | A Virtual Chassis (VC) port has transitioned to the Down state. VCPs form the interconnect fabric between VC members. Failure impacts inter-member communication, redundancy, and Virtual Chassis stability — a full VCP outage can split the VC into isolated fragments. |

### Severity note (no override)

Unlike most `warn`-shipped port alarms, Mist ships `sw_vc_port_down` as `critical` natively. This is one of the few port-related alarms where Mist's default severity already reflects the blast radius (VC split risk), so no override is applied.

## Impact

- Loss of Virtual Chassis redundancy on the affected VCP link.
- **Potential Virtual Chassis split** — if the VC has only one VCP path between two members (no redundant VCPs), losing it partitions the chassis into isolated islands, each running its own control plane.
- Reduced fabric switching capacity between VC members.
- Loss of resiliency for links that use LAGs spanning VC members (member-to-member load-share breaks).
- Downstream connectivity issues for clients whose traffic egresses through the failed inter-member path.
- Potential service disruption during master/backup failover if the master election path is affected.
- Stale MAC/ARP entries until the fabric reconverges.

## Required Information

| Category | Data to capture |
|---|---|
| Device | Site, Virtual Chassis name, Switch hostname, Serial Number, Junos version, Mist device ID |
| VC context | VC member ID (FPC number), member role (master / backup / linecard), total member count |
| VC port | VCP name (`vcp-0`, `vcp-255/1/0`, or dedicated VCP port), Interface status, Connected member (peer FPC) |
| Physical | DAC / fiber / SFP type, cable condition, is this a dedicated VCP or a converted network port |
| Timeline | Alert timestamp (UTC), recent VC config changes, member reboots, audit log entries |
| Correlated Alarms | Any active alarms on any VC member (or a co-fired `vc_master_changed` / `vc_member_deleted`) in the last 15 min |

See Shared Appendix §5 for the always-required ticket fields.

## Validation

| Check | Command / Action |
|---|---|
| VC healthy in Mist | Mist UI → Switches → *Virtual Chassis* → Health (primary/backup) |
| VC member roster | Switches → *Virtual Chassis* → Members |
| VC overall state | `show virtual-chassis` |
| VCP-specific state | `show virtual-chassis vc-port` |
| VCP detail (per port) | `show virtual-chassis vc-port <interface>` |
| Interface state | `show interfaces terse` |
| Interface detail | `show interfaces <vcp-interface> extensive` |
| Chassis hardware (per member) | `show chassis hardware` |
| Optics DDM (fiber VCP) | `show interfaces diagnostics optics <vcp-interface>` |
| Chassis alarms | `show chassis alarms` |
| Logs (VCP-scoped) | `show log messages \| match vcp` (or specific interface name) |
| VC master election events | `show log messages \| match vccpd` |

See Shared Appendix §6 for the full Junos command reference.

## Resolution

| Area | Action |
|---|---|
| Cable / DAC | Reseat or replace the VC cable / DAC. VC uses direct-attach copper or fiber depending on the VCP type — verify compatible cable spec (length, gauge, vendor). |
| Optics (fiber VCP) | Verify compatible optics on both ends; check DDM levels are within manufacturer spec. Replace faulty transceiver if DDM is out of range. |
| Member status | Confirm both VC members are online, powered, and reachable. If a member is down, resolve that first — the VCP alarm is a symptom, not root cause. |
| Configuration | Verify VC configuration consistency (VC ID, preprovisioned member roles, VCP assignments). A recent config change that revoked VCP status on a converted port will drop the port from VC. |
| Hardware | Replace failed VCP port, transceiver, or (last resort) the switch itself. |
| Audit | Review Mist audit logs for recent VC-related config changes in the last 24 h. |
| VC split recovery | If the VC has split, follow controlled rejoin procedure — do NOT power-cycle members without a plan, as this can force an unwanted master re-election. Escalate to Tier 2. |
| Recovery | Confirm the VCP returns to Up, all members are synchronized, master/backup roles are as expected, and the paired clear event has fired. |

## Closure Criteria

- Virtual Chassis is healthy: all expected members present, roles as designed.
- Affected VC port is `Up` and forwarding.
- **The paired clear event `sw_vc_port_up` has been received.**
- No recurrence of `sw_vc_port_down` for the same VCP within a 30-minute debounce window.
- No co-firing `vc_master_changed`, `vc_backup_failed`, or `vc_member_deleted` still active.
- Root cause is documented on the ticket, including which VCP link and whether redundant VCPs prevented a split.

## Mist GUI Navigation

| Task | Navigation |
|---|---|
| Verify alert | Monitor → Alerts (Alarms) → filter by `sw_vc_port_down` |
| Virtual Chassis health | Switches → *Virtual Chassis* → Health (primary/backup) |
| VC members | Switches → *Virtual Chassis* → Members |
| VC port status | Switches → *device* → Front Panel / Port Configuration |
| Switch events | Monitor → Events |
| Audit logs | Organization → Audit Logs |

## Junos Commands (quick reference)

| Purpose | Command |
|---|---|
| System info | `show system information` |
| Version | `show version` |
| Chassis hardware (per member) | `show chassis hardware` |
| Chassis alarms | `show chassis alarms` |
| Virtual Chassis state | `show virtual-chassis` |
| Virtual Chassis ports | `show virtual-chassis vc-port` |
| Specific VCP detail | `show virtual-chassis vc-port <interface>` |
| Interface summary | `show interfaces terse` |
| Interface detail | `show interfaces <vcp-interface> extensive` |
| Optics DDM (fiber VCP) | `show interfaces diagnostics optics <vcp-interface>` |
| VCP-scoped logs | `show log messages \| match vcp` |
| VC control-plane logs | `show log messages \| match vccpd` |

## Cross-references (sibling alarms)

If any of these are co-firing, resolve them together — VC-family alarms tend to cascade:

- `vc_master_changed` — new device elected as VC master (critical). Often co-fires when the current master's VCPs fail.
- `vc_backup_failed` — a new backup was elected (critical).
- `vc_member_deleted` — a VC member has left the chassis (critical) — usually root cause when this fires.
- `vc_member_restarted` — a member has rebooted (warn).
- `switch_down` — a whole member is offline.
- `sw_alarm_chassis_mgmt_link_down` — check whether `vme` is still reachable via a surviving member.

Triage rule: **`vc_member_deleted` or `switch_down` on a member is usually root cause; `sw_vc_port_down` alone is often the earliest symptom of an impending split.**

## Escalation

Per Shared Appendix §8. Tier 1 NOC can self-clear cable, optic, and single-VCP-flap causes when the VC remains healthy. **Escalate to Tier 2 immediately** for:

- Suspected or confirmed VC split
- Any active `vc_master_changed` / `vc_backup_failed` / `vc_member_deleted`
- Hardware replacement of a VC member
- Config changes to VCP assignment or preprovisioning

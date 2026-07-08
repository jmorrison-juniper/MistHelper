# SW_VC_PORT_DOWN

## Overview

| Field | Value |
|---|---|
| **Alert Name** | SW_VC_PORT_DOWN |
| **Mist alarm key** | `sw_vc_port_down` |
| **Mist display name** | Virtual Chassis Port Down |
| **Platform** | Juniper EX4100 Virtual Chassis (2-member pair at a retail branch — master + backup only, no linecard members). |
| **Mist native severity** | `critical` |
| **NOC severity** | **Critical** (native — no override) |
| **Group** | `infrastructure` |
| **Clear event key** | `sw_vc_port_up` |
| **Correlated alarms** | `vc_master_changed`, `vc_backup_failed`, `vc_member_deleted`, `vc_member_restarted`, `switch_down`, `sw_alarm_chassis_mgmt_link_down` |
| **Prerequisites** | The switch must be part of a Virtual Chassis. On the retail-branch EX4100 pair this is always a 2-member VC. Alarm fires when a VC port (VCP) between the two members goes down. Standalone switches cannot fire this alarm. |
| **Description** | A Virtual Chassis (VC) port between the two EX4100 members has transitioned to Down. VCPs form the inter-member interconnect. On a 2-member VC there is no third path to lean on: **if the branch is provisioned with only one VCP link between the members, this alarm is a pre-split warning**; if there is more than one VCP link, redundancy is degraded but the VC stays intact. |

### Severity note (no override)

Unlike most `warn`-shipped port alarms, Mist ships `sw_vc_port_down` as `critical` natively. This is one of the few port-related alarms where Mist's default severity already reflects the blast radius (VC split risk), so no override is applied.

## Impact

- Loss of Virtual Chassis redundancy on the affected VCP link.
- **Immediate VC split risk (2-member VC).** With only master + backup, if the site is wired with a single VCP link between them, losing it partitions the chassis into two isolated single-member fragments — each attempts to run its own control plane. If the site is wired with redundant VCPs (recommended), the VC survives the loss of one but is now unprotected against a second failure.
- Reduced fabric switching capacity between the two members.
- LAG bundles that span both members (e.g. the uplink to SSR130 built as a member-1 + member-2 LAG) lose the ability to load-share across members — the surviving link on each fragment continues to forward, but not as a bundle.
- Downstream connectivity issues for clients whose traffic must egress through the peer member (e.g. AP or POS terminal on member-1 whose only path to the SSR130 uplink lives on member-2).
- Potential service disruption during master/backup failover if the master-election path is affected.
- Stale MAC/ARP entries until the fabric reconverges.

## Required Information

| Category | Data to capture |
|---|---|
| Device | Site, Virtual Chassis name, both member hostnames, both serial numbers, Junos version, Mist device IDs |
| VC context | Which member (FPC 0 vs FPC 1) is currently master vs backup; total member count should be exactly 2 |
| VC port | VCP name (dedicated rear VCP on EX4100, or a converted network port), interface status, which member the peer end is on |
| Physical | DAC / fiber / SFP type; cable condition; is this a dedicated VCP port or a network port converted to VCP; is a second VCP link wired for redundancy? |
| Timeline | Alert timestamp (UTC), recent VC config changes, member reboots, audit log entries |
| Correlated Alarms | Any active alarms on either VC member (particularly a co-fired `vc_master_changed` / `vc_member_deleted` / `switch_down`) in the last 15 min |

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
| Member status | Confirm both EX4100 members are online, powered, and reachable. If a member is down, resolve that first — the VCP alarm is a symptom, not root cause. |
| Configuration | Verify VC configuration consistency (VC ID, preprovisioned master/backup roles, VCP assignments). A recent config change that revoked VCP status on a converted port will drop the port from VC. |
| Hardware | Replace failed VCP port, transceiver, DAC, or (last resort) the EX4100 member. |
| Audit | Review Mist audit logs for recent VC-related config changes in the last 24 h. |
| VC split recovery | If the VC has split into two single-member fragments, follow controlled rejoin procedure — do NOT power-cycle members without a plan, as this can force an unwanted master re-election. Escalate to Tier 2. |
| Recovery | Confirm the VCP returns to Up, all members are synchronized, master/backup roles are as expected, and the paired clear event has fired. |

## Closure Criteria

- Virtual Chassis is healthy: both EX4100 members present, master/backup roles as designed.
- Affected VC port is `Up` and forwarding.
- **The paired clear event `sw_vc_port_up` has been received.**
- No recurrence of `sw_vc_port_down` for the same VCP within a 30-minute debounce window.
- No co-firing `vc_master_changed`, `vc_backup_failed`, or `vc_member_deleted` still active.
- Root cause is documented on the ticket, including which VCP link failed and whether the branch was wired with redundant VCPs (i.e. whether the site was one failure away from a split).

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

- `vc_master_changed` — new device elected as VC master (critical). On a 2-member VC this means the former backup has taken over — often because the former master's VCPs or `me0`/`vme` path failed.
- `vc_backup_failed` — a new backup was elected (critical).
- `vc_member_deleted` — a VC member has left the chassis (critical) — on a 2-member pair this collapses the VC to a single standalone switch; usually root cause when this fires.
- `vc_member_restarted` — a member has rebooted (warn).
- `switch_down` — one of the two EX4100 members is offline.
- `sw_alarm_chassis_mgmt_link_down` — check whether `vme` is still reachable via the surviving member's `me0`.

Triage rule: **`vc_member_deleted` or `switch_down` on a member is usually root cause; `sw_vc_port_down` alone is often the earliest symptom of an impending split.**

## Escalation

Per Shared Appendix §8. Tier 1 NOC can self-clear cable, optic, and single-VCP-flap causes when the VC remains healthy (both members present, roles as designed). **Escalate to Tier 2 immediately** for:

- Suspected or confirmed VC split (2-member VC has partitioned into two single-member fragments)
- Any active `vc_master_changed` / `vc_backup_failed` / `vc_member_deleted`
- Hardware replacement of an EX4100 member
- Config changes to VCP assignment or preprovisioning

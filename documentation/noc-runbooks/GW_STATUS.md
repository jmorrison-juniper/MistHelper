# GW_STATUS

## Overview

| Field | Value |
|---|---|
| **Alert Name** | GW_STATUS |
| **Mist alarm key** | `gw_status` (generic gateway-state alarm — fires on transition to `Offline` / `Unreachable` / `Disconnected` / `Degraded`) |
| **Platform** | Juniper SSR130 (single gateway at a retail branch — no local HA peer). The same alarm key also fires on SRX gateways — an SRX-specific runbook is planned as Phase 2 because the CLI (Junos) differs from SSR PCLI. |
| **Mist native severity** | `critical` |
| **NOC severity** | **Critical** (native — no override) |
| **Group** | `infrastructure` |
| **Clear event key** | `gw_status_clear` (fires when the gateway returns to `Connected` / `Online`) |
| **Correlated alarms** | `switch_down`, `gw_bgp_neighbor_down`, `gw_vpn_path_down`, `vpn_peer_down`, `bad_wan_uplink`, `intermittent_wan_connectivity`, `sw_alarm_chassis_mgmt_link_down`, `sw_critical_port_down` |
| **Prerequisites** | None — fires automatically on any gateway operational-state transition away from `Connected` / `Online`. |
| **Description** | The branch SSR130's operational status has changed to `Offline`, `Unreachable`, `Disconnected`, or `Degraded`. Because there is only a single SSR130 at the branch and no local HA peer, any state other than `Connected` / `Online` means the branch has either lost management visibility, lost WAN, or both. Treat this alarm as a **branch outage** until proven otherwise. |

### Severity note (no override)

Mist ships `gw_status` as `critical` natively — with a single-gateway branch, any gateway-state transition away from `Connected` is site-impacting by construction. No override is applied.

### State-code interpretation

Not every `GW_STATUS` alarm means the same thing. Read the payload state code first, because it shapes the entire triage path:

| State | Meaning | Likely scope |
|---|---|---|
| `Disconnected` | SSR130 stopped talking to the Mist cloud, but may still be forwarding data plane. | Management plane only — check whether users are still online before treating as an outage. |
| `Unreachable` | Mist cloud cannot reach the SSR130 over any path. | Usually WAN or gateway-fatal — branch is likely dark. |
| `Offline` | SSR130 is confirmed down (no heartbeat, member of the site is not responding). | Full branch outage. |
| `Degraded` | Gateway is up but a component (interface, service, resource) is impaired. | Partial — traffic may continue but capacity or redundancy is reduced. |

Confirm which state fired before mobilizing hub-side on-call — a `Degraded` gateway is not the same page as an `Offline` one.

## Impact

- **Full branch outage (Offline / Unreachable):** the SSR130 is the only WAN gateway at the branch — when it is gone, the store is dark. All SD-WAN services stop, both SVR overlays to the DC hubs (Dallas + Chicago) fail, and every DC-hosted or Internet-hosted app becomes unreachable.
- **Management-plane loss (Disconnected):** Mist cloud can no longer reach the SSR130, so we lose remote monitoring, config push, and Marvis analytics on this device. Data plane may or may not still be forwarding — verify from the branch side (POS pings, IP-phone health, downstream AP status) before declaring an outage.
- **Degraded:** capacity or redundancy is reduced but traffic continues. Common triggers include a single WAN uplink down (dual-ISP branch reconverging onto the survivor), high CPU/memory, or a fabric component fault.
- Loss of routing / BGP — the SSR130 is the branch's overlay speaker; when it goes, all learned DC-hub routes withdraw.
- Loss of both SVR peer paths (Dallas + Chicago) — no overlay to either hub.
- No remote remediation possible — with the gateway down, in-band access is gone; unless the branch has independent OOB (rare in this environment), any fix requires an on-site touch or ISP-side action.
- Because there is only a single SSR130 at the branch, there is no gateway-side redundancy to fall back on. This alarm is branch-scope by construction.

## Required Information

| Category | Data to capture |
|---|---|
| Device | Site, Hostname, Serial Number, SSR software version, Mist device ID |
| State | Which of `Offline` / `Unreachable` / `Disconnected` / `Degraded` fired; time of transition (UTC); last known `Connected` time |
| Reachability | Can Mist reach the SSR130 at all? Can any downstream device (EX4100 VC, an AP) reach it? Are POS / phones still online? |
| WAN underlay | State of both ISP links at the branch (up / down / degraded); any co-firing `bad_wan_uplink` or `intermittent_wan_connectivity` alarms |
| Overlay | State of BGP peers to Dallas and Chicago hubs; state of SVR peer paths (from Mist history — the SSR130 is unreachable now) |
| Resource pressure | If `Degraded` — CPU, memory, session count, temperature (from most recent Mist telemetry) |
| Timeline | Alert timestamp (UTC), last successful config push, last firmware upgrade, recent audit-log entries, scheduled ISP maintenance |
| Correlated Alarms | Any active alarms on the SSR130, the EX4100 VC, either ISP underlay, or the DC-hub SSR1300 pair in the last 15 min |

See Shared Appendix §5 for the always-required ticket fields.

## Validation

The SSR130 may be unreachable from the NOC when this alarm fires — validate first from the Mist cloud side, then attempt PCLI only if reachability is restored.

### From Mist cloud (always available)

| Check | Command / Action |
|---|---|
| Confirm current state | Mist UI → WAN Edges → *SSR130* → Health / Insights (state, last-seen, reason for state change) |
| Alarms on the device | Monitor → Alerts (Alarms) → filter by device |
| Events leading up to the state change | Monitor → Events → filter by device, time range = last 1 h |
| WAN link history (both ISPs) | WAN Assurance → WAN Links → *SSR130* |
| SVR peer-path history (Dallas, Chicago) | WAN Assurance → Peer Path Insights → filter by device |
| Recent config pushes | Organization → Audit Logs → filter by device |
| Downstream reachability | Switches → *EX4100 VC* → Health (is the VC still reachable? do downstream APs / clients still show up?) |

### From SSR PCLI (only if the gateway is reachable — i.e. `Degraded` or recovered `Disconnected`)

| Check | Command / Action |
|---|---|
| System / model / uptime | `show system` |
| Conductor / cloud connectivity | `show system connected` |
| Alarms | `show alarms` |
| Recent events | `show events` |
| Interfaces (physical) | `show device-interface` |
| Interfaces (logical) | `show network-interface` |
| Routing table | `show route` |
| SVR peer paths | `show peers` |
| BGP session summary | `show bgp summary` |
| Reachability to hub with correct source | `ping <hub-public-ip> source <local-transport-ip>` |

**Never** run a bare `ping <target>` on SSR — it may egress from the wrong interface and produce a false-negative. Always pin the source with `source <local-transport-ip>`. See Shared Appendix §7.

### From the branch (on-site or via alternate access)

If the gateway is `Offline` / `Unreachable` and no OOB path exists, coordinate with a branch contact (store manager, field-tech dispatch):

- Confirm SSR130 power state — is it powered on, are LEDs solid, are the ISP-facing ports showing link?
- Confirm ISP modem / handoff state — did the ISP demarc go down (a cable cut or ISP-side outage will look identical to a gateway fault from Mist's perspective)?
- Physical console access if a field tech is on site.

## Resolution

Sequence the response by the reported state — `Offline` and `Unreachable` need on-site / ISP-side action; `Disconnected` may be management-plane only; `Degraded` is usually a specific correlated fault.

| Area | Action |
|---|---|
| Read the state code | Before mobilizing anyone, confirm which of `Offline` / `Unreachable` / `Disconnected` / `Degraded` fired. This determines whether the branch is dark or merely impaired. |
| Correlated underlay | If `bad_wan_uplink` or `intermittent_wan_connectivity` is co-firing on **both** ISPs, the gateway is likely up but has no transport — treat as ISP outage, not gateway fault. Coordinate with both ISPs. If only one ISP is down, the branch should still be reachable — investigate SSR130 further. |
| Correlated LAN | If `switch_down` is co-firing on the EX4100 VC serving the SSR130's LAN side, the SSR130 may be up but its LAN reach (and therefore Mist visibility) is broken. Fix the VC first. |
| Correlated management | If `sw_alarm_chassis_mgmt_link_down` is co-firing and the branch is management-in-band (typical), management is riding a broken path — fix the VC / uplink first; the gateway itself may be fine. |
| Power / physical | For `Offline` with no correlated network alarms — coordinate with branch to verify the SSR130 has power and is not showing hardware faults on the front panel. |
| ISP handoff | For `Unreachable` on a dual-ISP branch where both underlays are marked down — open tickets with both ISPs simultaneously (single-ISP outages should not knock the gateway `Unreachable`, so a dual-ISP hit is either coincidence or a shared upstream fault). |
| Resource pressure (`Degraded`) | Check CPU, memory, session count on the SSR130 — sustained resource exhaustion (rare on SSR130 at branch scale but possible during a scanning event or a DDoS reflection) can flip the state to `Degraded`. Investigate top talkers / sessions. |
| Hardware (`Degraded` or `Offline`) | If `show alarms` or the front panel indicates PSU / fan / thermal fault, plan an RMA. |
| Configuration drift | Review Mist audit logs for pushes in the last 24 h. If a recent push caused the outage, prepare a rollback via Mist (this only works if the gateway is reachable enough to receive it — otherwise a field-tech console session is required). |
| Firmware | If the state change coincides with a firmware upgrade, be prepared to roll back. Upgrades gone bad on the only branch gateway are a Tier 2 / vendor escalation. |
| Recovery | Confirm the SSR130 state returns to `Connected` in Mist, both ISP underlays are up, both SVR peer paths (Dallas + Chicago) are `up`, both BGP sessions are `Established`, and the paired clear event has fired. |

## Closure Criteria

- SSR130 state in Mist is `Connected` (not `Degraded`, `Disconnected`, `Unreachable`, or `Offline`).
- Both WAN underlay links (ISP-A and ISP-B) are up and within performance baseline.
- Both SVR peer paths to the DC hubs (Dallas + Chicago) are `up`.
- Both BGP overlay sessions to the DC hubs are `Established`.
- Downstream store services are functional (POS, IP phones, APs online, back-office reachable).
- **The paired clear event `gw_status_clear` has been received.**
- No recurrence of `gw_status` for this device within a 30-minute debounce window.
- All co-fired alarms on the SSR130, EX4100 VC, and either ISP underlay have cleared on their own tickets (do not implicitly close them from this ticket).
- Root cause is documented on the ticket, including which state code(s) the gateway transitioned through during the incident, whether the branch was fully dark or merely degraded, and (if applicable) which correlated alarm was the true root cause.

## Mist GUI Navigation

| Task | Navigation |
|---|---|
| Verify alert | Monitor → Alerts (Alarms) → filter by `gw_status` |
| Gateway health / state | WAN Edges → *SSR130* → Health / Insights |
| WAN link history | WAN Assurance → WAN Links |
| SVR peer-path history | WAN Assurance → Peer Path Insights |
| Gateway events (raw) | Monitor → Events → filter by device |
| Downstream switch view | Switches → *EX4100 VC* → Health |
| Audit logs | Organization → Audit Logs |

**Legacy path note:** older docs may say `Routers → SSR1300`. Current Mist UI unifies all gateways under `WAN Edges → …`.

## SSR PCLI Commands (quick reference)

SSR uses PCLI, not Junos. Do not paste Junos syntax into an SSR. These commands assume the gateway is reachable — during an `Offline` / `Unreachable` state they will not run.

| Purpose | Command |
|---|---|
| System / model / uptime | `show system` |
| Conductor / cloud connectivity | `show system connected` |
| Alarms | `show alarms` |
| Events (scoped) | `show events` |
| Device interfaces (physical) | `show device-interface` |
| Network interfaces (logical) | `show network-interface` |
| Routing table | `show route` |
| SVR peer paths | `show peers` |
| BGP summary | `show bgp summary` |
| BGP peer detail | `show bgp neighbor <peer-ip>` |
| Active sessions on device | `show sessions summary` |
| Reachability with correct source | `ping <target> source <local-transport-ip>` |
| Path to remote target | `traceroute <target>` |

See Shared Appendix §7 for the full SSR PCLI reference.

## Cross-references (sibling alarms)

`GW_STATUS` is a high-level roll-up alarm — it is often the *symptom* whose root cause is one of the sibling alarms below. When any of these are co-firing, resolve the co-fired alarm first:

- `bad_wan_uplink` — underlying transport failure (Marvis). If both ISPs are hit, the gateway will flip to `Unreachable` even though the box itself is fine.
- `intermittent_wan_connectivity` — flaky underlay. Common cause of `Degraded` / oscillating status.
- `gw_bgp_neighbor_down` — overlay control plane down; typically follows gateway-state changes but can also be the leading indicator during a soft-fail (e.g. BGP process crash).
- `gw_vpn_path_down` / `vpn_peer_down` — SVR overlay down; same relationship as BGP above.
- `switch_down` — EX4100 VC serving the SSR130's LAN side is offline; the gateway may be up but unreachable from Mist because its management path rides the VC.
- `sw_alarm_chassis_mgmt_link_down` — VC management link down; if branch is management-in-band (typical), Mist visibility to the gateway drops even though data plane may be fine.
- `sw_critical_port_down` — the physical port on the EX4100 serving the SSR130's uplink or management is down.

**Triage rule:** `gw_status` alone with no correlated alarms almost always means a gateway-local fault (power, hardware, firmware). `gw_status` co-firing with LAN or WAN sibling alarms means the gateway is a **symptom** — go find the root cause first.

## Escalation

Per Shared Appendix §8. Because a single SSR130 gateway state change can mean a full branch outage, escalate quickly:

- **Tier 1 NOC** can self-clear cases where a correlated ISP-underlay or LAN alarm is clearly root cause and the sibling runbook resolves the issue (the gateway state will recover on its own).
- **Escalate to Tier 2 immediately** for:
  - `Offline` or `Unreachable` state with no correlated ISP alarm (implies gateway-local fault: hardware, firmware, or power).
  - Suspected firmware / config rollback on the sole branch gateway (any change on the only WAN device at the branch is out-of-window by definition).
  - Hardware replacement (RMA of the SSR130).
  - `Degraded` state with sustained resource pressure (CPU / memory / sessions) — may need capacity or profile changes.
- **Page hub-side on-call in parallel** if the branch is confirmed fully dark and DC-hosted apps for that branch's users are impacted — hub-side may need to withdraw the branch's routes / advertise a coverage tunnel.
- **Change Advisory Board** for any planned config or firmware change on the recovered gateway, since it is the branch's single point of failure.

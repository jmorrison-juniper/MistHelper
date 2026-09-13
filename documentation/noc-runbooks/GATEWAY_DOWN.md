# GATEWAY_DOWN

## 1. Overview

| Field | Value |
|---|---|
| **Alert Name** | GATEWAY_DOWN |
| **Mist alarm key** | `gateway_down` (fires when Mist stops receiving heartbeat / telemetry from the gateway — the box is unreachable from the cloud) |
| **Platform** | Juniper SSR130 (single gateway at a retail branch — no local HA peer). The same alarm key also fires on SRX gateways — an SRX-specific runbook is planned as Phase 2 because the CLI (Junos) differs from SSR PCLI. |
| **Mist native severity** | `warn` (verified against `GET /api/v1/const/alarm_defs`) |
| **NOC severity** | **Critical** (override — see rationale below) |
| **Group** | `infrastructure` |
| **Clear event key** | No distinct clear-event key is enumerated in the Mist OpenAPI catalog for `gateway_down`. The alarm auto-clears when Mist starts receiving heartbeat / telemetry from the gateway again; treat the disappearance of the alarm on the device — and the gateway showing `Connected` in `WAN Edges → *SSR130* → Health` — as the machine-verifiable close signal. Verify current auto-clear behavior against `GET /api/v1/const/alarm_defs` at runtime; the alarm-definition catalog is dynamic and may add an explicit clear key in future firmware/cloud releases. |
| **Correlated alarms** | `switch_down`, `gw_bgp_neighbor_down`, `gw_vpn_path_down`, `vpn_peer_down`, `bad_wan_uplink`, `intermittent_wan_connectivity`, `sw_alarm_chassis_mgmt_link_down`, `sw_critical_port_down` |
| **Prerequisites** | None — fires automatically when Mist declares the gateway unreachable. |
| **Description** | Mist has stopped receiving heartbeat / telemetry from the branch SSR130. From the cloud's perspective the gateway is down. Because there is only a single SSR130 at the branch and no local HA peer, this alarm means the branch has either lost management visibility, lost WAN, or both. Treat this alarm as a **branch outage** until proven otherwise. |

### Severity rationale (Mist `warn` → NOC `critical`)

Mist ships `gateway_down` as `warn` natively, because many customers run gateways in redundant pairs where losing one node is a degraded state rather than an outage. This environment does not. The branch runs a single SSR130 with no local HA peer, so gateway loss is site-impacting by construction. We page it as **critical**.

The override lives in the downstream paging and ticketing layer, keyed off the alarm payload `type` value `gateway_down`. It does not live in Mist. See Shared Appendix §2.

### What this alarm does *not* tell you

`gateway_down` is a single-state alarm: Mist has lost the gateway. It does not distinguish between:

- The **box** being down (power / hardware / firmware fault) — data plane is definitely off.
- The **management path** being down (LAN uplink broken, `me0`/`vme` failed, in-band mgmt path riding a broken transport) — data plane may still be forwarding.
- Both **WAN underlays** being down (branch is dark, box is fine).

The triage sequence below (§4 / §5) is designed to distinguish these cases quickly using the correlated-alarm set, because the alarm payload itself will not.

## 2. Impact

Because the branch runs a single SSR130 with no local HA peer, gateway loss is branch-scope by construction. The specific impact depends on which failure mode drove the alarm:

- **Box-down / hardware / firmware fault:** full branch outage. Data plane is off — no WAN, both SVR overlays (Dallas + Chicago) dead, all BGP sessions withdrawn, POS / IP-phone / AP / back-office all offline. No remote remediation is possible; recovery requires on-site touch, ISP-side action, or firmware rollback if Mist can still push config.
- **Both WAN underlays down (box is fine):** functionally identical impact to a box-down event — branch is dark — but recovery is different (coordinate with ISPs, gateway itself needs no action).
- **Management-path loss (box is fine, data plane is forwarding):** Mist can no longer reach the SSR130. We lose remote monitoring, config push, and Marvis analytics on this device. **Users at the branch may still be working normally** — verify from the branch side (POS pings, IP-phone health, downstream AP status) before declaring an outage.
- **Loss of routing / overlay:** during any full-outage variant, the SSR130 is the branch's overlay speaker. When it is gone, all learned DC-hub routes withdraw and both SVR peers (Dallas + Chicago) fail; any branch-to-DC traffic depending on those routes stops.

## 3. Required Information

| Category | Data to capture |
|---|---|
| Device | Site, Hostname, Serial Number, SSR software version, Mist device ID |
| Timing | Time of transition (UTC), last known heartbeat, last successful Mist push |
| Reachability | Can Mist reach the SSR130 at all now? Can any downstream device (EX4100 VC, an AP, a POS terminal) reach it? Are POS / phones still online at the branch? |
| WAN underlay | State of both ISP links at the branch (up / down / degraded); any co-firing `bad_wan_uplink` or `intermittent_wan_connectivity` alarms |
| Overlay | State of BGP peers to Dallas and Chicago hubs; state of SVR peer paths (from Mist history — the SSR130 is unreachable now, so telemetry is stale) |
| LAN dependencies | Is `switch_down` or `sw_alarm_chassis_mgmt_link_down` co-firing? Management is typically in-band at these branches — a VC / mgmt-link failure will surface as `gateway_down` even though the SSR itself is healthy |
| Timeline | Alert timestamp (UTC), last known-good time, last firmware upgrade, recent audit-log entries, scheduled ISP maintenance |
| Correlated Alarms | Any active alarms on the SSR130, the EX4100 VC, either ISP underlay, or the DC-hub SSR1300 pair in the last 15 min |

See Shared Appendix §5 for the always-required ticket fields.

## 4. Validation

The SSR130 is unreachable from the NOC when this alarm fires. Validate from the Mist cloud side first; attempt PCLI only if reachability is restored (partial-outage cases where the gateway returns before the ticket closes).

### From Mist cloud (always available)

| Check | Command / Action |
|---|---|
| Confirm current state | Mist UI → WAN Edges → *SSR130* → Health / Insights (state, last-seen, last recorded reason for loss) |
| Alarms on the device | Monitor → Alerts → filter by device |
| Events leading up to the state change | Monitor → Events → filter by device, time range = last 1 h |
| WAN link history (both ISPs) | WAN Assurance → WAN Links → *SSR130* |
| SVR peer-path history (Dallas, Chicago) | WAN Assurance → Peer Path Insights → filter by device |
| Recent config pushes | Organization → Audit Logs → filter by device |
| Downstream reachability | Switches → *EX4100 VC* → Health (is the VC still reachable? do downstream APs / clients still show up?) |

### From SSR PCLI (only if the gateway is reachable — i.e. recovered mid-ticket, or partial-outage)

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

If the gateway is unreachable and no OOB path exists, coordinate with a branch contact (store manager, field-tech dispatch):

- Confirm SSR130 power state — is it powered on, are LEDs solid, are the ISP-facing ports showing link?
- Confirm ISP modem / handoff state — did the ISP demarc go down (a cable cut or ISP-side outage looks identical to a gateway fault from Mist's perspective)?
- Physical console access if a field tech is on site.

## 5. Resolution

Sequence the response by which correlated alarms are co-firing — the alarm payload itself tells you nothing beyond "gateway is unreachable," so the correlated set is where root cause lives.

| Area | Action |
|---|---|
| Correlated underlay (both ISPs) | If `bad_wan_uplink` or `intermittent_wan_connectivity` is co-firing on **both** ISPs, the gateway is likely up but has no transport — treat as ISP outage, not gateway fault. Coordinate with both ISPs. |
| Correlated underlay (one ISP) | If only one ISP is co-firing an underlay alarm, the branch should still be reachable — a single-ISP outage should not knock the gateway `gateway_down`. Continue investigating the SSR130 itself as primary suspect. |
| Correlated LAN | If `switch_down` is co-firing on the EX4100 VC serving the SSR130's LAN side, the SSR130 may be up but its LAN reach (and therefore Mist visibility) is broken. Fix the VC first — the `gateway_down` alarm should clear on its own. |
| Correlated management | If `sw_alarm_chassis_mgmt_link_down` is co-firing and the branch is management-in-band (typical), management is riding a broken path — fix the VC / uplink first; the gateway itself may be fine. |
| Power / physical | For no-correlated-alarm cases — coordinate with the branch to verify the SSR130 has power and is not showing hardware faults on the front panel. This is the most common no-correlation root cause. |
| ISP handoff | If both underlays are marked down on a dual-ISP branch — open tickets with both ISPs simultaneously. Single-ISP outages should not knock the gateway `gateway_down`, so a dual-ISP hit is either coincidence or a shared upstream fault. |
| Hardware | If `show alarms` (once reachable) or the front panel indicates PSU / fan / thermal fault, plan an RMA. |
| Configuration drift | Review Mist audit logs for pushes in the last 24 h. If a recent push caused the outage, prepare a rollback via Mist (this only works if the gateway is reachable enough to receive it — otherwise a field-tech console session is required). |
| Firmware | If the alarm coincides with a firmware upgrade, be prepared to roll back. Upgrades gone bad on the only branch gateway are a Tier 2 / vendor escalation. |
| Recovery | Confirm the SSR130 shows `Connected` in Mist, both ISP underlays are up, both SVR peer paths (Dallas + Chicago) are `up`, both BGP sessions are `Established`, and the `gateway_down` alarm has cleared. |

## 6. Closure Criteria

- SSR130 is `Connected` in `WAN Edges → *SSR130* → Health`.
- Both WAN underlay links (ISP-A and ISP-B) are up and within performance baseline.
- Both SVR peer paths to the DC hubs (Dallas + Chicago) are `up`.
- Both BGP overlay sessions to the DC hubs are `Established`.
- Downstream store services are functional (POS, IP phones, APs online, back-office reachable).
- **The `gateway_down` alarm on this device has cleared** (auto-cleared on heartbeat resumption — see §1 note about the clear-key catalog).
- No recurrence of `gateway_down` for this device within a 30-minute debounce window.
- All co-fired alarms on the SSR130, EX4100 VC, and either ISP underlay have cleared on their own tickets (do not implicitly close them from this ticket).
- Root cause is documented on the ticket, including which failure mode (box-down / dual-ISP / mgmt-path) applied, and (if applicable) which correlated alarm was the true root cause.

## 7. Mist GUI Navigation

| Task | Navigation |
|---|---|
| Verify alert | Monitor → Alerts → filter by `gateway_down` |
| Gateway health | WAN Edges → *SSR130* → Insights |
| WAN link history | Monitor → Service Levels → WAN |
| SVR peer-path history | Monitor → Service Levels → WAN → Peer Paths |
| Gateway events (raw) | Monitor → Events → filter by device |
| Downstream switch view | Switches → *EX4100 VC* → Insights |
| Audit logs | Organization → Audit Logs |

**Legacy path note:** older docs may say `Routers → SSR1300`. Current Mist UI unifies all gateways under `WAN Edges → …`.

## 8. SSR PCLI Commands (quick reference)

SSR uses PCLI, not Junos. Do not paste Junos syntax into an SSR. These commands assume the gateway is reachable — while `gateway_down` is active they will not run.

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

## 9. Cross-references (sibling alarms)

`gateway_down` is a high-level roll-up alarm — it is often the *symptom* whose root cause is one of the sibling alarms below. When any of these are co-firing, resolve the co-fired alarm first:

- `bad_wan_uplink` — underlying transport failure (Marvis). If both ISPs are hit, the gateway will go `gateway_down` from Mist's perspective even though the box itself is fine.
- `intermittent_wan_connectivity` — flaky underlay. Common cause of gateway-down alarms that clear on their own before anyone can log in.
- `gw_bgp_neighbor_down` — overlay control plane down; typically follows a `gateway_down` event but can also be the leading indicator during a soft-fail (e.g. BGP process crash before Mist declares the whole gateway down).
- `gw_vpn_path_down` / `vpn_peer_down` — SVR overlay down; same relationship as BGP above.
- `switch_down` — EX4100 VC serving the SSR130's LAN side is offline; the gateway may be up but unreachable from Mist because its management path rides the VC.
- `sw_alarm_chassis_mgmt_link_down` — VC management link down; if branch is management-in-band (typical), Mist visibility to the gateway drops even though data plane may be fine.
- `sw_critical_port_down` — the physical port on the EX4100 serving the SSR130's uplink or management is down.

**Triage rule:** `gateway_down` alone with no correlated alarms almost always means a gateway-local fault (power, hardware, firmware). `gateway_down` co-firing with LAN or WAN sibling alarms means the gateway is a **symptom** — go find the root cause first.

## 10. Escalation

Per Shared Appendix §8. Because a single SSR130 gateway going down can mean a full branch outage, escalate quickly:

- **Tier 1 NOC** can self-clear cases where a correlated ISP-underlay or LAN alarm is clearly root cause and the sibling runbook resolves the issue (the `gateway_down` alarm will recover on its own).
- **Escalate to Tier 2 immediately** for:
  - `gateway_down` with no correlated ISP or LAN alarm (implies gateway-local fault: hardware, firmware, or power).
  - Suspected firmware / config rollback on the sole branch gateway (any change on the only WAN device at the branch is out-of-window by definition).
  - Hardware replacement (RMA of the SSR130).
- **Page hub-side on-call in parallel** if the branch is confirmed fully dark and DC-hosted apps for that branch's users are impacted — hub-side may need to withdraw the branch's routes / advertise a coverage tunnel.
- **Change Advisory Board** for any planned config or firmware change on the recovered gateway, since it is the branch's single point of failure.

# GW_BGP_NEIGHBOR_DOWN

## Overview

| Field | Value |
|---|---|
| **Alert Name** | GW_BGP_NEIGHBOR_DOWN |
| **Mist alarm key** | `gw_bgp_neighbor_down` |
| **Platform** | Juniper SSR130 (single gateway at a retail branch — no local HA peer). The BGP peers this branch cares about are the DC hub SSR1300 pair (Dallas + Chicago). The same alarm key also fires on SRX gateways — an SRX-specific runbook is planned as Phase 2 because the CLI (Junos) differs from SSR PCLI. |
| **Mist native severity** | `warn` |
| **NOC severity** | **Critical** (override — see rationale below) |
| **Group** | `infrastructure` |
| **Clear event key** | `gw_bgp_neighbor_up` |
| **Correlated alarms** | `bad_wan_uplink`, `intermittent_wan_connectivity`, `vpn_peer_down`, `gw_vpn_path_down`, `vpn_path_down`, `gw_critical_port_down`, `switch_down` |
| **Prerequisites** | A BGP peer must be configured on the SSR130. In this environment BGP is the **overlay** to the DC hub SSR1300 pair (not typically to the ISP — underlay to ISPs is normally static). Alarm fires on BGP session state transition to `Idle` / `Active` / `Connect` (i.e. not `Established`). |
| **Description** | A configured BGP neighbor on the SSR130 has left the `Established` state. At a retail branch this is almost always an overlay peer to one of the DC hub SSR1300s (Dallas or Chicago). Losing one hub peer degrades redundancy; losing **both** hub peers isolates the branch's overlay routing entirely. |

### Severity rationale (Mist `warn` → NOC `critical`)

Mist ships `gw_bgp_neighbor_down` as `warn` on the assumption that BGP topologies are redundant. In this environment the branch SSR130 typically peers with **two** DC-hub SSR1300s (Dallas + Chicago), so losing one is degraded-but-serving. However:

- **Single branch SSR130** — there is no local HA peer. Any BGP problem on the branch gateway is the branch gateway's problem alone.
- **Both hub peers going down** isolates the branch's overlay routing entirely, so a single-peer alarm is a leading indicator we need to see immediately.

The downstream paging/ticketing tier escalates this alarm to **critical** on that basis. The override lives in the webhook consumer / paging tier, not in Mist (Mist alarm templates cannot change severity — see Shared Appendix §2). If a specific peer is truly non-critical (test lab, decommissioning window), suppress it downstream by device role or site tag.

### BGP vs SVR — two independent overlays on SSR

**This runbook is for BGP only.** On SSR gateways, BGP (control plane) and SVR / Session Smart Routing (data plane peer paths) are two independent overlays. SVR peer-path outages fire under different alarm keys and have their own runbook — do not conflate them.

| Concern | BGP (this alarm) | SVR / peer paths (separate alarms) |
|---|---|---|
| Alarm keys | `gw_bgp_neighbor_down` (+ `gw_bgp_neighbor_up` clear) | `vpn_peer_down`, `gw_vpn_path_down`, `vpn_path_down` |
| Layer | Control plane — exchanges routes | Data plane — forwards session-oriented traffic between SSRs |
| Transport | TCP/179 to peer IP over an underlay interface | UDP-based Secure Vector Routing between SSRs over one or more transports |
| Independence | BGP can be `Established` while SVR peer paths are down | SVR peer paths can be `up` while BGP is down |
| SSR command | `show bgp summary`, `show bgp neighbor <peer-ip>` | `show peers` |
| Mist GUI | BGP state is not surfaced in a dedicated view — use PCLI | WAN Assurance → Peer Path Insights |

The two often correlate: a shared WAN transport can bring both down at once. Validate each separately with its own commands.

## Impact

**Direct (BGP):**

- Loss of routes learned from or advertised to the affected DC-hub peer.
- **One hub peer down (Dallas or Chicago):** overlay routing continues via the surviving hub; branch stays up but is one failure away from full overlay isolation.
- **Both hub peers down:** the branch loses overlay reachability entirely; DC-hosted apps become unreachable even if the underlay ISP link is up.
- Applications relying on routes advertised by the peer(s) may become unreachable.
- Because there is only a single SSR130 at the branch, there is no gateway-side redundancy to fall back on — any BGP problem here is branch-scope.

**Correlated (SVR):**

- If BGP and SVR share the affected WAN transport, SVR peer paths to the same DC hub may also reconverge or fail — this will surface as a **separate** `vpn_peer_down` / `gw_vpn_path_down` / `vpn_path_down` alarm. Validate SVR independently rather than assuming it followed BGP's state.

## Required Information

### BGP peer (always capture)

| Category | Data to capture |
|---|---|
| Device | Site, Hostname, Serial Number, SSR software version, Mist device ID |
| Peer classification | Which DC hub: `hub-Dallas-SSR1300` / `hub-Chicago-SSR1300`. (In this environment, underlay-ISP BGP is uncommon — verify with your SOR if you see a non-hub peer.) |
| Hub redundancy state | Is the *other* hub peer (Dallas if this is Chicago, or vice versa) currently `Established`? This tells you whether the branch is degraded-but-serving or overlay-isolated. |
| BGP peer | Peer IP, Peer AS, Local AS, Address family (inet / inet-vpn / evpn), Import/Export policies |
| Local transport | Local interface, local transport IP, WAN link (SVR transport name) used to reach the peer |
| Session state | Last state (`Idle`, `Active`, `Connect`, `OpenSent`, `OpenConfirm`) and last error / notification code |
| Timeline | Alert timestamp (UTC), last known Established time, recent config changes |
| Correlated Alarms | Any active alarms on the SSR130, on the branch EX4100 VC, on the upstream ISP link, or on the peer DC-hub SSR1300 in the last 15 min |

### SVR peer path (only if an SVR alarm is co-firing)

| Category | Data to capture |
|---|---|
| Local SSR | Router name, node name |
| Remote SSR | Peer router name, peer node name |
| Transport | Which named WAN transport(s) the peer path uses (name from `show peers`) |
| Path state | Per-transport `up` / `down` / `standby` status |
| Timeline | Last state change per transport |

See Shared Appendix §5 for the always-required ticket fields.

## Validation

### BGP session checks (this alarm)

| Check | Command / Action |
|---|---|
| SSR reachable in Mist | Mist UI → WAN Edges → *device* → Health / Insights |
| SSR connected to conductor / cloud | `show system connected` |
| System status | `show system` |
| BGP session summary | `show bgp summary` |
| Specific peer detail | `show bgp neighbor <peer-ip>` |
| Received routes from peer | `show bgp neighbor <peer-ip> received-routes` |
| Advertised routes to peer | `show bgp neighbor <peer-ip> advertised-routes` |
| Routing table (does peer's prefix appear?) | `show route` |
| Physical / logical interface state | `show device-interface` and `show network-interface` |
| Reachability to peer using correct source | `ping <peer-ip> source <local-transport-ip>` |
| Path to peer | `traceroute <peer-ip>` |
| Alarms on device | `show alarms` |
| BGP-scoped event log | `show events filter type bgp` |

**Never** run a bare `ping <peer-ip>` on SSR — it may egress from the wrong interface and produce a false-negative. Always pin the source with `source <local-transport-ip>`. See Shared Appendix §7.

### SVR peer-path checks (only if correlated SVR alarm is active, or the shared transport is suspect)

| Check | Command / Action |
|---|---|
| Peer path status per transport | `show peers` |
| Peer path in Mist | WAN Assurance → Peer Path Insights → filter by device |

If SVR peer paths are healthy while BGP is down, transport is not the root cause — investigate BGP-specific causes (policy, MD5, peer-side process). If SVR paths are also down on the same transport, treat the shared transport as the primary suspect and prioritize the underlay-link alarms (`bad_wan_uplink`, `intermittent_wan_connectivity`).

## Resolution

| Area | Action |
|---|---|
| Underlay link | If a WAN link alarm (`bad_wan_uplink`, `intermittent_wan_connectivity`) is co-firing, resolve that first — BGP will re-establish once transport recovers. |
| Peer device | Verify the DC-hub SSR1300's BGP process is up (check the hub-side runbook / Mist WAN Edges view for that hub). If the hub-side gateway is impaired, coordinate with the hub-side on-call rather than driving from the branch. |
| Reachability | From SSR, confirm the peer is reachable **from the correct source IP** with `ping <peer-ip> source <local-transport-ip>`. |
| MTU / TCP MSS | If the session repeatedly reaches `OpenSent` then fails, suspect PMTUD blackhole. Verify path MTU and MSS clamping on the transport. |
| Timers / graceful restart | If flap coincides with peer maintenance, confirm hold-time, keepalive, and graceful-restart settings match on both ends. |
| Authentication | If the neighbor uses MD5, verify the shared secret is identical on both peers; a recent rotation on either side will drop the session. |
| Policy / prefix-limit | Verify import/export policies were not recently changed. If a max-prefix limit tripped, review announced route counts before clearing. |
| Firewall / policy | On SSR the peer path traverses a tenant / service-route / security policy — verify these were not recently changed. On an SRX gateway, verify a stateful firewall rule permits TCP/179 in both directions. |
| Configuration | Review Mist audit logs for BGP or interface config changes in the last 24 h. Rollback if a recent change caused the outage. |
| Clear session (last resort) | Only after other causes are ruled out and with change approval, bounce the neighbor to force renegotiation. |
| Recovery (BGP) | Confirm BGP peer transitions back to `Established`, expected prefixes are relearned, and the paired clear event has fired. |
| Recovery (SVR, if it was also affected) | Confirm `show peers` shows the affected peer path back to `up` on the expected transport(s). Do not close the BGP ticket until any SVR peer-path alarm has also cleared. |

## Closure Criteria

**BGP (required for this alarm):**

- BGP neighbor state is `Established`.
- Expected prefix counts (received / advertised) match the pre-incident baseline.
- Reachability to the peer's transport IP from the correct source succeeds.
- **The paired clear event `gw_bgp_neighbor_up` has been received.**
- No recurrence of `gw_bgp_neighbor_down` for this peer within a 30-minute debounce window.
- The *other* DC-hub peer (whichever of Dallas / Chicago was not the impaired one) is also confirmed `Established` — the branch is back to full 2-hub overlay redundancy, not just single-hub-serving.
- Root cause is documented on the ticket, including which hub peer was affected (Dallas vs Chicago) and whether the branch was ever in the "both hubs down" isolation state during the incident.

**SVR (only if SVR alarms co-fired):**

- `show peers` reports the affected peer path back to `up` on the expected transport(s).
- The paired SVR clear event(s) have been received on the correlated ticket(s).
- Close the SVR ticket per its own runbook — do not implicitly close it from this ticket.

## Mist GUI Navigation

**BGP-related:**

| Task | Navigation |
|---|---|
| Verify alert | Monitor → Alerts (Alarms) → filter by `gw_bgp_neighbor_down` |
| SSR health | WAN Edges → *SSR1300* → Health / Insights |
| WAN link health (shared underlay) | WAN Assurance → WAN Links |
| Gateway events | Monitor → Events |
| Audit logs | Organization → Audit Logs |

**SVR-related (use only when correlating with an SVR alarm):**

| Task | Navigation |
|---|---|
| SVR peer paths | WAN Assurance → Peer Path Insights |

**Legacy path note:** older docs may say `Routers → SSR1300`. Current Mist UI unifies all gateways under `WAN Edges → …`.

## SSR PCLI Commands (quick reference)

SSR uses PCLI, not Junos. Do not paste Junos syntax into an SSR.

**System / interface:**

| Purpose | Command |
|---|---|
| System / model / uptime | `show system` |
| Conductor / cloud connectivity | `show system connected` |
| Alarms | `show alarms` |
| Device interfaces (physical) | `show device-interface` |
| Network interfaces (logical) | `show network-interface` |
| Routing table | `show route` |
| Reachability with correct source | `ping <peer-ip> source <local-transport-ip>` |
| Path to peer | `traceroute <peer-ip>` |

**BGP (this alarm):**

| Purpose | Command |
|---|---|
| BGP summary | `show bgp summary` |
| BGP peer detail | `show bgp neighbor <peer-ip>` |
| BGP received routes | `show bgp neighbor <peer-ip> received-routes` |
| BGP advertised routes | `show bgp neighbor <peer-ip> advertised-routes` |
| BGP event log | `show events filter type bgp` |

**SVR (only for correlated peer-path checks — SVR outages are separate alarms):**

| Purpose | Command |
|---|---|
| SVR peer paths (all peers, all transports) | `show peers` |
| Active sessions on device | `show sessions summary` |

See Shared Appendix §7 for the full SSR PCLI reference.

## Cross-references (sibling alarms)

If any of these are co-firing, resolve the co-fired alarm first — it is usually root cause. Because the branch has a single SSR130 (no local HA), *any* gateway-side symptom here is branch-scope; coordinate with the hub-side on-call if the impairment is on the DC hub SSR1300's side of the peering:

- `bad_wan_uplink` — underlying transport failure (Marvis). Common shared root cause with SVR peer-path alarms.
- `intermittent_wan_connectivity` — flaky underlay. Expect BGP to flap in step with the underlay.
- `vpn_peer_down` / `gw_vpn_path_down` / `vpn_path_down` — SVR peer-path issues (distinct from BGP; follow the SVR runbook, not this one). Same DC-hub SSR1300 endpoints, different overlay layer.
- `gw_critical_port_down` — physical port on the SSR130 serving the peer transport is down. Fix the port before chasing BGP.
- `switch_down` — upstream EX4100 VC (or a member) is down; if the SSR130's LAN-side transport rides that VC, BGP can go with it.

## Escalation

Per Shared Appendix §8. Tier 1 NOC can self-clear underlay-transport, reachability, and rollback-driven root causes on the branch SSR130. Escalate to Tier 2 for:

- Routing policy / prefix-limit changes on either the branch SSR130 or the DC-hub SSR1300
- MD5 secret rotation (must be coordinated with the hub-side on-call)
- MTU/PMTUD suspected blackholes on the underlay
- Any ISP-side ticket handoff on the underlying transport
- Configuration restore that spans multiple devices
- **Both hub peers (Dallas + Chicago) down simultaneously** — branch overlay is isolated; page hub-side on-call in parallel and treat as a site outage, not a single-peer alarm.

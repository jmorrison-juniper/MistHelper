# GW_BGP_NEIGHBOR_DOWN

## Overview

| Field | Value |
|---|---|
| **Alert Name** | GW_BGP_NEIGHBOR_DOWN |
| **Mist alarm key** | `gw_bgp_neighbor_down` |
| **Platform** | Juniper SSR1300 (Session Smart Router). The same alarm key also fires on SRX gateways — an SRX-specific runbook is planned as Phase 2 because the CLI (Junos) differs from SSR PCLI. |
| **Mist native severity** | `warn` |
| **NOC severity** | **Critical** (override — see rationale below) |
| **Group** | `infrastructure` |
| **Clear event key** | `gw_bgp_neighbor_up` |
| **Correlated alarms** | `bad_wan_uplink`, `intermittent_wan_connectivity`, `vpn_peer_down`, `gw_vpn_path_down`, `vpn_path_down`, `gw_critical_port_down`, `switch_down` |
| **Prerequisites** | A BGP peer must be configured on the gateway. Alarm fires on BGP session state transition to `Idle` / `Active` / `Connect` (i.e. not `Established`). |
| **Description** | A configured BGP neighbor on the gateway has left the `Established` state. Depending on the peer's role (underlay ISP, internal route reflector, overlay CE), impact ranges from partial route loss to complete site isolation. |

### Severity rationale (Mist `warn` → NOC `critical`)

Mist ships `gw_bgp_neighbor_down` as `warn` because a well-designed BGP topology has redundant peers and a single neighbor down does not always mean loss of reachability. In our environment BGP peers are load-bearing (see Peer classification below), so we escalate to **critical**. If a specific peer is truly non-critical (test lab, decommissioning window), retune via a per-site alarm template rather than lowering the runbook default.

### BGP ≠ SVR — do not confuse them

On SSR, **BGP** and **SVR (Session Smart Routing / peer paths)** are two independent overlays. This alarm is for the underlying **BGP** control plane only.

- If SVR peer paths are down, look for `vpn_peer_down` / `gw_vpn_path_down` / `vpn_path_down` — those are separate alarms with a separate runbook.
- BGP can be `Established` while SVR peer paths are down, and vice-versa.
- On SSR, use `show bgp …` for BGP and `show peers` for SVR. Do not mix.

## Impact

- Loss of routes learned from or advertised to the affected peer.
- If underlay ISP peer: potential loss of internet or WAN transport for the site.
- If internal RR peer: loss of overlay route learning from a portion of the fabric.
- If overlay CE peer: reachability to that specific customer edge is lost.
- Session Smart Routing (SVR) tunnels riding the affected transport may reconverge or fail.
- Applications relying on routes advertised by the peer may become unreachable.
- If the BGP peer is the only path, complete site isolation until an alternate path is available.

## Required Information

| Category | Data to capture |
|---|---|
| Device | Site, Hostname, Serial Number, SSR software version, Mist device ID |
| Peer classification | `underlay-ISP` / `internal-RR` / `overlay-CE` (see Shared Appendix §5) |
| BGP peer | Peer IP, Peer AS, Local AS, Address family (inet / inet-vpn / evpn), Import/Export policies |
| Local transport | Local interface, local transport IP, WAN link (SVR transport name) used to reach the peer |
| Session state | Last state (`Idle`, `Active`, `Connect`, `OpenSent`, `OpenConfirm`) and last error / notification code |
| Timeline | Alert timestamp (UTC), last known Established time, recent config changes |
| Correlated Alarms | Any active alarms on the gateway, upstream ISP link, or peer device in the last 15 min |

See Shared Appendix §7 for the always-required ticket fields.

## Validation

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
| SVR peer paths (separate from BGP) | `show peers` |
| Active sessions on device | `show sessions summary` |
| Physical / logical interface state | `show device-interface` and `show network-interface` |
| Reachability to peer using correct source | `ping <peer-ip> source <local-transport-ip>` |
| Path to peer | `traceroute <peer-ip>` |
| Alarms on device | `show alarms` |
| BGP-scoped event log | `show events filter type bgp` |

**Never** run a bare `ping <peer-ip>` on SSR — it may egress from the wrong interface and produce a false-negative. Always pin the source with `source <local-transport-ip>`. See Shared Appendix §9.

## Resolution

| Area | Action |
|---|---|
| Underlay link | If a WAN link alarm (`bad_wan_uplink`, `intermittent_wan_connectivity`) is co-firing, resolve that first — BGP will re-establish once transport recovers. |
| Peer device | Verify peer's BGP process is up; on ISP peer, open a ticket with the ISP referencing the peer IP and last-seen timestamp. |
| Reachability | From SSR, confirm the peer is reachable **from the correct source IP** with `ping <peer-ip> source <local-transport-ip>`. |
| MTU / TCP MSS | If the session repeatedly reaches `OpenSent` then fails, suspect PMTUD blackhole. Verify path MTU and MSS clamping on the transport. |
| Timers / graceful restart | If flap coincides with peer maintenance, confirm hold-time, keepalive, and graceful-restart settings match on both ends. |
| Authentication | If the neighbor uses MD5, verify the shared secret is identical on both peers; a recent rotation on either side will drop the session. |
| Policy / prefix-limit | Verify import/export policies were not recently changed. If a max-prefix limit tripped, review announced route counts before clearing. |
| Firewall / policy | On SSR the peer path traverses a tenant / service-route / security policy — verify these were not recently changed. On an SRX gateway, verify a stateful firewall rule permits TCP/179 in both directions. |
| Configuration | Review Mist audit logs for BGP or interface config changes in the last 24 h. Rollback if a recent change caused the outage. |
| Clear session (last resort) | Only after other causes are ruled out and with change approval, bounce the neighbor to force renegotiation. |
| Recovery | Confirm BGP peer transitions back to `Established`, expected prefixes are relearned, and the paired clear event has fired. |

## Closure Criteria

- BGP neighbor state is `Established`.
- Expected prefix counts (received / advertised) match the pre-incident baseline.
- Reachability to the peer's transport IP from the correct source succeeds.
- **The paired clear event `gw_bgp_neighbor_up` has been received.**
- No recurrence of `gw_bgp_neighbor_down` for this peer within a 30-minute debounce window.
- If SVR peer paths were affected, they are also back to `up` (verified with `show peers`).
- Root cause is documented on the ticket, including peer classification and blast radius.

## Mist GUI Navigation

| Task | Navigation |
|---|---|
| Verify alert | Monitor → Alerts (Alarms) → filter by `gw_bgp_neighbor_down` |
| SSR health | WAN Edges → *SSR1300* → Health / Insights |
| WAN link health | WAN Assurance → WAN Links |
| SVR peer paths (separate from BGP) | WAN Assurance → Peer Path Insights |
| Gateway events | Monitor → Events |
| Audit logs | Organization → Audit Logs |

**Legacy path note:** older docs may say `Routers → SSR1300`. Current Mist UI unifies all gateways under `WAN Edges → …`. See Shared Appendix §6.

## SSR PCLI Commands (quick reference)

SSR uses PCLI, not Junos. Do not paste Junos syntax into an SSR.

| Purpose | Command |
|---|---|
| System / model / uptime | `show system` |
| Conductor / cloud connectivity | `show system connected` |
| Alarms | `show alarms` |
| BGP summary | `show bgp summary` |
| BGP peer detail | `show bgp neighbor <peer-ip>` |
| BGP received routes | `show bgp neighbor <peer-ip> received-routes` |
| BGP advertised routes | `show bgp neighbor <peer-ip> advertised-routes` |
| SVR peer paths (overlay) | `show peers` |
| Session count | `show sessions summary` |
| Device interfaces (physical) | `show device-interface` |
| Network interfaces (logical) | `show network-interface` |
| Routing table | `show route` |
| Reachability with correct source | `ping <peer-ip> source <local-transport-ip>` |
| Path to peer | `traceroute <peer-ip>` |
| BGP event log | `show events filter type bgp` |

See Shared Appendix §9 for the full SSR PCLI reference.

## Cross-references (sibling alarms)

If any of these are co-firing, resolve the co-fired alarm first — it is usually root cause:

- `bad_wan_uplink` — underlying transport failure (Marvis)
- `intermittent_wan_connectivity` — flaky underlay
- `vpn_peer_down` / `gw_vpn_path_down` / `vpn_path_down` — SVR peer path issues (distinct from BGP)
- `gw_critical_port_down` — physical port serving the peer transport is down
- `switch_down` — upstream L2/L3 switch is down

## Escalation

Per Shared Appendix §10. Tier 1 NOC can self-clear underlay-transport, reachability, and rollback-driven root causes. Escalate to Tier 2 for:

- Routing policy / prefix-limit changes
- MD5 secret rotation
- MTU/PMTUD suspected blackholes
- Any ISP-side ticket handoff
- Configuration restore that spans multiple devices

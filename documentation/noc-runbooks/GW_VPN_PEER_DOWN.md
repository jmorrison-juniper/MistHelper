# GW_VPN_PEER_DOWN

> **Read this first — the alert name is not the Mist alarm key.** This alert reaches the NOC as `GW_VPN_PEER_DOWN`, but Mist catalogues the alarm as **`vpn_peer_down`**, with no `gw_` prefix. There is no `gw_vpn_peer_down` key in Mist. If you filter Monitor → Alerts on `gw_vpn_peer_down` you get an empty result, which looks identical to "no alarms firing". **Always filter on `vpn_peer_down`.**
>
> This differs from the sibling path-down alarm, which really is `gw_vpn_path_down` with the prefix. The two keys are not named consistently in Mist. Check §1.1 before you filter.

## 1. Overview

| Field | Value |
|---|---|
| **Alert Name** | GW_VPN_PEER_DOWN |
| **Mist alarm key** | **`vpn_peer_down`** — note there is no `gw_` prefix. Verified against `GET /api/v1/const/alarm_defs`. The payload `type` value is also `vpn_peer_down`. |
| **Platform** | Juniper SSR130 (single gateway at a retail branch — no local HA peer). The SVR peers this branch cares about are the overlay peers to the DC-hub SSR1300 pair (Dallas + Chicago). The same alarm key also fires on SRX gateways running SD-WAN — an SRX-specific runbook is planned as Phase 2 because the CLI (Junos) differs from SSR PCLI. |
| **Mist native severity** | `warn` (verified against `GET /api/v1/const/alarm_defs`) |
| **NOC severity** | **Critical** (override — see rationale below) |
| **Group** | `infrastructure` |
| **Clear event key** | **`vpn_peer_up`** (native severity `info`) — again with no `gw_` prefix |
| **Correlated alarms** | `gw_vpn_path_down`, `vpn_path_down`, `bad_wan_uplink`, `intermittent_wan_connectivity`, `gw_bgp_neighbor_down`, `gw_critical_port_down`, `switch_down`, `gateway_down` |
| **Prerequisites** | An SVR peer relationship must be configured between this branch SSR130 and a remote SSR (in this environment, a DC-hub SSR1300). This alarm fires when the aggregate peer state is `down` — every transport path making up that peer is down. |
| **Description** | The SVR (Session Smart Routing) peer relationship between the branch SSR130 and a remote SSR is fully down — every underlying transport path has failed. Overlay traffic to that peer cannot flow. This is a strict escalation of `gw_vpn_path_down`. If only one transport failed and another survived, the peer would remain `up` and only the path-down alarm would fire. |

### 1.1 Key naming — the three SVR alarm keys

Mist does not use one prefix convention across the SVR alarm family. Copy the key from this table rather than guessing from the alert name:

| Alert name on the ticket | Mist alarm key | Native severity | Clear key |
|---|---|---|---|
| GW_VPN_PEER_DOWN (this runbook) | **`vpn_peer_down`** | `warn` | `vpn_peer_up` |
| GW_VPN_PATH_DOWN | `gw_vpn_path_down` | `warn` | `gw_vpn_path_up` |
| VPN_PATH_DOWN (Marvis) | `vpn_path_down` | `critical` | none enumerated |

`vpn_path_down` is a separate Marvis alarm. It is not the clear pair or the plural form of anything above. Do not confuse it with `gw_vpn_path_down`.

### Severity rationale (Mist `warn` → NOC `critical`)

Mist ships `vpn_peer_down` as `warn` natively, because many customers run several redundant peers and losing one is a degraded state rather than an outage. We page it as **critical**. An aggregate peer outage means the overlay to that hub is fully out. On a two-hub branch (Dallas and Chicago), one peer down is still degraded and serving through the surviving hub, but the paired-peer failure mode is one alarm away, and detection latency matters.

The override lives in the downstream paging and ticketing layer, keyed off the payload `type` value `vpn_peer_down`. It does not live in Mist. See Shared Appendix §2.

### Path-down vs peer-down — which am I looking at?

Both alarms cover the SVR overlay but at different granularities. Read the alarm key on the ticket before doing anything else:

| Alarm | Meaning | Serving state |
|---|---|---|
| `gw_vpn_path_down` | One or more (but not all) transports to a peer are down | Peer stays `up`. Traffic reconverges onto the surviving transport. |
| `vpn_peer_down` (this alarm) | **All** transports to a peer are down. The aggregate peer is `down`. | The overlay to that peer is fully out. |

If `vpn_peer_down` fires, expect one or more `gw_vpn_path_down` alarms to be co-firing on the same peer. They are the constituent path failures that added up to the peer outage. Resolve the underlying path failures. The peer comes back on its own once at least one path is restored.

### SVR vs BGP — two independent overlays on SSR

**This runbook is for the SVR peer relationship only.** On SSR gateways, SVR (data plane, per-transport peer paths) and BGP (control plane, TCP/179) are two independent overlays. BGP outages fire under `gw_bgp_neighbor_down` and have their own runbook — do not conflate them. See `GW_VPN_PATH_DOWN.md` for the SVR-vs-BGP comparison table.

## 2. Impact

**Direct (SVR):**

- Loss of the entire SVR overlay to the affected DC-hub peer.
- **One peer down (typical case):** the *other* DC-hub peer (Dallas if this is Chicago, or vice versa) still carries branch overlay traffic — branch is degraded-but-serving with no hub redundancy.
- **Both DC-hub peers down simultaneously:** the branch is overlay-isolated; DC-hosted apps unreachable even if an underlay ISP link is technically `up`. Any branch-to-branch communication that transits a DC hub is also down.
- Loss of dynamic path steering for the affected peer — any application policy or SLA routing that referenced that peer is offline.
- BFD / SVR control-plane adjacency loss for the affected peer.
- Routing convergence events on the SSR130 as it withdraws routes learned across the failed peer.
- Increased latency and jitter during and after failover; voice / video sessions transiting the affected peer will drop and re-establish (or fail if no secondary exists).
- Because there is only a single SSR130 at the branch, there is no gateway-side redundancy to fall back on — any SVR problem here is branch-scope.

**Correlated (BGP):**

- If SVR and BGP share the affected WAN transport(s), the BGP session to the same DC hub will also drop — this will surface as a **separate** `gw_bgp_neighbor_down` alarm. Validate BGP independently rather than assuming it followed SVR's state.

## 3. Required Information

### SVR peer (always capture)

| Category | Data to capture |
|---|---|
| Device | Site, Hostname, Serial Number, SSR software version, Mist device ID |
| Peer classification | Which DC hub: `hub-Dallas-SSR1300` / `hub-Chicago-SSR1300` |
| Hub redundancy state | Is the *other* hub peer (Dallas if this is Chicago, or vice versa) currently `up`? This tells you whether the branch is degraded-but-serving or overlay-isolated. |
| SVR peer | Peer name, remote router / node, tunnel status, downtime duration, last known `up` time |
| Constituent paths | Every transport path making up this peer and its state (all should be `down` when this alarm fires) |
| Transport underlay | Local device-interfaces, local WAN links (ISP-A / ISP-B), local transport IPs, remote public IPs |
| Performance (last known) | Packet loss %, latency (ms), jitter (ms) just before the outage (from Mist Peer Path Insights) |
| Timeline | Alert timestamp (UTC), last known `up` time, recent config changes, upstream ISP maintenance windows |
| Correlated Alarms | Any active alarms on the SSR130, on the branch EX4100 VC, on either ISP underlay, or on the peer DC-hub SSR1300 in the last 15 min |

### BGP (only if a BGP alarm is co-firing)

| Category | Data to capture |
|---|---|
| BGP peer | Peer IP, Peer AS, Local AS, session state |
| Shared transport | Do the BGP session and this SVR peer's paths ride the same underlay WAN link(s)? |

See Shared Appendix §5 for the always-required ticket fields.

## 4. Validation

### SVR peer checks (this alarm)

| Check | Command / Action |
|---|---|
| SSR reachable in Mist | Mist UI → WAN Edges → *device* → Health / Insights |
| SSR connected to conductor / cloud | `show system connected` |
| System status | `show system` |
| SVR peer status (aggregate) | `show peers` |
| SVR peer detail (per-path breakdown) | `show peers detail` |
| WAN transport / underlay interfaces | `show device-interface` and `show network-interface` |
| Routing table (routes learned from peer will be missing) | `show route` |
| Reachability to remote peer using correct source | `ping <remote-public-ip> source <local-transport-ip>` |
| Path to remote peer | `traceroute <remote-public-ip>` |
| Alarms on device | `show alarms` |
| Recent events (scoped) | `show events` |
| Peer path history in Mist | WAN Assurance → Peer Path Insights → filter by device → drill into affected peer |
| WAN link health | WAN Assurance → WAN Links |

**Never** run a bare `ping <remote-public-ip>` on SSR — it may egress from the wrong interface and produce a false-negative. Always pin the source with `source <local-transport-ip>` so you're actually testing the ISP transport that the peer uses. See Shared Appendix §7.

### BGP checks (only if correlated BGP alarm is active, or shared transports are suspect)

| Check | Command / Action |
|---|---|
| BGP session summary | `show bgp summary` |
| Specific peer detail | `show bgp neighbor <peer-ip>` |

If BGP is `Established` on some transport while the SVR peer is fully `down`, one or more underlays are up-enough for TCP/179 but not for SVR — investigate SVR-specific causes (MTU/PMTUD, UDP filtering, tenant / service-route / security policy). If BGP is also fully down, treat the shared underlay as the primary suspect and prioritize the underlay-link alarms.

## 5. Resolution

Because `vpn_peer_down` is the aggregate of all constituent paths failing, resolution is almost always "restore at least one path" — but which path and why depends on the co-fired alarms.

| Area | Action |
|---|---|
| Constituent paths | If any `gw_vpn_path_down` alarms are co-firing (they usually are), resolve them per `GW_VPN_PATH_DOWN.md` — the peer will come back on its own once at least one path is restored. |
| Underlay link | If a WAN link alarm (`bad_wan_uplink`, `intermittent_wan_connectivity`) is co-firing on any ISP, resolve that first. |
| Simultaneous ISP outages | If both ISPs are down, this is not an SVR problem — it is a dual-ISP branch outage. Open ISP tickets in parallel and treat as a site outage; page hub-side on-call. |
| Interface / optics | Check CRC, drops, and optics DDM on all WAN-facing interfaces (`show device-interface`). Replace cable / SFP if physical-layer fault is confirmed. |
| Default route / gateway | Verify default route and next-hop resolution on each transport (`show route`). |
| Firewall / NAT (branch-side) | Verify branch firewall / NAT is not blocking outbound to the peer's public IP(s) on the transport ports SVR uses. |
| Peer device | Verify the DC-hub SSR1300 (peer end) is up and its side of the peering is not the problem (hub-side runbook / Mist WAN Edges view for that hub). If the hub-side gateway is impaired, coordinate with the hub-side on-call rather than driving from the branch. |
| Authentication | Verify SVR peer certificates / secrets / NTP time-sync are not the cause of a peering refusal (Mist audit logs will show if a cert / secret rolled recently). |
| Reachability | From SSR, confirm the remote peer's public IP is reachable **from the correct source IP** with `ping <remote-public-ip> source <local-transport-ip>`. |
| MTU / PMTUD | SVR encapsulates in UDP; a PMTUD blackhole on the underlay will cause the peer to flap or stay down. Verify path MTU on each transport. |
| UDP filtering | If the peer flaps at a fixed interval, suspect stateful UDP filtering by an ISP or upstream firewall. |
| Routing | Verify next-hop resolution for the peer's public IP on each transport. |
| Configuration | Review Mist audit logs for SVR, tenant, service-route, or interface config changes in the last 24 h. Rollback if a recent change caused the outage. |
| Recovery (SVR) | Confirm `show peers` reports the peer back to `up`, at least one constituent path is `up`, and the paired clear event has fired. |
| Recovery (BGP, if it was also affected) | Confirm BGP transitions back to `Established`. Do not close the SVR ticket until any BGP alarm has also cleared. |

## 6. Closure Criteria

**SVR (required for this alarm):**

- `show peers` reports the peer back to `up`.
- At least one constituent transport path is `up`; ideally all expected paths are `up`.
- Packet loss, latency, and jitter on the recovered paths are within acceptable thresholds (per Peer Path Insights baseline).
- Reachability to the remote peer's public IP from the correct source succeeds.
- **The paired clear event `vpn_peer_up` has been received.**
- No recurrence of `vpn_peer_down` for this peer within a 30-minute debounce window.
- The *other* DC-hub peer (whichever of Dallas / Chicago was not the impaired one) is also confirmed `up` — the branch is back to full 2-hub overlay redundancy, not just single-hub-serving.
- Any co-fired `gw_vpn_path_down` alarms have cleared on their own tickets (do not implicitly close them from this ticket).
- Root cause is documented on the ticket, including which hub peer was affected, which underlay transport(s) failed, and whether the branch was ever in the "both hubs down" isolation state during the incident.

**BGP (only if BGP alarms co-fired):**

- BGP neighbor state is `Established` and the paired `gw_bgp_neighbor_up` has been received on its own ticket.
- Close the BGP ticket per its own runbook — do not implicitly close it from this ticket.

## 7. Mist GUI Navigation

| Task | Navigation |
|---|---|
| Verify alert | Monitor → Alerts → filter by `vpn_peer_down` (no `gw_` prefix — see §1.1) |
| Peer path health | Monitor → Service Levels → WAN → Peer Paths |
| WAN link health (underlay) | Monitor → Service Levels → WAN |
| SSR health | WAN Edges → *SSR130* → Insights |
| Gateway events | Monitor → Events |
| Audit logs | Organization → Audit Logs |

**Legacy path note:** older docs may say `Routers → SSR1300`. Current Mist UI unifies all gateways under `WAN Edges → …`.

## 8. SSR PCLI Commands (quick reference)

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
| FIB | `show fib` |
| Reachability with correct source | `ping <remote-public-ip> source <local-transport-ip>` |
| Path to remote peer | `traceroute <remote-public-ip>` |

**SVR (this alarm):**

| Purpose | Command |
|---|---|
| SVR peers (aggregate state) | `show peers` |
| SVR peer detail (per-path breakdown) | `show peers detail` |
| Active sessions on device | `show sessions summary` |
| Events (SVR-scoped) | `show events` |

**BGP (only for correlated control-plane checks — BGP outages are separate alarms):**

| Purpose | Command |
|---|---|
| BGP summary | `show bgp summary` |
| BGP peer detail | `show bgp neighbor <peer-ip>` |

See Shared Appendix §7 for the full SSR PCLI reference.

## 9. Cross-references (sibling alarms)

If any of these are co-firing, resolve the co-fired alarm first — it is usually root cause. Because the branch has a single SSR130 (no local HA), *any* gateway-side symptom here is branch-scope; coordinate with the hub-side on-call if the impairment is on the DC-hub SSR1300's side of the peering:

- `gw_vpn_path_down` — one or more constituent transport paths to this peer are down. Expected to co-fire with `vpn_peer_down` (they are the constituent failures that added up to the peer outage). Resolve per `GW_VPN_PATH_DOWN.md`; the peer will recover once at least one path is restored.
- `vpn_path_down` — related SVR path alarm on peered devices; usually co-fires when a shared underlay drops.
- `bad_wan_uplink` — underlying transport failure (Marvis). Common shared root cause; the SVR peer is a symptom, the ISP link is the cause.
- `intermittent_wan_connectivity` — flaky underlay. Expect the peer to flap in step with the underlay.
- `gw_bgp_neighbor_down` — BGP control-plane session on the same DC-hub peering is down (distinct from SVR; follow the BGP runbook, not this one). Same DC-hub SSR1300 endpoints, different overlay layer.
- `gw_critical_port_down` — physical port on the SSR130 serving a transport is down. Fix the port before chasing SVR.
- `switch_down` — upstream EX4100 VC (or a member) is down; if the SSR130's LAN-side transport rides that VC, SVR paths can go with it.
- `gateway_down` — Mist has lost heartbeat / telemetry from the gateway. If this is co-firing, the SVR peer is a symptom of a gateway-scope fault — chase `gateway_down` root cause first.

## 10. Escalation

Per Shared Appendix §8. Tier 1 NOC can self-clear underlay-transport, reachability, ISP-handoff, cert / NTP, and rollback-driven root causes on the branch SSR130. Escalate to Tier 2 for:

- Tenant / service-route / security policy changes on either the branch SSR130 or the DC-hub SSR1300
- MTU / PMTUD suspected blackholes on the underlay
- SVR configuration changes that span multiple devices
- Suspected UDP filtering by an ISP or transit provider (usually needs vendor-side coordination)
- Peer authentication / certificate / secret issues that cannot be resolved by rollback
- Configuration restore that spans multiple devices
- **Both DC-hub peers (Dallas + Chicago) down simultaneously** — branch overlay is isolated; page hub-side on-call in parallel and treat as a site outage, not a single-peer alarm.

# GW_VPN_PATH_DOWN

## 1. Overview

| Field | Value |
|---|---|
| **Alert Name** | GW_VPN_PATH_DOWN |
| **Mist alarm key** | `gw_vpn_path_down` |
| **Platform** | Juniper SSR130 (single gateway at a retail branch — no local HA peer). The SVR peer paths this branch cares about are the overlays to the DC-hub SSR1300 pair (Dallas + Chicago). The same alarm key also fires on SRX gateways running SD-WAN — an SRX-specific runbook is planned as Phase 2 because the CLI (Junos) differs from SSR PCLI. |
| **Mist native severity** | `warn` (verified against `GET /api/v1/const/alarm_defs`) |
| **NOC severity** | **Critical** (override — see rationale below) |
| **Group** | `infrastructure` |
| **Clear event key** | `gw_vpn_path_up` |
| **Correlated alarms** | `vpn_peer_down`, `vpn_path_down`, `bad_wan_uplink`, `intermittent_wan_connectivity`, `gw_bgp_neighbor_down`, `gw_critical_port_down`, `switch_down` |
| **Prerequisites** | An SVR peer path must be configured between this branch SSR130 and a remote SSR (in this environment, a DC-hub SSR1300). Alarm fires when one or more transport paths that make up the peer relationship go `down` while the overall peer may or may not remain `up`. |
| **Description** | One or more SD-WAN (SVR / Session Smart Routing) transport paths from the branch SSR130 to a remote SSR are unavailable. The overall VPN **peer** may remain `up` (traffic reconverges onto a surviving transport) or may itself go `down` (fires the separate `vpn_peer_down` alarm) — this alarm covers the per-path state, not the aggregate peer state. |

### Severity rationale (Mist `warn` → NOC `critical`)

Mist ships `gw_vpn_path_down` as `warn` natively, because a single-path outage on a multi-transport branch is degraded and still serving. We page it as **critical** anyway. On a dual-ISP branch the alarm is the earliest signal that full peer isolation is one failure away, and the branch has a single SSR130 with no local HA peer to absorb the second failure.

The override lives in the downstream paging and ticketing layer, keyed off the payload `type` value `gw_vpn_path_down`. It does not live in Mist. See Shared Appendix §2.

**Do not confuse this key with `vpn_path_down`.** That is a separate Marvis alarm with native severity `critical`, and its payload `type` is the uppercase `VPN_PATH_DOWN`. The two keys differ by the `gw_` prefix alone. See `GW_VPN_PEER_DOWN.md` §1.1 for the full SVR key table.

### SVR vs BGP — two independent overlays on SSR

**This runbook is for SVR peer paths only.** On SSR gateways, SVR (data plane, per-transport peer paths) and BGP (control plane, TCP/179 sessions) are two independent overlays. BGP outages fire under `gw_bgp_neighbor_down` and have their own runbook — do not conflate them.

| Concern | SVR (this alarm) | BGP (separate alarm) |
|---|---|---|
| Alarm keys | `gw_vpn_path_down` (+ `gw_vpn_path_up` clear), `vpn_peer_down`, `vpn_path_down` | `gw_bgp_neighbor_down` (+ `gw_bgp_neighbor_up` clear) |
| Layer | Data plane — forwards session-oriented traffic between SSRs | Control plane — exchanges routes |
| Transport | UDP-based Secure Vector Routing between SSRs over one or more transports | TCP/179 to peer IP over an underlay interface |
| Independence | SVR peer paths can be `down` while BGP is `Established` | BGP can be down while SVR paths are `up` |
| SSR command | `show peers`, `show peers detail` | `show bgp summary`, `show bgp neighbor <peer-ip>` |
| Mist GUI | WAN Assurance → Peer Path Insights | BGP state is not surfaced in a dedicated view — use PCLI |

The two often correlate: a shared WAN transport can bring both down at once. Validate each separately with its own commands.

## 2. Impact

**Direct (SVR):**

- Loss of one SVR transport to the affected DC-hub peer (typically one of the two branch ISPs).
- **One path down to one hub (typical case):** the peer stays `up` on the surviving transport; traffic reconverges — may see brief packet loss, then continues on the remaining ISP.
- **All paths to one hub down:** the `vpn_peer_down` alarm co-fires for that hub; overlay to that hub is fully out, but the *other* hub (Dallas or Chicago) continues to carry branch traffic.
- **All paths to both hubs down:** the branch loses overlay reachability entirely; DC-hosted apps become unreachable even if an underlay ISP link is technically up.
- Increased latency and jitter as traffic reconverges to the surviving transport(s); voice / video quality can degrade during the transition.
- Reduced aggregate bandwidth — a two-ISP branch operating on a single transport is capacity-halved.
- Because there is only a single SSR130 at the branch, there is no gateway-side redundancy to fall back on — any SVR problem here is branch-scope.

**Correlated (BGP):**

- If SVR and BGP share the affected WAN transport, the BGP session to the same DC hub may also drop — this will surface as a **separate** `gw_bgp_neighbor_down` alarm. Validate BGP independently rather than assuming it followed SVR's state.

## 3. Required Information

### SVR peer path (always capture)

| Category | Data to capture |
|---|---|
| Device | Site, Hostname, Serial Number, SSR software version, Mist device ID |
| Peer classification | Which DC hub: `hub-Dallas-SSR1300` / `hub-Chicago-SSR1300` |
| Hub redundancy state | Is the *other* hub peer (Dallas if this is Chicago, or vice versa) currently reachable via SVR? Are its paths `up`? This tells you whether the branch is degraded-but-serving or overlay-isolated. |
| SVR path | Local router / node, remote router / node, path name (from `show peers`), WAN transport name, WAN provider / circuit ID |
| Transport underlay | Local device-interface, local WAN link (ISP-A / ISP-B), local transport IP, remote public IP |
| Path state | Per-transport `up` / `down` / `standby` status; is the aggregate peer still `up` on another transport? |
| Performance | Packet loss %, latency (ms), jitter (ms) captured at time of alarm (from Mist Peer Path Insights or `show peers detail`) |
| Timeline | Alert timestamp (UTC), last known `up` time, recent config changes, upstream ISP maintenance windows |
| Correlated Alarms | Any active alarms on the SSR130, on the branch EX4100 VC, on either ISP underlay, or on the peer DC-hub SSR1300 in the last 15 min |

### BGP (only if a BGP alarm is co-firing)

| Category | Data to capture |
|---|---|
| BGP peer | Peer IP, Peer AS, Local AS, session state |
| Shared transport | Does the BGP session and this SVR path ride the same underlay WAN link? |

See Shared Appendix §5 for the always-required ticket fields.

## 4. Validation

### SVR peer-path checks (this alarm)

| Check | Command / Action |
|---|---|
| SSR reachable in Mist | Mist UI → WAN Edges → *device* → Health / Insights |
| SSR connected to conductor / cloud | `show system connected` |
| System status | `show system` |
| SVR peer path status (all peers, all transports) | `show peers` |
| SVR peer path detail | `show peers detail` |
| WAN transport / underlay interfaces | `show device-interface` and `show network-interface` |
| Routing table | `show route` |
| Reachability to remote peer using correct source | `ping <remote-public-ip> source <local-transport-ip>` |
| Path to remote peer | `traceroute <remote-public-ip>` |
| Alarms on device | `show alarms` |
| Recent events (scoped) | `show events` |
| Peer path history / performance in Mist | WAN Assurance → Peer Path Insights → filter by device → drill into affected path |
| WAN link health | WAN Assurance → WAN Links |

**Never** run a bare `ping <remote-public-ip>` on SSR — it may egress from the wrong interface and produce a false-negative. Always pin the source with `source <local-transport-ip>` so you're actually testing the ISP transport that the path uses. See Shared Appendix §7.

### BGP checks (only if correlated BGP alarm is active, or the shared transport is suspect)

| Check | Command / Action |
|---|---|
| BGP session summary | `show bgp summary` |
| Specific peer detail | `show bgp neighbor <peer-ip>` |

If BGP is `Established` while SVR paths are down, transport-to-BGP-peer-IP is fine but the SVR overlay is broken — investigate SVR-specific causes (MTU/PMTUD, UDP filtering on the underlay, tenant / service-route / security policy). If BGP is also down on the same transport, treat the shared underlay as the primary suspect and prioritize the underlay-link alarms (`bad_wan_uplink`, `intermittent_wan_connectivity`).

## 5. Resolution

| Area | Action |
|---|---|
| Underlay link | If a WAN link alarm (`bad_wan_uplink`, `intermittent_wan_connectivity`) is co-firing on the ISP that carries this path, resolve that first — SVR will re-establish once transport recovers. |
| ISP degradation | If the underlay is technically `up` but performance is bad (loss / latency / jitter above SVR thresholds), open an ISP ticket with the affected circuit ID; SVR is doing the right thing by marking the path down. |
| Interface / optics | Check CRC, drops, and optics DDM on the WAN-facing interface (`show device-interface`). Replace cable / SFP if physical-layer fault is confirmed. |
| Peer device | Verify the DC-hub SSR1300's SVR process is up and its side of the path is not the problem (hub-side runbook / Mist WAN Edges view for that hub). If the hub-side gateway is impaired, coordinate with the hub-side on-call rather than driving from the branch. |
| Reachability | From SSR, confirm the remote peer's public IP is reachable **from the correct source IP** with `ping <remote-public-ip> source <local-transport-ip>`. |
| MTU / PMTUD | SVR encapsulates in UDP; a PMTUD blackhole on the underlay will cause paths to flap or stay down. Verify path MTU on the affected transport. |
| UDP filtering | Some carrier / customer-edge firewalls silently drop UDP once a session ages out. If path repeatedly flaps at a fixed interval, suspect stateful UDP filtering upstream. |
| Firewall / policy | On SSR the peer path traverses a tenant / service-route / security policy — verify these were not recently changed. |
| Configuration | Review Mist audit logs for SVR or interface config changes in the last 24 h. Rollback if a recent change caused the outage. |
| Routing | Verify next-hop resolution for the peer's public IP on the affected transport (`show route`). |
| Recovery (SVR) | Confirm `show peers` reports the affected path back to `up` on the expected transport, and the paired clear event has fired. |
| Recovery (BGP, if it was also affected) | Confirm BGP transitions back to `Established`. Do not close the SVR ticket until any BGP alarm has also cleared. |

## 6. Closure Criteria

**SVR (required for this alarm):**

- `show peers` reports the affected path back to `up` on the expected transport.
- Packet loss, latency, and jitter on the recovered path are within acceptable thresholds (per Peer Path Insights baseline).
- Reachability to the remote peer's public IP from the correct source succeeds.
- **The paired clear event `gw_vpn_path_up` has been received.**
- No recurrence of `gw_vpn_path_down` for this path within a 30-minute debounce window.
- If `vpn_peer_down` co-fired, the overall peer is also back `up`.
- The *other* DC-hub peer (whichever of Dallas / Chicago was not the impaired one) is also confirmed reachable via SVR — the branch is back to full 2-hub overlay redundancy, not just single-hub-serving.
- Root cause is documented on the ticket, including which hub peer and which underlay transport were affected, and whether the branch was ever in the "both hubs down" isolation state during the incident.

**BGP (only if BGP alarms co-fired):**

- BGP neighbor state is `Established` and the paired `gw_bgp_neighbor_up` has been received on its own ticket.
- Close the BGP ticket per its own runbook — do not implicitly close it from this ticket.

## 7. Mist GUI Navigation

**SVR-related:**

| Task | Navigation |
|---|---|
| Verify alert | Monitor → Alerts → filter by `gw_vpn_path_down` |
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
| Reachability with correct source | `ping <remote-public-ip> source <local-transport-ip>` |
| Path to remote peer | `traceroute <remote-public-ip>` |

**SVR (this alarm):**

| Purpose | Command |
|---|---|
| SVR peer paths (all peers, all transports) | `show peers` |
| SVR peer path detail | `show peers detail` |
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

- `vpn_peer_down` — the aggregate SVR peer is down (all transports failed). This is a strict escalation of the per-path alarm; if it is co-firing, treat the peer outage as the primary incident.
- `vpn_path_down` — related SVR path alarm on the same or peered devices; usually co-fires when a shared underlay drops.
- `bad_wan_uplink` — underlying transport failure (Marvis). Common shared root cause; the SVR path is a symptom, the ISP link is the cause.
- `intermittent_wan_connectivity` — flaky underlay. Expect SVR paths to flap in step with the underlay.
- `gw_bgp_neighbor_down` — BGP control-plane session on the same DC-hub peering is down (distinct from SVR; follow the BGP runbook, not this one). Same DC-hub SSR1300 endpoints, different overlay layer.
- `gw_critical_port_down` — physical port on the SSR130 serving the transport is down. Fix the port before chasing SVR.
- `switch_down` — upstream EX4100 VC (or a member) is down; if the SSR130's LAN-side transport rides that VC, SVR paths can go with it.

## 10. Escalation

Per Shared Appendix §8. Tier 1 NOC can self-clear underlay-transport, reachability, ISP-handoff, and rollback-driven root causes on the branch SSR130. Escalate to Tier 2 for:

- Tenant / service-route / security policy changes on either the branch SSR130 or the DC-hub SSR1300
- MTU / PMTUD suspected blackholes on the underlay
- SVR configuration changes that span multiple devices
- Suspected UDP filtering by an ISP or transit provider (usually needs vendor-side coordination)
- Configuration restore that spans multiple devices
- **All paths to both hubs (Dallas + Chicago) down simultaneously** — branch overlay is isolated; page hub-side on-call in parallel and treat as a site outage, not a single-path alarm.

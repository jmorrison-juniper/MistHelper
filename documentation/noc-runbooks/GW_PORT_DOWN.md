# GW_PORT_DOWN

> **Read this first — `GW_PORT_DOWN` names two different objects in Mist.** The alarm you page on is catalogued as **`gw_critical_port_down`**, but the webhook payload it sends carries `"type": "gw_port_down"`. A separate, unrelated **device event** also uses the key `GW_PORT_DOWN`. The two objects have different trigger rules and different noise levels. Section 1.1 tells them apart. If your ticket source is a Mist webhook, you have the **alarm**. If your ticket source is an event search or an event-stream subscription, you have the **event**.

## 1. Overview

| Field | Value |
|---|---|
| **Alert Name** | GW_PORT_DOWN |
| **Mist alarm key** | `gw_critical_port_down` (alarm-definition catalog key). **The webhook payload `type` is `gw_port_down`** — filter downstream rules on `gw_port_down`, not on the catalog key. |
| **Platform** | Juniper SSR130 (single gateway at a retail branch — no local HA peer). The same alarm key also fires on SRX gateways. SRX uses Junos, not SSR PCLI, so an SRX-specific runbook is planned as Phase 2. |
| **Mist native severity** | `warn` |
| **NOC severity** | **Critical** (override — see rationale below) |
| **Group** | `infrastructure` |
| **Clear event key** | `gw_critical_port_up` (payload `type` is `gw_port_up`, native severity `info`) |
| **Default enabled** | `true` — the alarm is on by default in a new alarm template. |
| **Correlated alarms** | `gw_bgp_neighbor_down`, `gw_vpn_path_down`, `vpn_peer_down`, `vpn_path_down`, `bad_wan_uplink`, `intermittent_wan_connectivity`, `gateway_down`, `gw_bad_cable`, `gw_negotiation_mismatch`, `gw_mtu_mismatch`, `port_flap`, `port_stuck`, `switch_down` |
| **Prerequisites** | **The port must be flagged as critical on the gateway port configuration.** Without that flag the port transition raises only the `GW_PORT_DOWN` device event, and no alarm fires. See §1.2. |
| **Payload fields** | `hostnames`, `nodes`, `gateways`, `reasons` (per the alarm-definition catalog) |
| **Description** | A gateway port flagged as **critical** has transitioned to Down. At a retail branch the branch runs a single SSR130, so a critical gateway port is almost always an ISP transport port, the LAN uplink to the EX4100 Virtual Chassis, or a member of the uplink aggregate. Treat this alarm as **branch-impacting until the port role is confirmed**. |

### Severity rationale (Mist `warn` → NOC `critical`)

Mist ships this alarm as `warn` because gateway port-down events span a wide impact range across its whole customer base. In this environment the alarm fires **only** for ports an engineer explicitly flagged as critical, and the branch has a single SSR130 with no local HA peer. Every critical port on that gateway is therefore either WAN transport or the branch LAN uplink. We page it as **critical**.

The override lives in the downstream paging and ticketing layer, keyed off the payload `type` value `gw_port_down`. It does not live in Mist. See Shared Appendix §2.

If the critical-port flags turn out to be over-applied, retune the gateway port configuration. Do not lower the NOC severity.

### 1.1 Alarm or event? Tell them apart

| | **Alarm** | **Device event** |
|---|---|---|
| Catalog key | `gw_critical_port_down` | `GW_PORT_DOWN` |
| Payload `type` value | `gw_port_down` | `GW_PORT_DOWN` |
| Display name | Critical WAN Edge Port Down | WAN Edge Port Down |
| Catalog endpoint | `GET /api/v1/const/alarm_defs` | `GET /api/v1/const/device_events` |
| Has a severity | Yes — `warn` | **No** — events carry no severity |
| Has a group | Yes — `infrastructure` | No |
| Fires for | **Critical-flagged ports only** | **Every** gateway port transition |
| Delivered by | Alarm webhook, Monitor → Alerts | Event search, event webhook, Monitor → Events |
| Paired clear | `gw_critical_port_up` | `GW_PORT_UP` |
| Use it for | Paging and ticketing | Timeline reconstruction and flap counting |

**Operator rule:** page on the alarm. Investigate with the event. The event fires on every port on the box, including access and unused ports, so it is far noisier. Never wire the uppercase `GW_PORT_DOWN` event key into a paging rule.

A device-event record looks like this. Note that Mist derives it from the device SNMP trap:

```json
{
  "type": "GW_PORT_DOWN",
  "timestamp": 1575935387,
  "org_id": "b4e16c72-d50e-4c03-a952-a3217e231e2c",
  "site_id": "57b2f891-09c1-4dcc-8ff1-2f9fb3ff7d39",
  "mac": "0c8126c7054d",
  "version": "18.1R3.3",
  "text": "SNMP_TRAP_LINK_DOWN: ifIndex 515, ifAdminStatus up(1), ifOperStatus down(2), ifName ge-0/0/2",
  "model": "EX2300-C-12P",
  "port_id": "ge-0/0/2"
}
```

### 1.2 Prerequisite — the critical-port flag

The alarm is silent unless an engineer flags the port. Set the flag in **WAN Edges → *SSR130* → Port Configuration**, or in the gateway template that the site inherits.

At a retail branch, flag these gateway ports as critical:

- Both ISP-facing WAN transport ports.
- The LAN uplink to the EX4100 Virtual Chassis, and every member of that aggregate.
- Any dedicated out-of-band management port, where the branch has one.

Do not flag unused ports or ports that serve a single endpoint. Over-flagging turns a paging alarm into noise.

### 1.3 Read the `reasons` string

The alarm carries a `reasons` array. Each entry is a raw interface state string:

```text
ifIndex 564, ifAdminStatus up(1), ifOperStatus down(2), ifName ae0
```

Decode the two status values before you touch anything. They separate a human action from a real fault:

| `ifAdminStatus` | `ifOperStatus` | Meaning | First action |
|---|---|---|---|
| `up(1)` | `down(2)` | The port is enabled but the link is dead. This is a real fault — cable, optic, remote end, or ISP. | Work §5 from the top. |
| `down(2)` | `down(2)` | Somebody disabled the port, or a configuration push disabled it. | Check Organization → Audit Logs first. This is a change, not a fault. |
| `up(1)` | `up(1)` | The port recovered before you opened the ticket. | Confirm `gw_critical_port_up` arrived. Then count flaps — see §5. |

Read `ifName` to classify the port. `ae0` and similar names are aggregates, so the branch may still be forwarding on a surviving member. A `ge-` or `xe-` name is a single physical port with no member to fall back on.

## 2. Impact

Impact depends entirely on the role of the flagged port. Classify the port before you declare an outage.

- **ISP transport port (single-ISP branch).** The branch loses WAN. Both SVR overlays to the DC hubs (Dallas and Chicago) fail, both BGP sessions withdraw, and the store loses card processing, IP phones, and back-office access. This is a full branch outage.
- **ISP transport port (dual-ISP branch).** The branch fails over to the surviving ISP. Service continues in a degraded state with no transport redundancy. A second transport failure now goes straight to full outage.
- **LAN uplink aggregate member.** The aggregate loses a member and forwards on the survivor. Throughput to the EX4100 Virtual Chassis drops. The store normally sees no change.
- **LAN uplink at zero surviving members, or a single-link LAN uplink.** The gateway is isolated from the branch LAN. Every wired and wireless user loses WAN. Mist may also lose sight of the gateway and raise `gateway_down`, because branch management is usually in band.
- **Management port.** Mist loses remote visibility, configuration push, and Marvis analytics for the gateway. The data plane keeps forwarding, and branch users normally notice nothing.

## 3. Required Information

| Category | Data to capture |
|---|---|
| Device | Site name, site ID, hostname, serial number, SSR software version, Mist device ID, gateway MAC from the payload `gateways` array |
| Port classification | `ISP-A-transport` / `ISP-B-transport` / `LAN-uplink-member` / `LAN-uplink-single` / `management` / `unused` |
| Raw reason | The full `reasons` string, plus the decoded `ifAdminStatus` and `ifOperStatus` values from §1.3 |
| Interface | `ifName`, `ifIndex`, media type (copper or fiber), configured speed, aggregate name and surviving member count |
| HA node | The `nodes` value, where present. This field identifies the cluster node on an SRX HA pair. A branch SSR130 is a single node, so this field is normally empty. |
| Optics (fiber only) | Transmit power, receive power, laser bias, temperature, and the vendor threshold for each |
| Transport peer | ISP circuit ID, demarcation device, and any open ISP ticket for that circuit |
| Timing | Alarm timestamp in UTC, `last_seen`, `count` of repeats, time of the last known-good state |
| Timeline | Recent configuration pushes, recent firmware upgrades, scheduled ISP maintenance windows |
| Correlated alarms | Any alarm active on the SSR130, on the EX4100 Virtual Chassis, or on either ISP underlay in the last 15 minutes |

See Shared Appendix §5 for the always-required ticket fields.

## 4. Validation

Validate from the Mist cloud first. The gateway is usually still reachable when this alarm fires, because only one port went down, so PCLI is normally available.

### From Mist cloud

| Check | Command or action |
|---|---|
| Confirm the alarm and read `reasons` | Monitor → Alerts → filter by `gw_critical_port_down` |
| Port state on the front panel | WAN Edges → *SSR130* → Front Panel |
| Critical-port flag on the affected port | WAN Edges → *SSR130* → Port Configuration |
| Raw port transitions and flap count | Monitor → Events → filter by device, type `GW_PORT_DOWN` and `GW_PORT_UP` |
| WAN link history for both ISPs | Monitor → Service Levels → WAN |
| SVR peer-path history to both hubs | Monitor → Service Levels → WAN → Peer Paths |
| Gateway reachability | WAN Edges → *SSR130* → Insights |
| Recent configuration pushes | Organization → Audit Logs → filter by device |

### From SSR PCLI

| Check | Command |
|---|---|
| System, model, and uptime | `show system` |
| Cloud connectivity | `show system connected` |
| Physical port state | `show device-interface` |
| Logical interface state | `show network-interface` |
| Alarms on the box | `show alarms` |
| Recent events | `show events` |
| Routing table | `show route` |
| SVR peer paths | `show peers` |
| BGP session summary | `show bgp summary` |
| Reachability to the hub with a pinned source | `ping <hub-public-ip> source <local-transport-ip>` |

**Never** run a bare `ping <target>` on an SSR. The packet may leave through the wrong interface and report a false negative. Always pin the source with `source <local-transport-ip>`. See Shared Appendix §7.

### On an SRX gateway (Junos, not SSR)

If the alarm fired on an SRX rather than an SSR130, use Junos syntax. Do not paste PCLI into an SRX.

| Check | Command |
|---|---|
| Interface summary | `show interfaces terse` |
| Interface detail | `show interfaces <ifName> extensive` |
| Admin-down or link-down | `show configuration interfaces <ifName>` |
| Optics readings | `show interfaces diagnostics optics <ifName>` |
| Aggregate member state | `show lacp interfaces` |
| Chassis alarms | `show chassis alarms` |
| Interface-scoped logs | `show log messages \| match <ifName>` |

## 5. Resolution

Classify the port first, using `ifName` from the `reasons` string. The correct response differs completely between a transport port and a LAN uplink member.

| Area | Action |
|---|---|
| Administrative disable | If `ifAdminStatus` is `down(2)`, this is a change and not a fault. Review Organization → Audit Logs for the last 24 hours. If a push disabled the port, roll the push back through Mist. |
| ISP transport port | Verify the ISP demarcation device shows link. Open a ticket with that ISP and supply the circuit ID. A dead transport port on the branch side and a dark demarcation device look identical from Mist. |
| Dual-ISP branch | Confirm the surviving ISP carries the load. Verify both SVR peer paths and both BGP sessions on the surviving transport before you downgrade the ticket. |
| Cable or optic | Reseat or replace the cable, the direct-attach cable, or the transceiver. For fiber, compare the transmit and receive readings against the vendor threshold. |
| LAN uplink member | Confirm the surviving member carries traffic. Check the matching port on the EX4100 Virtual Chassis, which usually raises `sw_critical_port_down` at the same time. Fix whichever end shows the fault. |
| LAN uplink at zero members | Treat this as a branch outage. Follow the `GATEWAY_DOWN` runbook in parallel, because Mist will lose the gateway shortly. |
| Marvis co-fires | If `gw_bad_cable`, `gw_negotiation_mismatch`, or `gw_mtu_mismatch` is active on the same port, act on that alarm first. Marvis has already identified the physical or negotiation fault. |
| Flapping port | If `port_flap` is co-firing, or the event search shows repeated `GW_PORT_DOWN` and `GW_PORT_UP` pairs, do not close on the first recovery. A flapping transport port destabilizes both overlays and is worse than a clean failure. |
| Hardware | If `show alarms` reports a port or transceiver fault that survives a cable and optic swap, plan a replacement. Raise an RMA for the SSR130 where the port itself has failed. |
| Firmware | If the alarm started right after a firmware upgrade, prepare a rollback. Any change on the only branch gateway is a Tier 2 decision. |
| Recovery | Confirm the port is up, the `gw_critical_port_up` clear has arrived, both SVR peer paths are up, and both BGP sessions are established. |

## 6. Closure Criteria

- The affected port reports `ifAdminStatus up(1)` and `ifOperStatus up(1)`.
- **The paired clear alarm `gw_critical_port_up` has been received** (payload `type` is `gw_port_up`).
- Where the port is an aggregate member, the aggregate has recovered its full designed member count.
- Where the port is ISP transport, that WAN link is up and inside its performance baseline.
- Both SVR peer paths to the DC hubs (Dallas and Chicago) are up.
- Both BGP overlay sessions to the DC hubs are established.
- No recurrence of `gw_critical_port_down` on this port within a 30-minute debounce window.
- The `GW_PORT_DOWN` event search over the last hour shows no continuing flap on this port.
- No Marvis alarm (`gw_bad_cable`, `gw_negotiation_mismatch`, `gw_mtu_mismatch`, `port_flap`, `port_stuck`) remains active on the port.
- Every co-fired alarm has cleared on its own ticket. Do not close those tickets from this one.
- The root cause is documented on the ticket, including the port role and the decoded `ifAdminStatus` and `ifOperStatus` values.

## 7. Mist GUI Navigation

| Task | Navigation |
|---|---|
| Verify alert | Monitor → Alerts → filter by `gw_critical_port_down` |
| Raw port events and flap count | Monitor → Events → filter by device, type `GW_PORT_DOWN` |
| Gateway health | WAN Edges → *SSR130* → Insights |
| Port status | WAN Edges → *SSR130* → Front Panel |
| Critical-port flag | WAN Edges → *SSR130* → Port Configuration |
| WAN link history | Monitor → Service Levels → WAN |
| SVR peer-path history | Monitor → Service Levels → WAN → Peer Paths |
| Downstream switch view | Switches → *EX4100 VC* → Front Panel |
| Audit logs | Organization → Audit Logs |

**Legacy path note:** older documents may say `Routers → SSR130`. The current Mist interface groups all gateways under `WAN Edges → …`.

## 8. SSR PCLI Commands (quick reference)

SSR uses PCLI. Do not paste Junos syntax into an SSR.

| Purpose | Command |
|---|---|
| System, model, and uptime | `show system` |
| Cloud connectivity | `show system connected` |
| Physical ports | `show device-interface` |
| Logical interfaces | `show network-interface` |
| Alarms | `show alarms` |
| Events | `show events` |
| Routing table | `show route` |
| SVR peer paths | `show peers` |
| BGP summary | `show bgp summary` |
| BGP peer detail | `show bgp neighbor <peer-ip>` |
| Active sessions | `show sessions summary` |
| Reachability with a pinned source | `ping <target> source <local-transport-ip>` |
| Path to a remote target | `traceroute <target>` |

See Shared Appendix §7 for the full SSR PCLI reference, and §6 for the Junos reference used on SRX gateways.

## 9. Cross-references (sibling alarms)

If any of these are co-firing, resolve the co-fired alarm first. A port-down alarm is often the root cause of the alarms above it, and a symptom of the Marvis alarms below it.

**This alarm is usually the root cause of:**

- `gw_bgp_neighbor_down` — the BGP control-plane session rode the failed transport port.
- `gw_vpn_path_down`, `vpn_peer_down`, `vpn_path_down` — the SVR overlay rode the failed transport port.
- `bad_wan_uplink`, `intermittent_wan_connectivity` — Marvis has judged the surviving transport degraded.
- `gateway_down` — the failed port was the LAN uplink, and Mist has now lost the gateway entirely.

**This alarm is usually a symptom of:**

- `gw_bad_cable` — Marvis has identified a physical cable fault on the port.
- `gw_negotiation_mismatch` — speed or duplex disagreement with the peer.
- `gw_mtu_mismatch` — MTU disagreement with the peer.
- `port_flap` — the port is cycling rather than failing cleanly.
- `port_stuck` — the port reports up but passes no traffic.

**Peer alarm on the other end of the LAN uplink:**

- `sw_critical_port_down` — the matching EX4100 port. When both fire together, one physical link is at fault. Investigate the cable and both transceivers once, not twice.

**Triage rule:** `gw_critical_port_down` with a Marvis alarm on the same port means the Marvis alarm holds the root cause. `gw_critical_port_down` with overlay alarms above it means this alarm holds the root cause.

## 10. Escalation

Per Shared Appendix §8.

- **Tier 1 NOC** can self-clear cable, transceiver, administrative-disable, and remote-end causes, provided the branch keeps a working transport path throughout.
- **Escalate to Tier 2 immediately** for:
  - A branch with no surviving WAN transport, which is a full store outage.
  - A LAN uplink at zero surviving members.
  - A port that keeps flapping after a cable and transceiver replacement.
  - Suspected firmware or configuration rollback on the only branch gateway.
  - Hardware replacement of the SSR130.
- **Open an ISP ticket in parallel** whenever the failed port faces a carrier demarcation device. Do not wait for internal triage to finish before you start the carrier clock.
- **Change Advisory Board** for any planned configuration or firmware change on the recovered gateway, because it is the branch's single point of failure.

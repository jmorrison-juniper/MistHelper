# NODE_DOWN

> **Read this first — this alert does not come from Mist.** `Node Down` is raised by **NNMi**, which polls the device by SNMP and ICMP. Mist has no alarm with this key. Confirm this by searching the Mist alarm-definition catalog (`GET /api/v1/const/alarm_defs`): there is no `node_down` entry. The closest Mist alarms are `switch_down` and `gateway_down`, and they are **corroborating evidence, not the same alert**.
>
> Because the alert starts outside Mist, the first job is not to fix anything. The first job is to answer one question: **is this device managed by Mist?** That answer decides who owns the ticket and which runbook applies. Section 4.2 answers it in one lookup.

## 1. Overview

| Field | Value |
|---|---|
| **Alert Name** | Node Down |
| **Source system** | **NNMi** (Network Node Manager i), by SNMP and ICMP polling |
| **Mist alarm key** | **n/a — this is not a Mist alarm.** Corroborating Mist alarms are `switch_down` (display "Switch offline") and `gateway_down` (display "WAN Edge offline"). |
| **Mist device events** | `SW_DISCONNECTED` and `SW_CONNECTED` for switches. `GW_DISCONNECTED` and `GW_CONNECTED` for gateways. |
| **Platform** | Juniper **EX4400** access switch. See §1.1 — the reported model string "EX400" is not a real model and must be resolved before triage. |
| **Mist native severity** | n/a. For reference, `switch_down` is native `warn` and `gateway_down` is native `warn`. |
| **NOC severity** | **Critical** |
| **Group** | n/a in Mist. The corroborating Mist alarms sit in group `infrastructure`. |
| **Clear event key** | NNMi raises its own `Node Up` correlation. On the Mist side the corroborating clear signals are the `SW_CONNECTED` event and the disappearance of `switch_down`. |
| **Correlated alarms** | `switch_down`, `gateway_down`, `sw_vc_port_down`, `vc_member_deleted`, `vc_master_changed`, `sw_alarm_chassis_mgmt_link_down`, `sw_critical_port_down`, `gw_critical_port_down` |
| **Prerequisites** | The node must be in the NNMi topology with a working SNMP community or SNMPv3 credential. A node that NNMi never discovered cannot raise this alert. |
| **Description** | NNMi has stopped receiving SNMP and ICMP responses from a node and has declared it down. The node is an EX4400 access switch. NNMi and Mist are two independent monitoring systems with two independent management paths, so they can disagree. That disagreement is diagnostic information, not a fault in either tool. Section 4.2 turns the disagreement into a routing decision. |

### 1.1 Model name — resolve "EX400" before you triage

**"EX400" is not a Juniper switch model, and it is not in the Mist supported-model catalog.** Verified against `GET /api/v1/const/device_models`. Treat the string as a transcription error and resolve it to a real model before continuing.

| Candidate | Real model? | Where it is used | How to confirm |
|---|---|---|---|
| **EX4400** | **Yes** | Access and small-aggregation switching. The most likely intended model. Variants include EX4400-24P, EX4400-48P, EX4400-48MP, and EX4400-24X. | Read the `model` field from the Mist lookup in §4.2, or run `show chassis hardware`. |
| EX4100 | Yes | The standard access switch in this library's retail branch reference topology, deployed as a 2-member Virtual Chassis. | Same as above. |
| EX4000 | Yes | Newer entry access family. Named close enough to "EX400" to be worth ruling out. | Same as above. |

Do not guess. The `model` field returned by the Mist lookup in §4.2 is authoritative when the device is in Mist. Where the device is not in Mist, take the model from the NNMi node record or from `show chassis hardware` on the console.

### 1.2 Topology note — EX4400 against the library baseline

The Shared Appendix §0 reference topology specifies a 2-member **EX4100** Virtual Chassis at a retail branch. An **EX4400** in the same fleet normally means one of the following. Confirm which one applies, because it changes the blast radius:

- A larger branch or a back-office closet that needs more ports or higher uplink speed than an EX4100 provides.
- An aggregation or distribution switch at a site that has one, which the flat retail branch does not.
- A newer or a legacy refresh tier that sits beside the EX4100 standard.

EX4400 and EX4100 both run Junos and both raise the same Mist `switch_down` alarm. Every Junos command in §8 works on both. The difference that matters is **redundancy**: confirm whether this EX4400 is a standalone switch or a Virtual Chassis member. A standalone switch going down takes every port with it.

## 2. Impact

Impact depends on the role of the node and on whether it is a Virtual Chassis member. Establish both before you declare a scope.

- **Standalone EX4400 access switch down.** Every endpoint on that switch loses the network. At a retail site that means point-of-sale lanes, IP phones, access points, and back-office hosts on those ports. Access points served by that switch also drop, so wireless coverage in that area fails as well.
- **EX4400 as a Virtual Chassis member.** The Virtual Chassis survives on the remaining member. Ports on the failed member are dead, and the Virtual Chassis is now a single point of failure. Expect `vc_member_deleted` or `vc_master_changed` to co-fire.
- **EX4400 in an aggregation role.** Every access switch behind it is isolated. The blast radius is the whole downstream tree, not one closet. Treat this as a site outage.
- **Uplink path to the gateway lost.** If the failed node carried the path to the branch SSR130, the site loses WAN even though the gateway itself is healthy. Expect `gateway_down` to follow, because branch management is normally in band.
- **Monitoring visibility only.** If the node is up and only the SNMP or management path failed, there is **no user impact**. Section 4.2 separates this case from a real outage. Do not declare a store outage before you complete that check.

## 3. Required Information

| Category | Data to capture |
|---|---|
| From NNMi | Node name, management IP address, resolved model, NNMi node UUID, incident ID, incident type (`Node Down` or `Node or Connection Down`), first-seen time in UTC |
| Poll detail | Which poll failed — SNMP, ICMP, or both. Configured poll interval and retry count. Time of the last successful poll. |
| Neighbor confirmation | Whether NNMi confirmed the failure through neighbor analysis. See §4.1 — this changes how much you trust the alert. |
| From Mist | `managed` value, `status` value, site ID, Mist device ID, MAC, serial number, Junos version, `last_disconnected` timestamp |
| Model resolution | The real model from §1.1, and how it was confirmed |
| Redundancy role | Standalone switch, Virtual Chassis master, or Virtual Chassis backup |
| Power | Power over Ethernet budget, uninterruptible power supply status, and any site power event in the same window |
| Timeline | Recent configuration pushes, recent firmware upgrades, scheduled maintenance windows, recent physical work at the site |
| Correlated alarms | Every Mist alarm active on this device, on its Virtual Chassis peer, and on the site gateway in the last 15 minutes |

See Shared Appendix §5 for the always-required ticket fields.

## 4. Validation

Validate in three stages, in this order. Do not skip stage two.

### 4.1 Stage one — qualify the NNMi alert

NNMi raises two similar incidents. They carry different confidence, so read the incident type before you act:

| NNMi incident | What NNMi established | Confidence |
|---|---|---|
| **Node Down** | Every address on the node stopped responding, **and** a neighbor confirmed the failure. | High. The node is very probably down. |
| **Node or Connection Down** | The node stopped responding, but NNMi could **not** confirm through a neighbor. | Lower. The node may be up behind a broken path. |

Also capture these, because each one produces a false Node Down on a healthy device:

- Was the SNMP credential rotated or the community string changed recently?
- Did an access list or firewall rule change block the NNMi poller?
- Did the management address change, so NNMi is polling an address the device no longer owns?
- Is NNMi itself healthy, and are other nodes at the same site still polling normally?

### 4.2 Stage two — is the device managed by Mist?

**This is the decision point.** One lookup answers it. Run the graphical check for speed, or the API check when you need the exact field values on the ticket.

**Graphical check.** Open **Organization → Inventory** and search for the node by name, MAC address, or serial number. Read the **Managed** column and the **Status** column.

**API check.** The inventory search returns both fields directly. This call is verified working:

```bash
curl -s -H "Authorization: Token $MIST_APITOKEN" \
  "https://api.mist.com/api/v1/orgs/$ORG_ID/inventory/search?text=<node-name-or-mac-or-serial>"
```

The response carries the two fields that decide ownership:

```json
{
  "results": [
    {
      "type": "switch",
      "name": "Morrison-Switch",
      "mac": "209339051780",
      "model": "EX4100-F-12P",
      "serial": "FJ3724AV0131",
      "site_id": "cf36153a-97bb-4974-8f8f-e9cc25d64d83",
      "version": "25.4R1-S2.3",
      "managed": true,
      "status": "connected",
      "last_disconnected": 1787598084
    }
  ],
  "total": 1
}
```

Read the two fields as follows:

- **`managed`** — `true` means Mist owns the configuration of this device. `false` means Mist can see the device but does not manage it, which covers monitor-only and unadopted devices.
- **`status`** — `connected` means Mist is in contact with the device right now. `disconnected` means Mist has lost it too.

NNMi identifies a node by IP address, and Mist inventory does not search on IP address. Use the device search instead when the IP address is all you have. This call is also verified working:

```bash
curl -s -H "Authorization: Token $MIST_APITOKEN" \
  "https://api.mist.com/api/v1/orgs/$ORG_ID/devices/search?type=switch&ip=<nnmi-management-ip>"
```

**Two verified lookup gotchas.** Both will cost you time if you do not know them:

1. The `hostname` filter on the device search requires an **exact** match. A partial name returns zero results and looks identical to "device not found". Use the inventory search with `text=` when you need a wildcard on name, MAC address, or serial number.
2. The `hostname` field comes back as a **list**, not a string, because a Virtual Chassis reports one entry per member.

### 4.3 Stage three — route the ticket

Cross the NNMi result with the Mist result. This table is the whole point of the runbook.

| Mist result | Meaning | Who owns it | Next action |
|---|---|---|---|
| `managed: true`, `status: disconnected` | **Both systems agree the device is down.** This is a real outage. | Network operations | Treat as a confirmed outage. Follow §5. Expect `switch_down` to be active in Mist. |
| `managed: true`, `status: connected` | **The systems disagree.** Mist is talking to the device right now, so the device is alive. NNMi has lost its own polling path. | Monitoring team, with network operations assisting | Do **not** declare a store outage. Investigate the NNMi path — SNMP credential, access list, management address. Confirm health from Mist, then work §5.2. |
| `managed: false` (any status) | Mist can see the device but does not manage it. Mist telemetry is incomplete by design, so Mist silence proves nothing. | Network operations, using the Junos path | **NNMi is authoritative here.** Do not wait for a Mist alarm, because a monitor-only device may never raise one. Go straight to console and Junos in §4.4. |
| `total: 0` — no result | The device is not in Mist at all. | Network operations, using the Junos path | **NNMi is the only source of truth.** Follow the non-Mist switch process. Also raise a records ticket, because an unmanaged production switch is an inventory gap. |

**Rule:** never close a Node Down ticket on Mist silence alone. Mist silence is meaningful only when the device is `managed: true`.

### 4.4 Device-level validation

Where the device is reachable, or once console access is available:

| Check | Command or action |
|---|---|
| Mist health view (managed devices) | Switches → *device* → Insights |
| Mist connect and disconnect history | Monitor → Events → filter by device, type `SW_DISCONNECTED` and `SW_CONNECTED` |
| System, model, and uptime | `show system information` |
| Junos version | `show version` |
| Confirm the real model | `show chassis hardware` |
| Chassis alarms | `show chassis alarms` |
| Power, fan, and temperature | `show chassis environment` |
| Reboot cause | `show system reboot` |
| Virtual Chassis membership | `show virtual-chassis` |
| Management interface state | `show interfaces terse \| match "me0\|vme"` |
| Uplink state | `show interfaces terse` |
| Neighbor visibility | `show lldp neighbors` |
| SNMP configuration, for a suspected polling fault | `show configuration snmp` |
| Recent log entries | `show log messages \| last 100` |
| Recent configuration changes | `show system commit` |

## 5. Resolution

Work the branch that matches your §4.3 routing decision.

### 5.1 Confirmed outage (`managed: true`, `status: disconnected`)

| Area | Action |
|---|---|
| Power | Confirm the switch has power and check for a site power event in the same window. Loss of power is the most common cause of a clean, simultaneous NNMi and Mist loss. |
| Upstream path | Check the upstream switch or gateway port. If `sw_critical_port_down` or `gw_critical_port_down` is co-firing upstream, that port is the root cause. Fix it and this alert clears on its own. |
| Virtual Chassis | If the node is a Virtual Chassis member, check `show virtual-chassis` from the surviving member. If `vc_member_deleted` or `vc_master_changed` is co-firing, follow the `SW_VC_PORT_DOWN` runbook, which owns Virtual Chassis recovery. |
| Reboot loop | If the device returns and drops repeatedly, capture `show system reboot` and `show chassis alarms` while it is up. A power supply fault or a thermal fault presents exactly this way. |
| Firmware | If the loss started right after an upgrade, prepare a rollback. Treat an upgrade fault on an access switch that serves point-of-sale lanes as urgent. |
| Configuration | Review Organization → Audit Logs for the last 24 hours. A push that breaks the management path takes the device off both monitoring systems at once. |
| Hardware | If the switch is powered, shows no link, and does not respond on console, raise an RMA. |
| Site dispatch | Where no remote path exists, dispatch a technician. Ask for the front-panel indicator state and the power state before the technician leaves the site. |

### 5.2 Monitoring disagreement (`managed: true`, `status: connected`)

The device is alive. Mist proves it. Do not dispatch a technician and do not declare a store outage.

| Area | Action |
|---|---|
| Confirm health first | Verify in Mist that clients are attached and the uplink is passing traffic. Record this on the ticket as the evidence that the device is serving users. |
| SNMP credential | Compare the community string or the SNMPv3 credential on the device against the NNMi configuration. Run `show configuration snmp`. A credential rotation that missed one device produces exactly this alert. |
| Poller reachability | Verify the NNMi poller address is permitted. Check the SNMP client list on the device and any access list on the path. |
| Management address | Confirm the address NNMi polls is the address the device still owns. Run `show interfaces terse \| match "me0\|vme"`. |
| Out-of-band path | Where the branch has a separate out-of-band management network, confirm that path is up. Mist uses the in-band path at these branches, so an out-of-band failure hides from Mist and shows only in NNMi. |
| NNMi health | Confirm other nodes at the same site still poll normally. If they do not, the fault is in NNMi or in the path to the site, not in this switch. |
| Close the loop | Correct the polling fault, then force an NNMi rediscovery or poll to clear the incident. Record the root cause as a monitoring fault, not a network outage. |

### 5.3 Unmanaged or absent in Mist (`managed: false`, or no result)

| Area | Action |
|---|---|
| Trust NNMi | Treat NNMi as authoritative. Mist will not raise `switch_down` for a device it does not manage, so waiting for a Mist alarm wastes time. |
| Reach the device | Use the documented console or jump-host path for unmanaged devices. Work §4.4 from the console. |
| Recover | Apply §5.1 for the physical and power checks. Every Junos command in §8 still applies. |
| Close the records gap | Raise a separate records ticket. A production switch that is absent from Mist, or present but unmanaged, is an inventory and compliance gap. Note whether it should be adopted. |

## 6. Closure Criteria

Close against the branch you worked.

**Common to every branch:**

- The NNMi incident has cleared, and NNMi shows the node up on its next poll.
- The root cause is documented on the ticket, including the resolved model from §1.1 and the §4.3 routing decision that was applied.
- Every co-fired alarm has cleared on its own ticket. Do not close those tickets from this one.

**Confirmed outage (§5.1) adds:**

- The device is `status: connected` in Mist, where it is `managed: true`.
- **The Mist `SW_CONNECTED` event has been received for this device.**
- Any corroborating `switch_down` alarm has cleared.
- Every affected endpoint is back on the network — point-of-sale lanes, IP phones, access points, and back-office hosts.
- Where the node is a Virtual Chassis member, `show virtual-chassis` reports the full designed member count with the intended roles.
- No recurrence within a 30-minute debounce window.

**Monitoring disagreement (§5.2) adds:**

- The polling fault is identified and corrected, not merely worked around.
- NNMi polls the device successfully on two consecutive intervals.
- The ticket records that there was **no user impact**, so that trend reporting does not count this as an outage.

**Unmanaged or absent (§5.3) adds:**

- The device responds on its documented management path.
- A records ticket exists for the inventory gap, and its number is recorded here.

## 7. Mist GUI Navigation

| Task | Navigation |
|---|---|
| **Confirm managed status and current state** | **Organization → Inventory → search by name, MAC address, or serial number → read the Managed and Status columns** |
| Switch health | Switches → *device* → Insights |
| Connect and disconnect history | Monitor → Events → filter by device, type `SW_DISCONNECTED` and `SW_CONNECTED` |
| Corroborating alarm | Monitor → Alerts → filter by `switch_down` |
| Port status and front panel | Switches → *device* → Front Panel |
| Virtual Chassis members | Switches → *device* → Front Panel |
| Upstream gateway state | WAN Edges → *SSR130* → Insights |
| Attached clients | Clients → Wired Clients |
| Audit logs | Organization → Audit Logs |

## 8. Junos Commands (quick reference)

These apply to EX4400 and EX4100 alike. Both run Junos.

| Purpose | Command |
|---|---|
| System, model, and uptime | `show system information` |
| Junos version | `show version` |
| Chassis hardware and field-replaceable units | `show chassis hardware` |
| Chassis alarms | `show chassis alarms` |
| Power, fan, and temperature | `show chassis environment` |
| Reboot cause | `show system reboot` |
| Routing engine state | `show chassis routing-engine` |
| Virtual Chassis state | `show virtual-chassis` |
| Virtual Chassis ports | `show virtual-chassis vc-port` |
| Interface summary | `show interfaces terse` |
| Management interface state | `show interfaces terse \| match "me0\|vme"` |
| Neighbor visibility | `show lldp neighbors` |
| Power over Ethernet state | `show poe interface` |
| SNMP configuration | `show configuration snmp` |
| Recent log entries | `show log messages \| last 100` |
| Commit history | `show system commit` |
| Configuration difference | `show configuration \| compare rollback 1` |

See Shared Appendix §6 for the full Junos reference.

## 9. Cross-references (sibling alarms)

**Mist alarms that corroborate a real outage.** When one of these is active alongside the NNMi alert, the outage is confirmed:

- `switch_down` — Mist has lost the switch. This is the direct Mist counterpart to Node Down.
- `gateway_down` — Mist has lost the site gateway. If both fire, suspect a site-wide power or transport fault rather than a switch fault.

**Mist alarms that usually hold the root cause.** Resolve these first, because Node Down is the symptom:

- `sw_critical_port_down` — the upstream switch port serving this node is down. See `SW_CRITICAL_PORT_DOWN.md`.
- `gw_critical_port_down` — the gateway port serving this node's path is down. See `GW_PORT_DOWN.md`.
- `sw_vc_port_down` — a Virtual Chassis port failed, and the node may be an isolated fragment rather than a dead switch. See `SW_VC_PORT_DOWN.md`.
- `vc_member_deleted`, `vc_master_changed` — the Virtual Chassis lost or re-elected a member. See `SW_VC_PORT_DOWN.md`.

**Mist alarm that points at a monitoring fault rather than an outage:**

- `sw_alarm_chassis_mgmt_link_down` — the management link is down while the data plane keeps forwarding. This is the classic cause of the §4.3 disagreement row. See `SW_ALARM_CHASSIS_MGMT_LINK_DOWN.md`.

**Triage rule:** NNMi Node Down with a Mist `switch_down` is a real outage. NNMi Node Down with the device `connected` in Mist is a monitoring fault. NNMi Node Down on a device that Mist does not manage is a real outage that only NNMi can see.

## 10. Escalation

Per Shared Appendix §8.

- **Tier 1 NOC** owns the §4.2 managed-status lookup and the §4.3 routing decision. Tier 1 can self-clear a monitoring disagreement (§5.2) once the polling fault is corrected, and can self-clear a confirmed outage where an upstream port alarm is clearly the root cause and the sibling runbook resolves it.
- **Escalate to Tier 2** for:
  - A confirmed outage with no upstream alarm to explain it, which implies a device-local fault in power, hardware, or firmware.
  - A suspected or confirmed Virtual Chassis split.
  - A repeating reboot or a repeating disconnect on the same device.
  - Hardware replacement of the EX4400.
  - Suspected firmware or configuration rollback.
- **Engage the monitoring team** for every §5.2 disagreement, and for any suspected NNMi platform fault. Where several nodes at one site raise Node Down at the same time while Mist shows them all connected, treat this as an NNMi or poller-path fault and escalate to the monitoring team first.
- **Raise a records ticket** for every §5.3 device. An unmanaged production switch is an inventory and compliance gap, and it will produce this same ambiguity on its next failure.
- **Change Advisory Board** for any out-of-window configuration or firmware change needed to recover the node.

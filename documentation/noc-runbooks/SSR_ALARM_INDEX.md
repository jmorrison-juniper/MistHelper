# SSR_ALARM_INDEX

## 1. Overview

| Field | Value |
|---|---|
| **Document type** | Triage index. This document is not an alarm runbook. It routes an alarm to the runbook that holds it. |
| **Platform** | Any Mist-managed Juniper Session Smart Router. The content is model agnostic. |
| **Purpose** | Hold every alarm that an SSR raises about itself, with the severity, the trigger threshold, the clear threshold, and the first command to run. |
| **Audience** | Tier 1 and Tier 2 network operations. Knowledge management authors who write one article for each alarm. |

### Two alarm sources, one device

A Mist-managed SSR produces alarms in two places. A technician must read both.

| Source | Where you see it | What it tells you |
|---|---|---|
| The router | `show alarms` at the console | The router's own view of its own fault. It names the cause. |
| The Mist cloud | `Monitor`, then `Alerts` | The cloud's view of the device. It reports loss of contact, and it adds analytics. |

Warning: the two sources do not always agree. A gateway that shows `gateway_down`
in Mist can report zero alarms at the console. That combination means that the
management path failed, and that the router is healthy. Never declare a site
outage from the Mist view alone.

### Read a clear threshold before you close a ticket

Several SSR alarms fire at one level and clear at a lower level. A technician who
closes the ticket at the trigger level reopens it minutes later. Each row below
states the clear threshold when the vendor documents one.

## 2. Alarms that the router raises about itself

Every row comes from the Session Smart Networking alarm guide at
<https://docs.128technology.com/docs/events_alarms>.

### Category `interface`

| Severity | Message | First command | Action |
|---|---|---|---|
| Critical | `interface operational down` | `show device-interface` | The port lost its link. Check the cable, the transceiver, and the far-end port. On a cellular port, read `show lte signal` and `show lte sim`. Go to [GW_PORT_DOWN.md](GW_PORT_DOWN.md). |
| Info | `interface administratively down` | `show network-interface` | Someone disabled the port in the configuration. Confirm that the change was planned. Re-enable it through Mist. Do not page on this alarm. |

### Category `peer`

| Severity | Message | Trigger | First command | Action |
|---|---|---|---|---|
| Critical | `Peer <name> is not reachable.` | Every path to the peer is down. | `show peers` | The branch lost the data center over that peer. Go to [GW_VPN_PEER_DOWN.md](GW_VPN_PEER_DOWN.md). |
| Major | `Peer <name> path is down` | One path is down. | `show peers detail` | The peer survives on another path. Go to [GW_VPN_PATH_DOWN.md](GW_VPN_PATH_DOWN.md). The source field names the node, the interface, the address, and the VLAN. |
| Major | `Peer <name> path MTU is unresolvable.` | The router cannot measure the path size. | `ping set-df-bit size 1400 egress-interface <name> <peer-ip>` | Record the largest size that passes. Tier 2 sets the size on the device interface. |

### Category `bgp_neighbor`

| Severity | Message | First command | Action |
|---|---|---|---|
| Major | `Neighbor <address> failed to reach the ESTABLISHED state.` | `show bgp neighbors <address>` | Read the state and the last error. Go to [GW_BGP_NEIGHBOR_DOWN.md](GW_BGP_NEIGHBOR_DOWN.md). The three documented causes are an unreachable address, a far end that refuses the session, and a failed open exchange. |

### Category `giid`

| Severity | Message | First command | Action |
|---|---|---|---|
| Major | `DHCP address for interface [<name>] has not been resolved` | `show dhcp v4 detail` | Confirm the port is up in stage C of [SSR_CONSOLE_HEALTH_CHECK.md](SSR_CONSOLE_HEALTH_CHECK.md). Confirm the provider hands out a lease. Relearn with `release dhcp lease network-interface <name>`. |

### Category `platform`

Every alarm in this category is a resource limit. Each one fires at 90 percent and
clears at 80 percent. One command answers all four.

| Severity | Message | Trigger | Clears at | First command |
|---|---|---|---|---|
| Major | `flow table limit exceeded` | Above 90 percent | 80 percent or less | `show capacity` |
| Major | `fib table limit exceeded` | Above 90 percent | 80 percent or less | `show capacity` |
| Major | `action table limit exceeded` | Above 90 percent | 80 percent or less | `show capacity` |
| Major | `arp table limit exceeded` | Above 90 percent | 80 percent or less | `show capacity` |
| Critical | `Security Rekey failed for: <node>` | The cloud failed to deliver a new key. | No documented threshold. | `show security key-status` |

The flow table and the action table grow with the session count. A sudden rise
means a traffic event, so go to stage G of the console health check. The
forwarding table grows with the route count, and the vendor names a configuration
fault or a memory shortage as the cause.

### Category `process`

| Severity | Message | Trigger | First command | Action |
|---|---|---|---|---|
| Major | `Process has exited unexpectedly: <name>` | A process exited. The alarm clears when the process restarts. | `show system processes` | The router restarts a failed process by design. A single event that clears means the router recovered, and the vendor asks you to report it. A process that exits again and again needs a vendor case. |

### Category `system`

| Severity | Message | Trigger | Clears at | First command |
|---|---|---|---|---|
| Critical | `Node <name> went offline` | A node of a two-node router stopped. | Not stated. | `show system connectivity`, then `show system connectivity internal` |
| Critical | `system memory exceeded` | Above 90 percent | Below 80 percent | `show stats process memory rss` |
| Major | `Host cpu utilization exceeded` | Above 85 percent for 30 seconds | Below 70 percent | `show stats process cpu` |
| Major | `disk space low` | Less than 10 percent free | Not stated. | `show platform disk` |
| Major | `No connectivity to <router>.<node>` | A configured node is absent. | Not stated. | `show system connectivity` |
| Major | `Hostname [<name>] is unresolved` | A configured name did not resolve. | Not stated. | `show dns resolutions` |
| Major | `No active NTP server` | No time source is active. | Not stated. | `show ntp` |
| Major | `SNMP server failure` | The router cannot reach the trap receiver. | Not stated. | `ping egress-interface <name> <server-ip>` |
| Major | `Restart required` | A change needs a process restart. | Not stated. | `show config version` |
| Major | A configuration synchronization error. | The router cannot take the configuration. | Not stated. | `show config version` and `show config local-override` |
| Major | An entitlement certificate error. | The certificate is missing, corrupt, or invalid. | Not stated. | `show entitlement` |
| Minor | `Application Identification cache utilization is approaching maximum capacity` | 95 percent of the configured maximum | Below 85 percent | `show app-id cache-sizes` |

Warning: the `Restart required` alarm and the configuration synchronization alarm
both need a change through Mist. Do not restart the process from the shell on a
Mist-managed router. Raise the change to Tier 2.

Note: the vendor text for several of these alarms names a conductor command, such
as `show assets <id>`. Mist replaces the conductor, so that command does not run
here. Read the device state in the Mist portal instead. See §11 of
[SSR_CONSOLE_HEALTH_CHECK.md](SSR_CONSOLE_HEALTH_CHECK.md).

### Category `asset`

Every alarm in this category belongs to a conductor-managed deployment. A
Mist-managed router does not raise them. If you see one, the device is not
Mist-managed, and this index does not apply.

## 3. Mist gateway alarms

| Mist alarm key | Runbook | First command at the console |
|---|---|---|
| `gateway_down` | [GATEWAY_DOWN.md](GATEWAY_DOWN.md) | `show system`, then `show mist` |
| `gw_port_down` | [GW_PORT_DOWN.md](GW_PORT_DOWN.md) | `show device-interface` |
| `gw_bgp_neighbor_down` | [GW_BGP_NEIGHBOR_DOWN.md](GW_BGP_NEIGHBOR_DOWN.md) | `show bgp summary` |
| `gw_vpn_path_down` | [GW_VPN_PATH_DOWN.md](GW_VPN_PATH_DOWN.md) | `show peers detail` |
| `gw_vpn_peer_down` and `vpn_peer_down` | [GW_VPN_PEER_DOWN.md](GW_VPN_PEER_DOWN.md) | `show peers` |
| `bad_wan_uplink` | No dedicated runbook. Use stage C and stage D of [SSR_CONSOLE_HEALTH_CHECK.md](SSR_CONSOLE_HEALTH_CHECK.md). | `show device-interface <name> extended-statistics` |
| `intermittent_wan_connectivity` | No dedicated runbook. Use stage D and step E2 of [SSR_CONSOLE_HEALTH_CHECK.md](SSR_CONSOLE_HEALTH_CHECK.md). | `show peers detail` |

## 4. Choose the right document

| The ticket says | Go to |
|---|---|
| An alarm fired, and the alarm has a runbook. | The runbook in §3. |
| An alarm fired, and no runbook covers it. | §2 of this document, then the stage that it names. |
| The device is unreachable, and the console works. | [SSR_CONSOLE_HEALTH_CHECK.md](SSR_CONSOLE_HEALTH_CHECK.md), stage A. |
| A user reports that an application is slow or broken, and no alarm fired. | [SSR_APPLICATION_PERFORMANCE.md](SSR_APPLICATION_PERFORMANCE.md). |
| The case needs vendor evidence. | [SSR_EVIDENCE_CAPTURE.md](SSR_EVIDENCE_CAPTURE.md). |
| The fault followed a software change. | [SSR_FIRMWARE_HEALTH.md](SSR_FIRMWARE_HEALTH.md). |

## 5. Write a knowledge article from a row

Each row above holds the five fields that a knowledge article needs. Copy them in
this order.

1. **Trigger.** The message text and the threshold.
2. **Meaning.** One sentence that states what the router lost.
3. **First command.** One command, with the healthy output.
4. **Decision.** The unhealthy signature, and the branch that follows it.
5. **Closure.** The clear threshold, or the manual check when the vendor states no
   threshold.

Warning: never write a closure step that reads "confirm the alarm cleared" for an
alarm with a hysteresis threshold. State the real number. A flow table alarm
clears at 80 percent, not at 90 percent, so a ticket closed at 89 percent reopens.

## 6. Sources

| Source | Where |
|---|---|
| Session Smart Networking alarm guide | <https://docs.128technology.com/docs/events_alarms> |
| Session Smart Networking command line reference | <https://docs.128technology.com/docs/cli_reference> |
| Session Smart Networking statistics reference | <https://docs.128technology.com/docs/cli_stats_reference> |

Run `python scripts/fetch_ssr_docs.py` to build a local copy of every page above
under `documentation/references/ssr/`. That directory is not committed, because it
holds verbatim vendor text.

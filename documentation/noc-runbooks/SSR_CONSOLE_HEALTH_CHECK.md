# SSR_CONSOLE_HEALTH_CHECK

## 1. Overview

| Field | Value |
|---|---|
| **Document type** | Cross-alarm procedure. This document is not an alarm runbook. No Mist alarm key maps to it. |
| **Platform** | Any Mist-managed Juniper Session Smart Router. The steps are model agnostic. Two steps are platform dependent, and each one says so. |
| **Management model** | Mist-managed only. A conductor-managed router uses a different command set. See §11. |
| **Access method** | A local console session, or an out-of-band console server session. The steps do not need cloud reachability. |
| **Purpose** | Give a technician one ordered health check that proves whether the box is healthy, and that names the failure signature at each step. |
| **Audience** | Tier 1 and Tier 2 network operations. |

### What this document replaces

Each alarm runbook holds a short command list. That list states the command, but it
does not state the reason to run the command, and it does not state what a bad
output looks like. This document holds that detail one time. Each alarm runbook
points here.

### How to use the stages

The check runs in seven stages. Each stage answers one question. Run the stages in
order. Stop at the first stage that fails, and go to the action that the stage
names. Do not run all seven stages when stage A already found the fault.

| Stage | Question it answers |
|---|---|
| A | Does the router run, and does Mist manage it? |
| B | Does the platform have enough CPU, memory, disk, and cooling? |
| C | Do the physical ports and the logical interfaces work? |
| D | Can the router reach the next hop and the internet? |
| E | Do the SVR overlay peers work? |
| F | Does the routing plane hold the correct routes? |
| G | Do the sessions and the services work for users? |

## 2. Before you start

### Confirm that you reached the router, and not the conductor

The PCLI prompt states the user, the node, and the router.

```text
admin@node0.branch-router#
```

Read the prompt as `user@node.router`. A `#` character means that you hold
administrator rights. A `>` character means that you hold read-only rights, and
several commands in this document will fail.

### Two rules that apply to every command

1. Every `show` command accepts `router <name>` and `node <name>`. On a router
   console, the current router is the default. Omit both keywords unless the
   router runs two nodes.
2. A command that reports "This command can only be run on a Conductor" is not a
   defect. Mist replaces the conductor. See §11 for the full list.

### Capture the session

Turn on session logging in the terminal program before step A1. The evidence
matters more than the speed. If the box reboots during the check, the log holds
the only record of the state before the reboot.

## 3. Stage A. Does the router run, and does Mist manage it?

| Step | Command | Why you run it | Healthy output | Unhealthy signature and next action |
|---|---|---|---|---|
| A1 | `show system` | States the node status, the role, the software version, the uptime, and the active alarm count. This one command answers "is the box alive" faster than any other. | `Status: running`. The uptime matches the known service time. `Alarm Count: 0`. | `Status: starting` means the node still boots. Wait 5 minutes, then repeat. `Status: offline` means the configuration names a node that is not present. An uptime under 10 minutes means an unplanned reboot, so go to A5. A non-zero alarm count means go to A4. |
| A2 | `show system processes` | Lists every SSR process and its status. A single dead process explains a fault that looks like a hardware fault. | Every process reports `running`. | Any process that does not report `running` is the fault. Record the process name. Escalate to Tier 2. Do not restart a process without approval, because a restart destroys the evidence. |
| A3 | `show system services` | Lists the systemd services that sit outside the process manager. The web service and the plugin adapter live here. | Every service reports `active`. | A service that reports `failed` or `inactive` needs Tier 2. Record the service name. |
| A4 | `show alarms` | Lists every active alarm that the router raised about itself. The router names its own fault before you guess at it. | `There are 0 shelved alarms`, and no rows above that line. | Read the `Category` column. Map the category to the stage in §10, then go to that stage. Record the alarm identifier and the message text word for word. |
| A5 | `show events` | Shows the historical event record. This is the only way to learn what happened before the current state. | Events match the known work. No unexplained restart. | Narrow the window with `show events from 1d`. Narrow the type with `show events type system`. A configuration change appears as `admin.running_config_change`. A time correction appears as `system.ntp_adjustment`. |
| A6 | `show mist` | States the link between the router and the Mist cloud. Use it when Mist reports the device as disconnected but the console works. | The command reports a connected state. Add `detail` for the full record. | No connection means that the box is healthy and the management path is broken. Go to stage C and stage D. Do not treat the device as down. |
| A7 | `show system connectivity` | States the connection between the nodes of this router. It matters only on a two-node router. | Every row reports `connected`. | `disconnected` on a two-node router means that the pair lost its link. Check the high-availability interface in stage C. |
| A8 | `show system version detail` | States the exact build and the package version. Firmware mismatch explains many faults that look random. | The version matches the version that Mist reports for this device. | A mismatch between the console and Mist means that Mist holds stale data, or that a local override is in force. Go to A9. |
| A9 | `show config version` and `show config local-override` | The first states when the running configuration was committed. The second states whether someone froze local changes against the cloud. | The commit time matches a known change. Local override is disabled. | A commit time that matches the start of the fault points at a configuration change. Local override that is enabled means that Mist cannot push a repair. Tier 2 must clear the override. |

Warning: never run `restore config factory-default`, `restore system factory-default`,
or `delete sessions` during triage. Each one is service affecting, and the first
two are not reversible from the console.

## 4. Stage B. Does the platform have enough resources?

| Step | Command | Why you run it | Healthy output | Unhealthy signature and next action |
|---|---|---|---|---|
| B1 | `show platform` | Reports the CPU type, the core count, the memory, the disk, and the operating system in one view. Narrow it with `show platform cpu`, `show platform memory`, or `show platform disk`. | The core count and the memory match the model datasheet. The disk holds free space. | A full disk stops the logging and the statistics. Escalate to Tier 2 for a log cleanup. Never delete a file from the shell during triage. |
| B2 | `show capacity` | Reports the use of the five internal tables against their capacity. These tables hold the forwarding state, the flows, and the ARP entries. | Every `Usage` value stays well below 100 percent. | A table near 100 percent explains dropped traffic that no interface counter shows. The `flow-table` fills first under a denial-of-service condition. Record the table name and escalate. |
| B3 | `show system utilization session-processors` | Reports the CPU use of each thread that forwards packets. The overall CPU figure hides a single saturated thread. | The load spreads across the threads. No thread sits at 100 percent. | One thread at 100 percent while the others stay idle means a traffic polarization fault. Escalate to Tier 2 with the output. |
| B4 | `show chassis health` and `show chassis health details` | Reports the hardware health roll-up. | The command reports a healthy state. | Any fault state needs a hardware case. Record the detail output. |
| B5 | `show chassis temperature` and `show chassis power` | Reports the sensor readings and the power state. Heat causes a fault that looks like a software fault. | Every sensor sits inside its threshold. Compare against `show chassis temperature-thresholds`. | A reading above the threshold means a cooling fault. Check the intake, the exhaust, and the room. A power fault needs a hardware case. |
| B6 | `show chassis hardware` and `show chassis firmware` | Records the serial number and the firmware level for the hardware case. | The output matches the asset record. | A mismatch means that the asset record is wrong. Correct the record before the case. |

Caution: steps B4, B5, and B6 run on an SSR400 platform and an SSR440 platform
only. On any other model the command reports that it cannot run. That message is
not a fault. Skip the step, and read the temperature from the Mist device page
instead.

## 5. Stage C. Do the interfaces work?

| Step | Command | Why you run it | Healthy output | Unhealthy signature and next action |
|---|---|---|---|---|
| C1 | `show device-interface` | Reports the physical ports. This is the layer-one truth. Add `summary` for one line per port. | Each port that carries service reports an operational state of up. | A port that reports down is the fault. Check the cable, the transceiver, and the far-end port. The `interface operational down` alarm reports this same state. |
| C2 | `show device-interface <name> optics-statistics` | Reports the optical transmit and receive levels for a fiber port. A marginal optic causes loss that no other command shows. | The receive level sits inside the range that the transceiver datasheet states. | A receive level near the lower limit means a dirty connector, a bent fiber, or a failing optic. Clean the connector first, then replace the transceiver. |
| C3 | `show device-interface <name> extended-statistics` | Reports the error counters for the port. | The error counters hold at zero, or they do not grow between two runs. | A growing error counter means a physical fault. Repeat the command after 60 seconds to prove growth. A duplex mismatch and a bad cable both appear here. |
| C4 | `show network-interface` | Reports the logical interfaces, the addresses, the gateway, the VLAN, and the admin and operational status. This is the layer-three truth. | Each interface holds the expected address. `Admin Status` and `Oper Status` both report up. | An address of `--` on an interface that uses DHCP means no lease, so go to C6. An operational status of down with a physical port that is up means a configuration fault. |
| C5 | `show arp` and `show arp detail` | Reports the address resolution table. A gateway that does not resolve stops all traffic on that interface. | The gateway address appears with a `Valid` state. | A state of `Refresh` with a rising retry count means that the gateway does not answer. A missing gateway entry stops the forwarding on that interface. Check the far-end device. Clear one entry with `clear arp device-interface <name> ip <address>`. |
| C6 | `show dhcp v4` and `show dhcp v4 detail` | Reports the DHCP lease on each interface that learns its address. | `Dhcp State: Resolved`. The lease expiration time sits in the future. | Any other state means no address. The `giid` alarm reports this same condition. Confirm that the port is up, then confirm that the provider hands out a lease. Release and relearn with `release dhcp lease network-interface <name>`. |
| C7 | `show lte summary`, `show lte signal`, and `show lte sim` | Reports the cellular backup path. Run these steps only on a router that holds an LTE interface. | The registration status and the connection status both report a connected state. The signal rating is good. | A signal rating of marginal, poor, or zero means a radio fault or an antenna fault. A system mode that does not report LTE means a radio fault. A SIM that does not register means a carrier problem. |
| C8 | `show lldp-neighbors` | Reports the neighbor that each port sees. This proves the physical wiring without a site visit. | Each port reports the neighbor that the design names. | No neighbor on a port that should hold one means a wrong patch, a dead far-end port, or a far end that does not run the protocol. |
| C9 | `show network-interface redundancy` | Reports the state of an interface pair. Run this step only when the design uses interface redundancy. | The output matches the intended active and standby roles. | A pair that lost its partner runs with no protection. Repair it before the next maintenance window. |

## 6. Stage D. Can the router reach anything?

Warning: the `ping` command and the `service-ping` command are not the same test,
and they answer different questions. A technician who runs only one of them can
report a healthy router that carries no user traffic.

| Step | Command | Why you run it | Healthy output | Unhealthy signature and next action |
|---|---|---|---|---|
| D1 | `ping egress-interface <network-interface> <destination-ip>` | Sends an ICMP request out of a named interface. It bypasses the tenant policy and the service policy, so it tests the transport only. Name the interface, because a bare `ping` can leave through the wrong path and report a false failure. | Four replies. The round-trip time matches the transport type. | No reply to the local gateway means a layer-two fault, so return to C5. A reply from the gateway and no reply from the internet means an upstream fault. Open a case with the transport provider. |
| D2 | `ping set-df-bit size 1400 egress-interface <name> <destination-ip>` | Tests the path packet size. A path that drops a large packet breaks the overlay while a small ping still passes. | Replies at 1400 bytes. | Replies at 56 bytes and no reply at 1400 bytes means a path size fault. This breaks the SVR overlay and the applications, and it looks like a random fault. Record the largest size that passes, then escalate. |
| D3 | `service-ping service-name <service> tenant <tenant> source-ip <address> <destination-ip>` | Sends the request through the policy plane, as a user does. It proves that the tenant may reach the service. | Replies return. | A failure here with a success at D1 means a policy fault, not a transport fault. The router blocks the user. Go to stage G, then escalate to Tier 2 for the policy. |
| D4 | `traceroute <destination-ip>` | Shows each hop toward the target. It names the hop where the path stops. | The path reaches the target. Each hop answers. | The last hop that answers names the boundary of your control. A path that stops at the first upstream hop belongs to the provider. Add `egress-interface <name>` and `gateway-ip <address>` to bypass the service and the routing table. |
| D5 | `show ntp` | Reports the time source. Wrong time breaks the certificates, the logs, and the correlation between the console and Mist. | At least one source shows the `syspeer` tally code. The offset stays small. | No source means that the clock drifts. A certificate then fails, and the cloud link drops. Confirm that the router reaches the time source on UDP port 123. |
| D6 | `show dns resolutions` | Reports every hostname that the configuration needs, and whether the router resolved it. | Every row reports a resolved state, and holds an address. | An unresolved hostname stops the feature that uses it. Confirm the name server with `show network-interface`, then force a retry with `refresh dns resolutions`. |

## 7. Stage E. Do the SVR overlay peers work?

| Step | Command | Why you run it | Healthy output | Unhealthy signature and next action |
|---|---|---|---|---|
| E1 | `show peers` | Reports every SVR peer, the interface that reaches it, and the state. This is the overlay truth. | Each peer that the design names reports `up`. A designed standby path reports `standby`. | `down` on every path to one peer raises the `Peer is not reachable` alarm. `down` on one path of several raises the `Peer path is down` alarm. A branch that loses every peer path loses the data center. |
| E2 | `show peers detail` | Adds the latency, the jitter, the loss, the mean opinion score, and the uptime for each path. A path that reports up can still be unusable. | Loss at 0 percent. Latency and jitter match the transport type. | Loss at 5 percent or more marks a degraded path. A short uptime on a path that reports up means that the path flaps. Both conditions damage voice and video before any alarm fires. |
| E3 | `show bfd` and `show bfd peer <ip> detail` | Reports the protocol that decides whether a peer path is up. It explains why E1 reported down. | The session holds up. | A session that never comes up means that the far end never answers. Confirm that UDP port 1280 passes in both directions. A firewall in the path is the common cause. |
| E4 | `show udp-transform` | States whether the router rewrote the traffic to cross a stateful firewall, and states the test that triggered the rewrite. | The state matches the design. | An unexpected enabled state names a firewall in the path that the design did not plan. Record the reason text. |
| E5 | `show peers name <peer>` | Narrows every command above to one peer. Use it when one branch fails and the others work. | The single peer reports the expected state. | Compare the failing peer against a working peer on the same interface. A difference in the interface column isolates the transport. |

## 8. Stage F. Does the routing plane hold the correct routes?

| Step | Command | Why you run it | Healthy output | Unhealthy signature and next action |
|---|---|---|---|---|
| F1 | `show bgp summary` | Reports every BGP neighbor on one line, with the uptime and the prefix count. | Each neighbor holds a time value under `Up/Down`, and a prefix count under `State/PfxRcd`. | A word instead of a time value means that the session is not established. This raises the `Neighbor failed to reach the ESTABLISHED state` alarm. A prefix count of zero on an established session means a policy fault, not a session fault. |
| F2 | `show bgp neighbors <neighbor-ip>` | Reports the full state of one neighbor, and the reason that the session failed. | `BGP state = Established`. The hold time and the keepalive interval match the far end. | An `Active` state or an `Idle` state means that the far end does not answer, or that it rejects the connection. A mismatch in the address family stops the prefix exchange while the session stays up. |
| F3 | `show bgp neighbors <neighbor-ip> received-routes` and `... advertised-routes` | Separates a receive fault from a send fault. | The received list holds the data center prefixes. The advertised list holds the local prefixes. | An empty received list with an established session means that the far end filters the routes. An empty advertised list means that this router filters them. Name the direction before you escalate. |
| F4 | `show ospf neighbors` | Reports the interior routing neighbors. Run this step only when the design uses OSPF. | Each neighbor reports the `Full` state. | Any other state means that the adjacency did not form. A packet size mismatch and an area mismatch are the common causes. |
| F5 | `show rib` and `show rib summary` | Reports every route that the router learned, from every source. | The default route is present. The data center prefixes are present. | A missing default route stops the internet traffic. Narrow the source with `show rib bgp`, `show rib connected`, or `show rib static`. |
| F6 | `show fib <ip-prefix>` | Reports the forwarding table, which states where the traffic really goes. The routing table states intent. The forwarding table states behavior. | The prefix appears, with the expected tenant, the expected service, and the expected next hop. | A prefix in the routing table that is absent from the forwarding table means that the service policy blocks it. Always pass a prefix or a row limit, because the whole table is very large on a busy router. |
| F7 | `show fib lookup destination-ip <ip> destination-port <port> protocol <protocol>` | Answers one question directly. Where does this exact traffic go? | The lookup returns the expected service and the expected next hop. | An empty result means that no policy allows the traffic. This is the fastest proof that a user complaint is a policy fault. |
| F8 | `show vrf` | Reports each routing instance, with its tenants and its interfaces. Run this step only when the design uses more than one instance. | Each instance holds the interfaces that the design names. | A missing interface in an instance explains traffic that reaches the router and goes nowhere. |

## 9. Stage G. Do the sessions and the services work?

| Step | Command | Why you run it | Healthy output | Unhealthy signature and next action |
|---|---|---|---|---|
| G1 | `show service-path` | Reports every service, and the path that its traffic takes. This is the single best command for an application complaint. | Each service reports a state of `Up`. | A state of `Down` names the service that fails, and the reason appears beside the next hop. Add `detail` for the latency, the loss, and the jitter for each traffic class. |
| G2 | `show sessions rows 20` | Reports the active sessions. Always pass a row limit, because the full table can hold many thousands of rows. | Sessions appear for the services that users report. Each session holds a forward row and a reverse row. | A forward row with no reverse row means that the return traffic does not arrive. That is an upstream fault or a firewall fault, not a router fault. |
| G3 | `show sessions top bandwidth` | Reports the ten largest consumers. | The list matches the expected business traffic. | One unexpected session that holds most of the link explains a slow site. Record the source address, the destination address, and the tenant. |
| G4 | `show top sources` | Reports the largest consumers by source address over the last 30 minutes. | The list matches the expected users. | A single internal address that dominates the list points at a compromised host or a runaway backup. |
| G5 | `show tenant members` | Reports how the router maps a source address to a tenant. A user who lands in the wrong tenant receives the wrong policy. | Each prefix maps to the intended tenant. | A user whose address falls in an unexpected row receives the wrong policy. This explains a fault that affects one user and no other user. |
| G6 | `show application names` | Reports the applications that the router identified. | The business applications appear, and they hold a session count. | An application that never appears means that the identification failed. The policy that names the application then never matches. |
| G7 | `show entitlement` | Reports the bandwidth that the license covers against the bandwidth in use. | The use stays inside the entitlement. | Use above the entitlement is a commercial issue, not a fault. Report it to the account team. |

## 10. Map an alarm to a stage

Start at the stage that the alarm names. Run stage A first in every case, because
stage A takes under one minute and it names the fault in many cases.

### Alarms that the router raises about itself

| SSR alarm category | Message pattern | Start at |
|---|---|---|
| `asset` | A version mismatch, a duplicate identifier, or a node that does not run. | Stage A, steps A1, A2, and A8. |
| `bgp_neighbor` | A neighbor failed to reach the established state. | Stage F, steps F1 and F2. |
| `giid` | A DHCP address is not resolved. | Stage C, steps C4 and C6. |
| `interface` | An interface is operationally down, or administratively down. | Stage C, steps C1, C2, and C3. |
| `peer` | A peer is not reachable, a peer path is down, or the path size is unresolvable. | Stage E, steps E1, E2, and E3. For the size case go to D2. |
| `platform` | A security rekey failed, or a hardware condition. | Stage A, step A4. Then stage B. |
| `process` | A process condition. | Stage A, step A2. |
| `system` | A resource condition or a service condition. | Stage B, then stage A, step A3. |

### Mist gateway alarms

| Mist alarm key | Start at | Note |
|---|---|---|
| `gateway_down` | Stage A, steps A1 and A6. | If the console works, the box is not down. The management path is down. Go to stage C and stage D. |
| `gw_port_down` | Stage C, steps C1, C2, and C3. | Prove the physical layer before you touch the configuration. |
| `gw_bgp_neighbor_down` | Stage F, steps F1, F2, and F3. | Prove the transport in stage D first when every neighbor fails at once. |
| `gw_vpn_path_down` | Stage E, steps E1, E2, and E3. | One path down leaves the peer up. Confirm the peer state before you page. |
| `gw_vpn_peer_down` and `vpn_peer_down` | Stage E, step E1. Then stage D. | Every path to one peer is down. The transport is the usual cause. |
| `bad_wan_uplink` | Stage C, then stage D. | Run D2 as well, because a path size fault often hides here. |
| `intermittent_wan_connectivity` | Stage D, then stage E, step E2. | Read the uptime column in E2. A short uptime proves a flap. |

## 11. Commands that do not exist on a Mist-managed router

Jacob Skidmore reported that several commands in the current runbooks do not run.
That report is correct. This section names each one, and gives the command that
works. Every replacement comes from the Session Smart Networking command line
reference. See §13.

### Commands that no SSR release accepts

| Command in the old text | What happens | Use this instead |
|---|---|---|
| `show system connected` | The PCLI rejects it. | `show system connectivity` for the link between the nodes. `show mist` for the link to the cloud. |
| `show route` | The PCLI rejects it. This is Junos syntax. | `show rib` for the routes that the router learned. `show fib` for the forwarding decision. |
| `show bgp neighbor <ip>` | The PCLI rejects the singular form. | `show bgp neighbors <ip>`. The keyword is plural. |
| `show sessions summary` | The PCLI rejects it. No `summary` subcommand exists. | `show sessions rows 20` for the table. `show sessions top bandwidth` for the largest consumers. |
| `show events filter type <type>` | The PCLI rejects the `filter` keyword. | `show events type <type>`. |
| `ping <target> source <ip>` | The `ping` command holds no `source` keyword. | `ping egress-interface <name> <target>` to choose the path. `service-ping source-ip <ip> <target>` to test as a user. |

Warning: the difference between `ping` and `service-ping` is not cosmetic. The
`ping` command bypasses the policy plane. A successful `ping` therefore proves the
transport, and it proves nothing about the user experience. Run both commands
before you report that the router is healthy.

### Commands that exist, but only on a conductor

Mist replaces the conductor. These commands report that they cannot run here. That
message is correct behavior, and it is not a fault.

`connect`, `migrate`, `send command` and every one of its subcommands,
`show assets`, `show assets summary`, `show assets errors`,
`show assets software`, `show assets upgrade-required`, `show config out-of-sync`,
`show config locally-modified`, `show dynamic-peer-update`, `show peers hostnames`,
`show plugins available`, `show plugins installed`, `show plugins categories`,
`show step-repo clients`, and `show secure-conductor-onboarding`.

Perform the equal action in the Mist portal instead. Use `WAN Edges` for the
inventory, and use `Utilities` for an action against one device.

## 12. Capture the evidence before you escalate

Run these three steps before you hand the case to Tier 2 or to the vendor. A case
without evidence returns to you.

| Step | Command | What it gives the next engineer |
|---|---|---|
| 1 | `write log message "NOC ticket <number> triage start"` | Puts a marker in the log file. Every later log line belongs to your session. |
| 2 | `save tech-support-info` | Packages the statistics, the logs, and the diagnostic data into one archive. The command prints the file path when it finishes. |
| 3 | `show alarms` and `show events from 1d` | Gives the alarm state and the day of history in plain text, so the case holds it without an archive. |

Caution: `save tech-support-info` collects a large amount of data, and it takes
time to finish. Start it, then continue the triage while it runs. Narrow the range
with `save tech-support-info since 4h` when the fault is recent.

To capture live traffic, use `create session-capture`. Set a packet count and a
session count, because the capture writes to the local disk. Remove the capture
with `delete session-capture` when the test ends.

## 13. Mist portal equivalents

A technician who holds no console access reaches most of stage D, stage E, and
stage F from the portal. Mist runs the PCLI for you and returns the output.

| Task | Navigation |
|---|---|
| Open the tools | `WAN Edges`, then select the device, then `Utilities`, then `Testing Tools`. |
| Reachability | The `Ping` tab. Enter the address, the port name, the count, and the size. |
| Path to a target | The `Traceroute` tool in the same menu. |
| BGP state | The `BGP` tab, then `Summary`, then `Show Summary`. |
| Overlay service paths | The `Applications` tab. Select the application, then `Show Path`. |
| Address resolution | The `ARP` tab, then `Table`, then `Show ARP`. Use `Refresh ARP` to clear an entry. |
| Forwarding decision | The `FIB` tab. Use `FIB Lookup` for one flow, or `FIB By Application` for one application. |
| Interior routing | The `OSPF` tab. It holds the summary, the interfaces, the neighbors, the database, and the routes. |
| Device health and ports | `WAN Edges`, then select the device. Hover over each port and each status icon. |
| Event history | `WAN Edges`, then select the device, then `WAN Edge Insights`. Read the `Gateway Events` pane. |
| Service level metrics | `Monitor`, then `Service Levels`, then select the site, then `WAN`. |
| Alerts and email delivery | `Monitor`, then `Alerts`, then `Alerts Configuration`. |
| Suggested repairs | `Marvis`, then `Marvis Actions`. |
| Overlay advertisement | `Organization`, then `WAN`, then `Networks`. Confirm `Advertise to the Overlay`. |

Note: the service level metrics need about one week of data before they carry
meaning. Immediately after an installation they stay empty. That is expected, and
it is not a fault.

## 14. Sources

Every command in this document appears in one of these sources.

| Source | Where |
|---|---|
| Session Smart Networking command line reference | <https://docs.128technology.com/docs/cli_reference> |
| Session Smart Networking statistics reference | <https://docs.128technology.com/docs/cli_stats_reference> |
| Session Smart Networking alarm guide | <https://docs.128technology.com/docs/events_alarms> |
| Session Smart Networking application troubleshooting | <https://docs.128technology.com/docs/ts_applications> |
| About the PCLI | <https://docs.128technology.com/docs/concepts_pcli> |
| Juniper Mist WAN Assurance documentation | <https://www.juniper.net/documentation/us/en/software/mist/mist-wan/mist-wan.pdf> |
| WAN Edge with the Session Smart Router validated design | <https://www.juniper.net/documentation/us/en/software/jvd/jvd-wan-edge-for-ssr/jvd-wan-edge-for-ssr.pdf> |
| Juniper Mist AIOps documentation | <https://www.juniper.net/documentation/us/en/software/mist/mist-aiops/mist-aiops.pdf> |

Run `python scripts/fetch_ssr_docs.py` to build a local copy of every page above
under `documentation/references/ssr/`. Use `python scripts/pdf_to_markdown.py` on
a downloaded PDF. Neither output is committed, because both hold verbatim vendor
text. Confirm a command against the local copy when you have no network access.

## 15. Escalation

Follow the ladder in [Shared Appendix §8](_shared_common.md).

1. **Tier 1.** Run stage A through stage D. Record the output. Clear a fault that
   the runbook names.
2. **Tier 2.** Run stage E through stage G. Own a configuration change, a policy
   change, and a hardware replacement.
3. **Juniper support.** Attach the archive from §12. State the stage that failed,
   and state the exact command output.

State the stage identifier in the escalation note. The next engineer then starts
where you stopped, instead of starting again at stage A.

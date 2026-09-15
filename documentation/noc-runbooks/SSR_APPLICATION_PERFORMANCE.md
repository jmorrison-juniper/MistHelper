# SSR_APPLICATION_PERFORMANCE

## 1. Overview

| Field | Value |
|---|---|
| **Document type** | Cross-alarm procedure. No Mist alarm key maps to it. Most of these tickets arrive from a user, not from an alarm. |
| **Platform** | Any Mist-managed Juniper Session Smart Router. The steps are model agnostic. |
| **Purpose** | Turn a vague user complaint into a named fault, in a fixed number of steps. |
| **Audience** | Tier 1 and Tier 2 network operations. |
| **Typical ticket text** | "The application is slow." "Voice breaks up." "The site loads for me but not for him." "It worked yesterday." |

### Why this document exists

An alarm names its own fault. A user complaint does not. A technician who starts
at the interface counters on a complaint ticket wastes 20 minutes, because the
transport is healthy in most of these cases.

The router makes a per-application decision for each session. The fault therefore
sits at one of six decision points. This document walks the six points in the
order that the router uses.

### The six decision points

| Step | Question | The router's own term |
|---|---|---|
| 1 | Which application? | The service |
| 2 | Who asked? | The tenant |
| 3 | Which service did the traffic match? | The forwarding entry |
| 4 | Which path did the router pick? | The service path |
| 5 | Is that path healthy? | The peer path |
| 6 | Did a session really form? | The session |

Warning: do not skip a step. Step 3 answers most "it works for me and not for
him" tickets, and no interface command reaches that answer.

## 2. Before you start

Collect four facts from the user. Without them the steps below have no input.

| Fact | Why you need it |
|---|---|
| The source address of the affected client | Step 2 needs it. Without it you cannot find the tenant. |
| The destination address, the port, and the protocol | Step 3 needs all three. A service match uses all three. |
| The time that the fault started | Step 6 and the event history need it. |
| Whether one user or every user is affected | One user points at the tenant map. Every user points at the path. |

If the user cannot name the destination, run `show sessions rows 50` while the
user reproduces the fault, then read the destination from the table.

## 3. Step 1. Which application does the router see?

| Command | Why you run it | Healthy output | Unhealthy signature and next action |
|---|---|---|---|
| `show application names` | Lists every application that the router identified, with a session count and a discovery time. | The application that the user named appears, and it holds a session count above zero. | An absent application means that the identification failed. Any policy that names that application then never matches, and the traffic falls through to a default. Go to step 3 and read the real match. |
| `show app-id cache-sizes` | Reports the identification cache against its configured limit. | The current size sits well below the maximum. | A size near the maximum raises the minor `Application Identification cache utilization` alarm. The router then reduces the detail of its per-client statistics. Raise the limit through Tier 2. |
| `show domain-names most-recent` | Lists the domain names that recent sessions used. | The expected domain appears. | A missing domain means that the traffic never reached the router, or that it used an address with no name. |

## 4. Step 2. Which tenant does the client land in?

The router maps a source address to a tenant. The tenant decides the policy. A
client in the wrong tenant receives the wrong policy, and only that client fails.

| Command | Why you run it | Healthy output | Unhealthy signature and next action |
|---|---|---|---|
| `show tenant members` | Prints the source lookup table. It states the prefix that each tenant owns, for each interface and VLAN. | The user's address falls inside a prefix that maps to the intended tenant. | A match against a wider prefix than you expect means that the user inherits a different policy. This is the single most common cause of a one-user fault. Record the row, and escalate the tenant map to Tier 2. |

Read the table from the most specific prefix to the least specific prefix. A
address that matches both a `/32` row and a `/24` row uses the `/32` row.

The Mist portal shows the same table. Open the device, then the routing detail,
then the `Source Tenant` tab.

## 5. Step 3. Which service did the traffic match?

| Command | Why you run it | Healthy output | Unhealthy signature and next action |
|---|---|---|---|
| `show fib lookup destination-ip <ip> destination-port <port> protocol <protocol> tenant <tenant>` | Answers the question directly. It states the service that this exact traffic matches, and the next hop. | The lookup returns the intended service and a next hop. | An empty result means that no policy allows the traffic. That is a configuration fault, and no amount of transport work will fix it. A result that names a different service than you expect means that a wider entry won the match. |
| `show fib <ip-prefix>` | Shows every forwarding entry for a prefix, across every tenant. | The prefix appears once for each tenant that may reach it. | The absence of a tenant row proves that the tenant has no access. Always pass a prefix. The full table holds many thousands of rows. |
| `show service` | Lists the active services, with a summary or a detail view. | The service appears. | An absent service means that the configuration never created it, or that it applies to another router. |

Warning: never run `show fib` with no prefix and no row limit on a busy router.
The vendor documents that the output is very large, and the session can appear to
hang.

## 6. Step 4. Which path did the router pick?

The answer depends on the traffic type. Read the `Type` column from
`show service-path` to decide which branch applies.

| Command | Why you run it | Healthy output | Unhealthy signature and next action |
|---|---|---|---|
| `show service-path service-name <service>` | Lists every path for one service, with the type, the destination, the next hop, the interface, the vector, the cost, and the state. | The service reports `Up`, and the next hop matches the design. | A state of `Down` names the failed path. The reason appears beside the next hop, such as an unresolved gateway address. |
| `show service-path service-name <service> detail` | Adds the latency, the loss, and the jitter for each traffic class, and it names the class that breached its limit. | Every class sits inside its limit. | The output states the breach in plain text, such as an entry that exceeds a maximum latency. That line names the fault, and no further guessing is needed. |
| `show load-balancer service <service>` | States why the router chose one destination over another, when the service uses a service route. | The chosen agent matches the intended primary. | A choice that falls to a secondary agent means that the primary failed its check. This command exists for exactly this question. |
| `show rib <prefix>` | States the route for traffic that the router forwards natively, with no service route. | The route is present, with the expected next hop. | A missing route sends the traffic to the default route, or nowhere. |

## 7. Step 5. Is the chosen path healthy?

| Command | Why you run it | Healthy output | Unhealthy signature and next action |
|---|---|---|---|
| `show peers detail` | Reports the loss, the latency, the jitter, the mean opinion score, and the uptime for every overlay path. | Loss at 0 percent. The uptime matches the last known change. | Loss at 5 percent or more marks a degraded path. A short uptime on a path that reports up proves a flap. Both conditions break voice long before any alarm fires. |
| `show stats bfd by-peer-path latency` | Reports the measured latency for each path, from the protocol that watches the path. | The value matches the transport type. | A rise that matches the complaint time confirms a transport fault. Open a case with the transport provider, and quote the figure. |
| `show stats bfd by-peer-path jitter` | Reports the measured jitter for each path. | A low and steady value. | High jitter breaks voice and video while data still works. This explains a complaint that names only the phones. |
| `show stats bfd by-peer-path async received miss` | Counts the path-watch packets that did not arrive in time. | The count does not grow between two runs. | A growing count proves loss on the path, even when the interface counters stay clean. |
| `show device-interface <name> summary` | Confirms that the transport port is up. | The port reports up. | A port that is down moves the ticket to [GW_PORT_DOWN.md](GW_PORT_DOWN.md). |

### When every path is healthy but the application is still slow

Two conditions produce that result. Check both.

| Command | Why you run it | Unhealthy signature and next action |
|---|---|---|
| `show stats traffic-eng device-interface per-traffic-class` | Reports the queue behavior for each traffic class. | A growing count of packets that exceeded the buffer, or that failed to schedule, means that a class is overwhelmed. The link is full for that class even though the total use looks low. |
| `show stats packet-processing fragmentation` | Reports packet fragmentation. Run it twice, and compare. | A growing count means that the path breaks large packets. Confirm with `ping set-df-bit size 1400 egress-interface <name> <target>`. This produces slow transfers and failed uploads while a small test passes. |

## 8. Step 6. Did a session really form?

| Command | Why you run it | Healthy output | Unhealthy signature and next action |
|---|---|---|---|
| `service-ping service-name <service> tenant <tenant> source-ip <client-ip> <destination-ip>` | Drives the whole data path as the user does, and creates a real session. This is the only test that proves the user experience from the console. | Replies return. | A failure here with a successful `ping` in stage D of the console health check proves a policy fault, not a transport fault. |
| `show sessions rows 50` | Shows the live sessions. Run it while the user reproduces the fault. | The session appears with a forward row and a reverse row. | A forward row with no reverse row means that the return traffic never arrived. Look upstream, not at this router. |
| `show sessions by-id <session-id>` | Shows one session in full, including the state, the packet counts in each direction, and the address translation. | Both directions count packets. The state reports established. | A forward packet count that grows with a reverse count that stays at zero confirms one-way traffic. Record the session identifier. |

The session identifier follows the traffic to the next router in the overlay. Give
that identifier to the engineer who holds the far end, and both sides can trace
the same flow.

Note: a session created by `service-ping` expires about five seconds after the
last request. Run `show sessions` in a second window, or run it at once.

## 9. Decision summary

| The evidence | The conclusion | Who owns it |
|---|---|---|
| `show tenant members` maps the user to an unexpected tenant. | A policy fault that affects one user or one subnet. | Tier 2 configuration. |
| `show fib lookup` returns nothing. | No policy permits the traffic. | Tier 2 configuration. |
| `show service-path detail` names a class that breached its limit. | A transport quality fault. | The transport provider. |
| `show peers detail` reports loss at 5 percent or more. | A transport quality fault. | The transport provider. |
| The fragmentation count grows, and a 1400-byte test fails. | A path size fault. | The transport provider, then Tier 2 for the size setting. |
| A traffic engineering class drops packets. | The link is full for that class. | Capacity planning, or a policy change. |
| A forward session exists with no reverse session. | The return traffic fails upstream. | The far end, or the destination owner. |
| `ping` succeeds and `service-ping` fails. | A policy fault, not a transport fault. | Tier 2 configuration. |

## 10. Mist portal equivalents

A technician without console access reaches most of this document from the portal.

| Step | Navigation |
|---|---|
| Step 1, the applications | Open the device, then `WAN Edge Insights`, then the `Applications` pane. |
| Step 2, the tenant | Open the device, then the routing detail, then the `Source Tenant` tab. |
| Step 3, the service match | `WAN Edges`, then the device, then `Utilities`, then `Testing Tools`, then the `FIB` tab. Use `FIB Lookup`. |
| Step 4, the path | The same `Testing Tools` menu, then the `Applications` tab, then Show Path. |
| Step 5, the path quality | `Monitor`, then `Service Levels`, then the site, then `WAN`. Read `WAN Link Health` and `Application Health`. |
| Step 6, the session test | The `Ping` tab in `Testing Tools`. |
| Suggested repairs | `Marvis`, then `Marvis Actions`. A size mismatch appears here by name. |

Note: the service level metrics need about one week of data before they carry
meaning. Immediately after an installation they stay empty, and that is expected.

## 11. Closure criteria

- The user confirms that the application works.
- `show service-path service-name <service>` reports `Up`.
- `show peers detail` reports loss under 5 percent on the path that carries the
  service.
- `service-ping` succeeds for the affected tenant and the affected service.
- The ticket records which of the eight conclusions in §9 applied.

Warning: never close this ticket on a successful `ping` alone. A `ping` bypasses
the policy plane, so it can pass while every user still fails.

## 12. Sources

| Source | Where |
|---|---|
| Session Smart Networking application troubleshooting | <https://docs.128technology.com/docs/ts_applications> |
| Session Smart Networking command line reference | <https://docs.128technology.com/docs/cli_reference> |
| Session Smart Networking statistics reference | <https://docs.128technology.com/docs/cli_stats_reference> |
| Juniper Mist WAN Assurance documentation | <https://www.juniper.net/documentation/us/en/software/mist/mist-wan/mist-wan.pdf> |

Run `python scripts/fetch_ssr_docs.py` to build a local copy of every page above
under `documentation/references/ssr/`. That directory is not committed, because it
holds verbatim vendor text.

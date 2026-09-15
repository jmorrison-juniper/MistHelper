# SSR_EVIDENCE_CAPTURE

## 1. Overview

| Field | Value |
|---|---|
| **Document type** | Cross-alarm procedure. No Mist alarm key maps to it. |
| **Platform** | Any Mist-managed Juniper Session Smart Router. The steps are model agnostic. |
| **Purpose** | Capture the evidence that a Tier 2 engineer or a vendor engineer needs, without harming the running service. |
| **Audience** | Tier 1 and Tier 2 network operations. |

### Why the order matters

A case without evidence returns to the technician who raised it. A case with the
wrong evidence wastes a day. Collect in this order, because each step costs more
than the one above it.

| Tier | Cost | What it gives |
|---|---|---|
| 1 | None. Read only. | The state and the history. Collect this always. |
| 2 | Low. Writes to the local disk. | The support archive. Collect this for any vendor case. |
| 3 | Medium. Writes packets to the local disk. | A packet capture. Collect this only when tier 1 and tier 2 did not explain the fault. |
| 4 | High. Changes the running behavior. | A raised log level. Collect this only with Tier 2 approval. |

Warning: tier 3 and tier 4 both consume disk space on a live router. A full disk
stops the logging and the statistics, and it raises the `disk space low` alarm.
Always remove a capture and restore a log level when the test ends.

## 2. Mark the session before you start

Put a marker in the log. Every later line then belongs to your work, and the next
engineer can find the start of the incident in one search.

```text
write log message "NOC ticket 12345 triage start"
```

The message appears in the log with the category `USER`. Quote a message that
holds a space.

Optional. Rotate the logs first when the fault is reproducible. A rotation closes
the current file and opens an empty one, so the new file holds only your test.

```text
rotate log
```

Warning: a rotation discards the oldest stored file for each process. Do not
rotate when the fault already happened and you still need the history. Rotate
only before you reproduce a fault on purpose.

## 3. Tier 1. Read the state and the history

Run every command in this table. Paste the output into the ticket as plain text.
An archive is not a substitute, because a reader cannot search it quickly.

| Command | What it proves |
|---|---|
| `show system` | The node state, the role, the version, the uptime, and the alarm count. |
| `show alarms` | Every fault that the router currently reports about itself. |
| `show events from 1d` | The day of history that led to the current state. |
| `show events type admin` | Every change that a person or the cloud made. |
| `show events type alarm` | Every alarm that raised and cleared, with a time for each one. |
| `show config version` | When the running configuration last changed. |
| `show system version detail` | The exact build, so the vendor can match it to a defect. |
| `show history` | The commands that ran in this session, in order. |

Narrow a wide result rather than paging through it.

| Goal | Command |
|---|---|
| Only the last four hours | `show events from 4h` |
| Only configuration changes | `show events type admin.running_config_change` |
| Only time corrections | `show events type system.ntp_adjustment` |
| A fixed number of rows | `show events rows 100` |

## 4. Tier 2. Collect the support archive

One command packages the statistics, the logs, and the diagnostic data. The
command prints the file path when it finishes.

```text
save tech-support-info
```

| Goal | Command |
|---|---|
| Only the last four hours of logs | `save tech-support-info since 4h` |
| Only the last hour of logs | `save tech-support-info since 45m` |
| Name the file for the ticket | `save tech-support-info NOC12345` |
| Use a named collection profile | `save tech-support-info manifest <name>` |

Caution: the command collects a large amount of data, and it takes time to
finish. Start it, then continue the triage while it runs. The default range is one
day. Narrow the range with `since` when the fault is recent, because a narrow
archive uploads faster and reads faster.

Two smaller collections answer a specific vendor request. Run them only when the
vendor asks.

| Command | What it collects |
|---|---|
| `save runtime-stats <filename>` | The runtime statistics of each process. |
| `save packet-buffer-snapshot` | The state of the packet buffer pool. |

## 5. Tier 3. Capture packets

Two tools exist. They answer different questions. Choose one.

| Tool | Use it when | What it captures |
|---|---|---|
| A session capture | You know the service, and you want the traffic of that service. | The packets of the matched sessions, on both sides of the router. |
| A capture filter | You know the port, and you want everything on that port. | The packets that match a filter on one device interface. |

### Capture the traffic of one service

```text
create session-capture service <service> router <router> node <node> source-ip <ip> destination-ip <ip> session-count 10 packet-count 100
```

Always set `session-count` and `packet-count`. The default packet count is 100 in
each direction for each session. The default session count is unlimited, and an
unlimited capture on a busy service fills the disk.

| Goal | Argument |
|---|---|
| Match one client | `source-ip <address>` |
| Match one destination | `destination-ip <address>` |
| Match one protocol | `protocol tcp` |
| Keep the capture on one node | `local-only` |
| Name the files for the ticket | `tag NOC12345` |

Confirm, then remove.

```text
show session-captures
delete session-capture by-id service <service> router <router> node <node> <capture-id>
```

### Capture everything on one port

```text
create capture-filter device-interface <name> router <router> node <node> "host 10.1.2.3"
```

The filter uses the same syntax as a packet analyzer. Confirm it, then remove it.

```text
show capture-filters
delete capture-filter device-interface <name> router <router> node <node> "host 10.1.2.3"
```

Warning: a capture filter with no address matches every packet on the port. On a
transport port that fills the disk in minutes. Always name a host, a port, or a
protocol in the filter.

Warning: a capture that you create at the console does not disappear on its own.
Remove it in the same session that created it. A forgotten capture fills the disk
days later, and the fault then looks unrelated to your work.

### Capture from the Mist portal instead

The portal builds the filter for you, and it stores the result in the cloud. Open
the device, then `Utilities`. The portal offers a filter builder, and it accepts a
manual edit of the filter text. Prefer the portal when the router is reachable,
because the portal removes the capture for you.

## 6. Tier 4. Raise the log level

Warning: a raised log level changes the running behavior. A system-wide `debug`
level or `trace` level costs processing time and disk space on a live router. Get
Tier 2 approval first. Never leave a raised level in place.

Raise one category, not the whole system.

```text
set log level debug category RTG
```

| Category | Covers |
|---|---|
| `RTG` | The routing engine. |
| `RIB` | Changes to the route table. |
| `LINK` | The link detection between the nodes. |
| `DISC` | Address discovery. This covers DHCP and address resolution. |
| `SESS` | Session setup. |
| `FLPP` | The processing of the first packet of each session. |
| `DNS` | Name resolution. |
| `PLAT` | The underlying platform. |
| `CFGD` | The configuration engine. |
| `PCLI` | The command line itself. |

The levels run from least detail to most detail: `fatal`, `error`, `warning`,
`info`, `debug`, and `trace`. The vendor recommends `info` for normal operation.

Restore the configured level the moment the test ends.

```text
set log level configured
```

Confirm the restore before you close the session. A router left at `trace` fills
its disk within hours.

## 7. Hand the case over

State these six items in the escalation note. A case that holds all six moves
forward without a return trip.

1. The ticket number, and the marker text that you wrote in §2.
2. The stage or the step that failed, from
   [SSR_CONSOLE_HEALTH_CHECK.md](SSR_CONSOLE_HEALTH_CHECK.md) or
   [SSR_APPLICATION_PERFORMANCE.md](SSR_APPLICATION_PERFORMANCE.md).
3. The exact command output that shows the fault. Paste it as text.
4. The archive path that `save tech-support-info` printed.
5. The capture identifier, when you took one, and confirmation that you removed it.
6. The log level that you set, and confirmation that you restored it.

## 8. Clean up

Run this check before you leave the session. Each line must return an empty
result.

| Command | Expected result |
|---|---|
| `show session-captures` | No active capture. |
| `show capture-filters` | No filter that you created. A filter that the configuration owns may remain. |
| `show alarms` | No `disk space low` alarm that your work created. |

Warning: never delete a file from the shell to recover disk space on a live
router. Raise the space problem to Tier 2. A deleted log file destroys the
evidence that the case needs.

## 9. Sources

| Source | Where |
|---|---|
| Session Smart Networking command line reference | <https://docs.128technology.com/docs/cli_reference> |
| Session Smart Networking application troubleshooting | <https://docs.128technology.com/docs/ts_applications> |
| Juniper Mist WAN Assurance documentation | <https://www.juniper.net/documentation/us/en/software/mist/mist-wan/mist-wan.pdf> |

Run `python scripts/fetch_ssr_docs.py` to build a local copy of every page above
under `documentation/references/ssr/`. That directory is not committed, because it
holds verbatim vendor text.

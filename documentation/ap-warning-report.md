# AP warning report

Menu **307** exports APs with reported warning or error codes for one selected organization.
The operation reads cloud data only.
It does not change an AP, a site, or an organization.

## Run the report

Select menu 307, then select the organization if the tool requests one.
Use the standard export format selection.
The portal lists the operation under **AP Warning Reports**.

The report reads every organization site and AP inventory page.
It then reads AP statistics separately for each site, including connected and disconnected APs.
The report selects nonzero `last_trouble` codes from the last 15 minutes, including the exact boundary.
It also retains nonzero codes without observation times because their age is unknown.
An AP with an older or future timestamp does not qualify.
Unassigned APs do not qualify because site statistics do not cover them.

## Interpret the evidence

The code comes from `last_trouble` in site AP statistics.
This field records the latest trouble observation.
The 15-minute window limits old observations, but it does not prove that a fault remains active.
Review `trouble_timestamp` and `connection_status` before you use the report for an incident.
The `reported_at` column records report creation, not the start of the trouble.
Both timestamps use UTC.
An absent observation time remains empty.

### Recovery evidence

The report reads fresh device statistics and the previous 60 minutes of events for candidate APs only.
Each history read uses at most ten pages and the configured API page limit.
The live event catalogue must confirm `AP_CONNECTED` and `AP_DISCONNECTED`.
Only validated cloud-connectivity codes `02` through `08` and `12` through `16` can qualify for recovery.
A successful cloud connection does not clear unrelated firmware or management-tunnel trouble.

The report excludes a recovered warning only when all these conditions hold.

1. Complete history shows a cloud connection strictly after the trouble timestamp.
2. Fresh statistics confirm the same AP and site, with connected state.
3. `last_seen` is no more than 300 seconds old and is not before the reconnect.
4. No newer trouble, disconnection, configuration failure, restart, or assignment removal follows the reconnect.
5. Fewer than three distinct disconnection state transitions occur in the previous 60 minutes.

Equal trouble and reconnect timestamps do not prove recovery.
No ten-minute delay or AP uptime measurement determines recovery.
Duplicate events and consecutive disconnection notifications without an intervening connection count as one interruption.
Three interruptions keep the warning visible even when the AP reconnects.
Unknown codes, non-connectivity codes, and incomplete evidence remain visible.
Failed or truncated history cannot prove recovery.

`recovery_status` is `retained`, `repeated`, or `recovered`.
`recovery_reason` and `evidence_status` explain each decision.
`interruptions_60m` counts observed transitions. With incomplete history, this count is only a lower bound.
`history_start` and `history_end` give the exact UTC evidence window for that AP.
`statistics_observed_at` records the returned `last_seen`, not the request time.
The fresh connection and trouble columns preserve the later snapshot separately from the original candidate.

The report reads the live AP LED definitions through `listApLedDefinition`.
Known codes include their key, name, and description.
Unknown nonzero codes remain in the report with `definition_status=unknown`.
The report never invents their meaning.

Site names accompany site identifiers.
`site_lookup_status` distinguishes found sites, missing sites, and unassigned APs.
`connection_status` distinguishes connected, disconnected, and unknown states.
The log gives inventory AP, site-statistics AP, missing-code, excluded-code, and matched AP counts.
Missing evidence does not establish that an AP is healthy.

## Output and failure behavior

The filename is `ApWarningReport_<organization UUID>.csv` under the standard `data/` output directory.
Verified recoveries use `ApRecoveredReport_<organization UUID>.csv`, with a separate database identity strategy.
The log gives retained and recovered counts. Recovered observations are never discarded silently.
The existing export selection also supports the configured database backends.
SQLite uses the organization identifier and normalized MAC address as the composite primary key.
Repeated writes replace matching rows.
An AP that no longer qualifies can remain in an existing database table from a previous report.
Use `reported_at` to select the rows from the report run that you need.

No matches produce a log message and no new output.
If all candidates recover, the report writes only the recovered output.
The portal marks this result as completed and states that no output file exists.
A failed source page, invalid required data, or failed output write produces an explicit error.
The report completes every required source read before it writes output.
It does not export a partially read organization.

## Related runbook

The NOC runbook for this report is [AP_WARNING_REPORT_MENU_307](noc-runbooks/AP_WARNING_REPORT_MENU_307.md). It gives the API call sequence and the filter rules.


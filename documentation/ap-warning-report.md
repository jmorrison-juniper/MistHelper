# AP warning report

Menu **307** exports APs with reported warning or error codes for one selected organization.
The operation reads cloud data only.
It does not change an AP, a site, or an organization.

## Run the report

Select menu 307, then select the organization if the tool requests one.
Use the standard export format selection.
The portal lists the operation under **AP Warning Reports**.

The report reads every organization site, AP inventory page, and AP statistics page.
It includes connected and disconnected inventory APs with nonzero trouble codes.
An offline AP without a trouble code does not qualify.
Unassigned APs remain eligible when trouble evidence exists.

## Interpret the evidence

The code comes from `last_trouble`, usually in AP statistics.
This field records historical trouble evidence.
It does not prove that the AP currently displays a yellow LED or currently has a failure.
Review `trouble_timestamp` before you use the report for a current incident.
The `reported_at` column records report creation, not the start of the trouble.
Both timestamps use UTC.
An absent observation time remains empty.

The report reads the live AP LED definitions through `listApLedDefinition`.
Known codes include their key, name, and description.
Unknown nonzero codes remain in the report with `definition_status=unknown`.
The report never invents their meaning.

Site names accompany site identifiers.
`site_lookup_status` distinguishes found sites, missing sites, and unassigned APs.
`connection_status` distinguishes connected, disconnected, and unknown states.
The log gives scanned AP, missing-evidence, and matched AP counts.
Missing evidence does not establish that an AP is healthy.

## Output and failure behavior

The filename is `ApWarningReport_<organization UUID>.csv` under the standard `data/` output directory.
The existing export selection also supports the configured database backends.
SQLite uses the organization identifier and normalized MAC address as the composite primary key.
Repeated writes replace matching rows.
An AP that no longer qualifies can remain in an existing database table from a previous report.
Use `reported_at` to select the rows from the report run that you need.

No matches produce a log message and no new output.
A failed source page, invalid required data, or failed output write produces an explicit error.
The report completes every required source read before it writes output.
It does not export a partially read organization.

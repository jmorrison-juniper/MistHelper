# Export contract

`ApWarningReport.run()` will be the menu callable after final registration.
Use `ApWarningReport_<org_id>.csv` and the `ap_warning_report` primary-key strategy.
The registered composite key uses `org_id` and `mac` to replace each AP row on a repeated export.

The client uses only read operations:

- `mistapi.api.v1.const.ap_led_status.listApLedDefinition`
- `mistapi.api.v1.orgs.sites.listOrgSites`
- `mistapi.api.v1.orgs.inventory.getOrgInventory`, with `type="ap"`
- `mistapi.api.v1.orgs.stats.listOrgDevicesStats`, with `type="ap"` and `status="all"`

The shared runtime page limit applies to paginated organization reads.
Each page must report HTTP 200 and a list of object records.
Every required read finishes before any output write.
Use the existing session and SDK next-page transport.
Do not log response bodies or transport exception strings.

The exporter returns the number of exported rows after a successful writer result.
An empty match set returns zero and writes nothing.
A failed read or write raises an explicit error.
EOF or a missing organization selection stops before cloud reads.

The report columns and validation rules are defined in [the data model](../data-model.md).
The completion summary distinguishes scanned APs, missing trouble evidence, and matched APs.

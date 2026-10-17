# Display Data Model

The server response remains unchanged.

## Organization row

`org_id`, `name`, `request_status`, and endpoint outcome envelopes identify each result.
Manual rows retain stable `manual-` identifiers and session-only counts.
Normalize inventory lists by `type`: `ap`, `switch`, and `gateway`.
Manual inventory maps use uppercase count keys accepted by the existing validator.
Unknown device types remain included in the total count.

## License column

Normalize underscores to hyphens and uppercase.
Collect columns from summary counts, entitlement counts, and amendment records.
Render a used/entitled pair only from valid non-negative integer counts.
An absent count remains `Unavailable`, not zero.

## Totals

Sum known counts and identify incomplete totals whenever any contributing value is unavailable.
Summary cards use the same totals as the comparison table.

## Browser state

Retain selected organization IDs, manual count maps, and purchased count maps.
Prune removed selections after discovery and filter purchase maps before requests.
Do not persist API data or credentials.

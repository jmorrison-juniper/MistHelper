# Contract: Capture Page and Download

## Page identifiers

The capture page provides these table identifiers.

- `capture-table-devices`
- `capture-table-clients-wired`
- `capture-table-clients-wireless`
- `capture-table-clients-guest`
- `capture-table-switch-ports`
- `capture-table-poe`
- `capture-table-radios`
- `capture-table-tunnels`
- `capture-table-bgp-peers`
- `capture-table-alarms`

Each new section also provides `capture-empty-<key>` when it has no row.
A Tier 2 capture provides `capture-tier3-not-requested`.

## Download kinds

The `kind` field uses these exact values.

`device`, `client_wired`, `client_wireless`, `client_guest`, `switch_port`, `poe`, `radio`, `tunnel`, `bgp_peer`, `alarm`.

## Compatibility field

Every row provides `details_json`.
The value is a compact JSON object with all safe source fields.
The value excludes fields that match the existing credential filter.

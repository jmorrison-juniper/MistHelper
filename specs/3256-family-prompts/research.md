# Research: Endpoint family per-choice prompts

## Decision: Use exporter tables as the source of truth

`src/export/endpoint_family_exporter.py` defines the six endpoint family tables. Each row carries `operation` and `required`. The portal must read these tables to prevent drift.

## Decision: Store full required tuples on each chooser option

The guard can compare option metadata against the exporter tables. The browser can read the same metadata when the operator selects an endpoint.

## Decision: Render prompt controls from a mapping helper

The helper maps `site_id` to the existing site chooser, `msp_id` to a text control, and all other prompted identifiers to required text controls. It marks `org_id` as resolved by context, because the handler normally does not call `input()` for it in the portal.

## Alternatives considered

- Fixed controls per menu: rejected because the required tuple changes per operation.
- Command-line only: rejected because issue #3256 requires browser-runnable rows.
- Change the exporter prompt order: rejected because the CLI behavior is the source contract.

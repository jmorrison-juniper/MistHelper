# Contract: `PskHygieneReport.run()`

## Public entry point

`PskHygieneReport.run()` starts menu `274`.

## Required behavior

1. Resolve the API session through `SourceDependencyResolver.apisession`.
2. Resolve the organization ID without a prompt from the cached runtime context or `org_id` or `ORG_ID`.
3. Do not add a new prompt inside `run()`.
4. Fetch PSKs, organization WLANs, and organization templates through the client module.
5. Convert raw records into sanitized model entities.
6. Build report rows through pure model functions.
7. Build summary counts from the report rows.
8. Log the summary counts only.
9. Export through `DataExporter.write_with_format_selection`.
10. Return a value that existing menu test handling can treat as success.

## Client boundary

The client module owns:

- `mistapi.api.v1.orgs.psks.listOrgPsks`
- `mistapi.api.v1.orgs.wlans.listOrgWlans`
- `mistapi.api.v1.orgs.templates.listOrgTemplates`
- Pagination handling.
- SDK response normalization into plain Python records.

## Model boundary

The model module owns:

- Dataclasses.
- The `PskHygieneScorer` class.
- SSID normalization.
- Expire-time parsing.
- Finding evaluation.
- Summary counting.

The model module must not import `mistapi`, `DataExporter`, `ConfigUtils`, or `SourceDependencyResolver`.

## Test contract

Unit tests must:

- Use fake client records.
- Avoid network calls.
- Verify all finding labels.
- Verify summary counts.
- Verify secret stripping.
- Verify no prompt happens in `run()`.
- Verify the missing organization ID path fails closed without a prompt.

## Secret contract

Logs, console output, and exported rows must not include:

- A PSK passphrase value.
- An old passphrase value.
- A token value.

Rows may include only `old_passphrase_present`.

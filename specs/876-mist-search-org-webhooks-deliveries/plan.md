# Implementation Plan: searchOrgWebhooksDeliveries

## Scope

Add one read-only organization menu operation for webhook delivery search.
Keep the change separate from site webhook delivery work.

## Design

1. Add `OrgWebhookDeliveriesExporter` beside the site webhook exporter.
2. Resolve the organization with `ConfigUtils`.
3. List organization webhooks and select one with `InputUtils.safe_input`.
4. Call the installed SDK path `mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries`.
5. Page results with `mistapi.get_all`.
6. Flatten and persist rows through `DataExporter.write_with_format_selection`.
7. Register menu 249 as `interactive_safe`.
8. Keep the existing composite primary-key strategy for the operation.
9. Add unit coverage, README text, menu reference text, and a changelog entry.

## Validation

Run the focused exporter tests, then compile, Ruff, Black, and the related
operation-registry tests.

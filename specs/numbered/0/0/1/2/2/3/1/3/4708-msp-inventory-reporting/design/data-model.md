# Data Model: MSP inventory batch coverage

The change adds no database entity and no stored field. The batch uses in-memory values only.

## Organization Record

- Source: the MSP organization list from `listMspOrgs`. The OpenAPI schema `org_list` at `documentation/mist-api-openapi31yaml.yaml` lines 89182-89186 defines an array of `org` objects.
- Fields that the batch reads: `id` and `name`. The `id` field is at line 88841, and the `name` field is at line 88865.
- Natural key: `id`. The batch requires a non-empty `id` to run a record.
- Validation: A record without a non-empty `id` is skipped. The warning sits at `src/mist/resources/inventory/org_device_inventory_msp.py` line 480.

## Organization Result

- Source: the tuple `(model_rows, version_rows, ver_per_model, safe_org)` that `run_for_org` returns (`src/mist/resources/inventory/org_device_inventory_summary.py` line 425).
- A returned tuple is a successful result. A raised exception is a failed result.
- Storage: The batch converts a successful result to `_OrgProcessedResult` (`src/mist/resources/inventory/org_device_inventory_msp.py` line 35) for the combined reports.

## Batch Coverage

`_BatchCoverage` is a frozen value. It holds two counts. The other values derive from those counts.

| Name | Kind | Rule |
| --- | --- | --- |
| `total` | Stored count | The number of organization records from the MSP list. |
| `successful` | Stored count | The number of successful results that the batch collected. |
| `skipped_or_failed` | Derived count | `total` minus `successful`. |
| `is_partial` | Derived flag | True when `skipped_or_failed` is greater than zero. |
| `heading_label` | Derived text | `All Orgs` when the batch is complete. When partial, the text reads `Partial:` followed by the successful count, the word `successful`, a comma, the skipped or failed count, and the words `skipped or failed`. |
| `file_marker` | Derived text | `_Partial` when the batch is partial. Empty text when the batch is complete. |

## State Transitions

Batch states:

1. Listed. The MSP returns no organization records. The batch prints the no-organizations message and ends. It prints no footer.
2. Complete. Every organization record produces a successful result. The batch prints the complete footer.
3. Partial. At least one record is skipped or fails. The batch prints the partial footer.
4. Partial with fewer than two successful results. The batch writes no combined report.
5. Partial with two or more successful results. The batch writes combined reports that carry the partial label and the file marker.

Record states:

1. Pending. The batch has not reached the record.
2. Skipped. The record has no `id`. The console prints the skipped line.
3. Failed. The runner raises an exception. The console prints the error line.
4. Successful. The runner returns a tuple. The batch adds the result to the collected list.

## Relationships

- One batch contains zero or more organization records.
- Each successful record contributes one organization result.
- The batch coverage derives from the number of records and the number of organization results.

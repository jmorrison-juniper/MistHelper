# Contract: Console summary for skipped MSP sources

## Identity

- **Function**: `CrossOrgSubscriptionInventoryReport._print_summary` in `src/mist/intelligence/reports/subscription_expiry/operation.py`. Main lines 494 to 519.
- **New helpers**: `_skipped_rows` and `_print_skipped_sources`.

## Output Order

1. `Cross-org subscription inventory summary:`. The heading does not change.
2. `  Organizations discovered: <count>`. The count excludes skipped rows.
3. `  Organizations with data: <count>`. The line does not change.
4. `  Organizations with failure: <count>`. The line does not change.
5. `  MSP sources skipped: <count>`. This line is new, and the report always prints it.
6. One line for each skipped row: `  Skipped MSP source <msp_id>: <reason>`. These lines are new.
7. The remaining existing lines, in their current order.

## Example

This example shows a run with one direct organization and one skipped MSP source.

```text
Cross-org subscription inventory summary:
  Organizations discovered: 1
  Organizations with data: 1
  Organizations with failure: 0
  MSP sources skipped: 1
  Skipped MSP source msp-1: The account lacks the MSP organization listing right. The grant scope is "org", not "msp". The MSP organization list was not requested.
```

## Rules

- Log text and console text use ASCII only (FR-011).
- The printer copies the reason from the status row `error` field. It does not rewrite the text.
- The printer adds no line for a run without skipped rows, except the count line with the value `0`.

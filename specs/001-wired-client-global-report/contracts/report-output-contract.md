# Contract: Report Output Consistency

## Scope

Defines required consistency between local report artifact and standard export output.

## Required Outputs

1. Local report artifact for the run (in `data/`).
2. Standard export output using existing `DataExporter.write_with_format_selection` flow.

## Required Consistency Rules

1. Both outputs must contain identical matched-record sets for a given run.
2. Summary metadata must match across outputs:
   - requested filters
   - filtering method used (remote/local/both)
   - records retrieved
   - records matched
   - generation timestamp
3. Zero-match runs must still produce valid outputs with explicit zero-match summary.

## Compatibility Rules

- Output shape must remain compatible with existing downstream CSV/SQLite consumers.
- New columns/fields must be additive and not break existing export ingestion expectations.

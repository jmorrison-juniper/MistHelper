# Quickstart: Global Wired Client Search Report

## Purpose

Run the new read-only menu operation to generate an organization-wide wired client report with operator-based MAC/manufacturer filtering.

## Prerequisites

- Python 3.13+
- Valid Mist API token in `.env`
- Dependencies installed from `requirements.txt`
- Organization context available (cached or prompted at runtime)

## Run Locally

1. Activate your environment.
2. Run MistHelper interactively and choose the new wired client report menu option.
3. Provide filter operators/values as needed:
   - MAC operator/value (optional)
   - Manufacturer operator/value (optional)
4. Confirm output is generated in both:
   - local report artifact in `data/`
   - standard CSV/SQLite export path

## Validation Checklist

- No filters: full retrievable org wired client set is exported.
- Value-based operators: empty normalized values are rejected before execution.
- MAC/MFG positional parity: contains/starts-with/ends-with and negated variants behave consistently.
- Value-based negated manufacturer operators: blank/missing manufacturer values remain non-matches unless a blank/null operator is selected.
- Combined filters: result set respects logical AND.
- Output parity: local report and standard export have identical matched counts.

## FR-012 Failure-Path Verification (T028)

- API exception during fetch: `_fetch_clients` catches all exceptions, logs with traceback, prints user-facing error, returns empty list. No false success output is produced.
- Rate-limit interruption: `mistapi.get_all` handles retries internally; if ultimately exhausted, exception is caught by the same handler.
- Validation failure: `validate_operator_value` rejects empty values for value-required operators and returns `False` before any API call is made.
- Verification: simulate API failure by temporarily invalidating the token or org_id; confirm the operation prints an error and exits cleanly without writing matched records.

## FR-013 Compatibility Validation (T029)

- Output shape is additive: `GlobalWiredClientReport.csv` uses the same field set as existing `searchOrgWiredClients` output (flattened via `DataProcessingUtils.flatten_nested_fields`).
- SQLite export uses `globalWiredClientReport` as the `api_function_name`, creating a separate table with its own composite PK (`mac`, `timestamp`) -- no collision with existing `searchOrgWiredClients` table.
- Downstream consumers of existing CSV/SQLite exports are unaffected; the new report is a separate file/table.

## Operator Semantic Verification Matrix (T032)

| Operator | MAC Test | MFG Test | Expected |
| - | - | - | - |
| is | `aa:bb:cc:dd:ee:ff` matches `AA-BB-CC-DD-EE-FF` | `Juniper` matches `juniper` | case/delimiter insensitive match |
| is not | `aa:bb:cc:dd:ee:ff` excludes self | `Juniper` excludes `juniper` | False (same normalized value) |
| contains | `bb:cc` matches `aa:bb:cc:dd:ee:ff` | `uni` matches `Juniper` | substring match |
| doesn't contain | `zz` excludes `aa:bb:cc:dd:ee:ff` | `cisco` excludes `Juniper` | True (not found) |
| starts with | `aa:bb` matches `aa:bb:cc:dd:ee:ff` | `Jun` matches `Juniper` | prefix match |
| doesn't start with | `zz` excludes `aa:bb:cc:dd:ee:ff` | `Cis` excludes `Juniper` | True (no prefix) |
| ends with | `ee:ff` matches `aa:bb:cc:dd:ee:ff` | `per` matches `Juniper` | suffix match |
| doesn't end with | `zz` excludes `aa:bb:cc:dd:ee:ff` | `co` excludes `Juniper` | True (no suffix) |
| is blank | empty string field = True | empty MFG = True | blank string match |
| is not blank | non-empty field = True | non-empty MFG = True | non-blank match |
| is null | None field = True | None MFG = True | null match |
| is not null | non-None field = True | non-None MFG = True | non-null match |

## Required Verification Commands

- Syntax gate:
  - `python -m py_compile MistHelper.py`
- Test harness:
  - `python MistHelper.py --test`

## Deployment Reminder

After implementation, follow the project's mandatory full deployment pipeline (commit/push, CI build watch, image pull, container restart, runtime verification).

## Implementation Notes

- **Menu number**: 161
- **OperationRegistry category**: `interactive_safe`
- **Classes added**: `FilterOperatorEngine`, `GlobalWiredClientReportGenerator`
- **web_portal/menu_registry.py**: No change required (menu 161 > 80 threshold)

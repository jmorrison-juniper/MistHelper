# Data Model: Cradlepoint HTTP refusals

## Existing response

The SDK response contains `status_code`, `data`, `raw_data`, and transport metadata.
This repair reads only `status_code` before it accepts the response.

## Status decision

| Input | Decision |
| --- | --- |
| Integer `200` through `299` | Continue with the existing body handling. |
| Integer `100` through `199`, or `300` through `599` | Report the exact HTTP failure. |
| Missing status, `None`, boolean, non-integer, or integer outside `100` through `599` | Report an unavailable transport status. |

## Existing output

A nonempty successful dictionary still becomes one flattened row.
The row still contains `org_id` and the integration fields.
The shared writer still receives `api_function_name="testOrgCradlepointConnection"`.
The filename remains `OrgCradlepointConnection_<org_id>.csv`.

No schema, primary-key strategy, cache, or persistent record type changes.

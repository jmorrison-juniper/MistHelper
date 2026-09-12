# Research: Simple endpoint family stage one

## Discovery Method

The discovery pass scanned the installed `mistapi` package source for function
definitions. It imported the resolved module and used `inspect.signature()` to
read the required parameters after `mist_session`.

The issue list came from open GitHub issues with titles that match the Mist API
endpoint pattern. The pass classified only `get` and `list` style operation
names for stage one.

## Measured Counts

| Bucket | Issue rows | Shipped unique operations |
| - | -: | -: |
| No identifier | 29 | 29 |
| `org_id` | 56 | 55 |
| `site_id` | 57 | 57 |
| `msp_id` | 10 | 10 |

The total stage-one issue rows are 152. The shipped table contains 151 unique
operations because two issues name `getOrgSsrRegistrationCommands`.

## Phantom Result

The full endpoint issue scan found one operation that does not resolve against
the installed SDK: `searchOrgClientFingerprints` in issue #1369. It is not in
any stage-one table.

## Constraints

- Do not infer SDK modules from the endpoint URL.
- Do not use substring search to prove implementation.
- Do not include duplicate operation rows in the prompt table.
- Do not include unresolved operations.

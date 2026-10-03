# Capture Cleanup Contract

This feature changes validation for the existing Mist API cleanup calls. It does not add an endpoint or transport.

## Lookup

| Scope | Method | Path |
| --- | --- | --- |
| Site | `mist_get` | `/api/v1/sites/{site_id}/pcaps?limit=1` |
| Organization | `mist_get` | `/api/v1/orgs/{org_id}/pcaps?limit=1` |

Require integer response status 200. Reject missing status, booleans, strings, floats, and other malformed status values.

Preserve existing capture data selection. A lookup without a matching ID causes no DELETE.
Malformed capture data handling and endpoint migration remain outside this repair.

## Deletion

| Scope | Method | Path |
| --- | --- | --- |
| Site | `mist_delete` | `/api/v1/sites/{site_id}/pcaps` |
| Organization | `mist_delete` | `/api/v1/orgs/{org_id}/pcaps` |

Send DELETE only after lookup confirms the requested capture ID in the selected scope. Require response status 200. Any other status or API exception is a cleanup failure.

## Run completion

The runner must resolve stream close and required capture cleanup before it reports a terminal result. A cleanup failure must produce one `FAILED` result. If cleanup succeeds, preserve the existing runtime and operator-stop result mapping.

The monitor completion timestamp determines the normal completion reason. Stream close duration must not change that reason.
Cleanup exceptions produce structured error records and traceback locations. Exception text and remote content must not enter those records.

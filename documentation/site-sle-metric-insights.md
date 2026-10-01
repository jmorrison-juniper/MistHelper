# Site SLE metric insights (menu 73)

Menu 73 exports the available service-level expectation (SLE) metrics for one site.
It calls `listSiteSlesMetrics` with `scope="site"` and the selected site identifier.
The configured Mist API host selects the regional cloud.

The export file is `data/SiteSleMetricsInsights_<site_name>.csv`.
The file name replaces spaces and dashes in the site name with underscores.
The rows contain `site_id`, `site_name`, `metric_name`, `enabled`, and `supported`.
Menu 73 sorts the unique metric names from the `enabled` and `supported` lists.

## Successful responses

An HTTP `200` response with metrics produces one export.
An HTTP `200` response without metrics produces one empty export.
Only the successful empty export reports `no metrics available`.
The export notice uses the path separator of the current platform.

## Failed requests

An HTTP `4xx` or `5xx` response is a request failure, not an empty metrics result.
Menu 73 reports the HTTP status, `listSiteSlesMetrics`, and the selected site identifier at the `ERROR` level.
It does not report empty metrics or a successful export.
It does not create an empty file or replace a previous export.

Exceptions during metrics retrieval or parsing use the same failure-file policy.
Menu 73 reports the failure without an export write.
If the export writer raises an exception, menu 73 does not retry with empty rows.
The error log retains the exception type and traceback frames, but it omits the original exception message.
Menu 73 does not log response bodies or request headers.

This policy preserves previous successful output when retrieval or parsing fails.
A previous file remains an older report, not the result of the failed request.
The policy does not restore a file that the writer changed before its exception.

**Caution:** If a request fails, do not treat a previous export as current data.
Older metrics can cause an incorrect operational decision.

## Status guidance

| HTTP status | Next action |
| - | - |
| `400` | Check the request parameters. |
| `401` | Check the configured authentication without publishing the token. |
| `403` | Check the account or token permissions. |
| `404` | Check the regional API host and selected site. |
| `429` | Wait for the API rate limit to reset. |
| `500`, `502`, `503`, or `504` | Retry after the cloud service recovers. |

Menu 74 exports site metric values through a different operation.
This menu 73 repair does not change menu 74.

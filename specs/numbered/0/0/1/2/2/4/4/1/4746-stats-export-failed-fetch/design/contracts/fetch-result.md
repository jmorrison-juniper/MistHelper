# Contract: Fetch Result of APIDataFetcher.execute()

## Scope

This contract records the existing return contract of `APIDataFetcher.execute()` in `src\mist\access\api\api_data_fetcher.py`. The change does not alter this contract (FR-006). The statistics exports read the return value to set the processed count.

## Return Table

| Condition | Return value | Export call | Log level | Evidence |
| - | - | - | - | - |
| Rows were fetched and exported | True | Yes | Warning with the row count | RC-10 |
| HTTP status 400 or higher after the fetch step | False | No | Error with the status | RC-12, RC-13 |
| Unparsed response body | False | No | Report from the integrity checker | RC-78 |
| Empty response with no rows | False | No | Warning | RC-09 |
| Status 500 or higher on each attempt | Retry, then False | No | Warning for each retry, error at the end | RC-15, RC-18, RC-19 |
| HTTP 429 during pagination | False | No rows exist, so no file is written | Warning | RC-14, RC-16 |
| Any other exception from pagination or export | Raises | Not applicable | Error, then re-raise | RC-11 |

## Notes

- The pagination call assigns rows inside a try block (RC-14). If the call raises, the row list keeps its earlier value, which is empty on the normal path.
- The retry ceiling is `API_REQUEST_MAX_RETRIES`, with a default of 3 (RC-18). The retry delay is `API_REQUEST_RETRY_DELAY`, with a default of 5.0 seconds (RC-19).
- Both statistics exports map True to processed count 1 and False to processed count 0. Raised exceptions produce no completion event (D-8).

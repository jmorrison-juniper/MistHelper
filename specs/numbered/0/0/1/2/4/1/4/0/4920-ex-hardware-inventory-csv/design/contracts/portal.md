# Contract: Portal changes

This contract lists only what changes on the Multi Site tab and in its routes. Every route, field, and error code that this file does not name keeps its current behavior.

## Preview request

`POST /api/websockets/batches/previews` accepts the existing body for the hardware action:

```json
{"preset": "ex-hardware-xml", "format": "csv", "scope_revision": 0}
```

- `format` accepts `xml`, `json`, `both`, and the new value `csv`.
- With `csv`, the fixed commands list holds the XML command only: `show chassis hardware detail | display xml | no-more`. The per-switch XML files stay in the run folder as the source of the report.

## Preview response

The existing fields stay. For the hardware action, the route adds one object. The object holds counts only, so it holds no organization name and no identifier:

```json
{"scope": {"mode": "msp", "organization_count": 3, "failed_count": 1}}
```

- `scope.mode` is `organization` or `msp`. The rules are the rules of menu 309: the scope resolver reads the profile, chooses MSP scope only when the MSP list returns status 200 with an organization, and stops the preview with its plain sentence when the scope is not clear. The decision stays valid for five minutes.
- `scope.failed_count` is the number of organizations that Mist could not read. Each one becomes one outcome row of the report.
- The concurrency default comes from the catalog, not from the preview. The catalog answer `limits.hardware_concurrency` holds the value of `PORTAL_WS_HARDWARE_CONCURRENCY`, and the page starts its concurrency field with that value. The server still accepts 1 through 5 at the start.
- The 1000-target limit applies to the whole preview.

## Start request

`POST /api/websockets/batches` is unchanged. At the start, the service stores the full scope (the mode, the organization names, and the failed organizations) with the run. The report reads the organization names from that store. The page sends `concurrency` from its field.

## Manifest

For a `csv` run, `files` and the archive list `hardware/inventory.csv` next to the per-switch `.xml` files. A failure to compile or publish the report sets `artifact_status` to `failed`, marks the run partial, and keeps the XML files.

## Report download

`GET /api/websockets/batches/<session_id>/download?format=csv`

- A finished run with a report returns the file. `Content-Type` is `text/csv`. `Content-Disposition` names a server-made file, `ExHardwareInventory_<UTC time>.csv`, as an attachment.
- A run that still writes, or that has no report (an output other than `csv`, or a failed output), returns the existing error shape with the code `artifact_not_ready` and status 409. A session that is not a batch returns `not_batch`.
- The query must hold the single field `format` with the value `zip` or `csv`. Any other query returns `bad_request`.
- The existing `format=zip` download stays as it is.

## Report table

`GET /api/websockets/batches/<session_id>/csv-preview?offset=0&limit=1000&q=`

- The route reads the report through the same checked read as the download, so it gives the same refusals: `artifact_not_ready` (status 409) for a run that still writes or has no report, `not_batch` for a session that is not a batch, and `not_ready` (status 503) for a portal with no engine.
- The query accepts only `offset`, `limit`, and `q`. `offset` is a whole number from 0, and the default is 0. `limit` is a whole number from 1, the default is 1000, and a larger value becomes 1000. `q` is a plain text of at most 100 characters. Any other field, a value that is not a whole number, a negative offset, a limit below 1, and a longer `q` return `bad_request`.
- The answer holds the column names, one page of rows, and counts:

```json
{"columns": ["report_run_utc", "scope"], "rows": [["2026-11-25T12:00:00Z", "organization"]], "offset": 0, "limit": 1000, "total": 297, "matched": 297, "cut_cells": 0}
```

- `total` is the number of data rows in the file. `matched` is the number of rows that hold `q` in one cell, with case ignored. The filter runs over the whole file, and `offset` counts matching rows.
- A cell keeps at most 1000 characters. `cut_cells` is the number of cells in the page that lost text.
- A report over 16 MiB returns `too_large` (status 413). A file that is empty, is not valid UTF-8, or has a row of the wrong width returns `output_failed` (status 507). The download stays available in both cases.
- The route logs counts only. It never logs the filter text.

## Page

| Control | `data-testid` | Behavior |
|---------|---------------|----------|
| Output choice **One combined CSV report (.csv)** | `ws-batch-hardware-format` (an option with value `csv`) | Selects the new output. |
| Scope summary line | `ws-batch-scope-summary` | Shows the scope, the organization count, and the number of unread organizations after a preview. |
| **Download CSV report** link | `ws-batch-csv-download` | Appears only when a `csv` run is complete and its output is `ready`. A CSV run keeps polling until its output is `ready` or `failed`. |
| Report table panel | `ws-batch-csv-preview` | Appears when the same condition holds, and the page reads the first page once for each run. The panel holds the table `ws-batch-csv-table`, the filter box `ws-batch-csv-filter`, the buttons `ws-batch-csv-previous` and `ws-batch-csv-next`, and the status line `ws-batch-csv-status`. The page sets every cell as plain text. The filter waits 300 milliseconds after the last key. |
| Concurrency field | `ws-batch-concurrency` | Starts with the catalog value `hardware_concurrency` for the hardware action, and with 3 for every other action. |

## Locks and limits

- The shell lock `PORTAL_WS_ENABLE_SHELL` still gates the action.
- The typed phrase `RUN <count> TARGETS` still binds to the stored preview.
- The saved output limit of 64 MiB still applies to the whole run, including the report. The report may use the quota that the replies leave.

# Contract: Portal changes

This contract lists only what changes on the Multi Site tab and in its routes. Every route, field, and error code that this file does not name keeps its current behavior.

## Preview request

`POST /api/websockets/batches/previews` accepts the existing body for the hardware action:

```json
{"preset": "ex-hardware-xml", "format": "csv", "scope_revision": 0}
```

- `format` accepts `xml`, `json`, `both`, `csv`, and the new values `master-xml` and `csv-master-xml` (issue #4933).
- With `csv`, `master-xml`, or `csv-master-xml`, the fixed commands list holds the XML command only: `show chassis hardware detail | display xml | no-more`. The per-switch XML files stay in the run folder as the source of the combined reports.
- A name that is not in the list returns `bad_request` with the sentence `Choose XML, JSON, BOTH, CSV, MASTER-XML, or CSV-MASTER-XML for hardware output.`

| `format` | Per-switch files | Combined reports at the end of the run |
|----------|------------------|-----------------------------------------|
| `xml` | `.xml` | None. |
| `json` | `.json` | None. |
| `both` | `.xml` and `.json` | None. |
| `csv` | `.xml` | `hardware/inventory.csv` |
| `master-xml` | `.xml` | `hardware/inventory.xml` |
| `csv-master-xml` | `.xml` | `hardware/inventory.csv` and `hardware/inventory.xml` |

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

For a run with a combined report, `files` and the archive list `hardware/inventory.csv` and `hardware/inventory.xml` next to the per-switch `.xml` files, as the format says. A failure to compile or publish any report sets `artifact_status` to `failed`, marks the run partial, and keeps the XML files. The reports are published in one atomic step, so a failed run lists none of them.

## Report download

`GET /api/websockets/batches/<session_id>/download?format=csv`

- A finished run with a report returns the file. `Content-Type` is `text/csv`. `Content-Disposition` names a server-made file, `ExHardwareInventory_<UTC time>.csv`, as an attachment.
- A run that still writes, or that has no report (an output without the CSV, or a failed output), returns the existing error shape with the code `artifact_not_ready` and status 409. A session that is not a batch returns `not_batch`.
- The query must hold the single field `format` with the value `zip`, `csv`, or `xml`. Any other query returns `bad_request` with the sentence `The batch download requires format=zip, format=csv, or format=xml.`
- The existing `format=zip` download stays as it is.

## Combined XML download

`GET /api/websockets/batches/<session_id>/download?format=xml`

- A finished run whose format holds the XML returns the master XML file. `Content-Type` is `application/xml`. `Content-Disposition` names a server-made file, `ExHardwareInventory_<UTC time>.xml`, as an attachment. The bytes are the bytes that the finish step checked.
- The refusals are the same as for the CSV download: `artifact_not_ready` (status 409) for a run that still writes, has no XML report, or failed, and `not_batch` for a session that is not a batch.
- The read uses the same pin, the same checked path, and the same size limit as the other downloads of the run folder.

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
| Output choice **One combined CSV report (.csv)** | `ws-batch-hardware-format` (an option with value `csv`) | Selects the CSV output. |
| Output choice **One combined XML file (.xml)** | `ws-batch-hardware-format` (an option with value `master-xml`) | Selects the master XML output. |
| Output choice **Combined CSV and XML (.csv + .xml)** | `ws-batch-hardware-format` (an option with value `csv-master-xml`) | Selects both combined reports. The review names the output with the same text. |
| Scope summary line | `ws-batch-scope-summary` | Shows the scope, the organization count, and the number of unread organizations after a preview. |
| **Download CSV report** link | `ws-batch-csv-download` | Appears only when a run with the CSV is complete and its output is `ready`. A run with a combined report keeps polling until its output is `ready` or `failed`. |
| **Download combined XML** link | `ws-batch-xml-download` | Appears only when a run with the XML is complete and its output is `ready`. Its address is the `format=xml` route. The page sets the link again when it restores a batch after a reload. |
| Report table panel | `ws-batch-csv-preview` | Appears when a run with the CSV is ready, and the page reads the first page once for each run. A run with the XML only shows no table. The panel holds the table `ws-batch-csv-table`, the filter box `ws-batch-csv-filter`, the buttons `ws-batch-csv-previous` and `ws-batch-csv-next`, and the status line `ws-batch-csv-status`. The page sets every cell as plain text. The filter waits 300 milliseconds after the last key. |
| Concurrency field | `ws-batch-concurrency` | Starts with the catalog value `hardware_concurrency` for the hardware action, and with 3 for every other action. |

## Locks and limits

- The shell lock `PORTAL_WS_ENABLE_SHELL` still gates the action.
- The typed phrase `RUN <count> TARGETS` still binds to the stored preview.
- The saved output limit of 64 MiB still applies to the whole run, including the combined reports. Each report may use the quota that the replies and the earlier report leave.

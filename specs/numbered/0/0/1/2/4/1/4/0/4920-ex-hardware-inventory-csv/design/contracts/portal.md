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

## Page

| Control | `data-testid` | Behavior |
|---------|---------------|----------|
| Output choice **One combined CSV report (.csv)** | `ws-batch-hardware-format` (an option with value `csv`) | Selects the new output. |
| Scope summary line | `ws-batch-scope-summary` | Shows the scope, the organization count, and the number of unread organizations after a preview. |
| **Download CSV report** link | `ws-batch-csv-download` | Appears only when a `csv` run is complete and its output is `ready`. A CSV run keeps polling until its output is `ready` or `failed`. |
| Concurrency field | `ws-batch-concurrency` | Starts with the catalog value `hardware_concurrency` for the hardware action, and with 3 for every other action. |

## Locks and limits

- The shell lock `PORTAL_WS_ENABLE_SHELL` still gates the action.
- The typed phrase `RUN <count> TARGETS` still binds to the stored preview.
- The saved output limit of 64 MiB still applies to the whole run, including the report. The report may use the quota that the replies leave.

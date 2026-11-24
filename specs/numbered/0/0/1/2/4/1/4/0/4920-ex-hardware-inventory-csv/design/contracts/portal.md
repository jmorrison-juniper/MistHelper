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

The existing fields stay. For the hardware action, the response adds:

```json
{
  "scope": {
    "mode": "organization",
    "credential_type": "api_token",
    "organization_count": 1,
    "organizations": [
      {"org_id": "ORG-1", "org_name": "Example Org", "target_count": 15}
    ]
  }
}
```

- `scope.mode` is `organization` or `msp`.
- `limits.concurrency` is the value of `PORTAL_WS_HARDWARE_CONCURRENCY` for the hardware action. It is 3 for the other batch kinds, as now.
- Each entry of `targets` carries `org_name` next to `org_id`.
- The 1000-target limit applies to the whole preview.

## Start request

`POST /api/websockets/batches` is unchanged. The page sends `concurrency` from the preview limit. The server accepts 1 through 5.

## Manifest

For a `csv` run, `files` and the archive list `hardware/inventory.csv` next to the per-switch `.xml` files. A failure to compile the report sets `artifact_status` to `failed` and keeps the XML files.

## Report download

`GET /api/websockets/batches/<session_id>/download?format=csv`

- A finished run with a report returns the file. `Content-Type` is `text/csv; charset=utf-8`. `Content-Disposition` names `ex-hardware-inventory.csv` as an attachment.
- A run that still writes, or that has no report, returns the existing error shape with the existing `not_ready` or `not_found` code.
- The existing `format=zip` download stays as it is.

## Page

| Control | `data-testid` | Behavior |
|---------|---------------|----------|
| Output choice **One combined CSV report (.csv)** | `ws-batch-hardware-format` (an option with value `csv`) | Selects the new output. |
| Scope summary line | `ws-batch-scope-summary` | Shows the scope, the organization count, and the target count after a preview. |
| **Download report** link | `ws-batch-csv-download` | Appears when a `csv` run finishes with a report. |
| Concurrency field | `ws-batch-concurrency` | Starts with the value from the settings for the hardware action. |

## Locks and limits

- The shell lock `PORTAL_WS_ENABLE_SHELL` still gates the action.
- The typed phrase `RUN <count> TARGETS` still binds to the stored preview.
- The saved output limit of 64 MiB still applies to the whole run, including the report.

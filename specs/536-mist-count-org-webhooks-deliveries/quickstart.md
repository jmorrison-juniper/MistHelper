# Phase 1 Quickstart: countOrgWebhooksDeliveries (Menu 195)

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

This quickstart describes how to run the new menu item locally during implementation
and validation. It is written for a junior NOC engineer working on a Windows 11
developer host with the project venv activated.

## 1. Prerequisites

- Python 3.13+ installed and on PATH.
- Project venv exists at `.venv\` in the repo root.
- `mistapi` 0.59 or newer installed in the venv (`pip show mistapi`).
- `.env` file at the repo root with at least the values listed below.
- `data\` directory exists and is writable. Inside a Podman container the data volume
  must be `chmod -R 777 data/` before first run.

## 2. Required .env Variables

| Variable          | Required | Purpose |
|-------------------|----------|---------|
| `MIST_HOST`       | Yes      | Mist API host (e.g. `api.mist.com`, `api.eu.mist.com`) |
| `MIST_API_TOKEN`  | Yes      | Mist API token for the operator account; never logged |
| `MIST_ORG_ID`     | No       | Default org UUID accepted when the prompt is blank |
| `MIST_PAGE_LIMIT` | No       | Inherited convention; the count endpoint honors `limit` |

No new .env variable is introduced by this menu item.

## 3. Expected Output Files

For an invocation against org UUID `1a2b3c4d-...` with webhook UUID `9f8e7d6c-...`:

- `data\org_1a2b3c4d_webhook_9f8e7d6c_deliveries_count_summary.csv`
- `data\org_1a2b3c4d_webhook_9f8e7d6c_deliveries_count_buckets.csv`
- SQLite tables `org_webhook_deliveries_count_summary` and
  `org_webhook_deliveries_count_buckets` in `data\mist_data.db`. Upsert via
  `INSERT OR REPLACE` on the composite PKs documented in `data-model.md`.
- When the polyglot backend is active: ArangoDB graph nodes plus an edge from the
  parent `org_webhook` node, and a Redis cache key
  `mist:webhook:deliveries:count:<org_id>:<webhook_id>:<distinct>:<start>:<end>`.

## 4. Interactive Invocation

From the repo root with the venv activated:

```powershell
.\.venv\Scripts\Activate.ps1
python .\MistHelper.py
```

Enter `195` at the main-menu prompt. Prompt sequence (all via `safe_input()`):

1. Org ID (default to `MIST_ORG_ID` when set)
2. Webhook ID (required, no default)
3. Distinct grouping (empty = API default)
4. Topic filter (empty = all)
5. Status filter (empty = all)
6. Status code filter (empty = all)
7. Error filter (empty = all)
8. Duration (default `1d`; empty switches to absolute start/end)
9. Start epoch (only when duration is empty)
10. End epoch (only when duration is empty)
11. Limit (default `100`)

Expected ASCII-only log output:

```
INFO   Counting webhook deliveries for org 1a2b3c4d... webhook 9f8e7d6c... distinct=status duration=1d limit=100
DEBUG  Count result: distinct=status total=287 buckets=4
INFO   Flattening count summary and 4 bucket rows
DEBUG  Flattened: summary_rows=1 bucket_rows=4
INFO   Writing org_webhook_deliveries_count_summary and org_webhook_deliveries_count_buckets
DEBUG  Write complete: backend=csv+sqlite files=2
```

The menu item returns to the main menu on success and exits 0 on a single-shot
`--menu 195` invocation.

## 5. Direct (Non-Interactive) Invocation

```powershell
python .\MistHelper.py --menu 195 `
    --org-id 1a2b3c4d-1111-2222-3333-444444444444 `
    --webhook-id 9f8e7d6c-aaaa-bbbb-cccc-dddddddddddd `
    --distinct status `
    --duration 1d `
    --limit 100
```

`--org-id` and `--limit` already exist on the parser. The implementation adds
`--webhook-id`, `--distinct`, `--duration`, `--start`, `--end`, `--topic`,
`--status`, `--status-code`, `--error` as optional arguments consumed by this menu
item.

## 6. Method Skeleton (implementation reference)

The implementation lives on a new `WebhooksExportUtils` class. Every executable line
carries an inline comment in the real source per Principle VI, and every meaningful
action has paired `logging.info` / `logging.debug` per Principle VII.

```python
class WebhooksExportUtils:
    def __init__(self, apisession, exporter):
        self.apisession = apisession                          # mistapi session handle
        self.exporter = exporter                              # DataExporter instance

    def export_count_org_webhooks_deliveries(
        self,
        org_id: str,
        webhook_id: str,
        filters,
        window,
    ) -> int:
        logging.info(                                         # before API call
            "Counting webhook deliveries for org %s webhook %s distinct=%s",
            org_id, webhook_id, filters.distinct or "default",
        )
        response = count_module.countOrgWebhooksDeliveries(   # SDK call (single GET)
            self.apisession, org_id, webhook_id,
            distinct=filters.distinct, status=filters.status,
            status_code=filters.status_code, topic=filters.topic,
            error=filters.error, start=window.start, end=window.end,
            duration=window.duration, limit=window.limit,
        )
        body = response.data or {}                            # safe default for empty
        logging.debug(                                        # after API call
            "Count result: distinct=%s total=%d buckets=%d",
            body.get("distinct"), body.get("total", 0),
            len(body.get("results", [])),
        )
        summary_row = self._flatten_summary(                  # one envelope row
            org_id, webhook_id, body, filters,
        )
        bucket_rows = self._flatten_buckets(                  # N bucket rows
            org_id, webhook_id, body,
        )
        self.exporter.write_with_format_selection(            # persist summary
            [summary_row], "org_webhook_deliveries_count_summary",
            api_function_name="countOrgWebhooksDeliveries",
        )
        self.exporter.write_with_format_selection(            # persist buckets
            bucket_rows, "org_webhook_deliveries_count_buckets",
            api_function_name="countOrgWebhooksDeliveries",
        )
        return 0
```

The method body is approximately 22 executable lines (under the 25-line cap), takes 4
parameters plus `self` (cap is 5), and contains exactly 5 logical blocks. Both
flatteners are private helpers on the same class. The two dataclasses
`WebhookDeliveryFilters` and `WebhookDeliveryWindow` pack the 9 query knobs into 2
parameters per Principle I.

## 7. Quality Gates (run before every commit)

```powershell
python -m py_compile .\MistHelper.py
python -m ruff check .\MistHelper.py
python -m black --check .\MistHelper.py
```

All three must exit 0. To auto-fix Black: drop `--check`. To inspect Ruff:
`python -m ruff check .\MistHelper.py --output-format=concise`.

## 8. Smoke Test

```powershell
python .\MistHelper.py --test
```

The `--test` harness skips heavy and destructive operations (14, 18, 63-65, 90-100)
but does run menu 195 because it sits in the safe-export band. The harness exit
code must be 0 and the two new CSVs must appear under `data\`.

## 9. Container Verification

```powershell
podman pull ghcr.io/jmorrison-juniper/misthelper:latest
podman stop misthelper ; podman rm misthelper
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `
    -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" `
    ghcr.io/jmorrison-juniper/misthelper:latest
ssh -p 2200 misthelper@localhost
```

Inside the SSH session: enter `195` at the menu, supply the prompts, and confirm the
two output files appear in `data\` on the host.

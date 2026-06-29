# Phase 1 Quickstart: countOrgWanClients

How to run, validate, and inspect the new menu item locally.

## 1. Prerequisites

- Python 3.13+ activated venv (`.venv\Scripts\Activate.ps1` on Windows 11).
- `pip install -r requirements.txt` (or `uv pip install -r requirements.txt`).
- Container alternative: `ghcr.io/jmorrison-juniper/misthelper:latest` on port 2200 (SSH) / 8055 (web UI).

## 2. Required .env variables

Located at the repo root (`.env`, git-ignored). The template lives at
`deploy/.env.example`.

```
MIST_API_TOKEN=<your Mist API token, never logged>
MIST_HOST=api.mist.com
MIST_ORG_ID=<default org UUID; overridable at the prompt>
```

Optional tunables (already used by adjacent menus):

```
MIST_PAGE_LIMIT=1000
FAST_MODE_MAX_CONCURRENT_CONNECTIONS=8
```

## 3. Run the menu item

Interactive:

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py
# At the prompt, type:
230
```

Direct (automation):

```powershell
python MistHelper.py --menu 230
```

## 4. Example invocation transcript

```
> 230
[INFO] Counting org WAN clients for org 1234abcd-... distinct=mfg
Org ID [1234abcd-1111-2222-3333-444455556666]: <Enter to accept default>
Distinct attribute (optional, blank for default): mfg
Start time (epoch or relative like -1d, blank=skip): -7d
End time (epoch, relative, or 'now', blank=skip): now
Duration (default 1d): <Enter>
Limit (default 100, max 1000): 200
[DEBUG] countOrgWanClients returned 47 rows (total=1284)
[INFO] Wrote data/count_org_wan_clients.csv (47 rows)
[INFO] Upserted 47 rows into SQLite table count_org_wan_clients
```

All prompts go through `safe_input(prompt, context="count_org_wan_clients")`,
so a disconnected SSH session exits 0 cleanly (no traceback).

## 5. Expected outputs under `data/`

| Backend          | Artifact                                          |
|------------------|---------------------------------------------------|
| CSV (default)    | `data/count_org_wan_clients.csv`                  |
| SQLite           | `data/mist_data.db` table `count_org_wan_clients` |
| ArangoDB+Redis   | Collection `count_org_wan_clients` + Redis cache  |

The active backend is selected by the global MistHelper output configuration
and routed by `DataExporter.write_with_format_selection(data, filename, api_function_name="countOrgWanClients")`.

## 6. Verify SQLite upsert behavior

```powershell
python -c "import sqlite3; c=sqlite3.connect('data/mist_data.db'); print(c.execute('SELECT COUNT(*) FROM count_org_wan_clients').fetchone())"
# Run menu 230 a second time with the same parameters
python MistHelper.py --menu 230
# Re-check the count -- it must equal the first run, not double.
python -c "import sqlite3; c=sqlite3.connect('data/mist_data.db'); print(c.execute('SELECT COUNT(*) FROM count_org_wan_clients').fetchone())"
```

The unique constraint on
`(org_id, distinct_field, distinct_value, start_epoch, end_epoch)` ensures
`INSERT OR REPLACE` rather than duplicate rows.

## 7. Quality gates

Run all three before committing:

```powershell
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py
python -m black --check MistHelper.py
```

Functional test (this menu is *not* in the skip list 14, 18, 63-65, 90-100):

```powershell
python MistHelper.py --test
```

A successful run logs an exit code of 0 and writes a non-empty
`data/count_org_wan_clients.csv` when the upstream org has any WAN
client traffic in the requested window.

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `PermissionError: '/app/data/script.log'` (container) | Mounted `data/` not writable | `chmod -R 777 data/` before first container run. |
| `401 Unauthorized` | Stale `MIST_API_TOKEN` | Regenerate token in Mist UI; update `.env`. |
| `404 Not Found` | Bad `org_id` | Verify `MIST_ORG_ID` against `mistapi` `getSelf`. |
| `429 Too Many Requests` | Burst over 5000/hr | Adaptive delay system auto-throttles; re-run or add `--fast` cautiously. |
| Empty CSV | API returned no buckets | Confirmed by `[INFO] no data returned`; not an error. |

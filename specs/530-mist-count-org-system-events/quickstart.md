# Phase 1 Quickstart: countOrgSystemEvents (menu 195)

Spec: [spec.md](./spec.md) | Plan: [plan.md](./plan.md)

This quickstart shows how to run the new menu item locally on Windows
and verify the output. Replace `<org-uuid>` with a real org UUID you
have access to.

## 1. Prerequisites

- Python 3.13 or newer.
- mistapi 0.59+ installed (`pip install -r requirements.txt`).
- A populated `.env` at the repo root.
- Write access to `data/` (run `chmod -R 777 data/` once on first
  container launch).

## 2. Required .env variables

Add to the repo-root `.env` (git-ignored). The endpoint is org-scoped
and read-only.

```ini
MIST_HOST=api.mist.com
MIST_API_TOKEN=<your_personal_api_token>
MIST_ORG_ID=<org-uuid>
```

Optional knobs that affect every menu item, including 195:

```ini
MIST_PAGE_LIMIT=100        # query-param default if user accepts prompt default
FAST_MODE_MAX_CONCURRENT_CONNECTIONS=8
```

The token is loaded by `EnhancedSSHRunner` / `GlobalImportManager`
through python-dotenv. It is never logged; only the org UUID and the
time window appear in logs.

## 3. Expected output

| Backend | Artifact |
|---------|----------|
| CSV     | `data/count_org_system_events.csv` (created or appended) |
| SQLite  | row(s) in `data/mist_data.db` table `count_org_system_events` |
| ArangoDB+Redis | document(s) in `count_org_system_events` collection plus Redis cache key `mist:count_org_system_events:<org>:<distinct>:<start>:<end>` |

Re-running with the same prompts upserts in place via the unique
constraint `(org_id, distinct, start_epoch, end_epoch, bucket_value)`.

## 4. Interactive invocation

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py
```

At the menu prompt enter `195`. The dialog will look like:

```text
Org ID [from .env: 203d3d02-...-d4e]:        <enter to accept>
Distinct field (blank for none):             device_type
Duration (e.g. 1d, 7d, 2w) [1d]:             7d
Per-page limit [100]:                        <enter>
```

Sample log (ASCII only):

```text
INFO  Fetching system event count for org=203d3d02-...-d4e distinct=device_type duration=7d limit=100
DEBUG Received 4 buckets total=1842 elapsed=0.42s
INFO  Exported 4 rows to count_org_system_events
```

## 5. Non-interactive (automation) invocation

```powershell
python MistHelper.py --menu 195
```

Direct invocation reads `MIST_ORG_ID` from `.env` and falls back to
the prompt defaults for the remaining parameters (`distinct=None`,
`duration=1d`, `limit=100`). Exit code 0 on success, non-zero on
unrecoverable error.

## 6. Verifying the result

SQLite:

```powershell
python -c "import sqlite3; c=sqlite3.connect(r'data/mist_data.db'); print(list(c.execute('SELECT org_id, \"distinct\", bucket_value, count FROM count_org_system_events ORDER BY captured_at DESC LIMIT 5')))"
```

CSV:

```powershell
Get-Content data/count_org_system_events.csv -Head 5
```

## 7. Quality gates (run before commit)

All four MUST pass clean:

```powershell
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py
python -m black --check MistHelper.py
python MistHelper.py --test
```

`--test` walks every safe menu item; menu 195 should report a green
checkmark in the summary block. If the test harness skips it, confirm
it is not listed under the SKIP_LIST constants (operations 14, 18,
63-65, 90-100).

## 8. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `PermissionError data/script.log` | Container mounted `data/` without write perms | `chmod -R 777 data/` then restart container |
| `mistapi.errors.NotFound` | Bad `MIST_ORG_ID` | Verify UUID; the menu logs a WARNING and exits 0 |
| `429 Too Many Requests` | Rate-limit hit | Adaptive delay handles it; retry will succeed |
| Empty CSV | API returned `results: []` | Menu logs "no data returned" and exits 0 |
| EOF in SSH session | Detached client | `safe_input()` returns gracefully, exits 0 |

## 9. Where to look in the code

- New method on the existing org-events exporter class in
  `MistHelper.py` (~line TBD at implementation time).
- `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry near line 1672.
- README.md menu table -- add the row for 195.
- CHANGELOG.md -- add a `version YY.MM.DD.HH.MM` entry per project
  convention.

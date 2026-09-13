# Phase 1 Quickstart: countOrgAssetsByDistanceField (Menu 91)

This guide walks a developer through running and verifying the new menu item
on a local Windows venv (the standard MistHelper development environment).

## 1. Prerequisites

- Python 3.13+
- `mistapi` 0.59+ (installed by `pip install -r requirements.txt`)
- A populated `.env` at the repo root with at least:

  ```text
  MIST_HOST=api.mist.com           # or your regional cloud
  MIST_API_TOKEN=<token>           # never commit this
  MIST_ORG_ID=<org-uuid>           # optional but recommended for unattended runs
  ```

- Writable `data/` directory at the repo root (`chmod -R 777 data/` if running
  in the container).

## 2. Activate the venv

```powershell
.venv\Scripts\Activate.ps1
```

## 3. Run the menu item interactively

```powershell
python MistHelper.py --menu 91
```

You will be prompted (each prompt goes through `safe_input()`):

```text
Enter org_id [from .env if blank]: <enter>
Enter distinct field (e.g. map_id, mac, device_name) [server default]: map_id
Enter result limit [100]: <enter>
```

Expected output:

```text
2026-06-29 12:00:00 INFO  Counting org assets by distinct=map_id for org <org-uuid>
2026-06-29 12:00:01 DEBUG Asset count result: distinct=map_id total=42 buckets=7
2026-06-29 12:00:01 INFO  Writing org_assets_count_summary (1 row)
2026-06-29 12:00:01 INFO  Writing org_assets_count_results (7 rows)
2026-06-29 12:00:01 INFO  Export complete: data/org_<org-uuid>_assets_count_map_id_summary.csv
2026-06-29 12:00:01 INFO  Export complete: data/org_<org-uuid>_assets_count_map_id_results.csv
```

## 4. Expected output files

| Backend            | Artefact                                                                    |
|--------------------|------------------------------------------------------------------------------|
| CSV                | `data/org_<org-uuid>_assets_count_<distinct>_summary.csv` + `_results.csv`  |
| SQLite             | Tables `org_assets_count_summary` and `org_assets_count_results` in `data/mist_data.db` |
| ArangoDB + Redis   | Document collections `org_assets_count_summary` / `org_assets_count_results` + cache keys `mh:org:<org-uuid>:assets_count:<distinct>:*` |

## 5. Non-interactive / `--test` invocation

```powershell
python MistHelper.py --test
```

The default test sweep includes menu 91 (it is outside the heavy/destructive
skip list 14, 18, 63-65, 90-100). On `--test` runs, prompts are auto-filled
from `.env` (`MIST_ORG_ID`, `distinct=map_id`, `limit=100`).

## 6. Verify upsert (idempotency)

Run the menu item twice with identical inputs, then:

```powershell
python -c "import sqlite3; c = sqlite3.connect('data/mist_data.db'); print(c.execute('SELECT COUNT(*) FROM org_assets_count_summary').fetchone())"
```

Row count must not double after the second run -- the composite PK
`(org_id, distinct, start, end)` ensures `INSERT OR REPLACE` semantics.

## 7. Quality gates (must all pass before commit)

```powershell
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py
python -m black --check MistHelper.py
python MistHelper.py --test
```

If `black --check` fails, run `python -m black MistHelper.py` to auto-format
and re-run the checks.

## 8. Implementation skeleton (for tasks.md to flesh out)

Outline -- not final code -- showing where every required convention lives:

```python
class AssetStatsExportUtils:
    """BLE asset stats exports (org/site scope)."""  # New class for asset-stats domain

    def __init__(self, mist_session, exporter):
        self.session = mist_session                  # Mist API session from mistapi
        self.exporter = exporter                     # DataExporter instance

    def export_org_assets_count_by_distinct(
        self, org_id=None, distinct=None, limit=None
    ):
        org_id = org_id or safe_input(               # Prompt with .env fallback for unattended runs
            "Enter org_id [from .env if blank]: ",
            context="org_assets_count:org_id",
        ) or os.getenv("MIST_ORG_ID")
        distinct = distinct or safe_input(           # Optional; blank -> server default
            "Enter distinct field [server default]: ",
            context="org_assets_count:distinct",
        ).strip().lower() or None
        try:                                         # Coerce limit to int with safe default
            limit = int(limit or safe_input(
                "Enter result limit [100]: ",
                context="org_assets_count:limit",
            ) or 100)
        except ValueError:
            limit = 100                              # Fallback when user types non-numeric
        logging.info(                                # Action log BEFORE API call (Principle VII)
            "Counting org assets by distinct=%s for org %s", distinct, org_id
        )
        resp = mistapi.api.v1.orgs.stats_assets.countOrgAssetsByDistanceField(
            self.session, org_id, distinct=distinct, limit=limit
        )                                            # Single SDK call; mistapi handles auth/retry
        data = resp.data or {}                       # Defensive default for None payload
        logging.debug(                               # Action log AFTER API call
            "Asset count result: distinct=%s total=%d buckets=%d",
            data.get("distinct"), data.get("total", 0), len(data.get("results", []))
        )
        summary_row, result_rows = self._flatten(    # Inline-commented helper splits envelope/buckets
            org_id, data
        )
        self.exporter.write_with_format_selection(   # Multi-backend write (CSV/SQLite/Arango+Redis)
            summary_row, f"org_{org_id}_assets_count_{distinct or 'default'}_summary",
            api_function_name="countOrgAssetsByDistanceField",
        )
        self.exporter.write_with_format_selection(
            result_rows, f"org_{org_id}_assets_count_{distinct or 'default'}_results",
            api_function_name="countOrgAssetsByDistanceField",
        )
```

(Method body deliberately at the 25-line ceiling; the `_flatten` helper is a
private method on the same class -- not shown -- and stays under 25 lines.)

## 9. Rollback

The change is additive (one new class, one new dict entry, one new menu line,
two new tables created on first run). To roll back:

1. Revert the commit on `main`.
2. Drop the two tables in SQLite if desired:

   ```sql
   DROP TABLE IF EXISTS org_assets_count_results;
   DROP TABLE IF EXISTS org_assets_count_summary;
   ```

3. Remove the CSV files under `data/` matching the filename pattern.
4. Re-run the container build pipeline; the image will revert to the prior
   menu count.

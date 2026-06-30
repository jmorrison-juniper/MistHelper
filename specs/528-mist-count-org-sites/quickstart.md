# Phase 1 Quickstart: countOrgSites Menu Item

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

## What this menu item does

Calls `GET /api/v1/orgs/{org_id}/sites/count` and writes the aggregated count of
org sites (grouped by a `distinct` field such as `country_code` or `sitegroup_id`)
to `data/` using the configured backend (CSV / SQLite / ArangoDB+Redis).

## Required .env variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `MIST_HOST` | yes | Mist Cloud host (e.g. `api.mist.com`, `api.eu.mist.com`). |
| `MIST_API_TOKEN` | yes | API token. Never logged. |
| `MIST_ORG_ID` | optional | If set, used as the default `org_id` so `--test` runs non-interactively. |
| `MIST_OUTPUT_BACKEND` | optional | `csv` (default), `sqlite`, or `arango`. Read by `DataExporter`. |

## Expected output

CSV backend (default):

- `data/org_<org_id>_sites_count_summary.csv` -- one envelope row.
- `data/org_<org_id>_sites_count_results.csv` -- one row per `results[]` bucket.

SQLite backend:

- `data/mist_data.db` gains two tables: `org_sites_count_summary` and
  `org_sites_count_results`. Composite primary keys keep repeated runs idempotent.

ArangoDB backend:

- Collections `org_sites_count_summary` and `org_sites_count_results` plus edge
  `org_HAS_sites_count_summary` are upserted. Redis caches the latest envelope by
  `(org_id, distinct, start, end)`.

## Example invocation (interactive)

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py
# At the menu prompt:
58
# Then:
Org ID (UUID): 12345678-1234-1234-1234-123456789012
Distinct field (default country_code): country_code
Duration (default 1d, e.g. 7d, 2w):
Limit (default 100, max 1000):
```

Expected console (ASCII-only, log lines abbreviated):

```text
INFO  Counting sites for org 12345678 by distinct=country_code
DEBUG countOrgSites returned total=42 buckets=7
INFO  Flattening 7 result buckets to rows
DEBUG Flatten complete: 1 summary row, 7 result rows
INFO  Exporting via DataExporter (api_function_name=countOrgSites)
INFO  Wrote data/org_12345678..._sites_count_summary.csv (1 row)
INFO  Wrote data/org_12345678..._sites_count_results.csv (7 rows)
```

## Example invocation (non-interactive / test sweep)

```powershell
$env:MIST_ORG_ID = "12345678-1234-1234-1234-123456789012"
python MistHelper.py --menu 58
```

The `--test` driver also exercises menu 58 automatically because it is outside the
skip list (14, 18, 63-65, 90-100).

## Method outline (~20 executable lines, on SiteExportUtils)

```python
def export_org_sites_count(
    self,
    org_id: str | None = None,
    distinct: str | None = None,
    duration: str | None = None,
    limit: int | None = None,
) -> int:
    # Resolve org_id from arg, env, or prompt -- safe_input handles SSH/container EOF
    org_id = org_id or os.environ.get("MIST_ORG_ID") or safe_input(
        "Org ID (UUID): ", context="count_org_sites:org_id"
    )
    # Reject malformed UUIDs early to avoid a 404 round-trip
    if not is_valid_uuid(org_id):
        logging.warning("Invalid org_id %s -- aborting countOrgSites", org_id[:8])
        return 1

    # Prompt for distinct field; default country_code is the most common NOC view
    distinct = distinct or safe_input(
        "Distinct field (default country_code): ",
        context="count_org_sites:distinct",
    ) or "country_code"

    # Optional window and limit -- empty input lets the SDK apply API defaults
    duration = duration or safe_input(
        "Duration (default 1d, e.g. 7d, 2w): ",
        context="count_org_sites:duration",
    ) or None
    limit = limit or self._parse_int_or_default(
        safe_input("Limit (default 100, max 1000): ",
                   context="count_org_sites:limit"),
        default=100,
    )

    # Action log BEFORE the API call -- Constitution Principle VII
    logging.info("Counting sites for org %s by distinct=%s",
                 org_id[:8], distinct)
    # SDK call -- mistapi handles auth, retries, and adaptive delay
    response = mistapi.api.v1.orgs.sites.countOrgSites(
        self.apisession, org_id,
        distinct=distinct, duration=duration, limit=limit,
    )
    envelope = response.data or {}
    # Action log AFTER with bucket count and total -- ASCII only
    logging.debug("countOrgSites returned total=%d buckets=%d",
                  envelope.get("total", 0), len(envelope.get("results", [])))

    # Flatten envelope + buckets into the two-table shape documented in data-model.md
    summary_row, bucket_rows = self._flatten_count_envelope(envelope, org_id)
    # Multi-backend export -- DataExporter routes by MIST_OUTPUT_BACKEND
    DataExporter.write_with_format_selection(
        {"org_sites_count_summary": [summary_row],
         "org_sites_count_results": bucket_rows},
        filename_prefix=f"org_{org_id}_sites_count",
        api_function_name="countOrgSites",
    )
    return 0
```

Every executable line above will carry an inline `#` comment in the actual code
edit (per Constitution Principle VI).

## Quality gates (run in this order before commit)

```powershell
# 1. Syntax check -- no output means success
python -m py_compile MistHelper.py

# 2. Lint -- must pass clean
python -m ruff check MistHelper.py

# 3. Format -- run without --check to auto-fix if needed
python -m black --check MistHelper.py

# 4. Non-interactive smoke test (requires MIST_ORG_ID in .env)
python MistHelper.py --menu 58

# 5. Full test sweep (skip list 14, 18, 63-65, 90-100 -- menu 58 is in the sweep)
python MistHelper.py --test
```

All five must pass before opening the PR. The `auto-merge` label is added only
after CodeQL completes (use `gh pr checks <pr> --watch`).

## What to do if `data/` is read-only

The container runs MistHelper as a non-root user (`misthelper`). The mounted
`data/` directory must be writable:

```powershell
chmod -R 777 data/   # Required before first container run
```

Symptom of a missed step: `PermissionError: [Errno 13] Permission denied:
'/app/data/...'`.

## Verifying SQLite upsert idempotency

```powershell
# First run
python MistHelper.py --menu 58
# Second run with identical parameters
python MistHelper.py --menu 58
# Confirm row counts did not double
sqlite3 data/mist_data.db "SELECT COUNT(*) FROM org_sites_count_summary;"
sqlite3 data/mist_data.db "SELECT COUNT(*) FROM org_sites_count_results;"
```

The composite primary keys defined in `data-model.md` guarantee `INSERT OR REPLACE`
behavior; both counts should be stable across runs with identical `(org_id,
distinct, start, end)` tuples.

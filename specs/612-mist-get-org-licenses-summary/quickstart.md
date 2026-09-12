# Phase 1 Quickstart: getOrgLicensesSummary (Menu 96)

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Data Model**: [data-model.md](./data-model.md) | **Contract**: [contracts/get_org_licenses_summary.md](./contracts/get_org_licenses_summary.md)

## What this menu item does

Fetches the org license picture from the Mist Cloud (`GET
/api/v1/orgs/{org_id}/licenses`) and writes four CSV / SQLite tables under
`data/`: subscriptions, amendments, summary counts, and usage counts. Safe,
read-only, non-paginated, single API call.

## Required `.env` variables

```ini
# Mist API credentials (already required by every MistHelper menu item)
MIST_HOST=api.mist.com                                  # or api.eu.mist.com / api.gc1.mist.com / etc.
MIST_API_TOKEN=<your_api_token_here>                    # never commit; .env is git-ignored

# Convenience default for the new menu item (optional but recommended)
MIST_ORG_ID=00000000-0000-0000-0000-000000000000        # used when prompt is left blank
```

## How to run locally (Windows 11 + venv)

```powershell
# 1. Activate the project venv (PowerShell)
.venv\Scripts\Activate.ps1

# 2. Interactive run -- enter 96 at the menu prompt, then blank to use MIST_ORG_ID
python MistHelper.py

# 3. Direct invocation (skips the menu UI)
python MistHelper.py --menu 96

# 4. Non-interactive test sweep (uses MIST_ORG_ID from .env; skip list 14,18,63-65,90-100)
python MistHelper.py --test
```

## How to run in the container (Podman)

```powershell
# Container is built and pushed by GitHub Actions; pull the latest tag.
podman pull ghcr.io/jmorrison-juniper/misthelper:latest

# Restart with .env mounted read-only and data/ writable.
podman stop misthelper ; podman rm misthelper
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `
    -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" `
    ghcr.io/jmorrison-juniper/misthelper:latest

# SSH in and pick menu 96 (default creds: misthelper / misthelper123!)
ssh -p 2200 misthelper@localhost
```

## Example prompt session

```
> 96
[INFO] Org ID (blank to use MIST_ORG_ID):
[INFO] Fetching license summary for org 11111111-2222-3333-4444-555555555555
[DEBUG] License summary: subs=12 amendments=3 entitled_types=5 usage_types=15
[INFO] Writing org_licenses_subscriptions (12 rows)
[INFO] Writing org_licenses_amendments (3 rows)
[INFO] Writing org_licenses_summary_counts (5 rows)
[INFO] Writing org_licenses_usage_counts (15 rows)
[INFO] Done. Output under data/.
```

## Expected `data/` output

```text
data/
|-- org_licenses_subscriptions.csv          # one row per active subscription
|-- org_licenses_amendments.csv             # one row per amendment record
|-- org_licenses_summary_counts.csv         # one row per (org, license_type)
|-- org_licenses_usage_counts.csv           # one row per (org, license_type, metric)
`-- mist_data.db                            # same four tables when SQLite backend is selected
```

When the polyglot backend is configured, ArangoDB collections of the same
names are upserted in parallel and Redis caches the latest snapshot per
`(org_id, table_name)` key.

## Implementation skeleton (for reviewer reference)

```python
# Add to LicenseExportUtils in MistHelper.py
def export_org_licenses_summary(self, org_id: str | None = None) -> None:
    org_id = org_id or safe_input(                                       # one prompt only per Research Task 5
        "Org ID (blank to use MIST_ORG_ID): ",
        context="org_licenses_summary:org_id",
    ) or os.environ.get("MIST_ORG_ID", "")                               # .env fallback for --test path
    if not _is_valid_uuid(org_id):                                       # validate before spending API quota
        logging.warning("Invalid org_id %s -- aborting", org_id)         # ASCII-only WARNING per Principle V
        return                                                           # early return on validation failure
    logging.info("Fetching license summary for org %s", org_id)          # action log BEFORE the API call
    resp = mistapi.api.v1.orgs.licenses.getOrgLicensesSummary(           # sole permitted SDK entry point
        self.apisession, org_id,                                         # two positional args per contract
    )
    body = resp.data or {}                                               # mistapi wraps body in .data
    subs = body.get("licenses", []) or []                                # primary array row set
    amendments = body.get("amendments", []) or []                        # secondary array row set
    summary = body.get("summary", {}) or {}                              # consumed-count map
    snap = int(time.time())                                              # one snapshot timestamp for all maps
    summary_rows = [                                                     # flatten summary map into rows
        {"org_id": org_id, "license_type": k,                            # composite PK columns
         "consumed_count": v, "snapshot_time": snap}                     # value + snapshot
        for k, v in summary.items()                                      # one row per license type
    ]
    usage_rows = [                                                       # stack entitled/fully_loaded/usages
        {"org_id": org_id, "license_type": k, "metric": metric,          # composite PK columns
         "value": v, "snapshot_time": snap}                              # value + snapshot
        for metric in ("entitled", "fully_loaded", "usages")             # three source maps
        for k, v in (body.get(metric, {}) or {}).items()                 # one row per (type, metric)
    ]
    logging.debug(                                                       # action log AFTER fetch + flatten
        "License summary: subs=%d amendments=%d summary=%d usages=%d",
        len(subs), len(amendments), len(summary_rows), len(usage_rows),
    )
    for rows, name in (                                                  # one DataExporter call per row set
        (subs, "org_licenses_subscriptions"),                            # subscriptions table
        (amendments, "org_licenses_amendments"),                         # amendments table
        (summary_rows, "org_licenses_summary_counts"),                   # summary counts table
        (usage_rows, "org_licenses_usage_counts"),                       # usage counts table
    ):
        DataExporter.write_with_format_selection(                        # multi-backend dispatch
            rows, name, api_function_name="getOrgLicensesSummary",       # PK strategy lookup key
        )
```

## Quality gates (must all be green before commit)

```powershell
python -m py_compile MistHelper.py        # syntax check (no output on success)
python -m ruff check MistHelper.py        # lint must be clean
python -m black --check MistHelper.py     # format check (re-run without --check to auto-fix)
python MistHelper.py --test               # full sweep; new menu 96 runs against MIST_ORG_ID
```

After all four pass, follow the **Full Deployment Pipeline** in
`.github/copilot-instructions.md`: commit with `version YY.MM.DD.HH.MM - add
menu 96 getOrgLicensesSummary`, push, wait for container build, pull,
restart container, verify with `podman ps`.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `PermissionError: [Errno 13] Permission denied: '/app/data/...'` | Container's non-root user cannot write the mounted data dir | `chmod -R 777 data/` on the host before restart |
| `401 Unauthorized` in log | `MIST_API_TOKEN` invalid or expired | Regenerate the token in the Mist UI and update `.env` |
| `404 Not Found` in log | `org_id` does not belong to this token's tenant | Verify `MIST_ORG_ID` against the orgs the token can see |
| Four empty CSVs | Org has no purchased licenses | Expected; not an error. Menu logs "no data returned" and exits 0. |
| `429 Too Many Requests` | Rate limit hit | Adaptive delay system auto-backs-off via `delay_metrics.json`; rerun |

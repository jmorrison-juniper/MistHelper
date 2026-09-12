# Quickstart: countSiteAssets Menu Item

How to run, test, and validate the new MistHelper menu item that wraps the Mist
API endpoint `GET /api/v1/sites/{site_id}/stats/assets/count`.

## Required .env Variables

```ini
MIST_HOST=api.mist.com           # or your cloud's API host (e.g. api.eu.mist.com)
MIST_API_TOKEN=<your-api-token>  # never commit; loaded via python-dotenv
MIST_ORG_ID=<org-uuid>           # optional default; user may still be prompted
```

The API token must have at least read access on the target organization. Site
IDs are looked up at runtime via the existing menu item that lists sites
(operations 1-7) or supplied by hand at the prompt.

## Expected data/ Output

After a successful run the following files appear under `data/`:

```text
data/site_assets_count_summary.csv     # one row per invocation
data/site_assets_count_results.csv     # N rows, one per distinct bucket
data/mist_data.db                      # SQLite tables of the same names
```

If the active backend is ArangoDB+Redis, the same logical entities land in the
corresponding collections; CSV is always written as a local fallback.

## Local Run (Windows venv)

```powershell
# Activate venv (standard local environment)
.venv\Scripts\Activate.ps1

# Interactive run (recommended first invocation)
python MistHelper.py
# At the main menu, choose option 95 (countSiteAssets).
# Prompts:
#   Site ID (UUID):            <paste a known site UUID>
#   Distinct attribute (default: map_id):  <press Enter for default, or e.g. floor_id>
#   Limit (default 100, max 1000):         <press Enter for default>

# Non-interactive direct invocation (for automation / --test sweep)
python MistHelper.py --menu 95
```

## Containerized Run (Podman)

```powershell
# Pull latest
podman pull ghcr.io/jmorrison-juniper/misthelper:latest

# Start container (mounted data + .env)
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `
  -v "${PWD}/data:/app/data:rw" `
  -v "${PWD}/.env:/app/.env:ro" `
  ghcr.io/jmorrison-juniper/misthelper:latest

# SSH in and pick menu 95
ssh -p 2200 misthelper@localhost
```

## Expected Method Skeleton (illustrative; informs PASS verdict on 5-Item Rule)

```python
def export_site_assets_count(self, site_id, distinct=None, limit=100):
    # PROMPT and validate inputs via safe_input() so SSH/container EOF exits clean.
    site_id = site_id or safe_input("Site ID (UUID): ", context="site_assets_count:site_id")  # ask user
    if not _is_uuid(site_id):                                                                  # guard
        logging.warning("Invalid site_id; aborting export")                                    # log
        return                                                                                  # bail
    distinct = distinct or safe_input("Distinct (default map_id): ",                           # optional
                                       context="site_assets_count:distinct") or None           # empty -> None
    logging.info("Fetching asset count for site %s distinct=%s", site_id, distinct)            # before
    response = mistapi.api.v1.sites.stats_-_assets.countSiteAssets(                            # SDK call
        self.apisession, site_id, distinct=distinct, limit=limit)                              # named args
    payload = response.data or {}                                                              # envelope
    logging.debug("Asset count: total=%s buckets=%s", payload.get("total"),                    # after
                  len(payload.get("results", [])))                                              # count
    captured_at = int(time.time())                                                              # snapshot ts
    summary_row, result_rows = self._flatten_assets_count(site_id, payload, captured_at)        # split
    DataExporter.write_with_format_selection(                                                   # persist
        summary_row, "site_assets_count_summary",                                              # envelope
        api_function_name="countSiteAssets")                                                    # endpoint id
    DataExporter.write_with_format_selection(                                                   # persist
        result_rows, "site_assets_count_results",                                              # buckets
        api_function_name="countSiteAssets")                                                    # endpoint id
```

Line count: <=20 executable lines. Parameters: 4 (incl. self). Logical blocks:
prompt -> validate -> SDK call -> flatten -> two writes (5).

## Quality Gates (run before every commit)

```powershell
# Syntax check
python -m py_compile MistHelper.py

# Lint (must be clean)
python -m ruff check MistHelper.py

# Format (run without --check first to auto-fix)
python -m black --check MistHelper.py

# Project test sweep (skips heavy/destructive ops; menu 95 is in-scope)
python MistHelper.py --test
```

All four must exit 0 before pushing to `main`. The container build workflow
(`.github/workflows/container-build.yml`) validates again on GitHub-hosted
runners; CodeQL must also be green before the `auto-merge` label is added.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `PermissionError: '/app/data/...'` | Container data dir not writable | `chmod -R 777 data/` then re-run container |
| 401 from Mist API | Expired / wrong API token | Update `MIST_API_TOKEN` in `.env` |
| 404 from Mist API | Wrong site UUID | Pick a real site via menu items 1-7 |
| 429 from Mist API | Rate limited | Adaptive delay kicks in automatically; let it retry |
| Traceback on EOF | `input()` used instead of `safe_input()` | Bug -- file an issue; the new method must use `safe_input()` |

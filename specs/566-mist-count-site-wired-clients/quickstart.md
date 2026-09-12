# Phase 1 Quickstart: countSiteWiredClients (Menu 195)

How to run, validate, and ship the new menu item `countSiteWiredClients`
locally on Windows 11 and in the Podman container. Aimed at junior NOC
engineers -- clear language, no jargon. Mirrors the documented Mist API
endpoint at
`documentation/api/sites/GET_sites_site_id_wired_clients_count.md`.

## 1. Prerequisites

- Python 3.13 or newer.
- Active virtual environment: `.venv\Scripts\Activate.ps1` from the repo root.
- `pip install -r requirements.txt` (or `uv pip install -r requirements.txt`)
  including `mistapi>=0.59`.
- A `.env` file in the repo root containing valid credentials (template at
  `deploy/.env.example`).
- A site you have read access to in the target org.

## 2. Required `.env` Variables

| Variable | Required | Used For |
| - | - | - |
| `MIST_HOST` | Yes | Mist API host (`api.mist.com`, `api.eu.mist.com`, ...). |
| `MIST_API_TOKEN` | Yes | API token; never logged. |
| `MIST_ORG_ID` | Yes | Default org UUID, pre-fills the org prompt. |
| `MIST_SITE_ID` | Optional | If set, pre-fills the site prompt for `--test` runs. |
| `MIST_OUTPUT_BACKEND` | Optional | `csv` / `sqlite` / `arangodb`. Defaults to `sqlite`. |
| `MIST_PAGE_LIMIT` | Optional | Global pagination ceiling; the API default of 100 is used if unset. |

Secrets are loaded via `python-dotenv` through `mistapi.APISession`; nothing
in this menu item logs the token.

## 3. Expected Output Files Under `data/`

| Backend | File / Table | Behavior |
| - | - | - |
| CSV | `data/count_site_wired_clients.csv` | Appended with one summary row per run. |
| CSV | `data/count_site_wired_clients_results.csv` | Appended with N detail (bucket) rows per run. |
| SQLite | `data/mist_data.db` -> `count_site_wired_clients` table | Insert via `INSERT` (auto-increment PK). |
| SQLite | `data/mist_data.db` -> `count_site_wired_clients_results` table | Insert via `INSERT`. |
| ArangoDB | `count_site_wired_clients` collection | Document insert + edge to `sites` collection on `site_id`. |
| Redis | `cache:count_site_wired_clients:<site_id>:<distinct>` | Last-run snapshot cached for fast re-reads. |

The `data/` directory must be writable; on first container run the host
mount needs `chmod -R 777 data/`.

## 4. Interactive Invocation

```powershell
# From the repo root, with .venv activated
python MistHelper.py
# Menu prompt: type 195
# Prompt 1: Org ID [<MIST_ORG_ID from .env>]:        <Enter to accept>
# Prompt 2: Site ID:                                  6e7f4d4a-1234-5678-9abc-def012345678
# Prompt 3: Distinct field (mac/device_mac/port_id/vlan) [mac]: vlan
# Prompt 4: Duration (e.g. 1d, 7d, 2w) [1d]:          7d
# Prompt 5: Apply advanced filters? [y/N]:            N
```

The menu prints an ASCII progress line (no Unicode) such as:

```
[INFO] Fetching wired client count for site 6e7f4d4a... distinct=vlan duration=7d
[DEBUG] Wired client count payload: distinct=vlan total=42 results=12
[INFO] Wrote 1 summary row + 12 detail rows to backend=sqlite
```

Exit code is `0` on success and on a clean upstream 404 (a warning is
logged, no traceback emitted).

## 5. Direct (Non-Interactive) Invocation

For automation and the test sweep:

```powershell
python MistHelper.py --menu 195
```

When `MIST_SITE_ID` is set in `.env`, the menu accepts the default for the
site prompt and proceeds without further input -- this is how
`python MistHelper.py --test` drives the menu.

## 6. Container Invocation

After the deployment pipeline pushes the new image:

```powershell
podman pull ghcr.io/jmorrison-juniper/misthelper:latest
podman stop misthelper ; podman rm misthelper
podman run -d --name misthelper `
    -p 2200:2200 -p 8055:8055 `
    -v "${PWD}/data:/app/data:rw" `
    -v "${PWD}/.env:/app/.env:ro" `
    ghcr.io/jmorrison-juniper/misthelper:latest

# SSH in (default creds, change for prod)
ssh -p 2200 misthelper@localhost
# Then choose menu 195 at the prompt.
```

`safe_input()` ensures that EOF on the SSH channel exits with code 0; no
traceback reaches the client terminal.

## 7. Quality Gates (must be GREEN before commit)

Run all four locally; the container build job also runs the first three on
push and blocks merge if any fails.

```powershell
# 1. Syntax check -- silent success.
python -m py_compile MistHelper.py

# 2. Lint -- must pass clean.
python -m ruff check MistHelper.py

# 3. Formatter -- check-only (use without --check to auto-fix).
python -m black --check MistHelper.py

# 4. Functional smoke test for menu 195 specifically.
python MistHelper.py --menu 195
```

## 8. Method Skeleton (for the upcoming /speckit.tasks implementation)

This skeleton is *not* committed to MistHelper.py here -- it documents the
shape that the implementation task must produce, including the
Constitution VI inline comments and Constitution VII before/after action
logging on every executable line. Keep total length <=25 lines, <=5
parameters, <=5 logical blocks.

```python
def export_site_wired_clients_count(                                        # New SiteClientExporter method.
    self,                                                                   # Bound to SiteClientExporter instance.
    site_id: str,                                                           # Required path param (UUID).
    distinct_field: str = "mac",                                            # Bucket dimension; sensible default.
    duration: str = "1d",                                                   # Window size; matches API default.
    extra_filters: dict | None = None,                                      # Optional mac/device_mac/port_id/vlan/start/end/limit.
) -> None:                                                                  # Side-effect only (writes to DataExporter).
    logging.info("Counting wired clients for site %s distinct=%s", site_id, distinct_field)  # Before-action log.
    kwargs = {"distinct": distinct_field, "duration": duration} | (extra_filters or {})       # Merge optional filters.
    logging.debug("countSiteWiredClients kwargs=%s", kwargs)                                   # Echo filters at debug.
    response = wired_clients_count.countSiteWiredClients(self.session, site_id, **kwargs)      # SDK call (GET).
    payload = response.data                                                                    # Parsed JSON dict.
    logging.debug("Response total=%s results=%d", payload.get("total"), len(payload.get("results", [])))  # After-action log.
    summary, details = self._flatten_count_payload(site_id, payload, kwargs)                   # Flatten to row(s).
    logging.info("Persisting count_site_wired_clients summary + %d detail rows", len(details)) # Before-write log.
    DataExporter.write_with_format_selection(                                                  # Multi-backend export.
        {"summary": [summary], "results": details},                                            # Two collections, one call.
        "count_site_wired_clients",                                                            # Filename / table base.
        api_function_name="countSiteWiredClients",                                             # Drives PK strategy lookup.
    )                                                                                          # Returns when persistence is done.
    logging.debug("Persistence complete for site=%s distinct=%s", site_id, distinct_field)     # After-write log.
```

`_flatten_count_payload` is a private helper on the same
`SiteClientExporter` class; it converts the API JSON into the two row
shapes defined in `data-model.md` and stays under the 25-line / 5-block
budget on its own.

# Quickstart: Menu 195 -- Export Org SSL Proxy Certificate

Run the new menu item locally against a real Mist org.

## Prerequisites

- Python 3.13+ available in the active venv (`.venv\Scripts\Activate.ps1`
  on Windows 11 dev host).
- `pip install -r requirements.txt` (or `uv pip install -r
  requirements.txt`). Key dep: `mistapi >= 0.59`.
- A valid `.env` in the repo root -- see next section.
- Read access on the target organisation (the API token principal must
  have at least `read` scope on `/orgs/{org_id}`).

## Required `.env` variables

```dotenv
MIST_HOST=api.mist.com                 # Or api.eu.mist.com / api.gc1.mist.com / api.ac2.mist.com per region
MIST_API_TOKEN=<your-mist-api-token>   # Never commit; loaded via python-dotenv
MIST_ORG_ID=<default-org-uuid>         # Optional: prompt defaults to this value
```

Optional:

```dotenv
MISTHELPER_OUTPUT_BACKEND=csv          # csv | sqlite | polyglot (arangodb+redis)
MIST_PAGE_LIMIT=1000                   # Ignored for this non-paginated endpoint
```

## How to run

### Interactive

```powershell
# From the repo root, venv activated:
python MistHelper.py
# At the menu prompt:
195
# At the org prompt (press Enter to accept MIST_ORG_ID from .env, or type another UUID):
<paste-org-uuid-or-Enter>
```

### Non-interactive (automation / CI)

```powershell
python MistHelper.py --menu 195
# Uses MIST_ORG_ID from .env; safe_input() sees EOF and falls through cleanly.
```

### Example session

```text
$ python MistHelper.py --menu 195
2026-06-30 23:15:03 INFO  Loaded .env: MIST_HOST=api.mist.com org=****redacted****
2026-06-30 23:15:03 INFO  Menu 195 selected: getOrgSslProxyCert
Enter organization UUID [default: MIST_ORG_ID from .env]:
2026-06-30 23:15:04 INFO  Using org_id from .env
2026-06-30 23:15:04 INFO  Fetching SSL proxy certificate for org 203d3d02-****
2026-06-30 23:15:04 DEBUG SSL proxy cert response received: cert_len=1487 bytes
2026-06-30 23:15:04 INFO  Flattening SSL proxy cert response into 1 row
2026-06-30 23:15:04 DEBUG Flatten complete: rows=1
2026-06-30 23:15:04 INFO  Writing SSL proxy cert to data/org_ssl_proxy_cert_203d3d02-****.csv
2026-06-30 23:15:04 INFO  DataExporter: wrote 1 row(s) via backend=csv
2026-06-30 23:15:04 INFO  Menu 195 complete: exit=0
```

## Expected `data/` output

| Backend  | Artifact |
|----------|----------|
| CSV      | `data/org_ssl_proxy_cert_<org_id>.csv` -- header row + 1 data row. |
| SQLite   | `data/mist_data.db` gains table `org_ssl_proxy_cert` (created on first run by `DatabaseSchemaUtils`). Row upserts on `org_id`. |
| Polyglot | ArangoDB document collection `org_ssl_proxy_cert` with `_key=<org_id>`; Redis cache key `org_ssl_proxy_cert:<org_id>`. |

## Method outline (for reference during Phase 2 task work)

The new public method on `OrgConfigExporter` (line ~11995 in
`MistHelper.py`) is expected to look like this (inline comments retained
per Constitution Principle VI; action logging per Principle VII):

```python
@classmethod
def export_org_ssl_proxy_cert(cls) -> None:
    """Export the org-level SSL proxy inspection certificate (menu 195)."""
    org_id = safe_input(                                                                  # Collect org id; safe_input handles EOF cleanly in SSH/container
        "Enter organization UUID [default: MIST_ORG_ID from .env]: ",
        context="org_ssl_proxy_cert:org_id",
    ).strip() or os.environ.get("MIST_ORG_ID", "").strip()                                # Fall back to .env default so automation runs headless
    if not ValidationUtils.is_valid_uuid(org_id):                                         # Validate before any network call to fail fast
        logging.warning("Invalid or missing org_id for menu 195; aborting")               # ASCII-only WARNING per Principle V
        return                                                                            # Early return keeps 5-Item Rule intact
    session = ConfigUtils.get_shared_mist_session()                                       # Reuse the singleton mistapi.APISession built from .env
    logging.info("Fetching SSL proxy certificate for org %s", org_id)                     # INFO before the API call per Principle VII
    response = mistapi.api.v1.orgs.cert.getOrgSslProxyCert(session, org_id)               # Read-only GET; single JSON object response
    cert_body = (response.data or {}).get("cert") or ""                                   # Guard against empty body / missing key
    logging.debug("SSL proxy cert response received: cert_len=%d bytes", len(cert_body))  # DEBUG after the call with size only, never the PEM itself
    logging.info("Flattening SSL proxy cert response into 1 row")                         # INFO before flatten per Principle VII
    rows = [                                                                              # Wrap in a list so DataExporter receives its expected shape
        {
            "org_id":     org_id,                                                         # Injected natural PK; not in raw response
            "cert":       cert_body or None,                                              # None -> SQL NULL when no cert configured
            "cert_len":   len(cert_body),                                                 # Convenience column for quick presence checks
            "fetched_at": datetime.now(timezone.utc).isoformat(),                         # UTC ISO-8601 audit timestamp
        }
    ]
    logging.debug("Flatten complete: rows=%d", len(rows))                                 # DEBUG after flatten per Principle VII
    filename = f"org_ssl_proxy_cert_{org_id}.csv"                                         # Convention: <endpoint_snake>_<scope>.csv
    logging.info("Writing SSL proxy cert to data/%s", filename)                           # INFO before write per Principle VII
    DataExporter.write_with_format_selection(                                             # Multi-backend fan-out (CSV/SQLite/ArangoDB+Redis)
        data=rows,
        filename=filename,
        api_function_name="getOrgSslProxyCert",                                           # Enables PK strategy lookup in ENDPOINT_PRIMARY_KEY_STRATEGIES
    )
```

Line count: 20 executable lines (well under the 25-line Five-Item Rule
ceiling). Parameters: 0 (implicit `cls`). Logical blocks: 5 (prompt ->
validate -> API call -> flatten -> export).

## Menu registration

Append to the main dispatch table in `MistHelper.py` (currently around
line ~22267):

```python
"195": (                                                                                  # Next available integer above current top 194
    OrgConfigExporter.export_org_ssl_proxy_cert,                                          # Class method; no wrapper function
    "Export org SSL proxy inspection certificate (getOrgSslProxyCert)",                   # Menu label shown to the NOC engineer
),
```

## Quality gates (must all pass before commit)

```powershell
# 1. Syntax
python -m py_compile MistHelper.py

# 2. Lint (must be clean; no --fix in CI)
python -m ruff check MistHelper.py

# 3. Format (use --check in CI, or run without --check to auto-fix locally)
python -m black --check MistHelper.py

# 4. Full non-interactive sweep -- new menu 195 is inside the default range
python MistHelper.py --test

# 5. (Container path only) after commit + push, watch the build
gh run list --workflow=container-build.yml --limit 1
gh run watch <run-id>
```

## Rollback

The change is additive (one method, one dict entry, one menu row, one
SQLite table auto-created on first run). To roll back, revert the
commit and drop the SQLite table:

```sql
DROP TABLE IF EXISTS org_ssl_proxy_cert;
```

The `data/org_ssl_proxy_cert_*.csv` files are safe to delete at any
time; they will be regenerated on next run.

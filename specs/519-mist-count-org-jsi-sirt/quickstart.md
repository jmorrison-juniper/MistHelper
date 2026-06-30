# Phase 1 Quickstart: countOrgJsiSirt (menu 219)

**Feature**: 519-mist-count-org-jsi-sirt
**Date**: 2026-06-28
**Audience**: A developer (or AI agent) preparing to implement the menu item locally.

## 1. Prerequisites

- Python 3.13+ installed and on `PATH`.
- Repository worktree checked out at
  `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper.worktrees\copilot-openapi-mist-api-endpoint-cataloging`.
- Virtual environment activated:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- Dependencies installed:
  ```powershell
  pip install -r requirements.txt
  ```
- A valid Mist API token with read access to the target org.

## 2. Required `.env` variables

Create or edit `.env` (git-ignored) at the repo root:

```dotenv
MIST_HOST=api.mist.com
MIST_API_TOKEN=<your_token>
MIST_ORG_ID=<your_org_uuid>   # optional; menu item prompts and falls back to this
```

`MIST_ORG_ID` is optional. If set, the menu item uses it as the default `org_id`
prompt value so `--test` invocations work non-interactively.

## 3. Expected `data/` output

After a successful run:

| Backend | Artifact |
|---------|----------|
| CSV | `data/org_<org_id>_jsi_sirt_count_<distinct>.csv` |
| SQLite | Rows in table `org_jsi_sirt_count` inside `data/mist_data.db` |
| ArangoDB + Redis (if active) | Documents in `org_jsi_sirt_count` collection plus Redis cache keys keyed on the composite PK |

The `data/` directory must already exist and be writable by the running user. In the
container, this is satisfied by:

```powershell
chmod -R 777 data\
```

run once on the host before the first container start (the container user is non-root).

## 4. Example invocation (interactive)

```powershell
python MistHelper.py --menu 219
```

Prompt sequence:

```
Enter org_id [<MIST_ORG_ID default>]: <press Enter to accept default>
Enter distinct field [jsa_updated_date | models | severity | versions]: severity
Enter start (epoch seconds or relative like -1w, blank to omit): -1w
Enter end (epoch seconds or relative like now, blank to omit): now
```

Expected log tail (ASCII-only, `%s` formatted):

```
INFO  Fetching JSI SIRT count for org 11111111-2222-3333-4444-555555555555 distinct=severity
DEBUG JSI SIRT count: total=42 groups=4
INFO  Flattening 4 SIRT count rows
DEBUG Flatten complete: 4 rows ready for export
INFO  Writing org_jsi_sirt_count via DataExporter
DEBUG Wrote 4 rows to org_jsi_sirt_count (CSV + SQLite)
```

## 5. Example invocation (non-interactive `--test`)

```powershell
python MistHelper.py --test
```

The test harness skips heavy/destructive operations (14, 18, 63-65, 90-100) and runs
the rest. Menu 219 is read-only and stays in the default sweep; it consumes
`MIST_ORG_ID` from `.env`, defaults `distinct` to `severity`, and omits `start` / `end`
so the API picks defaults.

## 6. Method outline (target shape in `MistHelper.py`)

```python
class JsiSirtExportUtils:                                               # New owning class for JSI/SIRT exports
    def export_org_jsi_sirt_count(self, org_id, distinct, **window):    # Public menu method, <=5 params (window collapses start/end)
        logging.info("Prompting for JSI SIRT count parameters")         # Action log: before prompt phase
        org_id = self._resolve_org_id(org_id)                           # Fall back to MIST_ORG_ID env var if empty
        distinct = self._validate_distinct(distinct)                    # Enforce enum membership (jsa_updated_date|models|severity|versions)
        if not distinct:                                                # Early return on validation failure
            logging.warning("countOrgJsiSirt: invalid distinct value")  # Log and exit cleanly without traceback
            return                                                      # Return 0 rows -- caller handles None
        logging.info("Fetching JSI SIRT count for org %s distinct=%s",  # Action log: before API call
                     org_id, distinct)
        response = mistapi.api.v1.orgs.jsi.countOrgJsiSirt(             # Single SDK call, no manual retry loop
            self.session, org_id, distinct,
            start=window.get("start"), end=window.get("end"))
        payload = response.data                                         # Extract dict; mistapi wraps the JSON
        logging.debug("JSI SIRT count: total=%s groups=%s",             # Action log: after API call
                      payload.get("total"), len(payload.get("results", [])))
        rows = self._flatten_count_results(org_id, payload)             # Denormalize envelope onto each row
        logging.info("Writing org_jsi_sirt_count via DataExporter")     # Action log: before write
        DataExporter.write_with_format_selection(                       # Multi-backend write -- CSV / SQLite / ArangoDB
            rows,
            filename=f"org_{org_id}_jsi_sirt_count_{distinct}.csv",
            api_function_name="countOrgJsiSirt")                        # Resolves PK strategy registered in ENDPOINT_PRIMARY_KEY_STRATEGIES
        logging.debug("Wrote %s rows to org_jsi_sirt_count", len(rows)) # Action log: after write
```

Notes:

- Every executable line above carries an inline `#` comment per Principle VI.
- `safe_input()` lives inside `_resolve_org_id` and the menu-dispatch shim that calls
  this method -- both prompt for `org_id`, `distinct`, `start`, `end` with explicit
  `context=` strings.
- `_flatten_count_results` and `_validate_distinct` are private helpers on the same
  `JsiSirtExportUtils` class -- no module-level wrappers.

## 7. Quality gates (run before every commit)

```powershell
python -m py_compile MistHelper.py        # Syntax check; silent on success
python -m ruff check MistHelper.py        # Lint must pass clean
python -m black --check MistHelper.py     # Format must pass clean (omit --check to fix)
python MistHelper.py --test               # Functional sweep (requires .env with valid token)
```

All four must exit 0 before staging the change.

## 8. Commit + container pipeline (after gates pass)

```powershell
git add MistHelper.py README.md CHANGELOG.md
git commit -m "version YY.MM.DD.HH.MM - add menu 219 countOrgJsiSirt"
git push origin main
gh run list --workflow=container-build.yml --limit 1
gh run watch <run-id>
podman pull ghcr.io/jmorrison-juniper/misthelper:latest
podman stop misthelper ; podman rm misthelper
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `
  -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" `
  ghcr.io/jmorrison-juniper/misthelper:latest
podman ps
```

The full pipeline is documented in `.github/copilot-instructions.md`; do not skip
steps. The destructive-op gate does not apply (menu 219 is read-only) but the
build / pull / restart steps are still mandatory.

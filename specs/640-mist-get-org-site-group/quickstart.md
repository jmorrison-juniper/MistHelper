# Phase 1 Quickstart: getOrgSiteGroup (Menu 95)

**Feature**: `640-mist-get-org-site-group`
**Endpoint**: `GET /api/v1/orgs/{org_id}/sitegroups/{sitegroup_id}`
**Date**: 2026-06-30

Local developer walkthrough for exercising the new menu item end-to-end on
Windows 11 + venv. All commands assume the repo root working directory:
`C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper.worktrees\copilot-openapi-mist-api-endpoint-cataloging`.

## 1. Required `.env` Variables

Add these to the git-ignored `.env` at the repo root before running:

```dotenv
MIST_HOST=api.mist.com                # or api.eu.mist.com / api.gc1.mist.com
MIST_API_TOKEN=<your-personal-token>  # from Mist UI > My Account > API Tokens
MIST_ORG_ID=<default-org-uuid>        # optional; used as default at prompt 1
```

The API token is loaded through the existing `mistapi.APISession` and is
never echoed to logs.

## 2. Activate the Local Virtual Environment

```powershell
.venv\Scripts\Activate.ps1
```

## 3. Run the Menu Item Interactively

```powershell
python MistHelper.py --menu 95
```

Interactive prompts (both via `safe_input()`):

```
Enter org_id [default from MIST_ORG_ID]: <press Enter to accept default>
Enter sitegroup_id: 53f10664-3ce8-4c27-b382-0ef66432349f
```

Expected console log lines (ASCII only, `%s` formatting):

```
INFO  Fetching site group 53f10664-... for org a97c1b22-...
DEBUG Site group name=Retail-East site_count=42
INFO  Flattening site_ids array (count=42) for storage
DEBUG Flattened row written to buffer
INFO  Writing 1 row via DataExporter (target=sqlite|csv|arango)
```

## 4. Expected `data/` Output

CSV backend (default when no other backend configured):

```
data/org_site_group_a97c1b22-a4e9-411e-9bfd-d8695a0f9e61_53f10664-3ce8-4c27-b382-0ef66432349f.csv
```

SQLite backend (`data/mist_data.db`): row appears in table `org_site_groups`.
Re-run the menu item -- row is upserted (INSERT OR REPLACE on `id`) with no
duplicate.

ArangoDB backend: document appears in collection `org_site_groups`; a graph
edge from the org vertex to the site-group vertex is created (per the
existing polyglot exporter).

## 5. Non-Interactive Test Sweep

```powershell
python MistHelper.py --test
```

Menu 95 falls inside the default sweep window (skip list unchanged: 14, 18,
63-65, 90-100 heavy/destructive, 154-194 destructive). The test invokes the
method with `MIST_ORG_ID` and a probe `sitegroup_id` sourced from a test
fixture; a successful test writes exactly one row to the configured backend
and exits 0.

## 6. Quality Gates (run before every commit)

```powershell
python -m py_compile MistHelper.py     # syntax check; no output = pass
python -m ruff check MistHelper.py     # style + lint; must be clean
python -m black --check MistHelper.py  # format check; drop --check to auto-fix
```

All three must pass before committing.

## 7. Reference Method Sketch (~22 lines, comments per Principle VI)

```python
def export_org_site_group(self, org_id: str, sitegroup_id: str) -> None:
    """Retrieve a single org site group and persist via DataExporter."""
    if not self._is_uuid(org_id):                                 # UUID pre-check saves an API call
        logging.warning("Invalid org_id shape: %s", org_id)       # ASCII-only warning
        return                                                    # early exit -- no traceback
    if not self._is_uuid(sitegroup_id):                           # same guard for sitegroup_id
        logging.warning("Invalid sitegroup_id shape: %s", sitegroup_id)
        return
    logging.info("Fetching site group %s for org %s",             # Principle VII: log before
                 sitegroup_id, org_id)
    response = mistapi.api.v1.orgs.sitegroups.getOrgSiteGroup(    # sole permitted transport
        self.mist_session, org_id, sitegroup_id                   # positional args per SDK
    )
    payload = response.data or {}                                 # tolerate empty body on 404
    if not payload:                                                # empty payload -> clean exit
        logging.warning("No site group returned for %s", sitegroup_id)
        return
    logging.debug("Site group name=%s site_count=%d",             # Principle VII: log after
                  payload.get("name"), len(payload.get("site_ids") or []))
    filename = f"org_site_group_{org_id}_{sitegroup_id}.csv"      # deterministic per-invocation name
    self.data_exporter.write_with_format_selection(               # multi-backend fan-out
        [payload], filename, api_function_name="getOrgSiteGroup"  # operationId drives PK strategy
    )
```

Line count: 22 executable lines (excluding the docstring, blank lines, and
closing parentheses that Principle I explicitly exempts). Parameter count: 3
(`self`, `org_id`, `sitegroup_id`). Logical blocks: 5 (validate -> log-before
-> API call -> log-after -> export). All limits satisfied.

## 8. Post-Implementation Deployment Pipeline

After the quality gates pass locally:

```powershell
git add MistHelper.py README.md CHANGELOG.md
git commit -m "version YY.MM.DD.HH.MM - add menu 95 getOrgSiteGroup"
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

Do not skip any step; the container must be running the new build before the
task is considered done.

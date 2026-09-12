# Phase 1 Quickstart: getOrgSsoRole (Menu 46)

**Feature**: 644-mist-get-org-sso-role

## What this menu item does

Fetches the full detail of a single Mist SSO role -- including its IdP-attribute-
to-Mist-RBAC privilege mapping -- via
`GET /api/v1/orgs/{org_id}/ssoroles/{ssorole_id}` and writes two related tables
(`org_sso_role_summary` and `org_sso_role_privileges`) to the active output backend
(CSV, SQLite, or ArangoDB+Redis).

## Required `.env` variables

Only the standard MistHelper credentials are needed. No new variables introduced.

```dotenv
MIST_HOST=api.mist.com                        # Regional Mist API host
MIST_API_TOKEN=your-mist-api-token            # Never logged, never printed
MIST_ORG_ID=60f6bfdb-2f45-4022-8e2a-e00d977953fe   # Optional default org prompt
```

`MIST_HOST` and `MIST_API_TOKEN` are loaded automatically by `mistapi.APISession`.
`MIST_ORG_ID` (if present) becomes the default value shown to the user at the
`org_id` prompt; if absent the user must type the UUID.

## Expected output filenames

```text
data/mist_data.db                                       # SQLite backend (default fallback)
data/org_sso_role_summary_<org8>_<role8>.csv            # CSV backend
data/org_sso_role_privileges_<org8>_<role8>.csv         # CSV backend
```

Where `<org8>` and `<role8>` are the first 8 hex characters of the org UUID and the
SSO role UUID, respectively.

For ArangoDB+Redis, records land in the `org_sso_role_summary` and
`org_sso_role_privileges` collections plus their Redis caches; graph edges to the
parent org and to any referenced sites/sitegroups are created per the existing
polyglot pipeline.

## Running the menu item locally

### Interactive (Windows 11 + venv)

```powershell
.\.venv\Scripts\Activate.ps1                            # Activate the venv
python MistHelper.py                                    # Launch the menu
# At the prompt: type 46
# When prompted for org_id: paste the org UUID or press Enter to accept the .env default
# When prompted for ssorole_id: paste the SSO role UUID
```

### Non-interactive (direct invocation)

```powershell
python MistHelper.py --menu 46
```

`safe_input()` reads from stdin when the process is attached to a pipe, so:

```powershell
"60f6bfdb-2f45-4022-8e2a-e00d977953fe`n53f10664-3ce8-4c27-b382-0ef66432349f" | python MistHelper.py --menu 46
```

### Inside the container (SSH on 2200)

```powershell
ssh -p 2200 misthelper@localhost                        # Password prompt if enabled
# Menu launches directly (ForceCommand). Enter 46, then the two UUIDs.
```

## Expected console flow

```text
=== Menu 46: Get Org SSO Role Details (getOrgSsoRole) ===
Org id [60f6bfdb-2f45-4022-8e2a-e00d977953fe]: <enter>
SSO role id: 53f10664-3ce8-4c27-b382-0ef66432349f
INFO Fetching SSO role 53f10664 for org 60f6bfdb
DEBUG SSO role fetched: name=NOC-ReadOnly privileges=3 for_site=False
INFO Flattening SSO role response into summary + privilege rows
DEBUG Flatten complete: summary_rows=1 privilege_rows=3
INFO Writing SSO role export via DataExporter (backend=sqlite)
Menu 46 complete: 1 summary row, 3 privilege rows.
```

## Method outline (for implementation reference)

Sketch only -- the final implementation must add an inline comment on every executable
line per Principle VI. This outline is annotated to show the required density.

```python
def export_org_sso_role(self, org_id: str, ssorole_id: str) -> None:  # New op 46 on OrgAdminExporter
    if not ValidationUtils.is_uuid(org_id):                            # Reject bad org UUID before API call
        logging.warning("Invalid org_id %s -- aborting menu 46", org_id)   # Log why we bail
        return                                                          # Early return per Safety-First
    if not ValidationUtils.is_uuid(ssorole_id):                        # Same guard for role UUID
        logging.warning("Invalid ssorole_id %s -- aborting", ssorole_id)  # Log why we bail
        return                                                          # Early return per Safety-First
    logging.info("Fetching SSO role %s for org %s", ssorole_id[:8], org_id[:8])   # Before-call log (Principle VII)
    response = mistapi.api.v1.orgs.sso_roles.getOrgSsoRole(            # Only permitted Mist transport
        self.apisession, org_id, ssorole_id                             # Positional args per SDK signature
    )
    role = response.data or {}                                          # Guard against None payloads
    privileges = role.get("privileges", []) or []                       # Guard against missing key
    logging.debug(                                                      # After-call log (Principle VII)
        "SSO role fetched: name=%s privileges=%d for_site=%s",
        role.get("name"), len(privileges), role.get("for_site"),
    )
    summary_row = self._flatten_sso_role_summary(org_id, role)         # One row, no cartesian bloat
    privilege_rows = self._flatten_sso_role_privileges(                 # Zero or more rows
        org_id, ssorole_id, privileges,
    )
    DataExporter.write_with_format_selection(                           # Multi-backend export (Principle II)
        [summary_row], "org_sso_role_summary", api_function_name="getOrgSsoRole",
    )
    DataExporter.write_with_format_selection(
        privilege_rows, "org_sso_role_privileges", api_function_name="getOrgSsoRole",
    )
```

The two private helpers `_flatten_sso_role_summary()` and
`_flatten_sso_role_privileges()` live on the same class; each stays inside the
25-line / 5-block / 5-param structural limits.

## Prompt collection (uses `safe_input()`)

```python
default_org = ConfigUtils.get_default_org_id() or ""                        # From MIST_ORG_ID
prompt_org = f"Org id [{default_org}]: " if default_org else "Org id: "     # Compose prompt
org_id = safe_input(prompt_org, context="org_sso_role:org_id") or default_org  # EOF-safe
ssorole_id = safe_input("SSO role id: ", context="org_sso_role:ssorole_id")    # No default
```

## Quality gates (must all be green before commit)

Run these from the repo root before pushing. Each is a hard blocker per the
Full Deployment Pipeline (Principle IV).

```powershell
python -m py_compile MistHelper.py                     # Syntax gate -- silent on success
python -m ruff check MistHelper.py                     # Lint gate -- must pass clean
python -m black --check MistHelper.py                  # Format gate -- run without --check to auto-fix
python MistHelper.py --test                            # Regression sweep (menu 46 in default range)
```

If any gate fails, fix the code, re-run all four, and only then commit. Never bypass
a gate. Never push a red gate.

## Post-commit deployment pipeline

Follow the full documented pipeline in `.github/copilot-instructions.md`:

1. `git add MistHelper.py README.md CHANGELOG.md`
2. `git commit -m "version YY.MM.DD.HH.MM - add menu 46 getOrgSsoRole"`
3. `git push origin main`
4. `gh run watch <workflow-run-id>` -- wait for container build to succeed.
5. `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`
6. `podman stop misthelper ; podman rm misthelper`
7. `podman run -d --name misthelper -p 2200:2200 -p 8055:8055 -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" ghcr.io/jmorrison-juniper/misthelper:latest`
8. `podman ps` to confirm the container is up.

## Troubleshooting

- **`PermissionError: /app/data/script.log`**: run `chmod -R 777 data/` on the host
  and re-launch the container. The container runs as a non-root user.
- **404 from the SDK call**: the `ssorole_id` does not exist under this `org_id`.
  MistHelper logs a warning and exits 0; no traceback is produced.
- **429 rate limit**: the adaptive delay system in `delay_metrics.json` handles
  back-off transparently. If persistent, wait until the hourly quota resets.
- **EOFError in SSH**: cannot happen -- `safe_input()` traps `EOFError` and exits 0
  cleanly. If you see a traceback, `safe_input()` was bypassed and the code must be
  fixed.

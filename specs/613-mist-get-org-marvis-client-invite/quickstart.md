# Phase 1 Quickstart: getOrgMarvisClientInvite (Menu 195)

**Feature**: 613-mist-get-org-marvis-client-invite
**Date**: 2026-06-30
**Audience**: Junior NOC engineer running MistHelper locally or in the container.

## What this menu item does

Fetches a single Marvis Client Invite record from a Mist organization and
writes it to your configured output backend (CSV, SQLite, or
ArangoDB+Redis). The Marvis Client Invite carries the `provision_url`
required by an MDM (Mobile Device Management) install command to bootstrap
the Marvis mobile SDK on a managed device.

## Prerequisites

### Required `.env` variables

```dotenv
MIST_HOST=api.mist.com                                # Mist Cloud region host
MIST_API_TOKEN=<your-api-token>                       # Read-only token is sufficient
MIST_ORG_ID=<default-org-uuid>                        # Optional default for the org_id prompt
```

`MIST_API_TOKEN` is never logged. `MIST_ORG_ID` is optional -- if unset, the
menu prompts for `org_id` with no default.

### Required arguments at runtime

| Prompt              | Source                  | Validation                         |
|---------------------|-------------------------|------------------------------------|
| `org_id`            | `.env` or interactive   | Must match Mist UUID shape         |
| `marvisinvite_id`   | Interactive only        | Must match Mist UUID shape         |

Both are collected with `safe_input()` so SSH and container sessions that
disconnect exit cleanly (return code 0, no traceback).

## How to run it

### Interactive (menu-driven)

```powershell
.venv\Scripts\Activate.ps1                            # Activate the project venv
python MistHelper.py                                  # Launch the interactive menu
# Then select option 195: "Get Org Marvis Client Invite"
```

You will be prompted:

```text
Enter org_id (or press Enter for MIST_ORG_ID from .env): <Enter>
Enter marvisinvite_id (UUID of the Marvis client invite): 53f10664-3ce8-4c27-b382-0ef66432349f
```

### Direct invocation (automation)

```powershell
python MistHelper.py --menu 195
```

Direct invocation still uses `safe_input()` for prompts that are not piped on
stdin. To fully scripted-run, pipe answers:

```powershell
"`n53f10664-3ce8-4c27-b382-0ef66432349f`n" | python MistHelper.py --menu 195
```

### Containerized run

```powershell
podman exec -it misthelper python /app/MistHelper.py --menu 195
```

## Expected output

### CSV backend (default fallback)

```text
data\org_marvis_client_invite.csv
```

Columns (in order):
`id, name, disabled, provision_url, org_id, last_seen_at`

### SQLite backend

```text
data\mist_data.db
```

Table: `org_marvis_client_invite` (created automatically on first run from
the `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry).

Re-running the menu item upserts the same row by `id` -- no duplicates.

### ArangoDB + Redis backend

Document inserted into the `org_marvis_client_invite` ArangoDB collection
with `_key = <invite_id>`; Redis cache key `mist:org_marvis_client_invite:<id>`
is refreshed.

## Example output (CSV)

```csv
id,name,disabled,provision_url,org_id,last_seen_at
53f10664-3ce8-4c27-b382-0ef66432349f,Handhelds,False,https://api.mist.com/path/to/url,c4e3a1...,2026-06-30T20:03:47Z
```

## Example method outline (for review)

```python
def export_org_marvis_client_invite(                                 # New method on MarvisInviteOperations
    self,                                                            # Instance carries the apisession
    org_id: str | None = None,                                       # Optional caller-supplied org UUID
    marvisinvite_id: str | None = None,                              # Optional caller-supplied invite UUID
) -> int:                                                            # Returns exit code (0 = success)
    org_id = org_id or safe_input(                                   # Prompt only when caller did not supply
        "Enter org_id (or press Enter for MIST_ORG_ID from .env): ", # Human-readable prompt
        context="org_marvis_client_invite:org_id",                   # Stable EOF context label
    ) or os.environ.get("MIST_ORG_ID", "")                           # Fall back to .env default
    marvisinvite_id = marvisinvite_id or safe_input(                 # Prompt for the resource identifier
        "Enter marvisinvite_id (UUID of the Marvis client invite): ",# Prompt text
        context="org_marvis_client_invite:marvisinvite_id",          # Stable EOF context label
    )
    if not _is_uuid(org_id) or not _is_uuid(marvisinvite_id):        # Validate both UUIDs before API call
        logging.warning("Invalid UUID input -- aborting before API call")  # ASCII-only warn
        return 1                                                     # Non-zero exit on validation failure
    logging.info(                                                    # INFO before SDK call (Principle VII)
        "Fetching Marvis client invite %s for org %s",               # ASCII-only template
        marvisinvite_id, org_id,                                     # No tokens in the message
    )
    resp = mistapi.api.v1.orgs.marvis_invites.getOrgMarvisClientInvite(  # Mist API call via SDK
        self.apisession, org_id, marvisinvite_id,                    # Required path params
    )
    invite = resp.data or {}                                         # Empty dict guard for 404 / empty body
    logging.debug(                                                   # DEBUG after SDK call (Principle VII)
        "Marvis invite retrieved: name=%s disabled=%s",              # Result summary, no provision_url
        invite.get("name"), invite.get("disabled"),                  # Pull only the safe-to-log fields
    )
    invite["org_id"] = org_id                                        # Inject parent scope for SQLite join
    DataExporter.write_with_format_selection(                        # Multi-backend export
        [invite],                                                    # Wrap single object in list shape
        "org_marvis_client_invite",                                  # Filename / table base name
        api_function_name="getOrgMarvisClientInvite",                # PK strategy lookup key
    )
    return 0                                                         # Success
```

Every executable line above carries an inline comment per Constitution
Principle VI (NON-NEGOTIABLE).

## Quality gates (run before commit)

```powershell
python -m py_compile MistHelper.py                    # Syntax check (silent = pass)
python -m ruff check MistHelper.py                    # Lint -- must be clean
python -m black --check MistHelper.py                 # Format check -- run without --check to autofix
python MistHelper.py --test                           # Test sweep (menu 195 is inside the default range)
```

All four must pass before the standard deployment pipeline (commit ->
push -> container-build workflow -> `podman pull` -> restart -> `podman ps`)
is executed.

## Troubleshooting

| Symptom                                  | Likely cause                                                    | Fix                                                              |
|------------------------------------------|-----------------------------------------------------------------|------------------------------------------------------------------|
| `Invalid UUID input -- aborting...`      | User entered a non-UUID for one of the IDs                      | Re-enter using `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` format     |
| `WARNING ... 404 ...`                    | The `marvisinvite_id` does not exist in the supplied org        | Verify with the future list endpoint (menu 196) or the Mist UI   |
| `ERROR ... 401 ...`                      | Missing / invalid `MIST_API_TOKEN`                              | Refresh the token in `.env`, restart the container if running    |
| `ERROR ... 429 ...`                      | API quota exceeded                                              | Adaptive delay (`delay_metrics.json`) absorbs this -- just retry |
| `PermissionError on data/...`            | Container `data/` dir is not 0777                               | `chmod -R 777 data/` (see container instructions)                |

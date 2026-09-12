# Phase 1 Quickstart: getOrgNacPortal Menu Item

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md) | **Data model**: [data-model.md](./data-model.md)
**Contract**: [contracts/get_org_nac_portal.md](./contracts/get_org_nac_portal.md)

## Required `.env` Variables

Set the following in the repo-root `.env` (git-ignored) before running the
menu item:

```ini
# Mist Cloud authentication (required)
MIST_HOST=api.mist.com                # Cloud region host
MIST_API_TOKEN=<your-api-token>       # Read-only token is sufficient

# Org default for interactive prompts (recommended)
MIST_ORG_ID=<your-org-uuid>           # Used when the Org ID prompt is empty

# Optional -- used by `python MistHelper.py --test` only
MIST_TEST_NACPORTAL_ID=<known-portal-uuid>   # Skips the op if absent
```

The API token is loaded by the existing `mistapi.APISession` and is never
echoed to stdout, logs, or saved output. Output files live under `data/`.

## Expected Output Files

A single invocation produces, under `data/`:

| File | Backend | Notes |
|------|---------|-------|
| `data/org_nac_portal.csv` | CSV | One row per portal (this run: exactly 1) |
| `data/org_nac_portal_sso.csv` | CSV | One row if `sso` populated, else absent |
| `data/org_nac_portal_sso_role_matching.csv` | CSV | One row per role-match entry |
| `data/mist_data.db` (tables: `org_nac_portal`, `org_nac_portal_sso`, `org_nac_portal_sso_role_matching`) | SQLite | Upserts on the composite PKs from [data-model.md](./data-model.md) |
| ArangoDB doc + Redis cache | polyglot | When that backend is selected |

CSV writes are append-with-dedup; SQLite writes are `INSERT OR REPLACE` keyed
on `(org_id, id)` for the parent and the composite keys for children.

## Running the Menu Item Locally

### Interactive (Windows 11 + venv)

```powershell
# Activate venv (project standard)
.venv\Scripts\Activate.ps1

# Launch interactively and select menu 94
python MistHelper.py
# Then: enter 94 at the menu prompt, supply Org ID and NAC Portal ID.

# Or direct invocation (proposed menu number 94)
python MistHelper.py --menu 94
```

### Containerized (Podman)

```powershell
# Inside the running misthelper container (already deployed via the standard
# pipeline) -- SSH on port 2200 lands directly in the MistHelper menu.
ssh -p 2200 misthelper@localhost
# Then: enter 94 at the menu prompt.
```

### Example Prompt Flow

```text
Select menu item: 94
Org ID [press Enter for default from .env]:   <Enter>
NAC Portal ID: 51908ea7-dea7-4581-a578-f7320c4d5216
INFO  Fetching NAC portal 51908ea7-dea7-4581-a578-f7320c4d5216 for org <env-default>
DEBUG NAC portal type=guest_portal name=get-wifi sso_enabled=True role_match_count=2
INFO  Flattening NAC portal response into 3 sub-tables
DEBUG Flattened rows: parent=1 sso=1 role_matching=2
INFO  Writing NAC portal export via DataExporter
... (DataExporter emits per-backend confirmation lines)
Done.
```

## Expected Method Outline (for `/speckit.tasks`)

The implementation method is added to the existing NAC / org-config export
class as documented in [research.md](./research.md) Task 4. The skeleton
below illustrates the inline-comment + action-logging density expected by
Constitution Principles VI and VII; the concrete class name is chosen at
task generation time. Length stays under 25 lines per Principle I.

```python
def export_org_nac_portal(self, org_id=None, nacportal_id=None):          # New menu 94 method
    """Export a single NAC portal configuration to the active backend."""  # Public docstring
    org_id = org_id or safe_input(                                          # Allow .env fallback
        "Org ID [press Enter for default from .env]: ",                     # User-facing prompt
        context="org_nac_portal:org_id",                                    # Distinct EOF tag
    ) or os.environ.get("MIST_ORG_ID")                                      # .env final fallback
    nacportal_id = nacportal_id or safe_input(                              # No .env default
        "NAC Portal ID: ",                                                  # Per-invocation ID
        context="org_nac_portal:nacportal_id",                              # Distinct EOF tag
    )
    if not _is_uuid(org_id) or not _is_uuid(nacportal_id):                  # Cheap shape check
        logging.warning("Invalid UUID(s); aborting NAC portal export")      # No traceback exit
        return                                                              # Clean early return
    logging.info(                                                           # Action log: pre-call
        "Fetching NAC portal %s for org %s", nacportal_id, org_id,          # ASCII, %s style
    )
    response = mistapi.api.v1.orgs.nac_portals.getOrgNacPortal(             # SDK GET call
        self.apisession, org_id, nacportal_id,                              # Positional args
    )
    payload = response.data or {}                                           # Defensive default
    logging.debug(                                                          # Action log: post-call
        "NAC portal type=%s name=%s",                                       # Non-sensitive only
        payload.get("type"), payload.get("name"),                           # Never log secrets
    )
    rows = self._flatten_nac_portal(org_id, nacportal_id, payload)          # Build flat rows
    DataExporter.write_with_format_selection(                               # Multi-backend write
        rows, "org_nac_portal", api_function_name="getOrgNacPortal",        # PK strategy key
    )
```

## Quality Gates (Run Before Every Commit)

```powershell
# Activate venv (project standard)
.venv\Scripts\Activate.ps1

# 1. Syntax (must produce no output = valid)
python -m py_compile MistHelper.py

# 2. Lint (must pass clean)
python -m ruff check MistHelper.py

# 3. Format (run without --check to auto-fix if it reports differences)
python -m black --check MistHelper.py

# 4. Test sweep -- menu 94 is inside the default sweep range
#    (heavy/destructive skip list 14, 18, 63-65, 90-100 does not affect 94)
python MistHelper.py --test
```

All four must pass before committing. The full deployment pipeline
(`git commit` -> `git push` -> container build -> `podman pull` -> restart)
is documented in `.github/copilot-instructions.md` and applies unchanged
once these gates are green.

## Verification Checklist

- [ ] `data/org_nac_portal.csv` exists and contains exactly one row after
      a successful run.
- [ ] Re-running the menu item against the same `nacportal_id` does not
      produce a duplicate row in `data/mist_data.db` table `org_nac_portal`
      (upsert on `(org_id, id)`).
- [ ] No log line contains `portal_authorize_jwt_secret`, `idp_cert`, or
      any element of `additional_cacerts`.
- [ ] `python MistHelper.py --menu 94 --test` with `MIST_TEST_NACPORTAL_ID`
      set returns exit code 0.
- [ ] `python MistHelper.py --menu 94 --test` with `MIST_TEST_NACPORTAL_ID`
      absent logs a warning and skips the op without failing the sweep.

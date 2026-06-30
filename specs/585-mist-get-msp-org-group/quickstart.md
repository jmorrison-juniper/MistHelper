# Phase 1 Quickstart: getMspOrgGroup (Menu 96)

**Feature**: 585-mist-get-msp-org-group
**Audience**: Developer implementing or smoke-testing the new menu item locally.

This document covers everything needed to run the new menu item end-to-end on a
Windows 11 + venv workstation and validate it against the project's quality gates.

---

## Prerequisites

- Python 3.13 or newer
- A virtual environment at `.venv` (`python -m venv .venv` if it does not exist)
- The repo's `requirements.txt` installed (`pip install -r requirements.txt`)
- A valid Mist API token with MSP read scope
- An MSP UUID and an Org-Group UUID you are entitled to read

---

## Required `.env` Variables

Add (or confirm) the following entries in `.env` at the repo root. The first two are
shared across the whole tool; the latter two are new for this menu item's
non-interactive `--test` mode (interactive runs prompt instead).

```dotenv
# Existing -- required by mistapi.APISession
MIST_HOST=api.mist.com                          # Or api.eu.mist.com, api.gc1.mist.com, etc.
MIST_API_TOKEN=<your-api-token>                 # Never commit; .env is git-ignored

# New -- consumed only by the menu 96 non-interactive code path
MSP_ID=b9d42c2e-88ee-41f8-b798-f009ce7fe909     # Replace with your MSP UUID
MSP_ORG_GROUP_ID=53f10664-3ce8-4c27-b382-0ef66432349f  # Replace with your Org-Group UUID
```

The new variables are optional in interactive mode; if absent, the menu method falls
back to `safe_input()` prompts.

---

## Expected `data/` Output

After a successful interactive run with backend = CSV:

```text
data/msp_org_group_<msp_id>_<orggroup_id>.csv          # 1 row -- summary
data/msp_org_group_members_<orggroup_id>.csv           # N rows -- membership edges
```

After a successful run with backend = SQLite, the same data is upserted into
`data/mist_data.db` in tables `msp_org_groups` and `msp_org_group_members`.

The polyglot (ArangoDB + Redis) backend additionally writes the document collection
`msp_org_groups`, the edge collection `msp_org_group_members`, and the Redis cache key
`msp_org_group:<orggroup_id>`.

---

## Interactive Invocation

```powershell
# Activate the venv
.\.venv\Scripts\Activate.ps1

# Launch the menu and pick option 96 from the prompt
python MistHelper.py
# At the menu, type: 96
# When prompted "Enter MSP ID: ", paste your MSP UUID
# When prompted "Enter Org Group ID: ", paste your Org-Group UUID
```

Expected console output (abbreviated, ASCII-only):

```text
INFO  Fetching MSP org group msp=b9d42c2e-... orggroup=53f10664-...
DEBUG Org group received: name=North America Region member_orgs=4
INFO  Flattening org-group summary into 1 row
INFO  Flattening 4 member-org edges
INFO  Writing 1 summary row and 4 member rows via DataExporter
INFO  Menu 96 complete; exiting normally
```

---

## Direct (Non-Interactive) Invocation

```powershell
# Activate the venv
.\.venv\Scripts\Activate.ps1

# Skip the menu and run the operation directly; MSP_ID and MSP_ORG_GROUP_ID are
# read from .env so no prompts appear
python MistHelper.py --menu 96
```

Exit code `0` on success; non-zero only on API or backend failure (never on EOF -- the
`safe_input()` wrapper converts EOF into a clean log + `sys.exit(0)`).

---

## Method Outline (Implementation Sketch)

The implementation lives on a new `MspOrgGroupExportUtils` class in `MistHelper.py`.
Every executable line carries an inline comment per Principle VI; before/after log
calls bracket every meaningful step per Principle VII.

```python
class MspOrgGroupExportUtils:                                                      # New class -- owns MSP/orggroup read endpoints
    """Read-only export helpers for MSP-managed Organization Groups."""

    def __init__(self, apisession, data_exporter):                                 # Accepts the shared APISession and DataExporter
        self.apisession = apisession                                               # Reused mistapi session (token from .env)
        self.exporter = data_exporter                                              # Reused DataExporter (backend dispatch)

    def export_msp_org_group(self, msp_id=None, orggroup_id=None):                 # Menu 96 entry point; both args optional in interactive mode
        msp_id = msp_id or safe_input("Enter MSP ID: ",                            # Prompt only if not pre-supplied
                                       context="msp_org_group:msp_id")             # Context tag for SSH/EOF logs
        orggroup_id = orggroup_id or safe_input("Enter Org Group ID: ",            # Prompt only if not pre-supplied
                                                 context="msp_org_group:orggroup_id")
        if not _is_uuid(msp_id) or not _is_uuid(orggroup_id):                      # Reject malformed UUIDs before any API call
            logging.warning("Invalid MSP or org-group UUID -- aborting")           # ASCII-only warning, no secrets
            return                                                                  # Early return on validation failure
        logging.info("Fetching MSP org group msp=%s orggroup=%s",                  # Action log -- BEFORE the SDK call
                     msp_id, orggroup_id)
        response = mistapi.api.v1.msps.org_groups.getMspOrgGroup(                  # The actual Mist SDK call
            self.apisession, msp_id, orggroup_id)
        payload = response.data or {}                                              # Treat empty body as empty dict, not None
        logging.debug("Org group received: name=%s member_orgs=%d",                # Action log -- AFTER the SDK call, with counts
                      payload.get("name"), len(payload.get("org_ids") or []))
        summary_row, member_rows = self._flatten(payload)                          # Split into summary + edge rows (private helper)
        self.exporter.write_with_format_selection(                                 # Single multi-backend write call
            [summary_row], "msp_org_groups",
            api_function_name="getMspOrgGroup")
        self.exporter.write_with_format_selection(                                 # Second write for the edge rows
            member_rows, "msp_org_group_members",
            api_function_name="getMspOrgGroup")
```

(Method body is 16 executable lines, well under the 25-line ceiling of the 5-Item
Rule.)

---

## Quality Gates

Run all four locally before committing:

```powershell
.\.venv\Scripts\Activate.ps1

python -m py_compile MistHelper.py                    # Must produce no output
python -m ruff check MistHelper.py                    # Must report "All checks passed"
python -m black --check MistHelper.py                 # Must report no files to format

# Optional but recommended -- exercises the new menu item against a real Mist tenant
python MistHelper.py --test
```

CI replays the same gates in `.github/workflows/ci.yml`. The PR cannot auto-merge
until every gate is green and CodeQL completes.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `401 Unauthorized` from the SDK | Missing or expired `MIST_API_TOKEN` | Refresh the token; restart the venv (env vars are re-read on launch) |
| `403 Permission Denied` | Token lacks MSP read scope | Issue a new token with MSP scope on the Mist portal |
| `404 Not Found` | Wrong `msp_id` / `orggroup_id` pair | Verify both UUIDs in the Mist UI; the menu logs a warning and exits 0 |
| `PermissionError: '/app/data/script.log'` (container) | `data/` permissions not relaxed | `chmod -R 777 data/` on the host before launching the container |
| EOF traceback during prompts | `safe_input()` not used | Confirm the new method routes prompts through `safe_input()` |

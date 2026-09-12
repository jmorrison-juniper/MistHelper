# Phase 1 Quickstart: getOrgWxRule (Menu 96)

**Feature**: 654-mist-get-org-wx-rule
**Date**: 2026-07-01

This quickstart shows how to run the new menu item locally against a real Mist org,
verify the persisted output, and pass every quality gate before commit.

## 1. Prerequisites

- Windows 11 with Python 3.13+ on PATH (or the Podman container at
  `ghcr.io/jmorrison-juniper/misthelper:latest`).
- Cloned MistHelper worktree; venv activated:

  ```powershell
  cd C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper
  .venv\Scripts\Activate.ps1
  ```

## 2. Required `.env` Variables

Add / confirm the following in the repository `.env` (git-ignored):

```dotenv
# Mist API access
MIST_HOST=api.mist.com                            # Cloud region host
MIST_API_TOKEN=<your-api-token>                   # Loaded by mistapi.APISession
MIST_ORG_ID=<your-org-uuid>                       # Prompt default for org_id

# Optional -- enables --test to hit this menu non-interactively
MIST_TEST_WXRULE_ID=<a-known-wxrule-uuid-in-that-org>
```

`MIST_API_TOKEN` MUST NOT be logged or committed. Only the two ID variables are
read by menu 96 itself; the SDK reads the token internally.

## 3. Expected `data/` Output Filename

- CSV backend: `data/org_wxrule_<org_id_short>_<wxrule_id_short>.csv`
  (short = first 8 hex chars of each UUID; produced by DataExporter's default
  naming when `api_function_name="getOrgWxRule"` is passed in).
- SQLite backend: table `org_wxrule_detail` inside `data/mist_data.db`. Repeated
  runs upsert on `id` -- no duplicate rows.
- ArangoDB+Redis backend: collection `org_wxrule_detail` with graph edges to
  `orgs/<org_id>`, `sites/<site_id>` (when present), and
  `wlan_templates/<template_id>` (when present).

## 4. Example Invocation

### Interactive

```powershell
python MistHelper.py                          # Launch menu
# At the prompt, enter: 96
# When prompted:
#   Org UUID [default MIST_ORG_ID from .env]: <press Enter to accept default>
#   WxRule UUID: 53f10664-3ce8-4c27-b382-0ef66432349f
```

Expected console log (ASCII, no emoji):

```text
INFO  Fetching WxRule 53f10664-3ce8-4c27-b382-0ef66432349f for org a97c1b22-...
DEBUG Fetched WxRule id=53f10664-3ce8-4c27-b382-0ef66432349f action=allow enabled=True
INFO  Writing 1 row to org_wxrule_detail via DataExporter
DEBUG Wrote 1 row to org_wxrule_detail
```

### Direct (scripted)

```powershell
python MistHelper.py --menu 96                # requires MIST_ORG_ID + MIST_TEST_WXRULE_ID in .env
```

Return code: `0` on success, on empty/404 (warning), and on graceful EOF. Non-zero
only on unhandled exceptions.

## 5. Method Skeleton (Preview -- Full Implementation Belongs to `/speckit.tasks`)

For reference only, the target shape of the new method on `OrgExportUtils`:

```python
def export_org_wxrule_detail(self) -> None:                                     # Menu 96 entry point.
    logging.info("Menu 96 selected: export org WxRule detail")                   # Announce start of action.
    resolved_org_id = safe_input(                                                # Prompt for org UUID.
        "Org UUID [default MIST_ORG_ID from .env]: ",
        context="org_wxrule_detail:org_id",
    ).strip() or os.getenv("MIST_ORG_ID", "")                                    # Fall back to .env default.
    wxrule_id = safe_input(                                                      # Prompt for rule UUID.
        "WxRule UUID: ",
        context="org_wxrule_detail:wxrule_id",
    ).strip()
    if not self._is_valid_uuid(resolved_org_id) or not self._is_valid_uuid(wxrule_id):  # Guard clause.
        logging.warning("Invalid or missing org_id / wxrule_id; aborting")       # Explain why we bail.
        return                                                                   # Safe exit.
    logging.info(                                                                # Log before SDK call.
        "Fetching WxRule %s for org %s", wxrule_id, resolved_org_id,
    )
    api_response = mistapi.api.v1.orgs.wxrules.getOrgWxRule(                     # Single SDK call.
        self.apisession, resolved_org_id, wxrule_id,
    )
    rule_row = api_response.data or {}                                           # Empty dict on 404.
    logging.debug(                                                               # Log after SDK call.
        "Fetched WxRule id=%s action=%s enabled=%s",
        rule_row.get("id"), rule_row.get("action"), rule_row.get("enabled"),
    )
    DataExporter.write_with_format_selection(                                    # Persist via multi-backend writer.
        data=[rule_row] if rule_row else [],                                     # Wrap in list for DataExporter.
        filename=f"org_wxrule_{resolved_org_id[:8]}_{wxrule_id[:8]}",            # Discoverable stem.
        api_function_name="getOrgWxRule",                                        # Key into PK strategy table.
    )
```

This preview is 17 executable lines and fits inside the 5-Item Rule budget
(<=25 lines, <=3 params, <=5 logical blocks).

## 6. Quality Gates (Run Before Commit)

```powershell
python -m py_compile MistHelper.py            # Syntax gate: no output = pass
python -m ruff check MistHelper.py            # Lint gate: must exit 0
python -m black --check MistHelper.py         # Format gate: must exit 0
python MistHelper.py --test                   # Full test sweep (item 96 must pass)
```

All four must pass before `git add` + commit. See
`.github/copilot-instructions.md` for the full deployment pipeline (container
build via GitHub Actions, `podman pull`, container restart, `podman ps`
verification).

## 7. Rollback

- Local: `git restore MistHelper.py README.md CHANGELOG.md` reverts the code
  change; `del data\mist_data.db` (or the specific table via
  `sqlite3 data/mist_data.db "DROP TABLE org_wxrule_detail"`) removes the local
  SQLite artifact.
- Container: `podman pull` the previous image tag from GHCR and restart.

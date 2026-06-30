# Phase 1 Quickstart: GetOrgCurrentMatchingClientsOfAWxTag

**Branch**: `603-mist-get-org-current-matching-clients-of-a-wx-tag`
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md) | **Data Model**: [data-model.md](./data-model.md)

Local dev quickstart for the new menu item that exports the current matching clients
of a WxTag.

---

## Prerequisites

- Windows 11 with PowerShell 7+ and a working `MistHelper` venv at
  `.venv\Scripts\Activate.ps1` (per the canonical project guide).
- Python 3.13+ available on PATH inside the venv.
- `mistapi` 0.59+ installed (`uv pip install -r requirements.txt` or `pip install -r
  requirements.txt`).
- The `data/` directory exists and is world-writable
  (`chmod -R 777 data/` on Linux/container; on Windows, ensure the venv user has
  write access).

---

## Required `.env` variables

The new menu item reads no new env variables -- it reuses the existing Mist API
session bootstrap. Keep the following in `.env` (repo root, git-ignored):

```dotenv
MIST_HOST=api.mist.com            # Or your regional host: api.eu.mist.com, api.gc1.mist.com, etc.
MIST_API_TOKEN=<your-token>       # Long-lived org-scoped token; never logged
MIST_ORG_ID=<your-default-org>    # Optional: presented as default for the org_id prompt
```

You also need at least one WxTag UUID for the org. Find one with the existing
`listOrgWxTags` menu item (or directly via the Mist UI under
**Organization -> WxLAN Tags**); copy its UUID and paste it at the `wxtag_id` prompt.

---

## Expected output filenames

| Backend          | Output location                                                              |
|------------------|------------------------------------------------------------------------------|
| CSV (default)    | `data/org_<org_id>_wxtag_<wxtag_id>_matching_clients.csv`                    |
| SQLite           | `data/mist_data.db`, table `org_wxtag_matching_clients`                      |
| ArangoDB+Redis   | Collection `org_wxtag_matching_clients`; Redis key `wxtag:clients:<org_id>:<wxtag_id>` |

The CSV is per-tag (UUIDs in filename). The SQLite table is shared across runs and
uses the composite PK `(org_id, wxtag_id, mac)` for clean upserts.

---

## Run the menu item locally

Interactive run, from the worktree root:

```powershell
.venv\Scripts\Activate.ps1                       # Activate venv
python MistHelper.py                             # Launch interactive menu
# At the main prompt, type:
#   59
# At the prompts:
#   org_id:    <paste your org UUID, or press Enter to accept the MIST_ORG_ID default>
#   wxtag_id:  <paste your wxtag UUID>
```

Direct (non-interactive) run -- the same path the test harness uses:

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py --menu 59
# Feed the two UUIDs from stdin in order:
#   <org_uuid>\n<wxtag_uuid>\n
```

Successful runs print, in order (ASCII only, no emoji):

```text
INFO  Prompting for org_id and wxtag_id (context org_wxtag_clients)
INFO  Fetching matching clients for wxtag <wxtag_id> in org <org_id>
DEBUG WxTag <wxtag_id> returned N matching clients
INFO  Flattening response into table rows
DEBUG Flattened 1 element into N rows for table org_wxtag_matching_clients
INFO  Writing rows via DataExporter (backend=<csv|sqlite|arango>)
DEBUG DataExporter wrote N rows to org_wxtag_matching_clients
```

Empty result is logged as `INFO WxTag <wxtag_id> has no current matching clients`
and the menu exits 0 without invoking the exporter.

---

## Expected new menu method (sketch -- illustrates Principle VI / VII compliance)

The implementer adds something equivalent to the following on the `WxTagExportUtils`
class. Every executable line carries an inline comment per Principle VI, and the
action-logging pairs per Principle VII are explicit.

```python
def export_org_wxtag_matching_clients(self, org_id=None, wxtag_id=None):  # New menu method on WxTagExportUtils
    org_id = org_id or safe_input(                                        # Prompt only if caller did not pre-supply
        f"org_id [{os.environ.get('MIST_ORG_ID', '')}]: ",                # Show MIST_ORG_ID default in prompt
        context="org_wxtag_clients:org_id",                               # Stable context tag for SSH-EOF telemetry
    ) or os.environ.get("MIST_ORG_ID", "")                                # Fall back to env on empty input
    wxtag_id = wxtag_id or safe_input(                                    # Prompt only if caller did not pre-supply
        "wxtag_id: ",                                                     # No env default for tag UUIDs
        context="org_wxtag_clients:wxtag_id",                             # Stable context tag for SSH-EOF telemetry
    )
    if not _is_uuid(org_id) or not _is_uuid(wxtag_id):                    # Validate both UUIDs before any network call
        logging.warning("Invalid UUID(s): org_id=%s wxtag_id=%s", org_id, wxtag_id)  # Log and abort cleanly
        return                                                            # Exit early on validation failure
    logging.info("Fetching matching clients for wxtag %s in org %s", wxtag_id, org_id)  # Pre-call action log
    response = mistapi.api.v1.orgs.wxtags.getOrgCurrentMatchingClientsOfAWxTag(        # Single SDK call (non-paginated)
        self.api_session, org_id, wxtag_id,                               # Three positional args per research.md
    )
    payload = response.data or []                                         # Coerce None to empty list defensively
    logging.debug("WxTag %s returned %d matching clients", wxtag_id, len(payload))  # Post-call action log
    if not payload:                                                       # Short-circuit on empty result
        logging.info("WxTag %s has no current matching clients", wxtag_id)  # Inform the user, no exporter call
        return                                                            # Exit cleanly with 0
    retrieved_at = int(time.time())                                       # One observation timestamp for the whole batch
    rows = [                                                              # Flatten the array into uniform row dicts
        {                                                                  # Each row carries URL params + payload fields
            "org_id": org_id,                                              # Foreign-key column for cross-org queries
            "wxtag_id": wxtag_id,                                          # Foreign-key column for cross-tag queries
            "mac": item["mac"].lower().replace(":", "").replace("-", ""),  # Normalize MAC for stable PK
            "since": int(item["since"]),                                   # Cast to int per data-model.md
            "retrieved_at": retrieved_at,                                  # Identical for all rows in this batch
        }
        for item in payload                                                # One row per response array element
    ]
    logging.info("Writing %d row(s) via DataExporter", len(rows))         # Pre-write action log
    DataExporter.write_with_format_selection(                              # Single multi-backend write call
        rows,                                                              # The flattened row list
        f"org_{org_id}_wxtag_{wxtag_id}_matching_clients",                 # Base name; backend selects extension/table
        api_function_name="getOrgCurrentMatchingClientsOfAWxTag",          # Drives PK strategy lookup
    )
    logging.debug("DataExporter completed for table org_wxtag_matching_clients")  # Post-write action log
```

This sketch is illustrative; the implementer is free to adjust naming and ordering as
long as the seven principles continue to PASS.

---

## Quality gates (must pass before commit)

Run from the worktree root, in this order:

```powershell
.venv\Scripts\Activate.ps1                       # Activate venv
python -m py_compile MistHelper.py               # Gate 1: syntax check (no output on success)
python -m ruff check MistHelper.py               # Gate 2: lint (must report 0 issues)
python -m black --check MistHelper.py            # Gate 3: formatting (run without --check to auto-fix)
python MistHelper.py --test                      # Gate 4: full test sweep (op 59 must return 0)
```

All four must pass. The full deployment pipeline documented in
`.github/copilot-instructions.md` (commit -> push -> container build -> pull ->
restart -> `podman ps`) is run only after all four gates are green and the PR has
been reviewed; it is out of scope for this quickstart but mandatory before the menu
item ships.

---

## Manual smoke test

After the four gates are green:

```powershell
python MistHelper.py --menu 59                   # Direct invocation
# Provide org_id then wxtag_id when prompted; expect:
#   - data/org_<org>_wxtag_<tag>_matching_clients.csv exists
#   - sqlite3 data/mist_data.db "SELECT COUNT(*) FROM org_wxtag_matching_clients;" returns the right count
#   - Re-running does NOT duplicate rows (composite PK upsert)
```

If the API call returns no rows, the smoke test still passes -- the success criterion
is "exits 0 without traceback and writes a complete or empty result deterministically",
not "returns at least one row".

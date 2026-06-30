# Phase 1 Quickstart: Running Menu 96 (getOrgAptemplate)

This quickstart shows a developer how to exercise the new menu item locally
against a real Mist organization, what `.env` variables are required, what
appears in `data/` after a successful run, and which quality gates must be
green before commit.

## Prerequisites

- Python 3.13 or newer on Windows 11.
- Project venv activated: `.venv\Scripts\Activate.ps1`.
- Dependencies installed (mistapi 0.59+ plus the rest of `requirements.txt`).
- A Mist API token with read access to the target organization.
- A valid AP template UUID belonging to that organization. If you do not have
  one handy, run **Menu 35** (`listOrgApTemplates`) first and copy any `id`
  value from its output.

## Required `.env` variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `MIST_HOST` | Yes | Mist Cloud API host (e.g. `api.mist.com`). Loaded by `mistapi.APISession`. |
| `MIST_API_TOKEN` | Yes | API token. Never logged. |
| `MIST_ORG_ID` | Recommended | Default org UUID. Used as the `org_id` prompt default; empty user input keeps this value. |
| `MIST_TEST_APTEMPLATE_ID` | Optional | When set, `python MistHelper.py --test` can drive the menu non-interactively against this UUID. |

`.env` lives at the repository root and is git-ignored. Template:
`deploy/.env.example`.

## Interactive run

```powershell
# Activate venv and launch the menu.
.\.venv\Scripts\Activate.ps1
python MistHelper.py
```

At the main menu, select **96** (`Get Org AP Template Detail (read-only)`).
Expected prompt flow:

```
Org ID [press Enter to use MIST_ORG_ID from .env]: <enter or paste UUID>
AP Template UUID: 53f10664-3ce8-4c27-b382-0ef66432349f
```

Expected log lines (ASCII-only, `%s` formatted):

```
INFO   Prompting for org_id (context=org_aptemplate:org_id)
INFO   Prompting for aptemplate_id (context=org_aptemplate:aptemplate_id)
INFO   Fetching AP template detail for org=<org_id> template=<aptemplate_id>
DEBUG  AP template: id=<id> rules=<n> wifi_enabled=<bool>
INFO   Flattening AP template summary row
DEBUG  Summary row prepared (1 record)
INFO   Flattening AP template match-rule rows
DEBUG  Match-rule rows prepared (<n> records)
INFO   Exporting via DataExporter.write_with_format_selection
DEBUG  Export complete
```

## Direct (non-interactive) invocation

For automation or CI smoke checks:

```powershell
python MistHelper.py --menu 96
```

The CLI flag bypasses the main menu but still calls `safe_input()` for the two
UUID prompts. When `MIST_ORG_ID` and `MIST_TEST_APTEMPLATE_ID` are both set in
`.env`, the prompts can be answered by pressing Enter through both.

## Expected `data/` output

Two files per run (CSV backend; SQLite writes are simultaneous and idempotent):

```text
data\org_aptemplate_summary_<org_id>_<aptemplate_id>.csv
data\org_aptemplate_match_rules_<org_id>_<aptemplate_id>.csv
```

SQLite tables written to `data\mist_data.db`:

```text
org_aptemplates              -- one row per template (upserted on PK = id)
org_aptemplate_match_rules   -- zero or more rows per template (upserted on (aptemplate_id, rule_index))
```

When the ArangoDB + Redis backend is active (`OUTPUT_BACKEND=arango_redis`),
`DataExporter` writes the same shape into the graph (nodes for the template,
edges to the parent org / site, nested rule nodes) and caches the summary row
in Redis. No menu-side code change is needed -- backend dispatch lives inside
`DataExporter.write_with_format_selection`.

## Re-run idempotency check

Run the menu twice in a row against the same template. After the second run:

```powershell
python -c "import sqlite3; c=sqlite3.connect('data/mist_data.db'); print('summary:', c.execute('select count(*) from org_aptemplates where id=?',('<aptemplate_id>',)).fetchone()); print('rules:', c.execute('select count(*) from org_aptemplate_match_rules where aptemplate_id=?',('<aptemplate_id>',)).fetchone())"
```

`summary` must be exactly `(1,)` regardless of how many times you re-ran the
menu. `rules` must equal the source `len(ap_matching.rules)` -- not a multiple
of it.

## Quality gates (run before every commit)

```powershell
# Syntax: empty output on success.
python -m py_compile MistHelper.py

# Lint: must report zero violations.
python -m ruff check MistHelper.py

# Formatting: must report nothing to change.
python -m black --check MistHelper.py

# Functional smoke test (skips heavy / destructive operations per the
# documented skip list 14, 18, 63-65, 90-100; Menu 96 is inside the default
# sweep and must pass when MIST_ORG_ID + MIST_TEST_APTEMPLATE_ID are set).
python MistHelper.py --test
```

All four commands must exit with code 0 before `git add` / `git commit`. The
full deployment pipeline (commit -> push -> GitHub Actions container build
-> `podman pull` -> container restart -> `podman ps` verification) is
documented in `.github/copilot-instructions.md` under "MANDATORY: Full
Deployment Pipeline" and applies unchanged.

## Troubleshooting

- **`PermissionError: [Errno 13] Permission denied: '/app/data/script.log'`
  inside the container**: run `chmod -R 777 data/` on the host before the
  first container run (see `.github/copilot-instructions.md` -> "Data
  Directory Permissions").
- **`mistapi.APISession` raises 401**: confirm `MIST_API_TOKEN` in `.env`
  and that the token has read scope on the target org. The error message is
  logged at `WARNING`; the API token itself is never logged.
- **404 from Mist API**: the `aptemplate_id` does not exist in the supplied
  org. The menu logs `WARNING` and exits cleanly with code 0.
- **EOF when running over SSH on port 2200**: this is expected; `safe_input()`
  exits 0 without a traceback. Reconnect and retry interactively.

## Method shape sketch (for reviewer reference only)

A near-final outline of the new method on `OrgTemplateExportUtils`. Each
executable line carries the inline comment that will exist in the merged code
per Constitution VI. Action logging pairs (Constitution VII) bracket every
meaningful step.

```python
def export_org_aptemplate_detail(self, org_id: str | None = None,
                                  aptemplate_id: str | None = None) -> None:
    """Fetch one AP template by UUID and persist via DataExporter."""
    # Prompt for org UUID using safe_input so SSH/container EOF is handled.
    org_id = org_id or safe_input(
        "Org ID [Enter for MIST_ORG_ID]: ",
        context="org_aptemplate:org_id",
    ) or os.environ.get("MIST_ORG_ID", "")
    # Prompt for the template UUID; no env default by design.
    aptemplate_id = aptemplate_id or safe_input(
        "AP Template UUID: ",
        context="org_aptemplate:aptemplate_id",
    )
    # Validate both UUIDs before the SDK call to surface typos as warnings.
    if not (is_valid_uuid(org_id) and is_valid_uuid(aptemplate_id)):
        logging.warning("Invalid UUID supplied; aborting org_aptemplate fetch")
        return
    # ACTION LOG before the API call (INFO).
    logging.info("Fetching AP template detail for org=%s template=%s",
                 org_id, aptemplate_id)
    # Single GET via mistapi; raises on transport failure.
    response = mistapi.api.v1.orgs.ap_templates.getOrgAptemplate(
        self.apisession, org_id, aptemplate_id,
    )
    # ACTION LOG after the API call (DEBUG with summary).
    template = response.data or {}
    rules = (template.get("ap_matching") or {}).get("rules") or []
    logging.debug("AP template: id=%s rules=%d wifi_enabled=%s",
                  template.get("id"), len(rules),
                  (template.get("wifi") or {}).get("enabled"))
    # Persist through the multi-backend exporter; one call per logical table.
    DataExporter.write_with_format_selection(
        [self._flatten_summary(template)],
        f"org_aptemplate_summary_{org_id}_{aptemplate_id}",
        api_function_name="getOrgAptemplate",
    )
    DataExporter.write_with_format_selection(
        self._flatten_match_rules(template),
        f"org_aptemplate_match_rules_{org_id}_{aptemplate_id}",
        api_function_name="getOrgAptemplate__match_rules",
    )
```

Two private flatteners (`_flatten_summary`, `_flatten_match_rules`) on the
same class produce the dict shapes documented in `data-model.md`. Together
the public method stays well under the 25-line / 5-block ceiling.

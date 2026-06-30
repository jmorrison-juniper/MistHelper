# Phase 1 Quickstart: getOrgMxEdge Menu Item

**Feature**: 615-mist-get-org-mx-edge | **Date**: 2026-06-30
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

This quickstart is the developer-side recipe for running, validating, and shipping
the new menu item. It is intentionally short and prescriptive.

---

## 1. Prerequisites

- Windows 11 host with `.venv` activated, **OR** the official Podman container
  (`ghcr.io/jmorrison-juniper/misthelper:latest`).
- Python 3.13+.
- `mistapi` 0.59+ installed (`pip install -r requirements.txt` or via UV).
- A populated `.env` at the repo root (template at `deploy/.env.example`):

```text
MIST_HOST=api.mist.com              # or api.eu.mist.com / api.gc1.mist.com etc.
MIST_API_TOKEN=<your-token>         # Mist API token; never commit.
MIST_ORG_ID=<your-org-uuid>         # default org used by safe-org-export menu items.
MIST_TEST_MXEDGE_ID=<mxedge-uuid>   # OPTIONAL: used only when running `--test`. Skip
                                    # cleanly if unset.
```

The container reads `.env` via `-v "${PWD}/.env:/app/.env:ro"`.

---

## 2. Local Activation and Quality Gates (run BEFORE every commit)

PowerShell on Windows:

```powershell
# Activate venv
.venv\Scripts\Activate.ps1

# Syntax check (no output = pass)
python -m py_compile MistHelper.py

# Lint check (must pass clean)
python -m ruff check MistHelper.py

# Format check (run without --check to auto-fix)
python -m black --check MistHelper.py

# Functional sweep
python MistHelper.py --test
```

All four commands must succeed before pushing.

---

## 3. Running the New Menu Item

### Interactive

```powershell
python MistHelper.py
```

At the prompt:

```text
> 235
Enter org_id (UUID): a97c1b22-a4e9-411e-9bfd-d8695a0f9e61
Enter mxedge_id (UUID): 53f10664-3ce8-4c27-b382-0ef66432349f
```

Both prompts use `safe_input()` so pressing Ctrl-D / sending EOF in an SSH session
exits 0 without a traceback.

### Direct invocation (for automation)

```powershell
python MistHelper.py --menu 235
```

`--menu 235` reuses `MIST_ORG_ID` from `.env` and prompts for `mxedge_id`.

### Non-interactive test mode

```powershell
python MistHelper.py --test
```

When `MIST_ORG_ID` and `MIST_TEST_MXEDGE_ID` are both set, the menu runs end-to-end
and exits 0. When either is missing, the menu logs a `WARNING` and skips cleanly with
exit code 0 (does not fail the sweep).

---

## 4. Expected Output

- **CSV**: `data\OrgMxEdgeDetail.csv` (one row, columns mirror the flattened keys in
  [data-model.md](./data-model.md)).
- **SQLite**: `data\mist_data.db`, table `org_mxedge_detail`, one row keyed by `id`.
  Repeated runs upsert in place -- there is never a duplicate-PK error.
- **ArangoDB / Redis**: when polyglot backend is configured, the document lands in
  collection `org_mxedge_detail` with `_key = id` and a Redis cache entry
  `org_mxedge_detail:<id>` is set with the configured TTL.
- **Stdout / log file**:

```text
INFO  Prompting for org_id (context=org_mxedge_detail:org_id)
INFO  Prompting for mxedge_id (context=org_mxedge_detail:mxedge_id)
INFO  Fetching MxEdge detail for org a97c1b22... mxedge 53f10664...
DEBUG MxEdge detail: id=53f10664... model=ME-100 mxcluster_id=... tunterm_registered=True
INFO  Flattening MxEdge record
DEBUG MxEdge flattened: 47 columns
INFO  Writing OrgMxEdgeDetail via DataExporter
DEBUG OrgMxEdgeDetail write complete (1 row)
```

All log lines are ASCII-only. No API token, MxEdge `magic`, `mist_password`, or
`root_password` appears in any log line.

---

## 5. Implementation Sketch (target shape)

The new method lives on the existing `OrgConfigExporter` class in `MistHelper.py`,
adjacent to `mx_edges()` (line ~12007). Every executable line carries an inline
comment per Constitution Principle VI:

```python
class OrgConfigExporter:                                                                # existing class, no new wrapper
    @staticmethod                                                                       # menu binds the static method directly
    def get_org_mxedge_detail() -> None:                                                # menu 235: GET single MxEdge
        org_id = safe_input(                                                            # collect org UUID safely
            "Enter org_id (UUID): ",                                                    # operator-facing prompt
            context="org_mxedge_detail:org_id",                                         # EOF-handling context label
        ) or os.getenv("MIST_ORG_ID", "")                                               # fall back to .env default
        mxedge_id = safe_input(                                                         # collect mxedge UUID safely
            "Enter mxedge_id (UUID): ",                                                 # operator-facing prompt
            context="org_mxedge_detail:mxedge_id",                                      # EOF-handling context label
        )                                                                               # no env fallback in normal mode
        if not _is_valid_uuid(org_id) or not _is_valid_uuid(mxedge_id):                 # reject typos before burning a call
            logging.warning("Invalid UUID(s); aborting menu 235")                       # observability without leaking values
            return                                                                      # safe early exit
        logging.info("Fetching MxEdge detail for org %s mxedge %s", org_id, mxedge_id)  # action log BEFORE
        response = mistapi.api.v1.orgs.mxedges.getOrgMxEdge(                            # sole sanctioned SDK call
            apisession, org_id=org_id, mxedge_id=mxedge_id,                             # required path params
        )                                                                               # mistapi handles auth + retries
        record = _redact_mxedge_secrets(response.data or {})                            # strip magic + passwords
        logging.debug("MxEdge detail: id=%s model=%s",                                  # action log AFTER
                      record.get("id"), record.get("model"))                            # one-line summary, ASCII only
        flattened = flatten_dict(record)                                                # collapse nested objects
        logging.debug("MxEdge flattened: %d columns", len(flattened))                   # row-width observability
        DataExporter.write_with_format_selection(                                       # multi-backend persistence
            data=[flattened],                                                           # one row payload
            filename="OrgMxEdgeDetail",                                                 # base filename without extension
            api_function_name="getOrgMxEdge",                                           # used for PK strategy lookup
        )                                                                               # CSV + SQLite + Arango all served
```

The method is **15 executable lines**, **0 parameters** beyond `self`-equivalent
(static), and **4 logical blocks** -- well within the 5-Item Rule budget.

### Menu registration line

```python
235: ("Get single MxEdge detail (config + tunnel info)",                                # menu label
      OrgConfigExporter.get_org_mxedge_detail),                                         # dispatch target
```

### `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry

See [data-model.md](./data-model.md) for the canonical block; it is dropped verbatim
into the dictionary near line ~5203 (where `getOrgMxEdge` was previously stubbed).

---

## 6. Verifying Persistence

```powershell
# CSV
Get-Content .\data\OrgMxEdgeDetail.csv | Select-Object -First 2

# SQLite
python -c "import sqlite3; c=sqlite3.connect('data/mist_data.db'); print(list(c.execute('select id,name,model from org_mxedge_detail')))"

# Upsert sanity (run menu 235 twice; row count must stay at 1 per unique mxedge_id)
python -c "import sqlite3; c=sqlite3.connect('data/mist_data.db'); print(c.execute('select count(*) from org_mxedge_detail').fetchone())"
```

---

## 7. Quality Gates Summary

| Gate | Command | Pass criteria |
|------|---------|---------------|
| Syntax | `python -m py_compile MistHelper.py` | No output. |
| Lint | `python -m ruff check MistHelper.py` | "All checks passed." |
| Format | `python -m black --check MistHelper.py` | "would not reformat" only. |
| Functional sweep | `python MistHelper.py --test` | Exit code 0; menu 235 either runs or skips cleanly. |
| Manual smoke | `python MistHelper.py --menu 235` | Exit code 0; `data\OrgMxEdgeDetail.csv` exists; SQLite row count == 1 after two consecutive runs. |

All five gates must pass before opening the PR.

---

## 8. Pipeline After Push

The post-commit pipeline is the standard MistHelper flow (see
`.github/copilot-instructions.md`):

```powershell
git add MistHelper.py README.md CHANGELOG.md
git commit -m "version YY.MM.DD.HH.MM - add menu 235 getOrgMxEdge"
git push origin main
gh run list --workflow=container-build.yml --limit 1
gh run watch <run-id>
podman pull ghcr.io/jmorrison-juniper/misthelper:latest
podman stop misthelper ; podman rm misthelper
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `
    -v "${PWD}/data:/app/data:rw" `
    -v "${PWD}/.env:/app/.env:ro" `
    ghcr.io/jmorrison-juniper/misthelper:latest
podman ps
```

No deviation from the published pipeline; no special handling for menu 235.

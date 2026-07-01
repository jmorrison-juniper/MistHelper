# Phase 1 Quickstart: getOrgSecPolicy Menu Item

**Feature**: 636-mist-get-org-sec-policy
**Date**: 2026-06-30
**Menu number (proposed)**: 195

## Prerequisites

1. Python 3.13+ available and on PATH.
2. `.venv` already created and activated:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

3. Dependencies installed (mistapi 0.59+ present):

   ```powershell
   pip install -r requirements.txt   # or: uv pip sync requirements.txt
   ```

4. `data/` directory exists and is writable. If running the container, ensure
   permissions were fixed once with `chmod -R 777 data/` before first container run
   (see copilot-instructions.md "Data Directory Permissions").

## Required .env Variables

Located in the repo root as `.env` (git-ignored). Minimum entries:

```dotenv
MIST_HOST=api.mist.com                # Or the tenant-specific host, e.g. api.eu.mist.com
MIST_API_TOKEN=<redacted-64-char-token>   # Mist API token; NEVER commit
MIST_ORG_ID=<uuid>                    # Optional; used as prompt default for org_id
```

`MIST_ORG_ID` is optional -- if unset, the menu prompts explicitly.

## Expected data/ Output

After a successful run against org `<ORG>` and secpolicy `<POLICY>`, the following
files appear (subject to the configured backend):

| Backend            | Output                                                                                       |
|--------------------|----------------------------------------------------------------------------------------------|
| CSV (default)      | `data\OrgSecPolicy_<ORG>_<POLICY>.csv` and `data\OrgSecPolicyWlans_<ORG>_<POLICY>.csv`.      |
| SQLite             | Rows upserted into tables `org_sec_policy` and `org_sec_policy_wlans` in `data\mist_data.db`.|
| ArangoDB + Redis   | Collections `org_sec_policy` and `org_sec_policy_wlans` updated; Redis keys refreshed.       |

The parent CSV has one row. The child CSV has zero or more rows -- one per `wlans[]`
element in the response.

## Example Interactive Invocation

```powershell
python MistHelper.py --menu 195
```

Session transcript:

```text
[INFO] Menu 195: Get Organization Security Policy
Enter organization UUID (blank for MIST_ORG_ID from .env):
Enter security policy UUID: 53f10664-3ce8-4c27-b382-0ef66432349f
[INFO] Fetching security policy 53f10664-... for org a97c1b22-...
[DEBUG] Sec policy 53f10664-...: name=corp-wan-policy wlans=3
[INFO] Flattening 1 parent row and 3 child wlan rows
[DEBUG] Flatten complete: parent_rows=1 child_rows=3
[INFO] Writing OrgSecPolicy via DataExporter (getOrgSecPolicy)
[INFO] Writing OrgSecPolicyWlans via DataExporter (getOrgSecPolicyWlans)
[INFO] Menu 195 complete; exit 0
```

## Non-Interactive Direct Invocation

For scripted / test-sweep use, both IDs can be provided via environment variables that
the menu recognizes (falling back to prompts when unset):

```powershell
$env:MIST_ORG_ID="a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
$env:MIST_SECPOLICY_ID="53f10664-3ce8-4c27-b382-0ef66432349f"
python MistHelper.py --menu 195
```

## Sketch of the Implementation (for reviewer orientation)

The new method sits inside `class OrgTemplateExporter` (~line 11052 of
`MistHelper.py`). Every executable line carries an inline comment per Constitution
Principle VI, and every meaningful action is wrapped in before/after log calls per
Principle VII. Blank lines and closing parens are exempt.

```python
@staticmethod
def export_org_sec_policy(org_id: str, secpolicy_id: str) -> None:  # Menu 195 exporter.
    """Fetch and persist a single Mist security policy record."""
    logging.info("Fetching security policy %s for org %s", secpolicy_id, org_id)  # Log intent before API call.
    session = get_active_session()                                  # Reuse cached mistapi.APISession from .env.
    response = mistapi.api.v1.orgs.secpolicies.getOrgSecPolicy(     # Single non-paginated GET; may raise HTTPError.
        session, org_id, secpolicy_id
    )
    policy = response.data or {}                                    # Empty dict on 404 / no payload -- log warning below.
    if not policy:                                                  # Guard: nothing to persist means warn-and-exit.
        logging.warning("No security policy returned for %s", secpolicy_id)  # ASCII-only warning per Principle V.
        return                                                      # Exit early; DataExporter is not called.
    wlans = policy.get("wlans", []) or []                           # Defensive default; API may omit the key entirely.
    logging.debug("Sec policy %s: name=%s wlans=%d",                # DEBUG after-call summary per Principle VII.
                  policy.get("id"), policy.get("name"), len(wlans))
    parent_row = OrgTemplateExporter._flatten_sec_policy(policy)    # Promote scalars, preserve raw_json.
    child_rows = OrgTemplateExporter._flatten_sec_policy_wlans(policy, wlans)  # One row per wlan element.
    logging.info("Flattening 1 parent row and %d child wlan rows", len(child_rows))  # INFO before write.
    DataExporter.write_with_format_selection(                       # Multi-backend persistence entry point.
        [parent_row],
        f"OrgSecPolicy_{org_id}_{secpolicy_id}.csv",                # PascalCase filename convention.
        api_function_name="getOrgSecPolicy",                        # Routes to natural_pk strategy for parent table.
    )
    DataExporter.write_with_format_selection(                       # Second call for child rows.
        child_rows,
        f"OrgSecPolicyWlans_{org_id}_{secpolicy_id}.csv",
        api_function_name="getOrgSecPolicyWlans",                   # Routes to composite_pk strategy for child table.
    )
    logging.debug("Menu 195 export complete: parent=1 children=%d", len(child_rows))  # DEBUG after write.
```

The two `_flatten_*` helpers (each <=15 lines) are added as private static methods on
the same class and populate the columns documented in `data-model.md`. Prompt
collection is the responsibility of the menu dispatcher, which calls `safe_input()`
with the two `context=` values from `research.md` Task 5 and hands the validated UUIDs
to `export_org_sec_policy()`.

## Quality Gates

All four gates must pass before commit (per copilot-instructions.md pipeline):

```powershell
# 1. Syntax check (no output = pass).
python -m py_compile MistHelper.py

# 2. Lint (must pass clean).
python -m ruff check MistHelper.py

# 3. Format check (run WITHOUT --check locally to auto-apply; CI runs WITH --check).
python -m black --check MistHelper.py

# 4. Test sweep (menu 195 must return 0 against a known org).
python MistHelper.py --test
```

If any gate fails, fix the issue and re-run **all four** in order. Never skip a gate
"just for this commit" -- the CI pipeline runs the same gates and will fail the PR.

## Troubleshooting

| Symptom                                           | Likely cause                                  | Fix                                                                  |
|---------------------------------------------------|-----------------------------------------------|----------------------------------------------------------------------|
| `PermissionError: /app/data/script.log`           | Container data dir not writable               | `chmod -R 777 data/` on host, then restart container.                |
| `401 Unauthorized` in log                         | `MIST_API_TOKEN` missing or expired           | Rotate the token in Mist portal; update `.env`.                      |
| `404 Not Found` for the secpolicy_id              | Wrong org / policy UUID typed at prompt       | Re-verify UUIDs; list all policies with the sibling list endpoint.   |
| `AttributeError: module ... has no attribute ...` | `mistapi` version <0.59 or module path drift  | `pip install --upgrade mistapi` and retry; if it persists, log the actual attribute path and open an issue. |
| `EOFError` traceback                              | `safe_input()` not used somewhere in the path | Grep for stray `input(` calls in touched code and wrap them.         |

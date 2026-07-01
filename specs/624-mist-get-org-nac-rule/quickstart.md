# Phase 1 Quickstart: getOrgNacRule (Menu 59)

**Feature**: 624-mist-get-org-nac-rule
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Data model**: [data-model.md](./data-model.md)
**Contract**: [contracts/get_org_nac_rule.md](./contracts/get_org_nac_rule.md)

This quickstart lets a developer verify the new menu item locally on Windows
with a Python venv, and captures the exact quality-gate commands the
autonomous CI pipeline must run before merge.

---

## Prerequisites

- Python 3.13+ installed and on `PATH`.
- `.venv` created and activated (`.venv\Scripts\Activate.ps1`).
- Dependencies installed: `pip install -r requirements.txt` (or
  `uv pip sync requirements.txt`).
- A working `.env` file at repo root (never committed) with the
  variables listed below.
- Optional: an existing `data/org_nacrules.csv` produced by menu 43
  (`listOrgNacRules`) so you have a real `nacrule_id` to feed the prompt.

## Required `.env` variables

```
MIST_HOST=api.mist.com                     # or api.eu.mist.com, api.gc1.mist.com, etc.
MIST_API_TOKEN=<personal or org api token>
MIST_ORG_ID=<default org uuid>             # pre-fills the org_id prompt
```

No other environment variables are required for this menu item. Optional
tuning knobs (`MIST_PAGE_LIMIT`, `FAST_MODE_MAX_CONCURRENT_CONNECTIONS`,
etc.) do not affect this endpoint because it is a single-object,
non-paginated GET.

## Expected data output

- CSV: `data\org_nac_rule.csv` (one row per invocation; the same row is
  overwritten on subsequent runs of the same rule id when SQLite is the
  active backend).
- SQLite: table `org_nac_rule` in `data\mist_data.db` (created on first
  write by `DataExporter`).
- ArangoDB: document in collection `org_nac_rule` with `_key` = the rule
  UUID.
- Redis: cache key `mist:org_nac_rule:<nacrule_id>` with 300-second TTL
  (existing DataExporter default).

## Example invocation

### Interactive mode

```powershell
cd C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper.worktrees\copilot-openapi-mist-api-endpoint-cataloging
.venv\Scripts\Activate.ps1
python MistHelper.py
# Select 59 from the menu.
# Prompts:
#   Org ID [a97c1b22-a4e9-411e-9bfd-d8695a0f9e61]: <Enter to keep default>
#   NAC Rule ID: 53f10664-3ce8-4c27-b382-0ef66432349f
# Expected stdout:
#   INFO Fetching NAC rule 53f10664-... for org a97c1b22-...
#   DEBUG NAC rule 53f10664-... action=allow enabled=True matching_keys=3
#   INFO Wrote 1 row to data/org_nac_rule.csv
```

### Direct / non-interactive mode

```powershell
python MistHelper.py --menu 59 `
    --arg org_id=a97c1b22-a4e9-411e-9bfd-d8695a0f9e61 `
    --arg nacrule_id=53f10664-3ce8-4c27-b382-0ef66432349f
```

(exact `--arg` syntax follows the existing MistHelper CLI convention; the
`--test` sweep uses the same path.)

### Test-sweep mode

```powershell
python MistHelper.py --test
# Menu 59 is inside the default sweep range (not in the skip list 14, 18,
# 63-65, 90-100), so it runs automatically against the .env org using the
# first rule id returned by an initial listOrgNacRules probe.
```

## Method outline (for AI-generated implementation)

Every executable line below MUST carry an inline comment when written into
`MistHelper.py`, per Constitution VI. Every `logging.info` / `logging.debug`
pair MUST bracket every meaningful action, per Constitution VII.

```python
def export_org_nac_rule(self, org_id=None, nacrule_id=None):
    """Export a single Mist NAC rule (menu 59) via getOrgNacRule."""
    org_id = org_id or safe_input(                              # Prompt or use CLI arg for org
        f"Org ID [{self.default_org_id}]: ",
        context="org_nac_rule:org_id",
    ) or self.default_org_id                                    # Fall back to .env value
    nacrule_id = nacrule_id or safe_input(                      # Prompt or use CLI arg for rule
        "NAC Rule ID: ",
        context="org_nac_rule:nacrule_id",
    )
    if not is_valid_uuid(org_id) or not is_valid_uuid(nacrule_id):
        logging.warning("Invalid UUID input; aborting")         # Guard before API call
        return
    logging.info(                                               # Announce API call (Principle VII)
        "Fetching NAC rule %s for org %s", nacrule_id, org_id
    )
    resp = mistapi.api.v1.orgs.nac_rules.getOrgNacRule(         # SDK call (Principle II)
        self.apisession, org_id, nacrule_id
    )
    payload = resp.data or {}                                   # Empty dict on 404 / empty body
    if not payload:
        logging.warning("No NAC rule returned; nothing to write")
        return
    logging.debug(                                              # Post-call summary (ASCII, %s)
        "NAC rule %s action=%s enabled=%s matching_keys=%d",
        payload.get("id"),
        payload.get("action"),
        payload.get("enabled"),
        len((payload.get("matching") or {})),
    )
    row = self._flatten_nac_rule(payload, org_id)               # Class-private flattener
    DataExporter.write_with_format_selection(                   # Multi-backend persist
        [row],
        filename="org_nac_rule.csv",
        api_function_name="getOrgNacRule",                      # Resolves PK strategy
    )
```

The `_flatten_nac_rule` helper stays under 25 lines: iterate `matching` and
`not_matching` sub-dicts, prefix keys, join arrays with `";"`, cast `enabled`
to `int`, and stamp `misthelper_fetched_at = time.time()`.

## Quality gates (mandatory before commit)

Run all four gates before committing. Every one must pass with zero output
for lint/format and zero test failures. Refer to the constitution's
"Full Deployment Pipeline (NON-NEGOTIABLE)" principle.

```powershell
# 1. Syntax check (no output on success)
python -m py_compile MistHelper.py

# 2. Lint (Ruff must exit 0 with no findings)
python -m ruff check MistHelper.py

# 3. Format (Black must report "would be reformatted: 0")
python -m black --check MistHelper.py

# 4. Test-sweep including menu 59
python MistHelper.py --test
```

If any gate fails, fix in-place before committing. Do NOT add
`# noqa` / `# type: ignore` / Bandit suppressions without a documented
justification (constitution "Security Findings: Fix Over Suppress").

## CI expectations

The `.github/workflows/ci.yml` pipeline runs the same four gates plus
`mypy`, `Hypothesis`, `Bandit`, `pip-audit`, `CodeQL`, and `Playwright`
E2E (Playwright is a no-op for this CLI-only menu item). The
`auto-merge` label is added to the PR only after CodeQL is green.

## Rollback plan

If a post-merge issue is detected on menu 59:

1. Set `MIST_MENU_DISABLE=59` in `.env` (existing MistHelper disable list).
2. Revert the commit and re-run the container-build workflow.
3. Container consumers `podman pull` the reverted image and restart.

No database schema rollback is required because the new `org_nac_rule`
table is additive.

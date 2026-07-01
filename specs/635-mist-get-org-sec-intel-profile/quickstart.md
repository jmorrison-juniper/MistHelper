# Phase 1 Quickstart: getOrgSecIntelProfile (Menu 89)

Local dev quickstart for the new MistHelper menu item that reads a single
Security Intelligence profile from a Mist org.

## Prerequisites

- Python 3.13+ installed.
- Repository cloned; you are on branch `635-mist-get-org-sec-intel-profile`.
- Virtualenv activated: `.venv\Scripts\Activate.ps1` (Windows PowerShell).
- `mistapi` 0.59+ installed via `pip install -r requirements.txt` (or `uv
  sync`).

## Required `.env` Variables

Place these in `.env` at the repo root (git-ignored). None are logged.

| Variable                   | Required | Purpose                                                                 |
|----------------------------|----------|-------------------------------------------------------------------------|
| `MIST_HOST`                | Yes      | Mist API cloud host, e.g. `api.mist.com` or `api.gc1.mist.com`.         |
| `MIST_API_TOKEN`           | Yes      | API token used by `mistapi.APISession`. Never logged.                   |
| `MIST_ORG_ID`              | Optional | Presented as the default when prompted for `org_id`.                    |
| `MIST_SECINTEL_PROFILE_ID` | Optional | Consumed only when running under `--test` to keep CI deterministic.     |

## Expected Output Files (under `data/`)

- CSV summary: `data/org_secintel_profile_summary_{org_id}_{secintelprofile_id}.csv`
- CSV rules  : `data/org_secintel_profile_rules_{org_id}_{secintelprofile_id}.csv`
- SQLite    : `data/mist_data.db` -> tables
  `org_secintel_profile_summary` and `org_secintel_profile_rules`
- ArangoDB / Redis (if configured): documents keyed by
  `secintelprofile_id`; graph edge `org --owns--> secintel_profile` and
  `secintel_profile --has_rule--> secintel_rule`.

## How to Run

### Interactive

```powershell
# From the repo root, venv activated
python MistHelper.py
# At the main menu, type: 89
# When prompted:
#   Enter org_id [default from MIST_ORG_ID]: <UUID or blank to reuse default>
#   Enter secintelprofile_id: <UUID>
```

### Direct (non-interactive)

```powershell
# Direct dispatch for automation
python MistHelper.py --menu 89
```

### Full `--test` Sweep (CI / regression)

```powershell
# Runs the safe menu range; requires MIST_SECINTEL_PROFILE_ID in .env
python MistHelper.py --test
```

## Example Session

```
[MistHelper] Selected: 89 -- Get Sec Intel Profile
Enter org_id [12345678-90ab-cdef-1234-567890abcdef]:
Enter secintelprofile_id: aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
INFO  Fetching SecIntel profile aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee for org 12345678-90ab-cdef-1234-567890abcdef
DEBUG SecIntel profile: name=secintel-custom rules=3
INFO  Flattening 3 rule rows
DEBUG Flatten complete
INFO  Writing summary to data/org_secintel_profile_summary_12345678-90ab-cdef-1234-567890abcdef_aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee.csv
INFO  Writing rules to   data/org_secintel_profile_rules_12345678-90ab-cdef-1234-567890abcdef_aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee.csv
INFO  Menu 89 complete: 1 summary row, 3 rule rows
```

## Expected Method Outline (~20 lines) -- `SecurityExportUtils.export_org_secintel_profile`

Every executable line below carries an inline comment per Constitution
Principle VI. `logging.info` / `logging.debug` bracket every meaningful
action per Principle VII.

```python
def export_org_secintel_profile(self, org_id: str, secintelprofile_id: str) -> None:
    """Menu 89: read one Mist SecIntel profile and export it."""
    org_id = safe_input("Enter org_id: ", context="org_secintel_profile:org_id") or org_id  # Prompt with default fallback
    secintelprofile_id = safe_input("Enter secintelprofile_id: ", context="org_secintel_profile:profile_id") or secintelprofile_id  # Prompt for target profile
    if not self._is_uuid(org_id) or not self._is_uuid(secintelprofile_id):  # Validate UUID shape before API call
        logging.warning("Menu 89 aborted: invalid UUID input")  # Log guard-clause exit
        return  # Early return keeps the 5-Item Rule
    logging.info("Fetching SecIntel profile %s for org %s", secintelprofile_id, org_id)  # Pre-call action log
    response = mistapi.api.v1.orgs.secintel_profiles.getOrgSecIntelProfile(  # SDK call (sole permitted Mist interface)
        self.apisession, org_id, secintelprofile_id
    )
    payload = response.data or {}  # Defensive default when API returns empty body
    rules = payload.get("profiles") or []  # Nested per-category rule list
    logging.debug("SecIntel profile: name=%s rules=%d", payload.get("name"), len(rules))  # Post-call summary log
    summary_row = {  # Flatten header for the summary table
        "secintelprofile_id": secintelprofile_id,  # Natural PK column
        "org_id": org_id,  # Denormalized owning-org column
        "name": payload.get("name"),  # Human-readable profile name
        "rule_count": len(rules),  # Convenience count
        "retrieved_at": _now_iso(),  # ISO-8601 export timestamp
    }
    rule_rows = [  # Flatten nested profiles[] into one row per category
        {"secintelprofile_id": secintelprofile_id, "org_id": org_id,  # Composite PK columns
         "category": rule.get("category"), "action": rule.get("action"),  # Enum values
         "retrieved_at": summary_row["retrieved_at"]}  # Same timestamp for all rows in the batch
        for rule in rules
    ]
    logging.info("Writing SecIntel profile summary and %d rule rows", len(rule_rows))  # Pre-write log
    DataExporter.write_with_format_selection(  # Summary write (natural_pk upsert)
        [summary_row],
        filename=f"org_secintel_profile_summary_{org_id}_{secintelprofile_id}.csv",
        api_function_name="getOrgSecIntelProfile",
    )
    DataExporter.write_with_format_selection(  # Rule write (composite_pk upsert)
        rule_rows,
        filename=f"org_secintel_profile_rules_{org_id}_{secintelprofile_id}.csv",
        api_function_name="getOrgSecIntelProfile__rules",
    )
    logging.debug("Menu 89 complete: 1 summary row, %d rule rows", len(rule_rows))  # Post-write log
```

## Quality Gates (run before every commit)

```powershell
# 1. Syntax
python -m py_compile MistHelper.py

# 2. Lint (must be clean)
python -m ruff check MistHelper.py

# 3. Format (auto-fix by dropping --check)
python -m black --check MistHelper.py

# 4. Test sweep (interactive skip list respected)
python MistHelper.py --test
```

All four must be green before pushing. CI will re-run them and additionally
execute `mypy`, `bandit`, `pip-audit`, `pytest --cov`, Hypothesis, CodeQL,
and Playwright E2E per `.github/workflows/ci.yml`.

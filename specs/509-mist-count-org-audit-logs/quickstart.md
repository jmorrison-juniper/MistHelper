# Phase 1 Quickstart: countOrgAuditLogs (Menu 89)

How to run, validate, and verify the new menu item locally on Windows 11 + venv.

## Prerequisites

- Python 3.13+ installed and on `PATH`.
- Repo cloned to a worktree under `MistHelper.worktrees\`.
- Virtual env active: `.venv\Scripts\Activate.ps1` from the worktree root.
- Dependencies installed: `pip install -r requirements.txt` (or `uv pip install -r
  requirements.txt`).
- A `.env` file at the worktree root containing the variables listed below.

## Required `.env` Variables

| Variable          | Required | Example                                | Notes                                |
|-------------------|----------|----------------------------------------|--------------------------------------|
| `MIST_HOST`       | Yes      | `api.mist.com`                         | Mist Cloud region host.              |
| `MIST_API_TOKEN`  | Yes      | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`     | Org-scoped API token; never logged.  |
| `MIST_LOG_LEVEL`  | No       | `DEBUG`                                | Bump to `DEBUG` to see post-call counts. |
| `MIST_OUTPUT`     | No       | `csv` / `sqlite` / `arangodb`          | DataExporter backend selector.       |

The API token is loaded once by the existing `mistapi.APISession`. The new menu method
never logs, prints, or echoes the token.

## Expected `data/` Output

Two files / tables are produced per run:

| Filename / Table                                                                       | Contents                                              |
|----------------------------------------------------------------------------------------|-------------------------------------------------------|
| `data/org_audit_logs_count_summary_<org_id>_<distinct>_<window>.csv` / table `org_audit_logs_count_summary` | One row -- summary of the aggregation request and total count. |
| `data/org_audit_logs_count_buckets_<org_id>_<distinct>_<window>.csv` / table `org_audit_logs_count_buckets` | N rows -- one per distinct bucket value with its count. |

ArangoDB backend writes the same two logical entities into collections of the same name.

## Example Interactive Invocation

```powershell
# From the repo root with the venv active:
python MistHelper.py
# Menu appears -- type:
89
# Prompts (defaults shown in brackets):
Org ID (UUID): 203d3d02-aaaa-bbbb-cccc-1234567890ab
Distinct field [admin_id|admin_name|message|site_id] (default: admin_name):
Duration window (e.g. 1d, 7d, 2w) (default: 1d): 7d
Result limit (default: 100):
```

Expected console behaviour:

```text
INFO  Counting org audit logs for org 203d3d02-... by distinct=admin_name window=7d limit=100
INFO  Calling mistapi.api.v1.orgs.logs.countOrgAuditLogs
DEBUG Audit-log count: total=1342 buckets=18 distinct=admin_name window=1719012345..1719617145
INFO  Flattening summary + 18 bucket rows
DEBUG Flatten complete: summary=1 buckets=18
INFO  Writing output via DataExporter (backend: sqlite)
DEBUG Wrote 1 row to org_audit_logs_count_summary; 18 rows to org_audit_logs_count_buckets
```

## Non-Interactive Invocation (Used by `--test`)

```powershell
python MistHelper.py --menu 89
```

The `--test` sweep picks `org_id` from `.env` (`MIST_TEST_ORG_ID`) and falls back to the
documented prompt defaults (`distinct=admin_name`, `duration=1d`, `limit=100`). The
operation must return exit code 0 on a known-good org.

## Quality Gates (Must Pass Before Commit)

```powershell
# 1. Syntax check -- no output on success.
python -m py_compile MistHelper.py

# 2. Lint -- must report 0 violations.
python -m ruff check MistHelper.py

# 3. Format check -- run without --check to auto-fix if it fails.
python -m black --check MistHelper.py

# 4. Functional test -- exercises the new menu item against a real org.
python MistHelper.py --test
```

All four gates must be green before the commit hits `main`. The CI workflow
(`.github/workflows/ci.yml`) re-runs the same gates plus mypy, Bandit, pip-audit,
Hypothesis, pytest-cov >= 70%, and CodeQL.

## Implementation Outline (for reviewers)

The new method on the existing audit-log exporter class, with the expected
inline-comment density:

```python
def export_org_audit_logs_count(self) -> None:                                # Public menu method on existing class
    org_id = safe_input(                                                      # Step 1: prompt for org UUID
        "Org ID (UUID): ",                                                    # Human-readable prompt label
        context="org_audit_logs_count:org_id",                                # Context tag for safe_input EOF handler
    )
    if not is_valid_uuid(org_id):                                             # Reject malformed input before any API call
        logging.warning("Invalid org_id %s -- aborting", org_id)              # ASCII warning; no traceback
        return                                                                # Early return per safety-first
    distinct = safe_input(                                                    # Step 2: prompt for grouping field
        "Distinct field [admin_id|admin_name|message|site_id] (default: admin_name): ",
        context="org_audit_logs_count:distinct",
    ) or "admin_name"                                                         # Default per Research Task 5
    if distinct not in ALLOWED_AUDIT_LOG_DISTINCT:                            # Validate against documented enum
        logging.warning("Invalid distinct %s -- aborting", distinct)          # Reject unknown bucket field
        return                                                                # Early return per safety-first
    duration = safe_input(                                                    # Step 3: prompt for time window
        "Duration window (e.g. 1d, 7d, 2w) (default: 1d): ",
        context="org_audit_logs_count:duration",
    ) or "1d"                                                                 # Default per OpenAPI spec
    limit = _parse_int_or_default(                                            # Step 4: prompt for limit + parse
        safe_input("Result limit (default: 100): ",
                   context="org_audit_logs_count:limit"),
        default=100,                                                          # OpenAPI default
    )
    logging.info(                                                             # Action log BEFORE the SDK call
        "Counting org audit logs for org %s by distinct=%s window=%s limit=%d",
        org_id, distinct, duration, limit,
    )
    response = mistapi.api.v1.orgs.logs.countOrgAuditLogs(                    # The one and only SDK call
        self.apisession, org_id,
        distinct=distinct, duration=duration, limit=limit,
    )
    payload = response.data or {}                                             # Tolerate empty payload
    buckets = payload.get("results", [])                                      # Bucket array per schema
    logging.debug(                                                            # Action log AFTER the SDK call
        "Audit-log count: total=%s buckets=%d window=%s..%s",
        payload.get("total"), len(buckets),
        payload.get("start"), payload.get("end"),
    )
    summary_row, bucket_rows = self._flatten_audit_log_count(                 # Private flatten helper on same class
        org_id, payload, distinct,
    )
    DataExporter.write_with_format_selection(                                 # Multi-backend persistence
        {"org_audit_logs_count_summary": [summary_row],                       # One-row summary table
         "org_audit_logs_count_buckets": bucket_rows},                        # N-row bucket table
        filename_stem=f"org_audit_logs_count_{org_id}_{distinct}_{duration}", # Window-suffixed filename per Research Task 3
        api_function_name="countOrgAuditLogs",                                # Used by PK strategy lookup
    )
```

Total executable lines: ~22. Parameters: 1 (`self`). Logical blocks: 5 (prompt-and-
validate, prompt-distinct, prompt-window+limit, API call, flatten + write). All within
the Five-Item Rule budget.

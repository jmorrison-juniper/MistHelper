# Phase 1 Quickstart: countOrgJsiAssetsAndContracts (proposed menu 96)

**Feature**: Mist API GET `/api/v1/orgs/{org_id}/jsi/inventory/count`
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Prerequisites

1. **Python**: 3.13+ available on `PATH`.
2. **venv activated**:
   ```powershell
   .venv\Scripts\Activate.ps1
   ```
3. **Dependencies installed** (`mistapi` 0.59+):
   ```powershell
   pip install -r requirements.txt
   ```
4. **Linked Juniper account**: The org under test must have at least one Juniper
   account linked, otherwise the endpoint returns `400 - no Juniper Account Linked`
   (handled as a `WARNING` in the new method, not a traceback).

## Required `.env` variables

The file lives at the repo root and is git-ignored. It is loaded automatically by
`mistapi.APISession` via `python-dotenv`.

```dotenv
# Mist Cloud connection
MIST_HOST=api.mist.com                # or api.eu.mist.com, api.gc1.mist.com, etc.
MIST_API_TOKEN=<your_org_api_token>   # never log this, never commit this

# Optional: lets the menu prompt fall back to this value when the operator just
# presses Enter at the org_id prompt. Strongly recommended for daily-driver use.
MIST_ORG_ID=<your_org_uuid>
```

## Expected data/ output

For a run with `org_id=11111111-2222-3333-4444-555555555555`, `distinct=model`,
`limit=100`, the menu writes (timestamps will vary):

```text
data/org_11111111_jsi_inventory_count_20260628_214500.csv
data/org_11111111_jsi_inventory_count_summary_20260628_214500.csv
data/mist_data.db                # tables org_jsi_inventory_count_summary
                                 #        org_jsi_inventory_count_results
```

When the active backend is ArangoDB+Redis, the same data lands as a vertex per
bucket row and a single summary vertex, with edges joining bucket -> summary on
`(org_id, distinct, retrieved_at_epoch)`. No filesystem CSV is written in that
mode.

## Example invocation (interactive)

```text
PS C:\...\MistHelper> python MistHelper.py
...
Select menu item: 96
Org ID [press Enter to use MIST_ORG_ID from .env]: <Enter>
Distinct field to bucket by (model, family, sku, ...) [blank = unbucketed]: model
Limit (1-1000) [default 100]: 100
INFO  Counting JSI inventory for org 11111111-... distinct=model limit=100
DEBUG JSI count: total=421 buckets=14
INFO  Flattening response into summary + bucket rows
DEBUG Flatten complete: summary=1 row, results=14 rows
INFO  Writing to active backend (sqlite + csv)
DEBUG Wrote 14 result rows + 1 summary row
Done. Press Enter to return to menu.
```

## Example invocation (non-interactive / CI sweep)

```powershell
python MistHelper.py --menu 96
```

`--menu` skips the menu loop and runs the named item once with prompts that fall
back to `.env` values. Exit code 0 on success (including the "no data" edge case);
non-zero only on unhandled exceptions.

## Local quality gates

All three must pass before commit / push:

```powershell
# 1. Syntax check
python -m py_compile MistHelper.py     # No output = valid

# 2. Lint
python -m ruff check MistHelper.py     # Must pass clean

# 3. Format
python -m black --check MistHelper.py  # Run without --check to auto-fix

# 4. Functional sweep (uses MIST_ORG_ID from .env)
python MistHelper.py --test            # Menu 96 sits in the default sweep range
```

After all four pass locally, follow the standard pipeline in
`.github/copilot-instructions.md` (`commit -> push -> container-build.yml ->
podman pull -> restart container -> podman ps`).

## Method outline (for reviewers)

The new method on `InventoryExportUtils` looks like this -- every executable line
will carry an inline comment in the final PR (Constitution VI, NON-NEGOTIABLE):

```python
def export_org_jsi_inventory_count(                              # menu 96 entry point
    self,
    org_id: str | None = None,                                   # prompt + .env fallback
    distinct: str | None = None,                                 # optional bucketing field
    limit: int = 100,                                            # server default
) -> int:
    """Count JSI inventory items, optionally bucketed by `distinct`."""
    org_id = self._prompt_org_id(org_id)                         # safe_input + UUID validate
    distinct = self._prompt_distinct(distinct)                   # safe_input, may stay None
    limit = self._prompt_limit(limit, lo=1, hi=1000)             # safe_input + clamp
    logging.info(                                                # Action Logging: before call
        "Counting JSI inventory for org %s distinct=%s limit=%s",
        org_id, distinct, limit,
    )
    response = mistapi.api.v1.orgs.jsi.countOrgJsiAssetsAndContracts(  # single SDK call
        self.apisession, org_id, distinct=distinct, limit=limit,
    )
    payload = response.data or {}                                # defensive default
    logging.debug(                                               # Action Logging: after call
        "JSI count: total=%s buckets=%d",
        payload.get("total"), len(payload.get("results") or []),
    )
    summary_row, bucket_rows = self._flatten_jsi_count(          # split envelope vs buckets
        payload, org_id=org_id,
    )
    DataExporter.write_with_format_selection(                    # multi-backend persist
        data={"summary": [summary_row], "results": bucket_rows},
        filename=self._build_jsi_count_filename(org_id),
        api_function_name="countOrgJsiAssetsAndContracts",
    )
    return 0                                                     # success exit
```

The two private helpers `_flatten_jsi_count()` and `_build_jsi_count_filename()`
live on the same class so the 5-Item Rule holds (the public method stays under 25
lines).

## Troubleshooting

| Symptom                                                | Likely cause                                             | Fix                                            |
|--------------------------------------------------------|----------------------------------------------------------|------------------------------------------------|
| `400 - no Juniper Account Linked`                      | Org has no linked JSI account                            | Link a Juniper account in the Mist UI, retry. |
| `401 Unauthorized`                                     | `MIST_API_TOKEN` missing / expired                       | Regenerate token, update `.env`.              |
| `404 Not Found` on a valid-looking UUID                | Org UUID typo, or token does not have org access         | Verify org with `listMyOrgs`.                  |
| Empty `results[]`, `total=0`                           | Org has zero JSI items for that bucket                   | Expected; menu logs "no data returned" and exits 0. |
| Traceback on Enter at prompt                           | Not using `safe_input()` (regression -- file a bug)      | n/a                                            |
| `PermissionError: '/app/data/...'` inside container    | `data/` dir not chmod 777 on host                        | `chmod -R 777 data/` on the host.              |

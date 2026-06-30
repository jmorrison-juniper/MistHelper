# Phase 1 Quickstart: countSiteGuestAuthorizations (proposed menu 94)

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

This quickstart is for developers and AI agents implementing or testing menu item
**94 -- Count Site Guest Authorizations**.

---

## Prerequisites

- Windows 11 + Python 3.13+ (`python --version` must show 3.13 or newer).
- `.venv` activated:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- Dependencies installed:
  ```powershell
  pip install -r requirements.txt
  ```
- Repository root: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper.worktrees\copilot-openapi-mist-api-endpoint-cataloging`.

## Required `.env` variables

Placed at the repo root in the git-ignored `.env` file. Template lives in
`deploy/.env.example`.

| Variable          | Purpose                                                             |
|-------------------|---------------------------------------------------------------------|
| `MIST_HOST`       | API hostname, e.g. `api.mist.com` (or your regional cluster).       |
| `MIST_API_TOKEN`  | API token with read scope on the target org / site.                 |
| `MIST_ORG_ID`     | Optional fallback org id (not required by this endpoint).           |
| `MIST_SITE_ID`    | Optional convenience site id used by `--test` non-interactive mode. |

The endpoint itself only needs `MIST_HOST` and `MIST_API_TOKEN`; `MIST_SITE_ID` makes
`--test` runs reproducible without prompting.

## How to run this menu item locally

Interactive (will prompt for `site_id`, `distinct`, `duration`):

```powershell
python MistHelper.py --menu 94
```

Non-interactive `--test` sweep (uses `MIST_SITE_ID` from `.env` and the defaults
`distinct=wlan_id`, `duration=1d`):

```powershell
python MistHelper.py --test
```

Inside the running Podman container (when the container is up):

```powershell
podman exec -it misthelper python MistHelper.py --menu 94
```

## Expected `data/` output

After a successful run the following files are written / updated under `data/`:

- `data\SiteGuestAuthorizationCounts.csv` -- one row per distinct bucket plus one
  synthetic summary row (`is_summary = 1`).
- `data\mist_data.db` -- table `countSiteGuestAuthorizations` upserted with the same
  rows; composite unique constraint on
  `(site_id, distinct, bucket_value, window_start, window_end)` prevents duplicates.
- `data\script.log` -- structured log lines:
  ```
  INFO Counting guest authorizations for site <site_id> distinct=<attr> duration=<dur>
  DEBUG Guest auth count response: total=<N> buckets=<M>
  INFO Flattening guest auth count payload into <M+1> rows
  DEBUG Flatten complete: <M> bucket rows + 1 summary row
  INFO Writing SiteGuestAuthorizationCounts via DataExporter
  ```

(If running with the polyglot backend, `arangodb` collection
`countSiteGuestAuthorizations` and Redis cache keys `mist:csga:<site_id>:*` are also
updated.)

## Example invocation with prompts

```
$ python MistHelper.py --menu 94
Site ID: 1c7d2c0a-1234-5678-9abc-aabbccddeeff
Distinct attribute (ssid|wlan_id|auth_method|hostname) [wlan_id]:
Duration (e.g. 1d, 7d, 2w) [1d]: 7d

! Counting guest authorizations for site 1c7d2c0a-1234-5678-9abc-aabbccddeeff ...
! 4 buckets returned (total=873). Exported to SiteGuestAuthorizationCounts.csv
```

## Implementation outline (method skeleton)

The new method lives on `OrgSiteExporter` in `MistHelper.py`. Every executable line will
carry an inline comment (Principle VI) and the action-logging pattern (Principle VII):

```python
@staticmethod
def count_site_guest_authorizations():                       # New menu 94 entry point.
    """Count site guests grouped by a distinct attribute."""
    site_id = safe_input(                                    # Prompt for site UUID.
        "Site ID: ",
        context="count_site_guest_authorizations:site_id",
    )
    if not _is_uuid(site_id):                                # Validate before API call.
        logging.warning("Invalid site_id shape: %s", site_id)
        return                                               # Early exit, no traceback.
    distinct = safe_input(                                   # Prompt for distinct attr.
        "Distinct attribute [wlan_id]: ",
        context="count_site_guest_authorizations:distinct",
    ) or "wlan_id"                                           # Default when blank.
    duration = safe_input(                                   # Prompt for window length.
        "Duration [1d]: ",
        context="count_site_guest_authorizations:duration",
    ) or "1d"                                                # Default when blank.
    logging.info(                                            # INFO before API call.
        "Counting guest authorizations for site %s distinct=%s duration=%s",
        site_id, distinct, duration,
    )
    response = mistapi.api.v1.sites.guests.count.countSiteGuestAuthorizations(
        apisession, site_id, distinct=distinct, duration=duration,
    )                                                        # SDK call -- read only.
    payload = response.data or {}                            # Defensive default.
    logging.debug(                                           # DEBUG after API call.
        "Guest auth count response: total=%s buckets=%s",
        payload.get("total"), len(payload.get("results", [])),
    )
    rows = OrgSiteExporter._flatten_guest_count(payload, site_id)   # Flatten step.
    DataExporter.write_with_format_selection(                # Multi-backend export.
        rows,
        "SiteGuestAuthorizationCounts.csv",
        api_function_name="countSiteGuestAuthorizations",
    )
```

Helper `_flatten_guest_count(payload, site_id)` returns `[summary_row, *bucket_rows]`
matching the SQLite columns documented in `data-model.md`.

## Menu registration

Add to the menu dispatch table in `MistHelper.py`:

```python
94: (                                                        # Proposed menu number.
    "Count Site Guest Authorizations",                       # Human-readable label.
    OrgSiteExporter.count_site_guest_authorizations,         # Method reference, no call.
),
```

## Quality gates (run before every commit)

```powershell
python -m py_compile MistHelper.py        # Syntax must be clean.
python -m ruff check MistHelper.py        # Lint must pass.
python -m black --check MistHelper.py     # Format must pass.
python MistHelper.py --test               # Full menu sweep must return 0.
```

If any gate fails, do not commit. Fix the issue and re-run all four gates. The `--test`
sweep automatically skips heavy/destructive operations (14, 18, 63-65, 90-100); menu 94
is in scope and must pass.

## Smoke-test checklist

Use this list after wiring up the menu method:

- [ ] `python -m py_compile MistHelper.py` returns no output.
- [ ] `ruff check MistHelper.py` returns "All checks passed!".
- [ ] `black --check MistHelper.py` returns "would not be reformatted".
- [ ] `python MistHelper.py --menu 94` with a known site_id produces
      `data/SiteGuestAuthorizationCounts.csv` containing at least one row.
- [ ] Re-running the same command does not add duplicate rows to
      `data/mist_data.db` table `countSiteGuestAuthorizations`.
- [ ] `data/script.log` contains the INFO + DEBUG pair for the API call.
- [ ] `python MistHelper.py --test` exits 0 with menu 94 included.
- [ ] README.md operation count incremented and a new table row for menu 94 added.
- [ ] CHANGELOG.md updated with a `version YY.MM.DD.HH.MM` entry.

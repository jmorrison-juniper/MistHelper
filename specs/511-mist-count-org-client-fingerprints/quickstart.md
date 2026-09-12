# Phase 1 Quickstart: countOrgClientFingerprints Menu Item

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Menu number (proposed)**: 79
**Operation**: `countOrgClientFingerprints`
**Endpoint**: `GET /api/v1/sites/{site_id}/insights/fingerprints/count`

## Prerequisites

- Python 3.13+ installed and on PATH.
- Local virtual environment activated:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- `mistapi` 0.59+ and other requirements installed:
  ```powershell
  python -m pip install -r requirements.txt
  ```
- `.env` file at repo root (git-ignored) with at minimum:
  ```ini
  MIST_HOST=api.mist.com
  MIST_API_TOKEN=<your-token>
  MIST_TEST_SITE_ID=<a-known-site-uuid-for-non-interactive-tests>
  ```
- `data/` directory exists and is writable. When running in the
  container the mounted volume needs `chmod -R 777 data/` once on
  first run.

## Required `.env` Variables

| Variable | Purpose | Required? |
|----------|---------|-----------|
| `MIST_HOST` | Mist Cloud region host (for example `api.mist.com`, `api.eu.mist.com`). | Yes |
| `MIST_API_TOKEN` | Mist API token with read access to the target org / site. | Yes |
| `MIST_TEST_SITE_ID` | Site UUID used by `--test` mode for non-interactive runs. | Recommended (needed for CI / `--test` coverage of menu 79) |

No new environment variables are introduced by this feature; the three
above already exist for adjacent insight exports.

## Expected `data/` Output

- CSV backend (default):
  `data/site_client_fingerprints_count_<site_id>_<YYYYMMDD_HHMMSS>.csv`
  (summary fields) plus
  `data/site_client_fingerprints_count_buckets_<site_id>_<YYYYMMDD_HHMMSS>.csv`
  (one row per bucket). Naming follows the convention applied by
  `DataExporter.write_with_format_selection()` for paired summary +
  detail outputs.
- SQLite backend: rows upserted into
  `site_client_fingerprints_count_summary` and
  `site_client_fingerprints_count_buckets` inside
  `data/mist_data.db`. See [data-model.md](./data-model.md) for the
  DDL and PK strategy.
- ArangoDB+Redis backend: one document per `(site_id, distinct, start,
  end)` in the `site_client_fingerprints_count` collection with the
  buckets embedded as a nested array, plus the matching Redis cache
  key.

## How to Run Locally (Interactive)

1. Launch the CLI:
   ```powershell
   python MistHelper.py
   ```
2. From the main menu, select **79 -- Count Site Client Fingerprints
   (Insights)** (label finalized at task generation; the example uses
   the proposed wording from `plan.md`).
3. Respond to the prompts (all collected via `safe_input()`):
   - `Site ID (UUID)`: paste the site UUID; Enter on empty exits the
     menu with a warning.
   - `Distinct field [empty for server default]`: type one of
     `family`, `model`, `os`, `manufacturer`, or press Enter to
     accept the server default.
   - `Duration [default 1d]`: type a Mist duration like `7d`, `2w`,
     or press Enter for `1d`.
   - `Start (epoch or relative, optional)`: press Enter to skip and
     use `duration`.
   - `End (epoch or relative, optional)`: press Enter to skip and use
     `duration`.
   - `Result limit [default 100]`: press Enter or supply an integer.
4. MistHelper logs `INFO` ("Fetching client fingerprint count for site
   <id> distinct=<value> duration=<value>"), invokes the SDK once,
   logs `DEBUG` with returned counts ("Fingerprint count: total=<N>
   buckets=<M> limit=<L>"), flattens the response, writes through
   `DataExporter.write_with_format_selection(payload, filename,
   api_function_name='countOrgClientFingerprints')`, and returns to
   the menu.

## How to Run Non-Interactively (Direct Invocation)

```powershell
python MistHelper.py --menu 79
```

When `MIST_TEST_SITE_ID` is set, the menu uses that value and the
server defaults for all other prompts; otherwise the operation logs a
warning and returns early without making an API call. This is the path
exercised by `python MistHelper.py --test`.

## Example Inline Method Skeleton (for review during task generation)

The method below is illustrative -- the actual implementation lives in
`MistHelper.py` and conforms to the Constitution's Inline Comments
(VI) and Action Logging (VII) principles. Every executable line below
carries a comment that explains *why*; logging surrounds every
meaningful action.

```python
def export_site_client_fingerprints_count(self):                               # public menu method, no required positional args
    site_id = safe_input(                                                      # prompt for the only required path parameter
        "Site ID (UUID): ",
        context="site_client_fingerprints_count:site_id",
    )                                                                          # safe_input handles EOF in SSH / container
    if not is_valid_mist_uuid(site_id):                                        # validate before spending an API call
        logging.warning("Invalid site UUID; aborting menu 79")                 # warn, do not raise
        return                                                                 # early return preserves menu loop
    distinct = safe_input(                                                     # optional grouping field
        "Distinct field [empty for server default]: ",
        context="site_client_fingerprints_count:distinct",
    ) or None                                                                  # empty -> None so SDK uses server default
    duration = safe_input(                                                     # optional time window shorthand
        "Duration [default 1d]: ",
        context="site_client_fingerprints_count:duration",
    ) or "1d"                                                                  # preserve documented Mist default
    result_limit = parse_optional_int(                                         # tolerant int parser used elsewhere
        safe_input(
            "Result limit [default 100]: ",
            context="site_client_fingerprints_count:limit",
        ),
        default=100,
    )                                                                          # fall back to server default on parse failure
    logging.info(                                                              # action log BEFORE the call (Principle VII)
        "Fetching client fingerprint count for site %s distinct=%s duration=%s",
        site_id, distinct, duration,
    )
    response = mistapi.api.v1.orgs.nac_fingerprints.countOrgClientFingerprints(
        self.apisession,                                                       # shared mistapi.APISession from .env
        site_id,                                                               # path parameter
        distinct=distinct,                                                     # query parameter (or None)
        duration=duration,                                                     # query parameter
        limit=result_limit,                                                    # query parameter
    )                                                                          # single SDK call; adaptive delay applies
    payload = response.data or {}                                              # tolerate empty body on 404 / 204
    logging.debug(                                                             # action log AFTER the call (Principle VII)
        "Fingerprint count: total=%d buckets=%d limit=%d",
        payload.get("total", 0),
        len(payload.get("results", []) or []),
        payload.get("limit", result_limit),
    )
    DataExporter.write_with_format_selection(                                  # multi-backend write
        flatten_fingerprint_count(site_id, payload),                           # produces summary + bucket rows
        filename="site_client_fingerprints_count",                             # base name; backend adds suffix
        api_function_name="countOrgClientFingerprints",                        # ties the write to the PK strategy entry
    )
```

`parse_optional_int`, `is_valid_mist_uuid`, and
`flatten_fingerprint_count` are either existing helpers in
`MistHelper.py` or small private helpers added on the same class during
implementation (preferred over module-level wrappers per Principle II).

## Quality Gates (Run Before Commit)

```powershell
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py
python -m black --check MistHelper.py
python MistHelper.py --test
```

All four must pass green. The `--test` run exercises menu 79 in
non-interactive mode against `MIST_TEST_SITE_ID`. After commit, the
standard deployment pipeline (see
`.github/copilot-instructions.md` -> Full Deployment Pipeline) applies
without modification.

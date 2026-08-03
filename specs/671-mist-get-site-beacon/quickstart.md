# Quickstart Validation: getSiteBeacon

## Purpose

Validate the new Issue #1420 menu operation for `getSiteBeacon` end-to-end across input handling, API execution, and output persistence.

## Prerequisites

1. Python 3.13+ environment with project dependencies installed.
2. Valid Mist API token in `.env`.
3. Known valid `site_id` and `beacon_id` pair in target org.
4. Writable `data/` directory (and container permissions if running in Podman).

## Validation Scenario A: Static checks

Run from repo root:

1. `python -m py_compile MistHelper.py`
2. `python -m ruff check`
3. `python -m black --check .`

Expected:
- All commands exit 0.

## Validation Scenario B: Interactive menu happy path

1. Launch: `python MistHelper.py`
2. Select the new menu number for `getSiteBeacon`.
3. Enter required identifiers when prompted.
4. Complete run.

Expected:
- No traceback.
- Info log before API request; debug log with response count after request.
- Export artifact written under `data/`.

## Validation Scenario C: Non-interactive/EOF safety

1. Run the menu in an SSH/container context.
2. Trigger EOF during one prompt (or provide empty stream).

Expected:
- `safe_input()` handles EOF.
- Operation exits cleanly (status 0) without unhandled exception.

## Validation Scenario D: Repeat-run upsert behavior (SQLite)

1. Set SQLite output mode.
2. Run the same `site_id` + `beacon_id` twice.
3. Inspect resulting SQLite table row count for the same beacon `id`.

Expected:
- No duplicate rows for the same natural primary key.

## Validation Scenario E: Error handling

### Unknown beacon/site

- Use invalid `site_id` or `beacon_id`.
- Expect warning/error log with controlled exit (no traceback).

### Rate limit

- Simulate/observe 429 path.
- Expect retry/backoff behavior consistent with existing adaptive delay controls.

## Related Artifacts

- Data shape + keys: `data-model.md`
- Interface constraints: `contracts/get-site-beacon-contract.md`
- Response schema: `contracts/get-site-beacon-response.schema.json`

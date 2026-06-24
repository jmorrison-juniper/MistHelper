# Baseline Fixture Sample — Issue #429

**Purpose**: Enumerate the ≥ 30 logging call sites whose rendered output is captured on `main` (pre-refactor) and frozen as `tests/fixtures/issue_429_log_baseline.json`. The parity test (`tests/test_issue_429_log_parity.py`) re-exercises these exact sites post-refactor under `caplog` and asserts byte-identical `LogRecord.getMessage()` output.

**Selection rules**:
1. ≥ 30 total entries.
2. Every edge-case pattern from spec §Edge Cases MUST be represented by ≥ 1 entry (when such a pattern actually exists in `MistHelper.py` — patterns not present are noted "not found, skipped").
3. Prefer sites in functions that are testable without external dependencies (no live Mist API calls, no SSH connections). Where unavoidable, the test mocks the API/SSH layer.

## Fixture Catalog

| # | Line | Pattern | Call site (truncated) | Test approach |
|---:|---:|---|---|---|
| 1 | 315 | plain f-string at module top | `f"Python {version_str} detected. MistHelper requires Python {required_str}+. "` | Direct call: invoke `_check_python_version()` with a known version tuple |
| 2 | 800 | already-lazy baseline (NEGATIVE control) | `logging.info("UV package manager not found in PATH or Python environment")` | Confirms idempotency: codemod leaves this untouched |
| 3 | 1343 | attribute access in interpolation | `logging.info(f"Python executable: {sys.executable}")` | Patch `sys.executable` to a known value |
| 4 | 1483 | attribute access (.stderr) | `logging.error(f"Failed to install UV via pip: {result.stderr}")` | Build fake `result` with `.stderr = "fixture-error"` |
| 5 | 1776 | multi-arg interpolation (3 substitutions) | `logging.info(f"{desc}: {total} {unit}s to process")` | Call enclosing function with known args |
| 6 | 2776 | subscript + slicing in interpolation | `logging.debug(f"Could not fetch MSP name for {msp_id[:8]}...: {e}")` | Pass known `msp_id` and `Exception("e")` |
| 7 | 2871 | call expression in interpolation (`len(...)`) | `f"Successfully switched to interactive login session with {len(msp_privileges)} MSP(s)"` | Pass list of fixture privileges |
| 8 | 5848 | attribute call (`.__name__`) | `f"Failed to generate {file_name} using {generate_function.__name__}: {error}"` | Pass real function reference for `.__name__` |
| 9 | 6120 | **G003 — concat with `+`** | `logging.debug("\n" + table.get_string())` | Build fake `table` with `.get_string()` returning fixture string |
| 10 | 6898 | parenthesized interp with comma in literal | `f"! Failed to fetch config for {site_name} (ID: {site_id}): {error}"` | Three known args |
| 11 | 6988 | **format spec `.2f` + arithmetic in interp** | `f"Retrying device {failed_device_id} in {delay:.2f}s (attempt {attempt + 2}/{max_retries + 1})"` | Known floats / ints — also feeds the hypothesis test for `.2f` |
| 12 | 7368 | slicing + literal ellipsis | `f"Generated CREATE TABLE SQL for {safe_table_name}: {create_sql[:100]}..."` | Long `create_sql` to exercise the slice |
| 13 | 7881 | **ternary inside f-string** | `f"ENTRY: DataExporter.write_to_csv(data_rows={len(data) if data else 0}, csv_file=..."` | Once with `data=[1,2,3]`, once with `data=None` |
| 14 | 8151 | format spec `.2f` (simple) | `logging.debug(f"Applying rate limit delay: {delay:.2f}s")` | Iterate `delay` through `[0.0, 0.5, 1.23456, 100.0]` |
| 15 | 8316 | **G003 — concat with `+`** | `logging.debug("\n" + table.get_string())` | Same pattern as #9 — confirms multi-site consistency |
| 16 | 8684 | **G201 inside except — `error(..., exc_info=True)`** | `logging.error(f"Exception in PromptClientUtils.select_client_mac: {error}", exc_info=True)` | Raise `ValueError("fixture")` inside enclosing try; assert `.exception(...)` is called post-refactor; assert traceback emission still occurs |
| 17 | 9286 | **G201 inside except** (second site) | `logging.error(f"Exception in DeviceUtils.get_all_ap_macs_from_site: {error}", exc_info=True)` | Same protocol as #16 |
| 18 | 10898 | **G003 — concat** (third site) | `logging.debug("\n" + table.get_string())` | Same as #9 |
| 19 | 11634 | format spec `.1f` | `logging.info(f"Offline device report completed in {elapsed:.1f} seconds")` | Iterate `elapsed` for hypothesis seed |
| 20 | 12303 | **G201** inside except | `logging.error(f"Failed to fetch wired clients: {exception}", exc_info=True)` | Same protocol as #16 |
| 21 | 10991 | **G003 — concat** (fourth site) | `logging.debug("\n" + table.get_string())` | Same as #9 |
| 22 | 13421 | **G003 — concat** (fifth site) | `logging.debug("\n" + table.get_string())` | Same as #9 |
| 23 | 13296 | side-effecting call in args (NOT in f-string) | `response = mistapi.api.v1.orgs.logs.listOrgAuditLogs(apisession, org_id, **kwargs)` followed by logging | Mock `mistapi` call; assert log emitted after call |
| 24 | 15088 | already-non-logging line (NEGATIVE control) | `DataExporter.save_data_to_output([], config.filename)` | Confirms codemod ignores non-logging calls |
| 25 | 18146 | `logging.error(traceback.format_exc())` | bare exception trace | Assert format_exc string passed through unchanged |
| 26 | 23933 | tail of file — `logging.debug("EXIT: __main__ - unhandled exception")` | already lazy (NEGATIVE control) | Confirms no rewrite |
| 27 | (TBD — find by grep at exec time) | f-string with `%` literal in template | needs `%%` escape post-conversion | Search `Select-String -Pattern 'logging\.\w+\(f".*%.*\{'` and pick first match |
| 28 | (TBD) | multi-line f-string (implicit concat) | needs multi-line `%s` template re-flow | Search `Select-String -Pattern 'logging\.\w+\(\s*$' -Context 0,3` then filter for f-string continuation |
| 29 | (TBD) | `logging.log(level, f"...")` with explicit level | level arg preserved | Search `Select-String -Pattern 'logging\.log\(\w+,\s*f"'` |
| 30 | (TBD) | `self.logger.info(f"...")` (attribute access on `self`) | confirms codemod recognizes `self.logger.*` | Search `Select-String -Pattern 'self\.\w*logger?\.\w+\(f"'` |
| 31 | (TBD) | `f"{x:>10}"` width/align format spec | needs `%10s` or `%-10s` equivalent | Search `Select-String -Pattern 'logging\.\w+\(f".*\{[^}]+:>?\d+\}'` |
| 32 | (TBD) | `f"{x:05d}"` zero-pad integer | needs `%05d` equivalent | Search `Select-String -Pattern 'logging\.\w+\(f".*\{[^}]+:0?\d+d\}'` |

## Patterns NOT FOUND in `MistHelper.py` (skipped, no fixture entry needed)

Confirmed via grep on 2026-06-23 in this worktree — no match for any of:

| Pattern | Grep used |
|---|---|
| `f"{x!r}"` repr conversion in logging | `Select-String -Pattern 'logging\.\w+\(f".*\{[^}]+!r\}'` → 0 matches |
| `f"{x!s}"` explicit str conversion | `Select-String -Pattern 'logging\.\w+\(f".*\{[^}]+!s\}'` → 0 matches |
| `f"{x!a}"` ascii conversion | `Select-String -Pattern 'logging\.\w+\(f".*\{[^}]+!a\}'` → 0 matches |
| Walrus in f-string (`f"{(x:=foo())}"`) | `Select-String -Pattern 'logging\.\w+\(f".*:='` → 0 matches |
| `.format()`-based G003 | `Select-String -Pattern 'logging\.\w+\(.*\.format\('` → 0 matches |
| `%`-pre-format G003 | `Select-String -Pattern 'logging\.\w+\(\"[^"]*%[sdir][^"]*\"\s*%'` → 0 matches |
| `f"hello"` (no substitutions) | `Select-String -Pattern 'logging\.\w+\(f"[^{]+"\)'` → 0 matches (all logging f-strings have at least one substitution) |

If any of these patterns appear in `MistHelper.py` between plan-time and execution-time (e.g., introduced by a parallel PR), the fixture catalog MUST be extended before Phase 1 starts.

## Capture mechanism

```python
# tools/capture_log_baseline.py — runs on `main` (pre-refactor) only
import json, logging, pathlib
from tests.fixtures.issue_429_capture_scenarios import SCENARIOS  # one tuple per row above

results = {}
for site_id, callable_, kwargs in SCENARIOS:  # SCENARIOS list mirrors the table above
    with caplog_capture() as recs:  # context manager around stdlib logging.Handler
        callable_(**kwargs)  # exercise the enclosing function
    rendered = [r.getMessage() for r in recs if r.lineno == site_id]
    results[str(site_id)] = rendered[0] if rendered else None

pathlib.Path("tests/fixtures/issue_429_log_baseline.json").write_text(
    json.dumps(results, indent=2, sort_keys=True, ensure_ascii=True)
)
```

After Phase 4 the parity test loads this JSON and re-runs each `(callable_, kwargs)` under `caplog`, asserting byte equality.

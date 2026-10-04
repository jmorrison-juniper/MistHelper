# Validation Guide: Selective Insight Definitions

**Feature**: [spec.md](spec.md)

**Plan**: [plan.md](plan.md)

This guide describes later implementation validation.
The planned test names below do not exist yet.
Do not run this procedure as part of the current artifact-only step.

## Prerequisites and safety

Use the existing isolated branch `jmorrison-juniper-selective-insight-definitions`.
Keep the base revision `ff3cc1bea8ab58026210a968ff1465f61c9fec78`.
Run commands from this worktree's repository root.
Do not create or switch a branch.

The worktree already has `.venv` with Python 3.13.13 and the current dependency manifests.
Do not bootstrap or install dependencies again unless a later authorization requires it.

```bash
.venv/bin/python --version
git --no-pager branch --show-current
git --no-pager status --short
```

Expect Python `3.13.13` and the reserved branch.
Inspect any existing changes before implementation.
Keep exports and benchmark files under pytest `tmp_path`.
The existing `tests/conftest.py` moves test cwd there.
Do not use repository `data/` for fixtures or output.

Use an offline session whose `mist_get(uri, query)` records each request.
It must support the installed SDK call with `uri="/api/v1/const/insight_metrics"` and `query={}`.
Do not instantiate a live session or read credential files.
Fail any unscripted HTTP request or store operation.
Replace the backend writer before invoking a caller.
Do not contact Mist, ArangoDB, Redis, or a container.

For validation reports, choose an absolute scratch directory outside checkout data.

```bash
validation_root=$(mktemp -d "${TMPDIR:-/tmp}/misthelper-3300-validation.XXXXXX")
```

This directory is for gate reports and coverage metadata.
It is not an application output directory.

## 1. Establish red evidence before source implementation

Add tests only in `tests/unit/export/test_selective_insight_definitions.py` and the reserved analytics test file.
Use a parameterized `test_actual_stale_caller_refresh_is_selective`.
Run the four actual entries in the [caller contract](contracts/definition-refresh.md#caller-compatibility).
Instantiate the real site and device operations with only their external dependencies replaced.
Keep the real client refresh method and organization setup method.
Use the real shared helper, exporter, SDK function discovery, cache code, normalizer, and scope reader.

Prepare all 28 baseline caches with an age greater than 24 hours.
Provide offline successful responses for the complete baseline, including special handling.
Use an actual temporary CSV writer at the `DataExporter.write_with_format_selection` seam.
Return its real Boolean result.
Do not replace the refresh method, cache predicate, normalizer, or selected processing.

```bash
.venv/bin/python -m pytest \
  tests/unit/export/test_selective_insight_definitions.py \
  -k actual_stale_caller_refresh_is_selective \
  -q -s --no-cov --timeout=120
```

Expect four failures before the repair.
The failures must show unrelated definition activity from each actual caller.
Record the caller name, request list, definition writes, and unrelated cache accesses.
A direct exporter-only failure does not satisfy this evidence.

Use guarded file-access spies around real file operations.
Record definition reads, existence checks, timestamps, and writes during the refresh.
Snapshot unrelated bytes and modification times before and after that interval.
Exclude fixture setup and verification reads from refresh access counts.

## 2. Record controlled before measurements

Implement `test_controlled_refresh_benchmark` in the reserved export test file.
Use `ISSUE_3300_BENCHMARK_PHASE` to select measurement expectations.
This is a test-local environment value, not new application configuration.

Use the complete 28-definition SDK baseline.
Give each mock `mist_get` request an actual `time.sleep(0.05)` delay.
Use one gateway model and one country in the fixed responses.
Keep the real special-handling dispatch.
The baseline fixture expects 31 requests and 28 definition writes.
Measure the counts. Do not derive them from the number of definitions.

Use one untimed warm-up per caller and phase.
Create a new equivalent stale cache set for each measured trial.
Control `time.time` only for cache age.
Leave `time.perf_counter_ns` and the actual request delay unchanged.
Include each actual refresh entry's local work inside the measured interval.
Exclude fixture setup, snapshots, unrelated user prompts, and later insight collection.
Include the organization setup entry's existing scope read.

```bash
ISSUE_3300_BENCHMARK_PHASE=before \
.venv/bin/python -m pytest \
  tests/unit/export/test_selective_insight_definitions.py \
  -k controlled_refresh_benchmark \
  -q -s --no-cov --timeout=120
```

Record at least five durations for each of the four callers.
Print the phase, caller, trial number, fixture identity, duration, and counts for every trial.
Retain these records as the before evidence.
Do not copy production implementation into a benchmark or create another checkout.

## 3. Prove selected behavior after implementation

Exercise this matrix through all four caller entries.

| Scenario | Expected definition requests and writes |
| --- | --- |
| All definition caches expired. | One insight request and one successful definition write. |
| Insight cache missing, unrelated caches with mixed ages. | One insight request and one successful definition write. |
| Fresh insight cache with expired unrelated caches. | Zero requests and writes. |
| Insight cache one second younger than 24 hours. | Zero requests and writes, with unchanged bytes and modification time. |
| Insight cache exactly 24 hours old. | One insight request and one successful definition write. |
| Insight cache expired. | One insight request and one successful definition write. |
| Second call after successful refresh. | Zero requests and writes. |
| Timestamp cannot be read. | Existing refresh behavior, with only the selected cache involved. |

Every selected case must show zero unrelated discovery, cache access, and cache change.
Reject unknown, invalid, private, dotted, path-like, empty, and non-string selections without full discovery.
Test selected import failure and modules without a usable SDK function.
Ensure old registrations cannot conceal discovery failure.

Compare CSV bytes and normalized rows against the same baseline insight response.
Check the exact field order and interval formatting in the [data model](data-model.md#3-insight-definition-row).
Check ordered metrics for `site`, `device`, `client`, and `org`.
Include blank names, missing scopes, template names, Unicode descriptions, and a larger ordered payload.
Keep the existing scope exclusions and parsing behavior.

Check each public return contract and existing no-metrics output path.
Count organization empty insight outputs separately from definition writes.
Do not change the existing site, device, or organization caller files.
Verify that the client resolver no longer reads the direct exporter dependency.

## 4. Prove truthful failures and complete full export

Test HTTP `404` and HTTP `503`, both with an error body and with an empty body.
Use offline SDK-shaped responses with a real integer status.
Include a response with `status_code=None` and an SDK proxy-error case.
Include connection failure, timeout, malformed definition data, and discovery failure.
Include primary writer `False`, primary writer exceptions, and empty fallback failures.

Check the first error identity or first available boundary message.
Check the original HTTP status.
Check `updated=0` and exactly one failed count.
Check that a secondary writer failure does not replace the first error.
Check that an existing stale file never causes an availability success message after failure.
Check successful empty responses separately from failed empty-body responses.
Repeat attempts on one exporter instance to prove local result counts.

Check before-and-after logs for cache, fetch, normalization, primary write, and fallback actions.
Check ASCII, safe traceback text, and synthetic secret exclusion.
Do not use actual credentials for these checks.

Run `export_all` through real discovery with the same complete offline baseline.
Compare all 28 registered names and output filenames with the source revision.
Test fresh skips, required-parameter skips, and all three special-handling paths.
Retain existing model and country fallback behavior.
Do not replace `_process_all_endpoints` with a mock to claim full coverage.

The earlier supplied focused baseline passed 321 tests in 1.71 seconds.
Run that scope plus the new reserved test file after implementation:

```bash
.venv/bin/python -m pytest \
  tests/unit/export/test_selective_insight_definitions.py \
  tests/unit/export/test_const_definitions_exporter.py \
  tests/unit/analytics/test_insight_metrics_utils.py \
  tests/unit/serial_cc/test_site_client_insights.py \
  tests/unit/export/test_org_export_utils.py \
  tests/unit/export/test_site_insights_exporter.py \
  tests/unit/export/site_insights/test_site_insight_path.py \
  tests/unit/serial_cc/test_site_client_insight_path.py \
  tests/integration/serial_cc/test_site_client_insights_integration.py \
  -q --no-cov --timeout=120
```

Expect all focused tests to pass.
Do not edit the unreserved baseline test files to accommodate a regression.
Do not expand to the full unrelated test suite without a targeted reason.

Repeat this focused scope with these coverage options instead of `--no-cov`:

```text
--cov=src.operations.exporting.export.const_definitions_exporter
--cov=src.mist.intelligence.analytics.insight_metrics_utils
--cov=src.foundation.support.refactors.serial_cc.site_client_insights
--cov-branch
--cov-report=term-missing
--cov-report=json:<absolute-validation-root>/coverage.json
```

Set `COVERAGE_FILE` to a file under the validation scratch directory.
Retain the configured coverage floor. Do not lower it for a focused run.
Report line and branch coverage for every changed method.
Cover every new failure branch and cache decision.
Identify the focused denominator. Do not present it as repository-wide coverage.

## 5. Record matching after measurements

Use the same caller entries, fixture content, trial numbers, clock, delay, and writer as the before phase.
Run at least five matching trials for each caller.

```bash
ISSUE_3300_BENCHMARK_PHASE=after \
.venv/bin/python -m pytest \
  tests/unit/export/test_selective_insight_definitions.py \
  -k controlled_refresh_benchmark \
  -q -s --no-cov --timeout=120
```

Expect one definition, one request, one successful definition write, and zero unrelated cache accesses per measured after trial.
Pair records by caller, trial number, fixture identity, and cache age.
Do not pair runs with different response or cache fixtures.

Report each of the 40 elapsed durations in seconds.
For each caller, calculate the before median and after median from its measured durations.
Calculate the reduction with `100 * (before_median - after_median) / before_median`.
Require at least 90% for each caller, not only a combined median.
Investigate a missed target without deleting trials or changing the recorded request delay.

Include actual request counts, attempted definition writes, successful definition writes, and separate insight-output writes.
Identify the host, Python version, SDK version, fixture, delay, warm-ups, and elapsed clock.
Label the report **controlled offline measurements**.
State that these numbers do not replace or reproduce the issue's original live 67.3-second report.
Do not obtain a new live measurement.

## 6. Run the configured local gates

Keep thresholds, baselines, suppressions, exclusions, and dependency pins unchanged.
Use the full configured Ruff and Black scopes.
Use the exact current `MYPY_PATHS` from [ci.yml](../../.github/workflows/ci.yml).
The paths below match that workflow at the source revision.

```bash
RUFF_CACHE_DIR="$validation_root/ruff" .venv/bin/python -m ruff check .
BLACK_CACHE_DIR="$validation_root/black" .venv/bin/python -m black --check --diff .
MYPY_CACHE_DIR="$validation_root/mypy" .venv/bin/python -m mypy \
  src/ MistHelper.py wsgi.py \
  scripts/mist_ideas_analyzer_pkg/__init__.py \
  scripts/mist_ideas_distiller_v2_pkg/__init__.py \
  --config-file pyproject.toml
.venv/bin/python -m bandit -c pyproject.toml -r .
```

Before a local commit, include feature-owned untracked tests in the static ratchet scope.
Use the two test directories so a commit-only diff cannot omit the new test file.

```bash
.venv/bin/test-quality-analyzer --gate \
  --roots tests/unit/export tests/unit/analytics \
  --config .github/test-quality-config.toml \
  --baseline .github/test-quality-baseline.json \
  --report "$validation_root/test-quality/report.json" \
  --summary "$validation_root/test-quality/summary.md"
.venv/bin/check-citations src tests
.venv/bin/markdown-link-check --root . specs/3300-selective-insight-definitions/
```

Confirm that the ratchet reports both reserved test files in its measured scope.
Do not use baseline writing, rule disabling, pruning, or exclusions.
After a separately authorized local commit, repeat the configured changed-test ratchet with `--changed-from` and the agreed base.
Retain its CI `--full-gate-path` arguments.
Do not fetch or publish only to obtain local validation evidence.

Grade new documents and changed source with the configured STE linter.
Use `--config .ste-linter.toml --min-score 80`.
Include `--grade-logging-strings --grade-user-facing-strings` for changed source.
Keep [#3300](https://github.com/jmorrison-juniper/MistHelper/issues/3300),
[related #3266](https://github.com/jmorrison-juniper/MistHelper/issues/3266), and the
[scope claim](https://github.com/jmorrison-juniper/MistHelper/issues/3300#issuecomment-5936871419) in the evidence.

The host currently lacks `pwsh`, `powershell`, `hunspell`, `aspell`, and the configured STE dictionary.
Report structural STE results separately from unavailable dictionary checks.
Do not call a skipped check a pass.

## Completion boundary

Record focused tests, changed-method coverage, benchmark results, gate outcomes, and unavailable capabilities.
Verify that only reserved implementation files changed.
Prepare only `changelog.d/issue-3300-selective-insight-definitions.md` during later implementation.
Do not edit `README.md`, `CHANGELOG.md`, menu metadata, schemas, agent instructions, or shared SpecKit state.

This planning step stops before implementation and every commit operation.
Later local commit authorization requires a Conventional Commit and the required Copilot App trailer.
Publication remains blocked until the parent releases queue position 17 after
[#3335](https://github.com/jmorrison-juniper/MistHelper/issues/3335).

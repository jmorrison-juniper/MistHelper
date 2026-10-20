# Quickstart: MistCircuitStats Redis Dashboard Migration

**Status**: Cache-only reads and the fail-closed worker are implemented. Scheduled collection remains disabled until production test T004.

## Preconditions

- Resolve the source license and provenance decision.
- Review the existing #4252 dashboard, which closed #4195. Treat draft #4208 and #4200 as open proposed work.
- Assign one owner to each view and Mist API data set.
- Verify source settings and worker behavior against source code and tests.
- Verify each selected `mistapi` method and schema in [contracts/mist-api.md](contracts/mist-api.md).
- Approve the Redis namespace, ownership, serialization, TTL, and outage policy in [contracts/redis-cache.md](contracts/redis-cache.md).
- Use only mocked Mist responses and fictional records. Do not provide production credentials.

## Validation Scenarios

1. **Site and gateway view**: Load synthetic records for two sites. Select one site and verify that no record from the other site appears.
2. **WAN port and peer detail**: Open one gateway and verify its accepted port and peer views have one owner and one data collection path.
3. **Freshness**: Load records with known collection times. Verify current, stale, partial, and unavailable states.
4. **Mist failure**: Return a 4xx, 5xx, timeout, rate limit, and malformed page. Verify bounded requests and no invalid snapshot publication.
5. **Redis failure**: Fail cache reads and writes. Verify the page makes no live fallback call and reports unavailable state.
6. **Partial refresh**: Fail one collection stage after earlier stages succeed. Verify the prior valid snapshot remains readable and the refresh reports partial or failed state.
7. **Synthetic preview**: Disable external network access. Verify preview data is fictional and cannot satisfy a live route.
8. **Secret redaction**: Use fake token strings. Verify test logs and error messages contain none of them.

## Commands

After product implementation begins, use the smallest affected test selection from the implementation plan, then run the applicable local gates in `.github/copilot-instructions.md`.

The Spec Kit PowerShell prerequisite command could not run because this host has no `pwsh` executable:

```text
pwsh -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks
/bin/bash: pwsh: command not found
```

The original review read its feature path from `.specify/feature.json` and checked it with Python. The plan template was resolved with:

```text
specify preset resolve plan-template
```

The plan lists each expected artifact. This guide does not implement or run product behavior.

## Refresh Procedure: 2026-10-18

Use the existing feature directory explicitly. Do not replace `.specify/feature.json`, which selects another feature. Preserve the established layout.

The refresh applies specify, plan, and tasks to this record only. It updates current ownership evidence and preserves all implementation blockers. The read-only analyze phase reports findings without rewriting the historical `analysis.md`.

The app manages this branch. Do not run the branch-creation hook or create another feature. Optional `speckit.git.commit` hooks remain deferred until one coherent documentation commit. Disabled companion hooks do not execute.

The initial PowerShell command failed with `/bin/bash: pwsh: command not found`. The review recovered this prerequisite with session-local PowerShell 7.6.7. It used the official Microsoft release archive and verified the published SHA-256. It changed no repository dependency or system installation.

With that session-local executable on `PATH`, use the explicit selector:

```bash
export SPECIFY_FEATURE_DIRECTORY="$PWD/specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis"
pwsh -NoProfile -File .specify/scripts/powershell/setup-plan.ps1 -Json
pwsh -NoProfile -File .specify/scripts/powershell/setup-tasks.ps1 -Json
pwsh -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks
```

All three commands passed. Setup preserved the existing plan and returned the established artifact paths. The tracked `.specify/feature.json` hash stayed unchanged.

Run documentation checks from the repository root:

```bash
FEATURE=specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis
source .venv/bin/activate
ste-linter --config .ste-linter.toml --min-score 80 "$FEATURE"/*.md "$FEATURE"/contracts/*.md "$FEATURE"/checklists/*.md
markdown-link-check "$FEATURE"
speckit-task-audit --root "$PWD"
```

The audit CLI scans the repository and has no feature selector. Report unrelated failures without changing their records. Use its scanner and citation validator for a focused check.

## Recorded Refresh Results

| Check | Result |
|---|---|
| STE with explicit Markdown paths | All 11 files passed, with scores from 95 to 97. The initial directory argument read zero files and failed. |
| Markdown links | Eleven tracked files scanned. Zero broken local links. |
| Focused task audit | One record, 24 markers, one checked, 23 open, zero malformed, and zero missing citations. No blocking feature finding. |
| Full `speckit-task-audit --root "$PWD"` | Exit 1. Examined 836 records, 359 task files, and 10204 markers. Thirty-six unrelated records block the audit. |
| Explicit artifact check | Eleven required inputs exist. Sixteen functional requirements and seven success criteria map to 24 sequential tasks. |
| Read-only analyze | No critical planning conflict or uncovered requirement. Product approval gates remain unresolved. The historical report stays unchanged. |
| `git diff --check` | Passed. |

No product test, live Mist request, screenshot recreation, Redis operation, or deployment ran for this documentation refresh.

## Implementation Increment: 2026-10-20

The canonical WAN dashboard now reads its overview and detail data from the existing cache only.
The routes make no Mist SDK requests. A missing detail value returns unavailable.
The page disables Refresh until the background worker exists.
The dashboard shows cached data as stale when its collection time is unknown.
An in-memory snapshot becomes unavailable after 86,400 seconds.

At this cache-only increment, the worker, Redis lease, request queue, progress display, and scheduled refresh remained unimplemented.
Do not set refresh timing values before T004 passes.
Per-port Insights parity remains in issue #4330.

### Validation Results

The requested Python prerequisite script is absent from this checkout:

```text
python3 .specify/scripts/python/check_prerequisites.py --json --require-tasks --include-tasks
python3: can't open file '.specify/scripts/python/check_prerequisites.py': [Errno 2] No such file or directory
```

The requirements checklist has 16 items. All 16 are checked.

The focused tests passed:

```text
.venv/bin/python -m pytest -q tests/integration/web_portal/wan_dashboard/test_services.py tests/integration/web_portal/wan_dashboard/test_routes.py
53 passed in 0.44s
```

The changed Python modules passed type checking:

```text
.venv/bin/python -m mypy src/interfaces/portals/wan_dashboard/services.py src/interfaces/portals/wan_dashboard/routes.py --config-file pyproject.toml
Success: no issues found in 2 source files
```

The JavaScript syntax and whitespace checks passed:

```text
node --check src/interfaces/portals/wan_dashboard/static/dashboard.js
rtk git diff --check
```

The changed Python lint and format checks passed:

```text
.venv/bin/python -m ruff check src/interfaces/portals/wan_dashboard/services.py src/interfaces/portals/wan_dashboard/routes.py tests/integration/web_portal/wan_dashboard/test_services.py tests/integration/web_portal/wan_dashboard/test_routes.py
All checks passed!
.venv/bin/python -m black --check src/interfaces/portals/wan_dashboard/services.py src/interfaces/portals/wan_dashboard/routes.py tests/integration/web_portal/wan_dashboard/test_services.py tests/integration/web_portal/wan_dashboard/test_routes.py
4 files would be left unchanged.
```

The documentation checks passed:

```text
.venv/bin/ste-linter --config .ste-linter.toml --min-score 80 specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/tasks.md specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/quickstart.md changelog.d/issue-4220-cache-only-dashboard.md
tasks.md: 96/100 PASS
quickstart.md: 96/100 PASS
issue-4220-cache-only-dashboard.md: 99/100 PASS
.venv/bin/markdown-link-check specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/quickstart.md specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/tasks.md
Markdown link scan found 0 broken link(s)
```

The focused tasks marked complete are T007, T008, T009, T010, and T011.
T004 and the worker, queue, status, timing, and production-load tasks remain open.
No production credential, `.env` file, Redis service, or Mist API was used.

## Worker Increment

The current increment runs one background worker inside the existing web container. Redis elects one active collector across Gunicorn processes. The Refresh control queues work for that worker. The worker uses only the four approved bulk SDK reads and the shared pagination path.

Collection stays disabled unless `WAN_DASHBOARD_LOAD_TEST_APPROVED` and `WAN_DASHBOARD_REFRESH_ENABLED` are true and both timing values are positive. Do not set these values before T004 passes. The repository example environment file remains owned by draft PR #4208 and is unchanged.

The worker publishes a complete snapshot and its status in one Redis operation. A failed API page, rate limit, Redis write, or lease preserves the last complete snapshot and reports a safe stale error. Each web process uses only its own recent complete snapshot during a Redis outage. No dashboard request calls Mist.

The page displays refresh state, current bulk-read phase, completed page counts, the last complete timestamp, and safe refresh errors. One queued follow-up represents any number of Refresh requests during an active run. A snapshot expires after 86,400 seconds.

Per-port Insights parity remains out of scope and is tracked in issue #4330. No production load test, credential, Redis service, or Mist API request ran for this increment. T004 remains open.

### Focused Validation

```text
.venv/bin/python -m pytest tests/unit/wan_dashboard/test_worker.py tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py tests/integration/web_portal/wan_dashboard/test_routes.py tests/integration/web_portal/wan_dashboard/test_services.py tests/e2e/web_portal/test_wan_dashboard_cache_only.py -q
77 passed in 3.01s
```

The worker and route tests verify disabled configuration, one Redis lease owner, queue coalescing, complete-only publication, stale retention after rate limits and Redis failures, status output, and the CSRF-protected Refresh request. The SDK contract tests verify the four bulk methods, pagination progress, no request without the lease, and no partial snapshot after a failed or repeated page.

```text
.venv/bin/python -m black --check src/interfaces/portals/wan_dashboard/services/worker.py src/interfaces/portals/wan_dashboard/services/__init__.py src/interfaces/portals/wan_dashboard/routes.py tests/unit/wan_dashboard/test_worker.py tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py tests/integration/web_portal/wan_dashboard/test_routes.py tests/e2e/web_portal/test_wan_dashboard_cache_only.py
7 files would be left unchanged.
.venv/bin/python -m ruff check src/interfaces/portals/wan_dashboard/services/worker.py src/interfaces/portals/wan_dashboard/services/__init__.py src/interfaces/portals/wan_dashboard/routes.py tests/unit/wan_dashboard/test_worker.py tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py tests/integration/web_portal/wan_dashboard/test_routes.py tests/e2e/web_portal/test_wan_dashboard_cache_only.py
All checks passed!
node --check src/interfaces/portals/wan_dashboard/static/dashboard.js
Passed.
rtk git diff --check
Passed.
```

## Cache-Only Increment Revalidation (Historical): 2026-10-20

The cache-only routes now build their service from the organization scope and Redis client. A Mist SDK session is not required for a cache read. The Refresh control remains disabled because the worker does not exist.

The focused test command passed:

```text
.venv/bin/python -m pytest -q tests/integration/web_portal/wan_dashboard/test_services.py tests/integration/web_portal/wan_dashboard/test_routes.py
53 passed in 0.30s
```

The changed Python files passed Ruff and Black:

```text
.venv/bin/python -m ruff check src/interfaces/portals/wan_dashboard/services.py src/interfaces/portals/wan_dashboard/routes.py tests/integration/web_portal/wan_dashboard/test_services.py tests/integration/web_portal/wan_dashboard/test_routes.py
All checks passed!
.venv/bin/python -m black --check src/interfaces/portals/wan_dashboard/services.py src/interfaces/portals/wan_dashboard/routes.py tests/integration/web_portal/wan_dashboard/test_services.py tests/integration/web_portal/wan_dashboard/test_routes.py
4 files would be left unchanged.
```

Mypy found no issue in the two changed Python modules. Python compilation, JavaScript syntax, and `git diff --check` passed. The test-quality guide preflight passed one test and read all four required inputs.

The STE check passed all 12 feature and release-note Markdown files. Scores ranged from 94 to 99. The Markdown link check found no broken local links in the three tracked files it scanned. The read-only requirements checklist has 16 checked items and zero unchecked items.

The full task audit examined 839 feature records, 362 task files, and 10,252 task markers. It exited with 36 malformed records outside this feature. The #4220 record has 30 tasks, 7 checked tasks, 23 open tasks, and no malformed task markers.

The current shell cannot rerun the PowerShell prerequisite because `pwsh` is absent. The earlier session-local PowerShell run passed for this feature path and left `.specify/feature.json` unchanged.

No production load test, live Mist request, Redis service, or credential was used during the cache-only increment. T004 remained open at that point.

## Worker Increment Revalidation: 2026-10-20

The Spec Kit prerequisite passed for this feature with an explicit `SPECIFY_FEATURE_DIRECTORY`. The read-only requirements checklist has 16 checked items.

The focused worker, SDK contract, route, service, and browser tests passed:

```text
.venv/bin/python -m pytest tests/unit/wan_dashboard/test_worker.py tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py tests/integration/web_portal/wan_dashboard/test_routes.py tests/integration/web_portal/wan_dashboard/test_services.py tests/e2e/web_portal/test_wan_dashboard_cache_only.py -q
77 passed in 3.01s
```

Black, Ruff, mypy, compilation, Bandit, JavaScript syntax, complexity, and the module-move guard passed. Mypy checked three source files. The module-move guard passed 15 tests.

The test-quality preflight passed one test. It read four required inputs and checked one guide.
The explicit feature STE check passed nine files with scores from 94 to 100. The Markdown link scan found zero broken local links in eight tracked files.

The full task audit exited with 36 malformed task records outside this feature. It examined 840 feature records, 363 task files, and 10,289 task markers. The #4220 record has 30 task markers, 25 checked tasks, 5 open tasks, and no malformed task markers.

The prerequisite command passed with the session-local PowerShell binary and the explicit feature selector. It did not change `.specify/feature.json`.

No production load test, live Mist request, Redis service, or credential was used for this increment. T004 and dependent timing task T027 remain open. Synthetic-data tasks T020, T023, and T024 also remain open.

## Revalidation After Browser Coverage

The focused integration and browser tests passed:

```text
.venv/bin/python -m pytest -q tests/integration/web_portal/wan_dashboard/test_services.py tests/integration/web_portal/wan_dashboard/test_routes.py tests/e2e/web_portal/test_wan_dashboard_cache_only.py
54 passed in 2.48s
```

Ruff, Black, mypy, the complexity gate, Bandit, Python compilation, JavaScript syntax, and `git diff --check` passed. The test-quality guide preflight passed one test and validated all four required inputs. The STE gate passed for 12 changed Markdown files with scores from 94 to 99.

The integration test run checked 1 site lock trail. It held zero lines before and after the run. The browser test used fictional API responses and a local Flask server.

The read-only requirements checklist has 16 checked items and zero unchecked items. Its previous prerequisite check passed and left `.specify/feature.json` unchanged. This worktree lacks `pwsh`, so the PowerShell prerequisite could not run again.

The task audit examined 839 feature records, 362 task files, and 10,252 task markers. It exited with 36 malformed records outside this feature. The #4220 task record has 30 tasks, 8 checked tasks, 22 open tasks, and no malformed markers.

## Pull Request CI Corrections: 2026-10-20

The first CI run passed 32 checks and failed four checks. CodeQL passed. Three export tests used the former service methods. The shared WAN dashboard browser test expected an active Refresh control.

The export test service now supplies cache-only methods. The browser test now verifies that Refresh stays disabled until the worker exists.

```text
.venv/bin/python -m pytest -q tests/integration/web_portal/wan_dashboard/test_exports.py
3 passed in 0.16s
.venv/bin/python -m pytest -q tests/e2e/web_portal/test_portal_smoke.py::TestDashboardPage::test_wan_dashboard_navigation_and_page_shell
1 passed in 2.27s
```

The focused dashboard test set passed again after the rebase with 54 tests. The post-rebase test-quality gate checked three files and reported zero new findings. The repeat CI run remains pending.

## Worker Test-Quality Revalidation: 2026-10-20

The test helper now calls the worker class directly. The analyzer can include its failure cases in source-driving tests.

The focused worker, SDK contract, route, service, and browser tests passed:

```text
./.venv/bin/python -m pytest tests/unit/wan_dashboard/test_worker.py tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py tests/integration/web_portal/wan_dashboard/test_routes.py tests/integration/web_portal/wan_dashboard/test_services.py tests/e2e/web_portal/test_wan_dashboard_cache_only.py -q
87 passed in 2.94s
```

Ruff, Black, mypy, compilation, Bandit, complexity, JavaScript syntax, and whitespace checks passed:

```text
./.venv/bin/python -m ruff check src/interfaces/portals/wan_dashboard/services/worker.py src/interfaces/portals/wan_dashboard/services/__init__.py src/interfaces/portals/wan_dashboard/routes.py tests/unit/wan_dashboard/test_worker.py tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py tests/integration/web_portal/wan_dashboard/test_routes.py tests/integration/web_portal/wan_dashboard/test_services.py tests/e2e/web_portal/test_wan_dashboard_cache_only.py
All checks passed!
./.venv/bin/python -m black --check src/interfaces/portals/wan_dashboard/services/worker.py src/interfaces/portals/wan_dashboard/services/__init__.py src/interfaces/portals/wan_dashboard/routes.py tests/unit/wan_dashboard/test_worker.py tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py tests/integration/web_portal/wan_dashboard/test_routes.py tests/integration/web_portal/wan_dashboard/test_services.py tests/e2e/web_portal/test_wan_dashboard_cache_only.py
8 files would be left unchanged.
./.venv/bin/python -m mypy src/interfaces/portals/wan_dashboard/services/worker.py src/interfaces/portals/wan_dashboard/services/__init__.py src/interfaces/portals/wan_dashboard/routes.py --config-file pyproject.toml
Success: no issues found in 3 source files
./.venv/bin/python -m py_compile src/interfaces/portals/wan_dashboard/services/worker.py src/interfaces/portals/wan_dashboard/services/__init__.py src/interfaces/portals/wan_dashboard/routes.py
./.venv/bin/bandit -c pyproject.toml -r src/interfaces/portals/wan_dashboard -q
./.venv/bin/radon cc src/interfaces/portals/wan_dashboard -j | ./.venv/bin/complexity-gate --max 10
All functions within complexity threshold.
node --check src/interfaces/portals/wan_dashboard/static/dashboard.js
rtk git diff --check
```

The full test-quality gate checked 1,197 files and 684 findings. It reported zero new findings:

```text
./.venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
gate: 0 new findings vs baseline
```

The required preflight read all four test-quality inputs. The post-commit changed-test gate checked four files and reported zero new findings:

```text
./.venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
1 passed in 0.19s
./.venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
gate_scope: 4 files checked, 0 findings checked
gate: 0 new findings vs baseline
```

The latest focused tests use synthetic data. No production load test, live Mist request, Redis service, or credential was used. T004 remains a production-only blocker. T020, T023, and T024 still need synthetic-data work.

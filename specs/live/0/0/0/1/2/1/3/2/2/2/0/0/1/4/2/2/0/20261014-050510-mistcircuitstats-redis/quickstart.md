# Quickstart: MistCircuitStats Redis Dashboard Migration

**Status**: Partial implementation guide. Cache-only reads are implemented. Worker refresh remains blocked on T004.

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

The worker, Redis lease, request queue, progress display, and scheduled refresh remain unimplemented.
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

## Final Revalidation: 2026-10-20

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

No production load test, live Mist request, Redis service, or credential was used. T004 remains open. The worker, lease, refresh queue, progress status, and worker-refresh browser tests remain incomplete.

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

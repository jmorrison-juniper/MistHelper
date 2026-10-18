# Quickstart: MistCircuitStats Redis Dashboard Migration

**Status**: Planning validation guide. Product scenarios require a later approved implementation change.

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

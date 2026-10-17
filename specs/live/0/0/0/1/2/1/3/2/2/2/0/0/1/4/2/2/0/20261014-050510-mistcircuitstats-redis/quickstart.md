# Quickstart: MistCircuitStats Redis Dashboard Migration

**Status**: Planning validation guide. Run only after implementation starts in a later approved change.

## Preconditions

- Resolve the source license and provenance decision.
- Review landed changes for issues #4195 and #4200. Do not assume open PR #4208 is merged.
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

The equivalent feature path was read from `.specify/feature.json` and checked with Python. The plan template was resolved with:

```text
specify preset resolve plan-template
```

The plan lists each expected artifact. This guide does not implement or run product behavior.

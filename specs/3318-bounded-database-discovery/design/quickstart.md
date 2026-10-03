# Validation guide: Bounded database discovery

## Prerequisites

Use the isolated Python 3.13 environment for this worktree.
Install only the current runtime and development manifests if the selected validation command reports missing packages.
Do not load production credentials or start services.

## Controlled behavior

Run the dedicated tests:

```bash
rtk proxy .venv/bin/python -m pytest tests/unit/db_discovery -q
```

The suite must prove the real caller deadline, cache expiry, shared work, finite resources, and recovery.
No required case may skip.
Treat an unhandled helper-thread warning as a failure.

## Related behavior

Run the existing standalone, exporter, and router tests with the dedicated tests.
Use the actual router test paths discovered in the worktree.
Verify explicit standalone mode, partial backends, required credentials, file output, and readiness.

## Local gates

Run configured Ruff and Black across the repository.
Read the exact mypy scope from `.github/workflows/ci.yml`.
Run Bandit with `pyproject.toml`.
Run the unchanged test-quality ratchet with `.github/test-quality-config.toml` and `.github/test-quality-baseline.json`.
Check changed Markdown links and the configured STE score.
Report `dictionary_unavailable` as partial writing coverage if no authorized dictionary exists.

## Evidence

Record the failing baseline test names and their measured durations.
Record the passing controlled durations, cache counts, worker counts, and recovery results.
Record each exact validation command and its result.
Record the local commit SHA and its exact changed files.

## Remote gate

Stop before any push or pull request.
The local source grant names accepted predecessor `67a1ca625ab3526c68a8e54d1580dc1c92d3abc4`.
This grant does not authorize publication.
Wait for a separate explicit publication decision before any push or pull request.
After that decision, repeat required local evidence before a protected merge.
Test the exact actual merged SHA locally after that merge.

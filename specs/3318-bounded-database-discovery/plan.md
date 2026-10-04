# Implementation Plan: Bounded database discovery

**Branch**: `jmorrison-juniper-bounded-database-discovery` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/3318-bounded-database-discovery/spec.md`.

## Summary

Add a shared bounded resolver for central database discovery.
Cache positive and negative results for 30 seconds.
Use two finite daemon workers and admit at most two outstanding queries.
Use resolved numeric addresses for central TCP probes.
Share the released Redis and capture-store DNS preflights.
Share the inherited ArangoDB DNS preflight on the exact accepted predecessor.
Keep configured driver hostnames, URLs, TLS/SNI, and network handshakes unchanged.
Keep all declared-index and data behavior unchanged.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: The standard library and the existing `structlog` package.

**Storage**: A process-local cache with no persistence or schema change.

**Testing**: Existing pytest, coverage, quality analyzer, and configured local gates.

**Target Platform**: Windows, macOS, and Linux.

**Project Type**: The existing MistHelper application and database package.

**Performance Goals**: A one-second wait for each name and no repeated lookup inside the 30-second cache period.

**Constraints**: Two workers, two outstanding queries, 128 cached results, and no live service access.

**Scale/Scope**: Central discovery and the explicitly released DNS preflights.

## Constitution Check

- Use semantic classes for the new cache, worker ownership, and resolver policy.
- Keep new methods within five parameters, five logical blocks, and 25 lines where possible.
- Add no pass-through compatibility helper.
- Remove `_can_resolve` instead of retaining a wrapper.
- Existing `src/foundation/persistence/db/` has six direct Python files. The user explicitly reserves one new resolver module at this existing boundary.
- Existing package hierarchy debt remains outside this one-issue repair. A separate maintenance change can regroup the database package.
- Existing `DatabaseConfig.from_env` exceeds the method length limit. Preserve its configuration and credential semantics without an unrelated class migration.
- Existing `capture/store.py` uses long module functions. Add only the released DNS preflight and preserve its real connection logic.
- Follow the current branch and commit rules instead of the older constitution commit format.
- Run local gates before the local commit. Do not publish or deploy without a separate explicit publication grant.
- Use safe structured diagnostics. Do not log credentials.

## Project Structure

### Documentation (this feature)

```text
specs/3318-bounded-database-discovery/
  spec.md
  plan.md
  tasks.md
  checklists/requirements.md
  design/
    research.md
    data-model.md
    contracts.md
    quickstart.md
```

### Source Code (repository root)

```text
src/foundation/persistence/db/
  __init__.py
  host_resolver.py
  arango_writer.py
  redis_writer.py
src/interfaces/portals/upgrade_portal/capture/store.py
tests/unit/db_discovery/
  conftest.py
  fakes.py
  test_config.py
  test_resolver.py
  test_probe.py
tests/unit/test_standalone.py
tests/unit/test_redis_writer.py
tests/unit/upgrade_portal/test_store.py
documentation/bounded-database-discovery.md
changelog.d/issue-3318-bounded-database-discovery.md
```

**Structure Decision**: Keep the central change at its existing database boundary and place all new tests in one dedicated directory.

## SpecKit workflow

Use the current spec, plan, tasks, and checklist templates in this worktree.
Use the file-only workflow because the app owns the branch and the user prohibits shared SpecKit state changes.
The Git feature hook creates a branch, and the path helper writes `.specify/feature.json`.
Do not execute either operation.
Keep each design artifact inside the reserved feature directory.
Do not run automatic commit hooks or change `.specify/` files.

## Complexity Tracking

| Existing boundary | Reason for the surgical change | Separate maintenance action |
| - | - | - |
| Six files in `src/foundation/persistence/db/` | The user reserves `src/foundation/persistence/db/host_resolver.py` for this issue. | Regroup the existing writers in a separate issue. |
| Long `DatabaseConfig.from_env` method | Credential and standalone behavior must remain unchanged. | Refactor configuration assembly in a separate issue. |

## Design

The resolver uses a fixed port-free `getaddrinfo` query.
Its cache identity includes the actual hostname, family, and socket type.
Protocol and flags keep the fixed socket defaults.
TCP probes apply their configured port to the cached socket address.

Cache access, worker admission, and completion share one short-lived lock.
No lookup or caller wait holds that lock.
A cache miss either shares an active lookup or starts one daemon worker.
A full outstanding-work set reports unavailable capacity immediately.
Its finite handoff queue creates no extra job behind blocked workers.
Capacity refusal creates no negative DNS cache entry.

A caller timeout stores an empty result for the cache period.
The timed-out worker still owns its slot and its active lookup.
Late completion does not replace an existing unexpired cache result.
Completion releases the slot even when the caller already timed out.
Shutdown joins workers only within a finite caller budget.

## Accepted local inheritance

The [local source grant](https://github.com/jmorrison-juniper/MistHelper/issues/3318#issuecomment-5966338605) names the exact accepted predecessor.
Its SHA is `67a1ca625ab3526c68a8e54d1580dc1c92d3abc4`.
Its sole parent is `10fbd06110101e7f75705dbd585796dfeff8a3ab`.
Its tree is `7fb44231359a06e3623ccc403a85c97d4b8551f9`.

Preserve original preparation commit `4477312b0c891a59954c07044efc2f4afabf905f` before the bounded own-branch rebase.
The verified bundle retains its complete original one-commit range over `ff3cc1bea8ab58026210a968ff1465f61c9fec78`.
The rebase uses `rebase.updateRefs=false` and changes no peer branch.
The rebased preparation commit is `67e53ecad8b94bafa50b35796c7d2e68ef05224d`.

Only the inherited `_preflight_dns` method and necessary imports change in `src/foundation/persistence/db/arango_writer.py`.
All other writer methods and the declared-index manager remain unchanged.
Controlled native tests prove the caller deadline, cache expiry, refusal, recovery, finite work, and cleanup.
The separate publication decision remains open.

## Validation

First, run controlled regression tests against the unchanged central implementation.
Record repeated lookup counts and a blocked configuration caller.
Then run focused resolver, configuration, router, exporter, and central probe tests.
Measure real elapsed caller time separately from the injected cache clock.
Check cache expiry, address identity, capacity recovery, and helper cleanup.
Run configured Ruff, Black, exact CI mypy scope, Bandit, test quality, links, and STE checks.
Record missing dictionary coverage and any environment limitation without changing a baseline or exclusion.

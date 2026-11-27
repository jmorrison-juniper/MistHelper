# Implementation Plan: Read-only Mist target discovery for converter proposals

**Branch**: `4642-converter-target-discovery` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification from `/specs/numbered/0/0/1/2/2/0/3/2/4642-converter-target-discovery/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`. The feature root holds five children: `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design`.

## Summary

Add three read-only checks to the converter portal: status, sites, and gateways. Each check calls mistapi through the operator session that the upgrade portal runtime holds. Each check returns one state: verified, unavailable, denied, or failed. The offline preview path does not change. The change contains no write call.

## Technical Context

- **Language/Version**: Python, the repository runtime. This change adds no language version.
- **Primary Dependencies**: `mistapi==0.64.1` (R50) and `flask==3.1.3` (R51). Both pins already exist. This change adds no dependency.
- **Storage**: None. Discovery writes no file and stores no record.
- **Testing**: pytest with the Flask test client, `unittest.mock`, and the existing Playwright smoke module.
- **Target Platform**: Windows 11, macOS, and Linux. The Podman container build runs in CI.
- **Project Type**: A Flask portal feature inside the `src/` domain packages.
- **Performance Goals**: Each list read uses at most 50 pages of 1000 rows. A check makes one `getSelf` read plus its list reads.
- **Constraints**: Read-only SDK calls only. No direct HTTP. Five-item limits. ASCII logs. No secret in logs or responses. No browser storage.
- **Scale/Scope**: One organization per check. The upper bound is 50,000 rows per list (D-7).

## Constitution Check

Each rule has a result and a reason. Evidence IDs point to `design/research.md`.

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule (R30, R31, R41) | Pass | The new package `src/mist/access/targets/` holds four children. `src/mist/access` reaches five children (R73). The converter root stays at five children (R75). No direct child is added to `tests/contract` (R76). |
| II. Class-based architecture (R87) | Pass | Logic lives in `DiscoveryPager`, `MistTargetDiscovery`, `DiscoveryResult`, and `ConverterDiscoveryRoutes`. No wrapper function delegates to a method. |
| III. Safety-first (R33) | Pass | The route validates `org_id` as a UUID before any SDK call (FR-018). The change adds no `input()` call and no destructive operation. |
| IV. Full deployment pipeline (R34) | Pass | `T-LOCAL-GATES`, `T-PR`, `T-REMOTE-CI`, and `T-MERGE` cover steps 1 to 9. Steps 10 to 12 run after merge through the container-build workflow and the deployment owner. |
| V. Observability (R35, R88) | Pass | Log lines use ASCII only. Each SDK read logs before and after the call. Each log line uses a fixed prefix and key=value fields, which is the structured form that this change uses. No new logging dependency is added. |
| VI. Inline comments (R36, R44) | Pass | Each executable line of new code carries an inline comment that gives the cause or the purpose. Task `T-LOCAL-GATES` checks the comments in review. |
| VII. Action logging (R37) | Pass | Each SDK read logs an `info` line before the call and a `debug` line after it. Each exception logs an `error` line with the context. |
| Mist transport (R32) | Pass | Each read uses a mistapi function. The change adds no direct HTTP request and no owned WebSocket transport. |
| Test containers (R38) | Pass | No container starts. The tests run in process. |
| Data directory (R39) | Pass | The change writes no file under `data/` and no file under `test-artifacts/`. |
| Test quality (R42) | Pass | The new route and client tests include HTTP 4xx tests (400, 401, 403, 404) and HTTP 5xx tests (500, 502, 503, 504). Tests assert the returned state, not only the status code. |
| Spec Kit layout (R40, R47) | Pass | The record path uses the managed numeric root and the base-5 route `0/0/1/2/2/0/3/2`. The route equals the base-5 value of 4642 padded to eight digits. |
| Documentation and changelog (R45, R46) | Pass | The change adds the fragment `changelog.d/issue-4642-converter-target-discovery.md`. The README holds no converter section, so the README stays unchanged. |
| Dependency pins (R50, R51) | Pass | The change uses the installed mistapi 0.64.1 (R72). No dependency file changes. |

## Architecture

```text
Operator browser (converter.html, converter.js)
  -> GET /cisco-config-converter/discovery/{status,sites,gateways}
     ConverterDiscoveryRoutes (routes.py)
       -> identity.current_session() -> operator record -> cloud_session
       -> MistTargetDiscovery (src/mist/access/targets/discovery.py)
            -> getSelf / listOrgSites / getOrgInventory (mistapi, explicit keywords)
            -> DiscoveryPager (src/mist/access/targets/paging.py)
                 -> mistapi.get_next for later pages, bounded to 50 pages
            -> DiscoveryResult (src/mist/access/targets/results.py)
       -> JSON response with state, reason, and items (null unless verified)
```

The preview path (`POST /cisco-config-converter/preview`) does not call this chain.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/0/3/2/4642-converter-target-discovery/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      discovery-http.md
      mist-read.md
      ui.md
    checklists/
      requirements.md
      security.md
      ui.md
```

### Source Code (repository root)

```text
src/mist/access/targets/
  __init__.py
  results.py
  paging.py
  discovery.py
src/interfaces/portals/cisco_config_converter/
  routes.py            (modified: ConverterDiscoveryRoutes and three rules)
  presentation/
    converter.html     (modified: discovery section)
    converter.js       (modified: CiscoDiscoveryPage and the event)
tests/integration/web_portal/cisco_config_converter/
  test_discovery.py    (new)
tests/e2e/web_portal/
  test_portal_smoke.py (modified: two browser tests)
changelog.d/
  issue-4642-converter-target-discovery.md (new)
```

**Structure Decision**: Mist access code goes under `src/mist/access/targets/`. Route handlers stay in the converter `routes.py`. Tests go under the converter integration folder (D-1, D-2, D-10).

## File-by-File Change Map

| Path | Action | Purpose |
| - | - | - |
| `src/mist/access/targets/__init__.py` | Add | Package docstring. No re-export. |
| `src/mist/access/targets/results.py` | Add | `DiscoveryState`, `DiscoveryReason`, and the frozen `DiscoveryResult` value (D-4). |
| `src/mist/access/targets/paging.py` | Add | `DiscoveryPager`: bounded page walk, completion proof, and page-status mapping (D-5, D-6, D-7). |
| `src/mist/access/targets/discovery.py` | Add | `MistTargetDiscovery`: status, sites, and gateway checks with explicit SDK arguments (D-9, D-12, D-13). |
| `src/interfaces/portals/cisco_config_converter/routes.py` | Modify | Add `ConverterDiscoveryRoutes` with three GET handlers. Register three rules in `ConverterRoutes.blueprint`. Validate `org_id` as a UUID. |
| `src/interfaces/portals/cisco_config_converter/presentation/converter.html` | Modify | Add the `cisco-discovery` section with stable `data-testid` markers. |
| `src/interfaces/portals/cisco_config_converter/presentation/converter.js` | Modify | Add `CiscoDiscoveryPage`. Render the five page labels. Dispatch `cisco-target-changed` on a target change (D-11). |
| `tests/integration/web_portal/cisco_config_converter/test_discovery.py` | Add | Twenty-two integration tests with mocked SDK responses and synthetic sessions (research and tasks). |
| `tests/e2e/web_portal/test_portal_smoke.py` | Modify | Add two browser tests to `TestCiscoOfflinePreview`. |
| `changelog.d/issue-4642-converter-target-discovery.md` | Add | One fragment with one `Added` bullet that names issue #4642. |

Not changed: `src/interfaces/portals/cisco_config_converter/models.py` (issue #4636), `conversion.py`, `__init__.py`, `web_portal/` shared routes (issue #4648), `MistHelper.py`, `requirements.txt`, and `README.md` (R46 shows no converter section).

## Dependencies

- Pinned packages: `mistapi==0.64.1` (R50) and `flask==3.1.3` (R51).
- Issue #4634 supplies the contract evidence for each read. Issue #4641 supplies the review reset that listens to `cisco-target-changed`. Both must close before implementation starts.
- Issue #4648 supplies the shared operator session. Until then the page reports `no_session`.
- Issues #4636 and #4641 also edit `routes.py`. The merge order is #4636, then #4641, then #4642.

## Risks and Mitigations

- Warning: A write call inside a discovery check can change production Mist settings. The mitigation is the test in T002 that asserts the call list. The test fails for any write function.
- Caution: A rate-limited check can wait about 35 seconds. The mitigation is a running state label in the page. The retry belongs to the SDK (D-8).
- Risk: Mist omits `X-Page-Total`. Every full list fails safely. The mitigation is the proof rule (D-6) and research item U1.
- Risk: The SDK returns no status for a generic exception. The mitigation is the `exception` reason and a log line with the exception type (D-5, U5).
- Risk: `routes.py` reaches the five-name limit. The mitigation is the merge order and the nested-package guard in T015.
- Risk: The operator session is missing in the isolated host. The page reports `no_session`, and the preview continues to work (FR-008).
- Risk: A future change adds a child to `tests/integration/web_portal/cisco_config_converter/`. The mitigation is a count check in the review of each converter test change.

## Rollback Steps

1. Revert the pull request commit on `main`. No data migration exists.
2. Confirm that `src/mist/access/targets/` is absent from `main`.
3. Confirm that `GET /cisco-config-converter/discovery/status` returns 404 after the revert.
4. Re-run `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py`. The offline tests must pass.

## Complexity Tracking

No constitution rule is violated by this plan. The parity map paths differ from this plan in three places. Each difference follows a constitution rule.

| Parity map item | Plan item | Why the plan differs |
| - | - | - |
| T019 path `tests/contract/cisco_config_converter/test_discovery.py` (R01) | `tests/integration/web_portal/cisco_config_converter/test_discovery.py` | `tests/contract` holds 17 children (R76), and the constitution forbids a new child there (R31). |
| T020 path `src/interfaces/portals/cisco_config_converter/routes.py` (R02) | Handlers in `routes.py`. Client in `src/mist/access/targets/` | `ConverterRoutes` holds five members (R15). The converter root holds five children (R75). A client in `routes.py` would also mix Mist calls into the interface layer. |
| Parity discovery contract ID C19 to C21 (R03 to R05) | Same contract IDs in `design/contracts/` | Each contract ID keeps its meaning. The state set follows the issue (D-4). |

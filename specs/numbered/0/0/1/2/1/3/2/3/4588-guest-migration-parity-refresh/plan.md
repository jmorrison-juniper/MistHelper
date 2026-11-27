# Implementation Plan: Refresh guest migration parity planning

**Branch**: Not assigned in this run | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: `specs/numbered/0/0/1/2/1/3/2/3/4588-guest-migration-parity-refresh/spec.md`.

## Summary

Plan the full source-to-target migration with visual and functional parity. Keep the current product behavior unchanged. Keep the offline projection. Add approved workflows to the existing Flask portal later. Use exact scope, the shared mistapi session, the existing data services, typed confirmations, and truthful outcomes. The [parity inventory](design/contracts/parity.md) is the acceptance boundary.

## Technical Context

- **Language and version**: Python 3.15 or newer (T17 L20). The source image uses Python 3.13 (S05 L4). That image is not the target.
- **Primary dependencies**: Flask, flask-wtf, Gunicorn, and mistapi 0.64.1 (T10 L129). The portal already uses these packages.
- **Storage**: Mist remains the authority for authorization records. The approved coordination records use the SQLite store `data/mist_data.db` (D-12). ArangoDB and Redis run as existing containers (T09). No new database is planned.
- **Testing**: pytest for unit, contract, and integration tests. Playwright browser tests under `tests/e2e`. Use synthetic responses and isolated stores. Do not construct a live Mist session in a test.
- **Target platform**: Windows 11, macOS, Linux, and rootless Podman (T17 L8 to L16).
- **Project type**: One feature inside the existing portal. No second application.
- **Performance goals**: Bound CSV work by D-11. Use the repository page size of 1000 (T17 L350). No latency target exists in the source, so none is set here.
- **Constraints**: The five-child rule (T18 L38). PR 4208 owns the shared portal files (D-4). Direct HTTP to a Mist REST endpoint is not allowed (T18 L274 to L279).
- **Scale and scope**: One page, three dialogs, 73 inventory rows, 35 requirements, and 40 implementation tasks.

## Constitution Check

The check uses principles I to VII in the constitution (T18). "Pass" means the planning step complies. "Gate" means the implementation step must pass a stated condition first.

| Principle | Result | Reason | Future condition |
| --- | --- | --- | --- |
| I. Five-item rule | Pass | This record adds one route folder with five feature children and five design children. The route parent holds one child after this record, because the legacy folder is retired. | T007 checks the parent counts before any file is created. The legacy folder is retired and backed up, as in D-1. |
| II. Class-based architecture | Pass | This planning step writes no code. The proposed package uses named classes. | T013, T018, T024, and T030 enforce class design and no wrapper functions. |
| III. Safety-first | Pass for planning. Gate for implementation. | No live call or write is enabled. Typed words and CSRF protection are planned. | D-6, D-12, and D-14 must pass before any write. |
| IV. Full deployment pipeline | Partial by design | This change edits Markdown only. Steps 10 to 12 do not run, because `container-build.yml` runs only for product file changes (T17 L473). | The orchestrator runs steps 1 to 9. Merge waits for authorization. |
| V. Observability and logging | Pass for planning | This step writes no code. ASCII-only output is planned. | T030 and T033 check the logging and output rules. |
| VI. Inline comments | Pass for planning | This step writes no code. | Future code needs an inline comment on each executable line. |
| VII. Action logging | Pass for planning | This step writes no code. | Future code needs a log before and after each action. |
| Technology constraints | Pass | mistapi is the only REST interface (T18 L274 to L279). Podman is the test container runtime (T17 L354). | T008 checks the dependency and runtime rules. |
| Operational store | Gate | D-12 selects the SQLite store (T17 L309 to L353). The constitution names a declared store (T18 L315 to L316). No document names it (research U07). | T005 and T030 verify the store before any write. |
| Export boundary | Not applicable | No export operation is proposed. | A future export must use `DataExporter.write_with_format_selection`. |
| Database keys | Gate | The natural key is `(organization_id, site_id, wlan_id, normalized_mac)`. The guest endpoint entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` was not verified in this run. | T008 verifies the strategy entry before a new operation. |
| Spec Kit layout | Pass | The route is `0/0/1/2/1/3/2/3`. The base-5 radix function computes it (T19 L4). New records use `specs/numbered` (T17 L159 to L160). | T-LOCAL-GATES checks the route and the child counts. |

Existing folder debt is grandfathered. This record adds no child to an overfull parent. The planning step records the debt and names a separate remediation action in the [analysis](analysis.md).

## Architecture

- A feature package under `src/interfaces/portals/guest_authorizations/` holds the domain, service, and web layers.
- The portal adds one blueprint registration (T03 L182 to L207) and one navigation entry (T04 L51 to L78).
- Every Mist call goes through one API client class that uses mistapi.
- Durable intent and outcome records go to the SQLite store (D-12).
- The offline projection moves into the package. The package and the module cannot share one name, so the move replaces the module file in one change.

## Project Structure

### Documentation (this record)

```text
4588-guest-migration-parity-refresh/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      api.md
      parity.md
      portal.md
      e2e.md
      source-files.md
    checklists/
      requirements.md
      migration.md
```

### Source code (future, proposed)

```text
src/interfaces/portals/guest_authorizations/
  __init__.py
  domain/
    __init__.py
    read_model.py
    scope.py
    validation.py
  services/
    __init__.py
    api_client.py
    mutations.py
    imports.py
    audit.py
  web/
    __init__.py
    routes/
    templates/
    static/
```

Each directory above holds five children or fewer. The feature root holds four children. The `services` package holds five children.

Planned test roots are `tests/unit/web_portal/guest_authorizations/`, `tests/contract/web_portal/guest_authorizations/`, `tests/integration/web_portal/guest_authorizations/`, and `tests/e2e/web_portal/guest_authorizations/`. T007 checks each parent before it creates a directory.

**Structure decision**: Extend the existing `WebPortalApp` through one blueprint. Do not create a second Flask application, a second port, a second database, or a second Compose group.

## Dependencies

- Python 3.15 (T17 L20).
- mistapi 0.64.1 (T10 L129). The source pin is 0.64.0 (S08 L2). The target keeps 0.64.1.
- flask-wtf for CSRF protection (T05 L297 to L303).
- No new dependency is planned. A new dependency needs a separate decision and a dependency audit under the quality gates.

## Risks and mitigations

| ID | Risk | Mitigation |
| --- | --- | --- |
| RK-1 | Shared-file conflicts with PR 4208. | Wait for PR 4208 to close or for a handover (D-4, T007). |
| RK-2 | A write changes access by mistake. | Typed words, CSRF, exact scope, and zero-write negative tests (D-14, TEST-020, TEST-021). |
| RK-3 | SQLite locks under concurrent workers. | One writer lock and a worker test before any write (D-12, T030). |
| RK-4 | An unknown outcome is repeated. | No automatic repeat. Reconcile through an exact-scope read (D-8, T024). |
| RK-5 | Visual drift from the source. | Paired screenshots and approved differences (D-13, T034). |
| RK-6 | A licensing reading is wrong. | Human decision before implementation (D-5). |
| RK-7 | The guide's five-year claim is trusted. | The schema bound is enforced and the docs are updated (D-7, T036). |
| RK-8 | A CSV file is unbounded. | D-11 limits and boundary tests (TEST-018). |
| RK-9 | The source pin goes stale. | T001 repeats the pin check before implementation. |

Warning: a rollback after a cloud write does not reverse the write. Reconcile the audit record first. Then decide the next action with the operator.

## Complexity Tracking

| Existing constraint | Narrow treatment | Separate remediation |
| --- | --- | --- |
| Overfull process folders | Add only this routed record. | Tracked as a separate proposal outside this planning PR. |
| Shared portal registration | One owned registration change after handover. | T007 measures block limits before the change. |
| Existing projection module | Replace it with a nested package and update callers. | T009 applies the move gates and keeps each public contract. |
| Shared test roots | Validate concrete bounded destinations first. | T007 selects a compliant destination. |

No complexity threshold, hierarchy baseline, or analyzer allow-list changes in this plan.

## Rollback steps

1. For this planning PR, revert the merge commit on main if review rejects the record. No product code changes, so no runtime rollback is needed.
2. For a future implementation, remove the single blueprint registration in `web_portal/app.py`. Keep the offline projection and its tests.
3. Keep the SQLite intent records for audit. Do not delete them during rollback.

## Approval and stopping condition

- This run stops after the planning artifacts, the STATUS file, and the summary file.
- The next steps are T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE, in that order.
- No implementation task starts in this run.
- The planning PR does not close #4231 or #4278. It does not merge automatically.

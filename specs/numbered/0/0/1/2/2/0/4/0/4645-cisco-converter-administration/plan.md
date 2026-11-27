# Implementation Plan: Gated Converter Administration and Unassignment

**Branch**: `feat/4645-cisco-converter-administration` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `/specs/numbered/0/0/1/2/2/0/4/0/4645-cisco-converter-administration/spec.md`.

Keep `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Add gated administrative controls to the converter portal. The controls stay hidden by default. A run unassigns device profiles and deletes gateway templates, networks, or services. Each run uses explicit reviewed objects, two confirmations, a one-use approval, a verified backup, and a before-state check. Each object records one outcome. This record authorizes no live write.

## Technical Context

**Language/Version**: Python 3.15 or later. The live record names 3.15.2 as the current worktree interpreter.

**Primary Dependencies**: Existing Flask blueprint and CSRFProtect. The pinned `mistapi>=0.64.0,<0.65` package (installed version 0.64.1). The state package from issue 4636.

**Storage**: Operation records and approvals in the private store from issue 4636, under `data/cisco_config_converter/state/`. Backup manifests from issue 4643 in the same private area.

**Testing**: pytest. `unittest.mock` replaces the SDK functions. The Flask test client renders the page. No live credential is used.

**Target Platform**: The existing MistHelper portal on Windows, macOS, Linux, and Podman.

**Project Type**: Existing portal feature inside the converter package.

**Performance Goals**: Each run handles at most 25 objects. Each object uses one write call and one read-back call.

**Constraints**: No live write. Zero writes for each refusal. Fail closed when the store, the identity, or the backup evidence is missing. No automatic write retry.

**Scale/Scope**: One organization, one family, and at most 25 objects for each run.

## Constitution Check

| Rule | Result | Reason |
| --- | --- | --- |
| Principle I, five-item rule for levels | Fail until the `engine/` move lands, then pass | The converter root holds five children (RC-07). Issue 4636 fills the root with `state/`. The move of `conversion.py` into `engine/` frees the slot. |
| Principle I, no direct child in a noncompliant parent | Pass | Tests use `tests/integration/web_portal/cisco_config_converter/administration/`. The plan adds no child to `tests/contract/` (RC-13), `tests/e2e/` (RC-14), or `documentation/`. |
| Principle I, managed route for numeric records | Pass | The record uses `specs/numbered/0/0/1/2/2/0/4/0`. The route ancestor `specs/numbered/0/0/1/2/2` holds three children now and four after this record (RC-47). |
| Principle II, class-based architecture | Pass | Behavior sits in `AdministrationRoutes`, `AdministrationPermission`, `AdministrationScope`, `AdministrationExecutor`, and `ObjectOutcome`. No standalone wrapper function is planned. |
| Principle III, safety first | Pass | The design uses a typed `CONFIRM` checked on the server, refusal before any write, read-back, and no automatic retry. |
| Principle IV, deployment pipeline | Pass for this record. Pending for implementation | The final tasks run the local gates, open the pull request, watch CI, and wait for human review. |
| Principle V, ASCII logging | Pass | Task T010 requires ASCII text in each log line. |
| Principle VI, inline comments | Pass | Tasks T010, T011, and T012 require an inline comment on each changed Python and JavaScript line. |
| Principle VII, action logging | Pass | Each administrative action writes an `info` line before and a `debug` line after (FR-020). |
| Technology, mistapi only | Pass | Each Mist call names one mistapi function (FR-026). No WebSocket transport is planned. |
| Technology, data directory | Pass | Records and manifests stay under `data/`. `.gitignore` ignores `data/` (RC-52). |
| Technology, no compatibility shim | Pass | The move of `conversion.py` updates each call site in the same change. No alias remains. |
| Operational store | Pass with dependency | The store is `PrivateStateStore` from issue 4636. It refuses writes without `PORTAL_SECRET_KEY`. Retention deletes no record (issue 4636 D-9). |
| Export boundary | Pass | The change exports no collected API data. The scope JSON is not a collected-data export. |
| Test containers | Pass | No container starts. Tests run on the host with `python -m pytest`. |
| Container build and Zscaler | Pass | This record builds and pushes no container. The main build runs in CI after merge. |
| Security findings | Pass | The plan adds no suppression comment. |
| Documentation and release notes | Pass | One changelog fragment (FR-028) and the comments in `deploy/.env.example` (FR-027). README stays unchanged because no menu row changes (decision D-9). |
| Required labels | Pass | Labels `feature` and `web-portal` exist (issue 4645). Label `needs-human-review` stays. |
| Auto-merge for destructive changes | Pass | The pull request gets no `auto-merge` label (decision D-14, RC-48). |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/0/4/0/4645-cisco-converter-administration/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      portal-administration.md
      mist-administration.md
    checklists/
      requirements.md
      security.md
```

### Source and test changes

| Path | Action | Requirements | Task |
| --- | --- | --- | --- |
| `src/interfaces/portals/cisco_config_converter/engine/__init__.py` | Add. Module docstring only. | FR-025 | T002 |
| `src/interfaces/portals/cisco_config_converter/engine/conversion.py` | Add by moving `src/interfaces/portals/cisco_config_converter/conversion.py`. | FR-025 | T002 |
| `src/interfaces/portals/cisco_config_converter/conversion.py` | Delete after the move. No shim remains. | FR-025 | T002 |
| `src/interfaces/portals/cisco_config_converter/engine/administration/__init__.py` | Add. Module docstring only. | FR-025 | T010 |
| `src/interfaces/portals/cisco_config_converter/engine/administration/permission.py` | Add `AdministrationPermission`. | FR-001, FR-002, FR-003 | T010 |
| `src/interfaces/portals/cisco_config_converter/engine/administration/scope.py` | Add `AdministrationScope`. | FR-005, FR-006, FR-007, FR-008 | T010 |
| `src/interfaces/portals/cisco_config_converter/engine/administration/executor.py` | Add `AdministrationExecutor`. | FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-019 | T010 |
| `src/interfaces/portals/cisco_config_converter/engine/administration/outcome.py` | Add `ObjectOutcome` and `AdministrationOutcome`. | FR-016, FR-018, FR-020 | T010 |
| `src/interfaces/portals/cisco_config_converter/routes.py` | Modify. Register four rules in `ConverterRoutes.blueprint`. Add class `AdministrationRoutes`. Change the conversion import to `engine`. | FR-001, FR-004, FR-009, FR-023 | T011 |
| `src/interfaces/portals/cisco_config_converter/presentation/administration.html` | Add. Page controls with `data-testid` values. | FR-021, FR-022 | T012 |
| `src/interfaces/portals/cisco_config_converter/presentation/administration.js` | Add. Review state, run control, and safe text output. | FR-021, FR-022 | T012 |
| `deploy/.env.example` | Modify. Add two variables with safe defaults and comments. | FR-001, FR-002, FR-027 | T009 |
| `changelog.d/issue-4645-converter-administration.md` | Add. One heading and one bullet. | FR-028 | T013 |
| `tests/integration/web_portal/cisco_config_converter/administration/__init__.py` | Add. Module docstring only. | FR-024 | T004 |
| `tests/integration/web_portal/cisco_config_converter/administration/test_permission.py` | Add five tests. | FR-001, FR-002, FR-003, FR-004, FR-024 | T005 |
| `tests/integration/web_portal/cisco_config_converter/administration/test_scope.py` | Add seven tests. | FR-005, FR-006, FR-007, FR-008, FR-012, FR-024 | T006 |
| `tests/integration/web_portal/cisco_config_converter/administration/test_execute.py` | Add eleven tests. | FR-009 to FR-020, FR-024 | T007 |
| `tests/integration/web_portal/cisco_config_converter/administration/test_administration_page.py` | Add three tests. | FR-021, FR-022 | T008 |
| Each test module that imports `cisco_config_converter.conversion` | Modify the import path to `engine`. Find each import with grep before T002. | FR-025 | T002 |

The `specs/numbered/0/0/1/2/2/0/4/0/4645-cisco-converter-administration/` folder is the record itself. It is added with the pull request (T-PR).

## Architecture

Request path for one run:

1. The operator opens `GET /cisco-config-converter/admin`. The page is hidden unless the mode is enabled.
2. The operator sends `POST /cisco-config-converter/admin/scope` with explicit IDs. The server reads the current objects, the references, and the backup manifests. It returns a scope digest and a review status.
3. The operator sends `POST /cisco-config-converter/admin/approve` with the scope digest. This is the first confirmation. The server issues one approval.
4. The operator sends `POST /cisco-config-converter/admin/execute` with the approval ID and the typed `CONFIRM`. This is the second confirmation.
5. `AdministrationPermission` checks the mode, the family, and the identity. `AdministrationScope` checks the digest, the references, and the backups. `AdministrationExecutor` performs each read, write, and read-back in the fixed order. `PrivateStateStore` persists the operation record before the first write and after each outcome.
6. The response lists each object outcome. The page shows the outcome list with text only.

## Sequencing

1. Confirm the prerequisites in T001.
2. Reserve the converter root slot in T002. Issue 4636 performs the `engine/` move in its T004 change, or this issue performs it before T010.
3. Write the tests first (T004 to T008). Each refusal test must fail before T010 exists.
4. Implement the configuration, the package, the routes, the page, and the fragment (T009 to T013).
5. Run the final tasks.

## Approval Gates

| Gate | Required evidence | Work blocked |
| --- | --- | --- |
| G1 Legal | Issue 4635 decision | Reuse of external material. This change uses independent authorship only. |
| G2 API | Issue 4634 evidence for each write, read, reference, and read-back in `design/contracts/mist-administration.md` | Each Mist write family |
| G3 Integration owner | Issue 4648 handover and the release of shared files by PR 4208 | Shared portal registration |
| G4 Cloud owner | Decisions D-2 and D-3 | Enabling each family |
| G5 Operator | Scope confirmation, typed `CONFIRM`, verified backup, and identity from decision D-1 | Each run |

## Dependencies

- Issue 4633 (closed). Its coordinator decision authorizes offline work. It bars any live delete or unassign.
- Issue 4634 (open). It owns the Mist contract evidence.
- Issue 4635 (open). It owns the licensing and authorship decision.
- Issue 4636 (open). Its draft defines the `state/` package and the `engine/` move. The package is not on `main` (RC-08).
- Issue 4643 (open). It owns the backup catalog.
- PR 4208 (open). It owns `web_portal/app.py` and `web_portal/templates/base.html` (RC-57).
- PR 4596 (merged). It holds the 33-task map (RC-58).
- mistapi 0.64.1 in `.venv` (RC-59 to RC-70).

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| A live deletion removes an object that a template uses | Live site outage | Refuse each live reference. Require a verified backup. Keep each family disabled until decision D-2. |
| A write returns an unknown result | Hidden or repeated change | Read back the object. Mark the object `indeterminate` and stop the run. Retry nothing automatically (FR-016, FR-017). |
| Site-template unassignment changes inheritance | Settings drift on live sites | Keep the path refused until decision D-3 and issue 4634 close (FR-015). |
| Device profile unassignment removes settings from devices | Device settings change | Send only reviewed MAC addresses. Record each before-state digest. Reassignment restores the link. |
| The converter root has no slot after issue 4636 | Structure rule violation | Move `conversion.py` into `engine/` (decision D-6, task T002). |
| No operator identity provider exists | No run can start | Production refuses every identity until decision D-1 closes (FR-003). |
| The store is unavailable | Missing audit record | Refuse the run before the first write with 503 (FR-012). |
| A page is stale when the operator runs it | Wrong object changes | Clear the review on each change. Check the scope digest on the server (FR-021). |
| The deployed portal does not expose the routes | The feature stays unreachable | This is expected until issue 4648 completes the handover (decision D-16). |
| The live inventory lacks reference reads | Reference checks cannot pass | The scope review blocks each unverified reference (FR-007, UV-01). Issue 4634 adds the reads. |

## Rollback Steps

1. Set `CISCO_CONVERTER_ADMIN_MODE` to `disabled` or remove the variable. Every administrative route then returns 404.
2. Revert the squash commit of the pull request. The converter returns to its preview, review, and export behavior.
3. Do not restore a deleted Mist object with code.

Warning: A deleted Mist object has no automatic restore. Use the verified backup and a new approval from issue 4646.

4. Remove `data/cisco_config_converter/state/operations/` only after the owner approves a purge. Issue 4636 decision D-9 keeps every record.

## Complexity Tracking

| Item | Status | Reason | Action |
| --- | --- | --- | --- |
| `tests/contract/` | Grandfathered, 17 children (RC-13) | Adding a folder breaks the rule | Use the converter integration folder (decision D-5) |
| `tests/e2e/` | Five children, at the limit (RC-14) | Adding a folder breaks the rule | Use the converter integration folder for the page test (decision D-5) |
| `documentation/` | Grandfathered, many children | Adding a file breaks the rule | Use the comments in `deploy/.env.example` and the changelog fragment |
| Converter root | Five children (RC-07) | No slot for `administration/` | Move `conversion.py` into `engine/` (decision D-6) |
| `ConverterRoutes` | Five members (RC-05), at the limit | New methods break the rule | Add class `AdministrationRoutes` with four members |

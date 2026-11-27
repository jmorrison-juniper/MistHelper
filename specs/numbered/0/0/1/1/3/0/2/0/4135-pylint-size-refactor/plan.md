# Implementation Plan: Function and module size for Pylint limits

**Branch**: `chore/4135-pylint-size-refactor` | **Date**: 2026-11-26 | **Spec**: `spec.md` in this record

**Input**: Numeric specification at `specs/numbered/0/0/1/1/3/0/2/0/4135-pylint-size-refactor/`. The route uses eight base-5 segments from `.specify/scripts/powershell/spec-route.ps1`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, and checklists under `design/`. Contracts are omitted, as described below.

## Summary

Five files hold the seven listed Pylint message families. This plan splits three oversized modules and two long functions. It also removes one duplicated method body. The plan moves code into new packages under compliant parents. No Mist API call, menu key, portal row, or export output changes. The change keeps the public names that tests import from their current module paths.

## Technical Context

**Language/Version**: Python 3.15, as required by `pyproject.toml` and the copilot instructions.

**Primary Dependencies**: No new package. The pinned `mistapi>=0.64.0,<0.65` and the pinned development tools stay as pinned.

**Storage**: No schema change. The endpoint dictionary keeps its keys and values.

**Testing**: pytest with the guard tests under `tests/guardrails/`, the Juniper workflow tests, the portal tests, and the safe sweep `python MistHelper.py --test`.

**Target Platform**: Windows 11, macOS, and Linux. The new code uses `pathlib` and never joins path strings by hand.

**Project Type**: Command-line tool, with a Gunicorn web portal under `web_portal/`.

**Performance Goals**: No measured regression. The import of `MistHelper` must not start a network call or a new thread.

**Constraints**: LF line count of 1,000 or fewer for each named module. Five children or fewer for each directory that the change creates or grows. No new dependency.

**Scale/Scope**: Five named files, 612 endpoint entries, 309 menu entries, 308 registered operations, and about 805 test references to `MistHelper` names.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The check uses the constitution version 1.9.0 and the repository copilot instructions.

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule, hierarchy | Pass | Each new or grown directory holds five children or fewer. Research table lists the counts. |
| I. Five-item rule, grandfathered debt | Recorded | `web_portal/services/`, `juniper_rma/workflows/`, and `refactors/` already exceed five children. No child is added to them. Complexity Tracking lists each. |
| I. Five-item rule, count definition | Recorded | The nested-package guard excludes `__init__.py`, and the change follows it. A stricter count that includes `__init__.py` reaches six children in `src/foundation/support/`. Task T052 records the remediation. |
| I. Function limits | Recorded | `_build_registry` is fixed. Moved functions that exceed 25 lines keep their length. Task T052 records the remediation. |
| II. Class-based architecture | Pass for new code | New code uses classes. Moved module-level functions keep their form. Task T052 records the remediation. |
| III. Safety first | Pass | No input handling, destructive confirmation, or `safe_input` call changes. |
| IV. Full deployment pipeline | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run in order. |
| V. Observability and logging | Pass | New log text uses ASCII and `%s` formatting. No secret enters a log. |
| VI. Inline comments | Pass | Each changed or added line carries an inline comment. Task acceptance checks this. |
| VII. Action logging | Pass | Moved blocks keep their log lines. `JuniperRowWriter` logs before and after each write. |
| Technology: mistapi | Pass | No REST call or WebSocket transport changes. |
| Technology: UV and requirements | Pass | No dependency changes. Pip-audit is not applicable. |
| Technology: Podman and test containers | Not applicable | No gate starts a container. |
| Technology: file paths | Pass | New code uses `pathlib`. |
| Technology: output backends | Pass | `JuniperRowWriter` calls `write_with_format_selection`. |
| Technology: database keys | Pass | The endpoint keys stay the same. The hash test checks them. |
| Development workflow: menus | Pass | No menu is added or removed. |
| Development workflow: destructive menus | Pass | The destructive set does not change. |
| Documentation | Pass | Three documents change for counts and paths. The changelog fragment is added. |
| Audience standard | Pass | No user-facing text changes. |
| Spec Kit escalation | Pass | The change touches more than three files and splits modules, so the spec is required. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/3/0/2/0/4135-pylint-size-refactor/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    checklists/
      requirements.md
```

The `contracts/` folder is omitted. No interface contract applies. The menu surface, the portal surface, the CSV and XML output, and the operator text stay the same.

### Source Code (repository root)

```text
src/
  foundation/
    persistence/db/endpoint_strategies/        (new package)
      entries_first/block_1.py to block_3.py   (new)
      entries_second/block_4.py to block_6.py  (new)
    support/
      portal_operations/                       (new package)
        parameters.py, registry.py, run_log_handler.py, context_answers.py
        groups/site.py, client.py, cli_endpoint.py, juniper.py
    support/refactors/endpoint_primary_key_strategies.py  (modified, composition only)
  interfaces/
    cli/                                       (new package)
      bootstrap/   factories.py, dependency_installer.py, import_initializer.py, log_rotation.py
      context/     login.py, strategies.py, wiring.py
      menu/        entries_a.py to entries_d.py
      runtime/     systematic.py, launchers.py, cli_flags.py, dispatch.py
  operations/exporting/juniper_rma/
    workflows/juniper_menu_support.py, asset_lookup.py, correlation.py  (modified)
web_portal/services/operation.py               (modified)
MistHelper.py                                  (modified, host block only)
```

## File-by-File Change Map

| Path | Action | Purpose | Task |
| - | - | - | - |
| `src/foundation/support/portal_operations/__init__.py` | Add | Package docstring | T010 |
| `src/foundation/support/portal_operations/parameters.py` | Add | Class `PortalParameters` with the parameter builders from `operation.py` lines 174 to 327 | T010 |
| `src/foundation/support/portal_operations/groups/__init__.py` | Add | Package docstring | T011 |
| `src/foundation/support/portal_operations/groups/site.py` | Add | Class `SiteMenuGroups` for lines 410 to 603 | T011 |
| `src/foundation/support/portal_operations/groups/client.py` | Add | Class `ClientMenuGroups` for lines 604 to 749 | T011 |
| `src/foundation/support/portal_operations/groups/cli_endpoint.py` | Add | Class `CliEndpointMenuGroups` for lines 750 to 910 | T011 |
| `src/foundation/support/portal_operations/groups/juniper.py` | Add | Class `JuniperRmaMenuGroups` for lines 328 to 405 | T011 |
| `src/foundation/support/portal_operations/registry.py` | Add | Class `PortalRegistryBuilder` with `build()` | T012 |
| `src/foundation/support/portal_operations/run_log_handler.py` | Add | Class `_RunLogHandler` and helper `_is_plumbing_record` | T013 |
| `src/foundation/support/portal_operations/context_answers.py` | Add | Class `ContextAnswers` for the helpers at lines 1120 to 1243 | T014 |
| `web_portal/services/operation.py` | Modify | Keep `OperationExecutor`, constants, `_read_positive_int_env`, and the `PARAMETER_REGISTRY` assignment | T015 |
| `src/operations/exporting/juniper_rma/workflows/juniper_menu_support.py` | Modify | Add class `JuniperRowWriter` with the shared write body and update the module docstring to name the wider scope | T020 |
| `src/operations/exporting/juniper_rma/workflows/asset_lookup.py` | Modify | Remove `_write`, call `JuniperRowWriter` | T021 |
| `src/operations/exporting/juniper_rma/workflows/correlation.py` | Modify | Remove `_write`, call `JuniperRowWriter` | T021 |
| `src/foundation/persistence/db/endpoint_strategies/__init__.py` | Add | Package docstring | T030 |
| `src/foundation/persistence/db/endpoint_strategies/entries_first/__init__.py` | Add | Package docstring | T030 |
| `src/foundation/persistence/db/endpoint_strategies/entries_first/block_1.py` | Add | Entries 1 to 102, dictionary `ENDPOINT_BLOCK_1` | T030 |
| `src/foundation/persistence/db/endpoint_strategies/entries_first/block_2.py` | Add | Entries 103 to 204, dictionary `ENDPOINT_BLOCK_2` | T030 |
| `src/foundation/persistence/db/endpoint_strategies/entries_first/block_3.py` | Add | Entries 205 to 306, dictionary `ENDPOINT_BLOCK_3` | T030 |
| `src/foundation/persistence/db/endpoint_strategies/entries_second/__init__.py` | Add | Package docstring | T030 |
| `src/foundation/persistence/db/endpoint_strategies/entries_second/block_4.py` | Add | Entries 307 to 408, dictionary `ENDPOINT_BLOCK_4` | T030 |
| `src/foundation/persistence/db/endpoint_strategies/entries_second/block_5.py` | Add | Entries 409 to 510, dictionary `ENDPOINT_BLOCK_5` | T030 |
| `src/foundation/persistence/db/endpoint_strategies/entries_second/block_6.py` | Add | Entries 511 to 612, dictionary `ENDPOINT_BLOCK_6` | T030 |
| `src/foundation/support/refactors/endpoint_primary_key_strategies.py` | Modify | Keep the classes at lines 36 to 140 and compose the public dictionary from the six blocks | T031 |
| `src/interfaces/cli/__init__.py` | Add | Package docstring | T040 |
| `src/interfaces/cli/bootstrap/__init__.py` | Add | Package docstring | T040 |
| `src/interfaces/cli/bootstrap/log_rotation.py` | Add | Class `LogRotationSettings` from `MistHelper.py` lines 109 to 185 | T041 |
| `src/interfaces/cli/bootstrap/factories.py` | Add | Three nested factory classes from lines 1270 to 1345 | T042 |
| `src/interfaces/cli/bootstrap/dependency_installer.py` | Add | Installer class from the split map in `research.md` | T042 |
| `src/interfaces/cli/bootstrap/import_initializer.py` | Add | Initializer class from the split map in `research.md` | T042 |
| `src/interfaces/cli/context/__init__.py` | Add | Package docstring | T043 |
| `src/interfaces/cli/context/login.py` | Add | Login helpers from lines 2596 to 2808 | T043 |
| `src/interfaces/cli/context/strategies.py` | Add | Session strategy helpers from lines 2809 to 3377 | T043 |
| `src/interfaces/cli/context/wiring.py` | Add | Wiring builders and `_build_policy_api` from lines 3378 to 3651 | T043 |
| `src/interfaces/cli/menu/__init__.py` | Add | Composes `MENU_ACTIONS` from the four blocks | T044 |
| `src/interfaces/cli/menu/entries_a.py` | Add | Menu entries 1 to 78 in file order | T044 |
| `src/interfaces/cli/menu/entries_b.py` | Add | Menu entries 79 to 155 in file order | T044 |
| `src/interfaces/cli/menu/entries_c.py` | Add | Menu entries 156 to 232 in file order | T044 |
| `src/interfaces/cli/menu/entries_d.py` | Add | Menu entries 233 to 309 in file order | T044 |
| `src/interfaces/cli/runtime/__init__.py` | Add | Package docstring | T045 |
| `src/interfaces/cli/runtime/systematic.py` | Add | Systematic test helpers from lines 6502 to 6855 | T045 |
| `src/interfaces/cli/runtime/launchers.py` | Add | Launchers from lines 6856 to 7330 | T045 |
| `src/interfaces/cli/runtime/cli_flags.py` | Add | Flags and runtime setup from lines 7331 to 7827 | T045 |
| `src/interfaces/cli/runtime/dispatch.py` | Add | Dispatch helpers from lines 7828 to 8268 | T045 |
| `MistHelper.py` | Modify | Keep the host block, `__all__` for names still defined, bootstrap, globals, context module, and entry guard. Bind `menu_actions` to `MENU_ACTIONS` | T046 |
| `src/foundation/runtime/config/source_dependency_resolver.py` | Modify | Update `_module_symbols` for moved names read by name | T047 |
| `tests/unit/web_portal/test_portal_required_controls.py` | Modify | Add the registry hash test and its constant | T001, T012 |
| `tests/unit/web_portal/test_portal_log_routing.py` | Modify | Add the classification test | T013 |
| `tests/unit/juniper_rma/workflows/test_lookups.py` | Modify | Add the writer skip test | T022 |
| `tests/unit/juniper_rma/workflows/test_correlation.py` | Modify | Add the writer forwarding test | T022 |
| `tests/guardrails/test_endpoint_catalog.py` | Modify | Add the endpoint hash test and move the menu source-text reads to the menu package | T032, T048 |
| `tests/guardrails/test_operation_registry_menu_coverage.py` | Modify | Add the menu key order test and its constant | T001, T044 |
| `tests/guardrails/test_move_module_guidance.py` | Modify | Add the import-cycle test | T049 |
| Test files with `MistHelper` patch targets | Modify | Move each patch target to its new owner. The inventory search lists the files | T048 |
| `documentation/architecture.md` | Modify | Update the `MistHelper.py` row at line 196 and the description at line 164 | T050 |
| `documentation/CONTRIBUTING-MistHelper.md` | Modify | Update the symbol map at line 31 | T050 |
| `.github/copilot-instructions.md` | Modify | Update the key file row at line 580 | T050 |
| `changelog.d/issue-4135-pylint-size-refactor.md` | Add | One release-note fragment | T051 |

No file is deleted. Moved code leaves its old module, but the module stays.

## Architecture

- `MistHelper.py` keeps the host contract. It binds itself to the source resolver at line 712, keeps the bootstrap block, and keeps the module globals. The entry guard calls the runtime dispatch module.
- The menu package holds the 309 entries in four blocks. `MENU_ACTIONS` is the ordered union of the blocks.
- The CLI bootstrap package holds the import and installation classes. The initializer calls the installer. The installer never calls the initializer.
- The portal operation package holds the registry, the parameter builders, the run-log handler, and the context helpers. `web_portal/services/operation.py` imports them and keeps `OperationExecutor`.
- The endpoint package holds the dictionary in six blocks. `endpoint_primary_key_strategies.py` composes the blocks and keeps the classes.
- The Juniper row writer sits in `juniper_menu_support.py` and serves both Juniper workflows.

## Complexity Tracking

The table separates grandfathered debt from new design, as the constitution requires.

| Item | Type | Why needed | Simpler alternative rejected because |
| - | - | - | - |
| `web_portal/services/` holds nine modules | Grandfathered debt, touched | `operation.py` loses code. No module is added to this folder. | Adding a module there adds a child to a noncompliant parent. |
| `juniper_rma/workflows/` holds seven modules | Grandfathered debt, baseline entry | Two modules lose a duplicated method. No module is added. | Adding the writer there increases the count and fails the ratchet. |
| `src/foundation/support/refactors/` holds 33 children | Grandfathered debt, baseline entry | The endpoint module shrinks. No child is added. | Moving the endpoint module breaks the path that tests import. |
| `_build_registry` spans 507 lines | Existing violation, fixed | The split removes the R0914 and R0915 findings | Suppression comments are forbidden. |
| Moved module-level functions in `MistHelper.py` | Existing violation, moved | Each moved function keeps its form. Task T052 records the class-based remediation. | Rewriting every function into a class in this change expands the scope. |
| Functions longer than 25 lines in moved blocks | Existing violation, moved | The line rule is not a Pylint message. Task T052 records the remediation. | Splitting every function now expands the scope. |
| Eight-return method `_is_user_facing` | Existing violation, fixed | The helper reduces returns to six. | No simpler fix exists that keeps the branch order. |
| Ten new packages under compliant parents | New design | Each package holds five children or fewer | A single flat package under `src/interfaces/` breaks the child limit. |
| Static group builder classes | New design | Each class holds one group of menu rows | A module-level function per group breaks the class-based rule. |

## Dependencies

- No new package, no version change, and no lock file change.
- The new modules depend only on modules that exist on `main`.
- The import order of `MistHelper` changes only in the bootstrap classes. Task T049 checks the order by an import smoke test.

## Risks and Mitigations

- Risk: A moved name is still imported by a caller. Mitigation: Task T048 searches each caller. The full test shards import every module.
- Risk: An import cycle appears between `MistHelper` and a new module. Mitigation: Task T049 checks each new module for an import of `MistHelper`.
- Risk: The bootstrap split changes import-time side effects. Mitigation: Task T042 keeps the one-way call rule. Task T049 runs the import smoke test.
- Risk: A patch target points to the old owner. Mitigation: Task T048 moves each target. The full test run detects a missed target.
- Risk: The registry or the endpoint dictionary changes order. Mitigation: The hash tests from Task T001 check the content and the order.
- Risk: The symbol gate reports the moved names as lost. Mitigation: The pull request lists each removed name. The record makes no claim that the gate passed.
- Risk: R0913 or R0917 appears in a function that the reading did not find. Mitigation: Task T002 runs Pylint before the code change.
- Risk: A pull request for `MistHelper.py` overlaps another open pull request. Mitigation: Check open pull requests before each push.

Caution: a merge conflict in `MistHelper.py` costs review time. Check the open pull requests before the push.

Warning: a push after the squash merge creates an orphan branch that nobody merges. File a new issue and branch again from `main` instead.

## Rollback

1. Create a revert commit on a new branch. Do not force-push `main`.
2. The revert restores the moved names to `MistHelper.py`, the duplicated `_write` bodies, and the single endpoint dictionary.
3. Remove the new packages in the same revert.
4. Run `python -m pytest tests/guardrails/test_nested_package_structure.py` and the menu guards on the reverted tree.
5. Open a pull request titled `revert(lint): undo function and module size refactor`, with `Closes #4135` in the body.

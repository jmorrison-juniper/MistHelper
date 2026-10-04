# Implementation Plan: Source Domain Packages

**Branch**: `chore/3574-src-domain-packages`

**Date**: 2026-10-03

**Spec**: `specs/3574-src-domain-packages/spec.md`

## Summary

This plan moves all direct source packages into four domain packages.
It updates all repository imports in one atomic migration.
It preserves public symbols without forwarding modules or import aliases.

## Technical Context

**Language**: Python 3.13 or newer.

**Tools**: Git, Ruff, Black, mypy, pytest, `symbol-diff`, and `pytest-chunks`.

**Source scope**: `src`, Python call sites, package configuration, tests, and source documentation.

## Constitution Check

- The final `src` level has four domain packages and `__init__.py`.
- Each new domain and group level has five children or fewer.
- The change adds no wrapper or compatibility shim.
- The change preserves safety controls and runtime behavior.
- The change adds one unique release-note fragment.

## Existing Structural Debt

The migration moves 38 existing nested directories that exceed five direct children.
It does not add a child to these directories or change their internal behavior.
Issue #3824 records the required incremental remediation action for this debt.
Each #3824 slice will reduce the measured violation count and preserve public symbols.

The measured debt inventory is:

- `src/operations/execution/capture`: 12 children.
- `src/operations/execution/firmware`: 11 children.
- `src/operations/execution/ssh`: 9 children.
- `src/operations/execution/ssid_consolidation`: 7 children.
- `src/operations/exporting/export`: 47 children.
- `src/mist/access/api`: 6 children.
- `src/mist/access/audit`: 10 children.
- `src/mist/intelligence/analytics`: 6 children.
- `src/mist/intelligence/reports`: 18 children.
- `src/mist/intelligence/troubleshooting`: 7 children.
- `src/mist/networking/network`: 7 children.
- `src/mist/realtime/websocket`: 7 children.
- `src/mist/resources/device`: 14 children.
- `src/mist/resources/gateway`: 16 children.
- `src/mist/resources/inventory`: 7 children.
- `src/mist/resources/site/address_audit`: 13 children.
- `src/mist/realtime/websocket_streams/catalog`: 6 children.
- `src/mist/intelligence/juniper_docs/classify`: 6 children.
- `src/mist/intelligence/troubleshooting/rf_diagnostics`: 7 children.
- `src/interfaces/monitoring/metrics_gateway`: 8 children.
- `src/interfaces/portals/upgrade_portal`: 11 children.
- `src/interfaces/visualization/maps`: 19 children.
- `src/interfaces/visualization/ui`: 8 children.
- `src/interfaces/visualization/maps/launcher`: 8 children.
- `src/interfaces/portals/upgrade_portal/app`: 9 children.
- `src/interfaces/portals/upgrade_portal/capture`: 9 children.
- `src/interfaces/portals/upgrade_portal/compare`: 7 children.
- `src/interfaces/portals/upgrade_portal/runtime`: 9 children.
- `src/interfaces/portals/upgrade_portal/upgrade`: 21 children.
- `src/interfaces/portals/upgrade_portal/app/routes`: 12 children.
- `src/interfaces/portals/upgrade_portal/upgrade/org_cascade`: 6 children.
- `src/interfaces/portals/upgrade_portal/app/assets/templates`: 9 children.
- `src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade`: 7 children.
- `src/foundation/models/dataclasses`: 15 children.
- `src/foundation/persistence/db`: 6 children.
- `src/foundation/support/refactors`: 33 children.
- `src/foundation/support/utils`: 17 children.
- `src/foundation/support/refactors/serial_cc`: 9 children.

## Technical Approach

1. Create each domain and group package with an `__init__.py` file.
2. Move each current package or module through `git mv`.
3. Replace each old canonical import path with its new path.
4. Repair relative imports that cross a moved package boundary.
5. Update package-data and static-analysis configuration paths.
6. Add structural tests for package counts and old import paths.
7. Add representative public-symbol import tests.
8. Run focused behavior tests for each moved domain.
9. Update the contributor map and architecture diagrams.
10. Add the issue #3574 release-note fragment.

## Public Import Rule

The migration preserves each public symbol in its moved module.
The migration does not preserve the old internal module path.
All repository call sites use the new canonical module path.
No forwarding package, alias module, or runtime path mutation is permitted.

## Verification Plan

Run these focused checks before the required sweep gates:

```powershell
rtk python -m pytest tests\guardrails\test_src_domain_structure.py -q
rtk python -m pytest tests\unit\test_src_public_imports.py -q
rtk python -m pytest tests\unit\firmware tests\unit\export tests\unit\websocket_streams -q
rtk python -m pytest tests\contract\upgrade_portal tests\unit\upgrade_portal -q
```

Run these required sweep gates for each changed Python file set:

```powershell
rtk python -m compileall -q src tests MistHelper.py wsgi.py wsgi_capture.py
rtk python -m ruff check .
rtk python -m black --check .
rtk python -m mypy src MistHelper.py wsgi.py scripts\mist_ideas_analyzer_pkg\__init__.py scripts\mist_ideas_distiller_v2_pkg\__init__.py --config-file pyproject.toml
rtk symbol-diff --base origin/main <each-moved-module>
```

Run the bounded test shards after the focused checks:

```powershell
rtk pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
rtk pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

## Risks

- Active pull requests can conflict with moved source paths.
- Dynamic import strings can escape a static import replacement.
- Package data can fail if a configuration path still names the old package.
- A broad replacement can change prose that does not describe an import.

## Risk Controls

- Use an explicit old-to-new path map.
- Scan the full repository for every old path after the migration.
- Run structural, import, and behavior tests before the full gates.
- Rebase once after the active conflicting changes merge.

## Verification Evidence

- The focused non-portal behavior run passed 4,446 tests and skipped 4 tests.
- The upgrade portal behavior run passed 6,292 tests.
- The moved-module guard compared 808 Python modules and found no lost symbol.
- The package-data guard checks each tracked non-Python file from `origin/main`.
- Ruff, Black, mypy, Python compilation, and stable-path `symbol-diff` passed.
- The unit sweep reached 46 percent before its 900-second chunk timeout.
- The contract, guardrail, and integration sweep reached its 900-second timeout.
- The Windows `socket.AF_UNIX` failure reproduces on unchanged `origin/main`.
- The local test-quality analyzer path mismatch reproduces on unchanged `origin/main`.

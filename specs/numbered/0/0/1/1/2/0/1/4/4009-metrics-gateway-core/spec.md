# Feature Specification: Metrics Gateway Core Modules

**Feature Branch**: `chore/4009-metrics-gateway-core`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4009, "Refactor: isolate metrics gateway core modules". Move four data-plane modules into one core package, so the gateway root holds five structural children. The issue is a bounded child of #3824.

**Routed record**: `specs/numbered/0/0/1/1/2/0/1/4/4009-metrics-gateway-core/`

## Clarifications

### Session 2026-11-26

- Q: Should the candidate commit `033553b3` be replayed? → A: No. Its test paths moved, and it omits the hook catalog, the nested baseline, and the nested totals. The change starts from current `main`. The candidate stays unchanged on its archive branch.
- Q: What does the issue term "public symbol map" name? → A: The `MODULE_PATHS` mapping in `tests/guardrails/test_src_public_symbol_preservation.py`. No other map names the moved modules.
- Q: Which hook rows change? → A: The eight active rows in `hook-catalog.csv` that name the four moved modules. The historical inventory and the hook summary do not change.
- Q: Does the MIB change need regeneration? → A: Yes. The generator writes the header path. `python MistHelper.py --mib-check` confirms the stored file.
- Q: Which branch and fragment names apply? → A: The branch is `chore/4009-metrics-gateway-core`, because AGENTS.md allows the `chore` type. The fragment is `issue-4009-metrics-gateway-core.md`, because no pull request exists yet.
- Q: When may the change leave the local repository? → A: After the coordinator assigns the serial slot and PR #4208 releases the symbol guard file.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep the gateway root within the structure limit (Priority: P1)

A maintainer needs the gateway root to hold five structural children. The four moved modules go into `core/`. The four root modules stay at the root.

**Why this priority**: The gateway root holds eight children, which exceeds the limit of five. Its baseline entry is open debt under issue #3824.

**Independent Test**: Run `python -m pytest tests/guardrails/test_src_domain_structure.py -q`. Then run `python -m pytest tests/guardrails/test_nested_package_structure.py -q`. Both commands pass.

**Acceptance Scenarios**:

1. **Given** the moved layout, **When** the structure guard runs, **Then** the gateway root names `core`, `prometheus.py`, `service.py`, `snmp.py`, and `web.py`.
2. **Given** the moved layout, **When** the nested guard runs, **Then** the gateway root has no baseline entry. The totals are 32 violations and 233 total excess.

---

### User Story 2 - Keep runtime behavior through canonical imports (Priority: P1)

An operator runs the metrics gateway and the MIB generator. Both use the moved modules and produce the same output as before.

**Why this priority**: The move must keep metrics, SNMP output, and the MIB unchanged.

**Independent Test**: Run the targeted tests in `design/quickstart.md` section 4. Then run `python MistHelper.py --mib-check`. Each command passes.

**Acceptance Scenarios**:

1. **Given** a caller imports `metrics_gateway.core.catalog`, **When** the import runs, **Then** the import succeeds, and each root export keeps its name.
2. **Given** a caller imports `metrics_gateway.catalog`, **When** the import runs, **Then** Python raises `ModuleNotFoundError`, because no alias exists.
3. **Given** the stored MIB, **When** `--mib-check` runs, **Then** the command exits with status 0.

---

### User Story 3 - Keep active references current (Priority: P2)

A maintainer reads the MIB guide, the menu API pages, the hook catalog, and the Observium script. Each link names the canonical core path.

**Why this priority**: A stale path sends a maintainer to a file that no longer exists.

**Independent Test**: Run `python -m scripts.menu_api_map --check`. Then run `python -m pytest tests/guardrails/test_performance_hook_catalog.py -q`. Both commands pass.

**Acceptance Scenarios**:

1. **Given** the regenerated pages, **When** the drift check runs, **Then** the command exits with status 0, and each collector link names `core/collector.py`.
2. **Given** the eight updated hook rows, **When** the hook guard runs, **Then** each row resolves to a current symbol.

---

### User Story 4 - Preserve historical evidence (Priority: P3)

An auditor reads older records. The historical specifications and the historical inventory keep their old paths and values.

**Why this priority**: The inventory is evidence from source revision `7c4e57f3db93afda4c93ef0aec1e73c35fb7774e`. Regenerating it breaks that evidence.

**Independent Test**: Review the changed file list. No file under `specs/1924-failure-evidence/`, `specs/2159-openapi-mib-generator/`, or `artifacts/python-inventory.csv` appears in the list.

**Acceptance Scenarios**:

1. **Given** the completed change, **When** a reviewer lists the changed files, **Then** no historical record appears in the list.

### Edge Cases

- A new module that no `git add` stages stays invisible to `git ls-files`. The hook guard then reports unresolved rows. Stage the new files before the hook guard runs.
- A MIB regeneration changes lines outside the header. Stop, review the diff, and do not commit the diff.
- A caplog assertion keeps an old logger name. The test fails. Update the assertion to the core name.
- PR #4208 changes the symbol guard file. A parallel edit causes a conflict. Wait until PR #4208 releases the file.
- A shallow checkout lacks revision `7c4e57f3db93afda4c93ef0aec1e73c35fb7774e`. The inventory test fails. Fetch the revision as section 1 of `specs/2448-misthelper-performance-monitoring/quickstart.md` shows.
- An external script imports `metrics_gateway.catalog`. The import fails. The repository search found no such caller.
- `__pycache__` folders appear under the gateway root. The structure guard ignores them. Do not count them as children.
- Warning: deleting the archive branch removes the remote copy of commit `033553b3`. Keep the archive branch until a replacement merges and a preservation proof exists.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The change MUST move `cache.py`, `catalog.py`, `collector.py`, and `samples.py` into `src/interfaces/monitoring/metrics_gateway/core/` with `git mv`.
- **FR-002**: The change MUST keep `prometheus.py`, `service.py`, `snmp.py`, and `web.py` at the gateway root.
- **FR-003**: The change MUST add `core/__init__.py` that holds a documentation string and no re-export.
- **FR-004**: The change MUST NOT add a wrapper, an alias, or a fallback import at an old module path.
- **FR-005**: The change MUST rewrite each active import of the four moved modules to its core path.
- **FR-006**: The change MUST keep every export name in `metrics_gateway/__init__.py` and its `__all__` list.
- **FR-007**: The change MUST update the five logger assertions in four unit test modules to the core logger names.
- **FR-008**: The change MUST update the MIB generator modules and the MIB header, and `python MistHelper.py --mib-check` MUST exit with status 0.
- **FR-009**: The change MUST update each active documentation link and the Observium script comment to the core path.
- **FR-010**: The change MUST regenerate the two interactive-safe menu pages with repository tools.
- **FR-011**: The change MUST update the eight active hook rows that name the moved modules, and keep each row ID and symbol.
- **FR-012**: The change MUST NOT edit historical specifications, `python-inventory.csv`, or `hook-catalog-summary.json`.
- **FR-013**: The change MUST add four old-to-new entries to `MODULE_PATHS` in `tests/guardrails/test_src_public_symbol_preservation.py`.
- **FR-014**: The change MUST add a guard test that asserts the exact child sets of the gateway root and the core package.
- **FR-015**: The change MUST remove the gateway root entry from `tests/guardrails/nested_package_baseline.json`, and set the expected totals to 32 violations and 233 total excess.
- **FR-016**: The change MUST NOT edit `MistHelper.py`.
- **FR-017**: The change MUST keep every module-level name and every runtime behavior of the moved modules.
- **FR-018**: The change MUST add `changelog.d/issue-4009-metrics-gateway-core.md` with one `### Changed` heading.
- **FR-019**: The change MUST add the routed record at `specs/numbered/0/0/1/1/2/0/1/4/4009-metrics-gateway-core/`.
- **FR-020**: The change MUST stay local until the coordinator assigns the serial slot and PR #4208 releases the symbol guard file.
- **FR-021**: The change MUST NOT replay, push, delete, or edit commit `033553b3` or its archive branch.
- **FR-022**: The change MUST add an inline comment to each changed line of Python code.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- The collector imports the pinned `mistapi` stats module at `src/interfaces/monitoring/metrics_gateway/collector.py` line 157. The change keeps that import unchanged.
- The SDK functions are `getOrgStats`, `listOrgDevicesStats`, and `listOrgSiteStats`. They appear in `.venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py` at lines 17, 397, and 1308.
- The change adds no direct HTTP request and no owned WebSocket transport.
- Contract-test evidence for SDK insufficiency: Not applicable, because the change owns no transport.

### Key Entities *(include if feature involves data)*

- **Module path**: A source path that names one Python module. The change maps four old module paths to four core paths.
- **Logger name**: The `__name__` value of a module. The change moves four logger names into the core namespace.
- **Hook row**: One row of the hook catalog. The change updates eight hook rows.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The gateway root holds exactly five structural children.
- **SC-002**: The core package holds exactly four structural children.
- **SC-003**: The targeted tests named in `design/quickstart.md` section 4 pass.
- **SC-004**: The symbol guard reports no lost module-level name for the moved modules.
- **SC-005**: `python -m scripts.menu_api_map --check` exits with status 0 after regeneration.
- **SC-006**: The old-path search in `design/quickstart.md` section 4 prints no line.
- **SC-007**: `python MistHelper.py --mib-check` exits with status 0.
- **SC-008**: The nested guard reports 32 violations and 233 total excess.

## Assumptions

- Implementation starts from `origin/main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` or a later commit.
- The package path stays `src/interfaces/monitoring/metrics_gateway/`, as on main.
- No caller outside this repository imports the four old module paths.
- Python 3.15.2 runs all gates, because `pyproject.toml` line 23 requires 3.15 or newer.
- The installed SDK stays at `mistapi` 0.64.1, which is inside the pin `>=0.64.0,<0.65`.

## Out of Scope

- Changes to historical specifications, the historical inventory, and the candidate commit.
- Changes to `MistHelper.py`, menu behavior, endpoint calls, MIB object identifiers, and metric values.
- The package tree in `documentation/architecture.md` at line 227, which does not show the current layout. It needs a separate issue.
- Other nested packages in the baseline. They belong to issue #3824.
- Container changes beyond the comment in the Observium script.

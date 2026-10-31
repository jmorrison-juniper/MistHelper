# Feature Specification: Site Analytics Package

**Feature Branch**: `jmorrison-juniper-refactor-group-site-analytics-modules`

**Created**: 2026-10-06

**Status**: Draft

**Input**: MistHelper issue #3992 groups three site analytics modules in one bounded package.

**Authority**: GitHub `main` at `0b04cda81c8ef75096f3bedae0885038c775d665`

## User Scenarios & Testing

### User Story 1 - Find Site Analytics in One Package (Priority: P1)

A maintainer can find all site-focused analytics modules in one package with a clear site purpose.

**Why this priority**: The analytics package has six direct modules. This count exceeds the
five-child structural limit.

**Independent Test**: Inspect the analytics hierarchy. Confirm that its root has four structural
children and its `site` package has three.

**Acceptance Scenarios**:

1. **Given** the approved baseline, **When** the change adds the `site` package, **Then** it moves
   the three approved modules into that package.
2. **Given** the completed move, **When** a maintainer inspects the analytics root, **Then** it
   contains three direct modules and the `site` package.
3. **Given** the new `site` package, **When** a maintainer inspects it, **Then** it contains the
   three moved modules and a package initializer.
4. **Given** the old module locations, **When** the move is complete, **Then** no wrapper,
   forwarding module, alias module, or fallback remains there.

---

### User Story 2 - Preserve Analytics Behavior and Symbols (Priority: P2)

An operator receives the same site analytics behavior after the package move.

**Why this priority**: A path-only refactor must not change analytics results, prompts, exports,
logging, Mist calls, or operator safety.

**Independent Test**: Compare every module-level symbol against the authority commit. Run the
existing configurator, inventory health, zone, and delegation tests.

**Acceptance Scenarios**:

1. **Given** `site_analytics_configurator.py` at the authority commit, **When** its destination is
   compared, **Then** all 16 module-level symbols remain.
2. **Given** `site_inventory_health_analyzer.py` at the authority commit, **When** its destination
   is compared, **Then** all 14 module-level symbols remain.
3. **Given** `zone_analyzer.py` at the authority commit, **When** its destination is compared,
   **Then** all 92 module-level symbols remain.
4. **Given** imports from `src.mist.intelligence.analytics`, **When** callers request the four
   approved exports, **Then** each export remains available with the same object.
5. **Given** existing site analytics workflows, **When** their focused tests run, **Then** their
   behavior and safety contracts remain unchanged.

---

### User Story 3 - Use Only Canonical Site Paths (Priority: P3)

A maintainer can use one canonical module path for each site analytics module.

**Why this priority**: An old import, mock target, script path, or documentation link can hide an
incomplete move.

**Independent Test**: Search active runtime, test, script, mock, generated documentation, and
active documentation paths. Confirm that each uses the new package.

**Acceptance Scenarios**:

1. **Given** active Python imports, **When** the move is complete, **Then** each import uses the
   matching `src.mist.intelligence.analytics.site` module.
2. **Given** active test patch targets and logger names, **When** the tests run, **Then** each
   target resolves through the new module path.
3. **Given** generated and active documentation links, **When** the references are checked, **Then**
   each link points to the new `site` package path.
4. **Given** historical specifications and the released changelog, **When** active paths change,
   **Then** those immutable records remain unchanged.

---

### User Story 4 - Detect Analytics Structure Drift (Priority: P4)

A maintainer receives a clear failure when a checked analytics package gains a sixth structural
child.

**Why this priority**: A focused guard keeps the repaired hierarchy compliant without expanding
this issue into unrelated package debt.

**Independent Test**: Run the guard against the repository, a controlled six-child package, and
a missing package root.

**Acceptance Scenarios**:

1. **Given** the completed analytics hierarchy, **When** the guard runs, **Then** it reports two
   checked package directories and their measured counts.
2. **Given** one controlled package with six children, **When** the guard runs, **Then** it fails
   with one checked directory, the violating path, and a count of six.
3. **Given** a missing required analytics root, **When** the guard runs, **Then** it fails with the
   missing path and a clear inspection cause.
4. **Given** a hierarchy outside the analytics package, **When** the guard runs, **Then** it does
   not inspect or report that hierarchy.

### Edge Cases

- `__init__.py` and generated cache directories do not count as structural children.
- Delayed imports inside functions must use the new canonical path.
- Test patch targets and module logger strings must move with normal imports.
- The analytics root must keep its four exports without exporting `ZoneConfigurationAnalyzer`.
- The new `site/__init__.py` must not become a compatibility wrapper.
- A symbol name that starts with an underscore remains part of the preservation contract.
- Imported module-level names remain part of the symbol comparison.
- Historical specifications can contain old paths because they record earlier repository states.
- `CHANGELOG.md` can contain old paths because it is an immutable released record.
- The path scan must fail if it cannot read its required tracked-file input.
- The structure guard must fail before it returns a partial result for a missing root.

## Requirements

### Functional Requirements

- **FR-001**: The change MUST add
  `src/mist/intelligence/analytics/site/__init__.py`.
- **FR-002**: The new package initializer MUST contain only a package docstring.
- **FR-003**: The change MUST move
  `src/mist/intelligence/analytics/site_analytics_configurator.py` to
  `src/mist/intelligence/analytics/site/site_analytics_configurator.py`.
- **FR-004**: The change MUST move
  `src/mist/intelligence/analytics/site_inventory_health_analyzer.py` to
  `src/mist/intelligence/analytics/site/site_inventory_health_analyzer.py`.
- **FR-005**: The change MUST move
  `src/mist/intelligence/analytics/zone_analyzer.py` to
  `src/mist/intelligence/analytics/site/zone_analyzer.py`.
- **FR-006**: The change MUST NOT keep a wrapper, alias, forwarding module, fallback import, or
  deprecation path at an old module location.
- **FR-007**: Each moved module MUST keep its authority-commit module-level symbol set without an
  unapproved removal.
- **FR-008**: The symbol comparison MUST include definitions, assignments, annotated assignments,
  and imported names at module level.
- **FR-009**: The exact symbol-preservation mappings MUST be:

| Authority path | Canonical path | Authority symbol count |
| - | - | -: |
| `mist/intelligence/analytics/site_analytics_configurator.py` | `mist/intelligence/analytics/site/site_analytics_configurator.py` | 16 |
| `mist/intelligence/analytics/site_inventory_health_analyzer.py` | `mist/intelligence/analytics/site/site_inventory_health_analyzer.py` | 14 |
| `mist/intelligence/analytics/zone_analyzer.py` | `mist/intelligence/analytics/site/zone_analyzer.py` | 92 |

- **FR-010**: `tests/guardrails/test_src_public_symbol_preservation.py` MUST contain the three
  exact old-to-new mappings from FR-009.
- **FR-011**: The analytics root MUST continue to export
  `SiteAnalyticsConfigurator`, `SiteAnalyticsConfiguratorDeps`,
  `SiteInventoryHealthAnalyzer`, and `SiteInventoryHealthAnalyzerDeps`.
- **FR-012**: The four root exports MUST resolve to the classes in the new `site` package.
- **FR-013**: The change MUST NOT add a fifth analytics root export.
- **FR-014**: Existing analytics calculations, prompts, confirmation words, logs, CSV content,
  filenames, Mist calls, error handling, and cancellation behavior MUST remain unchanged.
- **FR-015**: The change MUST update canonical runtime paths in `MistHelper.py`,
  `src/mist/intelligence/analytics/__init__.py`, and
  `src/operations/exporting/export/site_export_utils.py`.
- **FR-016**: The change MUST update canonical script paths in `scripts/replace_zone.py`.
- **FR-017**: The change MUST update canonical test and mock paths in these files:
  `tests/unit/analytics/test_site_analytics_configurator.py`,
  `tests/unit/analytics/test_site_inventory_health_analyzer.py`,
  `tests/unit/test_zone_analyzer.py`, and
  `tests/unit/export/test_site_export_utils_extended.py`.
- **FR-018**: The change MUST update active documentation paths in
  `documentation/architecture.md`,
  `documentation/diagrams/core/architecture-overview.md`,
  `documentation/menu-api/safe.md`, and `documentation/menu-api/destructive.md`.
- **FR-019**: The change MUST update generated documentation paths in
  `documentation/wiki/Menu-API-Endpoints-Safe.md` and
  `documentation/wiki/Menu-API-Endpoints-Destructive.md`.
- **FR-020**: The change MUST leave historical specifications for other issues unchanged.
- **FR-021**: The change MUST leave `CHANGELOG.md` unchanged.
- **FR-022**: The change MUST add
  `changelog.d/issue-3992-site-analytics-package.md`.
- **FR-023**: The changelog fragment MUST contain one heading and one `Changed` bullet that names
  issue #3992.
- **FR-024**: The analytics root MUST have exactly four direct structural children after metadata
  exclusions: three modules and the `site` package.
- **FR-025**: The new `site` package MUST have exactly three direct structural children after
  metadata exclusions.
- **FR-026**: The change MUST add
  `tests/guardrails/test_analytics_package_structure.py`.
- **FR-027**: The analytics structure guard MUST inspect only package directories under
  `src/mist/intelligence/analytics`.
- **FR-028**: The guard MUST enforce a maximum of five direct structural children for each checked
  package directory.
- **FR-029**: The repository structure test MUST require these exact measured counts:
  `src/mist/intelligence/analytics` equals four and
  `src/mist/intelligence/analytics/site` equals three.
- **FR-030**: The guard MUST report that it checked exactly two repository package directories.
- **FR-031**: A controlled failure proof MUST create one checked package with six structural
  children.
- **FR-032**: The controlled failure proof MUST require the checked count, violating path, and
  measured count of six in the failure message.
- **FR-033**: A missing-root proof MUST require the absent root path and a clear inspection cause
  in the failure message.
- **FR-034**: An active old-path check MUST cover tracked runtime, test, script, mock, active
  documentation, and generated documentation files.
- **FR-035**: The active old-path check MUST exclude `specs/` and `CHANGELOG.md`.
- **FR-036**: The active old-path check MUST report each tracked file that still names an old
  dotted import or old slash path, except the preserved historical catalog mapping.
- **FR-037**: The implementation MUST use
  `0b04cda81c8ef75096f3bedae0885038c775d665` as the approved GitHub `main` authority.
- **FR-038**: The historical performance hook catalog MUST keep its recorded paths and resolve
  moved source paths through an explicit mapping in
  `tests/guardrails/test_performance_hook_catalog.py`.
- **FR-039**: The change MUST remove only the resolved analytics entry from
  `tests/guardrails/nested_package_baseline.json` and update its measured-count assertion.

### Preservation Boundaries

The change preserves these exact contracts:

- Preserve every module-level symbol in each moved module.
- Preserve each class, function, constant, type alias, imported name, and private helper.
- Preserve the four existing analytics root re-exports.
- Preserve each method signature and dependency container field.
- Preserve analytics output, safety prompts, logs, exports, and Mist API behavior.
- Preserve test file locations unless a path reference inside the test must change.
- Preserve generated documentation content except for the moved source links.
- Preserve active documentation content except for the moved source links.
- Preserve historical specifications and the released changelog byte for byte.

### Scope Boundaries

The implementation scope includes these items:

- Add the `site` package initializer.
- Move the three approved modules without wrappers.
- Update each exact canonical path surface in FR-015 through FR-019.
- Update the exact symbol-preservation mappings.
- Add the scoped analytics structure and active-path guard.
- Add the three direct guard failure proofs.
- Add the issue changelog fragment.

### Non-Goals

- Do not change analytics behavior or output.
- Do not rename a class, function, constant, helper, type alias, or dependency field.
- Do not split or combine the three moved modules.
- Do not move the analytics unit test files.
- Do not add new Mist API calls or direct HTTP calls.
- Do not change menu numbers, registry categories, or primary-key strategies.
- Do not repair an unrelated five-child violation.
- Do not broaden the guard beyond `src/mist/intelligence/analytics`.
- Do not change another issue's specification.
- Do not edit `CHANGELOG.md`.

### Required Tests

- Run `python -m pytest tests/unit/analytics/test_site_analytics_configurator.py`.
- Run `python -m pytest tests/unit/analytics/test_site_inventory_health_analyzer.py`.
- Run `python -m pytest tests/unit/test_zone_analyzer.py`.
- Run `python -m pytest tests/unit/export/test_site_export_utils_extended.py`.
- Run `python -m pytest tests/guardrails/test_src_public_symbol_preservation.py`.
- Run `python -m pytest tests/guardrails/test_analytics_package_structure.py -q -s`.
- Run the combined focused test set to detect shared-state failures.
- Run `python scripts/generate_menu_wiki.py` and require only the approved path updates.
- Run `python -m scripts.menu_api_map` and require only the approved path updates.
- Run the applicable compile, Ruff, Black, type, complexity, security, and documentation gates.
- Run the test-quality preflight before the test-quality analyzer.
- Run the changed-test quality gate against the pull request base after the implementation commit.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The analytics root has exactly four direct structural children after metadata
  exclusions.
- **SC-002**: The new `site` package has exactly three direct structural children after metadata
  exclusions.
- **SC-003**: All 122 authority-commit module-level symbols remain across the three canonical
  destination modules.
- **SC-004**: All four existing analytics root exports remain importable from the analytics root.
- **SC-005**: Zero active runtime, test, script, mock, or maintained documentation references use
  an old module path, except the preserved historical catalog mapping.
- **SC-006**: The repository structure guard reports exactly two checked package directories.
- **SC-007**: The six-child failure proof identifies one checked directory, its path, and a count
  of six.
- **SC-008**: The missing-root proof identifies the absent root and the inspection failure.
- **SC-009**: Each focused behavior test and each required guard test passes.
- **SC-010**: No file under another issue's specification directory changes.
- **SC-011**: `CHANGELOG.md` has zero changes.
- **SC-012**: One issue #3992 changelog fragment records the package move.
- **SC-013**: The historical performance catalog resolves its recorded site analytics paths to
  the canonical modules without changing the catalog records.
- **SC-014**: The nested package guard passes with 35 violations and 242 total excess, with no
  unrelated baseline entry changed.

## Assumptions

- The approved move changes module locations and required import references only.
- The four analytics root exports are the complete root export contract.
- The existing test files remain at their current paths.
- Package metadata includes `__init__.py` and generated cache directories.
- Active documentation includes maintained files under `documentation/`.
- Generated documentation includes the two maintained wiki endpoint files named in FR-019.
- Historical specifications and released changelog entries are immutable records.
- Existing focused tests remain the behavior authority for the three moved modules.

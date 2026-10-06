# Feature Specification: Metrics Gateway Core Package

**Feature Branch**: `4009-metrics-gateway-core`

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: "Issue #4009: move the metrics gateway cache, catalog, collector, and samples modules into a core package without compatibility wrappers, preserve symbols and behavior, update active imports, tests, MIB references, generated menu pages, and quality guards."

## User Scenarios & Testing

### User Story 1 - Keep the gateway structure within the project limit (Priority: P1)

As a maintainer, I need the gateway core modules in one package so the gateway root has five structural children.

**Independent Test**: Run the focused structure guard and inspect both package child sets.

### User Story 2 - Preserve runtime behavior through canonical imports (Priority: P1)

As an operator, I need metrics and MIB generation to use the moved modules without behavior changes.

**Independent Test**: Run the focused metrics gateway and MIB tests, the symbol guard, and the compile and type checks.

### User Story 3 - Keep active references current (Priority: P2)

As a maintainer, I need tests, MIB contracts, documentation, and generated menu pages to name the canonical source paths.

**Independent Test**: Run the menu generator, menu drift check, documentation checks, and path scans.

## Requirements

- **FR-001**: Move `cache.py`, `catalog.py`, `collector.py`, and `samples.py` to `metrics_gateway/core/`.
- **FR-002**: Keep `prometheus.py`, `service.py`, `snmp.py`, and `web.py` at the gateway root.
- **FR-003**: Do not leave wrappers, aliases, or fallback imports at the old module paths.
- **FR-004**: Preserve module-level symbols and runtime behavior.
- **FR-005**: Update gateway, MIB generator, test, logger, contract, documentation, and generated menu references.
- **FR-006**: Keep `MistHelper.py` unchanged.
- **FR-007**: Record each old-to-new module path in the public symbol guard.
- **FR-008**: Add a focused structure assertion for five gateway children and four core children.
- **FR-009**: Add one issue-specific changelog fragment and these three routed specification files.
- **FR-010**: Do not edit historical specifications.

## Success Criteria

- **SC-001**: The gateway root has exactly five structural children.
- **SC-002**: The core package has exactly four structural children.
- **SC-003**: Focused metrics gateway and MIB tests pass.
- **SC-004**: The public symbol guard reports no lost module-level symbols.
- **SC-005**: Menu generation and drift checks pass with canonical source links.
- **SC-006**: No compatibility module remains at an old location.

## Assumptions

- Existing tests define the supported behavior contract.
- Root package exports remain available from `metrics_gateway` and import their canonical core modules directly.
- The existing generated menu pages are active references and must be regenerated.

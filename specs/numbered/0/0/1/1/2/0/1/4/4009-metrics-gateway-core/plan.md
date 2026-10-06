# Implementation Plan: Metrics Gateway Core Package

**Branch**: `4009-metrics-gateway-core` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

## Summary

Move four data-plane modules into `src/interfaces/monitoring/metrics_gateway/core/`.
Update imports, logger assertions, MIB generator references, contracts, documentation, generated menu pages, and guards.
Preserve root exports without aliases. Keep `MistHelper.py` unchanged.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Testing**: Focused metrics gateway and MIB tests, source structure and symbol guards, compile, Ruff, Black, Mypy, Bandit, complexity, docstring, changelog, Markdown-link, menu generation, menu drift, and post-commit test-quality checks.

**Constraints**: Use `git mv`. Do not add compatibility wrappers. Do not edit historical specifications. Keep the gateway root at five children and core at four children.

## Design Decisions

### Decision: Use one nested core package

The four modules share the data-plane model and collector state. A nested package reduces the gateway root to the required five children without changing the output modules.

### Decision: Use canonical imports only

Every caller uses `metrics_gateway.core.<module>`. Root exports import these paths directly. The old paths remain absent.

### Decision: Extend the existing source guards

The public symbol guard maps each old module path to its new path. The domain structure guard asserts the exact gateway and core child sets.

## Implementation Phases

1. Move the four modules and add `core/__init__.py`.
2. Update runtime, MIB generator, test, logger, documentation, and generated page references.
3. Update the root exports and source guards.
4. Add the changelog fragment and routed task records.
5. Run focused tests, generated-page checks, repository quality gates, commit, and the required post-commit test-quality procedure.

## File Boundary

The change includes the four moved modules, the new core initializer, affected runtime and test imports, MIB references, active documentation and generated menu pages, source guards, one changelog fragment, and the three routed specification files.

The change excludes `MistHelper.py`, historical specifications, shared registries, issue state, workflows, pushes, and pull requests.

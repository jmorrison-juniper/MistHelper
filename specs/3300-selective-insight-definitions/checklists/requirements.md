# Specification Quality Checklist: Selective Insight Definitions

**Purpose**: Validate specification completeness and quality before proceeding to planning.

**Created**: 2026-10-01

**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs).
- [x] Focused on user value and business needs.
- [x] Written for non-technical stakeholders.
- [x] All mandatory sections completed.

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain.
- [x] Requirements are testable and unambiguous.
- [x] Success criteria are measurable.
- [x] Success criteria are technology-agnostic (no implementation details).
- [x] All acceptance scenarios are defined.
- [x] Edge cases are identified.
- [x] Scope is clearly bounded.
- [x] Dependencies and assumptions identified.

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria.
- [x] User scenarios cover primary flows.
- [x] Feature meets measurable outcomes defined in Success Criteria.
- [x] No implementation details leak into specification.

## Notes

Items marked incomplete require spec updates before `/speckit.clarify` or `/speckit.plan`.
Checklist marks evaluate specification quality, not completed implementation or validation.
The inherited constraints below record the user's limits.
They do not prescribe a new implementation design.

### Review Record

Review iteration 1 passed all 16 quality items.
The specification contains four user stories, 13 acceptance scenarios, 13 functional requirements, and seven measurable outcomes.
No clarification markers or unresolved quality issues remain.

The review confirmed these acceptance anchors:

- User Story 1 states, "It does not access or change another definition cache."
- FR-003 states, "An insight cache exactly 24 hours old, older than 24 hours, or missing MUST require a refresh."
- FR-009 states, "Every failed refresh MUST retain its first error and any original HTTP `4xx` or HTTP `5xx` status."
- SC-003 states, "Every caller reduces median refresh time by at least 90% across five equivalent paired offline trials."
- Scope and Authorization states, "The site, device, and organization caller files remain unchanged."

Requirements cover selective refresh, cache behavior, full coverage, compatibility, failures, logging, and offline isolation.
The required evidence section distinguishes future test results from specification review.
The technical file reservation and tool obligations remain in this checklist rather than becoming a new implementation design.

Artifact checks passed for template section order, relative links, table structure, ASCII text, and trailing whitespace.
The three inspected shared SpecKit files retained their original content hashes.
The branch and base revision remained unchanged.
No implementation tests, timing trials, or code quality gates run during this specification step.

### Actual Caller Coverage

Record red tests and before-and-after elapsed measurements through every entry below.
Do not replace the caller's refresh path with a mock.

| Operation | Actual refresh entry | Expected scope |
| --- | --- | --- |
| Menu 74 | `SiteMetricOperation._refresh_const_metrics` in [site_metric_operation.py](../../../src/export/site_insights/site_metric_operation.py) | `site` |
| Menu 75 | `SiteClientInsightsService._print_intro_and_refresh` in [site_client_insights.py](../../../src/refactors/serial_cc/site_client_insights.py) | `client` |
| Menu 76 | `DeviceMetricOperation._refresh_const_metrics` in [device_metric_operation.py](../../../src/export/site_insights/device_metric_operation.py) | `device` |
| Organization insight export | `OrgExportUtils._insight_setup_or_empty` in [org_export_utils.py](../../../src/export/org_export_utils.py) | `org` |

Use `tmp_path` for all test files and controlled cache directories.
Never use a production data directory.
Use offline constant responses and a known request delay.
Use a controlled cache clock and a real elapsed-time clock for timing trials.
Report actual request and write counts rather than assuming one request per definition.
Separate definition writes from existing empty insight-output writes.

### Inherited Repair Boundaries

Only these source files are reserved for later implementation:

- [src/export/const_definitions_exporter.py](../../../src/export/const_definitions_exporter.py)
- [src/analytics/insight_metrics_utils.py](../../../src/analytics/insight_metrics_utils.py)
- [src/refactors/serial_cc/site_client_insights.py](../../../src/refactors/serial_cc/site_client_insights.py)

Only these test files are reserved:

- `tests/unit/export/test_selective_insight_definitions.py`
- [tests/unit/analytics/test_insight_metrics_utils.py](../../../tests/unit/analytics/test_insight_metrics_utils.py)

The only reserved release note is `changelog.d/issue-3300-selective-insight-definitions.md`.
Do not create it during this specification step.

The existing semantic exporter may expose a proper named-definition entry.
Reuse `_inspect_module`, `_register_endpoint`, `EndpointConfig`, and `_process_single_endpoint`.
Reuse `_is_file_fresh`, `_fetch_and_export_endpoint`, and `_export_data`.
Do not duplicate cache logic or introduce pass-through wrappers.

Use `InsightMetricsUtils.export_const_insight_metrics` as the shared insight refresh contract.
Route the client refresh through that helper and remove its unused `ConstDefinitionsExporter` dependency.
Keep the three other callers unchanged.
Keep `ConstDefinitionsExporter.export_all` for the full-definition operation.

Never edit `MistHelper.py`, `endpoint_family_exporter.py`, `endpoint_catalog.py`, or `endpoint_primary_key_strategies.py`.
Never edit `web_portal/menu_registry.py`, `README.md`, `CHANGELOG.md`, agent instructions, or operator guides.
Never change dependency or SDK pins, database schemas, primary keys, baselines, suppressions, or exclusions.
Never change another branch or the main checkout.
Do not use live Mist credentials, live Mist requests, stores, or containers.

### Contract Checks Required Later

Preserve the eight definition fields listed in FR-006, including their order and normalized values.
Preserve scope parsing, missing-field exclusions, and template-name exclusions.

Site, device, and client refresh entries retain their `None` return contract.
Organization setup retains its metric-list return or `None` when no organization metrics exist.
Its no-metrics path retains four empty normalized outputs without a legacy output.
Other existing caller empty-output paths, prompts, banners, filenames, and error handling remain compatible.

Refresh messages must not claim a comprehensive export for selective refresh.
An existing `ConstInsightMetrics.csv` must not produce a success message after a failed refresh.
Test HTTP `4xx` and HTTP `5xx` status preservation, empty error bodies, and secondary write failures.
Retain the first error and the existing failure counters.
Test meaningful before-and-after action logs with counts and status.
Confirm that logs contain no secrets and use ASCII.

### Validation Obligations for Later Implementation

Use Python 3.13 in this worktree's own virtual environment.
Use the existing bootstrap and current dependency manifests without changing their pins.
Do not create the environment during this artifact-only step.

Run the focused tests and report coverage for every changed method.
Do not run the full unrelated test suite unless focused evidence requires it.
Do not reduce configured thresholds or change the test-quality ratchet.

Run the full configured Ruff scope with `ruff check .`.
Run the full configured Black scope with `black --check --diff .`.
Run configured Bandit with `bandit -c pyproject.toml -r .`.
Use the exact `MYPY_PATHS` from [ci.yml](../../../.github/workflows/ci.yml):

```text
src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py
```

Run mypy against that scope with `--config-file pyproject.toml`.
Retain `.github/test-quality-config.toml` and `.github/test-quality-baseline.json` unchanged.
Run the configured test-quality gate against the feature changes.
Record related issue links and review prose against the [STE guide](../../../documentation/ASD-STE100_writing-guide.md).

Report unavailable dictionary and PowerShell capabilities honestly.
The current host has no `hunspell`, `aspell`, or `pwsh` executable.
This observation does not certify a controlled STE dictionary check.

Any later local commit requires completed validation, a conventional message, and the required Copilot App trailer.
This specification step does not commit.
Stop before every push or pull request operation until the parent grants publication release.

### Workflow Scope

The active templates resolve from the core `.specify/templates/` directory.
The explicit feature directory replaces automatic feature numbering.
The branch already exists at the user's stated base revision.
Do not create or rename it.

The configured `before_specify` branch hook conflicts with the user's no-branch-change instruction.
The configured mandatory `after_specify` companion hook writes an unauthorized `.spec-context.json` artifact.
The optional commit hook also exceeds this step's authorization.
Do not execute those mutations during this step.
Leave `.specify/feature.json`, hook configuration, and all other shared state unchanged.

Pass `specs/3300-selective-insight-definitions` explicitly to any separately authorized downstream workflow.
No plan, tasks, source changes, tests, release note, commit, push, or pull request forms part of this step.

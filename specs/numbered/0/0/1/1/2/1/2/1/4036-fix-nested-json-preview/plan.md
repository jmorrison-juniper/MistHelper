# Implementation Plan: Nested JSON Result Preview

**Branch**: `3998-fix-nested-json-preview` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/1/2/1/2/1/4036-fix-nested-json-preview/spec.md`.

## Summary

The confirmed defect routes a nested file-preview request to `data.preview_table`. A synthetic Flask test returns 404 for nested JSON preview while download returns 200. Change request selection so a browsable file retains its complete relative path and remains distinct from an explicit SQLite table request. Retain the existing path guard, SQLite table behavior, JSON presentation, and output-list membership. Add route-level and browser-level regression tests and a user-facing changelog fragment.

## Technical Context

**Language/Version**: Python 3.13 or later, as declared by `pyproject.toml`.

**Primary Dependencies**: Flask 3.1 and pytest 9, already used by the portal and its tests.

**Storage**: Result files in the configured data directory and existing SQLite tables.

**Testing**: Flask test client and Playwright browser with temporary files and SQLite fixtures; pytest.

**Target Platform**: MistHelper web portal on supported Python platforms.

**Project Type**: Web application with a Flask portal.

**Performance Goals**: Preserve current preview pagination. No new performance target applies.

**Constraints**: Keep each requested relative file path intact. Keep SQLite table selection separate from file selection. Preserve the existing safe-path checks and denial results. Do not change output-list membership or preview content rules. Use synthetic local fixtures only.

**Scale/Scope**: One route selection correction, route and browser regression tests, and one issue-specific changelog fragment.

## Constitution Check

**Pre-design gate: PASS with setup limitation.** The feature uses the existing managed eight-segment base-5 path. The current feature directory already exists. The `design/` directory has two direct children. This plan adds `research.md`, `data-model.md`, and `quickstart.md`, bringing it to five.

- **Process-folder exception**: `specs/` has 795 direct children and `changelog.d/` has 272. These are existing folder debt. This feature adds no new child to `specs/`. The later implementation may add only its unique required fragment, `changelog.d/issue-4036-nested-json-preview.md`.
- **Separate remediation action**: Track a future maintenance change to reduce existing direct-child debt in `changelog.d/`. Do not move or combine this feature's unique fragment as part of this fix.
- **Path safety**: Preserve the existing path guard. Keep tests for traversal, absolute paths, encoded traversal, and links outside the data directory.
- **SQLite behavior**: Preserve current table selection, rows, order, pagination, and missing-table responses.
- **Mist Cloud**: Not applicable. This feature reads local result files and uses no live Mist calls.
- **Release pipeline**: Planning changes do not trigger the deployment pipeline. The implementation changelog fragment is a release artifact and must follow the repository's full release pipeline.
- **Setup check**: The required PowerShell setup script was attempted, but `pwsh` is not installed. The feature path is resolved from the specified path and the repository's `SPECIFY_FEATURE_DIRECTORY` override rules. The existing `.specify/feature.json` selector remains unchanged.

No constitution violation is introduced by this design.

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/1/2/1/2/1/4036-fix-nested-json-preview/
├── spec.md
├── plan.md
└── design/
    ├── evidence.md
    ├── checklists/
    │   └── requirements.md
    ├── research.md
    ├── data-model.md
    └── quickstart.md
```

### Source Code

```text
web_portal/
└── routes/
    └── data.py

tests/
├── unit/
    └── web_portal/
        └── test_preview_row_order.py
└── e2e/
    └── web_portal/
        └── test_operation_results_table.py

changelog.d/
└── issue-4036-nested-json-preview.md
```

**Structure Decision**: Keep the route fix in the existing Flask data route module. Add route regression cases to the existing portal test module, which builds a Flask test client with temporary data. Add a browser regression to the existing Results table test with a local synthetic file and no live Mist calls. Add one unique fragment in the repository's established `changelog.d/` location. Record the unchanged HTTP route contract in `design/data-model.md`. Do not add a contracts directory because the existing design folder has a five-child limit.

## Implementation Sequence

1. Make route selection distinguish a nested browsable file from an SQLite file-and-table request. Keep the complete relative path for a file preview.
2. Preserve the existing path guard and all denial behavior. Do not add a path bypass or widen file access.
3. Add a route-level regression test with a temporary `mib_generator/allowlist.json`. Assert that preview returns the expected JSON and that download remains successful.
4. Add a browser regression that previews a temporary nested JSON result through the Results panel and checks its contents.
5. In route test coverage, confirm that a nested SQLite table still returns its existing response and that a missing table retains its current error.
6. Add a local user-facing fragment at `changelog.d/issue-4036-nested-json-preview.md`. State that nested JSON result files can now be previewed in the Results panel.
7. Run the focused route tests, browser test, path-guard tests, SQLite preview tests, and applicable repository gates. Run the full required release pipeline for the implementation change.

## Complexity Tracking

No new subsystem, dependency, or public endpoint is planned. The only recorded structural debt is the existing process-folder child count described in the Constitution Check.

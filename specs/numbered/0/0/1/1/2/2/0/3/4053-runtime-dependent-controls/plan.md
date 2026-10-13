# Implementation Plan: Runtime-Dependent Portal Controls

**Branch**: `jmorrison-juniper-fix-4053-runtime-portal-controls` | **Date**: 2026-10-13 | **Spec**: [spec.md](spec.md)

**Input**: Numeric feature specification at `specs/numbered/0/0/1/1/2/2/0/3/4053-runtime-dependent-controls/spec.md`

## Summary

Expose the missing browser answers for menus 91 and 195. Keep the existing parameter registry and prompt handlers. Match browser answers to prompt contexts so conditional prompts cannot shift them. Build menu 195 file controls from the current `data/` files and validate answers before starting the operation.

## Technical Context

**Language/Version**: Python 3.13 or newer and existing browser JavaScript

**Primary Dependencies**: Existing MistHelper, Flask, pytest, and Playwright dependencies; no new packages

**Storage**: Existing local `data/` CSV and TSV files; no schema changes

**Testing**: Focused pytest tests and the existing web portal Playwright tests

**Target Platform**: Windows 11, macOS, Linux, and the existing Podman image

**Project Type**: Python application with a web portal

**Performance Goals**: Build each menu form from one bounded local directory scan

**Constraints**: Preserve CLI prompts. Do not make live Mist calls in tests. Reject stale or invalid browser selections before starting menu 195.

**Scale/Scope**: Menus 91 and 195 only. Menus 94, 95, and 96 already work and stay unchanged.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Use the existing `PARAMETER_REGISTRY` and menu parameter endpoint. Do not add a route adapter or a second parameter source.
- Preserve existing numeric command-line answers. Add exact manufacturer and file-name answers only for browser controls.
- Require an explicit browser choice before save or batch write-back. Keep the current safe defaults and per-site approvals.
- Mock local files and Mist responses in tests. Do not call Mist during validation.
- Add the feature record under the managed eight-level base-5 path. Do not add a direct child to `specs/`.
- Keep generated test output under `test-artifacts/` or pytest temporary directories.
- No new external Mist transport is needed. Existing Mist requests stay behind `mistapi`.
- No new dependency, compatibility shim, or broad rewrite is planned.
- Existing process-folder debt remains recorded in `tests/guardrails/process_folder_baseline.json`. Keep its incremental cleanup in a separate process-maintenance action. This issue adds no direct child under `specs/`.
- Use a Conventional Commit subject and the issue-linked pull request title.

**Gate result**: Pass. The design uses current portal services and prompts, stays within the issue scope, and does not introduce a new transport or a direct `specs/` child.

## Phase 0: Research

See [research.md](research.md). Current main already includes the fix for issue #4121 and the controls for menus 94 through 96. No open pull request owns the affected files. The remaining defect is the absent menu 91 and 195 parameter data, plus the manufacturer parser that accepts numeric input only.

## Phase 1: Design

See [data-model.md](data-model.md), [contracts/operations-parameter-controls.md](contracts/operations-parameter-controls.md), and [quickstart.md](quickstart.md).

Menu 91 gets one optional text control. Its prompt accepts an exact manufacturer name and retains numeric choices for CLI users.

Menu 195 gets controls that match prompts present at form-build time. The primary file control appears only when more than one candidate exists. File choices use exact basenames, while CLI numeric choices remain valid. The optional authority file uses an explicit skip value. The optional business-name control appears only when `BUSINESS_NAME` is empty. Each control names its prompt context. The service validates current contexts and choice values before it starts the operation.

**Constitution re-check**: Pass. The design preserves the single registry, keeps Mist changes opt-in, uses the existing local data directory, and adds no new dependency. A skipped prompt cannot consume a later answer. Each site still needs its current approval, and an unanswered browser prompt uses the no default.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/2/2/0/3/4053-runtime-dependent-controls/
├── checklists/requirements.md
├── contracts/operations-parameter-controls.md
├── data-model.md
├── plan.md
├── quickstart.md
├── research.md
├── spec.md
└── tasks.md
```

### Source Code (repository root)

```text
web_portal/
├── services/operation.py
└── static/js/operations.js

src/mist/
├── intelligence/reports/wired_client_manufacturer_report_generator.py
└── resources/site/address_audit/
    ├── audit_engine.py
    └── comparison_display.py

tests/
├── e2e/web_portal/
└── unit/
    ├── reports/test_issue_4053_manufacturer_input.py
    ├── site/address_audit/
    └── web_portal/
```

**Structure Decision**: Change the existing portal parameter service, browser control renderer, and the two prompt owners. Keep all tests in the existing E2E and unit test trees.

## Complexity Tracking

No constitution violations require an exception.

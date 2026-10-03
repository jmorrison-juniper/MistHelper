# Implementation Plan: RRM optimize or reset plan capture

**Branch**: `feat/3571-rrm-reset-plan`  
**Spec**: `specs/3571-rrm-reset-plan/spec.md`  
**Issue**: `#3571`  
**Menu**: `291`  
**Category**: `destructive`

## Summary

Add a new `src/mist/resources/site/rrm_reset/` package for menu `291`. The operation captures the current RRM plan, writes a before file, optionally sends an optimize or reset request, waits for the configured settle time, captures an after file, and writes a diff file.

## Technical Context

**Language**: Python `3.13+`  
**Dependencies**: Existing `mistapi>=0.64.0,<0.65` and standard library only  
**Output**: CSV files through the shared `DataExporter.write_with_format_selection` path  
**Testing**: `pytest`, `ruff`, `black`, `mypy`, `pydocstyle`, `vulture`, and `interrogate`  
**Package**: `src/mist/resources/site/rrm_reset/`  
**Tests**: `tests/unit/site/rrm_reset/`  
**Destructive Control**: Typed `OPTIMIZE` or `RESET` confirmation and dry-run support  
**Deferred Wiring**: `specs/3571-rrm-reset-plan/wiring.md`

## Constitution Check

- **Class-based design**: The package uses classes for the client, model logic, output writing, and operation entry point.
- **No wrappers**: The operation delegates through cohesive classes, not pass-through functions.
- **Safety-first input**: The operation validates the action, the site, and the typed confirmation before any Mist change request.
- **Action logging**: The client and operation log before and after each meaningful action.
- **Inline comments**: New Python lines include inline comments that explain intent.
- **STE**: User-facing text uses short and direct sentences.

## Project Structure

```text
src/mist/resources/site/rrm_reset/
├── __init__.py
├── client.py
├── model.py
├── operation.py
└── writer.py

tests/unit/site/rrm_reset/
├── __init__.py
├── test_rrm_reset_client.py
├── test_rrm_reset_model.py
└── test_rrm_reset_operation.py

specs/3571-rrm-reset-plan/
├── contracts/
│   └── operation-contract.md
├── data-model.md
├── plan.md
├── quickstart.md
├── research.md
├── spec.md
├── tasks.md
└── wiring.md
```

## Phase 0 Research

Research is recorded in `research.md`.

## Phase 1 Design

Design artifacts:

- `data-model.md`
- `contracts/operation-contract.md`
- `quickstart.md`

## Phase 2 Task Plan

Task execution is recorded in `tasks.md`.

## Risk and Mitigation

- **Risk**: The reset action changes the radio configuration for every AP at the selected site.  
  **Mitigation**: Require typed confirmation and state human review in the pull request.
- **Risk**: The installed SDK lacks `resetSiteAllApsToUseRrm`.  
  **Mitigation**: Use `apisession.mist_post` for the documented path and record the decision in research.
- **Risk**: A diff without a durable before file is unsafe.  
  **Mitigation**: The workflow stops if the before writer reports failure.

## Gates

Run these gates before each implementation commit:

```powershell
C:\Users\jmorrison\mh-fleet\3571-rrm-reset-plan\.venv\Scripts\python.exe -m py_compile <new-py-files>
C:\Users\jmorrison\mh-fleet\3571-rrm-reset-plan\.venv\Scripts\python.exe -m ruff check src/mist/resources/site/rrm_reset tests/unit/site/rrm_reset
C:\Users\jmorrison\mh-fleet\3571-rrm-reset-plan\.venv\Scripts\python.exe -m black --check src/mist/resources/site/rrm_reset tests/unit/site/rrm_reset
C:\Users\jmorrison\mh-fleet\3571-rrm-reset-plan\.venv\Scripts\python.exe -m mypy src/mist/resources/site/rrm_reset --config-file pyproject.toml
C:\Users\jmorrison\mh-fleet\3571-rrm-reset-plan\.venv\Scripts\python.exe -m pydocstyle src/mist/resources/site/rrm_reset
C:\Users\jmorrison\mh-fleet\3571-rrm-reset-plan\.venv\Scripts\python.exe -m pytest tests/unit/site/rrm_reset -q --timeout=120
```

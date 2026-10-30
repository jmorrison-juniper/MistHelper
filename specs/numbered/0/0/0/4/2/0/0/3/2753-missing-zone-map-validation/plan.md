# Implementation Plan: Missing Zone Map Validation

**Branch**: `jmorrison-juniper-missing-zone-map-validation` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification under the eight-level base-5 route for issue #2753.

## Summary

Require an explicit missing-zone dictionary before the report prints its count or claims that all sites have common zones. Preserve valid display behavior.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Primary Dependencies**: Existing Python logging and pytest dependencies

**Storage**: None

**Testing**: `python -m pytest tests/unit/test_zone_analyzer.py`

**Target Platform**: Windows, macOS, and Linux

**Project Type**: Python command-line report

**Performance Goals**: Preserve the existing display cap and runtime behavior for valid data.

**Constraints**: Reject an absent or non-dictionary map before writing any section output.

**Scale/Scope**: One display helper, focused unit tests, and this feature record.

## Constitution Check

- The feature root has four children after this record: `spec.md`, `plan.md`, `tasks.md`, and `design/`.
- The existing route parent has three feature directories. This record adds one child and keeps the total at four.
- The new `design/` directory has five children at most: `checklists/`, `research.md`, `data-model.md`, `quickstart.md`, and `contracts/`.
- The required changelog fragment adds a direct child to `changelog.d/`, which currently has 254 entries. This existing process-folder debt does not permit unrelated children.
- Separate remediation action: keep release cleanup and indexing of old `changelog.d/` fragments in the release process. This slice does not move or rewrite fragments.
- The source change adds no class or hierarchy level. The existing display helper remains below the function limits.
- The error log gives the invalid input contract. No API call, export, identifier, credential, upgrade, or destructive operation changes.
- The output check remains deterministic for empty and nonempty dictionaries.

**Gate result**: Pass. The scope follows the existing managed route and adds no source or process-folder structure beyond its required record.

## Project Structure

### Documentation

```text
specs/numbered/0/0/0/4/2/0/0/3/2753-missing-zone-map-validation/
  spec.md
  plan.md
  tasks.md
  design/
    checklists/requirements.md
    research.md
    data-model.md
    quickstart.md
    contracts/missing-zone-display.md
```

### Source Code

```text
src/mist/intelligence/analytics/zone_analyzer.py
tests/unit/test_zone_analyzer.py
changelog.d/issue-2753-missing-zone-map-validation.md
```

**Structure Decision**: Keep the current analyzer module and unit test. Add no new runtime module or dependency.

## Complexity Tracking

No structure or complexity exception is required.

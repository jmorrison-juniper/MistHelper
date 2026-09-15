# Implementation Plan: Menu Entry Rows and Menu Dependency Factories

**Branch**: `1704-menu-entry` | **Date**: 2026-09-14 | **Spec**: `specs/1704-menu-entry/spec.md`

## Summary

Replace menu tuple values with immutable `MenuEntry` rows. Move repeated constructor arguments into three factory classes. Update the CLI, the test runners, the web portal, and the menu reference generator to read named fields.

## Technical Context

**Language and Version**: Python 3.13.

**Primary Dependencies**: Standard library `dataclasses`, existing MistHelper classes, pytest, ruff, black, mypy, Bandit, Pylint, and Radon.

**Storage**: Not applicable. The change adds no persistent state.

**Testing**: pytest regression tests and the required local quality gates.

**Target Platform**: Windows development host and the existing Linux container runtime.

**Project Type**: Python CLI with a Flask web portal.

**Performance Goals**: The menu table must import without network access. The new tests must stay hermetic and fast.

**Constraints**: The refactor must not change a menu number, a menu name, or a menu category. `MistHelper.py` must keep the same module-level symbol table.

**Scale and Scope**: One runtime menu table with 268 entries. The related call sites are in `MistHelper.py`, `src/troubleshooting/interactive_test_runner.py`, `web_portal/`, and `scripts/generate_menu_wiki.py`.

## Constitution Check

- The change starts from `origin/main`.
- The implementation uses class-based factories.
- The implementation adds no wrapper functions.
- The implementation keeps `safe_input()` behavior unchanged.
- The implementation adds one release-note fragment.
- The implementation edits no `CHANGELOG.md`.

## Project Structure

```text
MistHelper.py
src/
  utils/
    menu_entry.py
  troubleshooting/
    interactive_test_runner.py
web_portal/
  menu_registry.py
  services/
    operation.py
scripts/
  generate_menu_wiki.py
tests/
  unit/
    test_menu_entry_metadata.py
specs/
  1704-menu-entry/
    spec.md
    plan.md
    tasks.md
    analysis.md
changelog.d/
  issue-1704-menu-entry.md
```

**Structure Decision**: Keep the public MistHelper module symbols unchanged. Put `MenuEntry` in `src/utils/menu_entry.py`. Put the factory classes under existing `GlobalImportManager` to avoid a new module-level symbol in `MistHelper.py`.

## Technical Approach

1. Add an immutable `MenuEntry` dataclass with named fields.
2. Convert each `menu_actions` value to a `MenuEntry`.
3. Add three real factory classes under `GlobalImportManager`.
4. Replace repeated inline dependency construction with factory builds.
5. Update each call site to read `handler`, `title`, `category`, `destructive`, and `supports_fast`.
6. Update the menu reference generator to parse `MenuEntry` call nodes.
7. Add regression tests for row shape, row count, destructive flags, duplicate keys, and invalid input.
8. Regenerate the menu reference files.
9. Run the required gates before commit.

## Complexity Tracking

No constitution violation remains. The factory classes sit under an existing class only to preserve the `MistHelper.py` symbol table gate.

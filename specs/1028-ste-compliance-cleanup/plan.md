# Implementation Plan: MistHelper.py STE Compliance Cleanup

**Branch**: `1028-ste-compliance-cleanup` | **Date**: 2026-07-27 | **Spec**: [spec.md](./spec.md)

## Summary

Clean up the comments and docstrings in `MistHelper.py` so the prose follows
Simplified Technical English. Fix the mechanical structural findings, split the four
over-length sentences, apply a curated dictionary swap map to comment prose, and add
a technical-noun allowlist to the linter. Change no code, no identifier, and no
logging string. Verify with the linter, the test suite, and the quality gates.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: None new for the file itself. The STE linter and its
optional spaCy backend measure progress.

**Storage**: No change. The dictionary stays git-ignored.

**Testing**: The existing test suite proves the code behavior did not change. The
linter measures the prose improvement.

**Target Platform**: Cross-platform.

**Project Type**: Single project. The change is to one file plus a linter config.

**Performance Goals**: No runtime change.

**Constraints**: Comments and docstrings only. No code behavior change. The
120-character line limit and the inline-comment rule apply.

**Scale/Scope**: One file of about 5100 lines. About 148 mechanical fixes, 4 sentence
splits, and a curated set of dictionary swaps.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Structural discipline**: The change edits prose, not structure. It adds no
  function and no class.
- **Inline comments**: Every touched line keeps its inline comment. The edits improve
  the comment text, they do not remove it.
- **Safety-first**: The change touches no input handling and no destructive path. The
  test suite guards behavior.
- **Quality gates**: Ruff, black, mypy, radon, and pytest must pass. `py_compile`
  must pass.
- **Writing style**: The whole point is to make the prose follow the STE guide.
- **No wrappers, class-based design**: Not applicable. No code changes.

## Project Structure

### Documentation (this feature)

```text
specs/1028-ste-compliance-cleanup/
├── plan.md              # This file
├── research.md          # Phase 0: fix categories and safe-edit method
├── tasks.md             # Phase 2: the task list
└── swap-map.md          # Phase 1: the curated word-swap map
```

### Source Code (repository root)

```text
MistHelper.py            # The file to clean up (comments and docstrings only)
pyproject.toml           # Add the technical-noun allowlist under [tool.ste_linter]
tools/ste_linter/        # Add allowlist support to the dictionary rules
```

**Structure Decision**: The change is almost entirely in `MistHelper.py`. The
allowlist is a small, additive linter feature so the dictionary rules can skip
approved technical terms.

## Phased Approach

- **Phase A (P1)**: Mechanical structural fixes. Latin, contractions, phrasal verbs,
  semicolons, and the four sentence splits. Verifiable in continuous integration.
- **Phase B (P2)**: Curated dictionary swaps in comment prose only, from a fixed map.
- **Phase C (P3)**: The technical-noun allowlist in the linter and the configuration.
- **Deferred**: Passive voice, noun clusters, and complex tense. Tracked for later.

## Risk and Mitigation

| Risk | Mitigation |
| - | - |
| A text edit changes code behavior | Edit comments and docstrings only. Run the full test suite. Run py_compile. |
| A swap changes a word inside an identifier or a logging string | Apply swaps by reading the comment text only, never the code. Review each swap. |
| A sentence split pushes a line past 120 characters | Wrap the comment across lines. Run ruff, which flags E501. |
| The hot file has a competing pull request | Confirm no other open pull request modifies MistHelper.py before starting. |

## Complexity Tracking

*No constitution deviations. The change adds no structure and no new dependency for
the file. The allowlist is a small, additive linter option.*

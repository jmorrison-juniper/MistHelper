# Implementation Plan: Audit Report Rendering Packages

**Branch**: `4011-audit-rendering` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Numeric feature specification from `specs/numbered/0/0/1/1/2/0/2/1/4011-audit-rendering/spec.md`

## Summary

Move `renderer.py` into `src/mist/access/audit/rendering/`. Move
`_renderer_delta.py`, `_renderer_format.py`, `_renderer_html.py`,
`_renderer_mermaid.py`, and `_renderer_time.py` into
`src/mist/access/audit/rendering/helpers/`. Update each active import to the
canonical path. Add six exact old-to-new paths to the public symbol-preservation
guard. Add a focused structure guard that measures each audit package level and
rejects an active old renderer path. Preserve each module-level symbol and the
rendering behavior without a wrapper, an alias, or a fallback import. Add one
issue-specific release-note fragment during the implementation.

The implementation uses only the authorized source moves, import updates, tests,
guards, release-note fragment, and three routed specification files.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Primary Dependencies**: Python standard library, the existing audit analysis
modules, `pytest`, and the repository guardrail helpers

**Storage**: No data store changes. The renderer writes report files only.

**Testing**: Focused `pytest` checks, structure, source import, and symbol
guards, Python compilation, Ruff, Black, Mypy, Bandit, Radon complexity,
pydocstyle, Interrogate, changelog and Markdown link guards, and the required
post-commit test-quality procedure

**Target Platform**: Windows 11, macOS, and Linux

**Project Type**: Python library and command-line operational tooling

**Performance Goals**: Preserve the current audit rendering behavior without a
new runtime path or a duplicate module

**Constraints**: Keep each audit package level within five direct structural
children. Remove each old module path. Do not add a wrapper, an alias, a
fallback import, a shared registry change, a generated reference change, a
historical spec change, an `AGENTS.md` change, or a `CLAUDE.md` change.

**Scale/Scope**: Six moved modules, the affected imports and tests, one focused
structure guard, six symbol-guard path entries, one release-note fragment, and
no Mist Cloud transport change

## Constitution Check

*GATE: Pass before research and after design.*

- **Five-Item Rule**: PASS. The audit package holds ten direct structural
  children before the change. The move produces five direct children:
  `analyzer.py`, `audit_analysis_ops.py`, `filter.py`, `rendering/`, and
  `time_parser.py`. The rendering package holds two children, and the helpers
  package holds five.
- **Class-Based Architecture**: PASS. The move preserves `AuditReportRenderer`,
  `_HtmlCluster`, `_MermaidCluster`, and `DiffKeyContext`. The plan prohibits a
  wrapper module and an alias.
- **Safety-First**: PASS. The move adds no input handling and no destructive
  operation. The HTML and Mermaid escaping behavior does not change.
- **Test Discipline**: PASS. The plan runs the existing renderer tests, the
  audit operation consumer test, the symbol guard, and a new focused structure
  guard with three direct failure proofs.
- **Documentation**: PASS. The plan adds one release-note fragment and three
  routed specification files. It changes no generated reference.

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/1/2/0/2/1/4011-audit-rendering/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code

```text
src/mist/access/audit/
├── analyzer.py
├── audit_analysis_ops.py
├── filter.py
├── rendering/
│   ├── renderer.py
│   └── helpers/
│       ├── _renderer_delta.py
│       ├── _renderer_format.py
│       ├── _renderer_html.py
│       ├── _renderer_mermaid.py
│       └── _renderer_time.py
└── time_parser.py
```

### Tests

```text
tests/
├── guardrails/test_audit_rendering_structure.py
├── guardrails/test_src_public_symbol_preservation.py
├── test_audit_renderer.py
└── unit/audit/
    ├── test_audit_analysis_ops.py
    ├── test_renderer_format_wave9.py
    └── test_renderer_time_wave9.py
```

## Complexity Tracking

The refactor adds no decision branch. Each moved module keeps its existing
cyclomatic complexity. The new structure guard holds one inspector class with
bounded methods.

## Risks and Mitigations

- **Risk**: An active file keeps an old renderer path and breaks at runtime.
  **Mitigation**: The focused structure guard scans each tracked active file and
  reports every violating path.
- **Risk**: The move loses a module-level symbol.
  **Mitigation**: The public symbol-preservation guard compares each moved module
  against the baseline commit and reports each lost name.
- **Risk**: A line exceeds the 120-character limit after the longer import path.
  **Mitigation**: Ruff and Black run on each changed file before the commit.

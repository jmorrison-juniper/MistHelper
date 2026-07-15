# Implementation Plan: Test Quality Analysis Engine

**Branch**: `1019-test-quality-analyzer` | **Date**: 2026-07-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/1019-test-quality-analyzer/spec.md`

## Summary

Build a Python-only, AST + filesystem based static analyzer at `tools/test_quality_analyzer/`
that audits the MistHelper test suite and emits a deterministic JSON report plus a
Markdown summary. It classifies findings across five detection categories (untested
modules, weak assertions, missing failure-mode coverage, missing edge-case coverage,
tautological tests), excludes the Mist Cloud API surface (`mistapi` imports and
`src/api/**`) from analysis, and supports a JSON baseline for gate mode with exit
codes 0/1/2. The engine ships with a golden regression set anchored on real
MistHelper findings and a synthetic bad/good fixture library with meta-tests. No
CI wiring in this feature; gate-mode CLI is shipped so a follow-up initiative can
wire it in trivially. Full-repo run must complete in under 60 seconds.

## Technical Context

**Language/Version**: Python 3.13 (matches project constitution binding minimum).

**Primary Dependencies**:
- Standard library only for the engine core: `ast`, `pathlib`, `tomllib`, `json`,
  `argparse`, `logging`, `dataclasses`, `re`, `sys`, `os`.
- Test-time only: `pytest` (already in project dev dependencies) for the engine's
  own meta-tests and golden regression tests.
- No third-party runtime dependencies. No `jsonschema` runtime dependency — the
  engine emits a JSON Schema document but validates its own output using an
  inline hand-rolled validator (avoids adding a dependency for one use).

**Storage**:
- Input: repository filesystem (source under `src/**`, tests under `tests/**`).
- Output: `tools/test_quality_analyzer/output/report.json`,
  `tools/test_quality_analyzer/output/summary.md`
  (directory git-ignored per Clarification Q4).
- Config: `tools/test_quality_analyzer/config.toml` (committed).
- Baseline: `tools/test_quality_analyzer/baseline.json` (committed).
- Schema: `tools/test_quality_analyzer/report.schema.json` (committed).

**Testing**: `pytest` under `tests/tools/test_quality_analyzer/` for:
- Unit tests per rule (each detection rule tested in isolation).
- Fixture-based meta-tests over `tools/test_quality_analyzer/fixtures/{bad,good}/`.
- Golden-set integration test that runs the engine against the real repo and
  asserts the SC-002 findings are present.
- CLI/gate-mode tests using `tmp_path` and captured stdout/exit codes.

**Target Platform**: Any host that runs Python 3.13. Primary environments are
Windows 11 developer laptops and the GitHub Actions Linux runners used by the
container-build workflow. AST + filesystem only, so cross-platform behavior is
identical.

**Project Type**: Repo-internal CLI utility (invokable both as
`python -m tools.test_quality_analyzer` and as a plain script), mirroring the
existing `tools/refactor_analyzer/` and `tools/compliance_analyzer/` conventions.

**Performance Goals**: Full-repo analysis of ~190 test files under 60 seconds
on a developer laptop (SC-001). AST parsing dominates; target < 300 ms per file
on cold read.

**Constraints**:
- **Zero network I/O** during a run (SC-006). Verified in tests by monkey-patching
  `socket.socket` to raise if invoked during analysis.
- **Zero runtime imports of test modules** (FR-014). Only `ast.parse()` is used
  against test source text.
- **Deterministic output** (SC-005). Findings sorted by
  `(severity_rank_desc, category, file_path, line_number, rule_id)`.
  Timestamps in the report are ISO-8601 UTC captured once at run start and
  never mid-analysis; they are the *only* non-deterministic field and are
  omitted from the baseline payload (Clarification Q2).
- **ASCII-only log output** (Constitution Principle V).
- **Inline comments on every executable line** (Constitution Principle VI).
- **`logging.info` before / `logging.debug` after** every meaningful action
  (Constitution Principle VII), using `%s`-style formatting.
- **Five-Item Rule** (Constitution Principle I): max 5 params, 5 blocks, 25 lines
  per function, and no directory or class with more than five children.
- **Class-based architecture** (Constitution Principle II): every unit of
  functionality lives inside a semantically named class; no stray wrapper
  functions. Modules expose one primary class each.

**Scale/Scope**:
- ~190 analyzed test files, ~40 source modules under `src/`, plus `MistHelper.py`
  at the repo root (in scope). Approximate final analyzer code size is
  1,200-1,800 lines of Python spread across five modules under
  `tools/test_quality_analyzer/`, plus fixture files and tests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Five-Item Rule | PASS | Module tree kept to 5 children (see Structure). Every planned function ≤ 25 lines / ≤ 5 blocks / ≤ 5 params. Where the natural rule count (5 detection rules) matches the ceiling, no additional detectors will be added without extracting a sub-package. |
| II. Class-Based Architecture | PASS | Every module hosts one primary class (`ConfigLoader`, `TestFileDiscoverer`, `MistApiExcluder`, per-rule `*Detector` classes, `ReportBuilder`, `MarkdownRenderer`, `BaselineDiffer`, `TestQualityCLI`). No wrapper functions. |
| III. Safety-First | PASS | Engine has no interactive input, no destructive operations. CLI flags are validated with `argparse` choices and existence checks before use. Path arguments are resolved and rejected if they escape the repo root. |
| IV. Full Deployment Pipeline | N/A for design phase | The engine is a repo-internal tool; the container-build pipeline is not triggered by tool-only changes. Deployment gate is: syntax check, `pytest`, `ruff`, `black` prior to commit. |
| V. Observability & Logging | PASS | ASCII-only log messages. `logging.info` before every phase (discover, parse, detect, render), `logging.debug` after with counts. `%s` formatting throughout. Structured summary line at end of run. |
| VI. Inline Comments | PASS | Enforced during implementation — every executable line receives a same-line comment explaining intent. Reviewed at PR time. |
| VII. Action Logging | PASS | Every meaningful action (config load, discovery, parse, detect, render, write) is bracketed by `info` before / `debug` after. |
| Complexity Escalation | PASS | This feature spans >3 files and introduces new architecture, so SpecKit is the correct workflow (spec + plan + tasks already produced). |

No constitutional violations — Complexity Tracking section left empty.

## Project Structure

### Documentation (this feature)

```text
specs/1019-test-quality-analyzer/
├── spec.md                # Feature specification (already written)
├── plan.md                # This file
├── research.md            # Phase 0 research and decisions
├── data-model.md          # Phase 1 entity definitions
├── quickstart.md          # Phase 1 validation guide
├── contracts/             # Phase 1 interface contracts
│   ├── cli.md             # CLI surface (flags, exit codes, examples)
│   ├── report.schema.json # JSON Schema for report.json
│   └── config.schema.md   # TOML config shape
├── checklists/            # (already present)
└── tasks.md               # /speckit.tasks output (NOT created here)
```

### Source Code (repository root)

```text
tools/test_quality_analyzer/
├── __init__.py              # Package marker + version string.
├── __main__.py              # `python -m tools.test_quality_analyzer` entrypoint;
│                            #   defines TestQualityCLI class.
├── config.py                # ConfigLoader class (TOML parse + validation).
├── discovery.py             # TestFileDiscoverer + MistApiExcluder classes.
├── detection/               # Sub-package for detection rules (keeps top-level to 5).
│   ├── __init__.py
│   ├── untested.py          # UntestedDetector.
│   ├── weak_assertion.py    # WeakAssertionDetector.
│   ├── failure_mode.py      # MissingFailureModeDetector.
│   ├── edge_case.py         # MissingEdgeCaseDetector.
│   └── tautological.py      # TautologicalTestDetector.
├── reporting.py             # ReportBuilder + MarkdownRenderer classes.
├── baseline.py              # BaselineDiffer class.
├── config.toml              # Committed default configuration.
├── baseline.json            # Committed baseline (initially populated post-first-run).
├── report.schema.json       # Committed JSON Schema for report.json.
├── output/                  # Git-ignored; created on first run.
│   ├── report.json
│   └── summary.md
└── fixtures/                # Synthetic fixture library for meta-tests.
    ├── bad/                 # One file per detection category.
    │   ├── test_untested_source_module_source.py  # Fixture "source under test".
    │   ├── test_weak_assertion_bad.py
    │   ├── test_failure_mode_bad.py
    │   ├── test_edge_case_bad.py
    │   └── test_tautological_bad.py
    └── good/
        ├── test_weak_assertion_good.py
        ├── test_failure_mode_good.py
        ├── test_edge_case_good.py
        ├── test_tautological_good.py
        └── test_untested_good.py

tests/tools/test_quality_analyzer/
├── __init__.py
├── conftest.py                     # Shared fixtures + repo-root discovery.
├── test_config_loader.py           # Unit tests for ConfigLoader.
├── test_discovery.py               # Unit tests for TestFileDiscoverer + MistApiExcluder.
├── test_detectors.py               # Unit tests per detector (parametrized).
├── test_baseline_differ.py         # Baseline round-trip + gate exit codes.
├── test_reporting.py               # ReportBuilder determinism + MarkdownRenderer output.
├── test_cli.py                     # End-to-end CLI test (tmp_path + captured exit code).
├── test_meta_fixtures.py           # Meta-tests over fixtures/bad/ and fixtures/good/.
└── test_golden_repo.py             # Golden regression: run engine against real repo,
                                    #   assert SC-002 findings present.
```

**Structure Decision**: Single-package repo-internal CLI utility placed at
`tools/test_quality_analyzer/` per Clarification Q1 and FR-020. Top-level
module count is exactly five (`__init__`, `__main__`, `config`, `discovery`,
`reporting`, `baseline`) — the five detection rules are grouped inside a
`detection/` sub-package so the top level stays within the Five-Item Rule.
Tests live under `tests/tools/test_quality_analyzer/` and mirror the analyzer
package tree. The `output/` directory is created lazily on first run and is
added to the repo `.gitignore`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. Table intentionally left empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

## Phase Outputs

### Phase 0 — research.md

Consolidated decisions covering AST parsing strategy, config format tradeoffs,
baseline canonicalization, JSON schema authoring approach, determinism strategy,
Mist-API exclusion predicate design, edge-case heuristic scope, and performance
budget allocation. All NEEDS CLARIFICATION items are resolved by the five
clarifications already recorded in `spec.md`; `research.md` records the
supporting rationale so implementation does not have to re-derive it.

### Phase 1 — data-model.md, contracts/, quickstart.md

- `data-model.md` — dataclass definitions for `Finding`, `Report`, `Baseline`,
  `Config`, `ExclusionDecision`, plus enums for `Severity` and `Category`.
- `contracts/report.schema.json` — JSON Schema (Draft 2020-12) that report.json
  must validate against (FR-011).
- `contracts/cli.md` — CLI surface documentation: flags, exit codes, invocation
  examples (FR-013).
- `contracts/config.schema.md` — TOML config table shape with defaults
  (FR-021, Clarification Q5).
- `quickstart.md` — maintainer validation guide: how to run the engine, how to
  interpret the report, how to (re)generate the baseline, how to run the
  meta-tests, and what SC-001 through SC-009 checks look like on the CLI.

### Post-Phase-1 Constitution Re-check

Re-evaluated after Phase 1 artifacts are drafted; no new violations introduced.
The `detection/` sub-package keeps the top-level directory at five children.
All dataclasses in `data-model.md` are frozen where read-only and use full-word
attribute names. CLI class remains under 25 lines per method.

## Deferred to /speckit.tasks

The following decisions are intentionally left for the tasks phase (they are
sequencing / dependency questions, not design questions):

1. **Detector implementation order** — which of the five detectors to build
   first. Recommendation is `UntestedDetector` and `WeakAssertionDetector`
   first because they anchor the P1 golden set; final ordering picked in
   tasks.md.
2. **Fixture authoring vs detector-first ordering** — whether to write each
   bad/good fixture before or after its detector. Both TDD orderings are
   viable; tasks.md picks one.
3. **Baseline seeding task** — the concrete task to run the engine once
   post-integration and commit the resulting `baseline.json`. This is a
   single follow-up task after all detectors are green.
4. **Repo-`.gitignore` edit task** — trivial one-line edit but should have
   its own task so it is not forgotten.
5. **`pyproject.toml` script entrypoint** — whether to expose the CLI via a
   `[project.scripts]` entry. Recommendation is yes (`test-quality-analyzer`)
   but this is a small polish task.

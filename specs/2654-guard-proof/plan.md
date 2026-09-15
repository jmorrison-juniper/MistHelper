# Implementation Plan: Guard Proof Enforcement

**Branch**: `chore/2654-guard-proof` | **Date**: 2026-09-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs\2654-guard-proof\spec.md`

## Summary

Add one enforced rule for guard code. A new or changed guard must prove that it
measured at least one path, and it must prove one failing path. A required guard
fails when it cannot read input. An environmental skip stays valid only when it
prints the reason.

The enforcement is a small repository analyzer in `tools\guard_proof_audit.py`.
It statically reads guard test files and rejects files whose tests all skip
unconditionally. Static analysis is the smallest mechanism that catches the live
issue #2689 pattern without running the full suite or needing credentials.

## Technical Context

**Language/Version**: Python 3.13+.

**Primary Dependencies**: Standard library only. The implementation uses `ast`,
`argparse`, `dataclasses`, `logging`, and `pathlib`.

**Storage**: Not applicable. The feature adds no persistent state.

**Testing**: `pytest`, `ruff`, `black`, and `mypy`.

**Target Platform**: Windows local development and Linux CI.

**Project Type**: Single-project Python repository.

**Performance Goals**: The audit completes in under one second on the current
guard file set.

**Constraints**:

- Do not edit frozen vendor API records under `documentation\api\` or the two
  OpenAPI files.
- Do not repair issue #2689 in this pull request.
- Keep known issue #2689 visible without blocking unrelated work.
- Use `pathlib.Path` for file paths.
- Keep log text ASCII only.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance | Notes |
| - | - | - |
| I. Five-Item Rule | PASS | The change adds one tool module, one guardrail test file, three spec files, and one release note. |
| II. Class-Based Architecture | PASS | `GuardProofAuditor` and `GuardProofCli` own the new behavior. |
| III. Safety-First | PASS | No new input prompt, secret, destructive operation, or network call exists. |
| IV. Full Deployment Pipeline | PASS BY PLAN | Local gates, commit, push, pull request checks, and CodeQL are planned. |
| V. Observability & Logging | PASS | The auditor logs each scan, parse, and result summary. |
| VI. Inline Comments | PASS BY PLAN | New executable Python lines include inline comments. |
| VII. Action Logging | PASS | The analyzer logs before and after meaningful actions. |

## Project Structure

### Documentation (this feature)

```text
specs\2654-guard-proof\
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code (repository root)

```text
.github\
├── PULL_REQUEST_TEMPLATE.md
├── copilot-instructions.md
└── instructions\
    └── git-flow-multi-agent.instructions.md

documentation\
└── CONTRIBUTING-MistHelper.md

tools\
└── guard_proof_audit.py

tests\
└── guardrails\
    └── test_guard_proof_audit.py

changelog.d\
└── issue-2654-guard-proof.md
```

**Structure Decision**: Put the analyzer under `tools\` because it is a
repository guard, not runtime product code. Put enforcement tests under
`tests\guardrails\` because this directory already holds repository policy
tests.

## Complexity Tracking

No constitution violation exists.

## Phase 0 Research

Issue #1924 shows the parent defect shape. A failure path erased its evidence.
Issue #2654 applies that shape to guard code. Pull request #2591 returned early
when a shallow checkout hid merge parents. Pull request #2611 closed a reopened
issue from a schedule. Pull request #2618 read only old timeline events.

Issue #2689 is the current worked example. The SDK compatibility test file uses
a module-level unconditional skip, so all seven tests skip. The suite reports
green although no SDK compatibility behavior ran.

The selected enforcement reads test source with `ast`. It flags module-level
`pytest.mark.skip` and guard files where every test uses an unconditional skip.
It does not flag `pytest.importorskip` or `pytest.mark.skipif`, because those
forms state an environmental condition and can still have a measured path.

## Phase 1 Design

`GuardProofAuditor` reads candidate guard files. A candidate is a pytest file
under `tests\guardrails\`, or a test file whose name contains `guard` or
`compatibility`.

The analyzer returns two finding classes.

- An active finding blocks the merge.
- A known finding prints its issue number and does not block this pull request.

The baseline has one known finding:
`tests\integration\test_mistapi_sdk_compatibility.py`, tracked by issue #2689.

## Validation Plan

Run these local gates.

```powershell
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
python -m pytest tests\guardrails\test_guard_proof_audit.py -v
python -m tools.guard_proof_audit --include-known
```

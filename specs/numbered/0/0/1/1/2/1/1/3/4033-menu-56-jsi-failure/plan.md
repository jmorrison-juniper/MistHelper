# Implementation Plan: Menu 56 Delay Metrics Integrity

**Branch**: `jmorrison-juniper-fix-4033-menu-56-jsi-failure` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/numbered/0/0/1/1/2/1/1/3/4033-menu-56-jsi-failure/spec.md`

## Summary

Repair the delay metrics writer in `rate_limiting.py`.
Use one process lock for the complete read-modify-write cycle.
Write complete JSONL content to a same-directory temporary file.
Replace the destination with `os.replace` only after the temporary write completes.

Add a deterministic concurrent-writer test before the source repair.
The first red run must capture `File I/O: Failed to read data/delay_metrics.json`.
The final tests must prove complete-row preservation, empty-file recovery, destination integrity, and temporary-file cleanup.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Primary Dependencies**: Python standard library `json`, `logging`, `os`, `tempfile`, and `threading`

**Storage**: A capped JSONL history at `data/delay_metrics.json`

**Testing**: pytest, `unittest.mock`, thread events, and temporary directories

**Target Platform**: Windows 11, macOS, Linux, and the Podman product container

**Project Type**: Python command-line application with web portal callers

**Performance Goals**: Serialize only delay history persistence and retain the existing 100-row default cap

**Constraints**: Preserve the row shape, retention rules, caller behavior, and nonfatal write-error behavior

**Scale/Scope**: One source module, one unit test module, and one unique changelog fragment

## Constitution Check

*GATE: Passed before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Result | Plan evidence |
| --- | --- | --- |
| Five-Item Rule | Pass with process-record exception | The implementation adds no package child. Required Spec Kit artifacts use the managed numeric route. |
| Class-Based Architecture | Pass | The repair remains in `RateLimitingUtils`. No wrapper or compatibility path is added. |
| Safety-First | Pass | The change does not add input, a destructive action, a Mist request, or a credential path. |
| Full Deployment Pipeline | Pass with user controls | The branch rebases before one force-with-lease push. The pull request remains draft and has no auto-merge. |
| Observability | Pass | Each expected exception is narrow, bound to a name, and used in an ASCII log message. |
| Inline Comments | Pass | Each changed executable source line receives an inline cause-and-purpose comment. |
| Action Logging | Pass | The write cycle retains failure logs and adds useful success and cleanup logs where required. |

The feature directory has more than five direct children after required Spec Kit generation.
The constitution permits required unique process records in an established process folder.
The separate remediation action is to revise the shared Spec Kit template structure in another issue.

No Juniper Mist Cloud request changes.
No owned WebSocket transport changes.
No product output moves outside `data/`.

### Post-design re-check

The data model keeps the existing JSONL row contract.
The persistence contract defines one lock boundary and one atomic replacement boundary.
The quickstart proves the feature without any production credential.
No constitution violation needs a product-code exception.

## Project Structure

### Documentation for this feature

```text
specs/numbered/0/0/1/1/2/1/1/3/4033-menu-56-jsi-failure/
├── checklists/
│   └── requirements.md
├── contracts/
│   └── delay-history-persistence.md
├── data-model.md
├── plan.md
├── quickstart.md
├── research.md
└── spec.md
```

### Implementation scope

```text
src/foundation/support/utils/
└── rate_limiting.py

tests/unit/
└── test_rate_limiting.py

changelog.d/
└── issue-4033-menu-56-jsi-failure.md
```

**Structure Decision**: Keep the repair in the existing rate-limit utility.
Keep all behavior tests in its existing unit test module.
Add only the unique issue fragment for user-visible behavior.

Do not modify `web_portal/services/operation.py`.
Do not modify `.specify/feature.json`.
Do not add another implementation file.

## Phase 0: Research Decisions

The decisions are in [research.md](research.md).

1. Use one module-level `threading.Lock` as the process-wide synchronization boundary.
2. Hold the lock from the destination read through replacement or cleanup.
3. Use a named temporary file in the destination directory.
4. Close the complete temporary file before `os.replace`.
5. Use thread events and a controlled write handle for the red proof.
6. Use narrow exception groups and use each bound exception in a log message.

## Phase 1: Design and Contracts

- [data-model.md](data-model.md) defines the destination, row, lock, and temporary-file states.
- [contracts/delay-history-persistence.md](contracts/delay-history-persistence.md) defines the persistence behavior.
- [quickstart.md](quickstart.md) defines the red, green, quality, and delivery checks.

The agent-context update is not run.
That script writes outside this feature directory, which the user prohibited.

## Implementation Sequence

1. Add the final concurrent-writer test to `tests/unit/test_rate_limiting.py`.
2. Coordinate the writers without an unbounded sleep.
3. Run only the new test against the current source.
4. Record the red result and the exact required warning.
5. Do not edit `rate_limiting.py` until the red proof exists.
6. Add one process-wide lock in `rate_limiting.py`.
7. Hold the lock for the complete read-modify-write cycle.
8. Treat a missing or zero-byte destination as empty history.
9. Create one named temporary file beside the destination.
10. Write every retained JSONL row completely to the temporary file.
11. Close the temporary file before replacement.
12. Call `os.replace` only after the full temporary write succeeds.
13. Remove the temporary file after every failed write or replacement.
14. Leave the previous destination unchanged when replacement fails.
15. Keep successful writes free of temporary files.
16. Bind only expected exceptions and use each bound value in its log.
17. Add tests for replacement failure, cleanup, empty history, and retention.
18. Add `changelog.d/issue-4033-menu-56-jsi-failure.md`.
19. Run the target tests and the applicable repository gates.

## Verification and Delivery Controls

Run these checks before the rebase:

```powershell
python -m pytest tests\unit\test_rate_limiting.py
python -m py_compile src\foundation\support\utils\rate_limiting.py
python -m mypy src\foundation\support\utils\rate_limiting.py --config-file pyproject.toml
python -m ruff check .
python -m black --check .
```

The Ruff and Black checks must cover the full repository tree.
Do not replace them with changed-file checks.

Build the explicit feature manifest with only these implementation files:

```text
src/foundation/support/utils/rate_limiting.py
tests/unit/test_rate_limiting.py
changelog.d/issue-4033-menu-56-jsi-failure.md
```

Commit the verified manifest with a Conventional Commit message.
Fetch `origin/main`, then rebase the committed branch before any push.
Repeat the target tests, Ruff, and Black after the rebase.

Push exactly once with `--force-with-lease`.
Do not use `--force`.
Do not add the `auto-merge` label.
Do not merge the pull request.

After the push, verify the pull request state:

```powershell
gh pr view --json isDraft,state,headRefName,headRefOid,labels,url
git rev-parse HEAD
```

The verification must show `isDraft` as `true`.
The state must be `OPEN`.
The remote head object ID must equal local `HEAD`.
The labels must not include `auto-merge`.

## Complexity Tracking

No product-code violation is planned.
The required Spec Kit direct children use the constitution process-record exception.

# Implementation Plan: Capture reads report a lost page

**Branch**: `jmorrison-juniper-capture-page-loss-reporting` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/3436-capture-page-loss/spec.md`.

## Summary

Use the existing checked `read_every_page` walk at all five required surfaces.
Preserve available records and the failed page status.
Carry wireless reasons through the real collector and tier 3 reasons through the existing extra sections.
Do not compare `X-Page-Total` against row counts.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: The declared `mistapi` 0.64 SDK, `requests`, and standard-library types.
No dependency change is necessary.

**Storage**: No store or schema change.
The tests build the final capture without a store call.

**Testing**: Native `APIResponse` objects from read-only `tests/support/sdk_pages.py`, pytest, and branch coverage.

**Target Platform**: The existing host and container platforms.
This validation uses an isolated macOS worktree.

**Project Type**: A repair to existing internal readers.

**Performance Goals**: Keep one initial endpoint call and one native `mist_get` call for each requested later page.

**Constraints**: No publication, live cloud, production store, container, browser, or firmware operation.
Preserve endpoint arguments and decision policy.

**Scale/Scope**: Five read surfaces in five existing source files.
The port source feeds both `switch_ports` and `poe`.

## Constitution Check

| Principle | Result |
| - | - |
| Structural discipline | Use existing source children. Place new tests in feature packages with at most five direct files. |
| Class-based design | Reuse the existing typed paged result. Do not introduce wrapper aliases or a second pagination implementation. |
| Safety | Keep writes, confirmations, settle rules, and numeric-input policy unchanged. Require human review. |
| Local gates | Run the applicable configured gates before the local commit. Publication remains expressly prohibited. |
| Observability | Name the lost section, real status, and retained record count. Do not log response bodies or exception text. |
| Documentation | Describe only the related reader behavior in this feature and its unique release note. |

The current capture modules exceed the structural limits.
The fleet reader also exceeds 25 physical lines, including documentation and its existing call construction.
This repair does not expand unrelated logic.
An independent later refactor can move these readers into semantic classes.
That refactor does not belong to issue #3436.

The application owns this branch.
The normal SpecKit branch hook cannot replace it.
The attempted PowerShell hook failed because `pwsh` is unavailable.
Use the current templates and feature-only completion records instead.
Do not change `.specify/feature.json`, shared agent context, or shared hook state.
Optional automatic commits remain disabled for this bounded local workflow.

The unchanged bootstrap reproduced issue #3701.
Its copied Python executable died with `SIGABRT` during `ensurepip`.
Recover only the ignored environment of this worktree with UV seeds, copy mode, and system certificates.
Do not change the bootstrap or another checkout.

## Project Structure

### Documentation (this feature)

```text
specs/3436-capture-page-loss/
  spec.md
  plan.md
  tasks.md
  .spec-context.json
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/readers.md
    checklists/requirements.md
```

### Source Code (repository root)

| Exact source path | Required change |
| - | - |
| `src/upgrade_portal/capture/devices.py` | Make `_read_group` use the checked walk. Keep row copying inside the error boundary. Preserve earlier valid pages after transport or record faults. |
| `src/upgrade_portal/capture/clients.py` | Make the wireless statistics branch of `_collect` carry records and reasons. Keep the three loud map reads unchanged. Keep `page_limit` byte unchanged. |
| `src/upgrade_portal/capture/collector.py` | Read the actual wireless result records and reasons before final assembly. Keep concurrency, lifecycle, section naming, and client normalization unchanged. |
| `src/upgrade_portal/capture/extras.py` | Replace `_paged` fallback success with the checked walk. Carry partial status and retained rows into every actual extra section. |
| `src/upgrade_portal/upgrade/gate.py` | Use the checked walk inside `read_fleet_statistics`. Keep reading conversion inside its error boundary. Change no settle decision. |

**Structure Decision**: Reuse `DeviceRead` for the checked raw wireless read.
The type already carries the needed section, records, and reasons.
A late import avoids the existing `devices` to `clients` import cycle.
The three map client reads retain their list interface.
The wireless statistics reader returns the typed result.
Existing injected row-list sources remain an explicit supported test seam.
The collector extracts the real typed rows and adds the real reasons.
The direct wireless client reader must not silently discard a partial result.

New test packages:

- `tests/unit/upgrade_portal/capture_page_loss/`
- `tests/contract/upgrade_portal/capture_page_loss/`

Update only the reserved existing reader tests when their former `get_all` stand-ins become obsolete.
The released `tests/unit/upgrade_portal/test_rehearsal_cascade.py` now checks actual walk and conversion traces.
Its native cases prove positive later-page counts and exact fleet reasons.
The existing cascade tests retain every schedule and settle assertion.
`tests/support/sdk_pages.py` stays read-only.
`assembly.py`, global E2E fixtures, entrypoints, firmware write services, dependencies, and gate settings stay unchanged.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| Existing oversized reader modules | The issue requires their actual reader boundaries. | A broad class migration adds unrelated risk and crosses other ownership reservations. |
| Existing oversized fleet reader | Its endpoint construction and settle-related documentation already exist. | Moving settle behavior is outside this evidence-only repair. |
| Normal SpecKit hook unavailable | `pwsh` is absent, and branch changes belong to the application. | Creating a second branch violates the current session contract. |

## Design and Validation

[Research](design/research.md) records the chosen reader contracts.
[The data model](design/data-model.md) records result shapes.
[The reader contract](design/contracts/readers.md) names every actual caller.
[The validation guide](design/quickstart.md) defines red, green, and negative proofs.

Measure changed statements and branches separately from whole-module coverage.
Confirm that all new result-handling regions appear in the coverage data.
Run the existing capture, gate, collector, client, extras, contract, and integration selections.
Record any named environment or opt-in skips separately.

Use the exact configured compile, Ruff, Black, mypy, Bandit, complexity, and documentation checks.
Run the required input preflight before test-quality analysis.
After the local commit, run the clean committed-scope analyzer against the exact fetched intended base.
If the SDK predicate excludes tests, also run the explicit scope with `--include-mist-api`.
Do not change thresholds, baselines, exclusions, or suppressions.

# Data Model: MistHelper.py Suppression Cleanup

**Feature**: `specs/1016-misthelper-suppression-cleanup/`

**Date**: 2026-07-13

## Purpose

Record the concrete shape of the four operational entities the workflow touches. This workflow has no runtime data schema; the "data model" here is the set of source-code artifacts each Story produces or freezes.

Every entity below carries: a concrete shape, the validation rule that determines success, and the Story that owns it.

---

## 1. `__all__` list (owned by Story 1 / Issue #895)

### Concrete shape

A module-level assignment in `MistHelper.py`:

```python
__all__: list[str] = [
    # -- from src.analytics --
    "AnalyticsSubsystemA",
    "AnalyticsSubsystemB",
    # -- from src.api --
    "ApiClient",
    # ... one entry per re-exported name, grouped by source subsystem ...
]
```

The list is grouped by the `src/` subsystem the name originates from, with a same-line comment header before each subsystem block. Ordering within a subsystem is alphabetical. The concrete list is enumerated by:

1. Running `python -c "import MistHelper; print('\n'.join(sorted(n for n in dir(MistHelper) if not n.startswith('_'))))"` at workflow start.
2. Filtering to names imported from `src/` (i.e., excluding names defined in `MistHelper.py` itself, unless they are part of the frozen public API per `contracts/public_api.md`).

The precise inventory is captured in `contracts/public_api.md`; `__all__` MUST be equal to (or a strict superset of) that inventory.

**Hoist decision**: Inline in `MistHelper.py` by default. Hoisted to `src/_bootstrap.py` only if the Phase 0 threshold (≥ 20 additional suppressions removable) is met per `research.md` §4.

### Validation rules

- Every name in `__all__` MUST be an attribute of the `MistHelper` module at import time (import-time smoke test).
- Every name currently accessible via `from MistHelper import <name>` at workflow start MUST appear in `__all__` (SC-007 preservation).
- No name in `__all__` may be prefixed with `_` (dunders excepted only where legacy public API includes them, which per current audit it does not).

---

## 2. Facade Global → Protocol mapping (owned by Story 4 / Issue #898)

### Concrete shape

For each Any-typed module-level attribute in `MistHelper.py` currently exposed to callers, a Protocol class is defined in `src/utils/misthelper_facade.py`:

```python
# src/utils/misthelper_facade.py
from typing import Protocol

class <FacadeName>Protocol(Protocol):
    def <method_1>(self, arg: <type>) -> <return_type>: ...
    def <method_2>(self, arg: <type>) -> <return_type>: ...
```

The mapping table is populated during Story 4 preparation:

| Facade Global (attribute in `MistHelper.py`) | Protocol class name | Methods on Protocol | Call sites in `MistHelper.py` |
|----------------------------------------------|---------------------|---------------------|-------------------------------|
| *(to be populated during Story 4 preparation from fresh audit)* | | | |

The full method-signature contract for each Protocol is captured in `contracts/misthelper_facade_protocols.md`.

### Validation rules

- **Exact coverage**: each Protocol MUST list exactly the methods `MistHelper.py` calls on the corresponding facade global — no more, no less (Story 4 Acceptance Scenario 3).
- **Signature fidelity**: method signatures on the Protocol MUST match the underlying implementation exactly, so no covariance / contravariance surprises appear at type-check time.
- **No implementation coupling**: `MistHelper.py` references only the Protocol type, not any concrete subsystem class.

---

## 3. Helper extraction boundaries (owned by Story 3 / Issue #901)

### Concrete shape

For each of the three complexity-flagged symbols, enumerated helpers with name, one-line purpose, and target size:

**`GlobalImportManager`** — extract helpers so the main method stays under `C901` threshold:

| Helper name (proposed) | Purpose | Target LOC |
|------------------------|---------|-----------:|
| `_resolve_import_target` | Look up the target module/name for a given legacy alias. | ≤ 25 |
| `_install_into_namespace` | Bind the resolved target into the module namespace. | ≤ 25 |
| `_record_import_diagnostics` | Emit the info/debug logging pair around each install. | ≤ 25 |

**`DeviceFetchConfig`** — reduce `PLR0913` by grouping construction arguments:

| Helper name (proposed) | Purpose | Target LOC |
|------------------------|---------|-----------:|
| `_from_dict_args` | Build the config from a dict-shaped source (menu path). | ≤ 25 |
| `_validate_config` | Validate normalized fields per constitution safety-first pattern. | ≤ 25 |

**`main()`** — extract per-menu-phase helpers so `main()` is a thin orchestrator:

| Helper name (proposed) | Purpose | Target LOC |
|------------------------|---------|-----------:|
| `_parse_cli_args` | Wrap argparse invocation with logging. | ≤ 25 |
| `_bootstrap_subsystems` | Call `GlobalImportManager` once and record readiness. | ≤ 25 |
| `_dispatch_menu` | Route to the appropriate menu handler; single-return exit. | ≤ 25 |

The proposed names above are recommendations; final helper names are settled by Story 3 during implementation and MUST be reflected back into this file before Story 3 merge.

### Validation rules

- Public signatures of `GlobalImportManager`, `DeviceFetchConfig`, and `main()` MUST NOT change (Story 3 Acceptance Scenario 2).
- Every extracted helper MUST have at least one direct unit test invoked from the existing `tests/` tree (Story 3 Independent Test).
- Every helper MUST fit under constitution Principle I's 25-LOC ceiling.
- Every helper MUST carry inline comments and before/after action logging per constitution Principles VI and VII.

---

## 4. `subprocess_runner` surface (owned by Story 7 / Issue #900, conditional)

### Concrete shape

Introduced only if the Phase 0 threshold is met (≥ 3 remaining subprocess call sites in `MistHelper.py`). If introduced:

```python
# src/utils/subprocess_runner.py
import subprocess  # single audited import in the repo for MistHelper.py's sites
from typing import Sequence

class SubprocessRunner:
    ALLOWED_EXECUTABLES: frozenset[str] = frozenset({
        # populated during Story 7 audit
    })

    @classmethod
    def run(
        cls,
        argv: Sequence[str],
        *,
        timeout: float,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Validate and dispatch. Rejects unknown executables and shell metacharacters."""
```

Full contract in `contracts/subprocess_runner.md`.

### Validation rules

- Every element of `argv` MUST be validated against the allow-list (index 0) or a strict character set (remaining indices) before `subprocess.run` is invoked.
- No caller may pass `shell=True`; the parameter is not surfaced.
- Unit test coverage ≥ 90% (Story 7 Acceptance Scenario 3).
- Inline comments and before/after action logging per constitution Principles VI and VII.

---

## State transitions

There are no runtime state transitions in this workflow. The "state" that changes is source-code hygiene, measured externally by the suppression-count delta captured in `research.md` §2 and refreshed by `tools/refactor_analyzer/` between stories per FR-014 / FR-015.

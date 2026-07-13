# Contract: `src/utils/misthelper_facade.py` Protocol Classes

**Feature**: `specs/1016-misthelper-suppression-cleanup/`

**Owning Story**: Story 4 / Issue #898

**Date**: 2026-07-13

## Purpose

Define the Protocol classes that describe the call surface `MistHelper.py` uses on its facade globals. Once these Protocols exist, `MistHelper.py` can type-annotate its references so mypy resolves the calls without `# type: ignore[no-untyped-call]`.

## File location and structure

```
src/utils/misthelper_facade.py
```

If the file does not exist at Story 4 start, it is created; the file is one of only two permitted `src/` additions in this workflow per FR-012 (the other is `src/utils/subprocess_runner.py`).

The file contains only Protocol class definitions and their supporting `TypeAlias` or `TypeVar` declarations. It does NOT import from `MistHelper.py` (would create a cycle) and does NOT import concrete subsystem classes (would defeat the facade indirection).

## Protocol enumeration

The complete list is populated during Story 4 preparation from the fresh audit. Template per Protocol:

```markdown
### `<FacadeName>Protocol`

**Backing facade global**: `MistHelper.<attribute_name>`

**Call sites in `MistHelper.py`**: (list line numbers or symbol paths — this is a source-level contract note, not a stable citation)

**Methods**:

- `def <method_name>(self, <arg>: <type>, ...) -> <return_type>: ...`
  - Contract: <two-line note on what the caller expects>.

**Coverage note**: exact-match required — this Protocol MUST list every method `MistHelper.py` calls on this facade global, and MUST NOT list any method that is not called. Verify with a static grep of `MistHelper.py` for `<attribute_name>.` before Story 4 merge.
```

## Consumption pattern

In `MistHelper.py`, the facade global is annotated with the Protocol type at assignment:

```python
from src.utils.misthelper_facade import <FacadeName>Protocol

<attribute_name>: <FacadeName>Protocol = <concrete_construction>()
```

Once annotated, mypy resolves calls of the form `<attribute_name>.<method_name>(...)` without `# type: ignore[no-untyped-call]`, satisfying Story 4's independent test.

## Validation checklist (Story 4 PR review)

- [ ] `src/utils/misthelper_facade.py` exists and contains only Protocol classes plus their type-support declarations.
- [ ] Every Protocol lists exactly the methods `MistHelper.py` calls on its backing facade global (grep-verified).
- [ ] Every method signature on a Protocol matches the underlying implementation exactly.
- [ ] `MistHelper.py` imports the Protocol types and annotates every facade global.
- [ ] `mypy MistHelper.py --strict` reports zero `no-untyped-call` findings.
- [ ] Zero `# type: ignore[no-untyped-call]` comments remain in `MistHelper.py`.
- [ ] Constitution Principles VI and VII (inline comments, action logging) satisfied on any new/modified lines.

# Feature Specification: Exempt Third-Party Overrides from STRUCT-PARAMS

**Issue**: #1800
**Status**: In progress

## Problem

The compliance analyzer reports a high-severity `STRUCT-PARAMS` violation on `send` in
`MistHelper.py`:

```
| high | STRUCT-PARAMS | send | Function takes 6 parameters (limit 5). |
| Remediation: Group related parameters into a dataclass/config object.
```

That `send` overrides `requests.adapters.HTTPAdapter.send`, whose signature the library fixes:

```
requests.adapters.HTTPAdapter.send parameters (excluding self): 6
(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None)
```

`requests` calls the adapter with those exact keyword arguments. Applying the suggested
remediation would break the adapter contract and every HTTP call the tool makes. The source
already records the constraint:

```python
# Issue #431: forward args verbatim. The signature must match parent for adapter contract.
```

The five-parameter rule protects readability in code this project owns. It cannot apply to a
method whose shape a third-party base class dictates. No refactor can clear the finding, so it
persists on every report and trains readers to ignore the high-severity column.

## Requirements

- **FR-001**: Skip `STRUCT-PARAMS` for a method whose enclosing class has a third-party base.
- **FR-002**: Treat a base as third-party when its bound name comes from outside `src`, `tools`,
  `scripts`, `tests`, and `web_portal`, and is not a relative import.
- **FR-003**: Keep every other rule active on those methods, including length and complexity.
- **FR-004**: Leave `STRUCT-PARAMS` fully active for classes the repository owns.

## Non-goals

- **NG-001**: Do not exempt whole files or whole classes from all rules.
- **NG-002**: Do not resolve base classes across modules. Name binding in the file is enough for
  the cases that occur, and a cross-module resolver would be far more machinery than the problem
  warrants.

## Design

`analyze` computes the exempt set once per file, then threads it into `_check_function`, which
adds `STRUCT-PARAMS` to that function's `noqa` set. Reusing the existing suppression path avoids
a second filtering mechanism.

Base names resolve to their leftmost `Name`, so `requests.adapters.HTTPAdapter` binds through
`requests`. Nested classes are covered, because the real case declares the adapter inside a
function.

## Success criteria

- **SC-001**: The `send` finding disappears, taking `MistHelper.py` to zero high-severity.
- **SC-002**: `STRUCT-PARAMS` still fires repository-wide for first-party classes.
- **SC-003**: The repository-wide compliance score does not move, proving nothing else was hidden.
- **SC-004**: Unit tests cover the foreign, first-party, relative, dotted, nested, and no-import
  cases.
- **SC-005**: Every quality gate passes.

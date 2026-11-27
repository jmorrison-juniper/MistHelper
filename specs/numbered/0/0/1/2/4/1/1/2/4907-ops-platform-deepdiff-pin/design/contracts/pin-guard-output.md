# Interface Contract: Ops Platform Pin Guard Output

This contract covers the test method `test_ops_platform_pins_obey_declared_constraints` in `tests/guardrails/test_dependency_export.py`. The method has no command-line interface and writes no file.

## Inputs

| Input | Path | Required form |
|-------|------|---------------|
| Declared constraints | `mist-ops-platform/pyproject.toml` | A TOML file with a `project.dependencies` list of PEP 508 strings. |
| Pins | `mist-ops-platform/requirements.txt` | Lines in the form `name==version`. Other lines, such as comments, are ignored. |

Both inputs are read with `DependencyExport.read_export`. A missing or empty input fails with the existing message.

## Success output

When the guard runs with output enabled (`pytest -s`), it prints one ASCII line:

```text
ops platform pins: examined <N> pins, <M> defects
```

On main, `<N>` is 22 and `<M>` is 0. `<N>` counts each pin that has a declared constraint. A pin without a declared constraint is not counted.

## Failure messages

| Condition | Assertion message |
|-----------|-------------------|
| The guard examined zero pins | `The guard compared no ops platform pins` |
| One or more pins fall outside their declared constraints | `Ops platform pins outside declared constraints: <names>`, where `<names>` is a sorted, comma-separated list of canonical package names |
| The synthetic conflict is not reported | `The guard missed the synthetic conflict` |
| The synthetic replacement changes no text | `The synthetic conflict did not change the requirements text` |
| A required input is missing | `Requirements export not found: <file name>` |
| A required input is empty | `Requirements export is empty: <file name>` |

## Exit behavior

A failed assertion fails the test. Pytest then exits with a non-zero code, and the job `Dependency lock and exports` fails. A passed test exits with code 0. The guard never skips. It fails on each unreadable input.

# Dependency Export Contract

## Inputs and Outputs

- Leave `pyproject.toml` unchanged.
- `uv.lock` holds the resolved package versions and platform conditions.
- `requirements.txt` contains the runtime export.
- `requirements-dev.txt` contains the runtime and development exports.

## Invariants

1. The lock satisfies the package constraints.
2. Both exports match the output from `uv export --locked`.
3. The runtime export retains all 11 existing platform markers.
4. The development export contains the runtime dependencies and the `dev` extra.
5. A single-platform security audit does not claim coverage for other platform markers.
6. The audit identifies each dependency source that it cannot inspect.

## Generation Commands

```text
uv export --locked --no-hashes --no-emit-project --output-file requirements.txt
uv export --locked --no-hashes --no-emit-project --extra dev --output-file requirements-dev.txt
```

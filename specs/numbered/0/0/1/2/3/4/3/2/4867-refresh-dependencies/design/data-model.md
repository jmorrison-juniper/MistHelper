# Dependency Refresh Data Model

## Root Python Manifest

**Purpose**: Declares direct Python runtime and development dependencies.

**Validation**:

- Direct package names must match existing application imports.
- Exact development pins must match requirements-dev.txt.
- Supported package ranges must not exclude Python 3.15.

## Root UV Lock

**Purpose**: Resolves exact transitive versions for Python 3.15.

**Validation**:

- UV lock check must succeed.
- No package entry may omit a resolved version.
- Exported requirements must match the lock.

## Pip Exports

**Purpose**: Give pip-based CI and container installs exact package versions.

**Validation**:

- requirements.txt must contain runtime packages only.
- requirements-dev.txt must contain development and test packages.
- Direct exact pins must match pyproject.toml.

## Ops Platform Manifest

**Purpose**: Declares platform runtime and test dependencies.

**Validation**:

- Python 3.15 remains the interpreter floor.
- Exact runtime and test exports must resolve.
- The platform test suite must reach at least 56 percent coverage.

## Ops Portal Manifest

**Purpose**: Declares direct npm runtime and development dependencies.

**Validation**:

- package-lock.json must match package.json.
- npm ci must install the lock exactly.
- npm audit must have no high or higher advisory.

## Package Exception Record

**Purpose**: Records each package that does not advance to a current release.

**Validation**:

- The exception must name the package and current release.
- The exception must name the compatibility blocker.
- The exception must state the retained package constraint.

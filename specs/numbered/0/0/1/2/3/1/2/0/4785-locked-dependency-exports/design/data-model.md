# Data Model: Locked Dependency Exports

This feature changes package records and generated text exports. It adds no application data.

## Dependency Record

- **Name**: The canonical package name.
- **Version**: The selected version that satisfies project limits.
- **Markers**: The platform conditions that restrict package installation.
- **Dependencies**: The packages that require this record.

## Requirement Export

- **Runtime export**: The locked packages required by MistHelper.
- **Development export**: The locked runtime packages and development tools.
- **Relationship**: UV generates each export from the same lock.

## Validation Rules

- Each export matches the output generated from `uv.lock`.
- Each locked version satisfies the project declarations.
- Each export retains the platform markers from the lock.

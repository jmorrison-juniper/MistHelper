# Data Model: Runtime Dependency Refresh

This feature changes dependency records and their generated exports. It does not change application data or database schemas.

## Entities

### Requested dependency

- **Identity**: Package identity and requested version from `requirements.txt`.
- **Validation**: The resolved version must match the request.

### Locked package

- **Identity**: Package identity and resolved version in `uv.lock`.
- **Validation**: Required package identities, versions, sources, and platform conditions must remain valid.
- **Relationship**: A locked package satisfies a requested dependency or a transitive dependency.

### Dependency export

- **Identity**: Runtime export in `requirements.txt` or development export in `requirements-dev.txt`.
- **Validation**: Each export must match the dependency information in `uv.lock`.
- **Relationship**: Both exports derive from the same lock.

### Platform marker

- **Identity**: One existing platform condition in the dependency declarations.
- **Validation**: All 11 conditions must remain unchanged.
- **Relationship**: A marker controls whether a package applies to a supported platform.

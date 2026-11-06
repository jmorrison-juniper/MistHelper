# Research: Runtime Dependency Refresh

## Decisions

### Resolve the requested versions as one locked dependency set

- **Decision**: Record requested package versions and required transitive packages in `uv.lock`, then generate both exports from that lock.
- **Rationale**: One resolved set keeps installation inputs consistent.
- **Alternatives considered**: Editing each export separately. This can produce different package versions.

### Use the public package index when the machine mirror changes package identity

- **Decision**: Resolve from the public package index when the machine mirror rewrites lock identities.
- **Rationale**: The lock must retain the package identity requested by the project.
- **Alternatives considered**: Accepting rewritten identities from the machine mirror. This can change the resolved package source.

### Retain platform markers and allow required transitive packages

- **Decision**: Preserve all existing platform markers and include transitive packages required by the requested versions.
- **Rationale**: Platform conditions define supported installations. Required transitive packages complete the resolved set.
- **Alternatives considered**: Removing markers or omitting transitive packages. Either choice can make an installation incomplete.

## Parent-Reported Evidence

The parent reports 23 requested runtime updates, `tzdata2026.6` as a transitive package, and all 11 platform markers preserved.

The parent reports 107 retained pins, six replacements associated with `tzdata`, and a clean audit.

## Unresolved Questions

None. The package list and requested versions remain in the parent-owned dependency changes.

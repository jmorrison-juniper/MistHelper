# Research: Upgrade Mutation Routes

## Decision: Reuse the existing request provider

**Rationale**: Issue #3834 added `PortalRequestDependencies` and request teardown for the database router. The issue #3977 reassessment found that the provider does not yet supply the firmware service, comparison service, or run-action store. Extending this boundary avoids a second lifecycle owner.

**Alternatives considered**:

- Keep reading services from application configuration. This keeps the current process-wide dependency gap.
- Move all Phase 2 and Phase 3 installers. This expands the change into unrelated startup behavior.

## Decision: Build request-bound services only when a route needs them

**Rationale**: Each service must receive the current operator's Mist session and request-owned router. Lazy creation prevents a route from failing because an unrelated service is not available.

**Alternatives considered**:

- Build all mutation services for every request. This adds work and creates unrelated failure paths.
- Use one process-wide service instance. This can reuse a Mist session across operators.

## Decision: Keep the durable action store actor-scoped

**Rationale**: `ActionRepository` already stores actions in ArangoDB and filters records by actor scope. It holds no Mist session, so the provider can expose the same durable repository to each authenticated request.

**Alternatives considered**:

- Create a second action repository for each request. This duplicates store initialization and index work.
- Replace durable storage with a request-local store. This loses the action record after the request ends.

## Decision: Keep route contracts and startup installers stable

**Rationale**: The issue changes dependency access, not endpoint paths or service behavior. Existing global installers remain for consumers outside the mutation scope.

**Alternatives considered**:

- Change response shapes or route paths. No requirement supports that change.
- Rework all upgrade-portal startup wiring. The issue explicitly excludes unrelated startup work.

## Environment note

The repository's PowerShell setup command could not run because `pwsh` is not installed. The route was calculated from the repository's `Get-SpecRadixSegments` and `Resolve-SpecFeaturePath` logic. A direct check confirmed that the managed destination does not exceed the parent-child limit.

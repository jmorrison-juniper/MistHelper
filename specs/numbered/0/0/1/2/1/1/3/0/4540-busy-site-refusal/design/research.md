# Busy-site refusal research

**Decision**: Move the busy-refusal declaration out of the replay-refusal body.

**Rationale**: `sendOrgForm` calls the declaration from the outer script scope.
The nested declaration is unavailable there and raises a browser page error.

**Alternatives considered**: Calling the replay handler would conceal the scope defect and couple two separate refusal paths.
A new wrapper would add unnecessary behavior.

**Ownership**: The open-PR file query found no owner for `portal.js`.
PR #4541 owns the journey file but released that file through the user's scoped handoff.
Its workflow, fixtures, and parity records remain excluded.

**Hooks**: `.specify/extensions.yml` enables one mandatory hook, `speckit.git.feature`, before specification.
It completed in dry-run mode on the app-managed branch.
All commit hooks are optional. Companion hooks are disabled.

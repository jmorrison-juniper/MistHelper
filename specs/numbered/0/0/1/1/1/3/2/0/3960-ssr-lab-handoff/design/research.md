# Research: SSR lab runbook validation

## Source Authority

**Decision**: Use [issue #3960](https://github.com/jmorrison-juniper/MistHelper/issues/3960) as the six-observation source.
Use [issue #3959](https://github.com/jmorrison-juniper/MistHelper/issues/3959) for coordination.

**Rationale**: The issue supplies commands, release thresholds, destinations, and ownership restrictions.
The parent recorded the current artifact-only claim on 2026-10-14.

**Alternatives considered**: Starting another claim or inferring work from labels would duplicate ownership records.

## Current Documentation State

**Decision**: Preserve the existing verification-status table until measured evidence exists.

**Rationale**: [PR #4114](https://github.com/jmorrison-juniper/MistHelper/pull/4114) merged on 2026-10-10.
The runbook records all six observations as `Not run`.
Older issue comments that describe that pull request as open are stale.

**Alternatives considered**: Repeating the verification-status change would deliver no physical evidence.
Changing the protected verifier would violate the assignment.

## Release and Command Evidence

**Decision**: Separate SSR 7.0.x observations from the fiber-port observation on SSR 7.1.0-50r1 or later.

**Rationale**: The issue distinguishes a missing `name` keyword from an unsupported `optics-statistics` value.
It also distinguishes summary columns from unverified detailed Mist fields.
Only live sanitized output can settle these questions.

**Alternatives considered**: Vendor documentation can explain expected behavior but cannot supply the missing exact error text or field names.

## Cloud-Loss Safety

**Decision**: Require a human-operated, approved lab experiment with independent console recovery.

**Rationale**: Blocking TCP port 443 can interrupt Mist management.
The current assignment prohibits the experiment.
The future evidence must prove both cloud loss and recovery, not merely that a firewall rule exists.

**Alternatives considered**: An ICMP result cannot prove the agent path.
An unverified block cannot establish portal behavior during cloud loss.
An automated experiment or a production target is outside scope.

## Artifact Structure and Checks

**Decision**: Keep core artifacts at the feature root and place supporting planning records under `design/`.

**Rationale**: This preserves five direct children without changing templates, scripts, or the process baseline.
The installed setup scripts still locate `spec.md`, `plan.md`, and `tasks.md`.
Task generation explicitly reads the linked design records.

**Alternatives considered**: Root-level copies would exceed the child limit and duplicate facts.
A new root under `specs/` would violate the managed taxonomy.

## Resolved Planning Questions

The issue defines all six observations.
No clarification is required for artifact preparation.
The exact outputs, router identity, approval, and experiment results remain absent because physical validation has not occurred.
No value in this record substitutes for a measurement.

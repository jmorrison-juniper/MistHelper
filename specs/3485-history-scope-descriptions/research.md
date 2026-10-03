# Research: History scope descriptions

## Existing scope authority

**Decision**: Reuse `HistoryScope.for_page` and its scoped capture rows.

**Rationale**: The history route authorizes the signed organization before it resolves any of its four readers.
The existing capture and run adapters enforce organization scope before count and page boundaries.
The operation reader uses site membership.
The audit reader applies organization and site scope before inference.

**Alternatives considered**: A new site lookup would add a source call.
A query-supplied name would bypass the trusted display-name policy.
Both alternatives are unnecessary.

## Description ownership

**Decision**: Preserve `HistoryScope` and use a dedicated `HistoryCardScope`.
Its three computed properties return frozen `HistoryCardDescription` records.

**Rationale**: The current Captures card already supplies validated site and name values.
The history template must not choose scope rules.
The existing two-field class contract remains unchanged.

**Alternatives considered**: Template branches would duplicate the scope rule.
The parent rejected an increase from six to ten existing scope members.
The bounded extraction adds genuine model names without moving unrelated routes or callers.

## Empty statements

**Decision**: Describe an empty visible page instead of claiming that the store holds no historical record.

**Rationale**: A valid offset can exceed the matching record count.
A statement about the visible page remains true for that case.
Each statement still names the actual site or organization scope.

**Alternatives considered**: "The site holds no run yet" becomes false on a later empty page.
Changing totals or readers would exceed this issue.

## Test inputs

**Decision**: Reuse the existing `HistoryCase` synthetic query fixture for real route contracts.
Use the current isolated browser fixture without changing its seeds or configuration.

**Rationale**: The synthetic fixture evaluates actual query clauses against interleaved organizations.
It provides populated capture, run, operation, and audit records.
The browser fixture supplies a named site with no run or operation and a populated organization.

**Alternatives considered**: Replacing complete readers would weaken the organization evidence.
Changing the shared browser fixture would conflict with another reserved repair.

## Shared audit history

**Decision**: Retain exact empty assertions and validate the two known native organization audit events.

**Rationale**: The full CI scope runs the existing audit-isolation journey before the owned organization history case.
That journey records a take and release for site `34983498-3498-3498-3498-349834983498`.
The selected organization therefore has two valid audit rows.
The history-only selection has no preceding audit journey and correctly shows the empty statement.

The owned case reads actual rendered cells, row identifiers, and the selected organization binding.
It also tests both decisions on a private copy of those real rendered elements.
Seven controlled variants reject extra or missing rows and incorrect organization, site, action, digest, or previous-holder data.
No server record, owner input, global fixture, source reader, or timeout changes.

**Alternatives considered**: Removing audit assertions would lose the empty contract.
Accepting arbitrary rows would weaken scope and privacy evidence.
Resetting shared history would change the behavior of the original 600 cases.

## Local capability limits

The Bash SpecKit plan script is absent.
The worktree contains PowerShell core scripts, but this machine has no PowerShell executable.
The branch hook uses raw checkout commands that conflict with the app-managed worktree.
Use the checked-in templates and the issue-owned context file.

The configured STE dictionary is unavailable for this task.
Run the configured heuristic checks and record `dictionary_unavailable`.
Do not create, copy, or modify a dictionary.

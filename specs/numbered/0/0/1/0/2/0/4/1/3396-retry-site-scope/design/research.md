# Retry scope research

## Decision

Use the validated aggregate targets to filter retry site rows before the aggregate service builds the parent.
Use the saved parent scope for later retry confirmation and submission.

## Rationale

The site records already permit an empty retry site.
The aggregate service stores every supplied site, even when no child uses that site.
The confirmation route and submission context currently read the full operator selection.
Lock acquisition already reads the durable parent, so narrowing the parent repairs that boundary without changing token handling.

## Alternatives considered

Changing the operator selection would lose the operator intent and change the options page.
Filtering all saves would change plain-save behavior.
Recomputing inventory at submission could change a plan after typed confirmation.

## Evidence

The existing focused contract file passes 44 tests before the change.
The issue has no comments or attached artifacts.
No open pull request owns a permitted path at the initial ownership check.
PowerShell was absent. A session-local official distribution runs the required managed-route commands.

# Research: Discoverable Upgrade Confirmation Navigation

## Decision
Use the existing confirmation endpoint and add a conditional link in the existing run-page template.

## Rationale
The hidden confirmation page already implements the safety boundary. Duplicating its logic or adding a new route would increase risk and could create inconsistent authorization behavior. The run page already exposes recovery actions by state, so a state-specific link is consistent with the portal's established navigation pattern.

## Alternatives considered
- Add a new confirmation route: rejected because the current route is already covered and safe.
- Automatically redirect awaiting runs: rejected because operators need to review the run state first.
- Show the link for every run: rejected because it would be misleading for states that are not ready.

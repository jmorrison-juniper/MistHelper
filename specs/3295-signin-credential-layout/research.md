# Research: Sign-in credential layout

## Decision 1: Keep the controls outside the flex fieldset

**Decision**: Move the existing token elements into one named group after the fieldset.
**Rationale**: The old label was a flex child beside the mode buttons.
At 1280x720, Chromium measured label left `754.96875` and field left `41`.
The exact offset was `713.96875` pixels.
**Alternative rejected**: A label-specific flex override leaves three unrelated children in the mode group.

## Decision 2: Disable the inactive field without erasing its value

**Decision**: Synchronize `hidden` on the group and `disabled` on the input.
**Rationale**: The provider-mode red measurement showed visible controls and a token entry in `FormData`.
A disabled field prevents inactive native submission. Hiding the group removes keyboard reach.
**Alternative rejected**: Clearing the token on a mode change introduces a credential-retention policy change.

## Decision 3: Reuse the signal-word rule

**Decision**: Add `.flash-danger.alert::before` to the existing common prefix selector.
**Rationale**: Both sign-in alerts measured weight 400. The actual 404 error page measured weight 700.
The existing colors and `"Warning: "` content remain unchanged.
**Alternative rejected**: New warning text, inline styles, or broad alert restyling changes unrelated behavior.

## Decision 4: Distinguish native acceptance from compatibility

**Decision**: Use upgrade-portal `magenta` and `default` for acceptance.
**Rationale**: Those are the actual native catalog and assets.
The main portal separately supplies `light`, `dark`, `magenta`, and `high-contrast`.
Their original bytes may support supplemental geometry measurements only.
**Alternative rejected**: New aliases or unsupported catalog entries would change the source scope.

## Decision 5: Preserve unrelated mobile overflow

**Decision**: Require the form and token group to fit. Preserve the existing service table.
**Rationale**: Its right edge is `399.71875` pixels on a `360`-pixel viewport.
Every observed overflowing element belongs to `dependency-panel`.
**Alternative rejected**: A table or page-width repair is outside this issue's presentation change.

## Evidence limits

The required native pre-edit run used full E2E collection and produced nine expected failures.
The later complete red run preserved actual 404 prefix measurements and genuine supplemental asset measurements.
These are Chromium measurements, not a claim that the old Edge screenshot is identical.
All raw credential values are synthetic or absent. No live Mist call is necessary.

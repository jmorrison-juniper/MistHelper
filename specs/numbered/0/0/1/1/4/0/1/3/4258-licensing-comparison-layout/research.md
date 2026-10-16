# Design Decisions

## Shared shell

**Decision**: Extend the existing `base.html` blocks.
**Rationale**: Navigation, theme controls, scripts, and footer already exist there.
**Alternative considered**: Copying shell markup would cause independent navigation drift.

## Display normalization

**Decision**: Normalize existing envelopes in the browser without changing API responses.
**Rationale**: Existing integration tests cover authorization, failures, bundles, and export.
**Alternative considered**: Changing backend response shapes would expand this visual repair.

## Input and calculations

**Decision**: Use labeled numeric count fields and existing per-row purchase semantics.
**Rationale**: Operators should not need JSON. Existing catalog-based bundle calculations remain authoritative.
**Alternative considered**: The source aggregate purchase-minus-entitlement model would change the existing service contract.

## Source evidence

The source screenshot shows organization controls above the comparison, purchases below it, and four summary cards.
The original template confirms license descriptions and used/entitled presentation.
The repair uses independently written markup, CSS, and DOM construction, with existing attribution retained.

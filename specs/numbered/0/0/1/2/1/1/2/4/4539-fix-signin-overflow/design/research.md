# Research: Sign-In Narrow Viewport Layout

## Findings

- **Decision**: Place the service table in the portal's existing table scroll box.
- **Rationale**: The local browser test measures a 400-pixel document at a 390-pixel viewport. The service table extends beyond the page.
- **Alternatives considered**: Hiding horizontal overflow could conceal sign-in content, so it is not acceptable.
- **External research**: Not needed. The defect is local to the portal layout and reproduces in its browser test.

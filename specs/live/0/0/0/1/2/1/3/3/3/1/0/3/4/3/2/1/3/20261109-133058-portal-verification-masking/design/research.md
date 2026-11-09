# Design decision

**Decision**: Keep the parameter type as `text` and add a password display override.

**Rationale**: Existing required-prompt tests and the positional input queue already depend on the current text parameter.
The renderer can preserve those contracts without changing validation or answer collection.

**Alternatives considered**: A new password parameter type would change existing metadata contracts.
A field-name condition would hide presentation policy inside the renderer.

No external research or service request is necessary.

# Research: Generated Operations control labels

## Decision

Assign `label.htmlFor = 'param-' + param.name` in `buildParameterLabel`.

## Rationale

`buildSelect`, `createTextInput`, and `createNumberInput` already use this identifier rule.
Static and endpoint-specific parameter groups share the label builder.
The existing browser proof reports one pass and three expected failures before the repair.

## Alternatives Considered

- An ARIA name would leave the visible label unassociated.
- Wrapping each control in a label would change the DOM structure and risk layout changes.
- Changing control IDs would risk dependencies and request collection.

## Scope

Reuse the existing #4041 proof only for regression coverage of #4059.
No new feature, dependency, or Mist transport is required.

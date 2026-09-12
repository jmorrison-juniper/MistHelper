# UI Contract: Per-Type Upgrade Version Defaults

The options page exposes three independent type controls. Tests and browser
code select them with these exact identifiers.

| Device type | Identifier |
| --- | --- |
| `ap` | `upgrade-version-select-ap` |
| `switch` | `upgrade-version-select-switch` |
| `gateway` | `upgrade-version-select-gateway` |

Each control contains only the common compatible returned versions for its
type. A control with no common candidate has no selected target and displays a
clear message.

The page retains each `upgrade-version-select-<mac>` individual control and
the `upgrade-options-save-button` save control. The page removes
`upgrade-version-select-all`. A type selection changes only device controls of
the same type that offer its exact version.

# Missing-Zone Display Contract

The zone report requires an explicit dictionary of sites that lack common zones.

| Input | Required output |
| - | - |
| Missing, null, or non-dictionary value | Log a validation error and raise `ValueError` before printing the section. |
| Empty dictionary | Print the section count and the existing all-sites reassurance. |
| Nonempty dictionary | Print the section count, site names, missing zones, and the existing overflow notice when needed. |
| Empty zone analysis | Preserve the existing skip before the display helper runs. |

This contract changes no API, export, identifier, or destructive operation.

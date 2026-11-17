# Data Model: VPN Inventory Result

## VPN Inventory

The VPN inventory contains all VPN definitions returned for one organization.

| Field | Meaning |
| - | - |
| `name` | Nonblank string checked before the builder offers creation. |
| `id` | Existing VPN identifier retained in the returned definition. |

## Inventory Result States

| State | Meaning | Builder behavior |
| - | - | - |
| Complete and non-empty | Every page succeeded, records have nonblank string names, and pagination metadata is valid and stable. | Display the inventory and reject duplicate names. |
| Complete and empty | A successful single-page response has no page headers, or every declared page succeeds with stable metadata and no VPN records. | Continue the normal name flow. |
| Unavailable | A request failed, an error payload appeared, a page or record had an invalid shape, a name was unusable, headers were invalid, a link repeated, or a declared page did not arrive. | Stop before the name prompt and VPN creation. |

The builder must not convert an unavailable inventory into a complete empty inventory.

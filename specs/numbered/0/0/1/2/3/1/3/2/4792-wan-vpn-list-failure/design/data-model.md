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
| Complete and non-empty | Every page succeeded and contains object records with nonblank string names. Pagination links do not repeat. | Display the inventory and reject duplicate names. |
| Complete and empty | Every page succeeded and contains a valid empty result list. | Continue the normal name flow. |
| Unavailable | A request failed, a page or record had an invalid shape, a name was unusable, a link repeated, or a declared page did not arrive. | Stop before the name prompt and VPN creation. |

The builder must not convert an unavailable inventory into a complete empty inventory.

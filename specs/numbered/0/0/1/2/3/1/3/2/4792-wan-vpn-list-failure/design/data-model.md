# Data Model: VPN Inventory Result

## VPN Inventory

The VPN inventory contains all VPN definitions returned for one organization.

| Field | Meaning |
| - | - |
| `name` | Name checked before the builder offers creation. |
| `id` | Existing VPN identifier retained in the returned definition. |

## Inventory Result States

| State | Meaning | Builder behavior |
| - | - | - |
| Complete and non-empty | Every page succeeded and contains a valid result list with one or more VPN definitions. | Display the inventory and reject duplicate names. |
| Complete and empty | Every page succeeded and contains a valid empty result list. | Continue the normal name flow. |
| Unavailable | A request failed, a page had an invalid status or shape, or pagination ended before the next page arrived. | Stop before the name prompt and VPN creation. |

The builder must not convert an unavailable inventory into a complete empty inventory.

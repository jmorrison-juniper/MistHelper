# Data Model: Gateway History After an Ordinary Refresh

## Identity Entities

| Entity | Fields | Natural key | Evidence |
| - | - | - | - |
| Gateway identity | Site (organization and site identifiers) and gateway identifier | Organization, site, and gateway identifier | R90 (natural key, line 69) |
| Circuit record identity | Gateway identity and port name | Gateway key followed by the port name | R39 (gateway field, line 90) and R91 (natural key, line 105) |
| Peer record identity | Gateway identity and peer fields | Gateway key followed by the peer fields | R40 (gateway field, line 116) and R92 (natural key, line 133) |

The identity module is `src/interfaces/wan_performance/domain/identity.py` on the candidate head (blob `c7baea89e2ac50d37237f8e99294c3d1db13c1b6`).

## Row to Record Mapping

- A port row becomes a circuit record. The record identity carries the gateway identity built from the row (R37, line 154).
- A peer row becomes a peer record (R38, line 168).
- The issue reports that an ordinary refresh produces port and peer rows without gateway insight rows. The main organization snapshot sets the gateway insight block to none (R13), and the main gateway insight method returns empty when no target exists (R14).

## Selection State Transitions

The gateway selection moves from the selected records to one of three outcomes.

| Selected records | Gateway identities found | Organization check | Outcome |
| - | - | - | - |
| None | 0 | Not reached | Refuse with the gateway message (R24). |
| Records of one gateway | 1 | The gateway belongs to the service organization (R99) | Read the history once. |
| Records of one gateway | 1 | The gateway belongs to another organization (R99) | Refuse with the gateway message (R24). |
| Records of two or more gateways | 2 or more | Not reached (R23) | Refuse with the gateway message (R24). |

For port and peer kinds, the rule differs. Exactly one selected record is required (R100). Any other count refuses with the port-or-peer message (R25).

## Retained History Lifecycle

- A scoped refresh collects the snapshot for one gateway target. It writes history, and then it publishes the snapshot (R41, R42).
- An ordinary refresh collects the snapshot without a target. It writes history, and then it publishes the snapshot (R41, R42). The published snapshot can lack gateway rows.
- Publishing a snapshot does not delete retained history from the history store. The history read selects by identity, so retained gateway history stays readable (R36 covers identity isolation at the store).
- The repair does not change the write order. It changes only how the page resolves the identity to read.

## Relationships

- One gateway identity owns zero or more circuit records and zero or more peer records.
- One circuit record or peer record names exactly one gateway identity.
- One organization owns zero or more gateway identities. Each gateway identity names one organization.
- The history store returns hourly records for one identity over a window of thirteen months.

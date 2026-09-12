# Research: Complete Tier 3 Capture Output

## Live finding

A Playwright walk created Tier 3 capture `cap-5ed7c0ae6ea241918cded4697c134d53-01`.
The capture verified and stored 76,490 bytes.

The stored document contained these records.

| Section | Count |
| - | -: |
| Devices | 9 |
| Wired clients | 38 |
| Wireless clients | 20 |
| Guest clients | 0 |
| Switch ports | 62 |
| PoE | 62 |
| Radios | 15 |
| Tunnels | 0 |
| BGP peers | 0 |
| Alarms | 88 |

The page rendered only devices, wired clients, and wireless clients.
The CSV and JSON exports contained only those same three row kinds.

## Decision 1: Keep the collector unchanged

The capture API and ArangoDB document contain all six Tier 3 keys.
The defect starts after storage, in the page and export boundaries.

## Decision 2: Use fixed section identities

Each section gets one stable key, label, and export kind.
The page uses the key in `data-testid` values.
The export uses the kind in each row.

## Decision 3: Preserve future safe fields

The Mist API can add fields without a portal release.
Each export row carries `details_json` with every safe source field.
The credential-name filter runs before JSON serialization.

## Decision 4: Keep the page bounded

Each table uses the existing 500-row cap.
If a table is cut, the page states the visible count and the stored count.
The download remains complete.

## Decision 5: Use stand-in browser data

The E2E server must not call the live Mist cloud.
The stand-in capture will contain one row for each Tier 3 section.
The browser will assert the page tables and both download row sets.

# Evidence Checklist: Hardware register rows

Each item checks the rows in `contracts/hardware-register.md`. Each item is checked against the local OpenAPI blob `b7fc2bfb` on `main` or the local mistapi 0.64.1 package.

## Citation Quality

- [x] Each verified row cites one inventory line and at least one port line.
- [x] Each cited line exists in the OpenAPI blob. The inventory line for SRX300 is 48412. The port lines are 29725 and 29729. The inventory line for SRX320 is 47236. The port lines are 47221 and 47223.
- [x] Each blocked row names one blocker code in `proposal-json.md`.
- [x] Each SDK reference names a local path under `.venv\Lib\site-packages\mistapi`. No reference names a path under `src/mistapi`.

## Verified Row Rules

- [x] SRX300 is verified for the standalone role only. Its WAN and LAN names are on explicit lines 29725 and 29729.
- [x] SRX320 is verified for the standalone role only. Its WAN and LAN names are on lines 47221 and 47223, after the HA ports are removed.
- [x] Each HA, fxp0, or OOB port stays outside the selectable list. The list names each excluded port and its line.
- [x] No open-ended range expands. The `ge-0/0/3-` range on SRX300 stays as one port.

## Blocked Row Rules

- [x] SRX340, SRX345, SRX380, SRX550, SRX1600, and SRX4100 have no inventory sample. Each row blocks with `model_without_inventory_sample`.
- [x] SRX1500 has two cabling sections that name different cluster members. The row blocks with `model_evidence_conflict`.
- [x] SSR120 has no port roles. The row blocks with `port_evidence_absent`.
- [x] VSRX is absent from the register. Selecting it yields `model_unknown`.

## Revision and Pins

- [x] Each row carries the revision string `openapi-b7fc2bfb-mistapi-0.64.1`.
- [x] A changed pin or a changed OpenAPI blob makes each row stale until a reviewer updates the revision and the row evidence.
- [ ] Issue 4634 records field semantics for each verified row. This item stays open until that issue closes (T001).

# Regression Checklist: Rogue client exports use the client endpoint name

**Purpose**: Show which test or check covers each behavior that the change must keep or fix.
**Created**: 2026-11-26
**Feature**: `spec.md`, User Stories 1 to 3

- [x] REG-01 Menu 29 sends `listSiteRogueClients` to the export writer (TST-01, TST-03).
- [x] REG-02 Menu 30 keeps `listSiteRogueAPs` as the endpoint name (TST-05, TST-07, TST-08).
- [x] REG-03 Menu 29 fetches with the client endpoint function (TST-04).
- [x] REG-04 The client primary key is `(client_mac, bssid)` in the DDL (TST-09).
- [x] REG-05 The AP primary key is `(bssid, ap_mac)` in the DDL (TST-10).
- [x] REG-06 A fast-mode cache hit makes no export writer call in either export (TST-02, TST-06).
- [x] REG-07 An empty result makes no export writer call (TST-08).
- [x] REG-08 The list-type assertion in `TestLoadSiteList` stays unchanged (TST-11).
- [ ] REG-09 An existing SQLite table keeps its key in Phase 1. Explained: the check runs after implementation with CHK-01 (scope check).
- [ ] REG-10 A key mismatch stops the SQLite write before insert. Explained: held for Phase 2 (TST-12).
- [ ] REG-11 The candidate-key report changes no row. Explained: held for Phase 2 (TST-13).
- [ ] REG-12 The ArangoDB rogue client vertex key includes `bssid`. Explained: held for Phase 2 (TST-14).

# Phase 1 Data Model Delta: Remaining Walkthrough Defects

**Parent data model**: [`data-model.md`](./data-model.md)

**Spec**: [`spec-remaining-defects.md`](./spec-remaining-defects.md)

**Date**: 2026-08-27

## Why this document exists

The parent `data-model.md` holds the whole schema. This document records only
the deltas that the seven remaining defects need. The implementation folds the
run-less capture decision into `data-model.md`, because FR-100 asks for that
record. The other deltas add a field or a behavior, and they do not replace any
parent entity.

## The run-less capture decision (#2096)

FR-100 asks `data-model.md` to record four facts. The implementation writes
these four facts into the parent `data-model.md`. This document states them
first, so the reader confirms the decision before the code lands.

1. A capture that names no run writes no run document and no `capture_for_run`
   edge. The capture stands alone as a pre-check for its site.
2. A standalone capture builds its own identifier from a capture nonce. It does
   not derive the identifier from a run. The key keeps the form `cap-{hex}-01`,
   and the nonce is a `uuid4` hex value.
3. An upgrade start creates the run and writes the edge at adoption time. The
   edge holds the role `pre`, and the run pre-check field names the capture.
4. A one-time repair removes every dangling edge that the old behavior left. A
   dangling edge is a `capture_for_run` edge whose run document does not exist.

## Entity delta - Standalone pre-check capture

**Base entity**: Capture (parent `data-model.md`).

**Change**: A capture document may hold an empty `run_id` field. An empty
`run_id` marks the capture as a standalone pre-check.

| Field | Rule for a standalone capture |
| --- | --- |
| `_key` | `cap-{nonce_hex}-01`, where the nonce is a fresh `uuid4` hex value. |
| `run_id` | Empty. The capture names no run. |
| `role` | `pre`. The capture records the state before an upgrade. |
| `ordinal` | 1. A standalone capture is always a first capture. |

**Graph rule**: The store writes no `capture_for_run` edge for a standalone
capture, because the edge builder skips an empty `run_id`.

**Readability rule**: The capture stays readable by site and by date. A query
reads a standalone capture through the site index and the ordinal index that the
parent model already names.

## Entity delta - Upgrade run adoption

**Base entity**: Upgrade run (parent `data-model.md`).

**Change**: The run gains one behavior at creation time. When an upgrade start
creates the run, the run adopts the most recent verified standalone pre-check
capture of the site.

| Step | Rule |
| --- | --- |
| Select | Read the newest verified standalone pre-check capture of the site. The capture holds `role=pre`, an empty `run_id`, and a verified state. |
| Link | Write the `capture_for_run` edge from the new run to that capture, with the role `pre`. |
| Set | Set the run pre-check field to the capture identifier. |

**Edge rule**: The edge `_from` names the run document, and the `_to` names the
capture document. The run document exists at adoption time, so the edge never
dangles.

**Idempotence**: A second start on the same site refuses, because a run of that
site has not finished (FR-105). So the adoption runs once for each run.

## Entity delta - Client comparison proved present count

**Base entity**: Client comparison (parent `data-model.md`, mirror of the
device comparison).

**Change**: The client comparison gains a `proved_present` integer. It mirrors
`DeviceComparison.proved_unchanged` from commit `c9431881`.

| Field | Rule |
| --- | --- |
| `proved_present` | The count of present clients that a digest match proved. Zero when the comparison read the client rows itself. |

**Section rule**: A client comparison holds three sections: wired, wireless, and
guest. The proved present count sums the count of each skipped section.

**Size rule**: Each section count reads the larger of the two client index
sizes. A partial document then never lowers a proved count (FR-114).

**Statistics rule**: The client present count adds `proved_present`. The client
return rate reads the corrected present count with no further change, because
the present count feeds both the numerator and the denominator.

**Contract rule**: The `to_dict` form of the client comparison still names
`client_deltas` and `skipped_sections` only. The proved count travels to the
page through the statistics object, as the device count does.

## Entity delta - Site lock grant on a capture start

**Base entity**: Site lock record (parent `data-model.md`).

**Change**: The stored lock record holds an empty run value when the lock names
no run.

| Field | Rule |
| --- | --- |
| `run_id` | Empty when a capture start took the lock, because a capture names no run. The value is an empty string, never the text `None` (FR-112). |

**Answer rule**: The capture start answer carries the lock grant when the start
took the lock. The grant holds the token, the expiry, and the state. The shape
matches the answer of `POST /api/sites/<site_id>/lock`.

## Entity delta - The unresolved-site lock state

**Base entity**: Site lock banner state (parent `data-model.md` and
`contracts/site-lock.md`).

**Change**: The banner state set gains one value for a page that cannot name its
site.

| State | Meaning |
| --- | --- |
| `free` | The lock store answered and named no holder. |
| `locked` | The lock store answered and named a holder. |
| `held` | This browser holds the lock. |
| `unknown` | The lock store did not answer. The wording stays reserved for this state (FR-118). |
| `site_unknown` | The page cannot name its site, so no lock key exists to read. New for #2097. |

**Rule**: A page reports `site_unknown` only when the site identifier is empty.
A page with a site identifier reports one of the other four states.

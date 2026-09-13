# Contract Deltas: Remaining Walkthrough Defects

**Parent contracts**: [`http-api.md`](./http-api.md) |
[`ui-testids.md`](./ui-testids.md) | [`site-lock.md`](./site-lock.md) |
[`upgrade-service.md`](./upgrade-service.md)

**Spec**: [`../spec-remaining-defects.md`](../spec-remaining-defects.md)

**Date**: 2026-08-27

## Why this document exists

The source code holds comments that name exact line numbers of the parent
contract files. An in-place edit of a parent contract would move those lines and
break the anchor comments. So this document records the contract deltas as a
separate note. The implementation edits the parent contract text and the anchor
comments together, inside the same commit that lands the code. This note tells
the reader what each edit must say.

Every delta names the parent section it changes. A reader reads the parent
section first, then reads the delta.

## HTTP API deltas

### Delta H1 - The capture start answer carries the lock grant (#2108)

**Parent section**: `POST /api/sites/<site_id>/captures` (http-api.md line 176).

**Change**: The 202 answer carries the lock grant when the start took the lock.
The grant shape matches the answer of the lock endpoint in section 3.

Current 202 body:

```json
{ "capture_id": "<string>", "status_url": "/api/captures/<id>/status" }
```

New 202 body when the start took the lock:

```json
{
  "capture_id": "<string>",
  "status_url": "/api/captures/<id>/status",
  "lock": {
    "token": "<string>",
    "expires_at": "<iso-8601>",
    "state": "held"
  }
}
```

**Rules**:

- The `lock` object appears only when the operator who started the capture took
  the lock on this call (FR-109).
- A start that names no owner takes no lock, so the answer holds no `lock`
  object (FR-111).
- The paragraph at http-api.md line 209 states that the refusal answer names no
  holder. This delta does not change the refusal answer. It changes the 202
  success answer only.

**Implementation note**: The 202 grant reuses the lock endpoint serializer. The
`lock` object holds `lock_token`, `expires_in`, and `state`, exactly as section 3
shows at line 129. The browser reads `lock_token` to start the beat. The banner
forces the `held` label, so `state` stays the lock endpoint value `acquired`. The
JSON sample above named the three fields loosely, and the real fields match
section 3.

### Delta H2 - A run-less capture writes no edge (#2096)

**Parent section**: `POST /api/sites/<site_id>/captures` (http-api.md line 176)
and the paragraph at line 190.

**Change**: The paragraph at line 190 states that the capture identifier derives
from the run alone. This delta corrects that statement for a run-less capture.

New wording for the paragraph:

- When the body names a run, the capture identifier derives from that run, and
  the repeat-in-place rule holds as written.
- When the body names no run, the capture identifier derives from a fresh
  capture nonce. The capture stands alone as a site pre-check. The portal writes
  no run document and no `capture_for_run` edge for that capture (FR-096).
- The `run_id` field of the body reads `null` or absent for a standalone
  capture. The stored capture document then holds an empty `run_id` field.

### Delta H3 - The run creation adopts a standalone pre-check (#2098)

**Parent section**: `POST /api/sites/<site_id>/runs` (http-api.md line 315).

**Change**: The 201 answer is unchanged. The handler gains one behavior.

New rule text:

- When the handler creates a run, it reads the newest verified standalone
  pre-check capture of the site. It writes a `capture_for_run` edge from the new
  run to that capture with the role `pre`. It sets the run pre-check field to
  that capture identifier (FR-103).
- When the site holds no standalone pre-check capture, the handler creates the
  run with no adopted pre-check. The answer is unchanged.
- The lock refusal at line 324 and the live-run refusal stay as written. The
  adoption runs only after the handler passes those refusals.

## UI test identifier deltas

### Delta U1 - New capture-page control (#2098)

**Parent file**: `ui-testids.md`.

**Change**: The capture page gains one control that starts an upgrade from the
verified pre-check.

| Test identifier | Element | Rule |
| --- | --- | --- |
| `capture-start-upgrade-button` | button | Starts an upgrade for the site of this capture. Posts to `POST /api/sites/<site_id>/runs`, then opens the options page (FR-101). |
| `capture-start-upgrade-error` | region | Shows a refusal from the run creation. Names the lock holder for a lock refusal (FR-104). Names the running run for a live-run refusal (FR-105). |

### Delta U2 - Radio groups replace three controls (#2101)

**Parent file**: `ui-testids.md`.

**Change**: Three single-choice controls become radio groups. The old
identifiers retire. The version controls keep their identifiers.

| Old identifier | New group identifier | New option identifiers |
| --- | --- | --- |
| `upgrade-strategy-select` | `upgrade-strategy-group` | `upgrade-strategy-big-bang`, `upgrade-strategy-canary` |
| `upgrade-reboot-toggle` | `upgrade-reboot-group` | `upgrade-reboot-yes`, `upgrade-reboot-no` |
| `upgrade-junos-file-action-toggle` | `upgrade-junos-file-action-group` | `upgrade-junos-file-action-yes`, `upgrade-junos-file-action-no` |

**Unchanged identifiers**: `upgrade-version-select-all` and
`upgrade-version-select-<mac>` stay dropdowns and keep their identifiers
(FR-122). The saved option body keeps the same three field names with the same
defaults (FR-124).

## Site lock deltas

### Delta S1 - The unresolved-site banner state (#2097)

**Parent file**: `site-lock.md`.

**Change**: The banner state set gains a fifth value for a page that cannot name
its site.

| State | Meaning |
| --- | --- |
| `site_unknown` | The page holds no site identifier, so no lock key exists to read. The banner shows a sentence that names this cause. |

**Rules**:

- The `unknown` wording stays reserved for a lock store that does not answer
  (FR-118). The `site_unknown` state does not reuse that sentence (FR-119).
- The banner reports `site_unknown` only when the site identifier is empty. A
  page with a site identifier reports `free`, `locked`, `held`, or `unknown`.
- The `held`, `free`, and `locked` sentences do not change. The plan keeps the
  accessible wording of those three states.

## Contract test impact

- The capture-start contract test asserts the 202 body carries the `lock` object
  after a lock take, and holds no `lock` object for a run with no owner.
- The run-create contract test asserts the handler adopts the newest standalone
  pre-check, and writes the `pre` edge to the new run.
- The upgrade-options contract test reads the new radio identifiers and asserts
  the saved body keeps the three field names.
- The comparison contract test keeps the two client keys `client_deltas` and
  `skipped_sections`, because the proved present count travels through the
  statistics object.

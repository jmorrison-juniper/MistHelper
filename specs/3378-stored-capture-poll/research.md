# Research: The poll of a stored capture stops

**Issue**: #3378 | **Spec**: [spec.md](spec.md)

## R1: Which words does the live path send at the end?

The collector writes the last progress change in `progress_change`
(`src/upgrade_portal/capture/collector.py`). It sends `verified` when the
read-back matched, and `failed` in every other case. It sets `verified` to the
same result. A write failure also sends `failed`, because the collector names
`WRITE_FAILED_MESSAGE` with the state `failed`.

The route sends `pending`, `collecting`, and `failed` before the collector
ends. No path of the release sends `write_failed` to the page.

The collector stores every assembled document, and this includes a document
whose content word is `failed` because the capture read no row. If the
read-back of that document holds, the live path sends `verified`. The old
stored rule sent `failed` for the same document, so the two paths disagreed
there too.

**Decision**: The stored path uses the rule of the live path. It sends
`verified` when the read-back holds, and `failed` in every other case.

## R2: Which field holds the read-back result of a stored capture?

`load_capture` in `src/upgrade_portal/capture/store.py` answers a
`CaptureLoad`. Its `comparable` flag holds true only when three checks pass.
The document exists, this release can read its schema version, and the
lifecycle field `state` holds `verified`. The route already passes that flag to
`stored_progress` as `comparable`, and the body already sends it as `verified`.

The flag is false in two cases where a document exists.

| Reason | Cause | The word after the repair |
| - | - | - |
| `capture_not_verified` | The lifecycle never reached `verified`. An example is a worker that stopped during the write. | `failed` |
| `schema_version_too_new` | A later release wrote the document. | `failed` |

**Decision**: `failed` is correct for both cases. This release cannot compare
either capture. The page then shows the start button again, so the operator can
take a new capture. The badge reads `Not verified`.

## R3: Does the page lose the partial word?

No. The capture page shows a partial capture through `partial_reasons`. The
template shows the partial warning when that list holds an entry, and the stored
path already copies the list. The live path also sends `verified` at the end of
a partial capture, together with the list.

The history page and the comparison page read `capture_status` from the stored
document, not from the status body. The repair does not change the document.

**Decision**: Add no field to the status body. The contract fixes its fields,
and `STATUS_FIELDS` removes any other field.

## R4: Should `portal.js` change?

An extra stop on `status.verified === true` would hide the server defect. It
would also leave the multi-site card wrong, because `takeOrgPrecheck` accepts a
pre-check only when `state` holds `verified`.

**Decision**: Change the server only. Both readers of the page already stop on
`verified` and `failed`.

## R5: Why did no test find the defect?

Two seeds hold `capture_status` `verified`, which the shipped store never
writes (`resolve_status` in `src/upgrade_portal/capture/assembly.py` writes
`complete`, `partial`, or `failed`).

- The contract test `test_a_stored_capture_reads_as_verified` seeds
  `STORED_CAPTURE` with that value.
- Every browser seed in `tests/e2e/upgrade_portal/conftest.py` holds that value.
  Issue #3375 owns those seeds.

**Decision**: Move the contract seed to the shipped shape. Add one browser seed
in the shipped shape on its own site, so it does not change a count, a picker,
or the pre-check adopter.

## R6: Where does the new browser seed go?

The history page and both capture pickers list every site when no site is
named. The stand-in store lists the captures in the order of the index. The
comparison fixture takes the first choice and the last choice, and
`test_capture.py` takes the first history row.

**Decision**: Seed `e2e-capture-stored-poll-0001` on the site
`e2e-stored-poll-site`. Put it between the seeded post-check and the Tier 3
capture, with the start time `2026-08-19T10:45:00+00:00`. The first key and
the last key of every list stay the same. The seed names no run, and its
`capture_status` is not `verified`, so the stand-in adopter never adopts it.

## R7: What does the repair save?

The diagnostic journey of the issue counted the requests of one open page.

| Case | Status requests in 10 seconds |
| - | - |
| Stored answer `verified` | 1 |
| Stored answer `complete` | 4 |

Each request of a stored capture reads the whole document from the store. The
repair removes about 20 document reads each minute for each open tab of a
stored capture.

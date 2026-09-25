# Research: The browser test store adopts only a standalone pre-check

**Issue**: #3360 | **Spec**: [spec.md](spec.md)

## Decision 1: Compare the run field with an empty text

The shipped query `_PRECHECK_QUERY` holds the line
`FILTER doc.run_id == @empty_run`, and the bind value is an empty text. In AQL,
a missing attribute reads as `null`, and `null == ""` is false. The shipped
reader therefore adopts no capture that holds no `run_id` field.

The stand-in uses `record.get("run_id") == ""`. A missing field reads as
`None`, which is not equal to an empty text. The two rules agree.

**Alternative that I rejected**: `not record.get("run_id")`. That rule accepts
a capture with no `run_id` field, which the shipped reader refuses.

## Decision 2: Sort by the start time as text

The shipped query sorts with `SORT doc.started_at DESC`. AQL compares two
texts character by character. Every stored start time uses ISO 8601 with a UTC
offset, so the text order is the time order.

The stand-in compares `str(record.get("started_at") or "")`. A capture with no
start time reads as an empty text, which sorts first. The shipped sort puts
`null` below every text, so both rules make that capture lose.

AQL states no order for two equal sort values. The stand-in picks the match
that the store holds last. That choice keeps the old answer for equal values,
so no journey changes for a tie.

## Decision 3: Seed a standalone pre-check, and do not take one

The journey `test_org_missing_precheck_journey.py` proves that the button for
the missing pre-checks skips a ready site. The first site must therefore hold a
standalone pre-check before the page opens. Two ways exist.

| Way | Result |
| - | - |
| Seed one standalone pre-check | The first site is ready in every test order. |
| Take one in the journey | The journey adds a slow capture step. The result depends on the order of the journeys, because the server serves the whole session. |

I chose the seed `e2e-capture-standalone-0001`. It names no run, and it starts
at `2026-08-19T10:15:00+00:00`.

## Decision 4: Put the seed between the seeded pre-check and post-check

The comparison journey takes the first choice and the last choice of the
pre-check picker. The seeded order is the seeded pre-check, the new seed, the
seeded post-check, and the Tier 3 capture. The start times follow the same
order. The first and the last capture stay the same in the insertion order and
in the time order.

## Decision 5: The browser assertion fails on the old stand-in

The old stand-in returns the last stored verified pre-check of the site. The
Tier 3 capture is the last stored seed, so the old card names
`e2e-capture-tier3-0001`. The new assertion states that the cell names no
capture that a run owns, so the old stand-in fails it.

An earlier journey can take a standalone pre-check of the first site. The card
then names that newer capture. The assertion reads the list of captures that a
run owns, and it never names one expected capture, so the order of the
journeys does not change the result.

## Decision 6: Keep the field that tells a verified capture

The shipped reader filters on the lifecycle field `state`. The stand-in and the
seeds use the content field `capture_status`. A change of that field changes
every seed and every capture that the stand-in runner stores. Issue #3375 holds
that repair, so this change keeps the current field.

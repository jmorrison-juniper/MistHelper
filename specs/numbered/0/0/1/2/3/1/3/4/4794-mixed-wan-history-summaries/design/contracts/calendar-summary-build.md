# Contract: CalendarSummaries.build

## Signature

`CalendarSummaries.build(records, identity)` takes a tuple of `HourlyMeasurement` records and one `MeasurementIdentity`. It returns a tuple of `PeriodSummary` values. The class `CalendarSummaries` is in `src/interfaces/wan_performance/domain/summary.py`. The period summaries call `LinkEventSummaries.build` at line 130 (remote check 55).

## Input Rules

- The builder keeps only the records whose identity equals the selected identity (remote check 88).
- Each record must carry a natural key that the measurement module defines (remote check 60).
- Snapshot hours and incomplete event hours are valid input. The repair removes the `KeyError` that a mixed period caused (FR-001).

## Output Rules

- Each call returns the daily, weekly, and monthly summaries, then the rolling summaries (remote check 56).
- The rolling summaries cover 3-hour, 12-hour, and 24-hour windows (remote check 57).
- One hour in one daily, weekly, and monthly period produces six summaries: one daily, one weekly, one monthly, and three rolling.
- Each summary carries its own `LinkEventSummary`, built from the hours in its period (remote check 102).

## Event Rules

| Input hours | Daily `link_event_summary` |
| - | - |
| One complete hour with up 60, down 0, flap 0 | `LinkEventSummary(1, 1, 24, 60, 0, 0, 100)` |
| The same complete hour and one snapshot hour | `LinkEventSummary(1, 1, 24, 60, 0, 0, 100)` |
| One incomplete event hour | `LinkEventSummary(0, 0, 24, None, None, None, None)` |
| One complete hour with flap 0 and no minutes | `LinkEventSummary(1, 0, 24, None, None, 0, None)` |
| Snapshot hours only | `None` |

The examples match the regression tests at the candidate head (remote checks 61, 63, and 64). The snapshot-only row is a new guard test (remote check 99 records the absence).

## Error Rules

The builder raises no `KeyError` for a period that mixes complete hours and snapshot hours (FR-001). Validation errors for other input faults stay unchanged by this repair.

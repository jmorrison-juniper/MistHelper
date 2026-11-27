# Contract: LinkEventSummary

## Identity

`LinkEventSummary` is a frozen dataclass in `src/interfaces/wan_performance/domain/summary.py`. The field `up_minutes` at line 47 is an example of the optional totals (remote check 85). The object is computed on request and is not stored or serialized (remote check 83).

## Fields

| Field | Type | Meaning | Unknown rule |
| - | - | - | - |
| `complete_hours` | int | Count of complete hours in the period | Never unknown. Zero when no complete hour exists. |
| `known_hours` | int | Count of complete hours that also have both minute totals | Never unknown. |
| `expected_hours` | int | Hours in the period (remote check 58) | Never unknown. |
| `up_minutes` | float or None | Sum of up minutes over known hours | Unknown when no known hour exists. |
| `down_minutes` | float or None | Sum of down minutes over known hours | Unknown when no known hour exists. |
| `flap_count` | float or None | Sum of flap counts over complete hours (remote check 104) | Unknown when no complete hour exists. |
| `observed_up_percent` | float or None | Up minutes as a percent of known minutes | Unknown unless both minute totals are known and their sum is nonzero (remote check 103). |

## Null Rules

- A known zero is the number 0 or 0.0. A known zero is never `None`.
- A `None` value never means zero, and it never means healthy service.
- The field `PeriodSummary.link_event_summary` is `None` when no hour in the period has a `flap_count` key (remote check 54).

## Callers

- `CalendarSummaries.build` sets this object on each period summary (remote check 55).
- The live portal block reads each field and guards each `None` value (remote checks 68 and 69).

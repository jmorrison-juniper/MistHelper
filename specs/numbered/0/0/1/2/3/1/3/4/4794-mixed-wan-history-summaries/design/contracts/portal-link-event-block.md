# Contract: Portal link-event block

## Location

The block is in `src/interfaces/wan_performance/presentation/templates/wan_performance/live.html`, lines 404 to 419 (remote checks 68 and 69).

## Rendered Text

Each line below is a rendered sentence. The text inside braces comes from the summary. Each quoted string must stay unchanged, because the e2e test asserts it.

- `{complete_hours} complete event windows of {expected_hours} expected hours.`
- When `up_minutes` and `down_minutes` are both known: `Known state covers {up plus down} minutes in {known_hours} hours.`
- When either minute total is unknown: `Known state duration: Unknown. No complete duration hours exist.`
- `Up: {up_minutes or Unknown} minutes.`
- `Down: {down_minutes or Unknown} minutes.`
- `Matching transitions: {flap_count or Unknown}.`
- `Up percentage of known minutes: {observed_up_percent or Unknown}.`

## Rules

- Each value tests `is not none`, not truthiness. A known zero renders as `0` (remote check 69).
- The block never renders a healthy value for an unknown total.
- The block never sums an unknown total. The sum appears only when both minute totals are known (remote check 68).

## Test Assertions

The e2e test `test_live_link_event_view_renders_missing_evidence_as_unknown` asserts these four strings in the rendered page (remote check 65):

- `Known state duration: Unknown.`
- `Up: Unknown minutes.`
- `Down: Unknown minutes.`
- `Matching transitions: Unknown.`

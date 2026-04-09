# Quickstart: MistAPI SDK Compatibility Audit

This quickstart describes how to use the planning artifacts to complete the MistAPI compatibility update for `MistHelper.py`.

## 1. Review the research

- Read `research.md` first.
- Confirm the target SDK line is `mistapi` `v0.61.4`.
- Note the only confirmed breaking call site: `getSiteInsightMetricsForClient()`.

## 2. Update the code path that changed

- Adjust the client insight call in `MistHelper.py` to use the newer `metrics=` form expected by the updated SDK.
- Keep the rest of the direct MistAPI call sites unchanged unless the implementation pass proves one of them needs a compatibility fix.

## 3. Align dependencies

- Update project dependency metadata to match the audited SDK floor.
- Keep the `websocket-client` minimum aligned with the MistAPI release notes because the SDK now requires a newer floor.

## 4. Run the representative checks

Use the standard MistHelper validation flow after implementation:

1. Syntax check `MistHelper.py`.
2. Run the test suite or `python MistHelper.py --test`.
3. Exercise representative exports or workflows for:
   - alarms
   - device events
   - stats / SLE summaries
   - client insight metrics
   - site maps and WLAN lookups
   - the E911 BSSID report

## 5. Confirm the audit trail

- Make sure the final documentation states which MistAPI release notes were reviewed.
- Confirm the compatibility finding for each direct `mistapi` call site in `MistHelper.py`.
- Record any deferred work as a follow-up, not as an unresolved surprise.

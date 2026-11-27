# Contract: Health and Services

## Scope

Test `test_health_reply_keeps_exact_shape` and test `test_ready_reply_unchanged_with_converter` (task T003). The same tests run after registration (task T009).

## `/health`

- **Route**: `web_portal/routes/dashboard.py` lines 47 to 66.
- **Status code**: 200.
- **Keys**: exactly `status`, `services`, and `uptime_seconds`.
- **Values**:
  - `status` is `healthy` (line 62). Monitors match this word exactly.
  - `services` is `{"web_portal": "running"}` (line 63).
  - `uptime_seconds` is an integer of zero or more (line 64).
- **Cost**: The reply reads no disk and opens no network connection (docstring lines 49 to 53).

## `/ready`

- **Route**: `web_portal/routes/dashboard.py` lines 69 to 91.
- **Payload**: `status` is `ready` or `not ready` (line 83).
- **Status code**: Set by the handler (line 91). The baseline snapshot records the code before composition.

## Rules

- Registration must not add a key to `services`.
- Registration must not add a converter field to `/health`.
- The baseline snapshot is taken before composition. The same test compares the reply after composition and after T009.
- Tests compare keys and types, not the exact uptime value.

## Decision

Decision D-13 chooses exact keys and an integer type for `uptime_seconds`. An exact value would fail each run.

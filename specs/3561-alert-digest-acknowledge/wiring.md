# Wiring Manifest: Alert Digest Acknowledge

**Feature**: `3561-alert-digest-acknowledge`

**Purpose**: Record the integration contract for menu 280 alert digest and menu 281 alarm acknowledgement.

## 1. Menu Contract

| Menu | Name | Safety | Required Handler |
|------|------|--------|------------------|
| 280 | Alert digest | Safe, read-only | `AlertDigestOperation.run_digest` |
| 281 | Alarm acknowledge | Destructive, human reviewed | `AlertDigestOperation.run_acknowledge` |

`AlertDigestOperation.run` can exist if it helps shared dispatch, but it is not the named menu handler for either menu.

## 2. Operation Contract

- `AlertDigestOperation.run_digest` creates the handover digest for the lookback window.
- `AlertDigestOperation.run_acknowledge` lists unacknowledged alarms for the same lookback window and acknowledges them only after exact confirmation.
- Menu 280 and menu 281 use the same source window rule.
- Menu 281 sends one bulk acknowledgement request only after valid confirmation.

## 3. Input Contract

- The default lookback window is 24 hours.
- `ALERT_DIGEST_HOURS` overrides the default when it is set to a valid hour count.
- Menu 280 supports `--test` and must not prompt in that mode.
- Menu 281 supports `--dry-run` and must not send an acknowledgement request in that mode.
- Menu 281 confirmation must be `ACK` followed by the exact alarm count shown to the operator.

## 4. Output Contract

| File | Producer | Required Content |
|------|----------|------------------|
| `data/AlertDigest.csv` | Menu 280 | One row per alarm type and site with category, severity, alarm type, site, recurrence, first seen, last seen, sample device or client, and acknowledged state. |
| `data/AlertDigest.md` | Menu 280 | Handover summary with one section per alarm category. |
| `data/AlertAcknowledgeLog.csv` | Menu 281 | One result row for each alarm id included in a confirmed acknowledgement attempt. |

## 5. Category Contract

- The category of an alarm comes from the alarm definitions constant.
- Known Mist categories are infrastructure, Marvis, security, and certificate.
- An unknown alarm type receives the category `unknown`.

## 6. Safety Contract

- Menu 280 is safe and read-only.
- Menu 281 is destructive.
- Menu 281 requires human review.
- Menu 281 sends no request until the operator types `ACK` followed by the exact alarm count.
- Menu 281 sends no request for any other input and logs the cancellation.
- Menu 281 sends no request in `--dry-run` mode and prints the alarm ids it would acknowledge.

## 7. Test Contract

- Menu 280 runs in `--test` with no prompt and writes `AlertDigest.csv` and `AlertDigest.md` under `data/`.
- Category mapping tests include a known type and an unknown type.
- Menu 281 confirmation tests cover exact confirmation, wrong count, wrong word, empty input, and dry run.
- Lookback tests cover the 24-hour default and the `ALERT_DIGEST_HOURS` override.

## 8. Release Contract

- The release note fragment `changelog.d/issue-3561-alert-digest-acknowledge.md` must exist before implementation is complete.
- This specify step does not create files outside `specs/3561-alert-digest-acknowledge/`.

## 9. Out-of-Scope Files

The feature must not edit `MistHelper.py`, `operation_registry.py`, `endpoint_primary_key_strategies.py`, `README.md`, copilot instructions, `menu_reference.md`, `web_portal`, `scripts`, guardrails, or existing `src/tests` owned by other work.

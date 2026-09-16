# Triage: Missing failure mode findings

## Re-measured counts

| Rule | Issue | 2026-09-15 count | Current main count | Repaired tree count | Decision | Follow-up |
| - | -: | -: | -: | -: | - | - |
| `missing_fm_connection_error` | #2700 | 117 | 122 | 90 | Real gap. Repair the highest-risk Mist SDK service now. Defer the rest. | #2743 |
| `missing_fm_connection_timeout` | #2701 | 116 | 121 | 90 | Real gap. Repair the highest-risk Mist SDK service now. Defer the rest. | #2744 |
| `missing_fm_empty_body` | #2702 | 120 | 125 | 115 | Mixed. The old rule missed real parser and SDK paths. Repair the highest-risk service signal now. Defer the rest. | #2745 |
| `missing_fm_http_4xx` | #2703 | 38 | 43 | 71 | Real gap. The scoped detector finds more real HTTP seams. Defer the rest. | #2746 |
| `missing_fm_http_5xx` | #2704 | 64 | 66 | 77 | Real gap. Repair the highest-risk Mist SDK service now. Defer the rest. | #2747 |
| `missing_fm_malformed_json` | #2705 | 122 | 127 | 115 | Real gap. Repair the highest-risk Mist SDK service now. Defer the rest. | #2748 |

## Group decision

All six rule groups contain real risk, because MistHelper calls the Mist cloud and must not hide network failures. The old detector also had rule noise, because it treated any `status_code` mention as HTTP behavior. This pull request repairs that misfire by reading the imported source under test.

## Misfire decision

The detector no longer flags tests that import a value object such as `ApiResult`. The source class stores response data and does not call Mist, `requests`, `httpx`, `aiohttp`, or `json.loads`. The detector also no longer treats a module import as a network source unless the test calls a symbol from that module.

## Real gap decision

`MistEndpointService` is the highest-risk service in this set. It resolves Mist SDK methods and sends cloud calls through `_invoke_with_protection`. The repair adds tests for timeout, connection error, HTTP 500, malformed JSON, and empty body behavior.

## Deferral cut

This pull request changes 10 files. It stays under the 20-file cap. It does not attempt the remaining 558 `missing_fm_*` findings. Issues #2743 through #2748 own that work.

## Detector proof

The repaired analyzer reports these metrics:

```text
detector_metric: MissingEdgeCaseDetector.inspected_modules=22
detector_metric: MissingFailureModeDetector.inspected_modules=117
```

A zero value for any `*.inspected_modules` metric now fails a real repository analyzer run. `tools.guard_proof_audit` also fails a report that contains a zero inspected-module metric.

## Failure proof for repaired tests

| Test | Observable failure signal | Why it can fail |
| - | - | - |
| `test_non_429_5xx_returns_without_retry` | `status_code` remains 500 and the call count remains 1. | If the service retries all 5xx replies or hides the status, the assertion fails. |
| `test_connection_timeout_reaches_the_caller` | `requests.exceptions.Timeout` reaches the caller. | If the service catches the exception and returns empty data, `pytest.raises` fails. |
| `test_connection_error_reaches_the_caller` | `requests.exceptions.ConnectionError` reaches the caller. | If the service catches the exception and returns empty data, `pytest.raises` fails. |
| `test_malformed_json_error_reaches_the_caller` | `json.JSONDecodeError` reaches the caller. | If the service catches the exception and returns empty data, `pytest.raises` fails. |
| `test_empty_body_warning_reaches_the_operator` | The warning log contains `Mist response body is empty`. | If the service silently maps an empty body to `{}`, the log assertion fails. |
| `test_missing_failure_mode_detector_ignores_status_value_objects` | The finding list is empty and the inspected count stays zero. | If the detector scopes on `status_code` text again, the assertion fails. |
| `test_missing_failure_mode_detector_counts_real_mist_endpoint_scope` | The inspected count is one and network rule findings appear. | If the detector stops reading imported source, the assertion fails. |

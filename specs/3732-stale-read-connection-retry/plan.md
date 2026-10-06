# Implementation Plan: Retry stale reads without repeating writes

**Issue**: #3732
**Branch**: `jmorrison-juniper-fix-3732-stale-read-recovery`
**Date**: 2026-10-06
**Spec**: [spec.md](spec.md)
**Research**: [research.md](research.md)

## Summary

The shared Mist session will use a bounded urllib3 retry policy for GET and HEAD only.
The policy will retry one stale read reset and permit at most three attempts for eligible connection failures.
An explicit method guard will stop every transport retry for POST and all other methods.
The main portal pick-list readers will validate the response status before they read response data.
An unavailable response will use one fixed operator message.
A valid empty HTTP 2xx response will keep the existing no-rows message.
The upgrade portal write-session contract will keep zero SDK and transport retries.

## Technical Context

| Item | Value |
| - | - |
| Language | Python 3.13 or newer |
| Primary dependencies | `mistapi>=0.64.0,<0.65`, `requests>=2.34.2,<3`, and `urllib3>=2.8.0,<3` |
| Storage | None |
| Testing | pytest with fake SDK responses and a local HTTP transport |
| Target platforms | Windows 11, macOS, Linux, and the Podman image |
| Project type | Python CLI with a Flask web portal |
| Performance goal | Recover one stale pooled read without an operator retry |
| Retry bound | One read retry, two connection retries, and three total attempts |
| Safety constraint | POST and every other write method get one transport attempt |
| Response constraint | Only a usable HTTP 2xx answer can become a successful pick-list result |
| Network constraint | Tests make zero live Mist API calls |
| Scope | Two production files, two reserved test files, this feature directory, and one changelog fragment |

## Retry Policy

`MistSessionConfigurator` will keep timeout and retry configuration in one adapter seam.
Its nested retry type will check the request method before urllib3 classifies the failure.
This guard is required because urllib3 does not apply `allowed_methods` to connection errors.

| Retry field | Value | Purpose |
| - | - | - |
| `total` | `2` | Permit at most three total attempts |
| `connect` | `2` | Permit two retries for eligible GET or HEAD connection failures |
| `read` | `1` | Permit one retry for a stale pooled read reset |
| `redirect` | `0` | Add no transport redirect retry |
| `status` | `0` | Add no HTTP status retry |
| `other` | `0` | Add no retry for an unclassified failure |
| `allowed_methods` | `GET`, `HEAD` | Identify the only repeatable methods |
| `status_forcelist` | Empty | Prevent status-based retries |
| `backoff_factor` | `0` | Retry the stale read without an added delay |
| `respect_retry_after_header` | `False` | Prevent a response header from enabling a retry |

The method guard will run before `Retry.increment`.
It will re-raise the original transport error for each method other than GET or HEAD.
It will then delegate eligible GET and HEAD failures to urllib3.
This design also blocks POST connection retries, which `allowed_methods` alone cannot block.

## Pick-List Response Rules

The existing `PickList` class will own response-status classification.
No new standalone wrapper function will be added.
Each picker will validate the response before it reads `response.data`.

| Response state | Result |
| - | - |
| `status_code is None` | Failed read with the Mist API reachability message |
| Missing or unusable status | Failed read with the Mist API reachability message |
| HTTP 300 through 399 | Failed read because the picker did not receive a final 2xx answer |
| HTTP 400 or more | Failed read with the Mist API reachability message |
| HTTP 200 through 299 with rows | Successful pick list |
| HTTP 200 through 299 with no rows | Valid empty pick list with the existing no-rows message |

The fixed failure message is:

> The portal could not reach the Mist API. Try again.

The log record will name the picker operation, the non-secret target identifier, and the status.
The log record will not include a token, an authorization header, or response secrets.
The exception paths will keep `logger.exception` and will use the same fixed operator message.

The site, device, wireless client, and wired client readers will use the same status rule.
The client merger will keep rows when one source succeeds.
It will retain the failed-source log record.
It will report a failed read when both sources fail or when no valid source returns rows.

## Upgrade Portal Safety Contract

This feature will not change `OrgUpgradeSession` or `OrgUpgradeService`.
The upgrade session will keep `_MAX_429_RETRIES = 0`.
Each mounted upgrade-session adapter will keep `max_retries.total` equal to zero.
`OrgUpgradeService.check_write_session` will continue to reject any transport retry.
The reserved unit test will prove that the shared read adapter cannot pass the write-session check.

## Constitution Check

| Rule | Pre-design result | Post-design result |
| - | - | - |
| Safety-first | Pass. The design repeats GET and HEAD only. | Pass. The method guard covers connection, read, and other transport failures. |
| Mist API contract | Pass. The named mistapi methods remain in use. | Pass. No direct Mist REST request is added. |
| Class-based design | Pass. Retry classification stays in `MistSessionConfigurator`. | Pass. Response classification stays in `PickList`. |
| Five-item rule | Pass with recorded existing debt. | Pass. The retry override has five parameters. |
| Inline comments | Pass as an implementation requirement. | Pass. Each changed executable line will receive a cause comment. |
| Action logging | Pass as an implementation requirement. | Pass. Each picker logs before and after the external read. |
| Secret safety | Pass. The design needs no credential value. | Pass. Tests and logs use only fake identifiers. |
| Test isolation | Pass. Tests use fake or local transport behavior. | Pass. No test uses a Mist credential fixture. |
| Release process | Pass. One unique changelog fragment is reserved. | Pass. `CHANGELOG.md` stays unchanged. |

The `specs/` and `changelog.d/` directories contain existing process-folder debt.
This feature adds only its unique required records.
A separate repository maintenance issue must reduce process-folder debt.
This feature will not mix that maintenance with issue #3732.

## Project Structure

```text
src/foundation/support/refactors/
└── initialize_mist_session.py

web_portal/routes/
└── operations.py

tests/unit/refactors/
└── test_issue_3732_read_retry.py

tests/integration/web_portal/
└── test_issue_3732_pick_list_failures.py

specs/3732-stale-read-connection-retry/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── pick-list-read.md
│   └── transport-retry.md
├── checklists/
│   └── requirements.md
└── spec.md

changelog.d/
└── issue-3732-stale-read-connection-retry.md
```

**Structure Decision**: Edit the two existing production modules.
Add only the two reserved tests and the unique feature records.
Do not change the upgrade portal source.

## File Plan

| File | Planned change |
| - | - |
| `src/foundation/support/refactors/initialize_mist_session.py` | Add the strict read-only retry policy to the existing timeout adapter. |
| `web_portal/routes/operations.py` | Validate each named picker response before data extraction. |
| `tests/unit/refactors/test_issue_3732_read_retry.py` | Prove GET and HEAD retry bounds, write refusal, status refusal, and upgrade write-session isolation. |
| `tests/integration/web_portal/test_issue_3732_pick_list_failures.py` | Prove the route results for missing status, HTTP errors, valid empty 2xx, and mixed client sources. |
| `specs/3732-stale-read-connection-retry/` | Hold the specification, plan, research, model, contracts, quickstart, and checklist. |
| `changelog.d/issue-3732-stale-read-connection-retry.md` | Record the operator-visible repair. |

## Excluded Work

- Do not change a file outside the declared file plan.
- Do not change a Mist API endpoint.
- Do not add a direct HTTP call to Mist Cloud.
- Do not change map readers or other portal routes.
- Do not change upgrade portal production code.
- Do not change dependency versions.
- Do not add a retry for an HTTP response status.
- Do not add a retry for POST, PUT, PATCH, DELETE, or another method.
- Do not use a live Mist API call in a test.

## Validation Plan

1. Run the two reserved tests.
2. Run the existing session, picker, SDK, and upgrade-session regression tests.
3. Run Ruff and Black on the scoped Python files.
4. Run mypy on the two production files with `pyproject.toml`.
5. Run Bandit on the two production files.
6. Run `symbol-diff` on each changed production module.
7. Run the test-quality preflight and changed-test gate after the implementation commit.
8. Run the STE linter on the feature artifacts and the changelog fragment.

The quickstart gives the exact commands and expected results.

## Complexity Tracking

| Existing debt | Effect on this feature | Incremental action |
| - | - | - |
| `operations.py` has more than five top-level names and several functions exceed 25 lines. | The implementation will make narrow edits and will not add a top-level helper. | Track a separate decomposition issue for the portal operations route. |
| Requests and urllib3 expose wide transport extension signatures. | The retry override uses three named inputs and one keyword context. | Keep the override at five parameters, including `self`. |
| The reserved test directories already exceed five children. | The issue requires the two reserved test paths from #3959. | Add only the reserved files and do not restructure unrelated tests. |
| The feature and changelog process folders exceed five children. | The required records use unique names and do not add shared records. | Track repository process-folder restructuring separately. |

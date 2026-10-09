# Implementation Plan: Juniper RMA Correlation for Mist Support Tickets

**Branch**: `3519-juniper-rma-correlation` | **Date**: 2026-10-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/numbered/0/0/1/0/3/0/3/4/3519-juniper-rma-correlation/spec.md`

## Summary

Add a read-only client for two Juniper service APIs. The Service Case API returns service requests and RMA details. The Service Asset API returns warranty and contract data. The feature links each Mist support ticket to its Juniper service requests by customer case number. It writes the result through `DataExporter`. It adds four operator menus (301 to 304). No write call reaches Juniper.

## Technical Context

**Language/Version**: Python 3.13 or newer (constitution minimum)

**Primary Dependencies**: `requests` (HTTP transport, existing pattern). `mistapi` 0.64.x (Mist ticket listing only). `python-dotenv` (existing `.env` loading). `structlog` is not used here. Unconfigured, it writes to stdout and bypasses the log file. These modules use the standard `logging` module (amendment A-1).

**Storage**: `DataExporter` outputs. CSV and SQLite (`data/mist_data.db`) are always written. ArangoDB mirror through `DatabaseRouter` when configured. Keys come from `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Testing**: pytest with recorded JSON fixtures. Automated tests make no network calls. One live smoke test runs only when `JUNIPER_LIVE_TESTS=1` is set.

**Target Platform**: Windows 11 (local venv) and Linux container (Podman, UID 1000).

**Project Type**: Operator menu application with library modules under `src/`.

**Performance Goals**: Default rate of 2 requests per second. 500 Mist tickets in under 30 minutes (SC-006). Asset requests in batches of 300 or fewer.

**Constraints**: Read-only. HTTPS only. Approved hosts only. No redirects. ASCII logs. No secrets in logs. Personal fields kept in the exports and masked in logs. Responses up to about 8 MB. Corporate TLS inspection may apply.

**Scale/Scope**: Up to 500 Mist support tickets per run (assumed). Service request list window of 90 days. Four new menus.

## Constitution Check

*Gate status: passed before Phase 0. Re-checked after Phase 1 design.*

| Principle | Status | Evidence |
| - | - | - |
| I. Five-Item Rule | Pass with recorded debt | New code enters `src/operations/exporting/juniper_rma/`. Its parent `src/operations/exporting/` has one child and gains one (two, allowed). Every new directory holds five or fewer children. The test package adds one direct child to `tests/unit/`, which is noncompliant. See C-1. |
| II. Class-Based Architecture | Pass | Each behavior lives in a named class. Menu entry points are static methods. No wrapper functions. |
| III. Safety-First | Pass | Operator input goes through `safe_input()`. Identifiers are validated before any call. The feature has no destructive action. Secrets are redacted at the logging boundary. |
| IV. Full Deployment Pipeline | Planned | Gates and the pipeline run during implementation. No branch pushes to `main`. |
| V. Observability and Logging | Pass | Logs use ASCII only. New modules use `structlog`. Secrets never appear in logs. |
| VI. Inline Comments | Planned | Every executable line gets an inline comment. Review checks each file. |
| VII. Action Logging | Planned | Each API call and each export write logs before and after. |

Technology and workflow constraints:

- **mistapi**: Mist ticket listing uses `mistapi.api.v1.orgs.tickets.listOrgTickets`. The Juniper service APIs are not Mist Cloud APIs. mistapi has no method for them. The Juniper client uses `requests`, the same pattern as `src/operations/execution/capture/client_pcap_downloader.py`. This is not a violation.
- **Output Backends**: Every export calls `DataExporter.write_with_format_selection()`.
- **Database Keys**: Six strategies enter `ENDPOINT_PRIMARY_KEY_STRATEGIES` before any operation code (task T005).
- **Data Directory**: Outputs go through `DataExporter`, which writes under `data/`.
- **Container Security**: No new mount, user, or port. Outbound HTTPS to the Juniper gateway is the only new network path.
- **Escalation**: This feature adds an API integration. The specification, plan, and tasks come before code.
- **Menu Sequence**: Each new menu follows the seven steps of the constitution. Step 1 (API discovery) uses `contracts/` instead of mistapi.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/0/3/0/3/4/3519-juniper-rma-correlation/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── juniper-case-api.md
│   ├── juniper-asset-api.md
│   ├── gateway-and-settings.md
│   └── menu-and-exports.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source (new)

```text
src/operations/exporting/juniper_rma/
├── __init__.py
├── settings.py              # JuniperSettings dataclass and JuniperSettingsLoader
├── api/
│   ├── __init__.py
│   ├── gateway.py           # JuniperTokenProvider and JuniperGatewayClient: HTTPS, host allowlist, token, timeouts, retries, throttle
│   ├── messages.py          # RequestMessageBuilder and ResponseStatusReader
│   ├── case_service.py      # JuniperCaseService: querysrlist, querysrdetails, queryrmadetails
│   └── asset_service.py     # JuniperAssetService: batches of 300 and not-processed retries
├── model/
│   ├── __init__.py
│   ├── service_request.py   # Service request, RMA, and RMA item parsers
│   ├── asset.py             # Asset parser: rmaInfo object or list, warranty, contracts
│   ├── run_record.py        # RunRecord counts and final status
│   └── export_rows.py       # Row builders, PersonalDataMasker (log masks), PersonalDataRetention
└── workflows/
    ├── __init__.py
    ├── access_check.py      # Menu 301
    ├── correlation.py       # Menu 302: MistTicketReader, CorrelationEngine, CorrelationWorkflow
    ├── lookup.py            # Menu 303
    └── asset_lookup.py      # Menu 304
```

Each directory holds five or fewer children. `src/operations/exporting/` holds two children after the change.

### Tests (new, see C-1)

```text
tests/unit/juniper_rma/
├── __init__.py
├── api/                     # settings, gateway (also covers messages), case service, asset service
├── model/                   # service request, asset, run record, and export row tests
├── workflows/               # access check, correlation, lookups, read-only boundary tests
└── fixtures/
    ├── __init__.py
    ├── case/                # Sample responses from the Service Case API export (five files or fewer)
    ├── asset/               # Sample responses from the Service Asset API export (three files)
    └── fake_gateway.py      # Test double that replays fixtures without network access
```

### Touched Existing Files

| File | Change |
| - | - |
| `src/foundation/support/utils/operation_registry.py` | Add entries `301` to `304`, category `interactive_safe` |
| `MistHelper.py` | Add four dispatch lines (hot file, see C-2) |
| `src/foundation/support/refactors/endpoint_primary_key_strategies.py` | Add six strategy entries |
| `deploy/.env.example` | Add Juniper variable names with comments. No values. |
| `README.md` | Update the operation count and add four menu rows |
| `changelog.d/` | Add one release-note fragment |
| Generated menu pages | Regenerate with `scripts/generate_menu_wiki.py` and `scripts.menu_api_map` |
| `.github/copilot-instructions.md` | Point the SPECKIT block to this plan |

## Design Overview

1. **Settings** (`JuniperSettingsLoader`) reads the environment and the `.env` file. It validates required names, HTTPS base addresses, the host allowlist, and numeric limits. It reports only the names of missing settings.
2. **Gateway** (`JuniperGatewayClient`) sends every request. It enforces HTTPS, the host allowlist, no redirects, timeouts, a response size cap, the rate limit, and bounded retries. Each attempt gets a new transaction identifier. It is the only code that reads the client secret or holds the bearer token (`JuniperTokenProvider`, same module, amendment A-2).
3. **Messages** (`RequestMessageBuilder`, `ResponseStatusReader`) build the request envelope. They read the body status code and the fault list. They map fault codes to plain text.
4. **Services** (`JuniperCaseService`, `JuniperAssetService`) expose the read operations. They call the gateway and parse results with the model parsers.
5. **Model** parsers accept the documented variants. Row builders keep personal fields in full, and `PersonalDataMasker.for_log` masks them in log lines. `RunRecord` tracks counts and the final status.
6. **Workflows** implement the four menus. `CorrelationEngine` applies the join rule. `CorrelationWorkflow` writes the exports through `DataExporter`.

Data flow for menu 302:

```text
Mist support tickets (listOrgTickets)
        |
        v
CorrelationEngine: exact match on customer case number
        ^
        |
Juniper list (querysrlist, last 90 days)     Older tickets: querysrdetails by case number
        |
        v
Matched requests: querysrdetails, then queryrmadetails for each RMA
        |
        v
DataExporter: CSV, SQLite, optional ArangoDB mirror, personal fields in full
```

## Complexity Tracking

| ID | Violation or debt | Why needed | Simpler alternative rejected because | Remediation |
| - | - | - | - | - |
| C-1 | `tests/unit/juniper_rma/` adds one direct child to `tests/unit/`. That parent has about 190 children. | The feature needs a test home that stays with its code. | No compliant test parent exists. `tests/contract/`, `tests/integration/`, and `tests/support/` have more than five children. `tests/fixtures/` has five. `tests/unit/org/` has seven. | New debt. Approval is needed before implementation. Separate remediation R-1: split `tests/unit/` into domain packages, then move this package into the split. |
| C-2 | `MistHelper.py`, a hot file, gains four dispatch lines. | Menu dispatch reads from this module. | A second dispatch module would split the menu map. | Only one open pull request may change `MistHelper.py` at a time. |
| C-3 | The Juniper client uses `requests` directly. | No mistapi method exists for the Juniper service APIs. | An SDK for these APIs does not exist in the repository. | None. The mistapi rule covers Mist Cloud APIs only. |

## Open Items to Confirm at Onboarding

The Juniper exports and the Mist API reference were checked on 2026-10-08. The status column records what those sources settle. Each open item needs the live key or an onboarding answer.

| ID | Item | Status | Evidence | Needed at onboarding |
| - | - | - | - | - |
| O-1 | Ticket field that holds the Juniper customer case number | Open. Two candidates. Default is `case_number` (setting `JUNIPER_TICKET_KEY_FIELD`). | Mist API reference: `case_number` is the display name of the ticket. `id` is the ticket identifier. Case export: `customerCaseNumber` is the "Customer Tracking Number" (40 characters). A production detail read returned a null customer case number for one request. | One known pair of values that matches on one field. If wrong, set the other field. |
| O-2 | Gateway credential | Resolved by the endpoints document. OAuth 2.0 client credentials. | The endpoints document lists OAuth2.0 as the mechanism and no API key. The token endpoint returns a bearer token. | Live confirmation that the bearer header works. |
| O-3 | Rate limits and quotas | Open. | Neither export states a request rate. The Asset export states payload sizes and the 300 identifier limit only. | The rate limit from Juniper. If wrong, change the default rate. |
| O-4 | Detail lookup by customer case number alone | Supported by the export. Confirm live. | The Case export lists `customerCaseNumber` as an identifier type. Fault 763 describes a case-number lookup that matches one request. | One unique case number that returns one request. If wrong, older tickets stay unmatched. |
| O-5 | Wrapper key of the `queryrmadetails` request | Partly resolved. Default is `queryRMARequest`. | Eleven real request examples each wrap their body under `<operation>Request`. The RMA request has no real example. The export never names `queryRMARequest`. | One test call with the wrapper. If it fails, test the top-level body. |
| O-6 | Asset response envelope | Both shapes are documented. The parser accepts both. | The example nests results under `queryAssetsDetailsResponse.data`. The schema lists the same keys at the top level. | The live shape. Then remove one branch. |
| O-7 | `rmaInfo` shape | Both shapes are possible. The parser accepts both. | The example shows one object. The schema enum lists `index`, which suggests a list. | The live shape. |
| O-8 | Client certificate requirement | Resolved. Certificate authentication is not used. | The endpoints document gives port 8443 for certificate authentication and port 443 for OAuth 2.0. This client uses OAuth 2.0. | None for this client. |
| O-9 | Production base addresses | Resolved by the endpoints document. Confirm the Asset API is enabled. | The endpoints document lists `https://apigw.juniper.net/` and the Case API endpoints. It does not list the Asset API. | Confirmation that the Asset API is enabled for this client. |
| O-10 | Placement of `customerSourceID` and `customerUniqueTransactionID` | Resolved per operation by the export. Confirm the two detail placements. | The placement table in `contracts/juniper-case-api.md`. | Confirmation for `querysrdetails` and `queryrmadetails`. |

## Phase Outputs

- **Phase 0**: [research.md](research.md) records the decisions and alternatives.
- **Phase 1**: [data-model.md](data-model.md), [contracts/](contracts/), and [quickstart.md](quickstart.md).
- **Phase 2**: [tasks.md](tasks.md) orders the work by user story.

## Risks

| Risk | Mitigation |
| - | - |
| The join rule (O-1) does not match Mist data. | Unmatched rows show the reason. Confirm the rule during onboarding before a production run. |
| Personal data reaches a log. | One log masking boundary (`PersonalDataMasker.for_log`). A scan test (SC-004). The exports keep personal fields in full by operator decision (2026-10-08). |
| Free-text ticket subjects carry personal data. | Subjects are not masked. Operators must not place personal data in subjects. Recorded here as a known gap. |
| A write call reaches Juniper. | The client has no write method. A read-only boundary test fails on any write operation name. |
| Corporate TLS inspection breaks calls. | `JUNIPER_CA_BUNDLE` setting. The access check names the TLS fault. See R-13. |
| Documentation variants break parsing. | Lenient parsers. Fixtures from the exports. Onboarding checks (O-5 to O-7). |
| Rate limits stop a long run. | Configurable rate. Bounded retries. Incomplete run status with the count of unfinished items. |

## Quality Gates for Implementation

Run these gates before the pull request. The table lists each gate and its threshold.

| Gate | Command | Threshold |
| - | - | - |
| Syntax | `python -m py_compile` on each changed file | No output |
| Lint and format | `python -m ruff check .` and `python -m black --check .` | Zero findings |
| Types | `python -m mypy` with the `MYPY_PATHS` value from `.github/workflows/ci.yml` | Success |
| Tests | `pytest tests/unit/juniper_rma` | At least 80 percent coverage of the new modules |
| Complexity | `radon cc` | No block above complexity 10 |
| Quality | `pylint`, `interrogate`, and `pydocstyle` | Pylint at least 9.5, interrogate at least 90 percent, pydocstyle with no violations |
| Security | `bandit`, `pip-audit`, and `vulture` | Zero findings |

Run the STE linter (`python -m misthelper_devtools.ste_linter`) on the Markdown files in this folder.

Regenerate the menu reference pages. The `menu_reference_drift` job must pass.

## Done When

- [ ] Phase 0 and Phase 1 artifacts exist and agree with each other.
- [ ] The Constitution Check has no violation that is not recorded in C-1 to C-3.
- [ ] Tasks cover every functional requirement in the spec.

## Implementation Amendments

These amendments record each decision that changed the plan during implementation. Each amendment gives the reason.

- **A-1 Logging**: The modules use the standard `logging` module, not `structlog`. Unconfigured `structlog` writes to stdout and bypasses the log file. The log lines keep the key=value form of `contracts/gateway-and-settings.md`.
- **A-2 Token provider**: `JuniperTokenProvider` lives in `api/gateway.py`. A separate module would give `api/` six children and break the five-item rule. The token request follows the endpoints document: a Basic header and the form fields `grant_type`, `client_id`, and `client_secret`.
- **A-3 Personal data**: Personal fields are stored in full in the exports, by operator decision (2026-10-08). The log lines mask them. `DataExporter` writes one format for each call. `PersonalDataRetention` removes the export files that hold personal fields when they pass `JUNIPER_PII_RETENTION_DAYS`.
- **A-4 Strategy names**: The asset coverage export uses `juniperQueryAssetCoverage`, a seventh strategy. Sharing the asset strategy would overwrite coverage rows in the database mirror, because the two files have different keys.
- **A-5 Fixtures**: The fixtures are synthetic values that follow the documented shapes. The Case export holds 21 e-mail-like strings, so a copy would publish contact data into the repository.
- **A-6 Failed list**: A failed request list gives the run record the status `failed`. No ticket is classified in that case.
- **A-7 Live check**: The one live check reads `MISTHELPER_ENV_FILE`, or `.env` in the working folder. It runs only with `JUNIPER_LIVE_TESTS=1`. It sends one read-only list request for a one-day window.
- **A-8 Portal**: Menus 301 to 304 join `web_portal/menu_registry.py` and a new `Juniper RMA` range in `web_portal/services/operation.py`.
- **A-9 Onboarding items**: Live confirmation of O-1, O-3, O-4, O-5, O-7, and O-9 remains open. The first live run closes them.


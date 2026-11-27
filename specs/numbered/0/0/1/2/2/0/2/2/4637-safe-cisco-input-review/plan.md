# Implementation Plan: Safe Cisco Input and Structured Review

**Branch**: `feat/4637-cisco-input-review` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric record at `specs/numbered/0/0/1/2/2/0/2/2/4637-safe-cisco-input-review/`. The route follows the base-5 rule in `.specify/scripts/powershell/spec-route.ps1`. Decimal 4637 equals `122022` in base 5. Padded to eight levels, it gives `0/0/1/2/2/0/2/2`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Add stored inputs, prepopulated selection, and a display-only structured review to the isolated Cisco converter. The change follows issue 4636 for the `state/` layout. It converts `state/intake.py` into an `intake/` package, because the module reaches its five-name limit. It adds two routes and one catalog route to the isolated blueprint. It keeps the DNS preview, review, and export shapes unchanged. It adds no Mist call, no dependency, no environment variable, and no shared portal change.

## Technical Context

- **Language/Version**: Python 3.15 or newer. Source: `.github/copilot-instructions.md`, section Language and environment, line 18.
- **Primary Dependencies**: Flask 3.1.3 and Flask-WTF 1.3.0, pinned in `requirements.txt` lines 49 and 54. The standard library supplies `hashlib`, `uuid`, `os`, `pathlib`, `ipaddress`, and `datetime`.
- **Storage**: Private files under `data/cisco_config_converter/input/` when retention is enabled. No database and no operational store.
- **Testing**: pytest with `tmp_path`, the Flask test client, and Playwright for the isolated browser journey.
- **Target Platform**: Windows 11, macOS, Linux, and the Podman container that runs as UID 1000.
- **Project Type**: Feature package inside the web portal interface package.
- **Performance Goals**: Each request reads at most 16,777,216 bytes plus 16,384 bytes of multipart allowance. No latency target exists.
- **Constraints**: No Mist call. No shared route registration. No new dependency. No new environment variable.
- **Scale/Scope**: Four new modules in one converted package, one converted module, two new routes, one catalog route, eleven families, and forty planned tests.

## Constitution Check

*GATE: Must pass before implementation. Re-check after each audit task.*

| Rule | Result | Reason |
| --- | --- | --- |
| I. Five-Item Rule, levels | Pass | The converter root keeps five children. `state/intake/` and the new test folder each hold five children. |
| I. Five-Item Rule, functions | Pass by design | Each planned method has five parameters or fewer and five blocks or fewer. Task T011 audits the 25-line limit and the complexity gate. |
| I. Structural debt | Pass | No change touches `src/interfaces/portals/`, `tests/contract/`, `tests/e2e/web_portal/` as a parent, or `web_portal/`. |
| II. Class-based architecture | Pass | Each behavior sits in a named class. No wrapper function is planned. |
| III. Safety-first input | Pass | Each external input validates before use. The server creates stored identifiers. No keyboard read is added, so `safe_input` does not apply. |
| III. Destructive operations | Pass | The change deletes no file. It writes no Mist object. A failed save removes only the file that the same save created. |
| III. Secrets in logs | Pass | Logs omit source text, file names, and secret values. The test `test_logs_omit_source_text_and_original_names` checks the logs. |
| IV. Deployment pipeline | Pass for this record | No code changed in this drafting pass. The pipeline applies to tasks T-LOCAL-GATES through T-MERGE. |
| V. ASCII logs | Pass | Each planned message uses ASCII text only. |
| V. Structured logs | Pass with reviewer check | The new modules use standard `logging` with `key=value` text, as decision D-18 records. The reviewer checks that reading. Issue 4636 item U-2 tracks the same question. |
| VI. Inline comments | Fail now, pass after T011 | `routes.py` and `conversion.py` hold no `#` comment. `models.py` holds one. Each touched or new line gets a comment in T007 and T009. |
| VII. Action logging | Fail now, pass after T011 | `ConverterRoutes.page` and `ConverterInput.source` hold no log call. Task T011 adds the logs before and after each action. |
| Technology: Python | Pass | Python 3.15 standard library and the pinned Flask. |
| Technology: mistapi | Pass, not applicable | No Mist REST request exists in this change. The pin at `requirements.txt` line 129 stays unchanged. |
| Technology: owned WebSocket | Not applicable | No WebSocket transport exists in this change. |
| Technology: UV and requirements | Pass | No dependency changes. |
| Technology: Podman | Pass | No container file changes. |
| Technology: test containers | Not applicable | No container starts for the tests. |
| Technology: file paths | Pass | The code uses `pathlib.Path` and `os` functions only. |
| Technology: operational store | Not applicable | Stored inputs are not operational records. Issue 4636 owns the state store. |
| Technology: export boundary | Not applicable | The change exports no Mist API data. |
| Technology: database keys | Not applicable | The change writes no Mist entity row. Decision D-5 explains the stored identifier. |
| Technology: data directory | Pass | Stored inputs sit under `data/`, which `.gitignore` line 95 ignores. Production enablement waits for decision D-11. |
| Technology: container security | Pass | The change alters no ownership. Enabling retention later needs UID 1000 write access, as `documentation/container-deployment.md` line 114 states. |
| Technology: Zscaler | Not applicable | No container build or push occurs. |
| Development: menu operations | Not applicable | No menu changes. |
| Development: testing skip list | Not applicable | No menu test changes. |
| Development: documentation | Pass | `README.md` and the operator guide do not mention the converter. The changelog fragment is decision D-19. |
| Escalation | Pass | The change touches more than three files and two classes. This record exists. |
| Multi-agent git: issue first | Pass | Issue 4637 exists with the `feature` and `web-portal` labels. |
| Multi-agent git: branch | Pass, planned | The branch `feat/4637-cisco-input-review` starts from `main` at task T-PR. |
| Multi-agent git: overlap | Pass | Open PR #4208 owns `web_portal/app.py` and `web_portal/templates/base.html`. Open PR #4813 names a different changelog fragment. This change touches neither file. |

## Capacity and Structure Inventory

The inventory uses `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, read on 2026-11-26. Remote listings and blob SHAs appear in `design/research.md`, section R4.

| Directory | Children now | Children after this change | Limit | Status |
| --- | --- | --- | --- | --- |
| `src/interfaces/portals/cisco_config_converter/` | 5: `__init__.py`, `conversion.py`, `models.py`, `presentation/`, `routes.py` | 5: `__init__.py`, `conversion.py`, `presentation/`, `routes.py`, `state/` after issue 4636 | 5 | At limit. No child is added. |
| `src/interfaces/portals/` | 6: `__init__.py`, `cisco_config_converter/`, `guest_authorizations.py`, `licensing_comparison/`, `upgrade_portal/`, `wan_dashboard/` | 6 | 5 | Over limit. Not touched. Remediation R-1. |
| `state/` after issue 4636 | 5 | 5: `__init__.py`, `intake/`, `lifecycle/`, `proposal.py`, `storage/` | 5 | At limit. `intake.py` becomes `intake/`. |
| `state/intake/` | Not present | 5: `__init__.py`, `source.py`, `review.py`, `private_files.py`, `observations.py` | 5 | At limit. |
| `tests/integration/web_portal/cisco_config_converter/` | 2: `__init__.py`, `test_routes.py` | 4: adds `input/` and keeps the issue 4636 `state/` folder | 5 | Compliant. |
| `tests/integration/web_portal/cisco_config_converter/input/` | Not present | 5: `__init__.py` and four test modules | 5 | At limit. |
| `tests/contract/` | 17 | 17 | 5 | Over limit. Not used. Decision D-17. |
| `tests/e2e/web_portal/` | 32 | 32 | 5 | Over limit. One existing file gains test functions. No child is added. |
| `tests/unit/marvis/mist/resources/gateway/overrides/` | 5 | 5 | 5 | At limit. One import line changes. No child is added. |
| `web_portal/` | 7 | 7 | 5 | Over limit. Not touched. |

The nested package guard counts direct Python modules, except `__init__.py`, plus directories that hold tracked Python files. The constitution counts every physical child, including `__init__.py`. This record reports both counts for each directory.

## Converted Layout

```text
src/interfaces/portals/cisco_config_converter/
  __init__.py                  unchanged
  conversion.py                import line changes, DNS logic unchanged
  presentation/                converter.html and converter.js change
  routes.py                    six routes, constants, comments, action logs
  state/                       issue 4636 package
    __init__.py                docstring only
    intake/                    replaces intake.py
      __init__.py              docstring only
      source.py                SOURCE_SUFFIXES, SOURCE_LIMIT_BYTES, SourceConfiguration, SourceRecord
      review.py                REVIEW_LIFETIME, ReviewState, ReviewRecord
      private_files.py         INPUT_IDENTIFIER_PATTERN, PrivateInputCatalog, PrivateInputRetention
      observations.py          FAMILY_RULES, ObservationReview
    proposal.py                issue 4636
    lifecycle/                 issue 4636
    storage/                   issue 4636
```

The `intake/` package keeps each module at four top-level names or fewer. The package holds five children, which is the limit.

## Symbol Map

Task T004 runs `symbol-diff` for each removed or moved module. Each name keeps its spelling and its class body. Only the module path changes.

| Name | Location after issue 4636 | Location after this change |
| --- | --- | --- |
| `REVIEW_LIFETIME` | `state/intake.py` | `state/intake/review.py` |
| `SourceConfiguration` | `state/intake.py` | `state/intake/source.py` |
| `ReviewState` | `state/intake.py` | `state/intake/review.py` |
| `SourceRecord` | `state/intake.py` | `state/intake/source.py` |
| `ReviewRecord` | `state/intake.py` | `state/intake/review.py` |

New names appear in this change only: `SOURCE_SUFFIXES`, `SOURCE_LIMIT_BYTES`, `INPUT_IDENTIFIER_PATTERN`, `PrivateInputCatalog`, `PrivateInputRetention`, `FAMILY_RULES`, and `ObservationReview`. Class `__module__` values change for the five moved names. The repository move rules require this record of the change. Source: `.github/copilot-instructions.md`, section Move a module, line 261.

## Import Updates

| File | Line after issue 4636 | Line after this change |
| --- | --- | --- |
| `src/interfaces/portals/cisco_config_converter/conversion.py` | `from .state.intake import SourceConfiguration` | `from .state.intake.source import SourceConfiguration` |
| `src/interfaces/portals/cisco_config_converter/routes.py` | `from .state.intake import ReviewState, SourceConfiguration` | Four lines: `ReviewState` from `.state.intake.review`, `SourceConfiguration` and `SOURCE_LIMIT_BYTES` from `.state.intake.source`, `PrivateInputCatalog` and `PrivateInputRetention` from `.state.intake.private_files`, and `ObservationReview` from `.state.intake.observations` |
| `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py` | Line 6 imports `SourceConfiguration` from `state.intake` | Line 6 imports from `state.intake.source` |

No module keeps the old path as a re-export. The old-path search in task T012 must return no match.

## Architecture

The request flow follows this order. Each step passes one value to the next step.

1. The browser sends either `file` or `stored_id`, plus `name`, `type`, and optional `retain`. `ConverterInput` refuses a request that sends both or neither.
2. For an upload, `ConverterInput` reads at most `SOURCE_LIMIT_BYTES + 1` bytes. For a stored identifier, `PrivateInputCatalog` resolves one file under the contained root.
3. `SourceConfiguration.read` checks the suffix, the byte limit, the strict UTF-8 text, the null characters, and the name. It returns a source in memory.
4. `/preview` clears the earlier review and converts the source with `IOSDnsConverter`. It saves the source when `retain` is set and retention is enabled. Then it publishes the review digest.
5. `/observations` builds `ObservationReview` sections and unsupported lines from the source. It writes no session value and it changes no review state.
6. `/inputs` returns the catalog metadata. It exposes no path.
7. `/review` and `/export` keep their current behavior.

Caution: The preview saves a stored input before it publishes the review. Keep this order, so an operator cannot approve a save that failed.

## File-by-File Change Map

| Path | Action | Content |
| --- | --- | --- |
| `src/interfaces/portals/cisco_config_converter/state/intake.py` | Delete after issue 4636 | Replaced by the `intake/` package. |
| `src/interfaces/portals/cisco_config_converter/state/intake/__init__.py` | Add | Module docstring only. |
| `src/interfaces/portals/cisco_config_converter/state/intake/source.py` | Add | Moved `SourceConfiguration` with the existing suffix, size, UTF-8, and null rules. Adds a refusal for control characters in file names. Holds `SourceRecord`. |
| `src/interfaces/portals/cisco_config_converter/state/intake/review.py` | Add | Moved `ReviewState` and `REVIEW_LIFETIME`. Holds `ReviewRecord`. |
| `src/interfaces/portals/cisco_config_converter/state/intake/private_files.py` | Add | `PrivateInputCatalog` lists contained stored inputs. `PrivateInputRetention` saves one input with exclusive creation. |
| `src/interfaces/portals/cisco_config_converter/state/intake/observations.py` | Add | `FAMILY_RULES` holds eleven families. `ObservationReview` builds sections and unsupported lines. |
| `src/interfaces/portals/cisco_config_converter/routes.py` | Modify | Adds `/inputs` and `/observations`. `/preview` accepts `stored_id` and `retain`. Replaces three copies of the byte limit with `SOURCE_LIMIT_BYTES`. Adds comments and action logs to each touched line. |
| `src/interfaces/portals/cisco_config_converter/conversion.py` | Modify | Import line only, after issue 4636. Adds comments to the touched line. |
| `src/interfaces/portals/cisco_config_converter/presentation/converter.html` | Modify | Adds the stored selection list, the retain checkbox, the observation sections, and the unsupported section. Each new control has a stable `data-testid`. |
| `src/interfaces/portals/cisco_config_converter/presentation/converter.js` | Modify | Loads the catalog, sends `file` or `stored_id`, renders sections with `textContent`, and clears sections after a change. |
| `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py` | Modify | Import line only. |
| `tests/integration/web_portal/cisco_config_converter/input/__init__.py` | Add | Package marker. |
| `tests/integration/web_portal/cisco_config_converter/input/test_input_contract.py` | Add | Ten contract tests (task T005). |
| `tests/integration/web_portal/cisco_config_converter/input/test_catalog_and_retention.py` | Add | Eight catalog and retention tests (task T006). |
| `tests/integration/web_portal/cisco_config_converter/input/test_observations.py` | Add | Eleven observation tests (task T008). |
| `tests/integration/web_portal/cisco_config_converter/input/test_input_routes.py` | Add | Nine route tests (tasks T006 and T008). |
| `tests/e2e/web_portal/test_portal_smoke.py` | Modify | Adds two test functions to the existing class `TestCiscoOfflinePreview`. |
| `changelog.d/issue-4637-safe-cisco-input-review.md` | Add | One `###` heading and one `Added` bullet that names issue 4637. |
| `data/cisco_config_converter/input/` | Runtime only | Created only when retention is enabled. Git ignores it and no commit includes it. |

Unchanged paths: `web_portal/app.py`, `web_portal/templates/base.html`, `web_portal/services/config.py`, `web_portal/services/data_browser.py`, `web_portal/services/output_scan.py`, `compose.yml`, `.gitignore`, `requirements.txt`, and `documentation/`.

## Dependencies

- No package is added and no pin changes.
- The new modules use the standard library and the pinned Flask.
- The stored input files carry no seal. The seal in issue 4636 applies to state records only.
- The code reads no `PORTAL_SECRET_KEY` value.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Issue 4636 does not land first, or it changes `state/intake.py`. | Task T004 blocks. The file map drifts. | Start T004 only after issue 4636 merges. Repeat the file-map check in task T001. |
| The shared data browser serves stored inputs. | Customer configuration reaches an operator who should not read it. | Retention stays disabled (decision D-11). A separate exclusion issue comes before enablement (remediation R-4). |
| Windows does not support `O_NOFOLLOW`. | A race can replace a checked file before it opens. | Check the link before and after opening. Record the residual race as unresolved item U-3. |
| A rule misreads a source line. | The review shows a wrong value. | Each rule shows the matched text only. Each family has a positive and a negative test. Unknown lines stay unsupported. |
| A browser test flakes. | The gate reports noise. | Use narrow edits, the strict environment variable, and failure screenshots as CI artifacts. |
| A reviewer rejects the logging reading of Principle V. | The pull request fails review. | Decision D-18 records the reading. The reviewer confirms it in the pull request. |
| Directory counts grow after this change. | The guard fails in a later change. | Test 10 checks the `intake/` package and the input test folder. Task T012 runs the nested package guard. |
| A failed write leaves a partial stored file. | The catalog lists an incomplete input. | The save removes the file that it created when a write fails. It then returns 409. |

## Rollback Steps

1. Revert the squash commit on `main` through a new pull request.
2. Confirm that `state/intake.py` returns from issue 4636 and that `state/intake/` is gone.
3. Confirm that `tests/integration/web_portal/cisco_config_converter/test_routes.py` passes.
4. Remove `data/cisco_config_converter/input/` only when a test or a manual run created it. Production retention stays disabled, so production holds no such folder.

Caution: Rollback restores the DNS preview only. Stored inputs created in a test run remain until an operator removes them.

## Complexity Tracking

| Item | Type | Reason | Action |
| --- | --- | --- | --- |
| `state/intake.py` becomes a package. | New design that replaces the issue 4636 module. | The module would exceed five top-level names. | Recorded in decision D-16 and in the symbol map. |
| `tests/contract/` is not used. | Avoided debt. | The folder already holds 17 children. | Decision D-17. |
| `tests/e2e/web_portal/` gains functions only. | Grandfathered parent, narrow edit. | The folder already holds 32 children. | Remediation R-3 from issue 4636. |
| `web_portal/` is not touched. | Grandfathered parent. | The folder already holds 7 children. | Remediation not required by this change. |

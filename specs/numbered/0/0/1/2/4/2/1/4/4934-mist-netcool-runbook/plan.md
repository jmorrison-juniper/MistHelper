# Implementation Plan: NOC runbook for the Juniper Mist to IBM Netcool alarm integration

**Branch**: `feat/4934-mist-netcool-runbook` | **Date**: 2026-11-25 | **Spec**: [spec.md](spec.md)

**Input**: The feature specification in this folder, and the sources that `design/research.md` names for each decision.

## Summary

This feature adds a NOC runbook and a read-only smoke test.

The runbook is one Markdown file that explains how to collect Mist alarms and events, send them to IBM Netcool, and operate the feed.

The baseline is REST polling of four organization search families.

Webhooks and a hybrid design need approval as enhancements.

The smoke test sends GET requests only through `mistapi.APISession`, and it checks the runbook facts and the readiness of one Mist organization.

Each run stays within a request budget of 60 requests and writes a redacted JSON evidence record under `test-artifacts/`.

An offline document test checks the runbook without a token or a network connection.

## Technical Context

**Language/Version**: Python 3.15 or newer, because `pyproject.toml` requires `>=3.15`.

**Primary Dependencies**: `mistapi==0.64.1` and `python-dotenv==1.2.4`, plus the Python standard library.

The pins come from `requirements.txt` lines 129 and 203. The repository range for the SDK is `mistapi>=0.64.0,<0.65`.

**Storage**: None. The evidence record is a JSON file under `test-artifacts/`, and `.gitignore` line 107 ignores that folder.

**Testing**: pytest with mocked `mistapi` sessions. The offline document test needs no token and no network access.

**Target Platform**: Windows 11, macOS, and Linux.

**Project Type**: Documentation and a command-line verification tool.

**Performance Goals**: The default budget is 60 requests for each run. A typical run takes 1 to 3 minutes. Two timeouts in one run bound the wait for stalled calls to about 60 seconds (spec FR-038). The worst case is about 33 minutes at the default budget and the default call timeout. The derivation is in `design/contracts/smoke-cli.md`, section 6.

**Constraints**: GET only. Each request that takes a limit sends `limit=1000`, except the `limit=5000` probe of SMK-09 (spec FR-033). Output is ASCII only, and no secret appears in any output.

**Scale/Scope**: One Mist organization in each run.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Initial gate result: pass with the exceptions in Complexity Tracking. The owner approves each exception before the implementation phase starts.

Post-design gate result: Principle I is open (issue #4937), and the other principles pass. The check ran after `design/data-model.md`, `design/contracts/`, and `design/quickstart.md` existed. Analysis pass 2 (`analysis.md`) reports 39 findings. The pass 2 decisions resolve 37 of them. Two items stay open: P2-C1, the folder rule of principle I (issue #4937), and U4, the live discovery run (tasks T021 and T022). Remediation 1 and the pass 2 decisions are recorded in `analysis.md`.

| Principle | Result | Plan |
| --- | --- | --- |
| I. Five-item rule | Pass with exceptions | The new package and its modules obey the five-item rule. The change adds direct children to three parents that already exceed five children. Complexity Tracking records each exception. |
| II. Class-based architecture | Pass | Each behavior sits in a named class, for example `SmokeCommand`, `ReadOnlyMistClient`, `RunbookClaims`, and `EvidenceWriter`. No wrapper function delegates to a method. Names use full words. |
| III. Safety-first | Pass | The token comes from an environment variable or an ignored file (FR-032). The options and the organization identifier are validated first. The smoke test sends no write request, so no typed confirmation applies. |
| IV. Full deployment pipeline | Pass with owner steps | The owner merges the pull request and runs steps 9 to 12. The change adds no runtime code to the product container. The coordinator runs steps 1 to 8. |
| V. Observability and logging | Pass by design | Log output is ASCII only (FR-047). Each log call uses a `%s` message template with positional values, for example `logger.info("GET %s started", path_label)`. The `structlog.stdlib.PositionalArgumentsFormatter()` processor formats each template, and the code never formats a message before the call. The client redacts each token at the logging boundary (FR-044). |
| VI. Inline comments | Pass by design | Each executable line of new code carries an inline comment. The review checks each line. |
| VII. Action logging | Pass by design | Each action has an `info` line before it and a `debug` line after it. Each exception has an `error` line with its context. Each log call follows the template rule of principle V. |
| Technology and compatibility | Pass | The code targets Python 3.15 or newer, and `mistapi` is the only interface to the Mist REST API. Paths use `pathlib.Path`. The smoke test collects no product data and writes no product output. The evidence file goes to `test-artifacts/`, which the constitution permits. |
| Development workflow and gates | Pass | The branch uses the type `feat`, which the constitution lists. |

Five-item rule interpretation (the reading of constitution principle I in `.specify/memory/constitution.md`):

- A package holds five modules or subpackages or fewer, not counting `__init__.py`.

- A module holds five top-level classes, functions, or constants or fewer, not counting imports and the `if __name__ == "__main__":` block.

- A class holds five methods or fewer, counting `__init__` and private methods. Dataclass fields are data, not methods.

- A function has five parameters or fewer, not counting `self`, and five logical blocks or fewer. It has 25 lines of code or fewer, not counting its docstring.

- Cyclomatic complexity is 10 or less, checked with radon and complexity-gate.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/2/1/4/4934-mist-netcool-runbook/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      runbook-structure.md
      smoke-cli.md
      evidence.md
    checklists/
      requirements.md
      runbook.md
      security.md
```

### Source Code (repository root)

| Path | Purpose |
| --- | --- |
| `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md` | The runbook, one self-contained file. |
| `scripts/netcool_runbook_smoke/__init__.py` | The package docstring and `__version__ = "1.0.0"`. The version belongs to the smoke tool, not to the constitution. |
| `scripts/netcool_runbook_smoke/__main__.py` | `SmokeSettings`, `SettingsLoader`, `IdentityRules`, `CheckSequence`, and `SmokeCommand` for the command line entry point, the settings, the check order, and the run order. |
| `scripts/netcool_runbook_smoke/client.py` | `CallRecord`, `PageSet`, `CallGovernor`, `PageWalker`, and `ReadOnlyMistClient` for GET calls, the budget, the timeout, the paging, and the origin check. |
| `scripts/netcool_runbook_smoke/command.py` | `TracebackFreeFormatter`, `StandardLogging`, `LogSetup`, `EnvFileReader`, and `RunReport` for the logging, the env file, and the run summary. |
| `scripts/netcool_runbook_smoke/documents.py` | `MarkdownTables`, `RunbookClaims`, `OpenApiIndex`, `EvidenceRedactor`, and `EvidenceWriter` for the runbook, the OpenAPI file, and the evidence record. |
| `scripts/netcool_runbook_smoke/checks/__init__.py` | `CheckStatus`, `CheckResult`, `StopRun`, `CheckContext`, and `EvidenceBuilder` for the shared check types. |
| `scripts/netcool_runbook_smoke/checks/identity.py` | `DocumentLoader`, `RunbookStructure`, `PrivilegeReader`, `UsageReader`, and `IdentityChecks` for SMK-01 to SMK-04. |
| `scripts/netcool_runbook_smoke/checks/catalogs.py` | `CatalogStore`, `NameComparison`, and `CatalogChecks` for SMK-05. |
| `scripts/netcool_runbook_smoke/checks/searches.py` | `SearchObservations`, `FamilyJudge`, `CountComparison`, `CountVerdict`, and `SearchChecks` for SMK-06 and SMK-07. |
| `scripts/netcool_runbook_smoke/checks/scope.py` | `FilterProbes`, `ScopeChecks`, `SiteListing`, `InventoryReader`, and `InventoryChecks` for SMK-08 to SMK-10. |
| `scripts/netcool_runbook_smoke/checks/support.py` | `SessionOpener` and `RequestTrail` for the SDK session and the request trail of each check. |
| `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_client.py` | Client tests: status matrix, HTTP 429, timeout, connection error, malformed JSON, empty body, foreign origin, repeated page, and budget. |
| `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_documents.py` | Parser tests on small Markdown fixtures, and tests of the OpenAPI index. |
| `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_checks.py` | Check tests with a fake client. |
| `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_command.py` | Settings, exit codes, evidence writing, and redaction. |
| `tests/unit/scripts/netcool_runbook_smoke/test_netcool_runbook_document.py` | The offline document test on the real runbook. |
| `changelog.d/issue-4934-mist-netcool-runbook.md` | The release-note fragment, with one `### Added` heading and one bullet that names issue #4934. |

### Structure Decision

The package `scripts/netcool_runbook_smoke/` holds five counted children: `__main__.py`, `client.py`, `command.py`, `documents.py`, and the subpackage `checks/`. The subpackage `checks/` holds five counted children: `catalogs.py`, `identity.py`, `scope.py`, `searches.py`, and `support.py`. The counts exclude `__init__.py`, as the repository guard `tests/guardrails/test_move_module_guidance.py` does. Each level stays within five children.

The test files go in `tests/unit/scripts/netcool_runbook_smoke/`, because CI runs the `tests/unit` folder and the test folders that the shards list (`.github/workflows/ci.yml` lines 252 to 269). The folder holds five test files and no `__init__.py`.

The runbook goes in `documentation/noc-runbooks/`, because FR-001 fixes that path. README.md does not change, because the change adds no MistHelper operation. Line 121 of README.md already links the runbook folder.

## Complexity Tracking

Each row records an existing violation that this feature touches. Counts are tracked children at HEAD of this worktree, measured with `git ls-tree` on 2026-11-25.

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| `scripts/` holds 52 children. This feature adds one direct child, `netcool_runbook_smoke/`, so the count becomes 53. | The repository keeps its verification scripts in `scripts/`. The package runs as `python -m scripts.netcool_runbook_smoke`. | `src/` ships in the product wheel, and its structure guards are strict (`tests/guardrails/test_move_module_guidance.py`). This tool verifies documentation, and a move of existing files is out of scope. |
| `tests/unit/scripts/` holds 9 children. This feature adds one direct child, `netcool_runbook_smoke/`, so the count becomes 10. The folder holds the five test files. | The five test files follow the test layout in `design/contracts/smoke-cli.md`, section 10. | Five test files directly in `tests/unit/scripts/` would make 14 children. The nested folder keeps the count at 10. |
| `documentation/noc-runbooks/` holds 16 children. This feature adds the runbook, so the count becomes 17. | FR-001 fixes the path, and customers already receive links to `documentation/noc-runbooks/`. The plan treats the runbook as a required unique record in an established process folder. | No alternative exists inside this feature, because FR-001 fixes the path. The owner confirms the interpretation. |
| `changelog.d/` holds 332 children. This feature adds one fragment. | The fragment is the required unique record of this change, in an established process folder. | Not applicable. The constitution names this folder as an exception. |
| Function-level limits: 14 functions exceed five operations in one block or 25 lines. `checks/scope.py`: `FilterProbes.filter_verdict`, `FilterProbes.record`, `ScopeChecks.smk_08`, `ScopeChecks.smk_09`, `ScopeChecks._site_part`, `SiteListing.first_site`, `InventoryReader.count_sum`, `InventoryReader.webhook_part`, `InventoryChecks.smk_10`, and `InventoryChecks._judge`. `checks/searches.py`: `SearchChecks.smk_06` and `SearchChecks.smk_07`. `client.py`: `CallGovernor._attempt` and `CallGovernor._run_with_timeout`. | The five-name, five-member, and five-child limits leave no helper capacity in these modules and classes. | Helper functions would add names or members to modules and classes that already hold five. Each CI gate passes (complexity 10 or less). |

The new package and the new test folder obey the five-item rule inside. Keeping the two new folders is an assumption that the owner confirms in the pull request review. Issue #4937 asks the owner for the constitution rule that covers them. The runbook is a unique process record in the established process folder `documentation/noc-runbooks/`, so the Principle I exception covers it. A move of the two new folders is a small change. The function-level row records 14 functions above the function-level limits. The owner decides that row in the pull request review, together with issue #4937.

Separate remediation action: file a separate issue to group the children of `scripts/`, `tests/unit/scripts/`, and `documentation/noc-runbooks/`. This feature adds children to those folders, and it moves no file.

## Phases

### Phase 0: Outline and research

Output: `design/research.md`. It records decisions D1 to D15. Each decision lists its sources. Each fact that the live smoke run must confirm carries the mark "Pending live verification". The research also records four source conflicts that the owner must resolve.

### Phase 1: Design and contracts

Output: `design/data-model.md`, the three contract files under `design/contracts/`, and `design/quickstart.md`. The Constitution Check runs again after this phase.

### Phase 2: Task approach

The file `tasks.md` comes from `speckit.tasks`. The task order follows the dependencies. The first tasks cover the runbook structure, the parser, and the OpenAPI index. The next tasks cover the client, the checks, the evidence writer, and the command. The last tasks cover the offline document test, the changelog fragment, and the quickstart. The live smoke run comes after the tasks, with the author's credentials.

## Assumptions

The plan records four assumptions. Each assumption needs owner confirmation.

A1: Accepted by the coordinator. A connection failure during token validation maps to the Configuration error class, exit code 2. The regional host belongs to the configuration, and spec FR-045 states the mapping.

A2: The client sends `limit=1000` on each paged request. The spec states no maximum for `limit`, and SMK-09 records the behavior at 5000.

A3: The approved origin is the regional host from `MIST_HOST`. Spec FR-031 states that the operator sets the approved origin to the regional host.

A4: No source checked states whether the SDK session exposes a `requests.Session`. The client never reads the private `_session` attribute of the SDK. The evidence record holds `sdk_retry_possible: true`, because the SDK can retry inside one client call.

## Open Items for the Owner

Each item below names its decision in `design/research.md`. The coordinator resolved items 1 to 4 and item 6.

Item 1: Resolved. The organization alarm search has the query parameters `site_id` and `ack_admin_name` (research D2). The OpenAPI file confirms both parameters.

Item 2: Resolved. The organization and site Mist Edge event searches have `start`, `end`, and `duration` (research D8). The OpenAPI file confirms these parameters.

Item 3: Resolved. The webhook topic scope comes from the live catalog, using `for_org` (research D12).

Item 4: Resolved. The branch type is `feat`, which the constitution lists (Constitution Check, workflow row).

Item 5: Three parents already exceed five children (Complexity Tracking).

Item 6: Resolved. The client runs each SDK call in a daemon worker thread and waits at most `--call-timeout` seconds (default 30) for the result (research D13).

## Local Gates for the Implementation

The implementation phase runs these gates on the changed files. The commands run from the worktree root with the `.venv` tools.

| Gate | Command | Expected result |
| --- | --- | --- |
| Compile | `.venv\Scripts\python.exe -m py_compile <each new .py file>` | No output |
| Lint | `.venv\Scripts\ruff.exe check --no-cache <changed files>` | `All checks passed` |
| Format | `.venv\Scripts\black.exe --check <changed files>` | No file needs a change |
| Types | `.venv\Scripts\mypy.exe <changed files> --config-file pyproject.toml` | `Success` |
| Tests | `.venv\Scripts\python.exe -m pytest tests/unit/scripts -q` | All tests pass |
| Complexity | `radon cc scripts/netcool_runbook_smoke -j \| complexity-gate --max 10` | No block above 10 |
| Security | `bandit -c pyproject.toml -r scripts/netcool_runbook_smoke -q` | No finding |
| Docstrings | `pydocstyle` and `interrogate --fail-under 90` on the new files | No violation, and coverage of at least 90 percent. The target for the new package is 100 percent. |
| Dead code | `vulture <changed files> --min-confidence 70` | No finding |
| Guardrails | `python -m pytest tests/guardrails/test_spec_route_contract.py tests/guardrails/test_process_folder_structure.py tests/guardrails/test_mistapi_spec_modules.py -p no:cacheprovider -q` | All tests pass |
| Changelog | `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q` | All tests pass |
| STE | `ste-linter --config .ste-linter.toml --min-score 80 --no-dictionary <file>`, then the same command with the dictionary option | Each file scores 80 or more in both modes |
| Links | Stage the file, then `python -m pytest tests/guardrails/test_markdown_links.py -q` | All tests pass |

The coverage gate covers `src/` and does not measure `scripts/`. The test quality ratchet applies, because the test modules import `mistapi` at module scope or make Mist API calls. Such a module covers HTTP 4xx, HTTP 5xx, timeout, connection error, malformed JSON, and an empty body (`.github/copilot-instructions.md`, section "Test quality ratchet").

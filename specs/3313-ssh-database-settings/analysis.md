# Analysis: SSH database settings

**Issue**: [#3313](https://github.com/jmorrison-juniper/MistHelper/issues/3313)

**Specification**: [spec.md](spec.md)

**Original base**: `ff3cc1bea8ab58026210a968ff1465f61c9fec78`

**Current accepted predecessor**: `18127a874259732e9e6770de027e9485388b7592`

**Accepted tree**: `203ead4ef7c0a9e51f53b459193c6b410c811732`

## Local Refresh on 2026-10-03

The complete [local-only grant](https://github.com/jmorrison-juniper/MistHelper/issues/3313#issuecomment-5967867728) contains 4,049 UTF-8 bytes.
Its SHA256 is `011df67cd673c9c9cc1654c8222ded45fb2dca68bed258fa6e1e7a8b3658601f`.
The [coordinator acceptance](https://github.com/jmorrison-juniper/MistHelper/pull/3751#issuecomment-5967859633) verifies the exact predecessor and tree.
No open pull request owns a reserved path.
The original issue assignment, labels, and app session remain active.

The owner preserved the complete range ending at `0970aad563681ca601ec49837f9ba123d8ba1038`.
A verified two-commit bundle requires only the explicit original base.
Two patches and the historical analysis preserve the original red evidence.
The owned local tag is `preservation/issue3313-original-0970aad5`.
No shared history restoration, peer-reference movement, or remote action occurred.

The bounded rebase uses `rebase.updateRefs=false`.
It produces preparation head `60f07acc964e98a63fca14eb599ecd669589c059`.
The two migrated commits are `9f3ea97f015a07d83297d276803c042cbd28a5e5` and `60f07acc964e98a63fca14eb599ecd669589c059`.
The first migrated commit has the accepted predecessor as its sole parent.
Both patches compare equal through `git range-diff`.
Every original reserved-path byte remains equal before this documentation refresh.

No coupled fixture correction is necessary.
The actual writer, verified-key SSH connection, fresh shell, configuration builder, exporter, and router pass with the original synthetic fixtures.
The current DNS resolver, cache, constructor refusals, indexes, keys, and every unrelated source file remain unchanged.
The original synthetic discovery and backend boundaries remain explicit.
This is not production OpenSSH on port `2200` or a live database write.

### Current Local Results

| Measurement | Current result |
| - | - |
| Owned writer and session contracts | 91 passed. No failure, error, skip, or warning. |
| Current related tests | 950 passed and one existing registry skip. No failure, error, or warning. |
| Native guide and analyzer behavior | 530 passed. No failure, error, skip, or warning. |
| Exporter coverage | 81 cases pass. Affected exporter coverage is 95.44 percent. |
| Bash syntax and Python compile | Passed for the writer, entrypoint, and all five owned Python files. |
| Full Ruff | Passed with no finding. |
| Full Black | 2,057 files remain unchanged. |
| Exact configured CI mypy | Passed for 668 source files. |
| Direct fixture mypy | Passed for the three fixture modules. No new suppression. |
| Full configured Bandit | 791 files, zero findings, and zero read errors. |
| Configured source and owned-test complexity | Passed at the unchanged maximum of 10. |
| Configured dead-code and docstring gates | Passed at the existing confidence and coverage thresholds. |
| Required input preflight | Six inputs and three guide procedures pass. |
| Full native quality comparison | 1,028 files discovered, 980 modules analyzed, and 48 existing exclusions. |
| Complete finding preservation | All fields of all 725 records match. No added, lost, or changed record. |
| Committed exact-base quality comparison | Three selected tests, zero findings, and zero parse errors. |
| Current STE heuristics | Twelve supported files pass. The minimum score is 88. Dictionary scope remains partial. |
| Markdown links | Six tracked files pass with zero broken links. |
| Offline template conformance | All 23 item texts, seven ordered headings, and the HTML comment match. |

The first related-test receipt has five JUnit format warnings.
The final receipt sets `junit_family=legacy` only for local output formatting.
It retains the same 951-case scope and has no warning.
The existing skip remains `The registry holds no option of the class unregistered.`
No new contract has a skip marker.

The native full quality command has no narrowed roots or changed-scope controls.
Its configuration and baseline remain unchanged.
Its comparison uses complete result objects, including each location, rather than finding identities alone.
The canonical complete-finding SHA256 is `28379074d9df1e096918d53fd9033c800ae52d1b016debfa4454d4fa2fa970d8`.
Historical findings are not a zero-finding claim.

### Current Commands

The current related command reports 950 passes and one existing skip:

```bash
.venv/bin/python -B -m pytest -p no:cacheprovider \
  tests/unit/container tests/unit/db_discovery \
  tests/unit/test_standalone.py tests/unit/test_arango_writer.py \
  tests/unit/test_redis_writer.py tests/unit/test_redis_json_writer.py \
  tests/unit/test_router.py tests/unit/db/test_database_schema_utils.py \
  tests/unit/arango_indexes tests/contract/test_arango_declared_indexes.py \
  tests/unit/export/test_data_exporter.py \
  tests/guardrails/test_portal_operation_coverage.py \
  tests/guardrails/test_operation_registry_menu_coverage.py \
  tests/unit/web_portal/test_output_scan_runtime_files.py \
  --tb=short -q -rs -o junit_family=legacy
```

The owned and native commands report 91 and 530 passes respectively:

```bash
.venv/bin/python -B -m pytest -p no:cacheprovider \
  tests/unit/container/session_database \
  tests/unit/container/test_write_session_env_script.py --tb=short -q -rs

.venv/bin/python -B -m pytest -p no:cacheprovider \
  tests/guardrails/local_test_quality_loop \
  tests/tools/test_quality_analyzer --tb=short -q -rs
```

The required preflight and full quality commands pass:

```bash
.venv/bin/python -B -m pytest -p no:cacheprovider -s -q \
  tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides

.venv/bin/test-quality-analyzer --gate \
  --config .github/test-quality-config.toml \
  --baseline .github/test-quality-baseline.json

.venv/bin/test-quality-analyzer --gate \
  --config .github/test-quality-config.toml \
  --baseline .github/test-quality-baseline.json \
  --changed-from origin/main \
  --full-gate-path .github/workflows/ci.yml \
  --full-gate-path requirements-dev.txt
```

The local `origin/main` resolves to the exact accepted predecessor.
The grant forbids moving shared references, so this refresh performs no fetch or reference substitution.
The changed-scope report lists two omitted full roots because it selects three committed tests only.
The separate native full scan covers both discovered roots.

The exact type and affected coverage commands pass:

```bash
.venv/bin/python -m mypy src/ MistHelper.py wsgi.py \
  scripts/mist_ideas_analyzer_pkg/__init__.py \
  scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml

.venv/bin/python -B -m pytest -p no:cacheprovider \
  tests/unit/export/test_data_exporter.py \
  --cov=src.export.data_exporter --cov-branch \
  --cov-report=term-missing --cov-fail-under=80 --tb=short -q
```

### Current Audit and Capability Limits

The normal current `pip_audit -r requirements.txt` again aborts in its temporary `ensurepip` subprocess with `SIGABRT`.
This command produces no vulnerability verdict.
UV separately compiles the complete unchanged runtime manifest with exact versions and hashes.
The strict `--no-deps --disable-pip --require-hashes --strict` audit checks all 105 applicable macOS ARM64 packages.
It has zero unaudited runtime packages and zero known vulnerabilities.

The current runtime manifest SHA256 is `848301049195163bb029b66e486efdea9ec2da71126a1c64219978613dee8d72`.
The Git-only development-tool commit remains outside the runtime audit.
No fresh Linux or Windows audit occurs in this refresh.
The earlier Linux result below remains historical, not current platform evidence.

The licensed STE dictionary remains unavailable.
Configured heuristic checks use the existing settings and remain partial.
The first writing command included the Bash file, which the linter does not support.
It exited with status 2 after its supported files passed.
The corrected command grades only Markdown and Python files.
The Bash file instead passes its actual `bash -n` syntax check.
PowerShell, spaCy, and VS Code browser tools are unavailable.
No production, container, complete-repository test, full-repository coverage, or live database proof is claimed.

The current native DNS properties measure approximately 1.001 through 1.010 seconds, including scheduling overhead.
The cached partial-backend refusal measures `0.0007542920066043735` seconds.
These are preflight caller measurements.
They do not establish a complete driver handshake, router, or production Windows deadline.

### Refresh Delivery Barrier

The current 23-item template belongs to an offline session artifact.
It retains ordered headings, its HTML comment, every item, exact results, and honest unmeasured items.
The final local commit records this documentation refresh only.
The final clean head, tree, complete lineage, twelve-path manifest, and protected-byte results belong to the persistent local handoff.

This grant authorizes no push, pull request, Actions request, auto-merge, merge, branch deletion, or production action.
The owner must pause for a separate coordinator decision.

## Historical Evidence from 2026-10-01

The sections below retain the original evidence.
Their original base, commands, counts, and platform results do not substitute for the current refresh results above.

## Scope

The production change adds seven names to the existing explicit allowlist.
The writer algorithm remains unchanged.
The two warnings now name the Mist API token and two database passwords.
The SSH guide describes the configuration file and its protection.

The change modifies no output default, session reader, database implementation, schema, primary key, dependency manifest, baseline, or exclusion.
The shared SpecKit state remains unchanged.
The app owns the branch.

## Original Failure

Before the production edit, four focused contracts failed.
The actual writer emitted no database name.
The fresh-shell configuration raised `Missing required environment variable: ARANGO_USERNAME`.
The exact allowlist contract found eleven names instead of eighteen.
Both export contracts preserved the CSV copy but found no stored database record.

The fourth contract used an authenticated local SSH connection.
The failure therefore crossed the actual SSH transport, actual writer output, fresh shell, exporter, and router.
No Mist request or production database request occurred.

The command below reported **4 failed** before the repair.
The same contracts passed after the repair.

```bash
.venv/bin/python -m pytest \
  tests/unit/container/session_database/test_environment.py::TestSessionDatabaseEnvironment::test_actual_database_configuration_reads_all_seven_names \
  tests/unit/container/session_database/test_environment.py::TestSessionFileProtection::test_exact_allowlist_and_report_have_eighteen_names \
  tests/unit/container/session_database/test_export.py::TestSessionDatabaseExport::test_fresh_shell_export_uses_the_actual_router \
  tests/unit/container/session_database/test_export.py::TestSessionDatabaseExport::test_owned_ssh_session_stores_two_fixture_records \
  --tb=short -q
```

## Requirement Evidence

| Requirement | Evidence |
| - | - |
| FR-001 and FR-002 | The declaration and name-only report contain the exact eighteen permitted names. |
| FR-003 | Fifty-six cases cover seven names with eight value cases. Restart cases remove empty and absent settings. |
| FR-004 | The actual file has mode `0400` and the requested valid owner. Replacement leaves no staged file. |
| FR-005 | Reports contain no value. Five unrelated secrets remain absent from the file and the fresh environment. |
| FR-006 | Both writer warnings name the API token and two database passwords. |
| FR-007 | The actual exporter and router store both fixture records and preserve the CSV copy. |
| FR-008 | An authenticated Paramiko connection runs the fresh-shell export and checks the generated host key. |
| FR-009 | Only the reserved writer, tests, SSH guide, specification files, and unique release fragment change. |

Each value case covers empty, plain, space, quote, dollar, newline, Unicode, or large input.
Command-shaped password text remains data and creates no marker file.
Nine missing-credential cases preserve required credential validation.
Four invalid-input cases fail instead of reporting an empty successful measurement.
Two unavailable-file cases stop the shell before an empty comparison can report success.
Both cases failed against the initial harness and passed after its source guard changed.
The visible allowlist proof prints `Checked 18 session configuration names.`

The new contracts have no skip marker.
All eighty-one new cases pass.
The ten existing writer cases also pass.

## Measured SSH Layer

The fixture uses generated keys in memory and one owned loopback connection.
It permits one public key, one session channel, and one fixed request.
The server starts a clean Bash process that reads the actual writer-generated file.
The process builds the actual `DatabaseConfig` and calls the actual `DataExporter` and `DatabaseRouter`.

Only host discovery and backend connections use fixture replacements.
The owned ArangoDB fixture stores the routed records with the configured natural primary key.
The probe checks all seven settings, the stored records, and the CSV copy.
The actual exporter writes this line to the owned `data/script.log`:

```text
Polyglot write: backend=arangodb, written=2, failed=0
```

This measurement is an actual SSH transport with fixture backends.
It is not a deployed OpenSSH login on port `2200`.
It is not a live ArangoDB or Redis write.
No test container, production port, production volume, or production service changes.
The fixture closes its listener, channels, transports, and worker before it returns.

## Local Gate Results

| Command | Result |
| - | - |
| `bash -n container/scripts/write-session-env.sh` | Passed. |
| `.venv/bin/python -m py_compile MistHelper.py tests/unit/container/test_write_session_env_script.py tests/unit/container/session_database/harness.py tests/unit/container/session_database/test_environment.py tests/unit/container/session_database/test_export.py` | Passed. |
| `.venv/bin/python -m ruff check .` | Passed with no finding. |
| `.venv/bin/python -m black --check .` | Passed for 2,004 files. |
| `.venv/bin/python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | Passed for 663 source files. |
| `.venv/bin/python -m mypy tests/unit/container/session_database/harness.py tests/unit/container/session_database/test_environment.py tests/unit/container/session_database/test_export.py --config-file pyproject.toml` | Passed with no suppression. |
| `.venv/bin/python -m bandit -c pyproject.toml -r . -q` | Passed for 786 files with no finding or parse error. |
| The combined regression command below | Passed with 283 passed and one existing skip. |
| The writer and new contracts alone | Passed with 91 passed and no skip. |
| Exporter tests with `--cov=src.export.data_exporter --cov-branch --cov-fail-under=80` | Passed with 95.44 percent coverage. |
| Full test-quality ratchet with the unchanged configuration and baseline | Checked 994 files and found no new finding. |
| Radon and `complexity-gate --max 10` on the new package | Passed. |
| An AST count of the new functions | Checked 37 functions. None exceeds 25 lines. |
| Configured STE heuristics with `--min-score 80` | Passed. Dictionary coverage remains partial. |
| `.venv/bin/markdown-link-check documentation/SSH_GUIDE.md changelog.d/issue-3313-ssh-database-settings.md specs/3313-ssh-database-settings` | Passed for six Markdown files with no broken link. |

The combined regression command is:

```bash
.venv/bin/python -m pytest \
  tests/unit/container \
  tests/unit/test_standalone.py \
  tests/unit/export/test_data_exporter.py \
  tests/guardrails/test_portal_operation_coverage.py \
  tests/guardrails/test_operation_registry_menu_coverage.py \
  tests/unit/web_portal/test_output_scan_runtime_files.py \
  --tb=short -q -rs
```

The existing skip is `test_portal_operation_coverage.py:135`.
Its reason is `The registry holds no option of the class unregistered.`
It does not skip a new contract.

The full ratchet command uses:

```bash
.venv/bin/test-quality-analyzer --gate \
  --config .github/test-quality-config.toml \
  --baseline .github/test-quality-baseline.json \
  --roots tests mist-ops-platform/tests \
  --report /Users/jmorrison/.copilot/session-state/16968e19-81d9-4180-a974-1578bc0302de/files/3313-full-test-quality.json \
  --summary /Users/jmorrison/.copilot/session-state/16968e19-81d9-4180-a974-1578bc0302de/files/3313-full-test-quality.md \
  --log-level WARNING
```

It measured the existing 725 findings and reported zero new findings.
Its existing Mist API predicate excluded 48 files.
No baseline, rule, or exclusion changed.

## Dependency Audit and Missing Capabilities

The standard `pip_audit -r requirements.txt` command aborted in the temporary environment.
The bundled `ensurepip` subprocess ended with `SIGABRT`.
This failure is not a vulnerability verdict.

UV compiled the unchanged runtime manifest with every transitive package and its hashes.
The strict audit used `--no-deps --disable-pip --require-hashes --strict`.
The macOS audit measured all 105 resolved packages.
The Linux ARM64 audit measured all 107 resolved packages.
Both audits found zero missing packages and zero known vulnerabilities.
The Git-only development tool stays outside the runtime audit.
The generated resolutions and audit reports remain session artifacts.

The configured `data/ste_dictionary.json` is unavailable.
No authorized dictionary artifact exists for this session.
The configured heuristic check passes, but its dictionary scope is `partial` with `dictionary_unavailable`.
This repair does not generate, obtain, or substitute a dictionary.

## Delivery State

The final review found a false successful comparison after the shell could not read its session file.
A local follow-up commit corrects the harness and proves both unavailable-file cases.
The initial local commit remains unchanged.

The local repair, specification, implementation, analysis, and quality evidence are complete.
The parent has not granted remote publication.
Do not push or create a pull request before the explicit verified-main SHA grant.

The protected merge and exact-main local tests remain pending.
They require the parent grant after position 26, a current-base rebase, and repeated local gates.
No observation of `main` substitutes for that grant.

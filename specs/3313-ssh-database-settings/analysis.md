# Analysis: SSH database settings

**Issue**: [#3313](https://github.com/jmorrison-juniper/MistHelper/issues/3313)

**Specification**: [spec.md](spec.md)

**Base**: `ff3cc1bea8ab58026210a968ff1465f61c9fec78`

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

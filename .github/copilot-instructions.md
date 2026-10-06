# MistHelper agent instructions

This file holds the rules that apply to `MistHelper` only. The rules that apply to each
repository of this owner are in `AGENTS.md` at the repository root. Read `AGENTS.md` first. This
file adds to it, and it does not hold a copy of a rule from it. Where the two files disagree, obey
`AGENTS.md` for a writing rule, a safety rule, or a security rule.

## What this repository is

MistHelper is a Python tool for the operation of a network on the Juniper Mist cloud. It gives a
network operations center 293 registered menu operations, numbered 0 through 293, for data
export, device management, and firmware upgrades. Each export writes to CSV, to SQLite, or to
ArangoDB and Redis. The audience is a junior engineer in a network operations center, so each
message uses plain words. The tool runs on Windows 11, on macOS, and on Linux, and it ships as a
Podman container.

## Language and environment

The language is Python 3.13 or newer, because `pyproject.toml` requires `>=3.13`. The package
`mistapi>=0.64.0,<0.65` is the only interface to the Mist REST API. UV is the preferred
installer, and `requirements.txt` stays current for pip. Podman is the container runtime, and
each example uses Podman.

A new worktree holds no `.venv`. Build the environment one time with these two commands.

```powershell
python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

On macOS or Linux, run `python3 scripts/bootstrap_worktree.py`, then `source .venv/bin/activate`.
The bootstrap installs `requirements.txt` and `requirements-dev.txt`, downloads the Chromium
browser for the browser tests, and sets the git credential account to `jmorrison-juniper`.

The `misthelper-devtools` package in `requirements-dev.txt` supplies the shared commands:
`test-quality-analyzer`, `complexity-gate`, `check-citations`, `speckit-task-audit`,
`symbol-diff`, `stranded-branch-report`, `codeql-verdict-register`, `bandit-exclude-check`,
`diagram-refs`, `exclusion-drift`, `pytest-chunks`, `worktree-cleanup`, `markdown-link-check`,
and `ste-linter`. The same repository supplies the shared workflows that `.github/workflows/`
calls at one pinned commit.

Spec Kit writes its generated technology context to `.specify/memory/agent-context.md`, and the
project constitution is `.specify/memory/constitution.md`. Spec Kit does not write `AGENTS.md`,
`CLAUDE.md`, or this file.

## Local gates

Run each gate that applies to the changed files. The `ci.yml` workflow runs the same gates in 24
quality jobs and one issue job, so a local pass predicts the CI result.

| Gate | Command | Expected result |
| - | - | - |
| Compile | `python -m py_compile MistHelper.py` | No output |
| Lint | `python -m ruff check .` | `All checks passed` |
| Format | `python -m black --check .` | No file needs a change |
| Types | `python -m mypy $MYPY_PATHS --config-file pyproject.toml` | `Success`. Read `MYPY_PATHS` from `.github/workflows/ci.yml`. |
| Tests | `python -m pytest tests/<the changed file>` | All tests pass |
| Full tests | The two `pytest-chunks` commands below | One summary line for each shard |
| Safe sweep | `python MistHelper.py --test` | Each `safe` operation completes. Without `MIST_APITOKEN` or `MIST_API_TOKEN`, the Mist API checks skip with a credential reason. |
| Coverage | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | The CI shards combine the reports and require 80 percent or above |
| Test quality | The `test-quality-analyzer` procedure below | `gate: 0 new findings vs baseline` |
| Complexity | `radon cc <package> -j \| complexity-gate --max 10` | No block above cyclomatic complexity 10 |
| Security lint | `bandit -c pyproject.toml -r <package> -q` | No finding at any severity |
| Dependency audit | `pip-audit -r requirements.txt` | No known vulnerability |
| Code quality | `pylint src/ --fail-under=9.5` | Score 9.5 or above |
| Dead code | `vulture $VULTURE_PATHS --min-confidence 70` | No finding. Read `VULTURE_PATHS` from `ci.yml`. |
| Docstrings | `pydocstyle $PYDOCSTYLE_PATHS` and `interrogate $INTERROGATE_PATHS --fail-under 90` | No violation, and coverage at 90 percent or above |
| Menu reference | `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map` | No changed file after the run |
| Symbols | `symbol-diff --base <base> <file>` | `no module-level name changed`, exit code 0 |
| STE | `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md` | Each file scores 80 or above |
| Ops portal | `npm audit --audit-level=high`, `npm run typecheck`, `npm run lint`, and `npm test` in `ops-portal/` | Each command exits 0 |
| Ops platform | `pytest --cov=src --cov-fail-under=56` in `mist-ops-platform/` | At least 390 tests, coverage at 56 percent or above |

The `ops_portal` job is the one gate that reads the npm dependency tree. It is the only check
that can report an advisory in `ops-portal/package-lock.json` (issue #1847).

On Windows, the `pytest-chunks` command divides the two large test trees of the portals into
chunks. It prints one summary line for each shard. With `-x`, it stops after the first failed chunk.
Measured on 2026-09-17, the unit shard took 1179.3 seconds and the second shard took 366.3
seconds.

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

A scripted sweep of many files runs the compile, lint, type, and symbol gates on each changed
file. The symbol gate exists because the other three gates miss a lost declaration. Pull request
#1791 removed a live declaration inside a 515-line comment sweep, and issue #1796 records it.

### Test quality ratchet

The `test_quality_gate` job in `ci.yml` is the authority for this procedure. The guard
`tests/guardrails/local_test_quality_loop/test_guidance.py` reads this section and fails when a
command below drifts from the live job. Commit the intended tests first, and stop if a relevant
staged, unstaged, or untracked change remains. Run each command separately, and stop at the
first failed command.

**Intended base for the required check:**

```powershell
$BASE_REF = "main"
git fetch --no-tags origin "+refs/heads/${BASE_REF}:refs/remotes/origin/${BASE_REF}"
git rev-parse --verify "origin/${BASE_REF}^{commit}"
```

Set `BASE_REF` to the branch that the pull request targets. The fetch destination, the commit
resolution, and the comparison must use the same branch.

**Required input preflight:**

```powershell
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

The preflight reads the four required inputs and checks this procedure against the live job. It
fails when a required file is absent or malformed, because the analyzer alone uses defaults for
an absent settings file. Zero counts do not prove that the inputs are readable.

**Required check after the local commit and before push:**

```powershell
test-quality-analyzer --gate `
  --config .github/test-quality-config.toml `
  --baseline .github/test-quality-baseline.json `
  --changed-from "origin/$BASE_REF" `
  --full-gate-path .github/workflows/ci.yml `
  --full-gate-path requirements-dev.txt
```

The `--changed-from` option compares the intended base with `HEAD` through
`git diff --name-only --relative -z REVISION HEAD`. It does not use a merge base. Only committed
`test_*.py` and `*_test.py` files enter the selection, and the analyzer reads them from the
working tree. If the committed difference names `.github/test-quality-config.toml`,
`.github/test-quality-baseline.json`, `.github/workflows/ci.yml`, or `requirements-dev.txt`, the
analyzer scans every test root.

**Full-suite check for push or manual CI:**

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

The `gate_scope` line counts the discovered files and the checked findings. The separate
`gate: K new findings vs baseline` line counts the new findings, and `K` must be zero before a
push. Do not rewrite `.github/test-quality-baseline.json` to hide a new finding.
`documentation/quality-gates.md` tells how to update that file for an accepted finding.

## Architecture and conventions

`MistHelper.py` is the entry point and the menu. It parses `--menu <number>` for one
operation, `--test` and `--testinteractive` for the unattended sweeps, `--fast` for the
multithreaded mode, and `--capture-portal` for the upgrade capture portal.

New Spec Kit records MUST use the managed roots `specs/numbered/`, `specs/live/`,
`specs/skills/`, or `specs/indexes/`. Numeric records MUST use the fixed
eight-level base-5 route from `.specify/scripts/powershell/spec-route.ps1`.
Timestamp records MUST use `specs/live/`. The guard reads
`tests/guardrails/process_folder_baseline.json`, reports examined counts, and
rejects each new direct child that is not a managed root or a grandfathered
baseline entry.

The `src/` tree holds four packages. The `foundation` package holds the runtime, the models, and
the support code. The `operations` package holds the export, the execution, the firmware, and
the SSH code. The `interfaces` package holds the portals and the visualization code. The `mist`
package holds the API access by domain.

`web_portal/` serves the Gunicorn web UI on port 8055 through `wsgi.py`. The package
`src/interfaces/portals/upgrade_portal/` serves the upgrade capture portal on port 8056 through
`wsgi_capture.py`. `ops-portal/` holds the npm frontend, and `mist-ops-platform/` holds the ops
platform backend.

```text
Menu selection -> Mist API call -> flatten -> DataExporter.write_with_format_selection()
                                                -> CSV / SQLite / ArangoDB and Redis
```

Class names give the subject: `GlobalImportManager`, `WebSocketManager`, `PacketCaptureManager`,
`FirmwareManager`, `EnhancedSSHRunner`, `DataExporter`, and `SFPTransceiverDataProcessor`.
Shared helpers are `InputUtils.safe_input` for each keyboard read,
`DataProcessingUtils.flatten_dict` for a nested response, and
`DataExporter.write_with_format_selection` for each export.

### Primary keys

Each table uses a natural key from the Mist API. The dictionary `ENDPOINT_PRIMARY_KEY_STRATEGIES`
in `src/foundation/support/refactors/endpoint_primary_key_strategies.py` holds one entry for each
endpoint, and three types exist.

| Type | Use it for | Example |
| - | - | - |
| `natural_pk` | An entity with a stable UUID, such as a site or a device | `'primary_key': ['id']` |
| `composite_pk` | Time-series data, such as an event or a statistic | `'primary_key': ['id', 'device_id', 'timestamp']` |
| `auto_increment_with_unique` | A summary with no stable key | `'primary_key': ['misthelper_internal_id']` |

The writer uses `INSERT OR REPLACE` for a natural key and a composite key, so a second run
updates a row and does not duplicate it. Define the strategy before you write the operation.

### Menu categories

`src/foundation/support/utils/operation_registry.py` is the single source of truth for the
category of each menu. The measurement date of the counts below is 2026-10-04. The guard
`tests/guardrails/test_destructive_menu_docs.py` fails when this table drifts from the registry.

| Category | Count | Menu numbers |
| - | - | - |
| `interactive_safe` | 95 | 60-96, 195-203, 209-229, 235-238, 240-242, 244-247, 254, 256-268, 270, 288-289 |
| `safe` | 84 | 1-13, 15-17, 20-58, 188, 193, 204-205, 230-234, 243, 248-253, 255, 269, 271-280, 282 |
| `destructive` | 48 | 154-187, 189-191, 194, 206-208, 239, 281, 286-287, 291-293 |
| `interactive` | 33 | 0, 124-150, 192, 283-285, 290 |
| `websocket` | 22 | 102-123 |
| `resource_intensive` | 10 | 14, 18-19, 59, 97-101, 153 |
| `continuous_loop` | 1 | 151 |

`--test` runs the `safe` category only, and `--testinteractive` adds `interactive_safe`. The
sweeps skip each other category.

### Add a menu operation

Write the operation in five steps.

1. Find the endpoint in `mistapi.api.v1.orgs.*` or `mistapi.api.v1.sites.*`.
2. Add the primary key strategy to `ENDPOINT_PRIMARY_KEY_STRATEGIES`.
3. Flatten the response with `DataProcessingUtils.flatten_dict`.
4. Write the rows with `DataExporter.write_with_format_selection(data, filename, api_function_name=...)`.
5. Register the operation in `OperationRegistry` with its category.

Then publish the operation in three steps.

1. Update the operation count and the menu table in `README.md`.
2. Run `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map`, then commit the changed pages.
3. Add one release-note fragment under `changelog.d/`.

The `menu_reference_drift` job fails when a generated page is stale. The 2026-09 feature program
added menus 271 through 293 across 22 branches, and seven gates failed at least one of those
pull requests. Run each check before you push.

| Gate | What fails | Local command |
| - | - | - |
| Complexity | A function above cyclomatic complexity 10. Divide a long classifier into helpers. | `radon cc <package> -j \| complexity-gate --max 10` |
| Test quality | A new API client test module with no HTTP 4xx test and no HTTP 5xx test, or a bare `assert result`. | The test quality ratchet above |
| SDK compatibility | A call that forwards `*args` or `**kwargs` into a `mistapi.api.v1` function. Pass explicit arguments. | `python -m pytest tests/integration/test_mistapi_sdk_compatibility.py` |
| Output scan | A test module that names a folder under `data/` with the word `test` in its name. Use `tmp_path`. | `python -m pytest tests/unit/web_portal/test_output_scan_runtime_files.py` |
| Bandit | An `assert` in production code, a hardcoded credential string, or a bare `try/except/pass`. | `bandit -c pyproject.toml -r <package> -q` |
| Portal registry | A regenerated `web_portal/menu_registry.py` that holds a row the portal cannot run. Feed the generator only the `safe` and `interactive_safe` titles. | `python -m pytest tests/guardrails/test_portal_operation_coverage.py` |
| Destructive marker | A `destructive` registry entry with a `skip_reason` that lacks the word `DESTRUCTIVE`. | `python -m pytest tests/guardrails/test_operation_registry_menu_coverage.py` |

When several agents add menu operations at the same time, give each feature branch its own
package under `src/` and its own test directory. Each branch writes a
`specs/<issue>-<slug>/wiring.md` manifest with the menu row, the registry entry, the primary key
strategies, and the import line. One integration pull request for each batch applies every
manifest to `MistHelper.py`, to `operation_registry.py`, to the category table above, and to the
generated references. Pull requests #3643, #3644, #3645, and #3679 show the shape, and
`documentation/menu-operations-271-293.md` describes the result.

### Hot files

`MistHelper.py` takes one open pull request at a time. If another agent holds that pull request,
wait, or work on a file that does not overlap. The integration pull request of a batch owns
`src/foundation/support/utils/operation_registry.py`,
`src/foundation/support/refactors/endpoint_primary_key_strategies.py`, `README.md`,
`documentation/menu_reference.md`, and the category table in this file.

### Web UI tests

A change to the web UI carries a test under `tests/e2e/`. The `flask_app` and `client` fixtures
in `tests/e2e/conftest.py` build a Flask test client with no browser, and
`tests/e2e/upgrade_portal/` holds the Playwright browser tests. Give each new interactive element
a stable `data-testid` attribute, and keep a screenshot or a trace of a failed flow as a CI
artifact.

## Safety in this repository

Warning: a `destructive` operation changes the Mist cloud or a production device, and a wrong
run can cause an outage that nobody can undo. Do not automate one without an explicit
confirmation from the user. The destructive set is 154-187, 189-191, 194, 206-208, 239, 281,
286-287, and 291-293. It is not one block, so do not treat a range boundary as a shortcut.

Menu 239 starts the upgrade capture portal and drives a firmware upgrade for the selected site.
Menus 281, 286-287, and 291-293 change alarm state, client sessions, inventory, RRM, CSV imports,
or Mist Edge state. An earlier version of the table stopped at 208, and issue #2825 records that
gap.

A destructive operation asks the operator to type a word such as `UPGRADE`, `REBOOT`, `CONVERT`,
or `CLEAR` through `InputUtils.safe_input`, and it returns at the first wrong answer.

| Location | Holds |
| - | - |
| `data/` | Each product output. The runtime enforces this directory. |
| `data/mist_data.db` | The SQLite store. ArangoDB and Redis run as containers. |
| `data/per-host-logs/` | The SSH session logs. |
| `data/SSH_COMMANDS.CSV` | The SSH command list. The root path is a fallback. |
| `data/tuning_data.json` | The adaptive rate-limit tuning data for each endpoint. |
| `data/script.log` | The runtime log. |
| `data/agent_logs/` | The agent telemetry directory. The portal output scan skips it. |
| `test-artifacts/` | Generated test evidence. Git ignores it. |

The container runs as the account `misthelper` with UID 1000, and the mounted `data/` directory
must accept a write from that identifier. On Windows and on macOS the runtime virtual machine
shares the folder as writable. On Linux with rootless Podman, run
`podman unshare chown -R 1000:1000 data`. The symptom of a wrong owner is
`PermissionError: [Errno 13] Permission denied: '/app/data/script.log'`.

The volumes `misthelper-arangodb-data` and `misthelper-redis-data` hold every capture and every
upgrade run. A removed volume is not recoverable, so remove a test volume by its own name only.

The default page size is `DEFAULT_API_PAGE_LIMIT = 1000`, and the `MIST_PAGE_LIMIT` variable
changes it in the range 1 through 1000. The `--fast` flag bypasses the adaptive rate limit, and
the `FAST_MODE_*` variables in `MistHelper.py` tune it.

## Containers and ports

The compose group is `compose.yml`, and `scripts/compose.ps1` starts it. Start a test container
in one of these three forms.

```powershell
.\scripts\compose.ps1 run --rm misthelper python -m pytest tests/<file>
.\scripts\compose.ps1 --profile test up -d
.\scripts\compose.ps1 up -d --no-deps misthelper
```

If a test needs a new service, add the service to `compose.yml` under a profile. Name an
ephemeral container, its volume, and its network `misthelper-tmp-<issue|pr><number>-<slug>`, for
example `misthelper-tmp-issue2059-portcheck`. The guard
`tests/guardrails/test_compose_naming_policy.py` reads the `misthelper` prefix.

Issue #2059 records the collision that created the policy. A second project took the vendor
default port, and the upgrade portal read a foreign database as its own store.

| Port | Owner |
| - | - |
| 1161/udp | The SNMP service |
| 1514/udp | The Observium syslog receiver |
| 2200 | The SSH runner |
| 8055 | The Gunicorn web UI |
| 8056 | The upgrade capture portal |
| 8057 | The metrics gateway |
| 8668 | The Observium web interface |
| 9379 | Redis |
| 9526 | The RedisInsight web UI |
| 9529 | ArangoDB |

Read `compose.yml` before you select a port, because the table can drift. Publish an ephemeral
port in the range 9600 through 9699, and bind it to `127.0.0.1`. The guard
`tests/guardrails/test_container_policy_docs.py` compares this table with `compose.yml`.

Warning: a test container on port 9529 or 9379 takes the port from the running store, so the
portal can write to the wrong database. The operator then loses the upgrade record.

Remove the container in the same session that started it. The two list commands confirm the
cleanup, and an empty result from each one means that the cleanup finished.

```powershell
.\scripts\compose.ps1 rm -s -f <the test service>
podman rm -f misthelper-tmp-<issue|pr><number>-<slug>
podman volume rm misthelper-tmp-<issue|pr><number>-<slug>
podman network rm misthelper-tmp-<issue|pr><number>-<slug>
podman ps -a --filter "name=misthelper-tmp-" --format "{{.Names}} {{.Status}}"
podman volume ls --filter "name=misthelper-tmp-" --format "{{.Name}}"
```

Build and start the product container on your own machine with these commands. Podman builds the
same image that the registry builds.

```powershell
podman build -t misthelper:local .
podman rm -f misthelper-app
.\scripts\compose.ps1 up -d --no-deps misthelper
podman ps
```

Caution: pass `--no-deps` and name the service, otherwise compose tries to create
`misthelper-arangodb` and `misthelper-redis` again. It then stops with
`the container name is already in use`. Issue #2228 holds that report.

The registry is `ghcr.io/jmorrison-juniper/misthelper`, and `.github/workflows/container-build.yml`
pushes the image on a push to `main` or on a manual dispatch. The version format is
`YY.MM.DD.HH.MM` in UTC. A corporate Zscaler proxy blocks a local `podman push` to `ghcr.io`
with a 403 response, so run `gh workflow run container-build.yml` when the registry must hold a
new image. Pull the registry image only when you need the exact image that a release produced.

The container exposes SSH on port 2200. A `ForceCommand` starts MistHelper directly, each
connection gets its own directory under `/app/sessions/`, and the account `misthelper` uses the
default password that the `Dockerfile` sets. Change that password in production. For a host
deployment, `deploy/misthelper.service` is the systemd unit, `deploy/misthelper.container` is
the Podman Quadlet unit, and `deploy/.env.example` is the template for the `.env` file.

## Git and GitHub in this repository

Each issue and each pull request carries one type label and one scope label, and an issue in
progress carries `in-progress`.

| Label set | Labels |
| - | - |
| Type | `bug`, `feature`, `chore`, `lint`, `security`, `refactor` |
| Scope | `MistHelper.py`, `tests`, `ci`, `container`, `docs`, `web-portal` |
| Status | `in-progress` |

| Error | Labels | Issue title |
| - | - | - |
| A `ruff check` violation | `lint` and the rule code | `Lint: <rule> -- <description>` |
| A `pytest` failure | `bug`, `test` | `Test failure: <test name>` |
| A `mypy` error | `chore`, `types` | `Type error: <file>:<line>` |
| A runtime exception | `bug` | `Runtime: <exception> in <function>` |
| A security finding | `security` | `Security: <tool> -- <finding>` |
| A workflow failure | `ci` | `CI: <workflow> -- <failure>` |

A change that a user sees adds one fragment under `changelog.d/`. Name it `pr-<number>.md` when
the pull request exists. Name it `issue-<number>-<slug>.md` when only the issue exists, and
`<YYYY-MM-DD>-<slug>.md` when neither exists. Write one `###` heading in the fragment. Write one
bullet for each change type, and name the issue in the bullet. The change types are `Added`,
`Changed`, `Fixed`, `Removed`, and `Security`. `changelog.d/README.md` holds the full rule.

The release coordinator moves the merged fragments into `CHANGELOG.md` on the release branch.
`CHANGELOG.md` carries a `merge=union` attribute as a safety net for old branches. That attribute
is not the release-note process.

The pull request template is `.github/PULL_REQUEST_TEMPLATE.md`, and a feature starts as an issue
from `.github/ISSUE_TEMPLATE/feature-spec.yml`. A new environment variable also enters
`deploy/.env.example`.

| Workflow | Purpose | Trigger |
| - | - | - |
| `ci.yml` | The 24 quality jobs and the `quality_gate_issues` job | Each pull request and each push to `main` |
| `codeql.yml` | CodeQL static analysis. Branch protection requires its check. | Each pull request, each push to `main`, and a weekly schedule |
| `pull-request-title.yml` | The `Conventional Commits PR title` check | Each pull request title change |
| `ste-lint.yml` | The `STE compliance` check on the instruction files and the README | Each pull request and each push to `main` |
| `auto-merge.yml` | Squash merges a pull request that carries the `auto-merge` label after each required check passes | A label, a push to the pull request, a push to `main`, and a schedule every six hours |
| `close-linked-issues.yml` | Closes the issue that a merged pull request names | A closed pull request and a schedule every twelve hours |
| `container-build.yml` | Builds and pushes the container image | A push to `main` that changes a product file, or a manual dispatch |
| `release.yml` | Builds the wheel, the source archive, the standalone ZIP, and the multi-arch image | A tag that matches `v*.*.*` |
| `stranded-branch-report.yml` | Reports a branch with no pull request | A weekly schedule or a manual dispatch |
| `wiki-publish.yml` | Publishes the generated wiki pages | A push to `main` that changes `documentation/wiki/`, or a daily schedule |

MistHelper is a public repository, so a standard runner costs no minutes. The `quality_gate_issues`
job opens a `quality-gate` issue when a gate fails on `main`, closes it when the gate passes, and
titles the issue `... failed (PR #<number>)` for a pull request. Wait for CodeQL before you add
the `auto-merge` label, because the check takes two to three minutes after the other gates.

### Pull request titles

The `Pull request title` workflow reports the `Conventional Commits PR title` check. The check
reads one exact title from `GITHUB_EVENT_PATH`. It applies the same rule to contributors, bots,
drafts, forks, and documentation-only changes. The check does not change the supplied title.

The check accepts these four forms.

```text
type: description
type(scope): description
type!: description
type(scope)!: description
```

The type must use lowercase. If you use a scope, give it a nonblank value without parentheses.
The optional `!` marker goes immediately before the colon. Use a colon followed by an ASCII
space. Use a nonblank one-line description.

Additional description spaces and Unicode text are valid. Do not use control characters U+0000
through U+001F or U+007F through U+009F. Do not use the Unicode line separator U+2028 or the
Unicode paragraph separator U+2029.

If the title fails, correct the pull request title. A title edit starts another check through the
`edited` event. A title decision prints the exact title through reversible ASCII JSON escapes. It
prints `Checked 1 pull request title`.

If the input is unavailable or invalid, the check fails. It prints
`Checked 0 pull request titles`. The check sends ASCII key/value action logs to stderr.

New pip updates use `chore`. New npm updates in `/ops-portal` use `chore(ops-portal)`. GitHub
Actions updates keep `ci`. Existing `deps` and `deps(ops-portal)` titles fail. A maintainer must
rename each existing invalid title. Do not close update pull requests or disable update streams.

The `Conventional Commits PR title` check is not a required status check. Require separate owner
approval before anyone makes this check required. This feature changes no repository settings,
branch protection, or required statuses. The `squash_merge_commit_title=PR_TITLE` setting stays
unchanged.

## Known pitfalls

- Issue #1866: a new worktree has no `.venv`, so the tests ran against the global interpreter.
  Run `python scripts/bootstrap_worktree.py` first. `python -m pytest` now stops with one message
  that names the bootstrap command.

- Issue #1893: `GH_TOKEN` or `GITHUB_TOKEN` named another account, and the push went to the wrong
  identity. Clear both variables, then run `gh auth switch --user jmorrison-juniper`.

- Issue #2006: `listSiteDevices` reports the configured firmware version, which can be old or
  `None`. Read the running version through `RunningFirmwareVersionResolver` in
  `src/operations/execution/firmware/running_version.py`, and warn when `reading.is_running` is
  `False`. `listSiteDevicesStats` and `getOrgInventory` report the running version.

- `listSiteDevices(site_id)` returns access points only. Pass `type="all"` to include switches
  and gateways.

- Dash 3 removed `app.run_server`. Call `app.run(host=host, port=port, debug=False,
  use_reloader=False, threaded=True)`, because a reloader starts the process twice on Windows.

- Issue #2689: the SDK compatibility guard skipped all seven tests and reported green. A guard
  prints the count that it checked and fails when it cannot read its input. Pull request #2591
  proves a guard with a red run, and pull request #2611 proves one with a direct decision test.

- Issue #2541: five instruction files held the release-note rule, and no gate read one of them.
  `tests/guardrails/test_changelog_fragment_policy.py` now reads the directory and this file.

- Issue #1952: a branch filter on a `pull_request` trigger let a stacked pull request merge with
  zero checks. A workflow that reports a required check carries no `paths` filter and no
  `branches` filter.

- Issue #3926: GitHub Actions does not cancel a job whose `if` condition calls `always()`. A
  force-push cancelled the older Quality Gates run, but each `always()` job ran to its end, and
  the newer run waited 21 minutes. Use `!cancelled()` for a job that must run after a failed
  gate. `tests/guardrails/test_ci_gate_triggers.py` fails on an `always()` job in `ci.yml`.

## Key files

| File | Purpose |
| - | - |
| `MistHelper.py` | The entry point and the menu. Measured on 2026-10-04, it has 8,382 lines, and `src/` holds 828 Python files with 235,285 lines. |
| `src/foundation/support/utils/operation_registry.py` | The category of each menu operation. |
| `src/foundation/support/refactors/endpoint_primary_key_strategies.py` | The primary key strategy of each endpoint. |
| `documentation/CONTRIBUTING-MistHelper.md` | The map of the stable `MistHelper.py` symbols and the `src/` packages. |
| `documentation/quality-gates.md` | Each quality gate and the way to update the test quality baseline. |
| `documentation/menu_reference.md` | The generated operator reference. `scripts/generate_menu_wiki.py` writes it. |
| `documentation/container-deployment.md` | The deployment methods and the test container policy for an operator. |
| `documentation/SSH_GUIDE.md` | The SSH runner guide. |
| `changelog.d/` | One release-note fragment for each change. |
| `CHANGELOG.md` | The released history in the Keep a Changelog format. The release coordinator owns it. |
| `compose.yml` | The compose group and the published ports. |
| `requirements.txt` and `requirements-dev.txt` | The runtime dependencies and the development tools. |
| `.env` | The credentials and the configuration. Git ignores it, and `deploy/.env.example` is the template. |
| `.specify/memory/constitution.md` | The project constitution for the Spec Kit workflow. |

## External resources

- The Mist API specification is `documentation/mist-api-openapi31json.json` and the other
  `documentation/mist-api-openapi3*` files.
- The `mistapi` SDK by Thomas Munzer: <https://github.com/tmunzer/mistapi_python>
- Example implementations: <https://github.com/tmunzer/mist_library>

# Contract: Bootstrap installer flow for the setup guide

This contract lists what the setup guide must state about the installer flow of `scripts/bootstrap_worktree.py`. The script defines the flow, and the guide describes it. Each line number refers to the script on `main` at commit `f03c6c9b` (blob `e16515ffa789cca7d0bdd7e9789898588e5f1312`).

## 1. Command-line options

| Option | Effect | Line |
|--------|--------|------|
| `--recreate` | Deletes the `.venv` directory before the bootstrap creates it. | 674 |
| `--public-lock-index` | Syncs from the public index for one run. It changes no pip configuration. | 679 |

The parser is built in the function `build_parser`, which starts at line 670.

## 2. Commands in run order

| Order | Command or check | Condition | Line |
|-------|------------------|-----------|------|
| 0 | Source sweep: lists the tracked names under `src` and removes cache-only orphan directories. The guide does not describe it (D-5). | Every run, before setup | 895 (call), 726 (tracked names) |
| 1 | `pip config list` through the worktree interpreter. | Every run, after the environment exists | 179 |
| 2 | TCP connection to the configured index host, with a 3-second timeout. | The configured index is not on the public host | 86 (timeout), 212 (connection) |
| 3 | `uv --version` through the bootstrap interpreter, as a module. | No uv on PATH and no uv in the per-user folders | 282 (probe), 313 (use) |
| 4 | `pip install --user uv` through the bootstrap interpreter. | No uv found, and the Python is not externally managed | 457 (install), 455 (refusal) |
| 5 | `uv sync --locked --extra dev` from the repository root. | Every run | 466 |
| 6 | `uv lock --check` from the repository root. | Only after a failed locked sync | 497 |
| 7 | `misthelper_devtools.venv_health` through the worktree interpreter. | After the locked sync succeeds | 623 |
| 8 | `playwright install chromium` through the worktree interpreter. | After the health check | 593 |
| 9 | `git config --local credential.https://github.com.username jmorrison-juniper`. | After the browser step | 820 |
| 10 | `gh api user --jq .login`. | After the Git setting | 848 |

## 3. Settings for child processes

An installer child process runs uv or pip. The browser child process downloads Chromium. Each child process starts with a copy of the caller environment (line 641).

| Setting | Value | Applies to | Condition | Line |
|---------|-------|------------|-----------|------|
| `UV_LINK_MODE` | `copy` | Installer child process | Every run | 416 |
| `UV_NATIVE_TLS` | `1` | Installer child process | Every run | 417 |
| `UV_SYSTEM_CERTS` | `1` | Installer child process | Every run | 418 |
| `UV_NO_CONFIG` | `1` | Installer child process | Every run | 419 |
| `UV_HTTP_RETRIES` | `1` | Installer child process | Every run | 420 |
| `UV_HTTP_TIMEOUT` | `15` | Installer child process | Every run | 421 |
| `UV_CONFIG_FILE` | Removed | Installer child process | Every run | 424 |
| `UV_INDEX`, `UV_DEFAULT_INDEX`, `UV_INDEX_URL`, `UV_EXTRA_INDEX_URL` | Removed before the pip sources map to uv | Installer child process | Every run | 407 to 412 |
| `UV_INDEX_URL` | The configured index value | Installer child process | A `PIP_INDEX_URL` value or a pip configuration value exists | 446 |
| `UV_EXTRA_INDEX_URL` | The configured extra index value | Installer child process | A `PIP_EXTRA_INDEX_URL` value or a pip configuration value exists | 446 |
| `UV_INDEX_URL` | `https://pypi.org/simple` | Installer child process | `--public-lock-index` | 354 |
| `UV_DEFAULT_INDEX`, `UV_INDEX`, `UV_EXTRA_INDEX_URL` | Removed | Installer child process | `--public-lock-index` | 352 |
| `PIP_RETRIES` | `1` | Every child process | Every run | 642 |
| `PIP_TIMEOUT` | `15` | Every child process | Every run | 643 |
| `PIP_INDEX_URL` | `https://pypi.org/simple` | Every child process | The configured index does not answer | 427 (installer), 645 (all) |
| `PIP_EXTRA_INDEX_URL` | Removed | Every child process | The configured index does not answer | 428 (installer), 646 (all) |
| `PIP_CONFIG_FILE` | The platform null device | Installer child process | The configured index does not answer | 429 |
| `PYTHONNOUSERSITE` | Removed | The child process that runs the pip install of uv | No uv found, and the Python is not externally managed | 456 |
| `NODE_OPTIONS` | The caller value, plus `--use-system-ca` when absent | Browser child process | The option is absent | 662 (check), 665 (append) |

## 4. Report lines

The report prints at the end of each successful run, in this order. The function `report_result` starts at line 689.

| Order | Report line | Line | Condition |
|-------|-------------|------|-----------|
| 1 | `The environment is ready.` | 692 | Every run |
| 2 | `Installed dependencies with uv sync --locked --extra dev.` | 693 | Every run |
| 3 | `Pip exports remain available: requirements.txt, requirements-dev.txt` | 694 | Every run |
| 4 | `Interpreter:` followed by the interpreter path | 695 | Every run |
| 5 | `To activate the environment, run:` followed by the activation command | 696 | Every run |
| 6 | `To run the tests, run: python -m pytest -q` | 697 | Every run |
| 7 | `To run the browser tests, run: python -m pytest tests/e2e/upgrade_portal` | 699 | The browser download succeeds |
| 8 | Browser warning and repair command | 701 to 703 | The browser download fails |

Each command also logs its elapsed time with the text `%s took %.1f seconds.` at line 533. The log line includes the command context, such as `The locked UV sync`, and it logs a failed command too.

## 5. Exit status

| Status | Cause | Line |
|--------|-------|------|
| 1 | The bootstrap interpreter is below Python 3.15 | 894 |
| 1 | An install or sync fails, or a tool cannot start | 900 to 901 |
| 0 | Every other run, including a failed browser download | 909 |

## 6. Messages that the script prints

| Constant | Line | Starts with |
|----------|------|-------------|
| `EXTERNALLY_MANAGED_MESSAGE` | 132 | The words "uv is not installed." |
| `INDEX_MISMATCH_MESSAGE` | 136 | The words "The configured package index does not match uv.lock." |
| `LOCK_DRIFT_MESSAGE` | 141 | The words "uv.lock does not match pyproject.toml." |
| `PUBLIC_LOCK_WARNING` | 145 | The word "Caution:" followed by the public index statement |
| `STALE_LOCK_TEXT` | 153 | The phrase that uv prints for a stale lock, which the script reads |

## 7. Rules for the guide

1. Name the locked sync in Step 2 and in the installer section.
2. Name each setting in section 3 that applies to an installer child process, the browser child process, or the public index case.
3. Quote the report line in section 4 exactly.
4. Describe no command in section 2 that the bootstrap does not run.
5. Describe the source sweep (row 0) only in a separate issue (D-5).
6. Keep the two pip export files described as manual installs only (FR-007).

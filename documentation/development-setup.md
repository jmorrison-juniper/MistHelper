# Development Setup

The container is the supported way to **run** MistHelper. This page describes
how to run the code from a source checkout, which is what a contributor needs.

Read [the container deployment page](container-deployment.md) if you want to run
the tool and not to change it.

## Requirements

| Item | Minimum |
|------|---------|
| Python | 3.13 or newer |
| mistapi | 0.64.0, less than 0.65 |
| Container runtime | Podman (primary) or Docker |

`requirements.txt` and `pyproject.toml` hold the full dependency list.

## Step 1: Get the code

```powershell
git clone https://github.com/jmorrison-juniper/MistHelper.git
cd MistHelper
```

## Step 2: Create the environment

The bootstrap script creates `.venv` and installs `requirements.txt` and
`requirements-dev.txt`, in that order. Use Python 3.13 or newer to run the script.

```powershell
python scripts/bootstrap_worktree.py   # Windows, Linux, or macOS
.\scripts\bootstrap_worktree.ps1       # Windows entry point
.venv\Scripts\Activate.ps1
```

Warning: `git worktree add` copies the tracked files only, so a new worktree
holds no `.venv` directory. Run the bootstrap one time in each new worktree. If
the environment is absent, the activation line fails and the tests then run
against the global interpreter. `python -m pytest` stops with one message that
names the bootstrap command. Issue #1866 records that case.

On Linux or macOS, activate the environment with `source .venv/bin/activate`.
Windows keeps `.venv\Scripts\python.exe`. Linux and macOS keep `.venv/bin/python`.
The `--recreate` option deletes the existing environment before creation.

The bootstrap uses symbolic links for the interpreter on Linux and macOS.
It keeps interpreter copies on Windows.
This policy matches `python -m venv` and preserves the base interpreter's runtime library paths.
Environment creation does not require uv.
The installer choices below remain unchanged.
`UV_LINK_MODE=copy` still applies to installed packages, not to the interpreter.

### Recover an earlier partial environment

If an earlier macOS bootstrap reported `@rpath/libpython3.13.dylib`, recreate the environment in that worktree.
Use a working Python 3.13 or newer outside the broken environment.

Caution: `--recreate` removes all packages in this worktree's `.venv`.
The bootstrap then creates the environment and installs the declared requirements again.

```bash
python3.13 scripts/bootstrap_worktree.py --recreate
```

Without `--recreate`, the bootstrap keeps an existing interpreter path, including one from a partial failed creation.
Issue #3701 records the copied-interpreter failure and this repair.

### Installer selection and reports

The bootstrap checks for `uv` once per invocation.
If `uv` is available, the bootstrap uses its resolved executable for each present requirement file.
Each command uses `uv pip install --python <worktree interpreter> -r <requirement file>`.
The explicit interpreter prevents installation into another environment.

If `uv` is absent, the bootstrap uses `<worktree interpreter> -m pip install -r <requirement file>`.
It reports the absence before installation.
The bootstrap does not install `uv` automatically.
It keeps pip available for configuration discovery and the absence-only fallback.
It changes no package pins or dependency declarations.

Each uv installation receives these child-only settings:

| Setting | Purpose |
|---------|---------|
| `UV_LINK_MODE=copy` | Use file copies instead of hardlinks for worktree storage, including OneDrive. |
| `UV_NATIVE_TLS=1` | Use system certificate trust with uv versions that recognize this setting. |
| `UV_SYSTEM_CERTS=1` | Use the modern uv setting for the same system certificate trust. |
| `UV_NO_CONFIG=1` | Prevent saved uv source settings from replacing the existing pip source choices. |

The bootstrap removes `UV_CONFIG_FILE` from each uv installation child.
It does not disable certificate verification.
Each file receives a new environment copy.
Proxy settings, certificate paths, and other unrelated caller settings remain available.
The caller environment and saved configuration remain unchanged.

The report identifies the installer and each attempted file.
Each attempt reports elapsed seconds to one decimal place, including failed attempts.
A successful invocation reports total installation time.
An invocation with no requirement files reports a total and installs no package.
Actual duration depends on caches, storage, and network conditions.

Caution: a failed installation leaves an incomplete environment.
The bootstrap returns status `1` and stops before later setup actions.
It does not retry a failed uv installation through pip.
This rule also applies when a discovered uv executable cannot start.
Correct the reported fault before you run setup again.

### Package sources

The bootstrap reads pip configuration once through the worktree interpreter.
It retains the existing connection probe, with a three-second timeout.
Working mirrors remain selected.
For uv, nonempty caller `PIP_INDEX_URL` and `PIP_EXTRA_INDEX_URL` values take precedence.
Install-specific pip configuration follows, then global pip configuration.
Primary and extra sources use this precedence independently.
Extra-source order remains unchanged.
The bootstrap removes competing uv source aliases only from installation children.
It keeps uv's default source-resolution policy.

If the configured mirror does not answer, the invocation uses `https://pypi.org/simple` exclusively.
The child removes inherited extra indexes and competing uv source aliases.
For pip installation, child `PIP_CONFIG_FILE` uses the platform's null device.
This setting prevents saved extra indexes from restoring the failed mirror.
For uv installation, child `UV_NO_CONFIG=1` prevents saved uv settings from restoring it.
The bootstrap changes no pip or uv configuration file.
Each later invocation makes a fresh installer and source decision, including after a failed invocation.

The pip path retains `PIP_RETRIES=1` and `PIP_TIMEOUT=15`.
The uv path uses `UV_HTTP_RETRIES=1` and `UV_HTTP_TIMEOUT=15` for the same transport bounds.
These controls remain in the installation child and do not change caller settings.
Bootstrap reports identify source hosts or decisions, not source credentials or environment dictionaries.

### Browser and account checks

After dependency installation succeeds, the bootstrap retains its health, browser, readiness, and account steps.
The browser child preserves caller `NODE_OPTIONS` and adds `--use-system-ca` only when absent.
It receives no newly forced uv controls or pip null-configuration setting.
The browser repair guidance below remains unchanged.

The bootstrap keeps the repository credential username `jmorrison-juniper`.
It also checks the active GitHub account.
If credential variables select another account, the warning names `GH_TOKEN` or `GITHUB_TOKEN`, not their values.
The report gives the existing account repair command.

To build the environment by hand instead:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
```

If uv is available, you can replace the final command with
`uv pip install --python .venv\Scripts\python.exe -r requirements.txt -r requirements-dev.txt`.
On Linux or macOS, use `.venv/bin/python` as the interpreter argument.
Manual installation does not perform the bootstrap's source probe or browser download.
The development requirements install the quality tools from a reviewed, immutable commit in `misthelper-devtools`.

## Step 3: Configure the credentials

```powershell
Copy-Item documentation\sample.env .env
```

Set these values in `.env`:

- Required: `MIST_APITOKEN` holds your Mist API token.
- Helpful: `org_id` skips the organization prompt.
- Optional: the SSH values, for the device command operations.

To create the token:

1. Sign in to <https://manage.mist.com>.
2. Open Organization, then API Tokens.
3. Create a token with the permissions that you need.
4. Copy the token into `.env`.

Warning: `.env` holds a live credential. The repository ignores that file. Never
commit it, and never paste its contents into an issue or a pull request.

## Step 4: Check the setup

```powershell
python MistHelper.py --help
python MistHelper.py --menu 1
python MistHelper.py --test
```

## Work on a change

Each change gets its own worktree and its own branch.

```powershell
git worktree add ../MistHelper-<slug> -b <type>/<issue>-<slug> main
cd ../MistHelper-<slug>
python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

Remove the worktree after the merge.

```powershell
cd ../MistHelper
git worktree remove ../MistHelper-<slug>
git pull origin main
```

Run [the quality gates](quality-gates.md) before every commit.

## Run the browser tests

The tests under `tests/e2e/` drive a real browser. The bootstrap installs the
two packages and downloads Chromium, so a fresh worktree needs no extra step.

```powershell
python -m pytest tests/e2e/upgrade_portal
```

Warning: a missing browser package does not fail the run. Each browser test
module calls `pytest.importorskip`, so the whole suite reports a skip, and
pytest reports a skip as a pass. Issue #2241 recorded 11 test files that covered
nothing while the gate stayed green.

Set one variable to turn that skip into a failure. The `E2E smoke tests` gate
sets it on every run.

```powershell
$env:UPGRADE_PORTAL_E2E_STRICT = "1"
python -m pytest tests/e2e/upgrade_portal
```

If the browser download failed, repair it with one command. The command sets
the Node option `--use-system-ca`, so the download trusts the certificate store
of the system.

```powershell
$env:NODE_OPTIONS = "--use-system-ca"; python -m playwright install chromium
```

On Linux, run `NODE_OPTIONS=--use-system-ca python -m playwright install chromium`.

Playwright downloads the browser with its own Node runtime. That runtime trusts
only its own certificate list by default. A proxy that inspects TLS, such as
Zscaler, signs each certificate with a root that only the system store holds.
Without the option, the download fails with `UNABLE_TO_GET_ISSUER_CERT_LOCALLY`.
The option removes no certificate, so it is safe on a network without a proxy.
The bootstrap sets the option for its own download. See issue #3302.

The tests start their own portal, because only that portal holds the sign-in
seam. If another process already listens on port 8056, every test reports an
error that names the port. A running portal container is the common cause. Stop
the container, or point the tests at an ephemeral port.

```powershell
$env:CAPTURE_PORT = "9606"
python -m pytest tests/e2e/upgrade_portal
```

Port 9606 sits in the ephemeral range 9600 through 9699. That range holds no
production service, so the tests never take a port from the running stack.

### Container rules for a browser test

If a browser test or a debug session needs a container, obey these four rules.
`documentation/container-deployment.md` § "Test and debug containers" holds the
full policy and the cleanup commands.

1. Start the container inside the compose group. Use
   `.\scripts\compose.ps1 run --rm`, or add the service to `compose.yml` under
   a profile. Never start a one-off container with a bare `podman run`.
2. Name an ephemeral container for the issue or the pull request that it
   serves. Use the format `misthelper-tmp-<issue|pr><number>-<slug>`.
3. Publish a port in the range 9600 through 9699. Never publish a production
   local port. Read `compose.yml` for the current set. Today it holds 1161/udp,
   1514/udp, 2200, 8055, 8056, 8057, 8668, 9379, 9526, and 9529.
4. Remove the container, its volume, and its network when the test ends. Never
   leave a test container running.

```powershell
podman rm -f misthelper-tmp-<issue|pr><number>-<slug>
podman ps -a --filter "name=misthelper-tmp-" --format "{{.Names}} {{.Status}}"
```

The second command confirms the cleanup. An empty result means the cleanup
finished.

## Never install this project into its own environment

Warning: do not run `pip install .` or `uv pip install .` in this repository. The
install copies `src/` into `site-packages`. That copy then shadows the real
package for every script that runs from another folder, and the tests read code
that nobody ships.

Both copies import cleanly, so no gate reports the difference. A green test run
proves nothing while the copy exists. Issue #2010 records a session that lost an
hour to it.

Issue #2246 narrowed the wheel, so an install no longer copies `tests/`,
`scripts/`, `specs/`, or `documentation/`. The wheel still ships `src`, because
every module of this project imports `src.<area>`. A local install therefore
still shadows the checkout, and this rule still holds.

Install the requirements instead. `scripts/bootstrap_worktree.py` does that
already.

If you suspect the copy, ask Python where it reads the package from.

```powershell
python -c "import src; print(src.__file__)"
```

A path inside `.venv` names the stale copy. Remove it with one command.

```powershell
python -m pip uninstall -y misthelper
```

`tests/conftest.py` also checks this before pytest collects a single module. The
session stops with a message that names the path and the command above.

## Where the code lives

New code goes in `src/`, and not in `MistHelper.py`. The entrypoint holds the
menu registry and delegates the work. Read [the architecture
page](architecture.md) for the package layout.

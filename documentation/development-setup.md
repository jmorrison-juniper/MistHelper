# Development Setup

The container is the supported way to **run** MistHelper. This page describes
how to run the code from a source checkout, which is what a contributor needs.

Read [the container deployment page](container-deployment.md) if you want to run
the tool and not to change it.

## Requirements

| Item | Minimum |
|------|---------|
| Python | 3.13 |
| mistapi | 0.63.1 |
| Container runtime | Podman (primary) or Docker |

`requirements.txt` and `pyproject.toml` hold the full dependency list.

## Step 1: Get the code

```powershell
git clone https://github.com/jmorrison-juniper/MistHelper.git
cd MistHelper
```

## Step 2: Create the environment

The bootstrap script creates `.venv` and installs `requirements.txt` and
`requirements-dev.txt`.

```powershell
python scripts/bootstrap_worktree.py   # Windows or Linux
.\scripts\bootstrap_worktree.ps1       # Windows entry point
.venv\Scripts\Activate.ps1
```

Warning: `git worktree add` copies the tracked files only, so a new worktree
holds no `.venv` directory. Run the bootstrap one time in each new worktree. If
the environment is absent, the activation line fails and the tests then run
against the global interpreter. `python -m pytest` stops with one message that
names the bootstrap command. Issue #1866 records that case.

To build the environment by hand instead:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install uv
uv pip install -r requirements.txt
```

UV installs faster than pip. `pip install -r requirements.txt` also works.

## Step 3: Configure the credentials

```powershell
cp documentation\sample.env .env
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
git checkout main
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

If the browser download failed, repair it with one command.

```powershell
python -m playwright install chromium
```

The tests start their own portal, because only that portal holds the sign-in
seam. If another process already listens on port 8056, every test reports an
error that names the port. A running portal container is the common cause. Stop
the container, or point the tests at a free port.

```powershell
$env:CAPTURE_PORT = "8066"
python -m pytest tests/e2e/upgrade_portal
```

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

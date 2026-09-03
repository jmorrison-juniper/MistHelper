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

## Where the code lives

New code goes in `src/`, and not in `MistHelper.py`. The entrypoint holds the
menu registry and delegates the work. Read [the architecture
page](architecture.md) for the package layout.

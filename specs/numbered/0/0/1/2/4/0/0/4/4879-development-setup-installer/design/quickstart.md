# Quickstart: Development setup installer text

This guide reproduces the defect and proves the fix. Run each verification command from the worktree root `..\MistHelper-4879` after task T001. The reproduction steps read files only, so they can run from the main checkout.

## Prerequisites

- The worktree `..\MistHelper-4879` on branch `fix/4879-development-setup-installer` (task T001).
- The environment that the bootstrap creates in the worktree. Run `uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py` once in that worktree. The environment provides `.venv\Scripts\ste-linter.exe` and `pytest`.
- No production credential is needed.

## Reproduce the defect on main

Run each command from the repository root. Each command reads files only.

1. Run `git grep -n "in that order" -- documentation/development-setup.md`. Expect line 29, which names the two requirement files (R-03).
2. Run `git grep -n "uv sync --locked --extra dev" -- documentation/development-setup.md`. Expect no output, because the guide does not name the locked sync (R-11).
3. Run `git grep -n -e "each attempted file" -e "total installation time" -e "no requirement files" -- documentation/development-setup.md`. Expect lines 83, 85, and 86 (R-06 to R-08).
4. Run `git grep -n "Enforce the committed lock" -- scripts/bootstrap_worktree.py`. Expect line 466, where the script runs the locked sync (R-15).
5. Run `git grep -n "Installed dependencies with uv sync" -- scripts/bootstrap_worktree.py`. Expect line 693, the report line (R-16).

## Verification after the change

Run each command from the worktree root. Each check names the requirement that it proves.

### TST-001 (FR-008): STE score

```powershell
.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation\development-setup.md changelog.d\issue-4879-development-setup-installer.md
```

Expect exit code 0. Each file scores 80 or above in the output.

### TST-002 (FR-002): retired statements absent

```powershell
git grep -n -e "in that order" -e "each attempted file" -e "no requirement files" -e "total installation time" -e "no installation exists" -e "Extra-source order" -e "browser repair guidance below" -e "Each file receives" -e "uv installation child" -- documentation/development-setup.md
```

Expect no output and exit code 1.

### TST-003 (FR-001): locked sync named

```powershell
git grep -c "uv sync --locked --extra dev" -- documentation/development-setup.md
```

Expect a count of 2 or more for `documentation/development-setup.md`. The count covers Step 2, the locked sync paragraph, and the report paragraph.

### TST-004 (FR-003): discovery and lock messages

```powershell
git grep -n -e "per-user folders" -e "uv lock" -e "needs an update" -- documentation/development-setup.md
```

Expect at least three lines. Line 57 names the per-user folders. The other lines name the drift message and the locked sync stop.

### TST-005 (FR-005): settings named

```powershell
foreach ($name in 'UV_LINK_MODE','UV_NATIVE_TLS','UV_SYSTEM_CERTS','UV_NO_CONFIG','UV_HTTP_RETRIES','UV_HTTP_TIMEOUT','UV_INDEX_URL','UV_EXTRA_INDEX_URL','PIP_RETRIES','PIP_TIMEOUT','PIP_INDEX_URL','PIP_CONFIG_FILE','UV_CONFIG_FILE','PYTHONNOUSERSITE','NODE_OPTIONS') {
    git grep -q -F $name -- documentation/development-setup.md
    "$name present=$($LASTEXITCODE -eq 0)"
}
```

Expect `present=True` for each name.

### TST-006 (FR-006): report line exact

```powershell
git grep -n -F "Installed dependencies with uv sync --locked --extra dev." -- documentation/development-setup.md
```

Expect one line, in the report paragraph.

### TST-007 (FR-007): pip export statement

```powershell
git grep -n -F "The bootstrap installs neither file." -- documentation/development-setup.md
```

Expect one line, in the pip export paragraph.

### TST-008 (FR-004): public index option

```powershell
git grep -n -F "for that run only" -- documentation/development-setup.md
git grep -n -F "changes no pip configuration" -- documentation/development-setup.md
```

Expect one line for each command. Both lines sit in the installer section.

### TST-009 (FR-009): changed files

```powershell
git diff --name-only origin/main
```

Expect exactly two paths: `documentation/development-setup.md` and `changelog.d/issue-4879-development-setup-installer.md`.

### TST-010 (FR-009): existing guard

```powershell
python -m pytest tests/guardrails/test_container_policy_docs.py -q -rs
```

Expect every test to pass. The output shows no skip for `documentation/development-setup.md`. The guard checks code blocks for destructive volume commands. The change must add no volume removal or volume prune line.

## Expected final state

- The guide names the locked sync command in at least two lines, as TST-003 shows.
- The guide holds no retired statement, as TST-002 shows.
- The guide names the twelve settings of the contract, as TST-005 shows.
- Both changed files score 80 or above, as TST-001 shows.
- Only the guide and the fragment changed, as TST-009 shows.

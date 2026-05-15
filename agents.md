# MistHelper - AI Agent Instructions

> **Canonical source**: `.github/copilot-instructions.md` contains the full project guide
> (architecture, database strategy, workflows, CI/CD, git workflow, web UI autonomy).
> This file supplements it with local VS Code Chat-specific notes.
> Do NOT duplicate content from copilot-instructions.md here.

## Role

You are an autonomous software engineer. Parse requests, infer missing details,
implement complete solutions, write tests, and run quality gates -- all without
requiring intervention unless a critical ambiguity blocks progress.

When refactoring, restructure into classes per project conventions. No wrappers.

## Local Development Quick Reference

```powershell
# Activate venv
.venv\Scripts\Activate.ps1

# Quality gates (run before every commit)
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py
python -m black --check MistHelper.py

# Test suite (skip heavy/destructive: 14, 18, 63-65, 90-100)
python MistHelper.py --test

# Worktree setup for feature work
git worktree add ../MistHelper-<slug> -b <type>/<issue>-<slug> main
cd ../MistHelper-<slug>

# Worktree teardown after merge
cd ../MistHelper
git worktree remove ../MistHelper-<slug>
git checkout main && git pull origin main
```

## VS Code Chat-Specific Notes

- **Browser tools**: Enable `workbench.browser.enableChatTools` for web UI testing
- **SpecKit agents**: Use `speckit.specify` / `speckit.plan` / `speckit.tasks` / `speckit.implement`
  for multi-file changes (see copilot-instructions.md for escalation criteria)
- **Copilot Spaces**: Use for planning sessions and architecture discussions --
  attach `agents.md`, `MistHelper.py`, and `CHANGELOG.md` for persistent context
- **Scratchpads**: Use for quick API exploration and prototyping -- no git, discard after use
- **Memory**: Store codebase facts in `/memories/repo/` for cross-session persistence

## Key Conventions (Quick Reminders)

- **Target audience**: Junior NOC engineers. Clear language, no jargon.
- **Python 3.13+**, **mistapi 0.59+**, **UV** preferred over pip
- **5-Item Rule**: Max 5 children per hierarchy level, max 5 params, max 25 lines per function
- **safe_input()**: Wrap all `input()` calls for EOF handling in SSH/container contexts
- **Natural business keys**: Define PK strategy in `ENDPOINT_PRIMARY_KEY_STRATEGIES` for new operations
- **ASCII only in logs**: No Unicode/emoji
- **File paths**: Use `os.path.join()` or `pathlib.Path()`, never hardcoded separators
- **Container**: Podman primary, port 2200 (SSH), port 8055 (web UI)
- **Zscaler**: Use GitHub Actions for container builds, never local `podman push`
- **Inline comments on EVERY line** (NON-NEGOTIABLE): Every executable line of AI-generated
  code must have an inline comment explaining *why*, not just *what*. Code without comments
  is incomplete. When editing existing code, add comments to the entire block being touched.
- **Action logging before/after EVERY operation** (NON-NEGOTIABLE): `logging.info()` before
  every action, `logging.debug()` after with result summary. Code without logging is code
  without observability. When editing existing code, add logging to the entire block being
  touched.

## External Resources

- Mist API Docs: `documentation/mist-api-openapi3*.{json,yaml}`
- mistapi SDK: https://github.com/tmunzer/mistapi_python
- Reference implementations: https://github.com/tmunzer/mist_library

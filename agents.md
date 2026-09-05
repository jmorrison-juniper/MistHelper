# MistHelper - AI Agent Instructions

> **Canonical source**: `.github/copilot-instructions.md` contains the full project guide
> (architecture, database strategy, workflows, CI/CD, web UI autonomy).
> **Branching, parallel agents, and GitHub Actions minutes** live in
> [.github/instructions/git-flow-multi-agent.instructions.md](.github/instructions/git-flow-multi-agent.instructions.md).
> This file supplements both with local VS Code Chat-specific notes.
> Do NOT duplicate content from either file here.

## Role

You are an autonomous software engineer. Parse requests, infer missing details,
implement complete solutions, write tests, and run quality gates -- all without
requiring intervention unless a critical ambiguity blocks progress.

When refactoring, restructure into classes per project conventions. No wrappers.

## Local Development Quick Reference

```powershell
# Prepare a new worktree. "git worktree add" does not copy .venv, so a new
# worktree has no virtual environment until you run this script.
.\scripts\bootstrap_worktree.ps1        # Windows
python scripts/bootstrap_worktree.py    # Windows or Linux

# Activate venv
.venv\Scripts\Activate.ps1

# Quality gates (run before every commit)
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py
python -m black --check MistHelper.py

# Test suite. The registry decides what runs: --test covers `safe`, and
# --testinteractive adds `interactive_safe`. Every other category is skipped,
# including destructive (154-187, 189-191, 194, 206-208).
python MistHelper.py --test

# Worktree setup for feature work
git worktree add ../MistHelper-<slug> -b <type>/<issue>-<slug> main
cd ../MistHelper-<slug>
python scripts/bootstrap_worktree.py   # Required. The new worktree has no .venv.
.venv\Scripts\Activate.ps1

# Worktree teardown after merge
cd ../MistHelper
git worktree remove ../MistHelper-<slug>
git checkout main && git pull origin main
```

**Warning**: A new worktree holds the tracked files only. `.venv` is not tracked, so
`.venv\Scripts\Activate.ps1` fails there and the tests then run against the global
interpreter. `python -m pytest` stops with one message that names the bootstrap
command. Run `python scripts/bootstrap_worktree.py`, activate the environment, then
run the tests again. See issue #1866.

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
- **Zscaler**: Zscaler blocks a `podman push` to `ghcr.io`. Build and run the image
  locally with `podman build` and `podman run`. Use GitHub Actions only when the
  registry must hold the image, such as a release.
- **Actions minutes**: MistHelper is public, so a standard runner costs nothing.
  A private repository spends the 2,000 free minutes each month. Validate locally
  first. Never push a commit only to start a workflow. See
  [git-flow-multi-agent.instructions.md](.github/instructions/git-flow-multi-agent.instructions.md)
  § Part 3.
- **Automated sweep**: An automated sweep runs four checks before a commit. See
  the "Automated Sweep Safety" section in `.github/copilot-instructions.md`.
- **Inline comments on EVERY line** (NON-NEGOTIABLE): Every executable line of AI-generated
  code must have an inline comment explaining *why*, not just *what*. Code without comments
  is incomplete. When editing existing code, add comments to the entire block being touched.
- **Action logging before/after EVERY operation** (NON-NEGOTIABLE): `logging.info()` before
  every action, `logging.debug()` after with result summary. Code without logging is code
  without observability. When editing existing code, add logging to the entire block being
  touched.
- **Token efficiency** (Effective June 2026): Use Auto mode by default. Share only relevant
  files/functions -- never entire repos. Start only needed MCP servers. Use agent mode for
  multi-step tasks, standard chat for quick questions. Ask for a plan before large changes.
  See `.github/copilot-instructions.md` § Agent Observability & Efficiency for full details.
- **Writing style -- Simplified Technical English (STE)** (NON-NEGOTIABLE): All
  documentation, code comments, pull request text, error messages, user-facing
  communication and printed output, and agent output MUST follow the STE writing
  guide at `documentation/ASD-STE100_writing-guide.md`. One word = one meaning; one
  term per concept, reused consistently; active voice; simple tenses; short
  sentences (<=20 words instructions, <=25 descriptions); imperative for steps with
  the condition first ("If X, do Y"); no semicolons, slang, jargon, or Latin
  abbreviations (e.g./i.e./etc.); American spelling; never alter quoted
  strings/identifiers. Warnings lead with a signal word and state the consequence.
  STE outranks the caveman rules in `.github/instructions/caveman.instructions.md`.
  If the two rule sets conflict, obey STE. Caveman may cut filler, pleasantries,
  and hedging. Caveman must not drop an article, write a fragment, or swap a
  synonym. Use the caveman `lite` level, because it is the only level that obeys
  STE.

## External Resources

- Mist API Docs: `documentation/mist-api-openapi3*.{json,yaml}`
- mistapi SDK: https://github.com/tmunzer/mistapi_python
- Reference implementations: https://github.com/tmunzer/mist_library

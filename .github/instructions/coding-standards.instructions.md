---
description: "Use when: writing or reviewing any code. Global coding standards, autonomous workflow, and quality principles that apply across all projects and workspaces."
applyTo: "**"
---

# Global Coding Standards

## Autonomous Workflow

You are an elite autonomous software engineer. Take high-level requests
and independently deliver complete, production-ready, fully tested
solutions without requiring intervention unless a critical ambiguity
blocks progress.

1. **Requirement Analysis** -- Parse the request, infer missing details,
   make reasonable assumptions.
2. **Architecture & Design** -- Decide on structure, algorithms, and
   libraries.
3. **Implementation** -- Write complete, functional, well-documented
   code.
4. **Self-Instrumentation** -- Embed test points, logging hooks,
   assertions, and sanity checks for critical logic paths.
5. **Self-Testing** -- Write unit, integration, and edge-case tests.
   Run them. If any fail, debug, refactor, and re-run until all pass.
6. **Final Output** -- Present only the final, improved, fully tested
   version.

### Rules

- Assume autonomy -- do not ask for clarifications unless absolutely
  necessary.
- Always produce runnable, tested code.
- Prefer clarity and maintainability over cleverness; optimize where it
  matters.
- Use stable, well-supported libraries and explain why they were chosen.
- If a feature is ambiguous, make a reasonable assumption and document
  it.

---

## Structural Discipline (5-Item Rule)

Every level of a project hierarchy should contain no more than five
children. If exceeded, refactor by extracting into sub-levels.

Hierarchy levels (largest to smallest):
1. **Project Root** -- top-level folder
2. **Packages / Directories** -- folders that organize code
3. **Module Files** -- individual source files
4. **Classes / Functions / Constants** -- top-level constructs in modules
5. **Methods / Attributes / Expressions** -- class members and function
   bodies

### Function / Method Limits

- **Max 5 parameters** per function. Use config objects/dataclasses or
  split into multiple functions if more are needed.
- **Max 5 logical blocks** per function body (if/else = 1 block,
  for-loop = 1 block). Extract blocks into helpers if exceeded.
- **Max 5 operations** per statement block. Break complex expressions
  into intermediate variables.
- **Max 25 lines** per function (5 blocks x ~5 lines). Extract logical
  sections into helper functions if longer.

**Rationale**: Keeps code navigable, reviewable, and maintainable.

---

## Architecture Principles

### Class-Based Design (No Wrappers)

All functionality should live within semantically named classes.
Standalone wrapper functions that merely delegate to a class method are
prohibited. When refactoring, restructure into proper classes -- never
wrap.

### No Legacy Compatibility Shims

Do not introduce or retain legacy compatibility shims during refactors.
Avoid temporary pass-through aliases, adapter wrappers, facade stubs,
or fallback compatibility paths kept only to preserve old call sites.
Complete the migration at real call sites and remove obsolete paths.

### Naming Standards

- Use full, descriptive names: `for device in devices` NOT
  `for d in devices`.
- No AI-generated marker text (`...existing code...`, double ellipses)
  in committed code.

---

## Safety-First Input Handling

All input handling should use EOF-safe patterns with context logging.
Every `input()` call in SSH/container contexts, destructive
confirmations, and interactive menus should be wrapped:

```python
def safe_input(prompt: str, context: str = "unknown") -> str:
    try:
        return input(prompt)
    except EOFError:
        logging.info(f"EOF detected in {context} - session disconnected")
        sys.exit(0)
```

Destructive operations require explicit typed confirmation:
```python
confirmation = safe_input("Type 'CONFIRM' to proceed: ", context="...")
if confirmation != "CONFIRM":
    return  # Early return on validation failure
```

All external inputs must be validated before use. Pattern: **validate
early, return early**.

---

## Inline Comments (NON-NEGOTIABLE)

Every line of AI-generated code MUST have an inline comment on the
same line explaining what it does and why. This is not optional.
Comments must be meaningful -- they explain intent, not just restate
the code.

```python
# WRONG: No comments
result = api.get_sites(org_id)
sites = [s for s in result if s.get("name")]

# WRONG: Restating the code
result = api.get_sites(org_id)  # get sites
sites = [s for s in result if s.get("name")]  # filter sites

# CORRECT: Explaining intent and context
result = api.get_sites(org_id)  # Fetch all sites for this org from Mist API
sites = [s for s in result if s.get("name")]  # Exclude unnamed/placeholder sites
```

**Rules**:
- Every executable line gets an inline comment (same line, after code).
- Comments explain *why* and *what for*, not just *what*.
- Blank lines, closing braces/parens, and decorators are exempt.
- If existing code is being modified, add inline comments to the
  changed lines AND to any adjacent uncommented lines in the same
  block.
- If existing code is found lacking inline comments during any edit,
  add them to the entire function or block being touched.
- Target audience: a junior engineer reading the code for the first
  time should understand every line without external context.

**Rationale**: Junior NOC engineers maintain this codebase. Inline
comments eliminate guesswork and reduce onboarding time. Code without
comments is incomplete code.

---

## Logging Standards

- **Debug**: Internal state changes, raw responses
- **Info**: User-facing progress messages
- **Error**: Exception context with full traceback
- **Never log secrets**: Redact tokens and passwords at the logging
  boundary
- **ASCII only**: No Unicode/emoji in log output for cross-platform
  compatibility

### Action Logging (NON-NEGOTIABLE)

Every meaningful action in AI-generated code MUST have a logging
statement before AND after execution. This enables operators to trace
exactly what happened during any run.

```python
# WRONG: No logging around actions
result = api.list_devices(site_id)
processed = flatten_response(result)

# CORRECT: Log before and after every action
logging.info("Fetching device list for site %s", site_id)  # Log before API call
result = api.list_devices(site_id)  # Call Mist API for all devices at this site
logging.debug("Received %d devices from API", len(result))  # Log result count
logging.info("Flattening device response data")  # Log before data transform
processed = flatten_response(result)  # Normalize nested JSON to flat structure
logging.debug("Flattened %d device records", len(processed))  # Log output count
```

**Rules**:
- Log an `info` message BEFORE every action (API call, file write,
  database operation, data transformation, user prompt).
- Log a `debug` message AFTER every action with the result summary
  (count, status, size -- never secrets).
- Log `error` with full context on any exception.
- If existing code is found lacking action logging during any edit,
  add logging to the entire function or block being touched.
- Format: use `%s` style formatting in logging calls (not f-strings)
  for performance and security.

**Rationale**: When a NOC engineer reports "it broke at step 3," the
logs must show exactly what happened before, during, and after step 3.
Code without logging is code without observability.

---

## Quality Gates

Before merging or deploying any code change:

1. **Syntax validation** -- Compile/parse check must pass before commit
2. **Linting** -- Zero lint violations (use project-configured linter)
3. **Formatting** -- Code formatter check must pass (e.g., black, ruff
   format)
4. **Type checking** -- Static type analysis must pass
5. **Tests** -- All unit and integration tests must pass
6. **Security** -- No known vulnerabilities in dependencies or code

### Security Findings: Fix Over Suppress

Security tool findings (bandit, pip-audit, CodeQL, etc.) must be
**resolved**, not suppressed. The priority order:

1. **Fix the root cause** -- Rewrite the code to eliminate the
   vulnerability (e.g., validate inputs, use parameterized queries).
2. **Refactor to avoid the pattern** -- If the tool flags a code
   pattern, restructure so the pattern isn't needed (e.g., move a
   secret from a default dict to `os.environ.get()` directly).
3. **`#nosec` only for verified false positives** -- When the tool
   misidentifies safe code (e.g., a logging f-string flagged as SQL
   injection, or an intentional `0.0.0.0` bind gated by container
   detection). The annotation MUST include a justification comment.

Never use `#nosec`, `# type: ignore`, `# noqa`, or similar
suppressions as a shortcut to silence legitimate findings. If a
finding requires more than a trivial fix, create a GitHub issue
and track it.

---

## File Path Management

- Use `os.path.join()` or `pathlib.Path()` -- never hardcode `/` or
  `\\` separators.
- Windows compatibility is always required.

---

## General Principles

- **Explicit > Implicit** -- Be clear about intent.
- **Readable > Concise** -- Prioritize understanding over brevity.
- **Safe > Fast** -- Safety and correctness before optimization.
- Target audience for user-facing text: clear, professional language
  without jargon.

---

## Writing & Communication Style (Simplified Technical English)

Write all prose in Simplified Technical English (STE): controlled, unambiguous
English that non-native readers and junior engineers understand the same way.
This applies to all documentation, code comments, pull request text, error
messages, user-facing communication and printed output, and agent (chat) output.

Core defaults:
- One word, one meaning; one term per concept, reused consistently (no synonym
  swapping).
- Active voice; simple tenses (no perfect/progressive); direct address (you/we).
- Short sentences: <=20 words for instructions, <=25 for descriptions; one idea
  each.
- Instructions use the imperative, one action per step, condition first
  ("If X, do Y").
- No semicolons, slang, jargon, regionalisms, phrasal verbs, or Latin
  abbreviations (e.g./i.e./etc.); American spelling; never alter quoted strings
  or identifiers.
- Warnings lead with a signal word (Warning = harm/irreversible; Caution =
  recoverable) and state the specific consequence.

In the MistHelper repo, the full guide is at
`documentation/ASD-STE100_writing-guide.md` (distilled from ASD-STE100 Issue 9).

### Precedence: STE outranks caveman

STE outranks the caveman compression rules in `caveman.instructions.md`. If the
two rule sets conflict, obey STE. STE is NON-NEGOTIABLE. Caveman is a preference.

Caveman may remove filler, pleasantries, and hedging. Caveman must not drop an
article, write a fragment, swap a synonym, or use slang. Use the caveman `lite`
level, because it is the only level that obeys STE. Use a higher caveman level
only when the user states that STE is suspended for the session.

---

## Copilot Token Efficiency

See `copilot-token-efficiency.instructions.md` in the VS Code user profile.
That file governs the local editor only, so no repository holds a copy.

---

## Multi-Agent Git Workflow

See `git-flow-multi-agent.instructions.md` for the branch model, the rules for
parallel agents, and the rules that protect the GitHub Actions minute balance.
That file is authoritative and replaces the retired workflow guide.

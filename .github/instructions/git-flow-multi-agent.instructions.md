---
description: "Use when: you create a branch, you commit, you open a pull request, or you start a workflow run. Defines the branch model, the rules that keep parallel agents apart, and the rules that protect the GitHub Actions minute balance."
applyTo: "**"
---

# Branching, parallel agents, and Actions minutes

This file is the single source for three subjects.

1. The branch model that every change follows.
2. The rules that keep parallel agents off each other's work.
3. The rules that protect the GitHub Actions minute balance.

## Precedence

Simplified Technical English outranks this file. See
`.github/skills/ste-writing/SKILL.md`.

This file outranks any older branching text or any older continuous integration
text in `.github/copilot-instructions.md`, in `agents.md`, and in `CLAUDE.md`.
If one of those files disagrees with this file, obey this file.

## Part 1. The branch model

### The branches

| Branch | Purpose | Branch from | Merge into |
| - | - | - | - |
| `main` | The released state. Every commit is deployable. | - | - |
| `feat/<issue>-<slug>` | One new capability. | `main` | `main` |
| `fix/<issue>-<slug>` | One defect repair. | `main` | `main` |
| `chore/<issue>-<slug>` | Maintenance, dependencies, or tooling. | `main` | `main` |
| `docs/<issue>-<slug>` | Text only. No code change. | `main` | `main` |

This repository uses a trunk-based model. There is no `develop` branch. If a
future change adds one, update this table first.

### The rules

1. Create the issue before you create the branch. The branch name carries the
   issue number.
2. Branch from `main`. Never branch from another feature branch.
3. Rebase onto `main`. Never merge `main` into a feature branch.
4. Push with `--force-with-lease`. Never push with `--force`.
5. One branch answers one issue. If you find a second defect, file a second
   issue.
6. Delete the branch after the merge. Delete the worktree in the same step.

Warning: a stacked branch creates a cascading conflict. Pull requests 12
through 15 branched from each other instead of from `main`. Each merge then
broke the next branch, and an engineer repaired the same conflict four times.

## Part 2. Parallel agents

Several agents work in this repository at the same time. These rules keep one
agent from destroying the work of another agent.

### Use a worktree. Never use `git checkout`

Each agent gets its own worktree and its own virtual environment.

```powershell
git worktree add ../MistHelper-<slug> -b fix/<issue>-<slug> main
cd ../MistHelper-<slug>
python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

Warning: `git worktree add` copies the tracked files only. `.venv` is not
tracked, so a new worktree holds no virtual environment. If you skip the
bootstrap step, the tests run against the global interpreter and report a
false result.

Remove the worktree after the merge.

```powershell
cd ../MistHelper
git worktree remove ../MistHelper-<slug>
```

### Check for an overlap before you start

One file cannot carry two open pull requests. Check first.

```powershell
gh pr list --state open --json number,headRefName,files --jq '.[] | "\(.number) \(.headRefName): \([.files[].path] | join(", "))"'
```

`MistHelper.py` is a hot file. Only one agent holds an open pull request that
changes it. If another agent holds that pull request, choose one of these
actions.

- Wait for the merge.
- Work on a file that does not overlap, such as a test, a document, or a
  workflow.
- Ask the other agent to hand the file over.

### Rules for shared state

1. Never edit a file inside another agent's worktree.
2. Never push to a branch that another agent owns.
3. Never run `git checkout` in the main checkout while an editor holds a file
   open.
4. Never push a commit to a branch after a maintainer squash-merged its pull
   request. The commit becomes an orphan.
5. State the file set you intend to change before you change it.

### When the same files keep conflicting

Apply the first strategy that fits.

| Strategy | Use it when | Action |
| - | - | - |
| Sequential merge | The conflicts are small. | Merge the cleanest pull request. Every other agent rebases. Repeat. |
| Merge agent | The conflicts are large. | One agent owns the reconciliation. Every other agent stops pushing. |
| New boundary | The same file conflicts again and again. | Split the contested code into separate modules. |

If a conflict covers more than 20 lines, abandon the branch. Start again from a
fresh `main`.

## Part 3. GitHub Actions minutes

### Know which meter you spend

| Repository | Visibility | Minutes |
| - | - | - |
| `MistHelper` | Public | Free. A standard runner costs nothing. |
| `fiber-planner-copilot` | Private | Counted against the 2,000 minutes each month. |

A free account receives 2,000 minutes each month for private repositories. When
the balance reaches zero, every run fails at once, and a refused run completes
in about 0.1 minutes. The balance resets on the first day of the month.

Warning: a drained balance stops every private workflow, including a security
scan and a release. Check the visibility before you start a run. Frugality
matters most in a private repository.

### The local-first loop

Run the cheap check on your own machine. Spend a runner only for the check that
your machine cannot perform.

```powershell
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
python -m mypy $MYPY_PATHS --config-file pyproject.toml
python -m pytest tests/<the one file you changed>
```

Read the `MYPY_PATHS` value from `.github/workflows/ci.yml`.

Build and run the container on your own machine. Do not push a commit to make a
registry build an image that Podman can build here.

```powershell
podman build -t misthelper:local .
podman stop misthelper ; podman rm misthelper
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `
  -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" misthelper:local
podman ps
```

### Spend a run only for these reasons

| Reason to start a run | Spend a run |
| - | - |
| A pull request needs its required checks. | Yes. One run for each push. |
| The check needs a service that your machine cannot host. | Yes. |
| The check needs a secret that your machine cannot hold. | Yes. |
| You changed a workflow file and must see it execute. | Yes. One run. |
| You want to confirm a lint result. | No. Run the linter here. |
| You want to confirm a format result. | No. Run the formatter here. |
| You want a container image for local use. | No. Build it with Podman here. |
| You changed a comment, a document, or a changelog line. | No. |
| A maintainer already merged the tree and every gate passed. | No. Never start `workflow_dispatch` on a validated tree. |

### Batch the work

1. Group the related edits into one commit. Ten small pushes cost ten runs.
2. Add `[skip ci]` to the commit subject for a text-only commit that no gate
   reads.
3. Push once, then read the result. Do not push again while a run is in
   flight, unless the new commit replaces the old one on purpose.

### Every workflow carries these four guards

Check each guard before you merge a change to a workflow file.

**Guard 1. One event starts one run.**

A workflow that declares `push` on every branch and also declares
`pull_request` starts two runs for one commit. Scope the push trigger.

```yaml
on:
  push:
    branches: [main]
  pull_request:
```

**Guard 2. A new commit cancels the old run.**

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.head_ref || github.ref }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}
```

Use `github.head_ref || github.ref`. On a pull request event `github.ref` holds
`refs/pull/<n>/merge`, and on a push event it holds `refs/heads/<branch>`. A
group keyed on `github.ref` alone puts the two runs for one commit into
different groups, so neither run cancels the other one.

Keep `cancel-in-progress` false on `main`. A cancelled run on `main` leaves no
record that the tree passed.

**Guard 3. An expensive job carries an event guard.**

An emulated arm64 container build takes about 90 minutes. A nightly job, a
performance job, and a full browser matrix each cost far more than a unit test.
Run the expensive leg on `main`, on a schedule, and on a manual request. Run
the cheap leg on every event.

```yaml
    strategy:
      matrix:
        include: ${{ fromJSON(
          (github.event_name == 'schedule'
            || github.event_name == 'workflow_dispatch'
            || (github.event_name == 'push' && github.ref == 'refs/heads/main'))
          && '[{"name":"amd64"},{"name":"arm64"}]'
          || '[{"name":"amd64"}]') }}
```

**Guard 4. A schedule runs no more often than the work needs.**

A nightly schedule costs 30 runs each month. A weekly schedule costs 4. Choose
the weekly schedule unless the job guards a daily risk.

### Never skip a required check with a path filter

A text-only change starts every gate. That looks wasteful, and `paths-ignore`
looks like the repair. It is not.

Warning: never add `paths-ignore` to a workflow that reports a required check.
The workflow never starts, so the check never reports. Branch protection then
waits for a status that no run will ever send, and the pull request blocks
forever.

Issue #1952 records the matching failure in the other direction. A branch
filter on the `pull_request` trigger let a stacked pull request merge with zero
checks. A reviewer read the empty check list as clean, when it was unmeasured.

Use this pattern instead when the saving is worth the complexity.

1. Add one filter job that always runs and outputs a boolean.
2. Guard each expensive job with an `if:` condition that reads the boolean.
3. Add one aggregator job that always runs and reports the combined result.
4. Make the aggregator the only required check.

The aggregator always reports, so branch protection always clears.

### Watch for a hidden failure

A job that declares `needs:` does not run when the job above it fails. The
lower job then reports `skipped`, and a real failure stays invisible.

Warning: a red gate near the top of the graph hides every gate below it. In one
repository `backend-pytest` reported `skipped` on 12 runs in a row. When the
gate above it turned green, the job ran and reported 14 failures. Those
failures dated from the previous week, and no run showed them.

Read the job table on every failed run. Treat `skipped` as unknown, never as
passed.

```powershell
gh run view <run-id> --json jobs --jq '.jobs[] | "\(.conclusion // .status)  \(.name)"'
```

### Fix a defect. Do not silence a gate

Never delete a gate to make a pull request green. Never add an ignore rule for
a finding that you did not read. Repair the cause, then record the evidence in
the pull request.

## Part 4. Prove the repair

A workflow change is a code change. A reader cannot see its behavior in the
diff. Give the reader a measurement.

| Claim | The measurement that proves it |
| - | - |
| The trigger no longer duplicates. | Count the runs for one commit. The count is 1. |
| The concurrency group works. | Push a second commit. The first run reports `cancelled`. |
| The matrix gate works. | Read the job list. The expensive leg is absent on a pull request. |
| The job passes now. | Name the run, and name the job conclusion. |

Add a contract test for each workflow setting that a future edit could undo. A
contract test reads the workflow file and asserts the setting.

## Part 5. The pull request

1. Link the issue. Write `Closes #<issue>`.
2. Add a type label and a scope label.
3. Complete every checklist item in the template.
4. Wait for every required check, including CodeQL. Use
   `gh pr checks <number> --watch`.
5. Add the `auto-merge` label only after every check reports green.
6. Never add `auto-merge` to a pull request that changes a destructive
   operation. A human reviews that change.

Warning: a pull request from a fork receives a read-only token and no secrets.
The automation in this repository writes labels, writes comments, and pushes a
container image. A fork breaks all three. Work from a branch in this
repository, never from a fork.

## Part 6. The commit and the merge

Write every commit message in the Conventional Commits format.

```text
<type>(<scope>): <description>

Closes #<issue>
```

Use one of these types: `fix`, `feat`, `chore`, `refactor`, `test`, `docs`,
`ci`, `style`, or `perf`.

Obey these merge rules.

1. Squash the merge. One pull request becomes one commit on `main`.
2. Write `Closes #<issue>` in the pull request body. A squash merge reads the
   body, not the commit trail.
3. Rebase onto `main` before the merge if the branch is behind.
4. Delete the branch and the worktree after the merge.
5. Never force-push to `main`. Never force-push to a branch that another agent
   shares.

Warning: never push a commit to a branch after a squash merge closes its pull
request. The squash merge rewrites the history, so the new commit becomes an
orphan and no one merges it. File a new issue, then branch again from `main`.

## Part 7. Escalate to SpecKit

Not every task needs a specification. Use this table to decide.

| Situation | Action |
| - | - |
| One file, and the intent is obvious. | Implement it directly. |
| A lint repair or a format repair with an automatic fix. | Implement it directly. |
| A text-only change. | Implement it directly. |
| A test for behavior that already exists. | Implement it directly. |
| Three or more files, or two or more classes. | Write a specification first. |
| A new menu operation or a new API integration. | Write a specification first. |
| A new class, a module split, or a change to the data flow. | Write a specification first. |
| A defect with an unclear cause, or a cause that spans components. | Write a specification first. |
| A change to a destructive operation. | Write a specification first. |
| Concurrency work or performance work. | Write a specification first. |
| A database schema change or a primary key change. | Write a specification first. |

Run the SpecKit steps in this order: `speckit.specify`, `speckit.clarify`
(optional), `speckit.plan`, `speckit.tasks`, `speckit.implement`, and
`speckit.analyze`.

If you cannot decide, write the specification. An unnecessary specification
costs minutes. A large change without one costs hours.

## Part 8. Turn an error into an issue

Every code change starts with an issue. Create the issue before you create the
branch. If a build, a linter, a test, or the runtime reports an error, file the
issue first. Then repair the defect.

| Trigger | Labels | Title pattern |
| - | - | - |
| A linter violation | `lint` and the rule code | `Lint: <rule> -- <description>` |
| A test failure | `bug`, `test` | `Test failure: <test name>` |
| A type error | `chore`, `types` | `Type error: <file>:<line>` |
| A runtime exception | `bug` | `Runtime: <exception> in <function>` |
| A security finding | `security` | `Security: <tool> -- <finding>` |
| A workflow failure | `ci` | `CI: <workflow> -- <failure>` |

Every issue carries a type label and a scope label. Add the `in-progress` label
when you start the work. One issue states one concern. Never bundle two
unrelated repairs.

Put the complete error output in the issue body. Create the issue with
`gh issue create --title "..." --label "..." --body "..."`.

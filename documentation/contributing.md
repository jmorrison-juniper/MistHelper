# Contributing

## The workflow

1. Open or claim a GitHub issue before you write code. Add the `in-progress`
   label.
2. Create a branch from `main`. Use `feat/<issue>-<slug>`, `fix/<issue>-<slug>`,
   or `chore/<issue>-<slug>`. Never branch from another feature branch.
3. Work in a worktree. Read [the development setup page](development-setup.md).
4. Add or change the tests where the logic changes.
5. Run [the quality gates](quality-gates.md) before every commit.
6. Open a pull request with the template. Write `Closes #<issue>` in the body.
7. Wait for every check, and for CodeQL, before you add the `auto-merge` label.

## Labels

Every issue and every pull request carries two labels at least.

| Kind | Examples |
|------|----------|
| Type | `bug`, `feature`, `chore`, `lint`, `security`, `refactor` |
| Scope | `MistHelper.py`, `tests`, `ci`, `container`, `docs`, `web-portal` |

Add `in-progress` while you work.

## The rules that a review checks

- New code goes in `src/`, and not in `MistHelper.py`.
- A class holds the feature. Do not add a wrapper function around one.
- Every function takes 5 parameters at most, and holds 25 lines at most.
- Every executable line of new code carries a comment that states why.
- Every operation writes a log record before it starts and after it ends.
- A log record holds ASCII characters alone.
- Every path uses `os.path.join` or `pathlib.Path`.
- Every document follows [the writing guide](ASD-STE100_writing-guide.md).

`.github/instructions/coding-standards.instructions.md` holds the full set.

## Hot files

`MistHelper.py` takes one open pull request at a time. Check the open list
before you start, and work on a file that nobody else holds.

```powershell
gh pr list --json files
```

Two branches that both change that file produce a conflict that costs more than
the wait.

## License

CC-BY-NC-SA-4.0, the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International license.

## Attribution

MistHelper is built for operational reliability and clarity in a large
enterprise network and in a network operations center.

The tool calls the Mist API through the `mistapi` library of Thomas Munzer. Read
<https://github.com/tmunzer/mistapi_python> for that library, and
<https://github.com/tmunzer/mist_library> for reference implementations.

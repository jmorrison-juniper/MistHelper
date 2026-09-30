# Contract: Title decisions and CLI

**Issue**: #3550
**Implementation boundary**: `scripts/pr_title_guard`

## Interfaces

| Interface | Result |
| --- | --- |
| `PullRequestTitleGuard.is_valid_title(title)` | Return an exact Boolean. Return false for a non-string value. Read no environment or file. |
| `PullRequestTitleGuard.read_title()` | Return the exact string from the event file. Raise an explicit input error when the source or shape is invalid. |
| `PullRequestTitleGuard.check(title)` | Check an available string, print the contracted stdout, and return exit code zero or one. |
| `PullRequestTitleGuard.main()` | Read and check the event. Handle input errors, report count zero, and return exit code one. |
| `python -m scripts.pr_title_guard` | Call `main` directly from `__main__.py` and use its result as the process exit code. |

Do not add command-line options, bot overrides, wrapper functions, or extra class members.
The class owns one compiled pattern and the four methods above.

## Accepted grammar

Accept these four forms.

```text
type: description
type(scope): description
type!: description
type(scope)!: description
```

- Allow only `fix`, `feat`, `chore`, `refactor`, `test`, `docs`, `ci`, `style`, and `perf`.
- Match the complete title with no leading character or trailing unmatched character.
- If present, require a scope with at least one non-whitespace character and no parentheses.
- Require one optional `!` immediately before the colon.
- Require an ASCII space after the colon and a nonblank description.
- Allow additional spaces within the description, including after the separator.
- Allow Unicode text, quotes, backslashes, and shell punctuation as data.
- Reject U+0000 through U+001F, U+007F through U+009F, U+2028, and U+2029 anywhere.
- Do not trim, rewrite, normalize, truncate, or impose an extra title-length limit.

An empty or whitespace-only title fails with count one.
Contributor, draft, bot, and fork titles use the same rule.

## Event input

`GITHUB_EVENT_PATH` must name a readable UTF-8 JSON file.
The JSON root must be an object.
Its `pull_request` field must be an object with a string `title` field.
Other fields do not affect the decision.
Read the title from the file, never from executable workflow interpolation.

## Exact stdout and exit codes

Use `json.dumps` with `ensure_ascii=True` for every available title.
Send action logs to stderr, not stdout.
End each stdout line with one newline.

A valid example produces these exact lines and exit code zero.

```text
Title: "fix(web-portal): model prompts"
Result: PASS
Checked 1 pull request title
```

An invalid example produces these exact lines and exit code one.

```text
Title: "wip: model prompts"
Result: FAIL - Invalid title grammar or forbidden character.
Use type[(scope)][!]: description.
Allowed types: fix, feat, chore, refactor, test, docs, ci, style, perf.
Use a nonblank scope without parentheses and a nonblank one-line description.
Do not use control characters, Unicode line separators, or Unicode paragraph separators.
Correct the pull request title. A title edit starts another check.
Checked 1 pull request title
```

Replace only the JSON string on the first line for another available title.
A Unicode example uses this exact title line.

```text
Title: "fix(web-portal): \u4fee\u590d\u6a21\u578b\u63d0\u793a"
```

An input failure produces two lines and exit code one.
It produces no title line and does not start a title decision.

```text
Result: FAIL - <fixed input problem>
Checked 0 pull request titles
```

Use these fixed input problems.

| Failure | Fixed input problem |
| --- | --- |
| Missing or empty environment value | `GITHUB_EVENT_PATH is missing or empty.` |
| Missing path, unreadable file, directory, or unusable path | `Cannot read the GITHUB_EVENT_PATH file.` |
| Bad UTF-8 | `The GITHUB_EVENT_PATH file is not valid UTF-8.` |
| Bad JSON | `The GITHUB_EVENT_PATH file is not valid JSON.` |
| Wrong root, missing record, or wrong record type | `The event must be an object with a pull_request object.` |
| Missing title or non-string title | `The pull_request.title field must be a string.` |

Do not print the event payload, raw event path, decoder bytes, or credentials.
Never report a successful skip after an input failure.

## Action log contract

Use stable key/value records with an ASCII level prefix.
Show an `info` before record and a `debug` after record for event reading.
The after record reports `ready` and count one, or `failed` and count zero.
Ensure the reader records the after result on its failure exit paths.

Show an `info` before record and a `debug` after record for the actual title decision.
The after record reports the Boolean decision and checked count one for a string.
For a non-string direct argument, report checked count zero.
An input failure produces no title-decision record.
Use `%s` formatting arguments in logging calls.

On an exception, log its category and complete stack-frame text through ASCII JSON escapes.
Do not send raw exception data through an automatic traceback formatter.
No variable output may insert a newline or a GitHub workflow command line.

## Required offline proofs

Prove all nine types, all four forms, invalid grammar, blank values, and non-string direct decisions.
Prove Unicode, every forbidden character boundary, escaped punctuation, and large valid and invalid values.
Prove exact stdout, JSON reversibility, ASCII output, counts, logging order, and CLI exit codes.
Prove every input failure category with temporary files or a narrow file-capability stand-in.
Do not mock the checker decision.

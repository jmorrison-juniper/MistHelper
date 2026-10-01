# Research: Bounded numeric inputs

## Existing readers

`select.read_whole_number` removes surrounding whitespace and permits one plus sign.
Its current `lstrip("+")` check also permits several plus signs before a failing conversion.
`build_org_view` clamps a valid offset past the available rows to the end of the list.
The largest usable sequence index is `sys.maxsize`.

`capture.tier_number` accepts integers except booleans.
Its text path removes no whitespace and permits no sign.
`read_tier` applies the existing tier membership rule.
`start_capture` applies authentication and site scope before the tier refusal.

`clients.page_limit` removes surrounding whitespace.
It uses `DEFAULT_PAGE_LIMIT` for invalid text and clamps valid numbers to the named bounds.
Zero therefore means `MIN_PAGE_LIMIT`, not the default.
An excessive positive number and the named fallback both mean `MAX_PAGE_LIMIT`, which is 1000.

## Shared reader decision

**Decision**: Add `AsciiWholeNumberReader` to the existing API package.
The immutable reader owns the caller's number bound and diagnostic field name.

**Rationale**: Searches found no reusable reader with both ASCII validation and a pre-conversion text bound.
The existing environment, history, report, and organization readers accept different input types or convert first.
Their ownership and behavior remain outside this issue.

**Alternatives considered**: Do not copy three separate validators.
Do not reuse the option mapper, which another open pull request owns.
Do not normalize Unicode digits or catch all failures.

## Length and number bounds

**Decision**: Check raw digit length against the Python backend representation limit before removing leading zeros.
Use the default backend limit if the active limit is disabled or larger.
Use a stricter active limit when present.

**Rationale**: This preserves existing ordinary leading zeros and prevents conversion of 5000 zeros.
The bound comes from Python, not a new application constant.
Removing zeros first would turn excessive input into a successful reading.

**Decision**: Compare significant decimal digits against the caller's number bound before conversion.

**Rationale**: The offset uses `sys.maxsize`, the tier uses its largest known tier,
and the page limit uses `MAX_PAGE_LIMIT`.
Equal digit lengths require a decimal text comparison.
The conversion therefore receives only a small, usable ASCII number.

## Local isolation

Use real Flask routes with in-memory sessions and injected offline read surfaces.
Replace the capture launch boundary with a recording callback.
Install no firmware callback and start no worker.
Keep existing authentication, CSRF, and site scope tests in the related regression run.

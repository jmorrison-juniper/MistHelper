# Data model

No output schema changes occur.
Each page retains its SDK status, data, and next link.
Accepted statuses are integer HTTP 2xx values.
Accepted rows are dictionaries in a list, either directly or in the `results` field.
`None` and the exact empty string mark a terminal cursor.
Other cursors must be nonblank strings not previously requested during the read.
The aggregate remains private to the request phase until every page succeeds.
Failure returns no aggregate, not a partial list or an empty success.
A search page can carry a JSON `total`. It is a nonnegative integer count of matching rows across all pages.
At a terminal cursor, the collected rows must equal or exceed the latest JSON `total`.
Present `X-Page-*` headers must hold three nonnegative integers. Absent metadata adds no count requirement.
A later page without a JSON `total` keeps the most recent present total.
A header name that exists with an empty value is present metadata and fails validation.
Each count has 1 to 18 ASCII digits, so integer conversion cannot fail.
A cursor starts with `/api/v1/` and has no whitespace or control character, so the request stays on the cloud host.

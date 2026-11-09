# Data model

No output schema changes occur.
Each page retains its SDK status, data, and next link.
Accepted statuses are integer HTTP 2xx values.
Accepted rows are dictionaries in a list, either directly or in the `results` field.
`None` and the exact empty string mark a terminal cursor.
Other cursors must be nonblank strings not previously requested during the read.
The aggregate remains private to the request phase until every page succeeds.
Failure returns no aggregate, not a partial list or an empty success.

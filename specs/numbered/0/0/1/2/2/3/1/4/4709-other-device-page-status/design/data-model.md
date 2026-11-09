# Data model

No output schema changes occur.
Each page retains its SDK status, data, and next link.
Accepted statuses are integer HTTP 2xx values.
Accepted rows are a list, either directly or in the `results` field.
The aggregate remains private to the request phase until every page succeeds.
Failure returns no aggregate, not a partial list or an empty success.

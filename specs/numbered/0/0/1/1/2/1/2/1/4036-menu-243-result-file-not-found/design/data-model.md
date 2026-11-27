# Data Model: Menu 243 Result File Not Found

## Output file

An output file is a file that a run lists in the Results panel.

| Field | Meaning | Rule |
| --- | --- | --- |
| Relative path | The path from the data directory, with forward slashes | This value is the natural key. Example: `mib_generator/oid_assignments.json`. |
| Extension | The lowercase suffix of the file name | Browsable extensions are `.csv`, `.db`, `.sqlite`, `.log`, and `.json` [RC-21]. |
| Exists | True when the file is present now | A name whose file is absent is removed from the list [RC-26]. |
| Real path | The path after link resolution | The real path must stay inside the real data root [RC-23]. |

## Preview request

A preview request selects one file or one SQLite table.

| Field | Meaning | Rule |
| --- | --- | --- |
| Selection kind | File or table | A table selection needs a database directory with a `.db` or `.sqlite` suffix [RC-18]. |
| Relative path | The complete file path, or the database path for a table | A nested file keeps every directory segment. |
| Table name | The selected table | Present only for a table selection. |
| Page | The requested page | Starts at 1. The service clamps lower values to 1. |
| Per page | The requested page size | The service clamps the size to its bounds. |
| Search | Filter text | Optional. Empty means no filter. |
| Sort column and direction | Requested order | Optional. The route ignores a column that the file does not have. |

## Preview response

| Field | Meaning | Rule |
| --- | --- | --- |
| Columns | Column names | Present on success. |
| Rows | Rows of the requested page | Present on success. |
| Total rows and total pages | Totals for the filtered result | Present on success. The panel reads them [RC-28]. |
| Page | The page that the response answers | Present on success. |
| Error | Failure text | Present on failure. The status is 404 when the text contains `not found`, otherwise 400. |

## Run record

| Field | Meaning | Rule |
| --- | --- | --- |
| Run identifier | The run key | Unique for each run. |
| Menu number | The operation number | For this change, 243. |
| Status | The run state | The browser test waits for `completed` or `failed`. |
| Output file paths | The ordered list of output file names | Finalization keeps existing names and places cache files after results [RC-26]. |

## State transitions

- Output file: listed, then previewable when the file exists and the extension is `.csv` or `.json`, then previewed with HTTP 200.
- Output file: listed, then previewed with a refused or missing path, which returns HTTP 404 and the text `File not found`.
- Output file: listed, then removed. The next preview returns HTTP 404 and no stale rows. This case follows FR-004.
- Output file: listed, then read with a malformed JSON body. The preview returns HTTP 400 with the parser reason. This case follows FR-006.

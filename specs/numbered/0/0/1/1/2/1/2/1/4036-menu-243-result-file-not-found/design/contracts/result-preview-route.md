# Contract: Result Preview and Download Routes

This contract describes the portal routes that the Results panel calls. The change keeps this behavior. It adds no route and changes no response shape.

## Endpoints

| Method | Path | Purpose | Source |
| --- | --- | --- | --- |
| GET | `/api/data/preview/<path:filepath>` | Rows of one CSV or JSON output file. Also the table list of a SQLite file. | `web_portal/routes/data.py` line 45 [RC-14] |
| GET | `/api/data/preview/<path:filepath>` with a table segment | Rows of one SQLite table when the directory part ends in `.db` or `.sqlite` | Same route, line 45. The helper is `preview_table` at line 94 [RC-19]. |
| GET | `/api/data/download/<path:filepath>` | The unchanged file as an attachment | `web_portal/routes/data.py` line 110 [RC-20] |

## Preview query parameters

- `page`: integer. The default is 1. Values below 1 become 1.
- `per_page`: integer. The default is 50. The service clamps the value to its bounds.
- `search`: text. The default is empty, which means no filter.
- `sort_column`: integer column index. Optional. The route ignores an index that the file does not have.
- `sort_dir`: `asc` or `desc`. The default is `asc`.

## Preview success response

HTTP 200 with a JSON object. The object holds `columns`, `rows`, `total_rows`, `total_pages`, and `page`. The Results panel reads these keys [RC-28, RC-30].

## Preview error response

HTTP status and a JSON object with an `error` text.

- The status is 404 when the text contains `not found`, in any letter case.
- The status is 400 for any other error.
- A refused or missing path returns `{"error": "File not found"}` with HTTP 404.
- A malformed JSON body returns the parser reason. For example, `Failed to read JSON: Expecting value (line 1, column 1)` with HTTP 400.
- A generic read failure returns `Failed to read JSON: Cannot read the selected result file.` with HTTP 400. The server log keeps the exception details [RC-24, RC-25].

## Download response

- HTTP 200 with the file as an attachment. The bytes match the source file.
- A refused or missing path returns `{"error": "File not found"}` with HTTP 404 [RC-22].

## Path rules

The resolver returns no file when any of these conditions holds [RC-23]:

- The real path leaves the real data root.
- The path names a directory.
- The extension is not one of `.csv`, `.db`, `.sqlite`, `.log`, or `.json` [RC-21].
- The path enters the private firmware settings backup directory.

Every refusal returns the same `File not found` text as a missing file. This shared text is the existing nondisclosing rule. A test asserts it for denied paths [RC-49].

## Unchanged behavior

- Table previews keep their response shape, pagination, and missing-table text.
- Downloads keep the source bytes.
- One route handles files and table paths. The change does not add a second route for either.

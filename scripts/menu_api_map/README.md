# Menu API endpoint map tool

This tool writes the menu API endpoint map. The map shows the Mist API
endpoints that each MistHelper menu option can call. Issue #3411 added the
tool.

Read [the map](../../documentation/menu-api/README.md) for the result.

## Commands

Run each command from the repository root.

| Command | Result |
| - | - |
| `python -m scripts.menu_api_map` | Writes the map pages again. |
| `python -m scripts.menu_api_map --check` | Compares the pages with the source and writes nothing. |
| `python -m scripts.menu_api_map --explain 11` | Prints the call path of each endpoint of menu 11. |
| `python -m scripts.menu_api_map --refresh-sdk-index` | Reads the installed mistapi source and writes `reference/sdk_index.json` again. |
| `python -m scripts.menu_api_map --verbose` | Prints the debug log records. |

If a page is stale, missing, or not expected, `--check` names the page and
exits with code 1. The `menu_reference_drift` CI job runs `--check`.

The tool uses the Python standard library only. It reads the source files as
text, and it does not import MistHelper. It needs no Mist token and no network.

## Output

The tool writes 16 pages.

- `documentation/menu-api/README.md` and one page for each menu category.
- `documentation/wiki/Menu-API-Endpoints.md` and one wiki page for each menu
  category.

Do not edit a page by hand. The next run of the tool replaces the change.

## How the walk works

1. The tool reads the menu table in `MistHelper.py`.
2. The tool reads the category of each menu option from
   `src/utils/operation_registry.py`.
3. The tool starts at the handler of each menu option. It follows each call
   that it can resolve.
4. The tool records each call to a mistapi function and each raw request
   through the Mist session.
5. The tool stops at a shared helper class. The helper gets its own section,
   and the menu section links to that section.
6. The tool reads `reference/sdk_index.json` to find the HTTP method, the path, and
   the document link of each SDK function.

The "Found by" column of each table tells how the tool found the endpoint. The
map index explains each value.

## Data files

| File | Content |
| - | - |
| `reference/sdk_index.json` | Each mistapi function, with its method, its path, and its document link. The file names the mistapi version. |
| `reference/curated.json` | The shared helper classes, the generic names, the dynamic calls, and the reason for each menu option that sends no request. |

A unit test proves that each curated rule names code that exists. If you
rename a class or a function that a rule names, change the rule in the same
pull request.

## Change the mistapi version

The unit test `test_vendored_sdk_index_matches_the_installed_mistapi` compares
the index with the installed mistapi release.

- If the two releases are the same, every row must match.
- If only the patch number differs, the test skips and prints the repair.
- If the major number or the minor number differs, the test fails.

If you change the mistapi requirement range, do these steps in the same pull
request.

1. Install the new mistapi release.
2. Run `python -m scripts.menu_api_map --refresh-sdk-index`.
3. Run `python -m scripts.menu_api_map`.
4. Commit the index and the changed pages.

## Limits

- The walk finds a call only when it can resolve the receiver of the call.
- A call that builds the function name at run time needs a curated rule.
- A menu diagram shows 12 endpoint nodes at most. The table below the diagram
  lists every endpoint.

# Research: issue #3411

## Decision 1: Use static analysis, not a live trace

**Decision**: Read the source with the `ast` module.

**Reason**: A live trace needs a Mist organization, credentials, and an
operator at each prompt. It also calls destructive endpoints. Static analysis
reads files only, and it runs in CI in seconds.

**Cost**: The map can hold a call that runs only under one condition. It can
miss a call that the code builds at run time. Each page states both limits.

## Decision 2: Vendor an SDK index

**Decision**: Store `sdk_index.json` in the repository, and build it from the
installed `mistapi` package with a refresh command.

**Reason**: The CI drift job installs no requirements. The index is about one
thousand rows, and it records the SDK version.

**Rejected**: The bundled OpenAPI file. Its operation names do not always
match the SDK function names, and issue #3338 tracks its refresh.

## Decision 3: Cut the walk at shared helper classes

**Decision**: The walker records a shared helper and does not enter it.

**Reason**: Prototype 1 entered every helper. `getSelfApiUsage` then appeared
in 159 menu options through the rate limiter, and the map lost its value. With
the cut, the median walk visits 30 functions, and the index page lists the
endpoints of each helper one time.

## Decision 4: Follow a forward by method name

**Decision**: If a class defines `__getattr__`, the resolver looks for a unique
method of the requested name, first in the package of the class.

**Reason**: Many managers forward members to cluster classes. Without this
rule, menu 145 and menu 179 showed no endpoint.

## Measurements of the prototype

| Version | Menu options with no endpoint | Median visits |
| - | - | - |
| Prototype 1 | 52 | Not measured |
| Prototype 2, no helper cut | 7 | 1,000 or more |
| Prototype 2, helper cut | 8 | 25 |
| Prototype 2, forwards and string dispatch | 6 | 30 |
| Prototype 2, scoped imports and helper roots | 5 | 30 |

The five options with no endpoint are 0 (exit), 141 (the TUI, which starts
other menu options), 175 (the SSH runner), 186 (the cache delete), and 243
(the MIB generator, which reads a local file).

A check by hand of menu options 1, 11, 60, 102, 120, 135, 153, 154, 166, and
195 found each listed endpoint in the handler code.

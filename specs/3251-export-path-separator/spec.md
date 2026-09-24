# Specification: the export notices name the data folder with the platform separator

- Issue: #3251
- Branch: `fix/3251-export-path-separator`
- Scope: the operator notices of menu 69 and menu 73

## Problem

Two export modules build the operator notice with a hardcoded Windows
separator:

| Module | Menu | Notice |
| - | - | - |
| `src/export/site_config_exporter.py` | 69, the WLAN export of a site | `! 0 records exported to data\%s` and `! %s records exported to data\%s` |
| `src/export/site_export_utils.py` | 73, the SLE metric insight export of a site | `! %s records exported to data\%s` and `! 0 records exported to data\%s (no metrics available)` |

The container runs Linux. The Execution Log of menu 69 therefore reads
`! 0 records exported to data\SiteWlans_AlamoSanAntonio.csv`. No file with a
backslash in its name exists. The defect is in the message only.

The repository rule forbids a hardcoded separator. Use `os.path.join()` or
`pathlib.Path()`.

## Measurements

A search of the whole repository for the text `data\\` found these four lines
and no other line. No test reads the backslash form.

The output file parser of the operations portal,
`_RunLogHandler._OUTPUT_FILE_RE` in `web_portal/services/operation.py`, accepts
`data\`, `data/`, and a bare file name. The repair therefore does not change
the output file list.

## Functional requirements

- FR-001: The WLAN notice of menu 69 names the file as
  `os.path.join("data", <file>)`, with the separator of the platform that runs
  the export.
- FR-002: The SLE metric insight notices of menu 73 name the file with the
  existing helper `_resolve_site_display_path()`, which uses the separator of
  the platform.
- FR-003: The words of each notice stay the same. On Windows, each notice stays
  the same byte for byte.
- FR-004: The file name, the write call, and the endpoint name of each export
  stay the same.
- FR-005: Each write that a changed block starts gets an info line before the
  write. The empty write of menu 73 gets a debug line after it.

## Success criteria

- SC-001: A unit test that simulates the Linux container finds `data/<file>`
  in each of the four notices, and no backslash.
- SC-002: A unit test that simulates Windows finds `data\<file>` in each of
  the four notices.
- SC-003: The existing tests of both modules stay green.

## Out of scope

- The notice wording of the other exporters. They name the file only, and
  they use no separator.
- The output folder itself. `DataExporter` owns the folder and the write.
- The HTTP status check of menu 73. If the cloud refuses the SLE metrics
  request, menu 73 prints "no metrics available". Issue #3305 owns that repair.

## Assumptions

- Each file name that reaches these notices is a bare name without a folder.
  `_resolve_site_display_path()` keeps a name that already holds a folder, so
  the assumption carries no risk for menu 73.

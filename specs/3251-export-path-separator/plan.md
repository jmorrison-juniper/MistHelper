# Plan: the export notices name the data folder with the platform separator

## Technical context

- Python 3.13, standard library only.
- Files to change: `src/export/site_config_exporter.py` and
  `src/export/site_export_utils.py`.
- New test module: `tests/unit/export/test_export_notice_separator.py`.
- No new dependency, no menu change, no container, and no workflow change.

## Design

1. `site_config_exporter.py` imports `os` and adds the constant
   `_DATA_SUBDIR = "data"`. `_persist_site_wlans_csv()` builds the display path
   one time with `os.path.join(_DATA_SUBDIR, filename)`, and both notices use
   it.
2. `site_export_utils.py` `_write_insight_rows()` builds the display path one
   time with the existing helper `_resolve_site_display_path()`, and both
   notices use it. Line 331 of the same module already uses that helper.
3. Each changed block gets an info line before its write. The empty write of
   menu 73 gets a debug line after it. The words of each existing notice stay
   the same.

## Test plan

The tests simulate a platform. Each test replaces the `os` name of the module
under test with a small namespace that holds `posixpath` or `ntpath`. The
global `os` module stays the same, so pytest and the logging framework see no
change.

The Windows case passes on the old code on purpose. It proves that the Windows
notice stays the same byte for byte.

| Requirement | Test |
| - | - |
| FR-001 | `test_the_wlan_notice_uses_the_platform_separator` (4 cases: empty and not empty, Linux and Windows) |
| FR-002 | `test_the_insight_notice_uses_the_platform_separator` (4 cases: empty and not empty, Linux and Windows) |
| FR-003 | The Windows cases of both tests |
| FR-004 | `test_the_wlan_write_keeps_the_file_name_and_the_endpoint` and `test_the_insight_write_keeps_the_file_name_and_the_endpoint` |
| FR-005 | `test_the_wlan_export_logs_before_the_write` and `test_the_insight_export_logs_before_the_write` |
| SC-003 | `tests/unit/export/test_site_config_exporter.py` and `tests/unit/export/test_site_export_utils_extended.py` |
| Issue #3305, out of scope | `test_a_refused_insight_request_names_the_http_status` (2 strict `xfail` cases: HTTP 404 and HTTP 503) |

The test-quality ratchet asks for an HTTP 4xx test and an HTTP 5xx test,
because `site_export_utils.py` reads HTTP status codes. The two strict `xfail`
cases state the correct behavior for a cloud refusal. The repair for #3305
removes the two markers.

## Risk

The operations portal reads each notice for output file names. Its pattern
accepts both separators, so the output file list stays the same. The new info
lines hold no file name, so the pattern does not read them.

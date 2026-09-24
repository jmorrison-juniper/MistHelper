# Plan: the bootstrap browser download trusts the system certificate store

## Technical context

- Python 3.13, standard library only.
- File to change: `scripts/bootstrap_worktree.py`.
- New test module: `tests/unit/scripts/test_browser_download_certificates.py`.
- Document to change: `documentation/development-setup.md`.
- No new dependency, no container, and no workflow change.

## Design

1. Add the constant `NODE_SYSTEM_CA_OPTION = "--use-system-ca"`. A comment
   states why the option exists and names issue #3302.
2. Add `WorktreeBootstrapper._browser_environment()`. It starts from
   `_install_environment()`, so the caller variables and the pip settings stay
   the same. It appends the option to the caller value of `NODE_OPTIONS`. It
   does not rebuild the caller value, so a quoted path in that value stays the
   same.
3. `install_browser_driver()` passes `_browser_environment()` to the download
   subprocess. The pip subprocess keeps `_install_environment()`.
4. Add the static method `WorktreeBootstrapper.browser_repair_command(platform)`.
   It returns a PowerShell command for `win32` and a POSIX shell command for
   each other platform. Both commands hold `PLAYWRIGHT_INSTALL_HINT`, so the
   existing tests that read the hint stay green.
5. The failure warning and `report_result()` print the repair command.
6. The setup document shows the repair command for each shell, and it names
   the error text that the proxy causes.

## Test plan

The new tests use the literal option text. The option is the interface that
Node reads, and a literal keeps the red proof precise, because the old module
holds no new name to import.

| Requirement | Test |
| - | - |
| FR-001 | `test_the_browser_download_trusts_the_system_certificate_store` |
| FR-002 | `test_the_browser_download_keeps_each_caller_node_option` and `test_an_empty_caller_node_option_gives_the_option_alone` |
| FR-003 | `test_the_browser_download_adds_the_option_one_time` |
| FR-004 | `test_the_pip_install_gets_no_node_option` and `test_the_browser_download_keeps_the_caller_proxy` |
| FR-005 | `test_a_failed_download_prints_the_repair_command_with_the_option`, `test_the_report_prints_the_repair_command_with_the_option`, and `test_a_report_with_no_installed_file_still_prints_the_repair_command` |
| FR-006 | `test_the_repair_command_for_powershell` and `test_the_repair_command_for_a_posix_shell` |
| FR-007 | The existing tests in `tests/unit/scripts/test_browser_driver_bootstrap.py` |

## Risk

A Node runtime older than 22.15 refuses an unknown option in `NODE_OPTIONS`.
The pin in `requirements-dev.txt` holds Playwright 1.63.0, which bundles Node
24.21.0, so the bootstrap never starts an older runtime.

# Tasks: the bootstrap browser download trusts the system certificate store

- [x] Record the failure, the cause, and the measurements in issue #3302.
- [x] Write the behavior tests in `tests/unit/scripts/test_browser_download_certificates.py`.
- [x] Record the red proof on the old code.
- [x] Add `NODE_SYSTEM_CA_OPTION` and `_browser_environment()`, and pass that environment to the download.
- [x] Add `browser_repair_command()`, and print it in the warning and in the report.
- [x] Update the repair section of `documentation/development-setup.md`.
- [x] Add no release-note fragment. The bootstrap is internal, and the repairs for #1866, #2000, and #2241 added none.
- [x] Run the tests and the quality gates.
- [x] Commit, push, open the pull request, and comment on the issue.

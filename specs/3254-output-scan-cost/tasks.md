# Tasks: Reduce Operations Portal Output Scan Cost

1. Measure the current scanner in the shared container.
2. Add a guard test for an in-place rewrite in a large nested output folder.
3. Prove the guard fails against the current scanner.
4. Implement the write tracker and directory-mark fallback in `output_scan.py`.
5. Add the full-walk fallback for runs with no fast-path result.
6. Add tests for `os.utime`, `os.open`, and `os.replace` rewrites.
7. Run the focused output scan tests.
8. Run syntax, lint, format, and the test quality analyzer.
9. Measure the updated scanner in the container with the probe.
10. Open a pull request without the `auto-merge` label.

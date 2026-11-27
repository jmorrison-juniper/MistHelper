# Implementation Plan: Batch Parent Terminal Requests

**Branch**: `fix/4782-batch-parent-terminal-requests` | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/1/2/3/1/1/2/4782-batch-parent-terminal-requests/spec.md`

**Input**: Feature specification in this record (`spec.md`). The route `0/0/1/2/3/1/1/2` uses base-5 digits, as Principle I requires.

## Summary

The defect in issue #4782 is fixed on `main`. Commit `4e81b2a4a7` added the guard in `isTerminalSession` (`websockets.js` line 1894, R-17). This plan adds regression coverage for both routes in the existing e2e module. It changes no production file.

## Technical Context

- **Language/Version**: Python 3.15 for the test module. Browser JavaScript in `websockets.js` stays unchanged.
- **Primary Dependencies**: pytest and Playwright for Python. The `websocket_portal` fixture serves the portal in-process with Werkzeug (R-44).
- **Storage**: None.
- **Testing**: pytest under `tests/e2e/websockets_tab/` with `UPGRADE_PORTAL_E2E_STRICT=1` (quality-gates line 68, R-08).
- **Target Platform**: Windows 11, macOS, and Linux.
- **Project Type**: Single project. The portal package is `src/mist/realtime/websocket_streams/web/`.
- **Performance Goals**: No change. The new wait is 1500 milliseconds, as in the existing test.
- **Constraints**: No production change. No Mist REST call. No owned WebSocket transport. ASCII output only.
- **Scale/Scope**: One helper and two test functions in one file.

## Constitution Check

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass | The record folder holds five children. The `design` folder holds five children. The route level `specs/numbered/0/0/1/2/3/1` gains child `1` and holds four children (R-67). |
| II. Class-Based Architecture | Pass | The change adds one helper that registers a listener. The helper wraps no class method. Names use full words. |
| III. Safety-First | Pass | The change adds no input, prompt, or destructive operation. The test uses no secret. |
| IV. Full Deployment Pipeline | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover each step. Execution is pending. |
| V. Observability and Logging | Pass | The change adds no log statement. The added text is ASCII. |
| VI. Inline Comments | Pass | Each new executable line carries an inline comment. The snippet below shows the pattern. |
| VII. Action Logging | Pass | Not applicable. The change adds no production action. |
| Python 3.15 or newer | Pass | The change uses standard syntax. |
| mistapi as sole Mist interface | Pass | Not applicable. The change makes no Mist REST call. The OpenAPI grep found no portal route (R-10). |
| Temporary Owned WebSocket Transport | Pass | Not applicable. The change adds no transport. The policy guard `test_websocket_transport_constitution.py` stays unchanged (R-13). |
| Test containers and container runtime | Pass | Not applicable. No container starts. |
| File paths | Pass | The change adds no path join. |
| Output backends and data directory | Pass | Not applicable. The change writes no product output. |
| Database keys and operational store | Pass | Not applicable. The change touches no store. |
| Container security and Zscaler | Pass | Not applicable. The change builds and pushes no image. |
| Documentation | Pass | Not applicable. The change alters no operator behavior (D-6). |
| Release notes | Pass | The constitution requires a fragment (R-65). The README exempts an internal-only change (R-66). D-6 states the reason in the pull request body. |
| Web UI tests under `tests/e2e/` | Pass | The change edits a test under `tests/e2e/websockets_tab/`. |
| Stable `data-testid` for new elements | Pass | Not applicable. The change adds no interactive element. |
| Multi-Agent file overlap | Pass | None of the seven open pull requests lists the test module or `websockets.js` (R-62, R-63). |
| Ownership hold on held files | Fail until T001 | The retained #4773 work holds `test_websockets_page.py` (issue #4782, owner comment). The edit waits for an explicit release. |
| MistHelper.py as hot file | Pass | `MistHelper.py` is not changed. |
| Security findings | Pass | Not applicable. The change adds no dependency and no production code. |

## Architecture

The flow below shows the selection path and the guard. Line numbers come from R-17 through R-24.

```text
selectSession(session)                            websockets.js line 1854
  restore path calls selectSession                line 1851
  mode multi_site: batch branch                   line 1857
  stopTerminalController before selection         line 1855
  isTerminalSession(session)                      line 1884
    true:  showTerminalSession                    line 1885
           TerminalController constructed         line 1928
           reader.js reads the terminal route     line 88
           transport.js posts the resize route    line 20
    false: showMessageSession, startPollTimer     line 1890
isTerminalSession(session)                        definition follows selectSession
  mode multi_site: return false (guard)           line 1894
```

## File-by-File Change Map

| Path | Action | Purpose |
| - | - | - |
| `tests/e2e/websockets_tab/test_websockets_page.py` | Modify | Add helper `session_route_requests`. Extend `test_a_batch_parent_of_a_shell_action_is_not_opened_as_a_terminal` (line 1562). Add `test_a_batch_parent_restored_after_reload_sends_no_terminal_or_resize_request`. |
| `specs/numbered/0/0/1/2/3/1/1/2/4782-batch-parent-terminal-requests/` | Add | This record. |
| `src/mist/realtime/websocket_streams/web/static/websockets.js` | No change | The guard exists at line 1894 (R-17). |
| `src/mist/realtime/websocket_streams/web/static/terminal/` | No change | Route strings occur only at lines 88 and 20 (R-25, R-26, R-29). |
| `src/mist/realtime/websocket_streams/live/terminal/gateway.py` | No change | The server contract stays (D-7). |
| `changelog.d/` | No change | No fragment. The reason goes in the pull request body (D-6). |
| `documentation/` | No change | No operator-visible behavior changes. |
| Retained branch `refs/heads/feat/4769-ex-hardware-inventory` | No change | D-4. |

## Test Design

The helper registers one `request` listener before the first navigation. It keeps only the URLs that contain the session route prefix. The helper belongs after `open_page` (line 753, R-45).

```python
def session_route_requests(page: Any) -> list[str]:
    """Record each browser request URL that targets a session route."""
    urls: list[str] = []  # Hold the URLs until the test asserts them.

    def record(request: Any) -> None:  # Keep the URL of each session route request.
        """Store one request URL when it targets a session route."""
        if "/api/websockets/sessions/" in request.url:  # Ignore page assets and other routes.
            urls.append(request.url)  # Keep the URL for the final assertion.

    page.on("request", record)  # Observe each request from the start of the journey.
    return urls  # Return the live list that the listener fills.
```

Changes to the existing batch parent test (R-48, R-49):

- Call `session_route_requests(page)` before `open_page`.
- Keep the existing `fake_services.terminal_reads == []` assertion.
- Add this assertion after it: `assert [url for url in route_urls if "/resize" in url or "/terminal" in url] == []`.

New reload test (R-47 shows the reload pattern):

- Register the helper, open the page, and start a hardware batch with `start_hardware_batch` (R-46).
- Reload with `page.reload(wait_until="networkidle")`. Open the Multi Site tab with `ws-multi-site-tab`.
- Wait for the batch progress panel, then wait 1500 milliseconds.
- Assert zero terminal reads and zero matching request URLs.

Each new executable line gets an inline comment. The reload test must fail on `main` with the guard removed. T005 proves it.

## Local Gate Applicability

| Gate | Applies | Command | Reason |
| - | - | - | - |
| Compile | No | `python -m py_compile MistHelper.py` | `MistHelper.py` is unchanged. |
| Lint | Yes | `python -m ruff check .` | The test module changes. |
| Format | Yes | `python -m black --check .` | The test module changes. |
| Types | No | `mypy` with `MYPY_PATHS` | `MYPY_PATHS` omits tests (R-68). |
| Tests | Yes | `python -m pytest tests/e2e/websockets_tab/test_websockets_page.py` with `UPGRADE_PORTAL_E2E_STRICT=1` | The changed file (quality-gates line 68, R-08). |
| Full tests | No | `pytest-chunks` | Only one e2e file changes. CI runs the full shard. |
| Safe sweep | No | `python MistHelper.py --test` | No menu or CLI behavior changes. |
| Coverage | No | `pytest --cov=src` | No `src` change. |
| Test quality | Yes | `test-quality-analyzer --gate` | The test module changes. |
| Complexity | No | `radon cc` | No `src` change. |
| Security lint | No | `bandit` on the package | No production change. |
| Dependency audit | No | `pip-audit -r requirements.txt` | No dependency change. |
| Code quality | No | `pylint src/` | No `src` change. |
| Dead code | No | `vulture` | `VULTURE_PATHS` omits tests (R-68). |
| Docstrings | No | `pydocstyle` and `interrogate` | Their path variables omit tests (R-68). |
| Menu reference | No | `generate_menu_wiki.py` | No menu change. |
| Symbols | Yes | `symbol-diff --base origin/main tests/e2e/websockets_tab/test_websockets_page.py` | The changed file. The gate checks removed or changed module names. |
| STE | Yes | `ste-linter` on changed Markdown in the record | AGENTS.md section Documentation requires each Markdown file to pass. |
| Ops portal and ops platform | No | npm and `mist-ops-platform` pytest | No change in those folders. |
| Guardrails | Yes | `python -m pytest tests/guardrails` | The record adds folders under `specs/numbered`. |
| Citations | Yes | `check-citations src tests` | The test module changes. |

## Dependencies

- Installed by the bootstrap: pytest, Playwright, and Chromium (R-09).
- No dependency change. The `pip-audit` gate does not apply.

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| The ownership hold is not released | The test edit stays blocked | T001 checks the release first. If the owner declines, close #4782 as fixed by PR #4924 and record the resize coverage gap (D-9). |
| A timing race in the new tests | A false failure in CI | Use the existing 1500 millisecond wait and explicit waits for visible panels. |
| A later change removes the guard | A regression returns | FR-005 tests fail on that change. |
| The retained #4773 work merges later | A revert of the guard | D-4 and the Caution in research. |
| The messages route for a batch parent misbehaves live | The page shows errors that the fake tests miss | U-2 remains open. D-8 covers the optional live smoke. |
| The websockets-tab shard runs longer | CI takes about two seconds more | Accept the cost (D-3). |

## Rollback Steps

1. Revert the squash commit on `main` with `git revert <squash-sha>` in a new worktree.
2. Open a pull request titled `revert(web-portal): remove batch parent terminal request checks`.
3. Confirm the revert touches only the test module and the record.

The rollback removes coverage only. It changes no runtime behavior, because no production file changes.

## Complexity Tracking

No violation needs justification. The ownership hold is a precondition (T001), not a violation.

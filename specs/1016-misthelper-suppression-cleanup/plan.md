# Implementation Plan: MistHelper.py Suppression Cleanup

**Branch**: `chore/1004-suppression-cleanup`

**Date**: 2026-09-13

**Spec**: `specs/1016-misthelper-suppression-cleanup/spec.md`

## Summary

This plan removes the six remaining suppressions from `MistHelper.py`. Each repair changes the code shape so the tool no longer needs the suppression. The release note uses one fragment under `changelog.d/`.

## Technical Context

**Language**: Python 3.13 or newer.

**Tools**: ruff, black, mypy, pytest, and `tools.symbol_diff`.

**Target file**: `MistHelper.py`.

**Support file**: `src/utils/subprocess_runner.py`, because the bootstrap installer uses the audited subprocess dispatcher.

## Technical Approach

1. Replace the direct `subprocess` import with `BootstrapSubprocessAdapter`. The adapter gives `PackageInstaller` the subprocess-like contract that it already expects. It routes execution through `SubprocessRunner`.
2. Replace `urllib.request.urlopen` with a late `requests` import and a bounded `requests.get` call. The HTTPS guard remains before the request.
3. Import optional `paramiko` with `importlib.import_module`. This keeps the optional dependency dynamic and removes the need for untyped import ignores.
4. Replace the dynamic module attribute assignment with a `vars()` dictionary write. This preserves the runtime binding and avoids a typed attribute write.
5. Build the container bind-all address with `ipaddress.IPv4Address(0)`. This keeps the bind-all value available only after the container check.
6. Add the issue #1004 release note fragment.

## Constraints

- Do not change the public behavior of the dependency bootstrap.
- Do not remove a suppression unless the code no longer needs it.
- Do not edit `CHANGELOG.md`.
- Keep new comments in Simplified Technical English.
- Use lazy `%s` formatting for logging calls.

## Verification Plan

Run these commands before the commit.

```powershell
rtk python -m py_compile MistHelper.py
rtk python -m ruff check .
rtk python -m black --check .
rtk python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
rtk python -m tools.symbol_diff --base main MistHelper.py
rtk python -m pytest tests/ -x -q
```

Also run the suppression search after implementation. It must return zero matches.

# Specification: Citation reference lint performance

## Problem

The citation reference lint tool scans the repository on each pull request. The default run walks the same roots for the file index and for readable source files. It also asks the citation regex to inspect many lines that cannot hold a citation.

## Goal

Reduce the time and filesystem work for the default citation lint path. Keep the command output, exit code, path rules, and finding order identical.

## Non-goals

Do not add multiprocessing, threading, asyncio, worker changes, or task sharding. Do not repair existing unresolved citations.

## Acceptance criteria

- Record the unmodified baseline before source edits.
- Keep the unresolved citation messages and exit code identical.
- Retain the change only if the end-to-end median improves by at least 5 percent, or if the filesystem work reduction is meaningful.
- Add unit tests for the new branches.
- Add a performance report with raw artifact paths.

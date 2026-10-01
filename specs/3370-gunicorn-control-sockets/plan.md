# Implementation Plan: Distinct Gunicorn control sockets

**Branch**: `jmorrison-juniper-gunicorn-control-sockets`

**Date**: 2026-10-01

**Spec**: [spec.md](spec.md)

## Summary

Add one explicit control socket argument to each existing Gunicorn command.
Preserve all other container startup behavior.
Use one dedicated contract module and one process support module.

## Technical Context

**Language/Version**: Bash and Python 3.13.

**Primary Dependencies**: The current requirements install Gunicorn 26.2.0 and pytest 9.1.1.

**Storage**: Temporary applications, socket directories, and local test logs only.

**Testing**: Parsed startup contracts and real same-user Gunicorn processes.

**Target Platform**: Linux containers. macOS can supply independent host process proof.

**Project Type**: Container startup repair.

**Constraints**: No production process signal, container restart, cloud request, or store access.

**Scale/Scope**: Two masters and two control sockets.

## Constitution Check

The repair changes an existing startup script without adding a service or a runtime class.
The new test modules share the dedicated `tests/contract/container/` directory.
The specification directory holds five feature-owned records.
New support methods use bounded operations and explicit types.

Existing repository directories exceed the five-item limit.
This repair does not reorganize their unrelated contents.
Separate incremental structure work remains outside issue #3370.

The source has two existing multi-line shell commands.
Each command needs one new flag only.
A nearby comment explains the socket isolation.
The existing start and result logs already identify each portal.

The user prohibits production deployment in this repair.
The parent controls publication and the protected merge.
These explicit restrictions limit the broader deployment steps in the constitution.

## SpecKit Execution

The legacy feature hook refused the existing app-managed branch.
It reported that `jmorrison-juniper-gunicorn-control-sockets` already exists.
Use the file-only specification, plan, tasks, implementation, and analysis records.
Do not change shared `.specify/feature.json` or other shared feature state.

## Project Structure

| File | Purpose |
| - | - |
| `container/scripts/start.sh` | Add the two socket flags. |
| `tests/contract/container/test_gunicorn_control_sockets.py` | Check parsed flags, failure cases, and real reload behavior. |
| `tests/contract/container/gunicorn_control_support.py` | Manage temporary applications, masters, and control readings. |
| `documentation/container-deployment.md` | State the two portal socket paths and the deployment boundary. |
| `changelog.d/issue-3370-gunicorn-control-sockets.md` | Record the user-visible repair. |

## Phase 0: Research

The installed `gunicorn --help` exposes `--control-socket PATH`.
The installed source defaults to one socket under `HOME` when `XDG_RUNTIME_DIR` is absent.
The SDK protocol supplies statistics and configuration readings for each master.
These readings prove the identity of each master without a worker count change.
The probe closes its socket on success and failure.

Distinct socket paths preserve the existing control capability.
Disabling both sockets would remove that capability without a need.
The image creates the `misthelper` account at `/home/misthelper`.
The two startup commands already run as that same account.

## Phase 1: Test Design

Parse only the active `su misthelper -c` Gunicorn commands.
Do not execute the rest of the container entrypoint on the host.
Read exactly two commands and reject missing, repeated, disabled, or shared socket options.
Compare every other parsed argument with its current value.

Start fake WSGI applications with the parsed commands.
Replace only the bind addresses, temporary file paths, and controlled environment values.
Use `127.0.0.1` ports between 9600 and 9699.
Use a temporary home for both masters.
Keep that home within the Unix socket path limit.
Read the actual control master PID and effective socket configuration.
Read each fake HTTP response to prove the user and parent PID.
Reload each owned master and repeat all identity checks.
Retain logs and check the cleanup.

## Phase 2: Delivery

Record the failing baseline before the source edit.
Run the focused contracts, real process tests, and related container regressions.
Run the configured syntax, lint, format, type, security, test-quality, link, and writing checks.
Use Podman only through an isolated compose service with owned names and no production dependencies.
Record the actual capability and proof limits.
Create one local commit and report its exact SHA and file set.
Stop before publication until the parent grants the release.

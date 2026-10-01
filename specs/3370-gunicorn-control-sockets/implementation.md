# Implementation: Distinct Gunicorn control sockets

## Baseline

The worktree starts at `ff3cc1bea8ab58026210a968ff1465f61c9fec78`.
The original script passes no control socket argument to either master.
The installed CLI reports Gunicorn 26.2.0.

The initial focused run checked 17 test cases.
It reported 14 passes and three expected failures.
The startup contract rejected the absent socket arguments.
Both real process cases found a control response with the wrong master PID.

The first case started masters 13930 and 13932 under one account.
The control response for master 13930 identified master 13932.
The second case started masters 13937 and 13939.
The control response for master 13939 identified master 13937.
Both pairs used their own temporary home and the same default socket path.

The host proof reproduced incorrect control identity.
It did not reproduce the Linux address error reported in the issue.
The test retained both master logs and the actual control and HTTP readings.
The retained baseline report is `3370-red.log` in this session's artifact directory.

## Source Repair

The web portal command adds `--control-socket /home/misthelper/.gunicorn/portal.ctl`.
The capture portal command adds `--control-socket /home/misthelper/.gunicorn/capture.ctl`.
The repair changes no other startup argument or service behavior.

## Environment

The standard bootstrap first failed during the new environment's `ensurepip` process.
The process ended with SIGABRT.
An owned UV seed environment repaired the local environment.
The standard bootstrap then installed both current requirement files successfully.
No dependency manifest changed.

Podman reports an available Linux arm64 host.
The local image build and isolated image proof both passed.

## Host Verification

The final host run passed 152 cases with zero skips.
The new contract module passed all 22 cases.
Both real process cases passed each reload order.
Each case checked two masters, two SIGHUP events, four workers, and two socket removals.
The actual readings prove the same user and the correct master for each portal.
The logs contain no control server error or address collision.

The readiness probe waits for HTTP and control access.
HTTP readiness alone occurred before the control server started.
The repair adds no delay or timeout to the production startup.
The probe retains its original 10-second deadline.

The socket probe uses the SDK protocol with a context-managed socket.
An unavailable socket closes its descriptor.
The dedicated failure case proves that cleanup.
The final run treats `ResourceWarning` as an error.

The final host command was:

```bash
rtk proxy .venv/bin/python -m pytest tests/contract/container/test_gunicorn_control_sockets.py tests/unit/container/test_build_files_match.py tests/unit/container/test_startup_no_recursive_chown.py tests/unit/web_portal/test_portal_stream_thread_release.py tests/contract/packaging/test_compose_rebuild_warning.py tests/guardrails/test_container_policy_docs.py tests/guardrails/test_container_account_identifiers.py tests/guardrails/test_container_tls_verification.py tests/guardrails/test_compose_naming_policy.py tests/guardrails/test_shipped_artifacts.py tests/unit/web_portal/test_output_scan_runtime_files.py -q --timeout=120 -W error::ResourceWarning --basetemp=/Users/jmorrison/.copilot/session-state/e638e16d-2ef1-48fd-ad36-1534e659d6ec/files/3370-verified
```

**Result**: 152 passed in 4.18 seconds.
The session artifact `3370-verified-tests.log` retains the complete result.

## Image Verification

The image build used the unchanged `Containerfile`.
The image held the repaired `/start.sh`.
The local image SHA was `2f8d1b54e1e2e39106c7eaf224c55c9f18413fd806372a22c49ae5da8b29a2c2`.

The test started through a dedicated compose group and its `test` profile.
The container, network, and volume names start with `misthelper-tmp-issue3370-`.
The network was internal.
The container published zero host ports.
The proof used only fake WSGI applications and loopback ports 9600 and 9601.
It started no production application or store.

The proof parsed `/start.sh` inside the image.
Both masters ran as UID 1000.
The masters retained `/home/misthelper/.gunicorn/portal.ctl` and `/home/misthelper/.gunicorn/capture.ctl`.
Both sockets retained UID 1000 and mode `0600`.

The proof sent four SIGHUP events in both orders.
Every control response retained the correct master PID.
Both error logs contained zero control server errors or address collisions.
The proof verified removal of two masters, six workers, and both sockets.
The final proof passed one test in 1.611 seconds.

The build command was:

```bash
rtk proxy podman build --format docker --file Containerfile --tag localhost/misthelper-tmp-issue3370-control-proof:local .
```

The final proof command was:

```bash
rtk proxy .venv/bin/python -m podman_compose -f /Users/jmorrison/.copilot/session-state/e638e16d-2ef1-48fd-ad36-1534e659d6ec/files/3370-compose.yml --profile test up --no-deps --exit-code-from misthelper misthelper
```

The session artifacts retain the compose configuration, verification script, logs, and JSON readings.
The final summary is `3370-image-final-evidence/summary.json`.
The final console report is `3370-image-final-proof.log`.
Neither report contains a resource warning.

The provider has no `rm` subcommand.
Cleanup therefore used the exact owned names with `podman rm`, `podman volume rm`, and `podman network rm`.
The final name-filtered container, volume, and network lists were empty.
The cleanup also removed the owned local image tag.
No prune command ran.

## Quality Results

| Command | Result |
| - | - |
| `rtk proxy bash -n container/scripts/start.sh` | Passed. |
| `shellcheck` | Not available on this host. The Bash syntax check passed. |
| `rtk proxy .venv/bin/python -m py_compile MistHelper.py tests/contract/container/gunicorn_control_support.py tests/contract/container/test_gunicorn_control_sockets.py` | Passed. |
| `rtk proxy .venv/bin/python -m ruff check MistHelper.py tests/contract/container` | Passed. |
| `rtk proxy .venv/bin/python -m black --check MistHelper.py tests/contract/container` | Passed. Three files need no format change. |
| `rtk proxy .venv/bin/python -m mypy tests/contract/container/gunicorn_control_support.py tests/contract/container/test_gunicorn_control_sockets.py --config-file pyproject.toml` | Passed. Two files have no type errors. |
| `rtk proxy .venv/bin/python -m bandit tests/contract/container/gunicorn_control_support.py` | Passed. The scan checked 299 code lines with zero findings and zero suppressions. |
| `rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --roots tests/contract/container` | Passed. One test file has zero new findings and zero parse errors. |
| `.venv/bin/python -m radon cc tests/contract/container -j \| .venv/bin/complexity-gate --max 10` | Passed. Every block meets the threshold. |
| `rtk proxy .venv/bin/python -m pydocstyle tests/contract/container/gunicorn_control_support.py tests/contract/container/test_gunicorn_control_sockets.py` | Passed. |
| `rtk proxy .venv/bin/ste-linter tests/contract/container/gunicorn_control_support.py tests/contract/container/test_gunicorn_control_sockets.py changelog.d/issue-3370-gunicorn-control-sockets.md --grade-logging-strings --grade-user-facing-strings` | Passed. All three files score 100 with zero writing findings. |
| `rtk proxy git diff --check` | Passed. |
| `rtk proxy .venv/bin/markdown-link-check --root . documentation/container-deployment.md specs/3370-gunicorn-control-sockets changelog.d/issue-3370-gunicorn-control-sockets.md` | Passed. Seven tracked Markdown files have zero broken links. |
| `rtk proxy .venv/bin/check-citations tests/contract/container` | Passed. The scope contains zero citations and zero unresolved references. |

An AST check measured both new Python files.
Every method uses at most 25 lines.
The writing checker reports partial coverage because `data/ste_dictionary.json` is absent.
The five specification records score 94, 95, 100, 98, and 97.
The related guide scores 98.
The related guide has pre-existing writing findings outside the new section.
No writing exclusion changed.

The configured Bandit command excludes `tests`.
Its first configured scan measured zero lines.
The direct helper scan above proves the new support code without that exclusion.
The test-quality analyzer skips the support module because it is not a test module.
It measured the complete new test module.
The ratchet configuration and baseline stayed unchanged.

## Runtime Dependency Audit

The standard `pip_audit -r requirements.txt` resolver failed during `ensurepip` with SIGABRT.
UV then resolved the complete runtime manifest into a fully hashed temporary file.
The strict host audit checked 105 dependencies.
It reported zero known vulnerabilities and zero skipped dependencies.

A second resolution targets Python 3.13 on Linux arm64.
Its strict audit checked 107 dependencies with zero known vulnerabilities and zero skipped dependencies.
This resolution includes the dependencies specific to the image platform.

```bash
rtk proxy uv pip compile --python .venv/bin/python --system-certs --generate-hashes --no-header --quiet --output-file /Users/jmorrison/.copilot/session-state/e638e16d-2ef1-48fd-ad36-1534e659d6ec/files/3370-runtime-lock.txt requirements.txt
rtk proxy .venv/bin/python -m pip_audit -r /Users/jmorrison/.copilot/session-state/e638e16d-2ef1-48fd-ad36-1534e659d6ec/files/3370-runtime-lock.txt --no-deps --disable-pip --strict --progress-spinner off --format json --output /Users/jmorrison/.copilot/session-state/e638e16d-2ef1-48fd-ad36-1534e659d6ec/files/3370-runtime-audit.json
rtk proxy uv pip compile --python-version 3.13 --python-platform aarch64-manylinux_2_28 --system-certs --generate-hashes --no-header --quiet --output-file /Users/jmorrison/.copilot/session-state/e638e16d-2ef1-48fd-ad36-1534e659d6ec/files/3370-linux-runtime-lock.txt requirements.txt
rtk proxy .venv/bin/python -m pip_audit -r /Users/jmorrison/.copilot/session-state/e638e16d-2ef1-48fd-ad36-1534e659d6ec/files/3370-linux-runtime-lock.txt --no-deps --disable-pip --strict --progress-spinner off --format json --output /Users/jmorrison/.copilot/session-state/e638e16d-2ef1-48fd-ad36-1534e659d6ec/files/3370-linux-runtime-audit.json
```

The audit covers the full runtime manifest, not every development tool.
The development manifest installs `misthelper-devtools` from a pinned Git commit.
The runtime audit supplies no PyPI advisory proof for that Git-only tool.
No dependency, baseline, suppression, exclusion, migration, or store configuration changed.

## Publication

The parent retains publication control.
The parent did not grant a publication release.
Do not push, create a pull request, merge, or deploy before that release.
The isolated image proof does not replace approval for a production container restart.

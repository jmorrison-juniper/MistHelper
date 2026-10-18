# Quickstart: Cisco Config Converter Validation

This guide validates preview, review, and JSON export. It does not start a container or contact a
live Mist organization.

## Prerequisites

- Use the project Python 3.13 environment and development dependencies.
- Use original Cisco IOS sample configurations without production credentials.
- Provide a template name with 1 to 120 non-whitespace characters.
- Convert only global IPv4 `ip name-server` commands to `dns_servers`.
- Select template type `standalone` or `spoke`.
- Keep hardware roles, hardware models, IPv6 commands, malformed directives, and unknown commands unsupported.
- Process uploads in memory. The file limit is 16 MiB.

## Parser and Conversion

Run the parser and conversion unit tests:

```sh
.venv/bin/python -m pytest tests/unit/gateway/overrides/test_cisco_config_converter.py
```

Expected result: supported IPv4 DNS commands produce `dns_servers`. Malformed directives remain
visible as unsupported items. Empty or whitespace-only files and invalid encodings are rejected.
The tests cover the exact 16 MiB boundary and reject one byte above it.

## Preview and Export

Run the isolated portal route tests without Mist credentials:

```sh
.venv/bin/python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py
```

Expected result: preview and export complete without cloud requests. Unsupported items remain
visible. An edited proposal is rejected.

## Browser Journey

Run the isolated browser journey:

```sh
.venv/bin/python -m pytest tests/e2e/web_portal/test_portal_smoke.py
```

Expected result: the isolated browser uploads a sample, selects a template type, reviews the
proposal, and exports it without Mist credentials. The existing smoke module includes this
journey. It does not prove shared navigation registration.

## Portal Regression

Run the converter tests with the existing portal browser suite:

```sh
.venv/bin/python -m pytest tests/unit/gateway/overrides/test_cisco_config_converter.py tests/integration/web_portal/cisco_config_converter tests/e2e/web_portal -q
```

Expected result: converter and existing portal tests pass. The feature adds no service, volume,
network, database, or Redis instance. Product output remains under `data/`.

Cloud apply remains outside this release. Reconcile shared portal-file changes with their owner
before publishing implementation changes.

## Local Implementation Results

On 2026-10-18, the combined parser, route, and portal smoke command passed 63 tests.
Feature coverage was 100 percent:

```sh
.venv/bin/python -m pytest tests/unit/gateway/overrides/test_cisco_config_converter.py tests/integration/web_portal/cisco_config_converter/test_routes.py tests/e2e/web_portal/test_portal_smoke.py --cov=src/interfaces/portals/cisco_config_converter --cov-report=term-missing --cov-fail-under=80 -q --screenshot=only-on-failure --output=test-artifacts/cisco-browser
```

The first test run failed with two missing-package collection errors before implementation.
The combined passing run includes two real Chromium journeys and 18 existing portal smoke tests.
The exact 16 MiB file boundary passes without temporary-file spooling. A larger file fails.
A request above the file limit plus 16 KiB fails with HTTP 413.

The host must use `ConverterRequest` and initialize `CSRFProtect` before blueprint registration.
Registration fails when either protection is absent. No shared application or navigation file
changes are included. PR #4208 owns those files, so T015 remains blocked.

Unsupported items identify source lines and safe command categories. Unknown values remain
omitted because they can contain credentials. Preview, review, and export responses prohibit
browser caching. The signed session contains proposal digests, not configuration content.

The focused Ruff, Black, mypy, Bandit, complexity, dead-code, and docstring commands passed.
The ten Markdown artifacts passed STE with scores from 96 to 99.
The structure and movement guards passed 15 tests. The test-quality input preflight passed
one test and read all four required inputs.
The targeted test-quality analyzer checked three test modules and reported zero new findings.
The compatibility test confirms that other routes retain Flask upload streams and body limits.

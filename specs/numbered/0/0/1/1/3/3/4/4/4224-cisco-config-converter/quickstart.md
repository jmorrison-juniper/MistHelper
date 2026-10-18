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

Expected result: the browser uploads a sample, selects a template type, reviews the proposal, and
exports it without Mist credentials. Add this journey to
`tests/e2e/web_portal/test_portal_smoke.py`. A failed browser run saves a screenshot as a test
artifact.

## Portal Regression

Run the converter tests with the existing portal browser suite:

```sh
.venv/bin/python -m pytest tests/unit/gateway/overrides/test_cisco_config_converter.py tests/integration/web_portal/cisco_config_converter tests/e2e/web_portal -q
```

Expected result: converter and existing portal tests pass. The feature adds no service, volume,
network, database, or Redis instance. Product output remains under `data/`.

Cloud apply remains outside this release. Reconcile shared portal-file changes with their owner
before publishing implementation changes.

# Quickstart: Cisco Config Converter Validation

This guide defines validation scenarios for implementation. It does not start a container or contact a live Mist organization.

## Prerequisites

- Use the project Python 3.13 environment and development dependencies.
- Use approved Cisco IOS sample configurations with no production credentials.
- Mock all Mist SDK responses.
- Complete the license, SDK, gateway mapping, and upload policy gates in [plan.md](plan.md) before implementation.
- Record the verified upload limit and permitted file types in [contracts/portal.md](contracts/portal.md). Do not substitute an assumed value.

## Parser and Conversion

Run the parser and conversion unit tests:

```sh
python -m pytest tests/unit/gateway/overrides/test_cisco_config_converter.py
```

Expected result: valid fixtures produce a proposal; invalid encodings, empty files, oversized files, and unsupported commands produce safe results. The size boundary must match the verified portal limit.

## Preview and Export

Run the portal tests in the feature directory with no Mist credentials configured:

```sh
python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py
```

Expected result: preview and export complete without cloud requests. Unsupported items remain visible.

## Mist Apply

Run the mocked SDK contract tests:

```sh
python -m pytest tests/integration/web_portal/cisco_config_converter/test_sdk_contract.py
```

Expected result: the verified SDK method receives the selected organization and reviewed settings only after the operator enters the required confirmation. Missing credentials, rejected confirmation, and request failures do not appear as success.

## Browser Journey

Run the portal smoke test after adding the converter journey:

```sh
python -m pytest tests/e2e/web_portal/test_portal_smoke.py
```

Expected result: the browser opens the converter, selects a sample file and gateway target, and shows a proposal without Mist credentials. A failed browser run must retain its screenshot or trace as a test artifact.

## Compose and Existing Portal

Inspect `compose.yml` and the product output configuration. Expected result: the feature adds no service, volume, network, database, or Redis instance, and all output remains under `data/`.

Run the portal test set that covers navigation and current workflows. Use the repository's documented E2E command and report each exact result. Confirm that all existing routes remain available.

After all focused, browser, Compose, and regression checks finish, update this guide once with the exact commands and observed results.

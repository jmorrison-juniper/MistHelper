# Quickstart: Verify VPN Inventory Failure Handling

## Prerequisites

- Use the worktree Python 3.15 environment.
- Do not set or use a production Mist credential for these tests.
- Do not run `tests/integration/test_wan_vpn_builder_live.py`. It creates and deletes VPNs.

## Validation

Run the focused mocked test module:

```bash
python -m pytest tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py
```

The tests must prove that a complete empty inventory remains valid, failed or incomplete inventory stops the workflow, and no create call occurs after an inventory failure.

Run static checks for the modified Python module and test module:

```bash
python -m py_compile src/operations/wan/wan_vpn_builder.py
python -m ruff check src/operations/wan/wan_vpn_builder.py tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py
python -m black --check src/operations/wan/wan_vpn_builder.py tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py
```

Do not use the live integration test as a substitute for these synthetic checks.

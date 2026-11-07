# Quickstart: Verify Failed Profile Response Handling

## Prerequisites

- Build the local environment with `python3 scripts/bootstrap_worktree.py`.
- Use only mocked Mist SDK responses. Do not call the live Mist API.

## Validation

Run `python -m pytest -q tests/unit/test_wan_vpn_builder.py`.

The test for an HTTP 503 response with a plausible `results` array must pass with an empty profile list. Tests for successful responses must preserve the existing sorted profile list.

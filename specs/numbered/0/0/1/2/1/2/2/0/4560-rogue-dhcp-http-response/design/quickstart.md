# Quickstart: Verify Failed HTTP Response Handling

## Prerequisites

- Build the worktree environment with `python3 scripts/bootstrap_worktree.py`.
- Use only mocked SDK responses. Do not call Mist.

## Validation

Run the focused scanner and operation tests:

```bash
python -m pytest tests/unit/security/rogue_dhcp/test_scanner.py tests/unit/security/rogue_dhcp/test_operation.py
```

The scanner tests reject 4xx and 5xx response data before pagination.

They keep findings from successful pages and reject malformed pages.

The operation tests name failed sites and label partial exports. They also reject clean-result messages when the scan is incomplete.

Run Ruff on the changed Python files:

```bash
python -m ruff check src/operations/protection/security/rogue_dhcp/scanner.py src/operations/protection/security/rogue_dhcp/operation.py tests/unit/security/rogue_dhcp/test_scanner.py tests/unit/security/rogue_dhcp/test_operation.py
```

Run Black on the changed Python files:

```bash
python -m black --check src/operations/protection/security/rogue_dhcp/scanner.py src/operations/protection/security/rogue_dhcp/operation.py tests/unit/security/rogue_dhcp/test_scanner.py tests/unit/security/rogue_dhcp/test_operation.py
```

Do not run the live menu operation during validation.

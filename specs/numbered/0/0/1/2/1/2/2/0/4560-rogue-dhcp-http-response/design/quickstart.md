# Quickstart: Verify Failed HTTP Response Handling

## Prerequisites

- Build the worktree environment with `python3 scripts/bootstrap_worktree.py`.
- Use only mocked SDK responses. Do not call Mist.

## Validation

Run the focused scanner tests:

```bash
python -m pytest tests/unit/security/rogue_dhcp/test_scanner.py
```

The tests must reject 4xx and 5xx response data before pagination. They must also keep a finding from a successful response and report a failed site request.

Run Ruff on the changed Python files:

```bash
python -m ruff check src/operations/protection/security/rogue_dhcp/scanner.py tests/unit/security/rogue_dhcp/test_scanner.py
```

Run Black on the changed Python files:

```bash
python -m black --check src/operations/protection/security/rogue_dhcp/scanner.py tests/unit/security/rogue_dhcp/test_scanner.py
```

Do not run the live menu operation during validation.

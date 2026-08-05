# Contract: `CredentialConsole`

**Feature**: 1034-codeql-cleartext-logging

**Owner module**: `src/utils/console.py`

**Date**: 2026-08-05

This contract states the behavior of the credential display primitive. The class serves
user story 1 and satisfies requirements FR-009 through FR-014. The format follows the
precedent of `specs/1031-warning-echo-refactor/contracts/echo_helper.md`.

---

## Purpose

`CredentialConsole` shows a secret to an operator on an interactive terminal and withholds
that secret from every other destination. The class exists because a redirected stream, a
pipe, and a log file all keep a permanent copy of a credential.

The class lives beside `echo()` in `src/utils/console.py`. The module already owns console
output, so the new class needs no new module.

---

## C-1: The public surface is one method

```python
class CredentialConsole:
    @staticmethod
    def reveal(label: str, secret: str) -> bool: ...
```

The method returns `True` when it wrote the secret. The method returns `False` when it
withheld the secret. A caller uses the return value for its own action logging.

The parameter count is two. The five-item rule caps the count at five.

---

## C-2: The method writes with `sys.stdout.write()`

The method never calls `print()` for the secret. Requirement FR-014 drives this clause.

The ruff configuration in `pyproject.toml` does not select the `T20` rule family today. A
comment in that file states the plan of issue #886. That plan enables `T20` and converts
every `print()` call to a logging call across 5053 sites. A `sys.stdout.write()` call is not
a `print()` call, so the migration never sees this line and never converts it.

---

## C-3: The method decides with `sys.stdout.isatty()`

The method calls `sys.stdout.isatty()` once. A `True` answer selects the reveal path. A
`False` answer selects the withhold path.

The check blocks a redirected stream and a pipe. The check does not block a recorded
session. Research note R-002 records the test that proves this limit.

---

## C-4: The reveal path warns before it shows

The reveal path writes three parts in this order.

1. The warning. The text names the capture risk of a session recording.
2. The label and the secret.
3. Nothing else.

The warning comes first, so the operator reads the risk before the screen holds the secret.

The warning text states the specific consequence. An example text follows.

```text
Warning: a session recording captures this screen. The next line holds a live credential.
```

---

## C-5: The withhold path states the reason

The withhold path writes the label, a withhold notice, and the reason. The path never writes
the secret and never writes a partial secret.

An example text follows.

```text
-> ZTP Password: withheld
-> The output stream is not an interactive terminal, so the tool withheld the credential.
-> Run the command on an interactive terminal to read the credential.
```

The notice tells the operator how to reach the value. A notice with no remedy leaves the
operator stuck.

---

## C-6: The method never logs the secret

The method emits one action log line before the write and one after the write. Constitution
principle VII requires both lines.

Neither line holds the `secret` value. Neither line holds any part of the `secret` value.
Neither line holds a digest of the `secret` value.

Pull request #1732 tried a SHA-256 fingerprint for a related alert. CodeQL rejected that
change with the query `py/weak-sensitive-data-hashing` at high severity. Do not hash a
credential for a log label.

The log line names the label and the outcome.

```python
logging.info("Credential display requested for %s", label)
logging.debug("Credential display outcome for %s: %s", label, outcome)
```

The `outcome` value is `revealed` or `withheld`.

---

## C-7: The caller keeps the comment honest

The old comment in `src/device/_utility_commands_action.py` claimed that the tool never logs
and never saves the password. Requirement FR-013 forbids a comment that claims a behavior
that the code does not provide.

The new comment states the true behavior in one line. The comment names the terminal check
and names the recording limit.

---

## C-8: A guard test enforces clause C-2 and clause C-6

The test file is `tests/unit/test_credential_console_contract.py`.

The test reads the source of `src/utils/console.py` and the source of
`src/device/_utility_commands_action.py`. The test fails on any of the conditions below.

- The credential reveal path contains a `print(` call.
- The credential reveal path contains a `logging.` call that takes the secret variable.
- The module `src/device/_utility_commands_action.py` passes the credential to any callable
  other than `CredentialConsole.reveal`.

The test is the durable marker that FR-014 requires. A comment is advice. A test is
enforcement. A mechanical migration under issue #886 fails the test instead of shipping a
regression.

---

## C-9: The class adds no prompt

The method asks the operator no question. The method needs no call to `safe_input()`.

A typed confirmation was considered and rejected. The prompt does not remove the recording
risk, because the operator still reads the secret on the recorded screen. The prompt also
adds a step that acceptance scenario 1 of user story 1 does not describe.

Any future prompt in this path must use `InputUtils.safe_input()`. Constitution principle
III requires that wrapper for every input call.

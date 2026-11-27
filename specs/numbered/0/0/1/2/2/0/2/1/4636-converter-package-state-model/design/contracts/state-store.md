# Contract: State Store

This contract defines the private file store in `state/storage/store.py`. The store writes every converter state record. Production writes stay disabled until the owner approves them (decision D-3).

## Construction

`PrivateStateStore(root, secret, clock, enabled)` takes four values.

| Parameter | Type | Default | Rule |
| --- | --- | --- | --- |
| `root` | `pathlib.Path` | None | Private directory under `data/cisco_config_converter/state/` in production. A temporary directory in tests. |
| `secret` | string or None | None | The value of `PORTAL_SECRET_KEY`. The store reads it from the caller and never logs it. |
| `clock` | callable | UTC now | Returns an aware UTC datetime. Tests inject a fixed clock. |
| `enabled` | boolean | `False` | Production writes stay disabled while this value is `False`. |

## Key Derivation

- The sealing key is `HMAC-SHA256(key=secret bytes, message=b"misthelper.cisco-converter.state.v1")`.
- The sealing key is never the Flask session key. A reader cannot use the session key to forge a seal.
- A missing or empty secret refuses every write and every read.

## Write Sequence

`write_record(kind, identifier, payload)` runs these steps in order.

1. Log an info line that names the kind and the identifier.
2. Refuse when `enabled` is `False`. Raise `PersistenceUnavailable`. Create no file.
3. Refuse when the secret is missing. Raise `PersistenceUnavailable`. Create no file.
4. Refuse when `kind` is not in the allow-list. Refuse when the identifier does not match `^[0-9a-f]{32}$`.
5. Refuse when `root` is a symbolic link or a regular file.
6. Create `<root>/<kind>` with mode `0o700` on POSIX.
7. Acquire the lock at `<root>/<kind>/<identifier>.lock`. Retry 50 times at 0.1 second intervals. Refuse on timeout.
8. Encode the payload in canonical form. Compute the digest and the seal.
9. Write an envelope to a temporary file. Use `O_CREAT` and `O_EXCL`, and mode `0o600`.
10. Flush and fsync the temporary file. Close it.
11. Replace the final file with `os.replace`.
12. Read the final file back. Recompute the digest and the seal. Compare both values with the expected values.
13. On any mismatch, remove the temporary file if present, raise `PersistenceUnavailable`, and log the exception class name.
14. Release the lock.
15. Log a debug line that names the kind, the identifier, and the digest.

Warning: A write that reports success before step 12 can hide a corrupt record. Keep the read-back before the success line.

## Envelope

```json
{"kind": "approval", "identifier": "<32 hex characters>", "payload": {}, "digest": "<64 hex characters>", "seal": "<64 hex characters>"}
```

The `payload` field holds the canonical record object. The `digest` field covers the canonical payload bytes. The `seal` field covers the kind, the identifier, and the canonical payload bytes, separated by newlines.

## Read Sequence

`read_record(kind, identifier)` opens the final file under the lock, parses the envelope, and recomputes the digest and the seal. A mismatch raises `PersistenceUnavailable` with the message `Seal check failed`. A missing file raises `PersistenceUnavailable` with the message `Record is absent`. No partial record is returned.

## Approval Consumption

`consume_approval(approval_id, operator_id, proposal_digest, scope_digest)` runs under the approval lock.

1. Read the approval record and verify its seal.
2. Refuse when the approval is expired. The boundary is inclusive, so `now >= expires_at` refuses.
3. Refuse when `operator_id` differs from the stored operator.
4. Refuse when either digest differs from the stored digest.
5. Refuse when the state is `consumed`.
6. Set the state to `consumed` and set `consumed_at` to the clock value.
7. Write the record through the write sequence while the lock is held.
8. Return the updated record only after the read-back passes.

Two processes that call this method for one approval produce one success and one refusal.

## Lock

`NativeFileLock` follows the firmware ownership pattern in `web_portal/routes/firmware_policy/jobs/ownership/__init__.py`.

- On Windows, the lock uses `msvcrt.locking` with `LK_NBLCK` on one byte. The file receives one byte before the lock is taken.
- On POSIX, the lock uses `fcntl.flock` with `LOCK_EX | LOCK_NB`.
- Closing the file descriptor releases the lock. The operating system also releases the lock when the process exits.

## Failure Rules

| Condition | Result |
| --- | --- |
| `enabled` is `False` | `PersistenceUnavailable`. No file is created. |
| Secret is missing | `PersistenceUnavailable`. No file is created. |
| Root is a file or a symbolic link | `PersistenceUnavailable`. No file is created. |
| Lock timeout | `PersistenceUnavailable`. The record is unchanged. |
| Disk write fails | `PersistenceUnavailable`. The temporary file is removed. |
| Read-back mismatch | `PersistenceUnavailable`. No success is reported. |
| Seal mismatch on read | `PersistenceUnavailable`. No record is returned. |
| Secret changed after restart | Every read fails with `Seal check failed`. |

## Retention, Backup, and Recovery

- Retention: The store deletes no record in this change. Decision D-9 keeps every record until an owner-approved purge task exists.
- Backup: The records sit under `data/`, which the existing data backup procedure covers. Coverage is unverified (U-4).
- Recovery: Restore copies the files back. A restored record needs the same secret. A restored record with a different secret fails the seal check.
- Verified persistence: A success line appears only after the read-back passes.

## Privacy

- The store never writes source text.
- The store never logs the secret, the sealing key, or the seal value.
- The store logs the record kind, the identifier, and the digest only.
- The store writes files only below `root`. It refuses any identifier that would leave `root`.

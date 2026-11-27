# Contract: Private Input Store

This contract defines the private folder for stored inputs. The module `state/intake/private_files.py` holds `INPUT_IDENTIFIER_PATTERN`, `PrivateInputCatalog`, and `PrivateInputRetention`. The store keeps source text only. It never keeps an original file name.

## Location

- The production root is `data/cisco_config_converter/input/`. The tests pass a `tmp_path` root.
- `.gitignore` line 95 ignores the `data/` folder. No commit includes a stored input.
- When retention is enabled, the code creates the root with mode 0700 on POSIX systems.
- Production enablement waits for decision D-11. This change does not enable retention.

## Names

- The identifier is `uuid.uuid4().hex`. It has 32 lowercase hexadecimal characters.
- The file name is the identifier followed by the suffix. The suffix is one of `.txt`, `.conf`, `.cfg`, `.ios`, `.config`, or `.log`.
- The store writes no sidecar file. The store keeps no original name.

## Catalog: `PrivateInputCatalog`

- The constructor takes one root path.
- `entries()` returns one document for each file whose name matches the pattern. It skips every other name.
- The method skips a symbolic link and a file that is not regular. It uses `follow_symlinks=False` for the check.
- Each entry holds `id`, `suffix`, `bytes`, and `created_at`. The value of `created_at` is the UTC ISO 8601 form of the modification time.
- The method sorts the entries from newest to oldest.
- A missing root returns an empty list.
- A root that is a symbolic link or a regular file raises `LookupError`.
- `resolve(identifier)` validates the identifier first. It raises `ValueError` when the identifier fails. It finds the one matching file. It checks that the file is not a link. It checks that the resolved parent equals the resolved root.

## Retention: `PrivateInputRetention`

The constructor takes a root path and an `enabled` flag. The default flag is `False`. The blueprint receives the object from the host. The blueprint default is no retention object.

`save(content, suffix)` runs these steps in order.

1. Log an info line: `Saving a private converter input.` The line carries no content and no name.
2. When `enabled` is `False`, raise `ValueError` with the message `Saving input is unavailable.` Create no file.
3. When the suffix is not one of the six allowed suffixes, raise `ValueError`.
4. Create the root when it does not exist. Refuse a root that is a symbolic link or a regular file with `LookupError`.
5. Generate the identifier with `uuid.uuid4().hex`.
6. Open the new file under the root with `os.O_WRONLY | os.O_CREAT | os.O_EXCL` and mode `0o600`. When the open raises `FileExistsError`, raise `LookupError` with the message `Retry the save.` Change nothing.
7. Write all the bytes. Flush the data and call `fsync`. Close the file. Compare the file size with the length of the content.
8. When a step after the open fails, remove the file that this save created. Then raise `LookupError` with the message `Retry the save.`
9. Log a debug line with the byte count only.
10. Return the identifier.

A failed write removes only the file that the same save created. The store never removes any other file.

## Read Path for a Stored Selection

1. Resolve the identifier with `resolve`.
2. Open the file for reading with the `O_NOFOLLOW` flag when the platform defines it.
3. Read at most 16,777,216 bytes plus one byte.
4. Pass the bytes and the stored file name to `SourceConfiguration.read`.

On Windows, `O_NOFOLLOW` does not exist. The link check runs before the open and again after the open. The residual race stays in unresolved item U-3.

## Failure Table

| Condition | Raised error | Route status |
| --- | --- | --- |
| Retention disabled | `ValueError` | 400 |
| Malformed identifier | `ValueError` | 400 |
| Unknown identifier | `ValueError` | 400 |
| Symbolic link or non-regular file | `ValueError` | 400 |
| Root is a symbolic link or a regular file | `LookupError` | 409 |
| Exclusive create collision | `LookupError` | 409 |
| Write or size check failure | `LookupError` after cleanup | 409 |

## Privacy

- The store logs no content, no client file name, and no source text.
- The store logs identifiers and counts only.
- The catalog exposes no absolute path.
- The stored file is not a state record. It carries no seal. The seal rule in issue 4636 applies to state records only.

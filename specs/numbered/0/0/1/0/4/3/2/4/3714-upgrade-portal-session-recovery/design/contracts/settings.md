# Contract: Session Recovery Settings

This contract lists each environment variable that the feature reads. Each variable is read by name only. Logs name a variable, and logs never print its value.

## Variables

| Variable | Required | Default | Format or range | Failure |
| - | - | - | - | - |
| `CAPTURE_SESSION_ENCRYPTION_KEY` | Required in a container. Generated locally when unset, with a warning that names the variable. | None | A Fernet key of 44 URL-safe base64 characters | A container start without a valid key raises `SettingsError` that names the variable |
| `CAPTURE_SESSION_ENCRYPTION_KEY_PREVIOUS` | Optional | None | The same format as the key above | An invalid value raises `SettingsError` |
| `CAPTURE_SESSION_TTL_SECONDS` | Optional | `28800` | Integer from `300` to `28800` | An out-of-range value raises `SettingsError` |
| `CAPTURE_SESSION_IDLE_SECONDS` | Optional | `1800` | Integer from `60` to the value of `CAPTURE_SESSION_TTL_SECONDS` | An out-of-range value raises `SettingsError` |
| `REDIS_PASSWORD` | Existing variable | The compose file sets a literal default (`compose.yml:149`) | In a container with the store enabled, the value must differ from the compose default (D-2) | A container start with the default value raises `SettingsError` |

## Rules

- `CAPTURE_SESSION_ENCRYPTION_KEY` must differ from `CAPTURE_SECRET_KEY`. A key that matches the signing key raises `SettingsError`.
- The store is enabled whenever the portal runs. The store serves environment token sessions only (D-4).
- The compose file requires `CAPTURE_SESSION_ENCRYPTION_KEY` with the same pattern as `CAPTURE_SECRET_KEY` (`compose.yml:109`).
- The example file `deploy/.env.example` documents each variable. It holds no value for a key (FR-020).
- Generating a key uses the Fernet key helper in the pinned cryptography package (`fernet.py:54`, `generate_key`).

Caution: changing `CAPTURE_SESSION_ENCRYPTION_KEY` without the old key in `CAPTURE_SESSION_ENCRYPTION_KEY_PREVIOUS` makes every stored record unreadable. Each affected operator authenticates again.

Warning: a key value written into a commit, a log, or a shared document cannot be withdrawn. Rotate the key at once after any such exposure.

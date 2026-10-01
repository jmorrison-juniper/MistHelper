### Fixed

- Fixed menu 273 so an admin with `two_factor_verified` set to `false` gets the `no_two_factor` finding.
- The report now writes `not_reported` when the live API omits SSO state, password age, and invite expiry fields. Closes #3693.

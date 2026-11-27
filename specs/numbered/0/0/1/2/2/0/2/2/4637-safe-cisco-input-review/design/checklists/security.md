# Security Checklist: Safe Cisco Input and Structured Review

**Purpose**: Check the security controls of the stored input, the upload path, and the observation review.
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

**Note**: Each item is checked. An item that needs an explanation carries the reason on the line below it.

## Path and Selection Controls

- [x] SEC001 The client never sends a file path. The server resolves each stored identifier.
  - Evidence: `test_client_path_is_never_accepted_as_stored_identifier`.
- [x] SEC002 A stored identifier must match `^[0-9a-f]{32}$`.
  - Evidence: `test_unknown_or_malformed_identifier_is_refused`.
- [x] SEC003 Traversal, drive, UNC, and control-character forms in a name are refused.
  - Evidence: `test_path_like_and_control_names_are_refused`.
- [x] SEC004 A name is display text only and never becomes a path.
  - Evidence: Decision D-3 and the name rule in `contracts/private-input-store.md`.
- [x] SEC005 A symbolic link is ignored by the catalog and refused by retrieval.
  - Evidence: `test_catalog_ignores_symlinks_and_non_regular_entries` and `test_symlink_escape_is_refused_for_stored_selection`.

## Storage Controls

- [x] SEC006 No route returns the body of a stored file.
  - Evidence: The route table in `contracts/input-routes.md` has no route for a stored body. `test_inputs_route_lists_catalog_without_paths` checks the catalog output.
- [x] SEC007 Production retention stays disabled. Browser exposure needs a separate exclusion change first.
  - Explanation: Decision D-11 and remediation R-4 cover the shared data browser and the output scan.
- [x] SEC008 Each save uses exclusive creation. A collision never overwrites a file.
  - Evidence: `test_retention_refuses_collision_without_overwrite`.
- [x] SEC009 On POSIX systems the folder uses mode 0700 and each file uses mode 0600.
  - Evidence: `test_retention_uses_exclusive_creation_and_owner_mode`.
- [x] SEC010 A failed write removes only the file that the same save created.
  - Evidence: The save steps in `contracts/private-input-store.md`.
- [x] SEC011 The original file name is never stored.
  - Evidence: Decision D-8 and `test_catalog_reports_only_safe_metadata`.

## Output and Logging Controls

- [x] SEC012 Logs omit source text, client file names, and secret values.
  - Evidence: `test_logs_omit_source_text_and_original_names`.
- [x] SEC013 Observation values omit identity values, credentials, communities, keys, and banner text.
  - Evidence: `test_identity_values_are_omitted` and `test_credential_values_are_omitted`.
- [x] SEC014 Error responses omit paths and tracebacks.
  - Evidence: The common rules in `contracts/input-routes.md`.
- [x] SEC015 No new code reads `PORTAL_SECRET_KEY`.
  - Explanation: Stored input files carry no seal. The seal rule in issue 4636 covers state records only.

## Residual Risks

- [x] SEC016 The Windows race between the link check and the open stays documented.
  - Explanation: Unresolved item U-3 in `analysis.md` records the residual race and the before and after checks.
- [x] SEC017 The observation route changes no review state and writes no file.
  - Evidence: `test_observations_route_requires_csrf_and_keeps_review_state` checks the review state. The observation design in `contracts/observation-families.md` has no write call.

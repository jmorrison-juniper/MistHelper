# Spec: Switch to interactive login (Menu 115)

Summary

Audit the "Switch to interactive login" command which likely toggles an interactive authentication flow or shell for devices or services. Validate behavior, error handling, and tests.

Scope

- Locate handler in MistHelper.py or auth modules.
- Verify it doesn't expose credentials in logs and supports secure prompts.
- Ensure tests exist or add tasks to create them.

Acceptance

- Clear mapping of function to CLI command
- Plan to add secure prompts and unit tests

Target path

specs/115-audit-menu-115-switch-to-interactive-login/

Menu metadata

- menu_id: 115
- display_text: "Switch to interactive login"
- function_ref: auth_manager.py::switch_to_interactive_login
- sql_export_relevant: false

Checklist

- [ ] Ensure no credentials logged
- [ ] Secure prompt behavior verified
- [ ] Tests for prompt-handling added

Notes

- This command is security-sensitive; test coverage and logging review are critical.


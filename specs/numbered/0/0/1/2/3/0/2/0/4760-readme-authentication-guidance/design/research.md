# Research: README Authentication Guidance

## Decisions

### Describe both authentication methods

- **Decision**: State that operators can use an API token or interactive `--login` with an email and password.
- **Rationale**: `MistHelper.py` passes `require_token=False` for `--login` and dispatches to the interactive initializer. The initializer builds `LoginOrchestrator` with the email/password prompt flow.
- **Alternatives considered**: Requiring a token for all operators would contradict the current command-line behavior.

### Explain conditional two-factor authentication

- **Decision**: State that MistHelper prompts for a verification code when Mist requires two-factor authentication.
- **Rationale**: `LoginOrchestrator._run_login_pipeline` checks the first SDK login response, prompts for a code when the response requires it, then resubmits the email, password, and code through `login_with_return`.
- **Alternatives considered**: Claiming that every account needs a code would misstate the conditional flow. Omitting the code prompt would leave the setup guidance incomplete.

### Explain token transmission

- **Decision**: State that MistHelper sends the token in an HTTPS authorization header and that `.env` is local storage.
- **Rationale**: `MistHelper.py` constructs `Authorization: Token <token>` for a request to an HTTPS Mist host. The existing Mist API reference identifies the same header.
- **Alternatives considered**: Saying that the token never leaves the host conflicts with both the request code and the API reference.

## Evidence

- `MistHelper.py:7839-7855` selects interactive authentication without a token when `--login` is set.
- `MistHelper.py:3013-3017` exempts interactive login from the API-token requirement.
- `src/foundation/support/refactors/initialize_mist_session_interactive.py` creates the interactive login orchestrator.
- `src/mist/access/auth/interactive/login_orchestrator.py:105-112,185-203` handles the initial login and conditional two-factor prompt.
- `tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py:246-270` exercises the installed SDK with the network transport mocked and checks the verification request.
- `MistHelper.py:3054-3059` sends a token in the `Authorization` header to an HTTPS Mist endpoint.
- `documentation/marvis-actions-api-endpoints.md:64` records the token authorization header. This file is evidence only and is outside this issue's scope.
- `documentation/cli-reference.md:27` documents `--login` as interactive email and password sign-in. This file is evidence only and is outside this issue's scope.

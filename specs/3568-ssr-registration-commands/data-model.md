# Data Model: SSR registration commands

## RegistrationCommandSet

Fields:

- `conductor_cmd`: The command for conductor registration.
- `registration_code`: The raw registration code. The operation must not log this value.
- `router_shell_cmd`: The command for router shell registration.

Rules:

- Empty and missing fields are omitted from the printed command text.
- The `registration_code` value appears in the file only when the operator confirms the write.
- Logs must not include any field value.

## RegistrationResponse

Fields:

- `status_code`: The HTTP status from Mist.
- `data`: The JSON body from Mist.

Rules:

- Any 2xx status can provide command text.
- Any non-2xx status prints `The API returned HTTP <status>.` and exits cleanly.

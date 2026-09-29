# Contract: SMS provider test operation

## Menu contract

- Menu number: `284`
- Category: `interactive`
- Handler: `src.troubleshooting.sms_provider_test.operation.SmsProviderTest.run`
- Output file: `SmsProviderTest.csv`

## Prompt contract

1. Ask the provider selection.
2. Ask provider-specific public values.
3. Ask provider-specific secret values with hidden input.
4. Ask destination number when the provider did not already supply `to`.
5. Ask `Send the SMS provider test message now? [y/N]:`.
6. Send the API request only when the answer is `y` or `Y`.

## Provider body contract

### Twilio

```json
{
  "from": "+185051234567",
  "to": "+19999999999",
  "twilio_auth_token": "secret",
  "twilio_sid": "AC5f4366878d193fb4865ab151739999eb"
}
```

### SMSGlobal

```json
{
  "smsglobal_api_key": "key",
  "smsglobal_api_secret": "secret",
  "to": "+911122334455"
}
```

### Telstra

```json
{
  "telstra_client_id": "client-id",
  "telstra_client_secret": "secret",
  "to": "+911122334455"
}
```

## Result row contract

```json
{
  "provider": "Twilio",
  "destination": "+19999999999",
  "verdict": "accepted",
  "http_status": 200,
  "response_text": "OK",
  "tested_at": "2026-09-29T20:59:35+00:00"
}
```

Credential fields are forbidden in the result row.

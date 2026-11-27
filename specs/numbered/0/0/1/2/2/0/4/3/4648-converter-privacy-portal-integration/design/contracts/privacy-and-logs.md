# Contract: Privacy, Logs, and Debug Defaults

## Responses

- Converter responses set `Cache-Control: no-store` (`routes.py` lines 113 and 149).
- Error bodies hold a safe message and no traceback.
- Error bodies hold no source text, no template name, no file name, and no secret value.

## Session

- The session holds `cisco_proposal` and `cisco_reviewed` as SHA-256 hex digests (`models.py` lines 94 to 112).
- The session holds no proposal, no template name, and no source text.
- Test `test_session_holds_digest_only` checks the session transaction.

## Logs

- Converter log messages use static templates. Example: "Converter input validation failed: %s" (`routes.py` line 83).
- Log values hold no file name, no template name, and no secret value.
- Test `test_logs_omit_source_name_and_secret` attaches a synthetic canary to the source text and to the secret. It fails when a canary appears in `caplog`.

Warning: a secret value in a log line exposes that value to every reader of the log. Keep each canary synthetic.

## Unsupported items

- An unsupported item holds a label, not the raw source line (`conversion.py` lines 78 to 83).
- The label for an `ip name-server` line is `ip name-server [values omitted]`.

## Debug

- Flask debug stays False in the factory. Test `test_debug_off_in_real_factory` checks this.
- The container runner forces `debug=False` (`MistHelper.py` line 6889).
- The local runner uses the `--debug` flag, which defaults to false (`MistHelper.py` line 7271).

## Network and secrets

- The converter package imports no network or SDK module. Test `test_converter_package_imports_no_network_module` parses four files with `ast`.
- The offline journey opens no socket. Test `test_offline_journey_opens_no_socket` patches `socket.socket.connect`.
- Tests set `PORTAL_SECRET_KEY` with `monkeypatch`. The value never appears in test output.
- Tests never print an environment variable value.

## Storage

- The converter writes no file. The offline journey patches `builtins.open` and expects no call (`test_routes.py` lines 60 to 66).
- Storage exposure rules activate with the storage issues (decision D-10).

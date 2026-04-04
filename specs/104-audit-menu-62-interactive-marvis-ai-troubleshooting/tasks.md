Implementation tasks — dependency-ordered and atomic

Guidelines
- Keep each todo atomic and testable.
- Each code change should be accompanied by unit tests before integration changes.
- Follow DI principle: accept optional dependencies; create defaults only when None.

Ordered todos (numbered, topological order)

1) Create MarvisClient core (unit tests first)
- File: src/marvis/client.py
- Tests: tests/unit/test_marvis_client_retry.py, tests/unit/test_marvis_client_token.py
- Description: implement call(), retry/backoff, integrate TokenCache.
- Estimated: 1 day

2) Create TokenCache and refresh logic
- File: src/auth/token_cache.py
- Tests: tests/unit/test_token_cache_refresh.py
- Description: implement token metadata, attempt_refresh(), lock-based concurrency, proactive refresh scheduling (but default disabled).
- Estimated: 1 day

3) Introduce OutputWriter abstraction and replace prints in one small path
- File: src/output/writer.py
- Tests: tests/unit/test_output_writer.py
- Description: add Writer interface and refactor a small section of MistHelper to use it.
- Estimated: 0.5 day

4) Modify MistHelper.launch_interactive to accept DI and return structured Result
- File: small change in MistHelper.py (no API change for callers)
- Tests: tests/unit/test_launch_interactive.py
- Description: accept marvis_client, output, logger; build InteractiveSession with correlation_id and return Result object.
- Estimated: 1 day

5) Add fixtures and integration harness
- Files: tests/fixtures/marvis/*.json; tests/integration/test_interactive_harness.py
- Description: record representative Marvis responses (happy-path, 401-then-200, slow/timeout) and implement harness asserting CSV and logs include correlation_id.
- Estimated: 1-2 days

6) Add prompt timeout abstraction and tests
- File: src/input/prompt.py or integrated in output/writer
- Tests: tests/unit/test_prompt_timeout.py
- Description: supports timeouts and non-interactive mode fallbacks.
- Estimated: 0.5 day

7) CI integration and final docs
- Title: CI integration and final docs
- File: CI pipeline changes and docs
- Description: add pytest invocations, fixtures handling, and update README/quickstart.
- Estimated: 0.5 day

Atomic change & commit instructions
- Make each task its own commit/PR with tests:
  - commit messages:
    * feat(marvis): add MarvisClient core (src/marvis/client.py)
    * feat(auth): add TokenCache with refresh-on-401 (src/auth/token_cache.py)
    * refactor(output): add OutputWriter and switch interactive prints
    * test(marvis): add unit tests for token refresh and retry
    * test(integration): add Marvis response fixtures and harness
  - PR description should reference this spec (specs/.../spec.md) and acceptance criteria.
  - Include Co-authored-by trailer in commits for any joint authors:
    - Co-authored-by: Automated Spec Agent <spec-agent@local>

If you'd like, I can produce ready-to-apply git patch snippets (unified diffs) for each of the small changes (client/token_cache/output writer + MistHelper small edits), or produce the actual file create commands to run locally (powershell or git patch) so you can apply them atomically.

Which would you prefer next?

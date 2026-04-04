Title: Tasks — dependency-ordered todos for feature work

Overview
- The tasks are dependency-ordered. Each todo includes target file edits/creates, tests to add, and CI validation steps.

Todos (ordered)

1) t1-add-input-utils
- Title: Add InputUtils.safe_input and exceptions
- Description:
  - Create file:
    C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\src\utils\input_utils.py
  - Implement InputUtils.safe_input signature and exceptions (UserCancelled, NonInteractiveError).
  - Provide unit tests:
    - tests/test_input_utils.py
      - test_safe_input_non_interactive_default
      - test_safe_input_keyboard_interrupt_returns_user_cancelled_or_raises
  - CI: pytest tests/test_input_utils.py
- Status: pending

2) t2-add-site-cache
- Title: Implement SiteCache manager
- Description:
  - Create file:
    C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\src\cache\site_cache.py
  - Implement SiteCache and SiteCacheEntry with TTL support, age_seconds(), force_refresh(), clear().
  - Provide unit tests:
    - tests/test_site_cache.py
      - test_set_and_get_returns_sites
      - test_is_fresh_within_ttl
      - test_expired_after_ttl (simulate time or inject clock)
      - test_force_refresh_clears_cache
  - CI: pytest tests/test_site_cache.py
- Depends on: t1-add-input-utils (for exception types, optional)
- Status: pending

3) t3-add-prompt-logging
- Title: Add prompt logging utilities and event schema
- Description:
  - Create file:
    C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\src\utils\prompt_logging.py
  - Provide get_prompt_logger() and log_prompt_event()
  - Modify existing log configuration if needed to include structured logs in JSON or dict form.
  - Provide unit tests:
    - tests/test_prompt_logging.py
      - test_log_prompt_event_emits_expected_fields
  - CI: pytest tests/test_prompt_logging.py
- Depends on: none
- Status: pending

4) t4-refactor-prompt-utils
- Title: Refactor select_site_with_logging and select_site_id_from_csv to use InputUtils and SiteCache
- Description:
  - Edit file:
    C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\src\prompt_utils.py
    - Import SiteCache singleton or accept SiteCache instance as parameter.
    - Replace existing input() usage with InputUtils.safe_input.
    - Show cache age in UI header using cache.age_seconds() conversion to human-readable.
    - Accept tokens 'c' and 'r' (case-insensitive).
    - Implement matching logic:
       * numeric index/ID match
       * case-insensitive substring search
       * single match -> return
       * multi-match -> display disambiguation list and allow choose index (1..N)
    - Implement pager with default page_size = 50 (configurable param).
    - Re-prompt once on invalid input.
    - Use prompt_logging.log_prompt_event calls at key points.
  - Provide unit tests:
    - tests/test_select_site.py
      - test_select_by_exact_id
      - test_case_insensitive_substring_match_single
      - test_substring_disambiguation_multiple
      - test_cancel_token_returns_none
      - test_refresh_token_forces_refetch
      - test_non_interactive_raises_or_uses_default
      - test_pager_respects_page_size
  - CI: pytest tests/test_select_site.py and overall suite
- Depends on: t1-add-input-utils, t2-add-site-cache, t3-add-prompt-logging
- Status: pending

5) t5-performance-tests-and-optimizations
- Title: Add performance tests and optimize matching for large lists
- Description:
  - Add tests:
    - tests/test_large_site_list_performance.py
      - Generate 10k sample sites, run substring matching and measure time (< threshold, e.g., 2s on CI baseline)
  - Implement performance optimizations:
    - Precompute lowercase name index (names_lower)
    - Limit displayed disambiguation results (e.g., show first 200 matches by default)
    - Use generators for pager rendering
  - CI: Run performance smoke test in CI optional stage or with marker (e.g., pytest -m perf)
- Depends on: t4-refactor-prompt-utils
- Status: pending

6) t6-ci-and-lint
- Title: Add CI steps and linter adjustments
- Description:
  - Update CI pipeline to ensure:
    - pytest -q (all tests)
    - flake8 / black check (or project's configured linter/formatter)
    - Optional: perf smoke test stage that runs the large list test but can be gated/marked slow
  - Update any CI docs or task runner scripts to include new test files.
- Depends on: t1..t5
- Status: pending

Notes about tests and test design
- Use dependency injection for time (pass a clock or monkeypatch datetime) to test TTL without sleeping.
- For interactive tests, simulate InputUtils.safe_input by patching it to return desired sequences (including 'r', 'c', invalid entries).
- Non-interactive tests should set interactive=False and assert NonInteractiveError or that non_interactive_default is used.

Files to create/edit summary (concise)
- Create:
  - src/utils/input_utils.py
  - src/cache/site_cache.py
  - src/utils/prompt_logging.py
  - tests/test_input_utils.py
  - tests/test_site_cache.py
  - tests/test_prompt_logging.py
  - tests/test_select_site.py
  - tests/test_large_site_list_performance.py
- Edit:
  - src/prompt_utils.py (select_site_with_logging and select_site_id_from_csv)
  - update any imports in CLI modules to use InputUtils and SiteCache as needed.

CI validation steps (explicit)
1) Run unit tests:
   pytest -q
2) Lint/format:
   flake8 src tests
   black --check .
3) Optional performance stage:
   pytest -m perf tests/test_large_site_list_performance.py

Performance considerations (short)
- For large lists use pre-lowercased name index, limit displayed disambiguation results, and consider using a more efficient search structure (trie or inverted index) if >100k entries are typical.

Estimated effort
- Implementation: 1–2 days
- Tests & CI: 0.5–1 day
- Perf tuning (if required): +0.5–1 day

-----------------------------------------------------------------------

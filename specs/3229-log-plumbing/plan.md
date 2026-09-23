# Implementation Plan: Keep plumbing lines out of the Execution Log

## Root cause

`_RunLogHandler._is_user_facing()` in `web_portal/services/operation.py` sends an INFO record to the Execution Log unless its logger is in `_DEBUG_LOGGERS` or its message starts with a prefix in `_INTERNAL_PREFIXES`. The resolver messages matched neither list.

## Design

Add the eight message prefixes to `_INTERNAL_PREFIXES`. The existing design already routes API plumbing this way, so the change follows it. A logger-name rule would be wrong here, because `src.config.config_utils` also logs lines that the operator needs.

## Guard

`tests/unit/web_portal/test_portal_log_routing.py` parses the three source modules with `ast`, finds each plumbing INFO call, and requires that each one routes to the debug channel. A reworded message therefore fails the test. The test also proves that operator lines and plumbing warnings stay in the Execution Log.

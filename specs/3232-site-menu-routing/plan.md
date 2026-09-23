# Implementation Plan: Keep the site menu and the store plumbing out of the Execution Log

## Root cause

`PromptUtils.select_site_id_from_csv()` logs its menu at WARNING (`src/ui/prompt_utils.py:146-148`), because the command line hides INFO by default (#886). `_RunLogHandler._is_user_facing()` sends every WARNING to the Execution Log. The same prompt refreshes `SiteList.csv`, and the refresh writes the polyglot store, which logs one JSON line for each collection at INFO.

## Design

1. `_is_site_menu_line()` matches the `src.ui.prompt_utils` logger and the two line shapes of the menu, and it runs before the WARNING rule. The match stays narrow, so no other warning is hidden.
2. `_DEBUG_LOGGER_PREFIXES = ("src.db.",)` routes database INFO lines. It runs after the WARNING rule, so a failure stays visible.
3. `redis_writer` and `redis_json_writer` join `_DEBUG_LOGGERS`, because those writers bind bare names outside `src.db`.
4. `Polyglot write:` and `Polyglot DatabaseRouter initialized` join `_INTERNAL_PREFIXES`.

## Guard

`tests/unit/web_portal/test_portal_log_routing.py` renders the two menu calls from their source with `ast` and requires that each one routes to the debug channel. It also proves that the not-found line, a database warning, and a numbered line from another module stay visible.

### Juniper documentation skill factory

- **Added**: A new package `src/juniper_skills/` converts the harvested Juniper
  Markdown corpus into agent-ready skill packages. The factory reads a converted
  document, joins its split parts, repairs the converter defects, re-fences the
  command samples, splits the text into bounded topics, restates each fact as a
  cited knowledge card, and assembles a domain skill. Each package holds three
  levels: a router, a document index, and a topic file. An agent reads the
  router and one topic instead of the whole document. A measured question costs
  6,856 bytes instead of 741,428 bytes, which is a 108 times reduction.
  Issue #2925.
- **Added**: A canonical skill store outside the repository publishes each skill
  by Windows directory junction to the GitHub Copilot path, the Claude path, and
  the repository `.github/skills` path. One build serves every agent host on the
  computer. Issue #2925.
- **Added**: A live watcher enqueues a document when the upstream converter
  writes it. The watcher ignores a touch that does not change content, waits for
  a slow write to finish, and rebuilds a whole part set when one part changes.
  Issue #2925.
- **Added**: A work queue records 5,693 logical documents, 10,081 parts, 28
  split part sets, and 4,186 duplicates. A version resolver marks 593 documents
  superseded across 115 product families, so the factory skips 102,198 pages of
  obsolete product versions. Issue #2925.
- **Security**: A verbatim similarity guard measures the longest run of prose
  that a generated topic shares with its source. The guard clears a run of 0 to
  7 words, warns at 8 to 12 words, and fails at 13 words. It excludes commands,
  configuration, command output, identifiers, numeric limits, and standard
  names, because the factory keeps those verbatim on purpose. A measured
  experiment flagged a verbatim copy at 42 words and a lightly edited copy at 14
  words, and cleared a genuine restatement at 1 word. A guard that checks zero
  files fails. Issue #2925.

# Research: Grade Python user text in the STE linter

## Decision: use `ast` call nodes

The implementation uses `ast` because it gives stable line numbers and direct access to call arguments. It also separates f-string constant text from expressions.

**Alternatives considered**:

- Token scanning. Token scanning sees strings but cannot reliably connect a literal to its call.
- Regular expressions. Regular expressions cannot safely parse nested calls or f-strings.

## Decision: clean text before span creation

The parser removes format placeholders and code tokens before the segmenter sees the text. This keeps the existing rules unchanged and keeps identifiers out of the grade.

**Alternatives considered**:

- Add a new rule skip path. That would spread Python-specific knowledge into general STE rules.
- Keep placeholders as words. That would produce false findings and wrong word counts.

## Decision: opt-in defaults

The new categories default off because the repository holds many existing logging strings. A default-on change would alter the score of old files outside this feature.

Operators can enable the new surfaces when they are ready to repair the reported text.

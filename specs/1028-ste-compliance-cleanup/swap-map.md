# Curated Word-Swap Map

**Feature**: 1028-ste-compliance-cleanup | **Phase**: 1

This map holds the unapproved words that have a single clear approved replacement in
comment prose. The maintainer applies these to comment and docstring text only,
never to code, identifiers, quoted strings, URLs, or logging strings.

A word is in this map only when the replacement fits every prose use with the same
meaning. Words with several senses are left out on purpose.

## Map

| Unapproved word | Approved replacement | Note |
| - | - | - |
| via | by | Or "through" when it means a path. |
| per | for each | "as per" becomes "as stated in". |
| attempt (verb) | try | The verb sense only. |
| attempt (noun) | try | Keep the noun as "try" or reword. |
| failure | fault | When it means a fault condition. |
| failed | did not work | Or "stopped" when it means a stop. |
| whether | if | When it introduces a condition. |
| both | the two | Matches the STE recurring-errors list. |
| prior to | before | Common non-STE phrase. |
| in order to | to | Removes filler. |
| additional | more | Matches the dictionary alternative. |
| adequate | sufficient | Matches the dictionary alternative. |
| approximately | about | Shorter and approved. |
| initiate | start | Matches the "start" convention. |
| terminate | stop | When it means to stop. |
| utilize | use | Plain word. |
| obtain | get | Plain word. |
| require | need | When it means need. |

## Words deliberately excluded

These frequent words are left unchanged because they are correct programming terms,
comment markers, or words with several senses. They belong in the allowlist, not the
swap map.

- `Log`, `log`, `file`, `list`, `call`, `return`, `run`, `build`, `dispatch`,
  `exception`, `option`, `progress`, `trace`, `pass`, `detect` — programming terms.
- `NOTE`, `Note` — comment markers, not prose.
- `present`, `real`, `direct`, `now`, `already`, `never`, `any`, `may` — several
  senses, or already clear enough. A wrong swap would change the meaning.

## Application rule

For each comment, replace only a whole-word prose use. Keep the sentence meaning.
After the pass, run the linter to confirm the mapped words dropped, and run the test
suite to confirm no code changed.

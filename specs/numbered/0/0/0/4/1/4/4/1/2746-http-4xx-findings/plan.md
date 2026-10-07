# Implementation plan

## Route

The fixed-width base-5 value of 2746 is `00041441`.

`2746 = 4 x 625 + 1 x 125 + 4 x 25 + 4 x 5 + 1`.

## Method

1. Measure the live findings.
2. Capture the analyzer failure output.
3. Exclude the files that PR #4067 and PR #4076 own.
4. Classify each of the 36 available findings.
5. Add source-driving HTTP 4xx evidence.
6. Repair false Mist SDK status exceptions.
7. Prune stale baseline entries.
8. Run the repository gates.
9. Rebase and measure again.
10. Push one time.

## Constraints

- Do not edit issue #2747 files.
- Do not edit an active pull request file.
- Do not edit the listed protected source files.
- Do not invent a baseline count.


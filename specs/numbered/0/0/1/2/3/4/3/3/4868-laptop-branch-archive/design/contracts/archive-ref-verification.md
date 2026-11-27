# Contract: Archive Ref Verification (GET)

## Scope

This contract defines the read interface between this record and origin. Origin is the GitHub repository `jmorrison-juniper/MistHelper`. Every request is a GET request. The checks in `design/quickstart.md` use these requests and no other.

## Requests

| # | Request path | Purpose | Expected count |
| - | - | - | - |
| Q-1 | `repos/jmorrison-juniper/MistHelper/git/matching-refs/heads/archive/laptop-20261121/` | Archive refs, including the stash ref | 491 |
| Q-2 | `repos/jmorrison-juniper/MistHelper/git/matching-refs/heads/rescue/uncommitted-20261121-` | Rescue branches | 6 |
| Q-3 | `repos/jmorrison-juniper/MistHelper/git/matching-refs/heads/` | Branch listing for the counterpart check | 598 |
| Q-4 | `repos/jmorrison-juniper/MistHelper/git/ref/heads/` followed by one branch name | One branch lookup | One object, or HTTP 404 |
| Q-5 | `repos/jmorrison-juniper/MistHelper/compare/` followed by a base and a head joined by three dots | Compare two tips | One object |
| Q-6 | `repos/jmorrison-juniper/MistHelper/commits/` followed by one commit SHA | Parent count of a rescue commit | One object |

Q-1, Q-2, and Q-3 use the `--paginate` option of `gh api`. Each request returns every page of results.

## Response Shape

Q-1, Q-2, and Q-3 return a JSON array. Each item holds these fields:

- `ref` (string): The full ref name, for example `refs/heads/archive/laptop-20261121/stash-0`.
- `object.sha` (string): The tip commit, as 40 lowercase hexadecimal characters.
- `object.type` (string): The value `commit` for each branch in this record.

The other fields, such as `node_id` and `url`, stay unread.

Q-4 returns one object with the same `ref` and `object` fields. HTTP 404 means that the branch is absent.

Q-5 returns these fields:

- `status` (string): One of `ahead`, `behind`, `identical`, or `diverged`.
- `ahead_by` (integer): The count of commits in the head that the base lacks.
- `behind_by` (integer): The count of commits in the base that the head lacks.

Q-6 returns `parents`, a JSON array. This record reads the length of the array.

## Output Columns

For each listed name, the record writes these columns:

1. The listed name, without the prefix `archive/laptop-20261121/` for archive refs.
2. The tip, as the first seven characters of `object.sha`.
3. The counterpart state, one of `none`, `differs`, `self`, or `not applicable`.
4. The claimed unpushed commit count from the issue body.

## Rules

1. Match names exactly. The prefix in Q-1 and Q-2 selects refs only. It does not match names by a partial string.
2. Treat an empty array from Q-1 or Q-2 as a count of zero. It does not mean an error.
3. Treat HTTP 404 from Q-4 as the absent state. It does not mean an error.
4. On HTTP 403 or HTTP 429, wait 60 seconds and retry up to three times. Then mark the check unverified.
5. Read the token only from the environment. Never print the token value.
6. Send no request other than GET. Never send a comment, label, edit, close, merge, or branch change.

Warning: a write request to origin can change a branch that another person needs. Do not send any write request from this contract.

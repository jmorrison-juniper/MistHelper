# Contract: Branch inventory

The branch inventory lists each stranded branch once. The verification steps in `design/quickstart.md` produce it. The preservation pull requests quote its rows. The inventory is a data file. It is not a product output.

## File

- Encoding: UTF-8 text, no byte order mark.
- Format: CSV with one header row. Use standard CSV quoting for any value with a comma, a quote, or a line break.
- Line end: the CSV writer default.
- Order: branch name in ordinal ascending order. Each branch appears once.
- Location: write the file outside the repository, for example under the session files folder. Do not commit the file.

## Columns

The header row holds these columns in this order.

| Column | Holds | Allowed values |
| - | - | - |
| `branch` | The branch name without `refs/heads/`. | Text. |
| `head_sha` | The full head SHA from GitHub. | 40 lowercase hexadecimal characters. |
| `main_sha` | The full `main` SHA used for the local counts. | 40 lowercase hexadecimal characters. |
| `ahead_commits` | The commits reachable from the head and not from `main`. | Integer, 0 or more. |
| `changed_paths` | The changed path entries between `main` and the head. | Integer, 0 or more. |
| `open_pull_requests` | The open pull request numbers whose head name equals the branch. | Numbers separated by spaces. Empty when none exists. |
| `closed_pull_requests` | The closed or merged pull request numbers whose head name equals the branch. | Numbers separated by spaces. Empty when none exists. |
| `holder_state` | Whether a pull request holds the current head. | `stranded` or `held`. |
| `overlap_pull_requests` | The open pull request numbers that share a changed path. | Numbers separated by spaces. Empty when none exists. |
| `owner_head_check` | The comparison with the head value in the owner comment. | `same`, `changed`, `not-recorded`, or `private`. |
| `batch` | The preservation batch. | `1`, `2`, or `3`. |
| `privacy_flag` | The privacy hold state. | `none` or `metadata-only`. |
| `commit_subjects` | The subjects of the commits ahead, newest first. | Text joined with ` / `. Empty when `privacy_flag` is `metadata-only`. |

## Rules

- A row with `privacy_flag` `metadata-only` holds no path name and no commit subject.
- A row with `holder_state` `held` names at least one pull request in `open_pull_requests` or `closed_pull_requests`. That pull request has a head SHA equal to `head_sha`.
- A row with `holder_state` `stranded` names no pull request in `open_pull_requests` or `closed_pull_requests` with a head SHA equal to `head_sha`.
- A row with `batch` `2` names at least one pull request in `overlap_pull_requests`.
- The file holds 51 data rows for issue #4719.

## Example header and first row

```text
branch,head_sha,main_sha,ahead_commits,changed_paths,open_pull_requests,closed_pull_requests,holder_state,overlap_pull_requests,owner_head_check,batch,privacy_flag,commit_subjects
fix/3158-wip-controls,0f6b375e71243311b5cf5856fe9f220842a14e3b,f03c6c9b36d612a48d7b9652998c2fd87dd777ca,1,7,,,stranded,,same,1,none,chore(web-portal): keep the uncommitted draft of #3158 [skip ci]
```

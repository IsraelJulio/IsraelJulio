# All-branch activity calendar

The workflow runs daily at 06:23 UTC (03:23 in Sao Paulo), manually from Actions, and when its implementation changes on main.

It enumerates all public repositories owned by IsraelJulio (including forks), all existing branches, and commits attributed to IsraelJulio. All API pages are read. Identical SHAs are counted once globally. Dates are author dates in UTC, restricted to the last 365 days.

## Additional repositories

For public repositories owned by someone else where you contribute, set the repository Actions variable ACTIVITY_EXTRA_REPOSITORIES to a comma-separated list such as owner/project,another/project. These are explicit additions; the calendar does not automatically discover all repositories you have ever contributed to.

## Scope and limitations

- Private repositories are not included. The default workflow token cannot read other private repositories. Supporting those requires a separately scoped read token and an explicit privacy policy for published aggregate data.
- Local commits, deleted branch history no longer reachable from any branch, unlinked author emails, and inaccessible repositories cannot be counted.
- Rebased or cherry-picked commits with different SHAs count separately.
- API errors fail the run and retain the previous image rather than publishing a partial total.
- The calendar is separate from GitHub's native contributions graph.
- To run immediately after merging, open Actions > Update all-branch activity > Run workflow.

# Local Overrides (`karpathy-guidelines`)

These local rules extend `SKILL.md` and must be preserved across upstream syncs.

## Keep Comments, Counts, and Docs in Sync (Pre/Post-Commit Diff Check)

When your changes invalidate comments, counts, or docs elsewhere:
- Comments, counters/totals, and docs are often separated from the edited lines and silently go stale. Update any comment, count description, or related doc invalidated by your change (while still avoiding unrelated edits).
- **Before `git commit`**: review `git diff` (and `git diff --staged`) to verify that comments, counts/summaries, and related docs are in sync with the code change.
- **After `git commit`**: run `git diff HEAD~1 HEAD` (or `git show`) to compare before and after the commit and double-check nothing was missed or left stale.

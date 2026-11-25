# Local Overrides (`web-gui-tester`)

These local rules extend `SKILL.md` and must be preserved across upstream syncs.

## Persistence with `sort-out`

When saving persistent test reports or screenshot directories (e.g., `gui-test-screenshots/` or a Markdown report file) inside a project:
- Check whether `sort-out.config.txt` exists at the project root. If it does not exist yet, invoke the `sort-out` skill once first to initialize it.
- Follow the project's registered test-artifact paths and tracked-vs-local boundary.
- Register any persistent report/config paths used by this skill in `sort-out.config.txt` with `关联Skill` including `web-gui-tester` (appending with a comma if shared with other skills, never overwriting existing entries).
